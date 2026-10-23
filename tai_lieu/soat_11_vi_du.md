# Soát cả tập ví dụ — vẽ lại được bao nhiêu

Soát ngày **18/10/2026**. Thư mục `tai_lieu/chiến thuật ví dụ/` có **11 tệp**
(vd1 → vd11), tổng **2.978 dòng** — không phải 12.

Mỗi dòng dưới đây là một lần CHẠY THẬT, không phải đọc mã rồi đoán.

---

## Bảng kết quả — soát lại 18/10/2026 CHIỀU, sau khi bày hết kệ LEAN

Sáng nay 4 trên 11 vẽ được. Sau khi bày hết kệ LEAN (136 món) và chữa hai lỗi mà
chính việc dựng lại lôi ra, con số là **9 trên 11**. Mỗi dòng là một lượt chạy thật.

| | vẽ được | chạy | lệnh khớp | còn phải bỏ gì |
|---|---|---|---|---|
| **vd1** Nasdaq Bollinger | ✅ 10/13 | ✅ | **30** | trần cứng 10 vị thế |
| **vd2** OmniFund Macro | ✅ | ✅ | **63** | — *(thiếu GLD · XLE)* |
| **vd3** AI Basket | ✅ | ✅ | **2** | — *(thiếu 7/8 mã)* |
| **vd4** Short Term Reversal | ❌ | — | — | **thiếu 2 tệp mã nguồn** |
| **vd5** Crypto Reserve | ✅ phần chính | ✅ | **389** | rổ crypto ĐỘNG |
| **vd6** Solana Adaptive | ✅ | ✅ | **0** | — *(không có SOLUSD)* |
| **vd7** Top12 US Market Cap | ✅ phần chính | ✅ | **435** | điểm 4 thành phần |
| **vd8** PCA Stat Arbitrage | ❌ | — | — | **PCA — LEAN không có** |
| **vd9** *(gần trùng vd7)* | ✅ phần chính | ✅ | **424** | như vd7 |
| **vd10** Growth V3 | ✅ phần chính | ✅ | **449** | hai chiến thuật con · trạng thái |
| **vd11** Sector Rotation | ✅ phần chính | ✅ | **122** | máy trạng thái 7 biến |

«Phần chính» nghĩa là: cùng rổ, cùng nhịp, cùng lối chia vốn, cùng cách phòng rủi ro
— chỉ thiếu đúng mấy thứ ghi ở cột cuối. Không phải «na ná», mà là cùng hình trừ đi
một chỗ gọi được tên.

### Mấy thứ đổi được nhờ bày hết kệ

| bản gốc viết tay | nay vẽ bằng |
|---|---|
| vd5 — HRP: 70 dòng scipy phân cụm tầng | `RiskParityPortfolioConstructionModel` |
| vd7 · vd9 — `_inv_vol_weights`: 40 dòng | `RiskParityPortfolioConstructionModel` |
| vd7 · vd9 — đỉnh vốn, cooldown | `TrailingStop` · `MaximumDrawdownPercentPortfolio` |
| vd10 — tối ưu tỷ trọng | `MeanVarianceOptimizationPortfolioConstructionModel` |
| vd10 — phí IB, trượt giá cố định | ô «Phí» · ô «Trượt giá» |
| vd3 · vd5 · vd10 — cân lại theo tháng | nhịp THÁNG × quy tắc giờ |
| vd11 — xếp hạng ngành | trọng số = `ROC(252)` + `InsightWeighting` |

### Và việc dựng lại lôi ra hai lỗi THẬT

Đây mới là giá trị chính của việc vẽ lại — không phải để khoe con số, mà để lòi ra
chỗ hỏng:

1. **Vẽ «Giá mua (bid)» là backtest ĐỨT.** `data.quote_bars[sym]` ném
   `KeyNotFoundException` vì bộ miễn phí không có nến báo giá cho cổ phiếu. Chữa:
   đọc qua `securities[sym].bid_price`, LEAN tự rơi về giá đóng.
2. **`RiskParity` + nhịp HẸN GIỜ = ĐỨT.** Làm nóng chỉ đếm chu kỳ chỉ báo, nên sơ đồ
   không chỉ báo nào thì không làm nóng gì, và model đọc 252 nến lịch sử chạy ngay
   nến đầu. Chữa: mỗi model chia vốn khai số nến nó đòi, làm nóng lấy `max` hai
   nguồn.

Cả hai đều nằm im từ ngày viết, vì không ví dụ nào trong tập mẫu đi qua đúng chỗ ấy.

---

---|---|---|---|---|---|
| **vd1** Nasdaq Bollinger Pullback | 437 | ✅ 10/13 yêu cầu | ✅ | **29** | trần cứng 10 vị thế — *LEAN có, chưa bày* |
| **vd2** OmniFund Macro Sovereign | 98 | ✅ | ✅ | **63** | bộ dữ liệu thiếu GLD, XLE |
| **vd3** AI Basket | 59 | ✅ | ✅ | **2** | bộ dữ liệu thiếu 7/8 mã |
| **vd4** Short Term Reversal | 34 | ❌ | — | — | **thiếu 2 tệp** mã nguồn |
| **vd5** Hierarchical Risk Parity | 116 | ❌ | — | — | *LEAN có 3 model làm hộ, chưa bày* |
| **vd6** Solana Adaptive | 42 | ✅ | ✅ | **0** | không có dữ liệu SOLUSD |
| **vd7** Top12 US Market Cap | 463 | ❌ | — | — | xếp hạng chéo mã · điểm nhiều thành phần — *cả hai LEAN đều có* |
| **vd8** PCA Stat Arbitrage | 71 | ❌ | — | — | **PCA — LEAN không có. Chỗ duy nhất nên dừng** |
| **vd9** *(gần trùng vd7)* | 466 | ❌ | — | — | như vd7 |
| **vd10** Growth V3 | 901 | ❌ | — | — | như vd7 + rổ doanh nghiệp + phí/trượt giá |
| **vd11** Sector Rotation V31 | 299 | ❌ | — | — | **máy trạng thái — LEAN không có khái niệm ấy** |

**4 vẽ được · 7 chưa** — nhưng 5 trong 7 chặn ở model **LEAN đã làm xong mà app
chưa bày ra**, không phải ở thuật toán ta còn phải viết. Xem mục cuối.

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

### vd5 — LEAN có làm hộ, ta chưa bày ra

Lần soát đầu tôi xếp vd5 vào "cần scipy, nên dừng". **Xếp sai.** vd5 làm: ma trận
tương quan → ma trận khoảng cách → phân cụm tầng → chia vốn đệ quy theo cụm, tức
*chia vốn sao cho mỗi tài sản gánh rủi ro bằng nhau*.

LEAN có sẵn đúng việc ấy, ba model, không cần một dòng toán nào của ta:

* `RiskParityPortfolioConstructionModel` — "equalize the risk carried by each asset".
  LEAN tự lấy history, tự tính biến động, tự ra trọng số.
* `MeanVarianceOptimizationPortfolioConstructionModel` — ma trận hiệp phương sai.
* `BlackLittermanOptimizationPortfolioConstructionModel`.

**Cả ba đều chưa được bày trong app.** Xem mục "Ta mới bày một nửa LEAN" ở cuối.

### vd8 — cái duy nhất thật sự cần thư viện ngoài

vd8 làm phân tích thành phần chính (`sklearn.decomposition.PCA`) → hồi quy OLS
(`statsmodels`) → z-score của phần dư. LEAN không có PCA. Vẽ nó thì phải có một khối
"chạy đoạn Python của tôi", và cái đó đi ngược D-11: mở cửa cho bộ máy tính toán thứ
hai nằm trong app. **Đây là chỗ nên dừng, và là chỗ DUY NHẤT nên dừng.**

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

**Nhưng LEAN có trần cứng ấy — ở tầng RỔ, không phải tầng chia vốn.**
`EmaCrossUniverseSelectionModel` nhận một tham số `count`: xếp hạng rồi lấy đúng N mã.
`CoarseFundamentalUniverseSelectionModel` cũng vậy. Tức câu "chỉ giữ 12 mã tốt nhất"
đúng ra phải nói ở ô **Rổ** của khối Bắt đầu, chứ không phải ở khối chia vốn — và đó
là chỗ tôi tìm sai suốt lần soát đầu. Không cần viết thuật toán nào; cần một ô.

### 2 · ĐIỂM NHIỀU THÀNH PHẦN — 4 ví dụ cần (vd7, vd9, vd10, vd11)

vd7 chấm điểm mỗi mã thế này (`vd7:407`):

```python
score = (0.25 * r63) + (0.35 * r126) + (0.40 * r252) - (0.20 * ann_vol)
```

Bốn đại lượng, bốn trọng số. Ghép đại lượng hiện nay chỉ **một tầng, hai vế**
(`a / b`, `a * b`…) — đủ cho "giá / đỉnh 60 nến" của vd1, không đủ cho câu trên.
Giới hạn ấy là cố ý (xem `_ve_py` trong `sinh_ma.py`): cây biểu thức lồng nhau thì
hàng điều kiện lại thành một ô gõ công thức, mất cái sạch của ba ô.

### 3 · NHỚ QUA CÁC NẾN — 1 ví dụ cần (vd11), không phải 3

Lần soát đầu tôi tính lỗ hổng này cho cả vd7, vd9, vd11. **Tính thừa hai.** Hai thứ
cần nhớ thường gặp nhất thì LEAN có model riêng, và **app đã bày cả hai rồi**:

* "giá rụng N% khỏi đỉnh của chính nó → bán" = `TrailingStopRiskManagementModel` ✅ đã bày
* "đỉnh vốn cao nhất từ đầu lượt" = `MaximumDrawdownPercentPortfolio` ✅ đã bày

Nên phần nhớ của vd7/vd9 (nghỉ 5 ngày sau khi bán, đỉnh vốn) **vẽ được**, chỉ cần
đổi cách nói: "nghỉ 5 ngày" thì dùng hạn của tín hiệu thay vì tự đếm ngày.

Còn lại một mình vd11. Nó nhớ **bảy** thứ (`vd11:59-65`):

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

## Ta từng mới bày một nửa LEAN — nay đã bày hết

Câu hỏi đúng không phải "còn thiếu tính năng gì", mà **"LEAN có sẵn những gì mà app
chưa bày ra"**. Đếm lần đầu (18/10/2026 sáng): app bày **18** trong khoảng 40 món của
năm bảng Framework, và **21** trong 122 chỉ báo.

Sau một buổi bày thêm:

| bảng | LEAN có | app bày | khai rõ lý do bỏ | THIẾU |
|---|---|---|---|---|
| Chỉ báo | 122 | **105** | 17 | **0** |
| Rổ (Universe) | 23 | **10** | 13 | **0** |
| Chia vốn | 11 | **8** | 3 | **0** |
| Phát tín hiệu (Alpha) | 9 | **6** | 3 | **0** |
| Phòng rủi ro | 7 | **4** | 3 | **0** |
| Đặt lệnh | 5 | **3** | 2 | **0** |
| | **177** | **136** | **41** | **0** |

41 món không bày đều có LÝ DO VIẾT BẰNG CHỮ, mỗi cái một dòng — Greeks quyền chọn
(không có dữ liệu), chỉ báo nhận hai mã (một đại lượng chỉ mang một ô mã), model đòi
hàm lọc Python (trái D-11), lớp nền, và mấy thứ cần dữ liệu trả tiền. Bài
`tests/test_du_lean.py` canh cả hai chiều: thiếu mà không khai lý do là ĐỎ, mà khai
lý do cho một món LEAN không còn có — hay món app đã bày — cũng ĐỎ.

### Mấy thứ lòi ra khi gọi THẬT cả 105 chỉ báo

Cổng chỉ ĐẾM tham số, nên nó bắt được «khai 2 mà LEAN cần 3». Ba thứ dưới đây chỉ nổ
lúc chạy, và lượt chạy thật thấy cả ba:

* `T3` tên Python là **`t_3`**, không phải `t3`. (Hỏi chính LEAN bằng `hasattr`:
  trong 125 tên, chỉ 2 cái khác `lower()` — `t_3` và `heikin_ashi`.)
* **Năm chỉ báo không gọi nổi nếu không truyền độ phân giải**: `SI` `ASI` `RDV` `TP`
  `VP` khai `Resolution? resolution = Resolution.Daily` — tham số nullable có mặc
  định khác null — và pythonnet không dựng nổi mặc định ấy.
* **Donchian Channel không có dải giữa**, và lỗi này có TỪ TRƯỚC: bản cũ chép danh
  sách đường của Bollinger sang. Ai chọn «Dải giữa» là backtest nổ ngay nến đầu.

---

## Ba chỗ bí cuối — và cái nào cũng là VỎ, không phải thuật toán

Soát xong còn ba thứ sơ đồ không nói nổi. Hoá ra cả ba đều nằm ở HÌNH của sơ đồ, nên
làm được mà không đụng gì tới LEAN.

### ① Một điểm GHÉP NHIỀU THÀNH PHẦN

`0,25×ROC(63) + 0,35×ROC(126) + 0,40×ROC(252) − 0,20×biến_động` — vd7 · vd9 · vd10 đều
cần. Trước đó một vế chỉ ghép được một tầng hai vế.

Nay một vế là một DANH SÁCH thành phần, mỗi cái có HỆ SỐ riêng. Hệ số nằm TRONG thành
phần chứ không thành một phép `×` rời, và đó là cả mẹo: có hệ số thì tổng có trọng số
viết được bằng một chuỗi nối trái→phải, không cần thứ tự ưu tiên. Không có nó thì
`0,25×a + 0,35×b` nối trái→phải ra `((0,25×a)+0,35)×b` — sai, mà sai LẶNG.

### ② NHỚ QUA NẾN

vd10 · vd11 cần cỗ máy nhớ quyết định của chính nó. Khối Bắt đầu khai ô nhớ (CHUNG
hoặc THEO MÃ), khối «Ghi nhớ» ghi vào, hàng điều kiện đọc ra. Người dùng đặt TÊN cho
ô, và thẻ khối gọi bằng tên ấy: *Nhớ «đang chờ mua lại» = ĐÚNG*.

Chạy thật vd11: 187 lệnh với cái cờ, 430 lệnh khi bỏ nó ra — tức ô nhớ thật sự chặn
lệnh, không phải một ô cho đẹp.

### ③ HAI CHIẾN THUẬT CON CHẠY SONG SONG RỒI TRỘN TỶ TRỌNG

Chỗ bí cuối, và chỗ dễ hiểu sai nhất.

**Không làm được bằng cách phát hai tín hiệu.** Đọc `PortfolioConstructionModel.
GetTargetInsights`: nó gộp theo Symbol rồi lấy `.Last()`, nên hai nhánh cùng phát cho
một mã thì cái sau ĐÈ cái trước — LEAN không cộng. Ai tưởng mình trộn được bằng hai
tín hiệu thì backtest vẫn chạy, chỉ là một nửa chiến thuật biến mất không báo gì.

Chỗ chặn thật nằm ở APP, không nằm ở LEAN: nhánh rẽ từ sơ đồ xưa nay sinh ra
`if / elif`, tức LOẠI TRỪ NHAU. Nên khối Bắt đầu nay có ô **«Nhánh chạy thế nào»**:

| | sinh ra | nghĩa |
|---|---|---|
| Lần lượt *(mặc định)* | `if / elif` + `else: return` | cây quyết định — rẽ MỘT đường |
| Chạy hết | mấy câu `if` RỜI, không `else` | mọi nhánh khớp đều chạy |

Và phép trộn làm ở TỶ TRỌNG: mỗi nhánh con ghi điểm của nó vào một ô nhớ, rồi chỗ gộp
phát một tín hiệu có trọng số là tổng có trọng số của mấy ô ấy. Ba thứ ở trên khớp
vào nhau đúng tại đây — ghép nhiều thành phần + ô nhớ + nhánh chạy hết.

**Ba luật rẽ nhánh phải NỚI, và luật thứ tư phải GIỮ.** Ba luật nói cùng một câu
("nhánh này khớp thì nhánh kia không bao giờ tới lượt") nên chúng chỉ đúng khi chạy
lần lượt; giữ nguyên là chặn đúng cái người dùng vừa cố ý bật. Còn luật *"hai nhánh
không được nằm ngang nhau"* thì GIỮ: chạy hết vẫn chạy theo một THỨ TỰ, và hai nhánh
ghi cùng một ô nhớ thì cái chạy sau thắng — để ngang nhau là để toạ độ canvas quyết
kết quả backtest.

#### Chạy thật: vd10 vẽ lại bằng ba sleeve

`net[s] = 0,34·gen263[s] + 0,33·s531[s] + 0,33·s504cg[s]` — đúng một dòng netting của
vd10 gốc. Vẽ: 6 nhánh (mỗi sleeve một nhánh bật, một nhánh tắt) cùng đổ về một khối
Phát tín hiệu. SPY · QQQ · IWM · EEM · AAPL, 2015–2020.

| | lệnh | lãi | Sharpe | sụt sâu nhất |
|---|---|---|---|---|
| **Chạy hết** | 5.979 | **+34,2 %** | 0,33 | 14,4 % |
| Lần lượt *(cùng sơ đồ, đổi đúng một ô)* | 3.526 | +8,4 % | −0,24 | 5,1 % |

Lượt thứ hai là phép thử ngược, không phải cho đủ bộ: lần lượt thì chỉ sleeve đầu
khớp được ghi, hai sleeve sau không bao giờ tới lượt, nên tổng trộn thiếu hai phần
ba. Hai lượt ra giống nhau mới là tin xấu — nó có nghĩa cái ô ấy không nối vào đâu.

#### Và một hàng rào không ai gác, lòi ra lúc làm

`lam.GHI_NHO` khai `can_ma=False` kèm chú thích *"suy từ ô nhớ"* — mà không có ai suy.
Nên một ô nhớ THEO MÃ trong sơ đồ chạy MỘT LƯỢT cho cả rổ sinh ra biến `sym` không tồn
tại: `NameError` lúc chạy, sau khi đã chờ cả phút. Nay `can_ma` hỏi theo KHỐI chứ
không theo loại, và có bài canh cả hai chiều.

---

## ④ Rổ DOANH NGHIỆP và lệnh MỞ CỬA — hai mảnh cuối của vd10

### Lệnh mở cửa: đã có sẵn, mà tôi vừa viết là chưa

⚠ **Sửa một câu sai ở ngay trang này.** Mục Kết bản trước viết *"lối đặt lệnh
`MarketOnOpenOrder` thì khối Hành động chưa bày"*. Sai: `lam.LENH_CHO` khai `moo` và
`moc` từ lâu, nằm trong bảy kiểu của ô «Loại lệnh».

Nhưng khai không phải là chạy, nên lần này chạy thật — SPY 2015–2016, cùng một sơ đồ,
đổi đúng ô «Loại lệnh»:

| | lệnh | giá khớp |
|---|---|---|
| Khớp lúc MỞ cửa | 86 | đúng giá MỞ cửa, **84/84** ngày đối chiếu được |
| Khớp lúc ĐÓNG cửa | 86 | đúng giá ĐÓNG cửa, **84/84** |

Khớp tới chữ số cuối, sau khi quy về cùng hệ số chỉnh giá. Đây đúng thứ vd10 gốc cần:
quyết trên giá đóng cửa hôm nay → lệnh khớp giá mở cửa hôm sau → không nhìn trộm
tương lai.

### Và vì sao tôi đoán sai: một bảng KHÔNG AI ĐẾM

Bài `test_du_lean` đếm 13 mặt của LEAN, mà **không mặt nào là mấy hàm ĐẶT LỆNH**. Bảy
mặt "khác" đều là ô của khối Bắt đầu — nhịp, độ phân giải, chuẩn hoá giá, loại tài
sản, phí, trượt giá. Còn cái khối Hành động thật sự gọi thì không ai so với LEAN.

Hôm nay đếm ra **đủ**: `QCAlgorithm.Trading.cs` có 18 hàm trả `OrderTicket`, app gọi
10, 8 cái còn lại bỏ có chủ ý. Nhưng "hoá ra là đủ" mới là chỗ dở — nó đúng do may,
không do có ai canh. Nay nó là **mặt thứ tám**, và lý do bỏ nằm trong
`lam.LENH_KHONG_BAY` để bài kiểm đọc thẳng, chứ không nằm trong một câu ở lời tựa.

| bỏ | vì sao |
|---|---|
| `Buy` · `Sell` · `Order` | chỉ là `MarketOrder` đổi dấu / đổi tên cũ |
| `SubmitOrderRequest` | cửa tầng dưới, mọi kiểu lệnh qua nó đều đã có hàm riêng |
| `ComboMarketOrder` · `ComboLimitOrder` · `ComboLegLimitOrder` · `ExerciseOption` | lệnh quyền chọn nhiều chân |

### Rổ doanh nghiệp: thêm một rổ, và nó là rổ ĐẦU TIÊN chọn nổi mã

Bảng Rổ vốn đã kín (mọi model LEAN hoặc bày, hoặc khai rõ lý do bỏ), nên chỗ thiếu
không phải một model — mà là một **hình**: *"xếp cả sàn rồi giữ N mã đầu bảng"*, đúng
việc `SectorTopUniverse` của vd10 làm.

Nay có rổ **«Giao dịch nhiều tiền nhất — giữ N mã»**, dựng trên
`FundamentalUniverseSelectionModel`. Lớp ấy trước đây nằm trong danh sách bỏ với lý do
*"đòi NGƯỜI DÙNG viết hàm lọc Python"* — lý do đúng, nhưng hẹp hơn tôi tưởng: ở đây
câu lọc **cố định**, nằm trong từ điển như mọi câu `lean` khác, và chỗ trống duy nhất
là một CON SỐ. Người dùng không gõ Python, app không tính gì — `dollar_volume` là
trường LEAN đưa, còn xếp hạng rồi cắt N thì bộ chọn rổ nào cũng phải làm.

#### Và một điều kiện đã giết cả rổ, lặng thinh

Bản đầu chép nguyên tầng một của QC500, kể cả `has_fundamental_data`. Kết quả: 0 lệnh,
backtest chạy hết, không một lời nào. Soi thẳng bằng một lượt chạy có ghi nhật ký:

```
DORO nhìn thấy 7111, lọc còn 0, trả về 0: []
DORO mẫu: price=55.26 volume=1983802 dollar=109624898.0 hasfund=False
```

Bảy nghìn mã có `price` · `volume` · `dollar_volume` **đúng số của tệp coarse**, mà
`has_fundamental_data` là False ở **cả 7.111** — vì trường ấy do `FundamentalService`
phục vụ, tức kho `fine`, chứ không đọc từ tệp coarse. Không có `fine` thì nó False
sạch, và một điều kiện `and` là đủ.

* Đây chính là lý do **`QC500` chọn 0 mã** trên bộ miễn phí.
* Và nó **KHÁC** lý do của `ema_cheo`: đọc `EmaCrossUniverseSelectionModel.SelectCoarse`
  thì model ấy không hề hỏi `HasFundamentalData` — nó chết vì mười một ngày không đủ
  làm nóng EMA. Hai rổ cùng ra 0, hai bệnh khác nhau, và trang này trước đây gộp cả
  hai vào một lời giải thích.

Bỏ đúng điều kiện ấy đi thì rổ **chạy thật**: 10 mã mỗi ngày (SPY · IWM · QQQ · AAPL ·
FB · GOOG · TSLA · NFLX · GILD · EEM…), rổ đổi mã theo ngày, và sơ đồ vẽ ra đặt
**211 lệnh trên 10 mã**. Đây là rổ doanh nghiệp đầu tiên của app chọn nổi một mã nào.

#### vd10 bản đầy đủ

Cả ba mảnh ghép vào nhau: rổ tự chọn mỗi ngày → ba sleeve chạy song song ghi điểm vào
ba ô nhớ → một tín hiệu với trọng số `0,34·A + 0,33·B + 0,33·C`. Chạy đúng mười một
ngày có dữ liệu: **40 lệnh trên 8 mã**. Mười một ngày thì con số lãi lỗ không nói lên
gì — cái được chứng minh là bộ máy, không phải chiến thuật.

#### Còn thiếu, và thiếu vì DỮ LIỆU

vd10 gốc chia rổ theo **NGÀNH** rồi lấy N mã **vốn hoá** lớn nhất mỗi ngành. Cả hai
trường ấy (`asset_classification.morningstar_sector_code`, `market_cap`) nằm trong
`fine` của Morningstar, mà `Data/equity/usa/fundamental/` kèm LEAN chỉ có `coarse/`.
Bày ô «Ngành» ra là bày một ô lọc ra rỗng mọi lúc — nên để nguyên, và ghi lý do ở đây
cùng ngay trên dòng rổ ấy trong `bat_dau.py`. Mua bộ fundamental rồi mới thêm.

---

## Kết

Về phần VỎ thì xong, và nay đếm trên **14 mặt** chứ không phải 13 — mặt mới là mấy
hàm ĐẶT LỆNH, thứ trước đây không ai so với LEAN. Mỗi mặt: bày hết, hoặc khai rõ lý
do bỏ bằng chữ, và có bài canh đứng đó.

Về khả năng VẼ thì **bốn lỗ hổng ban đầu nay hết**, và vd10 vẽ được cả ba mảnh của
nó. Chỗ còn lại không phải lỗ hổng của app:

* **vd4** — `import` hai tệp không có trong thư mục. Thiếu TỆP, không thiếu tính năng.
* **vd8** — PCA. LEAN không có, nên làm nó là tự viết thuật toán. Chỗ nên dừng.
* **Chia rổ theo NGÀNH, xếp theo VỐN HOÁ** — cần bộ `fine` của Morningstar. Thiếu
  DỮ LIỆU, không thiếu tính năng: hôm có `fine` thì thêm một dòng vào bảng `RO`.

Nói gọn: **ba chỗ bí cuối đã bịt, và cái nào cũng bịt bằng vỏ** — không một dòng thuật
toán nào của LEAN bị app viết lại.
