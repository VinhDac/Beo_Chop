"""ĐỦ LEAN — app có bày HẾT những gì LEAN cho, hay chỉ bày theo ví dụ vừa gặp.

VÌ SAO CÓ BÀI NÀY
-----------------
Soát 11 chiến thuật ví dụ xong thì lòi ra một chuyện khó chịu hơn mọi lỗi đã gặp:
bảng «Chia vốn» của app có **2** món, kệ của LEAN có **10**. Bảng Alpha có **0**,
LEAN có **7**. Bảy món chia vốn còn lại cứ nằm đó — trong đó có đúng mấy món làm hộ
ta phần toán mà ba ví dụ phải viết tay hàng chục dòng.

Không ai làm sai gì cả. Mỗi lần có một ví dụ mới, người viết thêm đúng cái model ví
dụ ấy cần — và thế là đủ, cho ví dụ ấy. Chuyện chưa từng xảy ra là **đứng ra đếm**:
LEAN tổng cộng cho bao nhiêu, app bày bao nhiêu.

Đây vẫn là cùng một bệnh với `test_moi_noi`, chỉ là ở tầng cao hơn một bậc:

    `test_moi_noi`   soi hai bảng CỦA TA phải dài bằng nhau
    bài này          soi bảng của TA so với kệ của LEAN

Và cũng cùng một kiểu hỏng LẶNG: một bảng tụt lại sau LEAN thì chẳng gì vỡ. App chạy
đúng, backtest ra số, cổng xanh. Người dùng chỉ không bao giờ biết là có cái họ cần
nằm sẵn trong backend, cách họ một ô chọn.

LỐI THOÁT HỢP LỆ
----------------
`CO_Y_BO` — cố ý không bày, kèm LÝ DO. Bày hết không phải là mục tiêu: có model cần
dữ liệu trả tiền, có model là lớp nền trừu tượng, có model đòi người dùng viết Python
(trái D-11). Nhưng mỗi cái bỏ phải NÓI RA VÌ SAO, ở đây, bằng chữ. "Quên" thì không.

Bài này cũng canh ngược lại: `CO_Y_BO` kể tên một model mà LEAN không còn có, hay
một model app đã bày rồi, thì cũng là đỏ — danh sách bỏ không được phép mục.

KHÔNG CÓ MÃ NGUỒN LEAN THÌ SAO
------------------------------
Máy nào chưa trỏ tới mã nguồn LEAN thì bài này không so được. Nhưng bỏ qua LẶNG đúng
là cái bệnh đang chữa, nên nó không im: in cảnh báo to, rồi vẫn soi `MOC` — bản chụp
số lượng của lần soát gần nhất. Nhờ `MOC` mà dù không có LEAN, không ai rút ngắn được
bảng nào mà cổng không kêu.

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, chay_lean, hoi, luu_tru

loi = []


def kiem(dieu, cau):
    if not dieu:
        loi.append(cau)
        print(f"  ✘ {cau}")
    return dieu


# ---------------------------------------------------------------------------
# Mấy hàm trong `QCAlgorithm.Indicators.cs` KHÔNG phải chỉ báo — chúng là hạ tầng
# (tự dựng, đăng ký, nối consolidator). Lọc ra kẻo đếm thừa.
# ---------------------------------------------------------------------------
KHONG_PHAI_CHI_BAO = {
    "Consolidate", "CreateIndicatorName", "FilteredIdentity", "Identity",
    "RegisterIndicator", "ResolveConsolidator", "WarmUpIndicator",
}

#: Lớp nền của từng họ model. Một lớp thuộc họ khi chuỗi kế thừa của nó với tới đây.
NEN = {
    "Alphas": {"AlphaModel", "IAlphaModel"},
    "Portfolio": {"PortfolioConstructionModel", "IPortfolioConstructionModel"},
    "Risk": {"RiskManagementModel", "IRiskManagementModel"},
    "Execution": {"ExecutionModel", "IExecutionModel"},
    "Selection": {"UniverseSelectionModel", "IUniverseSelectionModel",
                  "CustomUniverseSelectionModel"},
}

# ---------------------------------------------------------------------------
# CỐ Ý KHÔNG BÀY — mỗi dòng phải có lý do viết bằng chữ.
# ---------------------------------------------------------------------------
CO_Y_BO = {
    # --- chỉ báo: 17 cái LEAN có mà app CỐ Ý không bày ---
    'A':
        'Nhận HAI mã (`Symbol target, Symbol reference`) — '
        'alpha/beta/tương quan/hiệp phương sai của mã này SO VỚI mã '
        'kia. Một đại lượng trong từ điển hiện chỉ mang MỘT ô mã, nên '
        'bày ra là mã thứ hai không có chỗ nào để chọn.',
    'AO':
        'Có tham số BẮT BUỘC kiểu `MovingAverageType` (chọn loại trung '
        'bình trượt), mà ô tham số hiện chỉ nhận SỐ. Cần thêm ô chọn '
        'kiểu trung bình trượt trước — ô ấy dùng được cho cả ATR, RSI, '
        'CCI, MACD, KCH.',
    'APO':
        'Có tham số BẮT BUỘC kiểu `MovingAverageType` (chọn loại trung '
        'bình trượt), mà ô tham số hiện chỉ nhận SỐ. Cần thêm ô chọn '
        'kiểu trung bình trượt trước — ô ấy dùng được cho cả ATR, RSI, '
        'CCI, MACD, KCH.',
    'ARIMA':
        'Tham số bắt buộc `intercept` kiểu bool, mà ô tham số hiện chỉ '
        'nhận SỐ. Và ARIMA cần bốn bậc mô hình — bày ra mà đặt sai bậc '
        'thì nó không nổ, chỉ ra số vô nghĩa.',
    'B':
        'Nhận HAI mã (`Symbol target, Symbol reference`) — '
        'alpha/beta/tương quan/hiệp phương sai của mã này SO VỚI mã '
        'kia. Một đại lượng trong từ điển hiện chỉ mang MỘT ô mã, nên '
        'bày ra là mã thứ hai không có chỗ nào để chọn.',
    'C':
        'Nhận HAI mã (`Symbol target, Symbol reference`) — '
        'alpha/beta/tương quan/hiệp phương sai của mã này SO VỚI mã '
        'kia. Một đại lượng trong từ điển hiện chỉ mang MỘT ô mã, nên '
        'bày ra là mã thứ hai không có chỗ nào để chọn.',
    'COV':
        'Nhận HAI mã (`Symbol target, Symbol reference`) — '
        'alpha/beta/tương quan/hiệp phương sai của mã này SO VỚI mã '
        'kia. Một đại lượng trong từ điển hiện chỉ mang MỘT ô mã, nên '
        'bày ra là mã thứ hai không có chỗ nào để chọn.',
    'D':
        'Chỉ báo của QUYỀN CHỌN (Greeks). Bộ dữ liệu miễn phí kèm LEAN '
        'không có quyền chọn, và sơ đồ chưa có khối nào nói về quyền '
        'chọn.',
    'DEM':
        'Có tham số BẮT BUỘC kiểu `MovingAverageType` (chọn loại trung '
        'bình trượt), mà ô tham số hiện chỉ nhận SỐ. Cần thêm ô chọn '
        'kiểu trung bình trượt trước — ô ấy dùng được cho cả ATR, RSI, '
        'CCI, MACD, KCH.',
    'G':
        'Chỉ báo của QUYỀN CHỌN (Greeks). Bộ dữ liệu miễn phí kèm LEAN '
        'không có quyền chọn, và sơ đồ chưa có khối nào nói về quyền '
        'chọn.',
    'IV':
        'Chỉ báo của QUYỀN CHỌN (Greeks). Bộ dữ liệu miễn phí kèm LEAN '
        'không có quyền chọn, và sơ đồ chưa có khối nào nói về quyền '
        'chọn.',
    'PPO':
        'Có tham số BẮT BUỘC kiểu `MovingAverageType` (chọn loại trung '
        'bình trượt), mà ô tham số hiện chỉ nhận SỐ. Cần thêm ô chọn '
        'kiểu trung bình trượt trước — ô ấy dùng được cho cả ATR, RSI, '
        'CCI, MACD, KCH.',
    'R':
        'Chỉ báo của QUYỀN CHỌN (Greeks). Bộ dữ liệu miễn phí kèm LEAN '
        'không có quyền chọn, và sơ đồ chưa có khối nào nói về quyền '
        'chọn.',
    'SWISS':
        'Tham số bắt buộc `SwissArmyKnifeTool` là một enum chọn bộ lọc '
        '(Gauss / Butterworth / HighPass…), mà ô tham số hiện chỉ nhận '
        'SỐ.',
    'T':
        'Chỉ báo của QUYỀN CHỌN (Greeks). Bộ dữ liệu miễn phí kèm LEAN '
        'không có quyền chọn, và sơ đồ chưa có khối nào nói về quyền '
        'chọn.',
    'V':
        'Chỉ báo của QUYỀN CHỌN (Greeks). Bộ dữ liệu miễn phí kèm LEAN '
        'không có quyền chọn, và sơ đồ chưa có khối nào nói về quyền '
        'chọn.',
    'VAR':
        'LEAN dùng CÙNG MỘT TÊN `VAR` cho HAI chỉ báo khác nhau: '
        '`Variance` (phương sai, 1 tham số) và `ValueAtRisk` (giá trị '
        'chịu rủi ro, 2 tham số). Bày một dòng «VAR» ra thì không ai '
        'biết mình đang chọn cái nào — phải tách thành hai dòng tên '
        'khác nhau trước.',
    # --- app đã khai lý do ở CHÍNH BẢNG CỦA NÓ, đừng chép lại lần nữa ---
    # `PHONG_RUI_RO_DOC` · `DAT_LENH_DOC` · `CHIA_VON_THIEU_DU_LIEU` khai `(False,
    # lý do)` cho model nào app nuôi không nổi, kèm bằng chứng đã chạy thật. Hàm
    # `_app_tu_khai()` dưới đây đọc thẳng mấy bảng ấy, nên ba model này KHÔNG có
    # dòng riêng ở đây: một lý do chép hai chỗ là hai chỗ lệch nhau về sau.
    #     MaximumSectorExposureRiskManagementModel
    #     SpreadExecutionModel
    #     SectorWeightingPortfolioConstructionModel

    # --- lớp nền, không phải món dùng được ---
    "BasePairsTradingAlphaModel":
        "Lớp NỀN cho cặp giao dịch, không tự chạy được. Món dùng được là "
        "PearsonCorrelationPairsTradingAlphaModel kế thừa nó.",
    "FundamentalUniverseSelectionModel":
        "Lớp NỀN — đòi người dùng viết hàm lọc bằng Python, trái D-11. Mấy con "
        "kế thừa nó mà KHÔNG đòi hàm lọc (QC500, EmaCross) thì đã bày.",
    "CoarseFundamentalUniverseSelectionModel":
        "Chữ ký của nó là `(Func<IEnumerable<CoarseFundamental>, "
        "IEnumerable<Symbol>> coarseSelector, …)` — tham số BẮT BUỘC là một HÀM "
        "Python người dùng tự viết. Bày ra thì ô ấy là chỗ gõ mã Python, tức app "
        "mọc ra một bộ máy tính toán thứ hai (trái D-11).",
    "FineFundamentalUniverseSelectionModel":
        "Đòi HAI hàm lọc Python (`coarseSelector` + `fineSelector`), cùng lý do "
        "với CoarseFundamental. Và bộ dữ liệu miễn phí cũng không có `fine`: thư "
        "mục `fundamental/` chỉ có `coarse/`.",
    "UniverseSelectionModel":
        "Lớp NỀN của cả họ Rổ.",
    "CustomUniverseSelectionModel":
        "Lớp NỀN — đòi người dùng viết hàm chọn mã bằng Python, trái D-11.",

    # --- «không dùng» đã là một dòng trong ô chọn của app rồi ---
    "NullAlphaModel": "Ô chọn của app đã có dòng «— không dùng —».",
    "NullPortfolioConstructionModel": "Ô chọn đã có dòng «— không dùng —».",
    "NullRiskManagementModel": "Ô chọn đã có dòng «— không dùng —».",
    "NullExecutionModel": "Ô chọn đã có dòng «— không dùng —».",
    "NullUniverseSelectionModel": "Ô chọn đã có dòng «— không dùng —».",

    # --- GỘP NHIỀU MODEL: dùng được thật, nhưng ô chọn hiện chỉ chọn MỘT ---
    "CompositeAlphaModel":
        "Gộp nhiều model phát tín hiệu thành một. Ô «Phát tín hiệu» hiện chọn "
        "MỘT model; cho chọn nhiều là một hình giao diện khác, chưa làm.",
    "CompositeUniverseSelectionModel":
        "Gộp nhiều rổ thành một. Khối Bắt đầu hiện chọn MỘT rổ; cho chọn nhiều "
        "rổ là một hình giao diện khác, chưa làm.",

    # --- cần khối «quyền chọn» mà sơ đồ chưa có ---
    "OptionChainedUniverseSelectionModel":
        "Rổ quyền chọn nối theo một rổ cổ phiếu — bộ dữ liệu miễn phí không có "
        "quyền chọn, và sơ đồ chưa có khối nào nói về quyền chọn.",

    # --- cần dữ liệu app không có ---
    "AlphaStreamsPortfolioConstructionModel":
        "Cần dữ liệu Alpha Streams trả tiền của QuantConnect. Bộ dữ liệu kèm "
        "LEAN không có, chọn vào là chạy ra rỗng.",
    "FutureUniverseSelectionModel":
        "Hợp đồng tương lai — bộ dữ liệu miễn phí không có.",
    "FuturesUniverseSelectionModel":
        "Hợp đồng tương lai — bộ dữ liệu miễn phí không có.",
    "OpenInterestFutureUniverseSelectionModel":
        "Hợp đồng tương lai — bộ dữ liệu miễn phí không có.",
    "OptionUniverseSelectionModel":
        "Quyền chọn — bộ dữ liệu miễn phí không có, và sơ đồ chưa có khối nào "
        "nói về quyền chọn.",

    # --- đòi người dùng viết Python ---
    "ScheduledUniverseSelectionModel":
        "Nhận một HÀM Python trả về danh sách mã. Bày ra thì ô ấy là chỗ gõ mã "
        "Python — trái D-11.",
    "InceptionDateUniverseSelectionModel":
        "Nhận một dict {mã: ngày niêm yết} gõ tay. Mấy rổ ETF có sẵn "
        "(LiquidETFUniverse, MetalsETFUniverse…) đều kế thừa nó và ĐÃ bày.",
    "CompositeRiskManagementModel":
        "Gộp nhiều model phòng rủi ro thành một. Ô «Phòng rủi ro» hiện chọn MỘT "
        "model; gộp nhiều cái là một tính năng giao diện khác, chưa làm.",
    "ManualUniverseSelectionModel":
        "Rổ gõ tay danh sách mã — khối Bắt đầu đã có ô gõ mã sẵn, cùng một việc.",
}

# ---------------------------------------------------------------------------
# MỐC — bản chụp của lần soát gần nhất (18/10/2026). Để cổng còn răng khi máy
# không có mã nguồn LEAN: không ai rút ngắn được bảng nào mà cổng im.
# Sửa con số ở đây CHỈ khi vừa bày thêm thật, và phải sửa TĂNG.
# ---------------------------------------------------------------------------
MOC = {
    "chi_bao": 105,
    "chia_von": 8,
    "alpha": 6,
    "ro": 10,
    "phong_rui_ro": 4,
    "dat_lenh": 3,
}


def _doc(duong):
    return io.open(duong, encoding="utf-8", errors="replace").read()


def goc_lean():
    """-> thư mục mã nguồn LEAN, hay "" nếu máy này chưa trỏ tới."""
    g = str((luu_tru.doc_cai_dat().get(chay_lean.KHOA_LEAN) or "")).strip()
    return g if g and os.path.isdir(g) else ""


#: Mấy tham số ở ĐUÔI chữ ký mà LEAN tự lo — app không bày thành ô.
DUOI_LEAN_TU_LO = ("Resolution", "Func<", "PyObject", "selector", "riskFreeRate")


def _dem_tham_so(thamso):
    """-> (bắt buộc, tổng) số tham số THẬT của một chữ ký C#.

    ⚠ PHẢI GỘT `<...>` TRƯỚC KHI CẮT THEO DẤU PHẨY. `Func<IBaseData, decimal>
    selector` có một dấu phẩy BÊN TRONG ngoặc nhọn; cắt thẳng thì nó vỡ thành
    `Func<IBaseData` và `decimal> selector`, mảnh sau không còn chữ "Func<" nên
    lọt qua bộ lọc và bị đếm như một tham số thật.

    ⚠ VÀ PHẢI PHÂN BIỆT BẮT BUỘC VỚI CÓ MẶC ĐỊNH. `ATR(symbol, period,
    MovingAverageType type = Simple, …)` có hai tham số, nhưng chỉ `period` là
    bắt buộc — nên `self.atr(sym, n)` của app là ĐÚNG, nó mượn mặc định của LEAN.
    Đòi khớp đúng TỔNG số thì bài kiểm bắt oan bảy chỉ báo đang chạy tốt.

    Hai chỗ trên đều là lỗi bản đầu của chính bài kiểm này. Hàng rào kêu oan thì
    cũng vô dụng như hàng rào không kêu — người ta tắt nó đi là xong."""
    phang = re.sub(r"<[^<>]*>", "", thamso)
    that = [t for t in phang.split(",") if t.strip()
            and not any(x in t for x in DUOI_LEAN_TU_LO)]
    return len([t for t in that if "=" not in t]), len(that)


def chi_bao_lean(goc):
    """-> {TÊN: {số tham số của từng chữ ký}} cho mọi hàm chỉ báo của QCAlgorithm.

    Đọc THẲNG chữ ký, không tra tài liệu.

    `nhieu_ma` = mấy chỉ báo nhận HAI mã (`A`, `B`, `C`, `COV`, `G` — alpha, beta,
    tương quan, hiệp phương sai): chữ ký của chúng mở đầu `(Symbol target, Symbol
    reference, …)` chứ không `(Symbol symbol, …)`."""
    p = os.path.join(goc, "Algorithm", "QCAlgorithm.Indicators.cs")
    if not os.path.isfile(p):
        return {}, set()
    src = _doc(p)
    ra, nhieu_ma = {}, set()
    for ten, dau, thamso in re.findall(
            r"^        public [A-Za-z0-9_<>\[\]]+ ([A-Z][A-Za-z0-9_]*)"
            r"\(Symbol (\w+),?([^)]*)\)", src, re.M):
        if ten in KHONG_PHAI_CHI_BAO:
            continue
        ts = thamso
        if dau != "symbol" and ts.strip().startswith("Symbol "):
            nhieu_ma.add(ten)
            ts = ts.split(",", 1)[1] if "," in ts else ""
        ra.setdefault(ten, set()).add(_dem_tham_so(ts))
    return ra, nhieu_ma


def model_lean(goc, ho):
    """-> {tên model} của một họ Framework, lần theo chuỗi kế thừa tới lớp nền.

    ⚠ PHẢI QUÉT HAI THƯ MỤC. LEAN chẻ mỗi họ làm hai chỗ, và chỗ thứ hai không
    chỉ chứa lớp nền:

        Algorithm.Framework/Execution/   Spread · StandardDeviation · VWAP
        Algorithm/Execution/             ImmediateExecutionModel  ← món hay dùng nhất

    Bản đầu bài này chỉ quét thư mục trên, nên nó kết luận app đang bày một lớp
    "LEAN không có" — trong khi `ImmediateExecutionModel` là model đặt lệnh mặc
    định của mọi ví dụ. Hàng rào chỉ đúng khi nó soi đủ chỗ.

    Quét cả `.cs` và `.py`; bỏ `bin/` vì đó là bản build, kể tên lại y hệt."""
    cha = {}
    for goc_ho in (os.path.join(goc, "Algorithm.Framework", ho),
                   os.path.join(goc, "Algorithm", ho)):
        if not os.path.isdir(goc_ho):
            continue
        for ten in sorted(os.listdir(goc_ho)):
            if not (ten.endswith(".cs") or ten.endswith(".py")):
                continue
            src = _doc(os.path.join(goc_ho, ten))
            for lop, nen in re.findall(
                    r"(?:public (?:abstract |sealed )?class|^class) "
                    r"([A-Za-z0-9_]+)\s*[:\(]\s*([A-Za-z0-9_]+)", src, re.M):
                cha.setdefault(lop, nen)
            for lop in re.findall(r"^class ([A-Za-z0-9_]+)\s*:?\s*$", src, re.M):
                cha.setdefault(lop, "")
    ra = set()
    for lop in cha:
        # Lớp NỀN tự nó, và mấy lớp `*PythonWrapper` — hạ tầng để LEAN gọi được
        # model viết bằng Python. Không ai chọn chúng từ giao diện.
        #
        # ⚠ `Composite*` và `Null*` thì KHÔNG lọc ở đây, dù chúng cũng không bày.
        # Chúng là món dùng được thật ("gộp ba model alpha lại"), chỉ là app chưa
        # có hình nào cho việc ấy — nên chỗ đúng của chúng là CO_Y_BO kèm lý do,
        # không phải một dòng lọc âm thầm trong bộ đọc. Lọc theo tên ở đây thì
        # ba tháng nữa không ai còn biết là đã bỏ cái gì.
        if lop in NEN[ho] or lop.endswith("PythonWrapper"):
            continue
        x, sau = lop, 0
        while x and sau < 12:
            if x in NEN[ho]:
                ra.add(lop)
                break
            x, sau = cha.get(x, ""), sau + 1
    return ra


def _app_tu_khai():
    """-> {tên model: lý do} app đã tự khai là nuôi không nổi, ở bảng của chính nó.

    Mấy bảng `*_DOC` của `bat_dau` khai `(nuôi được?, nó cần gì)` cho TỪNG model,
    kể cả model chưa bày — và lý do ở đó kèm bằng chứng đã chạy thật
    (`SpreadExecutionModel`: chính docstring LEAN nói không chạy trên nhịp ngày).

    Đọc thẳng chúng thay vì chép lý do sang `CO_Y_BO`: một lý do nằm hai chỗ là hai
    chỗ sẽ lệch nhau, và chẳng ai biết chỗ nào mới đúng."""
    ra = {}
    for bang in (getattr(bat_dau, "PHONG_RUI_RO_DOC", {}),
                 getattr(bat_dau, "DAT_LENH_DOC", {}),
                 getattr(bat_dau, "CHIA_VON_THIEU_DU_LIEU", {})):
        for ten, v in bang.items():
            if isinstance(v, tuple) and len(v) == 2 and not v[0]:
                ra[ten] = str(v[1])
    return ra


def ma_app(ds):
    """-> {mã} app đang bày, bỏ dòng «— không dùng —»."""
    ra = set()
    for x in ds:
        m = str(x[0] if isinstance(x, (list, tuple)) else x).strip()
        if m:
            ra.add(m)
    return ra


# ---------------------------------------------------------------------------
print("① MỐC — bảng nào cũng không được NGẮN đi so với lần soát trước")
# ---------------------------------------------------------------------------
dang_bay = {
    "chi_bao": len([d for d in hoi.BANG_DAI_LUONG.values()
                    if hoi.la_chi_bao(d["ma"])]),
    "chia_von": len(ma_app(bat_dau.CHIA_VON)),
    "alpha": len(ma_app(getattr(bat_dau, "PHAT_TIN_HIEU", ()))),
    "ro": len(bat_dau.RO),
    "phong_rui_ro": len(ma_app(bat_dau.PHONG_RUI_RO)),
    "dat_lenh": len(ma_app(bat_dau.DAT_LENH)),
}
for khoa, moc in sorted(MOC.items()):
    n = dang_bay[khoa]
    kiem(n >= moc, f"bảng «{khoa}» đang bày {n} món, mốc là {moc} — có ai rút "
                   f"ngắn bảng? Bày thêm thì sửa MOC lên, đừng sửa xuống.")
print(f"  (đang bày: {dang_bay})")

# ---------------------------------------------------------------------------
# Danh sach BO day du = khai tay o day + phan app da tu khai o bang cua no.
BO = dict(CO_Y_BO)
BO.update(_app_tu_khai())

GOC = goc_lean()
if not GOC:
    print()
    print("  " + "!" * 70)
    print("  ! KHÔNG SO ĐƯỢC VỚI LEAN — máy này chưa trỏ tới mã nguồn LEAN.")
    print("  ! Chỉ mục ① chạy. Muốn soi đủ thì mở Cài đặt > thư mục LEAN.")
    print("  " + "!" * 70)
    sys.exit(1 if loi else 0)

print()
print("② CHỈ BÁO — app bày bao nhiêu trong số LEAN cho")
# ---------------------------------------------------------------------------
cb_lean, cb_nhieu_ma = chi_bao_lean(GOC)
kiem(len(cb_lean) > 100,
     f"đọc `QCAlgorithm.Indicators.cs` chỉ ra {len(cb_lean)} chỉ báo — ít bất "
     f"thường, chắc chữ ký đổi hình và bộ đọc hụt. Soát lại `chi_bao_lean`.")

# ⚠ SO TÊN PHẢI BỎ GẠCH DƯỚI. LEAN đặt tên hàm theo PascalCase rồi sinh ra tên
# Python snake_case, và hai lối ấy KHÔNG nghịch đảo nhau: `SMA` -> `sma` -> ngược
# lại là `SMA`, đúng; nhưng `HeikinAshi` -> `heikin_ashi` -> ngược lại ra
# `HEIKIN_ASHI`, mà LEAN tên là `HeikinAshi`. Bản đầu bài này so bằng `.upper()`
# nên nó kêu đúng một cái `HeikinAshi` là "LEAN không có hàm ấy" — kêu oan, mà lần
# này lời kêu oan lại chỉ đúng chỗ từ điển ghi SAI tên (`heikinashi`). Nên: so
# không phân biệt gạch dưới, và cái gì còn lệch thì lệch thật.
_phang_lean = {k.replace("_", "").upper(): k for k in cb_lean}
cb_app = {}          # TÊN LEAN -> dòng từ điển
for d in hoi.BANG_DAI_LUONG.values():
    m = re.match(r"self\.([a-z0-9_]+)\(", str(d.get("lean", "")))
    if m and hoi.la_chi_bao(d["ma"]):
        k = m.group(1).replace("_", "").upper()
        cb_app[_phang_lean.get(k, m.group(1).upper())] = d

la = sorted(t for t in cb_app if t not in cb_lean)
kiem(not la, f"app khai chỉ báo mà LEAN KHÔNG có hàm ấy: {', '.join(la)} — "
             f"ô `lean` đang bịa tên, backtest sẽ nổ lúc chạy.")

# Số tham số phải khớp MỘT chữ ký thật. Lệch là `self.bb(sym, n)` trong khi LEAN
# đòi `BB(symbol, period, k)` — sinh ra mã chạy là nổ, mà từ điển nhìn vẫn sạch.
for ten, d in sorted(cb_app.items()):
    if ten not in cb_lean:
        continue
    n = len(d.get("tham_so") or [])
    vua = [f"{a}–{b}" for a, b in sorted(cb_lean[ten])]
    kiem(any(a <= n <= b for a, b in cb_lean[ten]),
         f"chỉ báo «{d['ma']}» khai {n} tham số, LEAN nhận {' hoặc '.join(vua)} "
         f"— `{d['lean']}` sẽ nổ lúc chạy.")

thieu_cb = sorted(set(cb_lean) - set(cb_app) - set(BO))
print(f"  LEAN {len(cb_lean)} · app bày {len(cb_app)} · "
      f"cố ý bỏ {len(set(cb_lean) & set(BO))} · THIẾU {len(thieu_cb)}")
if thieu_cb:
    print(f"     {' '.join(thieu_cb)}")
kiem(not thieu_cb,
     f"{len(thieu_cb)} chỉ báo LEAN có mà app không bày và cũng không khai vào "
     f"CO_Y_BO. Bày ra, hoặc viết lý do bỏ.")

print()
print("③ NĂM BẢNG FRAMEWORK — model LEAN đã làm xong, app có ô để chọn chưa")
# ---------------------------------------------------------------------------
BANG = [
    ("Alphas", "Phát tín hiệu", ma_app(getattr(bat_dau, "PHAT_TIN_HIEU", ()))),
    ("Portfolio", "Chia vốn", ma_app(bat_dau.CHIA_VON)),
    ("Risk", "Phòng rủi ro", ma_app(bat_dau.PHONG_RUI_RO)),
    ("Execution", "Đặt lệnh", ma_app(bat_dau.DAT_LENH)),
    ("Selection", "Rổ", {r[2] for r in bat_dau.RO}),
]
for ho, nhan, bay in BANG:
    co = model_lean(GOC, ho)
    kiem(bool(co), f"không đọc ra model nào trong `Algorithm.Framework/{ho}` — "
                   f"bộ đọc hụt, không phải LEAN rỗng.")
    la = sorted(bay - co)
    kiem(not la, f"bảng «{nhan}» bày {', '.join(la)} mà LEAN không có lớp ấy.")
    thieu = sorted(co - bay - set(BO))
    print(f"  {nhan:<14} LEAN {len(co):>3} · app bày {len(bay & co):>3} · "
          f"cố ý bỏ {len(co & set(BO)):>2} · THIẾU {len(thieu)}")
    for t in thieu:
        print(f"       – {t}")
    kiem(not thieu,
         f"bảng «{nhan}» thiếu {len(thieu)} model LEAN đã làm xong. Bày ra, "
         f"hoặc khai vào CO_Y_BO kèm lý do.")

print()
print("④ MẤY MẶT KHÁC CỦA LEAN — không riêng năm bảng Framework")
# ---------------------------------------------------------------------------
# ⚠ VÌ SAO CÓ MỤC NÀY. Sáng 18/10 tôi đếm sáu bảng (chỉ báo + năm bảng Framework)
# rồi kết luận «app đã bày hết LEAN». Sai CÁCH ĐO: sáu bảng ấy là đúng những chỗ tôi
# tình cờ nhìn vào. Đếm thêm thì ra ngay `date_rules` 4/11 và `time_rules` 3/6 —
# cùng một bệnh, ở một bảng tôi chưa nghĩ tới. Nên mục này đếm TỪNG MẶT, và mỗi mặt
# lấy danh sách THẲNG từ mã nguồn.


def _ham_lean(mau, *duong):
    return sorted(set(re.findall(mau, _doc(os.path.join(GOC, *duong)))))


def _snake(x):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", x).lower()


def _mat(nhan, co, bay, bo):
    thieu = [x for x in co if x not in bay and x not in bo]
    print(f"  {nhan:<34} LEAN {len(co):>3} · app bày {len(set(co) & bay):>3} · "
          f"cố ý bỏ {len(set(co) & set(bo)):>2} · THIẾU {len(thieu)}")
    for t in thieu:
        print(f"       – {t}")
    kiem(not thieu, f"{nhan}: thiếu {thieu} — bày ra, hoặc khai lý do bỏ.")


#: Cố ý bỏ ở mấy mặt này, mỗi cái một lý do.
BO_MAT = {
    "On": "`date_rules.on(...)` nhận một DANH SÁCH NGÀY cụ thể («chạy đúng ba "
          "ngày này»), không phải một nhịp lặp đều — nó cần một ô kiểu khác (nhập "
          "danh sách ngày), chưa làm.",
    "Every": "`date_rules.every(...)` nhận danh sách THỨ («thứ Hai và thứ Tư») và "
             "`time_rules.every(...)` nhận một khoảng lặp trong ngày. Cả hai cần ô "
             "chọn-nhiều, chưa làm.",
}

# ① QUY TẮC NGÀY  ② QUY TẮC GIỜ — bảng `NHIP` × `QUY_TAC_GIO`
_ngay_lean = _ham_lean(r"public IDateRule ([A-Za-z]+)\(",
                       "Common", "Scheduling", "DateRules.cs")
_gio_lean = _ham_lean(r"public ITimeRule ([A-Za-z]+)\(",
                      "Common", "Scheduling", "TimeRules.cs")
_ngay_app = {x for x in _ngay_lean
             if any(f"date_rules.{_snake(x)}(" in (n[3] or "")
                    for n in bat_dau.NHIP)}
_gio_app = {x for x in _gio_lean
            if any(f"time_rules.{_snake(x)}(" in (g[2] or "")
                   for g in bat_dau.QUY_TAC_GIO)}
_mat("quy tắc NGÀY · date_rules", _ngay_lean, _ngay_app, BO_MAT)
_mat("quy tắc GIỜ · time_rules", _gio_lean, _gio_app, BO_MAT)

# ③ ĐỘ PHÂN GIẢI · ④ CHUẨN HOÁ GIÁ — hai enum của `Common/Global.cs`


def _enum(ten):
    src = _doc(os.path.join(GOC, "Common", "Global.cs"))
    m = re.search(r"public enum %s\b" % ten, src)
    if not m:
        return []
    than = src[m.end():]
    than = than[:than.index("\n    }")] if "\n    }" in than else than
    return [x for x in re.findall(r"^\s{8}([A-Z][A-Za-z0-9]*)", than, re.M)]


_res = _enum("Resolution")
_mat("độ phân giải · Resolution", _res,
     {m.title() for m, _n in bat_dau._O_DO_PHAN_GIAI["chon"]}, {})

_dnm = _enum("DataNormalizationMode")
_dnm_app = {m for m in _dnm
            if any(x == re.sub(r"(?<!^)(?=[A-Z])", "_", m).upper()
                   for x, _n in bat_dau.CHUAN_HOA_GIA)}
_mat("chuẩn hoá giá · DataNormalizationMode", _dnm, _dnm_app, {})

# ⑤ LOẠI TÀI SẢN · ⑥ PHÍ · ⑦ TRƯỢT GIÁ
BO_MAT.update({
    "Base": "Lớp NỀN của mọi loại tài sản, không phải một loại để chọn.",
    "Commodity": "LEAN khai enum này mà KHÔNG có `AddCommodity` — không có cửa nào "
                 "để thêm nó. Hàng hoá thì vào bằng CFD hay hợp đồng tương lai.",
    "Option": "Quyền chọn cần khối riêng (chuỗi quyền chọn, ngày đáo hạn, giá thực "
              "hiện) và bộ dữ liệu miễn phí không có. Chưa làm.",
    "FutureOption": "Quyền chọn trên HĐ tương lai — như Option, và còn xa hơn.",
    "IndexOption": "Quyền chọn trên chỉ số — như Option.",
    "CryptoFuture": "HĐ tương lai tiền mã hoá — bộ dữ liệu miễn phí không có.",
})
_ts = _enum("SecurityType")
_mat("loại tài sản · SecurityType", _ts,
     {m.title().replace("_", "") for m, _n, _h in bat_dau.LOAI_TAI_SAN}, BO_MAT)


def _lop_duoi(thu_muc, duoi):
    d = os.path.join(GOC, *thu_muc.split("/"))
    ra = set()
    for ten in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if ten.endswith(".cs"):
            ra |= {x for x in re.findall(
                r"public (?:abstract |sealed )?class ([A-Za-z0-9_]+)",
                _doc(os.path.join(d, ten))) if x.endswith(duoi)}
    return sorted(ra)


# ⚠ KHAI LÝ DO THEO HỌ, VÀ KHAI BẰNG CÁCH LOẠI TRỪ. Bản đầu tôi dò tên model phí
# xem có khớp một tên trong `BrokerageName` không — bắt được 4 trong 30, vì LEAN đặt
# tên không khớp enum (`GDAX` là Coinbase cũ, `India` là một THỊ TRƯỜNG chứ không
# phải sàn, `dYdX` viết hoa kiểu khác). Dò tên là một hàng rào có lỗ ở đúng chỗ tên
# lệch.
#
# Luật đúng ngắn hơn hẳn: trong họ phí của LEAN, ĐÚNG MỘT model không gắn với sàn
# nào — `ConstantFeeModel` — cộng lớp nền `FeeModel`. Mọi cái còn lại là phí RIÊNG
# của một sàn, và ô «Sàn» chọn sàn là LEAN tự lấy đúng model phí ấy.
_phi_lean = _lop_duoi("Common/Orders/Fees", "FeeModel")
_KHONG_THEO_SAN = {"ConstantFeeModel", "FeeModel"}
BO_MAT.setdefault("FeeModel", "Lớp NỀN của họ phí, không phải một model để chọn.")
for _x in _phi_lean:
    if _x in _KHONG_THEO_SAN or _x in {m for m, *_ in bat_dau.PHI if m}:
        continue
    BO_MAT.setdefault(
        _x, f"Phí RIÊNG của một sàn ({_x[:-len('FeeModel')]}) — ô «Sàn» chọn sàn là "
            f"LEAN tự lấy đúng model phí ấy. Bày lại ở ô «Phí» là bày hai cách nói "
            f"một thứ, và còn mời người dùng gắn phí sàn này cho sơ đồ sàn khác.")
_mat("model PHÍ · set_fee_model", _phi_lean,
     {m for m, *_ in bat_dau.PHI if m}, BO_MAT)

_truot_lean = _lop_duoi("Common/Orders/Slippage", "SlippageModel")
BO_MAT.update({k: v[1] for k, v in bat_dau.PHI_TRUOT_DOC.items() if not v[0]})
_mat("model TRƯỢT GIÁ · set_slippage_model", _truot_lean,
     {m for m, *_ in bat_dau.TRUOT_GIA if m}, BO_MAT)

print()
print("⑤ DANH SÁCH BỎ không được phép MỤC")
# ---------------------------------------------------------------------------
# Một dòng CO_Y_BO mục theo hai lối: LEAN bỏ món ấy đi (thì dòng này thành rác), hay
# app đã bày nó rồi (thì dòng này nói dối). Cả hai đều phải kêu.
tat_ca = set(cb_lean)
for ho, _nhan, _bay in BANG:
    tat_ca |= model_lean(GOC, ho)
# Mấy lớp NỀN không với tới lớp nền của chính nó nên `model_lean` không kể, mà
# CO_Y_BO vẫn phải được phép nói về chúng.
tat_ca |= set(NEN["Selection"]) | {"CustomUniverseSelectionModel"}

for ten, ly_do in sorted(BO.items()):
    kiem(len(str(ly_do).strip()) >= 20,
         f"CO_Y_BO[{ten}] không có lý do tử tế — một câu nói rõ vì sao bỏ.")
    kiem(ten in tat_ca,
         f"CO_Y_BO kể tên «{ten}» mà LEAN không còn có. Xoá dòng ấy đi.")

da_bay = set(cb_app)
for _ho, _nhan, bay in BANG:
    da_bay |= bay
cham = sorted(set(BO) & da_bay)
kiem(not cham, f"CO_Y_BO bảo bỏ {', '.join(cham)} mà app ĐÃ bày — hai chỗ nói "
               f"trái nhau, xoá dòng trong CO_Y_BO.")

# ---------------------------------------------------------------------------
print()
print("=" * 70)
if loi:
    print(f"  ✘ {len(loi)} chỗ hỏng")
    sys.exit(1)
print("  ✔ app đã bày HẾT những gì LEAN cho (trừ phần khai rõ lý do bỏ)")
sys.exit(0)
