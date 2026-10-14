# Sổ quyết định — Cat Studio

Mỗi mục là một quyết định đã CHỐT. Không bàn lại mục `locked` trừ khi chủ dự án chủ động
mở lại; khi đó mục cũ đổi thành `superseded` và thêm mục mới.

---

## D-01 · Động cơ: chuyển hẳn sang LEAN / QuantConnect  (chốt 2026-10-14)

- **Quyết định:** Cat Studio chỉ build lớp **game**: ngôn ngữ sơ đồ thân thiện với người dùng
  (vẽ, soát lỗi, đánh số, nhật ký "vì sao", tua lại). Mọi thứ còn lại dùng của LEAN /
  QuantConnect: dữ liệu, chỉ báo, khớp lệnh, backtest, tối ưu, live, kết nối sàn.
- **Phương án đã cân nhắc:**
  (a) chỉ học LEAN, giữ động cơ riêng + MT5 /
  (b) xây cầu thử + đối chiếu, giữ MT5 song song /
  (c) chuyển hẳn sang LEAN ← **chọn**
- **Lý do:** hạ tầng (data, chỉ báo, sàn, live) tự xây thì không bao giờ xong, LEAN đã làm
  hơn chục năm. Giá trị riêng của Cat Studio là **ngôn ngữ + lời giải thích**, không phải
  động cơ. Code để máy đọc; sơ đồ + nhật ký để người đọc.
- **Ranh giới:**
  - Của ta: `core.py` (đồ thị, đánh số, soát lỗi), `kho/` (thành bản đồ sang chỉ báo LEAN),
    nhật ký, giao diện (vẽ, tester, live).
  - Của LEAN: thay `nguon_nen`, `tinh_toan`, `khop_lenh`, vòng lặp `bo_chay`, `gui_lenh`,
    `ket_noi`, `phien_live`.
  - Khái niệm của LEAN không lọt lên sơ đồ: người chơi chỉ thấy cổng, lệnh, ATR, R.
- **Hệ quả đã biết lúc chốt** (ghi để sau này không ai bất ngờ):
  - **Bỏ MT5.** LEAN không có plugin MT5; live chuyển sang sàn LEAN hỗ trợ (IBKR, OANDA,
    Binance, Bybit, Coinbase…).
  - **Phụ thuộc QuantConnect.** Live qua LEAN cần gói đăng ký QC: plugin sàn tự gọi về QC
    kiểm gói trước khi chạy, kể cả trên máy mình (đã đọc mã IBKR, Binance, OANDA). LEAN CLI
    cũng đòi gói trả phí. Data của QC miễn phí trên cloud của họ, tải về máy thì trả theo
    file. Người dùng Cat Studio muốn live cũng phải có tài khoản QC.
  - **Con số sẽ đổi.** ATR của LEAN mặc định làm mượt kiểu Wilder, của MT5 là trung bình
    cộng (đúng bẫy `core.md` §12.13). Kiểu làm mượt của từng chỉ báo phải hiện rõ trên sơ đồ.
  - **Tốc độ ▶ chưa đo.** Vòng vẽ → ▶ → xem tua là luật sống còn của game, phải đo trước
    khi build tiếp.
  - Code MT5 hiện có **giữ nguyên cho tới khi phần LEAN thay nó chạy được**, rồi mới gỡ.
- **Trạng thái:** locked
