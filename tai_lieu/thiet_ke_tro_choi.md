# Cat Studio — BẢN THIẾT KẾ TRÒ CHƠI

> Viết ngày 19/10/2026. Đây là bản thiết kế, **chưa một dòng mã nào được viết theo nó**.
> Đọc, cắt, sửa, rồi mới dựng.
>
> Chốt trước khi đọc: trò chơi phải **dạy hết mọi thứ trong app**. Không phải một bản
> demo, không phải vài màn hướng dẫn rồi thả.

---

## 0. KIỂM KÊ THẬT — và con số «68» đã cũ

Tôi đếm thẳng trong từ điển của app, không đếm theo trí nhớ:

| Thứ | Số thật | Chia nhóm |
|---|---|---|
| **Đại lượng** | **164** | Chỉ báo 90 · Chỉ báo nhiều đường 16 · Vị thế 12 · Trí nhớ 12 · Giá 8 · Tài khoản 8 · Định giá 7 · Thời gian 6 · Trạng thái mã 5 |
| Họ câu hỏi | 6 | thị trường · vị thế · tài khoản · lịch · trí nhớ · doanh nghiệp |
| Loại hành động | 10 | tỷ trọng · lệnh thị trường · đóng · lệnh chờ · huỷ lệnh chờ · ghi chú · vẽ bảng · báo tin · phát tín hiệu · ghi nhớ |
| Ô khối Bắt đầu | 6 | mã · khoảng ngày · vốn · nhịp · nhánh chạy · chạy cho ai |
| Ô Cỗ máy | 11 | đệm tiền mặt · mốc so sánh · sàn · trí nhớ · phí · trượt giá · chuẩn hoá giá · phát tín hiệu · chia vốn · phòng rủi ro · đặt lệnh |
| Rổ | 11 | etf · qc500 · ema_cheo · gtgd · etf_thanh_khoan · kim_loại · năng lượng · công nghệ · trái phiếu · biến động · ngành S&P500 |
| Optimize | 2 cách tìm · 27 chỉ tiêu · 6 phép so | |
| Ngữ pháp vẽ | 4 | nhánh song song · Quay về (vòng lặp) · Nhóm/Hạt nhân · trí nhớ qua nến |

### ⚠ Hệ quả quan trọng nhất của bản kiểm kê này

**Không thể dạy 164 món bằng 164 màn.** 90 chỉ báo không phải 90 bài học — nó là **một**
ý tưởng ("lấy một con số máy tính tính hộ từ giá") lặp lại 90 lần. Dạy từng cái là 90 màn
giống hệt nhau, và người chơi bỏ ở màn thứ sáu.

Nên luật của cả bản thiết kế này:

> **Màn dạy NHÓM và NGỮ PHÁP. Kho dạy từng món.**
>
> 9 nhóm × "cách dùng nhóm này" = chừng 25 màn. Còn 164 món nằm trong **KHO** — một màn
> hình tra cứu, mở dần theo tiến trình, mỗi món một thẻ có hình, có câu LEAN thật, có nút
> «thả vào xưởng». Màn dạy người chơi **cách mở kho**, không bắt họ thuộc kho.

Đó cũng là lý do «dạy hết» vẫn làm được mà không thành 164 màn.

---

## 1. THẾ GIỚI

### XƯỞNG CỦA MÈO

Một con mèo kỹ sư, trong một cái xưởng tối, lắp **máy in tiền** từ linh kiện.

Tên app đã là Cat Studio. Giữ con mèo là giữ thứ nhớ được — thiên hạ có cả nghìn cái
terminal neon xanh lè, không ai có con mèo lắp máy. **Marketing được là thứ người ta kể
lại được.**

Nhưng «mèo» ở đây **không phải mèo dễ thương**. Nó là:

- **Thợ máy, không phải linh vật.** Nó bẩn dầu máy. Nó có bàn làm việc, có đồ nghề.
- **Giọng khô, có chính kiến.** Nó không cổ vũ "giỏi lắm!". Nó nói *"Màn ẩn vả cho một
  cái. Bạn không làm chiến thuật — bạn vẽ lại quá khứ."*
- **Nó đứng về phía sự thật,** không về phía người chơi. Đó là cả nhân vật.

### Ngôn ngữ hình

Sơ đồ **là cái máy**, không phải cái lưu đồ.

- Khối = **mô-đun** có vỏ, có ốc, có đèn trạng thái.
- Dây = **dây dẫn**, và nó **có dòng chảy** khi máy chạy.
- Cổng Hỏi = **van**. Qua được thì mở, không qua thì đóng — thấy bằng mắt.
- Hành động = **cơ cấu chấp hành**. Ra lệnh thì nó **nảy** một cái.
- Tiền = **đầu ra của máy**, chảy vào một cái đồng hồ.

### Màu

Giữ nền tối và cam hệ thống đang có (`#202020` / `#ffa657`) — nó đã đúng. Thêm:

- **Xanh dòng điện** cho dây đang có dòng chảy.
- **Đỏ** chỉ dùng cho **lỗ** và **lệnh bị từ chối**. Không dùng cho gì khác. Đỏ phải
  hiếm thì nó mới còn nghĩa.
- **Vàng** cho sao.

---

## 2. BỘ MÀN HÌNH

> Đây là câu trả lời cho *"đừng tự nhồi thêm frontend vào Home canvas"*.

Hôm nay app có **một** màn hình. Canvas cõng: ribbon, bảng dưới, thanh trạng thái, thẻ Cỗ
máy, **8 hộp thoại**, trong **1.987 dòng**. Mỗi tính năng mới lại treo thêm một thứ lên
nó. Đúng cái bệnh "nhồi ô vào khối Bắt đầu" mà ta vừa chữa ở cấp khối — nay nó lặp lại ở
cấp màn hình.

Trò chơi có **8 màn hình**, mỗi màn một việc:

| # | Màn hình | Một việc duy nhất của nó |
|---|---|---|
| 1 | **MỞ MÁY** | Con mèo, cái máy đang chạy, ba nút: Chơi tiếp · Hành trình · Sáng tạo |
| 2 | **HÀNH TRÌNH** | Bản đồ các hồi và màn. Sao, khoá, đường đi. Chọn màn. |
| 3 | **NHẬN VIỆC** | Mèo giao việc: thị trường này, boss này, **màn này mở thêm cái gì** |
| 4 | **XƯỞNG** | **Vẽ.** Chỉ có thế. (Chính là canvas hôm nay, đã lột sạch) |
| 5 | **KHO** | Tra 164 đại lượng · 10 hành động · 11 rổ. Mở dần. |
| 6 | **CHẠY MÁY** | Toàn màn hình. Máy chạy. **Đây là cảnh để quay video.** |
| 7 | **CHẤM** | Sao, so với boss, độ gọn — và **mở màn ẩn ra** |
| 8 | **SÁNG TẠO** | Xưởng mở khoá hết, không chấm, giữ nguyên lối cửa sổ chuyên nghiệp |

**Canvas thôi làm Home.** Nó thành màn hình số 4 — một phòng trong xưởng, không phải cả
cái xưởng. Ribbon, bảng dưới, 8 hộp thoại: mỗi thứ về đúng màn hình của nó.

### ⚠ Sáng tạo giữ nguyên lối cũ, có chủ ý

Chế độ Sáng tạo **không** bị game hoá. Nó giữ ribbon, giữ cửa sổ Kết quả riêng, giữ
Optimize, giữ chuyện mở bốn cửa sổ xếp cạnh nhau để so. Vì ở đó người dùng **đang làm
việc thật**, mà một công cụ làm việc thì cần nhiều cửa sổ.

Hai chế độ dùng **chung một xưởng**, khác nhau ở chỗ: Chiến dịch khoá bớt đồ và có chấm;
Sáng tạo mở hết và không chấm.

---

## 3. HÀNH TRÌNH — 25 màn, 9 hồi

Mỗi hồi mở một **nhóm**. Mỗi màn dạy đúng **một** ý mới, và ý ấy là thứ **giải được màn
đó** — không phải thứ đọc cho biết.

### MÀN 0 · «Bạn chính là boss»
Lắp máy hai khối: Bắt đầu → Đặt tỷ trọng 100%. Chạy. Nó **chính là** Mua-rồi-giữ.
*Người chơi tự tay dựng con boss mà cả trò chơi phải đánh bại.* Không màn nào dạy "boss
là gì" tốt hơn thế.
> Mở: khối Bắt đầu (mã · khoảng · vốn) · Đặt tỷ trọng · nút Chạy

### HỒI 1 · HỎI GIÁ — *"Máy phải biết nhìn"*
| Màn | Dạy | Mở |
|---|---|---|
| 1 | Cổng Hỏi đầu tiên — chỉ mua khi giá trên ngưỡng | Hỏi thị trường · nhóm **Giá** (8) |
| 2 | Hai nhánh: vào và ra | Đóng · nhánh rẽ |
| 3 | Mã có giao dịch được không | nhóm **Trạng thái mã** (5) |

### HỒI 2 · CHỈ BÁO — *"Đừng tự tính, bảo máy tính"*  ← hồi lớn nhất
| Màn | Dạy | Mở |
|---|---|---|
| 4 | Chỉ báo đầu tiên (RSI) + tham số | nhóm **Chỉ báo** (90) + **KHO** |
| 5 | Chỉ báo nhiều đường — chọn đường nào (Bollinger, MACD) | nhóm **nhiều đường** (16) |
| 6 | Ghép hai điều kiện: và / hoặc | phép ghép |
| 7 | **Tối ưu lần đầu** — ghim một núm, quét 20 giá trị | Optimize · 27 chỉ tiêu |
| 8 | **MÀN GÃY** — màn 7 ăn 2 sao, màn ẩn vả rụng xuống 1 | *(không mở gì — đây là bài học)* |

> **Màn 8 là trái tim của cả trò chơi.** Người chơi vừa học tối ưu xong, vừa thấy nó
> sướng thế nào, thì bị cho thấy đúng cái giá của nó. Mèo nói: *"Bạn không làm chiến
> thuật. Bạn vẽ lại quá khứ. Đồ thị khớp đẹp thế kia là dấu hiệu xấu, không phải dấu hiệu
> tốt."* Sau màn này người chơi mới hiểu **vì sao** có màn ẩn.

### HỒI 3 · VỊ THẾ & TÀI KHOẢN — *"Máy phải biết nó đang cầm gì"*
| Màn | Dạy | Mở |
|---|---|---|
| 9 | Đang giữ rồi thì đừng mua nữa | nhóm **Vị thế** (12) |
| 10 | Hết tiền thì đừng đặt lệnh | nhóm **Tài khoản** (8) |
| 11 | Lệnh chờ + huỷ lệnh chờ | Lệnh chờ · Huỷ lệnh chờ · Lệnh thị trường |

### HỒI 4 · TRÍ NHỚ — *"Máy phải nhớ được qua đêm"*
| Màn | Dạy | Mở |
|---|---|---|
| 12 | Ghi nhớ một quyết định cho nhịp sau | Ghi nhớ · nhóm **Trí nhớ** (12) · ô Cỗ máy «nhớ gì» |
| 13 | Vòng lặp — khối Quay về | Quay về · số vòng |

### HỒI 5 · THỜI GIAN — *"Lúc nào làm, lúc nào đứng im"*
| Màn | Dạy | Mở |
|---|---|---|
| 14 | Chỉ cân lại đầu tháng · tránh phiên mở cửa | nhóm **Thời gian** (6) · nhịp · lệnh mở cửa |

### HỒI 6 · NHIỀU MÃ — *"Một cái máy, nhiều cái cần câu"*
| Màn | Dạy | Mở |
|---|---|---|
| 15 | Hai mã cùng chạy | ô «chạy cho ai» |
| 16 | Rổ có sẵn | rổ etf · kim loại · năng lượng · công nghệ · trái phiếu · biến động |
| 17 | Rổ **tự lọc** theo thanh khoản / cắt EMA | rổ gtgd · ema_cheo · etf_thanh_khoan |

### HỒI 7 · DOANH NGHIỆP — *"Nhìn vào sổ sách, không chỉ nhìn giá"*
| Màn | Dạy | Mở |
|---|---|---|
| 18 | P/E, vốn hoá | Hỏi doanh nghiệp · nhóm **Định giá** (7) |
| 19 | Rổ 500 công ty, lọc theo ngành | rổ qc500 · ngành S&P500 |

> ⚠ **Rủi ro đã biết:** dữ liệu `fine` của QuantConnect là hàng trả tiền. Với dữ liệu
> miễn phí, `has_fundamental_data` trả False cho cả 7.111 mã — đã kiểm bằng một lượt LEAN
> thật. Hồi 7 phải thiết kế quanh giới hạn ấy, hoặc nói thẳng với người chơi.

### HỒI 8 · CỖ MÁY — *"Cái máy chạy trên cái gì"*
| Màn | Dạy | Mở |
|---|---|---|
| 20 | **Phí ăn hết lãi** — chạy lại đúng máy cũ, bật phí thật | Sàn · phí · trượt giá |
| 21 | Giữ tiền mặt, phòng rủi ro | đệm tiền mặt · phòng rủi ro · mốc so sánh |
| 22 | Phát tín hiệu — để LEAN tự chia vốn | Phát tín hiệu · chia vốn · đặt lệnh |

> **Màn 20 là màn đắt thứ hai sau màn 8.** Người chơi chạy lại đúng cỗ máy vừa ăn 3 sao,
> chỉ bật phí sàn lên — và nó lỗ. Không lời giải thích nào bằng.

### HỒI 9 · HỢP XƯỞNG — *"Nhiều máy trong một máy"*
| Màn | Dạy | Mở |
|---|---|---|
| 23 | Hai chiến thuật con chạy song song, trộn tỷ trọng | nhánh song song |
| 24 | Gom cả cụm thành một Nhóm | Nhóm · Hạt nhân |
| 25 | **BOSS CUỐI** — thị trường xấu, boss là một máy chứ không phải mua-giữ | *(mở Sáng tạo đầy đủ)* |

**Tổng: 26 màn, phủ hết 164 đại lượng (qua 9 nhóm), 10 hành động, 17 ô, 11 rổ, Optimize
và cả 4 thứ ngữ pháp vẽ.**

> 11 chiến thuật ví dụ đang có (`vd1`–`vd11`) là **lời giải mẫu** của mấy hồi cuối — đừng
> vứt, chúng là bằng chứng mấy màn ấy giải được.

---

## 4. LUẬT CHƠI

Chép nguyên từ `game.py` ở nhánh `main` — nó đã đúng:

- **Màn ẩn.** Mỗi màn có hai khoảng ngày. Khoảng **đã thấy** chạy thoải mái. Khoảng **ẩn**
  app giữ riêng, ngày tháng không bao giờ ra tới giao diện.
- **Boss** = Mua-rồi-giữ (mua nến đầu, giữ tới nến cuối).
- **Ba sao:** ⭐ chạy trọn + ít nhất một lệnh đóng · ⭐⭐ lãi hơn boss trên khoảng đã thấy
  · ⭐⭐⭐ **trên khoảng ẩn cũng hơn boss**.
- **Nộp** đòi một lượt chạy trọn của **đúng** cỗ máy ấy — so bằng vân tay.

### Thêm một thứ mới: HUY CHƯƠNG GỌN

`game.py` có đo **độ gọn** (số khối + số tham số) nhưng chỉ ghi lại, không chấm. Trong trò
chơi nó phải **có giá**:

> Mỗi màn có một **ngưỡng gọn**. Ăn 3 sao mà vẫn dưới ngưỡng thì được thêm **huy chương
> gọn**. Máy càng ít khối, càng ít núm, càng khó bị quá khớp — nên huy chương gọn và màn
> ẩn dạy **cùng một bài học** từ hai phía.

---

## 5. CẢM GIÁC — MÀN «CHẠY MÁY»

> Đây là màn hình bán cả sản phẩm. Nếu chỉ dựng được một màn hình cho tử tế, dựng màn này.

Hôm nay bấm Backtest xong chỉ có một thanh tiến độ và mấy con số. Phải thành:

1. **Toàn màn hình.** Sơ đồ ở giữa, phóng to. Không ribbon, không bảng.
2. **Dòng điện chạy trong dây.** Mỗi nhịp, dòng sáng chạy từ Bắt đầu theo đúng đường mà
   lượt ấy đi.
3. **Van mở / van đóng.** Tới cổng Hỏi: khớp thì van mở, dòng đi tiếp. Không khớp thì van
   đóng đánh *cạch*, dòng dừng ở đó. **Thấy được vì sao nó không vào lệnh** — không cần
   log, không cần bảng.
4. **Lệnh nổ.** Khối hành động nảy một cái, một hạt sáng bắn ra, đồng hồ tiền giật.
5. **Đường vốn mọc** ở mép dưới, theo thời gian thật của lượt chạy.
6. **Tua nhanh.** ×1 ×8 ×64 và «nhảy tới cuối». Backtest 6 năm không ai ngồi xem hết —
   nhưng xem 30 giây đầu thì ai cũng muốn.
7. **Dừng lại được** ở một nến để soi.

Dữ liệu để làm chuyện này **đã có sẵn**: mỗi lệnh LEAN trả về đã mang nhãn số khối và
chuỗi điều kiện đã khớp. Thiếu đúng một thứ — vệt của những nến **không** vào lệnh (xem
§8, rủi ro mở).

---

## 5b. NGÔN NGỮ MÀU — chép TradingView, không tự nghĩ

Chốt 20/10/2026, sau khi soi thẳng bảng biến của `tradingview.com` ở nền tối.

**Ba điều học được, và cả ba đều là chỗ bản cũ hỏng:**

1. **NỀN PHẢI SÂU.** Cũ: nền `#202020`, thẻ `#2b2b2b` — cách nhau 11 nấc, nên không gì
   nổi lên được và cả app phẳng lì. Họ đi `#0f0f0f` → `#1f1f1f` → `#2e2e2e`: bước 16
   nấc trên một nền sâu hơn hẳn, nên mỗi lớp tự tách ra mà **không cần một cái viền
   nào**. Nay: `--bg #0e0e0e` (trang) → `--chrome #1a1a1a` (khung app) → `--surface
   #1f1f1f` (đồ vật) → `--raised #2b2b2b`.
2. **MÀU THƯƠNG HIỆU CHỈ DÀNH CHO THỨ ĐÁNG BẤM.** Trước đây cam rải khắp nơi — chín câu
   phụ in nghiêng màu cam trên bản đồ hành trình, không cái nào bấm được. Nay cam chỉ
   còn ở **một** chỗ mỗi màn hình: nút chính, và màn người chơi đang đứng.
3. **MÀU TÍN HIỆU LÀ MỘT VAI RIÊNG,** không trộn với trang trí: xanh `#22ab94` / đỏ
   `#f23645` lấy thẳng của họ (đã chọn cho đúng nền tối này). Vàng `--warn` đẩy hẳn
   sang `#fbc02d` để thôi va vào cam.

**Và chữ trên thẻ khối tô THEO NGHĨA.** Một dòng khối là một câu đặc chữ — «RSI(14) <
30», «SPY · CFD», «Đặt tỷ trọng 100%». In cả câu một màu thì canvas thành bức tường
xám. Nay bốn vai, chép đúng cách mọi bộ tô chữ lập trình:

| vai | màu | ví dụ |
|---|---|---|
| tên đại lượng / chỉ báo | lam `--lam` | **RSI**(14) |
| con số, ngày, tiền | vàng `--warn` | RSI(**14**) < **30** |
| mã chứng khoán | trắng đậm | **SPY** · CFD |
| phép so | mờ `--dim` | RSI(14) **<** 30 |
| núm đã ghim | chip cam (có sẵn) | **chu_ky**=14 |

> ⚠ **PYTHON CẮT, GIAO DIỆN CHỈ TÔ.** Chữ nào mang vai nào do `core._net` nói ra, gài
> vào năm hàm dựng atom (`_so_gon`, `_tien`, `_ngay_vn`, `_so_the`, `_ve_dieu_kien`) —
> không gài vào từng câu, vì câu thì có hàng chục mà atom chỉ có năm. Để giao diện tự
> đọc câu mà đoán là dựng **bản thứ hai** của một bộ đọc Python vừa dùng để ghép ra
> chính câu ấy; nó sẽ tô «14» nằm trong «2014-06-09», và không bao giờ nhận ra «Trí
> nhớ: đang chờ mua lại» là cái tên người dùng tự gõ. Cùng một lời đã viết cho `num`.

---

## 6. ÂM THANH

Hiện tại: **không một file âm thanh nào trong cả dự án.** Đây là thứ phải dựng từ con số
không, và là thứ nâng cảm giác nhiều nhất trên mỗi giờ công bỏ ra.

Cần đúng chừng này, không hơn:

| Nhóm | Âm |
|---|---|
| Xưởng | thả khối · nối dây (kịch một cái) · ngắt dây · bấm sai |
| Máy chạy | tiếng máy nền chạy đều · van mở · van đóng (*cạch*) · lệnh nổ · tiền vào |
| Chấm | sao rơi xuống (3 nấc cao dần) · thắng boss · **màn ẩn vả** (một âm thật phũ) |
| Nhạc | mở máy · xưởng (êm, lặp được) · chạy máy (nhịp, dồn theo tốc độ tua) |

Mèo **không có giọng nói**. Nó kêu một tiếng ngắn, còn lại là chữ. Rẻ hơn, và không bao
giờ lỗi thời.

---

## 7. THỨ PHẢI DỰNG MỚI — nói thẳng

| Thứ | Có chưa | Ghi chú |
|---|---|---|
| Bộ 8 màn hình + chuyển cảnh | **chưa** | Gốc của cả việc. Canvas phải tách khỏi Home trước. |
| Hệ mở khoá | **chưa** | Từ điển phải biết "món này mở ở màn nào". Đụng `hoi.py` · `lam.py` · `bat_dau.py`. |
| Màn hình KHO | **chưa** | Chỗ "dạy hết" sống lâu dài. 164 thẻ. |
| Chạy máy có hình | **chưa** | Màn hình bán hàng. |
| Luật chơi, sổ điểm | **có ở `main`** | Chép về, thêm huy chương gọn. |
| 26 màn (nội dung) | **chưa** | Mỗi màn cần: mã, hai khoảng ngày, boss, lời dặn, ngưỡng gọn, lời giải mẫu. |
| Con mèo (hình + giọng văn) | **chưa** | Nay là đúng một `favicon.ico`. |
| Âm thanh | **chưa** | 0 file. |
| Dạy chơi màn 0 | **chưa** | |
| Khoe điểm / chia sẻ | **chưa** | Cho marketing: ảnh kết quả có sao, chép được một đường link. |
| Bộ máy chạy thật | **có** | LEAN. Phần khó nhất, đã xong. |
| Ngôn ngữ vẽ | **có** | 164 đại lượng, sinh mã Python thật. |
| 11 chiến thuật mẫu | **có** | Lời giải của mấy hồi cuối. |
| Song ngữ | **có** | Vừa xong. |

**Tóm một câu: phần khó nhất đã xong, phần trò chơi chưa bắt đầu một dòng nào.**

---

## 8. RỦI RO MỞ — chưa có lời giải

### ⚠ 8.1 · Bức tường LEAN *(cái này chặn chuyện marketing, không chặn chuyện dựng)*

Muốn bấm Chạy **một** lần, máy phải có LEAN đã **build xong** (biên dịch .NET) + thư mục
`Data` + `python3xx.dll`. Vài giờ cài, chỉ dân lập trình qua nổi.

Nửa **vẽ** thì chạy không cần gì — mở app lên là vẽ được, kho đầy đủ, sinh mã Python thật.
Chỉ đúng nút **Chạy** đụng tường.

Nghĩa là: dựng được cả trò chơi mà người lạ vẫn không chơi được. **Phải giải trước khi
phát hành, không cần giải trước khi dựng.** Để sau, nhưng đừng quên.

### ✅ 8.2 · Vệt của nến KHÔNG vào lệnh — ĐÃ CHỐT 19/10/2026

Màn «Chạy máy» muốn đóng **van** lại cho người xem thấy thì phải biết nến ấy hỏng ở điều
kiện nào. LEAN ngắt ở điều kiện sai đầu tiên nên nó không tự biết.

**Chốt: SUY RA, không chèn dòng chẩn đoán** — xem `DECISIONS.md` D-18. Bộ sinh mã không
đổi một dòng. Van có **ba** trạng thái chứ không phải hai: *dòng qua* (chắc chắn), *dòng
dừng* (dưới cổng không còn cổng nào mà cũng không lệnh nào ra), và *chưa rõ* (chuỗi nhiều
cổng — dừng ở khúc ấy, mà đúng cái nào thì chịu). Cái thứ ba là giá phải trả, và nó rẻ
hơn một màn hình chỉ bừa.

### ⚠ 8.3 · Dữ liệu doanh nghiệp phải trả tiền

Xem ghi chú ở Hồi 7.

---

## 9. DỰNG THEO THỨ TỰ NÀO

Mỗi mốc phải **nhìn thấy được**, không mốc nào là "hạ tầng xong rồi mà chưa thấy gì".

| Mốc | Làm gì | Xong là thấy gì |
|---|---|---|
| **M1** | Tách canvas khỏi Home. Dựng màn MỞ MÁY + HÀNH TRÌNH + XƯỞNG, chuyển cảnh. | App mở ra **không còn là canvas**. Đã ra dáng trò chơi. |
| **M2** ✅ | Màn CHẠY MÁY có hình (dây có dòng, van, lệnh nổ, tua nhanh). | **Quay được video đầu tiên.** |
| **M3** | Chép luật chơi từ `main`. Màn 0 + Hồi 1 + màn CHẤM + màn ẩn. | **Chơi thật được 4 màn.** |
| **M4** | Hệ mở khoá + màn hình KHO. Hồi 2 (gồm màn 8 — màn gãy). | Trò chơi **biết dạy**. |
| **M5** | Hồi 3→9. Nội dung là chính, không phải cơ chế. | Đủ 26 màn. |
| **M6** | Con mèo, âm thanh, đánh bóng, khoe điểm. | **Sản phẩm.** |
| **M7** | Giải bức tường LEAN (§8.1). | Người lạ chơi được. |

> **Đã làm tới đâu (20/10/2026).** M1→M6 xong, M7 mới xong nửa mã. Sau đó là một
> lượt **đánh bóng mắt nhìn** — thang màu dựng lại theo TradingView, bản đồ hành
> trình vẽ lại, chữ trên thẻ khối tô theo nghĩa (xem §5b).
> M1 `db9b06f` · M2 `2157c12` · M3 `71487e2` · M4 `cdbdb46` · M5 `458b94f` ·
> M6 `8de9af8` · M7 nửa mã `961b59c`.
>
> **Còn lại, và đều là việc của chủ dự án:**
> 1. **Ba màn chưa có sân** — m17 · m18 · m19, cả ba cần kho `fine` của QuantConnect
>    (hàng trả tiền). Hoặc mua dữ liệu, hoặc đổi ba màn ấy sang bài khác.
> 2. **Hình con mèo** — bản trong app là hình tạm vẽ bằng SVG, giữ đúng cỡ và đúng
>    tính cách để thay.
> 3. **M7 còn ba chỗ vướng:** .NET 10 phải có sẵn (hoặc build LEAN self-contained,
>    +~70 MB), Python phải gói kèm cho pythonnet, và **điều khoản dữ liệu** —
>    `Data/` không có file giấy phép nào, phải hỏi QuantConnect trước khi phát hành kèm.

> M1 và M2 làm xong là đã có thứ để đăng lên mạng, dù chưa có màn nào. Cố ý xếp thế.

---

## 10. THỨ TÔI CẦN BẠN CHỐT TIẾP

Không phải bây giờ, nhưng sớm muộn phải có:

1. **Con mèo trông thế nào.** Tôi tả được tính cách, không vẽ được nó.
2. **Thị trường của 26 màn.** Mỗi màn cần một mã + hai khoảng ngày có thật và có chuyện để
   kể. Chỗ này cần bạn — bạn biết thị trường, tôi không.
3. ~~**§8.2** — có cho bộ sinh mã tự chèn dòng chẩn đoán không.~~ ✅ chốt 19/10/2026:
   KHÔNG chèn, suy ra (D-18).
