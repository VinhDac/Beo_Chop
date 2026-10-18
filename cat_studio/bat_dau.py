"""TỪ ĐIỂN KHỐI BẮT ĐẦU — nửa «thiết lập» của một thuật toán.

Một script QuantConnect có HAI nửa, và sơ đồ ta vẽ phải ra đúng cả hai:

    def initialize(self):      ← NÓI MỘT LẦN: ngày nào, bao nhiêu tiền, mã nào, nhịp nào
    def on_data(self, data):   ← CHẠY LẠI mỗi nhịp: đọc, so, quyết, đặt lệnh

Sơ đồ (các khối Hỏi/Làm nối dây) là nửa dưới. **File này là nửa trên.** Đọc từ 444
thuật toán Python thật trong `Algorithm.Python/` của LEAN: `set_start_date` có mặt ở
395 cái, `set_end_date` 392, `set_cash` 250, `add_equity` 244 — tức nửa trên gần như
bắt buộc, mà canvas ta trước nay không có chỗ nào cho nó.

Cùng luật với `hoi.py` và `lam.py`: **mỗi ô phải chỉ ra được MỘT thứ có thật của
LEAN** (ô `lean`). Không khai được thì không được có mặt.

MỘT KHỐI ÔM TRỌN, và nó giải luôn hai thứ tưởng phải đẻ khối mới:

  · **Vòng lặp nhiều mã** — không cần khối "Với mỗi mã". Ô `nhip` + ô `ma` đã khai
    trọn vòng rồi: *"mỗi nến, cho mỗi mã trong danh sách"*. Cả sơ đồ bên dưới là ruột
    vòng. Vòng vẫn HIỆN RA (luật D-13), chỉ là hiện ở đúng chỗ nó sinh ra.
  · **Cái hack "chỉ một lần mỗi ngày"** — hai chiến lược kinh điển của QC
    (`MACDTrendAlgorithm`, `MovingAverageCrossAlgorithm`) đều phải tự nhớ *hôm qua là
    ngày nào* để chặn bớt. Đó là TRẠNG THÁI, đúng thứ ta cấm. Họ viết vậy vì không có
    cách khai nhịp; ta có ô `nhip`, nên cái hack ấy biến mất.

KHÔNG thành ô — bộ sinh mã tự lo:
  · **Làm nóng** (`set_warm_up`) — lấy chu kỳ dài nhất trong các chỉ báo đã vẽ trên sơ
    đồ. Đếm trên sơ đồ của CHÍNH TA, không tính trên dữ liệu thị trường, nên vẫn trong
    luật. Không có nó thì N nến đầu cỗ máy quyết định trên số rác.
  · **Khai chỉ báo** — `self.rsi("XAU", 14)` phải nằm trong `initialize`, và LEAN tự
    cập nhật mỗi nến (*"We never need to 'update' our indicators"* — chú thích trong
    `MovingAverageCrossAlgorithm`). Bộ sinh mã nhặt từ các khối Hỏi lên.

RỔ ĐỘNG — ô `ma` có HAI KIỂU. Chọn mã động từng là chỗ "cố ý chưa có" của file này,
và lời ghi hồi ấy nói sai một chữ: nó bảo đó phải là *khối khác, việc khác*. Không
phải. `set_universe_selection` gọi MỘT LẦN trong `initialize`, đúng cùng một luật với
ba ô chính sách ở dưới — *xảy ra mỗi nhịp thì thành khối, đặt một lần thì thành ô*.
Nên nó là KIỂU THỨ HAI của chính ô «Chạy trên mã nào», không phải một khối mới. Xem
mục «RỔ ĐỘNG» ở dưới.

CỐ Ý CHƯA CÓ: cửa vào thứ hai (`schedule.on` riêng, cho kiểu *mỗi nến xem tín hiệu +
cuối tháng cân danh mục*). Đó là khối khác, việc khác. Ghi lại để biết là bỏ có chủ ý.
"""

# ---------------------------------------------------------------------------
# Kiểu của một ô — ba kiểu đầu dùng chung với `lam.py`, hai kiểu cuối riêng
# ---------------------------------------------------------------------------
O_SO = "so"
O_CHU = "chu"
O_CHON = "chon"
O_KHOANG_NGAY = "khoang_ngay"   # {"tu": "2010-01-01", "den": "2019-01-01"}
O_DS_MA = "ds_ma"               # [{"ma": "XAUUSD", "loai": "cfd"}, …]


def _o(ten, nhan, kieu, mac_dinh, lean, don_vi="", goi_y="", chon=(),
       bat_buoc=True, nguyen=False):
    """Một ô của khối Bắt đầu.

    `nguyen` = chỉ nhận số NGUYÊN (giờ, phút). Khai ở đây chứ không để giao diện tự
    biết: "phút có được lẻ không" là luật của ô, mà luật của ô thì thuộc về từ điển.
    Giao diện từng tự quyết chuyện ấy, và cũng chính nó tự chế luôn câu gợi ý từ hai
    khoá không hề tồn tại — in ra "Từ undefined đến undefined" suốt một thời gian."""
    return {"ten": ten, "nhan": nhan, "kieu": kieu, "mac_dinh": mac_dinh,
            "lean": lean, "don_vi": don_vi, "goi_y": goi_y, "chon": list(chon),
            "bat_buoc": bat_buoc, "nguyen": nguyen}


# ---------------------------------------------------------------------------
# Loại tài sản — mỗi loại một hàm `add_*` riêng của LEAN
# ---------------------------------------------------------------------------
#: (mã, nhãn, hàm LEAN). Không gộp thành một `add_security` chung: LEAN có sáu hàm
#: khác nhau vì sáu loại có giờ giao dịch, đơn vị và đòn bẩy khác nhau.
LOAI_TAI_SAN = (
    ("cfd", "CFD — vàng, dầu, chỉ số", "add_cfd"),
    ("equity", "Cổ phiếu", "add_equity"),
    ("forex", "Ngoại hối", "add_forex"),
    ("crypto", "Tiền mã hoá", "add_crypto"),
    ("index", "Chỉ số", "add_index"),
    ("future", "Hợp đồng tương lai", "add_future"),
)

#: Bộ dữ liệu MIỄN PHÍ đi kèm LEAN có sẵn mấy thứ này — đếm từ `Data/` trên đĩa.
#: Để hộp thoại gợi ý, KHÔNG phải để chặn: ai có dữ liệu riêng thì gõ mã khác.
CO_SAN_MIEN_PHI = {
    "cfd": ("XAUUSD", "DE30EUR"),
    "forex": ("EURUSD", "NZDUSD"),
    "equity": ("SPY", "AAPL", "IBM", "GOOG", "QQQ", "BAC", "AIG", "EEM", "USO"),
}

#: Rổ ETF có dữ liệu CẤU THÀNH trong bộ miễn phí, và dữ liệu ấy rơi vào NGÀY NÀO.
#: Đếm từ `Data/equity/usa/universes/etf/` trên đĩa.
#:
#: ⚠ VÌ SAO PHẢI KHAI CẢ NGÀY. Rổ ETF chỉ "có dữ liệu" đúng mấy ngày ấy; backtest
#: không trùm qua ngày nào trong đó thì LEAN chọn ra RỖNG — chạy xong, không lỗi,
#: không cảnh báo, KHÔNG MỘT LỆNH NÀO. Đã dính thật: chọn QQQ cho 2020 ra 0 lệnh,
#: vì rổ QQQ miễn phí chỉ có đúng một ngày 30/03/2011. Cùng họ với nhãn «không có
#: dữ liệu» của ô mã — nói TRƯỚC, đừng để người ta chạy xong rồi ngồi đoán.
RO_ETF_CO_SAN = {
    "SPY": ("2020-11-30", "2020-12-01"),
    "QQQ": ("2011-03-30",),
    "GDVD": ("2020-12-10",),
}


def ro_etf_trum_khoang(ma_etf, tu, den):
    """Khoảng backtest có trùm qua ngày nào có dữ liệu rổ của ETF này không.

    -> (có hay không, mấy ngày có dữ liệu). ETF lạ thì trả (None, ()) — không biết
    chứ không phải không có, vì người dùng có thể tự tải dữ liệu rổ về."""
    ngay = RO_ETF_CO_SAN.get(str(ma_etf or "").strip().upper())
    if ngay is None:
        return None, ()
    tu, den = str(tu or ""), str(den or "")
    return any(tu <= n <= den for n in ngay), ngay


# ---------------------------------------------------------------------------
# Nhịp chạy — ĐỘ PHÂN GIẢI dữ liệu và KHI NÀO sơ đồ chạy, gộp làm một
# ---------------------------------------------------------------------------
# Hai thứ ấy trong LEAN là hai câu (`Resolution` lúc đăng ký mã, và `on_data` hay
# `schedule.on` lúc chạy), nhưng với người chơi nó là MỘT câu hỏi: *bao lâu tôi xem
# một lần*. Nên ở đây là một ô, và bộ sinh mã tách ra làm hai.
#
# `res` = độ phân giải dữ liệu MẶC ĐỊNH. Năm nhịp đầu chạy thẳng trong `on_data`, nên
# với chúng nhịp CHÍNH LÀ độ phân giải. Mấy nhịp hẹn giờ thì khác, và đây là chỗ bản
# D-15 suy luận SAI:
#
#   ⚠ Tôi từng viết "muốn hẹn được giờ trong ngày thì dữ liệu phải có nến phút" và ép
#     `MINUTE`. Sai. `schedule.on` chạy theo ĐỒNG HỒ của thuật toán, không theo lúc
#     dữ liệu về — nên dữ liệu NGÀY vẫn hẹn giờ được. Một chiến thuật thật (vd2) làm
#     đúng như thế: `Resolution.Daily` cộng `AfterMarketOpen(spy, 30)`.
#
#   Hậu quả của cái sai ấy không nhỏ: ép phút thì `self.sma(sym, 200)` thành 200
#   PHÚT chứ không phải 200 NGÀY — cùng một sơ đồ, khác hẳn chiến thuật.
#
# Nên nhịp hẹn giờ có thêm ô `do_phan_giai` cho người dùng tự chọn, mặc định NGÀY.
#: Ô ĐỘ PHÂN GIẢI — chỉ hiện với nhịp HẸN GIỜ. Với nhịp theo nến thì nhịp CHÍNH LÀ
#: độ phân giải, bày thêm một ô nữa chỉ tổ mâu thuẫn.
_O_DO_PHAN_GIAI = _o(
    "do_phan_giai", "Độ phân giải dữ liệu", O_CHON, "DAILY", "Resolution.…",
    chon=[("TICK", "Tick"), ("SECOND", "Giây"), ("MINUTE", "Phút"),
          ("HOUR", "Giờ"), ("DAILY", "Ngày")],
    goi_y="Lịch chạy theo ĐỒNG HỒ chứ không theo dữ liệu — nên dữ liệu ngày vẫn "
          "hẹn giờ được.")


def _o_phut(nhan, mac_dinh=10):
    # ⚠ `goi_y=` CÓ TÊN, không truyền chay: vị trí thứ sáu của `_o` là `don_vi`, nên
    # "Từ 0 đến 390." vẫn nằm ở ô ĐƠN VỊ suốt từ đầu — hiện ra cạnh ô số như một đơn
    # vị đo, còn ô gợi ý thì trống trơn.
    return _o("so_phut", nhan, O_SO, mac_dinh, "", goi_y="Từ 0 đến 390 phút.",
              nguyen=True)


# ⚠ Ô THỨ SÁU — CÙNG MỘT NHỊP, HAI CÂU LEAN, vì RỔ ĐỘNG không có mã nào để neo lịch
# vào. Năm câu `schedule.on` dưới đây đều cần một mã (`every_day(spy)`,
# `after_market_open(spy, 30)`): giờ mở cửa là giờ của SÀN mà mã ấy niêm yết. Rổ thì
# lúc `initialize` còn RỖNG, nên `self._ma[0]` ném `IndexError` ngay dòng đầu — cỗ
# máy chết trước khi chạy nến nào.
#
# LEAN có sẵn đường ra, và nó là cùng mấy hàm ấy ở dạng KHÔNG MÃ (đọc `DateRules.cs`
# và `TimeRules.cs`):
#   · `after_market_open(so_phut)` / `before_market_close(so_phut)` — *"Picks, per
#     date, the earliest market open across the algorithm's securities… Defaults to
#     US equities (SPY) when no eligible security is subscribed"*, và nó BỎ QUA ngày
#     sàn đóng (`EarliestMarketOpenTimes` không yield gì cho ngày đóng cửa).
#   · `every_day()` / `week_start()` — mọi ngày LỊCH.
#
# ⚠ Khác một chỗ, và chỗ ấy chỉ ảnh hưởng nhịp «Mỗi ngày đúng giờ»: `time_rules.at`
# là luật ĐỒNG HỒ thuần, không biết sàn đóng hay mở. Nên nhịp ấy cộng rổ động sẽ chạy
# cả THỨ BẢY, CHỦ NHẬT. Bốn nhịp kia neo vào giờ mở/đóng cửa nên tự bỏ ngày nghỉ.
NHIP = (
    ("tick", "Mỗi tick", "TICK", "on_data", (), "on_data"),
    ("giay", "Mỗi nến giây", "SECOND", "on_data", (), "on_data"),
    ("phut", "Mỗi nến phút", "MINUTE", "on_data", (), "on_data"),
    ("gio", "Mỗi nến giờ", "HOUR", "on_data", (), "on_data"),
    ("ngay", "Mỗi nến ngày", "DAILY", "on_data", (), "on_data"),
    ("moi_ngay_luc", "Mỗi ngày đúng giờ", "MINUTE",
     "schedule.on(date_rules.every_day(ma), time_rules.at(gio, phut))",
     (_o("gio", "Giờ", O_SO, 10, "", goi_y="Từ 0 đến 23.", nguyen=True),
      _o("phut", "Phút", O_SO, 0, "", goi_y="Từ 0 đến 59.", nguyen=True),
      _O_DO_PHAN_GIAI),
     "schedule.on(date_rules.every_day(), time_rules.at(gio, phut))"),
    ("sau_mo_cua", "Mỗi ngày, sau khi MỞ cửa", "MINUTE",
     "schedule.on(date_rules.every_day(ma), time_rules.after_market_open(ma, so_phut))",
     (_o_phut("Số phút sau khi mở"), _O_DO_PHAN_GIAI),
     "schedule.on(date_rules.every_day(), time_rules.after_market_open(so_phut))"),
    ("truoc_dong_cua", "Mỗi ngày, trước khi ĐÓNG cửa", "MINUTE",
     "schedule.on(date_rules.every_day(ma), "
     "time_rules.before_market_close(ma, so_phut))",
     (_o_phut("Số phút trước khi đóng"), _O_DO_PHAN_GIAI),
     "schedule.on(date_rules.every_day(), "
     "time_rules.before_market_close(so_phut))"),
    # Nhịp TUẦN — `date_rules.week_start`. Đây là nhịp của mọi chiến thuật "cân lại
    # danh mục mỗi tuần", mà bảy nhịp trên không cái nào nói được. Và nó cộng rổ động
    # chính là chiến thuật kinh điển nhất của LEAN: mỗi tuần sàng lại cả rổ.
    ("tuan", "Mỗi TUẦN, sau khi MỞ cửa", "MINUTE",
     "schedule.on(date_rules.week_start(ma), "
     "time_rules.after_market_open(ma, so_phut))",
     (_o_phut("Số phút sau khi mở", 30), _O_DO_PHAN_GIAI),
     "schedule.on(date_rules.week_start(), "
     "time_rules.after_market_open(so_phut))"),
)

NHIP_THEO_MA = {n[0]: n for n in NHIP}


def nhip_cua(ma):
    return NHIP_THEO_MA.get(ma)


# ---------------------------------------------------------------------------
# Sàn — mô hình phí và trượt giá
# ---------------------------------------------------------------------------
# LEAN biết 37 sàn; đây là mấy cái khớp với dữ liệu miễn phí. Chọn sai sàn thì phí và
# trượt giá tính sai, mà backtest vẫn chạy ngon lành — nên nó đáng một ô.
SAN = (
    ("DEFAULT", "Mặc định của QuantConnect"),
    ("INTERACTIVE_BROKERS_BROKERAGE", "Interactive Brokers — cổ phiếu"),
    ("OANDA_BROKERAGE", "Oanda — CFD, ngoại hối"),
    ("BINANCE", "Binance — tiền mã hoá"),
    ("COINBASE", "Coinbase — tiền mã hoá"),
)

#: ⚠ SÀN NÀO KHÔNG NHẬN LỆNH «KHỚP LÚC ĐÓNG CỬA» (MarketOnClose).
#:
#: Vì sao con số này đáng một ô riêng — ĐÃ GẶP THẬT, và nó hỏng LẶNG hoàn toàn:
#: với nhịp **mỗi nến NGÀY**, LEAN không có dữ liệu trong ngày để khớp lệnh thị
#: trường, nên nó tự đổi lệnh ấy thành **MarketOnClose** (xem `IsDailyResolutionOnly`
#: trong `QCAlgorithm.Trading.cs`). Sàn nào không nhận loại ấy sẽ từ chối SẠCH mọi
#: lệnh — mà backtest vẫn chạy hết và báo "111 lệnh, lãi 0%". Phải mở file
#: order-events ra đọc mới thấy chữ *"does not support MarketOnClose order type"*.
#:
#: Danh sách đọc thẳng từ `_supportedOrderTypes` của từng model trong
#: `Common/Brokerages/`: Oanda / Binance / Coinbase đều chỉ có
#: `[Limit, Market, StopMarket, StopLimit]`. Interactive Brokers và Default thì có.
# ---------------------------------------------------------------------------
# DÂY CHUYỀN CỦA LEAN — ba trạm đứng SAU cây quyết định
# ---------------------------------------------------------------------------
# Mỗi mục là MỘT lớp có thật trong `Algorithm.Framework/`, đã đối chiếu tên file.
# Để trống = không cắm trạm ấy.

#: Biến tín hiệu thành tỷ trọng. `EqualWeighting` chia đều 1/N cho mấy tín hiệu CÒN
#: HẠN — đọc mã nguồn: `percent = 1.0 / count`, với `count` đếm insight đang active.
#: ⚠ CHỈ BÀY MODEL MÀ KHỐI VẼ ĐƯỢC NUÔI. Mỗi model đọc một trường của `Insight`, và
#: trường nào không ai đặt thì model ấy chết LẶNG — đọc thẳng `Algorithm.Framework/
#: Portfolio/*.py`:
#:
#:   EqualWeighting            không đọc gì            -> chạy
#:   InsightWeighting          `insight.weight`        -> ô «Trọng số» của Phát tín hiệu
#:   ConfidenceWeighted        `insight.confidence`    -> CHƯA ai đặt được
#:   MeanVarianceOptimization  `insight.magnitude`     -> CHƯA ai đặt được
#:
#: Hai cái dưới: `should_create_target_for_insight` trả False cho MỌI tín hiệu (hay
#: `set_run_time_error` thẳng), nên chọn vào là backtest chạy hết rồi ra 0 lệnh, không
#: một lời nào. Thà không bày còn hơn bày rồi báo lỗi — thêm ô nuôi được chúng thì
#: mở lại, ĐỪNG mở trước.
CHIA_VON = (
    ("", "— không dùng —"),
    ("EqualWeightingPortfolioConstructionModel", "Chia ĐỀU cho mọi tín hiệu (1/N)"),
    ("InsightWeightingPortfolioConstructionModel",
     "Chia theo TRỌNG SỐ — mã điểm cao được nhiều vốn hơn"),
)

#: Model chia vốn -> khe nào của `Insight` nó ĐỌC ("" = không đọc gì). Giữ cả mấy
#: model CHƯA bày, để bài kiểm biết vì sao chúng chưa bày và ai muốn mở lại thì phải
#: thêm ô nuôi khe ấy trước. Đọc `should_create_target_for_insight` của từng model.
CHIA_VON_DOC = {
    "EqualWeightingPortfolioConstructionModel": "",
    "InsightWeightingPortfolioConstructionModel": "weight",
    "ConfidenceWeightedPortfolioConstructionModel": "confidence",
    "MeanVarianceOptimizationPortfolioConstructionModel": "magnitude",
}

#: Chạy SAU khi chia vốn, được quyền chỉnh lại tỷ trọng.
#: ⚠ Mấy thứ này trước đây ta TỪ CHỐI (SL/TP cần nhớ qua nến, xem `lam.py`). Lối cổ
#: điển thì đúng là cần; ở đây LEAN giữ mức hộ, app không nhớ gì cả.
PHONG_RUI_RO = (
    ("", "— không dùng —"),
    ("MaximumDrawdownPercentPerSecurity", "Cắt lỗ theo % từng mã"),
    ("MaximumUnrealizedProfitPercentPerSecurity", "Chốt lời theo % từng mã"),
    ("MaximumDrawdownPercentPortfolio", "Cắt lỗ theo % CẢ danh mục"),
    ("TrailingStopRiskManagementModel", "Trailing stop"),
)

#: Cách đẩy tỷ trọng thành lệnh.
DAT_LENH = (
    ("", "— không dùng —"),
    ("ImmediateExecutionModel", "Đặt NGAY bằng lệnh thị trường"),
    ("VolumeWeightedAveragePriceExecutionModel", "Rải theo VWAP"),
    ("StandardDeviationExecutionModel", "Chờ giá lệch khỏi trung bình"),
)


SAN_KHONG_NHAN_MOC = ("OANDA_BROKERAGE", "BINANCE", "COINBASE")


# ---------------------------------------------------------------------------
# RỔ ĐỘNG — khe thứ năm của dây chuyền: `set_universe_selection`
# ---------------------------------------------------------------------------
# Ô «Chạy trên mã nào» trước nay chỉ nói được MỘT câu: *mấy mã này, gõ sẵn*. Nhưng
# 97/444 thuật toán Python của LEAN không gõ mã nào cả — chúng nói *mã nào thoả điều
# kiện thì vào rổ*, và rổ ấy đổi theo ngày. Đó là nửa còn lại của «chạy trên cái gì».
#
# HAI KIỂU CHO MỘT Ô, đúng lối vế phải của điều kiện (một số / một đại lượng):
#   · ô `ma` là một LIST  -> mấy mã gõ sẵn, mỗi mã một câu `add_*`  (lối cũ);
#   · ô `ma` là một DICT  -> một rổ, một câu `set_universe_selection`.
# Phân biệt bằng HÌNH DẠNG chứ không bằng một ô "kiểu" riêng — nhờ vậy file cũ (ô `ma`
# là list) mở ra vẫn chạy, không cần di cư schema.
#
# Mỗi mục dưới đây là MỘT lớp CÓ THẬT, tên lấy từ tên file trong
# `Algorithm.Framework/Selection/`. Cả chín lớp đều là `UniverseSelectionModel`, nên
# cả chín cắm được vào đúng một câu `self.set_universe_selection(…)`.
#
# ⚠ CỐ Ý KHÔNG CÓ `ManualUniverseSelectionModel`, dù nó cũng có thật
# (`Algorithm/Selection/`). Nó nhận một danh sách mã gõ sẵn — tức ĐÚNG câu mà lối
# list ở trên đã nói, chỉ khác đường đi tới LEAN. Bày cả hai là bày cho người chơi
# hai cách nói một thứ, rồi để họ đoán cách nào mới đúng. Rổ ĐỘNG là lý do ô này có
# kiểu thứ hai; cái nào không động thì không vào đây.


def _o_ro(ten, nhan, kieu, mac_dinh, don_vi="", goi_y="", nguyen=False):
    """Một ô CON của rổ — nó nằm TRONG dict của ô `ma`, không phải ô riêng của khối.

    Vì sao nằm trong: «rổ nào» và «rổ ấy lấy mấy mã» là MỘT câu trả lời cho MỘT câu
    hỏi. Tách ra thành ô riêng của khối thì lưu một file chọn rổ ETF rồi đổi sang gõ
    mã tay là còn lại một ô `lay = 8` lơ lửng, không thuộc về câu nào."""
    return _o(ten, nhan, kieu, mac_dinh, "", don_vi=don_vi, goi_y=goi_y,
              nguyen=nguyen)


#: Lọc rổ ETF theo TRỌNG SỐ. Thân hàm khai Ở ĐÂY, không để bộ sinh mã tự nghĩ ra —
#: lời hứa D-11 là «bộ sinh mã không tự viết một câu LEAN nào», và một hàm lọc cũng
#: là mã LEAN.
#:
#: Ba dòng này chép từ ví dụ CỦA CHÍNH LEAN (`ETFConstituentsFrameworkAlgorithm.py`):
#:     selected = sorted([c for c in constituents if c.weight],
#:                       key=lambda c: c.weight, reverse=True)[:8]
#:     return [c.symbol for c in selected]
#: `weight` là trường CÓ THẬT của `ETFConstituentData` (`public decimal? Weight`), và
#: nó NULLABLE — nên dòng đầu phải gạn, y như LEAN gạn. Thiếu dòng ấy là `sorted` so
#: None với số và ném `TypeError` giữa lượt chọn rổ.
#:
#: Chỗ trống duy nhất là `{lay}`.
LOC_TRONG_SO = (
    "co = [c for c in ds if c.weight]",
    "co.sort(key=lambda c: c.weight, reverse=True)",
    "return [c.symbol for c in co[:{lay}]]",
)

#: (mã, nhãn, lớp LEAN, ô con). Lớp nào không cần tham số thì ô con rỗng.
RO = (
    ("etf", "Các mã trong một ETF", "ETFConstituentsUniverseSelectionModel",
     (_o_ro("ma_etf", "Mã ETF", O_CHU, "SPY",
            goi_y="Rổ là các mã CẤU THÀNH ETF này. Bộ miễn phí CHỈ có SPY "
                  "(30/11–01/12/2020) và QQQ (30/03/2011) — khoảng backtest phải "
                  "trùm qua đúng mấy ngày ấy, không thì rổ rỗng."),
      # «Lấy mấy mã» CẦN một hàm lọc, nên nó không chỉ là một con số — xem
      # `LOC_TRONG_SO` ngay trên.
      _o_ro("lay", "Lấy mấy mã", O_SO, 8, don_vi="mã", nguyen=True,
            goi_y="Lấy mấy mã NẶNG nhất trong ETF. Để 0 thì lấy cả rổ — SPY là "
                  "hơn 500 mã, nặng máy."))),
    ("qc500", "QC500 — 500 cổ phiếu Mỹ thanh khoản nhất",
     "QC500UniverseSelectionModel", ()),
    ("etf_thanh_khoan", "Rổ ETF thanh khoản — cả sáu nhóm", "LiquidETFUniverse", ()),
    ("kim_loai", "ETF kim loại — vàng, bạc, bạch kim", "MetalsETFUniverse", ()),
    ("nang_luong", "ETF năng lượng — dầu, khí, mặt trời", "EnergyETFUniverse", ()),
    ("cong_nghe", "ETF công nghệ", "TechnologyETFUniverse", ()),
    ("trai_phieu", "ETF trái phiếu Mỹ", "USTreasuriesETFUniverse", ()),
    ("bien_dong", "ETF biến động — VIX", "VolatilityETFUniverse", ()),
    ("nganh_sp500", "ETF các ngành của S&P 500", "SP500SectorsETFUniverse", ()),
)

RO_THEO_MA = {r[0]: r for r in RO}


def ro_cua(gia_tri):
    """Giá trị ô `ma` -> mục RỔ nếu nó là một rổ động, ngược lại None.

    MỘT CHỖ DUY NHẤT quyết định "ô này đang nói kiểu nào". Hai chỗ cùng đoán hình
    dạng là hai chỗ để trôi khỏi nhau — mà lệch ở đây thì bộ sinh mã viết `add_*`
    trong khi giao diện bày ô chọn rổ, và không ai thấy cho tới lúc chạy."""
    if not isinstance(gia_tri, dict):
        return None
    return RO_THEO_MA.get(str(gia_tri.get("ro") or "").strip())


def o_ro_cua(gia_tri):
    """Mấy ô CON của rổ đang chọn. -> [ô]. Không phải rổ thì rỗng."""
    r = ro_cua(gia_tri)
    return list(r[3]) if r else []


def gt_ro(gia_tri, ten):
    """Giá trị một ô con của rổ, rơi về mặc định nếu dict CHƯA CÓ KHOÁ ấy.

    ⚠ CHỈ rơi về mặc định khi khoá VẮNG, không khi nó RỖNG — đúng luật của
    `core.o_bat_dau`. Bản đầu của hàm này coi `""` như vắng, nên xoá trắng ô «Mã ETF»
    là nó lặng lẽ thành "SPY": hộp thoại trống trơn mà cỗ máy chạy rổ SPY, và phép
    soát không có gì để bắt. Rỗng là rỗng, và `_soat_ro` báo lỗi vì nó rỗng."""
    for o in o_ro_cua(gia_tri):
        if o["ten"] == ten:
            v = (gia_tri or {}).get(ten)
            return o["mac_dinh"] if v is None else v
    return None


def lean_ro(gia_tri):
    """Câu LEAN một rổ sinh ra — để hộp thoại nói thẳng ra. "" nếu không phải rổ.

    ⚠ PHẢI LÀ MỘT KHÚC CỦA MÃ THẬT, không phải một câu tả lại nó. Bản đầu bịa ra
    tham số thứ ba tên «lọc theo trọng số» và bỏ chữ `self.` giữa dòng — đọc thì
    hiểu, nhưng tìm trong mã sinh ra thì không có, mà dòng khai này tồn tại ĐÚNG ĐỂ
    người dùng đối chiếu với mã. Nói sai còn tệ hơn không nói. Nay nó khớp từng chữ
    với `sinh_ma._khai_ro`, trừ chữ `self.` MỞ ĐẦU mà mọi ô `lean` đều bỏ — và
    `test_sinh_ma` canh đúng chuyện ấy: câu này phải nằm nguyên trong mã sinh ra.

    Mã ETF để trống cũng bày ra đúng `''` chứ không bày một dấu «…» cho đẹp: đó là
    thứ bộ sinh mã thật sự viết, và `soat_khoi_bat_dau` đã báo lỗi vì nó rỗng."""
    r = ro_cua(gia_tri)
    if not r:
        return ""
    if r[0] != "etf":
        return f"set_universe_selection({r[2]}())"
    lay = _nguyen(gt_ro(gia_tri, "lay"))
    ma_etf = str(gt_ro(gia_tri, "ma_etf") or "").strip().upper()
    return (f"set_universe_selection({r[2]}({ma_etf!r}, self.universe_settings"
            + (", self._loc_ro))" if lay > 0 else "))"))


def _nguyen(v):
    """-> int, 0 nếu không phải số. Ô số có thể đang mang chuỗi người dùng đang gõ."""
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0



# ---------------------------------------------------------------------------
# SÁU Ô
# ---------------------------------------------------------------------------
O_BAT_DAU = [
    # ⚠ HAI KIỂU CHO MỘT Ô — xem mục «RỔ ĐỘNG» ở trên. `ds_ma` vẫn là tên kiểu, vì
    # giao diện bày ra MỘT widget cho cả hai; widget ấy tự biết đang ở kiểu nào.
    _o("ma", "Chạy trên mã nào", O_DS_MA,
       [{"ma": "XAUUSD", "loai": "cfd"}],
       "add_cfd / add_equity / add_forex / add_crypto / add_index / add_future · "
       "hoặc set_universe_selection(…) nếu chọn một rổ",
       goi_y="Gõ sẵn mấy mã, hoặc chọn một RỔ — rổ thì LEAN tự quyết hôm nay gồm "
             "những mã nào. Nhiều mã thì cả sơ đồ chạy lại một lượt cho TỪNG mã."),

    _o("khoang", "Từ ngày → đến ngày", O_KHOANG_NGAY,
       {"tu": "2010-01-01", "den": "2019-01-01"},
       "set_start_date(tu) · set_end_date(den)",
       goi_y="Dữ liệu vàng miễn phí có từ 20/03/2006 đến 25/02/2019."),

    _o("von", "Vốn", O_SO, 100000, "set_cash(von)", don_vi="$",
       goi_y="Tiền khởi đầu của cỗ máy."),

    # Đệm tiền mặt: phần vốn LEAN KHÔNG cho đặt lệnh, để lệnh khỏi bị từ chối vì
    # thiếu ký quỹ. Mặc định của LEAN là 0,0025 (0,25%). Đổi nó là đổi sức mua, tức
    # đổi cả kết quả — nên nó phải khai được chứ không để ngầm.
    _o("dem_tien_mat", "Đệm tiền mặt", O_SO, 0.0025,
       "self.settings.free_portfolio_value_percentage = dem_tien_mat",
       don_vi="phần",
       goi_y="0.05 = chừa 5% không đặt lệnh. Mặc định LEAN là 0.0025."),

    _o("nhip", "Nhịp", O_CHON, "ngay",
       "Resolution.* · on_data hoặc schedule.on",
       chon=[(m, nhan) for m, nhan, *_ in NHIP],
       goi_y="Bao lâu cỗ máy xem một lần."),

    # ⚠ HAI KIỂU CHIẾN THUẬT KHÁC HẲN NHAU, và trước nay ta chỉ có kiểu đầu.
    #
    #   · SÀNG TỪNG MÃ — "mã nào RSI < 30 thì mua". Cả sơ đồ chạy LẠI một lượt cho
    #     từng mã, nên khối không cần gõ tên mã: `sym` là mã đang xét.
    #   · CHIA DANH MỤC — "xếp hạng 3 ngành rồi chia 40/35/20". Chạy ĐÚNG MỘT lượt,
    #     rồi đặt tỷ trọng cho từng mã có tên. Không có "mã đang xét" nào cả.
    #
    # Lòi ra khi dựng lại một chiến thuật thật (vd2 trong `tai_lieu/chiến thuật ví
    # dụ/`): nó cân lại cả rổ mỗi tuần, mà bộ khối cũ không nói nổi câu ấy.
    _o("chay_cho", "Chạy cho ai", O_CHON, "moi_ma", "for sym in self._ma: …",
       chon=[("moi_ma", "Mỗi mã một lượt — sàng từng mã"),
             ("ca_danh_muc", "Một lượt cho CẢ RỔ — chia danh mục")],
       goi_y="Chia danh mục thì mọi khối phải gõ rõ tên mã."),

    # ⚠ ĐỂ TRỐNG KHÔNG PHẢI LÀ "KHÔNG CÓ MỐC". `DefaultBrokerageModel.GetBenchmark`
    # trả về **SPY** — tức cỗ máy vàng của bạn bị đem so với cổ phiếu Mỹ, và không
    # một dòng nào nói ra. Nên câu gợi ý phải nói thẳng.
    _o("moc_so_sanh", "Mốc so sánh", O_CHU, "", "set_benchmark(ma)",
       goi_y="Để trống thì LEAN tự lấy SPY (cổ phiếu Mỹ). Gõ chính mã mình chạy để "
             "so với «mua rồi ôm».",
       bat_buoc=False),

    _o("san", "Sàn", O_CHON, "DEFAULT", "set_brokerage_model(BrokerageName.san)",
       chon=list(SAN), goi_y="Quyết phí và trượt giá tính theo kiểu nào."),

    # --- BA CHÍNH SÁCH CỦA DÂY CHUYỀN LEAN ---
    #
    # ⚠ Chúng ở ĐÂY chứ không thành khối, vì cả ba gọi MỘT LẦN trong `initialize`
    # (xem `BaseFrameworkRegressionAlgorithm.py` của LEAN: năm cái `set_*` đều nằm
    # trong `initialize`). Thả một khối "Chia vốn đều" vào cuối một nhánh thì nó
    # nghĩa là gì — "chỉ đặt cách chia vốn khi RSI < 30"? Không có nghĩa nào.
    # Đường ranh là: xảy ra MỖI NHỊP -> khối Hành động; đặt MỘT LẦN -> ô ở đây.
    #
    # Cả ba chỉ có tác dụng khi sơ đồ có khối «Phát tín hiệu» — `soat_dây_chuyền`
    # trong `core.py` canh chuyện đó.
    _o("chia_von", "Chia vốn theo tín hiệu", O_CHON, "",
       "set_portfolio_construction(…)", chon=list(CHIA_VON),
       goi_y="Biến tín hiệu thành tỷ trọng. Không chọn thì tín hiệu phát ra "
             "KHÔNG ai nhận.", bat_buoc=False),
    _o("phong_rui_ro", "Phòng rủi ro", O_CHON, "",
       "set_risk_management(…)", chon=list(PHONG_RUI_RO),
       goi_y="Chạy SAU khi chia vốn, chỉnh lại tỷ trọng — cắt lỗ, chốt lời, "
             "trailing stop. LEAN giữ mức, app không nhớ gì.", bat_buoc=False),
    _o("dat_lenh", "Đặt lệnh", O_CHON, "",
       "set_execution(…)", chon=list(DAT_LENH),
       goi_y="Cách đẩy tỷ trọng thành lệnh thật.", bat_buoc=False),
]

O_THEO_TEN = {o["ten"]: o for o in O_BAT_DAU}


def o_cua(gia_tri=None):
    """Mọi ô của khối Bắt đầu, KỂ CẢ ô chỉ hiện theo nhịp đã chọn.

    Cùng lối với `lam.o_cua`: chọn "Mỗi ngày đúng giờ" thì ô Giờ/Phút mới hiện ra."""
    ra = list(O_BAT_DAU)
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if n:
        ra.extend(n[4])
    return ra


def do_phan_giai(gia_tri=None):
    """Độ phân giải dữ liệu THẬT của một khối Bắt đầu -> "DAILY" / "MINUTE"…

    Nhịp theo nến: nhịp chính là độ phân giải. Nhịp hẹn giờ: lấy ô người dùng chọn,
    thiếu thì rơi về mặc định của nhịp ấy."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return "DAILY"
    if n[3] == "on_data":
        return n[2]
    v = str((gia_tri or {}).get("do_phan_giai") or "").strip().upper()
    hop_le = {m for m, _nhan in _O_DO_PHAN_GIAI["chon"]}
    return v if v in hop_le else str(_O_DO_PHAN_GIAI["mac_dinh"])


def ham_chay(gia_tri=None):
    """Câu `on_data`/`schedule.on` THẬT SỰ sẽ sinh ra, theo cả nhịp VÀ kiểu ô `ma`.

    Chọn rổ thì lịch chạy bằng mấy hàm KHÔNG MÃ — xem chú thích ở `NHIP`.

    ⚠ NHỊP LẠ (file sửa tay) RƠI VỀ `on_data`, không trả chuỗi rỗng. `soat_khoi_bat_
    dau` đã báo lỗi nhịp lạ rồi, nhưng bộ sinh mã vẫn chạy tiếp để bày ra phần sinh
    được — mà chuỗi rỗng thì nó cắt một ký tự của chuỗi rỗng rồi ghép thành một câu
    `schedule.on` cụt đầu. Rơi về `on_data` là đúng cách `sinh_ma` vẫn rơi (nó lấy
    `NHIP[4]`, tức nhịp «mỗi nến ngày»)."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return "on_data"
    return n[5] if ro_cua((gia_tri or {}).get("ma")) else n[3]


def ham_lean(gia_tri=None):
    """Câu LEAN quyết định nhịp — để hộp thoại nói thẳng ra cho người dùng thấy."""
    n = nhip_cua(str((gia_tri or {}).get("nhip") or O_THEO_TEN["nhip"]["mac_dinh"]))
    if not n:
        return ""
    r = do_phan_giai(gia_tri)
    chay = ham_chay(gia_tri)
    # Rổ động không có dòng `add_*` nào — độ phân giải đi qua `universe_settings`.
    dau = (f"universe_settings.resolution = Resolution.{r}"
           if ro_cua((gia_tri or {}).get("ma")) else f"add_*(ma, Resolution.{r})")
    return dau if chay == "on_data" else f"{dau} · {chay}"


def khai(gia_tri=None):
    """MỌI câu LEAN khối Bắt đầu khai ra, theo đúng giá trị đang có. -> [câu].

    MỘT CỬA DUY NHẤT cho hộp thoại: nó bày lại nguyên văn danh sách này — không
    chọn, không ghép, không cần biết có mấy câu. Thêm một câu khai ở đây là hộp
    thoại có ngay, không phải sửa bên TypeScript.

    ⚠ HAI LỖ ĐÃ VÁ Ở ĐÂY, cùng một họ. `HopBatDau.tsx` TỰ DỰNG LẠI câu nhịp bằng
    TypeScript (nó tự quyết `add_*` hay `universe_settings`, rồi tự ghép với tên
    hàm lịch) trong khi `ham_lean` bên Python làm đúng việc ấy — hai bản ghép chữ
    nằm hai bên cầu nối, không ai đứng so. Còn `lean_ro` thì KHÔNG AI GỌI, nên
    chọn rổ động xong, dòng khai trong hộp chỉ nói về nhịp mà im đúng câu quan
    trọng nhất cái rổ sinh ra. Cả hai đều không gây lỗi nào, nên không ai thấy."""
    ra = [ham_lean(gia_tri)]
    ra.append(lean_ro((gia_tri or {}).get("ma")))
    return [c for c in ra if c]


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối."""
    return {
        "o": O_BAT_DAU,
        "loai_tai_san": [{"ma": m, "nhan": n, "lean": h} for m, n, h in LOAI_TAI_SAN],
        "co_san": {k: list(v) for k, v in CO_SAN_MIEN_PHI.items()},
        "nhip": [{"ma": m, "nhan": n, "res": r, "chay": c,
                  "o_them": list(th), "chay_ro": c_ro}
                 for m, n, r, c, th, c_ro in NHIP],
        # RỔ — kiểu thứ hai của ô «Chạy trên mã nào». Giao diện CHỈ BÀY: nhãn, lớp
        # LEAN và mấy ô con đều khai ở đây, không khai lại bên TypeScript.
        "ro": [{"ma": m, "nhan": n, "lop": lop, "o_them": list(th)}
               for m, n, lop, th in RO],
    }
