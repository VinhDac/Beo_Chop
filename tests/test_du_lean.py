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
    # --- lớp nền, không phải món dùng được ---
    "BasePairsTradingAlphaModel":
        "Lớp NỀN cho cặp giao dịch, không tự chạy được. Món dùng được là "
        "PearsonCorrelationPairsTradingAlphaModel kế thừa nó.",
    "FundamentalUniverseSelectionModel":
        "Lớp NỀN — đòi người dùng viết hàm lọc bằng Python, trái D-11. Mấy con "
        "kế thừa nó (QC500, EmaCross, Fine, Coarse) mới là món bày được.",
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
    "chi_bao": 21,
    "chia_von": 2,
    "alpha": 0,
    "ro": 9,
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

cb_app = {}          # TÊN LEAN -> dòng từ điển
for d in hoi.BANG_DAI_LUONG.values():
    m = re.match(r"self\.([a-z0-9_]+)\(", str(d.get("lean", "")))
    if m and hoi.la_chi_bao(d["ma"]):
        cb_app[m.group(1).upper()] = d

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

thieu_cb = sorted(set(cb_lean) - set(cb_app) - set(CO_Y_BO))
print(f"  LEAN {len(cb_lean)} · app bày {len(cb_app)} · "
      f"cố ý bỏ {len(set(cb_lean) & set(CO_Y_BO))} · THIẾU {len(thieu_cb)}")
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
    thieu = sorted(co - bay - set(CO_Y_BO))
    print(f"  {nhan:<14} LEAN {len(co):>3} · app bày {len(bay & co):>3} · "
          f"cố ý bỏ {len(co & set(CO_Y_BO)):>2} · THIẾU {len(thieu)}")
    for t in thieu:
        print(f"       – {t}")
    kiem(not thieu,
         f"bảng «{nhan}» thiếu {len(thieu)} model LEAN đã làm xong. Bày ra, "
         f"hoặc khai vào CO_Y_BO kèm lý do.")

print()
print("④ DANH SÁCH BỎ không được phép MỤC")
# ---------------------------------------------------------------------------
# Một dòng CO_Y_BO mục theo hai lối: LEAN bỏ món ấy đi (thì dòng này thành rác), hay
# app đã bày nó rồi (thì dòng này nói dối). Cả hai đều phải kêu.
tat_ca = set(cb_lean)
for ho, _nhan, _bay in BANG:
    tat_ca |= model_lean(GOC, ho)
# Mấy lớp NỀN không với tới lớp nền của chính nó nên `model_lean` không kể, mà
# CO_Y_BO vẫn phải được phép nói về chúng.
tat_ca |= set(NEN["Selection"]) | {"CustomUniverseSelectionModel"}

for ten, ly_do in sorted(CO_Y_BO.items()):
    kiem(len(str(ly_do).strip()) >= 20,
         f"CO_Y_BO[{ten}] không có lý do tử tế — một câu nói rõ vì sao bỏ.")
    kiem(ten in tat_ca,
         f"CO_Y_BO kể tên «{ten}» mà LEAN không còn có. Xoá dòng ấy đi.")

da_bay = set(cb_app)
for _ho, _nhan, bay in BANG:
    da_bay |= bay
cham = sorted(set(CO_Y_BO) & da_bay)
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
