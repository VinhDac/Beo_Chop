# vd2 — đối chiếu: mã gốc ↔ sơ đồ Cat_Studio

Chiến thuật **OmniFund Macro Sovereign** (`tai_lieu/chiến thuật ví dụ/vd2.py`) dựng
lại thành sơ đồ: **17 khối · 16 dây**. Mở trong app: Kho Strategy →
*vd2 OmniFund Macro Sovereign*.

Mã sinh ra: `du_lieu/ma_sinh/Vd2OmniFundMacroSovereign.py`

---

## Phần thiết lập

| Mã gốc | Sơ đồ sinh ra | |
|---|---|---|
| `SetStartDate(2020,1,1)` | `set_start_date(2020, 1, 1)` | ✅ |
| *(không có SetEndDate)* | `set_end_date(2026, 10, 17)` | ⚠ **khác** |
| `SetCash(100000)` | `set_cash(100000)` | ✅ |
| `Settings.FreePortfolioValuePercentage = 0.05` | `settings.free_portfolio_value_percentage = 0.05` | ✅ |
| `SetBrokerageModel(InteractiveBrokers, Margin)` | `set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE)` | ✅ *(Margin là mặc định)* |
| `SetBenchmark("SPY")` | `set_benchmark('SPY')` | ✅ |
| `AddEquity` × 4, `Resolution.Daily` | `add_equity` × 4, `Resolution.DAILY` | ✅ |
| `SMA(spy,200)` · `ROC(qqq/xle/gld,60)` | `sma(sym,200)` · `roc(sym,60)` cho **cả 4 mã** | ⚠ thừa, không đổi kết quả |
| `SetWarmUp(200, Daily)` | `set_warm_up(200)` | ✅ *(200 nến ngày)* |
| `Schedule.On(WeekStart(spy), AfterMarketOpen(spy,30), Rebalance)` | `schedule.on(date_rules.week_start(…), time_rules.after_market_open(…, 30), …)` | ✅ |

## Phần chạy

| Mã gốc | Sơ đồ sinh ra | |
|---|---|---|
| `if self.IsWarmingUp: return` | `if self.is_warming_up: return` | ✅ |
| `if not (… IsReady …): return` | *(bỏ)* | ✅ *(sau `set_warm_up(200)` thì cả bốn đã sẵn sàng — câu ấy không bao giờ chạy)* |
| `spy_price > sma200.Current.Value` | `securities[SPY].price > cb[SPY]['sma_200'].current.value` | ✅ |
| `sectors.sort(key=roc, reverse=True)` | **6 nhánh thử lần lượt** | ⚠ **khác về hình, giống về logic** |
| `SetHoldings(top1,.40) (top2,.35) (top3,.20)` | `set_holdings(QQQ, 0.4, False)` … | ✅ |
| nhánh gấu: `roc_gld >= roc_xle` | `if (ROC_GLD >= ROC_XLE)` | ✅ |

---

## Chỗ khác duy nhất về hình: sắp xếp → sáu nhánh

Mã gốc xếp 3 ngành bằng một dòng `sort`. Sơ đồ không có khối sắp xếp, nên nó **vẽ hẳn
6 thứ tự thành 6 nhánh**, thử lần lượt — nhánh đầu khớp thì thôi. Mỗi nhánh trượt làm
hẹp dần khả năng còn lại, nên điều kiện sau ngắn dần:

| Nhánh | Điều kiện thật sự | Thứ tự ra | Vì sao |
|---|---|---|---|
| 1 | `Q≥X và X≥G` | Q · X · G | |
| 2 | `Q≥X và Q≥G` | Q · G · X | nhánh 1 trượt ⇒ `X<G` |
| 3 | `Q≥X` | G · Q · X | ⇒ `X<G`, `Q<G` |
| 4 | `Q≥G` | X · Q · G | ⇒ `Q<X` |
| 5 | `X≥G` | X · G · Q | ⇒ `Q<X`, `Q<G` |
| 6 | *(mặc định)* | G · X · Q | ⇒ cả ba đều ngược |

**Sáu thứ tự, khớp cả sáu.** Kể cả lúc hoà: `sorted(reverse=True)` của Python là phép
sắp xếp **ổn định** nên giữ thứ tự gốc `[QQQ, XLE, GLD]`, mà `>=` của sơ đồ cũng ưu
tiên vế đứng trước — ra cùng kết quả.

Hai nhánh gấu cũng khớp.

---

## Ba điều phải nói rõ

1. **Ngày kết thúc.** Mã gốc không có `SetEndDate` nên nó chạy tới hôm nay. Sơ đồ bắt
   phải có khoảng ngày, nên đã ghim **17/10/2026**. Muốn so số thì bản trên web phải
   chạy đúng ngày ấy.

2. **Chỉ báo khai thừa.** Sơ đồ khai `SMA(200)` và `ROC(60)` cho cả bốn mã, trong khi
   mã gốc chỉ khai SMA cho SPY và ROC cho ba ngành. Chỉ báo không ai đọc thì không
   sinh ra lệnh nào — tốn chút sức máy, không đổi kết quả.

3. **Chưa chạy backtest để so số.** Bộ dữ liệu miễn phí đi kèm LEAN **không có XLE và
   GLD**, và SPY/QQQ chỉ tới 31/03/2021. Đối chiếu ở đây là **đối chiếu logic**, đọc
   từng dòng — không phải so thống kê.

---

## Bốn thứ chiến thuật này buộc phải thêm vào bộ khối

| | Thêm gì | Vì sao |
|---|---|---|
| ① | Nhịp **tuần** (`date_rules.week_start`) | tám nhịp cũ không cái nào nói được "mỗi tuần" |
| ② | Ô **đệm tiền mặt** (`free_portfolio_value_percentage`) | đổi nó là đổi sức mua, tức đổi kết quả |
| ③ | Ô **mã** trên khối Làm | không có thì không viết nổi `set_holdings(QQQ, 0.40)` |
| ④ | **Chạy một lượt cho cả rổ** | sơ đồ cũ luôn chạy lại cho từng mã; đây là chiến thuật **chia danh mục**, chạy một lần rồi chia cho cả bốn |

### ⚠ Và nó bắt được một lỗi thiết kế của D-15

Nhịp hẹn giờ trước nay **ép dữ liệu xuống nến phút**, với lý do "dữ liệu ngày thì
không có giờ nào trong đó mà hẹn". **Sai.** `schedule.on` chạy theo **đồng hồ** của
thuật toán, không theo lúc dữ liệu về — chính vd2 là bằng chứng: nó dùng
`Resolution.Daily` cộng `AfterMarketOpen(spy, 30)`.

Cái sai ấy không nhỏ: ép phút thì `sma(sym, 200)` thành **200 phút** chứ không phải
200 ngày. Cùng một sơ đồ, khác hẳn chiến thuật.

Nay độ phân giải tách khỏi nhịp: nhịp theo nến thì nhịp chính là độ phân giải; nhịp
hẹn giờ thì có ô chọn riêng, **mặc định NGÀY**. Hai bài kiểm từng đóng cứng điều sai
ấy thành luật cũng đã sửa lại.
