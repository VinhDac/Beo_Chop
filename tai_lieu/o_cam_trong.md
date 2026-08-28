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

## 1. Nguồn dữ liệu

**Nằm ở đâu** — không còn file nào. `cat_studio/__init__.py` liệt kê chỗ trống trong
bản đồ module.

**Trước cắm gì** — `nguon_nen.py` (527 dòng): kéo nến M1 từ MT5 theo lô 30 ngày, cất
`.npy` 48 byte/nến, luật **một dải liền** (chọn khoảng rời thì tải luôn phần ở giữa),
`khoang_thieu()` + `uoc_tinh()` để không bao giờ tải lén, ghi nguyên tử chống file cụt.

**Phải cắm gì** — nguồn tick, không phải nến. Ba cái bẫy đã trả giá để biết và sẽ gặp
lại ở bất kỳ sàn nào — đọc docstring cũ trước khi viết:

- thời gian là **giờ SERVER**, đừng "sửa cho đúng UTC";
- xin một dải dài một phát thì API có thể trả **thiếu mà không báo lỗi** — phải chia lô;
- dữ liệu thật **đầy lỗ hổng**; gộp theo biên thời gian tuyệt đối, không đếm phần tử.

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

Lớp CSS `soi-chay` · `soi-truot` · `soi-mo` · `dk-dat` · `dk-truot` vẫn nằm trong
`app.css`, hiện không ai dùng — đợt 4 quyết giữ hay bỏ.

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

Ba module **còn sống** mà giờ không có bài kiểm nào, vì bài kiểm của chúng dựng fixture
bằng `bo_chay.chay()`:

| Module còn sống | Bài kiểm đã mất | Kiểm cái gì |
|---|---|---|
| `nhat_ky.py` | `test_nhat_ky.py` (478) | bản ghi rỗng chữ · lưu id không lưu nhãn · ghi/đọc ngược không mất gì |
| bảng tham số (`core.py`) | `test_dat_ten.py` (333) | số gõ tay hai chỗ → cảnh báo + nút đặt tên |
| bảng tham số (`core.py`) | mục 4 của `test_kho_va_lenh.py` (~60) | bỏ tham số đang dùng → lỗi · khai tham số thừa → cảnh báo |

Giữ một `bo_chay` rỗng ruột chỉ để nuôi fixture thì đuôi vẫy được cả con chó — nên
chúng đi. Nhưng đây là **nợ**, không phải dọn xong: có bộ chạy mới thì viết lại ngay.

---

## Đợt sau sẽ thêm vào đây

Đợt 3 gỡ tiếp **từ vựng**: ruột `kho/` (`nen_tang` · `chi_bao` · `engine_d02`), bảng đơn
vị trong `core.py` (`atr` · `atr_zone` · `bien_zone` · `R`), `MOC_ENTRY`, `LOAI_LENH`,
`SUA_CHE_DO`, và `so_lenh.Zone`. Cùng lúc phải quyết số phận `nhat_ky.py` / `lich_su.py`
— hai module mồ côi vẫn mang hình dạng dữ liệu của bộ chạy theo nến.

Mỗi thứ gỡ xong thêm một mục vào sổ này **ngay trong đợt đó**, không để dồn: đúng cái
không được ghi ngay là cái sẽ không bao giờ được ghi.
