"""TỪ ĐIỂN OPTIMIZE — mỗi núm ở đây là MỘT khoá có thật trong config của LEAN.

Bộ Optimizer là một chương trình RIÊNG của LEAN (`Optimizer.Launcher`), đứng cạnh
launcher backtest ta đang chạy. Nó tự đẻ một tiến trình LEAN cho mỗi lượt backtest,
chạy song song, rồi gom kết quả. App không tính gì cả — y như D-11 đòi.

Đọc thẳng `Optimizer.Launcher/config.example.json`, nên mọi tên khoá dưới đây đều
là tên LEAN nhận:

    optimization-strategy            Grid hay Euler
    optimization-strategy-settings   `default-segment-amount` cho Euler
    optimization-criterion           {target, extremum}
    constraints                      [{target, operator, target-value}]
    parameters                       [{name, min, max, step}]
    maximum-concurrent-backtests     chạy mấy lượt một lúc
    optimizer-close-automatically    cùng họ với `close-automatically` đã vá vụ treo

HAI NÚM CỦA LEAN TA CỐ Ý KHÔNG BÀY
  · `target-value` ("đạt mức này thì dừng") — ít ai dùng, lại gây hiểu nhầm là hạn;
  · `min-step` — chỉ có nghĩa với Euler lúc soi sâu, để LEAN tự lo.
Bày một núm mà không ai biết vặn để làm gì thì thà đừng bày.

CẢ MÀN "Estimated Number and Cost" CỦA QC THÌ BỎ: chọn loại node, giá mỗi giờ, tổng
tiền USD, số dư QCC — đó là chuyện thuê máy trên cloud. Chạy tại máy thì không thuê
gì. Giữ đúng MỘT thứ trong khối ấy, và nó là thứ hữu ích nhất: BAO NHIÊU LƯỢT · ƯỚC
CHỪNG BAO LÂU (xem `uoc_luong`).
"""

#: Hai cách tìm LEAN có thật, trong `Optimizer/Strategies/`. Không bịa thêm cái nào.
GOC_CHIEN_LUOC = "QuantConnect.Optimizer.Strategies."
CACH_TIM = (
    (GOC_CHIEN_LUOC + "GridSearchOptimizationStrategy",
     "Quét CẢ lưới — thử hết mọi tổ hợp"),
    (GOC_CHIEN_LUOC + "EulerSearchOptimizationStrategy",
     "Quét rồi SOI SÂU vào vùng tốt nhất — ít lượt hơn"),
)

#: Phép so của ràng buộc — đúng `ComparisonOperatorTypes` của LEAN, viết y như JSON
#: của nó nhận (camelCase).
PHEP_SO = (
    ("greater", "lớn hơn"),
    ("greaterOrEqual", "lớn hơn hoặc bằng"),
    ("less", "nhỏ hơn"),
    ("lessOrEqual", "nhỏ hơn hoặc bằng"),
    ("equals", "bằng"),
    ("notEqual", "khác"),
)

#: Hướng tìm.
HUONG = (("max", "LỚN nhất"), ("min", "NHỎ nhất"))

#: 27 chỉ tiêu LEAN ghi vào `statistics` của file kết quả — đếm từ file thật, không
#: chép từ tài liệu. `Target` của optimizer là một ĐƯỜNG DẪN vào chính file ấy
#: (`Target.GetTokenInJsonBacktest` tách theo dấu chấm), nên mục tiêu và ràng buộc
#: chọn trong đúng danh sách này là chắc chắn trỏ tới một con số có thật.
#:
#: Nhờ vậy hai ô ấy là Ô CHỌN chứ không phải ô gõ — gõ sai một chữ thì `target` trỏ
#: vào hư không, optimizer chạy hết cả mẻ rồi không xếp hạng được gì.
CHI_TIEU = (
    "Sharpe Ratio", "Sortino Ratio", "Probabilistic Sharpe Ratio", "Net Profit",
    "Compounding Annual Return", "Drawdown", "Drawdown Recovery", "Win Rate",
    "Loss Rate", "Profit-Loss Ratio", "Expectancy", "Total Orders", "Total Fees",
    "Average Win", "Average Loss", "Start Equity", "End Equity", "Alpha", "Beta",
    "Annual Standard Deviation", "Annual Variance", "Information Ratio",
    "Tracking Error", "Treynor Ratio", "Portfolio Turnover",
    "Estimated Strategy Capacity", "Lowest Capacity Asset",
)

#: CỘT BẢNG XẾP HẠNG BÀY SẴN — sáu chỉ tiêu, không phải cả 27.
#:
#: Bày hết thì bảng rộng gấp ba màn hình và phải kéo ngang mới thấy cột mình cần;
#: mà thứ người ta nhìn để chọn một bộ số thì chỉ có ngần này: lãi bao nhiêu, sụt
#: sâu bao nhiêu, ăn thua mấy phần, và giao dịch có đủ nhiều để tin con số không.
#: 21 cột còn lại vẫn đọc được — cửa sổ có nút bày hết, nên không giấu gì cả.
#:
#: ⚠ CHỈ TIÊU ĐANG TÌM luôn được thêm vào, kể cả khi nó không nằm trong danh sách
#: này: quét để tìm Sortino mà bảng không có cột Sortino thì xếp hạng theo cái gì.
CHI_TIEU_CHINH = (
    "Sharpe Ratio", "Net Profit", "Compounding Annual Return",
    "Drawdown", "Win Rate", "Total Orders",
)


#: Đường dẫn LEAN hiểu cho một chỉ tiêu.
def duong_chi_tieu(ten):
    return f"Statistics.{ten}"


#: Mặc định cho một lượt Optimize mới.
MAC_DINH = {
    "cach_tim": CACH_TIM[0][0],
    "muc_tieu": "Sharpe Ratio",
    "huong": "max",
    "chia_doan": 10,          # `default-segment-amount`, chỉ Euler dùng
    "cung_luc": 0,            # 0 = để LEAN tự lấy nửa số nhân CPU
    "rang_buoc": [],
    "tham_so": {},            # tên núm -> {tu, den, buoc}
}

#: Một lượt backtest của bộ dữ liệu miễn phí ở nhịp NGÀY mất chừng ngần này giây —
#: đo từ mấy lượt chạy thật trong `du_lieu/ket_qua/`, không phải đoán. Chỉ dùng để
#: ƯỚC LƯỢNG, và câu chữ phải nói rõ là ước chừng.
GIAY_MOI_LUOT = 6.0


def so_buoc(tu, den, buoc):
    """Một núm quét ra mấy giá trị. -> int >= 0.

    Dùng đúng phép của `OptimizationStepParameterEnumerator`: đi từ `tu`, cộng dồn
    `buoc`, lấy cả hai đầu.

    ⚠ `den <= tu` TRẢ 0, kể cả khi bằng nhau. Một núm chỉ có đúng một giá trị thì
    không phải núm — và đó chính là cái bẫy nhìn thấy trong màn Optimize của QC: ô
    min và max cùng để 0, màn hình không kêu gì, cả mẻ chạy ra đúng một kết quả.
    Trả 1 ở đây là `uoc_luong` báo "1 lượt · 3 giây" nghe rất hợp lý — hỏng lặng."""
    try:
        tu, den, buoc = float(tu), float(den), float(buoc)
    except (TypeError, ValueError):
        return 0
    if buoc <= 0 or den <= tu:
        return 0
    return int((den - tu) / buoc) + 1


def uoc_luong(tham_so, cung_luc=0, nhan_cpu=4):
    """-> {so_luot, giay, thieu}. Thứ phải hiện NGAY TRÊN nút Chạy.

    Vì đây là chỗ cắn thật: ba núm × hai mươi bước là 8000 lượt backtest, hơn ba
    tiếng. Không nói trước thì người ta bấm Chạy rồi ngồi đoán — màn Optimize của QC
    có ô này, và đó là thứ đáng chép nhất của họ.

    `thieu` = tên mấy núm chưa khai nổi một khoảng quét; có cái nào thì CHƯA chạy
    được, vì một núm ra 0 giá trị là cả mẻ không có gì để thử."""
    so_luot, thieu = 1, []
    for ten, k in (tham_so or {}).items():
        n = so_buoc((k or {}).get("tu"), (k or {}).get("den"), (k or {}).get("buoc"))
        if n <= 0:
            thieu.append(ten)
        else:
            so_luot *= n
    if thieu or not tham_so:
        return {"so_luot": 0, "giay": 0, "thieu": thieu}
    song_song = max(1, int(cung_luc) if cung_luc else max(1, int(nhan_cpu) // 2))
    return {"so_luot": so_luot,
            "giay": so_luot * GIAY_MOI_LUOT / song_song,
            "thieu": []}


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối."""
    return {
        "cach_tim": [{"ma": m, "nhan": n} for m, n in CACH_TIM],
        "phep_so": [{"ma": m, "nhan": n} for m, n in PHEP_SO],
        "huong": [{"ma": m, "nhan": n} for m, n in HUONG],
        "chi_tieu": list(CHI_TIEU),
        "chi_tieu_chinh": list(CHI_TIEU_CHINH),
        "mac_dinh": {k: (dict(v) if isinstance(v, dict) else
                         list(v) if isinstance(v, list) else v)
                     for k, v in MAC_DINH.items()},
        "giay_moi_luot": GIAY_MOI_LUOT,
    }
