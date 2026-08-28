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
| **dung lượng** | ~**800 MB/ngày/symbol** (sổ 640 + khớp 160) → ~24 GB/tháng |
| **mất gói** | 0 · lỗ hổng 0 |

Độ trễ 207 ms là **ràng buộc thiết kế, không phải chi tiết**: nó nói cuộc chơi không
phải tốc độ mà là bề rộng báo giá và quản tồn kho.

### Hai phát hiện phải nhớ

**`@aggTrade` chết.** Trả **0 gói trong 10 giây** cho cả `trumpusdt` lẫn `btcusdt`,
trong khi `@trade` cùng lúc trả 944 và `@bookTicker` trả 1.259. Không lỗi, không đóng
kết nối — chỉ im lặng. Dùng `@trade`, và nó hợp hơn thật: `aggTrade` gộp các cú khớp
liên tiếp cùng giá, mà thứ ta cần là đúng chuỗi để trừ dần hàng đợi.

**Chỉ ghi ĐỈNH sổ lệnh, không ghi cả cuốn.** Vì spread đúng một tick trên gần như mọi
symbol còn cửa — không có chỗ chen vào giữa, ta chỉ xếp hàng ở đỉnh. Ngày nào spread
rộng ra nhiều tick thì phải xem lại.

### Việc còn lại của ổ cắm này

- chạy bộ ghi liên tục (một máy 24/7, ~24 GB/tháng/symbol);
- chốt danh sách symbol — lấy từ `tools/do_spread.py`;
- viết lớp phát lại: một `Su_kien` duy nhất cho cả backtest lẫn live, và **cho chiến
  lược thấy dữ liệu ở `t_ta`, không phải ở `T`** — nhìn ở `T` là cho nó thấy tương lai.

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

## 3. Mô hình khớp

**Nằm ở đâu** — không còn file nào.

**Trước cắm gì** — `khop_lenh.py` (220 dòng): biến mỗi nến M1 thành **đường đi 4 điểm**
(tăng: O→L→H→C, giảm: O→H→L→C) rồi mọi thứ thành một luật *"giá chạm mức X ở bước k"* —
lệnh chờ khớp, SL bị chạm, TP bị chạm, hết. Không còn ca đặc biệt "SL và TP cùng nến".
Cộng phép quy mọi mức về Bid một lần, và luật gap (chạm ở bước 0 = khớp tại giá mở cửa).

**Phải cắm gì** — mô hình khớp cho lệnh **thụ động**, và đây là chỗ khác bản chất so với
bản cũ: với lệnh limit thì **chạm ≠ khớp**. Giá phải đi xuyên qua, và còn phụ thuộc vị
trí trong hàng đợi. Bê nguyên luật "chạm là khớp" sang market making sẽ cho lãi khống
một cách có hệ thống — đúng loại lỗi mà cả file cũ được viết ra để tránh.

---

## 4. Bộ chạy

**Nằm ở đâu** — `api.Api.mo_tester` trả `{ok: false, "Chưa có bộ chạy."}`, sau khi vẫn
soát sơ đồ tử tế. Nút ▶ Chạy còn nguyên.

**Trước cắm gì** — `bo_chay.py` (1.259 dòng). Thứ đáng cứu nhất trong đó là
**`_chay_so_do`** (~80 dòng, khó nhất repo) cùng `_xet_cong`:

- **luật lùi** — cổng trượt thì lùi về ngã rẽ gần nhất còn nhánh chưa thử, TRỪ KHI lượt
  này đã chạm thị trường; đã bắn lệnh ra thì quay lui là đẻ lệnh thứ hai;
- **cổng luôn tính đủ mọi điều kiện**, không ngắt ở cái sai đầu tiên — nếu ngắt thì nhật
  ký vĩnh viễn không trả lời được "ba điều kiện kia lúc đó thế nào";
- **biên dịch trước** — mọi tên → chỉ số cột, chạy xong không đụng một chuỗi nào; và mọi
  lỗi "toán hạng chưa hỗ trợ" nổ ra kèm nhãn khối `[3A.1]` chứ không nổ ở nến 40.000;
- **một `mot_nhip` dùng chung** cho backtest lẫn live — "test như nào thì live như thế"
  thành chuyện của kiến trúc chứ không phải của kỷ luật.

Bốn điều trên không dính sàn nào. Chép lại được gần nguyên văn.

---

## 5. Cửa sổ Strategy Tester

**Nằm ở đâu** — không còn. `webui/src/main.tsx` cũng đã bỏ nhánh rẽ `?tester=1`.

**Trước cắm gì** — `webui/src/tester/` (2.033 dòng) + `api.ApiTester` (~720): `Chart`
(nến + hộp zone), `BangSoLieu`, `ThongKe` (bội R, drawdown), `Journey`, `LichSu`,
`BangDuoi`, `NutChart`.

**Phải cắm gì** — chưa quyết, và cố ý chưa. Màn hình của market maker không dùng chung
một dòng nào với chart nến: thang báo giá hai bên, tồn kho theo thời gian, khoảng cách
quote tới mid, và chất lượng khớp (bị chọn ngược bao nhiêu lần).

---

## 6. Cửa sổ Live

**Nằm ở đâu** — không còn.

**Trước cắm gì** — `webui/src/live/` (822 dòng) + `api.ApiLive` (~485).

**Phải cắm gì** — ý tưởng `CongChot` đáng dựng lại nguyên vẹn: **hộp chốt nằm TRONG cửa
sổ Live, không đóng được bằng ✕ hay Esc**, vì đó là cửa duy nhất giữa một sơ đồ đang vẽ
dở và một kết nối tiêu tiền thật. Không có đường tắt — đường tắt là thứ người ta dùng
đúng lúc vội, mà vội là lúc dễ sai nhất.

---

## 7. Soi một lượt trên sơ đồ

**Nằm ở đâu** — `webui/src/App.tsx`, chỗ khối `SOI MỘT LƯỢT` từng đứng (giờ là chú
thích). Đường ống còn sống nửa dưới: `api.Api._ban` và `window.__su_kien` trong
`api.ts` đều giữ lại, hiện không ai gọi.

**Trước cắm gì** — chuột phải một dòng nhật ký ở cửa sổ tester → cửa sổ vẽ nhảy lên
trước, tô đúng đường lượt đó đã đi, mờ phần còn lại, kèm dấu đạt/trượt trên **từng
dòng** điều kiện.

**Phải cắm gì** — chính nó, khi có bộ chạy mới nhả ra cùng hình dạng (`duong` · `cong` ·
`ve`). Ba cái bẫy đã trả giá, đừng gặp lại: kẹp `soi.tab === tab` ở **nơi tiêu thụ** chứ
đừng rải `setSoi(null)` khắp nơi; chỉ tô từng dòng khi **số dòng còn khớp**; phải có dải
nổi + nút ✕ chứ không chỉ phím Esc.

Lớp CSS của nó (`soi-chay` · `soi-truot` · `soi-mo` · `dk-dat` · `dk-truot`) đã đi ở
đợt 4.

---

## 8. Điều kiện chạy trong Cài đặt

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

## 9. Nợ độ phủ — KHÔNG phải ổ cắm, nhưng phải trả

Bộ test đi từ **4.213 dòng xuống 663**, và phần lớn là đúng — một bài kiểm không còn
đối tượng thì là rác, không phải độ phủ. Nhưng **ba nhóm dưới đây kiểm CƠ CHẾ chứ không
kiểm D_02**, nên chúng là nợ thật, phải trả khi cơ chế tương ứng quay lại:

| Bài kiểm đã mất | Kiểm CƠ CHẾ gì |
|---|---|
| `test_nhat_ky.py` (478) | bản ghi rỗng chữ · lưu id không lưu nhãn · ghi/đọc ngược không mất gì |
| `test_dat_ten.py` (333) + mục 4 `test_kho_va_lenh.py` (~60) | số gõ tay hai chỗ → cảnh báo · bỏ tham số đang dùng → lỗi · khai tham số thừa → cảnh báo |
| `test_bo_chay.py` (425) | thứ tự trong một nhịp · **luật lùi** · tính XÁC ĐỊNH (chạy lại ra kết quả y hệt) |
| 5 mục cuối `test_danh_so.py` (~160) | mô tả hành động đọc được · soát thiếu SL / thiếu mốc neo · cơ chế "so hai đại lượng" |

Còn lại **4 bài, 663 dòng**, phủ đúng thứ đang tồn tại: đánh số phân cấp · ghim số ⟲ ·
luật rẽ nhánh · ranh giới Entry/Manage · cơ chế kho · lưu trữ · biến CSS ma · ô số.

Giữ một `bo_chay` rỗng ruột chỉ để nuôi fixture thì đuôi vẫy được cả con chó — nên
chúng đi. Nhưng đây là **nợ**, không phải dọn xong: có bộ chạy mới thì viết lại ngay.

---

## 10. Kho toán hạng

**Nằm ở đâu** — `cat_studio/kho/__init__.py`, `MODULE = []`.

**Trước cắm gì** — ba module (312 dòng): `nen_tang` (giá · thời gian · tài khoản ·
"lệnh này"), `chi_bao` (ATR · MA, tính thẳng từ nến), `engine_d02` (bảng vùng nén và
máy nuôi nó).

**Phải cắm gì** — cơ chế ở lại nguyên vẹn, chỉ thiếu nội dung: thả một module vào
`MODULE` là hộp thoại Kho, dropdown toán hạng và `api.bootstrap` có ngay. Một market
maker cần ít nhất `bid` · `ask` · `mid` · `spread` · **tồn kho CÓ DẤU** · tuổi quote ·
lệch giá quote so với mid, cộng biến động thực và nhịp tick.

> Phép `_soat_trung` là thứ đáng giữ nhất ở đây: hai engine cùng khai `atr` với hai
> nghĩa khác nhau thì mọi chiến lược dùng nó đều sai mà **không báo gì**. Nó nổ ngay
> lúc import, không đợi tới lúc chạy.

---

## 11. Từ vựng của khối hành động

**Nằm ở đâu** — `core.py`, khối `# ---- TỪ VỰNG — Ổ CẮM TRỐNG`. Phía giao diện:
`ActionDialog.tsx` (735 → 120 dòng) và `Bootstrap` trong `types.ts`.

**Trước cắm gì** — 17 toán hạng · 8 phép so (`< ≤ > ≥ = ≠` · `là ĐÚNG` / `là SAI`) ·
6 đơn vị (`giá` · `bps` · `× ATR` · `× ATR zone` · `× R` · `mép zone đối diện`) cùng
mười bảng phụ · mốc neo · loại lệnh · 4 chế độ sửa · **bảng tham số** (hằng số CÓ TÊN
+ cảnh báo "số gõ tay hai chỗ" + nút đặt tên) · khung thời gian và nhịp M5/M1.

**Phải cắm gì** — thước của market maker, không phải thước cũ đổi tên:

| bỏ | thay bằng |
|---|---|
| `× ATR` · `× ATR zone` | `× spread` — bội của spread hiện tại |
| `× R` (rủi ro theo SL) | tồn kho, vì SL từng lệnh không còn là trục rủi ro |
| khung nến M1…MN1 | cửa sổ tick / mili-giây |
| mốc neo `zone_HH` · `zone_LL` | `mid` · `bid` · `ask` · microprice |
| loại lệnh `Chờ Stop` | **`Limit`** — và đệm phải ĐẢO DẤU: lùi vào trong, không nhô ra |
| chế độ sửa `dời SL` · `hoà vốn` | **`dời giá`** (requote) — động tác thường xuyên nhất |

**Còn lại ba thứ, và chúng là NGỮ PHÁP chứ không phải từ vựng** — đã đứng vững qua cả
D_02 lẫn MT5 và sẽ đứng tiếp: ba động từ `check_cond` · `vao_lenh` · `sua_lenh`; ranh
giới **Entry chỉ TẠO · Manage chỉ SỬA**; và hai phía **Mua · Bán**.

---

## 12. Sổ lệnh

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

## 13. Nhật ký và lịch sử

**Nằm ở đâu** — không còn file nào. Thư mục `du_lieu/nhat_ky/` vẫn được liệt kê trong
hộp thoại Kho nhưng KHÔNG AI GHI vào nữa.

**Trước cắm gì** — `nhat_ky.py` (283) và `lich_su.py` (197). Cả hai nhận thẳng
`bo_chay.KetQua` với `.nen1` / `.nen5` — kiểu tham số của chúng đã không còn tồn tại,
nên chúng không phải "mồ côi" mà là **không chạy được**.

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

## 14. Nhật ký thiết kế đã cắt khỏi `core.md`

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

## Xong phần dọn — việc còn lại

**Bốn đợt đã xong. Lần dọn kết thúc ở đây.**

Repo giờ là một trình soạn thảo sơ đồ sạch: vẽ · nối · đánh số · ghim số ⟲ · soát cấu
trúc · lưu/mở. Khối mang TÊN · ĐỘNG TỪ · (với `Vào lệnh`) HƯỚNG. Không còn một dòng mã,
một lớp CSS, một icon, một biến theme hay một đoạn tài liệu nào mô tả thứ không tồn tại.

Việc tiếp theo **không phải dọn nữa mà là chọn sàn** — mọi ổ cắm trong sổ này đều chờ
đúng một quyết định đó. Cắm theo thứ tự phụ thuộc: nguồn dữ liệu (§1) → kết nối sàn
(§2) → mô hình khớp (§3) → bộ chạy (§4) → kho toán hạng (§10) → từ vựng (§11) → sổ lệnh
(§12) → nhật ký (§13) → hai cửa sổ (§5, §6) → soi lượt (§7) → cài đặt (§8).

Mỗi ổ cắm xong thì **xoá khỏi sổ này**, không đánh dấu ✔. Sổ cạn tới rỗng là xong.
