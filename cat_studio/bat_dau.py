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

RỔ ĐỘNG — ô `ma` có HAI KIỂU. Chọn mã động từng là chỗ "cố ý chưa có" của file này,
và lời ghi hồi ấy nói sai một chữ: nó bảo đó phải là *khối khác, việc khác*. Không
phải. `set_universe_selection` gọi MỘT LẦN trong `initialize`, đúng cùng một luật với
ba ô chính sách ở dưới — *xảy ra mỗi nhịp thì thành khối, đặt một lần thì thành ô*.
Nên nó là KIỂU THỨ HAI của chính ô «Chạy trên mã nào», không phải một khối mới. Xem
mục «RỔ ĐỘNG» ở dưới.

CỐ Ý CHƯA CÓ: cửa vào thứ hai (`schedule.on` riêng, cho kiểu *mỗi nến xem tín hiệu +
cuối tháng cân danh mục*). Đó là khối khác, việc khác. Ghi lại để biết là bỏ có chủ ý.
"""

# ---------------------------------------------------------------------------
# Kiểu của một ô — ba kiểu đầu dùng chung với `lam.py`, hai kiểu cuối riêng
# ---------------------------------------------------------------------------
O_SO = "so"
O_CHU = "chu"
O_CHON = "chon"
O_KHOANG_NGAY = "khoang_ngay"   # {"tu": "2010-01-01", "den": "2019-01-01"}
O_DS_MA = "ds_ma"               # [{"ma": "XAUUSD", "loai": "cfd"}, …]


def _o(ten, nhan, kieu, mac_dinh, lean, don_vi="", goi_y="", chon=(),
       bat_buoc=True, nguyen=False, nhom=""):
    """Một ô của khối Bắt đầu.

    `nguyen` = chỉ nhận số NGUYÊN (giờ, phút). Khai ở đây chứ không để giao diện tự
    biết: "phút có được lẻ không" là luật của ô, mà luật của ô thì thuộc về từ điển.
    Giao diện từng tự quyết chuyện ấy, và cũng chính nó tự chế luôn câu gợi ý từ hai
    khoá không hề tồn tại — in ra "Từ undefined đến undefined" suốt một thời gian."""
    return {"ten": ten, "nhan": nhan, "kieu": kieu, "mac_dinh": mac_dinh,
            "lean": lean, "don_vi": don_vi, "goi_y": goi_y, "chon": list(chon),
            "bat_buoc": bat_buoc, "nguyen": nguyen, "nhom": nhom}


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

#: NĂM NHÓM CỦA HỘP BẮT ĐẦU — thứ tự bày ra là thứ tự người ta nghĩ.
#:
#: ⚠ VÌ SAO CÓ BẢNG NÀY (18/10/2026). Hộp Bắt đầu mở ra là MỘT danh sách phẳng, và
#: hồi nó có sáu ô thì thế là đủ. Hôm nay nó có mười lăm ô chính cộng ô con của nhịp,
#: của quy tắc giờ, của rổ, của bốn trạm dây chuyền, của model phí và trượt giá —
#: hơn hai mươi ô xếp thành một cột. Không ô nào sai, mà cả hộp thì không đọc được:
#: «Đệm tiền mặt» đứng cạnh «Nhịp», «Mốc so sánh» đứng giữa «Chạy cho ai» và «Sàn».
#:
#: Nhóm khai Ở ĐÂY, không gõ cứng trong .tsx — cùng luật với mọi thứ khác trong từ
#: điển: thêm một ô mới là khai luôn nó thuộc nhóm nào, và giao diện có ngay. Gõ danh
#: sách nhóm bên TypeScript thì đó là bảng tra thứ hai, và nó sẽ tụt lại.
NHOM_O = (
    ("chay_gi", "Chạy trên cái gì", "mã nào, giá tính thế nào, mỗi mã một lượt hay "
                                    "cả rổ một lượt"),
    ("tien", "Thời gian và tiền", "từ bao giờ đến bao giờ, bao nhiêu tiền"),
    ("nhip", "Nhịp — xem lại khi nào", "mỗi nến, hay hẹn giờ theo lịch"),
    ("day_chuyen", "Dây chuyền LEAN", "tín hiệu đi qua bốn trạm: phát → chia vốn → "
                                      "phòng rủi ro → đặt lệnh"),
    ("chi_phi", "Sàn và chi phí", "phí và trượt giá tính theo kiểu nào"),
    ("do_luong", "Đo lường", "so cỗ máy này với cái gì"),
)

#: Ô nào KHÔNG khai nhóm thì rơi về nhóm này — bày ra cuối cùng. Rơi về êm thì một ô
#: mới quên khai nhóm sẽ biến mất khỏi hộp thoại mà không ai thấy; rơi về đây thì nó
#: vẫn hiện, chỉ là hiện ở cuối, và `test_bat_dau` bắt được chuyện quên khai.
NHOM_KHAC = "khac"


#: Loại tài sản nào NHẬN được tham số `data_normalization_mode`. Đọc chữ ký trong
#: `Algorithm/QCAlgorithm.cs`: chỉ `AddEquity` và `AddFuture` có tham số ấy;
#: `AddForex` / `AddCrypto` / `AddCfd` / `AddIndex` thì KHÔNG.
#:
#: ⚠ Sinh nó cho loại không nhận là `TypeError` ngay dòng `initialize` — mà ô «Chuẩn
#: hoá giá» thì nằm ở khối Bắt đầu, chung cho mọi mã, nên một sơ đồ vàng + cổ phiếu
#: là nửa số dòng `add_*` sai. Phải lọc theo từng mã.
NHAN_CHUAN_HOA = ("equity", "future")

def _o_mo_hinh(ten, nhan, mac_dinh, don_vi="", goi_y="", nguyen=False):
    """Một ô CON của model phí / trượt giá — nằm TRONG bảng của model ấy."""
    return _o(ten, nhan, O_SO, mac_dinh, "", don_vi=don_vi, goi_y=goi_y,
              nguyen=nguyen)


#: PHÍ — `security.set_fee_model(...)`.
#:
#: ⚠ Ô «Sàn» ĐÃ quyết phí rồi, nên bảng này là để GHI ĐÈ nó. vd3 trong tập ví dụ làm
#: đúng thế: `SetSecurityInitializer(lambda s: s.SetFeeModel(ConstantFeeModel(0)))` —
#: chạy backtest không phí, để xem chiến thuật tự nó lãi bao nhiêu.
#:
#: LEAN có 32 model phí, nhưng 30 trong số đó là phí CỦA TỪNG SÀN
#: (`BinanceFeeModel`, `KrakenFeeModel`…), và chọn sàn ở ô «Sàn» là đã lấy đúng cái
#: ấy. Bày lại 30 dòng nữa là bày hai cách nói một thứ, và còn mời người dùng chọn
#: `BinanceFeeModel` cho một sơ đồ cổ phiếu Mỹ. Nên ở đây chỉ hai dòng KHÔNG gắn với
#: sàn nào — `test_du_lean` canh chuyện ấy, và 30 model kia khai lý do ở đó.
#:
#: (mã, nhãn, ô con, CÂU LEAN)
PHI = (
    ("", "— theo Sàn đã chọn —", (), ""),
    ("ConstantFeeModel", "Phí CỐ ĐỊNH mỗi lệnh",
     (_o_mo_hinh("phi_moi_lenh", "Phí mỗi lệnh", 0.0, don_vi="$",
                 goi_y="Để 0 là chạy KHÔNG phí — xem chiến thuật tự nó lãi bao "
                       "nhiêu trước khi trừ phí."),),
     "ConstantFeeModel(phi_moi_lenh)"),
    ("InteractiveBrokersFeeModel", "Theo bảng phí Interactive Brokers", (),
     "InteractiveBrokersFeeModel()"),
)

#: TRƯỢT GIÁ — `security.set_slippage_model(...)`. Cùng lối `PHI`.
TRUOT_GIA = (
    ("", "— theo Sàn đã chọn —", (), ""),
    ("ConstantSlippageModel", "Trượt giá CỐ ĐỊNH theo phần",
     (_o_mo_hinh("truot_phan", "Trượt mỗi lệnh", 0.001, don_vi="phần",
                 goi_y="0.001 = 0,1% giá. Đây là PHẦN, không phải phần trăm — "
                       "cùng lối ô «Đệm tiền mặt»."),),
     "ConstantSlippageModel(truot_phan)"),
    ("VolumeShareSlippageModel", "Theo tỉ lệ khối lượng mình chiếm",
     (_o_mo_hinh("gioi_han_kl", "Tối đa chiếm", 0.025, don_vi="phần",
                 goi_y="Lệnh của mình chiếm tối đa ngần này khối lượng một nến."),
      _o_mo_hinh("tac_dong", "Hệ số tác động", 0.1, don_vi="lần")),
     "VolumeShareSlippageModel(gioi_han_kl, tac_dong)"),
    # Nhận CHÍNH thuật toán làm tham số đầu — đọc chữ ký:
    # `MarketImpactSlippageModel(IAlgorithm algorithm, …)`.
    ("MarketImpactSlippageModel", "Mô hình tác động thị trường (Almgren)", (),
     "MarketImpactSlippageModel(self)"),
    ("NullSlippageModel", "KHÔNG trượt giá", (), "NullSlippageModel()"),
)

#: Model phí / trượt giá -> `(app nuôi được không, nó CẦN gì)`. Cùng lối
#: `PHONG_RUI_RO_DOC`, và `test_du_lean` đọc thẳng bảng này.
PHI_TRUOT_DOC = {
    "ConstantFeeModel": (True, "một con số phí, ô «Phí mỗi lệnh»"),
    "InteractiveBrokersFeeModel": (True, "không tham số"),
    "ConstantSlippageModel": (True, "một con số phần, ô «Trượt mỗi lệnh»"),
    "VolumeShareSlippageModel": (True, "giới hạn khối lượng + hệ số tác động"),
    "MarketImpactSlippageModel": (True, "chính thuật toán làm tham số đầu"),
    "NullSlippageModel": (True, "không tham số"),
    "AlphaStreamsSlippageModel":
        (False, "model dành riêng cho Alpha Streams của QuantConnect — không có "
                "dữ liệu ấy thì nó chỉ là một hằng số 0 không nói lên gì"),
}


def phi_cua(ma):
    """Một mục của `PHI` theo mã lớp. None nếu để trống hay mã lạ."""
    m = str(ma or "").strip()
    return next((x for x in PHI if x[0] and x[0] == m), None)


def truot_cua(ma):
    """Một mục của `TRUOT_GIA` theo mã lớp. None nếu để trống hay mã lạ."""
    m = str(ma or "").strip()
    return next((x for x in TRUOT_GIA if x[0] and x[0] == m), None)


#: CHUẨN HOÁ GIÁ — `DataNormalizationMode`, đủ tám cách của LEAN.
#:
#: Cổ tức và chia tách làm giá nhảy. LEAN cho tám cách tính chuyện đó vào giá, và
#: CHỌN SAI thì chiến thuật đọc được một mức giá khác hẳn — không lỗi, chỉ ra số
#: khác. vd4 khai `RAW`; vd7 · vd9 · vd10 đều gọi `SetDataNormalizationMode`. App
#: trước nay không có ô nào, tức mọi sơ đồ chạy ở `Adjusted` (mặc định LEAN) mà
#: không ai nói ra.
#:
#: Bốn cách sau chỉ có nghĩa với HỢP ĐỒNG TƯƠNG LAI nối chuỗi (hay chỉ dùng cho
#: `history`), và nhãn nói thẳng ra — bỏ chúng đi thì người dùng có dữ liệu futures
#: lại không dùng được đúng thứ LEAN cho.
CHUAN_HOA_GIA = (
    ("", "— theo mặc định LEAN (Adjusted) —"),
    ("RAW", "RAW — giá thật như đã khớp, không chỉnh gì"),
    ("ADJUSTED", "ADJUSTED — tính cả cổ tức và chia tách vào giá"),
    ("SPLIT_ADJUSTED", "SPLIT_ADJUSTED — chỉ tính chia tách, bỏ cổ tức"),
    ("TOTAL_RETURN", "TOTAL_RETURN — giá chia tách cộng dồn cổ tức"),
    ("FORWARD_PANAMA_CANAL",
     "FORWARD_PANAMA_CANAL — chỉ cho HĐ tương lai nối chuỗi (hợp đồng đầu giá thật)"),
    ("BACKWARDS_PANAMA_CANAL",
     "BACKWARDS_PANAMA_CANAL — chỉ cho HĐ tương lai (hợp đồng cuối giá thật)"),
    ("BACKWARDS_RATIO",
     "BACKWARDS_RATIO — chỉ cho HĐ tương lai, nối bằng tỉ số giá"),
    ("SCALED_RAW", "SCALED_RAW — chỉ dùng cho yêu cầu history"),
)

#: Bộ dữ liệu MIỄN PHÍ đi kèm LEAN có sẵn mấy thứ này — đếm từ `Data/` trên đĩa.
#: Để hộp thoại gợi ý, KHÔNG phải để chặn: ai có dữ liệu riêng thì gõ mã khác.
CO_SAN_MIEN_PHI = {
    "cfd": ("XAUUSD", "DE30EUR"),
    "forex": ("EURUSD", "NZDUSD"),
    "equity": ("SPY", "AAPL", "IBM", "GOOG", "QQQ", "BAC", "AIG", "EEM", "USO"),
}

#: Rổ ETF có dữ liệu CẤU THÀNH trong bộ miễn phí, và dữ liệu ấy rơi vào NGÀY NÀO.
#: Đếm từ `Data/equity/usa/universes/etf/` trên đĩa.
#:
#: ⚠ VÌ SAO PHẢI KHAI CẢ NGÀY. Rổ ETF chỉ "có dữ liệu" đúng mấy ngày ấy; backtest
#: không trùm qua ngày nào trong đó thì LEAN chọn ra RỖNG — chạy xong, không lỗi,
#: không cảnh báo, KHÔNG MỘT LỆNH NÀO. Đã dính thật: chọn QQQ cho 2020 ra 0 lệnh,
#: vì rổ QQQ miễn phí chỉ có đúng một ngày 30/03/2011. Cùng họ với nhãn «không có
#: dữ liệu» của ô mã — nói TRƯỚC, đừng để người ta chạy xong rồi ngồi đoán.
RO_ETF_CO_SAN = {
    "SPY": ("2020-11-30", "2020-12-01"),
    "QQQ": ("2011-03-30",),
    "GDVD": ("2020-12-10",),
}


def ro_etf_trum_khoang(ma_etf, tu, den):
    """Khoảng backtest có trùm qua ngày nào có dữ liệu rổ của ETF này không.

    -> (có hay không, mấy ngày có dữ liệu). ETF lạ thì trả (None, ()) — không biết
    chứ không phải không có, vì người dùng có thể tự tải dữ liệu rổ về."""
    ngay = RO_ETF_CO_SAN.get(str(ma_etf or "").strip().upper())
    if ngay is None:
        return None, ()
    tu, den = str(tu or ""), str(den or "")
    return any(tu <= n <= den for n in ngay), ngay


# ---------------------------------------------------------------------------
# Nhịp chạy — ĐỘ PHÂN GIẢI dữ liệu và KHI NÀO sơ đồ chạy, gộp làm một
# ---------------------------------------------------------------------------
# Hai thứ ấy trong LEAN là hai câu (`Resolution` lúc đăng ký mã, và `on_data` hay
# `schedule.on` lúc chạy), nhưng với người chơi nó là MỘT câu hỏi: *bao lâu tôi xem
# một lần*. Nên ở đây là một ô, và bộ sinh mã tách ra làm hai.
#
# `res` = độ phân giải dữ liệu MẶC ĐỊNH. Năm nhịp đầu chạy thẳng trong `on_data`, nên
# với chúng nhịp CHÍNH LÀ độ phân giải. Mấy nhịp hẹn giờ thì khác, và đây là chỗ bản
# D-15 suy luận SAI:
#
#   ⚠ Tôi từng viết "muốn hẹn được giờ trong ngày thì dữ liệu phải có nến phút" và ép
#     `MINUTE`. Sai. `schedule.on` chạy theo ĐỒNG HỒ của thuật toán, không theo lúc
#     dữ liệu về — nên dữ liệu NGÀY vẫn hẹn giờ được. Một chiến thuật thật (vd2) làm
#     đúng như thế: `Resolution.Daily` cộng `AfterMarketOpen(spy, 30)`.
#
#   Hậu quả của cái sai ấy không nhỏ: ép phút thì `self.sma(sym, 200)` thành 200
#   PHÚT chứ không phải 200 NGÀY — cùng một sơ đồ, khác hẳn chiến thuật.
#
# Nên nhịp hẹn giờ có thêm ô `do_phan_giai` cho người dùng tự chọn, mặc định NGÀY.
#: Ô ĐỘ PHÂN GIẢI — chỉ hiện với nhịp HẸN GIỜ. Với nhịp theo nến thì nhịp CHÍNH LÀ
#: độ phân giải, bày thêm một ô nữa chỉ tổ mâu thuẫn.
_O_DO_PHAN_GIAI = _o(
    "do_phan_giai", "Độ phân giải dữ liệu", O_CHON, "DAILY", "Resolution.…",
    chon=[("TICK", "Tick"), ("SECOND", "Giây"), ("MINUTE", "Phút"),
          ("HOUR", "Giờ"), ("DAILY", "Ngày")],
    goi_y="Lịch chạy theo ĐỒNG HỒ chứ không theo dữ liệu — nên dữ liệu ngày vẫn "
          "hẹn giờ được.")


def _o_phut(nhan, mac_dinh=10):
    # ⚠ `goi_y=` CÓ TÊN, không truyền chay: vị trí thứ sáu của `_o` là `don_vi`, nên
    # "Từ 0 đến 390." vẫn nằm ở ô ĐƠN VỊ suốt từ đầu — hiện ra cạnh ô số như một đơn
    # vị đo, còn ô gợi ý thì trống trơn.
    return _o("so_phut", nhan, O_SO, mac_dinh, "", goi_y="Từ 0 đến 390 phút.",
              nguyen=True)


# ⚠ Ô THỨ SÁU — CÙNG MỘT NHỊP, HAI CÂU LEAN, vì RỔ ĐỘNG không có mã nào để neo lịch
# vào. Năm câu `schedule.on` dưới đây đều cần một mã (`every_day(spy)`,
# `after_market_open(spy, 30)`): giờ mở cửa là giờ của SÀN mà mã ấy niêm yết. Rổ thì
# lúc `initialize` còn RỖNG, nên `self._ma[0]` ném `IndexError` ngay dòng đầu — cỗ
# máy chết trước khi chạy nến nào.
#
# LEAN có sẵn đường ra, và nó là cùng mấy hàm ấy ở dạng KHÔNG MÃ (đọc `DateRules.cs`
# và `TimeRules.cs`):
#   · `after_market_open(so_phut)` / `before_market_close(so_phut)` — *"Picks, per
#     date, the earliest market open across the algorithm's securities… Defaults to
#     US equities (SPY) when no eligible security is subscribed"*, và nó BỎ QUA ngày
#     sàn đóng (`EarliestMarketOpenTimes` không yield gì cho ngày đóng cửa).
#   · `every_day()` / `week_start()` — mọi ngày LỊCH.
#
# ⚠ Khác một chỗ, và chỗ ấy chỉ ảnh hưởng nhịp «Mỗi ngày đúng giờ»: `time_rules.at`
# là luật ĐỒNG HỒ thuần, không biết sàn đóng hay mở. Nên nhịp ấy cộng rổ động sẽ chạy
# cả THỨ BẢY, CHỦ NHẬT. Bốn nhịp kia neo vào giờ mở/đóng cửa nên tự bỏ ngày nghỉ.
#: QUY TẮC GIỜ — `time_rules.*`. Bảng RIÊNG, và đó là cả điểm.
#:
#: ⚠ VÌ SAO TÁCH LÀM HAI BẢNG (18/10/2026). Bản trước gộp «ngày nào» và «mấy giờ»
#: vào MỘT danh sách nhịp: `sau_mo_cua` · `truoc_dong_cua` · `tuan` · `thang_dau`…
#: Mỗi dòng là một CẶP đã chốt sẵn. Nhưng hai thứ ấy độc lập trong LEAN —
#: `schedule.on(date_rules.X, time_rules.Y)` nhận mọi X với mọi Y — nên một danh
#: sách cặp chỉ phủ được đúng những cặp ai đó nghĩ ra để thêm:
#:
#:     LEAN có 9 quy tắc ngày lặp lại × 5 quy tắc giờ = 45 cách.
#:     Bảng cặp cũ có 6 dòng. Và không ai thấy thiếu, vì nó không VỠ.
#:
#: Thật ra đã lòi ra hai lần rồi mà tôi vẫn vá theo cặp: thêm `tuan` khi vd2 cần,
#: thêm `thang_dau`/`thang_cuoi` khi ba ví dụ cần. Lần thứ ba thì phải sửa cái HÌNH,
#: không vá thêm dòng: nay 9 dòng ngày + 5 dòng giờ khai ra đủ 45 cách.
#:
#: (mã, nhãn, câu CÓ mã, câu KHÔNG mã, ô con)
QUY_TAC_GIO = (
    ("sau_mo", "sau khi MỞ cửa",
     "time_rules.after_market_open(ma, so_phut)",
     "time_rules.after_market_open(so_phut)",
     (_o_phut("Số phút sau khi mở", 30),)),
    ("truoc_dong", "trước khi ĐÓNG cửa",
     "time_rules.before_market_close(ma, so_phut)",
     "time_rules.before_market_close(so_phut)",
     (_o_phut("Số phút trước khi đóng", 30),)),
    ("truoc_mo", "trước khi MỞ cửa",
     "time_rules.before_market_open(ma, so_phut)",
     "time_rules.before_market_open(so_phut)",
     (_o_phut("Số phút trước khi mở", 30),)),
    ("sau_dong", "sau khi ĐÓNG cửa",
     "time_rules.after_market_close(ma, so_phut)",
     "time_rules.after_market_close(so_phut)",
     (_o_phut("Số phút sau khi đóng", 30),)),
    # ⚠ `time_rules.at` là luật ĐỒNG HỒ THUẦN — nó không biết sàn mở hay đóng. Cộng
    # với rổ động thì lịch chạy cả THỨ BẢY và CHỦ NHẬT. Bốn luật trên neo vào giờ
    # mở/đóng cửa nên tự bỏ ngày nghỉ. Nói ra trong nhãn, vì không nói thì người dùng
    # thấy lượt chạy có lệnh ngày cuối tuần rồi tưởng dữ liệu sai.
    ("dung_gio", "đúng giờ (kể cả ngày sàn ĐÓNG)",
     "time_rules.at(gio, phut)", "time_rules.at(gio, phut)",
     (_o("gio", "Giờ", O_SO, 10, "", goi_y="Từ 0 đến 23.", nguyen=True),
      _o("phut", "Phút", O_SO, 0, "", goi_y="Từ 0 đến 59.", nguyen=True))),
)

QUY_TAC_GIO_THEO_MA = {g[0]: g for g in QUY_TAC_GIO}


def gio_cua(ma):
    """Một mục của `QUY_TAC_GIO` theo mã. None nếu mã lạ."""
    return QUY_TAC_GIO_THEO_MA.get(str(ma or "").strip())


#: Ô chọn quy tắc giờ — chỉ hiện với nhịp HẸN GIỜ, xem `o_cua`.
_O_QUY_TAC_GIO = _o(
    "quy_tac_gio", "Lúc nào trong ngày", O_CHON, "sau_mo",
    "time_rules.*", chon=[(m, n) for m, n, *_ in QUY_TAC_GIO],
    goi_y="LEAN nhận mọi quy tắc ngày ghép với mọi quy tắc giờ, nên hai ô này độc "
          "lập với nhau.")

#: NHỊP. Năm dòng đầu là theo NẾN — nhịp chính là độ phân giải, không có lịch nào.
#: Chín dòng sau là HẸN GIỜ, mỗi dòng ĐÚNG MỘT quy tắc ngày của LEAN; giờ thì ô
#: `quy_tac_gio` quyết.
#:
#: ⚠ Ô THỨ TƯ VÀ THỨ SÁU — CÙNG MỘT NHỊP, HAI CÂU LEAN, vì RỔ ĐỘNG không có mã nào
#: để neo lịch vào. Mấy câu `schedule.on` đều cần một mã (`every_day(spy)`): giờ mở
#: cửa là giờ của SÀN mà mã ấy niêm yết. Rổ thì lúc `initialize` còn RỖNG, nên
#: `self._ma[0]` ném `IndexError` ngay dòng đầu — cỗ máy chết trước khi chạy nến nào.
#:
#: LEAN có sẵn đường ra, cùng mấy hàm ấy ở dạng KHÔNG MÃ (đọc `DateRules.cs` và
#: `TimeRules.cs`): *"Picks, per date, the earliest market open across the
#: algorithm's securities… Defaults to US equities (SPY) when no eligible security
#: is subscribed"*, và nó BỎ QUA ngày sàn đóng.
#:
#: ⚠ `date_rules.on(...)` và `date_rules.every(...)` KHÔNG có ở đây, cố ý: `on` nhận
#: một DANH SÁCH NGÀY cụ thể ("chạy đúng 3 ngày này"), `every` nhận một danh sách
#: THỨ ("chạy thứ Hai và thứ Tư"). Chúng không phải một nhịp lặp đều, nên chúng cần
#: một ô kiểu khác (chọn nhiều thứ / nhập danh sách ngày) — khai vào `test_du_lean`
#: kèm lý do, chứ không im.
NHIP = (
    ("tick", "Mỗi tick", "TICK", "on_data", (), "on_data"),
    ("giay", "Mỗi nến giây", "SECOND", "on_data", (), "on_data"),
    ("phut", "Mỗi nến phút", "MINUTE", "on_data", (), "on_data"),
    ("gio", "Mỗi nến giờ", "HOUR", "on_data", (), "on_data"),
    ("ngay", "Mỗi nến ngày", "DAILY", "on_data", (), "on_data"),

    ("moi_ngay", "Mỗi NGÀY", "MINUTE",
     "schedule.on(date_rules.every_day(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.every_day(), {gio})"),
    ("tuan", "Mỗi TUẦN — đầu tuần", "MINUTE",
     "schedule.on(date_rules.week_start(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.week_start(), {gio})"),
    ("tuan_cuoi", "Mỗi TUẦN — cuối tuần", "MINUTE",
     "schedule.on(date_rules.week_end(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.week_end(), {gio})"),
    ("thang_dau", "Mỗi THÁNG — đầu tháng", "MINUTE",
     "schedule.on(date_rules.month_start(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.month_start(), {gio})"),
    ("thang_cuoi", "Mỗi THÁNG — cuối tháng", "MINUTE",
     "schedule.on(date_rules.month_end(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.month_end(), {gio})"),
    ("quy_dau", "Mỗi QUÝ — đầu quý", "MINUTE",
     "schedule.on(date_rules.quarter_start(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.quarter_start(), {gio})"),
    ("quy_cuoi", "Mỗi QUÝ — cuối quý", "MINUTE",
     "schedule.on(date_rules.quarter_end(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.quarter_end(), {gio})"),
    ("nam_dau", "Mỗi NĂM — đầu năm", "MINUTE",
     "schedule.on(date_rules.year_start(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.year_start(), {gio})"),
    ("nam_cuoi", "Mỗi NĂM — cuối năm", "MINUTE",
     "schedule.on(date_rules.year_end(ma), {gio})",
     (_O_DO_PHAN_GIAI, _O_QUY_TAC_GIO),
     "schedule.on(date_rules.year_end(), {gio})"),
)

#: NHỊP CŨ -> (nhịp mới, quy tắc giờ). Ba mã này từng là ba dòng riêng trong bảng
#: cặp, nay cả ba đều là `every_day` chỉ khác quy tắc giờ. Giữ bảng này để FILE CŨ
#: MỞ ĐƯỢC — không có nó thì mọi sơ đồ đã lưu đều thành "nhịp lạ".
NHIP_CU = {
    "moi_ngay_luc": ("moi_ngay", "dung_gio"),
    "sau_mo_cua": ("moi_ngay", "sau_mo"),
    "truoc_dong_cua": ("moi_ngay", "truoc_dong"),
}

NHIP_THEO_MA = {n[0]: n for n in NHIP}


def nhip_cua(ma):
    """Một mục của `NHIP` theo mã, HIỂU CẢ MÃ CŨ (xem `NHIP_CU`).

    ⚠ Không có nhánh `NHIP_CU` thì mọi sơ đồ đã lưu đều thành «nhịp lạ»: ô `nhip`
    của chúng ghi `sau_mo_cua`, mã ấy không còn trong bảng nữa. Và `ham_chay` rơi về
    `on_data` khi nhịp lạ, nên cái sơ đồ cân lại danh mục mỗi ngày lúc mở cửa sẽ im
    lặng đổi thành chạy mỗi nến — không lỗi, không một lời nào."""
    m = str(ma or "").strip()
    if m in NHIP_CU:
        m = NHIP_CU[m][0]
    return NHIP_THEO_MA.get(m)


def gio_da_chon(gia_tri=None):
    """Quy tắc GIỜ của một khối Bắt đầu -> mục của `QUY_TAC_GIO`.

    Nhịp theo nến thì không có giờ nào -> None. Nhịp cũ (`NHIP_CU`) thì lấy quy tắc
    giờ mà mã cũ ấy từng mang, nên sơ đồ đã lưu sinh ra ĐÚNG câu LEAN như trước."""
    nhip = str((gia_tri or {}).get("nhip")
               or O_THEO_TEN["nhip"]["mac_dinh"]).strip()
    n = nhip_cua(nhip)
    if not n or n[3] == "on_data":
        return None
    v = str((gia_tri or {}).get("quy_tac_gio") or "").strip()
    if not v and nhip in NHIP_CU:
        v = NHIP_CU[nhip][1]
    return gio_cua(v) or gio_cua(_O_QUY_TAC_GIO["mac_dinh"])


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

#: ⚠ SÀN NÀO KHÔNG NHẬN LỆNH «KHỚP LÚC ĐÓNG CỬA» (MarketOnClose).
#:
#: Vì sao con số này đáng một ô riêng — ĐÃ GẶP THẬT, và nó hỏng LẶNG hoàn toàn:
#: với nhịp **mỗi nến NGÀY**, LEAN không có dữ liệu trong ngày để khớp lệnh thị
#: trường, nên nó tự đổi lệnh ấy thành **MarketOnClose** (xem `IsDailyResolutionOnly`
#: trong `QCAlgorithm.Trading.cs`). Sàn nào không nhận loại ấy sẽ từ chối SẠCH mọi
#: lệnh — mà backtest vẫn chạy hết và báo "111 lệnh, lãi 0%". Phải mở file
#: order-events ra đọc mới thấy chữ *"does not support MarketOnClose order type"*.
#:
#: Danh sách đọc thẳng từ `_supportedOrderTypes` của từng model trong
#: `Common/Brokerages/`: Oanda / Binance / Coinbase đều chỉ có
#: `[Limit, Market, StopMarket, StopLimit]`. Interactive Brokers và Default thì có.
# ---------------------------------------------------------------------------
# DÂY CHUYỀN CỦA LEAN — ba trạm đứng SAU cây quyết định
# ---------------------------------------------------------------------------
# Mỗi mục là MỘT lớp có thật trong `Algorithm.Framework/`, đã đối chiếu tên file.
# Để trống = không cắm trạm ấy.

#: Biến tín hiệu thành tỷ trọng. `EqualWeighting` chia đều 1/N cho mấy tín hiệu CÒN
#: HẠN — đọc mã nguồn: `percent = 1.0 / count`, với `count` đếm insight đang active.
#: ⚠ CHỈ BÀY MODEL MÀ KHỐI VẼ ĐƯỢC NUÔI. Mỗi model đọc một trường của `Insight`, và
#: trường nào không ai đặt thì model ấy chết LẶNG — đọc thẳng `Algorithm.Framework/
#: Portfolio/*.py`:
#:
#:   EqualWeighting            không đọc gì            -> chạy
#:   InsightWeighting          `insight.weight`        -> ô «Trọng số» của Phát tín hiệu
#:   ConfidenceWeighted        `insight.confidence`    -> CHƯA ai đặt được
#:   MeanVarianceOptimization  `insight.magnitude`     -> CHƯA ai đặt được
#:
#: Hai cái dưới: `should_create_target_for_insight` trả False cho MỌI tín hiệu (hay
#: `set_run_time_error` thẳng), nên chọn vào là backtest chạy hết rồi ra 0 lệnh, không
#: một lời nào. Thà không bày còn hơn bày rồi báo lỗi — thêm ô nuôi được chúng thì
#: mở lại, ĐỪNG mở trước.
#: ⚠ VÀ ĐÃ ĐẾM LẠI CẢ KỆ (18/10/2026). Luật trên đúng, nhưng suốt thời gian qua nó
#: chỉ được áp cho mấy model TÌNH CỜ GẶP trong ví dụ. Đếm thẳng
#: `Algorithm.Framework/Portfolio/` ra 10 model, app bày 2 — và ba trong tám cái còn
#: lại KHÔNG đọc khe nào của `Insight` cả, tức nuôi được ngay từ đầu:
#:
#:   RiskParity           không đọc khe nào  -> LEAN tự lấy history, tự tính biến
#:                                              động, tự cân rủi ro. ĐÂY đúng là
#:                                              40 dòng `_inv_vol_weights` mà vd7
#:                                              và vd9 phải viết tay.
#:   MeanReversion        không đọc khe nào
#:   AccumulativeInsight  chỉ đọc `direction` -> app đã đặt từ lâu
#:
#: Bài `test_du_lean` canh chỗ này từ nay: nó đếm kệ của LEAN rồi so với bảng này.
CHIA_VON = (
    ("", "— không dùng —"),
    ("EqualWeightingPortfolioConstructionModel", "Chia ĐỀU cho mọi tín hiệu (1/N)"),
    ("InsightWeightingPortfolioConstructionModel",
     "Chia theo TRỌNG SỐ — mã điểm cao được nhiều vốn hơn"),
    ("RiskParityPortfolioConstructionModel",
     "CÂN RỦI RO — mã càng biến động càng ít vốn (LEAN tự tính)"),
    ("MeanReversionPortfolioConstructionModel",
     "HỒI QUY TRUNG BÌNH — dồn vốn vào mã vừa rơi xa trung bình"),
    ("AccumulativeInsightPortfolioConstructionModel",
     "CỘNG DỒN — mỗi tín hiệu thêm 3% vị thế, tín hiệu sau cộng vào tín hiệu trước"),
    # ⚠ BA MODEL DƯỚI ĐÂY MỞ ĐƯỢC NHỜ HAI Ô MỚI ở khối «Phát tín hiệu» (`do_lon` =
    # magnitude, `do_tin` = confidence). Trước đó bộ sinh mã truyền `None` vào hai
    # khe ấy, nên ba model này trả False cho MỌI tín hiệu: chạy hết, 0 lệnh, không
    # một lời. Luật cũ «chỉ bày model mà khối vẽ được nuôi» vẫn nguyên — nay nuôi
    # được nên bày.
    ("MeanVarianceOptimizationPortfolioConstructionModel",
     "TỐI ƯU TRUNG BÌNH–PHƯƠNG SAI — LEAN dựng ma trận hiệp phương sai từ history"),
    ("BlackLittermanOptimizationPortfolioConstructionModel",
     "BLACK-LITTERMAN — trộn kỳ vọng của mình với cân bằng thị trường"),
    # Nhãn nói THẲNG chuyện nó chia y hệt «chia đều» khi mọi tín hiệu cùng độ tin:
    # ô «Độ tin» hiện là MỘT con số cho mọi mã, chưa phải đại lượng xếp hạng được.
    # Không nói ra thì người dùng chọn vào, thấy kết quả y chia đều, rồi ngồi đoán.
    ("ConfidenceWeightedPortfolioConstructionModel",
     "Chia theo ĐỘ TIN — cùng độ tin thì y như chia đều (ô «Độ tin» là một số chung)"),
)

#: Model chia vốn -> khe nào của `Insight` nó ĐỌC ("" = không đọc gì). Giữ cả mấy
#: model CHƯA bày, để bài kiểm biết vì sao chúng chưa bày và ai muốn mở lại thì phải
#: thêm ô nuôi khe ấy trước. Đọc `should_create_target_for_insight` của từng model.
CHIA_VON_DOC = {
    "EqualWeightingPortfolioConstructionModel": "",
    "InsightWeightingPortfolioConstructionModel": "weight",
    "RiskParityPortfolioConstructionModel": "",
    "MeanReversionPortfolioConstructionModel": "",
    "AccumulativeInsightPortfolioConstructionModel": "",
    "ConfidenceWeightedPortfolioConstructionModel": "confidence",
    "MeanVarianceOptimizationPortfolioConstructionModel": "magnitude",
    "BlackLittermanOptimizationPortfolioConstructionModel": "magnitude",
}

#: Model chia vốn CHƯA BÀY VÌ THIẾU DỮ LIỆU, không vì thiếu khe `Insight`. Tách khỏi
#: `CHIA_VON_DOC` vì hai bệnh khác nhau cần hai cách chữa khác nhau: khe thiếu thì
#: thêm ô; dữ liệu thiếu thì phải mua dữ liệu, app không làm gì được.
#:
#: Cùng một lối với `PHONG_RUI_RO_DOC["MaximumSectorExposure…"]` — hai model này
#: chặn ở ĐÚNG MỘT thứ (`CompanyReference.industry_template_code`), nên phải đối xử
#: giống nhau. Bày một cái ra và giấu một cái đi là cái kiểu không ai giải thích nổi
#: ba tháng sau.
CHIA_VON_THIEU_DU_LIEU = {
    "SectorWeightingPortfolioConstructionModel":
        (False, "fundamentals.company_reference.industry_template_code — không có "
                "dữ liệu doanh nghiệp thì nó bỏ qua MỌI mã và ra 0 lệnh"),
}


def _o_alpha(ten, nhan, mac_dinh, don_vi="", goi_y="", nguyen=True):
    """Một ô CON của một model Phát tín hiệu — nằm TRONG bảng `PHAT_TIN_HIEU`.

    Cùng lối `_o_ro` và `_o_nguong`: ô của model nào thì nằm trong dòng model ấy, nên
    đổi model là ô cũ đi theo, không còn một ô lơ lửng không thuộc câu nào."""
    return _o(ten, nhan, O_SO, mac_dinh, "", don_vi=don_vi, goi_y=goi_y,
              nguyen=nguyen)


#: TRẠM ALPHA của dây chuyền LEAN — model TỰ phát tín hiệu, không cần khối vẽ nào.
#:
#: ⚠ VÌ SAO TRẠM NÀY ĐÁNG CÓ. Sơ đồ của app phát tín hiệu bằng khối «Phát tín hiệu»,
#: và đó là một cách. LEAN còn một cách thứ hai: cắm một model Alpha, nó tự xem mọi
#: mã trong rổ rồi tự phát. vd4 trong `tai_lieu/chiến thuật ví dụ/` là đúng hình ấy —
#: 34 dòng, không một câu if nào, chỉ `add_alpha(...)` cộng ba trạm sau. Không có ô
#: này thì cả một họ chiến thuật của LEAN không vẽ được, mà lỗ hổng ấy KHÔNG lòi ra
#: ở đâu cả: sơ đồ vẫn vẽ được, backtest vẫn ra số.
#:
#: (mã, nhãn, ô con, CÂU LEAN). Trong câu: `{tên_ô}` thay bằng giá trị ô, `{res}`
#: thay bằng độ phân giải thật của sơ đồ.
#:
#: ⚠ `{res}` KHÔNG PHẢI MỘT Ô, và phải truyền. Bốn model dưới đây dựng chỉ báo rồi
#: nối consolidator theo tham số `resolution` của chính chúng, mặc định `DAILY`. Đó
#: đúng là bệnh `StandardDeviationExecutionModel` đã dính: tham số độ phân giải
#: không ai truyền thì model chạy ở mặc định của LEAN, và `CreateConsolidator` ném
#: ngoại lệ ngay nến đầu khi độ phân giải xin NHỎ HƠN cái đã đăng ký. Ô «Nhịp» đã
#: trả lời câu ấy rồi — hỏi lần thứ hai là mời người dùng nói hai câu khác nhau cho
#: một thứ.
PHAT_TIN_HIEU = (
    ("", "— không dùng —", (), ""),
    ("EmaCrossAlphaModel", "EMA nhanh cắt lên EMA chậm thì LÊN",
     (_o_alpha("ema_nhanh", "EMA nhanh", 12, don_vi="nến"),
      _o_alpha("ema_cham", "EMA chậm", 26, don_vi="nến")),
     "add_alpha(EmaCrossAlphaModel({ema_nhanh}, {ema_cham}, {res}))"),
    ("RsiAlphaModel", "RSI quá bán thì LÊN, quá mua thì XUỐNG",
     (_o_alpha("rsi_n", "Chu kỳ RSI", 14, don_vi="nến"),),
     "add_alpha(RsiAlphaModel({rsi_n}, {res}))"),
    ("MacdAlphaModel", "MACD vượt đường tín hiệu thì LÊN",
     (_o_alpha("macd_nhanh", "Chu kỳ nhanh", 12, don_vi="nến"),
      _o_alpha("macd_cham", "Chu kỳ chậm", 26, don_vi="nến"),
      _o_alpha("macd_tin_hieu", "Chu kỳ tín hiệu", 9, don_vi="nến")),
     "add_alpha(MacdAlphaModel({macd_nhanh}, {macd_cham}, {macd_tin_hieu}, "
     "MovingAverageType.EXPONENTIAL, {res}))"),
    # ⚠ MODEL NÀY CHỈ ĐỌC KWARGS. `__init__(self, *args, **kwargs)` rồi
    # `kwargs['lookback'] if 'lookback' in kwargs else 1` — truyền theo VỊ TRÍ là nó
    # bỏ qua LẶNG LẼ và chạy ở lookback=1. Nên câu dưới đây gọi bằng TÊN, và đó là
    # chỗ duy nhất trong bảng này gọi bằng tên.
    ("HistoricalReturnsAlphaModel", "Lợi suất N nến qua còn dương thì LÊN",
     (_o_alpha("nhin_lai", "Nhìn lại", 1, don_vi="nến"),),
     "add_alpha(HistoricalReturnsAlphaModel(lookback={nhin_lai}, "
     "resolution={res}))"),
    # ⚠ MODEL NÀY LEAN DỰNG CHO NHỊP PHÚT — mặc định của chính nó là
    # `Resolution.MINUTE`, và ĐÃ THỬ THẬT: bốn bộ tham số trên nhịp NGÀY
    # (nhìn lại 15/60/250, ngưỡng 0,5–2%, tương quan 0,3–0,5) đều ra 0 lệnh, 0
    # insight, không một ngoại lệ nào. Nó chỉ không tìm ra cặp nào đáng vào.
    #
    # Vẫn bày, và nói ra trong nhãn: app CÓ nhịp phút, nên model này dùng được thật
    # ở đó. Giấu đi thì người dùng không biết LEAN có lối giao dịch cặp.
    #
    # `nguong_lech` là PHẦN TRĂM 0–100, không phải số lần: docstring LEAN ghi rõ
    # *"The percent [0, 100] deviation of the ratio from the mean"*. Bản đầu tôi khai
    # đơn vị "lần" — đọc thì vẫn mượt, mà người dùng gõ 2 nghĩ là «gấp đôi» trong khi
    # LEAN hiểu «2%».
    ("PearsonCorrelationPairsTradingAlphaModel",
     "Giao dịch CẶP — hai mã tương quan cao mà giá rời nhau "
     "(LEAN dựng cho nhịp PHÚT; nhịp ngày thử ra 0 lệnh)",
     (_o_alpha("nhin_lai", "Nhìn lại", 15, don_vi="nến"),
      _o_alpha("nguong_lech", "Lệch khỏi trung bình quá", 1, don_vi="%",
               nguyen=False,
               goi_y="Tỉ số hai mã rời khỏi trung bình quá ngần này PHẦN TRĂM thì "
                     "phát tín hiệu. LEAN hiểu 0–100, nên 1 là 1%."),
      _o_alpha("tuong_quan_toi_thieu", "Tương quan tối thiểu", 0.5,
               don_vi="phần", nguyen=False,
               goi_y="Chỉ coi là một cặp đáng giao dịch khi tương quan từ ngần "
                     "này trở lên. 0.5 = 50%.")),
     "add_alpha(PearsonCorrelationPairsTradingAlphaModel({nhin_lai}, {res}, "
     "{nguong_lech}, {tuong_quan_toi_thieu}))"),
    ("ConstantAlphaModel", "Luôn phát MỘT hướng cho mọi mã trong rổ",
     (_o_alpha("han_tin", "Giữ tối đa", 15, don_vi="ngày"),),
     "add_alpha(ConstantAlphaModel(InsightType.PRICE, InsightDirection.UP, "
     "timedelta(days={han_tin})))"),
)

#: Model Alpha -> `(app nuôi được không, nó ĐỌC/CẦN cái gì)`. Cùng lối
#: `PHONG_RUI_RO_DOC`: giữ cả model CHƯA bày kèm lý do, và phần đầu là một CỜ chứ
#: không phải một câu — hàng rào đọc văn xuôi là hàng rào có lỗ.
PHAT_TIN_HIEU_DOC = {
    "EmaCrossAlphaModel": (True, "chỉ báo của chính nó · CẦN truyền độ phân giải"),
    "RsiAlphaModel": (True, "chỉ báo của chính nó · CẦN truyền độ phân giải"),
    "MacdAlphaModel": (True, "chỉ báo của chính nó · CẦN truyền độ phân giải"),
    "HistoricalReturnsAlphaModel":
        (True, "ROC của chính nó · CHỈ đọc kwargs, truyền theo vị trí là bỏ qua"),
    # Vẫn `True` — app nuôi được nó (truyền đủ bốn tham số, đúng đơn vị). Chuyện
    # «nhịp ngày ra 0 lệnh» là giới hạn của CHÍNH MODEL, không phải app thiếu gì, và
    # nó nói ra trong nhãn chứ không im.
    "PearsonCorrelationPairsTradingAlphaModel":
        (True, "history của cả rổ · tự tìm cặp tương quan cao nhất · LEAN dựng cho "
               "nhịp PHÚT, nhịp ngày đã thử 4 bộ tham số đều 0 lệnh"),
    "ConstantAlphaModel": (True, "không đọc gì — phát một hướng cố định"),
}


def _o_nguong(nhan):
    """Ô NGƯỠNG của một model phòng rủi ro — nó nằm TRONG bảng `PHONG_RUI_RO`.

    Cả bốn model nhận ĐÚNG MỘT tham số đầu là một phần trăm, nhưng phần trăm ấy
    nghĩa khác nhau ở từng model (lỗ / lãi / tụt khỏi đỉnh), nên mỗi model một
    nhãn riêng — y lối `NHIP` cho mỗi nhịp mấy ô thêm của riêng nó.

    ⚠ ĐƠN VỊ LÀ "PHẦN", KHÔNG PHẢI "%" — y hệt ô «Đệm tiền mặt». Giá trị đi THẲNG
    vào câu LEAN, không ai chia cho 100 ở giữa: có một phép tính giữa đường là có
    một chỗ cho hai bên nói khác nhau.

    Cùng tên ô cho cả bốn (`nguong`), nên đổi model thì con số người dùng vừa gõ
    còn nguyên, không bị reset về mặc định."""
    return _o("nguong", nhan, O_SO, 0.05, "", don_vi="phần",
              goi_y="0.05 = 5%. Mặc định của LEAN cũng là 0.05.")


#: Chạy SAU khi chia vốn, được quyền chỉnh lại tỷ trọng.
#: ⚠ Mấy thứ này trước đây ta TỪ CHỐI (SL/TP cần nhớ qua nến, xem `lam.py`). Lối cổ
#: điển thì đúng là cần; ở đây LEAN giữ mức hộ, app không nhớ gì cả.
#:
#: ⚠ MỖI MODEL KÈM Ô THÊM CỦA RIÊNG NÓ, cùng lối `NHIP` và `RO`. Cả bốn model đọc
#: `security.holdings.*` — thứ LEAN tự giữ, không khối vẽ nào phải nuôi — nên không
#: cái nào mắc bệnh của `CHIA_VON`. Nhưng cả bốn có MỘT THAM SỐ NGƯỠNG mà bộ sinh mã
#: trước đây không truyền, nên chúng chạy ở 5% mặc định của LEAN trong khi nhãn hứa
#: «theo %» mà không có ô % nào để điền. Ngưỡng là CẢ cái phanh; đóng cứng 5% rồi
#: không nói ra là một kiểu nói dối lặng — xem `PHONG_RUI_RO_DOC`.
PHONG_RUI_RO = (
    ("", "— không dùng —", ()),
    ("MaximumDrawdownPercentPerSecurity", "Cắt lỗ theo % từng mã",
     (_o_nguong("Cắt khi mã ấy lỗ quá"),)),
    ("MaximumUnrealizedProfitPercentPerSecurity", "Chốt lời theo % từng mã",
     (_o_nguong("Chốt khi mã ấy lãi quá"),)),
    ("MaximumDrawdownPercentPortfolio", "Cắt lỗ theo % CẢ danh mục",
     (_o_nguong("Cắt khi cả danh mục lỗ quá"),)),
    ("TrailingStopRiskManagementModel", "Trailing stop",
     (_o_nguong("Cắt khi tụt khỏi đỉnh lãi quá"),)),
)

#: Model phòng rủi ro -> `(app nuôi được không, nó ĐỌC/CẦN cái gì)`. Giữ cả model
#: CHƯA bày, kèm lý do — ai muốn mở lại thì phải nuôi được thứ ấy trước. Đọc
#: `manage_risk` của từng model trong `Algorithm.Framework/Risk/`.
#:
#: Khác `CHIA_VON_DOC` một chỗ quan trọng: ở đây không có model nào đọc một khe của
#: `Insight`. Cả bốn đọc trạng thái danh mục, thứ LEAN tự giữ. Cái CHẾT LẶNG ở trạm
#: này là một thứ khác — THAM SỐ KHỞI TẠO không ai truyền. Nên `CHIA_VON_DOC` khai
#: được bằng MỘT CHỮ (tên khe, đối chiếu thẳng với mấy khe khối tín hiệu điền), còn
#: hai bảng này phải khai thành hai phần.
#:
#: ⚠ PHẦN ĐẦU LÀ MỘT CỜ, KHÔNG PHẢI MỘT CÂU. Bản đầu của tôi gộp cả hai vào một
#: chuỗi rồi để bài kiểm dò chữ «CHƯA ai nuôi» trong đó — và khi tôi ép thử bằng cách
#: bày `SpreadExecutionModel` ra, bài kiểm XANH, vì dòng khai của nó nói lý do bằng
#: chữ khác. Một hàng rào đọc văn xuôi là một hàng rào có lỗ ở đúng chỗ người sau sẽ
#: bước vào.
PHONG_RUI_RO_DOC = {
    "MaximumDrawdownPercentPerSecurity":
        (True, "security.holdings.unrealized_profit_percent · ngưỡng = tham số 1"),
    "MaximumUnrealizedProfitPercentPerSecurity":
        (True, "security.holdings.unrealized_profit_percent · ngưỡng = tham số 1"),
    # ⚠ CHỈ CẮN Ở NHỊP CÓ MỤC TIÊU MỚI: `manage_risk` của nó có thêm điều kiện
    # `len(targets) != 0`, tức nó chỉ cắt khi model chia vốn VỪA phát ra mục tiêu
    # trong đúng nhịp ấy. `EqualWeighting`/`InsightWeighting` cân lại mỗi ngày nên
    # trên nhịp ngày là mỗi nến một lần — đã chạy thật, 12 lệnh so với 2. Ba model
    # kia quét `algorithm.securities` nên cắn ở MỌI nhịp.
    "MaximumDrawdownPercentPortfolio":
        (True, "portfolio.total_portfolio_value · ngưỡng = tham số 1 · CẦN nhịp "
               "có mục tiêu"),
    "TrailingStopRiskManagementModel":
        (True, "security.holdings.absolute_holdings_value · ngưỡng = tham số 1"),
    # CHƯA NUÔI ĐƯỢC: nó lọc `active_securities` theo `fundamentals.has_fundamental_
    # data` rồi nhóm theo `company_reference.industry_template_code`. Không có dữ
    # liệu fundamental thì danh sách lọc ra RỖNG và nó trả về [] mọi nhịp — chạy hết,
    # không lỗi, không tác dụng. Bộ miễn phí chỉ có `fundamental/coarse/` từ
    # 20140324, và chỉ cho mấy mã rổ.
    "MaximumSectorExposureRiskManagementModel":
        (False, "fundamentals.company_reference.industry_template_code — chưa có "
                "dữ liệu fundamental thì nó lặng"),
}

#: Cách đẩy tỷ trọng thành lệnh.
#:
#: ⚠ NHÃN PHẢI NÓI RA CON SỐ LEAN DÙNG. Hai model dưới cùng có tham số mặc định mà
#: app không truyền; chúng vẫn chạy đúng, nhưng người dùng không có đường nào biết
#: «lệch khỏi trung bình» là lệch mấy lần, của bao nhiêu nến. Nói ra trong nhãn thì
#: không cần thêm ô — khác ngưỡng cắt lỗ, đây là tham số TINH CHỈNH, không phải cả
#: cái phanh.
DAT_LENH = (
    ("", "— không dùng —"),
    ("ImmediateExecutionModel", "Đặt NGAY bằng lệnh thị trường"),
    ("VolumeWeightedAveragePriceExecutionModel",
     "Rải theo VWAP — chờ giá tốt hơn VWAP, mỗi nến tối đa 1% khối lượng"),
    ("StandardDeviationExecutionModel",
     "Chờ giá lệch 2 lần độ lệch chuẩn khỏi trung bình 60 nến"),
)

#: Model đặt lệnh -> `(app nuôi được không, nó ĐỌC/CẦN cái gì)`. Cùng lối
#: `PHONG_RUI_RO_DOC`, kể cả chuyện phần đầu là một CỜ chứ không phải một câu.
DAT_LENH_DOC = {
    "ImmediateExecutionModel": (True, "không đọc gì — đặt thẳng mọi mục tiêu"),
    # `price_is_favorable` đọc `security.bid_price`/`ask_price`. Trên dữ liệu chỉ có
    # nến giao dịch (bộ miễn phí) thì `SecurityCache` không đặt hai cái ấy, nhưng
    # `Security.BidPrice` có dòng `Cache.BidPrice == 0 ? Price : Cache.BidPrice` —
    # rơi về giá đóng, nên điều kiện vẫn có nghĩa. Đã chạy thật: 2 lệnh, giá khác
    # lượt không dùng model (lãi -13.248% so với -13.082%).
    "VolumeWeightedAveragePriceExecutionModel":
        (True, "security.bid_price/ask_price (rơi về giá đóng) · VWAP nội nhật "
               "tự dựng"),
    # ⚠ CHẾT THẬT, ĐÃ CHỨNG MINH. Tham số thứ ba `resolution` MẶC ĐỊNH LÀ
    # `Resolution.MINUTE`, mà `SymbolData` lấy consolidator theo đúng tham số ấy.
    # `QCAlgorithm.CreateConsolidator` ném `ArgumentException` khi độ phân giải xin
    # NHỎ HƠN độ phân giải đã đăng ký: "Unable to create SPY consolidator because
    # SPY is registered for Daily data." Nhịp ngày (mặc định của app) là chết ngay
    # nến đầu — backtest ghi ra kết quả, bảng Kết quả nói «0 lệnh, lãi 0%», câu lỗi
    # chỉ nằm trong nhật ký. Nên `lean_day_chuyen` PHẢI truyền độ phân giải thật.
    "StandardDeviationExecutionModel":
        (True, "SMA/STD của chính nó · CẦN truyền đúng độ phân giải của sơ đồ "
               "(tham số 3)"),
    # CHƯA NUÔI ĐƯỢC: docstring của CHÍNH LEAN ghi «will not work using Resolution.
    # DAILY since Exchange.exchange_open will be false». Thêm nữa `spread_is_
    # favorable` đòi `ask_price > 0 and bid_price > 0` VÀ chênh lệch mua/bán nhỏ hơn
    # ngưỡng — dữ liệu chỉ có nến giao dịch thì bid = ask = giá đóng, tức chênh lệch
    # 0, tức nó mất hẳn tác dụng. Chạy hết, không lỗi, không lọc gì.
    "SpreadExecutionModel":
        (False, "exchange.exchange_open + chênh lệch bid/ask — LEAN nói rõ KHÔNG "
                "chạy trên nhịp ngày"),
}


SAN_KHONG_NHAN_MOC = ("OANDA_BROKERAGE", "BINANCE", "COINBASE")


# ---------------------------------------------------------------------------
# RỔ ĐỘNG — khe thứ năm của dây chuyền: `set_universe_selection`
# ---------------------------------------------------------------------------
# Ô «Chạy trên mã nào» trước nay chỉ nói được MỘT câu: *mấy mã này, gõ sẵn*. Nhưng
# 97/444 thuật toán Python của LEAN không gõ mã nào cả — chúng nói *mã nào thoả điều
# kiện thì vào rổ*, và rổ ấy đổi theo ngày. Đó là nửa còn lại của «chạy trên cái gì».
#
# HAI KIỂU CHO MỘT Ô, đúng lối vế phải của điều kiện (một số / một đại lượng):
#   · ô `ma` là một LIST  -> mấy mã gõ sẵn, mỗi mã một câu `add_*`  (lối cũ);
#   · ô `ma` là một DICT  -> một rổ, một câu `set_universe_selection`.
# Phân biệt bằng HÌNH DẠNG chứ không bằng một ô "kiểu" riêng — nhờ vậy file cũ (ô `ma`
# là list) mở ra vẫn chạy, không cần di cư schema.
#
# Mỗi mục dưới đây là MỘT lớp CÓ THẬT, tên lấy từ tên file trong
# `Algorithm.Framework/Selection/`. Cả chín lớp đều là `UniverseSelectionModel`, nên
# cả chín cắm được vào đúng một câu `self.set_universe_selection(…)`.
#
# ⚠ CỐ Ý KHÔNG CÓ `ManualUniverseSelectionModel`, dù nó cũng có thật
# (`Algorithm/Selection/`). Nó nhận một danh sách mã gõ sẵn — tức ĐÚNG câu mà lối
# list ở trên đã nói, chỉ khác đường đi tới LEAN. Bày cả hai là bày cho người chơi
# hai cách nói một thứ, rồi để họ đoán cách nào mới đúng. Rổ ĐỘNG là lý do ô này có
# kiểu thứ hai; cái nào không động thì không vào đây.


def _o_ro(ten, nhan, kieu, mac_dinh, don_vi="", goi_y="", nguyen=False):
    """Một ô CON của rổ — nó nằm TRONG dict của ô `ma`, không phải ô riêng của khối.

    Vì sao nằm trong: «rổ nào» và «rổ ấy lấy mấy mã» là MỘT câu trả lời cho MỘT câu
    hỏi. Tách ra thành ô riêng của khối thì lưu một file chọn rổ ETF rồi đổi sang gõ
    mã tay là còn lại một ô `lay = 8` lơ lửng, không thuộc về câu nào."""
    return _o(ten, nhan, kieu, mac_dinh, "", don_vi=don_vi, goi_y=goi_y,
              nguyen=nguyen)


#: Lọc rổ ETF theo TRỌNG SỐ. Thân hàm khai Ở ĐÂY, không để bộ sinh mã tự nghĩ ra —
#: lời hứa D-11 là «bộ sinh mã không tự viết một câu LEAN nào», và một hàm lọc cũng
#: là mã LEAN.
#:
#: Ba dòng này chép từ ví dụ CỦA CHÍNH LEAN (`ETFConstituentsFrameworkAlgorithm.py`):
#:     selected = sorted([c for c in constituents if c.weight],
#:                       key=lambda c: c.weight, reverse=True)[:8]
#:     return [c.symbol for c in selected]
#: `weight` là trường CÓ THẬT của `ETFConstituentData` (`public decimal? Weight`), và
#: nó NULLABLE — nên dòng đầu phải gạn, y như LEAN gạn. Thiếu dòng ấy là `sorted` so
#: None với số và ném `TypeError` giữa lượt chọn rổ.
#:
#: Chỗ trống duy nhất là `{lay}`.
LOC_TRONG_SO = (
    "co = [c for c in ds if c.weight]",
    "co.sort(key=lambda c: c.weight, reverse=True)",
    "return [c.symbol for c in co[:{lay}]]",
)

#: (mã, nhãn, lớp LEAN, ô con, CÂU LEAN). Lớp nào không cần tham số thì ô con rỗng.
#:
#: ⚠ Ô THỨ NĂM — CÂU LEAN — THÊM NGÀY 18/10/2026, và đây là vì sao. Trước đó không rổ
#: nào khai câu của mình; `lean_ro` và `sinh_ma._ro_py` cùng ĐOÁN theo một dòng:
#:
#:     if ro[0] != "etf":  ->  f"set_universe_selection({lop}())"
#:
#: Tức mọi rổ khác ETF đều được gọi KHÔNG THAM SỐ. Đúng, nhưng đúng tình cờ: chín rổ
#: đang có thì tám cái thật sự không nhận tham số nào. Thêm một rổ CÓ tham số là nó
#: sinh ra lời gọi rỗng — `EmaCrossUniverseSelectionModel()` chạy ở 100/300/**500 mã**
#: mặc định của LEAN trong khi hộp thoại hứa «giữ 20 mã», và không một lời nào. Đúng
#: bệnh `StandardDeviationExecutionModel`: nhãn hứa một đằng, mã sinh ra một nẻo.
#:
#: Nay mỗi rổ tự khai, và CẢ HAI chỗ (hộp thoại + bộ sinh mã) gọi cùng `lean_ro`, nên
#: không còn hai bộ chữ để mà lệch nhau.
#:
#: Trong câu: `{tên_ô}` thay bằng giá trị ô ấy — ô CHỮ thành chuỗi Python có dấu
#: nháy, ô SỐ thành số. `{loc_ro}` là chỗ duy nhất có điều kiện, xem `lean_ro`.
RO = (
    ("etf", "Các mã trong một ETF", "ETFConstituentsUniverseSelectionModel",
     (_o_ro("ma_etf", "Mã ETF", O_CHU, "SPY",
            goi_y="Rổ là các mã CẤU THÀNH ETF này. Bộ miễn phí CHỈ có SPY "
                  "(30/11–01/12/2020) và QQQ (30/03/2011) — khoảng backtest phải "
                  "trùm qua đúng mấy ngày ấy, không thì rổ rỗng."),
      # «Lấy mấy mã» CẦN một hàm lọc, nên nó không chỉ là một con số — xem
      # `LOC_TRONG_SO` ngay trên.
      _o_ro("lay", "Lấy mấy mã", O_SO, 8, don_vi="mã", nguyen=True,
            goi_y="Lấy mấy mã NẶNG nhất trong ETF. Để 0 thì lấy cả rổ — SPY là "
                  "hơn 500 mã, nặng máy.")),
     "set_universe_selection(ETFConstituentsUniverseSelectionModel({ma_etf}, "
     "self.universe_settings{loc_ro}))"),
    # ⚠ BA RỔ DƯỚI ĐÂY DỰA TRÊN DỮ LIỆU DOANH NGHIỆP, và bộ miễn phí kèm LEAN chỉ
    # có đúng MƯỜI MỘT NGÀY của nó: `Data/equity/usa/fundamental/coarse/` từ
    # 24/03/2014 đến 07/04/2014. Ngoài khoảng ấy, LEAN nói thẳng trong nhật ký
    # *"Failed universe data requests 100%"* và rổ ra RỔNG — backtest chạy hết,
    # 0 lệnh, bảng Kết quả không một lời nào.
    #
    # `qc500` đã bày từ lâu mà nhãn KHÔNG nói chuyện ấy — một cái bẫy có sẵn, chỉ
    # lòi ra khi chạy thật rổ `ema_cheo`. Nay nói ngay trong NHÃN, đúng lối bảng
    # «Đặt lệnh» nói con số LEAN dùng vào nhãn vì không có ô nào để điền.
    #
    # ⚠ ĐÃ CHẠY THẬT, VÀ SỰ THẬT CÒN HẸP HƠN THẾ. Chạy `ema_cheo` trong đúng khoảng
    # 25/03–07/04/2014: «universe data requests 21/21 succeeded, 0 failed» — tức cơ
    # chế rổ chạy đúng. Nhưng 0 mã được chọn, vì mười một ngày không đủ LÀM NÓNG
    # EMA: mặc định của LEAN là EMA(100)/EMA(300), mà hạ xuống EMA(5)/EMA(10) thì
    # cũng vẫn 0. Nên với bộ dữ liệu miễn phí, ba rổ doanh nghiệp này BÀY RA ĐƯỢC
    # nhưng chưa chọn nổi một mã nào — mua bộ fundamental của QuantConnect mới dùng
    # thật. Bày kèm câu nhắc còn hơn giấu: giấu thì người dùng không biết là app
    # nói được câu «chỉ giữ N mã», và đó mới là câu họ đi tìm.
    ("qc500", "QC500 — 500 cổ phiếu Mỹ thanh khoản nhất "
               "(cần dữ liệu doanh nghiệp: chỉ có 24/03–07/04/2014)",
     "QC500UniverseSelectionModel", (),
     "set_universe_selection(QC500UniverseSelectionModel())"),
    # ⚠ ĐÂY LÀ TRẦN CỨNG «CHỈ GIỮ N MÃ» mà soát 11 ví dụ đi tìm suốt — và tôi đã tìm
    # sai tầng. Câu "chấm điểm cả rổ rồi giữ 12 mã tốt nhất" KHÔNG nói được ở trạm
    # chia vốn: model chia cho MỌI mã có tín hiệu, không cắt ở mã thứ 12. Nó nói ở
    # đây, tầng RỔ. `EmaCrossUniverseSelectionModel(nhanh, cham, count)` giữ mã nào
    # EMA nhanh còn trên EMA chậm, rồi lấy `count` mã NẶNG nhất — xếp hạng là việc
    # của LEAN, app không đếm hộ gì.
    ("ema_cheo", "EMA nhanh TRÊN EMA chậm — giữ N mã nặng nhất "
                 "(cần dữ liệu doanh nghiệp: chỉ có 24/03–07/04/2014)",
     "EmaCrossUniverseSelectionModel",
     (_o_ro("ema_nhanh", "EMA nhanh", O_SO, 100, don_vi="nến", nguyen=True,
            goi_y="Chu kỳ EMA nhanh. LEAN mặc định 100."),
      _o_ro("ema_cham", "EMA chậm", O_SO, 300, don_vi="nến", nguyen=True,
            goi_y="Chu kỳ EMA chậm. LEAN mặc định 300."),
      _o_ro("giu_n", "Giữ mấy mã", O_SO, 20, don_vi="mã", nguyen=True,
            goi_y="Trong số mã đạt điều kiện, giữ ngần này mã NẶNG nhất. LEAN "
                  "mặc định 500 — để cao thì nặng máy.")),
     "set_universe_selection(EmaCrossUniverseSelectionModel({ema_nhanh}, "
     "{ema_cham}, {giu_n}))"),
    ("etf_thanh_khoan", "Rổ ETF thanh khoản — cả sáu nhóm", "LiquidETFUniverse", (),
     "set_universe_selection(LiquidETFUniverse())"),
    ("kim_loai", "ETF kim loại — vàng, bạc, bạch kim", "MetalsETFUniverse", (),
     "set_universe_selection(MetalsETFUniverse())"),
    ("nang_luong", "ETF năng lượng — dầu, khí, mặt trời", "EnergyETFUniverse", (),
     "set_universe_selection(EnergyETFUniverse())"),
    ("cong_nghe", "ETF công nghệ", "TechnologyETFUniverse", (),
     "set_universe_selection(TechnologyETFUniverse())"),
    ("trai_phieu", "ETF trái phiếu Mỹ", "USTreasuriesETFUniverse", (),
     "set_universe_selection(USTreasuriesETFUniverse())"),
    ("bien_dong", "ETF biến động — VIX", "VolatilityETFUniverse", (),
     "set_universe_selection(VolatilityETFUniverse())"),
    ("nganh_sp500", "ETF các ngành của S&P 500", "SP500SectorsETFUniverse", (),
     "set_universe_selection(SP500SectorsETFUniverse())"),
)

RO_THEO_MA = {r[0]: r for r in RO}


def ro_cua(gia_tri):
    """Giá trị ô `ma` -> mục RỔ nếu nó là một rổ động, ngược lại None.

    MỘT CHỖ DUY NHẤT quyết định "ô này đang nói kiểu nào". Hai chỗ cùng đoán hình
    dạng là hai chỗ để trôi khỏi nhau — mà lệch ở đây thì bộ sinh mã viết `add_*`
    trong khi giao diện bày ô chọn rổ, và không ai thấy cho tới lúc chạy."""
    if not isinstance(gia_tri, dict):
        return None
    return RO_THEO_MA.get(str(gia_tri.get("ro") or "").strip())


def o_ro_cua(gia_tri):
    """Mấy ô CON của rổ đang chọn. -> [ô]. Không phải rổ thì rỗng."""
    r = ro_cua(gia_tri)
    return list(r[3]) if r else []


def gt_ro(gia_tri, ten):
    """Giá trị một ô con của rổ, rơi về mặc định nếu dict CHƯA CÓ KHOÁ ấy.

    ⚠ CHỈ rơi về mặc định khi khoá VẮNG, không khi nó RỖNG — đúng luật của
    `core.o_bat_dau`. Bản đầu của hàm này coi `""` như vắng, nên xoá trắng ô «Mã ETF»
    là nó lặng lẽ thành "SPY": hộp thoại trống trơn mà cỗ máy chạy rổ SPY, và phép
    soát không có gì để bắt. Rỗng là rỗng, và `_soat_ro` báo lỗi vì nó rỗng."""
    for o in o_ro_cua(gia_tri):
        if o["ten"] == ten:
            v = (gia_tri or {}).get(ten)
            return o["mac_dinh"] if v is None else v
    return None


def lean_ro(gia_tri):
    """Câu LEAN một rổ sinh ra — để hộp thoại nói thẳng ra. "" nếu không phải rổ.

    ⚠ PHẢI LÀ MỘT KHÚC CỦA MÃ THẬT, không phải một câu tả lại nó. Bản đầu bịa ra
    tham số thứ ba tên «lọc theo trọng số» và bỏ chữ `self.` giữa dòng — đọc thì
    hiểu, nhưng tìm trong mã sinh ra thì không có, mà dòng khai này tồn tại ĐÚNG ĐỂ
    người dùng đối chiếu với mã. Nói sai còn tệ hơn không nói. Nay nó khớp từng chữ
    với `sinh_ma._khai_ro`, trừ chữ `self.` MỞ ĐẦU mà mọi ô `lean` đều bỏ — và
    `test_sinh_ma` canh đúng chuyện ấy: câu này phải nằm nguyên trong mã sinh ra.

    Mã ETF để trống cũng bày ra đúng `''` chứ không bày một dấu «…» cho đẹp: đó là
    thứ bộ sinh mã thật sự viết, và `soat_khoi_bat_dau` đã báo lỗi vì nó rỗng."""
    r = ro_cua(gia_tri)
    if not r:
        return ""
    cau = r[4]
    for o in r[3]:
        v = gt_ro(gia_tri, o["ten"])
        if o["kieu"] == O_CHU:
            lit = repr(str(v or "").strip().upper())
        elif o.get("nguyen"):
            lit = repr(_nguyen(v))
        else:
            lit = repr(float(v) if str(v).strip() not in ("", "None") else 0.0)
        cau = cau.replace("{%s}" % o["ten"], lit)
    # ⚠ `{loc_ro}` LÀ CHỖ DUY NHẤT CÓ ĐIỀU KIỆN, và luật ở đúng một dòng dưới đây:
    # «lấy mấy mã» > 0 thì rổ ETF phải nhận thêm HÀM LỌC (`LOC_TRONG_SO`), vì lọc
    # theo trọng số không phải một con số truyền vào mà là một hàm LEAN gọi lại.
    # Để 0 là lấy cả rổ, không cần hàm nào.
    if "{loc_ro}" in cau:
        lay = _nguyen(gt_ro(gia_tri, "lay"))
        cau = cau.replace("{loc_ro}", ", self._loc_ro" if lay > 0 else "")
    return cau


def _nguyen(v):
    """-> int, 0 nếu không phải số. Ô số có thể đang mang chuỗi người dùng đang gõ."""
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0



# ---------------------------------------------------------------------------
# SÁU Ô
# ---------------------------------------------------------------------------
O_BAT_DAU = [
    # ⚠ HAI KIỂU CHO MỘT Ô — xem mục «RỔ ĐỘNG» ở trên. `ds_ma` vẫn là tên kiểu, vì
    # giao diện bày ra MỘT widget cho cả hai; widget ấy tự biết đang ở kiểu nào.
    _o("ma", "Chạy trên mã nào", O_DS_MA,
       [{"ma": "XAUUSD", "loai": "cfd"}],
       "add_cfd / add_equity / add_forex / add_crypto / add_index / add_future · "
       "hoặc set_universe_selection(…) nếu chọn một rổ",
       goi_y="Gõ sẵn mấy mã, hoặc chọn một RỔ — rổ thì LEAN tự quyết hôm nay gồm "
             "những mã nào. Nhiều mã thì cả sơ đồ chạy lại một lượt cho TỪNG mã.", nhom="chay_gi"),

    _o("khoang", "Từ ngày → đến ngày", O_KHOANG_NGAY,
       {"tu": "2010-01-01", "den": "2019-01-01"},
       "set_start_date(tu) · set_end_date(den)",
       goi_y="Dữ liệu vàng miễn phí có từ 20/03/2006 đến 25/02/2019.", nhom="tien"),

    _o("von", "Vốn", O_SO, 100000, "set_cash(von)", don_vi="$",
       goi_y="Tiền khởi đầu của cỗ máy.", nhom="tien"),

    # Đệm tiền mặt: phần vốn LEAN KHÔNG cho đặt lệnh, để lệnh khỏi bị từ chối vì
    # thiếu ký quỹ. Mặc định của LEAN là 0,0025 (0,25%). Đổi nó là đổi sức mua, tức
    # đổi cả kết quả — nên nó phải khai được chứ không để ngầm.
    _o("dem_tien_mat", "Đệm tiền mặt", O_SO, 0.0025,
       "self.settings.free_portfolio_value_percentage = dem_tien_mat",
       don_vi="phần",
       goi_y="0.05 = chừa 5% không đặt lệnh. Mặc định LEAN là 0.0025.", nhom="tien"),

    _o("nhip", "Nhịp", O_CHON, "ngay",
       "Resolution.* · on_data hoặc schedule.on",
       chon=[(m, nhan) for m, nhan, *_ in NHIP],
       goi_y="Bao lâu cỗ máy xem một lần.", nhom="nhip"),

    # ⚠ HAI KIỂU CHIẾN THUẬT KHÁC HẲN NHAU, và trước nay ta chỉ có kiểu đầu.
    #
    #   · SÀNG TỪNG MÃ — "mã nào RSI < 30 thì mua". Cả sơ đồ chạy LẠI một lượt cho
    #     từng mã, nên khối không cần gõ tên mã: `sym` là mã đang xét.
    #   · CHIA DANH MỤC — "xếp hạng 3 ngành rồi chia 40/35/20". Chạy ĐÚNG MỘT lượt,
    #     rồi đặt tỷ trọng cho từng mã có tên. Không có "mã đang xét" nào cả.
    #
    # Lòi ra khi dựng lại một chiến thuật thật (vd2 trong `tai_lieu/chiến thuật ví
    # dụ/`): nó cân lại cả rổ mỗi tuần, mà bộ khối cũ không nói nổi câu ấy.
    _o("chay_cho", "Chạy cho ai", O_CHON, "moi_ma", "for sym in self._ma: …",
       chon=[("moi_ma", "Mỗi mã một lượt — sàng từng mã"),
             ("ca_danh_muc", "Một lượt cho CẢ RỔ — chia danh mục")],
       goi_y="Chia danh mục thì mọi khối phải gõ rõ tên mã.", nhom="chay_gi"),

    # ⚠ ĐỂ TRỐNG KHÔNG PHẢI LÀ "KHÔNG CÓ MỐC". `DefaultBrokerageModel.GetBenchmark`
    # trả về **SPY** — tức cỗ máy vàng của bạn bị đem so với cổ phiếu Mỹ, và không
    # một dòng nào nói ra. Nên câu gợi ý phải nói thẳng.
    _o("moc_so_sanh", "Mốc so sánh", O_CHU, "", "set_benchmark(ma)",
       goi_y="Để trống thì LEAN tự lấy SPY (cổ phiếu Mỹ). Gõ chính mã mình chạy để "
             "so với «mua rồi ôm».",
       bat_buoc=False, nhom="do_luong"),

    _o("san", "Sàn", O_CHON, "DEFAULT", "set_brokerage_model(BrokerageName.san)",
       chon=list(SAN), goi_y="Quyết phí và trượt giá tính theo kiểu nào.", nhom="chi_phi"),

    _o("phi", "Phí (ghi đè Sàn)", O_CHON, "",
       "security.set_fee_model(…)", chon=[(m, n) for m, n, *_ in PHI],
       goi_y="Để trống thì phí theo Sàn đã chọn. Đặt phí cố định 0 là cách xem "
             "chiến thuật tự nó lãi bao nhiêu trước khi trừ phí.", bat_buoc=False, nhom="chi_phi"),
    _o("truot_gia", "Trượt giá (ghi đè Sàn)", O_CHON, "",
       "security.set_slippage_model(…)",
       chon=[(m, n) for m, n, *_ in TRUOT_GIA],
       goi_y="Để trống thì trượt giá theo Sàn đã chọn.", bat_buoc=False, nhom="chi_phi"),

    _o("chuan_hoa_gia", "Chuẩn hoá giá", O_CHON, "",
       "add_equity(…, data_normalization_mode=…) · universe_settings."
       "data_normalization_mode",
       chon=list(CHUAN_HOA_GIA),
       goi_y="Cổ tức và chia tách tính vào giá thế nào. Để trống thì LEAN dùng "
             "ADJUSTED. Chỉ có tác dụng với CỔ PHIẾU, HĐ tương lai và rổ động — "
             "ngoại hối / tiền mã hoá / CFD / chỉ số không nhận tham số này.",
       bat_buoc=False, nhom="chay_gi"),

    # --- BA CHÍNH SÁCH CỦA DÂY CHUYỀN LEAN ---
    #
    # ⚠ Chúng ở ĐÂY chứ không thành khối, vì cả ba gọi MỘT LẦN trong `initialize`
    # (xem `BaseFrameworkRegressionAlgorithm.py` của LEAN: năm cái `set_*` đều nằm
    # trong `initialize`). Thả một khối "Chia vốn đều" vào cuối một nhánh thì nó
    # nghĩa là gì — "chỉ đặt cách chia vốn khi RSI < 30"? Không có nghĩa nào.
    # Đường ranh là: xảy ra MỖI NHỊP -> khối Hành động; đặt MỘT LẦN -> ô ở đây.
    #
    # Cả ba chỉ có tác dụng khi sơ đồ có khối «Phát tín hiệu» — `soat_dây_chuyền`
    # trong `core.py` canh chuyện đó.
    # ⚠ TRẠM THỨ TƯ, THÊM 18/10/2026 — xem `PHAT_TIN_HIEU`. Trước đây dây chuyền chỉ
    # có ba trạm ở đây (chia vốn · phòng rủi ro · đặt lệnh) vì tín hiệu luôn do khối
    # «Phát tín hiệu» trên sơ đồ phát ra. LEAN còn một nguồn nữa: model Alpha tự xem
    # cả rổ rồi tự phát. Thiếu ô này thì cả họ chiến thuật ấy không vẽ được (vd4), mà
    # lỗ hổng KHÔNG lòi ra ở đâu — sơ đồ vẫn vẽ được, backtest vẫn ra số.
    _o("phat_tin_hieu", "Phát tín hiệu tự động", O_CHON, "",
       "add_alpha(…)", chon=[(m, n) for m, n, *_ in PHAT_TIN_HIEU],
       goi_y="Model TỰ phát tín hiệu cho mọi mã trong rổ, không cần khối vẽ nào. "
             "Dùng được CÙNG LÚC với khối «Phát tín hiệu» — LEAN gộp cả hai nguồn.",
       bat_buoc=False, nhom="day_chuyen"),
    _o("chia_von", "Chia vốn theo tín hiệu", O_CHON, "",
       "set_portfolio_construction(…)", chon=list(CHIA_VON),
       goi_y="Biến tín hiệu thành tỷ trọng. Không chọn thì tín hiệu phát ra "
             "KHÔNG ai nhận.", bat_buoc=False, nhom="day_chuyen"),
    _o("phong_rui_ro", "Phòng rủi ro", O_CHON, "",
       "set_risk_management(…)", chon=[(m, n) for m, n, *_ in PHONG_RUI_RO],
       goi_y="Chạy SAU khi chia vốn, chỉnh lại tỷ trọng — cắt lỗ, chốt lời, "
             "trailing stop. LEAN giữ mức, app không nhớ gì.", bat_buoc=False, nhom="day_chuyen"),
    _o("dat_lenh", "Đặt lệnh", O_CHON, "",
       "set_execution(…)", chon=list(DAT_LENH),
       goi_y="Cách đẩy tỷ trọng thành lệnh thật.", bat_buoc=False, nhom="day_chuyen"),
]

O_THEO_TEN = {o["ten"]: o for o in O_BAT_DAU}


def rui_ro_cua(ma):
    """Một mục của `PHONG_RUI_RO` theo mã lớp. None nếu để trống hay mã lạ."""
    m = str(ma or "").strip()
    return next((x for x in PHONG_RUI_RO if x[0] and x[0] == m), None)


def alpha_cua(ma):
    """Một mục của `PHAT_TIN_HIEU` theo mã lớp. None nếu để trống hay mã lạ."""
    m = str(ma or "").strip()
    return next((x for x in PHAT_TIN_HIEU if x[0] and x[0] == m), None)


def o_cua(gia_tri=None):
    """Mọi ô của khối Bắt đầu, KỂ CẢ ô chỉ hiện theo nhịp hay theo model đã chọn.

    Cùng lối với `lam.o_cua`: chọn "Mỗi ngày đúng giờ" thì ô Giờ/Phút mới hiện ra,
    chọn một model phòng rủi ro thì ô Ngưỡng mới hiện ra."""
    ra = list(O_BAT_DAU)
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if n:
        ra.extend(n[4])
        # Ô «Lúc nào trong ngày» nay nằm NGAY TRONG `o_them` của từng nhịp hẹn giờ,
        # nên dòng trên đã lấy nó rồi. Chỉ còn ô con của chính quy tắc giờ (số phút,
        # hay giờ+phút) — một tầng nữa.
        #
        # ⚠ TRƯỚC ĐÂY Ô ẤY CHÈN RIÊNG Ở ĐÂY, và `o_cua` thì chỉ Python gọi. Giao diện
        # dựng danh sách ô từ `O_BAT_DAU` cộng mấy bảng `o_them`, nên một ô chỉ sống
        # trong `o_cua` là một ô KHÔNG BAO GIỜ HIỆN RA: người dùng chọn nhịp QUÝ rồi
        # không thấy đâu chỗ chọn giờ, và lịch chạy ở mặc định. Nhìn ảnh mới thấy —
        # đo bằng JS thì ô ấy vẫn có trong `o_cua`, vẫn lưu được, vẫn sinh mã đúng.
        g = gio_da_chon(gia_tri)
        if g:
            ra.extend(g[4])
    r = rui_ro_cua((gia_tri or {}).get("phong_rui_ro"))
    if r:
        ra.extend(r[2])
    a = alpha_cua((gia_tri or {}).get("phat_tin_hieu"))
    if a:
        ra.extend(a[2])
    for tim, khoa in ((phi_cua, "phi"), (truot_cua, "truot_gia")):
        m = tim((gia_tri or {}).get(khoa))
        if m:
            ra.extend(m[2])
    return ra


def cau_phi_truot(gia_tri=None):
    """Hai câu `set_fee_model` / `set_slippage_model` của bộ khởi tạo mã. -> [câu].

    ⚠ DÙNG `add_security_initializer`, KHÔNG `set_`. `set_` GHI ĐÈ bộ khởi tạo mặc
    định, mà mặc định ấy là `BrokerageModelSecurityInitializer(BrokerageModel, …)` —
    nó đặt đòn bẩy và model phí theo SÀN. Ghi đè là mất cả hai, âm thầm: lượt chạy
    vẫn ra số, chỉ là đòn bẩy về mặc định của LEAN chứ không còn của sàn đã chọn.
    `add_` thì LEAN tự gói thành `CompositeSecurityInitializer` (đọc
    `QCAlgorithm.cs` quanh dòng 1062) — giữ nguyên mặc định rồi chồng cái của ta lên.

    vd3 trong tập ví dụ dùng `SetSecurityInitializer` và vì thế mất mặc định của sàn;
    ta không copy chỗ ấy."""
    ra = []
    for tim, khoa, ham in ((phi_cua, "phi", "set_fee_model"),
                           (truot_cua, "truot_gia", "set_slippage_model")):
        m = tim((gia_tri or {}).get(khoa))
        if not m:
            continue
        cau = m[3]
        for o in m[2]:
            v = gt_o(gia_tri, o["ten"])
            cau = cau.replace(o["ten"],
                              repr(_nguyen(v) if o.get("nguyen") else _phan(v)))
        ra.append(f"s.{ham}({cau})")
    return ra


def do_phan_giai(gia_tri=None):
    """Độ phân giải dữ liệu THẬT của một khối Bắt đầu -> "DAILY" / "MINUTE"…

    Nhịp theo nến: nhịp chính là độ phân giải. Nhịp hẹn giờ: lấy ô người dùng chọn,
    thiếu thì rơi về mặc định của nhịp ấy."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return "DAILY"
    if n[3] == "on_data":
        return n[2]
    v = str((gia_tri or {}).get("do_phan_giai") or "").strip().upper()
    hop_le = {m for m, _nhan in _O_DO_PHAN_GIAI["chon"]}
    return v if v in hop_le else str(_O_DO_PHAN_GIAI["mac_dinh"])


def ham_chay(gia_tri=None):
    """Câu `on_data`/`schedule.on` THẬT SỰ sẽ sinh ra, theo cả nhịp VÀ kiểu ô `ma`.

    Chọn rổ thì lịch chạy bằng mấy hàm KHÔNG MÃ — xem chú thích ở `NHIP`.

    ⚠ NHỊP LẠ (file sửa tay) RƠI VỀ `on_data`, không trả chuỗi rỗng. `soat_khoi_bat_
    dau` đã báo lỗi nhịp lạ rồi, nhưng bộ sinh mã vẫn chạy tiếp để bày ra phần sinh
    được — mà chuỗi rỗng thì nó cắt một ký tự của chuỗi rỗng rồi ghép thành một câu
    `schedule.on` cụt đầu. Rơi về `on_data` là đúng cách `sinh_ma` vẫn rơi (nó lấy
    `NHIP[4]`, tức nhịp «mỗi nến ngày»)."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return "on_data"
    co_ro = bool(ro_cua((gia_tri or {}).get("ma")))
    cau = n[5] if co_ro else n[3]
    if "{gio}" not in cau:
        return cau
    g = gio_da_chon(gia_tri)
    return cau.replace("{gio}", (g[3] if co_ro else g[2]) if g else "")


def ham_lean(gia_tri=None):
    """Câu LEAN quyết định nhịp — để hộp thoại nói thẳng ra cho người dùng thấy."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return ""
    r = do_phan_giai(gia_tri)
    chay = ham_chay(gia_tri)
    # Rổ động không có dòng `add_*` nào — độ phân giải đi qua `universe_settings`.
    dau = (f"universe_settings.resolution = Resolution.{r}"
           if ro_cua((gia_tri or {}).get("ma")) else f"add_*(ma, Resolution.{r})")
    return dau if chay == "on_data" else f"{dau} · {chay}"


def lean_day_chuyen(gia_tri=None):
    """BA TRẠM của dây chuyền LEAN -> [câu], để hộp thoại nói thẳng ra.

    MỘT BẢN SỰ THẬT cho cả `sinh_ma` và hộp thoại. Trước đây `sinh_ma._khai_mo` tự
    ghép `self.{ham}({lop}())` ngay tại chỗ — luôn KHÔNG THAM SỐ — và đó là chỗ hai
    lỗi lặng mọc lên:

      1. `StandardDeviationExecutionModel()` có tham số thứ ba `resolution` mặc định
         `Resolution.MINUTE`, mà `SymbolData` lấy consolidator theo đúng tham số ấy.
         Sơ đồ nhịp ngày (mặc định của app) thì `QCAlgorithm.CreateConsolidator` ném
         ngay nến đầu: *"Unable to create SPY consolidator because SPY is registered
         for Daily data"*. Kết quả vẫn ghi ra, bảng Kết quả nói «0 lệnh, lãi 0%», câu
         lỗi chỉ nằm trong nhật ký. ĐÃ ÉP TÁI HIỆN: 0 lệnh; truyền đúng độ phân giải
         thì 6 lệnh.
      2. Cả bốn model phòng rủi ro có tham số ngưỡng mà không ai truyền, nên chúng
         chạy ở 5% mặc định trong khi nhãn hứa «theo %» và hộp không có ô % nào.

    Mỗi câu ở đây PHẢI là một khúc của mã `sinh_ma` sinh ra, trừ chữ `self.` MỞ ĐẦU
    — cùng quy ước `lean_ro`, và `test_sinh_ma` canh đúng chuyện ấy."""
    ra = []
    # TRẠM ALPHA đứng TRƯỚC chia vốn, đúng thứ tự dữ liệu chảy qua dây chuyền LEAN:
    # Rổ -> Alpha -> Chia vốn -> Phòng rủi ro -> Đặt lệnh.
    a = alpha_cua((gia_tri or {}).get("phat_tin_hieu"))
    if a:
        cau = a[3]
        for o in a[2]:
            v = gt_o(gia_tri, o["ten"])
            cau = cau.replace("{%s}" % o["ten"],
                              repr(_nguyen(v) if o.get("nguyen")
                                   else _phan(v)))
        ra.append(cau.replace("{res}", f"Resolution.{do_phan_giai(gia_tri)}"))

    chia = str((gia_tri or {}).get("chia_von") or "").strip()
    if chia:
        ra.append(f"set_portfolio_construction({chia}())")

    r = rui_ro_cua((gia_tri or {}).get("phong_rui_ro"))
    if r:
        # Ngưỡng đi THẲNG vào câu LEAN. `repr` của một float Python là literal Python
        # — không có phép tính nào ở giữa, nên không có chỗ nào để hai bên lệch nhau.
        ra.append(f"set_risk_management({r[0]}({_phan(gt_o(gia_tri, 'nguong'))!r}))")

    lenh = str((gia_tri or {}).get("dat_lenh") or "").strip()
    if lenh == "StandardDeviationExecutionModel":
        # ĐỘ PHÂN GIẢI KHÔNG PHẢI MỘT Ô — nó đã được ô «Nhịp chạy» trả lời rồi. Hỏi
        # lần thứ hai là mời người dùng nói hai câu khác nhau cho một thứ.
        # Hai số kia là mặc định CỦA LEAN, viết thẳng ra để mã sinh ra không mang một
        # con số ngầm nào; nhãn trong `DAT_LENH` nói đúng hai số này.
        ra.append(f"set_execution({lenh}(60, 2, Resolution.{do_phan_giai(gia_tri)}))")
    elif lenh:
        ra.append(f"set_execution({lenh}())")
    return ra


def gt_o(gia_tri, ten):
    """Giá trị một ô của khối Bắt đầu, rơi về mặc định nếu khối CHƯA CÓ KHOÁ ấy.

    Ô THÊM (của nhịp, của model phòng rủi ro) không nằm trong `O_THEO_TEN`, nên phải
    tìm qua `o_cua` — chính danh sách ô ĐANG hiện.

    ⚠ CHỈ rơi về mặc định khi khoá VẮNG, không khi nó RỖNG — đúng luật `gt_ro` và
    `core.o_bat_dau`. Coi `""` như vắng là xoá trắng ô «Ngưỡng» rồi cỗ máy lặng lẽ
    cắt lỗ ở 5%: hộp thoại trống trơn mà mã sinh ra mang một con số, và phép soát
    không có gì để bắt. Rỗng là rỗng, và `soat_khoi_bat_dau` báo lỗi vì nó rỗng."""
    for o in o_cua(gia_tri):
        if o["ten"] == ten:
            v = (gia_tri or {}).get(ten)
            return o["mac_dinh"] if v is None else v
    return None


def _phan(v):
    """-> float, 0.0 nếu không phải số. Ô số có thể đang mang chuỗi người dùng gõ."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def khai(gia_tri=None):
    """MỌI câu LEAN khối Bắt đầu khai ra, theo đúng giá trị đang có. -> [câu].

    MỘT CỬA DUY NHẤT cho hộp thoại: nó bày lại nguyên văn danh sách này — không
    chọn, không ghép, không cần biết có mấy câu. Thêm một câu khai ở đây là hộp
    thoại có ngay, không phải sửa bên TypeScript.

    ⚠ HAI LỖ ĐÃ VÁ Ở ĐÂY, cùng một họ. `HopBatDau.tsx` TỰ DỰNG LẠI câu nhịp bằng
    TypeScript (nó tự quyết `add_*` hay `universe_settings`, rồi tự ghép với tên
    hàm lịch) trong khi `ham_lean` bên Python làm đúng việc ấy — hai bản ghép chữ
    nằm hai bên cầu nối, không ai đứng so. Còn `lean_ro` thì KHÔNG AI GỌI, nên
    chọn rổ động xong, dòng khai trong hộp chỉ nói về nhịp mà im đúng câu quan
    trọng nhất cái rổ sinh ra. Cả hai đều không gây lỗi nào, nên không ai thấy."""
    ra = [ham_lean(gia_tri)]
    ra.append(lean_ro((gia_tri or {}).get("ma")))
    ra.extend(lean_day_chuyen(gia_tri))
    return [c for c in ra if c]


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối."""
    return {
        "o": O_BAT_DAU,
        # NHÓM — giao diện xếp ô theo đây. Thứ tự trong bảng là thứ tự bày.
        "nhom": [{"ma": m, "nhan": n, "mo_ta": d} for m, n, d in NHOM_O],
        "nhom_khac": NHOM_KHAC,
        "loai_tai_san": [{"ma": m, "nhan": n, "lean": h} for m, n, h in LOAI_TAI_SAN],
        "co_san": {k: list(v) for k, v in CO_SAN_MIEN_PHI.items()},
        "nhip": [{"ma": m, "nhan": n, "res": r, "chay": c,
                  "o_them": list(th), "chay_ro": c_ro}
                 for m, n, r, c, th, c_ro in NHIP],
        # RỔ — kiểu thứ hai của ô «Chạy trên mã nào». Giao diện CHỈ BÀY: nhãn, lớp
        # LEAN và mấy ô con đều khai ở đây, không khai lại bên TypeScript.
        "ro": [{"ma": m, "nhan": n, "lop": lop, "o_them": list(th)}
               for m, n, lop, th, _l in RO],
        # PHÒNG RỦI RO — mỗi model mang ô NGƯỠNG của riêng nó, cùng lối `nhip`/`ro`.
        # Nhãn ô khác nhau ở từng model (lỗ / lãi / tụt khỏi đỉnh), nên giao diện
        # KHÔNG dựng lại ô ấy — nó bày thẳng `o` Python gửi sang.
        "phong_rui_ro": [{"ma": m, "nhan": n, "o_them": list(th)}
                         for m, n, th in PHONG_RUI_RO],
        # ⚠ BỐN BẢNG DƯỚI ĐÂY PHẢI GỬI, không thì giao diện không biết ô con của
        # chúng tồn tại. Mỗi bảng mang ô con của riêng mình đúng hình `{ma, nhan,
        # o_them}` như ba bảng trên, nên hộp thoại chỉ cần biết «ô TÊN NÀY tra BẢNG
        # NÀO» — không cần biết trong đó có mấy ô, cũng không cần biết ô gõ hay ô
        # chọn. Thiếu một bảng ở đây thì ô ấy chọn xong không có núm nào hiện ra, và
        # model chạy ở mặc định của LEAN — đúng bệnh đã gặp ba lần hôm nay.
        "quy_tac_gio": [{"ma": m, "nhan": n, "o_them": list(th)}
                        for m, n, _c, _ck, th in QUY_TAC_GIO],
        "phat_tin_hieu": [{"ma": m, "nhan": n, "o_them": list(th)}
                          for m, n, th, _l in PHAT_TIN_HIEU],
        "phi": [{"ma": m, "nhan": n, "o_them": list(th)}
                for m, n, th, _l in PHI],
        "truot_gia": [{"ma": m, "nhan": n, "o_them": list(th)}
                      for m, n, th, _l in TRUOT_GIA],
    }
