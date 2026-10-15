"""Cat_Studio — lõi ứng dụng.

Mọi module của app nằm trong gói này; ở thư mục gốc chỉ còn `app_web.py`, tức ĐIỂM KHỞI
ĐỘNG. Nhìn vào gốc là thấy ngay "chạy cái gì", còn "gồm những gì" thì mở gói ra xem.

Thứ tự phụ thuộc, đọc từ dưới lên — không có vòng nào:

    luu_tru       chỗ DUY NHẤT biết file nằm ở đâu
    core          đồ thị, đánh số, soát lỗi đồ thị, bảng tham số, cài đặt
    tram          TỪ ĐIỂN 5 trạm: khối Làm · đại lượng · tham số · Gom
    may           cỗ máy 5 trạm: định dạng, chuẩn hoá, soát lỗi, đánh số, chữ trên khối
    chuoi_nen     nến + chỉ báo tính dần (thuần Python, chạy cả trên QuantConnect)
    bo_may        bộ máy chạy cỗ máy 5 trạm — ra mục tiêu và ý định lệnh
    mau_tram      22 mẫu dựng sẵn từng trạm + bốn cỗ máy dựng sẵn
    nhat_ky_may   chữ «vì sao» của từng lượt
    goi_qc        đóng gói bộ file gửi lên QuantConnect
    qc_api        nói chuyện với API của QuantConnect
    ket_qua_may   đọc nhật ký tải về
    game          luật chơi: màn, boss, sao, sổ nộp
    qc_chay       một lượt chạy trên QC, trong luồng nền
    khung_cua_so  vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
    api           bề mặt DUY NHẤT giao diện gọi tới

Gói CỐ Ý không re-export gì ở đây: `from cat_studio import core` phải nạp đúng module đó,
không kéo theo cả cây — nạp `api` là kéo theo cả lớp cửa sổ Win32, mà `tests/test_may`
chỉ cần `may`.

Bộ chạy cũ (sơ đồ Entry/Manage, `bo_chay` · `khop_lenh` · `so_lenh` · `tinh_toan` ·
`nhat_ky` · `kho/`) đã bị xoá hẳn ở phần 7 của D-10: app chỉ còn MỘT thế giới — cỗ máy
5 trạm chạy trên QuantConnect.
"""
