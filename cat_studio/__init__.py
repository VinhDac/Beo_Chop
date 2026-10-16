"""Cat_Studio — lõi ứng dụng.

Mọi module của app nằm trong gói này; ở thư mục gốc chỉ còn `app_web.py`, tức ĐIỂM KHỞI
ĐỘNG. Nhìn vào gốc là thấy ngay "chạy cái gì", còn "gồm những gì" thì mở gói ra xem.

    luu_tru       chỗ DUY NHẤT biết file nằm ở đâu
    core          đồ thị, đánh số, soát lỗi đồ thị, bảng tham số, cài đặt
    game          luật chơi: màn, boss, sao, sổ nộp
    qc_api        nói chuyện với API của QuantConnect (khoá, project, file, backtest)
    qc_chay       soát đầu vào một lượt chạy (rổ mã, loại thị trường, ngày, vốn)
    khung_cua_so  vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
    api           bề mặt DUY NHẤT giao diện gọi tới

**D-11: app chỉ là VỎ của QuantConnect.** Không còn module nào mô phỏng thị trường tại
máy — bộ máy chạy, chuỗi nến, chỉ báo, lớp vỏ LEAN và bộ đóng gói đã bị xoá.

**D-12: bộ khối cũ cũng đã xoá.** `tram` / `may` / `mau_tram` — từ điển khối, định dạng
cỗ máy 5 trạm và các mẫu dựng sẵn — không còn. Chúng được nghĩ ra TRƯỚC khi có luật
D-11, nên mỗi khối là một phép tính của riêng app chứ không phải một thứ QuantConnect
thật sự cho. Bộ khối mới sẽ dựng lại từ đầu, mỗi khối ứng với một thứ QC có thật.

Còn lại trong gói là phần KHÔNG dính bộ khối: `core` (đồ thị thuần — đánh số, soát nối
dây), `luu_tru`, `game`, `qc_api`, `khung_cua_so`, `api`. App hiện mở lên được, đặt được
khoá QC, chưa vẽ và chưa chạy được gì.
"""
