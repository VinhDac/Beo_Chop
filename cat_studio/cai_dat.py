"""TỪ ĐIỂN CÀI ĐẶT APP — những thứ người dùng chỉnh được, và chỉ những thứ ấy.

CÙNG MỘT LUẬT VỚI BA TỪ ĐIỂN KIA (`hoi`, `lam`, `bat_dau`): Python khai, giao diện
chỉ bày ra. Hộp Cài đặt không được tự biết có bao nhiêu ô, ô nào kiểu gì — nó đọc
`tu_dien()` rồi dựng, y như `HopHanhDong` dựng ô của khối Làm. Thêm một cài đặt mới
là thêm một dòng ở đây, không phải sửa hai nơi.

⚠ CHỈ KHAI THỨ CÓ NGƯỜI ĐỌC. `cai_dat.json` xưa nay mang sẵn `symbol`, `accent` và
`ui.panel_cao` / `ui.panel_gap` — bốn khoá còn sót từ bản tkinter mà KHÔNG MỘT DÒNG
nào trong app đọc tới (đã grep cả `cat_studio/` lẫn `webui/src/`). Một hộp Cài đặt
bày ra bốn cái núm không nối vào đâu thì còn tệ hơn không có hộp: người ta vặn rồi
ngồi đợi một thứ không bao giờ đổi.
"""
O_SO = "so"
O_CHU = "chu"
O_CHON = "chon"
O_CO_KHONG = "co_khong"

#: Khoá trong `cai_dat.json`. `lean_goc` là khoá CÓ SẴN, giữ nguyên tên — đổi tên là
#: mọi người đang dùng mất đường dẫn LEAN đã trỏ.
#:
#: ⚠ Module này KHÔNG import gì của app. Nó là nơi khai mặc định, mà `luu_tru` phải
#: dựng `CAI_DAT_MAC_DINH` từ đây — import ngược lại là vòng tròn. `chay_lean` lấy
#: `KHOA_LEAN` từ đây chứ không tự khai.
KHOA_LEAN = "lean_goc"
KHOA_HAN_GIO = "han_gio_phut"
KHOA_MO_KET_QUA = "mo_ket_qua"
KHOA_KHO_BACKTEST = "kho_backtest"
KHOA_KHO_TOI_UU = "kho_toi_uu"
KHOA_NGON_NGU = "ngon_ngu"
KHOA_AM_THANH = "am_thanh"

#: NGÔN NGỮ GIAO DIỆN. Nấc ĐẦU là mặc định — tiếng Anh, vì người đọc được tiếng Anh
#: thì mở app lên là dùng được ngay, còn người Việt bật lại một lần là xong.
#:
#: ⚠ MỘT CHỖ DUY NHẤT biết có mấy nấc và mặc định là nấc nào: `core.ngon_ngu` đọc
#: bảng này, `ngon_ngu.dat` rơi về cùng một giá trị, và hộp Cài đặt dựng ô chọn từ
#: chính nó. Gõ "en" lần thứ hai ở đâu đó là mở đường cho hai bên lệch nhau.
NGON_NGU = (("en", "English"), ("vi", "Tiếng Việt"))   # không dịch


def _o(ten, nhan, kieu, mac_dinh, goi_y="", nguyen=False, don_vi="", chon=()):
    return {"ten": ten, "nhan": nhan, "kieu": kieu, "mac_dinh": mac_dinh,
            "goi_y": goi_y, "nguyen": nguyen, "don_vi": don_vi,
            "chon": [list(c) for c in chon], "bat_buoc": False, "lean": ""}


#: (mã nhóm, nhãn nhóm, các ô). Nhóm chứ không phải tab: ba ô thì chia tab là chia
#: cho có, mà mỗi tab lại là một chỗ để quên không lưu.
NHOM = (
    # ĐỨNG ĐẦU, và nhãn ghi CẢ HAI TIẾNG — cố ý, cả hai thứ. Ai lỡ chọn tiếng mình
    # không đọc được thì vẫn phải tìm ra đường về: mắt chạy từ trên xuống, và chữ
    # "Language" nhận ra được mà không cần đọc chữ nào khác. Hai nhãn này KHÔNG đi qua
    # bộ dịch (dòng `# không dịch`) vì dịch chúng là phá đúng cái lối về ấy.
    ("ngon_ngu", "Ngôn ngữ · Language", (  # không dịch
        # Nhãn NGẮN, vì tiêu đề nhóm ngay trên đã nói đủ: để dài thì nó xuống hai dòng
        # và ô chọn tụt xuống một hàng riêng — mọi hàng khác của hộp là nhãn|ô một dòng.
        _o(KHOA_NGON_NGU, "Tiếng · Language",  # không dịch
           O_CHON, NGON_NGU[0][0], chon=NGON_NGU),
    )),
    ("chay", "Chạy backtest", (
        _o(KHOA_LEAN, "Thư mục LEAN", O_CHU, "",
           "Thư mục gốc của LEAN trên máy này — chỗ có Launcher/ và Data/."),
        _o(KHOA_HAN_GIO, "Hạn giờ một lượt", O_SO, 15,
           "Quá ngần này thì dừng hẳn lượt chạy. Backtest nhiều năm theo nến phút "
           "thì nâng lên.", nguyen=True, don_vi="phút"),
        _o(KHOA_MO_KET_QUA, "Xong thì mở luôn bảng kết quả", O_CO_KHONG, True,
           "Tắt đi thì chạy xong chỉ ghi một dòng nhật ký — bấm Results khi nào "
           "muốn xem."),
        _o(KHOA_AM_THANH, "Tiếng", O_CO_KHONG, True,
           "Van đóng mở, lệnh nổ, sao rơi. Tiếng dựng ngay trong app chứ không có "
           "file nhạc nào — tắt là im hẳn."),
    )),
    ("kho", "Kho lượt chạy", (
        _o(KHOA_KHO_BACKTEST, "Giữ mấy lượt backtest", O_SO, 20,
           "Quá số này thì lượt CŨ NHẤT bị xoá để nhường chỗ. Mỗi lượt là một thư "
           "mục vài trăm KB, nhưng chạy cả ngày thì nó dồn lại.",
           nguyen=True, don_vi="lượt"),
        # Một MẺ Optimize nặng hơn một lượt backtest cả trăm lần — mỗi lượt trong mẻ
        # là một thư mục riêng. Nên con số ở đây đếm MẺ, không đếm lượt.
        _o(KHOA_KHO_TOI_UU, "Giữ mấy mẻ Optimize", O_SO, 20,
           "Đếm MẺ, không đếm lượt: một mẻ có thể chứa hàng trăm lượt backtest, nên "
           "nó nặng gấp bội một lượt thường.",
           nguyen=True, don_vi="mẻ"),
    )),
)

BANG_O = {o["ten"]: o for _m, _n, ds in NHOM for o in ds}


def mac_dinh():
    return {ten: o["mac_dinh"] for ten, o in BANG_O.items()}


def doc(s):
    """Giá trị đã lưu + rơi về mặc định cho ô thiếu. -> dict

    Ô nào kiểu `so` mà trong file là chữ (người sửa tay) thì rơi về mặc định chứ
    KHÔNG nổ: một file cài đặt hỏng không được làm app không mở lên được."""
    ra = mac_dinh()
    for ten, o in BANG_O.items():
        if ten not in (s or {}):
            continue
        v = s[ten]
        if o["kieu"] == O_SO:
            try:
                v = int(v) if o["nguyen"] else float(v)
            except (TypeError, ValueError):
                continue
        elif o["kieu"] == O_CO_KHONG:
            v = bool(v)
        elif o["kieu"] == O_CHON:
            # Giá trị KHÔNG CÓ trong danh sách nấc thì rơi về mặc định. Không có nhánh
            # này thì `ngon_ngu: "fr"` gõ tay vào file đi thẳng vào giao diện, và cả
            # hai bên — Python lẫn web — mỗi bên tự đoán một kiểu.
            if str(v) not in [m for m, _n in o["chon"]]:
                continue
            v = str(v)
        else:
            v = str(v)
        ra[ten] = v
    return ra


def han_gio_giay(s=None):
    """Hạn giờ một lượt chạy, tính bằng GIÂY — `chay_lean` cần đúng đơn vị ấy.

    Chặn dưới 1 phút: đặt 0 rồi tự hỏi sao lượt nào cũng chết ngay là một cái bẫy
    người dùng tự giăng cho mình."""
    p = doc(s or {}).get(KHOA_HAN_GIO) or BANG_O[KHOA_HAN_GIO]["mac_dinh"]
    return max(60, int(p) * 60)


def gioi_han_kho(khoa, s=None):
    """Giữ tối đa mấy lượt/mẻ. -> int >= 1.

    Chặn dưới 1 chứ không chặn dưới 0: đặt 0 nghĩa là "xoá sạch mọi thứ ngay sau
    khi chạy xong", và người đặt con số ấy gần như chắc chắn không định thế."""
    v = doc(s or {}).get(khoa)
    if v in (None, ""):
        v = BANG_O[khoa]["mac_dinh"]
    try:
        return max(1, int(float(v)))
    except (TypeError, ValueError):
        return int(BANG_O[khoa]["mac_dinh"])


def tu_dien():
    """Cả từ điển, dạng gửi được qua cầu nối cho giao diện."""
    return {"nhom": [{"ma": m, "nhan": n, "o": list(ds)} for m, n, ds in NHOM]}
