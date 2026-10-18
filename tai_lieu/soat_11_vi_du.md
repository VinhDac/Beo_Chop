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

## Kết

Về phần VỎ thì xong: 177 món của LEAN, 136 bày ra, 41 khai rõ lý do, không còn món
nào thiếu mà không ai biết. Và từ nay có bài canh đứng ở đó, nên bảng nào tụt lại sau
LEAN là cổng đỏ chứ không phải chờ một ví dụ lòi ra.

Về mười một ví dụ thì **chưa**, và chỗ còn thiếu nay đã gọn lại thành những thứ
KHÔNG phải vỏ:

* **vd4** — Alpha slot nay có, nhưng nó `import` hai tệp không có trong thư mục.
  Thiếu tệp, không thiếu tính năng.
* **vd5** — nay vẽ được: `RiskParity` / `MeanVariance` / `BlackLitterman` làm đúng
  việc mà nó gọi scipy để làm.
* **vd7 · vd9** — phần nghịch đảo biến động nay là `RiskParity`; phần nhớ (cooldown,
  đỉnh vốn) là `TrailingStop` / `MaximumDrawdownPercentPortfolio`; phần trần cứng N
  mã là rổ `ema_cheo`. Còn đúng MỘT thứ: **điểm nhiều thành phần**
  (`0.25×r63 + 0.35×r126 + 0.40×r252 − 0.20×vol`), vì ghép đại lượng chỉ một tầng
  hai vế. Đó là một câu hỏi về HÌNH của hàng điều kiện, không phải về LEAN.
* **vd10 · vd11** — cần **máy trạng thái** (vd11 nhớ bảy thứ). LEAN không có khái
  niệm ấy, nên làm nó là tự viết thuật toán. Đây là chỗ nên dừng.
* **vd8** — PCA. LEAN không có. Chỗ nên dừng thứ hai.

Nói gọn: **bốn lỗ hổng ban đầu nay còn một** (điểm nhiều thành phần), cộng hai chỗ
cố ý dừng (máy trạng thái · PCA) và một ví dụ thiếu tệp.
