"""BỘ SINH MÃ — sơ đồ thành một thuật toán LEAN Python chạy được.

LỜI HỨA D-11, chỗ nó thành sự thật kiểm được: file này **không tự nghĩ ra một câu LEAN
nào**. Mọi câu nó viết đều lấy từ ô `lean` của ba từ điển (`bat_dau.py`, `hoi.py`,
`lam.py`), chỉ thay chỗ trống bằng giá trị người chơi gõ. Muốn thêm một chỉ báo hay một
loại lệnh thì sửa từ điển, không sửa file này.

BA THỨ NÓ TỰ LO, không hỏi người dùng — và cả ba đều là đếm trên SƠ ĐỒ CỦA CHÍNH TA,
không phải tính trên dữ liệu thị trường:

  1. **Nâng chỉ báo lên `initialize`.** `self.rsi(sym, 14)` phải khai một lần ở đó rồi
     LEAN tự cập nhật mỗi nến — *"We never need to 'update' our indicators with the
     data, the engine takes care of this for us"* (`MovingAverageCrossAlgorithm`).
     Hai khối cùng viết RSI(14) trên một mã thì dùng CHUNG một chỉ báo.
  2. **Làm nóng.** `set_warm_up(chu kỳ dài nhất)`. Không có nó thì N nến đầu cỗ máy
     quyết định trên số rác — đúng cái mà mọi chiến lược thật phải tự chặn bằng
     `if not x.is_ready: return`.
  3. **Vòng lặp nhiều mã.** Ô *nhịp* + ô *mã* của khối Bắt đầu đã khai trọn vòng rồi.

HÌNH DẠNG MÃ SINH RA — cố ý dễ đọc, vì cả dự án dựng trên một câu: *cái script và cái
ta vẽ phải ra cùng một thứ, chỉ khác cách trình bày*. Nên không sinh máy trạng thái,
không sinh bảng nhảy: khối Hỏi thành `if`, nhánh thành `if/elif`, khối Làm thành đúng
một câu gọi. Người đọc file phải nhận ra sơ đồ của mình trong đó.

CHƯA SINH ĐƯỢC — báo rõ chứ không đoán:
  · **Vòng lặp** (khối Quay về, đường ↻). Trong một nến thì dữ liệu không đổi, nên
    chạy lại một đoạn sẽ cho đúng kết quả cũ; sinh bừa một `for` là sinh ra thứ sơ đồ
    không nói. Vòng DUY NHẤT có nghĩa trong giao dịch — mỗi nến, mỗi mã — thì khối
    Bắt đầu đã lo.
  · **Mã lạ**: điều kiện trỏ tới một mã chưa khai ở khối Bắt đầu. Tự `add_*` thêm là
    tự quyết hộ người chơi một đăng ký dữ liệu.
"""
import re
import unicodedata

from . import bat_dau
from . import core
from . import hoi
from . import lam

#: Trần số khối sinh ra trong một lượt — chốt chặn, như `core.MAX_PROCESS_STEPS`.
MAX_KHOI = 2000

TAB = "    "


def _bo_dau(s):
    """Bỏ dấu tiếng Việt -> chữ ASCII. Tên lớp Python không nên mang dấu."""
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def ten_lop(ten):
    """Tên Strategy -> tên lớp Python hợp lệ. "Cỗ máy vàng" -> "CoMayVang"."""
    chu = re.sub(r"[^0-9a-zA-Z]+", " ", _bo_dau(str(ten or ""))).split()
    ra = "".join(w[:1].upper() + w[1:] for w in chu)
    if not ra or ra[0].isdigit():
        ra = "CoMay" + ra
    return ra


def _lit(v):
    """Một giá trị -> hằng Python. Chuỗi thì `repr` để dấu nháy tự lo."""
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (int, float)):
        return repr(v)
    return repr("" if v is None else str(v))


class _Kho:
    """Kho CHỈ BÁO — gom hết chỉ báo của cả sơ đồ, mỗi cái đúng MỘT lần.

    Hai khối cùng viết RSI(14) phải dùng chung một chỉ báo: đăng ký hai lần là LEAN
    nuôi hai bộ đếm y hệt nhau, tốn công mà chẳng khác gì."""

    def __init__(self):
        self.ds = {}          # khoá -> (dòng tạo, dòng đăng ký)
        self.chu_ky = [0]     # chu kỳ dài nhất, để tính làm nóng

    def khoa(self, dl, ve):
        ts = ve.get("tham_so") or {}
        duoi = "_".join(str(ts[t["ten"]]) for t in dl["tham_so"])
        return f"{dl['ma']}_{duoi}" if duoi else dl["ma"]

    def them(self, dl, ve, res):
        """Ghi nhận một chỉ báo. -> khoá của nó trong `self._cb[sym]`."""
        k = self.khoa(dl, ve)
        if k not in self.ds:
            ts = ve.get("tham_so") or {}
            cau = _thay(dl["lean"], {"sym": "sym", **{t["ten"]: str(ts[t["ten"]])
                                                      for t in dl["tham_so"]}})
            dk = (dl.get("lean_dk") or "").format(bien="_cb", res=res)
            self.ds[k] = (cau, _thay(dk, {"sym": "sym"}) if dk else "")
            for t in dl["tham_so"]:
                try:
                    self.chu_ky.append(int(ts[t["ten"]]))
                except (TypeError, ValueError, KeyError):
                    pass
        return k


def _thay(mau, gia_tri):
    """Thay `sym`, `n`, `k`… trong một mẫu `lean` bằng giá trị thật.

    Dùng ranh giới TỪ và thay MỘT LƯỢT: thay lần lượt thì giá trị vừa chèn vào có thể
    chứa đúng cái tên sắp thay tới (mã "N" chẳng hạn), và chuỗi hỏng mà không ai thấy."""
    if not mau:
        return ""
    ten = sorted(gia_tri, key=len, reverse=True)
    return re.sub(r"\b(" + "|".join(re.escape(t) for t in ten) + r")\b",
                  lambda m: gia_tri[m.group(1)], mau)


class _Nc:
    """Ngữ cảnh một lượt sinh: bảng khối, dây, kho chỉ báo, danh sách vấn đề."""

    def __init__(self, steps, edges):
        self.theo_id, self.ke = core.flow_map(steps, edges)
        self.kho = _Kho()
        self.van_de = []
        self.da = set()
        self.ma_khai = {}      # ticker -> True, lấy từ khối Bắt đầu
        self.res = "Resolution.DAILY"
        #: True = chạy MỘT LƯỢT cho cả rổ (chia danh mục), nên KHÔNG có biến `sym`.
        self.ca_danh_muc = False
        #: Mục RỔ đang chọn, hay None nếu khối Bắt đầu gõ mã sẵn. Khác nhau ở ba chỗ:
        #: khai mã, khai chỉ báo, và `self._ma` lấy từ đâu.
        self.ro = None
        self.thu_tu = {}
        self.dem = 0

    def loi(self, sid, msg, sev="error"):
        core._loi(self.van_de, sev, sid, msg)


# ---------------------------------------------------------------------------
# Điều kiện -> biểu thức Python
# ---------------------------------------------------------------------------

def _sym_py(nc, ve, sid):
    """Mã của một vế hay một hành động -> biểu thức Python. Trống = mã đang xét.

    ⚠ Khi khối Bắt đầu chạy cho CẢ RỔ thì KHÔNG có mã đang xét — không có biến `sym`
    nào trong hàm sinh ra. Để trống lúc ấy là sinh ra mã không chạy được, nên báo."""
    m = str((ve or {}).get("ma") or "").strip().upper()
    if not m:
        if nc.ca_danh_muc:
            nc.loi(sid, "Khối Bắt đầu chạy MỘT LƯỢT cho cả rổ nên không có «mã đang "
                        "xét» — khối này phải gõ rõ tên mã.")
        return "sym"
    if m not in nc.ma_khai:
        # RỔ ĐỘNG thì KHÔNG mã nào gõ được tên: rổ gồm những mã nào là chuyện LEAN
        # quyết lại mỗi ngày, app không có danh sách ấy để mà đối chiếu. Câu báo lỗi
        # phải nói đúng chuyện đó, chứ bảo "thêm mã ấy vào khối Bắt đầu" là bảo
        # người chơi làm một việc mà hộp thoại không có chỗ để làm.
        if nc.ro:
            nc.loi(sid, f'Khối Bắt đầu chạy trên một RỔ nên không khối nào gõ được '
                        f'tên mã — rổ gồm những mã nào là chuyện LEAN quyết lại mỗi '
                        f'ngày. Bỏ mã "{m}" khỏi khối này để nó chạy cho MÃ ĐANG '
                        f"XÉT, hoặc đổi khối Bắt đầu về gõ mã sẵn.")
        else:
            nc.loi(sid, f'Điều kiện trỏ tới mã "{m}" mà khối Bắt đầu chưa khai nó. '
                        f"Thêm mã ấy vào khối Bắt đầu, hoặc bỏ nó khỏi điều kiện.")
        return "sym"
    return f"self._ten[{m!r}]"


def _ve_py(nc, ve, sid):
    """Một VẾ của điều kiện -> biểu thức Python."""
    if not isinstance(ve, dict):
        return "0"
    if "ma_dl" not in ve:
        return _lit(ve.get("so", 0))
    dl = hoi.dai_luong(ve["ma_dl"])
    if not dl:
        nc.loi(sid, f'Không có đại lượng "{ve["ma_dl"]}".')
        return "0"
    sym = _sym_py(nc, ve, sid)
    if hoi.la_chi_bao(ve["ma_dl"]):
        k = nc.kho.them(dl, ve, nc.res)
        duong = f".{ve['duong']}" if ve.get("duong") else ""
        return f"self._cb[{sym}][{k!r}]{duong}.current.value"
    ts = {t["ten"]: str((ve.get("tham_so") or {}).get(t["ten"], t["mac_dinh"]))
          for t in dl["tham_so"]}
    return _thay(dl["lean"], {"sym": sym, **ts})


def _dieu_kien_py(nc, step):
    """Khối HỎI -> (biểu thức Python, chữ mô tả để điền vào `tag`)."""
    ds = step.get("dieu_kien") or []
    if not ds:
        # Cổng rỗng LUÔN khớp — `soat_khoi_hoi` đã cảnh báo, ở đây sinh đúng như thế.
        return "True", "không điều kiện"
    ve = []
    for dk in ds:
        trai = _ve_py(nc, dk.get("trai"), step["id"])
        phep = dk.get("phep")
        dl = hoi.dai_luong((dk.get("trai") or {}).get("ma_dl"))
        if dl and dl["kieu"] == hoi.KIEU_CO_KHONG:
            ve.append(f"not ({trai})" if phep == "khong" else f"({trai})")
        else:
            ve.append(f"({trai} {phep} {_ve_py(nc, dk.get('phai'), step['id'])})")
    # Chữ mô tả phải nói CẢ cổng, không phải mỗi dòng đầu: một cổng hai điều kiện mà
    # `tag` chỉ ghi một dòng thì đọc nhật ký lệnh sẽ tưởng nó khớp vì lý do khác.
    return " and ".join(ve), " và ".join(core.mo_ta_dieu_kien(dk) for dk in ds)


# ---------------------------------------------------------------------------
# Hành động -> câu lệnh Python
# ---------------------------------------------------------------------------

def _lam_py(nc, a, sid, mach):
    """Một hành động -> MỘT dòng Python, lấy thẳng từ mẫu `lean` của từ điển."""
    t = a.get("type")
    d = lam.LOAI_LAM.get(t)
    if not d:
        nc.loi(sid, f'Chưa sinh được khối loại "{t}".')
        return []
    mau = lam.ham_lean(t, a)
    # Mã lấy từ ô `ma` của CHÍNH khối ấy — thiếu chỗ này thì mọi hành động đều viết
    # `set_holdings(sym, …)` và không chiến thuật chia danh mục nào diễn đạt được.
    gt = {"sym": _sym_py(nc, a, sid) if d["can_ma"] else "sym"}
    for o in lam.o_cua(t, a):
        gt[o["ten"]] = _lit(core.o_lam(a, o["ten"]))

    # Ô `tag` để trống thì ĐIỀN HỘ: số khối + điều kiện vừa khớp. Đó là lời hứa D-11
    # "chữ vì sao do chính đoạn code tự ghi", và LEAN nhận sẵn tham số này.
    if "tag" in gt and not str(core.o_lam(a, "tag") or "").strip():
        gt["tag"] = _lit(_chu_tag(nc, sid, mach))
    if t == lam.LAM_GHI_CHU and not str(core.o_lam(a, "cau") or "").strip():
        gt["cau"] = _lit(_chu_tag(nc, sid, mach))
    if t == lam.LAM_VE_BANG:
        gt["gia_tri"] = _ve_py(nc, a.get("gia_tri"), sid)
    try:
        return [mau.format(**gt)]
    except KeyError as e:
        nc.loi(sid, f'Mẫu LEAN của khối cần ô {e} mà khối không có.')
        return []


def _chu_tag(nc, sid, mach):
    """Chữ đi theo lệnh sang LEAN: số khối + chuỗi điều kiện đã khớp để tới đây."""
    so = nc.thu_tu.get(sid) or "?"
    return f"[{so}] " + (" · ".join(mach) if mach else "không điều kiện")


# ---------------------------------------------------------------------------
# Đồ thị -> luồng điều khiển
# ---------------------------------------------------------------------------

def _chuoi(nc, cur, dung_tai, sau, mach):
    """Sinh một CHUỖI khối từ `cur`, dừng ở `dung_tai`. -> [dòng] (chưa thụt lề)."""
    ra = []
    for _ in range(MAX_KHOI):
        if not cur or cur == dung_tai:
            return ra
        if cur in nc.da:
            nc.loi(cur, "Sơ đồ có VÒNG LẶP — chưa sinh mã được. Trong một nến thì dữ "
                        "liệu không đổi, nên chạy lại một đoạn chỉ cho đúng kết quả "
                        "cũ. Vòng «mỗi nến, mỗi mã» thì khối Bắt đầu đã lo.")
            return ra
        nc.da.add(cur)
        st = nc.theo_id.get(cur)
        if st is None:
            return ra
        nhanh = list(nc.ke.get(cur) or [])

        if st.get("type") == core.QUAY_VE:
            nc.loi(cur, "Khối QUAY VỀ — chưa sinh mã được (xem đầu `sinh_ma.py`).")
            return ra

        # ---- khối HỎI: điều kiện BAO phần còn lại của nhánh -------------------
        if hoi.la_loai_hoi(st.get("type")):
            dk, mo_ta = _dieu_kien_py(nc, st)
            ra.append(f"# {nc.thu_tu.get(cur, '?')} · {core.step_title(st)}")
            ben_trong = _toa(nc, cur, nhanh, dung_tai, sau, mach + [mo_ta])
            ra.append(f"if {dk}:")
            ra += [TAB + d for d in (ben_trong or ["pass"])]
            return ra

        # ---- khối LÀM / NHÓM --------------------------------------------------
        ra.append(f"# {nc.thu_tu.get(cur, '?')} · {core.step_title(st)}")
        # `hanh_dong_cua` chỉ trả hành động BÊN TRONG một Nhóm; khối lẻ thì CHÍNH NÓ
        # là hành động. Quên chỗ này là mọi khối Làm sinh ra một dòng `pass`.
        cau = []
        for a in (core.hanh_dong_cua(st) if core.is_group_step(st) else [st]):
            cau += _lam_py(nc, a, cur, mach)
        ra += cau or ["pass"]

        if len(nhanh) > 1:
            ra += _toa(nc, cur, nhanh, dung_tai, sau, mach)
            return ra
        cur = nhanh[0] if nhanh else None
    nc.loi(cur, "Sơ đồ quá dài — dừng ở đây để khỏi chạy mãi.")
    return ra


def _toa(nc, cur, nhanh, dung_tai, sau, mach):
    """Toả ra nhiều nhánh từ `cur`. -> [dòng].

    Các nhánh được thử LẦN LƯỢT, nhánh đầu khớp thì thôi — đúng ngữ nghĩa `is_branch_
    gate` đã chốt (*"ở điểm rẽ các nhánh được thử lần lượt, nên nhánh trượt phải LÙI
    LẠI ĐƯỢC"*). Nên `if / elif`, không phải mấy câu `if` rời."""
    if not nhanh:
        return []
    if len(nhanh) == 1:
        return _chuoi(nc, nhanh[0], dung_tai, sau, mach)

    gop = core.diem_gop(cur, nc.ke, nc.da)
    if gop == dung_tai:
        gop = dung_tai
    ra = []
    co_cua_chot = True            # mọi làn đều có cổng -> cần `else: return`
    for i, head in enumerate(nhanh):
        st = nc.theo_id.get(head)
        if st is None:
            continue
        if hoi.la_loai_hoi(st.get("type")):
            nc.da.add(head)
            dk, mo_ta = _dieu_kien_py(nc, st)
            than = _toa(nc, head, list(nc.ke.get(head) or []), gop or dung_tai, sau,
                        mach + [mo_ta])
            ra.append(f"{'if' if not ra else 'elif'} {dk}:"
                      f"  # {nc.thu_tu.get(head, '?')} · {core.step_title(st)}")
            ra += [TAB + d for d in (than or ["pass"])]
        else:
            # Làn KHÔNG có cổng thì nó luôn chạy — tức là nhánh mặc định, và mọi làn
            # xếp sau nó không bao giờ tới lượt.
            co_cua_chot = False
            than = _chuoi(nc, head, gop or dung_tai, sau, mach)
            if not ra:
                ra += than or ["pass"]
            else:
                ra.append("else:")
                ra += [TAB + d for d in (than or ["pass"])]
            if i < len(nhanh) - 1:
                nc.loi(head, f'Nhánh "{core.step_title(st)}" không có cổng nên nó luôn '
                             f"chạy — {len(nhanh) - i - 1} nhánh xếp sau nó không bao "
                             f"giờ tới lượt.", "warning")
            break
    if gop and gop != dung_tai:
        if co_cua_chot:
            # Không làn nào khớp thì hết lượt — chứ không rơi xuống chỗ gộp.
            ra.append("else:")
            ra.append(TAB + "return")
        ra += _chuoi(nc, gop, dung_tai, sau, mach)
    return ra


# ---------------------------------------------------------------------------
# initialize
# ---------------------------------------------------------------------------

def _khai_ro(nc, gt_ma):
    """Ô `ma` là một RỔ -> mấy dòng khai rổ trong `initialize`. -> [dòng].

    ⚠ `universe_settings.resolution` phải đứng TRƯỚC `set_universe_selection`: model
    nhận `universe_settings` làm tham số, nên nó chụp lấy giá trị ở ngay lúc dựng.
    Đặt sau thì rổ lặng lẽ chạy bằng độ phân giải MẶC ĐỊNH của LEAN (phút) trong khi
    sơ đồ nói nến ngày — và `self.sma(sym, 200)` thành 200 PHÚT. Đã dò bằng backtest
    thật, không phải suy ra.

    KHÔNG có dòng `add_*` nào ở nhánh này, và đó là cả điểm: rổ gồm mã nào thì LEAN
    quyết lại mỗi ngày. Nên `self._ma` cũng không khai được ở đây — xem `_ghep`."""
    ra = ["# RỔ ĐỘNG: không gõ mã nào, LEAN tự quyết hôm nay rổ gồm những gì.",
          f"self.universe_settings.resolution = {nc.res}"]
    lop = nc.ro[2]
    if nc.ro[0] != "etf":
        ra.append(f"self.set_universe_selection({lop}())")
        return ra

    ma_etf = str(bat_dau.gt_ro(gt_ma, "ma_etf") or "").strip().upper()
    lay = core._f(bat_dau.gt_ro(gt_ma, "lay")) or 0
    if lay > 0:
        ra.append(f"self.set_universe_selection({lop}({ma_etf!r}, "
                  f"self.universe_settings, self._loc_ro))")
    else:
        ra.append(f"self.set_universe_selection({lop}({ma_etf!r}, "
                  f"self.universe_settings))")
    return ra


def _ham_loc_ro(nc, st):
    """Hàm lọc rổ ETF theo trọng số -> [dòng] của một phương thức, hay [].

    THÂN HÀM LẤY TỪ TỪ ĐIỂN (`bat_dau.LOC_TRONG_SO`), đúng luật D-11 — một hàm lọc
    cũng là mã LEAN, nên nó không được sinh ra ở đây. Chỗ trống duy nhất là `{lay}`."""
    if not nc.ro or nc.ro[0] != "etf":
        return []
    gt_ma = core.o_bat_dau(st, "ma")
    lay = int(core._f(bat_dau.gt_ro(gt_ma, "lay")) or 0)
    if lay <= 0:
        return []
    return ["def _loc_ro(self, ds):",
            TAB + '"""Rổ ETF -> mấy mã NẶNG nhất. `weight` là trường có thật của',
            TAB + '`ETFConstituentData`, và nó NULLABLE nên phải gạn trước khi xếp."""',
            ] + [TAB + d.format(lay=lay) for d in bat_dau.LOC_TRONG_SO]


def _khai_mo(nc, st):
    """Khối Bắt đầu -> các dòng của `initialize`. -> [dòng].

    KHÔNG trả về nhịp nữa: câu lịch nay do `bat_dau.ham_chay` quyết, vì nó phụ thuộc
    cả vào KIỂU ô `ma`. Trả thêm một bản sao của "nhịp nào" ở đây là để hai chỗ cùng
    biết một thứ, rồi trôi khỏi nhau."""
    ra = []
    k = core.o_bat_dau(st, "khoang") or {}
    for ten, ham in (("tu", "set_start_date"), ("den", "set_end_date")):
        p = str(k.get(ten) or "").split("-")
        if len(p) == 3:
            ra.append(f"self.{ham}({int(p[0])}, {int(p[1])}, {int(p[2])})")
    ra.append(f"self.set_cash({_lit(core.o_bat_dau(st, 'von'))})")
    # Đệm tiền mặt: chỉ viết ra khi KHÁC mặc định của LEAN. Viết thừa một dòng bằng
    # đúng mặc định chỉ tổ làm người đọc tưởng ta đang đổi một thứ gì đó.
    dem = core._f(core.o_bat_dau(st, "dem_tien_mat"))
    if dem is not None and abs(dem - 0.0025) > 1e-12:
        ra.append(f"self.settings.free_portfolio_value_percentage = {_lit(dem)}")
    san = str(core.o_bat_dau(st, "san") or "DEFAULT")
    ra.append(f"self.set_brokerage_model(BrokerageName.{san})")

    nc.ca_danh_muc = str(core.o_bat_dau(st, "chay_cho") or "") == "ca_danh_muc"
    if not bat_dau.nhip_cua(str(core.o_bat_dau(st, "nhip") or "")):
        # Nhịp lạ = file sửa tay. Báo rồi đi tiếp: `bat_dau.ham_chay` và
        # `do_phan_giai` đều rơi về nhịp «mỗi nến ngày», nên phần còn lại vẫn sinh
        # ra được và người dùng thấy bảng Vấn đề chỉ đúng một chỗ hỏng.
        nc.loi(st.get("id"), "Khối Bắt đầu chưa có nhịp chạy.")
    nc.res = f"Resolution.{bat_dau.do_phan_giai(st)}"

    ra.append("")
    gt_ma = core.o_bat_dau(st, "ma")
    nc.ro = bat_dau.ro_cua(gt_ma)
    if nc.ro:
        ra += _khai_ro(nc, gt_ma)
    else:
        ra.append("self._ten = {}")
        ten_ham = {m: h for m, _nh, h in bat_dau.LOAI_TAI_SAN}
        for m in gt_ma or []:
            k2 = str((m or {}).get("ma") or "").strip().upper()
            h = ten_ham.get((m or {}).get("loai"))
            if not k2 or not h:
                continue
            nc.ma_khai[k2] = True
            ra.append(f"self._ten[{k2!r}] = self.{h}({k2!r}, {nc.res}).symbol")
        ra.append("self._ma = list(self._ten.values())")

    moc = str(core.o_bat_dau(st, "moc_so_sanh") or "").strip().upper()
    if moc:
        ra.append(f"self.set_benchmark({moc!r})")

    # DÂY CHUYỀN CỦA LEAN — ba trạm đứng sau cây quyết định, cắm ở `initialize`.
    # Thứ tự viết ra theo đúng thứ tự dữ liệu chảy qua chúng (insight -> tỷ trọng ->
    # chỉnh rủi ro -> lệnh), để đọc mã sinh ra là thấy ngay dây chuyền.
    for ten_o, ham in (("chia_von", "set_portfolio_construction"),
                       ("phong_rui_ro", "set_risk_management"),
                       ("dat_lenh", "set_execution")):
        lop = str(core.o_bat_dau(st, ten_o) or "").strip()
        if lop:
            ra.append(f"self.{ham}({lop}())")
    return ra


# ---------------------------------------------------------------------------
# Cửa chính
# ---------------------------------------------------------------------------

def sinh(doc):
    """Một tài liệu Strategy -> {ok, ma, ten_lop, van_de}.

    `ok` False thì `ma` vẫn có (phần sinh được), nhưng ĐỪNG chạy nó — bảng `van_de`
    nói chỗ nào sơ đồ chưa diễn đạt hết."""
    d = doc if isinstance(doc, dict) else {}
    steps = [s for s in (d.get("steps") or []) if isinstance(s, dict)]
    edges = d.get("edges") or core.default_edges(steps)
    nc = _Nc(steps, edges)
    lop = ten_lop(d.get("name") or "Co May")

    # Lỗi đồ thị và lỗi ruột khối đi TRƯỚC: sinh mã từ một sơ đồ đã hỏng chỉ ra một
    # file hỏng theo kiểu khó hiểu hơn.
    nc.van_de += core.validate_flow_graph(steps, edges)
    for s in steps:
        nc.van_de += core.soat_khoi_hoi(s)
        nc.van_de += core.soat_khoi_lam(s)
        nc.van_de += core.soat_khoi_bat_dau(s)
    nc.van_de += core.soat_ca_ro(steps)
    nc.van_de += core.soat_ro_dong(steps)
    nc.van_de += core.soat_day_chuyen(steps)
    kq = core.flow_order(steps, edges)
    nc.thu_tu = kq["order"]

    bd = kq["entry"]
    st_bd = nc.theo_id.get(bd)
    if st_bd is None or not core.is_start_step(st_bd):
        nc.loi(None, "Sơ đồ chưa có khối Bắt đầu — không biết chạy trên mã gì.")
        return {"ok": False, "ma": "", "ten_lop": lop, "van_de": nc.van_de}

    dong_mo = _khai_mo(nc, st_bd)
    nc.da.add(bd)

    # Ruột phải sinh TRƯỚC `initialize`: chính lúc đi qua các khối Hỏi mới biết sơ đồ
    # dùng những chỉ báo nào, mà chỉ báo thì phải khai trong `initialize`.
    than = _toa(nc, bd, list(nc.ke.get(bd) or []), None, None, [])
    chua_toi = [s["id"] for s in steps
                if s.get("id") not in nc.da and s.get("id") not in nc.thu_tu]
    for sid in chua_toi:
        nc.loi(sid, "Khối này không nối vào sơ đồ nên không sinh mã.", "warning")

    # --- chỉ báo + làm nóng ---
    dong_doi_ro = []
    if nc.ro:
        # RỔ ĐỘNG: KHÔNG khai chỉ báo được ở đây. Lúc `initialize` chạy, rổ còn rỗng
        # (`self._ma` chưa có mã nào) — LEAN chỉ chọn rổ lần đầu khi nến đầu về. Nên
        # chỉ báo khai ở `on_securities_changed`, hàm LEAN gọi mỗi lần rổ đổi.
        dong_mo.append("")
        dong_mo.append("self._cb = {}")
        dong_doi_ro = _khai_cb_theo_ro(nc)
    elif nc.kho.ds:
        dong_mo.append("")
        dong_mo.append("self._cb = {}")
        # Khai chỉ báo cho MỌI mã trong rổ, kể cả khi sơ đồ chạy một lượt: một khối
        # có thể hỏi RSI của QQQ còn khối kia hỏi RSI của GLD.
        dong_mo.append("for sym in self._ma:")
        dong_mo.append(TAB + "self._cb[sym] = {}")
        for k, (cau, dk) in nc.kho.ds.items():
            if dk:
                dong_mo.append(TAB + f"_cb = {cau}")
                dong_mo.append(TAB + dk)
                dong_mo.append(TAB + f"self._cb[sym][{k!r}] = _cb")
            else:
                dong_mo.append(TAB + f"self._cb[sym][{k!r}] = {cau}")
        dong_mo.append("")
        dong_mo.append(f"self.set_warm_up({max(nc.kho.chu_ky)})")
    else:
        dong_mo.append("")
        dong_mo.append("self._cb = {sym: {} for sym in self._ma}")

    # --- hẹn giờ ---
    # ⚠ CÂU LỊCH ĐỔI THEO KIỂU Ô `ma`, không chỉ theo nhịp. `self._ma[0]` trên một rổ
    # động là `IndexError` ở dòng đầu `initialize` — rổ lúc ấy còn rỗng. Nhịp mang
    # sẵn hai câu, lấy đúng câu qua `bat_dau.ham_chay` (xem chú thích ở `NHIP`).
    cau_chay = bat_dau.ham_chay(st_bd)
    if cau_chay != "on_data":
        hen = _thay(cau_chay, {"ma": "self._ma[0]",
                              "gio": str(core.o_bat_dau(st_bd, "gio") or 0),
                              "phut": str(core.o_bat_dau(st_bd, "phut") or 0),
                              "so_phut": str(core.o_bat_dau(st_bd, "so_phut") or 0)})
        hen = hen.replace("date_rules", "self.date_rules")
        hen = hen.replace("time_rules", "self.time_rules")
        hen = "self." + hen[:-1] + ", self._nhip)"
        dong_mo.append("")
        dong_mo.append(hen)

    ok = not any(p["severity"] == "error" for p in nc.van_de)
    return {"ok": ok, "ten_lop": lop, "van_de": nc.van_de,
            "ma": _ghep(lop, d.get("name"), cau_chay != "on_data", dong_mo, than,
                        nc.ca_danh_muc, nc.ro, dong_doi_ro,
                        _ham_loc_ro(nc, st_bd), bool(nc.kho.ds))}


def _khai_cb_theo_ro(nc):
    """Chỉ báo của một RỔ ĐỘNG -> thân `on_securities_changed`. -> [dòng].

    `on_securities_changed(self, changes)` là hàm CÓ THẬT của `QCAlgorithm`, LEAN gọi
    nó mỗi lần rổ đổi, với `changes.added_securities` và `changes.removed_securities`.

    ⚠ HAI CHỖ HỎNG LẶNG Ở ĐÂY, cả hai đã dò bằng backtest thật:

      1. **Dòng `self._cb[sym] = {}` phải viết ra KỂ CẢ KHI SƠ ĐỒ KHÔNG CÓ CHỈ BÁO
         NÀO.** `self._ma` lấy từ `active_securities` có lọc `if kvp.key in self._cb`
         (xem `_ghep`) — lọc ấy tồn tại để không mã nào lọt vào vòng trước khi chỉ
         báo của nó kịp sinh ra. Bỏ dòng này thì `self._cb` rỗng mãi, `self._ma` lọc
         ra rỗng, và cỗ máy chạy đủ mọi nến mà không làm gì. Không lỗi, không cảnh
         báo, chỉ một bảng kết quả "0 lệnh".

      2. **`set_warm_up` VÔ DỤNG với chỉ báo sinh giữa đường**, nên thay bằng
         `self.warm_up_indicator(sym, cb, res)` — hàm có thật của `QCAlgorithm`, nó
         nạp lịch sử đủ cho đúng chỉ báo ấy ngay lúc tạo. `set_warm_up` chặn cả thuật
         toán trong N nến ĐẦU; mã vào rổ ở tháng thứ năm thì nó đã hết tác dụng từ
         lâu.
         `warm_up_indicator` nạp được bao nhiêu thì tuỳ đĩa có bao nhiêu, nên nó
         KHÔNG thay được chặn `is_ready` — xem `_ghep`, chỗ dựng chặn ấy."""
    ra = ["for s in changes.removed_securities:",
          TAB + "self._cb.pop(s.symbol, None)",
          "for s in changes.added_securities:",
          TAB + "if s.symbol in self._cb:",
          TAB * 2 + "continue",
          TAB + "self._cb[s.symbol] = {}"]
    for k, (cau, dk) in nc.kho.ds.items():
        ra.append(TAB + "_cb = " + _thay(cau, {"sym": "s.symbol"}))
        if dk:
            ra.append(TAB + _thay(dk, {"sym": "s.symbol"}))
        ra.append(TAB + f"self.warm_up_indicator(s.symbol, _cb, {nc.res})")
        ra.append(TAB + f"self._cb[s.symbol][{k!r}] = _cb")
    return ra


def _ghep(lop, ten, hen, dong_mo, than, ca_danh_muc=False, ro=None, doi_ro=(),
          loc_ro=(), co_cb=False):
    """Ghép thành một file Python hoàn chỉnh."""
    r = [
        '"""Thuật toán sinh bởi Cat_Studio — ' + str(ten or "") + ".",
        "",
        "ĐỪNG SỬA TAY: mở lại sơ đồ trong Cat_Studio rồi sinh lại, bản sửa tay sẽ bị",
        "ghi đè. Mỗi câu LEAN dưới đây lấy thẳng từ ô `lean` của từ điển khối.",
        '"""',
        "from AlgorithmImports import *",
        "",
        "",
        f"class {lop}(QCAlgorithm):",
        "",
        TAB + "def initialize(self):",
    ]
    r += [TAB * 2 + d if d else "" for d in dong_mo]

    # --- RỔ ĐỘNG: hai phương thức nữa, cả hai là cửa CÓ THẬT của `QCAlgorithm` ---
    if loc_ro:
        r += [""] + [TAB + d if d else "" for d in loc_ro]
    if ro:
        r += ["", TAB + "def on_securities_changed(self, changes):",
              TAB * 2 + "# Rổ đổi thì LEAN gọi vào đây — mã vào rổ thì khai chỉ báo",
              TAB * 2 + "# cho nó, mã ra rổ thì bỏ. `initialize` khai không được:",
              TAB * 2 + "# lúc ấy rổ còn rỗng."]
        r += [TAB * 2 + d if d else "" for d in doi_ro]

    r += ["", TAB + "def on_data(self, data):"]
    if hen:
        r += [TAB * 2 + "# Nhịp hẹn giờ: ruột chạy ở `_nhip`, không chạy theo nến.",
              TAB * 2 + "pass", "",
              TAB + "def _nhip(self):",
              TAB * 2 + "data = self.current_slice"]
    r += [TAB * 2 + "if self.is_warming_up:", TAB * 3 + "return"]
    if ro:
        # RỔ ĐỘNG: danh sách mã đổi theo NGÀY, nên phải đọc lại mỗi nhịp từ chính
        # LEAN. `active_securities` là cửa có thật của `QCAlgorithm`, duyệt ra cặp
        # khoá–giá trị. Lọc `in self._cb` để mã vừa vào rổ mà chỉ báo chưa kịp sinh
        # thì chưa vào vòng — xem `_khai_cb_theo_ro`.
        r += [TAB * 2 + "self._ma = [kvp.key for kvp in self.active_securities",
              TAB * 2 + "            if kvp.key in self._cb]"]
    if ca_danh_muc:
        # CHIA DANH MỤC: chạy đúng một lượt, mọi khối tự gọi tên mã của nó.
        r += [TAB * 2 + "self._mot_luot(data)",
              "",
              TAB + "def _mot_luot(self, data):"]
    else:
        # SÀNG TỪNG MÃ: cả sơ đồ chạy lại cho từng mã, `sym` là mã đang xét.
        r += [TAB * 2 + "for sym in self._ma:",
              TAB * 3 + "self._mot_ma(sym, data)",
              "",
              TAB + "def _mot_ma(self, sym, data):"]
        if ro and co_cb:
            # ⚠ CHẶN CHỈ BÁO CHƯA SẴN SÀNG — chỉ nhánh rổ cần, và nó hỏng LẶNG.
            #
            # Lối gõ mã sẵn không cần dòng này: `set_warm_up(N)` chặn hộ ở N nến đầu,
            # và mọi mã đều đã có mặt từ nến đầu. Rổ thì mã vào giữa đường, nên
            # `set_warm_up` không với tới — ta thay bằng `warm_up_indicator`, mà nó
            # chỉ nạp được ĐÚNG NHỮNG GÌ CÓ TRÊN ĐĨA.
            #
            # ĐÃ ÉP TÁI HIỆN BẰNG BACKTEST THẬT (SPY 12/2020, rổ top 8), và đây là
            # hai dạng «chưa sẵn sàng» đo được, không phải suy ra:
            #   · mã KHÔNG CÓ dữ liệu trên máy (AMZN, BRK.B trong bộ miễn phí):
            #     `is_ready=False`, `current.value` đọc ra ĐÚNG **0.0**;
            #   · mã CÓ dữ liệu mà lịch sử NGẮN HƠN chu kỳ (thử RSI 20000 ngày):
            #     `is_ready=False`, mà giá trị đọc ra ~**53** — một con số trông
            #     bình thường đến mức không ai nghi. Đây là dạng nguy hơn.
            # `RSI < 60` trên dạng thứ hai: CÒN chặn thì 0 lệnh; BỎ chặn thì **17
            # lệnh khớp hết** trên một chỉ báo chưa bao giờ chín. Backtest sạch cả
            # hai lần. Đó là lý do dòng này có mặt.
            r += [TAB * 2 + "# Mã mới vào rổ mà chưa đủ nến thì chỉ báo chưa chín —",
                  TAB * 2 + "# nó vẫn đọc ra một con số, chỉ là số ấy chưa có nghĩa.",
                  TAB * 2 + "if not all(x.is_ready for x in self._cb[sym].values()):",
                  TAB * 3 + "return"]
    r += [TAB * 2 + d if d else "" for d in (than or ["pass"])]
    return "\n".join(r) + "\n"
