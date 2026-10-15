"""MẪU DỰNG SẴN cho từng trạm — mô phỏng các mô hình có sẵn của QuantConnect.  (D-10, phần 3)

Mỗi mẫu là một SƠ ĐỒ dựng từ đúng những khối người chơi có trong tay — không có khối "bí
mật" nào. Chọn mẫu xong là mở ra xem được, sửa được, như sơ đồ tự vẽ. Núm vặn của mẫu (chu
kỳ, ngưỡng) thành THAM SỐ có tên của cỗ máy, nên chỉnh ở bảng tham số mà không phải lục khối.

Không có Markowitz / Black-Litterman: chúng cần ma trận hiệp phương sai, không phải thứ diễn
tả được bằng một sơ đồ đọc từng mã (để sau, nếu có khối Gom riêng cho chúng).
"""
import copy

from . import core
from . import may as M
from . import tram as T


def _dk(trai, phep, phai):
    return {"trai": trai, "phep": phep, "phai": phai}


def _ts(ten, gia_tri, nhan, don_vi=""):
    return core.make_tham_so(ten, nhan, gia_tri, don_vi)


def _so_do(bd, *nhanh):
    """Bắt đầu rẽ ra các nhánh, mỗi nhánh là một chuỗi khối. Nhánh xếp trái → phải và mỗi
    đầu nhánh thấp hơn nhánh trước 60 px — thứ tự thử phải NHÌN THẤY được (core §5)."""
    bd["pos"] = [80.0, 60.0]
    steps, edges = [bd], []
    for j, chuoi in enumerate(nhanh):
        truoc = bd["id"]
        for i, st in enumerate(chuoi):
            st["pos"] = [80.0 + 320.0 * j, 200.0 + 140.0 * i + 60.0 * j]
            steps.append(st)
            edges.append({"from": truoc, "to": st["id"], "port": "out"})
            truoc = st["id"]
    return steps, edges


def _bd(tram_key, **o):
    st = M.khoi_bat_dau(tram_key)
    st.update(o)
    return st


# ---------------------------------------------------------------------------
# ① Chọn mã
# ---------------------------------------------------------------------------
def _moi_ma(ma=None):
    pv = {"loai": "danh_sach", "ma": list(ma)} if ma else {"loai": "tat_ca"}
    return {"so_do": _so_do(_bd(T.CHON_MA, lich="bat_dau", pham_vi=pv),
                            [M.khoi_lam("vao_ro")])}


def _thanh_khoan(ma=None):
    diem = {"ten": "gia_tri_gd_tb", "khung": "D1", "chu_ky": "tk_chu_ky"}
    return {"so_do": _so_do(_bd(T.CHON_MA, lich="dau_thang"),
                            [M.khoi_lam("vao_ro", diem=diem)]),
            "gom": {"top_n": "so_ma", "xep": "cao"},
            "tham_so": [_ts("so_ma", 5, "giữ bao nhiêu mã"),
                        _ts("tk_chu_ky", 20, "thanh khoản: trung bình bao nhiêu ngày", "nen")]}


def _manh_nhat(ma=None):
    roc = {"ten": "roc_pt", "khung": "D1", "chu_ky": "dl_chu_ky"}
    return {"so_do": _so_do(_bd(T.CHON_MA, lich="dau_thang"),
                            [M.khoi_hoi([_dk(roc, ">", {"value": 0})], "Đang đi lên?"),
                             M.khoi_lam("vao_ro", diem=dict(roc))]),
            "gom": {"top_n": "so_ma", "xep": "cao"},
            "tham_so": [_ts("so_ma", 5, "giữ bao nhiêu mã"),
                        _ts("dl_chu_ky", 60, "động lượng: so với bao nhiêu ngày trước", "nen")]}


# ---------------------------------------------------------------------------
# ② Tín hiệu — phát lại MỖI nến, hạn ngắn: tín hiệu sống khi điều kiện còn đúng
# ---------------------------------------------------------------------------
def _hai_chieu(cong_len, ten_len, cong_xuong, ten_xuong, han, xuong="xuong", ts=()):
    return {"so_do": _so_do(_bd(T.TIN_HIEU),
                            [M.khoi_hoi(cong_len, ten_len),
                             M.khoi_lam("bao", huong="len", thoi_han=han)],
                            [M.khoi_hoi(cong_xuong, ten_xuong),
                             M.khoi_lam("bao", huong=xuong, thoi_han=han)]),
            "tham_so": list(ts)}


def _giao_cat_ema(ma=None):
    f, s = {"ten": "ema", "chu_ky": "ema_nhanh"}, {"ten": "ema", "chu_ky": "ema_cham"}
    return _hai_chieu([_dk(f, ">", s)], "EMA nhanh trên chậm?",
                      [_dk(dict(f), "<", dict(s))], "EMA nhanh dưới chậm?", 2,
                      ts=[_ts("ema_nhanh", 20, "EMA nhanh", "nen"),
                          _ts("ema_cham", 50, "EMA chậm", "nen")])


def _rsi(ma=None):
    r = {"ten": "rsi", "chu_ky": "rsi_chu_ky"}
    return _hai_chieu([_dk(r, "<", {"value": "rsi_duoi"})], "Quá bán?",
                      [_dk(dict(r), ">", {"value": "rsi_tren"})], "Quá mua?", 5,
                      ts=[_ts("rsi_chu_ky", 14, "chu kỳ RSI", "nen"),
                          _ts("rsi_duoi", 30, "RSI dưới mức này là quá bán"),
                          _ts("rsi_tren", 70, "RSI trên mức này là quá mua")])


def _macd(ma=None):
    h = {"ten": "macd", "dong": "histogram"}
    return _hai_chieu([_dk(h, ">", {"value": 0})], "MACD trên đường tín hiệu?",
                      [_dk(dict(h), "<", {"value": 0})], "MACD dưới đường tín hiệu?", 2)


def _dong_luong(ma=None):
    r = {"ten": "roc_pt", "chu_ky": "dl_chu_ky"}
    return _hai_chieu([_dk(r, ">", {"value": 0})], "Động lượng dương?",
                      [_dk(dict(r), "<=", {"value": 0})], "Động lượng âm?", 2,
                      xuong="dung_ngoai",
                      ts=[_ts("dl_chu_ky", 20, "động lượng: so với bao nhiêu nến trước",
                              "nen")])


def _gia_tren_ma(ma=None):
    c, s = {"ten": "gia_dong"}, {"ten": "sma", "chu_ky": "ma_chu_ky"}
    return _hai_chieu([_dk(c, ">", s)], "Giá trên MA?",
                      [_dk(dict(c), "<=", dict(s))], "Giá dưới MA?", 2, xuong="dung_ngoai",
                      ts=[_ts("ma_chu_ky", 200, "chu kỳ MA", "nen")])


def _pha_kenh(ma=None):
    c = {"ten": "gia_dong"}
    tren = {"ten": "donchian", "chu_ky": "kenh_chu_ky", "bien": "tren"}
    duoi = {"ten": "donchian", "chu_ky": "kenh_chu_ky", "bien": "duoi"}
    return _hai_chieu([_dk(c, ">", tren)], "Phá biên trên?",
                      [_dk(dict(c), "<", duoi)], "Phá biên dưới?", "kenh_han",
                      ts=[_ts("kenh_chu_ky", 20, "kênh: bao nhiêu nến", "nen"),
                          _ts("kenh_han", 20, "tín hiệu phá kênh sống bao nhiêu nến", "nen")])


# ---------------------------------------------------------------------------
# ③ Chia vốn
# ---------------------------------------------------------------------------
def _chia(cach, **o):
    def dung(ma=None):
        return {"so_do": _so_do(_bd(T.CHIA_VON),
                                [M.khoi_lam("dat_ty_trong", cach=cach, **o)])}
    return dung


# ---------------------------------------------------------------------------
# ④ Rủi ro
# ---------------------------------------------------------------------------
def _khong_quan(ma=None):
    return {"so_do": _so_do(_bd(T.RUI_RO))}


def _cat_ra(cong, ten, ts):
    return {"so_do": _so_do(_bd(T.RUI_RO),
                            [M.khoi_hoi(cong, ten), M.khoi_lam("dua_ve_0"),
                             M.khoi_lam("cam_vao_lai", so_nen="cam_nen")]),
            "tham_so": list(ts) + [_ts("cam_nen", 24, "cấm vào lại bao nhiêu nến", "nen")]}


def _cat_lo(ma=None):
    return _cat_ra([_dk({"ten": "lai_lo_pt"}, "<=", {"value": "lo_toi_da_pt"})], "Lỗ quá mức?",
                   [_ts("lo_toi_da_pt", -5, "lỗ tối đa mỗi mã (%, số âm)")])


def _chot_lai(ma=None):
    return _cat_ra([_dk({"ten": "lai_lo_pt"}, ">=", {"value": "chot_lai_pt"})], "Lãi đủ?",
                   [_ts("chot_lai_pt", 10, "chốt lời khi lãi mỗi mã đạt (%)")])


def _trailing(ma=None):
    return _cat_ra([_dk({"ten": "sut_tu_dinh_pt"}, ">=", {"value": "trailing_pt"})],
                   "Rơi từ đỉnh quá mức?",
                   [_ts("trailing_pt", 3, "trailing: rơi từ đỉnh bao nhiêu % thì bán")])


def _cau_dao(ma=None):
    return {"so_do": _so_do(_bd(T.RUI_RO),
                            [M.khoi_hoi([_dk({"ten": "sut_giam_tk_pt"}, ">=",
                                             {"value": "cau_dao_pt"})], "Tài khoản sụt quá mức?"),
                             M.khoi_lam("dung_tai_khoan")]),
            "tham_so": [_ts("cau_dao_pt", 10, "cầu dao: tài khoản sụt bao nhiêu % thì dừng")]}


# ---------------------------------------------------------------------------
# ⑤ Khớp lệnh
# ---------------------------------------------------------------------------
def _khop_ngay(ma=None):
    return {"so_do": _so_do(_bd(T.KHOP_LENH), [M.khoi_lam("lenh_thi_truong")])}


def _chia_lat(ma=None):
    return {"so_do": _so_do(_bd(T.KHOP_LENH, khung="M5"),
                            [M.khoi_lam("lenh_thi_truong", phan_pt="lat_pt")]),
            "tham_so": [_ts("lat_pt", 25, "mỗi lát khớp bao nhiêu % phần còn lệch")]}


def _do_lech_chuan(ma=None):
    lech = {"ten": "lech_muc_tieu_pt"}
    c = {"ten": "gia_dong", "khung": "M1"}
    bb = {"ten": "bollinger", "khung": "M1", "chu_ky": "dlc_chu_ky", "do_lech": "dlc_k"}
    return {"so_do": _so_do(
        _bd(T.KHOP_LENH),
        [M.khoi_hoi([_dk(lech, ">", {"value": 0}), _dk(c, "<", dict(bb, dai="duoi"))],
                    "Cần mua, giá đang thấp?"), M.khoi_lam("lenh_thi_truong")],
        [M.khoi_hoi([_dk(dict(lech), "<", {"value": 0}), _dk(dict(c), ">", dict(bb, dai="tren"))],
                    "Cần bán, giá đang cao?"), M.khoi_lam("lenh_thi_truong")],
        [M.khoi_lam("cho")]),
        "tham_so": [_ts("dlc_chu_ky", 60, "trung bình bao nhiêu phút", "nen"),
                    _ts("dlc_k", 2, "lệch bao nhiêu độ lệch chuẩn thì vào")]}


def _theo_spread(ma=None):
    return {"so_do": _so_do(
        _bd(T.KHOP_LENH),
        [M.khoi_hoi([_dk({"ten": "spread_pt"}, "<=", {"value": "spread_max_pt"})],
                    "Spread đủ hẹp?"), M.khoi_lam("lenh_thi_truong")],
        [M.khoi_lam("cho")]),
        "tham_so": [_ts("spread_max_pt", 0.05, "spread tối đa (% giá)")]}


# ---------------------------------------------------------------------------
# Danh mục
# ---------------------------------------------------------------------------
def _m(key, ten, qc, mo_ta, dung):
    return {"key": key, "ten": ten, "qc": qc, "mo_ta": mo_ta, "dung": dung}


MAU = {
    T.CHON_MA: [
        _m("moi_ma", "Mọi mã của màn", "ManualUniverseSelectionModel",
           "Rổ cố định: mọi mã của màn (hoặc danh sách riêng), chọn một lần lúc đầu.", _moi_ma),
        _m("thanh_khoan", "N mã thanh khoản nhất", "QC500 / lọc thô theo giá trị giao dịch",
           "Đầu mỗi tháng giữ N mã có giá trị giao dịch trung bình lớn nhất.", _thanh_khoan),
        _m("manh_nhat", "N mã mạnh nhất", "Momentum universe",
           "Đầu mỗi tháng giữ N mã tăng mạnh nhất trong các mã đang đi lên.", _manh_nhat),
    ],
    T.TIN_HIEU: [
        _m("giao_cat_ema", "Giao cắt EMA", "EmaCrossAlphaModel",
           "EMA nhanh trên EMA chậm → LÊN, dưới → XUỐNG.", _giao_cat_ema),
        _m("rsi", "RSI quá mua / quá bán", "RsiAlphaModel",
           "RSI dưới 30 → LÊN (bật lại), trên 70 → XUỐNG.", _rsi),
        _m("macd", "MACD", "MacdAlphaModel",
           "Đường MACD trên đường tín hiệu → LÊN, dưới → XUỐNG.", _macd),
        _m("dong_luong", "Động lượng", "MomentumAlphaModel",
           "Giá cao hơn N nến trước → LÊN, không thì đứng ngoài.", _dong_luong),
        _m("gia_tren_ma", "Giá trên MA", "—",
           "Giá đóng trên SMA 200 → LÊN, dưới → đứng ngoài.", _gia_tren_ma),
        _m("pha_kenh", "Phá kênh Donchian", "—",
           "Đóng cửa vượt đỉnh 20 nến → LÊN, thủng đáy 20 nến → XUỐNG.", _pha_kenh),
    ],
    T.CHIA_VON: [
        _m("chia_deu", "Chia đều", "EqualWeightingPortfolioConstructionModel",
           "Mọi mã báo LÊN chia đều ngân sách.", _chia("chia_deu")),
        _m("theo_tin_cay", "Theo độ tin cậy", "ConfidenceWeightedPortfolioConstructionModel",
           "Tín hiệu càng chắc càng nhiều vốn.", _chia("theo_tin_cay")),
        _m("theo_trong_so", "Theo trọng số tín hiệu", "InsightWeightingPortfolioConstructionModel",
           "Mỗi mã nhận đúng trọng số mà khối Báo đặt.", _chia("theo_trong_so")),
        _m("rui_ro_ngang", "Rủi ro ngang nhau", "RiskParityPortfolioConstructionModel (gần đúng)",
           "Mã càng giật (ATR % lớn) càng ít vốn.",
           _chia("rui_ro_ngang", khung="D1", chu_ky=20)),
    ],
    T.RUI_RO: [
        _m("khong", "Không quản rủi ro", "NullRiskManagementModel",
           "Để trạm ③ quyết hết.", _khong_quan),
        _m("cat_lo", "Cắt lỗ mỗi mã", "MaximumDrawdownPercentPerSecurity",
           "Lỗ quá 5% so với giá vốn → bán, cấm vào lại một lúc.", _cat_lo),
        _m("chot_lai", "Chốt lời mỗi mã", "MaximumUnrealizedProfitPercentPerSecurity",
           "Lãi đủ 10% → bán, cấm vào lại một lúc.", _chot_lai),
        _m("trailing", "Trailing stop", "TrailingStopRiskManagementModel",
           "Rơi 3% từ chỗ cao nhất kể từ lúc vào → bán.", _trailing),
        _m("cau_dao", "Cầu dao tài khoản", "MaximumDrawdownPercentPortfolio",
           "Cả tài khoản sụt 10% từ đỉnh → bán sạch, thôi giao dịch.", _cau_dao),
    ],
    T.KHOP_LENH: [
        _m("khop_ngay", "Khớp ngay", "ImmediateExecutionModel",
           "Lệch mục tiêu là đặt lệnh thị trường cho trọn phần lệch.", _khop_ngay),
        _m("chia_lat", "Chia lát", "VolumeWeightedAveragePriceExecutionModel (gần đúng)",
           "Mỗi 5 phút khớp 25% phần còn lệch — không đổ cả lệnh một lúc.", _chia_lat),
        _m("do_lech_chuan", "Theo độ lệch chuẩn", "StandardDeviationExecutionModel",
           "Chỉ mua khi giá thấp hơn trung bình 2 độ lệch chuẩn, bán khi cao hơn; không thì "
           "chờ.", _do_lech_chuan),
        _m("theo_spread", "Theo spread", "SpreadExecutionModel",
           "Chỉ khớp khi spread đủ hẹp; không thì chờ.", _theo_spread),
    ],
}
MAU_THEO_KEY = {(k, m["key"]): m for k, ds in MAU.items() for m in ds}


def ap_mau(may, tram_key, mau_key, ma=None):
    """Thay trạm `tram_key` của cỗ máy bằng mẫu `mau_key`. Trả bản MỚI (không sửa bản gốc).

    Tham số của mẫu được THÊM vào bảng; tên nào đã có thì GIỮ giá trị người chơi đã chỉnh —
    đổi mẫu không được lặng lẽ đặt lại núm vặn đã vặn."""
    d = MAU_THEO_KEY.get((tram_key, mau_key))
    if d is None:
        raise KeyError(f"Không có mẫu «{mau_key}» cho trạm {T.nhan_tram(tram_key)}.")
    ra = copy.deepcopy(may)
    x = d["dung"](ma)
    steps, edges = x["so_do"]
    g = {"steps": steps, "edges": edges}
    if tram_key in T.GOM:
        g["gom"] = dict(M._gom_mac_dinh(tram_key), **(x.get("gom") or {}))
    ra.setdefault("tram", {})[tram_key] = g
    co = {t["ten"] for t in ra.get("tham_so") or []}
    ra["tham_so"] = list(ra.get("tham_so") or []) + [
        t for t in x.get("tham_so") or [] if t["ten"] not in co]
    return M.chuan_hoa(ra)


#: Cỗ máy mẫu: đủ năm trạm, chạy được ngay — điểm khởi đầu cho người chơi mới.
MAY_MAU = {T.CHON_MA: "moi_ma", T.TIN_HIEU: "giao_cat_ema", T.CHIA_VON: "chia_deu",
           T.RUI_RO: "trailing", T.KHOP_LENH: "khop_ngay"}


def may_tu_mau(ten="Cỗ máy mẫu", chon=None, ma=None):
    m = M.may_moi(ten)
    for k, mau_key in dict(MAY_MAU, **(chon or {})).items():
        m = ap_mau(m, k, mau_key, ma)
    return m


# ---------------------------------------------------------------------------
# CỖ MÁY DỰNG SẴN của chương 1  (D-10, phần 6)
# ---------------------------------------------------------------------------
#: Bốn cỗ máy, bốn Ý TƯỞNG khác hẳn nhau — không phải bốn biến thể của một cái. Người chơi
#: mới mở một cái ra là có thứ CHẠY ĐƯỢC để đọc và sửa; người chơi cũ lấy chúng làm điểm so.
#:
#: Mỗi cái chỉ là một bộ năm mẫu dựng sẵn, không có khối bí mật nào: mở ra thấy đúng những
#: khối tự vẽ được. Tên và mô tả nói đúng việc nó làm, không hứa lãi.
MAY_SAN = (
    {"key": "theo_ema", "ten": "Theo EMA",
     "mo_ta": "Bám xu hướng: EMA nhanh cắt lên EMA chậm thì LÊN, cắt xuống thì XUỐNG. "
              "Chia đều vốn, trailing stop giữ lãi, khớp lệnh ngay.",
     "chon": dict(MAY_MAU)},
    {"key": "bat_day_rsi", "ten": "Bắt đáy RSI",
     "mo_ta": "Ngược xu hướng: RSI dưới 30 thì LÊN, trên 70 thì XUỐNG. Cắt lỗ mỗi mã, "
              "khớp ngay — hợp với thị trường đi ngang.",
     "chon": {T.CHON_MA: "moi_ma", T.TIN_HIEU: "rsi", T.CHIA_VON: "chia_deu",
              T.RUI_RO: "cat_lo", T.KHOP_LENH: "khop_ngay"}},
    {"key": "manh_nhat", "ten": "Chọn mã mạnh nhất",
     "mo_ta": "Mỗi đầu tháng giữ lại N mã tăng mạnh nhất, rồi theo động lượng của chúng. "
              "Chia đều phần vốn cho những mã còn lại, và chia lát khi đặt lệnh — không "
              "đổ cả lệnh vào một phút.",
     # ③ cố ý KHÔNG dùng «theo độ tin cậy»: mẫu ② «Động lượng» không đặt độ tin cậy, nên
     # ghép vào là cỗ máy mẫu mở ra đã có sẵn một cảnh báo — thứ tệ nhất để đưa cho người
     # chơi mới, vì họ không biết đó là lỗi của mẫu hay của mình.
     "chon": {T.CHON_MA: "manh_nhat", T.TIN_HIEU: "dong_luong",
              T.CHIA_VON: "chia_deu", T.RUI_RO: "trailing",
              T.KHOP_LENH: "chia_lat"}},
    {"key": "than_trong", "ten": "Thận trọng",
     "mo_ta": "Chỉ nhìn mã thanh khoản nhất, chỉ vào khi giá trên SMA 200, mã càng giật "
              "càng ít vốn, và có cầu dao cho cả tài khoản.",
     "chon": {T.CHON_MA: "thanh_khoan", T.TIN_HIEU: "gia_tren_ma",
              T.CHIA_VON: "rui_ro_ngang", T.RUI_RO: "cau_dao",
              T.KHOP_LENH: "khop_ngay"}},
)
MAY_SAN_THEO_KEY = {m["key"]: m for m in MAY_SAN}


def may_san(key, ma=None):
    """Một cỗ máy dựng sẵn của chương 1, dựng từ chính các mẫu của từng trạm."""
    d = MAY_SAN_THEO_KEY.get(key)
    if d is None:
        raise KeyError(f"Không có cỗ máy dựng sẵn «{key}».")
    return may_tu_mau(d["ten"], d["chon"], ma)
