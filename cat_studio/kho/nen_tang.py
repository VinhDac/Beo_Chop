"""Kho NỀN TẢNG — thứ MỌI chiến lược market maker đều có, không thuộc engine nào.

Sổ lệnh, tồn kho, sức khoẻ dữ liệu. Ba nhóm này không do chiến lược nào đóng góp:
chúng đến từ sàn và từ sổ lệnh của chính app. Gỡ hết engine ra thì chúng vẫn còn.

TÁM TOÁN HẠNG, VÀ VÌ SAO ĐÚNG TÁM
----------------------------------
Suy thẳng từ bản chất một market maker, không thêm cái nào cho đẹp:

    bid ask     treo lệnh phải biết đỉnh sổ đang ở đâu
    bid_kl      khối lượng đang đứng TRƯỚC ta ở đỉnh — đây CHÍNH LÀ hàng đợi,
    ask_kl      thứ duy nhất quyết định ta có được khớp hay không
    mid         giá công bằng đơn giản nhất
    spread      thước tự nhiên của nửa biên, và là doanh thu gộp
    ton_kho     ±lot, CÓ DẤU. Trái tim của quản trị rủi ro market making
    co_so       có nhìn thấy sổ lệnh không — mù thì phải rút, không phải đoán

Thứ ĐÁNG THÊM NGAY SAU nhưng chưa thêm, để tuyến thông trước:
    microprice  giá công bằng có trọng số theo khối lượng phía ĐỐI DIỆN. Bid chất
                40.000 lot mà ask chỉ 200 thì giá thật nằm sát ask — `mid` mù chỗ đó
    bien_dong   biến động thực trên cửa sổ N giây → giãn biên khi chợ động
    tuoi_bao_gia  quote đã nằm trong hàng bao lâu — thay cho vị trí hàng đợi
    lech_luong  lệch dòng lệnh chủ động mua/bán

⚠ KHÔNG có SL, TP, R, ATR, zone. Market maker quản rủi ro ở mức TỒN KHO, không ở
từng lệnh — nên cả cụm từ vựng đó không có chỗ đứng, không phải "chưa làm".
"""

TEN = "Core"
MA_SO = "nen_tang"
MO_TA = "Order book · inventory · data health — available to every strategy."

# Không tính chỉ báo nào, không nuôi bảng trạng thái nào.
CHI_BAO = []
BANG_TRANG_THAI = []

#: HAI TÊN cho mỗi đại lượng, và cả hai đều cần:
#:
#:   `nhan`  tên đầy đủ kèm lời giải — cho DROPDOWN, nơi người dùng đang CHỌN và cần
#:           biết mình chọn cái gì;
#:   `ngan`  tên trần — cho CHỮ TRÊN HỘP và cho câu mô tả, nơi người dùng đã biết rồi
#:           và chỉ cần liếc. `lệch += tồn kho × 0,5 tick/lot` đọc được trong một
#:           nhịp mắt; cùng câu ấy với tên đầy đủ thì tràn hộp và phải đọc bằng chữ.
#:
#: Không dùng thẳng `key` làm tên ngắn: `ton_kho` là mã, không phải tiếng Việt.
#:
#: `loai` QUYẾT ĐỊNH Ô ĐƠN VỊ — xem `core.DON_VI`.
#:
#:   `muc_gia`     — một MỨC giá (bid, ask, mid). KHÔNG quy đổi: `mid / mid × 10⁴`
#:                   luôn ra 10000, vô nghĩa. Chỉ so được với một mức khác.
#:   `khoang_cach` — một BỀ RỘNG giá (spread). Quy đổi được: tick, bps, × spread.
#:   `dem`         — số đếm. ⚠ PHẢI khai thêm `don_vi`, vì `bid_kl` và `ton_kho` cùng
#:                   đếm lot nhưng một cái là khối lượng CỦA NGƯỜI KHÁC còn một cái là
#:                   vị thế CỦA TA — gộp đơn vị thì nút chọn tham số sẽ mời nhầm.
#:   `dung_sai`    — không có vế phải.
#:
#: Tách `muc_gia` khỏi `khoang_cach` là chỗ dễ bỏ sót nhất: cả hai đều "đơn vị giá",
#: nhưng chỉ bề rộng mới chuẩn hoá được.
TOAN_HANG = [
    # ---- Sổ lệnh: cái gì đang ở đỉnh ----
    {"key": "bid", "nhan": "Bid — best buy price", "ngan": "bid", "nhom": "Order book",
     "loai": "muc_gia", "tham_so": [],
     "mo_ta": "Top of the buy side. A sell resting here fills instantly — you become the taker."},
    {"key": "ask", "nhan": "Ask — best sell price", "ngan": "ask", "nhom": "Order book",
     "loai": "muc_gia", "tham_so": []},
    {"key": "bid_kl", "nhan": "Size at bid", "ngan": "bid size", "nhom": "Order book",
     "loai": "dem", "don_vi": "lot", "tham_so": [],
     "mo_ta": "How many lots sit at the top of the book. Joining puts you BEHIND "
              "every one of them — this is the queue, the one thing that decides "
              "whether you fill at all."},
    {"key": "ask_kl", "nhan": "Size at ask", "ngan": "ask size", "nhom": "Order book",
     "loai": "dem", "don_vi": "lot", "tham_so": []},

    # ---- Suy ra từ sổ lệnh ----
    {"key": "mid", "nhan": "Mid — halfway between bid and ask", "ngan": "mid", "nhom": "Order book",
     "loai": "muc_gia", "tham_so": [],
     "mo_ta": "The simplest fair value there is. It IGNORES the size on either "
              "side, so it drifts whenever the book is lopsided — `microprice` "
              "fixes exactly that."},
    {"key": "spread", "nhan": "Spread — ask minus bid", "ngan": "spread", "nhom": "Order book",
     "loai": "khoang_cach", "tham_so": [],
     "mo_ta": "Gross revenue if both legs fill. It must beat twice the maker fee, "
              "or the sign is wrong before you even start — see `tools/do_spread.py`."},

    # ---- Của ta ----
    {"key": "ton_kho", "nhan": "Inventory (±lots)", "ngan": "inventory", "nhom": "Ours",
     "loai": "dem", "don_vi": "lot", "tham_so": [],
     "mo_ta": "Net position, SIGNED: positive is long, negative is short. The sign "
              "is the whole point — drop it and you can no longer skew your quotes, "
              "and skewing on inventory is the heart of market-making risk control."},

    # ---- Sức khoẻ dữ liệu ----
    {"key": "co_so", "nhan": "Order book visible", "ngan": "book visible",
     "nhom": "Health", "loai": "dung_sai", "tham_so": [], "dung_sai": True,
     "mo_ta": "FALSE before the first book record arrives, and right after a data "
              "gap. Every price is NaN then and every comparison fails — so a gate "
              "reading stale numbers cannot match by accident. Blind means PULL, "
              "not guess.\n"
              "⚠ It answers ONLY 'can I see?'. Whether the market is SANE (spread "
              "unusually wide, latency spiking) is a different question and will "
              "get its own operand — merging the two throws away the difference "
              "between blind and chaotic."},
]


# ---------------------------------------------------------------------------
# CÁCH TÍNH — mỗi toán hạng khai công thức của CHÍNH NÓ
# ---------------------------------------------------------------------------
#
# ⚠ Bảng này phải nằm ở ĐÂY, cạnh chỗ khai toán hạng, chứ không nằm trong bộ chạy.
#
# Bộ chạy mà tự viết cứng tám công thức thì hợp đồng "thả một module vào `kho.MODULE`
# là xong" gãy ngay: thêm `microprice` vào danh mục sẽ cho ra một dòng dropdown chọn
# được, vẽ được lên hộp, soát tĩnh không kêu — mà bộ chạy không biết tính. Nó sẽ nổ
# giữa lúc backtest, hoặc tệ hơn là lặng lẽ trả 0.
#
# `kho/__init__.py` soát ngay lúc import: khai một toán hạng mà quên công thức thì nổ
# tại chỗ, cùng loại bảo vệ với `_soat_trung`.
#
# Tham số `nh` là NHÌN — ảnh chụp thị trường + sổ của ta tại một thời điểm. Duck typing
# cố ý: module kho không được import bộ chạy, nếu không thì `kho/` hết là một danh mục
# thuần và bắt đầu phụ thuộc ngược lên tầng trên.

def _bid(nh):
    return nh.bid


def _ask(nh):
    return nh.ask


def _bid_kl(nh):
    return nh.bid_kl


def _ask_kl(nh):
    return nh.ask_kl


def _mid(nh):
    # `* 0.5` chứ không `/ 2`: nhân nhanh hơn chia, và hàm này chạy mười triệu lần/ngày.
    return (nh.bid + nh.ask) * 0.5


def _spread(nh):
    return nh.ask - nh.bid


def _ton_kho(nh):
    return nh.ton_kho


def _co_so(nh):
    return nh.co_so


#: khoá → hàm tính. Khoá phải khớp CHÍNH XÁC với `TOAN_HANG` phía trên.
TINH = {
    "bid": _bid, "ask": _ask, "bid_kl": _bid_kl, "ask_kl": _ask_kl,
    "mid": _mid, "spread": _spread, "ton_kho": _ton_kho, "co_so": _co_so,
}
