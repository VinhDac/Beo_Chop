# Soát cả tập ví dụ — vẽ lại được bao nhiêu

Soát ngày **18/10/2026**. Thư mục `tai_lieu/chiến thuật ví dụ/` có **11 tệp**
(vd1 → vd11), tổng **2.978 dòng** — không phải 12.

Mỗi dòng dưới đây là một lần CHẠY THẬT, không phải đọc mã rồi đoán.

---

## Bảng kết quả

| | dòng | vẽ được | chạy thật | lệnh khớp | chặn ở đâu |
|---|---|---|---|---|---|
| **vd1** Nasdaq Bollinger Pullback | 437 | ✅ 10/13 yêu cầu | ✅ | **29** | trần cứng 10 vị thế |
| **vd2** OmniFund Macro Sovereign | 98 | ✅ | ✅ | **63** | bộ dữ liệu thiếu GLD, XLE |
| **vd3** AI Basket | 59 | ✅ | ✅ | **2** | bộ dữ liệu thiếu 7/8 mã |
| **vd4** Short Term Reversal | 34 | ❌ | — | — | **thiếu 2 tệp** mã nguồn |
| **vd5** Hierarchical Risk Parity | 116 | ❌ | — | — | toán ma trận (scipy) |
| **vd6** Solana Adaptive | 42 | ✅ | ✅ | **0** | không có dữ liệu SOLUSD |
| **vd7** Top12 US Market Cap | 463 | ❌ | — | — | xếp hạng chéo mã · điểm nhiều thành phần · nhớ qua nến |
| **vd8** PCA Stat Arbitrage | 71 | ❌ | — | — | toán ma trận (sklearn) |
| **vd9** *(gần trùng vd7)* | 466 | ❌ | — | — | như vd7 |
| **vd10** Growth V3 | 901 | ❌ | — | — | như vd7 + rổ doanh nghiệp + phí/trượt giá |
| **vd11** Sector Rotation V31 | 299 | ❌ | — | — | điểm nhiều thành phần · nhớ qua nến |

**4 vẽ được · 7 chưa.**

---

## Bốn ví dụ vẽ được — và cả bốn đều bị DỮ LIỆU chặn, không phải bị VẼ chặn

Đây là chỗ đáng chú ý nhất của lần soát này. Cả bốn ví dụ vẽ được đều sinh ra mã
đúng và chạy hết lượt; con số lệnh thấp **không** phải vì sơ đồ nói sai, mà vì bộ
dữ liệu miễn phí kèm LEAN không có mã ấy. LEAN nói thẳng điều đó ra tệp
`failed-data-requests-*.txt` trong thư mục kết quả:

* **vd2** — `\equity\usa\daily\xle.zip`, `\equity\usa\daily\gld.zip` đều không có.
  Nên 63 lệnh đều là QQQ. Ba nhánh chia 40/35/20 vẫn chạy đúng, chỉ là hai trong
  ba mã không tồn tại để mà mua.
* **vd3** — thiếu NVDA, AMD, TSM, AVGO, MSFT, META, PLTR. Còn đúng GOOGL, nên 2 lệnh.
* **vd6** — không có SOLUSD. Mã sinh ra đúng (`add_crypto('SOLUSD', Resolution.HOUR)`,
  hai EMA, `set_warm_up(100)`), chạy xong, 0 lệnh.

Nói cách khác: với bốn ví dụ này, việc của app đã xong. Muốn thấy số thật thì phải
có dữ liệu thật — tải thêm từ QuantConnect, chứ không sửa gì trong app.

**vd1** là ngoại lệ duy nhất có chặn thật: 10/13 yêu cầu vẽ được, cái thứ 11 —
"giữ tối đa 10 vị thế" — không có model LEAN nào làm. Đã đọc hết 10 model chia vốn
và 5 model phòng rủi ro để chắc chuyện đó.

---

## Bảy ví dụ chưa được — và tường chắn thật là gì

### vd4 — không phải lỗ hổng, là thiếu tệp

34 dòng của vd4 chỉ là phần vỏ. Bộ não của nó nằm trong hai tệp nó `import`:

```python
from alpha import ShortTermReversalAlphaModel
from universe import MostLiquidFundamentalUniverseSelectionModel
```

Hai tệp `alpha.py` và `universe.py` **không có trong thư mục**. Không ai dựng lại
được vd4 từ những gì đang có — kể cả viết tay. Cần copy thêm hai tệp ấy.

### vd5 và vd8 — thật sự cần thư viện toán ngoài

Hai ví dụ này là hai ví dụ DUY NHẤT trong cả tập làm toán mà LEAN không có sẵn:

* vd5: ma trận tương quan → ma trận khoảng cách → phân cụm tầng (`scipy.cluster.hierarchy`)
  → chia vốn đệ quy theo cụm.
* vd8: phân tích thành phần chính (`sklearn.decomposition.PCA`) → hồi quy OLS
  (`statsmodels`) → z-score của phần dư.

Đây không phải chỉ báo viết lại bằng tay. Đây là toán ma trận trên cả rổ cùng lúc.
Vẽ nó bằng khối thì phải có một khối "chạy đoạn Python của tôi" — và cái đó là đi
ngược D-11, vì nó mở cửa cho bộ máy tính toán thứ hai nằm trong app.

### vd7 · vd9 · vd10 · vd11 — ba lỗ hổng, không phải 3.000 dòng toán

Bốn ví dụ này dài 2.129 dòng, nhìn thì tưởng vô vọng. Nhưng bóc ra thì **phần lớn
số dòng ấy là chỉ báo LEAN viết lại bằng tay** — thứ kho khối đã có từ lâu:

| Mã gốc viết tay | LEAN đã có | kho khối |
|---|---|---|
| `vd11:137` `np.mean(spy_closes[-200:])` | `self.sma(sym, 200)` | ✅ SMA |
| `vd11:184-192` `np.diff` → `gains/losses` → `100 - 100/(1+rs)` | `self.rsi(sym, n)` | ✅ RSI |
| `vd7:404` `sum(closes[-n:]) / n` | `self.sma(sym, n)` | ✅ SMA |
| `vd7:396-398` `c0 / c63 - 1` | `self.roc(sym, 63)` | ✅ ROC |
| `vd10:762` `np.mean([px[-1]/px[-lb-1]-1 …])` | trung bình mấy `roc` | ✅ ROC |
| `vd7:422` `sqrt(var) * sqrt(252)` | `STD(n).Of(LOGR(1))` × √252 | ⚠ xem dưới |
| `vd10:688` `px.pct_change()[-20:].std()` | `STD(20).Of(LOGR(1))` | ⚠ xem dưới |

### ⚠ Một chỗ tôi đã nói quá, nay nói lại cho đúng

Tôi từng bảo *"nghịch đảo biến động đã vẽ được"* — `trọng số = 1 / Độ lệch chuẩn(60)`.
**Không đúng hẳn.** Từ điển của ta khai `self.std(sym, n)` với đơn vị là **giá**,
và khai thế là thật: LEAN cho `StandardDeviation` ăn **giá đóng**, nên nó là độ lệch
chuẩn của GIÁ, không phải của lợi suất.

Khác nhau thế nào: một mã $500 và một mã $50 biến động y hệt **10%/năm** thì mã $500
có độ lệch chuẩn giá to gấp mười. Chia vốn theo `1 / std(giá)` là dồn vốn vào mã GIÁ
THẤP, không phải vào mã ÍT BIẾN ĐỘNG.

Biến động thật thì LEAN có đủ mảnh: `LOGR(1)` ra log-lợi-suất, `STD(n)` ra độ lệch
chuẩn, và `IndicatorExtensions.Of` nối cái sau vào cái trước. Nhưng kho khối **không
có cách nói "chỉ báo của chỉ báo"** — ghép đại lượng chỉ ghép hai đại lượng bằng
`+ − × ÷`, không lồng chỉ báo vào nhau. Đó là lỗ hổng thứ **4** bên dưới.

Bản vá thẻ ở `13d9d30` vẫn đúng và vẫn cần: thẻ phải nói ra trọng số có ghép, kể cả
khi phần gốc bằng 1. Chỉ cái tên tôi đặt cho nó là sai.

---

Bỏ hết phần viết lại ấy đi thì còn lại đúng **bốn** thứ app chưa nói nổi:

---

## Bốn lỗ hổng thật, xếp theo số ví dụ cần

### 1 · XẾP HẠNG CHÉO MÃ — 5 ví dụ cần (vd4, vd7, vd9, vd10, vd11)

Lỗ hổng lớn nhất. Mọi khối hiện nay chỉ biết xét **một** mã: "mã này RSI < 30 à?".
Không khối nào so mã này với mã khác, nên không nói được câu
*"chấm điểm cả rổ rồi lấy 12 mã cao nhất"*.

Đã lách được một nửa: **xếp hạng theo tỷ lệ thì được** — cho `InsightWeightingPortfolioConstructionModel`
một trọng số là điểm, LEAN tự so trọng số của mọi mã rồi chia vốn theo tỷ lệ.
vd1 đang chạy đúng kiểu ấy. Nhưng **trần cứng "chỉ lấy N mã" thì không** — LEAN chia
cho tất cả mã có tín hiệu, không cắt ở mã thứ 12.

vd2 lách bằng cách khác, và nó cho thấy giới hạn rõ nhất: nó cần sắp xếp 3 ngành,
nên **vẽ hẳn 6 nhánh** cho 6 thứ tự có thể. 3 ngành thì 6 nhánh còn vẽ được.
vd7 xếp hạng ~100 mã. Không vẽ được bằng nhánh.

### 2 · ĐIỂM NHIỀU THÀNH PHẦN — 4 ví dụ cần (vd7, vd9, vd10, vd11)

vd7 chấm điểm mỗi mã thế này (`vd7:407`):

```python
score = (0.25 * r63) + (0.35 * r126) + (0.40 * r252) - (0.20 * ann_vol)
```

Bốn đại lượng, bốn trọng số. Ghép đại lượng hiện nay chỉ **một tầng, hai vế**
(`a / b`, `a * b`…) — đủ cho "giá / đỉnh 60 nến" của vd1, không đủ cho câu trên.
Giới hạn ấy là cố ý (xem `_ve_py` trong `sinh_ma.py`): cây biểu thức lồng nhau thì
hàng điều kiện lại thành một ô gõ công thức, mất cái sạch của ba ô.

### 3 · NHỚ QUA CÁC NẾN — 3 ví dụ cần (vd7, vd9, vd11)

Sơ đồ hiện nay không nhớ gì giữa hai nhịp: mỗi nhịp xét lại từ đầu. vd11 nhớ **bảy**
thứ (`vd11:59-65`):

```
held_signal · held_trade · is_leveraged · peak_price · last_top
waiting_for_pullback · market_force_cash_active
```

Vì nó không phải sơ đồ nếu-thì, nó là một **máy trạng thái**: "đang giữ đòn bẩy 3x,
giá đã rụng 25% từ đỉnh của chính nó → hạ về 1x", "vừa bán xong thì chờ RSI tụt
dưới 40 mới vào lại". Câu "từ đỉnh của chính nó" và "vừa bán xong" là hai câu cần nhớ.
vd7/vd9 nhẹ hơn: chỉ cần "mã này vừa bị bán, nghỉ 5 ngày" và "đỉnh vốn cao nhất từ
đầu lượt".

### 4 · CHỈ BÁO CỦA CHỈ BÁO — 3 ví dụ cần (vd7, vd9, vd10)

LEAN có `IndicatorExtensions.Of`: nối đầu ra chỉ báo này vào đầu vào chỉ báo kia.
Nhờ nó mà **biến động thật** nói được bằng một câu LEAN duy nhất:

```python
IndicatorExtensions.of(self.std(sym, 20), self.logr(sym, 1))   # × sqrt(252) là ra vol năm
```

Kho khối không có cách nói câu ấy. Hàng điều kiện ghép được hai ĐẠI LƯỢNG bằng
`+ − × ÷`, nhưng không lồng chỉ báo nọ vào chỉ báo kia. Nên "độ lệch chuẩn của
lợi suất" — thứ cả ba ví dụ dùng để đo rủi ro — hiện chỉ nói được thành "độ lệch
chuẩn của GIÁ", là một đại lượng khác.

Đây là lỗ hổng **rẻ nhất** trong bốn cái: nó không cần khối mới, không cần bộ nhớ,
chỉ cần ô «đại lượng» cho chọn thêm một chỉ báo làm NGUỒN thay vì giá đóng.

---

## Hai lỗ hổng nhỏ hơn, đã biết từ trước

* **Rổ theo chỉ số doanh nghiệp** (`FineFundamentalUniverseSelectionModel`) — vd4,
  vd7, vd9, vd10 cần. Nhưng bộ dữ liệu miễn phí cũng không có chỉ số doanh nghiệp,
  nên `HOI_DOANH_NGHIEP` đang khai `tat` là đúng. Mở ô này ra mà không có dữ liệu thì
  người dùng chọn xong chạy ra rổ rỗng.
* **Phí và trượt giá** (`ConstantFeeModel`, `ConstantSlippageModel`,
  `InteractiveBrokersFeeModel`) — vd3, vd10 cần. Ô «Sàn» ở khối Bắt đầu đã quyết
  phí/trượt giá theo kiểu sàn; đặt riêng từng model thì chưa.

---

## Kết

Lý thuyết **chưa** xử lý hết. Nhưng khoảng cách nhỏ hơn con số 7/11 gợi ra:

* 1 ví dụ (vd4) không phải lỗ hổng — thiếu tệp.
* 2 ví dụ (vd5, vd8) cần toán ma trận, và đó là chỗ nên dừng: làm nó là mở cửa cho
  bộ máy tính toán thứ hai, trái D-11.
* 4 ví dụ còn lại (vd7, vd9, vd10, vd11) chặn ở đúng **ba** lỗ hổng trên — và lỗ
  hổng số 1 (xếp hạng chéo mã) một mình gỡ được phần lõi của cả bốn.
