# Ổ cắm trống

Sổ này ghi những chỗ đã bị **gỡ có chủ ý** trong lần dọn Cat_Studio sang HFT market
maker, và chưa có gì cắm vào.

Vì sao phải có sổ: một khoảng trống không đánh dấu thì sáu tháng nữa không ai đọc ra
được nó là *chưa làm* hay là *cố tình không có*. Mỗi mục dưới đây trả lời đúng ba câu —
**nằm ở đâu · trước cắm gì · phải cắm gì**.

Luật của sổ: một ổ cắm được cắm xong thì **xoá khỏi đây**, không đánh dấu ✔. Sổ này chỉ
liệt kê cái còn trống; nó cạn dần tới rỗng, và rỗng nghĩa là dọn xong.

Lấy lại bất cứ thứ gì đã xoá: `git checkout f1c90fb -- <đường dẫn>`, hoặc đọc mà không
lấy: `git show f1c90fb:<đường dẫn>`.

> **`f1c90fb` là mốc "trước khi dọn".** Mọi tham chiếu trong repo trỏ về đó. Đừng
> rebase mất nó.

---

## 1. Nguồn dữ liệu — ĐÃ CẮM MỘT NỬA

**Nằm ở đâu** — `cat_studio/nguon_tick.py` (định dạng · đọc · dò mất gói · sổ lỗ hổng)
và `tools/ghi_tick.py` (bộ ghi 24/7). Bài kiểm: `tests/test_nguon_tick.py`.

**Còn trống** — **lịch sử**. Bộ ghi vừa xong, nên hôm nay chưa có gì để backtest. Đây
là ổ cắm duy nhất không rút ngắn được bằng cách viết code nhanh hơn: **phải chạy và
phải chờ.**

### Vì sao tự ghi, không tải về

Đo kho miễn phí của Binance ngày **2026-08-28**:

| luồng | phủ |
|---|---|
| `aggTrades` · `trades` | 996 symbol · 2019-12-31 → **2026-08-27** ✔ |
| `bookTicker` | 315 symbol · 2023-05-16 → **2024-03-30** ✘ ngừng hẳn |
| `bookDepth` | hiện hành, nhưng **không phải sổ lệnh** — thanh khoản ở ±1…5 % quanh mid, mẫu 2,5 s |

Và 315 symbol có sổ lệnh đúng là nhóm **BTC/ETH/SOL** mà `tools/do_spread.py` đã loại.
Nhóm còn cửa thì `bookTicker` **rỗng hoàn toàn**. Hyperliquid có kho nhưng
**requester-pays** — 403 nếu không có tài khoản AWS.

Đổi lại được thứ đắt hơn dữ liệu: **backtest và live đọc cùng một luồng byte từ cùng
một ổ cắm.**

### Bốn con số đã đo, không phải ước lượng

Chạy thật 60 giây trên TRUMPUSDT + PUMPUSDT:

| | |
|---|---|
| **độ trễ** | trung vị **207 ms**, p99 **350 ms** — đồng hồ máy chỉ lệch −121 ms nên đây là mạng thật |
| **nhịp** | ~115 bản ghi sổ/s · ~33 khớp/s cho một symbol tầm trung |
| **dung lượng** | ~**800 MB/ngày/symbol** (sổ 640 + khớp 160) → ~24 GB/tháng. Cộng độ sâu từ 2026-08-28: **+340…580 MB/ngày**, phần thêm có trần cứng |
| **mất gói** | 0 · lỗ hổng 0 |

Độ trễ 207 ms là **ràng buộc thiết kế, không phải chi tiết**: nó nói cuộc chơi không
phải tốc độ mà là bề rộng báo giá và quản tồn kho.

### Hai phát hiện phải nhớ

**`@aggTrade` chết.** Trả **0 gói trong 10 giây** cho cả `trumpusdt` lẫn `btcusdt`,
trong khi `@trade` cùng lúc trả 944 và `@bookTicker` trả 1.259. Không lỗi, không đóng
kết nối — chỉ im lặng. Dùng `@trade`, và nó hợp hơn thật: `aggTrade` gộp các cú khớp
liên tiếp cùng giá, mà thứ ta cần là đúng chuỗi để trừ dần hàng đợi.

**Ban đầu chỉ ghi ĐỈNH sổ lệnh — và đã đổi ý, ngày 2026-08-28.** Lý do cũ: spread đúng
một tick trên gần như mọi symbol còn cửa, không có chỗ chen vào giữa, ta chỉ xếp hàng ở
đỉnh. Lý do đó **vẫn đúng cho việc phát lại hàng đợi**, và `bookTicker` vẫn là luồng
duy nhất giữ đúng thứ tự từng thay đổi.

Nhưng nó trả lời sai câu hỏi. Độ sâu không sinh ra để phát lại hàng đợi; nó trả lời
*"phía sau ta còn bao nhiêu"* (đúng cái `phan_muc_sau` trong `khop_lenh.py` đang **đoán**)
và *"sổ đang nghiêng bên nào"*. Hai câu đó cần một **hình dạng lấy đều đặn**, không cần
đúng thứ tự — nên 100 ms một ảnh là thừa đủ.

Và ước lượng dung lượng cũ (*"gấp mười"*) sai: bản ghi to gấp mười, nhưng tới **thưa
hơn gần mười lần**. Đo thật 1…2× tuỳ chợ sôi hay lặng — và vì sàn gộp về 100 ms, luồng
này có **trần cứng 580 MB/ngày/symbol** bất kể thị trường thế nào, trong khi `bookTicker`
không có trần.

Nên từ nay ghi **ba luồng**: `so` (đỉnh, đủ độ phân giải) · `khop` · `sau`
(`@depth20@100ms`, ảnh chụp 20 mức mỗi bên).

**`@depth20` là ẢNH CHỤP, `@depth` là BẢN SAI KHÁC** — hai tên gần giống nhau, cùng báo
`"e": "depthUpdate"`, và chọn nhầm thì phải dựng lại cả cuốn sổ. Đã đo để phân biệt:

| | mức mỗi gói | dòng kl = 0 | giá sắp thứ tự | |
|---|---|---|---|---|
| `@depth20@100ms` | đúng 20/20 | 0 | có | **ảnh chụp** — tự đọc được |
| `@depth@100ms` | 1…106 / 0…59 | 10 | không | bản sai khác — cần ảnh REST, nối `U`/`u`/`pu`, đồng bộ lại sau mỗi lỗ hổng |

Đối chiếu trên dữ liệu thật: ghi 35 s live, so đỉnh của từng ảnh độ sâu với bản ghi
`bookTicker` gần nhất trước nó — **khớp 100 % cả hai bên trên 226 ảnh**. Hai luồng độc
lập nói cùng một chuyện.

### ⚠ Còn nợ: CHƯA AI ĐỌC luồng `sau`

Bộ phát lại vẫn chỉ ăn `so` và `khop`. Luồng độ sâu đang được **ghi mà không được
dùng** — cố ý: dữ liệu quá khứ không mua lại được, mỗi giờ không ghi là một giờ vĩnh
viễn không có, còn mã đọc thì tuần sau viết vẫn kịp.

Ba chỗ sẽ dùng nó, theo thứ tự đáng làm:

1. **`khop_lenh.phan_muc_sau`** — hiện là một **núm người dùng đoán**. Có độ sâu thì nó
   thành số **đo được**, và một dòng nữa chuyển từ tab "Fill model" sang tab
   "Data source" theo đúng luật *đo được thì đừng hỏi*.
2. **Toán hạng `lech_luong`** (§8) — sổ nghiêng bên nào, ứng viên đầu tiên cho một
   `cong_bang` khá hơn `mid`.
3. **Trộn vào `phat_lai`** — việc này chạm vòng nóng và mô hình khớp, nên phải là một
   đợt riêng, không ghép vào đợt ghi.

### Lớp phát lại — XONG

`cat_studio/phat_lai.py` + `tests/test_phat_lai.py` (21 phép). Ba luật đã cài và có
bài kiểm riêng cho từng cái:

1. **Trục thời gian là `t_ta`, không phải `T`.** Một cú khớp xảy ra ở sàn *trước* một
   thay đổi sổ vẫn được phát *sau*, nếu gói của nó tới muộn hơn. Xếp theo `T` là cho
   chiến lược thấy tương lai — lỗi nhìn trước ở dạng tinh vi nhất: mọi con số đều có
   thật, chỉ thứ tự là bịa.
2. **Lỗ hổng là SỰ KIỆN** (`MO_LO_HONG` / `DONG_LO_HONG`), không phải khoảng trống. Ra
   khỏi vùng mù thì sổ lệnh trở lại **chưa biết** (`co_so = False`, `mid = NaN`) cho
   tới bản ghi `so` kế tiếp.
3. **Tất định.** Hoà `t_ta` thì phá hoà bằng `(T, nguồn, chỉ số)`.

Tốc độ **1,97 triệu sự kiện/giây** — một ngày ~5 s, một tháng ~2,5 phút. Bản đầu chạy
0,40 triệu/s; chỗ mất thời gian là `a[k]["bid"]` (numpy dựng một `np.void` trung gian
cho cả bản ghi). Tách cột một lần lúc dựng → nhanh gấp 5.

> ⚠ Một điều người đọc kết quả backtest phải biết: trong **cùng một mili giây** ta
> không biết thứ tự thật. `t_ta` chỉ mịn tới ms mà nhịp là ~150 sự kiện/giây, nên đụng
> nhau thường xuyên. Phá hoà bằng `T` là phỏng đoán tốt nhất có thể, không phải sự thật.

### Bảng điều khiển trong app — XONG

**Cài đặt → tab "Nguồn dữ liệu"** (`webui/src/components/NguonPanel.tsx`). Tự làm mới
mỗi 3 giây — một bảng điều khiển đứng hình là bảng nói dối.

> ⚠ Bản đầu làm nó thành hộp thoại RIÊNG ở File → Nguồn dữ liệu, lý lẽ là "Cài đặt để
> đặt một lần rồi quên, còn đây là bảng điều khiển sống". Người dùng đi thẳng vào Cài
> đặt tìm nó — và họ đúng: nguồn dữ liệu là một thiết lập, mắt tìm nó ở chỗ mọi thiết
> lập khác nằm. Đã dời vào và **bỏ hẳn cửa cũ**; hai đường vào một thứ thì sớm muộn
> một đường mục đi mà không ai biết.

**APP KHÔNG SỞ HỮU BỘ GHI.** Bộ ghi là tiến trình riêng phải sống 24/7 kể cả khi app
đóng — đúng bài học cửa sổ Live cũ đã trả giá: *"đóng cửa sổ không được dừng phiên"*.
Nên app chỉ **nhìn** và **xin**:

| cơ chế | vì sao không làm cách khác |
|---|---|
| **nhịp tim** — file `_dang_ghi.json`, đập mỗi 5 s | `song` suy từ TUỔI NHỊP, không từ pid: hệ điều hành cấp lại pid cho tiến trình khác là app báo "còn sống" trên một tiến trình chẳng ghi gì |
| **cờ dừng** — file `_dung` | `taskkill /F` cắt ngang, mất phần đệm chưa xả. Tín hiệu Ctrl+Break thì phụ thuộc tiến trình được sinh kiểu gì — đúng máy này, sai máy khác. File thì luôn đúng |
| **`DETACHED_PROCESS`** khi mở | tiến trình con chết theo cha, mà cha là một app người ta đóng/mở suốt ngày |
| stdout → `_ghi.log` | tiến trình rời không có console; không hứng thì mọi lời than của nó rơi vào hư không |

Đã chạy đủ vòng đời qua API: bật → nhịp lên sau 2 s → **bật chồng bị từ chối** → **xoá
khi đang ghi bị từ chối** → xin dừng → thoát sạch sau 10 s. Bằng chứng đệm được xả:
sau khi dừng, số bản ghi **nhiều hơn** lúc trước khi dừng (3.006 vs 2.433).

### Bốn con số CHỈNH ĐƯỢC — và chỉ bốn

Cài đặt → **Nguồn dữ liệu**. Nguyên tắc: **đo được thì đừng hỏi.** Một ô cài đặt chỉ
chính đáng khi con người phải phán đoán mà máy không đo được; hỏi một thứ đo được là
mời người ta gõ số sai rồi tin nó — đúng cái bẫy ô `spread = 20 points` của bản MT5 cũ.

| ô | vì sao chỉnh vào là đổi thật |
|---|---|
| **thư mục** | ~800 MB/ngày/symbol → 24 GB/tháng. Ổ C: không phải lúc nào cũng chịu nổi, mà ổ đầy thì bộ ghi chết lúc 3 giờ sáng |
| **giữ N ngày** | không đặt thì sớm muộn đĩa đầy. Mặc định 0 = giữ tất, vì xoá là việc không lùi được |
| **ngưỡng im lặng** | thấp quá → lỗ hổng GIẢ trên symbol thưa; cao quá → ngồi mù mà tưởng đang chạy |
| **nhịp xả** | "mất điện thì mất bao nhiêu" |

Cộng **danh sách symbol** (lưu lại — bộ ghi khởi động lại phải nhớ ghi gì) và nút **Đo
thị trường** gọi thẳng `do_thi_truong.do()`, cùng lõi với `tools/do_spread.py` — bảng
trên màn hình và bảng trong app là cùng con số, không hai bản chép tay.

### Lệch đồng hồ — đã cắm, và nó là thứ gấp nhất

`t_ta` đóng dấu bằng đồng hồ MÁY, `T` đến từ SÀN. Đo được: máy chậm hơn sàn **~90 ms**.
Mà `t_ta` là trục thời gian của cả backtest, nên sai số đó chui thẳng vào mọi kết quả —
và lệch một chiều, không tự triệt tiêu.

    thời điểm THẬT = t_ta − lệch        độ trễ thô 248 ms  →  thật 342 ms

Bộ ghi đo mỗi 5 phút (lấy mẫu **RTT nhỏ nhất**, kiểu NTP — không lấy trung bình, vì sai
số một lần đo bị chặn bởi ±RTT/2) và cất cạnh dữ liệu. `phat_lai` sửa **cả cột một lần**
bằng `np.searchsorted`, TRƯỚC khi trộn — sửa sau khi trộn là xếp hai luồng theo một trục
đang lệch, và bài kiểm chứng minh nó đổi thứ tự thật.

> **Chưa đo lần nào → KHÔNG hiệu chỉnh gì**, và `co_dong_ho = False` nói ra điều đó.
> "Đo được là 0" nghĩa là đồng hồ đúng; "chưa đo" nghĩa là không biết. Gộp hai thứ đó
> là biến một chỗ không biết thành một lời khẳng định.

> ⚠ RTT tới Binance từ đây là **~240 ms**, nên chính con số hiệu chỉnh có sai số
> **±120 ms**. Độ trễ "342 ms" thật ra là 342 ± 120. Ai đọc kết quả phải biết.

### Ba con số đo được trong lúc dựng phần này

| | |
|---|---|
| bắt tay đóng WebSocket | mặc định chờ **10 s** → dừng bộ ghi mất 10,7 s. Đặt `close_timeout=1` → **1,6 s** |
| khởi động bộ ghi | đo đồng hồ 1,3 s + bắt tay WS 1,7 s = **3,0 s** trước byte đầu tiên |
| `a[k]["field"]` vs cột tách sẵn | **5 lần** chênh lệch (xem `phat_lai`) |

### Việc còn lại của ổ cắm này

- **chạy bộ ghi liên tục** — một máy 24/7, ~24 GB/tháng/symbol. Đây là thứ duy nhất
  không rút ngắn được bằng cách viết code nhanh hơn;
- chốt danh sách symbol — lấy từ `tools/do_spread.py`;
- lớp live cùng bề mặt `buoc()` — thuộc về ổ cắm §2.

---

## 2. Kết nối sàn

**Nằm ở đâu** — `api.Api.mo_live` trả `{ok: false, "Chưa có kết nối sàn."}`. Nút ● Live
vẫn còn trên ribbon và vẫn nói được thành lời.

**Trước cắm gì** — hai file:

- `ket_noi.py` (1.149 dòng) — đo **có TIN được không**, không phải "có nối được không".
  Ba kiểu chết im lặng nó sinh ra để bắt: terminal báo connected mà feed đứng; nút
  AlgoTrading tắt nên mọi lệnh bị từ chối trong im lặng; spread live khác xa spread đã
  backtest. Cộng vòng hiệu chuẩn bằng lệnh nháp và phép dò `stops_level`.
- `gui_lenh.py` (636 dòng) — đặt/sửa/huỷ lệnh, mỗi lần bị từ chối thì sửa yêu cầu theo
  luật rồi thử lại, và **chốt chống gửi trùng** (xin 5 lot mà bắn ra 3 lệnh thành 15 lot
  thật, hai ticket đầu biến mất).

**Phải cắm gì** — tương đương cho sàn mới. Docstring cũ của `ket_noi.py` là bản đặc tả
tốt nhất đang có cho tầng này: **đọc `git show f1c90fb:cat_studio/ket_noi.py` trước khi
viết một dòng nào**. Với market maker thì phần đo độ trễ còn quan trọng hơn hẳn — nó
thôi là "sức khoẻ", nó thành tham số của chiến lược.

---

## 3. Cửa sổ Live

**Nằm ở đâu** — không còn.

**Trước cắm gì** — `webui/src/live/` (822 dòng) + `api.ApiLive` (~485).

**Phải cắm gì** — ý tưởng `CongChot` đáng dựng lại nguyên vẹn: **hộp chốt nằm TRONG cửa
sổ Live, không đóng được bằng ✕ hay Esc**, vì đó là cửa duy nhất giữa một sơ đồ đang vẽ
dở và một kết nối tiêu tiền thật. Không có đường tắt — đường tắt là thứ người ta dùng
đúng lúc vội, mà vội là lúc dễ sai nhất.

---

## 4. Soi một lượt — CÒN THIẾU THANG BÁO GIÁ

**Nằm ở đâu** — `bo_chay.mot_luot_ghi` + `soi_luot` · `api.soi_luot` ·
`webui/src/components/SoiPanel.tsx` · phần soi trong `StepNode` và `App`.

Bấm một điểm trên biểu đồ Kết quả → sơ đồ sáng lên đúng đường lượt đó đã đi, mờ phần
còn lại, kèm CON SỐ THẬT của từng điều kiện (`−0,05 ≥ 5`). Thẻ nổi chở hai đầu của lượt
chạy: sổ lệnh + tồn kho lúc đó, và báo giá đã làm tròn về tick.

> ⭐ **Cách nó chạy được là điều đáng nhớ nhất của mục này.** Cách hiển nhiên — *phát
> lại tới thời điểm T rồi chụp* — mất tới hai phút cho một ngày dữ liệu, tức bấm xong
> ngồi chờ một phút và không ai bấm lần thứ hai.
>
> Mà điểm mẫu vốn được lấy ĐÚNG LÚC sơ đồ vừa chạy xong lượt đó. Cho mẫu chở thêm năm
> số nữa (sổ lệnh + có_sổ) thì soi thành một **hàm THUẦN**: không phát lại, không đọc
> file, không giữ trạng thái. Tức thì, và bấm lại đúng mốc đó luôn ra đúng một kết quả.
> Giá phải trả: mẫu phình gấp đôi (~160 KB), và chỉ soi được đúng những mốc đã lấy mẫu.

**Ba cái bẫy của bản cũ, đã tránh được cả ba:** kẹp `soi.tab === tab` ở nơi tiêu thụ
(giờ chỉ còn một sơ đồ nên chưa cần); chỉ tô khi số dòng còn khớp (giờ tô theo `id`
khối, không theo chỉ số dòng, nên sửa sơ đồ xong soi lại vẫn trỏ đúng); có nút ✕ chứ
không chỉ phím Esc — **cả hai đều có**.

**Phải cắm gì** — hai thứ, chung một cơ chế, nên làm cùng lúc:

| còn thiếu | vì sao |
|---|---|
| **thang báo giá hai bên** — vẽ bid/ask của ta CẠNH bid/ask thị trường | thẻ hiện bốn con số, nhưng "ta đang treo trong hay ngoài sổ" là một câu hỏi HÌNH HỌC. Bốn số bắt người đọc tự dựng hình trong đầu |
| **soi được lúc ĐANG MÙ** | lỗ hổng không sinh sự kiện nào nên KHÔNG có điểm mẫu nào rơi vào trong nó — đúng quãng đáng ngờ nhất lại là quãng soi không tới. Cần một mẫu ép ở mốc mở lỗ hổng |

> ⚠ **Và bộ chạy vẫn NGẮT SỚM ở điều kiện sai đầu tiên** (`mot_luot`), trong khi
> `mot_luot_ghi` tính đủ. Hai bản này là MỘT NGUỒN SỰ THẬT BỊ CHÉP LÀM HAI — cố ý, vì
> một bản chạy mười triệu lần một ngày còn bản kia chạy mỗi lần bấm chuột. Cái giá trả
> bằng `tests/test_soi.py`: 3.000 lượt trên 120 sơ đồ ngẫu nhiên, so từng ô. **Sửa một
> bản thì phải sửa bản kia**, và bài kiểm sẽ nói ngay nếu quên.


> **Ba chỗ đã cân nhắc rồi bỏ, ghi ra để khỏi bàn lại:**
> · *Đếm số lần bị từ chối theo thời gian* — `mau` đã chở sẵn cột đó (cột thứ 5), chỉ
>   chưa vẽ. Rẻ, thêm lúc nào cũng được.
> · *Biểu đồ phân bố markout* — thú vị nhưng một con số trung bình đã đủ để quyết định,
>   và phân bố cần chỗ bằng cả hai biểu đồ hiện có. **Đã trả một nửa món này**: thay
>   một mốc bằng THANG năm mốc (100 ms … 30 s) trên một hàng. Không phải phân bố, nhưng
>   là HÌNH DẠNG theo thời gian, và tốn đúng một dòng.
> · *So hai lượt chạy cạnh nhau* — đúng là thứ người ta muốn khi vặn `phan_huy_truoc`
>   qua ba mức. Đợi tới khi có ai thật sự làm việc đó nhiều lần.

---

## 5. Điều kiện chạy trong Cài đặt

**Nằm ở đâu** — `webui/src/components/SettingsDialog.tsx` giờ chỉ còn mã mặc định và
màu nhấn. Khoá `test` trong `luu_tru.CAI_DAT_MAC_DINH` và hàm `api.save_test_settings`
đều đã bỏ.

**Trước cắm gì** — bảng nguồn nến (số nến, MB, nút xoá), nút kiểm kết nối MT5, và bảy
con số: khoảng thời gian, spread tính bằng point, vốn, phí round-turn, đòn bẩy, nhịp
phát lại.

**Phải cắm gì** — chưa biết đơn vị. Market maker cần **phí maker và phí taker tách
riêng** (bản cũ chỉ có một con số round-turn) và một ngân sách độ trễ; cả hai chỉ định
nghĩa được sau khi chọn sàn.

> File `cai_dat.json` cũ trên máy người dùng vẫn còn khoá `test`; nó nằm im, không ai
> đọc. Cố ý **không** viết mã dọn: một phép xoá chạy đúng một lần trong đời rồi ở lại
> vĩnh viễn thì đắt hơn mấy trăm byte nó dọn được.

---

## 6. Nợ độ phủ — KHÔNG phải ổ cắm, nhưng phải trả

Bộ test đi từ **4.213 dòng xuống 663**, và phần lớn là đúng — một bài kiểm không còn
đối tượng thì là rác, không phải độ phủ. Nhưng **ba nhóm dưới đây kiểm CƠ CHẾ chứ không
kiểm D_02**, nên chúng là nợ thật, phải trả khi cơ chế tương ứng quay lại:

| Bài kiểm đã mất | Kiểm CƠ CHẾ gì |
|---|---|
| `test_nhat_ky.py` (478) | bản ghi rỗng chữ · lưu id không lưu nhãn · ghi/đọc ngược không mất gì |
| `test_dat_ten.py` (333) + mục 4 `test_kho_va_lenh.py` (~60) | số gõ tay hai chỗ → cảnh báo · bỏ tham số đang dùng → lỗi · khai tham số thừa → cảnh báo |
| `test_bo_chay.py` (425) | thứ tự trong một nhịp · **luật lùi** · tính XÁC ĐỊNH (chạy lại ra kết quả y hệt) |
| 5 mục cuối `test_danh_so.py` (~160) | mô tả hành động đọc được · soát thiếu SL / thiếu mốc neo · cơ chế "so hai đại lượng" |

**Dòng cuối bảng ĐÃ TRẢ**, bằng một bộ luật khác hẳn: `test_ngu_phap.py` phủ mô tả
hành động, luật kiểu, và ranh giới *sửa hộ ⟷ đoán ý* của chuẩn hoá. Cơ chế "so hai đại
lượng" thì không trả mà **bỏ hẳn** — nó là một cờ tách rời khỏi dữ liệu, tức một nguồn
sự thật thứ hai, và nó đã lệch một lần rồi. Giờ chế độ so suy thẳng từ `!!phai.ten`,
không còn gì để lệch.

Giữ một `bo_chay` rỗng ruột chỉ để nuôi fixture thì đuôi vẫy được cả con chó — nên
chúng đi. Nhưng phần còn lại là **nợ**, không phải dọn xong: có bộ chạy mới thì viết
lại ngay.

---

## 7. Bảng tham số — hằng số CÓ TÊN

**Nằm ở đâu** — `core.normalize_process` giữ khoá `tham_so` và luôn trả `[]`;
`api.bootstrap` không gửi gì; `types.ts` khai `tham_so: never[]`.

**Trước cắm gì** — ~60 dòng ở `core.py` cộng bảng bên `ActionDialog.tsx`: mỗi tham số
là một hằng số có TÊN, khối tham chiếu bằng tên, cộng phép quét
`_tham_so_dang_dung` để biết khối nào đọc tham số nào, cảnh báo **"số gõ tay hai chỗ"**
kèm nút đặt tên ngay tại đó, và luật *"nhập chiến lược khác thì tên đã có GIỮ NGUYÊN
giá trị hiện tại"* — đè lên là lặng lẽ đổi hành vi của cả chiến lược đang làm dở.

**Phải cắm gì** — sơ đồ mẫu đang có ba con số trần mà mỗi con đều đáng có tên:

| số trần | tên nó muốn mang |
|---|---|
| `lệch += tồn kho × 0,5 tick/lot` | `độ_lệch_theo_tồn_kho` |
| `lot = 500` | `cỡ_lệnh_gốc` |
| `khi tồn kho ≥ 2000` | `hạn_mức_tồn_kho` |

Hai con số cuối xuất hiện ở **hai khối khác nhau** (`lot mua` và `lot bán` cùng đọc
`hạn_mức`), nên đây đúng là ca mà cảnh báo "số gõ tay hai chỗ" sinh ra để bắt — sửa
một chỗ quên chỗ kia thì báo giá lệch hẳn một phía và nhìn sơ đồ không thấy gì lạ.

Phép quét thì **cố ý dùng LẠI đúng bộ quét của validator**: viết bộ quét thứ hai là
sớm muộn hai bên hiểu khác nhau, và cái lệch thì im lặng.

---

## 8. Bốn toán hạng còn thiếu của market maker

**Nằm ở đâu** — `cat_studio/kho/nen_tang.py` khai tám toán hạng; docstring của nó liệt
kê bốn cái tiếp theo.

**Trước cắm gì** — không phải "trước": bốn cái này CHƯA từng có. Ghi vào sổ vì tám
toán hạng hiện tại đủ dựng một market maker sơ cấp nhưng **không đủ để nó kiếm ra
tiền**, và khoảng cách đó phải nhìn thấy được.

**Phải cắm gì**

| toán hạng | vì sao thiếu nó là mù |
|---|---|
| `microprice` | giá công bằng có trọng số theo khối lượng phía ĐỐI DIỆN. Bid chất 40.000 lot mà ask chỉ 200 thì giá thật nằm sát ask — `mid` mù đúng chỗ đó, và đó là chỗ hay bị chọn ngược nhất |
| `bien_dong` | biến động thực trên cửa sổ N giây → giãn biên khi chợ động. Không có nó thì biên cố định, và chợ động là lúc bị chọn ngược nhiều nhất |
| `tuoi_bao_gia` | quote đã nằm trong hàng bao lâu — thứ thay thế được cho vị trí hàng đợi, cái mà L1 không bao giờ nhìn thấy |
| `lech_luong` | lệch dòng lệnh chủ động mua/bán, để đoán hướng ngắn hạn |

Cả bốn đều là **module mới thả vào `kho.MODULE`**, không sửa `core.py`, không sửa
`api.py`, không sửa hộp thoại — cơ chế đã chịu được điều đó (`vi_cau_truc.py`).

---

## 9. Động từ thứ ba — LỆNH CHỦ ĐỘNG

**Nằm ở đâu** — `core.ACTION_TYPES` có đúng hai động từ: `check_cond` · `so_hang`.

**Trước cắm gì** — `vao_lenh` và `sua_lenh` của D_02, nhưng chúng KHÔNG phải thứ thiếu
ở đây. Cả hai nói về một thế giới có LỆNH RỜI mang SL/TP riêng; market maker phát biểu
lại toàn bộ báo giá mỗi sự kiện, nên chúng không dịch sang được. Xem mục 11 cũ trong
`git show f1c90fb:tai_lieu/o_cam_trong.md` nếu cần đọc lại bảng đối chiếu.

**Phải cắm gì** — một động từ **taker**, và chỉ một chỗ thật sự cần nó:

> Tồn kho chạm hạn mức CỨNG thì phải ĐÓNG chủ động, không chờ ai lấy hàng.

Sơ đồ mẫu hiện xử lý hạn mức bằng cách tắt một phía (`lot mua = 0`), tức chỉ *ngừng
nhồi thêm* rồi chờ phía kia xả dần. Đủ cho trường hợp thường, nhưng khi giá chạy một
chiều thì phía kia không bao giờ khớp và tồn kho đứng nguyên ở hạn mức — lúc đó chỉ
lệnh thị trường mới cắt được.

Nó **không nhét vào ngữ pháp số hạng được**, và đó là lý do phải ghi ra: một số hạng
góp vào báo giá, còn cái này VỨT báo giá đi và bắn một lệnh ăn ngay. Hai việc khác
loại.

Mô hình khớp chỉ mô phỏng lệnh THỤ ĐỘNG — lệnh taker là đường đi khác hẳn: khớp ngay,
ăn qua nhiều mức, trả phí taker chứ không phải phí maker.

**Giờ đã có CON SỐ chứ không còn là suy đoán.** Cho sơ đồ mẫu chạy 400.000 sự kiện thì
đúng lúc tồn kho chạm hạn mức, `lệch` đẩy báo giá lấn qua phía đối diện và post-only từ
chối — chiến lược đang nói *"tôi muốn thoát hàng bằng mọi giá"* mà lệnh thụ động thì
không thoát bằng mọi giá được. Đó chính xác là chỗ động từ thứ ba phải đứng.

---

## 10. Sổ lệnh

**Nằm ở đâu** — không còn file nào.

**Trước cắm gì** — `so_lenh.py` (223 dòng): bảng `Lenh` + bảng `Zone`, mỗi thứ một id
**của CHÍNH TA** (`L-0001`, `V-0003`) đếm tăng chứ không phải uuid.

**Phải cắm gì** — sổ lệnh mới, và ba quyết định cũ đáng bê nguyên sang:

- **id của ta, không mượn ticket sàn.** Backtest không có ticket; định danh phụ thuộc
  sàn thì nửa hệ thống không chạy được khi chưa nối. D_02 không có id nối lệnh chờ với
  vị thế sinh ra từ nó nên phải ĐOÁN bằng `HasOpenPosition()`.
- **Id đếm tăng, không uuid** — chạy lại cùng dữ liệu ra cùng id, nên so được hai lần
  backtest. uuid thì mất cả hai.
- **Giữ cả lệnh đã chết**, không xoá đi: những câu hỏi kiểu "vùng này đã sinh lệnh
  chưa" phải trả lời được kể cả khi lệnh đó đã đóng từ lâu.

Thứ **phải thêm mới** và bản cũ không có: **tồn kho có dấu** (±lot), tuổi quote tính
bằng mili-giây, và theo dõi từng phía bid/ask riêng.

---

## 11. Nhật ký và lịch sử

**Nằm ở đâu** — không còn file nào. Thư mục `du_lieu/nhat_ky/` vẫn được liệt kê trong
hộp thoại Kho nhưng KHÔNG AI GHI vào nữa.

**Trước cắm gì** — `nhat_ky.py` (283) và `lich_su.py` (197). Cả hai nhận thẳng
`bo_chay.KetQua` với `.nen1` / `.nen5` — kiểu tham số của chúng đã không còn tồn tại,
nên chúng không phải "mồ côi" mà là **không chạy được**.

> ⚠ **Bộ chạy đang NGẮT SỚM ở điều kiện sai đầu tiên** (`bo_chay.mot_luot`), trong khi
> bản D_02 cố ý tính đủ mọi điều kiện để nhật ký trả lời được *"ba điều kiện kia lúc đó
> bằng bao nhiêu"*. Ngắt sớm vì hiện chưa có nhật ký nên cái mất bằng 0. Làm nhật ký
> thì thêm một `mot_luot_ghi()` chạy đủ — **đừng bỏ bản ngắt sớm**: soi một lượt là
> việc thỉnh thoảng, chạy mười triệu lượt là việc thường xuyên.

**Phải cắm gì** — nhật ký mới, giữ nguyên ba luật đã trả giá để có:

1. **Bản ghi RỖNG CHỮ.** Bộ chạy chỉ nhả số nguyên, số thực và id; chữ tiếng Việt được
   dựng lúc HIỂN THỊ, và chỉ cho lô đang nhìn (~200 dòng). 135.000 bản ghi vì thế
   không tốn một byte chữ nào lúc chạy.
2. **Lưu `id` khối, KHÔNG lưu nhãn `[3A.1]`.** Nhãn là hàm thuần của (đồ thị + VỊ TRÍ):
   ghi nhãn vào nhật ký thì kéo một khối lên 1 px là toàn bộ nhật ký cũ trỏ vào khối
   khác, không đối chiếu lại được với lần chạy trước.
3. **Một bản ghi = MỘT LƯỢT chạy**, không ghi từng khối đi qua — 7 khối × 71.000 nhịp
   là 500.000 dòng rác không ai đọc nổi.

`lich_su.py` thì lưu **thứ ĐẺ RA kết quả** (sơ đồ + cài đặt đã đóng băng) chứ không lưu
kết quả: nhờ vậy chạy lại được, và so được hai lần chạy.


---

## 12. Nhật ký thiết kế đã cắt khỏi `core.md`

**Nằm ở đâu** — `tai_lieu/core.md`, mỗi chỗ cắt để lại một dòng `<!-- ĐÃ CẮT (đợt 4): …
-->` nói rõ mất gì.

**Trước cắm gì** — file đi từ **2.403 xuống ~1.000 dòng**:

| Cắt | Dòng |
|---|---|
| §12 toàn bộ thiết kế Strategy Tester + nhật ký hoàn thiện nó | ~1.030 |
| §7 chiến lược mẫu Compress (D_02) | 94 |
| §6.4 bảng tham số | 187 |
| §11 kế hoạch cũ · §4.3 nút ▶ Chạy · §12.23 · §13.4 · §13 việc còn treo | ~150 |

Cùng `tai_lieu/D02_Compress_ban_giao.md` (276 dòng) — bản tóm tắt một buổi mổ xẻ EA gốc.

**Phải cắm gì** — không phải "cắm lại" mà **viết mới** khi thiết kế market maker chốt:
một §12 mới cho cửa sổ chạy, và một §7 mới cho chiến lược mẫu.

> Phần Ở LẠI của `core.md` là phần đã sống sót qua cả D_02 lẫn MT5, và nhiều khả năng
> sẽ sống tiếp: §3 cơ chế đánh số · §4 ghim số ⟲ và khối Bắt đầu · §5 luật rẽ nhánh ·
> §6.0–6.3 hai sơ đồ / mỗi sơ đồ là một vòng lặp / hai loại khối / ba động từ ·
> §8 giao diện · §9 định dạng file. **Đọc nó trước khi sửa bất cứ thứ gì.**


---

## Trạng thái — đã cắm được gì

**Bốn đợt dọn xong.** Từ đó đã cắm được bảy mảng, và mỗi mảng xoá một mục khỏi sổ này:

| đã cắm | thay cho mục nào |
|---|---|
| **nguồn tick** — bộ ghi 24/7, lớp phát lại, lệch đồng hồ, bảng điều khiển trong app | phần lớn *Nguồn dữ liệu* (còn lại: xem cuối §1) |
| **kho `nen_tang`** — 8 toán hạng, mỗi cái tự khai công thức của nó | *Kho toán hạng* |
| **ngữ pháp báo giá** — 2 động từ · đích/phép/lượng/khi · luật kiểu · sơ đồ mẫu | *Từ vựng của khối hành động* |
| **mô hình khớp** — `khop_lenh.py` + tab Cài đặt · 58 phép kiểm | *Mô hình khớp* |
| **bộ chạy** — `bo_chay.py`, vòng phản hồi khép kín · 45 phép kiểm | *Bộ chạy* |
| **bảng Kết quả** — tách gộp/phí · markout · tồn kho · dải mù · giả định | *Cửa sổ Strategy Tester* |
| **soi một lượt** — bấm biểu đồ → sơ đồ sáng lên kèm số thật · 23 phép kiểm | phần lớn *Soi một lượt* |

**VÒNG ĐÃ KHÉP: vẽ → chạy → hiểu vì sao → sửa.** Vẽ sơ đồ, soát tĩnh, chạy trên tick
đã ghi, đọc kết quả tách gộp/phí/markout, rồi bấm vào chỗ bất thường để thấy sơ đồ lúc
đó nghĩ gì. Đó là toàn bộ vòng làm việc, và nó chạy được từ đầu đến cuối.

### Bốn điều bộ máy TỰ NÓI RA, không phải ta suy đoán

Đây là lý do phải dựng bộ chạy trước cửa sổ: cho nó chạy là nó chỉ ra chỗ thiếu.

1. **Sơ đồ mẫu requote gần như mỗi sự kiện** (399k lần / 400k sự kiện), vì
   `công bằng = mid`. Mà đổi giá là **về cuối hàng đợi** — nên ba mức `phan_huy_truoc`
   chỉ chênh nhau ~2,5%: vị trí hàng đợi chưa kịp có nghĩa thì đã bị vứt. Giữ báo giá
   cho tới khi nó lệch quá N tick thì cần một toán hạng kho CHƯA CÓ — xem §8.
2. **Sơ đồ mẫu từng KẸT CỨNG** ở hạn mức tồn kho: 99% số sự kiện bị post-only từ chối.
   Nguyên nhân là một bất đẳng thức không ai viết ra: treo ở đúng đỉnh thì
   `hạn_mức × hệ_số_lệch < spread`. Đã sửa, ghi lại trong `Api.demo_process`.
3. **Chỗ để lệch gần như không có trên thị trường spread hẹp**, nên tồn kho phải quản
   chủ yếu bằng KHỐI LƯỢNG chứ không bằng giá. Bản chất market making, không phải hạn
   chế của app.
4. **Markout −0,52 tick/lot** — chiến lược sơ cấp bị chọn ngược đều đặn. Đây là con số
   nói rằng **nới spread không cứu được**: vấn đề là báo giá đứng im khi chợ đã đi, chứ
   không phải treo chưa đủ rộng.

### Thứ tự cắm tiếp

**§8 — bốn toán hạng còn thiếu** (`microprice` · `bien_dong` · `tuoi_bao_gia` ·
`lech_luong`). Điều 1 và điều 4 ở trên đều trỏ về đúng chỗ này: sơ đồ hiện không có
cách nào diễn tả *"giữ báo giá cho tới khi nó cũ quá"* hay *"giãn biên khi chợ động"*.
Cắm chúng vào là ngữ pháp có đủ từ để viết một chiến lược không ngây thơ nữa — và bộ
máy đo được ngay là có khá hơn không.

Sau đó mới tới **§2 kết nối sàn**, và chỉ khi đã có DỮ LIỆU THẬT cùng một chiến lược ra
số dương trên đó. Cả hai đều chưa có: **repo chưa từng chạy trên một byte dữ liệu thật
nào** — mọi con số trong sổ này đến từ `tools/gia_lap.py`.

Rồi: §10 sổ lệnh → §11 nhật ký → §3 cửa sổ Live → §5 cài đặt.

Mỗi ổ cắm xong thì **xoá khỏi sổ này**, không đánh dấu ✔. Sổ cạn tới rỗng là xong.