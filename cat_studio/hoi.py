"""TỪ ĐIỂN KHỐI XÁC NHẬN — những câu hỏi về thế giới mà sơ đồ hỏi được.

LUẬT MỘT CÂU: **mỗi đại lượng ở đây phải chỉ ra được MỘT thứ có thật của LEAN.**
Ô `lean` của mỗi mục chính là lời khai ấy. Không khai được thì không được có mặt —
đó là cách chặn việc app tự đẻ ra một bộ máy tính toán thứ hai (D-11).

Mọi chữ ký LEAN trong file này đã được đọc THẲNG từ mã nguồn `QuantConnect/Lean`
(`Algorithm/QCAlgorithm.Indicators.cs`, `Common/Securities/*`, `Common/Data/*`), không
chép từ trí nhớ.

HÌNH CỦA MỘT DÒNG ĐIỀU KIỆN

    [ vế trái ]   [ phép so ]   [ vế phải ]

Hai vế rút từ CÙNG một kho đại lượng, nên "so sánh chéo mã" không phải tính năng
riêng — nó chỉ là đổi ô `ma` ở một vế.

VÌ SAO CHIA NĂM LOẠI chứ không một khối "so sánh bất cứ gì": chọn mã thì vô nghĩa với
tài khoản, chọn chu kỳ thì vô nghĩa với vị thế. Chia ra thì mỗi hộp thoại chỉ bày đúng
thứ nó cần, và nhìn khối trên sơ đồ là biết nhánh ấy hỏi về *ngoài kia*, *mã này*,
*túi tiền*, *đồng hồ*, hay *công ty*.
"""

# ---------------------------------------------------------------------------
# Phép so
# ---------------------------------------------------------------------------
# CHỈ CÓ SÁU. Mọi phép "nhìn lại" (cắt lên, cao nhất N nến, tăng N nến…) đều KHÔNG
# phải phép so — chúng là CHỈ BÁO của LEAN:
#     cắt lên        -> `giá > EMA` VÀ `Delay(giá,1) <= Delay(EMA,1)`  (hai dòng)
#     cao nhất N nến -> chỉ báo MAX(n)
#     tăng N nến     -> chỉ báo ROC(n) > 0
# Tự viết phép "cắt" là tự đẻ backend, và rồi phải tự gỡ lỗi nó.
PHEP_SO = (
    (">", "lớn hơn"),
    ("<", "nhỏ hơn"),
    (">=", "lớn hơn hoặc bằng"),
    ("<=", "nhỏ hơn hoặc bằng"),
    ("==", "bằng"),
    ("!=", "khác"),
)

#: Đại lượng kiểu đúng/sai dùng hai phép này thay cho sáu phép trên.
PHEP_CO_KHONG = (("la", "là ĐÚNG"), ("khong", "là SAI"))

#: GHÉP hai đại lượng thành một vế: «giá / đỉnh 60 nến ≤ 0,97» — tức rơi 3% từ đỉnh.
#: Bốn phép này là bốn phép LEAN khai trong `IndicatorExtensions`: `Plus` · `Minus` ·
#: `Times` · `Over`. Không bịa thêm phép nào ngoài bộ ấy.
#:
#: ⚠ CHIA CHO 0: LEAN tự quy định sẵn, đọc `GetOverIndicatorComposer()` —
#:     (l, r) => r.Current.Value == 0m ? new IndicatorResult(0m, MathError) : l / r
#: tức ra SỐ 0 chứ không nổ. Bộ sinh mã copy đúng thế (`a / b if b else 0`), không tự
#: nghĩ ra cách xử lý khác.
PHEP_GHEP = (("+", "cộng"), ("-", "trừ"), ("*", "nhân"), ("/", "chia cho"))

KIEU_SO = "so"
KIEU_CO_KHONG = "co_khong"


def _can_ma(lean, lean_dk):
    """Đại lượng này có cần CHỌN MÃ không — SUY THẲNG từ đoạn code của nó.

    ⚠ KHÔNG phải một cờ viết tay cho cả họ. Bản trước để `can_ma` ở mức HỌ khối, và
    một cờ cho cả họ thì luôn chỉ là xấp xỉ: «Hỏi lịch» khai `can_ma=False` trong khi
    «Phiên đang mở» là `self.is_market_open(sym)` — nó CẦN mã, mà hộp thoại không cho
    chọn. Suy từ `lean` thì đúng từng cái, và tự đúng khi thêm đại lượng mới.

    Phải xét cả `lean_dk`: `Delay(n)` không có `sym` trong biểu thức, nhưng dòng đăng
    ký của nó thì có — nó vẫn gắn vào một mã."""
    return "sym" in lean or "sym" in lean_dk


def _s(ma, nhan, lean, don_vi="", tham_so=(), lean_dk=""):
    """Một đại lượng trả về SỐ.

    `lean` là BIỂU THỨC PYTHON CHẠY ĐƯỢC, không phải lời khai cho người đọc: bộ sinh
    mã viết ra đúng chuỗi này (thay `sym` và tên tham số). Nhờ vậy không còn chỗ nào
    cho một bộ chuyển đổi sai âm thầm — lời khai và đoạn code là MỘT.

    `don_vi` KHÔNG phải chú thích cho vui: giao diện xếp vế phải theo nó ("cùng đơn vị
    «giá»" lên trước). Bỏ trống là đại lượng ấy không so được với ai — nên bắt buộc,
    và `test_hoi` canh.

    `lean_dk` = dòng ĐĂNG KÝ phải viết thêm, cho chỉ báo nào dựng xong còn phải nối
    vào dữ liệu (xem `delay`). `{bien}` = tên biến chỉ báo, `{res}` = độ phân giải."""
    return {"ma": ma, "nhan": nhan, "lean": lean, "kieu": KIEU_SO,
            "don_vi": don_vi, "tham_so": list(tham_so), "lean_dk": lean_dk,
            "can_ma": _can_ma(lean, lean_dk)}


def _ck(ma, nhan, lean):
    """Một đại lượng trả về ĐÚNG/SAI."""
    return {"ma": ma, "nhan": nhan, "lean": lean, "kieu": KIEU_CO_KHONG,
            "don_vi": "", "tham_so": [], "lean_dk": "",
            "can_ma": _can_ma(lean, "")}


def _ts(ten, nhan, mac_dinh, nho_nhat=1, lon_nhat=5000):
    """Một ô tham số của đại lượng (chu kỳ, hệ số…)."""
    return {"ten": ten, "nhan": nhan, "mac_dinh": mac_dinh,
            "nho_nhat": nho_nhat, "lon_nhat": lon_nhat}


# ---------------------------------------------------------------------------
# ① HỎI THỊ TRƯỜNG — thế giới ngoài kia đang thế nào
# ---------------------------------------------------------------------------
# Đây là loại DUY NHẤT cần ô chọn mã ở CẢ HAI vế: đổi mã một bên là ra ngay so sánh
# chéo mã ("SPY tăng hơn QQQ không").

GIA = [
    _s("gia", "Giá hiện tại", "self.securities[sym].price", "giá"),
    _s("mo", "Giá mở", "data.bars[sym].open", "giá"),
    _s("cao", "Giá cao", "data.bars[sym].high", "giá"),
    _s("thap", "Giá thấp", "data.bars[sym].low", "giá"),
    _s("dong", "Giá đóng", "data.bars[sym].close", "giá"),
    _s("khoi_luong", "Khối lượng", "data.bars[sym].volume", "lượng"),
    _s("gia_mua", "Giá mua (bid)", "data.quote_bars[sym].bid.close", "giá"),
    _s("gia_ban", "Giá bán (ask)", "data.quote_bars[sym].ask.close", "giá"),
]

#: CHỈ BÁO. LEAN có 167 cái; đây là bộ ĐANG MỞ, chọn theo mức hay dùng. Thêm một cái
#: mới chỉ là thêm một dòng vào đây — miễn là ô `lean` ghi đúng chữ ký thật.
#:
#: `duong` = chỉ báo trả NHIỀU đường (MACD, Bollinger, Stochastic…). Giao diện bắt
#: chọn một đường; thiếu nó thì "giá > Bollinger" là một câu vô nghĩa.
CHI_BAO = [
    _s("sma", "SMA — trung bình trượt", "self.sma(sym, n)", "giá",
       [_ts("n", "Chu kỳ", 20)]),
    _s("ema", "EMA — trung bình trượt luỹ thừa", "self.ema(sym, n)", "giá",
       [_ts("n", "Chu kỳ", 20)]),
    _s("rsi", "RSI — sức mạnh tương đối", "self.rsi(sym, n)", "0–100",
       [_ts("n", "Chu kỳ", 14)]),
    _s("atr", "ATR — biên độ thật trung bình", "self.atr(sym, n)", "giá",
       [_ts("n", "Chu kỳ", 14)]),
    _s("adx", "ADX — độ mạnh xu hướng", "self.adx(sym, n)", "0–100",
       [_ts("n", "Chu kỳ", 14)]),
    _s("cci", "CCI", "self.cci(sym, n)", "±100", [_ts("n", "Chu kỳ", 20)]),
    _s("mfi", "MFI — dòng tiền", "self.mfi(sym, n)", "0–100", [_ts("n", "Chu kỳ", 14)]),
    _s("wilr", "Williams %R", "self.wilr(sym, n)", "-100–0", [_ts("n", "Chu kỳ", 14)]),
    _s("mom", "Momentum", "self.mom(sym, n)", "giá", [_ts("n", "Chu kỳ", 10)]),
    _s("roc", "ROC — tốc độ đổi giá", "self.roc(sym, n)", "tỉ lệ",
       [_ts("n", "Chu kỳ", 10)]),
    _s("std", "Độ lệch chuẩn", "self.std(sym, n)", "giá", [_ts("n", "Chu kỳ", 20)]),
    _s("obv", "OBV — khối lượng cân bằng", "self.obv(sym)", "lượng"),
    _s("vwap", "VWAP — giá bình quân theo khối lượng", "self.vwap(sym)", "giá"),
    _s("psar", "Parabolic SAR", "self.psar(sym)", "giá"),
    # --- NHỚ LẠI QUÁ KHỨ: ba cái này thay cho mọi phép "nhìn lại" ---
    _s("max", "Cao nhất N nến", "self.max(sym, n)", "giá", [_ts("n", "Số nến", 20)]),
    _s("min", "Thấp nhất N nến", "self.min(sym, n)", "giá", [_ts("n", "Số nến", 20)]),
    # ⚠ `Delay` KHÔNG phải hàm của QCAlgorithm — grep `QCAlgorithm.Indicators.cs` ra
    # 0 chữ ký. Nó là một LỚP chỉ báo: dựng tay rồi ĐĂNG KÝ vào mã, đúng như
    # `DisplacedMovingAverageRibbon.py` của QuantConnect làm. Nên nó cần `lean_dk`.
    _s("delay", "Giá trị N nến TRƯỚC", "Delay(n)", "giá",
       [_ts("n", "Lùi mấy nến", 1, 1, 500)],
       lean_dk="self.register_indicator(sym, {bien}, {res})"),
]

#: Chỉ báo NHIỀU ĐƯỜNG — khai riêng vì giao diện phải bắt chọn đường.
CHI_BAO_NHIEU_DUONG = [
    {**_s("macd", "MACD", "self.macd(sym, nhanh, cham, tin_hieu)", "giá",
          [_ts("nhanh", "Chu kỳ nhanh", 12), _ts("cham", "Chu kỳ chậm", 26),
           _ts("tin_hieu", "Chu kỳ tín hiệu", 9)]),
     "duong": [("fast", "Đường nhanh"), ("slow", "Đường chậm"),
               ("signal", "Đường tín hiệu"), ("histogram", "Histogram")]},
    {**_s("bb", "Bollinger Bands", "self.bb(sym, n, k)", "giá",
          [_ts("n", "Chu kỳ", 20), _ts("k", "Số lần độ lệch", 2, 1, 10)]),
     "duong": [("upper_band", "Dải trên"), ("middle_band", "Dải giữa"),
               ("lower_band", "Dải dưới")]},
    {**_s("sto", "Stochastic", "self.sto(sym, n)", "0–100", [_ts("n", "Chu kỳ", 14)]),
     "duong": [("stoch_k", "%K"), ("stoch_d", "%D")]},
    {**_s("kch", "Keltner Channel", "self.kch(sym, n, k)", "giá",
          [_ts("n", "Chu kỳ", 20), _ts("k", "Số lần ATR", 2, 1, 10)]),
     "duong": [("upper_band", "Dải trên"), ("middle_band", "Dải giữa"),
               ("lower_band", "Dải dưới")]},
    {**_s("dch", "Donchian Channel", "self.dch(sym, n)", "giá", [_ts("n", "Chu kỳ", 20)]),
     "duong": [("upper_band", "Dải trên"), ("middle_band", "Dải giữa"),
               ("lower_band", "Dải dưới")]},
]

#: Trạng thái của một mã — không so số, chỉ đúng/sai.
TRANG_THAI_MA = [
    _ck("giao_dich_duoc", "Mã này giao dịch được", "self.securities[sym].is_tradable"),
    _ck("huy_niem_yet", "Mã này đã huỷ niêm yết", "self.securities[sym].is_delisted"),
    _ck("co_du_lieu", "Mã này có dữ liệu", "self.securities[sym].has_data"),
    _ck("chia_co_tuc", "Hôm nay chia cổ tức", "sym in data.dividends"),
    _ck("chia_tach", "Hôm nay chia tách", "sym in data.splits"),
]

# ---------------------------------------------------------------------------
# ② HỎI VỊ THẾ — mã này tôi đang ra sao
# ---------------------------------------------------------------------------
VI_THE = [
    _ck("dang_giu", "Đang giữ mã này", "self.portfolio[sym].invested"),
    _ck("dang_long", "Đang LONG", "self.portfolio[sym].is_long"),
    _ck("dang_short", "Đang SHORT", "self.portfolio[sym].is_short"),
    _s("so_luong", "Số lượng đang giữ", "self.portfolio[sym].quantity", "lượng"),
    _s("gia_von", "Giá vốn trung bình", "self.portfolio[sym].average_price", "giá"),
    _s("lai_lo", "Lãi/lỗ chưa chốt", "self.portfolio[sym].unrealized_profit", "tiền"),
    _s("lai_lo_pt", "Lãi/lỗ chưa chốt (%)",
       "self.portfolio[sym].unrealized_profit_percent", "%"),
    _s("gia_tri_giu", "Giá trị đang giữ", "self.portfolio[sym].holdings_value", "tiền"),
    _s("phi_da_tra", "Phí đã trả cho mã này", "self.portfolio[sym].total_fees", "tiền"),
    _s("lai_lan_truoc", "Lãi lần đóng gần nhất",
       "self.portfolio[sym].last_trade_profit", "tiền"),
    _s("don_bay", "Đòn bẩy", "self.portfolio[sym].leverage", "lần"),
    # Đọc THUẦN — không sinh ra trạng thái nào của app.
    _s("so_lenh_cho", "Số lệnh đang chờ",
       "len(self.transactions.get_open_orders(sym))", "lượng"),
]

# ---------------------------------------------------------------------------
# ③ HỎI TÀI KHOẢN — cả túi tiền tôi ra sao  (không có ô mã)
# ---------------------------------------------------------------------------
TAI_KHOAN = [
    _s("tong_gia_tri", "Tổng giá trị danh mục",
       "self.portfolio.total_portfolio_value", "tiền"),
    _s("tien_mat", "Tiền mặt", "self.portfolio.cash", "tiền"),
    _s("ky_quy_con", "Ký quỹ còn lại", "self.portfolio.margin_remaining", "tiền"),
    _s("ky_quy_dung", "Ký quỹ đã dùng", "self.portfolio.total_margin_used", "tiền"),
    _s("lai_chua_chot", "Tổng lãi chưa chốt",
       "self.portfolio.total_unrealized_profit", "tiền"),
    _s("lai_da_chot", "Tổng lãi đã chốt", "self.portfolio.total_profit", "tiền"),
    _s("tong_phi", "Tổng phí đã trả", "self.portfolio.total_fees", "tiền"),
    _s("gia_tri_giu_het", "Tổng giá trị đang giữ",
       "self.portfolio.total_holdings_value", "tiền"),
]

# ---------------------------------------------------------------------------
# ④ HỎI LỊCH — bây giờ là lúc nào  (không có ô mã, trừ «phiên mở»)
# ---------------------------------------------------------------------------
# ⚠ ĐÃ BỎ «số nến đã chạy»: LEAN không đếm nến cho cả thuật toán, nó chỉ có `Samples`
# của TỪNG chỉ báo. Muốn con số ấy là app phải tự đếm — tức tự đẻ backend.
LICH = [
    _s("gio", "Giờ", "self.time.hour", "0–23"),
    _s("phut", "Phút", "self.time.minute", "0–59"),
    _s("thu", "Thứ trong tuần", "self.time.isoweekday()", "1–7 (2=thứ Hai)"),
    _s("ngay", "Ngày trong tháng", "self.time.day", "1–31"),
    _s("thang", "Tháng", "self.time.month", "1–12"),
    _ck("phien_mo", "Phiên đang mở", "self.is_market_open(sym)"),
]

# ---------------------------------------------------------------------------
# ⑤ HỎI DOANH NGHIỆP — công ty này tốt không
# ---------------------------------------------------------------------------
# ⚠ DỰNG SAU CÙNG. LEAN có 970 trường (Morningstar), nhưng BỘ DỮ LIỆU MIỄN PHÍ chỉ có
# `fundamental/coarse` (giá, khối lượng). Mấy trường dưới đây dựng ra thì hộp thoại
# bày được, nhưng CHẠY KHÔNG RA SỐ cho tới khi mua bộ fine. Để `tat = True` nên giao
# diện làm mờ và nói rõ vì sao, thay vì để người chơi vẽ xong rồi ngồi hỏi sao nó lặng.
DOANH_NGHIEP = [
    _s("pe", "P/E", "self.securities[sym].fundamentals.valuation_ratios.pe_ratio", "lần"),
    _s("pb", "P/B", "self.securities[sym].fundamentals.valuation_ratios.pb_ratio", "lần"),
    _s("ps", "P/S", "self.securities[sym].fundamentals.valuation_ratios.ps_ratio", "lần"),
    _s("peg", "PEG", "self.securities[sym].fundamentals.valuation_ratios.peg_ratio", "lần"),
    _s("ev_ebitda", "EV/EBITDA",
       "self.securities[sym].fundamentals.valuation_ratios.ev_to_ebitda", "lần"),
    _s("loi_suc_co_tuc", "Lợi suất cổ tức",
       "self.securities[sym].fundamentals.valuation_ratios.forward_dividend_yield", "%"),
    _s("von_hoa", "Vốn hoá thị trường",
       "self.securities[sym].fundamentals.market_cap", "tiền"),
]

# ---------------------------------------------------------------------------
# NĂM HỌ — và chúng KHÔNG còn là tường ngăn
# ---------------------------------------------------------------------------
# Trước: hai vế của một dòng chỉ rút được trong CÙNG một họ. Nên `Giá hiện tại >
# Giá vốn trung bình` — câu cắt lỗ cơ bản nhất — không vẽ được, chỉ vì một bên là
# thị trường còn một bên là vị thế. LEAN không có rào ấy: cả hai chỉ là biểu thức
# Python trên cùng một `sym`.
#
# Nay cả 68 đại lượng nằm trong MỘT kho (`tu_dien()["kho"]`); năm họ dưới đây còn
# đúng hai việc: làm đầu mục trong bảng chọn, và cho khối cái icon + cảnh báo dữ
# liệu. Ô chọn mã thì hỏi TỪNG đại lượng (`can_ma`), không hỏi họ nữa.
#
#   tat         họ chưa chạy được với dữ liệu miễn phí: bày mờ, nói rõ vì sao
HOI_THI_TRUONG = "hoi_thi_truong"
HOI_VI_THE = "hoi_vi_the"
HOI_TAI_KHOAN = "hoi_tai_khoan"
HOI_LICH = "hoi_lich"
HOI_DOANH_NGHIEP = "hoi_doanh_nghiep"

LOAI_HOI = {
    HOI_THI_TRUONG: {
        "nhan": "Hỏi thị trường",
        "mo_ta": "giá và chỉ báo — thế giới ngoài kia đang thế nào",
        "icon": "kieu-nen",
        "tat": False,
        "nhom": [("Giá", GIA), ("Chỉ báo", CHI_BAO),
                 ("Chỉ báo nhiều đường", CHI_BAO_NHIEU_DUONG),
                 ("Trạng thái mã", TRANG_THAI_MA)],
    },
    HOI_VI_THE: {
        "nhan": "Hỏi vị thế",
        "mo_ta": "mã này tôi đang giữ ra sao",
        "icon": "vao-lenh",
        "tat": False,
        "nhom": [("Vị thế", VI_THE)],
    },
    HOI_TAI_KHOAN: {
        "nhan": "Hỏi tài khoản",
        "mo_ta": "cả túi tiền tôi ra sao",
        "icon": "dat-co",
        "tat": False,
        "nhom": [("Tài khoản", TAI_KHOAN)],
    },
    HOI_LICH: {
        "nhan": "Hỏi lịch",
        "mo_ta": "bây giờ là lúc nào",
        "icon": "lich",
        "tat": False,
        "nhom": [("Thời gian", LICH)],
    },
    HOI_DOANH_NGHIEP: {
        "nhan": "Hỏi doanh nghiệp",
        "mo_ta": "công ty này tốt không — CẦN MUA dữ liệu cơ bản",
        "icon": "motSo",
        "tat": "Bộ dữ liệu miễn phí chỉ có fundamental/coarse. Mấy trường này cần bộ "
               "fine của QuantConnect, phải mua — vẽ ra thì chạy không ra số.",
        "nhom": [("Định giá", DOANH_NGHIEP)],
    },
}


# ---------------------------------------------------------------------------
# Tra cứu
# ---------------------------------------------------------------------------

def _bang():
    """{(loại, mã đại lượng): đại lượng} — dựng một lần, tra nhanh."""
    ra = {}
    for loai, d in LOAI_HOI.items():
        for ten_nhom, ds in d["nhom"]:
            for dl in ds:
                # Đóng dấu HỌ và NHÓM lên từng đại lượng. Trước đây chỉ cái khoá
                # `(loại, mã)` giữ thông tin ấy, nên rút một đại lượng ra khỏi bảng
                # là mất luôn chỗ nó thuộc về — mà bảng chọn thì cần biết để xếp mục.
                dl["ho"] = loai
                dl["nhom"] = ten_nhom
                ra[dl["ma"]] = dl
    return ra


#: Cả 68 đại lượng trong MỘT kho, tra thẳng bằng mã.
#:
#: ⚠ Khoá là MÃ, không phải `(họ, mã)`. 68 mã đều khác nhau — đã đếm, và `test_hoi`
#: canh để nó còn đúng khi thêm đại lượng mới. Khoá ghép đôi chính là bức tường cũ:
#: nó bắt mọi chỗ tra phải biết trước câu hỏi thuộc họ nào, mà cái biết ấy thì không
#: có thật khi hai vế của một dòng ở hai họ khác nhau.
BANG_DAI_LUONG = _bang()

#: Thứ tự bày trong bảng chọn — giữ đúng thứ tự khai, không sắp lại theo bảng chữ cái.
KHO = [BANG_DAI_LUONG[m] for m in
       [dl["ma"] for d in LOAI_HOI.values() for _t, ds in d["nhom"] for dl in ds]]


def dai_luong(ma):
    """Một đại lượng, hay None nếu mã không có trong kho."""
    return BANG_DAI_LUONG.get(ma)


def la_loai_hoi(t):
    return t in LOAI_HOI


#: Mã của mọi đại lượng là CHỈ BÁO — thứ phải khai trong `initialize` rồi LEAN tự cập
#: nhật mỗi nến, chứ không đọc thẳng ra số được như `giá` hay `tiền mặt`.
#: (*"We never need to 'update' our indicators with the data, the engine takes care of
#: this for us"* — chú thích trong `MovingAverageCrossAlgorithm` của QuantConnect.)
MA_CHI_BAO = frozenset(d["ma"] for d in CHI_BAO + CHI_BAO_NHIEU_DUONG)


def la_chi_bao(ma):
    """Đại lượng này có phải chỉ báo không — tức bộ sinh mã phải NÂNG nó lên
    `initialize`, và hai khối cùng dùng một chỉ báo thì dùng CHUNG một cái."""
    return ma in MA_CHI_BAO


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối cho giao diện.

    `kho` là MỘT mảng phẳng đủ 68 đại lượng — bảng chọn bày đúng mảng này, nên không
    có cách nào một đại lượng khai ở đây mà người dùng với không tới. `loai` chỉ còn
    là thông tin HỌ: nhãn, icon, và câu cảnh báo dữ liệu."""
    return {
        "phep_so": [{"ma": m, "nhan": n} for m, n in PHEP_SO],
        "phep_co_khong": [{"ma": m, "nhan": n} for m, n in PHEP_CO_KHONG],
        "phep_ghep": [{"ma": m, "nhan": n} for m, n in PHEP_GHEP],
        "loai": [
            {"ma": loai, "nhan": d["nhan"], "mo_ta": d["mo_ta"], "icon": d["icon"],
             "tat": d["tat"]}
            for loai, d in LOAI_HOI.items()
        ],
        "kho": KHO,
    }
