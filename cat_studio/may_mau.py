"""CỖ MÁY GỢI Ý của chế độ Chiến dịch — máy mới, dựng cho người mới, KHÔNG phải Compress.

Mỗi màn có thể gợi ý một cỗ máy để bắt đầu (như câu đố đầu của một game lắp máy: đưa sẵn
một cỗ máy chạy được, để người chơi bấm ▶ trước rồi mới học sửa). Máy ở đây cố ý NHỎ:
vài khối, vài tham số — đủ để thấy trọn vòng chơi, và để độ gọn có chỗ mà tốt lên.

Dựng bằng code, ID CỐ ĐỊNH (cùng lý do với `mau.py`: vân tay của một hằng số phải không
đổi giữa các lần mở). Mọi khung đều nằm trong `cat_lean.KHUNG_HO_TRO` (chạy được trên QC).
"""
from . import core

#: Khối lượng mặc định của máy gợi ý: ~0,05 lot vàng ≈ dùng trọn 10.000 $ mà không đòn
#: bẩy — để so với boss "Mua rồi giữ" (cũng dùng trọn vốn, không đòn bẩy) là so công bằng.
LOT_MAC_DINH = 0.05


def _dung(ten_may, tien_to):
    dem = [0]

    def ma():
        dem[0] += 1
        return f"{tien_to}{dem[0]:02d}"

    def dk(ten, conds, x, y):
        s = core.make_action_step({"id": ma(), "type": core.CHECK_COND, "name": ten,
                                   "conditions": conds})
        s["pos"] = [x, y]
        return s

    def hd(ten, act, x, y):
        s = core.make_action_step(dict(act, id=ma(), name=ten))
        s["pos"] = [x, y]
        return s

    def bd(ten, nhip, tab):
        s = core.make_start_step(ten, nhip)
        s["id"] = f"{tien_to}-bd-{tab}"
        s["pos"] = [40, 240]
        return s

    def canh(a, b):
        return {"from": a["id"], "to": b["id"], "port": "out",
                "from_side": "right", "to_side": "left"}

    return ma, dk, hd, bd, canh


def _gia_vs_ma(phep):
    return {"trai": {"ten": "close", "tf": "H1"}, "phep": phep,
            "phai": {"ten": "ma", "tf": "H1", "period": "chu_ky_ma", "method": "SMA"}}


_TAY_TRONG = {"trai": {"ten": "so_vi_the"}, "phep": "==", "phai": {"value": 0}}


def _vao(huong, tp=None):
    a = {"type": core.VAO_LENH, "huong": huong, "loai": "market", "lot": "lot",
         "entry": {"moc": "gia_hien_tai"}, "sl": {"tinh": "atr", "value": "sl_atr"}}
    if tp:
        a["tp"] = tp
    return a


def _tham_so(*them):
    ds = [
        {"ten": "chu_ky_ma", "nhan": "Chu kỳ MA", "gia_tri": 50, "don_vi": "nen",
         "ghi_chu": "Đường trung bình của bao nhiêu nến H1."},
        {"ten": "sl_atr", "nhan": "Stop Loss", "gia_tri": 3.0, "don_vi": "atr",
         "ghi_chu": "Cách giá vào bao nhiêu lần ATR — định nghĩa 1R."},
        {"ten": "lot", "nhan": "Khối lượng", "gia_tri": LOT_MAC_DINH, "don_vi": "lot",
         "ghi_chu": "≈ dùng trọn vốn, không đòn bẩy — so công bằng với boss."},
        {"ten": "chu_ky_atr", "nhan": "Chu kỳ ATR", "gia_tri": 14, "don_vi": "nen",
         "ghi_chu": "ATR dùng để đo SL."},
    ]
    return ds + list(them)


#: Khoảng cách ngang giữa hai khối liền nhau. Hộp rộng ~300 px — 380 để dây nối còn chỗ.
_X = 380


def theo_ma():
    """MÁY ĐẦU TAY — 5 khối: tay trống và giá trên MA thì mua, giá cắt xuống MA thì đóng.

    Cỗ máy đơn giản nhất mà vẫn là một cỗ máy thật: có mắt, có tay (vào lệnh), có tay
    chỉnh (kết thúc lệnh), có SL. Màn 1-1 đưa sẵn nó để người chơi bấm ▶ ngay.

    "Tay đang trống?" và "Giá trên MA?" là HAI cổng nối tiếp, không gộp một: một cổng chỉ
    một cơ chế so — so với một con số, HOẶC so hai đại lượng (`core.normalize_process`).
    Gộp vào là chuẩn hoá xong vế phải `0` rơi mất, trình vẽ báo lỗi ngay khi lắp máy.
    Nối tiếp chính là VÀ."""
    ma, dk, hd, bd, canh = _dung("Theo MA", "tma")
    e_bd = bd("Mỗi giờ", "H1", "entry")
    e_trong = dk("Tay đang trống?", [_TAY_TRONG], 40 + _X, 240)
    e_mat = dk("Giá trên MA?", [_gia_vs_ma(">")], 40 + 2 * _X, 240)
    e_tay = hd("Mua", _vao("mua"), 40 + 3 * _X, 240)
    m_bd = bd("Trông lệnh mỗi giờ", "H1", "manage")
    m_mat = dk("Giá cắt xuống MA?", [_gia_vs_ma("<")], 40 + _X, 240)
    m_tay = hd("Đóng lệnh", {"type": core.SUA_LENH, "che_do": "ket_thuc"}, 40 + 2 * _X, 240)
    return {"schema": 3, "type": "strategy", "name": "Theo MA", "symbol": "XAUUSD",
            "tham_so": _tham_so(),
            "entry": {"steps": [e_bd, e_trong, e_mat, e_tay],
                      "edges": [canh(e_bd, e_trong), canh(e_trong, e_mat),
                                canh(e_mat, e_tay)]},
            "manage": {"steps": [m_bd, m_mat, m_tay],
                       "edges": [canh(m_bd, m_mat), canh(m_mat, m_tay)]}}


def hai_chieu():
    """HAI CHIỀU — 7 khối: tay trống thì xem giá: trên MA mua, dưới MA bán; chốt ở bội R;
    đủ 1R thì dời SL về hoà vốn. Gợi ý cho màn dạy rẽ nhánh và dời hoà vốn.

    "Tay đang trống?" là MỘT cổng chung đứng trước ngã rẽ — không lặp lại ở hai nhánh, nên
    con số 0 chỉ nằm một chỗ (và người chơi thấy luôn cách một cổng gác cả hai nhánh)."""
    ma, dk, hd, bd, canh = _dung("Hai chiều", "hc")
    tp = {"tinh": "R", "value": "chot_R"}
    e_bd = bd("Mỗi giờ", "H1", "entry")
    e_trong = dk("Tay đang trống?", [_TAY_TRONG], 40 + _X, 240)
    e_len = dk("Giá trên MA?", [_gia_vs_ma(">")], 40 + 2 * _X, 110)
    e_mua = hd("Mua", _vao("mua", tp), 40 + 3 * _X, 110)
    e_xuong = dk("Giá dưới MA?", [_gia_vs_ma("<")], 40 + 2 * _X, 370)
    e_ban = hd("Bán", _vao("ban", tp), 40 + 3 * _X, 370)
    m_bd = bd("Trông lệnh mỗi giờ", "H1", "manage")
    m_be = dk("Lãi đủ 1R, SL chưa hoà vốn?", [
        {"trai": {"ten": "lenh_da_khop"}, "phep": "la_dung"},
        {"trai": {"ten": "lenh_sl_hoa_von"}, "phep": "la_sai"},
        {"trai": {"ten": "lenh_lai_R"}, "phep": ">=", "phai": {"value": 1}},
    ], 40 + _X, 240)
    m_tay = hd("Dời SL về hoà vốn", {"type": core.SUA_LENH, "che_do": "hoa_von"},
               40 + 2 * _X, 240)
    return {"schema": 3, "type": "strategy", "name": "Hai chiều", "symbol": "XAUUSD",
            "tham_so": _tham_so({"ten": "chot_R", "nhan": "Chốt lời", "gia_tri": 2.0,
                                 "don_vi": "R", "ghi_chu": "Chốt ở bao nhiêu R."}),
            "entry": {"steps": [e_bd, e_trong, e_len, e_mua, e_xuong, e_ban],
                      "edges": [canh(e_bd, e_trong), canh(e_trong, e_len), canh(e_len, e_mua),
                                canh(e_trong, e_xuong), canh(e_xuong, e_ban)]},
            "manage": {"steps": [m_bd, m_be, m_tay],
                       "edges": [canh(m_bd, m_be), canh(m_be, m_tay)]}}


#: Tên máy → hàm dựng. `game.MAN[...]["may_goi_y"]` trỏ vào đây.
MAY = {"theo_ma": theo_ma, "hai_chieu": hai_chieu}

#: Tên HIỆN của từng máy — lấy từ chính cỗ máy, để nút "Lắp máy gợi ý «…»" không bao giờ
#: nói một tên khác với cái nó lắp.
TEN_MAY = {k: f()["name"] for k, f in MAY.items()}


def may(ten):
    return MAY[ten]()
