"""Cat_Studio — lõi.

Không phụ thuộc giao diện, không import tkinter/webview → test được mà không mở cửa sổ nào.
Mọi hiểu biết về ĐỊNH DẠNG FILE nằm ở đây; `api.py` chỉ chuyển JSON, `webui/` chỉ vẽ.

Ba tầng:  webui/ (vẽ)  →  api.py (cầu nối duy nhất)  →  core.py (lõi)

Xem `tai_lieu/core.md` để hiểu VÌ SAO. File này giữ HÀNH VI.
"""
import json
import uuid

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
#   · Nhóm — cấu trúc của một chiến lược đến từ TÁCH TRÁCH NHIỆM, không từ lồng hộp.
#     Gộp nhóm chỉ đẻ thêm câu hỏi "nhóm có phải một đơn vị chạy không".
KIND_START = "start"     # điểm neo đánh số — mỗi nến chạy lại từ đây
KIND_ACTION = "action"   # đúng một hành động


def is_start_step(s):
    return isinstance(s, dict) and s.get("kind") == KIND_START


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
    """Tên khối cho câu báo lỗi. Mọi khối đi qua chuẩn hoá đều CÓ tên (`may.chuan_hoa`
    đặt tên mặc định theo từ điển), nên nhánh cuối chỉ là lưới an toàn."""
    ten = (step.get("name") or "").strip()
    if ten:
        return ten
    return "Bắt đầu" if is_start_step(step) else "Khối"


# ---------------------------------------------------------------------------
# Mô tả hành động — CHỮ HIỆN TRÊN HỘP DO ĐÂY SINH
# ---------------------------------------------------------------------------
# Giao diện không tự ghép câu: nếu nó ghép thì sớm muộn nó mô tả khác với thứ lõi
# thực sự hiểu, và người dùng tin vào cái sai.


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
        a, b = e.get("from"), e.get("to")
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
    return (isinstance(step, dict) and step.get("kind") == KIND_ACTION
            and step.get("type") == CHECK_COND)


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
            khoa = _khoa_dieu_kien(theo_id[uv].get("conditions"))
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

    # ---- Khối không bao giờ chạy tới ----
    for sid in kq["unreachable"]:
        _loi(ra, "warning", sid,
             f"{ten(sid)} không bao giờ chạy tới — chưa có đường nối dẫn vào từ khối "
             f"bắt đầu.")

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
        ra.append(moi)
    return ra


# ---------------------------------------------------------------------------
# Chuẩn hoá & tài liệu
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


