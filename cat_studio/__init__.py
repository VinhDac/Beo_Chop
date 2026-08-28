"""Cat_Studio — lõi ứng dụng.

Mọi module của app nằm trong gói này; ở thư mục gốc chỉ còn `app_web.py`, tức ĐIỂM KHỞI
ĐỘNG. Nhìn vào gốc là thấy ngay "chạy cái gì", còn "gồm những gì" thì mở gói ra xem.

Thứ tự phụ thuộc, đọc từ dưới lên — không có vòng nào:

    luu_tru      chỗ DUY NHẤT biết file nằm ở đâu
    kho/         danh mục toán hạng · chỉ báo · engine (app TỰ GOM từ đây) — ĐANG RỖNG
    core         đồ thị, đánh số, soát cấu trúc, chuẩn hoá tài liệu
    khung_cua_so vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
    api          bề mặt DUY NHẤT giao diện gọi tới

Gói CỐ Ý không re-export gì ở đây: `from cat_studio import core` phải nạp đúng module đó,
không kéo theo cả cây.

⚠ MƯỜI HAI MODULE ĐÃ ĐI trong lần dọn sang HFT market maker, và cái hố chúng để lại là
thứ quan trọng nhất phải biết khi đọc gói này:

  đợt 2 — MT5 và bộ chạy theo nến
    nguon_nen    chỗ DUY NHẤT biết MetaTrader5 — kéo nến M1, cất .npy
    ket_noi      sức khoẻ kết nối: độ trễ, feed đứng, stops_level, hiệu chuẩn
    gui_lenh     tầng đặt/sửa/huỷ lệnh, có chốt chống gửi trùng
    phien_live   vòi cấp nến cho Live
    khop_lenh    mô hình khớp — đường đi 4 điểm trong một nến M1
    tinh_toan    chỉ báo theo nến (ATR, MA, gộp khung)
    bo_chay      vòng lặp backtest — ráp tất cả những thứ trên

  đợt 3 — từ vựng
    kho/nen_tang · kho/chi_bao · kho/engine_d02   17 toán hạng, ATR/MA, máy vùng nén
    so_lenh      sổ lệnh + vùng nén, id của CHÍNH TA
    nhat_ky      nhật ký lượt chạy
    lich_su      lịch sử các lần chạy

Nghĩa là gói HIỆN KHÔNG CÓ: nguồn dữ liệu, kết nối sàn, mô hình khớp, bộ chạy, sổ lệnh,
và bất kỳ toán hạng nào. Cái còn lại là TRÌNH SOẠN THẢO SƠ ĐỒ — vẽ, nối, đánh số, ghim
số, soát CẤU TRÚC, lưu/mở — cộng hạ tầng cửa sổ và lưu trữ.

Một khối hành động vì thế mang đúng ba thứ: TÊN · ĐỘNG TỪ · (với `vao_lenh`) HƯỚNG.
Xem `tai_lieu/o_cam_trong.md`.
"""
