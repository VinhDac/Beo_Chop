"""Cat_Studio — lõi ứng dụng.

Mọi module của app nằm trong gói này; ở thư mục gốc chỉ còn `app_web.py`, tức ĐIỂM KHỞI
ĐỘNG. Nhìn vào gốc là thấy ngay "chạy cái gì", còn "gồm những gì" thì mở gói ra xem.

Thứ tự phụ thuộc, đọc từ dưới lên — không có vòng nào:

    luu_tru      chỗ DUY NHẤT biết file nằm ở đâu
    so_lenh      sổ lệnh + vùng nén
    core         đồ thị, đánh số, soát lỗi, chuẩn hoá tài liệu
    kho/         danh mục toán hạng · chỉ báo · engine (app TỰ GOM từ đây)
    nhat_ky      nhật ký lượt chạy
    lich_su      lịch sử các lần chạy
    khung_cua_so vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
    api          bề mặt DUY NHẤT giao diện gọi tới

Gói CỐ Ý không re-export gì ở đây: `from cat_studio import core` phải nạp đúng module đó,
không kéo theo cả cây.

⚠ NĂM MODULE ĐÃ ĐI ở đợt 2 của lần dọn sang HFT market maker, và cái hố chúng để lại là
thứ quan trọng nhất phải biết khi đọc gói này:

    nguon_nen    chỗ DUY NHẤT biết MetaTrader5 — kéo nến M1, cất .npy
    ket_noi      sức khoẻ kết nối: độ trễ, feed đứng, stops_level, hiệu chuẩn
    gui_lenh     tầng đặt/sửa/huỷ lệnh, có chốt chống gửi trùng
    phien_live   vòi cấp nến cho Live
    khop_lenh    mô hình khớp — đường đi 4 điểm trong một nến M1
    tinh_toan    chỉ báo theo nến (ATR, MA, gộp khung)
    bo_chay      vòng lặp backtest — ráp tất cả những thứ trên

Nghĩa là gói HIỆN KHÔNG CÓ: nguồn dữ liệu, kết nối sàn, mô hình khớp, bộ chạy. Cái còn
lại là TRÌNH SOẠN THẢO SƠ ĐỒ — vẽ, đánh số, soát cấu trúc, lưu/mở — cộng hạ tầng.

`nhat_ky` và `lich_su` vì thế đang MỒ CÔI: không ai gọi chúng nữa, và cả hai vẫn mang
hình dạng dữ liệu của bộ chạy theo nến (`nen`, `j`). Chúng ở lại chờ đợt 3 quyết, không
phải vì còn dùng được. Xem `tai_lieu/o_cam_trong.md`.
"""
