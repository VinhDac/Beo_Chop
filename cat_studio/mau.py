"""SƠ ĐỒ MẪU — chiến lược Compress (D_02), dựng bằng code, ID cố định.

Tách khỏi `api.py` để dùng được ở nơi KHÔNG có giao diện: `api` nạp kèm cửa sổ Win32 và
MetaTrader5, còn công cụ đóng gói sang QuantConnect (`tools/dong_goi_lean.py`) và bài kiểm
chạy trên máy không có cả hai. Nội dung giữ NGUYÊN VĂN — chỉ đổi chỗ ở, không đổi một khối,
một id hay một tham số nào, nên vân tay của sơ đồ mẫu không đổi.
"""
from . import core
from . import kho

# ---------------------------------------------------------------------------
# Sơ đồ mẫu — chiến lược Compress (D_02)
# ---------------------------------------------------------------------------
#
# Chép lại từ EA thật:
#   MQL5\Experts\D_02_Compress\Projects\Experts\Compress.mq5
#                             \Include\Controller\{FilterEngine,TradeManager}.mqh
#
# HAI SƠ ĐỒ, và ranh giới giữa chúng là điều quan trọng nhất:
#
#   ENTRY   chạy MỘT lượt mỗi nến, đi săn tín hiệu. Chỉ nó được TẠO lệnh.
#   MANAGE  chạy MỘT LƯỢT CHO MỖI LỆNH đang sống, cũng mỗi nến. Chỉ nó được SỬA lệnh.
#
# Thứ tự trong một nến: MANAGE trước, ENTRY sau — đúng `OnTick`:
#     CheckPendingActivation → ManageBreakEven → rồi mới tới phần quyết định.
# Chạy ngược lại thì lệnh vừa sinh bị quản lý ngay trong chính nến đẻ ra nó.
#
# BA THỨ D_02 PHẢI GIẤU TRONG C++, Ở ĐÂY HIỆN RA THÀNH CỔNG:
#
#   `if(m_has_pending) return false`      → điều kiện "số lệnh chờ = 0"
#   `if(pos_count >= max_positions) skip` → điều kiện "số vị thế < 3"
#   `if(sl >= entry) continue`            → điều kiện "SL chưa ở hoà vốn"
#
# VÀ `COMP_CONSUMED` KHÔNG CẦN CỜ ẨN: lệnh mang `vùng_id`, nên "vùng này đã sinh lệnh"
# chỉ là một phép tra bảng — có lệnh nào trỏ về vùng hiện hành không.


def so_do_mau():
    """Compress: biến động co lại như lò xo → đặt lệnh chờ ngay mép vùng → phá ra là khớp.

    Mọi khoảng cách là bội của ATR hoặc của R, không một pip hay đô nào — nên cùng một
    bộ số mang cùng một ý nghĩa trên vàng, forex, crypto và chỉ số."""

    # ⚠ ID CỐ ĐỊNH, không phải id sinh ngẫu nhiên. Sơ đồ mẫu là một HẰNG SỐ, nên nó phải
    # ra y hệt nhau mỗi lần mở. Trước đây mỗi lần mở lại sinh ids mới, mà `_van_tay` băm
    # cả id — thành ra mở sơ đồ mẫu hai lần là hai "chiến lược khác nhau": lịch sử đẻ hai
    # dòng trùng hệt, và "so với lần trước" lúc nào cũng nói "sơ đồ ĐÃ ĐỔI".
    # Id chỉ cần duy nhất TRONG MỘT tài liệu, nên đặt cứng ở đây hoàn toàn an toàn — và
    # nhập sơ đồ này vào một sơ đồ khác thì `clone_steps` vẫn cấp id mới như thường.
    dem = [0]

    def _ma():
        dem[0] += 1
        return f"mau{dem[0]:02d}"

    def dk(ten, conds, x, y, cong_zone=False):
        a = {"id": _ma(), "type": core.CHECK_COND, "name": ten, "conditions": conds}
        if cong_zone:
            a["cong_zone"] = True
        s = core.make_action_step(a)
        s["pos"] = [x, y]
        return s

    def hd(ten, act, x, y):
        s = core.make_action_step(dict(act, id=_ma(), name=ten))
        s["pos"] = [x, y]
        return s

    def so(ten, phep, gia_tri, **kw):
        return {"trai": dict({"ten": ten}, **kw), "phep": phep,
                "phai": {"value": gia_tri}}

    def ts(ten, phep, ten_tham_so, **kw):
        """Vế phải là một THAM SỐ CÓ TÊN, không phải số gõ tay.

        Nhờ vậy `nguong_nen_bps` chỉ tồn tại ở MỘT chỗ, dù nó được hỏi ở cả hai sơ đồ —
        Entry hỏi "còn nén không", Manage hỏi "nén tan chưa". Gõ tay hai nơi thì sửa
        một chỗ là hai vế lệch nhau âm thầm."""
        return {"trai": dict({"ten": ten}, **kw), "phep": phep,
                "phai": {"value": ten_tham_so}}

    def ts_dv(ten, phep, ten_tham_so, don_vi, **kw):
        """Như `ts` nhưng có ĐƠN VỊ — vế trái được quy đổi trước khi so.

        `atr < nguong_nen_bps [bps]` thay cho toán hạng `atr_bps` cũ. Đại lượng nằm
        trong kho, thước nằm ở dòng điều kiện."""
        c = ts(ten, phep, ten_tham_so, **kw)
        c["phai"]["tinh"] = don_vi          # ĐƠN VỊ nằm trong LƯỢNG, như SL/TP
        return c

    def dung_sai(ten, dao=False):
        # ĐÚNG/SAI là một PHÉP SO, không phải ô tick — mọi điều kiện cùng hình dạng.
        return {"trai": {"ten": ten}, "phep": "la_sai" if dao else "la_dung"}

    def canh(a, b):
        return {"from": a["id"], "to": b["id"], "port": "out",
                "from_side": "right", "to_side": "left"}

    # ========================= ENTRY =========================
    e_bd = core.make_start_step("Tìm tín hiệu", core.NHIP_MAC_DINH[core.TAB_ENTRY])
    e_bd["id"] = "mau-bd-entry"
    e_bd["pos"] = [40, 300]

    # ⭐ CỔNG ZONE — chính cổng này ĐỊNH NGHĨA zone.
    #
    # Trước đây bốn điều kiện dưới đây nằm CHUNG một khối, còn việc đếm nến nén thì do
    # một cỗ máy ẩn chạy ngoài sơ đồ. Nhìn khối không biết zone sinh ra từ đâu.
    #
    # Giờ tách đôi, và thứ tự nói lên đúng nhân quả:
    #   khối này  = ĐIỀU KIỆN ĐẾM. Qua thì zone lớn thêm một nến, trượt thì zone chết.
    #   khối sau  = hỏi về zone VỪA ĐƯỢC ĐỊNH NGHĨA ở trên.
    # Không có khối này thì `zone_dem`, `zone_HH`… không có nghĩa gì cả.
    e_nen = dk("Nến này có nén không?", [
        ts_dv("atr", "<", "nguong_nen_bps", "bps", tf="M5", period="chu_ky_atr"),
    ], 340, 300, cong_zone=True)

    e_zone = dk("Zone đã đủ điều kiện chưa?", [
        ts("zone_dem", ">=", "zone_can_nen"),           # đủ K nến liên tiếp
        ts_dv("zone_range", "<=", "zone_range_max", "atr"),  # zone không quá rộng
        dung_sai("zone_da_sinh_lenh", dao=True),        # = COMP_CONSUMED
    ], 640, 300)

    e_cho = dk("Còn chỗ cho lệnh mới?", [
        so("so_lenh_cho", "==", 0),      # D_02: đúng MỘT lệnh chờ tại một thời điểm
        ts("so_vi_the", "<", "so_vi_the_toi_da"),   # bằng nhau là đã đầy
    ], 940, 300)

    def vao(huong):
        return {
            "type": core.VAO_LENH, "huong": huong, "loai": "stop", "lot": "lot",
            # Đệm đo bằng ATR HIỆN TẠI — tấm khiên mỏng ngoài mép vùng, đủ lọc một
            # nhịp phá giả. Lệnh chờ luôn neo vào mép vùng thuận chiều.
            "dem": {"tinh": "atr", "value": "dem_vao_lenh"},
            # Rủi ro đo bằng ATR TRUNG BÌNH CẢ VÙNG NÉN — lấy mức nhiễu thật suốt cú
            # nén, nên mỗi lệnh rủi ro một R tương đương dù vùng rộng hẹp khác nhau.
            # HAI CHỮ ATR NÀY LÀ HAI THỨ KHÁC NHAU, tách ra là có chủ ý.
            "sl": {"tinh": "atr_zone", "value": "sl_theo_atr_vung"},
            "tp": {"tinh": "R", "value": "ty_le_RR"},
            # MỐC NEO hiện ra thành một trường, không còn suy ra từ hướng lệnh nữa.
            # `entry = HH của zone + đệm` giờ đọc thẳng được trên khối.
            "entry": {"moc": "zone_HH" if huong == "mua" else "zone_LL"},
        }

    e_len = dk("Xu hướng LÊN?", [{
        "trai": {"ten": "close", "tf": "M15"}, "phep": ">",
        "phai": {"ten": "ma", "tf": "M15", "period": "chu_ky_ma",
                 "method": "SMA"}}], 1060, 160)
    e_mua = hd("Buy Stop trên đỉnh vùng", vao("mua"), 1660, 160)

    e_xuong = dk("Xu hướng XUỐNG?", [{
        "trai": {"ten": "close", "tf": "M15"}, "phep": "<",
        "phai": {"ten": "ma", "tf": "M15", "period": "chu_ky_ma",
                 "method": "SMA"}}], 1060, 440)
    e_ban = hd("Sell Stop dưới đáy vùng", vao("ban"), 1660, 440)

    entry = {
        "steps": [e_bd, e_nen, e_zone, e_cho, e_len, e_mua, e_xuong, e_ban],
        "edges": [canh(e_bd, e_nen), canh(e_nen, e_zone), canh(e_zone, e_cho),
                  canh(e_cho, e_len), canh(e_len, e_mua),
                  canh(e_cho, e_xuong), canh(e_xuong, e_ban)],
    }

    # ========================= MANAGE =========================
    # Chạy lại từ đầu mỗi nến, CHO TỪNG LỆNH. Không giữ con trỏ — mọi câu hỏi đều tính
    # lại từ trạng thái quan sát được, y như D_02 làm mỗi tick.
    m_bd = core.make_start_step("Quản lý lệnh", core.NHIP_MAC_DINH[core.TAB_MANAGE])
    m_bd["id"] = "mau-bd-manage"
    m_bd["pos"] = [40, 300]

    m_huy = dk("Chưa khớp mà nén đã tan?", [
        dung_sai("lenh_da_khop", dao=True),
        # CÙNG một `nguong_nen_bps` với cổng nén bên Entry — đây chính là chỗ hai
        # hằng số gõ tay sẽ lệch nhau nếu không có bảng tham số.
        ts_dv("atr", ">=", "nguong_nen_bps", "bps", tf="M5", period="chu_ky_atr"),
    ], 400, 160)
    m_huy_hd = hd("Huỷ lệnh chờ",
                  {"type": core.SUA_LENH, "che_do": "ket_thuc"}, 760, 160)

    # Ba dòng guard của `ManageBreakEven` gói đúng vào một cổng. Vế "SL chưa ở hoà vốn"
    # KHÔNG được thiếu: Manage chạy lại mỗi nến, không có nó thì lệnh sửa SL bắn hoài.
    m_be = dk("Đã khớp, đủ 1R, SL chưa hoà vốn?", [
        dung_sai("lenh_da_khop"),
        dung_sai("lenh_sl_hoa_von", dao=True),
        ts("lenh_lai_R", ">=", "hoa_von_tai"),
    ], 400, 440)
    m_be_hd = hd("Dời SL về giá vào",
                 {"type": core.SUA_LENH, "che_do": "hoa_von"}, 760, 440)

    manage = {
        "steps": [m_bd, m_huy, m_huy_hd, m_be, m_be_hd],
        "edges": [canh(m_bd, m_huy), canh(m_huy, m_huy_hd),
                  canh(m_bd, m_be), canh(m_be, m_be_hd)],
    }

    return {"schema": 3, "type": "strategy", "name": "Compress (mẫu)",
            "symbol": "XAUUSD",
            # Bộ tham số lấy thẳng từ `kho/engine_d02.py` — cùng một nguồn với mặc
            # định của EA, nên không có chuyện tài liệu nói một đằng mẫu chạy một nẻo.
            "tham_so": [dict(t) for t in kho.engine_d02.THAM_SO_MAC_DINH],
            "entry": entry, "manage": manage}
