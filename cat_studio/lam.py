"""TỪ ĐIỂN KHỐI HÀNH ĐỘNG — những việc sơ đồ làm được với thị trường.

Cùng luật với `hoi.py`: **mỗi khối phải chỉ ra được MỘT hàm có thật của LEAN** (ô
`lean`). Không khai được thì không được có mặt. Mọi chữ ký ở đây đọc THẲNG từ
`Algorithm/QCAlgorithm.Trading.cs`, `Common/Securities/SecurityTransactionManager.cs`,
`Common/Notifications/NotificationManager.cs`.

KHÁC `hoi.py` Ở HÌNH DẠNG: một khối Hỏi là N dòng điều kiện giống nhau; một khối Làm
là một bộ Ô CỐ ĐỊNH do loại của nó quyết định. Nên ở đây không có "kho đại lượng dùng
chung" — mỗi loại khai ô của riêng nó.

MỘT ĐƯỜNG RANH ĐÃ VẠCH, và vạch có lý do:
  ✅ ĐẶT lệnh chờ, và HUỶ HẾT lệnh chờ của một mã — `CancelOpenOrders(sym)` là một câu,
     app không phải nhớ gì.
  ❌ SỬA một lệnh cụ thể (`ticket.UpdateStopPrice`) — phải giữ cái ticket qua nhiều
     nến, tức sơ đồ sinh ra trạng thái, tức app lại có backend để mà gỡ lỗi.
  Muốn dời cắt lỗ thì: huỷ hết → đặt lại. Hai khối, không nhớ gì.

CỐ Ý BỎ: `ComboMarketOrder` / `ComboLimitOrder` / `ComboLegLimitOrder` /
`ExerciseOption` — lệnh quyền chọn nhiều chân, cần cả một bộ chọn chuỗi quyền chọn.
Ghi lại để biết là bỏ có chủ ý, không phải quên.
"""

# ---------------------------------------------------------------------------
# Kiểu của một ô
# ---------------------------------------------------------------------------
O_SO = "so"                  # một con số
O_CHU = "chu"                # một dòng chữ
O_CHON = "chon"              # một trong mấy lựa chọn
O_CO_KHONG = "co_khong"      # ô tích

#: Hai NHÓM trên ribbon. Tám nút một hàng thì thanh công cụ dài quá khổ cửa sổ, mà
#: chúng cũng khác hẳn nhau: năm cái ĐỤNG VÀO thị trường, ba cái chỉ ghi ra ngoài.
NHOM_LENH = "Lệnh"
NHOM_GHI = "Ghi & báo"
#: Nhóm thứ ba — nói với DÂY CHUYỀN của LEAN thay vì tự đặt lệnh. Xem `TIN_HIEU`.
NHOM_TIN_HIEU = "Tín hiệu"


def _o(ten, nhan, kieu, mac_dinh, don_vi="", goi_y="", chon=(), bat_buoc=True):
    return {"ten": ten, "nhan": nhan, "kieu": kieu, "mac_dinh": mac_dinh,
            "don_vi": don_vi, "goi_y": goi_y, "chon": list(chon),
            "bat_buoc": bat_buoc}


#: Ô `tag` có mặt trên MỌI khối hành động — câu chữ đi theo lệnh sang LEAN.
#: Để trống thì bộ sinh mã tự điền số khối + điều kiện vừa khớp. Đó là lời hứa D-11
#: "chữ vì sao do chính đoạn code tự ghi", và nó miễn phí vì LEAN nhận sẵn tham số này.
O_TAG = _o("tag", "Ghi chú đi kèm lệnh", O_CHU, "", "",
           "Để trống = tự điền số khối và điều kiện vừa khớp.", bat_buoc=False)

#: Số lượng ÂM = bán khống. LEAN nhận số âm ở mọi hàm đặt lệnh, không có hàm riêng.
_O_SO_LUONG = _o("so_luong", "Số lượng", O_SO, 1, "đơn vị",
                 "Số âm = bán khống.")

#: Ô MÃ — có mặt trên mọi khối đụng tới một mã.
#:
#: Để trống = **mã đang xét**, tức biến vòng lặp khi khối Bắt đầu chạy "mỗi mã một
#: lượt". Nhưng khi nó chạy "một lượt cho CẢ RỔ" thì không có mã đang xét nào cả —
#: lúc ấy ô này BẮT BUỘC, và `core.soat_khoi_lam` bắt chỗ bỏ trống.
#:
#: Thiếu ô này thì không viết nổi `set_holdings(QQQ, 0.40)` — tức không diễn đạt
#: được bất cứ chiến thuật chia danh mục nào.
#: ⚠ Giao diện bày ô này là Ô CHỌN, danh sách lấy từ khối Bắt đầu — không cho gõ.
#: Nên câu gợi ý đừng nói "để trống" như một việc người dùng tự làm: lúc chạy cho cả
#: rổ thì «mã đang xét» KHÔNG CÓ TRONG DANH SÁCH, chứ không phải có mà bị cấm.
O_MA = _o("ma", "Mã", O_CHU, "", "",
          "Chọn trong mấy mã khối Bắt đầu đã khai. «Mã đang xét» chỉ có khi khối "
          "Bắt đầu chạy TỪNG MÃ một.",
          bat_buoc=False)


# ---------------------------------------------------------------------------
# ① ĐẶT TỶ TRỌNG — cách dùng nhiều nhất
# ---------------------------------------------------------------------------
# Khai "muốn giữ bao nhiêu phần danh mục", LEAN tự tính số lượng, tự tính phần chênh
# so với đang giữ, tự gửi lệnh. Người chơi không phải nghĩ tới số cổ phiếu, lô tối
# thiểu hay ký quỹ — đó là việc LEAN đã làm.
#
# ⚠ LƯU Ở DẠNG CỦA LEAN: 0.30 chứ không phải 30. Hộp thoại hiện % cho dễ đọc, nhưng
# file ghi đúng con số LEAN nhận — để không ai phải nhớ "chỗ nào nhân 100".
DAT_TY_TRONG = {
    "nhan": "Đặt tỷ trọng",
    "mo_ta": "cho mã này bao nhiêu phần vốn — lo cả vào, thêm, bớt, thoát",
    "icon": "dat-co",
    "nhom": NHOM_LENH,
    "can_ma": True,
    "lean": "self.set_holdings({sym}, {ty_trong}, {ban_sach_truoc}, tag={tag})",
    "o": [
        O_MA,
        _o("ty_trong", "Tỷ trọng mục tiêu", O_SO, 0.3, "phần",
           "0.3 = 30% danh mục. Số âm = bán khống. 0 = thoát sạch."),
        _o("ban_sach_truoc", "Bán sạch mã khác trước", O_CO_KHONG, False, "",
           "Bật thì mọi mã KHÁC bị bán sạch trước khi vào mã này.", bat_buoc=False),
        O_TAG,
    ],
}

# ---------------------------------------------------------------------------
# ② LỆNH THỊ TRƯỜNG — theo SỐ LƯỢNG, khớp ngay
# ---------------------------------------------------------------------------
LENH_THI_TRUONG = {
    "nhan": "Lệnh thị trường",
    "mo_ta": "mua/bán ngay theo số lượng, không theo tỷ trọng",
    "icon": "vao-lenh",
    "nhom": NHOM_LENH,
    "can_ma": True,
    "lean": "self.market_order({sym}, {so_luong}, tag={tag})",
    "o": [O_MA, _O_SO_LUONG, O_TAG],
}

# ---------------------------------------------------------------------------
# ③ ĐÓNG
# ---------------------------------------------------------------------------
DONG = {
    "nhan": "Đóng",
    "mo_ta": "bán sạch mã này, hoặc sạch tất cả",
    "icon": "minus",
    "nhom": NHOM_LENH,
    "can_ma": True,
    "lean": "self.liquidate(…)",
    "o": [
        O_MA,
        _o("pham_vi", "Đóng cái gì", O_CHON, "ma_nay", "", "", [
            ("ma_nay", "Chỉ mã này"),
            ("tat_ca", "TẤT CẢ mã đang giữ"),
        ]),
        O_TAG,
    ],
    # Hai phạm vi là HAI câu gọi khác nhau của LEAN, nên mỗi cái một mẫu riêng.
    "theo_loai": {
        "ma_nay": {"lean": "self.liquidate({sym}, tag={tag})", "o": []},
        "tat_ca": {"lean": "self.liquidate(tag={tag})", "o": []},
    },
}

# ---------------------------------------------------------------------------
# ④ LỆNH CHỜ — nằm trên sàn, khớp sau
# ---------------------------------------------------------------------------
# Bảy loại, mỗi loại cần ô khác nhau — nên `loai_lenh` là ô CHỌN, và mỗi lựa chọn mang
# theo ô riêng của nó (`o_them`). Cùng lối với chỉ báo trong `hoi.py`: chọn RSI thì ô
# "Chu kỳ" mới hiện ra.
LENH_CHO = {
    "nhan": "Lệnh chờ",
    "mo_ta": "đặt lệnh nằm trên sàn, khớp khi giá chạm điều kiện",
    "icon": "an-lenh",
    "nhom": NHOM_LENH,
    "can_ma": True,
    "lean": "LimitOrder / StopMarketOrder / StopLimitOrder / TrailingStopOrder / "
            "LimitIfTouchedOrder / MarketOnOpenOrder / MarketOnCloseOrder",
    "o": [
        O_MA,
        _o("loai_lenh", "Loại lệnh", O_CHON, "limit", "", "", [
            ("limit", "Giới hạn (Limit)"),
            ("stop", "Dừng (Stop Market)"),
            ("stop_limit", "Dừng giới hạn (Stop Limit)"),
            ("trailing", "Dừng trượt (Trailing Stop)"),
            ("lit", "Chạm rồi giới hạn (Limit If Touched)"),
            ("moo", "Khớp lúc MỞ cửa (Market On Open)"),
            ("moc", "Khớp lúc ĐÓNG cửa (Market On Close)"),
        ]),
        _O_SO_LUONG,
        O_TAG,
    ],
    #: Ô thêm theo từng loại lệnh, kèm đúng hàm LEAN của nó.
    "theo_loai": {
        "limit": {"lean": "self.limit_order({sym}, {so_luong}, {gia_gh}, tag={tag})",
                  "o": [_o("gia_gh", "Giá giới hạn", O_SO, 0, "giá")]},
        "stop": {"lean": "self.stop_market_order({sym}, {so_luong}, {gia_kh}, tag={tag})",
                 "o": [_o("gia_kh", "Giá kích hoạt", O_SO, 0, "giá")]},
        "stop_limit": {
            "lean": "self.stop_limit_order({sym}, {so_luong}, {gia_kh}, {gia_gh}, tag={tag})",
            "o": [_o("gia_kh", "Giá kích hoạt", O_SO, 0, "giá"),
                  _o("gia_gh", "Giá giới hạn", O_SO, 0, "giá")]},
        "trailing": {
            "lean": "self.trailing_stop_order({sym}, {so_luong}, {khoang_truot}, "
                    "{truot_theo_pt}, tag={tag})",
            "o": [_o("khoang_truot", "Khoảng trượt", O_SO, 0.05, "",
                     "Theo % thì 0.05 = 5%; theo tiền thì là số tiền."),
                  _o("truot_theo_pt", "Trượt theo %", O_CO_KHONG, True, "",
                     "Tắt = trượt theo số tiền tuyệt đối.", bat_buoc=False)]},
        "lit": {"lean": "self.limit_if_touched_order({sym}, {so_luong}, {gia_cham}, {gia_gh}, tag={tag})",
                "o": [_o("gia_cham", "Giá chạm", O_SO, 0, "giá"),
                      _o("gia_gh", "Giá giới hạn", O_SO, 0, "giá")]},
        "moo": {"lean": "self.market_on_open_order({sym}, {so_luong}, tag={tag})", "o": []},
        "moc": {"lean": "self.market_on_close_order({sym}, {so_luong}, tag={tag})", "o": []},
    },
}

# ---------------------------------------------------------------------------
# ⑤ HUỶ LỆNH CHỜ
# ---------------------------------------------------------------------------
# CHỈ có "huỷ hết của một mã". Huỷ ĐÚNG MỘT lệnh cần id của nó, tức app phải nhớ —
# xem đường ranh ở đầu file.
HUY_LENH_CHO = {
    "nhan": "Huỷ lệnh chờ",
    "mo_ta": "huỷ hết lệnh đang chờ của mã này",
    "icon": "unlink",
    "nhom": NHOM_LENH,
    "can_ma": True,
    "lean": "self.transactions.cancel_open_orders({sym}, {tag})",
    "o": [O_MA, O_TAG],
}

# ---------------------------------------------------------------------------
# ⑥ GHI CHÚ — và DỪNG HẲN
# ---------------------------------------------------------------------------
GHI_CHU = {
    "nhan": "Ghi chú",
    "mo_ta": "viết một dòng vào nhật ký chạy, hoặc dừng hẳn cỗ máy",
    "icon": "edit",
    "nhom": NHOM_GHI,
    "can_ma": False,
    "lean": "self.debug / log / error / quit",
    "o": [
        _o("muc", "Mức", O_CHON, "debug", "", "", [
            ("debug", "Debug — hiện ngay trong nhật ký"),
            ("log", "Log — ghi vào file nhật ký"),
            ("error", "Error — ghi như một lỗi"),
            ("quit", "DỪNG HẲN — cỗ máy thôi chạy từ đây"),
        ]),
        # KHÔNG bắt buộc: để trống thì bộ sinh mã điền số khối + điều kiện vừa khớp,
        # y như ô `tag`. Bắt gõ câu ở đây chỉ là bắt gõ lại thứ nó biết sẵn.
        _o("cau", "Câu chữ", O_CHU, "", "",
           "Viết thẳng, hoặc để trống cho bộ sinh mã tự điền.", bat_buoc=False),
    ],
    # Bốn mức là BỐN hàm khác nhau của LEAN, không phải một hàm có tham số mức.
    "theo_loai": {
        "debug": {"lean": "self.debug({cau})", "o": []},
        "log": {"lean": "self.log({cau})", "o": []},
        "error": {"lean": "self.error({cau})", "o": []},
        "quit": {"lean": "self.quit({cau})", "o": []},
    },
}

# ---------------------------------------------------------------------------
# ⑦ VẼ LÊN BẢNG — đường riêng trên chart kết quả
# ---------------------------------------------------------------------------
# `Plot` nhận một CON SỐ. Lấy số ấy từ đâu thì dùng lại đúng kho đại lượng của
# `hoi.py` — không khai một kho thứ hai, vì hai kho thì sớm muộn lệch nhau.
VE_BANG = {
    "nhan": "Vẽ lên bảng",
    "mo_ta": "thêm một đường vào chart kết quả",
    "icon": "kieu-line",
    "nhom": NHOM_GHI,
    "can_ma": True,
    "lean": "self.plot({bang}, {ten_duong}, {gia_tri})",
    "o": [
        O_MA,
        _o("bang", "Tên bảng", O_CHU, "Chỉ báo"),
        # `ten_duong` chứ không phải `duong`: trong một vế đại lượng, `duong` đã có
        # nghĩa khác (chọn đường nào của chỉ báo nhiều đường, như Bollinger).
        _o("ten_duong", "Tên đường", O_CHU, "RSI"),
    ],
    #: Giá trị vẽ = một đại lượng bất kỳ trong kho, chọn bằng chính bảng chọn của
    #: khối Hỏi. Trước đây khoá cứng vào họ "hỏi thị trường", nên vẽ được RSI mà
    #: không vẽ được «Tổng giá trị danh mục» — thứ ai cũng muốn nhìn.
    "co_dai_luong": True,
}

# ---------------------------------------------------------------------------
# ⑧ BÁO TIN — chỉ có nghĩa khi chạy thật
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⑨ PHÁT TÍN HIỆU — nói "mã này nên LÊN", rồi để LEAN lo phần còn lại
# ---------------------------------------------------------------------------
# ⚠ KHỐI NÀY MỞ RA NỬA KIA CỦA LEAN. Từ trước tới nay cả bộ khối chỉ dựng theo lối
# CỔ ĐIỂN: `on_data` rồi tự đặt lệnh. Nhưng `QCAlgorithm` còn năm cái khe khai sẵn —
# Universe · Alpha · Portfolio Construction · Risk · Execution — nối thành một dây
# chuyền, và LEAN làm sẵn mỗi khe mấy model.
#
# Đọc thẳng `QCAlgorithm.Framework.cs`:
#     Alpha.Update(…)                     -> insights
#     PortfolioConstruction.CreateTargets -> targets
#     RiskManagement.ManageRisk           -> targets đã chỉnh
#     Execution.Execute                   -> lệnh
# Dây chuyền ấy BẮT ĐẦU TỪ INSIGHT. Không có insight thì ba trạm sau không có gì làm.
#
# `emit_insights` là phương thức CÔNG KHAI của `QCAlgorithm` (`EmitInsights`), nên
# phát được thẳng từ `on_data` — KHÔNG phải dựng một lớp Alpha model nào. Nhờ vậy
# hình dạng mã sinh ra không đổi: vẫn cây quyết định, chỉ khác cái lá.
#
# ĐỔI LẠI ĐƯỢC GÌ (mấy thứ trước đây ta từ chối vì lối cổ điển bắt app tự giữ sổ):
#   · thoát theo HẠN      -> `Insight` mang sẵn `period`, LEAN tính `CloseTimeUtc`
#                            và `IsActive()`; app không đếm nến nào cả;
#   · chia đều 1/N        -> `EqualWeightingPortfolioConstructionModel`;
#   · cắt lỗ / trailing   -> mấy model trong `Algorithm.Framework/Risk/`.
# Cả ba chọn ở khối BẮT ĐẦU, vì chúng gọi một lần trong `initialize` (xem ví dụ
# `BaseFrameworkRegressionAlgorithm.py` của LEAN) — chúng là CHÍNH SÁCH của cỗ máy,
# không phải việc xảy ra ở một chỗ trong luồng.
TIN_HIEU = {
    "nhan": "Phát tín hiệu",
    "mo_ta": "nói «mã này nên LÊN» — LEAN lo chia vốn, phòng rủi ro và đặt lệnh",
    "icon": "branch",
    "nhom": NHOM_TIN_HIEU,
    "can_ma": True,
    "lean": "self.emit_insights(Insight.price({sym}, timedelta(days={han}), "
            "InsightDirection.…))",
    "o": [
        _o("huong", "Hướng", O_CHON, "UP", "", "", [
            ("UP", "LÊN — nên mua / giữ"),
            ("DOWN", "XUỐNG — nên bán khống"),
            ("FLAT", "PHẲNG — thôi giữ mã này"),
        ]),
        # HẠN chính là "giữ tối đa bao lâu". Hết hạn, LEAN tự bỏ tín hiệu khỏi rổ
        # đang tính, và model chia vốn chia lại cho những mã còn hạn — tức vị thế tự
        # đóng mà KHÔNG khối nào phải đếm ngày.
        _o("han", "Giữ tối đa", O_SO, 15, "", "ngày",
           "Hết ngần này ngày, LEAN tự bỏ tín hiệu và chia lại vốn cho mã còn hạn. "
           "Không khối nào phải đếm ngày — đó là việc của LEAN."),
    ],
    # ⚠ HƯỚNG viết thẳng vào câu LEAN, nên phải đi qua `theo_loai` chứ KHÔNG nhét
    # vào `{…}` của mẫu: mọi ô đều qua `_lit()` để thành literal Python, nên
    # `InsightDirection.{huong}` sinh ra `InsightDirection.'UP'` — sai cú pháp.
    # Cùng lối với ô «Gửi bằng» của khối Báo tin: mỗi lựa chọn một câu LEAN riêng.
    "theo_loai": {
        h: {"lean": "self.emit_insights(Insight.price({sym}, "
                    f"timedelta(days={{han}}), InsightDirection.{h}))", "o": []}
        for h in ("UP", "DOWN", "FLAT")
    },
}


BAO_TIN = {
    "nhan": "Báo tin",
    "mo_ta": "gửi tin ra ngoài — CHỈ chạy thật mới có tác dụng",
    "icon": "up",
    "nhom": NHOM_GHI,
    "can_ma": False,
    "lean": "self.notify.email / sms / telegram / web",
    "tat": "Backtest KHÔNG gửi gì — khối này chỉ có tác dụng khi chạy thật (paper "
           "hoặc tiền thật). Vẽ ra thì chạy backtest sẽ lặng.",
    "o": [
        _o("kenh", "Gửi bằng", O_CHON, "telegram", "", "", [
            ("email", "Email"),
            ("sms", "SMS"),
            ("telegram", "Telegram"),
            ("web", "Gọi một địa chỉ web"),
        ]),
        _o("dich", "Gửi tới", O_CHU, "",
           "", "Địa chỉ email / số điện thoại / id Telegram / địa chỉ web."),
        _o("cau", "Nội dung", O_CHU, ""),
    ],
    # Bốn kênh, bốn chữ ký khác nhau — đọc từ `NotificationManager.cs`:
    #   Email(address, subject, message)  ·  Sms(phoneNumber, message)
    #   Telegram(id, message)             ·  Web(address, data)
    "theo_loai": {
        "email": {"lean": "self.notify.email({dich}, {cau}, {cau})", "o": []},
        "sms": {"lean": "self.notify.sms({dich}, {cau})", "o": []},
        "telegram": {"lean": "self.notify.telegram({dich}, {cau})", "o": []},
        "web": {"lean": "self.notify.web({dich}, {cau})", "o": []},
    },
}

# ---------------------------------------------------------------------------
# Bảng tra
# ---------------------------------------------------------------------------
LAM_DAT_TY_TRONG = "lam_dat_ty_trong"
LAM_LENH_THI_TRUONG = "lam_lenh_thi_truong"
LAM_DONG = "lam_dong"
LAM_LENH_CHO = "lam_lenh_cho"
LAM_HUY_LENH_CHO = "lam_huy_lenh_cho"
LAM_GHI_CHU = "lam_ghi_chu"
LAM_VE_BANG = "lam_ve_bang"
LAM_BAO_TIN = "lam_bao_tin"
LAM_TIN_HIEU = "lam_tin_hieu"

LOAI_LAM = {
    LAM_DAT_TY_TRONG: DAT_TY_TRONG,
    LAM_LENH_THI_TRUONG: LENH_THI_TRUONG,
    LAM_DONG: DONG,
    LAM_LENH_CHO: LENH_CHO,
    LAM_HUY_LENH_CHO: HUY_LENH_CHO,
    LAM_GHI_CHU: GHI_CHU,
    LAM_VE_BANG: VE_BANG,
    LAM_BAO_TIN: BAO_TIN,
    LAM_TIN_HIEU: TIN_HIEU,
}


def la_loai_lam(t):
    return t in LOAI_LAM


def o_cua(loai, gia_tri=None):
    """Mọi ô của một loại hành động, KỂ CẢ ô chỉ hiện theo lựa chọn.

    `gia_tri` = giá trị hiện tại của khối; thiếu thì lấy lựa chọn mặc định."""
    d = LOAI_LAM.get(loai)
    if not d:
        return []
    ra = list(d["o"])
    theo = d.get("theo_loai")
    if theo:
        o_chon = next((o for o in d["o"] if o["kieu"] == O_CHON), None)
        if o_chon:
            v = (gia_tri or {}).get(o_chon["ten"], o_chon["mac_dinh"])
            ra = ra + list((theo.get(v) or {}).get("o", []))
    return ra


def ham_lean(loai, gia_tri=None):
    """Đúng hàm LEAN khối này sẽ gọi — để hộp thoại nói thẳng ra cho người dùng thấy."""
    d = LOAI_LAM.get(loai)
    if not d:
        return ""
    theo = d.get("theo_loai")
    if theo:
        o_chon = next((o for o in d["o"] if o["kieu"] == O_CHON), None)
        if o_chon:
            v = (gia_tri or {}).get(o_chon["ten"], o_chon["mac_dinh"])
            return (theo.get(v) or {}).get("lean", d["lean"])
    return d["lean"]


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối."""
    return {
        "loai": [
            {"ma": ma, "nhan": d["nhan"], "mo_ta": d["mo_ta"], "icon": d["icon"],
             "can_ma": d["can_ma"], "lean": d["lean"], "tat": d.get("tat", False),
             "nhom": d["nhom"],
             "o": d["o"], "theo_loai": d.get("theo_loai", {}),
             "co_dai_luong": d.get("co_dai_luong", False)}
            for ma, d in LOAI_LAM.items()
        ],
    }
