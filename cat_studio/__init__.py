"""Cat_Studio — lõi ứng dụng.

Mọi module của app nằm trong gói này; ở thư mục gốc chỉ còn `app_web.py`, tức ĐIỂM KHỞI
ĐỘNG. Nhìn vào gốc là thấy ngay "chạy cái gì", còn "gồm những gì" thì mở gói ra xem.

    luu_tru       chỗ DUY NHẤT biết file nằm ở đâu
    core          đồ thị, đánh số, soát lỗi đồ thị, bảng tham số, cài đặt
    hoi · lam · bat_dau · cai_dat   bốn TỪ ĐIỂN: mỗi ô khai một thứ LEAN có thật
    sinh_ma       sơ đồ -> thuật toán LEAN Python
    chay_lean     chạy LEAN tại máy, lưu từng lượt chạy
    qc_api        nói chuyện với API của QuantConnect (khoá, project, file, backtest)
    khung_cua_so  vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
    api           bề mặt DUY NHẤT giao diện gọi tới

**D-11: app chỉ là VỎ của QuantConnect.** Không còn module nào mô phỏng thị trường tại
máy — bộ máy chạy, chuỗi nến, chỉ báo, lớp vỏ LEAN và bộ đóng gói đã bị xoá.

**D-12: bộ khối cũ cũng đã xoá.** `tram` / `may` / `mau_tram` — từ điển khối, định dạng
cỗ máy 5 trạm và các mẫu dựng sẵn — không còn. Chúng được nghĩ ra TRƯỚC khi có luật
D-11, nên mỗi khối là một phép tính của riêng app chứ không phải một thứ QuantConnect
thật sự cho. Bộ khối mới sẽ dựng lại từ đầu, mỗi khối ứng với một thứ QC có thật.

**Đã xoá `game` và `qc_chay`.** Hai module ấy là LUẬT CHƠI (màn, boss, sao, sổ nộp) và
phép soát đầu vào của cỗ máy 5 trạm — viết TRƯỚC D-11 và D-12, nên chúng tính điểm cho
một bộ máy chạy tại máy và soát một định dạng khối, mà cả hai thứ ấy đều đã bị xoá.
Không module nào import chúng nữa. Lớp game vẫn là chủ ý của dự án: **nó nằm ở
DECISIONS.md D-05 · D-06 · D-08**, và dựng lại thì dựng từ mấy quyết định ấy chứ không
từ đoạn mã đang tính điểm cho một cỗ máy không còn tồn tại.

⚠ CÒN MỘT CHỖ NỬA CHỪNG: trong `qc_api`, phần QUẢN LÝ KHOÁ đang chạy (app đặt được khoá
QC), nhưng cả luồng chạy backtest trên cloud — `tim_project` · `tao_project` ·
`bien_dich` · `chay_backtest` · `tai_nhat_ky` … — KHÔNG ai gọi. Nó là D-06 làm dở, không
phải rác: xoá nó là bỏ luôn quyết định "vòng chơi chạy qua API của QuantConnect".
"""
