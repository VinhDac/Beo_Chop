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

TEN = "Nền tảng"
MA_SO = "nen_tang"
MO_TA = "Sổ lệnh · tồn kho · sức khoẻ dữ liệu — có sẵn cho mọi chiến lược."

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
    {"key": "bid", "nhan": "Bid — giá mua tốt nhất", "ngan": "bid", "nhom": "Sổ lệnh",
     "loai": "muc_gia", "tham_so": [],
     "mo_ta": "Đỉnh phía mua. Treo lệnh bán ở đây là khớp ngay — thành taker."},
    {"key": "ask", "nhan": "Ask — giá bán tốt nhất", "ngan": "ask", "nhom": "Sổ lệnh",
     "loai": "muc_gia", "tham_so": []},
    {"key": "bid_kl", "nhan": "Khối lượng ở Bid", "ngan": "KL bid", "nhom": "Sổ lệnh",
     "loai": "dem", "don_vi": "lot", "tham_so": [],
     "mo_ta": "Đang có bao nhiêu lot đứng ở đỉnh mua. Treo vào đó là ta xếp SAU chừng "
              "ấy — đây chính là hàng đợi, thứ quyết định có được khớp hay không."},
    {"key": "ask_kl", "nhan": "Khối lượng ở Ask", "ngan": "KL ask", "nhom": "Sổ lệnh",
     "loai": "dem", "don_vi": "lot", "tham_so": []},

    # ---- Suy ra từ sổ lệnh ----
    {"key": "mid", "nhan": "Mid — giữa bid và ask", "ngan": "mid", "nhom": "Sổ lệnh",
     "loai": "muc_gia", "tham_so": [],
     "mo_ta": "Giá công bằng đơn giản nhất. Nó KHÔNG nhìn khối lượng hai bên, nên "
              "lệch khi sổ lệnh mất cân — `microprice` sẽ vá chỗ đó."},
    {"key": "spread", "nhan": "Spread — ask trừ bid", "ngan": "spread", "nhom": "Sổ lệnh",
     "loai": "khoang_cach", "tham_so": [],
     "mo_ta": "Doanh thu gộp nếu ăn trọn cả hai chân. Phải lớn hơn hai lần phí maker, "
              "nếu không thì âm dấu ngay từ đầu — xem `tools/do_spread.py`."},

    # ---- Của ta ----
    {"key": "ton_kho", "nhan": "Tồn kho (±lot)", "ngan": "tồn kho", "nhom": "Của ta",
     "loai": "dem", "don_vi": "lot", "tham_so": [],
     "mo_ta": "Vị thế ròng, CÓ DẤU: dương là đang ôm hàng mua, âm là đang thiếu hàng. "
              "Dấu là toàn bộ ý nghĩa — bỏ dấu đi thì không lệch báo giá được, mà lệch "
              "theo tồn kho là thứ quan trọng nhất của quản trị rủi ro market making."},

    # ---- Sức khoẻ dữ liệu ----
    {"key": "co_so", "nhan": "Có thấy sổ lệnh", "ngan": "thấy sổ lệnh", "nhom": "Sức khoẻ",
     "loai": "dung_sai", "tham_so": [], "dung_sai": True,
     "mo_ta": "SAI khi chưa nhận bản ghi sổ nào, hoặc vừa ra khỏi một lỗ hổng. Lúc đó "
              "mọi mức giá đều là NaN và mọi phép so đều trượt — nên cổng đọc nhầm sẽ "
              "không khớp bừa. Mù thì phải RÚT, không phải đoán.\n"
              "⚠ Nó CHỈ trả lời 'tôi có nhìn thấy không'. Câu 'chợ có bình thường "
              "không' (spread rộng bất thường, độ trễ vọt) là chuyện khác, sẽ có toán "
              "hạng riêng — gộp hai thứ đó là mất khả năng phân biệt mù với loạn."},
]
