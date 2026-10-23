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


def ds_ghep(ve):
    """Phần GHÉP của một vế -> DANH SÁCH thành phần. [] nếu vế không ghép gì.

    ⚠ MỘT VẾ NAY LÀ MỘT CHUỖI, KHÔNG PHẢI MỘT CẶP (18/10/2026). Bản trước `ghep` là
    một dict, tức đúng hai vế một phép: `giá / đỉnh 60 nến`. Đủ cho vd1, không đủ cho
    cái mà ba ví dụ khác cần:

        điểm = 0,25×ROC(63) + 0,35×ROC(126) + 0,40×ROC(252) − 0,20×biến_động

    Bốn thành phần, mỗi cái một HỆ SỐ. Đó không phải cây biểu thức — nó là một DANH
    SÁCH, nên hàng điều kiện vẫn là mấy dòng đọc được chứ không thành ô gõ công thức.
    Đúng chỗ lằn ranh cũ muốn giữ.

    HỆ SỐ nằm TRONG từng thành phần chứ không thành một phép `*` riêng, và đó là cả
    mẹo: có hệ số thì tổng có trọng số viết được bằng một chuỗi nối TRÁI→PHẢI, không
    cần thứ tự ưu tiên. Không có nó thì `0,25×a + 0,35×b` nối trái→phải ra
    `((0,25×a)+0,35)×b` — sai, mà sai lặng.

    FILE CŨ: `ghep` là dict thì gói thành danh sách một phần tử. Bỏ nhánh này là mọi
    sơ đồ đã lưu mất phần ghép — thẻ vẫn vẽ, mã vẫn sinh, chỉ thiếu mất nửa điều kiện.
    """
    g = ve.get("ghep") if isinstance(ve, dict) else None
    if isinstance(g, dict):
        g = [g]
    if not isinstance(g, list):
        return []
    return [t for t in g if isinstance(t, dict) and t.get("phep")]


def he_so_cua(x):
    """Hệ số của một thành phần ghép. 1 nếu không khai — tức «không nhân gì»."""
    try:
        v = float(x.get("he_so")) if isinstance(x, dict) else 1.0
    except (TypeError, ValueError):
        return 1.0
    return 1.0 if v is None else v


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
    # ⚠ ĐỌC QUA `securities`, KHÔNG QUA `data.quote_bars` — và đây là lý do.
    #
    # `data.quote_bars[sym]` NÉM `KeyNotFoundException` khi nhịp ấy không có nến báo
    # giá, và bộ dữ liệu miễn phí thì cổ phiếu CHỈ có nến giao dịch, không có nến báo
    # giá nào. Tức vẽ một điều kiện «Giá mua (bid) > …» là backtest ĐỨT GIỮA CHỪNG —
    # không phải sai số, mà chết hẳn: *"'SPY' wasn't found in the QuoteBars object"*.
    #
    # LEAN có sẵn lối an toàn, và nó CÙNG MỘT CON SỐ:
    #     Security.BidPrice => Cache.BidPrice == 0 ? Price : Cache.BidPrice
    # tức có nến báo giá thì lấy bid thật, không có thì rơi về giá đóng. Điều kiện vẫn
    # có nghĩa, và không nổ.
    #
    # Tìm ra bằng cách VẼ THỬ TỪNG ĐẠI LƯỢNG rồi cho LEAN đọc cả 148 cái trong một
    # lượt chạy — không ví dụ nào trong tập mẫu dùng bid/ask, nên chỗ này nằm im từ
    # ngày viết. Đúng loại lỗi chỉ lộ khi có người vẽ đúng nó.
    _s("gia_mua", "Giá mua (bid)", "self.securities[sym].bid_price", "giá"),
    _s("gia_ban", "Giá bán (ask)", "self.securities[sym].ask_price", "giá"),
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
    # ───────────────────────────────────────────────────────────────────────
    # ĐẾM LẠI CẢ KỆ CỦA LEAN (18/10/2026) — 73 chỉ báo một đường thêm ở đây.
    #
    # Chú thích cũ ngay trên bảng này viết: «LEAN có 167 cái; đây là bộ ĐANG MỞ,
    # chọn theo mức hay dùng». Câu ấy thật thà, nhưng «hay dùng» là ai quyết? Thực
    # tế nó là «cái nào ví dụ vừa gặp thì thêm». Đếm thẳng
    # `QCAlgorithm.Indicators.cs` ra 122 hàm chỉ báo; app bày 21.
    #
    # NHÃN · ĐƠN VỊ · MẶC ĐỊNH là phần người đặt (máy không đặt hộ được, và đơn vị
    # đặt sai thì giao diện bày ra một phép so vô nghĩa). TÊN và SỐ LƯỢNG tham số
    # thì đối chiếu từng dòng với chữ ký thật trước khi viết ra đây — `test_du_lean`
    # canh lại chuyện đó mỗi lần chạy cổng, nên sai một tham số là cổng đỏ chứ không
    # phải backtest nổ.
    # ───────────────────────────────────────────────────────────────────────
    _s('alma', 'ALMA — trung bình Arnaud Legoux', "self.alma(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('dema', 'DEMA — trung bình luỹ thừa KÉP', "self.dema(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('tema', 'TEMA — trung bình luỹ thừa BA LẦN', "self.tema(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('trima', 'TRIMA — trung bình tam giác', "self.trima(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('t_3', 'T3 — trung bình Tillson', "self.t_3(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('hma', 'HMA — trung bình Hull (ít trễ)', "self.hma(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('lwma', 'LWMA — trung bình có trọng số tuyến tính', "self.lwma(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('vwma', 'VWMA — trung bình theo khối lượng', "self.vwma(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('wwma', 'WWMA — trung bình Wilder', "self.wwma(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('zlema', 'ZLEMA — trung bình luỹ thừa không trễ', "self.zlema(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('frama', 'FRAMA — trung bình thích nghi fractal', "self.frama(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('vidya', 'VIDYA — trung bình thích nghi theo biến động', "self.vidya(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('mgd', 'McGinley Dynamic — trung bình bám thị trường', "self.mgd(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('rma', 'RMA — trung bình tương đối', "self.rma(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('mama', 'MAMA — trung bình thích nghi MESA', "self.mama(sym)",
       'giá', []),
    _s('kama', 'KAMA — trung bình thích nghi Kaufman', "self.kama(sym, n, ema_nhanh, ema_cham)",
       'giá', [_ts('n', 'Chu kỳ', 10), _ts('ema_nhanh', 'EMA nhanh', 2), _ts('ema_cham', 'EMA chậm', 30)]),
    _s('midpoint', 'Trung điểm N nến (cao nhất + thấp nhất)/2', "self.midpoint(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('midprice', 'Trung giá N nến (đỉnh + đáy)/2', "self.midprice(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('tsf', 'Dự báo chuỗi thời gian', "self.tsf(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('sum', 'Tổng N nến', "self.sum(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('str', 'SuperTrend', "self.str(sym, n, he_so)",
       'giá', [_ts('n', 'Chu kỳ', 10), _ts('he_so', 'Nhân ATR', 3.0)]),
    _s('sarext', 'Parabolic SAR mở rộng', "self.sarext(sym)",
       'giá', []),
    _s('pphl', 'Pivot Points — đỉnh/đáy đảo chiều', "self.pphl(sym, n_dinh, n_day)",
       'giá', [_ts('n_dinh', 'Số nến bên đỉnh', 10), _ts('n_day', 'Số nến bên đáy', 10)]),
    _s('zz', 'ZigZag — điểm quay đầu', "self.zz(sym)",
       'giá', []),
    _s('tp', 'Time Profile — giá theo thời gian', "self.tp(sym)",
       'giá', []),
    _s('vp', 'Volume Profile — giá theo khối lượng', "self.vp(sym)",
       'giá', []),
    _s('ar', 'Biên độ trung bình', "self.ar(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 14)]),
    _s('tr', 'Biên độ thật (một nến)', "self.tr(sym)",
       'giá', []),
    _s('natr', 'ATR chuẩn hoá theo giá', "self.natr(sym, n)",
       '%', [_ts('n', 'Chu kỳ', 14)]),
    _s('mad', 'Độ lệch tuyệt đối trung bình', "self.mad(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('rsv', 'Biến động Rogers-Satchell', "self.rsv(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 20)]),
    _s('tdd', 'Độ lệch xuống dưới mục tiêu', "self.tdd(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 20)]),
    _s('mass', 'Mass Index — phình biên độ', "self.mass(sym)",
       'lần', []),
    _s('chop', 'Choppiness — thị trường đi ngang hay có xu hướng', "self.chop(sym, n)",
       '0–100', [_ts('n', 'Chu kỳ', 14)]),
    _s('he', 'Hurst Exponent — nhớ dài hạn (0,5 = ngẫu nhiên)', "self.he(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 20)]),
    _s('sm', 'Squeeze Momentum — 1 là đang bị nén', "self.sm(sym)",
       'lần', []),
    _s('adxr', 'ADXR — ADX làm mượt', "self.adxr(sym, n)",
       '0–100', [_ts('n', 'Chu kỳ', 14)]),
    _s('cmo', 'Chande Momentum Oscillator', "self.cmo(sym, n)",
       '±100', [_ts('n', 'Chu kỳ', 20)]),
    _s('crsi', 'Connors RSI', "self.crsi(sym, n_rsi, n_chuoi, n_xep_hang)",
       '0–100', [_ts('n_rsi', 'Chu kỳ RSI', 3), _ts('n_chuoi', 'Chu kỳ RSI chuỗi', 2), _ts('n_xep_hang', 'Chu kỳ xếp hạng', 100)]),
    _s('stc', 'Schaff Trend Cycle', "self.stc(sym, n_chu_trinh, n_nhanh, n_cham)",
       '0–100', [_ts('n_chu_trinh', 'Chu kỳ chu trình', 10), _ts('n_nhanh', 'Chu kỳ nhanh', 23), _ts('n_cham', 'Chu kỳ chậm', 50)]),
    _s('do', 'Derivative Oscillator', "self.do(sym, n_rsi, n_muot_1, n_muot_2, n_tin_hieu)",
       'tỉ lệ', [_ts('n_rsi', 'Chu kỳ RSI', 14), _ts('n_muot_1', 'Làm mượt lần 1', 5), _ts('n_muot_2', 'Làm mượt lần 2', 3), _ts('n_tin_hieu', 'Chu kỳ tín hiệu', 9)]),
    _s('ultosc', 'Ultimate Oscillator', "self.ultosc(sym, n1, n2, n3)",
       '0–100', [_ts('n1', 'Chu kỳ ngắn', 7), _ts('n2', 'Chu kỳ vừa', 14), _ts('n3', 'Chu kỳ dài', 28)]),
    _s('momersion', 'Momersion — động lượng hay hồi quy', "self.momersion(sym, n_nho_nhat, n)",
       '0–100', [_ts('n_nho_nhat', 'Chu kỳ nhỏ nhất', 20), _ts('n', 'Chu kỳ đầy đủ', 200)]),
    _s('momp', 'Momentum theo phần trăm', "self.momp(sym, n)",
       '%', [_ts('n', 'Chu kỳ', 10)]),
    _s('rocp', 'ROC theo phần trăm', "self.rocp(sym, n)",
       '%', [_ts('n', 'Chu kỳ', 10)]),
    _s('rocr', 'ROC dạng tỉ số (giá / giá cũ)', "self.rocr(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 10)]),
    _s('logr', 'Log lợi suất — log(giá / giá trước)', "self.logr(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 1)]),
    _s('trix', 'TRIX — ROC của EMA ba lần', "self.trix(sym, n)",
       '%', [_ts('n', 'Chu kỳ', 15)]),
    _s('dpo', 'Detrended Price Oscillator — bỏ xu hướng', "self.dpo(sym, n)",
       'giá', [_ts('n', 'Chu kỳ', 20)]),
    _s('cc', 'Coppock Curve', "self.cc(sym)",
       'tỉ lệ', []),
    _s('kst', 'Know Sure Thing', "self.kst(sym)",
       'tỉ lệ', []),
    _s('tsi', 'True Strength Index', "self.tsi(sym)",
       '±100', []),
    _s('rvi', 'Relative Vigor Index', "self.rvi(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 10)]),
    _s('fish', 'Fisher Transform', "self.fish(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 10)]),
    _s('pso', 'Premier Stochastic Oscillator (−1…1)', "self.pso(sym, n, n_ema)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 14), _ts('n_ema', 'Chu kỳ EMA', 10)]),
    _s('tds', 'Tom DeMark Sequential — điểm cạn xu hướng', "self.tds(sym)",
       'lần', []),
    _s('ibs', 'Internal Bar Strength — vị trí giá đóng trong nến', "self.ibs(sym)",
       'tỉ lệ', []),
    _s('bop', 'Balance of Power — (đóng − mở)/(cao − thấp)', "self.bop(sym)",
       'tỉ lệ', []),
    _s('aps', 'Augen Price Spike — đổi giá tính theo độ lệch chuẩn', "self.aps(sym, n)",
       'lần', [_ts('n', 'Chu kỳ', 3)]),
    _s('si', 'Swing Index (Wilder)', "self.si(sym, gioi_han, res)",
       'tỉ lệ', [_ts('gioi_han', 'Giới hạn dịch giá', 3.0)]),
    _s('asi', 'Accumulative Swing Index (Wilder)', "self.asi(sym, gioi_han, res)",
       'tỉ lệ', [_ts('gioi_han', 'Giới hạn dịch giá', 3.0)]),
    _s('ker', 'Kaufman Efficiency Ratio', "self.ker(sym)",
       'tỉ lệ', []),
    _s('rdv', 'Khối lượng hôm nay so với bình quân cùng giờ', "self.rdv(sym, n)",
       'lần', [_ts('n', 'Số ngày', 2)]),
    _s('ad', 'Accumulation/Distribution — tích luỹ phân phối', "self.ad(sym)",
       'lượng', []),
    _s('adosc', 'A/D Oscillator', "self.adosc(sym, n_nhanh, n_cham)",
       'lượng', [_ts('n_nhanh', 'Chu kỳ nhanh', 3), _ts('n_cham', 'Chu kỳ chậm', 10)]),
    _s('co', 'Chaikin Oscillator', "self.co(sym, n_nhanh, n_cham)",
       'lượng', [_ts('n_nhanh', 'Chu kỳ nhanh', 3), _ts('n_cham', 'Chu kỳ chậm', 10)]),
    _s('kvo', 'Klinger Volume Oscillator', "self.kvo(sym, n_nhanh, n_cham)",
       'lượng', [_ts('n_nhanh', 'Chu kỳ nhanh', 34), _ts('n_cham', 'Chu kỳ chậm', 55)]),
    _s('sobv', 'OBV làm mượt', "self.sobv(sym, n)",
       'lượng', [_ts('n', 'Chu kỳ', 20)]),
    _s('emv', 'Ease of Movement — giá đi dễ hay khó', "self.emv(sym)",
       'lượng', []),
    _s('fi', 'Force Index — lực của dòng tiền', "self.fi(sym, n)",
       'lượng', [_ts('n', 'Chu kỳ', 13)]),
    _s('cmf', 'Chaikin Money Flow', "self.cmf(sym, n)",
       'tỉ lệ', [_ts('n', 'Chu kỳ', 21)]),
    _s('sr', 'Sharpe Ratio (cuốn theo N nến)', "self.sr(sym, n)",
       'lần', [_ts('n', 'Số nến', 252)]),
    _s('sortino', 'Sortino Ratio (cuốn theo N nến)', "self.sortino(sym, n)",
       'lần', [_ts('n', 'Số nến', 252)]),
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
    # ⚠ DONCHIAN KHÔNG CÓ DẢI GIỮA. Bản trước chép danh sách đường của Bollinger
    # sang đây cho nhanh — `DonchianChannel.cs` chỉ khai `UpperBand` và `LowerBand`,
    # không có `MiddleBand`. Chọn «Dải giữa» là backtest nổ ngay nến đầu:
    # *'DonchianChannel' object has no attribute 'middle_band'*.
    # Lỗi này nằm trong app từ lâu, và chỉ lòi ra khi gọi THẬT cả 105 chỉ báo — bài
    # kiểm chỉ đếm tham số thì không thấy, vì tham số của `dch` vẫn đúng.
    {**_s("dch", "Donchian Channel", "self.dch(sym, n)", "giá", [_ts("n", "Chu kỳ", 20)]),
     "duong": [("upper_band", "Dải trên"), ("lower_band", "Dải dưới")]},
    # ─── ĐẾM LẠI CẢ KỆ (18/10/2026) — 11 chỉ báo nhiều đường thêm ở đây ───
    {**_s('lsma', 'LSMA — trung bình hồi quy bình phương nhỏ nhất', "self.lsma(sym, n)",
          'giá', [_ts('n', 'Chu kỳ', 20)]),
     "duong": [('intercept', 'Chặn'), ('slope', 'Độ dốc')]},
    {**_s('abands', 'Acceleration Bands — dải gia tốc', "self.abands(sym, n)",
          'giá', [_ts('n', 'Chu kỳ', 20)]),
     "duong": [('middle_band', 'Dải giữa'), ('upper_band', 'Dải trên'), ('lower_band', 'Dải dưới')]},
    {**_s('rc', 'Kênh hồi quy', "self.rc(sym, n, k)",
          'giá', [_ts('n', 'Chu kỳ', 20), _ts('k', 'Số độ lệch', 2.0)]),
     "duong": [('upper_channel', 'Kênh trên'), ('lower_channel', 'Kênh dưới')]},
    {**_s('cks', 'Chande Kroll Stop — mức chốt lỗ', "self.cks(sym, n_atr, he_so_atr, n)",
          'giá', [_ts('n_atr', 'Chu kỳ ATR', 10), _ts('he_so_atr', 'Nhân ATR', 3.0), _ts('n', 'Chu kỳ', 9)]),
     "duong": [('short_stop', 'Chốt cho vị thế SHORT'), ('long_stop', 'Chốt cho LONG')]},
    {**_s('ichimoku', 'Ichimoku Kinko Hyo', "self.ichimoku(sym, n_tenkan, n_kijun, n_senkou_a, n_senkou_b, tre_senkou_a, tre_senkou_b)",
          'giá', [_ts('n_tenkan', 'Tenkan', 9), _ts('n_kijun', 'Kijun', 26), _ts('n_senkou_a', 'Senkou A', 26), _ts('n_senkou_b', 'Senkou B', 52), _ts('tre_senkou_a', 'Trễ Senkou A', 26), _ts('tre_senkou_b', 'Trễ Senkou B', 26)]),
     "duong": [('tenkan', 'Tenkan-sen'), ('kijun', 'Kijun-sen'), ('senkou_a', 'Senkou span A'), ('senkou_b', 'Senkou span B'), ('chikou', 'Chikou span')]},
    {**_s('heikin_ashi', 'Nến Heikin-Ashi', "self.heikin_ashi(sym)",
          'giá', []),
     "duong": [('open', 'Mở'), ('high', 'Cao'), ('low', 'Thấp'), ('close', 'Đóng'), ('volume', 'Khối lượng')]},
    {**_s('aroon', 'Aroon Oscillator', "self.aroon(sym, n_len, n_xuong)",
          '±100', [_ts('n_len', 'Chu kỳ lên', 25), _ts('n_xuong', 'Chu kỳ xuống', 25)]),
     "duong": [('aroon_up', 'Aroon lên'), ('aroon_down', 'Aroon xuống')]},
    {**_s('srsi', 'Stochastic RSI', "self.srsi(sym, n_rsi, n_stoch, n_k, n_d)",
          '0–100', [_ts('n_rsi', 'Chu kỳ RSI', 14), _ts('n_stoch', 'Chu kỳ Stochastic', 14), _ts('n_k', 'Làm mượt %K', 3), _ts('n_d', 'Làm mượt %D', 3)]),
     "duong": [('k', 'Đường %K'), ('d', 'Đường %D')]},
    {**_s('vtx', 'Vortex — bắt đầu và tiếp diễn xu hướng', "self.vtx(sym, n)",
          'tỉ lệ', [_ts('n', 'Chu kỳ', 14)]),
     "duong": [('plus_vortex', 'Vortex dương (+VI)'), ('minus_vortex', 'Vortex âm (−VI)')]},
    {**_s('wto', 'WaveTrend Oscillator', "self.wto(sym, n_kenh, n_trung_binh, n_tin_hieu)",
          'tỉ lệ', [_ts('n_kenh', 'Chu kỳ kênh', 10), _ts('n_trung_binh', 'Chu kỳ trung bình', 21), _ts('n_tin_hieu', 'Chu kỳ tín hiệu', 4)]),
     "duong": [('channel_average', 'Trung bình kênh'), ('channel_deviation', 'Độ lệch kênh'), ('channel_index_average', 'Trung bình chỉ số kênh'), ('signal', 'Đường tín hiệu')]},
    {**_s('ht', 'Hilbert Transform', "self.ht(sym, n, he_so_pha, he_so_vuong)",
          'giá', [_ts('n', 'Độ dài', 7), _ts('he_so_pha', 'Hệ số cùng pha', 0.635), _ts('he_so_vuong', 'Hệ số vuông pha', 0.338)]),
     "duong": [('in_phase', 'Cùng pha'), ('quadrature', 'Vuông pha')]},
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
# ⑤ HỎI TRÍ NHỚ — cỗ máy đã quyết gì ở nhịp trước
# ---------------------------------------------------------------------------
# ⚠ ĐÂY LÀ HỌ DUY NHẤT KHÔNG ĐỌC GÌ CỦA LEAN, nên nó phải được biện hộ cẩn thận.
#
# D-11 cấm app đẻ ra bộ máy tính toán thứ hai: thứ gì LEAN tính thì để LEAN tính.
# Trí nhớ KHÔNG vi phạm điều ấy, vì nó không TÍNH gì cả — nó chỉ giữ lại một quyết
# định mà CHÍNH SƠ ĐỒ vừa ra. LEAN không có khái niệm nào cho chuyện đó (`object_
# store` là để lưu giữa các LƯỢT CHẠY, không phải giữa hai nến), nên không có gì để
# mà «để LEAN làm».
#
# VÀ RANH GIỚI PHẢI RÕ, không thì họ này nuốt dần mọi thứ. Ba thứ vd10/vd11 nhớ mà
# KHÔNG được vào đây, vì LEAN đã lo rồi:
#     peak_price   -> `TrailingStopRiskManagementModel`
#     close_win    -> chỉ báo (`max` · `min` · `sma`…)
#     held_trade   -> «Đang giữ mã này» (`portfolio[sym].invested`)
# Còn lại mới là trí nhớ thật: cờ «đang chờ mua lại», đếm «đã hồi phục mấy tháng»,
# và giá trị của chính một đại lượng ở nhịp TRƯỚC.
#
# ⚠ MƯỜI HAI Ô CỐ ĐỊNH, KHÔNG SINH ĐỘNG. Cho người dùng tự khai tên biến thì từ điển
# hết là từ điển: `BANG_DAI_LUONG` đổi theo từng sơ đồ, và mọi hàng rào lặp qua từ
# điển (`test_hoi`, `test_moi_noi`, `test_du_lean`) mất chỗ đứng. Nên: mười hai ô
# khai sẵn ở đây, còn TÊN thì khối Bắt đầu đặt (xem `bat_dau.TRI_NHO`). Giao diện bày
# tên người dùng đặt, chỉ những ô đã khai.
#
#   CHUNG   — một giá trị cho cả cỗ máy ("đang ở chế độ phòng thủ").
#   THEO MÃ — mỗi mã một giá trị ("mã này đang chờ mua lại").
SO_O_NHO = 3        #: mỗi loại (số / đúng-sai) × mỗi phạm vi (chung / theo mã)

TRI_NHO = (
    [_s(f"nho_so_{i}", f"Trí nhớ CHUNG — số {i}", f"self._nho['so_{i}']", "tuỳ")
     for i in range(1, SO_O_NHO + 1)]
    + [_ck(f"nho_co_{i}", f"Trí nhớ CHUNG — đúng/sai {i}", f"self._nho['co_{i}']")
       for i in range(1, SO_O_NHO + 1)]
    + [_s(f"nho_ma_so_{i}", f"Trí nhớ THEO MÃ — số {i}",
          f"self._nho_cua(sym)['so_{i}']", "tuỳ")
       for i in range(1, SO_O_NHO + 1)]
    + [_ck(f"nho_ma_co_{i}", f"Trí nhớ THEO MÃ — đúng/sai {i}",
           f"self._nho_cua(sym)['co_{i}']")
       for i in range(1, SO_O_NHO + 1)]
)

HOI_TRI_NHO = "hoi_tri_nho"


def la_tri_nho(ma):
    """Mã này có phải một ô trí nhớ không."""
    return any(d["ma"] == ma for d in TRI_NHO)


def o_nho_cua(ma):
    """Một ô trí nhớ theo mã, hay None. Dùng để biết nó CHUNG hay THEO MÃ."""
    return next((d for d in TRI_NHO if d["ma"] == ma), None)


# ---------------------------------------------------------------------------
# ⑥ HỎI DOANH NGHIỆP — công ty này tốt không
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
    HOI_TRI_NHO: {
        "nhan": "Hỏi trí nhớ",
        "mo_ta": "cỗ máy đã quyết gì ở nhịp trước",
        "icon": "ghim",
        "tat": False,
        "nhom": [("Trí nhớ", TRI_NHO)],
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


#: Đơn vị «giá» — 59 đại lượng mang nó, và nay nó KHÔNG CÒN LÀ MỘT CÁI NHÃN NỮA:
#: cửa sổ View hỏi đúng ô này để biết vẽ một đại lượng Ở ĐÂU. Cùng thang với giá thì
#: nó chồng lên nến (trung bình trượt, dải Bollinger, đỉnh/đáy N nến); không cùng
#: thang thì nó phải có khung riêng, vì RSI chạy 0–100 mà vàng chạy quanh 1250 —
#: nhét chung một trục thì một trong hai thành đường thẳng dính mép.
#:
#: ⚠ ĐỂ TỪ ĐIỂN NÓI, ĐỪNG ĐỂ GIAO DIỆN ĐOÁN. Cách duy nhất khác là giao diện tự nhìn
#: con số rồi suy ra thang — tức một bản luật thứ hai, viết bằng TypeScript, cho thứ
#: Python đã khai sẵn ở đây.
DON_VI_GIA = "giá"


def dai_luong(ma):
    """Một đại lượng, hay None nếu mã không có trong kho."""
    return BANG_DAI_LUONG.get(ma)


def cung_thang_gia(ma):
    """Đại lượng này có vẽ chung trục với nến được không. -> bool"""
    d = BANG_DAI_LUONG.get(ma)
    return bool(d) and d.get("don_vi") == DON_VI_GIA


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
