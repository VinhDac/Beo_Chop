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

## D-12 · Xoá TOÀN BỘ bộ khối cũ — làm lại khối và cách tương tác từ đầu  (chốt 2026-10-16)

> Chủ dự án: *"xóa toàn bộ khối cũ đi, bây giờ ta sẽ làm lại khối, cách tương tác từ
> đầu"* — ngay sau D-11, và sau nhận xét *"đánh giá hiện tại là hơi bừa"*.

- **Vấn đề:** D-11 chốt app chỉ là VỎ của QuantConnect, nhưng bộ khối thì được nghĩ ra
  TRƯỚC luật đó. Nó sinh ra từ câu hỏi "người chơi muốn vẽ gì", rồi app tự tính phần
  còn lại. Mỗi khối Làm, mỗi đại lượng, mỗi ô Gom đều là một phép tính của riêng app —
  đúng cái D-11 cấm. Giữ lại bộ khối ấy thì D-11 chỉ là lời hứa: sớm muộn phải dựng lại
  một bộ máy tính toán sau lưng nó để nó chạy được.
- **Quyết định:** xoá sạch bộ khối, từ điển, mẫu dựng sẵn, trình vẽ và màn chơi. Bộ khối
  mới thiết kế lại từ đầu với MỘT luật bắt buộc: **mỗi khối phải ứng với một món CÓ THẬT
  của QuantConnect** — một API, một loại lệnh, một chỉ báo, một bước trong khung 5 phần
  của họ. Khối nào không chỉ ra được món QC tương ứng thì không được có.
- **Phương án đã cân nhắc:** (a) xoá hết, làm lại ← **chọn** / (b) giữ khối, sửa dần
  từng cái cho khớp QC — sửa dần thì lúc nào cũng còn một nửa cũ một nửa mới, và không
  ai biết đang ở nửa nào / (c) giữ khối làm "bản phác", dịch sang QC lúc chạy — tức là
  hai ngôn ngữ phải khớp nhau mãi mãi, đúng cái bẫy D-11 vừa thoát.
- **Đã xoá (2026-10-16):** `tram.py` · `may.py` · `mau_tram.py` · bốn bài kiểm của
  chúng · cả thư mục `webui/src/may/` (trình vẽ 5 trạm, 14 file) · `webui/src/qc/
  ManChoi.tsx` · `webui/src/chung/` · hai bài kiểm giao diện của chúng. Cùng với D-11 là
  ≈ 9.000 dòng rời khỏi kho trong một ngày.
- **Dọn theo, vì chúng chỉ phục vụ bộ khối cũ:** `api.py` mất hết cửa `may_*` và cả lớp
  `ApiQC`; `game.py` mất `do_gon`/`van_tay` (chúng đọc định dạng cỗ máy cũ); `luu_tru`
  mất kho chiến lược; `app.css` mất 1.360 dòng; `types.ts` còn ba kiểu.
- **Giữ lại, vì KHÔNG dính bộ khối:** `core` (đồ thị thuần: đánh số phân cấp, thứ tự ưu
  tiên nhánh, soát nối dây — nó chưa bao giờ biết khối là gì) · `luu_tru` · `game` (luật
  chơi) · `qc_api` · `khung_cua_so` · khung giao diện (thanh tiêu đề, hộp thoại, menu).
  Và `so.ts` — bài học "gõ từng phím, đừng ép `Number()` ngay" vẫn còn nguyên giá trị.
- **Một lỗi lộ ra nhờ dọn:** hộp Khoá QC gọi `qc_khoa`, mà hàm đó nằm ở `ApiQC` — bề mặt
  của cửa sổ Màn chơi. Cửa sổ chính không có nó. Bản xem thử trong trình duyệt che mất
  vì nó tự định tuyến mọi tên `qc_*` sang `ApiQC`, tức **cầu nối giả nói dối so với app
  thật**. Nay `api.py` chỉ còn MỘT bề mặt, và `tools/xem_thu.py` cũng vậy.
- **Trạng thái app sau D-12:** mở lên được, đặt được khoá QC, xem được chỗ lưu file.
  **Chưa vẽ được gì, chưa chạy được gì** — và cửa sổ nói thẳng ra điều đó thay vì bày
  một trình vẽ rỗng. 3 bài kiểm còn lại đều xanh.
- **Trạng thái quyết định:** chốt, đã dọn. Bộ khối mới và cách tương tác mới sẽ do chủ
  dự án chỉ đường lối, bắt đầu từ danh sách những gì QuantConnect thật sự cho.

## D-13 · Chép hạ tầng trình vẽ từ Jenifer_Studio  (chốt 2026-10-16)

> Chủ dự án chỉ sang `Jenifer_Studio` — một bộ tự động hoá game của chính mình — và
> nói: *"đó là những gì tôi thực sự muốn về cách tạo sơ đồ, tư duy"*, rồi
> *"copy hết những gì copy được, sau đó ta tự sửa chi tiết sau"*.

- **Vì sao tin được:** không phải tham khảo một thư viện đẹp trên mạng, mà một sơ đồ
  THẬT đã được dựng tới quy mô ấy: template `trial chaos 30` có **1.170 khối ·
  1.468 dây · 243 Nhóm ôm 2.253 hành động** trên canvas **19.367 × 16.055**. Mọi thứ
  chép về đều là lời giải cho một câu hỏi duy nhất: *làm sao không lạc trong 1.170
  khối*.
- **NGỮ PHÁP CHỈ CÓ BỐN HÌNH** (đo trên chính sơ đồ ấy):
  1. **Chuỗi** → gập thành **Nhóm** (một hộp ôm một dãy hành động).
  2. **Bảng tra vẽ ra** — một khối rẽ N nhánh, **mỗi nhánh mở đầu bằng CÙNG MỘT KIỂU
     CÂU HỎI chỉ khác tham số**, rồi gộp về một chỗ. Đo được **45/45 chỗ rẽ ≥3 nhánh
     đều đồng loại**, nhánh thoát không cổng xếp dưới cùng ở 28/45 chỗ.
  3. **Quay về** — khối cụt nhảy ngược lên, 91 cái, 37 đích, **91/91 trỏ trong cùng
     một lớp**.
  4. **Hình thoi khép kín** — mở ra bao nhiêu thì đóng lại bấy nhiêu.
- **Lối tư duy đứng sau:** **559/610 khối mở đầu nhánh là khối HỎI**. Chương trình
  không viết theo lối "làm A rồi B rồi C" mà theo lối *nhìn xem thế giới đang ở trạng
  thái nào → chạy tay xử lý của trạng thái ấy → quay về nhìn lại*. Đó là **máy trạng
  thái phản ứng**, và nó khớp đúng hình dạng của QuantConnect: mỗi nến, nhìn dữ liệu,
  quyết, đặt lệnh, chờ nến sau.
- **Hệ quả quan trọng nhất:** khối hỏi chỉ trả lời được về MỘT thứ, nên *"cái nào
  trong N cái"* không có cú pháp — nó thành **hình học**: N làn kẻ cạnh nhau.
  **Cấu trúc CHÍNH LÀ chương trình.** Giữ nguyên lối ấy, không đẻ ra một khối "rẽ theo
  giá trị" nhiều cổng có nhãn: nhãn trên cổng là thứ có thể nói dối, còn N làn thì mỗi
  làn tự nói ra nó là nhánh nào và ưu tiên nhìn thấy được trên canvas.
- **Chốt hình dạng tài liệu:** **MỘT SƠ ĐỒ PHẲNG DUY NHẤT**, không chia năm trạm. Cấu
  trúc do người chơi tự đặt bằng **hạt nhân**, không do app áp sẵn.
- **Đã chép về (8 bước, mỗi bước một commit, mỗi bước xanh rồi mới sang bước sau):**
  Nhóm · Quay về (hai cách khai đổ vào một bảng `canh_vong`) · `KHOA_CANVAS` (pos, màu,
  ghim, hạt nhân — khoá tả CÁI NÚT, bộ chạy không đọc) · một cửa soát duy nhất · ba
  tầng lưu · thẻ khối do Python dựng · dây ↻ vồng lên · **hạt nhân** · ô tìm không dấu
  + bốn lọc hỏi theo dây · menu chuột phải · phím tắt tra bảng · bảng dưới.
- **Cố ý KHÔNG chép:** bộ song ngữ (Cat chỉ tiếng Việt), chế độ (Cat chỉ một loại tài
  liệu), và mọi thứ dính game.
- **Bài học đắt nhất, đã ghi vào `tools/xem_thu.py`:** khung xem thử không vẽ thì phép
  đo nói dối. `ResizeObserver` chỉ bắn trong nhịp vẽ, mà cửa sổ bị che là trình duyệt
  bỏ nhịp ấy — đọc DOM thấy đủ khối mà KHÔNG một đường nối nào. Đã truy nhầm sang bản
  React Flow, bản React, StrictMode và CSS trước khi nhận ra không có lỗi nào cả.
- **Trạng thái:** trình vẽ chạy thật — vẽ được sơ đồ rẽ nhánh có vòng, đánh số
  `1 · 2 · 2A · 2A.1 · 2B · 2B.1 · 3 · 4`, gom hạt nhân và bấm đúp vào trong sửa.
  **Bộ khối vẫn chưa có**: khối hiện mới là `Nhóm` / `Khối lẻ` / `Quay về` trống ruột.
  Việc kế tiếp là nghĩ nội dung từng khối HỎI và LÀM, mỗi cái phải là một món có thật
  của QuantConnect.

## D-14 — Bộ khối: XÁC NHẬN và HÀNH ĐỘNG

- **Bản chất cỗ máy, theo lời chủ dự án:** *so sánh, rồi ra quyết định*. Nên bộ khối
  chỉ có hai nửa: khối **HỎI** đọc thế giới và rẽ nhánh, khối **LÀM** đụng vào thị
  trường. Hai từ điển: `cat_studio/hoi.py` (5 loại, 68 đại lượng) và
  `cat_studio/lam.py` (8 loại việc).
- **Luật gốc, và nó là một phép kiểm chạy được:** mỗi mục phải chỉ ra được MỘT thứ có
  thật của LEAN — ô `lean` là lời khai ấy; không khai được thì không được có mặt.
  `test_hoi` / `test_lam` quét cả hai từ điển và trượt nếu thiếu. Hộp thoại Hành động
  còn **bày thẳng hàm LEAN nó sẽ gọi** ra màn hình, để lời hứa D-11 kiểm được chứ
  không phải tin suông.
- **Đã bỏ vì chúng bắt app tự tính:** `tỷ trọng hiện tại` (ta chia) · `số mã đang giữ`
  (ta đếm) · `số ngày đã giữ` (ta ghi sổ) · `số nến đã chạy` (LEAN không đếm) · phép
  `cắt lên` / `cắt xuống` (so hai nến là ta nhớ nến trước). Bốn cái tên ấy bị canh để
  không quay lại.
- **Phép so chỉ có SÁU** (`> < >= <= == !=`). Mọi phép "nhìn lại quá khứ" tan vào chỉ
  báo nhờ `IndicatorExtensions` + `Delay/Maximum/Minimum` của LEAN: *"giá cao nhất 20
  nến"* là `MAX(20)`, không phải một toán tử thứ bảy do ta nghĩ ra.
- **⚠ Đường ranh ĐẶT / SỬA:** đặt lệnh và **huỷ hết** lệnh chờ của một mã thì được —
  mỗi cái là MỘT câu gọi. **Sửa một lệnh cụ thể** (`ticket.UpdateStopPrice`) thì KHÔNG
  — phải giữ ticket qua nhiều nến, tức sơ đồ sinh ra trạng thái, tức app lại có backend
  để mà gỡ lỗi. Muốn dời cắt lỗ: **huỷ hết → đặt lại**, hai khối, không nhớ gì.
- **Cố ý bỏ:** lệnh quyền chọn nhiều chân (`Combo*`, `ExerciseOption`) — cần cả một bộ
  chọn chuỗi quyền chọn.
- **Ô `tag` không phải sáng kiến của ta:** LEAN nhận nó trên mọi hàm đặt lệnh. Để trống
  thì bộ sinh mã điền số khối + điều kiện vừa khớp — đó là lời hứa D-11 "chữ *vì sao*
  do chính đoạn code tự ghi". Và nó VẮNG MẶT ở Ghi chú / Vẽ bảng / Báo tin, vì `Debug`,
  `Plot`, `Notify` không nhận tham số ấy.
- **Soát ruột khối chỉ bắt thứ hỏng LẶNG:** cổng không điều kiện (luôn khớp) · số lượng
  0 · giá 0 · tỷ trọng vượt 100% · `Quit` · đại lượng ĐÚNG/SAI đem `Plot`. Lời khuyên
  kiểu "đòn bẩy thế là cao đấy" không thuộc về đây.
- **Bài kiểm lại làm đúng việc của nó:** bắt `--font-mono` là biến CSS ma ngay lượt
  chạy đầu, và lần này bắt thêm một loại ma mới — **lớp `hien-tu-*`**. `Ribbon.tsx`
  sinh `hien-tu-1090` / `hien-tu-1250` từ D-13 mà `app.css` chưa bao giờ có dòng nào:
  hai nhóm ribbon không hề ẩn ở cửa sổ hẹp, không lỗi, không cảnh báo, build sạch.
- **Trạng thái:** bộ khối đọc/ghi xong, 7/7 bài kiểm xanh. **Bộ sinh mã chưa có** — sơ
  đồ chưa biến thành thuật toán LEAN Python. Việc kế tiếp: ô của khối Bắt đầu (nhịp
  chạy, chạy cho mã nào), rồi bộ sinh mã.

## D-15 — Khối Bắt đầu: mọi thiết lập gom vào MỘT khối

- **Cách tìm ra:** đọc **444 thuật toán Python thật** của LEAN (`Algorithm.Python/`),
  chứ không suy từ tài liệu. Phát hiện: một script có hai nửa — `initialize` nói MỘT
  LẦN (ngày nào, bao nhiêu tiền, mã nào, nhịp nào), `on_data` chạy LẠI mỗi nhịp. Sơ đồ
  ta vẽ là nửa dưới; nửa trên **không có chỗ nào trên canvas**, khối Bắt đầu trước đó
  chỉ có cái tên. Mà `set_start_date` có ở 395/444, `set_cash` 250, `add_equity` 244.
- **Chốt:** mọi thiết lập gom vào **một khối Bắt đầu, sáu ô** — mã (danh sách, mỗi
  dòng một loại tài sản) · từ ngày → đến ngày · vốn · nhịp · mốc so sánh · sàn.
- **Và nó giải luôn hai thứ tưởng phải đẻ khối mới:**
  - **Không cần khối "Với mỗi mã".** Ô *nhịp* + ô *mã* đã khai trọn vòng lặp rồi:
    *"mỗi nến, cho mỗi mã trong danh sách"*. Cả sơ đồ bên dưới là ruột vòng. Vòng vẫn
    HIỆN RA theo luật D-13, chỉ là hiện ở đúng chỗ nó sinh ra.
  - **Cái hack "chỉ một lần mỗi ngày" biến mất.** Hai chiến lược kinh điển của QC
    (`MACDTrendAlgorithm`, `MovingAverageCrossAlgorithm`) đều phải tự nhớ *hôm qua là
    ngày nào* — đó là TRẠNG THÁI, đúng thứ ta cấm. Họ viết vậy vì không có cách khai
    nhịp. Nên ô *nhịp* không phải một ô cho tiện: nó xoá hẳn một loại hack.
- **Nhịp gộp hai thứ của LEAN làm một:** độ phân giải dữ liệu và lúc nào sơ đồ chạy là
  hai câu trong script, nhưng với người chơi là MỘT câu hỏi — *bao lâu tôi xem một
  lần*. Năm nhịp theo nến chạy trong `on_data`; ba nhịp hẹn giờ qua `schedule.on` và
  đăng ký dữ liệu PHÚT, vì dữ liệu ngày không có giờ nào trong đó mà hẹn.
- **Làm nóng (`set_warm_up`) KHÔNG thành ô** — bộ sinh mã lấy chu kỳ dài nhất trong
  các chỉ báo đã vẽ. Đếm trên sơ đồ của chính ta, không tính trên dữ liệu thị trường.
- **Cố ý CHƯA có:** `add_universe` (chọn mã động — 97/444 dùng) và cửa vào thứ hai
  (*mỗi nến xem tín hiệu + cuối tháng cân danh mục*). Cái sau đụng vào hệ đánh số, vì
  nó đang neo vào đúng MỘT khối Bắt đầu.
- **Một khả năng đã xác minh, chưa làm:** sáu phép so hiện không viết nổi
  `fast > slow * 1.00015` — mà **`IndicatorExtensions` của LEAN có sẵn**
  `Plus/Minus/Times/Over` với vế phải là một số hoặc một chỉ báo khác, kết quả là
  `CompositeIndicator` do LEAN tự tính. Nên cho phép ghép đại lượng **không phá luật
  "không đẻ backend"**.
- **Hai chỗ hỏng LẶNG bắt được:** `chuan_hoa_khoi` dựng lại khối Bắt đầu chỉ giữ cái
  tên (sáu ô bay sạch mỗi lần lưu); và mặc định list/dict dùng chung khiến hai khối
  Bắt đầu xài chung một danh sách mã.
- **Tiện thể:** dữ liệu miễn phí đi kèm LEAN **có XAUUSD giá ngày 2006–2019, 3.948
  ngày**. Backtest vàng được ngay, không trả xu nào — nên khối Bắt đầu mặc định chạy
  trên XAUUSD.
- **Trạng thái:** cả hai nửa của thuật toán đã khai được trên canvas, 8/8 bài kiểm
  xanh. **Bộ sinh mã vẫn chưa có.**

## D-16 — Bộ sinh mã: sơ đồ thành thuật toán LEAN chạy được

- **Luật gốc:** bộ sinh mã **không tự nghĩ ra một câu LEAN nào**. Mọi câu nó viết lấy
  từ ô `lean` của ba từ điển, chỉ thay chỗ trống bằng giá trị.
- **Hệ quả: ô `lean` phải đổi từ lời khai sang BIỂU THỨC PYTHON CHẠY ĐƯỢC**
  (`Securities[sym].Price` → `self.securities[sym].price`). Vì nếu `lean` chỉ là lời
  khai thì phải có một bộ chuyển đổi ở giữa, mà bộ đó sai thì sai ÂM THẦM. Nay lời
  khai và đoạn code là MỘT — thêm một chỉ báo là thêm một dòng vào từ điển.
  Bản LEAN này cũng đã bỏ PascalCase: 392/444 thuật toán Python dùng snake_case.
- **Đổi xong lộ ra một mục BỊA:** `Delay(n)` khai là chỉ báo, mà
  `QCAlgorithm.Indicators.cs` không có chữ ký nào. Nó là một lớp dựng tay rồi
  `register_indicator` — nay có thêm ô `lean_dk` cho đúng.
- **Ba thứ bộ sinh mã tự lo**, cả ba đều đếm trên sơ đồ của chính ta: nâng chỉ báo lên
  `initialize` (hai khối cùng RSI(14) dùng chung một cái) · `set_warm_up` · vòng lặp
  nhiều mã.
- **Mã sinh ra cố ý DỄ ĐỌC**: không máy trạng thái, không bảng nhảy. Khối Hỏi thành
  `if`, nhánh thành `if/elif`, khối Làm thành đúng một câu gọi. Người đọc file phải
  nhận ra sơ đồ của mình trong đó — đó là cả lý do dự án tồn tại.
- **Chưa sinh được thì BÁO, không đoán:** vòng lặp (trong một nến dữ liệu không đổi,
  chạy lại một đoạn chỉ cho đúng kết quả cũ) và mã chưa khai ở khối Bắt đầu (tự
  `add_*` là tự quyết hộ một đăng ký dữ liệu).
- **✅ ĐÃ CHẠY THẬT:** sơ đồ vàng + RSI(14) trên XAUUSD giá ngày 2015–2018 (dữ liệu
  miễn phí) → **15 lệnh, +16,376%, thắng 71%, sụt sâu nhất 13,2%**.
- **⚠⚠ BẪY LỚN NHẤT, và nó lặng hoàn toàn:** lần chạy đầu ra *111 lệnh, lãi 0%*. Mở
  `order-events.json` mới thấy cả 111 lệnh đều `invalid` vì
  *"OandaBrokerageModel does not support MarketOnClose"*. Gốc rễ: nhịp **mỗi nến
  NGÀY** thì LEAN không có giá trong ngày để khớp nên nó tự đổi lệnh thị trường thành
  **MarketOnClose**, mà Oanda/Binance/Coinbase không nhận loại ấy. Backtest vẫn chạy
  hết, báo đủ thống kê, không một dòng lỗi. Nay `soat` cảnh báo đúng tổ hợp đó.
- **Và một cảnh báo SAI đã sống từ D-14:** `validate_flow_graph` đọc khoá `conditions`
  đã chết từ D-12, nên MỌI cặp cổng đều bị báo "trùng điều kiện" — kể cả `RSI < 30`
  với `RSI > 70`. Cảnh báo sai thì người ta học cách bỏ qua nó.
- **Trạng thái:** vẽ → sinh → chạy đã thông, 9/9 bài kiểm xanh. Chưa có: chạy LEAN
  *từ trong app* (hiện phải chạy tay), vòng lặp, chọn mã động, lớp game.

## D-17 — Chạy LEAN từ trong app, và màn Kết quả

- **Đoạn cuối của vòng** *vẽ → sinh → chạy → đọc → sửa*. Cụm nút chính
  (`Sinh mã · Chạy · Tối ưu · Chạy thật · Kết quả`) **ghim sát mép phải, tô sáng**.
  Hai nút chưa có thì bày ra mờ kèm lý do, không giấu — giấu thì không ai biết còn
  thiếu gì.
- **⚠ Cụm ấy phải GHIM, không được đẩy bằng `margin-left: auto`:** ribbon có bảy
  nhóm nên luôn dài hơn cửa sổ, mà đẩy chỉ ăn khi còn chỗ trống — cụm chính trôi hẳn
  ra ngoài màn. Nay ribbon chia hai vùng: trái tự cuộn, phải đứng im.
- **Ba cái bẫy của bộ chạy, cả ba đã cắn thật:** đừng tin mã thoát (pythonnet ném
  lỗi GIL lúc tắt, SAU khi kết quả ghi xong) · phải gột sạch biến môi trường của venv
  (venv không có pandas, LEAN sẽ chết mà không nhắc gì tới venv) · `config.json` của
  LEAN có chú thích `//` và dấu phẩy thừa, mà gột phải biết đang ở trong chuỗi hay
  không.
- **Chỗ đặt LEAN là cấu hình người dùng phải điền** — không đoán hộ.
- **Màn Kết quả dựng theo 11 ảnh chụp chủ dự án đưa** (`tai_lieu/backtest/`). **Mã
  giao diện của QuantConnect thì KHÔNG chép** — đó là mã nguồn của họ, và chép cũng
  vô dụng: trang ấy là ứng dụng React, HTML lấy về chỉ là hộp rỗng. Bố cục và từng
  khả năng thì dựng lại bằng mã của ta.
- **Và không phải tính gì cả:** 8 ô số là `runtimeStatistics`, 8 biểu đồ là `charts`
  (kèm `seriesType` nói rõ nến/cột/treemap), thống kê trượt là `rollingWindow`, thông
  tin máy là `serverStatistics`. App chỉ bày ra.
- **Cố ý KHÔNG dựng, nói rõ chứ không giả vờ quên:** Research Guide · Share Results ·
  Report — cả ba là dịch vụ đám mây và tài liệu có thương hiệu của QuantConnect.
- **⚠ Một chỗ cố ý làm KHÁC bản web:** bảng Strategy Equity có vốn tính bằng ĐÔ và
  lợi suất tính bằng PHẦN TRĂM. Hai trục dọc trên một khung là nói dối bằng tỉ lệ —
  hai đường cắt nhau ở chỗ do người vẽ chọn thang. Nên mỗi đơn vị một DẢI RIÊNG xếp
  chồng, chung trục ngang. Nhìn gần như y hệt, mà không còn chỗ cho phép so sánh sai.
- **⚠ Bớt điểm phải GỘP, không nhảy cách:** nhảy cách làm mất đỉnh và đáy — một cú
  sụt gọn trong vài nến biến mất khỏi biểu đồ mà người xem không biết.
- **⚠ Để trống «Mốc so sánh» KHÔNG phải là không có mốc:**
  `DefaultBrokerageModel.GetBenchmark` trả về SPY, tức cỗ máy vàng bị đem so với cổ
  phiếu Mỹ mà không một dòng nào nói ra. Nay gợi ý nói thẳng và biểu đồ ghi tên thật.
- **Trạng thái:** vẽ → sinh → chạy → đọc đã thông trọn vòng, 11/11 bài kiểm xanh.
  Chưa có: Tối ưu, Chạy thật, vòng lặp trong mã sinh ra, lớp game.

## D-17 · RỔ ĐỘNG — khe thứ năm, và nó là một Ô chứ không phải một khối

Dây chuyền LEAN có năm khe; D-16 mở bốn (tín hiệu · chia vốn · phòng rủi ro · đặt
lệnh). Khe còn lại là `set_universe_selection` — *chạy trên mã nào*, mà LEAN quyết
lại mỗi ngày.

- **MỘT Ô, HAI KIỂU — không phải khối mới.** `set_universe_selection` gọi MỘT LẦN
  trong `initialize`, đúng cùng luật đã chốt ở D-16: *xảy ra mỗi nhịp thì thành khối,
  đặt một lần thì thành ô*. Nên nó là kiểu thứ hai của chính ô «Chạy trên mã nào»:
  ô ấy nhận một LIST (mã gõ sẵn) hoặc một DICT (một rổ). Phân biệt bằng HÌNH DẠNG,
  đúng lối vế phải của điều kiện (`{so}` hay `{ma_dl}`) — nhờ vậy file cũ mở ra vẫn
  chạy, không phải di cư schema.
- **Chín rổ, chín lớp CÓ THẬT** trong `Algorithm.Framework/Selection/`.
  **⚠ Cố ý KHÔNG có `ManualUniverseSelectionModel`** dù nó cũng có thật: nó nhận một
  danh sách mã gõ sẵn, tức đúng câu mà kiểu LIST đã nói. Bày cả hai là bày hai cách
  nói một thứ rồi để người chơi đoán cách nào mới đúng.
- **Hàm lọc «lấy mấy mã» cũng khai trong từ điển** (`bat_dau.LOC_TRONG_SO`), không để
  bộ sinh mã tự nghĩ ra: một hàm lọc cũng là mã LEAN, và lời hứa D-11 không có ngoại
  lệ. Ba dòng ấy chép từ ví dụ của chính LEAN; `weight` là trường có thật của
  `ETFConstituentData`, và nó NULLABLE nên phải gạn trước khi xếp.
- **⚠ BA chỗ nhánh này khác hẳn, cả ba đã ÉP TÁI HIỆN bằng backtest thật** (SPY
  12/2020, rổ top 8 — 14 lệnh khớp hết):
  1. `universe_settings.resolution` phải đứng TRƯỚC `set_universe_selection`: model
     chụp lấy settings ngay lúc dựng. Đặt sau thì rổ chạy bằng phút trong khi sơ đồ
     nói ngày, và `sma(sym, 200)` thành 200 PHÚT.
  2. Chỉ báo khai ở `on_securities_changed`, không ở `initialize` — lúc ấy rổ còn
     rỗng. Và hàm ấy phải ghi `self._cb[sym] = {}` **kể cả khi sơ đồ không có chỉ báo
     nào**: ĐÃ ĐO — còn dòng ấy 15 lệnh, bỏ nó **0 lệnh**, backtest sạch cả hai lần.
  3. `set_warm_up` vô dụng với chỉ báo sinh giữa đường -> `warm_up_indicator`. Nhưng
     nó chỉ nạp được những gì CÓ trên đĩa, nên vẫn phải chặn `is_ready`: ĐÃ ĐO —
     `RSI(20000) < 60` còn chặn thì 0 lệnh, bỏ chặn thì **17 lệnh khớp hết trên một
     chỉ báo chưa bao giờ chín**, đọc ra ~53, một con số trông bình thường.
- **Nhịp hẹn giờ phải có câu LEAN THỨ HAI.** `date_rules.every_day(ma)` cần một mã,
  mà `self._ma[0]` trên một rổ là `IndexError` ở dòng đầu `initialize`. LEAN có sẵn
  mấy hàm KHÔNG MÃ (`after_market_open(so_phut)` lấy giờ mở sớm nhất trong các mã
  đang có, mặc định SPY), nên mỗi nhịp khai thêm một câu cho nhánh rổ.
