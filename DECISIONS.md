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

---

## D-02 · LEAN chạy trên cloud QuantConnect  (chốt 2026-10-14)

- **Quyết định:** backtest, tối ưu và live đều chạy trên **cloud QuantConnect**. Cat Studio
  gửi sơ đồ lên, kéo kết quả và nhật ký về rồi hiển thị.
- **Phương án đã cân nhắc:**
  (a) cloud QuantConnect ← **chọn** /
  (b) LEAN trên máy (LEAN CLI + Docker) /
  (c) cả hai: máy cho vòng chơi nhanh, cloud cho data lớn và live
- **Lý do:** D-01 là "tận dụng tất cả của QC", mà kho data, live node và tối ưu chỉ có đủ
  trên cloud. Data dùng miễn phí trên cloud; người dùng không phải cài Docker hay LEAN.
- **Hiện trạng:** tài khoản QC gói **Free**, đủ để chạy backtest trên cloud qua giao diện
  web. Gọi API từ Cat Studio và chạy live có thể phải nâng gói (bảng giá ghi API từ gói
  Researcher).
- **Điều kiện mở lại:** đo thấy ▶ trên cloud chậm tới mức mất cảm giác chơi, hoặc nhật ký
  không kéo về được vì giới hạn của gói → mở lại, cân nhắc (c).
- **Trạng thái:** locked

---

## D-03 · Tốc độ ▶ trên cloud: giữ cloud, game có hai nút chạy  (chốt 2026-10-14)

- **Quyết định:** giữ D-02 (cloud). Game có **hai nút ▶**:
  - **▶ nhanh** chạy 1–3 tháng, khoảng 20 giây, để thử ý tưởng;
  - **▶ đầy đủ** chạy cả năm, khoảng 40 giây, để chấm điểm.
- **Phương án đã cân nhắc:**
  (a) giữ cloud + hai nút ▶ ← **chọn** /
  (b) mở lại D-02, thêm LEAN trên máy cho vòng chơi nhanh
- **Số đo** (slice 1, `lean/do_nhip.py`, gói Free, XAUUSD M1 năm 2025):
  - dựng lần chạy 12,5 giây · chạy 23,4 giây (343.544 nến M1, 15 nghìn điểm dữ liệu/giây)
    · từ lúc bấm tới lúc có kết quả khoảng 35–40 giây, so với khoảng 3 giây của động cơ cũ;
  - mỗi ▶ tốn khoảng 15–20 giây cố định (biên dịch + dựng máy), phần còn lại tăng theo độ
    dài dữ liệu;
  - tải sát bản thật: 68.800 lượt Entry, 52.891 lượt Manage (động cơ cũ khoảng 63 nghìn).
- **Lý do:** một động cơ, kiến trúc gọn. Khoảng 20 giây một lần thử vẫn giữ được nhịp
  vẽ → ▶ → xem vì sao; chạy cả năm chỉ cần lúc chấm điểm.
- **Còn treo:**
  - nhật ký cả năm 121.691 dòng = 12,9 MB **không cất được vào Object Store gói Free**
    (lỗi `Invalid…`, chưa biết giới hạn) → thử nén trước khi tính chuyện nâng gói;
  - đo lại khi lên gói Researcher.
- **Bài học cho slice 2:** nến M5 phải xếp hàng chờ, không được đè. Lần đo mất 243 lượt
  Entry (0,35%) ở chỗ nối phiên vì hai nến M5 đóng sát nhau.
- **Trạng thái:** locked

---

## D-04 · Cat Studio chỉ ôm thứ phục vụ vòng chơi  (chốt 2026-10-14)

- **Quyết định:** Cat Studio chỉ đưa vào app những thứ phục vụ vòng
  **vẽ → ▶ → xem vì sao → sửa**. Những gì QuantConnect đã làm tốt trên web của họ thì dùng
  thẳng trên web, không làm lại.
- **Xếp mọi thứ của QC làm ba loại:**
  - **Nằm sau nút ▶** (nối vào app): data, chỉ báo, khớp lệnh, backtest.
  - **Dùng thẳng trên web QC** (không làm lại): notebook nghiên cứu, thư viện chiến lược
    mẫu, tài liệu, diễn đàn.
  - **Thành tính năng game sau này**, thêm từng cái một: tối ưu tham số (vd "dò ngưỡng":
    bản đồ màu lời/lỗ theo tham số), live/paper trading, báo cáo.
- **Phương án đã cân nhắc:** (a) chỉ ôm thứ phục vụ vòng chơi ← **chọn** /
  (b) đưa thêm nhiều thứ của QC vào thẳng app
- **Lý do:** app gọn; làm lại thứ QC đã làm tốt vừa tốn công vừa kém hơn họ (D-01: ta chỉ
  build lớp game).
- **Trạng thái:** locked

---

## D-05 · Trái tim của trò chơi: CHẾ TẠO CỖ MÁY  (chốt 2026-10-14)

- **Quyết định:** Cat Studio là game **lắp cỗ máy giao dịch bằng khối, thả nó vào thị
  trường thật trong quá khứ, xem nó nghĩ gì ở từng nến, rồi chấm điểm nó trên đoạn thị
  trường nó chưa từng thấy**. Thể loại game lắp máy (kiểu Factorio / Opus Magnum).
- **Vòng chơi:** chọn màn → lắp máy → ▶ chạy thử → xem tua + "vì sao" → sửa → nộp, chấm
  trên **màn ẩn** → mở khoá → (cuối cùng) ra trận.
- **Phương án đã cân nhắc:**
  (a) chế tạo cỗ máy ← **chọn** /
  (b) Bạn vs Máy — luyện "sense" là trọng tâm /
  (c) Đấu trường — thi đấu, xếp hạng là trọng tâm
- **Lý do:** dùng đúng thứ Cat Studio đã mạnh (sơ đồ có luật, nhật ký "vì sao", tua lại).
  QC đưa đồ nghề; ta đưa luật chơi, mục tiêu và một tấm gương. Bệnh tự lừa mình (chỉnh
  tham số tới khi đẹp) QC chỉ cảnh báo, game của ta biến thành LUẬT: chấm trên màn ẩn.
- **Chế độ phụ:** Bạn vs Máy · Thử thách tuần · Xưởng tự do · Ra trận.
- **Khung đề xuất đi kèm** (chưa chốt từng món — bàn tiếp từng phần):
  - *Chấm điểm:* ⭐ chạy sạch · ⭐⭐ thắng boss trên màn đã thấy · ⭐⭐⭐ vẫn thắng trên màn
    ẩn · cộng điểm **độ gọn** (ít khối, ít tham số) · boss đầu tiên là **"Mua rồi giữ"**.
  - *QC thành item:* Bản đồ (dữ liệu giá) · Màn (giai đoạn lịch sử) · Giác quan (chỉ báo,
    mẫu nến) · Giác quan hiếm (dữ liệu thay thế) · Vũ khí + ma sát (kiểu lệnh, phí) ·
    5 bộ phận (Algorithm Framework) · Garage (Projects) · ▶ (Backtest) · Dò ngưỡng
    (Optimization) · Boss + bản vẽ (Strategies) · Sân tập (Paper) · Ra trận (Live) ·
    Bộ đàm (thông báo) · Cố vấn (AI) · Thư viện ngoài game (notebook, tài liệu — D-04).
  - *Bản chơi được đầu tiên:* 1 bản đồ (Vàng) · 1 màn (2024) · 1 màn ẩn (2025) · 1 boss
    (Mua rồi giữ) · khoảng 10 item.
- **Trạng thái:** locked (phần lõi); khung đi kèm còn mở

---

## D-06 · Vòng chơi chạy qua API của QuantConnect — nâng gói Researcher  (chốt 2026-10-14)

- **Quyết định:** nâng tài khoản QC lên gói **Researcher**. App Cat Studio tự gửi sơ đồ lên
  QC qua API: ▶ một chạm trong app, **app giữ màn ẩn** và **đếm số lần nộp**.
- **Phương án đã cân nhắc:**
  (a) nâng Researcher, dùng API ← **chọn** /
  (b) dựng game trên động cơ cũ trước, nối QC sau /
  (c) ở gói Free, dán tay
- **Lý do:** lõi của D-05 là màn ẩn — người chơi tự sửa ngày trong `main.py` được thì
  màn ẩn không còn ẩn. Chỉ khi app điều khiển việc chạy thì điểm mới là điểm thật. Dán tay
  mỗi vòng (~1 phút thao tác + 40 giây chạy) cũng không thành vòng chơi. Đúng hướng D-01,
  D-02; bước ra trận (D-05) đằng nào cũng cần gói trả phí.
- **Hệ quả:**
  - Tốn phí gói hằng tháng.
  - Khoá API của QC là BÍ MẬT: cất ở máy người chơi (ngoài repo), không bao giờ vào git.
  - Trần mỗi file của Researcher là 64 KB — gói hiện tại vừa một file; qua API thì app tự
    tải bao nhiêu file cũng được, không còn chuyện dán.
- **Tiến độ:** slice 3 — `tools\chay_qc.bat` gửi sơ đồ lên, chạy, tải nhật ký về, in tổng
  kết; chưa có nút trong app (core.md §15). Đã kiểm trên máy chủ QC giả; **chưa chạy trên QC
  thật** — chờ nâng gói và đặt khoá trên máy người chơi.
- **Trạng thái:** locked

---

## D-07 · Sáng tạo không trần — game có màn, nhưng thế giới mở  (chốt 2026-10-14)

- **Quyết định:** như Minecraft: màn chơi để dẫn đường và chấm điểm thật, nhưng người chơi
  xây được BẤT CỨ THỨ GÌ thị trường và LEAN cho phép, kể cả thứ ta chưa nghĩ ra. Năm thứ:
  1. **Chế độ Sáng tạo** — mọi bản đồ, giai đoạn, giác quan, bộ phận mở NGAY từ ngày đầu.
     Mở khoá dần CHỈ là lộ trình của chế độ Chiến dịch (sửa khung đề xuất ở D-05).
  2. **Khối tự chế** — gói một cụm khối thành khối mới, đặt tên, dùng lại, chia sẻ ("vùng
     nén", "phá đỉnh 20 phiên"…). Đây là "mạch đỏ" của game: vài khối gốc ghép ra vô số
     khái niệm.
  3. **Khối code** — lối thoát cho thứ khối chưa diễn tả được: một ô Python dùng thẳng
     dữ liệu LEAN, nằm trên sơ đồ như khối thường, mang dấu "hộp đen", nhật ký ghi vào/ra.
     Trần của game = trần của LEAN.
  4. **Người chơi tự tạo màn** — chọn thị trường, giai đoạn, màn ẩn, mục tiêu → thử thách
     cho người khác.
  5. **Chia sẻ và remix** — mở cỗ máy người khác, xem tua, sửa thành bản của mình.
- **Rào duy nhất: tiền thật.** Ra trận bằng tiền thật vẫn phải qua kiểm định — dây an
  toàn, không phải giới hạn. Điểm thật vẫn luôn chấm trên dữ liệu chưa thấy.
- **Phương án đã cân nhắc:** (a) cả gói ← **chọn** / (b) không có khối code (mọi thứ là sơ
  đồ nhìn thấy) / (c) bỏ rào tiền thật
- **Lý do:** ta xây game nhưng không giới hạn tiềm năng (lời chủ dự án). Minecraft hay vì
  khối đơn giản ghép ra mọi thứ, không vì màn.
- **Trạng thái:** locked

---

## D-08 · Bản chơi được đầu tiên: cửa sổ Màn chơi, luật chấm cụ thể  (đề xuất 2026-10-14)

> Chủ dự án giao "làm từ đầu đến cuối cả backend lẫn frontend, rồi mang về máy debug".
> Những chi tiết D-05 để mở được chọn ở đây **để làm cho chạy được** — chưa phải chốt.
> Sửa được hết; con số nào nằm ở đâu ghi ở core.md §16.

- **Quyết định (đề xuất):**
  - Một cửa sổ riêng **◆ Màn chơi** (nút trên ribbon, Ctrl+M), y khuôn cửa sổ Live. Hai
    chế độ: **Chiến dịch** và **Sáng tạo** (D-07: mọi symbol CFD OANDA, mọi khoảng ngày,
    không chấm).
  - Màn đầu tiên **Vàng · 2024**: ▶ nhanh = quý IV/2024 · ▶ đầy đủ = cả năm 2024 ·
    **màn ẩn = cả năm 2025**. App giữ màn ẩn: không hiện ngày, không link QC, không
    nhật ký, không lệnh của lượt nộp — chỉ điểm.
  - **Nộp** chỉ được khi đã ▶ đầy đủ ĐÚNG cỗ máy đó (cùng vân tay — sửa một tham số là cỗ
    máy khác). Mỗi lần nộp được đếm.
  - **Sao:** ★ chạy sạch = ▶ đầy đủ có ít nhất một lệnh đóng · ★★ = thêm lãi % trên màn
    đã thấy hơn % của **Mua rồi giữ** (giá đầu → giá cuối cùng khoảng) · ★★★ = thêm trên
    màn ẩn cũng hơn. Mỗi sao cần mọi sao trước nó.
  - **Độ gọn** = số khối (trừ khối Bắt đầu) + số tham số — ghi kèm mỗi lần nộp, không cộng
    vào sao (chưa có "par" từng màn).
  - **Không có chart nến** cho lượt chạy trên QC: mang chuỗi giá của QC về máy là trái
    điều khoản dữ liệu của QC. Thay vào đó mỗi lượt nhật ký mang giờ của nó, có đường vốn,
    có nút mở trang backtest trên quantconnect.com.
- **Phương án đã cân nhắc:** (a) cửa sổ riêng ← **chọn** / (b) nhét vào Strategy Tester —
  tester cần nến tại máy ở mọi chỗ, mà nến QC không được mang về / (c) chỉ công cụ dòng lệnh
- **Lý do:** đúng vòng chơi D-05 (lắp → ▶ → vì sao → sửa → nộp), màn ẩn là luật thật
  (D-06), không đụng gì tới Strategy Tester và Live đang chạy.
- **Trạng thái:** đề xuất — chủ dự án duyệt lại khi chạy thật trên máy (màn, mốc ngày,
  định nghĩa "chạy sạch", boss so bằng % giá, độ gọn).

## D-09 · Gỡ sạch MT5 — app chỉ phục vụ QuantConnect  (chốt 2026-10-14)

> Chủ dự án: *"xóa sạch dấu vết của MT5 ra khỏi app hiện tại đi, vì bây giờ trò chơi chỉ
> phục vụ cho QuantConnect thôi"*. Đây là bước "rồi mới gỡ" mà D-01 hẹn trước.

- **Quyết định:** gỡ khỏi app mọi thứ nói chuyện với MetaTrader 5 —
  - cửa sổ **Live** (chạy sơ đồ trên tài khoản MT5, đo kết nối, hiệu chuẩn, đề phòng) cùng
    nút ● Live, Ctrl+L, mục File → Mở Live;
  - **tải nến** từ terminal MT5 (kể cả tự tải khi bấm ▶) và nút "Kiểm tra kết nối MT5";
  - thư viện `MetaTrader5` khỏi requirements, gói phát hành và hướng dẫn;
  - cột `ticket` (mã lệnh của sàn) trong sổ lệnh;
  - mọi câu chữ nhắc MT5 trong giao diện và chú thích mã (nay nói đúng điều nó canh:
    công thức D_02 đã dò).
- **Còn lại:** Strategy Tester chạy tại máy trên những bộ nến **đã có** sẵn trong
  `du_lieu/nen/` — kho nến thành chỉ đọc. Thiếu phần đầu khoảng đã đặt thì ▶ dừng và nói rõ.
  Bộ chạy cũ vẫn là chuẩn đối chiếu cho cầu nối QuantConnect.
- **Hệ quả cần biết:** máy chưa có bộ nến nào thì Strategy Tester không chạy được — dữ liệu
  của QC không được mang về máy (D-08), nên app không còn nguồn nến nào để tải.
- **Trạng thái:** chốt. Chi tiết gỡ những gì, ở đâu: core.md §17. Ý "Còn lại" (Strategy
  Tester chạy trên nến tại máy) đã bị **D-10** thay: tester bỏ hẳn.


## D-10 · Cỗ máy 5 trạm theo khung của QuantConnect · khớp lệnh để QC làm · bỏ Strategy Tester  (chốt 2026-10-14)

> Chủ dự án: *"đồng ý cả 3, xoá luôn tester, xây 5 trạm đi"* — sau khi được trình bày rằng hai
> sơ đồ Entry / Manage là khuôn của EA MetaTrader (chạy theo từng nến, theo từng lệnh), còn
> QuantConnect chia một thuật toán làm 5 phần. Trước đó: *"tôi muốn xây hết 1 mạch, tất cả
> những gì xây được… ta đang làm game mà"*.

- **Quyết định (ba ý, duyệt cùng lúc):**
  1. **Một cỗ máy = 5 trạm**, đúng 5 phần trong khung thuật toán của QC:
     ① **Chọn mã** (Universe) → ② **Tín hiệu** (Alpha) → ③ **Chia vốn** (Portfolio
     Construction) → ④ **Rủi ro** (Risk Management) → ⑤ **Khớp lệnh** (Execution).
     Mỗi trạm là một sơ đồ khối CÙNG một ngữ pháp — khối Bắt đầu mang lịch chạy và phạm vi,
     cổng Hỏi (nối tiếp = VÀ, nhiều nhánh = HOẶC thử từ trên xuống), luật lùi, đánh số —
     chỉ khác **phạm vi chạy** và bộ khối **Làm**. Luật gốc: *một sơ đồ = một phạm vi chạy*.
     Thay hẳn hai sơ đồ Entry / Manage.
  2. **Khớp lệnh để QC làm.** Bộ máy của ta chỉ ra **tỷ trọng mục tiêu** và **ý định lệnh**;
     QC đổi ra số lượng, đặt lệnh, khớp (phí, trượt giá, ký quỹ). Bỏ bộ khớp lệnh riêng.
  3. **Bỏ Strategy Tester.** Không còn chạy tại máy; lối chạy duy nhất là ◆ Màn chơi trên QC.
- **Phương án đã cân nhắc:** (a) 5 trạm ← **chọn** / (b) giữ hai sơ đồ, thêm chọn mã — vẫn là
  khuôn EA, không khớp cách QC chạy / (c) một sơ đồ to gộp hết — mất "một sơ đồ = một phạm vi
  chạy", số thứ tự hết còn nghĩa.
- **Lý do:** đúng thực tế của nơi cỗ máy thật sự chạy; mỗi trạm trả lời đúng một câu hỏi, nên
  người chơi học đúng cách một quỹ thật chia việc. Tester cần nến tại máy mà nến của QC không
  được mang về (D-08) — giữ nó là giữ một thế giới thứ hai với bộ khớp lệnh lệch luật.
- **Làm theo 7 phần**, mỗi phần một bài kiểm và một commit: ① xoá tester · ② lõi cỗ máy 5 trạm
  · ③ bộ máy chạy · ④ cầu nối QC mới · ⑤ trình vẽ · ⑥ Màn chơi chạy cỗ máy 5 trạm · ⑦ dọn bộ
  máy cũ + tài liệu. Tới phần ⑦, bộ máy cũ (Entry / Manage, `bo_chay`) vẫn sống vì cầu nối QC
  hiện tại còn dùng nó.
- **Chốt thêm (2026-10-15, lúc làm phần ⑥): vân tay cỗ máy là vân tay LOGIC, không có
  `id` khối.** Vé nộp ("đúng cỗ máy đó") chấm theo vân tay, mà vân tay cũ băm cả id, nên
  lắp lại y hệt một mẫu dựng sẵn — id mới toàn bộ, luật không đổi một chữ — là mất vé.
  Nay dây nối ghi bằng NHÃN ĐÁNH SỐ (`1 · 1A · 1A.1`) thay cho id, và khối không có đường
  nối tới (không bao giờ chạy) không vào vân tay. Đổi thứ tự nhánh VẪN đổi vân tay: nhánh
  xếp trên được thử trước, đó là luật chứ không phải cách bày.
- **Trạng thái: XONG CẢ BẢY PHẦN** (2026-10-15). core.md §18 (bỏ tester) · §19 (lõi) ·
  §20 (bộ máy chạy) · §21 (cầu nối QC) · §22 (trình vẽ 5 trạm) · §23 (Màn chơi theo rổ mã,
  boss cả rổ, nộp, chấm sao, cỗ máy dựng sẵn) · §24 (dọn bộ máy cũ).
  **App giờ chỉ còn MỘT thế giới: cỗ máy 5 trạm chạy trên QuantConnect.** Sơ đồ
  Entry/Manage, bộ chạy tại máy, cầu nối cũ và giao diện của chúng đã bị xoá hẳn
  (≈ 13.700 dòng). Việc còn lại là của chủ dự án: chạy thật trên tài khoản QuantConnect
  bằng khoá của mình — đến giờ mọi lượt mới chạy trên bản giả lập QC trong bài kiểm.

## D-11 · App chỉ là VỎ của QuantConnect — không mô phỏng gì tại máy nữa  (chốt 2026-10-16)

> Chủ dự án: *"ta tuyệt đối không được động vào backend nữa, ta chỉ làm cái vỏ cho
> QuantConnect thôi"* — sau khi soi ra rằng hệ thống đang nuôi một bộ mô phỏng thứ hai
> bên cạnh QC.

- **Vấn đề đã đo được:** ta tự gộp nến, tự tính 16 chỉ báo, tự đổi «% vốn» ra số lượng,
  tự huỷ lệnh hết hạn, tự tính trailing stop, tự tính lãi lỗ và boss. QC làm sẵn tất cả
  những thứ đó. Hai nơi cùng tính một thứ thì sẽ ra hai số — rõ nhất là nến: nến H1 của
  ta cắt theo giờ UTC chẵn, nến H1 của QC cho cổ phiếu Mỹ cắt theo giờ mở cửa sàn. Người
  chơi mở chart QC đối chiếu sẽ thấy khác, và ta không có gì để giải thích.
- **Quyết định:** app KHÔNG tính gì về thị trường nữa. Người chơi vẽ sơ đồ → app dịch sơ
  đồ thành một thuật toán QuantConnect → QC chạy và tính hết: nến, chỉ báo, chọn mã, số
  lượng, lệnh, rủi ro, thống kê. App giữ đúng ba việc: **vẽ · soát lỗi · dịch ra thuật
  toán**, cộng với luật chơi (màn, boss, sao).
- **Phương án đã cân nhắc:** (a) vỏ thuần ← **chọn** / (b) giữ bộ máy riêng và chấp nhận
  hai bảng điểm — người chơi sẽ không biết tin bảng nào / (c) giữ bộ máy chỉ để xem
  trước tại máy — vẫn là hai bộ luật phải đồng bộ bằng tay.
- **Cái mất, nói trước:** (1) không còn chỗ chạy thử tại máy trong vài giây — muốn biết
  cỗ máy làm gì phải gửi lên QC, vài phút một lượt và cần khoá; bài kiểm từ nay canh
  "sơ đồ này dịch ra đúng đoạn code kia" chứ không canh được kết quả giao dịch. (2) chữ
  «vì sao» phải do chính đoạn code gửi lên QC tự ghi.
- **Đã dọn (2026-10-16):** xoá `bo_may` · `chuoi_nen` · `nhat_ky_may` · `ket_qua_may` ·
  `goi_qc` · `lean/vo_may.py` · ba đồ giả (sàn giá, LEAN, máy chủ QC) · năm bài kiểm của
  chúng · `tools/chay_qc.py`. `qc_api` còn phần nói chuyện với QC; `qc_chay` còn phép
  soát đầu vào. App vẽ và soát cỗ máy được, **chưa chạy được** — mọi cửa chạy nói đúng
  một câu thay vì giả vờ chạy rồi hỏng ở đâu đó.
- **Trạng thái:** chốt, đã dọn. Đường chạy mới (dịch sơ đồ → thuật toán QC) chưa thiết
  kế — chủ dự án sẽ chỉ đường lối, và từ nay mỗi "item" trong game phải là một món CÓ
  THẬT của QuantConnect.

