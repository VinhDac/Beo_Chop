"""Cat_Studio — lõi.

Không phụ thuộc giao diện, không import tkinter/webview → test được mà không mở cửa sổ nào.
Mọi hiểu biết về ĐỊNH DẠNG FILE nằm ở đây; `api.py` chỉ chuyển JSON, `webui/` chỉ vẽ.

Ba tầng:  webui/ (vẽ)  →  api.py (cầu nối duy nhất)  →  core.py (lõi)

Xem `tai_lieu/core.md` để hiểu VÌ SAO. File này giữ HÀNH VI.
"""
import json
import uuid

from . import kho
from . import luu_tru

PHIEN_BAN = "0.2"

#: Phiên bản định dạng file. 4 = nhịp chạy chuyển từ `doc["timeframe"]` (một nhịp cho cả
#: tài liệu) sang khoá `nhip` trên chính khối Bắt đầu của TỪNG sơ đồ. `normalize_process`
#: đọc được cả file cũ, nên không cần script di cư riêng.
SCHEMA = 4

# ---------------------------------------------------------------------------
# Thư mục dữ liệu
# ---------------------------------------------------------------------------


# Đường dẫn và đọc/ghi file nằm HẾT ở `luu_tru.py` — đây chỉ là lối tắt cho code cũ.
app_dir = luu_tru.thu_muc_app
load_settings = luu_tru.doc_cai_dat
save_settings = luu_tru.ghi_cai_dat

SETTINGS_DEFAULT = luu_tru.CAI_DAT_MAC_DINH

ACCENT_PRESETS = {
    "Cam": "#ffa657", "Xanh dương": "#4a9eff", "Lục": "#3fb950", "Tím": "#a371f7",
    "Đỏ": "#f85149", "Vàng": "#d29922", "Hồng": "#db61a2", "Xanh ngọc": "#39c5cf",
}


# ---------------------------------------------------------------------------
# Khung thời gian — Ổ CẮM TRỐNG
# ---------------------------------------------------------------------------
#
# ⚠ `TIMEFRAMES` · `TF_PHUT` · `MA_METHODS` · `NHIP_MAC_DINH` đã đi ở đợt 3.
#
# Cả bốn nói về một thế giới dựng bằng NẾN: chín khung từ M1 tới MN1, số phút của mỗi
# khung để gộp nến, bốn kiểu trung bình động, và nhịp mặc định "Entry mỗi nến M5 ·
# Manage mỗi nến M1".
#
# Nhịp M5/M1 khác nhau là CÓ CHỦ Ý và lý do đáng giữ lại trong đầu: Entry là QUYẾT
# ĐỊNH nên 5 phút xem một lần là đủ, còn Manage là PHẢN ỨNG nên càng nhanh càng đúng.
# Một market maker đẩy cùng lý lẽ đó tới tận cùng — cả hai đều là phản ứng, và nhịp
# không còn đo bằng nến nữa. Nên khung thời gian không "đổi số", nó biến mất.
#
# Khối Bắt đầu vì thế KHÔNG còn trường `nhip`. Xem `tai_lieu/o_cam_trong.md`.
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

KIND_LABELS = {
    KIND_START: "Bắt đầu",
    KIND_ACTION: "Khối",
}


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
VAO_LENH = "vao_lenh"
SUA_LENH = "sua_lenh"

ACTION_TYPES = [CHECK_COND, VAO_LENH, SUA_LENH]

# Nhãn THUẦN CHỮ, không emoji: chúng hiện ở dropdown "Loại:" của hộp thoại, và giao
# diện tự vẽ icon nét theo `type` cho khớp phần còn lại.
ACTION_LABELS = {
    CHECK_COND: "Kiểm tra điều kiện",
    VAO_LENH: "Vào lệnh",
    SUA_LENH: "Sửa lệnh",
}

# ---------------------------------------------------------------------------
# HAI SƠ ĐỒ trong một chiến lược
# ---------------------------------------------------------------------------
#
#   ENTRY   — con trỏ đi SĂN. Chạy lại từ khối Bắt đầu ở mỗi nến. Có thể SINH một lệnh.
#   MANAGE  — chạy MỘT LƯỢT CHO MỖI LỆNH đang sống, cũng từ đầu, cũng mỗi nến.
#
# Thứ tự trong một nến:  cập nhật dữ liệu → MANAGE (từng lệnh) → ENTRY.
# Manage TRƯỚC Entry, đúng `OnTick` của D_02: CheckPendingActivation → ManageBreakEven
# → rồi mới tới phần quyết định. Chạy ngược lại thì lệnh vừa sinh bị quản lý ngay
# trong chính nến đẻ ra nó.
#
# Manage KHÔNG giữ con trỏ giữa các nến: nó tính lại từ trạng thái quan sát được, y
# như D_02 làm mỗi tick. Nhờ vậy mấy câu guard kiểu `if(sl >= entry) continue` không
# còn nằm trong code mà HIỆN RA THÀNH CỔNG trên sơ đồ.
TAB_ENTRY = "entry"
TAB_MANAGE = "manage"
TABS = [TAB_ENTRY, TAB_MANAGE]
TAB_LABELS = {TAB_ENTRY: "Entry", TAB_MANAGE: "Manage"}

# Entry chỉ TẠO, Manage chỉ SỬA. Một câu, và soát tĩnh được.
ACTION_TABS = {
    CHECK_COND: (TAB_ENTRY, TAB_MANAGE),
    VAO_LENH: (TAB_ENTRY,),
    SUA_LENH: (TAB_MANAGE,),
}


def hanh_dong_cua_tab(tab):
    return [t for t in ACTION_TYPES if tab in ACTION_TABS[t]]

# Hành động QUYẾT ĐỊNH ĐƯỜNG ĐI: không khớp thì nhánh đang chạy chết tại đó.
BRANCH_TYPES = (CHECK_COND,)

# ---- TỪ VỰNG — Ổ CẮM TRỐNG ------------------------------------------------
#
# ⚠ ~320 dòng từ vựng đã đi ở đợt 3 của lần dọn sang HFT market maker. Cái mất không
# phải vài bảng tra: nó là TOÀN BỘ NỘI DUNG mà một khối hành động từng mang được.
#
#   TOAN_HANG        17 toán hạng — giá · ATR · MA · sổ lệnh · "lệnh này" · zone
#   PHEP_SO          < ≤ > ≥ = ≠ · là ĐÚNG / là SAI
#   DON_VI           giá · bps · × ATR · × ATR zone · × R · mép zone đối diện
#     + DON_VI_CHO · DON_VI_NGAN · DON_VI_CHINH_NO · DON_VI_CAN_ZONE · LOAI_DON_VI
#     + DON_VI_DEM · NHAN_DON_VI · TOAN_HANG_DON_VI và bốn bảng "tên cũ → tên mới"
#   MOC_ENTRY        đỉnh zone · đáy zone · giá hiện tại
#   LOAI_LENH        Thị trường · Chờ Stop
#   SUA_CHE_DO       dời SL · dời TP · SL về hoà vốn · kết thúc lệnh này
#   BẢNG THAM SỐ     hằng số có tên, và cảnh báo "số gõ tay hai chỗ"
#
# VÌ SAO ĐI CẢ CỤM chứ không giữ lại vài chữ "chắc vẫn dùng được":
#
#   1. Mỗi đơn vị là một PHÉP TÍNH, và phép tính nằm ở `bo_chay._quy_doi` / `_khoang`
#      — đã xoá ở đợt 2. Một đơn vị không có bộ quy đổi là một dòng trong dropdown
#      không sinh ra được con số nào.
#   2. `atr` · `atr_zone` · `R` · `bien_zone` đo bằng thước của một chiến lược dựng
#      trên nến và stop-loss. Market maker đo bằng spread và tồn kho — thước khác hẳn,
#      không phải cùng thước đổi tên.
#   3. Giữ nửa bảng thì hộp thoại bày ra một dropdown lưng chừng, và người dùng phải
#      đoán vì sao có `bps` mà không có `× ATR`. Rỗng hẳn thì câu trả lời rõ: chưa có.
#
# CÒN LẠI ĐÚNG BA THỨ, và cả ba là NGỮ PHÁP của Cat_Studio chứ không phải từ vựng của
# một sàn hay một chiến lược — chúng đã đứng vững qua cả D_02 lẫn MT5 và sẽ đứng tiếp:
#
#   · ba động từ  `check_cond` · `vao_lenh` · `sua_lenh`   (khai phía trên)
#   · ranh giới   Entry chỉ TẠO · Manage chỉ SỬA           (khai phía trên)
#   · hai phía    Mua · Bán                                 (ngay dưới đây)
#
# Xem `tai_lieu/o_cam_trong.md`. Bản cũ: `git show f1c90fb:cat_studio/core.py`.

#: Danh mục do `kho/` gom từ các module con — HIỆN RỖNG, xem `kho/__init__.py`.
#: Dây nối giữ nguyên: thả một module vào `kho.MODULE` là những bảng này có nội dung
#: ngay, không phải sờ vào `core.py`.
TOAN_HANG = kho.TOAN_HANG
TOAN_HANG_KEYS = kho.TOAN_HANG_KEYS
TOAN_HANG_LABELS = {t["key"]: t["nhan"] for t in TOAN_HANG}

#: HAI PHÍA. Không phải tham số chiến lược — đây là bản chất của một lệnh, và là trục
#: duy nhất của khối `Vào lệnh` còn sống sót. Nó cũng quyết màu khối (`api._mau_khoi`):
#: Mua xanh, Bán đỏ, nhìn xa là thấy sơ đồ nghiêng về phía nào.
HUONG = {"mua": "Mua", "ban": "Bán"}
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


def make_start_step(name="Chạy lại từ đây"):
    """Khối BẮT ĐẦU — không làm gì cả, nhưng nói ra một điều quan trọng.

    CẢ SƠ ĐỒ là một vòng lặp: nó chạy lại từ khối này ở MỖI LƯỢT. Nên "chờ tới khi"
    không phải vẽ — không cổng nào khớp thì hết lượt, lượt sau tự chạy lại từ đây.

    Đúng MỘT khối mỗi sơ đồ, tạo sẵn khi mở canvas trắng, không xoá được và không nhận
    đường nối đi vào. Nhờ nó `flow_entry` không bao giờ trả None, nên một đường nối
    ngược lên trên không thể "nuốt" mất điểm bắt đầu (xem core.md §3.3).

    ⚠ Tham số `nhip` ĐÃ BỎ (đợt 3). Nó ghi khung nến của lượt chạy — "Mỗi nến M5" cho
    Entry, "M1" cho Manage — mà khung thời gian là khái niệm của một thế giới dựng
    bằng nến. `normalize_step` vứt khoá `nhip` trong file cũ đi, không báo lỗi: sơ đồ
    vẫn mở được, chỉ mất một dòng chữ trên hộp."""
    return {"kind": KIND_START, "id": new_step_id(), "name": name}


def make_action_step(action):
    """Bọc một hành động thành một khối.

    GIỮ LẠI `action["id"]` nếu có: nếu không thì mỗi lần sửa hành động là khối đổi id
    và mọi đường nối trỏ vào nó gãy hết."""
    st = dict(action or {})
    st["kind"] = KIND_ACTION
    st["id"] = st.get("id") or new_step_id()
    return st


def step_title(step):
    ten = (step.get("name") or "").strip()
    if ten:
        return ten
    if is_start_step(step):
        return "Bắt đầu"
    return ACTION_LABELS.get(step.get("type"), "Hành động")


# ---------------------------------------------------------------------------
# Mô tả hành động — CHỮ HIỆN TRÊN HỘP DO ĐÂY SINH
# ---------------------------------------------------------------------------
# Giao diện không tự ghép câu: nếu nó ghép thì sớm muộn nó mô tả khác với thứ lõi
# thực sự hiểu, và người dùng tin vào cái sai. LUẬT NÀY KHÔNG ĐỔI dù chữ có ngắn tới
# đâu — đó là lý do hai hàm dưới đây ở lại thay vì để JS tự ghép mấy chữ còn sót.
#
# ⚠ ~220 dòng đã đi ở đợt 3 cùng với từ vựng: `khoang_display` · `toan_hang_display` ·
# `ve_phai_display` · `cond_display`, và ba hàm phụ `_so` · `_thay_so` ·
# `_so_hoac_ten` (thay một TÊN THAM SỐ bằng giá trị của nó khi vẽ chữ).
#
# Chúng dựng ra những câu kiểu:
#
#     ATR(M5, 14) < 7 bps của giá
#     Vào lệnh Mua Chờ Stop · 0.01 lot · đệm 0.1 × ATR ngoài mép vùng · SL 1.5 × ATR
#       zone · TP 2 × R
#
# Không câu nào còn dựng được: mọi mảnh trong đó — toán hạng, phép so, đơn vị, mốc
# neo, loại lệnh, chế độ sửa — đều đã rời khỏi `core.py`. Một khối hành động bây giờ
# mang đúng ba thứ: TÊN · ĐỘNG TỪ · (với `vao_lenh`) HƯỚNG.
#
# Cắm lại: khi có từ vựng mới thì viết lại ở ĐÂY, không viết bên JS.
# Bản cũ: `git show f1c90fb:cat_studio/core.py`. Xem `tai_lieu/o_cam_trong.md`.


def action_display(a, tham_so=None):
    """Một CÂU đầy đủ mô tả khối — dùng cho tooltip và hộp thoại.

    `tham_so` giữ trong chữ ký dù hiện không dùng tới: bảng tham số sẽ quay lại cùng
    từ vựng mới, và mọi chỗ gọi (`api._the_buoc`, `api.describe`) đã truyền sẵn nó."""
    a = a or {}
    ten = (a.get("name") or "").strip()
    dau = f"{ten}: " if ten else ""
    nhan = ACTION_LABELS.get(a.get("type"), str(a.get("type")))
    if a.get("type") == VAO_LENH and a.get("huong") in HUONG:
        return f"{dau}{nhan} {HUONG[a['huong']]}"
    return dau + nhan


def dong_khoi(a, tham_so=None, tab=None):
    """Chữ trên HỘP — danh sách dòng NGẮN, mỗi trường một dòng.

    Khác `action_display` (một câu đầy đủ): trên hộp, một câu chạy dài bốn dòng thì
    đọc không ra. Tách mỗi trường một dòng thì mắt quét dọc được.

    Hiện mỗi khối chỉ còn một trường để nói, nên danh sách dài nhất là một dòng — và
    thường là rỗng. Hộp rỗng chữ là ĐÚNG với trạng thái bây giờ: khối thật sự chưa
    mang nội dung nào."""
    if is_start_step(a):
        ds = []
        if tab == TAB_MANAGE:
            # Không phải chuyện đặt tên: Manage chạy MỘT LƯỢT CHO MỖI lệnh đang sống.
            # Đó là cấu trúc, nên phải hiện ra dù người dùng đặt tên khối là gì.
            ds.append("một lượt cho MỖI lệnh đang sống")
        return ds

    if (a or {}).get("type") == VAO_LENH and a.get("huong") in HUONG:
        return [HUONG[a["huong"]]]
    return []


def step_display(step):
    if is_start_step(step):
        return "◆ Bắt đầu   ·  mỗi lượt chạy lại từ đây"
    return f"⚡ {action_display(step)}"
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


def canh_quay_lai(steps, edges):
    """Tập {(từ, tới)} các cạnh quay lại — giao diện vẽ nét đứt cho chúng."""
    return {tuple(c) for c in flow_order(steps, edges)["quay_lai"]}


# ---------------------------------------------------------------------------
# Soát lỗi
# ---------------------------------------------------------------------------


def _loi(ds, sev, sid, msg):
    ds.append({"severity": sev, "step": sid, "index": None, "message": msg})


def validate_flow_graph(steps, edges):
    """Soát riêng phần ĐỒ THỊ — lỗi ở mức nối dây, không phải ở mức một hành động."""
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

    # ---- HAI khối Vào lệnh trên CÙNG một đường ----
    # Cổng "số lệnh chờ = 0" chỉ được hỏi MỘT LẦN ở đầu lượt, nên hai khối Vào lệnh nối
    # tiếp nhau sẽ đẻ ra hai lệnh mà không cổng nào chặn được. D_02 chốt cứng đúng MỘT
    # lệnh chờ (`TradeManager.mqh:330-334`).
    #
    # Chặn ở đây chứ không chặn trong bộ chạy: bộ chạy phải làm ĐÚNG những gì sơ đồ vẽ,
    # còn thứ không nên vẽ thì đừng cho vẽ. Bộ chạy tự ý dừng sau lệnh đầu là nó âm thầm
    # bỏ qua một khối người dùng đã đặt vào.
    vao_lenh = [sid for sid, st in theo_id.items() if st.get("type") == VAO_LENH]
    for sid in vao_lenh:
        tham, hang = {sid}, list(ke.get(sid, []))
        while hang:
            uv = hang.pop(0)
            if uv in tham:
                continue
            tham.add(uv)
            if theo_id.get(uv, {}).get("type") == VAO_LENH:
                _loi(ra, "error", uv,
                     f"{ten(uv)} nằm SAU {ten(sid)} trên cùng một đường — một lượt sẽ "
                     f"đẻ ra HAI lệnh, mà cổng \"số lệnh chờ\" chỉ được hỏi một lần ở "
                     f"đầu lượt nên không chặn được. Hãy tách chúng thành hai NHÁNH.")
                break
            hang += ke.get(uv, [])

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
                 f'nhánh nào. Mỗi nhánh phải bắt đầu bằng khối HĐ lẻ '
                 f'"{ACTION_LABELS[CHECK_COND]}", nhiều nhất một nhánh được để trống '
                 f"làm nhánh mặc định.")
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

        # ⚠ CẢNH BÁO "hai cổng trùng điều kiện" ĐÃ BỎ (đợt 3).
        #
        # Nó so dấu vân tay của hai bộ điều kiện để bắt ca "cổng dưới không bao giờ
        # tới lượt vì cổng trên khớp trước". Không còn điều kiện thì MỌI cổng đều có
        # vân tay rỗng — phép so sẽ tố cáo mọi cặp cổng trên cùng một ngã rẽ, tức báo
        # sai trên đúng cái sơ đồ hợp lệ nhất.
        #
        # Cảnh báo này về NỘI DUNG, không về cấu trúc, nên nó thuộc về từ vựng và quay
        # lại cùng từ vựng. Xem `tai_lieu/o_cam_trong.md`.

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


def validate_actions(actions, err, tab=None, ten_tham_so=None):
    """`err(msg, i)` được gọi cho từng lỗi. Tách khỏi phần đồ thị vì đây là lỗi ở mức
    một hành động, không phải ở mức nối dây.

    `tab` = sơ đồ đang soát. Nhờ nó bắt được loại lỗi mà MQL5 không bao giờ bắt: đặt
    lệnh trong sơ đồ Manage, sửa lệnh trong sơ đồ Entry.

    ⚠ ~90 dòng đã đi ở đợt 3, và cái mất là toàn bộ phần soát NỘI DUNG:

        · cổng rỗng · toán hạng không tồn tại · thiếu khung thời gian / chu kỳ
        · phép so lệch kiểu (đúng/sai dùng phép số, và ngược lại)
        · đơn vị không quy đổi được với toán hạng đó
        · thiếu hướng · thiếu loại lệnh · thiếu mốc neo · thiếu SL ban đầu
        · lệnh chờ neo giá hiện tại mà không đệm → khớp ngay, hết là lệnh chờ
        · chế độ sửa thiếu ô khoảng cách

    Không phép nào còn ĐỐI TƯỢNG để soát: mọi trường chúng đọc đã rời khỏi khối. Giữ
    lại là mắng người dùng vì thiếu một ô mà giao diện không hề bày ra.

    CÒN LẠI HAI PHÉP, và đó đúng là hai phép không phụ thuộc sàn nào — chúng soát NGỮ
    PHÁP chứ không soát từ vựng:

      1. động từ phải nằm trong ba động từ đã biết;
      2. **Entry chỉ TẠO, Manage chỉ SỬA** — ranh giới mà cả app dựng lên để bảo vệ.

    `ten_tham_so` giữ trong chữ ký dù hiện không ai đọc: bảng tham số quay lại cùng từ
    vựng mới, và mọi chỗ gọi đã truyền sẵn nó. Xem `tai_lieu/o_cam_trong.md`."""
    for i, a in enumerate(actions or []):
        def e(m, _i=i):
            err(m, _i)
        t = (a or {}).get("type")
        if t not in ACTION_TYPES:
            e(f'Loại hành động "{t}" không còn được hỗ trợ — xoá dòng này hoặc thay '
              f"bằng loại khác.")
            continue

        if tab and tab not in ACTION_TABS[t]:
            cho = ", ".join(TAB_LABELS[x] for x in ACTION_TABS[t])
            e(f'"{ACTION_LABELS[t]}" không dùng được ở sơ đồ {TAB_LABELS[tab]} — '
              f"nó chỉ thuộc về {cho}. Entry chỉ TẠO lệnh, Manage chỉ SỬA lệnh.")
            continue

        if t == VAO_LENH and a.get("huong") not in HUONG:
            e('"Vào lệnh" chưa chọn hướng Mua/Bán.')


def validate_so_do(steps, edges, tab, ten_tham_so=None):
    """Soát MỘT sơ đồ. Thông báo dùng NHÃN trên huy hiệu, không dùng index."""
    if edges is None:
        edges = default_edges(steps)
    ra = [dict(p, tab=tab) for p in validate_flow_graph(steps, edges)]
    nhan = flow_order(steps, edges)["order"]

    for st in steps or []:
        if not isinstance(st, dict) or is_start_step(st):
            continue
        sid = st.get("id")
        n = nhan.get(sid)
        dau = f"[{n}] " if n else ""

        def err(m, i=None, _sid=sid, _dau=dau):
            ra.append({"severity": "error", "step": _sid, "index": i,
                       "tab": tab, "message": f"{_dau}{m}"})

        validate_actions([st], lambda m, i=None: err(m), tab, ten_tham_so)
    return ra


# ---------------------------------------------------------------------------
# Ổ CẮM TRỐNG — soát ZONE và BẢNG THAM SỐ
# ---------------------------------------------------------------------------
#
# ⚠ ~450 dòng đã đi ở đợt 3. Bảy hàm, hai cơ chế:
#
# **Cơ chế CỔNG ZONE** — `TOAN_HANG_CAN_ZONE` · `_khoi_can_zone` ·
# `khoi_sau_cong_zone` · `_soat_cong_zone`. Zone không do một cỗ máy ẩn dựng ra; nó do
# chính CỔNG mang cờ `cong_zone` trong sơ đồ định nghĩa — cổng qua thì zone lớn thêm
# một nến, cổng trượt thì zone chết. Bốn hàm này soát tĩnh cái hợp đồng đó: khối nào
# đọc `zone_HH` mà dòng chảy chưa đi qua cổng zone thì báo lỗi ngay trên canvas, chứ
# không để nó đọc `NaN` giữa lúc chạy. Cả cụm là ý tưởng riêng của D_02.
#
# **BẢNG THAM SỐ** — `di_o_so` · `_soat_so_lap` · `_don_vi_dang_dung` ·
# `_tham_so_dang_dung` · `toan_hang_dung` · `bang_tham_so`. Hằng số CÓ TÊN, cộng cảnh
# báo *"số 7 gõ tay ở hai khối"* kèm nút đặt tên một phát. Nó sinh ra để chặn đúng một
# lỗi: ngưỡng nén được hỏi ở cả Entry lẫn Manage, gõ số thẳng vào hai nơi thì sửa một
# chỗ là hai vế lệch nhau âm thầm.
#
# Cơ chế bảng tham số KHÔNG dính sàn nào và đáng dựng lại nguyên vẹn — nhưng nó đặt
# tên cho những con số nằm trong ĐIỀU KIỆN, mà điều kiện thì vừa đi cùng từ vựng. Đưa
# nó về trước từ vựng là dựng một cái bảng không có gì để đặt tên.
#
# Xem `tai_lieu/o_cam_trong.md`. Bản cũ: `git show f1c90fb:cat_studio/core.py`.


def bang_tham_so(doc):
    """Bảng tra `{tên: giá trị}` của một tài liệu — LUÔN RỖNG cho tới khi bảng tham số
    quay lại.

    Giữ hàm chứ không xoá: `api.describe`, `api._kem_the`, `api.save_action` đều gọi
    nó trên mọi đường đi, và cả ba truyền kết quả xuống `action_display`. Bỏ hàm là
    phải sửa sáu chỗ gọi rồi sửa ngược lại khi bảng tham số trở về."""
    return {}


def validate_process(doc):
    """Soát CẢ HAI sơ đồ. Mỗi vấn đề mang thêm khoá `tab` để giao diện biết chỗ.

    Cố ý soát cả hai chứ không chỉ tab đang mở: giấu lỗi của tab kia đi thì người dùng
    bấm ▶ Chạy mới biết, và không hiểu vì sao.

    ⚠ ~90 dòng phép soát ở mức TÀI LIỆU đã đi ở đợt 3, tất cả đều về bảng tham số hoặc
    về nhịp nến:

      · tham số khai trùng tên — bộ chạy lấy dòng ĐẦU, chữ trên khối lấy dòng CUỐI,
        hai nơi nói hai số khác nhau trong CÙNG một lần chạy;
      · tham số khai ra mà không khối nào dùng;
      · MỘT THAM SỐ, MỘT ĐƠN VỊ — `nguong = 7` khi đọc là bps khi đọc là × ATR;
      · bảng tham số khai một đơn vị nhưng chỗ dùng đo bằng đơn vị khác;
      · số gõ tay lặp ở hai khối → gợi ý đặt tên;
      · **Manage phải chạy nhanh bằng hoặc hơn Entry** — chậm hơn thì lệnh vừa sinh
        nằm chờ vài nhịp mới được quản lý.

    Phép cuối là phép tiếc nhất và lý lẽ của nó đáng giữ trong đầu: quản lý là PHẢN
    ỨNG, vào lệnh là QUYẾT ĐỊNH, nên phản ứng không được chậm hơn quyết định. Nó cần
    `TF_PHUT` để so hai khung nến — mà khung nến thì vừa đi. Với một market maker, câu
    hỏi tương đương sẽ là về ĐỘ TRỄ chứ không về khung.

    Còn lại: soát cấu trúc đồ thị của từng sơ đồ, cộng hai phép ngữ pháp trong
    `validate_actions`. Xem `tai_lieu/o_cam_trong.md`."""
    ra = []
    for tab in TABS:
        g = (doc or {}).get(tab) or {}
        ra += validate_so_do(g.get("steps") or [], g.get("edges"), tab)
    return ra


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

_KHOA_CHUNG = ("id", "name", "pos", "ghim")


def _giu_chung(nguon, dich):
    """Chuyển các khoá dùng chung từ dict gốc sang dict đã chuẩn hoá.

    `normalize_step` dựng lại từng khối bằng danh sách khoá cố định (cố ý — để file rác
    không lọt vào). Nhưng thế thì mấy khoá này bị rơi mất: `id` là định danh nút,
    `pos` là chỗ người dùng đã kéo nút tới, `ghim` là cờ ghim số."""
    if nguon.get("id"):
        dich["id"] = nguon["id"]
    if nguon.get("name"):
        dich["name"] = str(nguon["name"])
    if nguon.get("ghim"):
        dich["ghim"] = True
    pos = nguon.get("pos")
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        try:
            dich["pos"] = [float(pos[0]), float(pos[1])]
        except (TypeError, ValueError):
            pass
    return dich


def normalize_action(a):
    """Một hành động từ file / từ giao diện → dạng CHUẨN mà lõi hiểu.

    ⚠ ~110 dòng đã đi ở đợt 3. Chúng chuẩn hoá NỘI DUNG của khối và, quan trọng hơn,
    dịch mọi file cũ sang cách gọi hiện hành — bốn bảng `*_CU` (`PHEP_CU`, `DON_VI_CU`,
    `SUA_CHE_DO_CU`, `DON_VI_THAM_SO_CU`) chính là bộ nhớ của mọi lần đổi tên đã xảy
    ra. Cộng cơ chế **so hai đại lượng** (`so_dai_luong` — MỘT cờ cho cả khối, không
    phải một chip trên từng dòng) và phép suy cờ đó ra từ file cũ không có nó.

    Không mảnh nào còn đích đến: điều kiện, đơn vị, mốc neo, loại lệnh, chế độ sửa đều
    đã rời khỏi `core.py` cùng từ vựng.

    LUẬT MỞ FILE CŨ KHÔNG ĐỔI, và đây là chỗ nó được giữ: **thà mất một trường còn hơn
    giữ một trường không ai hiểu.** Sơ đồ D_02 cũ mở lên vẫn ra đúng số khối, đúng dây
    nối, đúng nhãn — chỉ rỗng nội dung. Nó không nổ, không im lặng chạy sai, và nhìn
    vào là biết ngay còn thiếu gì.

    Xem `tai_lieu/o_cam_trong.md`. Bản cũ: `git show f1c90fb:cat_studio/core.py`."""
    if not isinstance(a, dict):
        return None
    t = a.get("type")
    if t not in ACTION_TYPES:
        return None
    ra = {"type": t}
    if a.get("name"):
        ra["name"] = str(a["name"])
    if t == VAO_LENH:
        # Trường DUY NHẤT còn lại của một khối hành động. Xem `HUONG`.
        ra["huong"] = a.get("huong") if a.get("huong") in HUONG else "mua"
    return ra


def normalize_step(s):
    if not isinstance(s, dict):
        return None
    if s.get("kind") == KIND_START:
        # ⚠ Khoá `nhip` của file cũ RƠI ĐI TẠI ĐÂY, không báo gì. Nó ghi khung nến của
        # lượt chạy ("M5"/"M1") — một khái niệm của thế giới nến, xem chú thích ở đầu
        # file. `_giu_chung` chỉ mang sang những khoá được liệt kê, nên không cần xoá.
        return _giu_chung(s, {"kind": KIND_START})
    a = normalize_action(s)
    if a is None:
        return None
    a["kind"] = KIND_ACTION
    return _giu_chung(s, a)


def _chuan_so_do(g):
    steps = [x for x in (normalize_step(s) for s in (g or {}).get("steps") or []) if x]
    ensure_step_ids(steps)
    edges = (g or {}).get("edges")
    edges = default_edges(steps) if edges is None else clean_edges(edges, steps)
    return {"steps": steps, "edges": edges}


# ---------------------------------------------------------------------------
# Ổ CẮM TRỐNG — bộ dịch tên cũ
# ---------------------------------------------------------------------------
#
# ⚠ `_doi_ten_cu` và ba bảng của nó (`TEN_CU` · `TEN_THAM_SO_CU` · `THANH_DON_VI`) đã
# đi ở đợt 3. Đó là BỘ NHỚ của mọi lần đổi tên từng xảy ra trong đời app: `vung` →
# `zone`, `atr_bps` → `atr [bps]`, `zone_range_atr` → `zone_range [× ATR]`, cùng bốn
# bảng `*_CU` nằm trong khối từ vựng.
#
# Chúng dịch những cái tên mà bây giờ KHÔNG CÒN ĐÍCH ĐẾN: dịch `atr_bps` thành `atr`
# rồi cũng chẳng có toán hạng `atr` nào để trỏ tới. Một bộ dịch mà cả hai đầu đều
# trống thì chỉ còn là mã chạy qua trong im lặng.
#
# LUẬT KHÔNG ĐỔI khi từ vựng quay lại: **mọi phép đổi tên phải nằm ở ĐÚNG MỘT CHỖ mà
# mọi file đều đi qua** — tức trong `normalize_process`, không rải ở từng chỗ đọc.
# Xem `tai_lieu/o_cam_trong.md`.


def normalize_process(doc):
    doc = doc or {}
    # ⚠ CHẶN file của bản MỚI HƠN. `normalize_action` trả None cho mọi `type` lạ và
    # `_chuan_so_do` lọc `if x`, nên khối BIẾN MẤT — kéo theo cả hai đường nối bám vào
    # nó, tức chuỗi bị CẮT ĐÔI. Rồi Ctrl+S ghi đè bản đã mất khối: hỏng vĩnh viễn, im
    # lặng. `validate_actions` có sẵn câu 'Loại hành động "…" không còn được hỗ trợ'
    # nhưng nó không bao giờ hiện được, vì mọi doc tới tay validator đều đã qua đây và
    # khối đã bị xoá trước. Chặn, đừng cố cứu — `@_bat_loi` bên `api` sẽ đưa câu này lên
    # giao diện.
    v = doc.get("schema")
    if isinstance(v, int) and not isinstance(v, bool) and v > SCHEMA:
        raise ValueError(
            f"File này thuộc bản mới hơn (schema {v}, app đang hiểu {SCHEMA}). "
            f"Cập nhật app rồi mở lại — mở bằng bản cũ sẽ MẤT những khối nó chưa biết.")
    # File schema 1 chỉ có MỘT sơ đồ ở gốc — nhận nó làm Entry. Rẻ, và mở lại được
    # mọi thứ đã lưu trước khi tách hai tab.
    if "steps" in doc and TAB_ENTRY not in doc:
        doc = dict(doc, entry={"steps": doc.get("steps"), "edges": doc.get("edges")})
    ra = {
        "schema": SCHEMA,
        "type": "strategy",
        "name": (doc.get("name") or "").strip() or "Chiến lược 1",
        "symbol": (doc.get("symbol") or "").strip() or "XAUUSD",
        # ⚠ BẢNG THAM SỐ luôn rỗng cho tới khi từ vựng quay lại. Giữ khoá chứ không bỏ:
        # `schema` không đổi, nên file lưu ra vẫn cùng hình dạng với file đọc vào, và
        # sơ đồ cũ mở lên không bị coi là hỏng. Bảng cũ trong file thì rơi đi — nó đặt
        # tên cho những con số nằm trong điều kiện, mà điều kiện đã đi.
        "tham_so": [],
    }
    for tab in TABS:
        ra[tab] = _chuan_so_do(doc.get(tab))
    return ra



def new_process():
    """Chiến lược mới — HAI sơ đồ, mỗi cái có sẵn khối Bắt đầu.

    Không mở ra canvas trắng trơn: khối Bắt đầu là điểm neo đánh số, thiếu nó thì khối
    đầu tiên người dùng thả ra sẽ tự nhận số 1 rồi đổi số ngay khi họ thả khối thứ hai
    lên phía trên nó."""
    s = load_settings()
    ra = {"schema": SCHEMA, "type": "strategy", "name": "Chiến lược 1",
          "symbol": s.get("symbol", "XAUUSD"), "tham_so": []}
    for tab, ten in ((TAB_ENTRY, "Tìm tín hiệu vào lệnh"),
                     (TAB_MANAGE, "Với TỪNG lệnh đang sống")):
        bd = make_start_step(ten)
        bd["pos"] = [80.0, 300.0]
        ra[tab] = {"steps": [bd], "edges": []}
    return ra


def clone_steps(steps):
    """Nhân bản: id MỚI cho từng khối + bảng tra cũ→mới để nối lại dây.

    Không remap là dây của bản sao trỏ về BẢN GỐC."""
    moi, tra = [], {}
    for s in steps or []:
        st = normalize_step(s)
        if not st:
            continue
        cu = st.get("id")
        st["id"] = new_step_id()
        # Cờ ghim KHÔNG chép sang bản sao: hai khối cùng ghim là hai điểm quay lại,
        # gần như chắc chắn không phải ý người dùng khi họ chỉ bấm Ctrl+D.
        st.pop("ghim", None)
        if cu:
            tra[cu] = st["id"]
        moi.append(st)
    return moi, tra


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

# CHỈ lưu được cả chiến lược, không lưu cụm khối rời.
#
# Từng có template riêng cho Vòng theo dõi và Nhóm. Bỏ: một template phải là thứ CHẠY
# ĐƯỢC. Cụm khối rời thì chưa biết nó nối vào đâu, mở ra là một mớ khối lạc không có
# đường vào — dán xong vẫn phải tự nối lại từ đầu.
TEMPLATE_KINDS = {"strategy": "Chiến lược"}


# Đọc/ghi uỷ quyền hết cho `luu_tru.py`. `kind` giữ lại cho code cũ nhưng chỉ còn
# một loại — mọi lời gọi đều là "strategy".
def list_templates(kind="strategy"):
    return luu_tru.liet_ke_chien_luoc()


def save_template(kind, name, data):
    return luu_tru.ghi_chien_luoc(name, data)


def load_template(kind, name):
    return luu_tru.doc_chien_luoc(name)


def delete_template(kind, name):
    return luu_tru.xoa_chien_luoc(name)
