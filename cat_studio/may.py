"""CỖ MÁY 5 TRẠM — định dạng, chuẩn hoá, soát lỗi, đánh số, chữ trên khối.  (D-10)

Một cỗ máy là NĂM sơ đồ khối, mỗi sơ đồ là một trạm của khung thuật toán QuantConnect
(`tram.py` khai trạm nào làm gì). Mọi trạm dùng chung MỘT ngữ pháp sơ đồ — đúng bộ đồ thị
của `core` (đánh số, luật rẽ nhánh, luật lùi), nên file này không viết lại phần đó mà chỉ
thêm thứ riêng của cỗ máy: khối nào được đặt ở trạm nào, đại lượng nào đọc được ở đâu, mỗi
trạm có ra được kết quả không, và Gom của trạm.

ĐỊNH DẠNG
---------
    {"dang": "may5", "phien_ban": 1, "name": "…",
     "tham_so": [{"ten", "nhan", "gia_tri", "don_vi", "ghi_chu"}],
     "tram": {"chon_ma":  {"steps": […], "edges": […], "gom": {…}},
              "tin_hieu": {"steps": […], "edges": […]},
              "chia_von": {"steps": […], "edges": […], "gom": {…}},
              "rui_ro":   {"steps": […], "edges": […]},
              "khop_lenh":{"steps": […], "edges": […]}}}

Khối:  Bắt đầu  {"kind": "start", "lich", "khung"?, "pham_vi"? (chỉ ①)}
       Hỏi      {"kind": "action", "type": "check_cond", "conditions": [{trai, phep, phai}]}
       Làm      {"kind": "action", "type": <khoá trong tram.KHOI_LAM>, …các ô của nó}

LUẬT XUYÊN SUỐT (giữ nguyên của app): ở đâu chờ một con số, một CHUỖI nghĩa là TÊN THAM SỐ.

Không import giao diện, không import QuantConnect — kiểm được bằng vài dict dựng tay.
"""
import copy
import re

from . import core
from . import tram as T

DANG = "may5"
PHIEN_BAN = 1

#: Ký hiệu mã hợp lệ cho danh sách riêng của trạm ①: chữ HOA, số, dấu chấm/gạch (BRK.B).
_RE_MA = re.compile(r"^[A-Z0-9][A-Z0-9./-]{0,19}$")


# ---------------------------------------------------------------------------
# Con số
# ---------------------------------------------------------------------------
def _so(x):
    """2.0 → '2', 1.5 → '1.5'."""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)
    return str(int(f)) if f == int(f) else f"{f:g}"


def _so_hoac_ten(v, ts, hien_ten=True):
    """Ô số trên thẻ: con số, hoặc `tên = giá trị` nếu là tham số."""
    if not isinstance(v, str):
        return _so(v)
    gt = (ts or {}).get(v)
    if not hien_ten:
        return _so(gt) if gt is not None else f"{v}=?"
    return f"{v} = {_so(gt) if gt is not None else '?'}"


def _la_so(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _chuan_o_so(v):
    """Ô số: số → float; chuỗi → tên tham số (bỏ khoảng trắng); còn lại GIỮ NGUYÊN để soát
    lỗi còn mắng đúng chỗ — đoán thay người dùng là âm thầm đổi nghĩa một con số."""
    if _la_so(v):
        return float(v)
    if isinstance(v, str):
        return v.strip()
    return v


# ---------------------------------------------------------------------------
# Tạo mới
# ---------------------------------------------------------------------------
def khoi_bat_dau(tram_key):
    t = T.TRAM_THEO_KEY[tram_key]
    st = {"kind": core.KIND_START, "id": core.new_step_id(), "name": "Bắt đầu",
          "pos": [80.0, 300.0], "lich": t["lich_mac_dinh"]}
    if st["lich"] == "moi_nen":
        st["khung"] = t["khung_mac_dinh"]
    if tram_key == T.CHON_MA:
        st["pham_vi"] = {"loai": "tat_ca"}
    return st


def khoi_hoi(conditions=None, name=None):
    return {"kind": core.KIND_ACTION, "id": core.new_step_id(), "type": T.HOI,
            "name": name or T.NHAN_HOI, "conditions": list(conditions or [])}


def khoi_lam(loai, name=None, **o):
    """Khối Làm `loai` với các ô mặc định của nó; `o` đè lên ô nào cần khác."""
    d = T.KHOI_LAM[loai]
    st = {"kind": core.KIND_ACTION, "id": core.new_step_id(), "type": loai,
          "name": name or d["nhan"]}
    st.update(o)
    return st


def _gom_mac_dinh(tram_key):
    ra = {}
    for f in T.GOM.get(tram_key) or []:
        if "mac_dinh" in f:
            ra[f["key"]] = f["mac_dinh"]
    return ra


def may_moi(ten="Cỗ máy mới"):
    """Cỗ máy trắng: năm trạm, mỗi trạm đúng một khối Bắt đầu.

    Không tự lắp gì thêm: soát lỗi sẽ nói rõ trạm nào còn thiếu gì (①②③⑤ đều cần một khối
    Làm mới ra được kết quả). Lắp sẵn là việc của các mẫu dựng sẵn — người chơi CHỌN, không
    phải gỡ bỏ thứ máy tự đặt vào."""
    ra = {"dang": DANG, "phien_ban": PHIEN_BAN, "name": ten, "tham_so": [], "tram": {}}
    for k in T.TRAM_KEYS:
        g = {"steps": [khoi_bat_dau(k)], "edges": []}
        if k in T.GOM:
            g["gom"] = _gom_mac_dinh(k)
        ra["tram"][k] = g
    return ra


def la_may(doc):
    """Tài liệu này có phải cỗ máy 5 trạm không (khác sơ đồ Entry/Manage cũ)."""
    return isinstance(doc, dict) and doc.get("dang") == DANG


# ---------------------------------------------------------------------------
# Chuẩn hoá — BẤT BIẾN: chạy hai lần bằng đúng một lần
# ---------------------------------------------------------------------------
def _giu_chung(nguon, dich):
    for k in ("id", "name"):
        if nguon.get(k):
            dich[k] = str(nguon[k]).strip() if k == "name" else nguon[k]
    if nguon.get("ghim"):
        dich["ghim"] = True
    pos = nguon.get("pos")
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        try:
            dich["pos"] = [float(pos[0]), float(pos[1])]
        except (TypeError, ValueError):
            pass
    return dich


def _khung_mac_dinh(tram_key, bd):
    """Khung cho đại lượng bỏ trống ô khung: khung của khối Bắt đầu nếu trạm chạy mỗi nến,
    còn không thì khung mặc định của trạm (D1 cho ① và ③). Thẻ khối hiện khung đó ra,
    nên không có con số nào bị giấu."""
    if bd and bd.get("lich") == "moi_nen" and bd.get("khung") in T.KHUNG:
        return bd["khung"]
    return T.TRAM_THEO_KEY[tram_key]["khung_mac_dinh"]


def _chuan_toan_hang(o, khung):
    """Giữ đúng các ô đại lượng này khai, điền mặc định cho ô bỏ trống.

    Đại lượng LẠ thì giữ nguyên để soát lỗi gọi đúng tên nó ra — vứt đi là cả điều kiện
    biến mất trong im lặng (đúng lỗi bản Entry/Manage từng dính với khối lạ)."""
    if not isinstance(o, dict):
        return {"ten": ""}
    ten = o.get("ten") or ""
    d = T.TOAN_HANG_THEO_KEY.get(ten)
    if not d:
        return dict(o)
    ra = {"ten": ten}
    for k in d["tham_so"]:
        v = o.get(k)
        if v in (None, ""):
            if k == "khung":
                v = khung
            elif k in d["mac_dinh"]:
                v = d["mac_dinh"][k]
            elif k == "dong":
                v = next(iter(d["dong"] or {}), None)
            else:
                v = T.THAM_SO_TH[k].get("mac_dinh")
        elif T.THAM_SO_TH.get(k, {}).get("loai") == "so":
            v = _chuan_o_so(v)
        if v is not None:
            ra[k] = v
    if "he_so" in o and o.get("he_so") not in (None, "", 1, 1.0):
        ra["he_so"] = _chuan_o_so(o["he_so"])
    return ra


def _chuan_dieu_kien(c, khung):
    if not isinstance(c, dict):
        return None
    ra = {"trai": _chuan_toan_hang(c.get("trai"), khung),
          "phep": c.get("phep") if c.get("phep") in T.PHEP_SO else (c.get("phep") or ">")}
    p = c.get("phai")
    if isinstance(p, dict) and "ten" in p:
        ra["phai"] = _chuan_toan_hang(p, khung)
    else:
        v = p.get("value") if isinstance(p, dict) else p
        ra["phai"] = {"value": _chuan_o_so(0.0 if v is None else v)}
    return ra


def _ap_dung(f, st):
    """Ô `f` có nghĩa với khối `st` không (luật `khi`)."""
    return all(st.get(k) == v for k, v in (f.get("khi") or {}).items())


def _chuan_o(f, v, khung):
    if f["loai"] == "so":
        return _chuan_o_so(v)
    if f["loai"] == "toan_hang":
        return _chuan_toan_hang(v, khung) if isinstance(v, dict) and v.get("ten") else None
    if f["loai"] == "bat_tat":
        return bool(v)
    return v                       # chon: giữ nguyên, soát lỗi bắt giá trị lạ


def _chuan_lam(s, tram_key, khung):
    t = s.get("type")
    d = T.KHOI_LAM[t]
    ra = {"kind": core.KIND_ACTION, "type": t}
    # Đặt các ô CHỌN trước: luật `khi` của ô khác đọc chúng.
    for f in sorted(d["truong"], key=lambda f: f["loai"] != "chon"):
        if not _ap_dung(f, ra):
            continue
        v = s.get(f["key"])
        if v in (None, ""):
            if f.get("tuy_chon") or "mac_dinh" not in f:
                continue
            v = f["mac_dinh"]
        v = _chuan_o(f, v, khung)
        if v is not None:
            ra[f["key"]] = v
    _giu_chung(s, ra)
    ra.setdefault("name", d["nhan"])
    return ra


def _chuan_bat_dau(s, tram_key):
    t = T.TRAM_THEO_KEY[tram_key]
    ra = {"kind": core.KIND_START}
    lich = s.get("lich")
    ra["lich"] = lich if lich in t["lich"] else t["lich_mac_dinh"]
    if ra["lich"] == "moi_nen":
        k = s.get("khung")
        ra["khung"] = k if k in T.KHUNG else t["khung_mac_dinh"]
    if tram_key == T.CHON_MA:
        pv = s.get("pham_vi") if isinstance(s.get("pham_vi"), dict) else {}
        if pv.get("loai") == "danh_sach":
            ma, thay = [], set()
            for x in pv.get("ma") or []:
                x = str(x or "").strip().upper()
                if x and x not in thay:
                    thay.add(x)
                    ma.append(x)
            ra["pham_vi"] = {"loai": "danh_sach", "ma": ma}
        else:
            ra["pham_vi"] = {"loai": "tat_ca"}
    _giu_chung(s, ra)
    ra.setdefault("name", "Bắt đầu")
    return ra


def _chuan_khoi(s, tram_key, khung):
    if not isinstance(s, dict):
        return None
    if s.get("kind") == core.KIND_START:
        return _chuan_bat_dau(s, tram_key)
    t = s.get("type")
    if t == T.HOI:
        ra = {"kind": core.KIND_ACTION, "type": T.HOI,
              "conditions": [x for x in (_chuan_dieu_kien(c, khung)
                                         for c in s.get("conditions") or []) if x]}
        _giu_chung(s, ra)
        ra.setdefault("name", T.NHAN_HOI)
        return ra
    if t in T.KHOI_LAM:
        return _chuan_lam(s, tram_key, khung)
    # Khối LẠ (file của bản mới hơn, hoặc gõ tay): GIỮ, để soát lỗi gọi tên nó ra.
    # Vứt đi là cắt đôi chuỗi nối dây trong im lặng, rồi lưu lại là mất hẳn.
    ra = copy.deepcopy(s)
    ra["kind"] = core.KIND_ACTION
    return ra


def _chuan_gom(tram_key, g):
    g = g if isinstance(g, dict) else {}
    ra = {}
    for f in T.GOM.get(tram_key) or []:
        v = g.get(f["key"])
        if v in (None, ""):
            if f.get("tuy_chon") or "mac_dinh" not in f:
                continue
            v = f["mac_dinh"]
        ra[f["key"]] = _chuan_o(f, v, None)
    return ra


def _chuan_tram(tram_key, g):
    g = g if isinstance(g, dict) else {}
    tho = [s for s in g.get("steps") or [] if isinstance(s, dict)]
    if not tho:
        # Trạm trắng hẳn (file thiếu trạm): dựng khối Bắt đầu để có điểm neo. Có khối rồi mà
        # thiếu Bắt đầu thì KHÔNG tự thêm — soát lỗi nói ra, vì chèn một khối không nối vào
        # đâu chỉ đổi lỗi này thành lỗi khác.
        tho = [khoi_bat_dau(tram_key)]
    bd = next((s for s in tho if s.get("kind") == core.KIND_START), None)
    bd = _chuan_bat_dau(bd, tram_key) if bd else None
    khung = _khung_mac_dinh(tram_key, bd)
    steps = [x for x in (_chuan_khoi(s, tram_key, khung) for s in tho) if x]
    core.ensure_step_ids(steps)
    ra = {"steps": steps, "edges": core.clean_edges(g.get("edges") or [], steps)}
    if tram_key in T.GOM:
        ra["gom"] = _chuan_gom(tram_key, g.get("gom"))
    return ra


def _chuan_tham_so(ds):
    ra, thay = [], set()
    for t in ds or []:
        if not isinstance(t, dict):
            continue
        ten = str(t.get("ten") or "").strip()
        if not ten or ten in thay:
            continue
        thay.add(ten)
        try:
            v = float(t.get("gia_tri"))
        except (TypeError, ValueError):
            v = 0.0
        ra.append(core.make_tham_so(ten, str(t.get("nhan") or "").strip(), v,
                                    str(t.get("don_vi") or "").strip(),
                                    str(t.get("ghi_chu") or "")))
    return ra


def chuan_hoa(doc):
    """Mọi cỗ máy tới tay soát lỗi, bộ máy chạy hay giao diện đều đi qua đây trước."""
    doc = doc if isinstance(doc, dict) else {}
    v = doc.get("phien_ban")
    if la_may(doc) and _la_so(v) and v > PHIEN_BAN:
        raise ValueError(
            f"Cỗ máy này thuộc bản mới hơn (phiên bản {v}, app đang hiểu {PHIEN_BAN}). "
            f"Cập nhật app rồi mở lại — mở bằng bản cũ có thể làm mất khối nó chưa biết.")
    tram = doc.get("tram") if isinstance(doc.get("tram"), dict) else {}
    return {
        "dang": DANG, "phien_ban": PHIEN_BAN,
        "name": str(doc.get("name") or "").strip() or "Cỗ máy mới",
        "tham_so": _chuan_tham_so(doc.get("tham_so")),
        "tram": {k: _chuan_tram(k, tram.get(k)) for k in T.TRAM_KEYS},
    }


def bang_tham_so(doc):
    return {t["ten"]: t["gia_tri"] for t in (doc or {}).get("tham_so") or []}


# ---------------------------------------------------------------------------
# Chữ — DO PYTHON SINH, giao diện không ghép một mẩu nào
# ---------------------------------------------------------------------------
def toan_hang_chu(o, ts=None):
    """{"ten": "ema", "khung": "H1", "chu_ky": 20, "lui": 1} → 'EMA(H1, 20)[1]'."""
    if not isinstance(o, dict):
        return "?"
    ten = o.get("ten") or ""
    d = T.TOAN_HANG_THEO_KEY.get(ten)
    if not d:
        return f"«{ten}»" if ten else "?"
    phan = []
    for k in d["tham_so"]:
        if k == "lui":
            continue
        v = o.get(k)
        if v in (None, ""):
            continue
        tsk = T.THAM_SO_TH.get(k, {})
        if k == "dong":
            phan.append((d["dong"] or {}).get(v, str(v)))
        elif tsk.get("loai") == "chon":
            phan.append(str(tsk["chon"].get(v, v)) if k != "khung" else str(v))
        else:
            phan.append(_so_hoac_ten(v, ts, hien_ten=False))
    chu = f"{d['nhan']}({', '.join(phan)})" if phan else d["nhan"]
    lui = o.get("lui")
    if lui not in (None, "", 0, 0.0):
        chu += f"[{_so_hoac_ten(lui, ts, hien_ten=False)}]"
    if o.get("he_so") not in (None, "", 1, 1.0):
        chu += f" × {_so_hoac_ten(o['he_so'], ts)}"
    return chu


def dieu_kien_chu(c, ts=None):
    """Một dòng điều kiện: 'EMA(H1, 20) > EMA(H1, 50)' · 'RSI(H1, 14) < nguong = 30'."""
    c = c or {}
    p = c.get("phai")
    if isinstance(p, dict) and "ten" in p:
        phai = toan_hang_chu(p, ts)
    else:
        phai = _so_hoac_ten((p or {}).get("value") if isinstance(p, dict) else p, ts)
    return f"{toan_hang_chu(c.get('trai'), ts)} {T.PHEP_SO.get(c.get('phep'), '?')} {phai}"


def _pham_vi_chu(st):
    pv = st.get("pham_vi") or {}
    if pv.get("loai") == "danh_sach":
        ma = pv.get("ma") or []
        return "cho các mã: " + (", ".join(ma) if ma else "(chưa có mã nào)")
    return "cho mỗi mã của màn chơi"


def dong_khoi(st, tram_key, ts=None):
    """Chữ trên HỘP — vài dòng ngắn, mỗi ý một dòng."""
    if st.get("kind") == core.KIND_START:
        lich = st.get("lich")
        dau = (f"Mỗi nến {st.get('khung') or '?'}" if lich == "moi_nen"
               else T.LICH.get(lich, "?")[:1].upper() + T.LICH.get(lich, "?")[1:])
        if tram_key == T.CHON_MA:
            return [dau, _pham_vi_chu(st)]
        return [dau, "cho " + T.TRAM_THEO_KEY[tram_key]["cho_ai"]]

    t = st.get("type")
    if t == T.HOI:
        return ([dieu_kien_chu(c, ts) for c in st.get("conditions") or []]
                or ["chưa có điều kiện nào — luôn qua"])

    if t not in T.KHOI_LAM:
        return [f"khối «{t}» không có trong từ điển"]

    if t == "vao_ro":
        return ["vào rổ"] + ([f"điểm = {toan_hang_chu(st['diem'], ts)}"]
                             if st.get("diem") else [])
    if t == "loai_ro":
        return ["không vào rổ"]
    if t == "bao":
        ds = [f"{T.HUONG_TIN_HIEU.get(st.get('huong'), '?')} · hạn "
              f"{_so_hoac_ten(st.get('thoi_han'), ts)} nến"]
        phu = []
        if st.get("tin_cay") not in (None, ""):
            phu.append(f"tin cậy {_so_hoac_ten(st['tin_cay'], ts)}")
        if st.get("trong_so") not in (None, ""):
            phu.append(f"trọng số {_so_hoac_ten(st['trong_so'], ts)}")
        return ds + ([" · ".join(phu)] if phu else [])
    if t == "dat_ty_trong":
        cach = st.get("cach")
        if cach == "co_dinh":
            return [f"cố định {_so_hoac_ten(st.get('pt'), ts)}% vốn"]
        if cach == "rui_ro_ngang":
            return ["rủi ro ngang nhau",
                    f"theo ATR %({st.get('khung') or '?'}, "
                    f"{_so_hoac_ten(st.get('chu_ky'), ts, hien_ten=False)})"]
        return [T.CACH_CHIA.get(cach, "?")]
    if t == "ve_0":
        return ["mục tiêu = 0"]
    if t == "giu_nguyen":
        return ["mục tiêu = đang giữ"]
    if t == "dua_ve_0":
        return ["bán sạch mã này"]
    if t == "giam_ve":
        return [f"tối đa {_so_hoac_ten(st.get('pt'), ts)}% vốn"]
    if t == "cam_vao_lai":
        return [f"cấm vào lại {_so_hoac_ten(st.get('so_nen'), ts)} nến"]
    if t == "dung_tai_khoan":
        return ["bán sạch MỌI mã", "thôi giao dịch tới hết lượt"]

    def phan(v):
        return ("toàn bộ phần lệch" if _la_so(v) and float(v) >= 100
                else f"{_so_hoac_ten(v, ts)}% phần còn lệch")

    if t == "lenh_thi_truong":
        return [f"khớp ngay {phan(st.get('phan_pt'))}"]
    if t in ("lenh_gioi_han", "lenh_cho_stop"):
        ten = "giới hạn" if t == "lenh_gioi_han" else "chờ stop"
        return [f"{ten} cách giá {_so_hoac_ten(st.get('lech_pt'), ts)}%",
                f"hạn {_so_hoac_ten(st.get('het_han'), ts)} nến · {phan(st.get('phan_pt'))}"]
    if t == "cho":
        return ["chưa đặt lệnh lượt này"]
    return [T.KHOI_LAM[t]["nhan"]]


def the_khoi(st, tram_key, ts=None, so=None):
    """Một khối → thẻ cho giao diện vẽ. `so` = nhãn đánh số (`2A.1`)."""
    la_bd = st.get("kind") == core.KIND_START
    t = st.get("type")
    if la_bd:
        mau, mo_ta = "start", (f"{T.nhan_tram(tram_key)}: "
                               f"{T.TRAM_THEO_KEY[tram_key]['hoi']} Cả sơ đồ chạy lại "
                               f"từ khối này cho từng đối tượng.")
    elif t == T.HOI:
        mau, mo_ta = "hoi", "Qua thì đi tiếp; trượt thì thử nhánh kế bên dưới."
    else:
        mau, mo_ta = "lam", (T.KHOI_LAM.get(t) or {}).get("mo_ta", "")
    return {"id": st.get("id"), "kind": st.get("kind"), "type": t, "tram": tram_key,
            "title": st.get("name") or "", "so": so,
            "lines": [{"text": x} for x in dong_khoi(st, tram_key, ts)],
            "mo_ta": mo_ta, "mau": mau, "ghim": bool(st.get("ghim")),
            "la_cong": core.is_branch_gate(st),
            "vai": (T.KHOI_LAM.get(t) or {}).get("vai")}


def danh_so(doc):
    """{trạm: kết quả `core.flow_order`} — nhãn đánh số của từng khối, theo từng trạm."""
    doc = chuan_hoa(doc)
    return {k: core.flow_order(doc["tram"][k]["steps"], doc["tram"][k]["edges"])
            for k in T.TRAM_KEYS}


def kem_the(doc):
    """Gắn `cards` (kèm nhãn đánh số) vào từng trạm. Chuẩn hoá NGAY tại đây: mọi cỗ máy tới
    tay giao diện đều phải qua chuẩn hoá — một chỗ bảo đảm, không trông vào từng chỗ gọi."""
    doc = chuan_hoa(doc)
    ts = bang_tham_so(doc)
    for k in T.TRAM_KEYS:
        g = doc["tram"][k]
        so = core.flow_order(g["steps"], g["edges"])["order"]
        g["cards"] = [the_khoi(s, k, ts, so.get(s.get("id"))) for s in g["steps"]]
    return doc


# ---------------------------------------------------------------------------
# Soát lỗi
# ---------------------------------------------------------------------------
def _van_de(ds, sev, tram_key, sid, msg, index=None):
    ds.append({"severity": sev, "tram": tram_key, "step": sid, "index": index,
               "message": msg})


class _Soat:
    """Soát MỘT trạm. Mỗi câu báo lỗi gọi khối bằng nhãn thật trên huy hiệu (`[2A]`), đúng
    luật của bảng Vấn đề cũ: nói "Bước 7" về một khối mà huy hiệu ghi "2A" là bắt người
    dùng đi dò."""

    def __init__(self, may, tram_key, ra):
        self.may, self.k, self.ra = may, tram_key, ra
        g = may["tram"][tram_key]
        self.steps, self.edges = g["steps"], g["edges"]
        self.gom = g.get("gom") or {}
        self.ts = bang_tham_so(may)
        self.nhan = core.flow_order(self.steps, self.edges)["order"]
        self.theo_id, self.ke = core.flow_map(self.steps, self.edges)

    def ten(self, st):
        n = self.nhan.get(st.get("id"))
        tieu_de = st.get("name") or "?"
        return f'[{n}] "{tieu_de}"' if n else f'"{tieu_de}"'

    def loi(self, st, msg, index=None):
        _van_de(self.ra, "error", self.k, st.get("id") if st else None, msg, index)

    def canh(self, st, msg, index=None):
        _van_de(self.ra, "warning", self.k, st.get("id") if st else None, msg, index)

    # ---- ô số ----
    def so(self, st, v, cho, f, index=None):
        """Một ô số theo khai báo `f` (min/max/nguyen). Tên tham số thì soát GIÁ TRỊ của
        tham số đó — chính con số ấy mới là thứ bộ máy chạy dùng."""
        if isinstance(v, str):
            if v not in self.ts:
                self.loi(st, f'{self.ten(st)}: {cho} dùng tham số "{v}" không có trong '
                             f"bảng tham số của cỗ máy.", index)
                return
            gt, nguon = self.ts[v], f'tham số "{v}" = {_so(self.ts[v])}'
        elif _la_so(v):
            gt, nguon = float(v), _so(v)
        else:
            self.loi(st, f"{self.ten(st)}: {cho} cần một con số, hoặc tên một tham số.", index)
            return
        if f.get("nguyen") and gt != int(gt):
            self.loi(st, f"{self.ten(st)}: {cho} cần số nguyên ({nguon}).", index)
        elif "min" in f and gt < f["min"]:
            self.loi(st, f"{self.ten(st)}: {cho} không được nhỏ hơn {_so(f['min'])} "
                         f"({nguon}).", index)
        elif "max" in f and gt > f["max"]:
            self.loi(st, f"{self.ten(st)}: {cho} không được lớn hơn {_so(f['max'])} "
                         f"({nguon}).", index)

    # ---- đại lượng ----
    def toan_hang(self, st, o, cho, index=None):
        """Trả đơn vị của đại lượng nếu hợp lệ, None nếu không."""
        ten = (o or {}).get("ten") or ""
        if not ten:
            self.loi(st, f"{self.ten(st)}: {cho} chưa chọn đại lượng.", index)
            return None
        d = T.TOAN_HANG_THEO_KEY.get(ten)
        if not d:
            self.loi(st, f'{self.ten(st)}: {cho} dùng đại lượng "{ten}" không có trong '
                         f"từ điển.", index)
            return None
        if not T.doc_duoc_o(ten, self.k):
            noi = ", ".join(T.nhan_tram(x) for x in d["tram"])
            self.loi(st, f"{self.ten(st)}: «{d['nhan']}» chỉ đọc được ở {noi} — trạm "
                         f"{T.nhan_tram(self.k)} chưa có thứ đó lúc nó chạy.", index)
            return None
        for k in d["tham_so"]:
            f = T.THAM_SO_TH[k]
            v = o.get(k)
            if f["loai"] == "chon":
                chon = d["dong"] if k == "dong" else f["chon"]
                if v not in chon:
                    self.loi(st, f"{self.ten(st)}: {cho} «{d['nhan']}» chưa chọn "
                                 f"{f['nhan']}.", index)
            else:
                self.so(st, v, f"{cho} «{d['nhan']}» — {f['nhan']}", f, index)
        if d["key"] == "macd" and _la_so(o.get("nhanh")) and _la_so(o.get("cham")) \
                and o["nhanh"] >= o["cham"]:
            self.loi(st, f"{self.ten(st)}: {cho} MACD có đường nhanh ({_so(o['nhanh'])}) "
                         f"không ngắn hơn đường chậm ({_so(o['cham'])}).", index)
        if "he_so" in o:
            self.so(st, o["he_so"], f"{cho} — hệ số nhân", {}, index)
            if _la_so(o["he_so"]) and o["he_so"] == 0:
                self.loi(st, f"{self.ten(st)}: {cho} nhân với 0 — vế đó luôn bằng 0.", index)
        return d["don_vi"]

    def hoi(self, st):
        dk = st.get("conditions") or []
        if not dk:
            self.canh(st, f"{self.ten(st)} chưa có điều kiện nào — luôn qua. Thêm điều kiện, "
                          f"hoặc bỏ khối này đi cho sơ đồ gọn.")
        for i, c in enumerate(dk):
            cho = f"điều kiện {i + 1}"
            dv_trai = self.toan_hang(st, c.get("trai"), f"{cho}, vế trái", i)
            if c.get("phep") not in T.PHEP_SO:
                self.loi(st, f"{self.ten(st)}: {cho} chưa chọn phép so.", i)
            p = c.get("phai") or {}
            if "ten" in p:
                dv_phai = self.toan_hang(st, p, f"{cho}, vế phải", i)
                if dv_trai and dv_phai and dv_trai != dv_phai:
                    self.loi(st, f"{self.ten(st)}: {cho} so "
                                 f"«{toan_hang_chu(c.get('trai'), self.ts)}» "
                                 f"({T.DON_VI[dv_trai]}) với «{toan_hang_chu(p, self.ts)}» "
                                 f"({T.DON_VI[dv_phai]}) — hai đại lượng khác loại, phép so "
                                 f"không có nghĩa.", i)
            else:
                self.so(st, p.get("value"), f"{cho}, vế phải", {}, i)

    # ---- khối Làm ----
    def lam(self, st):
        t = st.get("type")
        d = T.KHOI_LAM[t]
        if d["tram"] != self.k:
            self.loi(st, f"{self.ten(st)}: «{d['nhan']}» là khối của trạm "
                         f"{T.nhan_tram(d['tram'])} — trạm {T.nhan_tram(self.k)} không dùng "
                         f"được.")
            return
        for f in d["truong"]:
            if not _ap_dung(f, st):
                continue
            v = st.get(f["key"])
            if v in (None, ""):
                if not f.get("tuy_chon"):
                    self.loi(st, f"{self.ten(st)}: chưa điền ô «{f['nhan']}».")
                continue
            if f["loai"] == "chon" and v not in f["chon"]:
                self.loi(st, f"{self.ten(st)}: ô «{f['nhan']}» mang giá trị lạ «{v}».")
            elif f["loai"] == "so":
                self.so(st, v, f"ô «{f['nhan']}»", f)
            elif f["loai"] == "toan_hang":
                self.toan_hang(st, v, f"ô «{f['nhan']}»")

    def bat_dau(self, st):
        if self.k == T.CHON_MA:
            pv = st.get("pham_vi") or {}
            if pv.get("loai") == "danh_sach":
                ma = pv.get("ma") or []
                if not ma:
                    self.loi(st, f"{self.ten(st)}: chọn «danh sách riêng» mà chưa có mã nào "
                                 f"— rổ luôn rỗng.")
                xau = [m for m in ma if not _RE_MA.match(m)]
                if xau:
                    self.loi(st, f"{self.ten(st)}: mã không hợp lệ: {', '.join(xau)}.")

    # ---- cả trạm ----
    def chay(self):
        ds = [s for s in self.steps if isinstance(s, dict)]
        bd = [s for s in ds if s.get("kind") == core.KIND_START]
        # Phần ĐỒ THỊ: đúng bộ luật của `core`, chỉ gọi cổng bằng tên mới.
        for p in core.validate_flow_graph(self.steps, self.edges, nhan_cong=f'"{T.NHAN_HOI}"'):
            if not bd and p["step"] is None and "chưa có khối Bắt đầu" in p["message"]:
                continue                     # câu riêng, gắt hơn, ở dưới
            _van_de(self.ra, p["severity"], self.k, p["step"], p["message"], p.get("index"))
        if not bd:
            _van_de(self.ra, "error", self.k, None,
                    f"Trạm {T.nhan_tram(self.k)} chưa có khối Bắt đầu — không biết chạy lúc "
                    f"nào, cho ai.")

        for st in ds:
            if st.get("kind") == core.KIND_START:
                self.bat_dau(st)
            elif st.get("type") == T.HOI:
                self.hoi(st)
            elif st.get("type") in T.KHOI_LAM:
                self.lam(st)
            else:
                self.loi(st, f"{self.ten(st)}: khối «{st.get('type')}» không có trong từ điển "
                             f"5 trạm — có thể là file của bản mới hơn.")

        self.mot_quyet_dinh_moi_duong()
        self.co_ket_qua()
        self.soat_gom()

    def mot_quyet_dinh_moi_duong(self):
        """Hai khối Làm `quyet_dinh` trên CÙNG một đường: cái sau lặng lẽ đè cái trước.
        Báo ở cái SAU — đó là cái không bao giờ có tác dụng như người vẽ tưởng."""
        qd = [sid for sid, s in self.theo_id.items()
              if (T.KHOI_LAM.get(s.get("type")) or {}).get("vai") == "quyet_dinh"]
        da_bao = set()
        for sid in qd:
            tham, hang = {sid}, list(self.ke.get(sid, []))
            while hang:
                uv = hang.pop(0)
                if uv in tham:
                    continue
                tham.add(uv)
                if uv in qd and uv not in da_bao:
                    da_bao.add(uv)
                    a, b = self.theo_id[sid], self.theo_id[uv]
                    self.loi(b, f"{self.ten(b)} nằm SAU {self.ten(a)} trên cùng một đường — "
                                f"một lượt chạy tới cả hai thì cái sau đè cái trước. Hãy tách "
                                f"chúng ra hai NHÁNH, mỗi nhánh mở đầu bằng một khối Hỏi.")
                    break
                hang += self.ke.get(uv, [])

    def co_ket_qua(self):
        can = T.CAN_CO.get(self.k)
        if not can:
            return
        toi_duoc = [s for sid, s in self.theo_id.items()
                    if sid in self.nhan and s.get("type") in can]
        if toi_duoc:
            return
        ten = " / ".join(f"«{T.KHOI_LAM[x]['nhan']}»" for x in can)
        ra_gi = {T.CHON_MA: "rổ luôn rỗng", T.TIN_HIEU: "không mã nào có tín hiệu",
                 T.CHIA_VON: "không mã nào được chia vốn",
                 T.KHOP_LENH: "mục tiêu không bao giờ thành lệnh"}[self.k]
        _van_de(self.ra, "error", self.k, None,
                f"Trạm {T.nhan_tram(self.k)} chưa có khối {ten} nào được nối tới từ khối Bắt "
                f"đầu — {ra_gi}, nên cỗ máy không bao giờ giao dịch.")

    def soat_gom(self):
        if self.k not in T.GOM:
            return
        for f in T.GOM[self.k]:
            v = self.gom.get(f["key"])
            if v in (None, ""):
                continue
            cho = f"Gom của trạm {T.nhan_tram(self.k)} — ô «{f['nhan']}»"
            if f["loai"] == "so":
                if isinstance(v, str) and v not in self.ts:
                    _van_de(self.ra, "error", self.k, None,
                            f'{cho} dùng tham số "{v}" không có trong bảng tham số.')
                    continue
                gt = self.ts.get(v) if isinstance(v, str) else v
                if not _la_so(gt):
                    _van_de(self.ra, "error", self.k, None, f"{cho} cần một con số.")
                elif (f.get("nguyen") and gt != int(gt)) or gt < f.get("min", gt) \
                        or gt > f.get("max", gt):
                    _van_de(self.ra, "error", self.k, None,
                            f"{cho} phải {'là số nguyên ' if f.get('nguyen') else ''}trong "
                            f"khoảng {_so(f['min'])}–{_so(f['max'])}.")
            elif f["loai"] == "chon" and v not in f["chon"]:
                _van_de(self.ra, "error", self.k, None, f"{cho} mang giá trị lạ «{v}».")
        if self.k == T.CHON_MA and self.gom.get("top_n") not in (None, ""):
            ko_diem = [s for s in self.theo_id.values()
                       if s.get("type") == "vao_ro" and not s.get("diem")]
            for s in ko_diem:
                self.canh(s, f"{self.ten(s)} không có điểm, mà Gom giữ N mã điểm cao nhất — "
                             f"mã vào rổ qua khối này luôn xếp CUỐI, gần như không bao giờ "
                             f"được giữ.")


def soat(doc):
    """Mọi vấn đề của cỗ máy: `[{severity, tram, step, index, message}]`."""
    ra = []
    if isinstance(doc, dict) and doc.get("dang") not in (None, DANG):
        _van_de(ra, "error", None, None,
                f"Tài liệu dạng «{doc.get('dang')}» không phải cỗ máy 5 trạm.")
        return ra
    may = chuan_hoa(doc)
    for k in T.TRAM_KEYS:
        _Soat(may, k, ra).chay()
    _soat_giua_cac_tram(may, ra)
    return ra


def _cac_khoi(may, tram_key, loai):
    return [s for s in may["tram"][tram_key]["steps"] if s.get("type") == loai]


def _soat_giua_cac_tram(may, ra):
    """Những câu chỉ trả lời được khi nhìn HAI trạm cùng lúc."""
    bao = _cac_khoi(may, T.TIN_HIEU, "bao")
    for st in _cac_khoi(may, T.CHIA_VON, "dat_ty_trong"):
        cach = st.get("cach")
        for o, ten_o in (("tin_cay", "độ tin cậy"), ("trong_so", "trọng số")):
            can = (cach == "theo_tin_cay" and o == "tin_cay") or \
                  (cach == "theo_trong_so" and o == "trong_so")
            if can and bao and not any(b.get(o) not in (None, "") for b in bao):
                hau_qua = ("mọi mã được chia đều" if o == "tin_cay"
                           else "mọi mã được tỷ trọng 0")
                _van_de(ra, "warning", T.CHIA_VON, st.get("id"),
                        f'"{st.get("name")}" chia {T.CACH_CHIA[cach]} nhưng trạm '
                        f"{T.nhan_tram(T.TIN_HIEU)} không khối «Báo tín hiệu» nào đặt "
                        f"{ten_o} — {hau_qua}.")
