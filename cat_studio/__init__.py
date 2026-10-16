"""Cat_Studio — lõi ứng dụng.

Mọi module của app nằm trong gói này; ở thư mục gốc chỉ còn `app_web.py`, tức ĐIỂM KHỞI
ĐỘNG. Nhìn vào gốc là thấy ngay "chạy cái gì", còn "gồm những gì" thì mở gói ra xem.

    luu_tru       chỗ DUY NHẤT biết file nằm ở đâu
    core          đồ thị, đánh số, soát lỗi đồ thị, bảng tham số, cài đặt
    tram          TỪ ĐIỂN 5 trạm: khối Làm · đại lượng · tham số · Gom
    may           cỗ máy 5 trạm: định dạng, chuẩn hoá, soát lỗi, đánh số, chữ trên khối
    mau_tram      22 mẫu dựng sẵn từng trạm + 4 cỗ máy dựng sẵn
    game          luật chơi: màn, boss, sao, sổ nộp
    qc_api        nói chuyện với API của QuantConnect (khoá, project, file, backtest)
    qc_chay       soát đầu vào một lượt chạy (rổ mã, loại thị trường, ngày, vốn)
    khung_cua_so  vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
    api           bề mặt DUY NHẤT giao diện gọi tới

**D-11: app chỉ là VỎ của QuantConnect.** Không còn module nào mô phỏng thị trường tại
máy — bộ máy chạy, chuỗi nến, chỉ báo, lớp vỏ LEAN và bộ đóng gói đã bị xoá. Đường chạy
mới (dịch sơ đồ thành một thuật toán QC) chưa dựng; app hiện vẽ và soát cỗ máy được,
chưa chạy được.
"""
