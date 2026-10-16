"""TỪ ĐIỂN KHỐI BẮT ĐẦU — nửa «thiết lập» của một thuật toán.

Một script QuantConnect có HAI nửa, và sơ đồ ta vẽ phải ra đúng cả hai:

    def initialize(self):      ← NÓI MỘT LẦN: ngày nào, bao nhiêu tiền, mã nào, nhịp nào
    def on_data(self, data):   ← CHẠY LẠI mỗi nhịp: đọc, so, quyết, đặt lệnh

Sơ đồ (các khối Hỏi/Làm nối dây) là nửa dưới. **File này là nửa trên.** Đọc từ 444
thuật toán Python thật trong `Algorithm.Python/` của LEAN: `set_start_date` có mặt ở
395 cái, `set_end_date` 392, `set_cash` 250, `add_equity` 244 — tức nửa trên gần như
bắt buộc, mà canvas ta trước nay không có chỗ nào cho nó.

Cùng luật với `hoi.py` và `lam.py`: **mỗi ô phải chỉ ra được MỘT thứ có thật của
LEAN** (ô `lean`). Không khai được thì không được có mặt.

MỘT KHỐI ÔM TRỌN, và nó giải luôn hai thứ tưởng phải đẻ khối mới:

  · **Vòng lặp nhiều mã** — không cần khối "Với mỗi mã". Ô `nhip` + ô `ma` đã khai
    trọn vòng rồi: *"mỗi nến, cho mỗi mã trong danh sách"*. Cả sơ đồ bên dưới là ruột
    vòng. Vòng vẫn HIỆN RA (luật D-13), chỉ là hiện ở đúng chỗ nó sinh ra.
  · **Cái hack "chỉ một lần mỗi ngày"** — hai chiến lược kinh điển của QC
    (`MACDTrendAlgorithm`, `MovingAverageCrossAlgorithm`) đều phải tự nhớ *hôm qua là
    ngày nào* để chặn bớt. Đó là TRẠNG THÁI, đúng thứ ta cấm. Họ viết vậy vì không có
    cách khai nhịp; ta có ô `nhip`, nên cái hack ấy biến mất.

KHÔNG thành ô — bộ sinh mã tự lo:
  · **Làm nóng** (`set_warm_up`) — lấy chu kỳ dài nhất trong các chỉ báo đã vẽ trên sơ
    đồ. Đếm trên sơ đồ của CHÍNH TA, không tính trên dữ liệu thị trường, nên vẫn trong
    luật. Không có nó thì N nến đầu cỗ máy quyết định trên số rác.
  · **Khai chỉ báo** — `self.rsi("XAU", 14)` phải nằm trong `initialize`, và LEAN tự
    cập nhật mỗi nến (*"We never need to 'update' our indicators"* — chú thích trong
    `MovingAverageCrossAlgorithm`). Bộ sinh mã nhặt từ các khối Hỏi lên.

CỐ Ý CHƯA CÓ: `add_universe` (chọn mã động theo điều kiện — 97/444 thuật toán dùng) và
cửa vào thứ hai (`schedule.on` riêng, cho kiểu *mỗi nến xem tín hiệu + cuối tháng cân
danh mục*). Cả hai là khối khác, việc khác. Ghi lại để biết là bỏ có chủ ý.
"""

# ---------------------------------------------------------------------------
# Kiểu của một ô — ba kiểu đầu dùng chung với `lam.py`, hai kiểu cuối riêng
# ---------------------------------------------------------------------------
O_SO = "so"
O_CHU = "chu"
O_CHON = "chon"
O_KHOANG_NGAY = "khoang_ngay"   # {"tu": "2010-01-01", "den": "2019-01-01"}
O_DS_MA = "ds_ma"               # [{"ma": "XAUUSD", "loai": "cfd"}, …]


def _o(ten, nhan, kieu, mac_dinh, lean, don_vi="", goi_y="", chon=(), bat_buoc=True):
    return {"ten": ten, "nhan": nhan, "kieu": kieu, "mac_dinh": mac_dinh,
            "lean": lean, "don_vi": don_vi, "goi_y": goi_y, "chon": list(chon),
            "bat_buoc": bat_buoc}


# ---------------------------------------------------------------------------
# Loại tài sản — mỗi loại một hàm `add_*` riêng của LEAN
# ---------------------------------------------------------------------------
#: (mã, nhãn, hàm LEAN). Không gộp thành một `add_security` chung: LEAN có sáu hàm
#: khác nhau vì sáu loại có giờ giao dịch, đơn vị và đòn bẩy khác nhau.
LOAI_TAI_SAN = (
    ("cfd", "CFD — vàng, dầu, chỉ số", "add_cfd"),
    ("equity", "Cổ phiếu", "add_equity"),
    ("forex", "Ngoại hối", "add_forex"),
    ("crypto", "Tiền mã hoá", "add_crypto"),
    ("index", "Chỉ số", "add_index"),
    ("future", "Hợp đồng tương lai", "add_future"),
)

#: Bộ dữ liệu MIỄN PHÍ đi kèm LEAN có sẵn mấy thứ này — đếm từ `Data/` trên đĩa.
#: Để hộp thoại gợi ý, KHÔNG phải để chặn: ai có dữ liệu riêng thì gõ mã khác.
CO_SAN_MIEN_PHI = {
    "cfd": ("XAUUSD", "DE30EUR"),
    "forex": ("EURUSD", "NZDUSD"),
    "equity": ("SPY", "AAPL", "IBM", "GOOG", "QQQ", "BAC", "AIG", "EEM", "USO"),
}


# ---------------------------------------------------------------------------
# Nhịp chạy — ĐỘ PHÂN GIẢI dữ liệu và KHI NÀO sơ đồ chạy, gộp làm một
# ---------------------------------------------------------------------------
# Hai thứ ấy trong LEAN là hai câu (`Resolution` lúc đăng ký mã, và `on_data` hay
# `schedule.on` lúc chạy), nhưng với người chơi nó là MỘT câu hỏi: *bao lâu tôi xem
# một lần*. Nên ở đây là một ô, và bộ sinh mã tách ra làm hai.
#
# `res` = độ phân giải dữ liệu phải đăng ký. Năm nhịp đầu chạy thẳng trong `on_data`;
# ba nhịp sau cần `schedule.on`, mà muốn hẹn được giờ trong ngày thì dữ liệu phải có
# nến phút — nên `res` của chúng là `MINUTE`, không phải `DAILY`.
NHIP = (
    ("tick", "Mỗi tick", "TICK", "on_data", ()),
    ("giay", "Mỗi nến giây", "SECOND", "on_data", ()),
    ("phut", "Mỗi nến phút", "MINUTE", "on_data", ()),
    ("gio", "Mỗi nến giờ", "HOUR", "on_data", ()),
    ("ngay", "Mỗi nến ngày", "DAILY", "on_data", ()),
    ("moi_ngay_luc", "Mỗi ngày đúng giờ", "MINUTE",
     "schedule.on(date_rules.every_day(ma), time_rules.at(gio, phut))",
     (("gio", "Giờ", 10, 0, 23), ("phut", "Phút", 0, 0, 59))),
    ("sau_mo_cua", "Mỗi ngày, sau khi MỞ cửa", "MINUTE",
     "schedule.on(date_rules.every_day(ma), time_rules.after_market_open(ma, so_phut))",
     (("so_phut", "Số phút sau khi mở", 10, 0, 390),)),
    ("truoc_dong_cua", "Mỗi ngày, trước khi ĐÓNG cửa", "MINUTE",
     "schedule.on(date_rules.every_day(ma), "
     "time_rules.before_market_close(ma, so_phut))",
     (("so_phut", "Số phút trước khi đóng", 10, 0, 390),)),
)

NHIP_THEO_MA = {n[0]: n for n in NHIP}


def nhip_cua(ma):
    return NHIP_THEO_MA.get(ma)


# ---------------------------------------------------------------------------
# Sàn — mô hình phí và trượt giá
# ---------------------------------------------------------------------------
# LEAN biết 37 sàn; đây là mấy cái khớp với dữ liệu miễn phí. Chọn sai sàn thì phí và
# trượt giá tính sai, mà backtest vẫn chạy ngon lành — nên nó đáng một ô.
SAN = (
    ("DEFAULT", "Mặc định của QuantConnect"),
    ("INTERACTIVE_BROKERS_BROKERAGE", "Interactive Brokers — cổ phiếu"),
    ("OANDA_BROKERAGE", "Oanda — CFD, ngoại hối"),
    ("BINANCE", "Binance — tiền mã hoá"),
    ("COINBASE", "Coinbase — tiền mã hoá"),
)


# ---------------------------------------------------------------------------
# SÁU Ô
# ---------------------------------------------------------------------------
O_BAT_DAU = [
    _o("ma", "Chạy trên mã nào", O_DS_MA,
       [{"ma": "XAUUSD", "loai": "cfd"}],
       "add_cfd / add_equity / add_forex / add_crypto / add_index / add_future",
       goi_y="Nhiều mã thì cả sơ đồ chạy lại một lượt cho TỪNG mã."),

    _o("khoang", "Từ ngày → đến ngày", O_KHOANG_NGAY,
       {"tu": "2010-01-01", "den": "2019-01-01"},
       "set_start_date(tu) · set_end_date(den)",
       goi_y="Dữ liệu vàng miễn phí có từ 20/03/2006 đến 25/02/2019."),

    _o("von", "Vốn", O_SO, 100000, "set_cash(von)", don_vi="$",
       goi_y="Tiền khởi đầu của cỗ máy."),

    _o("nhip", "Nhịp", O_CHON, "ngay",
       "Resolution.* · on_data hoặc schedule.on",
       chon=[(m, nhan) for m, nhan, _r, _c, _t in NHIP],
       goi_y="Bao lâu cỗ máy xem một lần."),

    _o("moc_so_sanh", "Mốc so sánh", O_CHU, "", "set_benchmark(ma)",
       goi_y="Để trống = LEAN tự chọn. Đây là thứ quyết định thắng hay thua.",
       bat_buoc=False),

    _o("san", "Sàn", O_CHON, "DEFAULT", "set_brokerage_model(BrokerageName.san)",
       chon=list(SAN), goi_y="Quyết phí và trượt giá tính theo kiểu nào."),
]

O_THEO_TEN = {o["ten"]: o for o in O_BAT_DAU}


def o_cua(gia_tri=None):
    """Mọi ô của khối Bắt đầu, KỂ CẢ ô chỉ hiện theo nhịp đã chọn.

    Cùng lối với `lam.o_cua`: chọn "Mỗi ngày đúng giờ" thì ô Giờ/Phút mới hiện ra."""
    ra = list(O_BAT_DAU)
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if n:
        for ten, nhan, mac_dinh, nho, lon in n[4]:
            ra.append(_o(ten, nhan, O_SO, mac_dinh, n[3],
                         goi_y=f"Từ {nho} đến {lon}."))
    return ra


def ham_lean(gia_tri=None):
    """Câu LEAN quyết định nhịp — để hộp thoại nói thẳng ra cho người dùng thấy."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return ""
    return (f"add_*(ma, Resolution.{n[2]})" if n[3] == "on_data"
            else f"add_*(ma, Resolution.{n[2]}) · {n[3]}")


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối."""
    return {
        "o": O_BAT_DAU,
        "loai_tai_san": [{"ma": m, "nhan": n, "lean": h} for m, n, h in LOAI_TAI_SAN],
        "co_san": {k: list(v) for k, v in CO_SAN_MIEN_PHI.items()},
        "nhip": [{"ma": m, "nhan": n, "res": r, "chay": c,
                  "o_them": [{"ten": t, "nhan": nh, "mac_dinh": md,
                              "nho_nhat": no, "lon_nhat": lo}
                             for t, nh, md, no, lo in th]}
                 for m, n, r, c, th in NHIP],
    }
