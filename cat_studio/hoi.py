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

KIEU_SO = "so"
KIEU_CO_KHONG = "co_khong"


def _s(ma, nhan, lean, don_vi="", tham_so=()):
    """Một đại lượng trả về SỐ."""
    return {"ma": ma, "nhan": nhan, "lean": lean, "kieu": KIEU_SO,
            "don_vi": don_vi, "tham_so": list(tham_so)}


def _ck(ma, nhan, lean):
    """Một đại lượng trả về ĐÚNG/SAI."""
    return {"ma": ma, "nhan": nhan, "lean": lean, "kieu": KIEU_CO_KHONG,
            "don_vi": "", "tham_so": []}


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
    _s("gia", "Giá hiện tại", "Securities[sym].Price", "giá"),
    _s("mo", "Giá mở", "slice.Bars[sym].Open", "giá"),
    _s("cao", "Giá cao", "slice.Bars[sym].High", "giá"),
    _s("thap", "Giá thấp", "slice.Bars[sym].Low", "giá"),
    _s("dong", "Giá đóng", "slice.Bars[sym].Close", "giá"),
    _s("khoi_luong", "Khối lượng", "slice.Bars[sym].Volume", "lượng"),
    _s("gia_mua", "Giá mua (bid)", "slice.QuoteBars[sym].Bid.Close", "giá"),
    _s("gia_ban", "Giá bán (ask)", "slice.QuoteBars[sym].Ask.Close", "giá"),
]

#: CHỈ BÁO. LEAN có 167 cái; đây là bộ ĐANG MỞ, chọn theo mức hay dùng. Thêm một cái
#: mới chỉ là thêm một dòng vào đây — miễn là ô `lean` ghi đúng chữ ký thật.
#:
#: `duong` = chỉ báo trả NHIỀU đường (MACD, Bollinger, Stochastic…). Giao diện bắt
#: chọn một đường; thiếu nó thì "giá > Bollinger" là một câu vô nghĩa.
CHI_BAO = [
    _s("sma", "SMA — trung bình trượt", "SMA(sym, n)", "giá",
       [_ts("n", "Chu kỳ", 20)]),
    _s("ema", "EMA — trung bình trượt luỹ thừa", "EMA(sym, n)", "giá",
       [_ts("n", "Chu kỳ", 20)]),
    _s("rsi", "RSI — sức mạnh tương đối", "RSI(sym, n)", "0–100",
       [_ts("n", "Chu kỳ", 14)]),
    _s("atr", "ATR — biên độ thật trung bình", "ATR(sym, n)", "giá",
       [_ts("n", "Chu kỳ", 14)]),
    _s("adx", "ADX — độ mạnh xu hướng", "ADX(sym, n)", "0–100",
       [_ts("n", "Chu kỳ", 14)]),
    _s("cci", "CCI", "CCI(sym, n)", "", [_ts("n", "Chu kỳ", 20)]),
    _s("mfi", "MFI — dòng tiền", "MFI(sym, n)", "0–100", [_ts("n", "Chu kỳ", 14)]),
    _s("wilr", "Williams %R", "WILR(sym, n)", "-100–0", [_ts("n", "Chu kỳ", 14)]),
    _s("mom", "Momentum", "MOM(sym, n)", "giá", [_ts("n", "Chu kỳ", 10)]),
    _s("roc", "ROC — tốc độ đổi giá", "ROC(sym, n)", "tỉ lệ",
       [_ts("n", "Chu kỳ", 10)]),
    _s("std", "Độ lệch chuẩn", "STD(sym, n)", "giá", [_ts("n", "Chu kỳ", 20)]),
    _s("obv", "OBV — khối lượng cân bằng", "OBV(sym)", "lượng"),
    _s("vwap", "VWAP — giá bình quân theo khối lượng", "VWAP(sym)", "giá"),
    _s("psar", "Parabolic SAR", "PSAR(sym)", "giá"),
    # --- NHỚ LẠI QUÁ KHỨ: ba cái này thay cho mọi phép "nhìn lại" ---
    _s("max", "Cao nhất N nến", "MAX(sym, n)", "giá", [_ts("n", "Số nến", 20)]),
    _s("min", "Thấp nhất N nến", "MIN(sym, n)", "giá", [_ts("n", "Số nến", 20)]),
    _s("delay", "Giá trị N nến TRƯỚC", "Delay(n)", "",
       [_ts("n", "Lùi mấy nến", 1, 1, 500)]),
]

#: Chỉ báo NHIỀU ĐƯỜNG — khai riêng vì giao diện phải bắt chọn đường.
CHI_BAO_NHIEU_DUONG = [
    {**_s("macd", "MACD", "MACD(sym, nhanh, cham, tin_hieu)", "",
          [_ts("nhanh", "Chu kỳ nhanh", 12), _ts("cham", "Chu kỳ chậm", 26),
           _ts("tin_hieu", "Chu kỳ tín hiệu", 9)]),
     "duong": [("Fast", "Đường nhanh"), ("Slow", "Đường chậm"),
               ("Signal", "Đường tín hiệu"), ("Histogram", "Histogram")]},
    {**_s("bb", "Bollinger Bands", "BB(sym, n, k)", "giá",
          [_ts("n", "Chu kỳ", 20), _ts("k", "Số lần độ lệch", 2, 1, 10)]),
     "duong": [("UpperBand", "Dải trên"), ("MiddleBand", "Dải giữa"),
               ("LowerBand", "Dải dưới")]},
    {**_s("sto", "Stochastic", "STO(sym, n)", "0–100", [_ts("n", "Chu kỳ", 14)]),
     "duong": [("StochK", "%K"), ("StochD", "%D")]},
    {**_s("kch", "Keltner Channel", "KCH(sym, n, k)", "giá",
          [_ts("n", "Chu kỳ", 20), _ts("k", "Số lần ATR", 2, 1, 10)]),
     "duong": [("UpperBand", "Dải trên"), ("MiddleBand", "Dải giữa"),
               ("LowerBand", "Dải dưới")]},
    {**_s("dch", "Donchian Channel", "DCH(sym, n)", "giá", [_ts("n", "Chu kỳ", 20)]),
     "duong": [("UpperBand", "Dải trên"), ("MiddleBand", "Dải giữa"),
               ("LowerBand", "Dải dưới")]},
]

#: Trạng thái của một mã — không so số, chỉ đúng/sai.
TRANG_THAI_MA = [
    _ck("giao_dich_duoc", "Mã này giao dịch được", "Securities[sym].IsTradable"),
    _ck("huy_niem_yet", "Mã này đã huỷ niêm yết", "Securities[sym].IsDelisted"),
    _ck("co_du_lieu", "Mã này có dữ liệu", "Securities[sym].HasData"),
    _ck("chia_co_tuc", "Hôm nay chia cổ tức", "sym in slice.Dividends"),
    _ck("chia_tach", "Hôm nay chia tách", "sym in slice.Splits"),
]

# ---------------------------------------------------------------------------
# ② HỎI VỊ THẾ — mã này tôi đang ra sao
# ---------------------------------------------------------------------------
VI_THE = [
    _ck("dang_giu", "Đang giữ mã này", "Portfolio[sym].Invested"),
    _ck("dang_long", "Đang LONG", "Portfolio[sym].IsLong"),
    _ck("dang_short", "Đang SHORT", "Portfolio[sym].IsShort"),
    _s("so_luong", "Số lượng đang giữ", "Portfolio[sym].Quantity", "lượng"),
    _s("gia_von", "Giá vốn trung bình", "Portfolio[sym].AveragePrice", "giá"),
    _s("lai_lo", "Lãi/lỗ chưa chốt", "Portfolio[sym].UnrealizedProfit", "tiền"),
    _s("lai_lo_pt", "Lãi/lỗ chưa chốt (%)",
       "Portfolio[sym].UnrealizedProfitPercent", "%"),
    _s("gia_tri_giu", "Giá trị đang giữ", "Portfolio[sym].HoldingsValue", "tiền"),
    _s("phi_da_tra", "Phí đã trả cho mã này", "Portfolio[sym].TotalFees", "tiền"),
    _s("lai_lan_truoc", "Lãi lần đóng gần nhất",
       "Portfolio[sym].LastTradeProfit", "tiền"),
    _s("don_bay", "Đòn bẩy", "Portfolio[sym].Leverage", "lần"),
    # Đọc THUẦN — không sinh ra trạng thái nào của app.
    _s("so_lenh_cho", "Số lệnh đang chờ",
       "len(Transactions.GetOpenOrders(sym))", "lượng"),
]

# ---------------------------------------------------------------------------
# ③ HỎI TÀI KHOẢN — cả túi tiền tôi ra sao  (không có ô mã)
# ---------------------------------------------------------------------------
TAI_KHOAN = [
    _s("tong_gia_tri", "Tổng giá trị danh mục",
       "Portfolio.TotalPortfolioValue", "tiền"),
    _s("tien_mat", "Tiền mặt", "Portfolio.Cash", "tiền"),
    _s("ky_quy_con", "Ký quỹ còn lại", "Portfolio.MarginRemaining", "tiền"),
    _s("ky_quy_dung", "Ký quỹ đã dùng", "Portfolio.TotalMarginUsed", "tiền"),
    _s("lai_chua_chot", "Tổng lãi chưa chốt",
       "Portfolio.TotalUnrealizedProfit", "tiền"),
    _s("lai_da_chot", "Tổng lãi đã chốt", "Portfolio.TotalProfit", "tiền"),
    _s("tong_phi", "Tổng phí đã trả", "Portfolio.TotalFees", "tiền"),
    _s("gia_tri_giu_het", "Tổng giá trị đang giữ",
       "Portfolio.TotalHoldingsValue", "tiền"),
]

# ---------------------------------------------------------------------------
# ④ HỎI LỊCH — bây giờ là lúc nào  (không có ô mã, trừ «phiên mở»)
# ---------------------------------------------------------------------------
# ⚠ ĐÃ BỎ «số nến đã chạy»: LEAN không đếm nến cho cả thuật toán, nó chỉ có `Samples`
# của TỪNG chỉ báo. Muốn con số ấy là app phải tự đếm — tức tự đẻ backend.
LICH = [
    _s("gio", "Giờ", "Time.hour", "0–23"),
    _s("phut", "Phút", "Time.minute", "0–59"),
    _s("thu", "Thứ trong tuần", "Time.isoweekday()", "1–7 (2=thứ Hai)"),
    _s("ngay", "Ngày trong tháng", "Time.day", "1–31"),
    _s("thang", "Tháng", "Time.month", "1–12"),
    _ck("phien_mo", "Phiên đang mở", "IsMarketOpen(sym)"),
]

# ---------------------------------------------------------------------------
# ⑤ HỎI DOANH NGHIỆP — công ty này tốt không
# ---------------------------------------------------------------------------
# ⚠ DỰNG SAU CÙNG. LEAN có 970 trường (Morningstar), nhưng BỘ DỮ LIỆU MIỄN PHÍ chỉ có
# `fundamental/coarse` (giá, khối lượng). Mấy trường dưới đây dựng ra thì hộp thoại
# bày được, nhưng CHẠY KHÔNG RA SỐ cho tới khi mua bộ fine. Để `tat = True` nên giao
# diện làm mờ và nói rõ vì sao, thay vì để người chơi vẽ xong rồi ngồi hỏi sao nó lặng.
DOANH_NGHIEP = [
    _s("pe", "P/E", "Securities[sym].Fundamentals.ValuationRatios.PERatio", "lần"),
    _s("pb", "P/B", "Securities[sym].Fundamentals.ValuationRatios.PBRatio", "lần"),
    _s("ps", "P/S", "Securities[sym].Fundamentals.ValuationRatios.PSRatio", "lần"),
    _s("peg", "PEG", "Securities[sym].Fundamentals.ValuationRatios.PEGRatio", "lần"),
    _s("ev_ebitda", "EV/EBITDA",
       "Securities[sym].Fundamentals.ValuationRatios.EVToEBITDA", "lần"),
    _s("loi_suc_co_tuc", "Lợi suất cổ tức",
       "Securities[sym].Fundamentals.ValuationRatios.ForwardDividendYield", "%"),
    _s("von_hoa", "Vốn hoá thị trường",
       "Securities[sym].Fundamentals.MarketCap", "tiền"),
]

# ---------------------------------------------------------------------------
# NĂM LOẠI KHỐI
# ---------------------------------------------------------------------------
#   can_ma      hộp thoại có ô chọn MÃ không
#   hai_ve_ma   vế phải có ô chọn mã RIÊNG không (chỉ ① — để so chéo mã)
#   tat         loại chưa chạy được với dữ liệu miễn phí: bày mờ, nói rõ vì sao
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
        "can_ma": True, "hai_ve_ma": True, "tat": False,
        "nhom": [("Giá", GIA), ("Chỉ báo", CHI_BAO),
                 ("Chỉ báo nhiều đường", CHI_BAO_NHIEU_DUONG),
                 ("Trạng thái mã", TRANG_THAI_MA)],
    },
    HOI_VI_THE: {
        "nhan": "Hỏi vị thế",
        "mo_ta": "mã này tôi đang giữ ra sao",
        "icon": "vao-lenh",
        "can_ma": True, "hai_ve_ma": False, "tat": False,
        "nhom": [("Vị thế", VI_THE)],
    },
    HOI_TAI_KHOAN: {
        "nhan": "Hỏi tài khoản",
        "mo_ta": "cả túi tiền tôi ra sao",
        "icon": "dat-co",
        "can_ma": False, "hai_ve_ma": False, "tat": False,
        "nhom": [("Tài khoản", TAI_KHOAN)],
    },
    HOI_LICH: {
        "nhan": "Hỏi lịch",
        "mo_ta": "bây giờ là lúc nào",
        "icon": "delay",
        "can_ma": False, "hai_ve_ma": False, "tat": False,
        "nhom": [("Thời gian", LICH)],
    },
    HOI_DOANH_NGHIEP: {
        "nhan": "Hỏi doanh nghiệp",
        "mo_ta": "công ty này tốt không — CẦN MUA dữ liệu cơ bản",
        "icon": "motSo",
        "can_ma": True, "hai_ve_ma": True,
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
        for _ten_nhom, ds in d["nhom"]:
            for dl in ds:
                ra[(loai, dl["ma"])] = dl
    return ra


BANG_DAI_LUONG = _bang()


def dai_luong(loai, ma):
    """Một đại lượng, hay None nếu loại/mã không có trong từ điển."""
    return BANG_DAI_LUONG.get((loai, ma))


def la_loai_hoi(t):
    return t in LOAI_HOI


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối cho giao diện."""
    return {
        "phep_so": [{"ma": m, "nhan": n} for m, n in PHEP_SO],
        "phep_co_khong": [{"ma": m, "nhan": n} for m, n in PHEP_CO_KHONG],
        "loai": [
            {"ma": loai, "nhan": d["nhan"], "mo_ta": d["mo_ta"], "icon": d["icon"],
             "can_ma": d["can_ma"], "hai_ve_ma": d["hai_ve_ma"], "tat": d["tat"],
             "nhom": [{"ten": ten, "dai_luong": ds} for ten, ds in d["nhom"]]}
            for loai, d in LOAI_HOI.items()
        ],
    }
