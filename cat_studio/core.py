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
SCHEMA = 5

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

# HAI ĐỘNG TỪ: ĐỌC — DỰNG.
#
#   check_cond  ĐỌC  sổ lệnh + tồn kho rồi quyết ĐI ĐƯỜNG NÀO   (cổng rẽ nhánh)
#   so_hang     DỰNG một số hạng của báo giá đang được lắp
#
# ⚠ BA ĐỘNG TỪ CŨ (`check_cond` · `vao_lenh` · `sua_lenh`) CHẾT CÙNG D_02, và lý do
# đáng ghi lại vì nó là chỗ hai loại chiến lược khác nhau về BẢN CHẤT:
#
#   D_02 RỜI RẠC.     Có tín hiệu → đặt một lệnh. Về sau → dời SL của nó. Hai việc
#                     thật sự khác nhau, ở hai thời điểm khác nhau. Tách TẠO khỏi SỬA
#                     là đúng, và ranh giới Entry/Manage canh được nó bằng soát tĩnh.
#
#   MARKET MAKER      Ở MỌI thời điểm luôn có một báo giá. Nó không "tạo rồi sửa" —
#   LIÊN TỤC.         nó liên tục PHÁT BIỂU mình muốn đứng ở đâu. Cùng một câu, lần
#                     đầu thành đặt lệnh, lần sau thành huỷ-đặt-lại, nói y hệt thì
#                     KHÔNG LÀM GÌ. Ba kết quả từ một câu — chọn cái nào là việc của
#                     bộ máy, không phải của người vẽ.
#
# Ép market maker vào ngữ pháp cũ thì người vẽ phải tự viết "nếu chưa có lệnh thì Vào
# lệnh, ngược lại thì Sửa lệnh" — tức vẽ ra phần ống nước mà bộ máy phải giấu đi.
#
# ⚠ VÌ SAO KHÔNG CHỈ LÀ "MỘT ĐỘNG TỪ BÁO GIÁ" — chỗ này đã sai một lần và sửa lại.
#
# Bản đầu tôi vẽ báo giá thành BỐN NHÁNH: mù → rút · tồn kho đầy mua → chỉ bán · đầy
# bán → chỉ mua · còn lại → hai phía. Nhìn thì gọn. Nhưng nó là một BỘ CHỌN, trần của
# nó là bốn hành vi — mà nửa biên của market maker là một TỔNG:
#
#     nửa biên = nền + phần theo biến động + phần theo tồn kho + phần theo dòng lệnh
#
# Mọi số hạng CÙNG ÁP MỘT LÚC, không cái nào loại cái nào. Cây quyết định buộc phải
# liệt kê tổ hợp: k yếu tố độc lập → 2^k nhánh. Ba yếu tố là tám nhánh.
#
# Nên chia làm HAI TẦNG, và `so_hang` là tầng thứ hai:
#
#     tầng CỔNG   trạng thái HIẾM và loại trừ nhau (mù, vượt hạn cứng) → cây rẽ nhánh,
#                 ít nhánh, gần như không đổi theo thời gian
#     tầng TÍNH   đường BÌNH THƯỜNG → chuỗi số hạng cộng dồn. Thêm một yếu tố là thêm
#                 MỘT DÒNG; số nhánh không nhúc nhích.
CHECK_COND = "check_cond"
SO_HANG = "so_hang"

ACTION_TYPES = [CHECK_COND, SO_HANG]

# Nhãn THUẦN CHỮ, không emoji: chúng hiện ở dropdown "Loại:" của hộp thoại, và giao
# diện tự vẽ icon nét theo `type` cho khớp phần còn lại.
ACTION_LABELS = {
    CHECK_COND: "Kiểm tra điều kiện",
    SO_HANG: "Số hạng",
}


# ---------------------------------------------------------------------------
# MỘT SƠ ĐỒ
# ---------------------------------------------------------------------------
#
# ⚠ TỪNG LÀ HAI: `entry` đi săn (một lượt mỗi nến, chỉ nó được TẠO lệnh) và `manage`
# chạy một lượt cho MỖI lệnh đang sống (chỉ nó được SỬA). Ranh giới đó là một trong
# những quyết định cốt lõi của bản D_02, và soát tĩnh canh được nó.
#
# Nó tan vì market maker không "tạo rồi quản": ở mọi thời điểm luôn có một báo giá, và
# mỗi sự kiện là một lần phát biểu lại TOÀN BỘ báo giá đó. Không có lệnh nào để "quản
# riêng", nên "một lượt cho mỗi lệnh" mất đối tượng.
#
# Hệ quả đẹp: BỊ KHỚP KHÔNG CẦN XỬ LÝ RIÊNG. Khớp thì tồn kho đổi; sự kiện kế tiếp
# chạy lại sơ đồ, thấy tồn kho mới, phát biểu lại báo giá. Không khối nào phải nói về
# chuyện "vừa bị khớp".
#
# GIỮ `TABS` là một DANH SÁCH dù chỉ có một phần tử: cả bộ đánh số, soát lỗi, lưu file
# đều lặp trên nó. Ngày cần sơ đồ thứ hai (ví dụ một sơ đồ rủi ro chạy theo nhịp khác)
# thì thêm một dòng, không phải dựng lại.
TAB_BAO_GIA = "bao_gia"
TABS = [TAB_BAO_GIA]
TAB_LABELS = {TAB_BAO_GIA: "Báo giá"}

#: Động từ nào dùng được ở sơ đồ nào. Còn đúng một sơ đồ nên cả hai đều được — nhưng
#: giữ bảng này chứ không xoá: nó là chỗ ranh giới Entry/Manage từng sống, và là chỗ
#: một ranh giới mới sẽ sống nếu có sơ đồ thứ hai.
ACTION_TABS = {
    CHECK_COND: (TAB_BAO_GIA,),
    SO_HANG: (TAB_BAO_GIA,),
}


def hanh_dong_cua_tab(tab):
    return [t for t in ACTION_TYPES if tab in ACTION_TABS[t]]


# Hành động QUYẾT ĐỊNH ĐƯỜNG ĐI: không khớp thì nhánh đang chạy chết tại đó.
BRANCH_TYPES = (CHECK_COND,)

# ---- TỪ VỰNG của market maker ---------------------------------------------
#
# ⚠ Từ vựng cũ (17 toán hạng nến, `× ATR`, `× R`, mốc neo zone, SL/TP, chế độ sửa)
# đã đi ở đợt 3. Không phải đổi tên — thước đo khác hẳn: D_02 đo bằng ATR và bội R
# của một stop-loss, market maker đo bằng SPREAD và TỒN KHO. Bản cũ nếu cần đối chiếu:
# `git show f1c90fb:cat_studio/core.py`.

#: Danh mục do `kho/` gom từ các module con. Thả một module vào `kho.MODULE` là những
#: bảng này có nội dung ngay, không phải sờ vào `core.py`.
TOAN_HANG = kho.TOAN_HANG
TOAN_HANG_KEYS = kho.TOAN_HANG_KEYS
TOAN_HANG_LABELS = {t["key"]: t["nhan"] for t in TOAN_HANG}
#: Tên NGẮN — dùng cho chữ trên hộp và câu mô tả. Rơi về tên đầy đủ nếu module không
#: khai, nên thêm một toán hạng mà quên `ngan` thì chỉ dài chữ, không vỡ gì.
TOAN_HANG_NGAN = {t["key"]: t.get("ngan") or t["nhan"] for t in TOAN_HANG}
TOAN_HANG_NHOM = {t["key"]: t["nhom"] for t in TOAN_HANG}
TOAN_HANG_LOAI = {t["key"]: t.get("loai", "muc_gia") for t in TOAN_HANG}
TOAN_HANG_DON_VI = {t["key"]: t["don_vi"] for t in TOAN_HANG if t.get("don_vi")}
TOAN_HANG_DUNG_SAI = tuple(t["key"] for t in TOAN_HANG if t.get("dung_sai"))

#: HAI PHÍA. Không phải tham số chiến lược — đây là bản chất của một lệnh, và là trục
#: mà cả báo giá xoay quanh. Nó cũng quyết màu khối (`api._mau_khoi`).
HUONG = {"mua": "Mua", "ban": "Bán"}

# ---- PHÉP SO ---------------------------------------------------------------
# KÝ HIỆU, không phải chữ. Một cổng mang 3–4 điều kiện; viết "lớn hơn hoặc bằng" thì
# mỗi dòng dài gấp đôi và mắt phải đọc chữ thay vì liếc thấy quan hệ.
PHEP_SO = {
    "<": "<", "<=": "≤", ">": ">", ">=": "≥", "==": "=", "!=": "≠",
    # ĐÚNG/SAI là một PHÉP SO, không phải một ô tick riêng. Nhờ vậy mọi điều kiện có
    # cùng một hình dạng `[đại lượng] [phép] [lượng]` — hết ngoại lệ.
    "la_dung": "là ĐÚNG", "la_sai": "là SAI",
}
#: Phép nào KHÔNG có vế phải, và cũng là phép DUY NHẤT dùng cho toán hạng đúng/sai.
PHEP_DUNG_SAI = ("la_dung", "la_sai")

# ---- ĐƠN VỊ ----------------------------------------------------------------
#
# Ba thước, và cả ba đều là của market maker chứ không phải của chiến lược nào:
#
#   tick    bước giá NHỎ NHẤT của sàn. Bắt buộc phải có, vì không treo được lệnh ở
#           giá tuỳ ý — chỉ ở bội số tick. Mọi giá cuối cùng đều làm tròn về đây.
#   spread  thước TỰ NHIÊN của nửa biên: "treo cách công bằng nửa spread" đúng nghĩa
#           trên mọi symbol, mọi thang giá.
#   bps     phổ quát, để so giữa các symbol có thang giá khác nhau.
#   gia     số tuyệt đối. Giữ vì đôi khi cần gõ thẳng, nhưng nó KHÔNG chuẩn hoá —
#           cùng một con số mang nghĩa khác nhau trên hai symbol.
DON_VI = {
    "tick": "× tick",
    "spread": "× spread",
    "bps": "bps của giá",
    "gia": "giá tuyệt đối",
}
DON_VI_NGAN = {"tick": "tick", "spread": "× spread", "bps": "bps", "gia": "giá"}

#: ĐƠN VỊ ĐẾM — ô số KHÔNG quy đổi gì, nhưng con số trong đó vẫn đo một thứ cụ thể.
DON_VI_DEM = {"lot": "lot"}

#: MỌI đơn vị, một bảng nhãn.
NHAN_DON_VI = {**DON_VI, **DON_VI_DEM}

#: Loại đại lượng NÀO được chọn đơn vị. Còn lại: nhãn cố định, ô mờ.
#:
#: `mid` KHÔNG quy đổi được dù cũng "đơn vị giá": nó là một MỨC, không phải một BỀ
#: RỘNG. `mid / mid × 10⁴` luôn ra 10000 — một con số không nói gì.
LOAI_CO_DON_VI = "khoang_cach"

#: Loại đại lượng → đơn vị CỐ ĐỊNH của ô so với nó. `None` = không có vế phải.
LOAI_DON_VI = {"muc_gia": "gia", "dung_sai": None}

# ---- SỐ HẠNG: đích · phép · lượng · điều kiện ------------------------------
#
# Một lượt chạy DỰNG DẦN một báo giá. Trạng thái nó dựng lên:
#
#     cong_bang                giá công bằng — gốc để đo mọi thứ khác
#     bien_mua · bien_ban      treo cách công bằng bao xa, mỗi phía
#     lech                     dịch CẢ HAI phía để đẩy tồn kho về 0
#     lot_mua  · lot_ban       khối lượng mỗi phía
#
# Chốt ở CUỐI LƯỢT:
#
#     bid = cong_bang − lech − bien_mua       (lot_mua)
#     ask = cong_bang − lech + bien_ban       (lot_ban)
#
# ⚠ TÁCH MUA/BÁN NGAY TỪ ĐẦU dù chiến lược sơ cấp không dùng: miễn phí bây giờ, đắt
# về sau. Ngày muốn biên lệch hai phía thì không phải đổi mô hình. Và nhờ tách `lot`,
# KHÔNG CẦN động từ "rút" hay "tắt một phía" — chúng chỉ là `lot = 0`, `lot_mua = 0`.
DICH = {
    "cong_bang": "Giá công bằng",
    "bien": "Nửa biên (cả hai phía)",
    "bien_mua": "Nửa biên — phía MUA",
    "bien_ban": "Nửa biên — phía BÁN",
    "lech": "Lệch báo giá",
    "lot": "Khối lượng (cả hai phía)",
    "lot_mua": "Khối lượng — phía MUA",
    "lot_ban": "Khối lượng — phía BÁN",
}

#: Tên NGẮN của đích — cùng lý lẽ với `TOAN_HANG_NGAN`: dropdown cần rõ, hộp cần gọn.
#: Đây chính là mấy chữ trong sơ đồ tay mà cả ngữ pháp này dựng theo.
DICH_NGAN = {
    "cong_bang": "công bằng",
    "bien": "biên", "bien_mua": "biên mua", "bien_ban": "biên bán",
    "lech": "lệch",
    "lot": "lot", "lot_mua": "lot mua", "lot_ban": "lot bán",
}

#: Đích nào sửa CẢ HAI phía cùng lúc → nhắm `bien` là đặt cả `bien_mua` lẫn `bien_ban`.
DICH_CA_HAI = {"bien": ("bien_mua", "bien_ban"), "lot": ("lot_mua", "lot_ban")}

#: KIỂU của từng đích — quyết định `lượng` nhận cái gì.
#:
#:   muc_gia      một MỨC giá. `=` nhận một mức khác (mid, bid); `+=` nhận khoảng cách.
#:   khoang_cach  một BỀ RỘNG. Luôn nhận khoảng cách.
#:   lot          số lot.
DICH_KIEU = {
    "cong_bang": "muc_gia",
    "bien": "khoang_cach", "bien_mua": "khoang_cach", "bien_ban": "khoang_cach",
    "lech": "khoang_cach",
    "lot": "lot", "lot_mua": "lot", "lot_ban": "lot",
}

#: PHÉP. `*=` chỉ dành cho `lot` — nhân một mức giá hay một bề rộng với hệ số là phép
#: không có nghĩa vật lý nào ("gấp đôi giá công bằng" là gì?).
PHEP_GAN = {"=": "=", "+=": "+=", "*=": "×="}
PHEP_CHO_DICH = {
    "muc_gia": ("=", "+="),
    "khoang_cach": ("=", "+="),
    "lot": ("=", "+=", "*="),
}

#: THỨ TỰ TRONG CHUỖI LÀ NGỮ NGHĨA, và đây là chỗ ghi lại điều đó.
#:
#:     biên = 1 × spread   rồi   biên += 2 tick      → 1 spread + 2 tick
#:     biên += 2 tick      rồi   biên = 1 × spread   → 1 spread. Hai tick BỐC HƠI.
#:
#: Đánh số đã hiện thứ tự ra rồi, nhưng một phép `=` đứng SAU một phép `+=` trên cùng
#: một đích gần như luôn là lỗi gõ nhầm. `validate_actions` cảnh báo, không chặn —
#: có thể có người cố ý reset giữa chừng.
PHEP_GHI_DE = "="


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
    # Một chuỗi sáu số hạng mà hộp nào cũng đề "Số hạng" thì tiêu đề không nói gì.
    # Lấy ĐÍCH làm tên: nhìn danh sách khối là biết ngay khối nào động vào cái gì, kể
    # cả khi người dùng chưa đặt tên cho khối nào.
    if step.get("type") == SO_HANG and step.get("dich") in DICH_NGAN:
        return DICH_NGAN[step["dich"]]
    return ACTION_LABELS.get(step.get("type"), "Hành động")


# ---------------------------------------------------------------------------
# Mô tả hành động — CHỮ HIỆN TRÊN HỘP DO ĐÂY SINH
# ---------------------------------------------------------------------------
# Giao diện không tự ghép câu: nếu nó ghép thì sớm muộn nó mô tả khác với thứ lõi
# thực sự hiểu, và người dùng tin vào cái sai.


def _so(x):
    """Số cho người đọc: bỏ đuôi `.0`, dùng dấu phẩy thập phân kiểu Việt."""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)
    s = f"{f:.6f}".rstrip("0").rstrip(".")
    # Dấu phẩy thập phân kiểu Việt, và dấu TRỪ THẬT (U+2212) chứ không phải gạch nối.
    # `ton_kho ≤ -2000` với gạch nối trông như một khoảng nối số ở cỡ chữ nhỏ.
    return (s or "0").replace(".", ",").replace("-", "−")


def luong_display(l):
    """`{he_so, toan_hang, don_vi}` → chữ.

    ⚠ ĐƠN VỊ GHÉP ĐƯỢC SUY RA, không có bảng nào khai nó. Khi `lượng` nhân với một
    toán hạng, hệ số mang đơn vị `<đơn vị đích>/<đơn vị toán hạng>`:

        lệch += ton_kho × 0,5 tick/lot     ← "mỗi lot tồn kho thì dịch nửa tick"

    Suy chứ không khai vì một bảng đơn vị ghép sẽ phình theo tích số của hai danh sách,
    và mỗi lần thêm một toán hạng lại phải nhớ thêm mấy dòng vào đó."""
    if not isinstance(l, dict):
        return "?"
    dv = DON_VI_NGAN.get(l.get("don_vi"), l.get("don_vi") or "")
    th = l.get("toan_hang")
    if not th:
        return f"{_so(l.get('he_so', 0))} {dv}".strip()

    ten = TOAN_HANG_NGAN.get(th, th)
    # HỆ SỐ 1 KHÔNG HIỆN. `biên = 1 × spread` và `biên = spread` là cùng một câu, mà
    # câu sau ngắn hơn và đúng cách người ta nói. Chỉ giấu khi bằng đúng 1 — `0,5 ×`
    # hay `2 ×` là thông tin thật, giấu đi là mất.
    try:
        mot = float(l.get("he_so", 0)) == 1
    except (TypeError, ValueError):
        mot = False
    mau = DON_VI_DEM.get(TOAN_HANG_DON_VI.get(th), "")
    ghep = f"{dv}/{mau}" if mau else dv
    if mot and not ghep:
        return ten
    return f"{ten} × {_so(l.get('he_so', 0))} {ghep}".strip()


def dieu_kien_display(c):
    """Một điều kiện `{trai, phep, phai}` → chữ. Dùng cho CẢ cổng lẫn ô `khi`."""
    if not isinstance(c, dict):
        return "?"
    ten = (c.get("trai") or {}).get("ten")
    trai = TOAN_HANG_NGAN.get(ten, ten or "?")
    phep = c.get("phep") or "<"
    if phep in PHEP_DUNG_SAI:
        return f"{trai} {PHEP_SO[phep]}"
    p = c.get("phai") or {}
    if p.get("ten"):
        return f"{trai} {PHEP_SO.get(phep, '?')} {TOAN_HANG_NGAN.get(p['ten'], p['ten'])}"
    dv = NHAN_DON_VI.get(p.get("tinh"), p.get("tinh") or "")
    return f"{trai} {PHEP_SO.get(phep, '?')} {_so(p.get('value', 0))} {dv}".strip()


def action_display(a, tham_so=None):
    """Một CÂU đầy đủ mô tả khối — dùng cho tooltip và hộp thoại."""
    a = a or {}
    ten = (a.get("name") or "").strip()
    dau = f"{ten}: " if ten else ""
    t = a.get("type")

    if t == CHECK_COND:
        ds = a.get("conditions") or []
        if not ds:
            return dau + "Kiểm tra điều kiện — CHƯA có điều kiện nào"
        return dau + " VÀ ".join(dieu_kien_display(c) for c in ds)

    if t == SO_HANG:
        cau = (f"{DICH_NGAN.get(a.get('dich'), '?')} "
               f"{PHEP_GAN.get(a.get('phep'), '?')} "
               f"{luong_display(a.get('luong'))}")
        if a.get("khi"):
            cau += f"  ·  khi {dieu_kien_display(a['khi'])}"
        return dau + cau

    return dau + ACTION_LABELS.get(t, str(t))


def dong_khoi(a, tham_so=None, tab=None):
    """Chữ trên HỘP — danh sách dòng NGẮN, mỗi dòng một ý.

    Khác `action_display` (một câu đầy đủ, cho tooltip): nhìn hộp là để liếc ra ngay,
    rê chuột mới cần biết đủ chi tiết."""
    if is_start_step(a):
        return []

    t = (a or {}).get("type")
    if t == CHECK_COND:
        return [dieu_kien_display(c) for c in (a.get("conditions") or [])] \
            or ["chưa có điều kiện nào — luôn khớp"]

    if t == SO_HANG:
        ds = [f"{DICH_NGAN.get(a.get('dich'), '?')} {PHEP_GAN.get(a.get('phep'), '?')} "
              f"{luong_display(a.get('luong'))}"]
        if a.get("khi"):
            ds.append(f"khi {dieu_kien_display(a['khi'])}")
        # HẬU QUẢ ĐẦY ĐỦ phải hiện trên hộp, không bắt nhớ luật trong đầu. `lot = 0`
        # nghĩa là rút; `lot_mua = 0` nghĩa là bỏ hẳn một phía — hai chuyện lớn mà đọc
        # dòng trên không thấy ngay.
        if a.get("phep") == "=" and _la_khong(a.get("luong")):
            ds.append({"lot": "→ rút hết báo giá",
                       "lot_mua": "→ bỏ phía MUA",
                       "lot_ban": "→ bỏ phía BÁN"}.get(a.get("dich"), ""))
        return [x for x in ds if x]

    return [action_display(a)]


def _la_khong(l):
    """Lượng có bằng 0 không — và KHÔNG nhân với toán hạng nào."""
    if not isinstance(l, dict) or l.get("toan_hang"):
        return False
    try:
        return float(l.get("he_so", 0)) == 0
    except (TypeError, ValueError):
        return False


def step_display(step):
    if is_start_step(step):
        return "◆ Bắt đầu   ·  mỗi sự kiện chạy lại từ đây"
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

    # ⚠ PHÉP SOÁT "HAI KHỐI VÀO LỆNH TRÊN CÙNG MỘT ĐƯỜNG" ĐÃ BỎ.
    #
    # Nó chặn hai khối `vao_lenh` nối tiếp nhau, vì với D_02 thì đó là đẻ ra hai lệnh
    # mà cổng "số lệnh chờ" chỉ hỏi được một lần ở đầu lượt.
    #
    # Với market maker thì NGƯỢC LẠI: nhiều khối `so_hang` nối tiếp nhau trên một
    # đường chính là hình dạng BÌNH THƯỜNG và bắt buộc — mỗi khối cộng thêm một số
    # hạng vào báo giá đang lắp. Chặn nó là chặn đúng cái ta cần.
    #
    # Ghi lại vì nó cho thấy một luật soát tĩnh có thể ĐÚNG TUYỆT ĐỐI với một loại
    # chiến lược và SAI TUYỆT ĐỐI với loại kia. Luật soát cũng có tuổi thọ.

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


def _soat_dieu_kien(c, cho, e):
    """Một điều kiện — dùng chung cho CỔNG và cho ô `khi` của số hạng.

    Cùng một hình dạng `[đại lượng] [phép] [lượng]` ở cả hai chỗ, nên cũng cùng một
    bộ luật — không có phiên bản thứ hai để lệch dần theo thời gian."""
    ten = (c.get("trai") or {}).get("ten") if isinstance(c, dict) else None
    if ten not in TOAN_HANG_KEYS:
        e(f'{cho} chưa chọn đại lượng, hoặc "{ten}" không có trong kho.')
        return
    phep = c.get("phep")

    # ĐÚNG/SAI dùng phép riêng và KHÔNG có vế phải. Hai luật canh nhau: một đại lượng
    # số mà mang "là ĐÚNG" cũng vô nghĩa như một đại lượng đúng/sai mà mang "≥".
    if ten in TOAN_HANG_DUNG_SAI:
        if phep not in PHEP_DUNG_SAI:
            e(f'{cho} — "{TOAN_HANG_LABELS[ten]}" vốn đã đúng/sai, chỉ dùng được '
              f'"{PHEP_SO["la_dung"]}" hoặc "{PHEP_SO["la_sai"]}".')
        return
    if phep in PHEP_DUNG_SAI:
        e(f'{cho} — "{PHEP_SO[phep]}" chỉ dùng cho đại lượng đúng/sai, mà '
          f'"{TOAN_HANG_LABELS[ten]}" là một con số.')
        return
    if phep not in PHEP_SO:
        e(f"{cho} chưa chọn phép so sánh.")

    p = c.get("phai") or {}
    loai = TOAN_HANG_LOAI.get(ten)

    # Vế phải là một ĐẠI LƯỢNG KHÁC — so hai thứ cùng loại, không cần đơn vị.
    if p.get("ten"):
        if p["ten"] not in TOAN_HANG_KEYS:
            e(f'{cho} — vế phải "{p["ten"]}" không có trong kho.')
        elif TOAN_HANG_LOAI.get(p["ten"]) != loai:
            e(f'{cho} — "{TOAN_HANG_LABELS[ten]}" và "{TOAN_HANG_LABELS[p["ten"]]}" '
              f"không cùng loại đại lượng, so với nhau không ra nghĩa gì.")
        return

    if not isinstance(p.get("value"), (int, float)) or isinstance(p.get("value"), bool):
        e(f"{cho} — vế phải cần một con số.")
    dv = p.get("tinh")
    if dv and dv not in NHAN_DON_VI:
        e(f'{cho} — đơn vị "{dv}" không có.')
        return

    # ĐƠN VỊ PHẢI KHỚP LOẠI ĐẠI LƯỢNG. So `tồn kho` (lot) với `2 tick` là một câu
    # không có nghĩa vật lý — mà nếu để lọt thì nó vẫn CHẠY ĐƯỢC và cho một kết quả
    # sai trong im lặng, đúng loại lỗi đắt nhất.
    if loai == "dem":
        can = TOAN_HANG_DON_VI.get(ten)
        if dv and dv != can:
            e(f'{cho} — "{TOAN_HANG_LABELS[ten]}" đếm bằng {DON_VI_DEM.get(can, can)}, '
              f"không so được với {NHAN_DON_VI.get(dv, dv)}.")
    elif loai == "muc_gia" and dv and dv != "gia":
        e(f'{cho} — "{TOAN_HANG_LABELS[ten]}" là một MỨC giá chứ không phải bề rộng, '
          f"nên không quy đổi sang {NHAN_DON_VI.get(dv, dv)} được.")


def _soat_luong(l, dich, phep, cho, e):
    """`{he_so, toan_hang, don_vi}` — toàn bộ luật KIỂU nằm ở đây.

    Câu hỏi duy nhất: lượng này ĐO CÁI GÌ, và đích có nhận thứ đó không."""
    if not isinstance(l, dict):
        e(f"{cho} chưa có gì.")
        return
    if not isinstance(l.get("he_so"), (int, float)) or isinstance(l.get("he_so"), bool):
        e(f"{cho} — hệ số cần một con số.")

    th = l.get("toan_hang")
    if th and th not in TOAN_HANG_KEYS:
        e(f'{cho} — "{th}" không có trong kho.')
        return
    if th in TOAN_HANG_DUNG_SAI:
        e(f'{cho} — "{TOAN_HANG_LABELS[th]}" là đúng/sai, không nhân với hệ số được. '
          f'Đúng/sai thuộc về ô "khi", không thuộc về lượng.')
        return
    loai = TOAN_HANG_LOAI.get(th) if th else None
    ten = TOAN_HANG_LABELS.get(th, th)
    kieu = DICH_KIEU[dich]
    dv = l.get("don_vi")

    if kieu == "lot":
        if loai and loai != "dem":
            e(f'{cho} — "{DICH[dich]}" là số lot, chỉ nhân được với một đại lượng ĐẾM. '
              f'"{ten}" là giá.')
        elif dv and dv != "lot":
            e(f"{cho} — khối lượng đo bằng lot, không phải {NHAN_DON_VI.get(dv, dv)}.")
        return

    # Đại lượng giá TỰ MANG đơn vị của nó. Cho chọn thêm một thước nữa là mời người
    # dùng viết `spread × 2 tick` — một câu không quy được về đâu.
    if loai in ("muc_gia", "khoang_cach"):
        if dv:
            e(f'{cho} — "{ten}" đã tự mang đơn vị giá, bỏ ô thước đo đi.')
        # `=` trên một mức giá cần một MỨC; mọi trường hợp còn lại cần một KHOẢNG
        # CÁCH. Đây là luật phân biệt `công bằng = mid` (đúng) với `công bằng = spread`
        # (một giá công bằng bằng bề rộng spread — vô nghĩa, mà chạy vẫn ra số).
        can = "muc_gia" if (kieu == "muc_gia" and phep == PHEP_GHI_DE) else "khoang_cach"
        if loai != can:
            e(f'{cho} — "{DICH[dich]} {PHEP_GAN[phep]}" cần một '
              f'{"MỨC giá" if can == "muc_gia" else "KHOẢNG CÁCH giá"}, mà "{ten}" là '
              f'{"một mức" if loai == "muc_gia" else "một bề rộng"}.')
        return

    # Còn lại: một con số, hoặc một số ĐẾM nhân với hệ số → phải khai thước đo.
    if dv not in DON_VI:
        e(f'{cho} chưa chọn thước đo — {" · ".join(DON_VI.values())}.')
    elif kieu == "muc_gia" and phep == PHEP_GHI_DE and dv != "gia":
        e(f'{cho} — "{DICH[dich]} =" đặt một MỨC giá, nên con số phải là giá tuyệt '
          f"đối. {NHAN_DON_VI[dv]} là bề rộng, chỉ dùng được với `+=`.")


def validate_actions(actions, err, tab=None, ten_tham_so=None):
    """`err(msg, i)` được gọi cho từng lỗi. Tách khỏi phần đồ thị vì đây là lỗi ở mức
    MỘT hành động, không phải ở mức nối dây.

    Phần soát nội dung từng đi ở đợt 3 nay quay lại, nhưng soát một từ vựng khác hẳn:
    không còn mốc neo zone, SL ban đầu, bội R, chế độ sửa — chỉ còn ba câu hỏi, và
    cả ba đều bắt được lỗi CHẠY ĐƯỢC MÀ SAI, loại lỗi mà backtest không tố cáo:

      1. đại lượng có thật trong kho không;
      2. phép có hợp với KIỂU của đại lượng không (đúng/sai vs số, `×=` vs mức giá);
      3. đơn vị có quy đổi được không (`tồn kho ≥ 2 tick` là một câu không có nghĩa).

    `ten_tham_so` giữ trong chữ ký dù chưa ai đọc: bảng tham số sẽ quay lại, và mọi
    chỗ gọi đã truyền sẵn nó. Xem `tai_lieu/o_cam_trong.md`."""
    for i, a in enumerate(actions or []):
        def e(m, _i=i):
            err(m, _i)
        t = (a or {}).get("type")
        if t not in ACTION_TYPES:
            e(f'Loại hành động "{t}" không còn được hỗ trợ — xoá khối này hoặc đổi loại.')
            continue
        if tab and tab not in ACTION_TABS[t]:
            cho = ", ".join(TAB_LABELS[x] for x in ACTION_TABS[t])
            # `.get` chứ không `[]`: tab lạ là đúng thứ phép này sinh ra để tố cáo,
            # nên nó phải BÁO LỖI, không được ném KeyError và giết cả lượt soát.
            e(f'"{ACTION_LABELS[t]}" không dùng được ở sơ đồ '
              f'"{TAB_LABELS.get(tab, tab)}" — nó chỉ thuộc về {cho}.')
            continue

        if t == CHECK_COND:
            ds = a.get("conditions") or []
            if not ds:
                e('"Kiểm tra điều kiện" chưa có điều kiện nào — nó sẽ LUÔN khớp, và '
                  "nhánh bên cạnh không bao giờ chạy tới.")
            for k, c in enumerate(ds):
                _soat_dieu_kien(c, f"Điều kiện {k + 1}", e)

        elif t == SO_HANG:
            dich = a.get("dich")
            if dich not in DICH:
                e('"Số hạng" chưa chọn sửa cái gì.')
                continue
            phep = a.get("phep")
            cho_phep = PHEP_CHO_DICH[DICH_KIEU[dich]]
            if phep not in cho_phep:
                # `×=` trên một mức giá hay một bề rộng không có nghĩa vật lý nào —
                # "gấp đôi giá công bằng" là gì?
                them = f", không nhận {PHEP_GAN[phep]}" if phep in PHEP_GAN else ""
                e(f'"{DICH[dich]}" chỉ nhận {" · ".join(PHEP_GAN[p] for p in cho_phep)}'
                  f"{them}.")
                continue
            _soat_luong(a.get("luong"), dich, phep, "Lượng", e)
            if a.get("khi"):
                _soat_dieu_kien(a["khi"], "Điều kiện áp dụng", e)


def _khoa_nhan(n):
    """Nhãn `2A.1` → khoá sắp xếp. Tách số khỏi chữ, nếu không `10` đứng trước `2`."""
    ra, so = [], ""
    for ch in str(n):
        if ch.isdigit():
            so += ch
            continue
        if so:
            ra.append((0, int(so), ""))
            so = ""
        if ch != ".":
            ra.append((1, 0, ch))
    if so:
        ra.append((0, int(so), ""))
    return ra


def _soat_ghi_de(steps, nhan, tab):
    """Cảnh báo khi một phép `=` XOÁ MẤT một phép `+=` đứng trước nó trên cùng đích.

        biên = 1 × spread   rồi   biên += 2 tick     → 1 spread + 2 tick
        biên += 2 tick      rồi   biên = 1 × spread  → 1 spread. Hai tick BỐC HƠI.

    Đây là cái giá của việc chọn chuỗi-số-hạng thay vì cây quyết định: thứ tự trở
    thành ngữ nghĩa, nên đổi chỗ hai khối là đổi kết quả. Không có chỗ nào khác lộ ra
    điều đó — sơ đồ nhìn vẫn hợp lý, chỉ có một số hạng lặng lẽ không bao giờ có tác
    dụng, và bảng lãi lỗ thì không biết kêu.

    CẢNH BÁO chứ không chặn: đặt lại giữa chừng vẫn có thể là cố ý.

    Đi theo THỨ TỰ ĐÁNH SỐ, tức đúng thứ tự bộ chạy sẽ đi."""
    ra = []
    theo_id = {s.get("id"): s for s in (steps or []) if isinstance(s, dict)}
    thu_tu = sorted((s for s in nhan if s in theo_id), key=lambda s: _khoa_nhan(nhan[s]))

    cong_don = {}                      # đích → id khối `+=` gần nhất chưa bị đè
    for sid in thu_tu:
        st = theo_id[sid]
        if st.get("type") != SO_HANG or st.get("dich") not in DICH:
            continue
        # `biên` chạm CẢ HAI phía, nên đè lên nó là đè lên hai đích. Theo dõi từng
        # phía một (nếu không, `biên mua += …` rồi `biên = …` sẽ lọt), nhưng CHỈ KÊU
        # MỘT LẦN cho mỗi khối: hai dòng cảnh báo giống hệt nhau cho cùng một khối
        # đọc như hai lỗi khác nhau, và người dùng đi sửa hai lần.
        bi_de = []
        for d in DICH_CA_HAI.get(st["dich"], (st["dich"],)):
            if st.get("phep") == "+=":
                cong_don[d] = sid
            elif st.get("phep") == PHEP_GHI_DE and d in cong_don:
                bi_de.append(cong_don.pop(d))
        if bi_de:
            ai = " và ".join(f"[{nhan[x]}]" for x in dict.fromkeys(bi_de))
            ra.append({
                "severity": "warning", "step": sid, "index": None, "tab": tab,
                "message": f'[{nhan[sid]}] gán ĐÈ lên "{DICH[st["dich"]]}", xoá sạch '
                           f"thứ {ai} vừa cộng vào. Đổi thành `+=`, hoặc kéo khối này "
                           f"lên TRƯỚC nó."})
    return ra


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

    # Soát LIÊN KHỐI: mỗi khối trên đúng cả, chuỗi vẫn sai. Không nhét được vào
    # `validate_actions` vì nó chỉ nhìn thấy một hành động.
    ra += _soat_ghi_de(steps, nhan, tab)
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


def _chuan_dieu_kien(c):
    """Một điều kiện → dạng chuẩn, hoặc `None` nếu không còn gì để giữ.

    ⚠ TOÁN HẠNG LẠ THÌ GIỮ NGUYÊN, không vứt cả điều kiện. Vứt đi thì cổng thành RỖNG,
    và câu app nói ra là "cổng chưa có điều kiện nào" — đúng về hình thức nhưng lạc đề:
    người dùng có viết điều kiện, chỉ là nó trỏ vào một đại lượng không còn tồn tại.
    Giữ lại thì `validate_actions` nói đúng chuyện đó, và nói ra CÁI TÊN.

    Nó không chỉ là chuyện thẩm mỹ của thông báo: đổi tên hay gỡ một module trong `kho/`
    sẽ lặng lẽ ăn mất điều kiện của MỌI chiến lược đang dùng nó, mà sơ đồ nhìn vẫn
    nguyên vẹn — chỉ có một cổng bỗng luôn khớp.

    Vứt thật sự chỉ khi KHÔNG CÓ `trai` nào — lúc đó không còn gì để chỉ mặt."""
    if not isinstance(c, dict):
        return None
    ten = (c.get("trai") or {}).get("ten") if isinstance(c.get("trai"), dict) else None
    if not ten:
        return None
    la_ds = ten in TOAN_HANG_DUNG_SAI
    phep = c.get("phep")
    if phep not in PHEP_SO:
        phep = "la_dung" if la_ds else ">="
    ra = {"trai": {"ten": str(ten)}, "phep": phep}
    if phep in PHEP_DUNG_SAI:
        return ra                       # không có vế phải, và đó là toàn bộ ý nghĩa

    p = c.get("phai") if isinstance(c.get("phai"), dict) else {}
    if p.get("ten") in TOAN_HANG_KEYS:
        ra["phai"] = {"ten": p["ten"]}
        return ra
    try:
        gt = float(p.get("value", 0))
    except (TypeError, ValueError):
        gt = 0.0
    dv = p.get("tinh")
    if dv not in NHAN_DON_VI:
        # Đơn vị SUY RA TỪ LOẠI ĐẠI LƯỢNG khi file không nói. `dem` mang đơn vị riêng
        # (lot), `muc_gia` chỉ so được với giá tuyệt đối, bề rộng thì mặc định tick.
        loai = TOAN_HANG_LOAI.get(ten)
        dv = TOAN_HANG_DON_VI.get(ten) if loai == "dem" else \
            LOAI_DON_VI.get(loai, "tick")
    ra["phai"] = {"value": gt}
    if dv:
        ra["phai"]["tinh"] = dv
    return ra


def _chuan_luong(l, dich):
    """`{he_so, toan_hang, don_vi}` — luôn trả về một dict dùng được.

    Khác `_chuan_dieu_kien` ở chỗ này: thiếu điều kiện thì bỏ cả điều kiện được, còn
    một số hạng KHÔNG CÓ lượng thì không còn là số hạng. Rơi về `0` của đúng đơn vị —
    một giá trị vô hại, nhìn là biết chưa điền."""
    l = l if isinstance(l, dict) else {}
    try:
        he = float(l.get("he_so", 0))
    except (TypeError, ValueError):
        he = 0.0
    th = l.get("toan_hang")
    if th not in TOAN_HANG_KEYS or th in TOAN_HANG_DUNG_SAI:
        th = None
    ra = {"he_so": he}
    if th:
        ra["toan_hang"] = th

    kieu = DICH_KIEU.get(dich, "khoang_cach")
    if kieu == "lot":
        return dict(ra, don_vi="lot")
    # Đại lượng giá tự mang đơn vị → ô thước đo phải TRỐNG, không phải mặc định.
    if th and TOAN_HANG_LOAI.get(th) in ("muc_gia", "khoang_cach"):
        return ra
    # ⚠ KHÔNG ĐOÁN THƯỚC ĐO. `biên = 2` mà tự điền `tick` là tự chọn một CON SỐ KHÁC —
    # 2 tick và 2 bps là hai lượng khác hẳn nhau. Để trống thì `validate_actions` nói
    # "chưa chọn thước đo", và người dùng chọn cái họ định.
    #
    # Khác hẳn hai chỗ ngay trên, nơi chuẩn hoá SỬA thật: `lot` thì đơn vị chỉ có thể
    # là lot, và đại lượng giá thì đã tự mang đơn vị. Ở đó không có gì để chọn nhầm,
    # nên sửa là dọn rác chứ không phải đoán ý.
    dv = l.get("don_vi")
    return dict(ra, don_vi=dv) if dv in DON_VI else ra


def normalize_action(a):
    """Một hành động từ file / từ giao diện → dạng CHUẨN mà lõi hiểu.

    ⚠ Bộ dịch tên cũ (bốn bảng `*_CU`) đã đi ở đợt 3 và KHÔNG quay lại: nó dịch những
    cái tên của thế giới nến (`atr_bps`, `zone_range_atr`, chế độ sửa lệnh) mà bây giờ
    không còn đích đến. Dịch `atr_bps` thành `atr` rồi cũng chẳng có toán hạng `atr`
    nào để trỏ tới.

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

    if t == CHECK_COND:
        ra["conditions"] = [c for c in (_chuan_dieu_kien(x)
                                        for x in a.get("conditions") or []) if c]

    elif t == SO_HANG:
        dich = a.get("dich") if a.get("dich") in DICH else "cong_bang"
        ra["dich"] = dich
        # PHÉP SAI THÌ GIỮ NGUYÊN, KHÔNG SỬA HỘ. `biên ×= 2` là câu không có nghĩa,
        # nhưng lặng lẽ đổi nó thành `biên = 2` là đổi Ý NGHĨA của một khối rồi bày ra
        # như thể người dùng viết vậy — mà `validate_actions` đã có sẵn câu "biên chỉ
        # nhận = · +=, không nhận ×=" thì nó không bao giờ hiện được.
        #
        # Chỉ rơi về phép mặc định khi phép ấy KHÔNG PHẢI phép gán nào cả (file rác,
        # trường thiếu) — lúc đó không có gì để bảo toàn.
        phep = a.get("phep")
        ra["phep"] = phep if phep in PHEP_GAN else PHEP_CHO_DICH[DICH_KIEU[dich]][0]
        ra["luong"] = _chuan_luong(a.get("luong"), dich)
        # `khi` VẮNG MẶT chứ không phải `None`: khối không điều kiện là trường hợp
        # thường, và một khoá luôn có mặt mang giá trị rỗng sẽ khiến mọi chỗ đọc phải
        # hỏi lại "rỗng nghĩa là gì".
        khi = _chuan_dieu_kien(a.get("khi"))
        if khi:
            ra["khi"] = khi
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
    v = doc.get("schema")
    v = v if isinstance(v, int) and not isinstance(v, bool) else 0

    # ⚠ CHẶN file của bản MỚI HƠN. `normalize_action` trả None cho mọi `type` lạ và
    # `_chuan_so_do` lọc `if x`, nên khối BIẾN MẤT — kéo theo cả hai đường nối bám vào
    # nó, tức chuỗi bị CẮT ĐÔI. Rồi Ctrl+S ghi đè bản đã mất khối: hỏng vĩnh viễn, im
    # lặng. `validate_actions` có sẵn câu 'Loại hành động "…" không còn được hỗ trợ'
    # nhưng nó không bao giờ hiện được, vì mọi doc tới tay validator đều đã qua đây và
    # khối đã bị xoá trước. Chặn, đừng cố cứu — `@_bat_loi` bên `api` sẽ đưa câu này
    # lên giao diện.
    if v > SCHEMA:
        raise ValueError(
            f"File này thuộc bản mới hơn (schema {v}, app đang hiểu {SCHEMA}). "
            f"Cập nhật app rồi mở lại — mở bằng bản cũ sẽ MẤT những khối nó chưa biết.")

    # ⚠ VÀ CHẶN CẢ FILE CŨ HƠN, đây là điều mới. Trước kia mở file cũ luôn được, vì
    # mỗi lần chỉ có vài trường đổi tên — `_doi_ten_cu` dịch là xong. Lần này khác về
    # bản chất: schema 4 nói bằng ĐỘNG TỪ `vao_lenh`/`sua_lenh` trên hai sơ đồ
    # Entry/Manage, còn schema 5 chỉ có `check_cond`/`so_hang` trên MỘT sơ đồ Báo giá.
    # Không có phép dịch nào giữa hai bên: "vào lệnh Mua, SL 1.5 × ATR" không quy được
    # về một số hạng của báo giá.
    #
    # Nên mở file cũ = mọi khối rơi hết = canvas trắng mang tên chiến lược cũ. Ctrl+S
    # một cái là mất bản gốc. Đúng cái bẫy mà đoạn chặn phía trên dựng lên để tránh,
    # chỉ khác chiều. Chặn thẳng, và NÓI RA nó nằm ở đâu để lấy lại.
    if 0 < v < SCHEMA:
        raise ValueError(
            f"File này là chiến lược của bản nến/MT5 (schema {v}). App giờ nói bằng "
            f"từ vựng market maker — không có phép dịch nào giữa hai bên, mở lên sẽ "
            f"ra sơ đồ TRỐNG rồi lưu đè mất bản gốc.\n"
            f"Bản app đọc được nó: git checkout f1c90fb")

    ra = {
        "schema": SCHEMA,
        "type": "strategy",
        "name": (doc.get("name") or "").strip() or "Chiến lược 1",
        "symbol": (doc.get("symbol") or "").strip() or "BTCUSDT",
        # ⚠ BẢNG THAM SỐ vẫn rỗng. Giữ khoá chứ không bỏ: file lưu ra cùng hình dạng
        # với file đọc vào. Nó sẽ quay lại khi có chỗ ĐẶT TÊN cho những con số nằm
        # trong số hạng (`hạn_mức`, `nửa_biên_gốc`) — xem `tai_lieu/o_cam_trong.md`.
        "tham_so": [],
    }
    for tab in TABS:
        ra[tab] = _chuan_so_do(doc.get(tab))
    return ra


def new_process():
    """Chiến lược mới — MỘT sơ đồ, có sẵn khối Bắt đầu.

    Không mở ra canvas trắng trơn: khối Bắt đầu là điểm neo đánh số, thiếu nó thì khối
    đầu tiên người dùng thả ra sẽ tự nhận số 1 rồi đổi số ngay khi họ thả khối thứ hai
    lên phía trên nó."""
    s = load_settings()
    bd = make_start_step("Mỗi sự kiện")
    bd["pos"] = [80.0, 300.0]
    return {"schema": SCHEMA, "type": "strategy", "name": "Chiến lược 1",
            "symbol": s.get("symbol", "BTCUSDT"), "tham_so": [],
            TAB_BAO_GIA: {"steps": [bd], "edges": []}}


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
