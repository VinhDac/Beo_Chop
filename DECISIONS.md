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

## D-09 · Game trong cửa sổ vẽ, khuôn Opus Magnum — sơ đồ khối CHÍNH LÀ xưởng  (đề xuất 2026-10-14)

> Chủ dự án: *"lấy cảm hứng từ một game thật, upgrade giao diện cho giống game thật, làm kĩ
> flow chơi"* — và giữa chừng: *"vẽ sơ đồ kiểu này vẫn rất hay, đừng bỏ nhé"*.
> Mọi con số dưới đây chọn **để chơi được** — chủ dự án duyệt lại. Chi tiết: core.md §17.

- **Cảm hứng: Opus Magnum** (Zachtronics, 2017) — game lắp cỗ máy giả kim: câu đố chia
  chương có truyện mở/đóng; mỗi câu đố cho sẵn bộ linh kiện; chạy thử bao nhiêu lần cũng
  được; giải xong thì ba histogram (Cost · Cycles · Area) so với mọi người chơi khác —
  không lời giải nào đứng đầu cả ba, nên người chơi tự chọn đánh đổi; xong cả chương mới
  qua chương sau.
- **Quyết định (đề xuất):**
  - Game chạy **trong cửa sổ vẽ chính** (◆ Màn chơi / Ctrl+M), không còn là cửa sổ riêng.
    **Xưởng của game là trình vẽ sơ đồ khối giữ nguyên** — chỉ dải ribbon đổi thành thanh
    xưởng (khay linh kiện Mắt · Tay vào lệnh · Tay chỉnh lệnh · Núm vặn, độ gọn, ▶ nhanh,
    ▶ đầy đủ, Nộp) và bảng màu đổi sang đồng thau / giấy cũ. Cửa sổ ◆ cũ ở lại làm
    **bảng QC kỹ thuật** (File → Bảng QC kỹ thuật).
  - Luồng màn hình: màn hình chính → bản đồ chương → truyện (lần đầu vào chương) → phiếu
    đặt máy → xưởng ⇄ kết quả (ba histogram) → xem máy nghĩ (phát lại từng lượt, tô đường
    đi lên sơ đồ, nói bằng tên khối) → đấu màn ẩn (VS boss, phải bấm «Bắt đầu đấu» — mỗi
    lần nộp bị đếm) → hoàn thành (mở khoá màn sau, giác quan mới).
  - **Chương 1 «Tiệm vàng nhà Tư»** — khách Bà Tư, người dẫn đường Mèo Thợ Cả, bốn màn:
    1-1 Năm đi ngang (thấy 2021 · ẩn 2022) · 1-2 Cắt lỗ cho kịp (2018 · 2019) · 1-3 Biết
    đứng ngoài (2016 · 2017) · 1-4 Năm vàng (2023 · 2024). Năm đã thấy và năm ẩn KHÔNG BAO
    GIỜ trùng trong một chương. ▶ nhanh = quý 4 năm đã thấy. Chương 2 «Mùa sập», 3 «Bạc»:
    khoá, «sắp ra mắt».
  - **Giác quan mở dần** (như bộ linh kiện từng câu đố): 1-1 chỉ có giá đóng cửa, MA, số
    vị thế; 1-2 thêm ATR và nhóm «lệnh này» (đã khớp, SL hoà vốn, lãi bao nhiêu R); 1-3
    thêm giá mở/cao/thấp, số lệnh chờ. Vùng nén chưa mở ở chương 1. Python chặn khi chạy
    (`game.soat_giac_quan`), hộp sửa khối chỉ bày giác quan đã mở. Sáng tạo: có hết (D-07).
  - **Mở khoá:** màn sau mở khi màn trước có ★ (nộp được ít nhất chạy sạch); chương sau mở
    khi mọi màn chương trước có ★. Đi tuần tự (Opus Magnum cho chọn tự do trong chương) vì
    mỗi màn dạy một thứ màn sau cần.
  - **Ba histogram:** Lãi % (có vạch boss) · Sụt giảm % · Độ gọn. Chưa có người chơi khác
    nên **đám đông là các lần ▶ đầy đủ của chính bạn trên màn đó** — có cộng đồng thì chỉ
    đổi nguồn số.
  - **Máy gợi ý mới** (`cat_studio/may_mau.py`), không dùng Compress làm ví dụ nữa:
    «Theo MA» (5 khối, màn 1-1) và «Hai chiều» (7 khối, màn 1-2).
- **Phương án đã cân nhắc:** (a) Opus Magnum ← **chọn**: lắp cỗ máy + chạy thử thoải mái +
  ba histogram đánh đổi khớp đúng vòng chơi D-05 / (b) Human Resource Machine: lệnh mở
  dần theo màn, thử thách kích thước/tốc độ — lấy ý "giác quan mở dần" / (c) giữ cửa sổ
  Màn chơi riêng — game và sơ đồ ở hai cửa sổ thì người chơi phải đi qua lại.
- **Lý do:** cái Opus Magnum KHÔNG có mà ta có — **màn ẩn** — là thứ làm game này dạy
  điều thật (chỉnh tham số tới khi đẹp không cứu được cỗ máy trên năm nó chưa thấy).
- **Trạng thái:** đề xuất — chủ dự án duyệt: tên/truyện, năm từng màn, thứ tự giác quan,
  luật mở khoá, đám đông của histogram.

