"""Cat_Studio — lõi.

Không phụ thuộc giao diện, không import tkinter/webview → test được mà không mở cửa sổ nào.
Mọi hiểu biết về ĐỊNH DẠNG FILE nằm ở đây; `api.py` chỉ chuyển JSON, `webui/` chỉ vẽ.

Ba tầng:  webui/ (vẽ)  →  api.py (cầu nối duy nhất)  →  core.py (lõi)

Xem `tai_lieu/core.md` để hiểu VÌ SAO. File này giữ HÀNH VI.
"""
import datetime as _dt
import json
import re
import uuid

from . import bat_dau
from . import hoi
from . import lam
from . import luu_tru

PHIEN_BAN = "0.2"


# ---------------------------------------------------------------------------
# Thư mục dữ liệu
# ---------------------------------------------------------------------------


load_settings = luu_tru.doc_cai_dat


# ---------------------------------------------------------------------------
# Khung thời gian & ký hiệu
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# LOẠI KHỐI
# ---------------------------------------------------------------------------

# HAI loại khối, không hơn.
#
# Từng có thêm "Vòng theo dõi" (lặp mỗi nến) và "Nhóm 1 lần" (gộp nhiều hành động).
# Bỏ cả hai, vì cả hai đều thừa:
#
#   · Vòng theo dõi — CẢ SƠ ĐỒ vốn đã là một vòng lặp: nó chạy lại từ khối Bắt đầu ở
#     mỗi nến mới, đúng như `OnTick` của MQL5 chạy lại từ đầu mỗi tick. "Chờ tới khi"
#     không cần vẽ: không cổng nào khớp thì hết lượt, nến sau tự chạy lại.
#   · Nhóm — TRƯỚC ĐÂY BỊ TỪ CHỐI ở đây, với lý do "gộp nhóm chỉ đẻ thêm câu hỏi
#     nhóm có phải một đơn vị chạy không". Lý do ấy SAI, và một sơ đồ thật đã chứng
#     minh: nó gộp 2.253 hành động vào 243 Nhóm, nếu không thì canvas có 3.180 hộp
#     thay vì 1.170 — gấp ba, và hết đọc nổi.
#     Câu hỏi kia có câu trả lời: Nhóm KHÔNG phải một đơn vị chạy. Nó là một hộp
#     chứa một CHUỖI hành động chạy thẳng một lượt, không lặp, không rẽ. Đúng bằng
#     ngần ấy khối lẻ nối thành hàng, chỉ khác là vẽ gọn lại một chỗ.
KIND_START = "start"     # điểm neo đánh số — mỗi nến chạy lại từ đây
KIND_ACTION = "action"   # đúng một hành động
KIND_GROUP = "group"     # một CHUỖI hành động gói vào một hộp, chạy thẳng một lượt


def is_start_step(s):
    return isinstance(s, dict) and s.get("kind") == KIND_START


def is_group_step(s):
    """Khối NHÓM — hộp ôm một chuỗi hành động.

    Cố ý KHÔNG cho Nhóm làm cổng rẽ nhánh (xem `is_branch_gate`): ở điểm rẽ các nhánh
    được thử lần lượt nên nhánh trượt phải LÙI LẠI ĐƯỢC, mà một Nhóm có thể đã đặt
    lệnh rồi mới tới chỗ kiểm tra — cú đặt lệnh ấy không rút lại được."""
    return isinstance(s, dict) and s.get("kind") == KIND_GROUP


def hanh_dong_cua(s):
    """Danh sách hành động bên trong một Nhóm; khối khác trả danh sách rỗng."""
    return list(s.get("actions") or []) if is_group_step(s) else []


# ---------------------------------------------------------------------------
# HÀNH ĐỘNG
# ---------------------------------------------------------------------------

# BA ĐỘNG TỪ: ĐỌC — TẠO — SỬA. Đủ để diễn tả mọi chiến lược, không thừa cái nào.
#
#   check_cond  ĐỌC  thị trường + tài khoản rồi quyết đi nhánh nào  (cũng là CỔNG rẽ nhánh)
#   vao_lenh    TẠO  một vị thế mới, kèm SL/TP ban đầu
#   sua_lenh    SỬA  một lệnh ĐÃ CÓ: dời SL, dời TP, hoà vốn, trailing, đóng, huỷ chờ
#
# Mấy khái niệm tưởng là hành động riêng thật ra tan hết vào ba cái trên:
#   "cầu dao"  -> toán hạng tài khoản/thời gian trong check_cond (so_lenh_mo, drawdown_pt, gio)
#   "cổng"     -> chính là check_cond đứng đầu một nhánh
#   "kích hoạt"-> không phải hành động mà là LOẠI KHỐI "Vòng theo dõi" (chờ tới khi thoả)
#   "thoát"    -> chế độ "đóng" / "huỷ chờ" của sua_lenh
CHECK_COND = "check_cond"



# Nhãn THUẦN CHỮ, không emoji: chúng hiện ở dropdown "Loại:" của hộp thoại, và giao
# diện tự vẽ icon nét theo `type` cho khớp phần còn lại.


def make_tham_so(ten, nhan, gia_tri, don_vi="", ghi_chu=""):
    return {"ten": ten, "nhan": nhan or ten, "gia_tri": gia_tri,
            "don_vi": don_vi, "ghi_chu": ghi_chu}


# ---------------------------------------------------------------------------
# Định danh khối
# ---------------------------------------------------------------------------


def new_step_id():
    """ID bền cho một khối.

    Đồ thị cần định danh KHÔNG ĐỔI khi khối bị kéo sang chỗ khác hay đổi tên:
    dùng số thứ tự thì kéo-thả một cái là mọi đường nối trỏ sai, dùng tên thì đổi
    tên một cái là gãy."""
    return "s" + uuid.uuid4().hex[:8]


def ensure_step_ids(steps):
    """Cấp id cho khối chưa có, và dọn id trùng. Sửa TẠI CHỖ rồi trả lại chính nó."""
    da_dung = set()
    for st in steps or []:
        if not isinstance(st, dict):
            continue
        sid = st.get("id")
        if not sid or sid in da_dung:
            sid = new_step_id()
            st["id"] = sid
        da_dung.add(sid)
    return steps


# ---------------------------------------------------------------------------
# Dựng khối
# ---------------------------------------------------------------------------


def step_title(step):
    """Tên khối cho câu báo lỗi. Khối đi qua chuẩn hoá đều CÓ tên, nên nhánh cuối chỉ
    là lưới an toàn."""
    ten = (step.get("name") or "").strip()
    if ten:
        return ten
    if is_start_step(step):
        return "Bắt đầu"
    if is_group_step(step):
        return "Nhóm"
    return "Quay về" if step.get("type") == QUAY_VE else "Khối"


# ---------------------------------------------------------------------------
# Dựng khối
# ---------------------------------------------------------------------------


def make_start_step(name="Bắt đầu"):
    """Khối BẮT ĐẦU — nửa `initialize` của thuật toán, mọi ô đã điền mặc định.

    Trước D-15 khối này chỉ có cái tên: sơ đồ vẽ được nửa `on_data` mà không có chỗ
    nào nói chạy trên mã gì, từ ngày nào, bao nhiêu tiền. Xem `bat_dau.py`."""
    st = {"kind": KIND_START, "id": new_step_id(), "name": name}
    for o in bat_dau.o_cua():
        st[o["ten"]] = _chep_sau(o["mac_dinh"])
    return st


def _chep_sau(v):
    """Chép sâu một giá trị mặc định.

    ⚠ Không có hàm này thì MỌI khối Bắt đầu dùng chung đúng một list/dict mặc định —
    sửa danh sách mã của khối này là khối kia đổi theo. Bẫy cũ của Python, và nó im
    lặng cho tới lúc có hai khối."""
    if isinstance(v, dict):
        return {k: _chep_sau(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_chep_sau(x) for x in v]
    return v


def o_bat_dau(step, ten):
    """Giá trị một ô của khối Bắt đầu, rơi về mặc định của từ điển nếu khối chưa có.

    Nhờ hàm này mà file cũ (lưu khi khối Bắt đầu còn trống ruột) mở ra vẫn chạy."""
    if isinstance(step, dict) and ten in step:
        return step[ten]
    for o in bat_dau.o_cua(step):
        if o["ten"] == ten:
            return _chep_sau(o["mac_dinh"])
    return None


def make_group_step(name="Nhóm mới"):
    """Nhóm: nhiều hành động, chạy đúng MỘT lượt, không lặp.

    Cố ý không có số vòng: nhóm không lặp nên ô ấy vô nghĩa, có mặt chỉ tổ hiểu nhầm."""
    return {"kind": KIND_GROUP, "id": new_step_id(), "name": name, "actions": []}


def make_action_step(action):
    """Một hành động lẻ thành một khối.

    GIỮ id cũ nếu có: giao diện thay cả khối mỗi lần sửa xong hành động, cấp id mới ở
    đây thì mỗi lần bấm "Sửa" là khối đó thành một nút khác và mất hết đường nối."""
    st = dict(action or {})
    st["kind"] = KIND_ACTION
    st["id"] = st.get("id") or new_step_id()
    return st


#: Mấy khoá chỉ có nghĩa với một KHỐI trên canvas, không có nghĩa với một hành động
#: nằm trong Nhóm: `kind`/`id` do `make_action_step` gắn, `pos`/`hat_nhan`/`mau` do
#: giao diện gắn. Gom thì gỡ đúng mấy khoá này, tách thì cấp lại.
_KHOA_CUA_KHOI = ("kind", "id", "pos", "hat_nhan", "mau")


def gom_nhom(steps, ten=None):
    """Gộp nhiều KHỐI HÀNH ĐỘNG thành MỘT Nhóm. -> (nhóm, lỗi)

    BÓC KHỐI THÀNH HÀNH ĐỘNG Ở ĐÂY, không để giao diện tự làm. "Một khối khác một
    hành động ở chỗ nào" là kiến thức của `core`, và hai nơi cùng quyết một thứ là
    hai nơi để trôi khỏi nhau.

    `name` thì GIỮ: nó là chữ người dùng đặt, nhờ vậy gom rồi tách lại không mất tên.

    CHỈ GOM KHỐI HÀNH ĐỘNG. Nhét một khối Hỏi vào `actions` thì bộ sinh mã duyệt nó
    như một hành động — mà một cổng rẽ nhánh không phải hành động, nên nó sẽ lặng lẽ
    không sinh ra gì. Chặn ở đây, nói rõ vì sao.

    ⚠ LỌC THEO `type`, KHÔNG THEO `kind`. Khối Hỏi và khối Quay về cũng mang
    `kind = "action"` — `kind` chỉ nói "đây là một khối thường trên canvas", còn thứ
    phân biệt việc với câu hỏi là `type`. Bản đầu của hàm này lọc theo `kind` nên nó
    nhận cả khối Xác nhận vào Nhóm; bắt được lúc chạy thử."""
    ds = [s for s in (steps or []) if isinstance(s, dict)]
    if not ds:
        return None, "Chưa chọn khối nào để gom."
    la = [s for s in ds if not lam.la_loai_lam(s.get("type"))]
    if la:
        return None, ("Chỉ gom được khối HÀNH ĐỘNG. Bỏ chọn khối Bắt đầu, Xác nhận, "
                      "Quay về và Nhóm — chúng không phải một việc để xếp vào hàng.")
    nhom = make_group_step(ten or ten_nhom_tu(ds))
    for s in ds:
        nhom["actions"].append({k: v for k, v in s.items()
                                if k not in _KHOA_CUA_KHOI})
    return nhom, ""


def ten_nhom_tu(ds):
    """Tên gợi sẵn cho Nhóm vừa gom: mấy MÃ nó đụng tới, như thẻ khối vẫn hiện.

    "Nhóm mới" thì phải mở ra mới biết bên trong có gì; "QQQ · XLE · GLD" thì nhìn
    một cái là biết — và đó đúng là chữ `the_buoc` đã dựng cho Nhóm từ trước."""
    ma = []
    for s in ds:
        m = str((s or {}).get("ma") or "").strip()
        if m and m not in ma:
            ma.append(m)
    return " · ".join(ma) if ma else "Nhóm mới"


def ra_nhom(step):
    """Tách một Nhóm thành từng KHỐI HÀNH ĐỘNG. Ngược đúng `gom_nhom`. -> (ds, lỗi)

    Cấp id MỚI ở đây: định dạng id là kiến thức của `new_step_id`, và một hành động
    nằm trong Nhóm thì chưa bao giờ có id của riêng nó."""
    if not is_group_step(step):
        return [], "Chỉ tách được khối Nhóm."
    ds = [make_action_step({k: v for k, v in a.items() if k != "id"})
          for a in hanh_dong_cua(step) if isinstance(a, dict)]
    if not ds:
        return [], "Nhóm này chưa có hành động nào để tách."
    return ds, ""


def make_hoi_step(loai, name=None):
    """Một khối XÁC NHẬN rỗng của loại `loai` (xem `hoi.LOAI_HOI`)."""
    d = hoi.LOAI_HOI.get(loai)
    if not d:
        raise ValueError(f"không có loại hỏi {loai!r}")
    return {"kind": KIND_ACTION, "id": new_step_id(), "type": loai,
            "name": name or d["nhan"], "dieu_kien": []}


def make_lam_step(loai, name=None):
    """Một khối HÀNH ĐỘNG của loại `loai`, mọi ô ĐÃ điền mặc định (`lam.LOAI_LAM`).

    Điền sẵn chứ không để rỗng, khác khối Hỏi: khối vừa thả ra đã đọc được thành câu,
    và bảng Vấn đề không nổi một tràng lỗi về thứ người chơi chưa kịp chạm tới."""
    d = lam.LOAI_LAM.get(loai)
    if not d:
        raise ValueError(f"không có loại hành động {loai!r}")
    st = {"kind": KIND_ACTION, "id": new_step_id(), "type": loai,
          "name": name or d["nhan"]}
    for o in lam.o_cua(loai):
        st[o["ten"]] = o["mac_dinh"]
    if d.get("co_dai_luong"):
        # Mặc định do TỪ ĐIỂN khai, không gõ cứng ở đây. «Giá trị vẽ» thì rỗng — không
        # có đại lượng nào đáng đoán hộ; «Trọng số» thì là số 1 — bỏ trống nó là
        # `insight.weight = None`, và model chia theo trọng số lặng lẽ ra 0 lệnh.
        st["gia_tri"] = dict(d.get("gia_tri_mac_dinh") or {})
    return st


def o_lam(step, ten):
    """Giá trị một ô của khối Làm, rơi về mặc định của từ điển nếu khối chưa có ô ấy.

    Nhờ hàm này mà file cũ (lưu trước khi thêm một ô) mở ra vẫn đọc được, không phải
    di cư gì."""
    if isinstance(step, dict) and ten in step:
        return step[ten]
    for o in lam.o_cua((step or {}).get("type"), step):
        if o["ten"] == ten:
            return o["mac_dinh"]
    return None


def _chon_lam(loai, ten, step=None):
    """Danh sách lựa chọn của một ô CHỌN -> [(mã, nhãn)]."""
    for o in lam.o_cua(loai, step):
        if o["ten"] == ten:
            return o["chon"]
    return []


def _f(v):
    """-> float, hay None nếu không phải số. Không ném, vì file có thể sửa tay."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _so_gon(n):
    """Số -> chữ gọn, bỏ đuôi `.0`: "30%" đọc dễ hơn "30.0%"."""
    f = _f(n)
    if f is None:
        return str(n)
    return str(int(f)) if f.is_integer() else str(round(f, 6))


def _pt(v):
    """Phần (0.3) -> phần trăm đọc được ("30"). Làm tròn vì 0.3*100 ra 30.000000004."""
    f = _f(v)
    return "?" if f is None else _so_gon(round(f * 100, 6))


def _ngay_vn(s):
    """"2010-01-01" -> "01/01/2010". Hỏng khuôn thì trả nguyên xi, đừng ném."""
    p = str(s or "").split("-")
    return f"{p[2]}/{p[1]}/{p[0]}" if len(p) == 3 and all(p) else str(s or "?")


def _tien(n):
    """100000 -> "100.000". Dấu chấm phân nhóm, như người Việt vẫn viết."""
    f = _f(n)
    return str(n) if f is None else f"{int(f):,}".replace(",", ".")


def mo_ta_bat_dau(step):
    """Khối BẮT ĐẦU -> mấy dòng chữ trên thẻ."""
    gt_ma = o_bat_dau(step, "ma")
    ro = bat_dau.ro_cua(gt_ma)
    ds = [] if ro else (gt_ma or [])
    ten_loai = {m: n for m, n, _h in bat_dau.LOAI_TAI_SAN}
    if ro:
        # RỔ phải hiện NGUYÊN câu của nó, kể cả mã ETF và số mã lấy: "rổ ETF" chung
        # chung thì thẻ khối không nói nổi hai cỗ máy khác nhau ở chỗ nào.
        dong = [f"rổ: {ro[1]}"]
        if ro[0] == "etf":
            lay = _f(bat_dau.gt_ro(gt_ma, "lay")) or 0
            etf = str(bat_dau.gt_ro(gt_ma, "ma_etf") or "").strip().upper() or "?"
            dong = [f"rổ {etf}" + (f" · {int(lay)} mã nặng nhất" if lay > 0
                                   else " · cả rổ")]
    elif not ds:
        dong = ["chưa chọn mã nào"]
    elif len(ds) == 1:
        m = ds[0]
        dong = [f"{m.get('ma') or '?'} · {ten_loai.get(m.get('loai'), m.get('loai'))}"]
    else:
        dong = [f"{len(ds)} mã: " + ", ".join(str(m.get("ma") or "?") for m in ds)]
    k = o_bat_dau(step, "khoang") or {}
    dong.append(f"{_ngay_vn(k.get('tu'))} → {_ngay_vn(k.get('den'))}")
    dong.append(f"vốn {_tien(o_bat_dau(step, 'von'))}$")
    moc = str(o_bat_dau(step, "moc_so_sanh") or "").strip()
    if moc:
        dong.append(f"mốc so sánh: {moc}")
    return dong


def mo_ta_lam(step):
    """Khối HÀNH ĐỘNG -> mấy dòng chữ trên thẻ. BẢNG TRA, mỗi loại một câu viết tay.

    Cùng lý do như `mo_ta_dieu_kien`: giao diện KHÔNG tự ghép chữ này, vì nếu nó ghép
    thì sớm muộn nó tả khác với thứ bộ sinh mã thật sự viết ra."""
    t = (step or {}).get("type")
    d = lam.LOAI_LAM.get(t)
    if not d:
        return ["?"]

    def g(ten):
        return o_lam(step, ten)

    def nhan_chon(ten):
        v = str(g(ten) or "")
        return next((n for m, n in _chon_lam(t, ten, step) if m == v), v)

    dong = []
    if t == lam.LAM_DAT_TY_TRONG:
        p = _f(g("ty_trong"))
        if p is None:
            dong.append("Đặt tỷ trọng ?")
        elif p == 0:
            dong.append("Đặt tỷ trọng 0% — thoát sạch mã này")
        else:
            dong.append(f"Đặt tỷ trọng {_pt(p)}%" + (" — bán khống" if p < 0 else ""))
        if g("ban_sach_truoc") is True:
            dong.append("bán sạch mọi mã KHÁC trước")

    elif t == lam.LAM_LENH_THI_TRUONG:
        q = _f(g("so_luong"))
        dong.append("Lệnh thị trường ?" if q is None else
                    f"{'Mua' if q >= 0 else 'Bán'} {_so_gon(abs(q))} đơn vị, khớp ngay")

    elif t == lam.LAM_DONG:
        dong.append("Đóng TẤT CẢ mã đang giữ" if g("pham_vi") == "tat_ca"
                    else "Đóng mã này")

    elif t == lam.LAM_LENH_CHO:
        ll = str(g("loai_lenh") or "")
        q = _f(g("so_luong")) or 0
        # Nhãn loại lệnh có dạng "Giới hạn (Limit)" — trên thẻ lấy phần tiếng Việt.
        cau = (f"{nhan_chon('loai_lenh').split(' (')[0]}: "
               f"{'mua' if q >= 0 else 'bán'} {_so_gon(abs(q))}")
        if ll == "limit":
            cau += f" @ {_so_gon(g('gia_gh'))}"
        elif ll == "stop":
            cau += f", chạm {_so_gon(g('gia_kh'))}"
        elif ll == "stop_limit":
            cau += f", chạm {_so_gon(g('gia_kh'))} -> giới hạn {_so_gon(g('gia_gh'))}"
        elif ll == "trailing":
            cau += (f", trượt {_pt(g('khoang_truot'))}%"
                    if g("truot_theo_pt") is not False
                    else f", trượt {_so_gon(g('khoang_truot'))} tiền")
        elif ll == "lit":
            cau += f", chạm {_so_gon(g('gia_cham'))} -> giới hạn {_so_gon(g('gia_gh'))}"
        dong.append(cau)

    elif t == lam.LAM_HUY_LENH_CHO:
        dong.append("Huỷ hết lệnh chờ của mã này")

    elif t == lam.LAM_GHI_CHU:
        ngan = nhan_chon("muc").split(" — ")[0]
        cau = str(g("cau") or "").strip()
        dong.append(f"{ngan}: «{cau}»" if cau else f"{ngan} — câu để bộ sinh mã điền")

    elif t == lam.LAM_VE_BANG:
        gt = step.get("gia_tri")
        chu = (_ve_dieu_kien(gt)
               if isinstance(gt, dict) and gt.get("ma_dl") else "chưa chọn đại lượng")
        dong.append(f"Vẽ {chu}")
        dong.append(f"bảng «{g('bang')}» · đường «{g('ten_duong')}»")

    elif t == lam.LAM_TIN_HIEU:
        huong = {"UP": "LÊN", "DOWN": "XUỐNG", "FLAT": "PHẲNG"}.get(
            str(g("huong") or ""), "?")
        han = _f(g("han"))
        if huong == "PHẲNG":
            # FLAT là "thôi giữ mã này", nên nói theo việc chứ đừng nói "tín hiệu
            # PHẲNG giữ 1 ngày" — câu ấy đúng chữ mà sai nghĩa.
            dong.append("Thôi giữ — bỏ tín hiệu cũ")
        else:
            # `_so_gon`, KHÔNG phải `_pt`: `_pt` là bộ in phần trăm, nó nhân 100 — ô
            # «Giữ tối đa 15 ngày» đọc ra "1500 ngày".
            dong.append(f"Tín hiệu {huong}"
                        + (f" · giữ tối đa {_so_gon(han)} ngày" if han else ""))
        # TRỌNG SỐ chỉ nói ra khi nó KHÁC 1. Mặc định 1 nghĩa là "mọi mã ngang nhau",
        # tức không xếp hạng gì — bày nó lên thẻ chỉ làm rối thẻ.
        gt = step.get("gia_tri")
        if isinstance(gt, dict) and gt.get("ma_dl"):
            dong.append(f"trọng số: {_ve_dieu_kien(gt)}")
        elif isinstance(gt, dict) and _f(gt.get("so")) not in (None, 1):
            dong.append(f"trọng số: {_so_gon(_f(gt.get('so')))}")

    elif t == lam.LAM_BAO_TIN:
        dich = str(g("dich") or "").strip()
        dong.append(f"{nhan_chon('kenh')} -> {dich or '(chưa có nơi gửi)'}")
        cau = str(g("cau") or "").strip()
        if cau:
            dong.append(f"«{cau}»")

    # MÃ đứng đầu dòng khi khối trỏ tới một mã cụ thể. Thiếu chỗ này thì một Nhóm ba
    # dòng "Đặt tỷ trọng 40% / 35% / 20%" không nói được nó chia cho những mã nào —
    # đúng thứ người đọc sơ đồ cần biết nhất ở một chiến thuật chia danh mục.
    ma = str(g("ma") or "").strip().upper()
    if ma and dong:
        dong[0] = f"{ma} · {dong[0]}"

    # NÚM ĐÃ GHIM nói ở MỘT dòng chung, không nhét vào từng nhánh. `mo_ta_lam` là
    # bảng tra chín nhánh; sửa riêng từng nhánh là lại đúng cái bẫy "thêm loại quên
    # thêm nhánh" đã làm cả ba khối Phát tín hiệu hiện dấu «?».
    ghim = [f'{o["nhan"]} → {step["ghim"][o["ten"]]}'
            for o in lam.o_cua(t, step)
            if o["kieu"] == lam.O_SO
            and str(((step or {}).get("ghim") or {}).get(o["ten"]) or "").strip()]
    if ghim:
        dong.append("núm: " + " · ".join(ghim))

    tag = str(g("tag") or "").strip()
    if tag:
        dong.append(f"ghi chú lệnh: «{tag}»")
    return dong or ["?"]


def make_dieu_kien(ma_dl, phep=">", so=0.0, ma=None, tham_so=None, duong=None):
    """Một DÒNG điều kiện.

    Hình: {trai, phep, phai}. Hai vế rút từ cùng kho đại lượng, nên vế phải có thể là
    một con số (`{"so": 30}`) hoặc một đại lượng khác (`{"ma_dl": …}`) — chính chỗ này
    làm được "so sánh chéo mã" mà không cần tính năng riêng nào."""
    trai = {"ma_dl": ma_dl}
    if ma:
        trai["ma"] = ma
    if tham_so:
        trai["tham_so"] = dict(tham_so)
    if duong:
        trai["duong"] = duong
    return {"trai": trai, "phep": phep, "phai": {"so": so}}


def make_quay_ve_step(ve=None, so_vong=None, name=None):
    """Khối QUAY VỀ — nhảy ngược lên một khối phía trước.

    `so_vong` None = lặp mãi (hết lượt thì nến sau tự chạy lại từ khối Bắt đầu)."""
    st = {"kind": KIND_ACTION, "id": new_step_id(), "type": QUAY_VE,
          "name": name or "Quay về", "ve": ve or ""}
    if so_vong:
        st["so_vong"] = int(so_vong)
    return st


# ---------------------------------------------------------------------------
# Mô tả hành động — CHỮ HIỆN TRÊN HỘP DO ĐÂY SINH
# ---------------------------------------------------------------------------
# Giao diện KHÔNG tự ghép câu. Nếu nó ghép thì sớm muộn nó mô tả khác với thứ lõi thật
# sự hiểu, và người dùng tin vào cái sai. Bản vẽ SVG gửi đi nơi khác cũng gọi đúng
# mấy hàm này, không chép lại.


def _ve_dieu_kien(ve):
    """Một VẾ của dòng điều kiện -> chữ. Dùng cho cả vế trái lẫn vế phải."""
    if not isinstance(ve, dict):
        return "?"
    if "so" in ve and "ma_dl" not in ve:
        n = ve["so"]
        # Số nguyên thì đừng in ".0" — "RSI < 30" đọc dễ hơn "RSI < 30.0".
        chu = str(int(n)) if isinstance(n, float) and n.is_integer() else str(n)
        return _ghep_chu(ve, _so_the(ve, "so", chu))
    dl = hoi.dai_luong(ve.get("ma_dl"))
    if not dl:
        return str(ve.get("ma_dl") or "?")
    chu = dl["nhan"]
    # Tham số hiện trong ngoặc: "EMA — trung bình trượt luỹ thừa" quá dài trên thẻ,
    # nên lấy phần TRƯỚC dấu gạch làm tên ngắn.
    ngan = chu.split(" — ")[0]
    ts = ve.get("tham_so") or {}
    if ts:
        ngan += "(" + ",".join(_so_the(ve, k, v) for k, v in ts.items()) + ")"
    if ve.get("duong"):
        ngan += "." + str(ve["duong"])
    if ve.get("ma"):
        ngan = f"{ve['ma']}·{ngan}"
    return _ghep_chu(ve, ngan)


def _so_the(chu, ten_o, gia_tri):
    """Con số trên THẺ KHỐI — hay TÊN THAM SỐ nếu ô ấy đã ghim.

    Ghim rồi mà thẻ vẫn đọc "RSI(14)" thì nhìn sơ đồ không biết mình đã ghim cái gì,
    và lúc Optimize quét `rsi_chu_ky` thì chẳng thấy nó ở đâu trên canvas."""
    ten = str(((chu or {}).get("ghim") or {}).get(ten_o) or "").strip()
    return ten or str(gia_tri)


def _ghep_chu(ve, ngan):
    """Thêm phần GHÉP vào chữ của một vế: «Giá hiện tại / Cao nhất N nến(60)».

    ⚠ THIẾU HÀM NÀY LÀ THẺ KHỐI NÓI DỐI. Bộ sinh mã viết `giá / đỉnh 60 nến ≤ 0,97`,
    mà thẻ lại đọc "Giá hiện tại ≤ 0,97" — một câu VÔ LÝ (giá có bao giờ dưới 1 đô)
    nhưng không sai cú pháp nào, nên chẳng ai thấy gì. Đúng thứ `mo_ta_lam` đã cảnh
    báo ngay ở đầu: chữ trên thẻ phải tả ĐÚNG thứ bộ sinh mã thật sự viết ra."""
    ghep = ve.get("ghep") if isinstance(ve.get("ghep"), dict) else None
    if not ghep or not ghep.get("phep"):
        return ngan
    return f"{ngan} {ghep['phep']} {_ve_dieu_kien(ghep)}"


def mo_ta_dieu_kien(dk):
    """Một DÒNG điều kiện -> một dòng chữ trên thẻ khối."""
    if not isinstance(dk, dict):
        return "?"
    trai = _ve_dieu_kien(dk.get("trai"))
    phep = str(dk.get("phep") or ">")
    dl = hoi.dai_luong((dk.get("trai") or {}).get("ma_dl"))
    # Đại lượng ĐÚNG/SAI không so với số nào — "Đang giữ mã này là SAI".
    if dl and dl["kieu"] == hoi.KIEU_CO_KHONG:
        return f"{trai} {'là SAI' if phep == 'khong' else 'là ĐÚNG'}"
    return f"{trai} {phep} {_ve_dieu_kien(dk.get('phai'))}"


def mo_ta_hanh_dong(a):
    """Một dòng chữ tả một hành động. BẢNG TRA theo loại, không ghép câu tự động.

    Giao diện KHÔNG tự ghép chữ này — nếu nó ghép thì sớm muộn nó mô tả khác với thứ
    lõi thật sự hiểu, và người dùng tin vào cái sai."""
    if not isinstance(a, dict):
        return "?"
    t = str(a.get("type") or "?")
    if t == QUAY_VE:
        n = a.get("so_vong")
        return f"Quay về ({n} vòng)" if n else "Quay về"
    if hoi.la_loai_hoi(t):
        ds = a.get("dieu_kien") or []
        return ds and mo_ta_dieu_kien(ds[0]) or "chưa có điều kiện nào"
    # Hành động nằm TRONG một Nhóm chỉ được một dòng, nên nối bằng dấu chấm giữa.
    if lam.la_loai_lam(t):
        return " · ".join(mo_ta_lam(a))
    o = [f"{k}={v}" for k, v in a.items()
         if k not in ("type", "kind", "id", "name", "actions", "dieu_kien")
         + KHOA_CANVAS and v not in (None, "", [], {}, False)]
    return f"{t} · {' · '.join(o[:3])}" if o else t


#: Tên tham số: chữ thường, số và gạch dưới. Đúng khuôn LEAN nhận trong `parameters`
#: của config optimizer, và cũng là khuôn đọc được khi nó hiện trên thẻ khối.
_RE_TEN_THAM_SO = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def _o_so_cua(step):
    """Mọi ô SỐ ghim được của một khối -> [(tên ô, nhãn, giá trị)].

    MỘT chỗ duy nhất trả lời "khối này có những con số nào" — hộp Optimize, phép
    soát và bộ sinh mã đều hỏi ở đây, nên không có cách nào ghim được một ô mà hộp
    Optimize không thấy, hay ngược lại."""
    ra = []
    t = (step or {}).get("type")
    if hoi.la_loai_hoi(t):
        for i, dk in enumerate(step.get("dieu_kien") or []):
            if not isinstance(dk, dict):
                continue
            for ten_ve, ve in (("trái", dk.get("trai")), ("phải", dk.get("phai"))):
                for chu, dau in ((ve, ""), ((ve or {}).get("ghep"), "ghép ")):
                    if not isinstance(chu, dict):
                        continue
                    nhan_ve = f"dòng {i + 1} vế {ten_ve} {dau}".strip()
                    if "ma_dl" not in chu:
                        ra.append((chu, "so", f"{nhan_ve} — con số", chu.get("so", 0)))
                        continue
                    dl = hoi.dai_luong(chu.get("ma_dl")) or {}
                    for ts in dl.get("tham_so") or []:
                        gt = (chu.get("tham_so") or {}).get(ts["ten"], ts["mac_dinh"])
                        ra.append((chu, ts["ten"],
                                   f'{nhan_ve} — {dl["nhan"].split(" — ")[0]} · '
                                   f'{ts["nhan"]}', gt))
    elif lam.la_loai_lam(t):
        for o in lam.o_cua(t, step):
            if o["kieu"] == lam.O_SO:
                ra.append((step, o["ten"], o["nhan"], o_lam(step, o["ten"])))
    return ra


def ds_tham_so(steps):
    """Mọi núm đã GHIM trong sơ đồ -> [{ten, mac_dinh, o_tai}], xếp theo tên.

    Đây là danh sách hộp Optimize bày ra. Nó KHÔNG phải một bảng riêng: nó đọc thẳng
    từ sơ đồ mỗi lần, nên sửa sơ đồ là nó đúng theo ngay — một bảng riêng thì sớm
    muộn trỏ vào một ô đã bị xoá, và lặng lẽ quét một tham số không ai đọc."""
    gom = {}
    for s in steps or []:
        for chu, ten_o, nhan, gt in _o_so_cua(s):
            ten = str((chu.get("ghim") or {}).get(ten_o) or "").strip()
            if not ten:
                continue
            d = gom.setdefault(ten, {"ten": ten, "mac_dinh": gt, "o_tai": []})
            d["o_tai"].append(f"{step_title(s)} · {nhan}")
    return [gom[k] for k in sorted(gom)]


def icon_cua(loai):
    """Tên icon của MỘT loại khối, lấy thẳng từ từ điển. "" nếu loại ấy không có.

    Một chỗ duy nhất trả lời câu "khối này vẽ hình gì" — giao diện chỉ bày lại."""
    # «Quay về» không nằm trong từ điển nào — nó là khối riêng của `core`, nên khai
    # icon của nó ngay cạnh chỗ nó được dựng, không để lạc sang giao diện.
    if loai == QUAY_VE:
        return "quay-ve"
    d = lam.LOAI_LAM.get(loai) or hoi.LOAI_HOI.get(loai) or {}
    return d.get("icon") or ""


def the_buoc(step):
    """Một khối -> DỮ LIỆU vẽ hộp trên canvas (không phải HTML).

    Phía giao diện tự quyết trình bày, nhưng mọi chuỗi mô tả đều do đây sinh ra."""
    kind = step.get("kind")
    hd = hanh_dong_cua(step)

    if kind == KIND_GROUP:
        nhan = ["chạy 1 lần"]
        dong = [{"text": mo_ta_hanh_dong(a), "type": a.get("type")} for a in hd]
    elif kind == KIND_START:
        # Huy hiệu nói NHỊP: đó là thứ quyết cả sơ đồ chạy bao lâu một lần, nên nó
        # phải đọc được mà không cần mở khối ra.
        n = bat_dau.nhip_cua(str(o_bat_dau(step, "nhip") or ""))
        nhan = [n[1]] if n else []
        dong = [{"text": x, "type": None} for x in mo_ta_bat_dau(step)]
    elif hoi.la_loai_hoi(step.get("type")):
        # KHỐI HỎI: MỖI điều kiện một dòng, nối bằng VÀ. Nhồi thành một chuỗi dài là
        # thẻ cắt cụt mất vế phải — đúng chỗ người ta cần đọc nhất.
        ds = step.get("dieu_kien") or []
        nhan = [hoi.LOAI_HOI[step["type"]]["nhan"]]
        if len(ds) > 1:
            nhan.append(f"{len(ds)} điều kiện · VÀ")
        dong = ([{"text": mo_ta_dieu_kien(dk), "type": step["type"]}
                 for dk in ds]
                or [{"text": "chưa có điều kiện nào", "type": step["type"]}])
    elif lam.la_loai_lam(step.get("type")):
        d = lam.LOAI_LAM[step["type"]]
        nhan = [d["nhan"]]
        if d.get("tat"):
            # Huy hiệu nói thẳng trên thẻ, không đợi người ta mở bảng Vấn đề.
            nhan.append("chỉ chạy thật")
        dong = [{"text": x, "type": step["type"]} for x in mo_ta_lam(step)]
    else:
        nhan = ["chạy 1 lần"]
        dong = [{"text": mo_ta_hanh_dong(step), "type": step.get("type")}]

    # ICON ĐI KÈM TỪNG DÒNG, lấy từ chính từ điển đã khai nó.
    #
    # ⚠ TRƯỚC ĐÂY GIAO DIỆN TỰ TRA, và bảng tra ấy còn giữ năm tên từ một thiết kế cũ
    # (`check_cond`, `vao_lenh`…). Loại khối đã đổi tên hết, nên phép tra luôn trượt,
    # rơi về `?? ''`, và MỌI dòng trong thân thẻ mất icon — không lỗi, không cảnh báo.
    # Nay chỉ còn MỘT chỗ khai: từ điển. Thêm loại khối là icon có ngay.
    for d in dong:
        d["icon"] = icon_cua(d.get("type"))

    return {
        "id": step.get("id"),
        "kind": kind,
        "title": step_title(step),
        "badges": nhan,
        "lines": dong,
        "so_hanh_dong": len(hd) if kind == KIND_GROUP else (0 if kind == KIND_START else 1),
        # Cổng rẽ nhánh: giao diện vẽ khác đi, và bảng Vấn đề tra cùng một hàm.
        "la_cong": is_branch_gate(step),
    }


# ---------------------------------------------------------------------------
# Nhân bản
# ---------------------------------------------------------------------------


def clone_steps(steps, edges=None, giu_hat_nhan=False):
    """Chép một mảng khối + dây GIỮA chúng, cấp id mới. -> (khối mới, dây mới, bảng id).

    Hai chỗ dễ sai, cả hai đều im lặng:

    · Dây trỏ ra NGOÀI mảng được chép thì bỏ — chép 3 khối giữa sơ đồ mà kéo theo dây
      đi tới khối thứ tư là bản dán dính vào bản gốc.
    · Khối Quay về có đích NẰM NGOÀI mảng được chép thì ĐỂ TRỐNG đích. Giữ đích cũ là
      bản dán nhảy về chỗ của bản gốc: sửa bên này đổi đường đi bên kia. Bảng Vấn đề
      sẽ nhắc chọn lại — thà nhắc còn hơn chạy sai lặng lẽ.

    `giu_hat_nhan` False = bỏ khoá hạt nhân (khối rời). Giao diện tự gắn lại cho đúng
    lớp đang đứng."""
    ds = [s for s in (steps or []) if isinstance(s, dict) and s.get("id")]
    bang = {}
    moi = []
    for s in ds:
        c = json.loads(json.dumps(s))     # chép sâu: `actions` không được dùng chung
        c["id"] = new_step_id()
        bang[s["id"]] = c["id"]
        if not giu_hat_nhan:
            c.pop("hat_nhan", None)
        moi.append(c)
    for c in moi:
        if c.get("type") == QUAY_VE:
            c["ve"] = bang.get(str(c.get("ve") or ""), "")
    day = []
    for e in (edges or []):
        if not isinstance(e, dict):
            continue
        a, b = bang.get(e.get("from")), bang.get(e.get("to"))
        if a and b:
            n = dict(e)
            n["from"], n["to"] = a, b
            day.append(n)
    return moi, day, bang
# Giao diện không tự ghép câu: nếu nó ghép thì sớm muộn nó mô tả khác với thứ lõi
# thực sự hiểu, và người dùng tin vào cái sai.


# ---------------------------------------------------------------------------
# QUAY VỀ — vòng lặp VẼ RA, thay vì để ngầm
# ---------------------------------------------------------------------------
# Trước đây lõi này nói: "CẢ SƠ ĐỒ vốn đã là một vòng lặp, chạy lại từ khối Bắt đầu ở
# mỗi nến mới, nên không cần vẽ vòng". Đúng, nhưng CHƯA ĐỦ: vòng ngầm chỉ quay về ĐÚNG
# MỘT chỗ (khối Bắt đầu). Một sơ đồ thật cần quay về giữa chừng — thử lại đúng một
# đoạn, không phải chạy lại cả lượt.
#
# MỘT BẢNG, HAI CÁCH KHAI: đường ↻ kéo tay mang số vòng (`so_vong_canh`), và khối
# Quay về điền đích (`khoi_quay_ve`). Cả hai đổ vào `canh_vong`, nên bộ chạy và bộ
# đánh số chỉ phải đọc một chỗ.

QUAY_VE = "quay_ve"


def so_vong_canh(e):
    """Số vòng ghi trên một ĐƯỜNG ↻, hay None nếu đó là dây thường.

    Có khoá `so_vong` tức đây là đường quay lại — kể cả khi giá trị là 0/None, vì
    "quay lại mãi" cũng là quay lại."""
    if not isinstance(e, dict) or "so_vong" not in e:
        return None
    n = e.get("so_vong")
    if n in (None, "", 0, False):
        return -1                        # -1 = lặp mãi, nhưng VẪN là đường ↻
    try:
        n = int(n)
    except (TypeError, ValueError):
        return -1
    return n if n >= 1 else -1


def khoi_quay_ve(st):
    """(id khối đích, số vòng | None) của một khối Quay về; None nếu không phải.

    `None` ở số vòng = lặp mãi — thứ đường ↻ cũng khai được bằng số 0."""
    if not isinstance(st, dict) or st.get("type") != QUAY_VE:
        return None
    ve = str(st.get("ve") or "").strip()
    if not ve:
        return None                      # chưa chọn đích: `validate_flow_graph` nói
    n = st.get("so_vong")
    if n in (None, "", 0, False):
        return ve, None
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ve, None
    return ve, (n if n >= 1 else None)


def canh_vong(edges, steps=None):
    """{id khối cuối vòng: (id khối đầu vòng, số vòng | None)} — MỌI vòng của sơ đồ.

    Một khối chỉ quay lại được MỘT chỗ; vẽ hai đường ↻ ra từ một khối là mâu thuẫn —
    `validate_flow_graph` báo lỗi, còn ở đây lấy cái đầu để bộ chạy vẫn chạy được."""
    ra = {}
    for e in (edges or []):
        n = so_vong_canh(e)
        if n and e.get("from") and e.get("to") and e["from"] not in ra:
            ra[e["from"]] = (e["to"], None if n < 0 else n)
    for st in (steps or []):
        q = khoi_quay_ve(st)
        if q and st.get("id") and st["id"] not in ra:
            ra[st["id"]] = q
    return ra


# ---------------------------------------------------------------------------
# ĐỒ THỊ
# ---------------------------------------------------------------------------

# Trần số bước chạy trong 1 chiến lược. Đồ thị CHO PHÉP nối ngược lên trên (vòng lặp),
# nên phải có chốt chặn — nếu không, một cái nối sai là chạy mãi không dừng.
MAX_PROCESS_STEPS = 10000


def _khoa_nhanh(step):
    """Khoá sắp thứ tự ưu tiên nhánh: CẠNH QUAY LẠI xuống cuối, rồi TRÊN→DƯỚI, TRÁI→PHẢI.

    Vì sao lấy vị trí trên canvas chứ không phải thứ tự tạo dây: thứ tự tạo dây là thứ
    VÔ HÌNH — kéo khối cách mấy cũng không đổi, nên người dùng không có cách nào biết
    nhánh nào được thử trước. Vị trí thì nhìn thấy, và nhãn A/B trên huy hiệu đổi ngay
    lúc thả chuột, nên ưu tiên không bao giờ là thứ ngầm.
    Chốt bằng `id` để hai khối chồng khít nhau vẫn ra thứ tự cố định.

    Nhánh trỏ vào khối ĐÃ GHIM luôn xếp CUỐI, bất kể nó nằm đâu trên canvas. Đó là
    cạnh quay lại — nghĩa của nó là "không nhánh nào khớp thì quay về trên", tức đúng
    vai nhánh mặc định. Mà khối quay về gần như luôn nằm phía TRÊN (đầu vòng lặp), nên
    xếp theo vị trí sẽ đẩy nó lên đầu và mọi nhánh dưới nó không bao giờ được thử."""
    pos = step.get("pos") or []
    try:
        x, y = float(pos[0]), float(pos[1])
    except (TypeError, ValueError, IndexError):
        x = y = 0.0
    return (1 if step.get("ghim") else 0, y, x, str(step.get("id") or ""))


#: Hai đầu nhánh chênh nhau ÍT HƠN chừng này pixel thì coi như NGANG NHAU — mắt không
#: phân biệt được cái nào trên, mà `_khoa_nhanh` vẫn phải chọn một thứ tự. Xem
#: `_soat_thu_tu_nhanh`.
LECH_TOI_THIEU = 8.0


def flow_map(steps, edges):
    """(bảng_tra_id, kế_tiếp) với `kế_tiếp[id] = [id, ...]` THEO ĐÚNG THỨ TỰ ƯU TIÊN.

    ĐÂY LÀ NGUỒN SỰ THẬT DUY NHẤT VỀ THỨ TỰ NHÁNH — cả bộ đánh số lẫn bộ chạy đều
    chỉ lấy thứ tự từ đây, nên huy hiệu không thể ghi A trước B mà máy lại thử B trước."""
    theo_id = {s.get("id"): s for s in (steps or [])
               if isinstance(s, dict) and s.get("id")}
    ke = {}
    for e in (edges or []):
        if not isinstance(e, dict) or (e.get("port") or "out") != "out":
            continue
        if so_vong_canh(e):
            continue      # đường ↻ không phải một nhánh đi tiếp — xem `canh_vong`
        a, b = e.get("from"), e.get("to")
        if a in theo_id and theo_id[a].get("type") == QUAY_VE:
            # Khối Quay về KHÔNG có lối đi tiếp: chạy tới đó là nhảy về, hết vòng là
            # hết nhánh. Nối ra từ nó chỉ là dây thừa — bảng Vấn đề nói ra, còn ở đây
            # bỏ qua để bộ đánh số không vẽ một nhánh không bao giờ đi.
            continue
        if a in theo_id and b in theo_id:
            ds = ke.setdefault(a, [])
            if b not in ds:      # nối hai lần cùng một cặp vẫn chỉ là một nhánh
                ds.append(b)
    for ds in ke.values():
        ds.sort(key=lambda sid: _khoa_nhanh(theo_id[sid]))
    return theo_id, ke


def is_branch_gate(step):
    """Khối này có phải CỔNG của một nhánh không.

    Cổng = khối HĐ lẻ mang đúng một hành động `check_cond`.

    Cố ý KHÔNG cho Nhóm hay Vòng theo dõi làm cổng: ở điểm rẽ các nhánh được thử lần
    lượt, nên nhánh trượt phải LÙI LẠI ĐƯỢC — mà lùi chỉ an toàn khi nhánh đó chưa kịp
    làm gì ra thị trường. Một khối `check_cond` chỉ ĐỌC dữ liệu nên lùi bao nhiêu lần
    cũng vô hại; một Nhóm thì không hứa được điều đó (nó có thể đã đặt lệnh rồi mới
    kiểm tra, và lệnh đó không rút lại được)."""
    if not (isinstance(step, dict) and step.get("kind") == KIND_ACTION):
        return False
    t = step.get("type")
    # NĂM LOẠI HỎI đều là cổng: cả năm chỉ ĐỌC thế giới, không đụng vào thị trường,
    # nên nhánh trượt lùi lại bao nhiêu lần cũng vô hại.
    return t == CHECK_COND or hoi.la_loai_hoi(t)


def _khoa_dieu_kien(conds):
    """Dấu vân tay của một bộ điều kiện, để phát hiện hai cổng giống hệt nhau.
    Sắp khoá trước khi ghép: hai dict cùng nội dung khác thứ tự khoá vẫn phải ra cùng
    một chuỗi, nếu không cảnh báo 'hai nhánh trùng điều kiện' sẽ bỏ sót."""
    return json.dumps(conds or [], sort_keys=True, ensure_ascii=False, default=str)


def flow_entry(steps, edges):
    """Khối BẮT ĐẦU của sơ đồ.

    Ưu tiên tuyệt đối cho khối `kind == "start"`: nó là điểm neo, KHÔNG nhận đường vào,
    nên nó luôn hợp lệ làm điểm bắt đầu. Nhờ vậy một vòng lặp nối ngược lên trên không
    thể làm mọi khối đều có đường vào — lỗi khiến TOÀN BỘ huy hiệu biến thành "–".

    Không có khối `start` (file cũ / chép tay) thì quay về luật cũ: khối đầu tiên trong
    danh sách mà không có đường nối đi vào. Không tìm được thì trả None và
    `validate_flow_graph` báo lỗi thay vì đoán bừa."""
    ds = [s for s in (steps or []) if isinstance(s, dict) and s.get("id")]
    if not ds:
        return None
    for s in ds:
        if is_start_step(s):
            return s["id"]
    co_vao = {e.get("to") for e in (edges or [])
              if isinstance(e, dict) and (e.get("port") or "out") == "out"}
    for s in ds:
        if s["id"] not in co_vao:
            return s["id"]
    return None


# Sentinel: "khối này không phải điểm rẽ". Phải khác `None`, vì None đã có nghĩa
# riêng rồi — "là điểm rẽ nhưng các nhánh không chụm lại ở đâu cả".
_KHONG_RE = object()


def _chu_nhanh(k):
    """0 -> 'A', 1 -> 'B'. Quá 26 nhánh từ một khối là chuyện không xảy ra thật,
    nhưng vẫn phải ra chuỗi phân biệt được."""
    return chr(65 + k) if k < 26 else f"({k + 1})"


def diem_gop(cur, ke, da_nhan=None):
    """Khối GẦN NHẤT mà MỌI nhánh ĐI TỚI của `cur` đều dẫn tới, hoặc None.

    Nhờ nó mà số quay về mức trên cùng sau khi hết nhánh: 4 rẽ ra 4A/4B, hai nhánh
    chụm lại thì khối sau đó là "5" chứ không phải "4A.4". Không nhánh nào gặp nhau
    -> None, nghĩa là mỗi nhánh tự kết thúc và đơn giản là KHÔNG CÓ số 5 nào cả.

    `da_nhan` = những khối ĐÃ được đánh nhãn, tức nằm phía SAU LƯNG phép duyệt.
    Phải truyền vào, nếu không đồ thị có vòng lặp sẽ cho kết quả vô nghĩa: đi vòng một
    lượt là "tới được" lại chính các nhánh vừa xuất phát, nên phép giao nhận nhầm một
    ĐẦU NHÁNH làm điểm gộp — khi đó nhánh A vừa mang nhãn "3A" vừa mang nhãn "4".
    Đúng lỗi làm sơ đồ mẫu Compress đánh số lệch (một nhánh "4", nhánh kia "3B").

    Hai việc `da_nhan` làm:
      · nhánh nào có ĐẦU đã mang nhãn thì bỏ qua hẳn — đó là cạnh quay lại, nó không
        đi tới đâu cả mà là về chỗ cũ;
      · phép loang dừng lại ở mọi khối đã có nhãn, không đi xuyên qua chúng.
    """
    da_nhan = da_nhan or set()
    nhanh = [uv for uv in (ke.get(cur) or []) if uv not in da_nhan]
    if len(nhanh) < 2:
        return None

    def toi_duoc(bd):
        tham, hang = set(), [bd]
        while hang:
            n = hang.pop(0)
            if n in tham or n in da_nhan:
                continue
            tham.add(n)
            hang.extend(ke.get(n) or [])
        return tham

    chung = None
    for uv in nhanh:
        t = toi_duoc(uv)
        chung = t if chung is None else (chung & t)
    chung = (chung or set()) - {cur}
    if not chung:
        return None
    tham, hang = set(), list(nhanh)
    while hang:
        n = hang.pop(0)
        if n in tham or n in da_nhan:
            continue
        tham.add(n)
        if n in chung:
            return n
        hang.extend(ke.get(n) or [])
    return None


def flow_order(steps, edges):
    """Nhãn hiện ở góc khối -> {id: "1" | "4" | "4A" | "4A.2" | "4A.2B.1"}.

    LUẬT: SỐ = đi được bao xa, CHỮ = đi nhánh nào.
    Chữ dính ngay sau số của khối RẼ (khối 4 rẽ ra thì cổng hai nhánh là 4A, 4B), dấu
    chấm ngăn giữa nhãn nhánh và số bước bên trong nhánh (4A.1, 4A.2).

    Ngữ pháp: các nhóm ngăn bởi dấu chấm, mỗi nhóm = SỐ rồi tới các CHỮ (có thể không
    có). "4A.2B" tách thành "4A" | "2B" — chữ không bao giờ mở đầu một nhóm, số luôn
    đứng ngay sau dấu chấm, nên tách được bằng máy, không nhập nhằng.

    GẶP LẠI KHỐI ĐÃ CÓ NHÃN — ba trường hợp KHÁC HẲN nhau (Auto_Clicker gộp cả ba
    thành một cờ `loop` duy nhất và báo động sai; xem core.md §3.3 Bẫy 1):

      1. Khối đã GHIM  -> vòng lặp CÓ CHỦ Ý. Giữ nguyên nhãn cũ, ghi lại là cạnh
                          quay lại, KHÔNG cảnh báo gì. Đây là "số cũ vẫn hợp lệ".
      2. Khối nằm trên ĐƯỜNG ĐANG ĐI (ancestor) -> vòng lặp ngoài ý muốn -> cảnh báo
                          kèm gợi ý ghim khối đó lại.
      3. Còn lại -> hai nhánh chụm vào cùng một khối mà `diem_gop` không nhận ra
                          (nhánh chụm không đều). KHÔNG phải vòng lặp.

    Trả về: {"order", "unreachable", "entry", "quay_lai", "vong_ho", "lech_nhanh"}
    """
    theo_id, ke = flow_map(steps, edges)
    bat_dau = flow_entry(steps, edges)
    nhan = {}
    duong = []          # ngăn xếp các khối ĐANG MỞ trên đường đi hiện tại
    quay_lai = []       # [(từ, tới)] cạnh quay lại hợp lệ — tới khối đã ghim
    vong_ho = []        # [(từ, tới)] vòng lặp chưa ghim
    lech_nhanh = []     # [id] khối bị hai nhánh cùng với tới

    def gap_lai(dich, tu):
        if theo_id.get(dich, {}).get("ghim"):
            if (tu, dich) not in quay_lai:
                quay_lai.append((tu, dich))
        elif dich in duong:
            if (tu, dich) not in vong_ho:
                vong_ho.append((tu, dich))
        elif dich not in lech_nhanh:
            lech_nhanh.append(dich)

    def chuoi(tu, cur, tien_to, i, dung_tai):
        """Đánh số một chuỗi; khối đầu mang nhãn f"{tien_to}{i}", rồi +1 dần.
        Dừng khi tới `dung_tai` (điểm gộp — để dành cho mức trên) hoặc hết đường."""
        them = 0
        try:
            for _ in range(MAX_PROCESS_STEPS):
                if cur is None or cur not in theo_id or cur == dung_tai:
                    return
                if cur in nhan:
                    gap_lai(cur, tu)
                    return
                nhan[cur] = f"{tien_to}{i}"
                duong.append(cur)
                them += 1
                gop = re_nhanh(cur, f"{tien_to}{i}", dung_tai)
                if gop is _KHONG_RE:
                    ds = ke.get(cur) or []
                    tu, cur, i = cur, (ds[0] if ds else None), i + 1
                    continue
                if gop is None or gop == dung_tai:
                    return
                tu, cur, i = cur, gop, i + 1
        finally:
            for _ in range(them):
                duong.pop()

    def re_nhanh(cur, nhan_cur, dung_tai):
        """Nếu `cur` là điểm rẽ thì đánh số hết các nhánh của nó.

        Trả về ĐIỂM GỘP (có thể None), hoặc `_KHONG_RE` nếu đây không phải điểm rẽ.
        Điểm gộp phải tính MỘT LẦN ở đây rồi dùng lại — tính lại sau khi các nhánh đã
        có nhãn thì `da_nhan` đã khác và ra kết quả khác."""
        nhanh = ke.get(cur) or []
        if len(nhanh) < 2:
            return _KHONG_RE
        gop = diem_gop(cur, ke, set(nhan))
        for k, uv in enumerate(nhanh):
            dau_nhanh(cur, uv, nhan_cur + _chu_nhanh(k),
                      gop if gop is not None else dung_tai)
        return gop

    def dau_nhanh(tu, uv, nhan_nhanh, dung_tai):
        """Khối ĐẦU nhánh mang đúng nhãn nhánh ("4A" — chính là cái cổng), các khối
        sau nó mang "4A.1", "4A.2"… Cổng lại rẽ tiếp thì chữ nối thêm chữ ("4AA"),
        vẫn đúng ngữ pháp vì một nhóm cho phép nhiều chữ."""
        if uv is None or uv not in theo_id or uv == dung_tai:
            return
        if uv in nhan:
            gap_lai(uv, tu)
            return
        nhan[uv] = nhan_nhanh
        duong.append(uv)
        try:
            gop = re_nhanh(uv, nhan_nhanh, dung_tai)
            if gop is not _KHONG_RE:
                if gop is not None and gop != dung_tai:
                    chuoi(uv, gop, nhan_nhanh + ".", 1, dung_tai)
                return
            sau = ke.get(uv) or []
            if sau:
                chuoi(uv, sau[0], nhan_nhanh + ".", 1, dung_tai)
        finally:
            duong.pop()

    chuoi(None, bat_dau, "", 1, None)
    return {
        "order": nhan,
        "unreachable": [sid for sid in theo_id if sid not in nhan],
        "entry": bat_dau,
        "quay_lai": quay_lai,
        "vong_ho": vong_ho,
        "lech_nhanh": lech_nhanh,
        # Giữ khoá `loop` cho giao diện: giờ nó chỉ bật khi có vòng THẬT.
        "loop": bool(quay_lai or vong_ho),
    }


# ---------------------------------------------------------------------------
# Soát lỗi
# ---------------------------------------------------------------------------


def _loi(ds, sev, sid, msg):
    ds.append({"severity": sev, "step": sid, "index": None, "message": msg})


def validate_flow_graph(steps, edges, nhan_cong=None):
    """Soát riêng phần ĐỒ THỊ — lỗi ở mức nối dây, không phải ở mức một hành động.

    `nhan_cong` = tên khối CỔNG trong câu báo lỗi. Cỗ máy 5 trạm gọi cổng là «Hỏi» (D-10);
    hai sơ đồ Entry/Manage cũ gọi là «Kiểm tra điều kiện». Luật nối dây y hệt nhau."""
    nhan_cong = nhan_cong or "cổng rẽ nhánh"
    ra = []
    ds = [s for s in (steps or []) if isinstance(s, dict) and s.get("id")]
    if not ds:
        return ra

    theo_id, ke = flow_map(steps, edges)
    kq = flow_order(steps, edges)
    nhan = kq["order"]

    def ten(sid):
        """Tên khối kèm NHÃN THẬT trên huy hiệu.

        Cố ý không dùng index trong danh sách: Auto_Clicker ghi f"Bước {i+1}" nên panel
        Vấn đề có thể nói "Bước 7" về một khối mà huy hiệu ghi "4A.2" (core.md §3.3)."""
        n = nhan.get(sid)
        return f'[{n}] "{step_title(theo_id[sid])}"' if n else f'"{step_title(theo_id[sid])}"'

    # ---- Khối trùng id ----
    # `flow_map` tra theo id nên hai khối cùng id thì một cái BIẾN MẤT khỏi sơ đồ:
    # không nhãn, không dấu vết. Nhìn canvas thấy đủ khối, chạy thì thiếu.
    dem = {}
    for s in ds:
        dem[s["id"]] = dem.get(s["id"], 0) + 1
    for sid, n in dem.items():
        if n > 1:
            _loi(ra, "error", sid,
                 f'Có {n} khối trùng id với nhau ({ten(sid)}) — chỉ MỘT cái được chạy, '
                 f"những cái còn lại biến mất khỏi sơ đồ mà không báo gì. "
                 f"Hãy xoá bớt rồi tạo lại.")

    # ---- Khối Bắt đầu ----
    bd = [s for s in ds if is_start_step(s)]
    if len(bd) > 1:
        _loi(ra, "error", bd[1]["id"],
             f"Sơ đồ có {len(bd)} khối Bắt đầu — chỉ được đúng một. "
             f"Hãy xoá bớt, giữ lại một cái.")
    if not bd:
        _loi(ra, "warning", None,
             "Sơ đồ chưa có khối Bắt đầu. Thêm một cái để việc đánh số có điểm neo cố "
             "định — không có nó, một vòng lặp nối ngược lên trên có thể làm mất luôn "
             "điểm bắt đầu và mọi khối đều mất số.")
    for s in bd:
        vao = [e for e in (edges or [])
               if isinstance(e, dict) and e.get("to") == s["id"]]
        if vao:
            _loi(ra, "error", s["id"],
                 f"Khối Bắt đầu có {len(vao)} đường nối ĐI VÀO. Nó là điểm neo, "
                 f"không bao giờ được chạy tới từ chỗ khác. Hãy gỡ mấy đường đó.")

    # ---- Đường nối trỏ về chính nó ----
    for e in (edges or []):
        if isinstance(e, dict) and e.get("from") and e.get("from") == e.get("to") \
                and e["from"] in theo_id:
            _loi(ra, "error", e["from"],
                 f"{ten(e['from'])} có đường nối trỏ về CHÍNH NÓ — chạy tới đây là quay "
                 f"lại chính mình mãi mãi. Muốn lặp thì nối về một khối phía trước và "
                 f"ghim số khối đó.")

    # ---- Cổng khớp rồi mà phía sau trống ----
    for sid, st in theo_id.items():
        if is_branch_gate(st) and not ke.get(sid):
            _loi(ra, "warning", sid,
                 f"{ten(sid)} khớp điều kiện rồi thì không có gì phía sau — chiến lược "
                 f"kết thúc ngay tại đó. Nối tiếp một khối vào nếu bạn muốn nhánh này "
                 f"làm gì đó.")

    # ---- Luật rẽ nhánh ----
    # Nhiều đường ra KHÔNG phải lỗi, nhưng phải quyết định được đi đường nào. Ở điểm rẽ
    # các nhánh được thử lần lượt trên->dưới, nên mỗi nhánh phải mở đầu bằng một CỔNG,
    # trừ tối đa MỘT nhánh mặc định — và nhánh mặc định luôn khớp nên bắt buộc xếp CUỐI.
    for sid, nhanh in ke.items():
        if len(nhanh) < 2 or sid not in theo_id:
            continue
        # Cạnh QUAY LẠI (trỏ vào khối đã ghim) không cần cổng và luôn được thử cuối —
        # nghĩa của nó vốn đã là "không nhánh nào khớp thì quay về trên", tức đúng vai
        # nhánh mặc định. Bắt nó phải có cổng là bắt viết lại điều kiện phủ định của
        # tất cả các nhánh trên, thừa và dễ sai.
        quay = [uv for uv in nhanh if theo_id[uv].get("ghim")]
        thang = [uv for uv in nhanh if uv not in quay]
        khong_cong = [uv for uv in thang if not is_branch_gate(theo_id[uv])]
        if len(khong_cong) > 1:
            ds_ten = ", ".join(ten(uv) for uv in khong_cong)
            _loi(ra, "error", sid,
                 f"{ten(sid)} rẽ {len(nhanh)} nhánh nhưng có {len(khong_cong)} nhánh "
                 f"không có cổng kiểm tra ({ds_ten}) — chạy tới đây không biết chọn "
                 f'nhánh nào. Mỗi nhánh phải bắt đầu bằng khối {nhan_cong}, nhiều '
                 f"nhất một nhánh được để trống làm nhánh mặc định.")
        elif khong_cong and khong_cong[0] != thang[-1]:
            _loi(ra, "error", sid,
                 f"{ten(khong_cong[0])} là nhánh mặc định (không có cổng kiểm tra) "
                 f"nhưng không nằm dưới cùng của {ten(sid)} — nhánh mặc định luôn khớp "
                 f"nên các nhánh xếp dưới nó không bao giờ chạy tới. Hãy kéo nó xuống "
                 f"thấp nhất.")
        # CỐ Ý KHÔNG cảnh báo "nhánh nào cũng có điều kiện". Trước đây có, vì tưởng
        # không khớp nhánh nào là chiến lược chết đứng. Sai: cả sơ đồ là một vòng lặp
        # chạy lại ở mỗi nến, nên không khớp gì = HẾT LƯỢT, nến sau chạy lại từ đầu.
        # Đó là cách "chờ" được diễn tả, và nó là trường hợp thường gặp nhất.

        # ---- Thứ tự nhánh phải NHÌN THẤY ĐƯỢC ----
        # `_khoa_nhanh` xếp nhánh theo (ghim, y, x, id). Hai đầu nhánh chênh `y` vài
        # pixel thì mắt thấy chúng ngang nhau, nhưng bộ chạy vẫn thử một cái trước —
        # và nếu chênh 0 thì phân định bằng `id`, một uuid KHÔNG ai nhìn thấy và không
        # ai đổi được. Kết quả backtest khi đó phụ thuộc toạ độ canvas: hai file có đồ
        # thị y hệt mà khác vị trí sẽ chạy ra khác nhau.
        # Báo LỖI chứ không cảnh báo: sửa chỉ tốn một cú kéo, còn để nguyên thì cái sai
        # không bao giờ lộ ra — sơ đồ trông vẫn đúng.
        for i, a in enumerate(thang):
            for b in thang[i + 1:]:
                ya, yb = _khoa_nhanh(theo_id[a])[1], _khoa_nhanh(theo_id[b])[1]
                if abs(ya - yb) >= LECH_TOI_THIEU:
                    continue
                _loi(ra, "error", a,
                     f"{ten(a)} và {ten(b)} là hai nhánh của {ten(sid)} nhưng nằm "
                     f"NGANG NHAU (lệch {abs(ya - yb):.0f} px). Nhánh nào được thử "
                     f"trước là do vị trí quyết, nên đặt ngang nhau là để máy tự chọn "
                     f"bằng thứ mắt không thấy. Hãy kéo một trong hai lên hoặc xuống "
                     f"ít nhất {LECH_TOI_THIEU:.0f} px.")

        # Hai cổng cùng điều kiện y hệt: cái dưới không bao giờ tới lượt.
        da_thay = {}
        for uv in nhanh:
            if not is_branch_gate(theo_id[uv]):
                continue
            # ⚠ Bản trước đọc khoá `conditions` — thứ đã chết cùng bộ khối cũ (D-12).
            # Nên MỌI cặp cổng đều băm ra `[]` giống nhau và phép kiểm này báo "hai
            # nhánh trùng điều kiện" cho cả những cặp khác hẳn nhau. Cảnh báo sai thì
            # người ta học cách bỏ qua nó, và lần nó đúng cũng bị bỏ qua nốt.
            khoa = _khoa_dieu_kien(theo_id[uv].get("dieu_kien")
                                   or theo_id[uv].get("conditions"))
            if khoa in da_thay:
                _loi(ra, "warning", uv,
                     f"{ten(uv)} có điều kiện giống hệt {ten(da_thay[khoa])} xếp trên — "
                     f"khớp thì nhánh trên thắng, nhánh này không bao giờ chạy.")
            else:
                da_thay[khoa] = uv

    # ---- Điểm bắt đầu ----
    if kq["entry"] is None:
        _loi(ra, "error", None,
             "Không tìm được khối bắt đầu — mọi khối đều có đường nối đi vào. Hãy thêm "
             "một khối Bắt đầu, hoặc gỡ bớt một đường nối.")

    # ---- Vòng lặp CHƯA ghim ----
    for tu, toi in kq["vong_ho"]:
        _loi(ra, "warning", toi,
             f"{ten(tu)} nối ngược về {ten(toi)} tạo thành VÒNG LẶP, nhưng {ten(toi)} "
             f'chưa được ghim số. Bấm chuột phải vào nó → "Ghim số" để xác nhận đây là '
             f"vòng lặp cố ý — số của nó sẽ được giữ nguyên và cảnh báo này biến mất. "
             f"Vòng chỉ dừng khi chạy đủ {MAX_PROCESS_STEPS} bước.")

    # ---- Nhánh chụm không đều ----
    # KHÔNG gọi là vòng lặp. Đây là lúc `diem_gop` không tìm ra khối chung cho MỌI
    # nhánh (vd 3 nhánh mà chỉ 2 nhánh gặp nhau), nên số không quay về được mức trên.
    for sid in kq["lech_nhanh"]:
        _loi(ra, "warning", sid,
             f"{ten(sid)} được nhiều nhánh cùng dẫn tới, nhưng KHÔNG PHẢI mọi nhánh của "
             f"điểm rẽ đều dẫn tới đây — nên số không quay về được mức trên cùng và khối "
             f"này mang nhãn của nhánh chạm tới nó trước. Nối nốt các nhánh còn lại vào "
             f"đây nếu bạn muốn nó là điểm gộp thật.")

    # ---- Đường ↻ và khối Quay về ----
    # Ba chỗ chúng có thể trỏ hỏng, và cả ba đều IM LẶNG lúc chạy: khối lặng lẽ không
    # nhảy, lượt chạy kết thúc như thể đã đi hết đường.
    ra_vong = {}
    for e in (edges or []):
        if isinstance(e, dict) and so_vong_canh(e) and e.get("from") in theo_id:
            ra_vong.setdefault(e["from"], []).append(e.get("to"))
    for nguon, dich_ds in ra_vong.items():
        if len(dich_ds) > 1:
            _loi(ra, "error", nguon,
                 f"{ten(nguon)} có {len(dich_ds)} đường ↻ đi ra — một khối chỉ quay lại "
                 f"được MỘT chỗ. Hãy gỡ bớt.")

    for s in ds:
        if s.get("type") != QUAY_VE:
            continue
        ve = str(s.get("ve") or "").strip()
        if not ve:
            _loi(ra, "error", s["id"],
                 f"{ten(s['id'])} chưa chọn khối để quay về — chạy tới đây là hết nhánh, "
                 f"không lặp gì cả.")
        elif ve == s["id"]:
            _loi(ra, "error", s["id"],
                 f"{ten(s['id'])} quay về CHÍNH NÓ — đó không phải vòng lặp, chỉ là một "
                 f"khối tự gọi mãi.")
        elif ve not in theo_id:
            _loi(ra, "error", s["id"],
                 f"{ten(s['id'])} trỏ về một khối KHÔNG CÒN trong sơ đồ — khối đích đã bị "
                 f"xoá. Hãy chọn lại khối đích.")

    # Vòng phải thật sự KHÉP: từ đích đi theo dây thường phải tới lại được nguồn. Không
    # thì đó là một cú nhảy ngang mang tên vòng lặp — máy nhảy thật, người vẽ thì tưởng
    # mình vừa vẽ một vòng.
    for nguon, (dich, _n) in canh_vong(edges, ds).items():
        if nguon not in theo_id or dich not in theo_id:
            continue
        tham, hang = set(), [dich]
        while hang:
            x = hang.pop(0)
            if x in tham:
                continue
            tham.add(x)
            hang.extend(ke.get(x) or [])
        if nguon not in tham:
            _loi(ra, "error", nguon,
                 f"{ten(nguon)} quay về {ten(dich)} mà từ đó KHÔNG đi tới được nó — vòng "
                 f"không khép, chạy tới đây là nhảy đi chỗ khác chứ không phải lặp.")

    # ---- Khối không bao giờ chạy tới ----
    for sid in kq["unreachable"]:
        _loi(ra, "warning", sid,
             f"{ten(sid)} không bao giờ chạy tới — chưa có đường nối dẫn vào từ khối "
             f"bắt đầu.")

    return ra


def _soat_dai_luong(ra, sid, dau_cau, ve):
    """Soát MỘT vế đại lượng -> đại lượng ấy, hay None nếu nó không có thật.

    `dau_cau` = phần đầu câu lỗi, để chỗ gọi tự đặt cảnh ("dòng 2:" hay tên khối).
    MỘT bản dùng chung cho cả hai vế của khối Hỏi và ô "giá trị vẽ" của khối Vẽ lên
    bảng — hai bản thì sớm muộn một bên nhận đúng cái bên kia chối."""
    if not isinstance(ve, dict):
        ve = {}
    ma_dl = ve.get("ma_dl")
    if not ma_dl:
        # Chưa chọn gì (khối vừa thả ra) khác với chọn một thứ không có thật (file sửa
        # tay, hay đại lượng đã bỏ) — hai cảnh ấy nói hai câu khác nhau.
        _loi(ra, "error", sid, f"{dau_cau}chưa chọn đại lượng nào.")
        return None
    dl = hoi.dai_luong(ma_dl)
    if not dl:
        _loi(ra, "error", sid,
             f'{dau_cau}không có đại lượng "{ma_dl}" trong kho. Hãy chọn lại.')
        return None
    thieu = [ts["nhan"] for ts in dl["tham_so"]
             if ts["ten"] not in (ve.get("tham_so") or {})]
    if thieu:
        _loi(ra, "error", sid,
             f'{dau_cau}{dl["nhan"]} còn thiếu ô {", ".join(thieu)}.')
    if dl.get("duong") and not ve.get("duong"):
        _loi(ra, "error", sid,
             f'{dau_cau}{dl["nhan"]} có nhiều đường — phải chọn một '
             f'({", ".join(n for _m, n in dl["duong"])}).')
    _soat_ghep(ra, sid, dau_cau, ve, dl)
    return dl


def _soat_ghep(ra, sid, dau_cau, ve, dl):
    """Soát phần GHÉP của một vế: «giá / đỉnh 60 nến».

    Đặt trong `_soat_dai_luong` nên nó canh CẢ BA chỗ có vế đại lượng — hai vế của
    khối Hỏi và ô đại lượng của khối Làm — chỉ bằng một bản."""
    ghep = ve.get("ghep")
    if not isinstance(ghep, dict) or not ghep.get("phep"):
        return
    ten_phep = dict(hoi.PHEP_GHEP).get(ghep["phep"])
    if not ten_phep:
        _loi(ra, "error", sid, f'{dau_cau}không có phép ghép "{ghep["phep"]}".')
        return
    # ĐÚNG/SAI không cộng trừ được — cả hai bên của phép ghép.
    if dl and dl["kieu"] == hoi.KIEU_CO_KHONG:
        _loi(ra, "error", sid,
             f'{dau_cau}{dl["nhan"]} chỉ trả ĐÚNG/SAI, không {ten_phep} được.')
    if "ma_dl" not in ghep:
        so = ghep.get("so", 0)
        # Chia cho hằng số 0: LEAN ra 0 nên không nổ, nhưng cả vế thành số 0 cứng —
        # dòng điều kiện mất nghĩa mà chẳng ai thấy gì.
        if ghep["phep"] == "/" and not so:
            _loi(ra, "warning", sid,
                 f"{dau_cau}chia cho 0 — LEAN trả về 0 chứ không báo lỗi, nên cả vế "
                 f"này luôn bằng 0.")
        return
    # MỘT TẦNG THÔI. Bộ sinh mã chỉ dịch một tầng ghép (xem `_ve_py`), nên tầng thứ
    # hai mà nhận ở đây là nó biến mất khỏi mã sinh ra — soát sạch mà chạy sai.
    if isinstance(ghep.get("ghep"), dict) and ghep["ghep"].get("phep"):
        _loi(ra, "error", sid,
             f"{dau_cau}ghép hai tầng — chỉ ghép được MỘT phép. Chuyển hằng số sang "
             f"vế kia thường là đủ: «a / b − 1 ≤ −0,03» cũng là «a / b ≤ 0,97».")
        return
    dl2 = _soat_dai_luong(ra, sid, f"{dau_cau}phần {ten_phep} ", ghep)
    if dl2 and dl2["kieu"] == hoi.KIEU_CO_KHONG:
        _loi(ra, "error", sid,
             f'{dau_cau}{ten_phep} {dl2["nhan"]} không được — nó chỉ trả ĐÚNG/SAI, '
             f"không phải một con số.")


def soat_khoi_hoi(step):
    """Soát RUỘT một khối Xác nhận. -> [{severity, step, index, message}]

    Mấy chỗ này đều hỏng LẶNG lúc chạy: thiếu điều kiện thì cổng luôn khớp (nhánh
    dưới nó không bao giờ được thử), đại lượng lạ thì bộ sinh mã không biết viết gì,
    chỉ báo nhiều đường mà chưa chọn đường thì "giá > Bollinger" là câu vô nghĩa."""
    ra = []
    t = step.get("type")
    if not hoi.la_loai_hoi(t):
        return ra
    sid = step.get("id")
    ten = step_title(step)
    d = hoi.LOAI_HOI[t]
    ds = step.get("dieu_kien") or []

    if not ds:
        _loi(ra, "warning", sid,
             f'"{ten}" chưa có điều kiện nào — cổng không có điều kiện thì LUÔN khớp, '
             f"nên mọi nhánh xếp dưới nó không bao giờ được thử.")

    if d.get("tat"):
        _loi(ra, "warning", sid, f'"{ten}": {d["tat"]}')

    for i, dk in enumerate(ds):
        if not isinstance(dk, dict):
            _loi(ra, "error", sid, f'"{ten}" có dòng điều kiện {i + 1} hỏng.')
            continue
        # ⚠ Đại lượng ĐÚNG/SAI thì KHÔNG CÓ vế phải — không phải "có mà bỏ trống".
        # Phải biết điều ấy TRƯỚC khi soát từng vế, không thì «Đang giữ mã này» bị
        # đòi một vế phải mà giao diện cố tình không bày ra: người dùng nhìn thấy
        # một lỗi về thứ họ không có cách nào điền.
        _t = hoi.dai_luong((dk.get("trai") or {}).get("ma_dl"))
        co_ve_phai = not (_t and _t["kieu"] == hoi.KIEU_CO_KHONG)
        ve_can_soat = (("trái", dk.get("trai")), ("phải", dk.get("phai"))) \
            if co_ve_phai else (("trái", dk.get("trai")),)
        for ten_ve, ve in ve_can_soat:
            if not isinstance(ve, dict):
                _loi(ra, "error", sid,
                     f'"{ten}" dòng {i + 1}: vế {ten_ve} để trống.')
                continue
            if "ma_dl" not in ve:
                if ten_ve == "trái":
                    _loi(ra, "error", sid,
                         f'"{ten}" dòng {i + 1}: vế trái phải là một đại lượng, '
                         f"không phải một con số.")
                continue        # vế phải là số: hợp lệ
            _soat_dai_luong(ra, sid, f'"{ten}" dòng {i + 1}: ', ve)
        # Đại lượng đúng/sai không so với số nào.
        dl_trai = hoi.dai_luong((dk.get("trai") or {}).get("ma_dl"))
        phep = dk.get("phep")
        if dl_trai and dl_trai["kieu"] == hoi.KIEU_CO_KHONG:
            if phep not in [m for m, _n in hoi.PHEP_CO_KHONG]:
                _loi(ra, "error", sid,
                     f'"{ten}" dòng {i + 1}: {dl_trai["nhan"]} chỉ trả ĐÚNG/SAI, '
                     f"không so lớn-nhỏ được.")
        elif dl_trai and phep not in [m for m, _n in hoi.PHEP_SO]:
            _loi(ra, "error", sid,
                 f'"{ten}" dòng {i + 1}: phép so "{phep}" không có.')
    return ra


#: Khuôn ngày lưu trong file. Lưu ISO chứ không lưu "01/01/2010": thẻ khối hiện kiểu
#: Việt, nhưng file phải xếp được theo thứ tự chữ và không mập mờ ngày/tháng.
_KHUON_NGAY = "%Y-%m-%d"


def _doc_ngay(s):
    try:
        return _dt.datetime.strptime(str(s), _KHUON_NGAY).date()
    except (TypeError, ValueError):
        return None


def _soat_ro(step, sid, ten, gt):
    """Soát ô `ma` khi nó là một RỔ. -> [vấn đề]

    Hai chỗ hỏng LẶNG:
      · mã rổ không có trong từ điển — file sửa tay, hay file của một bản app sau.
        Bộ sinh mã sẽ coi nó là "không phải rổ" rồi đi nhánh gõ-mã-sẵn với danh sách
        rỗng, tức sinh ra một cỗ máy không có mã nào mà không ai báo gì.
      · ETF để trống tên — `Symbol.create('', …)` không ném, nó dựng một mã rỗng, rồi
        rổ chọn ra số không mã và backtest chạy hết sạch, báo 0 lệnh."""
    ra = []
    ma_ro = str(gt.get("ro") or "").strip()
    ro = bat_dau.ro_cua(gt)
    if not ro:
        _loi(ra, "error", sid,
             f'"{ten}": không có rổ "{ma_ro}" — chọn lại một rổ, hoặc đổi về gõ mã '
             f"sẵn. Bản app này biết: "
             + ", ".join(m for m, *_ in bat_dau.RO) + ".")
        return ra
    if ro[0] != "etf":
        return ra

    etf = str(bat_dau.gt_ro(gt, "ma_etf") or "").strip()
    if not etf:
        _loi(ra, "error", sid,
             f'"{ten}": rổ ETF mà chưa gõ mã ETF nào — LEAN sẽ dựng một mã rỗng, '
             f"chọn ra số không mã, và backtest chạy hết rồi báo 0 lệnh.")
    lay = _f(bat_dau.gt_ro(gt, "lay"))
    if lay is None:
        _loi(ra, "error", sid, f'"{ten}": «lấy mấy mã» không phải một con số.')
    elif lay < 0:
        _loi(ra, "error", sid,
             f'"{ten}": «lấy mấy mã» âm — `co[:{int(lay)}]` cắt từ đuôi nên rổ ra '
             f"gần như rỗng, mà không có lỗi nào.")
    return ra


def soat_khoi_bat_dau(step):
    """Soát RUỘT khối Bắt đầu. -> [{severity, step, index, message}]

    Mấy chỗ này đều hỏng LẶNG: không có mã thì cỗ máy chạy đủ mọi nến mà không mua bán
    gì; ngày ngược thì LEAN không chạy nến nào; mã trùng thì LEAN đăng ký hai lần."""
    ra = []
    if not is_start_step(step):
        return ra
    sid = step.get("id")
    ten = step_title(step)

    ds = o_bat_dau(step, "ma")
    # Ô `ma` có HAI KIỂU (xem `bat_dau.RO`). Kiểu rổ thì mấy phép dưới đây vô nghĩa —
    # không có dòng mã nào để mà soát trống hay trùng — nên nó có phép soát riêng.
    if isinstance(ds, dict):
        ra += _soat_ro(step, sid, ten, ds)
        ds = []
    elif not isinstance(ds, list) or not ds:
        _loi(ra, "error", sid,
             f'"{ten}": chưa chọn mã nào — cỗ máy sẽ chạy đủ mọi nến mà không mua '
             f"bán gì.")
        ds = []
    hop_le = {m for m, _n, _h in bat_dau.LOAI_TAI_SAN}
    da_thay = set()
    for i, m in enumerate(ds):
        if not isinstance(m, dict):
            _loi(ra, "error", sid, f'"{ten}": dòng mã {i + 1} hỏng.')
            continue
        k = str(m.get("ma") or "").strip().upper()
        if not k:
            _loi(ra, "error", sid, f'"{ten}": dòng mã {i + 1} để trống.')
            continue
        if m.get("loai") not in hop_le:
            _loi(ra, "error", sid,
                 f'"{ten}": mã {k} chưa chọn loại tài sản — mỗi loại một hàm LEAN '
                 f"khác nhau.")
        if k in da_thay:
            _loi(ra, "error", sid,
                 f'"{ten}": mã {k} khai hai lần — LEAN sẽ đăng ký trùng.')
        da_thay.add(k)

    k = o_bat_dau(step, "khoang") or {}
    tu, den = _doc_ngay(k.get("tu")), _doc_ngay(k.get("den"))
    if tu is None or den is None:
        _loi(ra, "error", sid,
             f'"{ten}": ngày sai khuôn — phải là dạng 2010-01-31.')
    elif tu >= den:
        _loi(ra, "error", sid,
             f'"{ten}": ngày bắt đầu không trước ngày kết thúc — LEAN sẽ không chạy '
             f"nến nào.")

    v = _f(o_bat_dau(step, "von"))
    if v is None:
        _loi(ra, "error", sid, f'"{ten}": vốn không phải một con số.')
    elif v <= 0:
        _loi(ra, "error", sid,
             f'"{ten}": vốn phải lớn hơn 0 — không có tiền thì mọi lệnh đều bị từ '
             f"chối, mà backtest vẫn chạy hết.")

    nhip = str(o_bat_dau(step, "nhip") or "")
    if not bat_dau.nhip_cua(nhip):
        _loi(ra, "error", sid, f'"{ten}": không có nhịp "{nhip}".')

    # ⚠ BẪY ĐÃ GẶP THẬT, và nó lặng hoàn toàn: nhịp mỗi nến NGÀY thì LEAN không có dữ
    # liệu trong ngày để khớp, nên nó đổi lệnh thị trường thành MarketOnClose — mà ba
    # sàn dưới đây không nhận loại ấy. Backtest chạy hết, báo "111 lệnh", lãi 0%, và
    # chỉ mở file order-events ra đọc mới thấy mọi lệnh đều `invalid`.
    if nhip == "ngay" and str(o_bat_dau(step, "san")) in bat_dau.SAN_KHONG_NHAN_MOC:
        nhan_san = dict(bat_dau.SAN)[str(o_bat_dau(step, "san"))]
        _loi(ra, "warning", sid,
             f'"{ten}": nhịp mỗi nến NGÀY cộng sàn {nhan_san} là MỌI LỆNH BỊ TỪ CHỐI. '
             f"Nến ngày không có giá trong ngày để khớp, nên LEAN đổi lệnh thị trường "
             f"thành «khớp lúc đóng cửa», mà sàn này không nhận loại ấy — backtest "
             f"vẫn chạy hết và báo lãi 0%. Hãy đổi nhịp xuống giờ/phút, hoặc chọn sàn "
             f"Mặc định.")

    # NGƯỠNG của model phòng rủi ro. Ô này chỉ hiện khi có chọn model, nên không có
    # model thì không có gì để soát.
    #
    # ⚠ NGƯỠNG 0 LÀ MỘT CÁI PHANH ĐẠP CỨNG, không phải "không phanh". Cả bốn model
    # lấy `-abs(ngưỡng)` rồi so `pnl < ngưỡng`, nên 0 nghĩa là CẮT NGAY khi mã chớm
    # lỗ một xu — cỗ máy mua rồi bán sạch mỗi nến, backtest chạy hết, không một lời
    # nào. Số âm thì `abs` ăn mất dấu, tức người dùng gõ -0.05 lại thành 5%: con số
    # trong hộp và con số LEAN dùng không còn là một.
    if bat_dau.rui_ro_cua(o_bat_dau(step, "phong_rui_ro")):
        ng = _f(o_bat_dau(step, "nguong"))
        if ng is None:
            _loi(ra, "error", sid, f'"{ten}": ngưỡng phòng rủi ro không phải một '
                                   f"con số.")
        elif ng <= 0:
            _loi(ra, "error", sid,
                 f'"{ten}": ngưỡng phòng rủi ro phải lớn hơn 0 — LEAN lấy trị tuyệt '
                 f"đối của số này, nên 0 là cắt ngay khi mã chớm lỗ và số âm thì "
                 f"thành chính nó dương. Ghi 0.05 cho 5%.")
        elif ng >= 1:
            _loi(ra, "warning", sid,
                 f'"{ten}": ngưỡng phòng rủi ro là PHẦN, không phải phần trăm — '
                 f"{ng:g} nghĩa là {ng * 100:g}%, tức trạm này gần như không bao giờ "
                 f"cắn. Ghi 0.05 cho 5%.")
    return ra


def soat_day_chuyen(steps):
    """Soát chéo: DÂY CHUYỀN của LEAN phải khớp đầu khớp đuôi. -> [vấn đề]

    Khối «Phát tín hiệu» không tự đặt lệnh — nó đưa một `Insight` cho dây chuyền:

        tín hiệu -> chia vốn -> phòng rủi ro -> đặt lệnh

    Dây ấy bắt đầu từ tín hiệu và chỉ chạy nếu có người nhận. Ba cách hỏng dưới đây
    đều HỎNG LẶNG — LEAN chạy xong, không lỗi, mà không một lệnh nào được đặt:

      1. Phát tín hiệu mà không chọn «Chia vốn»: insight bay vào hư không.
      2. Chọn «Chia vốn» mà chẳng khối nào phát tín hiệu: trạm ấy ngồi không.
      3. Trộn tín hiệu với khối đặt lệnh tay: model chia vốn cân lại danh mục theo
         target của nó, nên cú `set_holdings` tay bị gỡ ngay nhịp sau.
    """
    ra = []
    bd = next((x for x in (steps or []) if is_start_step(x)), None)
    if not bd:
        return ra

    co_tin_hieu, co_lenh_tay = [], []
    for x in (steps or []):
        for a_ in (hanh_dong_cua(x) if is_group_step(x) else [x]):
            if not isinstance(a_, dict):
                continue
            t = a_.get("type")
            if t == lam.LAM_TIN_HIEU:
                co_tin_hieu.append(x)
            elif lam.la_loai_lam(t) and lam.LOAI_LAM[t]["nhom"] == lam.NHOM_LENH:
                co_lenh_tay.append(x)

    chia = str(o_bat_dau(bd, "chia_von") or "").strip()

    if co_tin_hieu and not chia:
        _loi(ra, "error", co_tin_hieu[0].get("id"),
             "Sơ đồ có khối «Phát tín hiệu» mà khối Bắt đầu chưa chọn «Chia vốn theo "
             "tín hiệu» — tín hiệu phát ra KHÔNG ai nhận, và backtest chạy xong sẽ "
             "không có lệnh nào.")
    if chia and not co_tin_hieu:
        _loi(ra, "warning", bd.get("id"),
             f'Khối Bắt đầu chọn chia vốn «{chia}», mà sơ đồ không có khối «Phát tín '
             f"hiệu» nào — trạm ấy không có gì để chia.")
    if co_tin_hieu and co_lenh_tay:
        _loi(ra, "error", co_lenh_tay[0].get("id"),
             "Sơ đồ vừa «Phát tín hiệu» vừa đặt lệnh tay. Hai thứ giành nhau danh "
             "mục: model chia vốn cân lại theo tỷ trọng của nó, nên lệnh đặt tay bị "
             "gỡ ngay nhịp sau. Chọn MỘT lối.")

    # RỔ ETF phải có dữ liệu RƠI VÀO khoảng backtest, không thì rổ chọn ra rỗng và
    # cả lượt chạy lặng — chạy xong, không lỗi, không một lệnh nào. Đã dính thật.
    ro = bat_dau.ro_cua(bd.get("ma"))
    if ro and ro[0] == "etf":
        k = bd.get("khoang") or {}
        co, ngay = bat_dau.ro_etf_trum_khoang(
            (bd.get("ma") or {}).get("ma_etf"), k.get("tu"), k.get("den"))
        if co is False:
            _loi(ra, "warning", bd.get("id"),
                 f'Bộ dữ liệu miễn phí chỉ có rổ của ETF này vào {", ".join(ngay)} — '
                 f'khoảng backtest đang chọn KHÔNG trùm qua ngày nào trong đó, nên rổ '
                 f'sẽ rỗng và backtest chạy xong sẽ không có lệnh nào.')

    # Hai trạm sau cũng cần dây: không có chia vốn thì chúng không bao giờ được gọi.
    for ten_o, nhan in (("phong_rui_ro", "Phòng rủi ro"), ("dat_lenh", "Đặt lệnh")):
        if str(o_bat_dau(bd, ten_o) or "").strip() and not chia:
            _loi(ra, "warning", bd.get("id"),
                 f"«{nhan}» chỉ chạy sau khi có chia vốn — mà «Chia vốn theo tín "
                 f"hiệu» đang để trống, nên trạm này không bao giờ tới lượt.")

    _soat_ghim(ra, steps)
    return ra


def _soat_ghim(ra, steps):
    """Soát mấy núm đã GHIM. Cả hai lỗi dưới đây đều hỏng LẶNG lúc Optimize chạy.

    · TÊN SAI KHUÔN — `get_parameter("Chu kỳ RSI", 14)` vẫn là Python chạy được, mà
      config optimizer của LEAN thì không khai nổi một tên có dấu cách; nó quét một
      tên khác, thuật toán đọc tên này, và mỗi lượt backtest ra y hệt nhau.
    · CÙNG TÊN NHƯNG KHÁC MẶC ĐỊNH — hai ô cùng ghim `chu_ky`, một ô mặc định 14 một
      ô 200. Lúc Optimize thì cả hai cùng nhận một giá trị, nên nó CHẠY ĐƯỢC; nhưng
      lúc backtest thường, hai ô ấy giữ hai số khác nhau. Cùng một sơ đồ mà hai lối
      chạy hiểu khác nhau — không gì kêu lên cả."""
    thay = {}
    for s in steps or []:
        for chu, ten_o, nhan, gt in _o_so_cua(s):
            ten = str((chu.get("ghim") or {}).get(ten_o) or "").strip()
            if not ten:
                continue
            cho = f"{step_title(s)} · {nhan}"
            if not _RE_TEN_THAM_SO.match(ten):
                _loi(ra, "error", s.get("id"),
                     f'Tên tham số "{ten}" ({cho}) không dùng được — chỉ chữ thường '
                     f"không dấu, số và gạch dưới, bắt đầu bằng chữ.")
                continue
            thay.setdefault(ten, []).append((cho, gt))
    for ten, ds in thay.items():
        mac_dinh = {str(g) for _c, g in ds}
        if len(mac_dinh) > 1:
            _loi(ra, "error", None,
                 f'Tham số "{ten}" bị ghim ở {len(ds)} ô mà mặc định khác nhau '
                 f'({", ".join(sorted(mac_dinh))}) — {" · ".join(c for c, _g in ds)}. '
                 f"Cho chúng cùng một số, hoặc đặt tên khác nhau.")


def soat_ro_dong(steps):
    """Soát chéo: khối Bắt đầu chạy trên một RỔ ĐỘNG thì hai thứ phải khớp theo.

    Cả hai đều HỎNG LẶNG — backtest chạy hết, không một lỗi nào, và bảng kết quả chỉ
    nói "0 lệnh" hoặc nói một con số vô nghĩa:

      1. **Rổ cộng «chia danh mục»** (chạy MỘT LƯỢT cho cả rổ). Lối chia danh mục
         sống bằng việc gõ rõ tên từng mã rồi đặt tỷ trọng cho nó — "40% QQQ, 35%
         GLD". Mà rổ gồm mã nào thì LEAN quyết lại mỗi ngày: hôm nay 8 mã, tháng sau
         11 mã, và không mã nào gõ trước được. Nên mọi khối trong sơ đồ ấy sẽ bị
         `_sym_py` chối từng cái một — tức là lỗi, nhưng lỗi ở MƯỜI chỗ khác nhau,
         trong khi nguyên nhân chỉ có một chỗ. Nói ở đây, nói đúng chỗ.
      2. **Rổ mà không có «Phát tín hiệu»**. Rổ động là nửa trên của dây chuyền
         LEAN (`set_universe_selection` -> insight -> chia vốn -> lệnh). Không có
         khối phát tín hiệu thì sơ đồ phải tự đặt lệnh cho từng mã — mà không mã nào
         gõ được tên, nên cả sơ đồ chỉ còn mỗi mã-đang-xét, và «Đặt tỷ trọng» cho
         mã đang xét trên một rổ 500 mã là 500 lần giành nhau một danh mục. Đây là
         CẢNH BÁO chứ không phải lỗi: một sơ đồ chỉ «Ghi chú» hay «Vẽ bảng» thì vẫn
         có nghĩa — nó đang xem rổ hôm nay gồm những gì."""
    ra = []
    bd = next((x for x in (steps or []) if is_start_step(x)), None)
    if not bd:
        return ra
    ro = bat_dau.ro_cua(o_bat_dau(bd, "ma"))
    if not ro:
        return ra

    if str(o_bat_dau(bd, "chay_cho") or "") == "ca_danh_muc":
        _loi(ra, "warning", bd.get("id"),
             f"Khối Bắt đầu chạy trên rổ «{ro[1]}» mà lại đặt «Một lượt cho CẢ RỔ — "
             f"chia danh mục». Hai thứ chống nhau: chia danh mục cần gõ rõ tên từng "
             f"mã, mà rổ gồm mã nào thì LEAN quyết lại mỗi ngày — hôm nay 8 mã, "
             f"tháng sau 11 mã. Đổi sang «Mỗi mã một lượt — sàng từng mã».")

    co_tin_hieu = any(
        isinstance(a_, dict) and a_.get("type") == lam.LAM_TIN_HIEU
        for x in (steps or [])
        for a_ in (hanh_dong_cua(x) if is_group_step(x) else [x]))
    if not co_tin_hieu:
        _loi(ra, "warning", bd.get("id"),
             f"Khối Bắt đầu chạy trên rổ «{ro[1]}» mà sơ đồ không có khối «Phát tín "
             f"hiệu» nào. Rổ động là nửa trên của dây chuyền LEAN — nửa dưới là tín "
             f"hiệu rồi chia vốn. Thiếu nó thì mỗi mã trong rổ sẽ tự đặt lệnh và "
             f"giành nhau cùng một danh mục.")
    return ra


def soat_ca_ro(steps):
    """Soát chéo khối: chạy MỘT LƯỢT cho cả rổ thì mọi khối phải gõ rõ tên mã.

    Phép này không nằm trong `soat_khoi_lam` được, vì một khối Làm nhìn vào chính nó
    thì không biết khối Bắt đầu đang chạy kiểu nào. Mà bỏ sót thì mã sinh ra gọi một
    biến `sym` không tồn tại — Python ném NameError lúc chạy, sau khi đã chờ cả phút."""
    ra = []
    bd = next((s for s in (steps or []) if is_start_step(s)), None)
    if not bd or str(o_bat_dau(bd, "chay_cho") or "") != "ca_danh_muc":
        return ra
    for s in (steps or []):
        for a in (hanh_dong_cua(s) if is_group_step(s) else [s]):
            if not isinstance(a, dict):
                continue
            d = lam.LOAI_LAM.get(a.get("type"))
            if not d or not d["can_ma"]:
                continue
            if not str(a.get("ma") or "").strip():
                _loi(ra, "error", s.get("id"),
                     f'"{step_title(s)}": khối Bắt đầu chạy MỘT LƯỢT cho cả rổ nên '
                     f"không có «mã đang xét» — khối này phải gõ rõ tên mã.")
    # Hỏi cũng vậy: vế nào để trống mã là trỏ vào một thứ không tồn tại.
    for s in (steps or []):
        if not hoi.la_loai_hoi(s.get("type")):
            continue
        for i, dk in enumerate(s.get("dieu_kien") or []):
            for ve in ((dk or {}).get("trai"), (dk or {}).get("phai")):
                if not isinstance(ve, dict) or "ma_dl" not in ve:
                    continue
                # Hỏi TỪNG đại lượng chứ không hỏi cả họ: «Giờ» chạy cho cả rổ vẫn
                # là một con số duy nhất, bắt nó gõ tên mã là bắt vô lý.
                dl = hoi.dai_luong(ve.get("ma_dl"))
                if not dl or not dl["can_ma"]:
                    continue
                if not str(ve.get("ma") or "").strip():
                    _loi(ra, "error", s.get("id"),
                         f'"{step_title(s)}" dòng {i + 1}: chạy cho cả rổ thì vế nào '
                         f"cũng phải gõ rõ tên mã.")
    return ra


def soat_khoi_lam(step):
    """Soát RUỘT một khối Hành động. -> [{severity, step, index, message}]

    CHỈ bắt mấy chỗ hỏng LẶNG: LEAN nhận lệnh rồi bỏ, hoặc bộ sinh mã không có gì mà
    viết. Lời khuyên kiểu "đòn bẩy thế là cao đấy" là việc khác, để sau."""
    ra = []
    t = step.get("type")
    if not lam.la_loai_lam(t):
        return ra
    sid = step.get("id")
    ten = step_title(step)
    d = lam.LOAI_LAM[t]

    def g(k):
        return o_lam(step, k)

    if d.get("tat"):
        _loi(ra, "warning", sid, f'"{ten}": {d["tat"]}')

    o_hien = lam.o_cua(t, step)
    # Ô BẮT BUỘC để trống -> bộ sinh mã không có gì mà viết vào chỗ ấy.
    for o in o_hien:
        if not o["bat_buoc"]:
            continue
        v = g(o["ten"])
        if v is None or (isinstance(v, str) and not v.strip()):
            _loi(ra, "error", sid, f'"{ten}": ô {o["nhan"]} còn trống.')

    if t == lam.LAM_DAT_TY_TRONG:
        p = _f(g("ty_trong"))
        if p is None:
            _loi(ra, "error", sid, f'"{ten}": tỷ trọng không phải một con số.')
        elif abs(p) > 1:
            _loi(ra, "warning", sid,
                 f'"{ten}": tỷ trọng {_pt(p)}% vượt 100% — LEAN phải dùng đòn bẩy, và '
                 f"nếu tài khoản không cho thì nó từ chối lệnh mà không báo gì.")

    elif t in (lam.LAM_LENH_THI_TRUONG, lam.LAM_LENH_CHO):
        q = _f(g("so_luong"))
        if q is None:
            _loi(ra, "error", sid, f'"{ten}": số lượng không phải một con số.')
        elif q == 0:
            _loi(ra, "error", sid,
                 f'"{ten}": số lượng 0 — LEAN nhận rồi bỏ, sơ đồ chạy mà chẳng có '
                 f"lệnh nào.")
        if t == lam.LAM_LENH_CHO:
            ll = str(g("loai_lenh") or "")
            if ll not in d["theo_loai"]:
                _loi(ra, "error", sid, f'"{ten}": không có loại lệnh "{ll}".')
            # Giá 0 thì lệnh nằm đó không bao giờ khớp, mà cũng không ai báo.
            for o in o_hien:
                if o["ten"] not in ("gia_gh", "gia_kh", "gia_cham", "khoang_truot"):
                    continue
                v = _f(g(o["ten"]))
                if v is None or v <= 0:
                    _loi(ra, "error", sid,
                         f'"{ten}": {o["nhan"]} phải lớn hơn 0 — bằng 0 thì lệnh nằm '
                         f"trên sàn mà không bao giờ khớp.")

    elif t == lam.LAM_GHI_CHU:
        if g("muc") == "quit":
            _loi(ra, "warning", sid,
                 f'"{ten}" là DỪNG HẲN — chạm tới khối này là cỗ máy thôi chạy, mọi '
                 f"nến sau đó không được xét nữa.")

    # Ô ĐẠI LƯỢNG — soát theo TỪ ĐIỂN, không theo tên khối, nên khối nào khai
    # `co_dai_luong` cũng được canh.
    d_loai = lam.LOAI_LAM.get(t) or {}
    if d_loai.get("co_dai_luong"):
        nhan_o = d_loai.get("nhan_dai_luong", "Giá trị")
        gt = step.get("gia_tri") or {}
        if not gt.get("ma_dl") and not d_loai.get("dai_luong_so"):
            _loi(ra, "error", sid, f'"{ten}": chưa chọn {nhan_o.lower()}.')
        dl = _soat_dai_luong(ra, sid, f'"{ten}": ', gt) if gt.get("ma_dl") else None
        if dl and dl["kieu"] == hoi.KIEU_CO_KHONG:
            _loi(ra, "error", sid,
                 f'"{ten}": {dl["nhan"]} chỉ trả ĐÚNG/SAI, mà {nhan_o.lower()} cần '
                 f"một con số.")
    return ra


# ---- soát HÀNH ĐỘNG -------------------------------------------------------


#: ⚠ `DON_VI_CAN_ZONE` từng được khai LẠI ngay tại đây — hai dòng y hệt nhau cách nhau
#: 1100 dòng. Trùng như vậy thì sửa một chỗ là hai nơi nói khác nhau mà không ai thấy.
#: Bản duy nhất nằm cạnh `DON_VI_CHO`, chỗ mọi luật về đơn vị sống chung.


# ---------------------------------------------------------------------------
# Đường nối
# ---------------------------------------------------------------------------


def default_edges(steps):
    """Chuỗi thẳng 1 → 2 → 3…

    Nhờ hàm này mà "không có đường nối" và "nối thành chuỗi thẳng" là MỘT — file cũ
    (không có khoá `edges`) mở ra vẫn ra đúng sơ đồ nó vẫn chạy, không phải di cư gì."""
    ds = [s for s in (steps or []) if isinstance(s, dict) and s.get("id")]
    return [{"from": a["id"], "to": b["id"], "port": "out"} for a, b in zip(ds, ds[1:])]


def clean_edges(edges, steps):
    """Bỏ đường nối trỏ tới khối không còn tồn tại, và bỏ trùng.

    KHÔNG tự ý sửa ý người dùng thành thứ khác — chỉ vứt cái đã vô nghĩa."""
    co = {s.get("id") for s in (steps or []) if isinstance(s, dict)}
    ra, thay = [], set()
    for e in edges or []:
        if not isinstance(e, dict):
            continue
        a, b = e.get("from"), e.get("to")
        if a not in co or b not in co:
            continue
        khoa = (a, b, e.get("port") or "out")
        if khoa in thay:
            continue
        thay.add(khoa)
        moi = {"from": a, "to": b, "port": e.get("port") or "out"}
        # Cạnh nào của hộp thì đường nối cắm vào — thuần thị giác, nhưng PHẢI lưu,
        # nếu không mở lại file là sơ đồ tự vẽ khác đi so với lúc người dùng sắp.
        for k in ("from_side", "to_side"):
            if e.get(k):
                moi[k] = str(e[k])
        # Số vòng của đường ↻: PHẢI giữ, vì chính nó phân biệt đường quay lại với dây
        # thường. Mất nó là mở lại file thấy một vòng lặp biến thành cú nhảy ngang.
        if "so_vong" in e:
            moi["so_vong"] = e["so_vong"]
        ra.append(moi)
    return ra


# ---------------------------------------------------------------------------
# Chuẩn hoá & tài liệu
# ---------------------------------------------------------------------------

#: Khoá tả CÁI NÚT TRÊN CANVAS, không tả việc khối ấy làm. Chuẩn hoá dựng lại khối từ
#: một danh sách khoá cố định (cố ý — để file rác không lọt vào), nên mấy khoá này phải
#: được chép tay sang, nếu không mở lại file là sơ đồ tự xếp khác đi.
#:
#:   id          định danh nút trên đồ thị
#:   pos         chỗ người dùng đã kéo nút tới
#:   mau         màu người dùng tự đặt để phân loại bằng mắt — bộ chạy KHÔNG đọc
#:   ghim        số của khối này được giữ nguyên (xác nhận một vòng lặp cố ý)
#:   hat_nhan    {id, ten, x, y} — khối nằm trong mảng sơ đồ nào. CŨNG chỉ là cách
#:               nhìn: bộ chạy, đánh số, bảng Vấn đề đều không đọc. Ghi trên TỪNG
#:               khối chứ không thành một danh sách riêng, nên lưu / mở / tự lưu /
#:               hoàn tác đều tự mang theo, không phải thêm một cửa API nào.
KHOA_CANVAS = ("pos", "mau", "ghim", "hat_nhan")


def giu_khoa_canvas(nguon, dich):
    """Chép mấy khoá "cách nhìn" từ khối gốc sang khối đã chuẩn hoá. Sửa tại chỗ."""
    if nguon.get("id"):
        dich["id"] = nguon["id"]
    pos = nguon.get("pos")
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        try:
            dich["pos"] = [float(pos[0]), float(pos[1])]
        except (TypeError, ValueError):
            pass
    mau = nguon.get("mau")
    if isinstance(mau, str) and mau.strip():
        dich["mau"] = mau.strip()
    if nguon.get("ghim") is True:
        dich["ghim"] = True
    hn = nguon.get("hat_nhan")
    if isinstance(hn, dict) and str(hn.get("id") or "").strip():
        tag = {"id": str(hn["id"]).strip(),
               "ten": str(hn.get("ten") or "").strip() or "Hạt nhân"}
        # Chỗ đứng của cái KHUNG trên sơ đồ chính: chỉ nhận số thật. Hỏng thì bỏ —
        # giao diện tự lấy góc trên-trái các khối bên trong, khung không bay đi đâu.
        for k in ("x", "y"):
            v = hn.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                tag[k] = round(v)
        dich["hat_nhan"] = tag
    else:
        dich.pop("hat_nhan", None)
    return dich


def chuan_hoa_khoi(s):
    """Một khối về đúng hình dạng lưu được.

    ⚠ CHƯA LỌC KHOÁ THEO LOẠI. Bộ khối giao dịch chưa thiết kế xong (D-12), nên khoá
    riêng của từng loại hành động còn được giữ nguyên xi. Khi có từ điển khối thì chỗ
    này đổi thành dựng lại từ một danh sách khoá cố định, đúng như Jenifer làm — và
    đó mới là chỗ chặn file rác."""
    if not isinstance(s, dict):
        return None
    kind = s.get("kind")
    if kind == KIND_START:
        ra = {"kind": KIND_START, "name": (s.get("name") or "").strip() or "Bắt đầu"}
        # Dựng lại từ DANH SÁCH Ô CỐ ĐỊNH của từ điển, không chép bừa mọi khoá: đây
        # đúng là chỗ chặn file rác mà `TIEP_TUC.md` vẫn ghi là còn thiếu.
        for o in bat_dau.o_cua(s):
            ra[o["ten"]] = (s[o["ten"]] if o["ten"] in s
                            else _chep_sau(o["mac_dinh"]))
    elif kind == KIND_GROUP:
        acts = [dict(a) for a in (s.get("actions") or []) if isinstance(a, dict)]
        ra = {"kind": KIND_GROUP, "name": (s.get("name") or "").strip() or "Nhóm mới",
              "actions": acts}
    else:
        ra = {k: v for k, v in s.items() if k not in KHOA_CANVAS}
        ra["kind"] = KIND_ACTION
        ra.pop("id", None)
    giu_khoa_canvas(s, ra)
    if not ra.get("id"):
        ra["id"] = new_step_id()
    return ra


def normalize_process(data):
    """Một tài liệu cỗ máy về đúng hình dạng lưu được, dù nó đến từ đâu.

    Nhận cả file cũ (thiếu `edges` thì nối thành chuỗi thẳng) lẫn file sửa tay."""
    d = data if isinstance(data, dict) else {}
    steps = [x for x in (chuan_hoa_khoi(s) for s in (d.get("steps") or [])) if x]
    ensure_step_ids(steps)
    edges = d.get("edges")
    edges = clean_edges(edges, steps) if edges is not None else default_edges(steps)
    return {
        "schema": SCHEMA,
        "type": LOAI_TAI_LIEU,
        "name": str(d.get("name") or "").strip() or "Strategy mới",
        "steps": steps,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

#: Số hiệu định dạng file. Tăng khi hình dạng đổi tới mức file cũ phải di cư.
SCHEMA = 1
#: Một STRATEGY — sơ đồ PHẲNG duy nhất. Không chia năm trạm: cấu trúc do người chơi
#: tự đặt bằng hạt nhân, không do app áp sẵn (xem `KHOA_CANVAS`).
#:
#: Gọi là «Strategy» chứ không «Process» (tên bên Jenifer) và cũng không «cỗ máy»: thứ
#: người dùng lưu ra ở đây là một CHIẾN LƯỢC giao dịch, và đó cũng là từ QuantConnect
#: dùng cho đúng vật ấy.
LOAI_TAI_LIEU = "strategy"


def make_process_template(name, steps, edges=None):
    """Đóng gói cả Strategy thành một tài liệu lưu được."""
    return normalize_process({"name": name, "steps": steps, "edges": edges})


