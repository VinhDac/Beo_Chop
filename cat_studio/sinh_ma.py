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
        self.thu_tu = {}
        self.dem = 0

    def loi(self, sid, msg, sev="error"):
        core._loi(self.van_de, sev, sid, msg)


# ---------------------------------------------------------------------------
# Điều kiện -> biểu thức Python
# ---------------------------------------------------------------------------

def _sym_py(nc, ve, sid):
    """Mã của một vế -> biểu thức Python. Trống = mã đang xét."""
    m = str((ve or {}).get("ma") or "").strip().upper()
    if not m:
        return "sym"
    if m not in nc.ma_khai:
        nc.loi(sid, f'Điều kiện trỏ tới mã "{m}" mà khối Bắt đầu chưa khai nó. '
                    f"Thêm mã ấy vào khối Bắt đầu, hoặc bỏ nó khỏi điều kiện.")
        return "sym"
    return f"self._ten[{m!r}]"


def _ve_py(nc, ve, loai, sid):
    """Một VẾ của điều kiện -> biểu thức Python."""
    if not isinstance(ve, dict):
        return "0"
    if "ma_dl" not in ve:
        return _lit(ve.get("so", 0))
    dl = hoi.dai_luong(loai, ve["ma_dl"])
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
    loai = step["type"]
    ds = step.get("dieu_kien") or []
    if not ds:
        # Cổng rỗng LUÔN khớp — `soat_khoi_hoi` đã cảnh báo, ở đây sinh đúng như thế.
        return "True", "không điều kiện"
    ve = []
    for dk in ds:
        trai = _ve_py(nc, dk.get("trai"), loai, step["id"])
        phep = dk.get("phep")
        dl = hoi.dai_luong(loai, (dk.get("trai") or {}).get("ma_dl"))
        if dl and dl["kieu"] == hoi.KIEU_CO_KHONG:
            ve.append(f"not ({trai})" if phep == "khong" else f"({trai})")
        else:
            ve.append(f"({trai} {phep} {_ve_py(nc, dk.get('phai'), loai, step['id'])})")
    return " and ".join(ve), core.mo_ta_dieu_kien(ds[0], loai)


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
    gt = {"sym": "sym"}
    for o in lam.o_cua(t, a):
        gt[o["ten"]] = _lit(core.o_lam(a, o["ten"]))

    # Ô `tag` để trống thì ĐIỀN HỘ: số khối + điều kiện vừa khớp. Đó là lời hứa D-11
    # "chữ vì sao do chính đoạn code tự ghi", và LEAN nhận sẵn tham số này.
    if "tag" in gt and not str(core.o_lam(a, "tag") or "").strip():
        gt["tag"] = _lit(_chu_tag(nc, sid, mach))
    if t == lam.LAM_GHI_CHU and not str(core.o_lam(a, "cau") or "").strip():
        gt["cau"] = _lit(_chu_tag(nc, sid, mach))
    if t == lam.LAM_VE_BANG:
        gt["gia_tri"] = _ve_py(nc, a.get("gia_tri"), d["dai_luong_tu"], sid)
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

def _khai_mo(nc, st):
    """Khối Bắt đầu -> các dòng của `initialize`. -> ([dòng], nhịp)."""
    ra = []
    k = core.o_bat_dau(st, "khoang") or {}
    for ten, ham in (("tu", "set_start_date"), ("den", "set_end_date")):
        p = str(k.get(ten) or "").split("-")
        if len(p) == 3:
            ra.append(f"self.{ham}({int(p[0])}, {int(p[1])}, {int(p[2])})")
    ra.append(f"self.set_cash({_lit(core.o_bat_dau(st, 'von'))})")
    san = str(core.o_bat_dau(st, "san") or "DEFAULT")
    ra.append(f"self.set_brokerage_model(BrokerageName.{san})")

    n = bat_dau.nhip_cua(str(core.o_bat_dau(st, "nhip") or ""))
    if not n:
        nc.loi(st.get("id"), "Khối Bắt đầu chưa có nhịp chạy.")
        n = bat_dau.NHIP[4]
    nc.res = f"Resolution.{n[2]}"

    ra.append("")
    ra.append("self._ten = {}")
    ten_ham = {m: h for m, _nh, h in bat_dau.LOAI_TAI_SAN}
    for m in core.o_bat_dau(st, "ma") or []:
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
    return ra, n


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
    kq = core.flow_order(steps, edges)
    nc.thu_tu = kq["order"]

    bd = kq["entry"]
    st_bd = nc.theo_id.get(bd)
    if st_bd is None or not core.is_start_step(st_bd):
        nc.loi(None, "Sơ đồ chưa có khối Bắt đầu — không biết chạy trên mã gì.")
        return {"ok": False, "ma": "", "ten_lop": lop, "van_de": nc.van_de}

    dong_mo, nhip = _khai_mo(nc, st_bd)
    nc.da.add(bd)

    # Ruột phải sinh TRƯỚC `initialize`: chính lúc đi qua các khối Hỏi mới biết sơ đồ
    # dùng những chỉ báo nào, mà chỉ báo thì phải khai trong `initialize`.
    than = _toa(nc, bd, list(nc.ke.get(bd) or []), None, None, [])
    chua_toi = [s["id"] for s in steps
                if s.get("id") not in nc.da and s.get("id") not in nc.thu_tu]
    for sid in chua_toi:
        nc.loi(sid, "Khối này không nối vào sơ đồ nên không sinh mã.", "warning")

    # --- chỉ báo + làm nóng ---
    if nc.kho.ds:
        dong_mo.append("")
        dong_mo.append("self._cb = {}")
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
    if nhip[3] != "on_data":
        hen = _thay(nhip[3], {"ma": "self._ma[0]",
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
            "ma": _ghep(lop, d.get("name"), nhip, dong_mo, than)}


def _ghep(lop, ten, nhip, dong_mo, than):
    """Ghép thành một file Python hoàn chỉnh."""
    hen = nhip[3] != "on_data"
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
    r += ["", TAB + "def on_data(self, data):"]
    if hen:
        r += [TAB * 2 + "# Nhịp hẹn giờ: ruột chạy ở `_nhip`, không chạy theo nến.",
              TAB * 2 + "pass", "",
              TAB + "def _nhip(self):",
              TAB * 2 + "data = self.current_slice"]
    r += [TAB * 2 + "if self.is_warming_up:",
          TAB * 3 + "return",
          TAB * 2 + "for sym in self._ma:",
          TAB * 3 + "self._mot_ma(sym, data)",
          "",
          TAB + "def _mot_ma(self, sym, data):"]
    r += [TAB * 2 + d if d else "" for d in (than or ["pass"])]
    return "\n".join(r) + "\n"
