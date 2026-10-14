"""TỪ ĐIỂN 5 TRẠM — cỗ máy chia việc y như khung thuật toán của QuantConnect.  (D-10)

    ① Chọn mã  →  ② Tín hiệu  →  ③ Chia vốn  →  ④ Rủi ro  →  ⑤ Khớp lệnh
    (Universe)     (Alpha)        (Portfolio)     (Risk)       (Execution)

File này chỉ KHAI, không tính gì và không biết đồ thị: trạm nào chạy cho ai, lúc nào, được
đặt khối Làm nào, đọc được đại lượng nào. Ba chỗ đọc cùng một danh sách:

    may.py        soát lỗi + dựng chữ trên khối
    (phần 3)      bộ máy chạy — tính đúng những đại lượng khai ở đây
    (phần 5)      trình vẽ — bảng khối, hộp thoại

Thêm một đại lượng hay một khối là thêm MỘT mục ở đây; không ai phải chép lại danh sách.

LUẬT GỐC: MỘT SƠ ĐỒ = MỘT PHẠM VI CHẠY
--------------------------------------
Mỗi trạm là một sơ đồ khối, chạy lại từ khối Bắt đầu cho TỪNG đối tượng trong phạm vi của nó
(từng mã trong rổ, từng mã đang giữ…) theo lịch của nó. Ngữ pháp sơ đồ y hệt nhau ở cả năm
trạm — Hỏi nối tiếp = VÀ, nhiều nhánh = HOẶC thử từ trên xuống, luật lùi, đánh số. Chỉ khác
hai thứ: chạy cho AI, và khối LÀM ra cái gì.
"""

# ---------------------------------------------------------------------------
# Năm trạm — THỨ TỰ CÓ NGHĨA: đó là đường đi của một quyết định trong QC.
# ---------------------------------------------------------------------------
CHON_MA = "chon_ma"
TIN_HIEU = "tin_hieu"
CHIA_VON = "chia_von"
RUI_RO = "rui_ro"
KHOP_LENH = "khop_lenh"

TRAM_KEYS = [CHON_MA, TIN_HIEU, CHIA_VON, RUI_RO, KHOP_LENH]

#: Lịch chạy. `moi_nen` đi kèm một KHUNG (M1…D1) đặt trên khối Bắt đầu.
LICH = {
    "bat_dau": "một lần, lúc bắt đầu",
    "moi_ngay": "mỗi ngày",
    "dau_tuan": "đầu mỗi tuần",
    "dau_thang": "đầu mỗi tháng",
    "moi_nen": "mỗi nến",
    "khi_tin_hieu_doi": "khi tín hiệu đổi",
}

#: Khung nến. Thứ tự CÓ NGHĨA (nhỏ → lớn). Không có W1/MN1: không trạm nào cần, mà mỗi khung
#: thêm vào là một bộ gom nến nữa trên QC.
KHUNG = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
KHUNG_PHUT = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}

TRAM = [
    {"key": CHON_MA, "so": "①", "ten": "Chọn mã", "qc": "Universe Selection",
     "hoi": "Mã nào đáng để mắt tới?",
     "cho_ai": "mỗi mã của màn chơi (hoặc một danh sách riêng)",
     "ra": "rổ mã — Gom giữ N mã điểm cao nhất",
     "lich": ["bat_dau", "moi_ngay", "dau_tuan", "dau_thang"], "lich_mac_dinh": "bat_dau",
     "khung_mac_dinh": "D1"},
    {"key": TIN_HIEU, "so": "②", "ten": "Tín hiệu", "qc": "Alpha",
     "hoi": "Mã này sắp lên, xuống, hay nên đứng ngoài?",
     "cho_ai": "mỗi mã trong rổ",
     "ra": "tín hiệu LÊN / XUỐNG / ĐỨNG NGOÀI, có thời hạn",
     "lich": ["moi_nen"], "lich_mac_dinh": "moi_nen", "khung_mac_dinh": "H1"},
    {"key": CHIA_VON, "so": "③", "ten": "Chia vốn", "qc": "Portfolio Construction",
     "hoi": "Mỗi mã được bao nhiêu phần vốn?",
     "cho_ai": "mỗi mã đang có tín hiệu hoặc đang giữ",
     "ra": "tỷ trọng mục tiêu — Gom chia ngân sách, chặn trần mỗi mã",
     "lich": ["khi_tin_hieu_doi", "moi_ngay", "dau_tuan", "dau_thang"],
     "lich_mac_dinh": "khi_tin_hieu_doi", "khung_mac_dinh": "D1"},
    {"key": RUI_RO, "so": "④", "ten": "Rủi ro", "qc": "Risk Management",
     "hoi": "Có gì phải cắt bớt ngay không?",
     "cho_ai": "mỗi mã đang giữ",
     "ra": "mục tiêu đã chỉnh",
     "lich": ["moi_nen"], "lich_mac_dinh": "moi_nen", "khung_mac_dinh": "H1"},
    {"key": KHOP_LENH, "so": "⑤", "ten": "Khớp lệnh", "qc": "Execution",
     "hoi": "Đưa vị thế về mục tiêu bằng lệnh gì, lúc nào?",
     "cho_ai": "mỗi mã còn lệch giữa đang giữ và mục tiêu",
     "ra": "lệnh gửi sang QuantConnect",
     "lich": ["moi_nen"], "lich_mac_dinh": "moi_nen", "khung_mac_dinh": "M1"},
]
TRAM_THEO_KEY = {t["key"]: t for t in TRAM}


def nhan_tram(key):
    """`② Tín hiệu` — tên đầy đủ kèm số trạm, dùng trong mọi câu báo lỗi."""
    t = TRAM_THEO_KEY.get(key)
    return f"{t['so']} {t['ten']}" if t else str(key)


# ---------------------------------------------------------------------------
# Khối HỎI — cổng rẽ nhánh, y hệt ở mọi trạm.
# ---------------------------------------------------------------------------
#: Giữ đúng `type` của cổng cũ: bộ đánh số và luật rẽ nhánh (`core.is_branch_gate`) nhận ra
#: cổng bằng chính khoá này, nên cả phần đồ thị dùng lại được nguyên vẹn.
HOI = "check_cond"
NHAN_HOI = "Hỏi"

#: Ký hiệu, không phải chữ — một cổng mang 3–4 điều kiện thì mắt phải liếc thấy quan hệ.
PHEP_SO = {"<": "<", "<=": "≤", ">": ">", ">=": "≥", "==": "=", "!=": "≠"}

# ---------------------------------------------------------------------------
# ĐƠN VỊ — để biết hai vế của một phép so có cùng loại đại lượng không.
# ---------------------------------------------------------------------------
#: `gia` là cả MỨC giá lẫn KHOẢNG giá (ATR, độ lệch chuẩn): so ATR với giá đóng × 0.02 là
#: một câu có nghĩa. Còn so RSI (thang 0–100) với một mức giá thì không.
DON_VI = {"gia": "giá", "pt": "%", "so": "số", "nen": "nến", "tien": "tiền"}

# ---------------------------------------------------------------------------
# THAM SỐ của đại lượng — ô nào, nhận gì, mặc định bao nhiêu.
# ---------------------------------------------------------------------------
#: `so`: ô số (nhận cả TÊN tham số của cỗ máy — luật xuyên suốt app).
#: `chon`: chọn một trong mấy khoá.
THAM_SO_TH = {
    "khung": {"loai": "chon", "nhan": "khung", "chon": {k: k for k in KHUNG}},
    "chu_ky": {"loai": "so", "nhan": "chu kỳ", "nguyen": True, "min": 1, "max": 1000,
               "mac_dinh": 14},
    "lui": {"loai": "so", "nhan": "lùi", "nguyen": True, "min": 0, "max": 500, "mac_dinh": 0},
    "nhanh": {"loai": "so", "nhan": "nhanh", "nguyen": True, "min": 1, "max": 500,
              "mac_dinh": 12},
    "cham": {"loai": "so", "nhan": "chậm", "nguyen": True, "min": 1, "max": 1000,
             "mac_dinh": 26},
    "tin_hieu": {"loai": "so", "nhan": "tín hiệu", "nguyen": True, "min": 1, "max": 500,
                 "mac_dinh": 9},
    "do_lech": {"loai": "so", "nhan": "số độ lệch", "min": 0.1, "max": 10, "mac_dinh": 2},
    "chu_ky_d": {"loai": "so", "nhan": "chu kỳ %D", "nguyen": True, "min": 1, "max": 100,
                 "mac_dinh": 3},
    "dai": {"loai": "chon", "nhan": "dải",
            "chon": {"tren": "dải trên", "giua": "dải giữa", "duoi": "dải dưới"},
            "mac_dinh": "tren"},
    "bien": {"loai": "chon", "nhan": "biên",
             "chon": {"tren": "biên trên", "duoi": "biên dưới"}, "mac_dinh": "tren"},
    "kieu": {"loai": "chon", "nhan": "cách làm mượt",
             "chon": {"rma": "Wilder", "sma": "trung bình đơn"}, "mac_dinh": "rma"},
    # Chỉ báo NHIỀU ĐƯỜNG chọn đọc đường nào. Bộ lựa chọn nằm trên chính đại lượng (`dong`)
    # vì mỗi chỉ báo một bộ: MACD có ba đường, Stochastic có hai.
    "dong": {"loai": "chon", "nhan": "đường", "chon": {}},
}

#: Chọn "đường" của chỉ báo nhiều đường — mỗi chỉ báo một bộ riêng.
DONG_MACD = {"macd": "đường MACD", "tin_hieu": "đường tín hiệu", "histogram": "histogram"}
DONG_STOCH = {"k": "%K", "d": "%D"}


def _th(key, nhan, nhom, don_vi, tham_so=(), mac_dinh=None, tram=None, mo_ta="",
        dong=None):
    """Một đại lượng. `tram=None` = đọc được ở mọi trạm."""
    return {"key": key, "nhan": nhan, "nhom": nhom, "don_vi": don_vi,
            "tham_so": list(tham_so), "mac_dinh": dict(mac_dinh or {}),
            "tram": list(tram) if tram else None, "mo_ta": mo_ta,
            "dong": dict(dong) if dong else None}


_G = ("khung", "lui")
_C = ("khung", "chu_ky", "lui")

#: Mọi đại lượng khối Hỏi đọc được. `lui = 0` là nến VỪA ĐÓNG — bộ máy chạy ở lúc đóng nến,
#: nên không có "nến đang chạy" nào để mà nhìn trộm tương lai.
TOAN_HANG = [
    # ---- giá ----
    _th("gia_dong", "Giá đóng", "Giá", "gia", _G),
    _th("gia_mo", "Giá mở", "Giá", "gia", _G),
    _th("gia_cao", "Giá cao nhất", "Giá", "gia", _G),
    _th("gia_thap", "Giá thấp nhất", "Giá", "gia", _G),
    _th("khoi_luong", "Khối lượng", "Giá", "so", _G,
        mo_ta="forex/CFD trên QC không có khối lượng — đọc ra 0"),
    _th("gia_tri_gd", "Giá trị giao dịch", "Giá", "tien", _G,
        mo_ta="giá đóng × khối lượng — đo độ thanh khoản"),
    # ---- chỉ báo ----
    _th("sma", "SMA", "Chỉ báo", "gia", _C, {"chu_ky": 20}),
    _th("ema", "EMA", "Chỉ báo", "gia", _C, {"chu_ky": 20}),
    _th("wma", "WMA", "Chỉ báo", "gia", _C, {"chu_ky": 20}),
    _th("rma", "RMA (Wilder)", "Chỉ báo", "gia", _C, {"chu_ky": 14}),
    _th("atr", "ATR", "Chỉ báo", "gia", ("khung", "chu_ky", "kieu", "lui"), {"chu_ky": 14},
        mo_ta="biên độ thật trung bình — đo bằng đơn vị giá"),
    _th("atr_pt", "ATR % giá", "Chỉ báo", "pt", ("khung", "chu_ky", "kieu", "lui"),
        {"chu_ky": 14}, mo_ta="ATR chia giá đóng — so được giữa các mã"),
    _th("rsi", "RSI", "Chỉ báo", "so", _C, {"chu_ky": 14}, mo_ta="thang 0–100"),
    _th("macd", "MACD", "Chỉ báo", "gia",
        ("khung", "nhanh", "cham", "tin_hieu", "dong", "lui"), {"dong": "macd"},
        dong=DONG_MACD),
    _th("bollinger", "Bollinger", "Chỉ báo", "gia",
        ("khung", "chu_ky", "do_lech", "dai", "lui"), {"chu_ky": 20}),
    _th("roc_pt", "Đổi giá %", "Chỉ báo", "pt", _C, {"chu_ky": 20},
        mo_ta="giá đóng so với chu_ky nến trước, tính %"),
    _th("donchian", "Kênh Donchian", "Chỉ báo", "gia", ("khung", "chu_ky", "bien", "lui"),
        {"chu_ky": 20},
        mo_ta="đỉnh cao nhất / đáy thấp nhất của chu_ky nến TRƯỚC nến đang xét"),
    _th("adx", "ADX", "Chỉ báo", "so", _C, {"chu_ky": 14}, mo_ta="sức mạnh xu hướng, 0–100"),
    _th("stoch", "Stochastic", "Chỉ báo", "so", ("khung", "chu_ky", "chu_ky_d", "dong", "lui"),
        {"dong": "k"}, dong=DONG_STOCH),
    _th("do_lech_chuan", "Độ lệch chuẩn", "Chỉ báo", "gia", _C, {"chu_ky": 20}),
    _th("kl_tb", "Khối lượng TB", "Chỉ báo", "so", _C, {"chu_ky": 20}),
    # ---- thời gian & tài khoản ----
    _th("gio", "Giờ (UTC)", "Thời gian", "so", mo_ta="0–23"),
    _th("thu", "Thứ", "Thời gian", "so", mo_ta="1 = thứ Hai … 7 = Chủ nhật"),
    _th("von", "Vốn hiện có", "Tài khoản", "tien"),
    _th("lai_tk_pt", "Lãi tài khoản %", "Tài khoản", "pt", mo_ta="so với vốn ban đầu"),
    _th("sut_giam_tk_pt", "Sụt giảm tài khoản %", "Tài khoản", "pt",
        mo_ta="vốn đang thấp hơn đỉnh vốn bao nhiêu %"),
    _th("tien_mat_pt", "Tiền mặt %", "Tài khoản", "pt"),
    _th("so_ma_dang_giu", "Số mã đang giữ", "Tài khoản", "so"),
    # ---- tín hiệu — chỉ trạm ③ ----
    _th("huong_tin_hieu", "Hướng tín hiệu", "Tín hiệu", "so", tram=[CHIA_VON],
        mo_ta="+1 LÊN · −1 XUỐNG · 0 đứng ngoài hoặc đã hết hạn"),
    _th("tin_cay", "Độ tin cậy", "Tín hiệu", "so", tram=[CHIA_VON], mo_ta="0–1"),
    _th("trong_so_tin_hieu", "Trọng số tín hiệu", "Tín hiệu", "so", tram=[CHIA_VON],
        mo_ta="0–1"),
    _th("so_ma_len", "Số mã báo LÊN", "Tín hiệu", "so", tram=[CHIA_VON]),
    _th("so_ma_xuong", "Số mã báo XUỐNG", "Tín hiệu", "so", tram=[CHIA_VON]),
    # ---- vị thế của mã đang xét ----
    _th("ty_trong_pt", "Tỷ trọng đang giữ %", "Vị thế", "pt",
        tram=[CHIA_VON, RUI_RO, KHOP_LENH], mo_ta="% vốn, âm = đang bán khống"),
    _th("lai_lo_pt", "Lãi/lỗ vị thế %", "Vị thế", "pt", tram=[RUI_RO, KHOP_LENH],
        mo_ta="giá hiện tại so với giá vốn"),
    _th("sut_tu_dinh_pt", "Rơi từ đỉnh %", "Vị thế", "pt", tram=[RUI_RO],
        mo_ta="giá đã lùi bao nhiêu % từ chỗ tốt nhất kể từ lúc vào — cho trailing stop"),
    _th("so_nen_giu", "Số nến đã giữ", "Vị thế", "nen", tram=[RUI_RO],
        mo_ta="đếm theo khung của trạm ④"),
    # ---- khớp lệnh — chỉ trạm ⑤ ----
    _th("lech_muc_tieu_pt", "Lệch mục tiêu %", "Khớp lệnh", "pt", tram=[KHOP_LENH],
        mo_ta="mục tiêu trừ đang giữ, % vốn"),
    _th("spread_pt", "Spread % giá", "Khớp lệnh", "pt", tram=[KHOP_LENH],
        mo_ta="cổ phiếu trên QC không có giá chào mua/bán — đọc ra 0"),
    _th("so_lenh_cho", "Số lệnh đang chờ", "Khớp lệnh", "so", tram=[KHOP_LENH]),
    _th("phut_tu_muc_tieu", "Phút từ lúc đổi mục tiêu", "Khớp lệnh", "so", tram=[KHOP_LENH]),
]
TOAN_HANG_THEO_KEY = {t["key"]: t for t in TOAN_HANG}


def doc_duoc_o(key, tram):
    """Đại lượng `key` có đọc được ở trạm `tram` không."""
    t = TOAN_HANG_THEO_KEY.get(key)
    return bool(t) and (t["tram"] is None or tram in t["tram"])


def toan_hang_cua_tram(tram):
    return [t for t in TOAN_HANG if t["tram"] is None or tram in t["tram"]]


# ---------------------------------------------------------------------------
# KHỐI LÀM — mỗi trạm một bộ. Đây là chỗ DUY NHẤT trạm khác nhau về hành động.
# ---------------------------------------------------------------------------
#: `vai`:
#:   `quyet_dinh` — chốt kết quả cho đối tượng đang xét. Một đường chỉ được MỘT cái: hai
#:                  cái nối tiếp nhau thì cái sau lặng lẽ đè cái trước.
#:   `phu`        — kèm theo một quyết định (vd "cấm vào lại N nến" sau "đưa về 0").
#:
#: `truong`: các ô của khối. `khi` = ô chỉ có nghĩa khi một ô khác mang giá trị đó.
HUONG_TIN_HIEU = {"len": "LÊN", "xuong": "XUỐNG", "dung_ngoai": "ĐỨNG NGOÀI"}

CACH_CHIA = {
    "co_dinh": "cố định X%",
    "chia_deu": "chia đều",
    "theo_tin_cay": "theo độ tin cậy",
    "theo_trong_so": "theo trọng số tín hiệu",
    "rui_ro_ngang": "rủi ro ngang nhau",
}
#: Cách nào là TƯƠNG ĐỐI — chia nhau phần ngân sách còn lại sau các tỷ trọng cố định.
CACH_TUONG_DOI = ("chia_deu", "theo_tin_cay", "rui_ro_ngang")


def _o(key, loai, nhan, **k):
    return {"key": key, "loai": loai, "nhan": nhan, **k}


KHOI_LAM = {
    # ---- ① Chọn mã ----
    "vao_ro": {"tram": CHON_MA, "nhan": "Cho vào rổ", "vai": "quyet_dinh",
               "mo_ta": "Mã đi tới đây thì vào rổ. Có điểm thì Gom xếp theo điểm để "
                        "giữ N mã đứng đầu.",
               "truong": [_o("diem", "toan_hang", "điểm", tuy_chon=True)]},
    "loai_ro": {"tram": CHON_MA, "nhan": "Loại khỏi rổ", "vai": "quyet_dinh",
                "mo_ta": "Nói rõ mã này KHÔNG vào rổ, kèm lý do trên đường đi.",
                "truong": []},
    # ---- ② Tín hiệu ----
    "bao": {"tram": TIN_HIEU, "nhan": "Báo tín hiệu", "vai": "quyet_dinh",
            "mo_ta": "Phát một tín hiệu cho mã này. Hết hạn thì tín hiệu tự tắt.",
            "truong": [
                _o("huong", "chon", "hướng", chon=HUONG_TIN_HIEU, mac_dinh="len"),
                _o("thoi_han", "so", "hạn", nguyen=True, min=1, max=10000, mac_dinh=24,
                   don_vi="nen"),
                _o("tin_cay", "so", "tin cậy", min=0, max=1, tuy_chon=True),
                _o("trong_so", "so", "trọng số", min=0, max=1, tuy_chon=True),
            ]},
    # ---- ③ Chia vốn ----
    "dat_ty_trong": {"tram": CHIA_VON, "nhan": "Đặt tỷ trọng", "vai": "quyet_dinh",
                     "mo_ta": "Mã này được bao nhiêu phần vốn. Dấu theo hướng tín hiệu: "
                              "LÊN là mua, XUỐNG là bán.",
                     "truong": [
                         _o("cach", "chon", "cách", chon=CACH_CHIA, mac_dinh="chia_deu"),
                         _o("pt", "so", "%", min=0, max=100, mac_dinh=10,
                            khi={"cach": "co_dinh"}),
                         _o("khung", "chon", "khung", chon={k: k for k in KHUNG},
                            mac_dinh="D1", khi={"cach": "rui_ro_ngang"}),
                         _o("chu_ky", "so", "chu kỳ", nguyen=True, min=2, max=1000,
                            mac_dinh=20, khi={"cach": "rui_ro_ngang"}),
                     ]},
    "ve_0": {"tram": CHIA_VON, "nhan": "Về 0", "vai": "quyet_dinh",
             "mo_ta": "Không giữ mã này nữa.", "truong": []},
    "giu_nguyen": {"tram": CHIA_VON, "nhan": "Giữ nguyên", "vai": "quyet_dinh",
                   "mo_ta": "Mục tiêu = đúng phần đang giữ: không mua thêm, không bán bớt.",
                   "truong": []},
    # ---- ④ Rủi ro ----
    "dua_ve_0": {"tram": RUI_RO, "nhan": "Đưa về 0", "vai": "quyet_dinh",
                 "mo_ta": "Bán sạch mã này, bất kể trạm ③ muốn gì.", "truong": []},
    "giam_ve": {"tram": RUI_RO, "nhan": "Giảm về", "vai": "quyet_dinh",
                "mo_ta": "Mục tiêu của mã này không được quá X% vốn.",
                "truong": [_o("pt", "so", "%", min=0, max=100, mac_dinh=5)]},
    "cam_vao_lai": {"tram": RUI_RO, "nhan": "Cấm vào lại", "vai": "phu",
                    "mo_ta": "Trong N nến tới, trạm ③ đặt gì cho mã này cũng thành 0.",
                    "truong": [_o("so_nen", "so", "số nến", nguyen=True, min=1, max=10000,
                                  mac_dinh=5, don_vi="nen")]},
    "dung_tai_khoan": {"tram": RUI_RO, "nhan": "Dừng cả tài khoản", "vai": "quyet_dinh",
                       "mo_ta": "Bán sạch MỌI mã và thôi giao dịch tới hết lượt chạy.",
                       "truong": []},
    # ---- ⑤ Khớp lệnh ----
    "lenh_thi_truong": {"tram": KHOP_LENH, "nhan": "Lệnh thị trường", "vai": "quyet_dinh",
                        "mo_ta": "Khớp ngay theo giá thị trường. Dưới 100% là chia nhỏ: mỗi "
                                 "lượt chỉ khớp một phần của phần còn thiếu.",
                        "truong": [_o("phan_pt", "so", "% phần lệch", min=1, max=100,
                                      mac_dinh=100)]},
    "lenh_gioi_han": {"tram": KHOP_LENH, "nhan": "Lệnh giới hạn", "vai": "quyet_dinh",
                      "mo_ta": "Chờ giá tốt hơn: mua thấp hơn / bán cao hơn giá hiện tại "
                               "X%. Hết hạn chưa khớp thì huỷ.",
                      "truong": [
                          _o("lech_pt", "so", "% cách giá", min=0, max=50, mac_dinh=0.1),
                          _o("het_han", "so", "hạn", nguyen=True, min=1, max=10000,
                             mac_dinh=30, don_vi="nen"),
                          _o("phan_pt", "so", "% phần lệch", min=1, max=100, mac_dinh=100),
                      ]},
    "lenh_cho_stop": {"tram": KHOP_LENH, "nhan": "Lệnh chờ stop", "vai": "quyet_dinh",
                      "mo_ta": "Chỉ vào khi giá chạy đúng hướng: mua cao hơn / bán thấp hơn "
                               "giá hiện tại X%. Hết hạn chưa khớp thì huỷ.",
                      "truong": [
                          _o("lech_pt", "so", "% cách giá", min=0, max=50, mac_dinh=0.1),
                          _o("het_han", "so", "hạn", nguyen=True, min=1, max=10000,
                             mac_dinh=30, don_vi="nen"),
                          _o("phan_pt", "so", "% phần lệch", min=1, max=100, mac_dinh=100),
                      ]},
    "cho": {"tram": KHOP_LENH, "nhan": "Chờ", "vai": "quyet_dinh",
            "mo_ta": "Lượt này chưa đặt lệnh — lượt sau hỏi lại.", "truong": []},
}

#: Khối Làm nào trạm cần có ÍT NHẤT MỘT thì cỗ máy mới chạy ra được gì. Trạm ④ không có:
#: không quản rủi ro là một lựa chọn (QC cũng mặc định vậy), không phải lỗi.
CAN_CO = {
    CHON_MA: ("vao_ro",),
    TIN_HIEU: ("bao",),
    CHIA_VON: ("dat_ty_trong",),
    KHOP_LENH: ("lenh_thi_truong", "lenh_gioi_han", "lenh_cho_stop"),
}


def khoi_lam_cua_tram(tram):
    return [k for k, v in KHOI_LAM.items() if v["tram"] == tram]


# ---------------------------------------------------------------------------
# GOM — bước cuối của trạm, chạy MỘT LẦN cho cả trạm sau khi mọi đối tượng đã đi qua sơ đồ.
# ---------------------------------------------------------------------------
#: Sơ đồ trả lời từng mã một; có những câu chỉ trả lời được khi nhìn CẢ rổ (giữ 10 mã điểm
#: cao nhất, tổng tỷ trọng không quá ngân sách). Những câu đó nằm ở Gom, không ở khối nào.
GOM = {
    CHON_MA: [
        _o("top_n", "so", "giữ tối đa", nguyen=True, min=1, max=1000, tuy_chon=True,
           don_vi="ma"),
        _o("xep", "chon", "giữ mã điểm", chon={"cao": "cao nhất", "thap": "thấp nhất"},
           mac_dinh="cao"),
    ],
    CHIA_VON: [
        _o("giu_tien_pt", "so", "giữ tiền mặt %", min=0, max=99, mac_dinh=0),
        _o("tran_moi_ma_pt", "so", "trần mỗi mã %", min=1, max=100, mac_dinh=100),
        _o("chi_mua", "bat_tat", "chỉ mua, không bán khống", mac_dinh=True),
    ],
}
