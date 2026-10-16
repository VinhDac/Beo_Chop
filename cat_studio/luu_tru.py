"""Cơ sở lưu trữ — MỘT chỗ duy nhất biết file nằm ở đâu.

    <cạnh app>/du_lieu/
        cai_dat.json          cài đặt app
        chien_luoc/*.json     chiến lược đã lưu
        nhat_ky/              nhật ký "vì sao" của từng lượt chạy trên QuantConnect

Trước đây đường dẫn rải rác trong `core.py` (`app_dir`, `_thu_muc_tpl`, …) và dùng
từ vựng cũ của Auto_Clicker ("templates", 3 loại). Giờ chỉ còn một loại — chiến lược —
nên gọi đúng tên nó, và gom về một module để đổi bố cục chỉ phải sửa một nơi.

KHÔNG ném lỗi khi đọc: file rác hay thiếu quyền thì trả mặc định. Đọc cài đặt mà chết
thì app không mở lên được, đắt hơn nhiều so với việc mất vài tuỳ chọn.
"""
import json
import os
import re
import sys

THU_MUC_GOC = "du_lieu"
FILE_CAI_DAT = "cai_dat.json"
#: STRATEGY người chơi lưu. Thư mục này KHÔNG biết gì về hình dạng bên trong file — nó
#: chỉ ghi/đọc JSON — nên nó sống sót qua D-12 (xoá bộ khối cũ) mà không phải sửa gì.
#: ⚠ File cũ còn nằm đây vẫn mở được bằng tay, nhưng app KHÔNG đọc được nữa: chúng viết
#: bằng bộ khối đã xoá. Cố ý không tự xoá — đó là công người chơi bỏ ra.
THU_MUC_STRATEGY = "strategy"
#: Tên thư mục đời trước. `di_cu` chép sang tên mới, KHÔNG xoá bản cũ.
THU_MUC_CU = "co_may"
THU_MUC_NHAT_KY = "nhat_ky"
#: Nơi đặt file .py do bộ sinh mã viết ra — để riêng, vì chúng là thứ SINH LẠI ĐƯỢC
#: từ sơ đồ, không phải tài liệu người dùng.
THU_MUC_MA = "ma_sinh"

CAI_DAT_MAC_DINH = {
    "symbol": "XAUUSD",
    "accent": "#ffa657",
    "ui": {"panel_cao": 176, "panel_gap": False},
}


#: Thư mục GỐC DỰ ÁN khi chạy từ mã nguồn — LÊN MỘT BẬC từ file này.
#: ⚠ File này nằm trong gói `cat_studio/`, nên `dirname(__file__)` là thư mục GÓI chứ
#: không phải gốc dự án. Thiếu bậc `..` thì `du_lieu/` bị đẻ vào trong gói và `webui/dist`
#: tìm không ra — đúng hai thứ vỡ khi gom module vào package.
_GOC_MA_NGUON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def thu_muc_app():
    """Nơi ĐẶT DỮ LIỆU NGƯỜI DÙNG: cạnh file exe (bản đóng gói) hoặc gốc dự án."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return _GOC_MA_NGUON


def thu_muc_goi():
    """Nơi chứa TÀI NGUYÊN ĐI KÈM (giao diện đã build trong `webui/dist`).

    ⚠ KHÁC HẲN `thu_muc_app`, và trộn hai cái là hỏng theo cả hai chiều. Bản đóng gói
    một-file giải nén tài nguyên vào một thư mục TẠM (`sys._MEIPASS`) rồi xoá lúc thoát:
    để dữ liệu người dùng ở đó là mất sạch sau mỗi lần chạy. Ngược lại, tìm `webui/dist`
    cạnh .exe thì không thấy, vì nó nằm trong gói."""
    return getattr(sys, "_MEIPASS", None) or _GOC_MA_NGUON


def trang_giao_dien():
    """Đường dẫn tới `index.html` đã build. Một chỗ duy nhất, hai cửa sổ cùng dùng."""
    return os.path.join(thu_muc_goi(), "webui", "dist", "index.html")


def goc():
    d = os.path.join(thu_muc_app(), THU_MUC_GOC)
    os.makedirs(d, exist_ok=True)
    return d


def _thu_muc(ten):
    d = os.path.join(goc(), ten)
    os.makedirs(d, exist_ok=True)
    return d


def thu_muc_strategy():
    return _thu_muc(THU_MUC_STRATEGY)


def thu_muc_nhat_ky():
    return _thu_muc(THU_MUC_NHAT_KY)


def thu_muc_ma():
    return _thu_muc(THU_MUC_MA)


def ghi_ma(ten_lop, ma):
    """Ghi một file .py bộ sinh mã vừa viết. -> đường dẫn đầy đủ."""
    p = os.path.join(thu_muc_ma(), _ten_an_toan(ten_lop) + ".py")
    # `newline="\n"`: file Python, LEAN đọc trên Linux lẫn Windows — đừng để CRLF.
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(ma)
    return p


# ---------------------------------------------------------------------------
# Cài đặt
# ---------------------------------------------------------------------------


def doc_cai_dat():
    """Đọc cài đặt. Hỏng thì trả mặc định, không ném lỗi.

    CHỈ giữ những khoá còn trong bảng mặc định: khi một cài đặt bị bỏ đi (ví dụ
    `timeframe` chuyển thành `nhip` trên khối Bắt đầu), khoá cũ trong file sẽ nằm lại
    vĩnh viễn và người đọc sau này tưởng nó vẫn có tác dụng."""
    ra = json.loads(json.dumps(CAI_DAT_MAC_DINH))
    try:
        with open(os.path.join(goc(), FILE_CAI_DAT), encoding="utf-8") as f:
            d = json.load(f) or {}
        ra.update({k: v for k, v in d.items() if k in CAI_DAT_MAC_DINH})
    except Exception:
        pass
    return ra


def ghi_cai_dat(s):
    """Lưu cài đặt. NÉM LỖI nếu không ghi được — không nuốt.

    Trước đây bọc `try/except: pass` rồi vẫn `return s`, nên đĩa đầy hoặc mất quyền ghi
    thì nơi gọi tưởng đã lưu xong. Lần mở app sau, cài đặt lặng lẽ về mặc định và không ai
    hiểu vì sao. `api` đã có `@_bat_loi` để đưa câu lỗi lên giao diện —
    cứ để nó làm việc của nó."""
    ghi_json_nguyen_tu(os.path.join(goc(), FILE_CAI_DAT), s)
    return s


def ghi_json_nguyen_tu(duong, du_lieu):
    """Ghi JSON qua file TẠM rồi `os.replace` — đổi tên trên NTFS là nguyên tử.

    Ngắt giữa lúc ghi (bấm ✕, mất điện, antivirus xen vào) mà ghi thẳng lên file đích thì
    để lại một file JSON CỤT: `doc_cai_dat` trả mặc định, còn một template cụt thì mất
    hẳn chiến lược. Cách này cùng lắm để lại một `.tmp` rác, bản cũ nguyên vẹn."""
    tam = duong + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tam, duong)


# ---------------------------------------------------------------------------
# Tên file an toàn
# ---------------------------------------------------------------------------
def _ten_an_toan(ten):
    """Tên file an toàn. Chặn cả `..` và dấu phân cách để một cái tên gõ tay không
    ghi được ra ngoài thư mục chiến lược."""
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (ten or "").strip())
    s = s.strip(". ")
    # ⚠ Tên THIẾT BỊ của Windows: `NUL.json` bị ánh xạ vào hố đen ở BẤT KỲ thư mục nào.
    # Đã chạy thử dưới pythonw.exe (đường app thật): lưu tên "NUL" báo THÀNH CÔNG,
    # `os.path.exists` trả True, nhưng đĩa không có file và sơ đồ bốc hơi không một dòng
    # lỗi; "AUX"/"COM1" còn TREO CỨNG lúc đọc lại. Đáng lo vì "con" là từ tiếng Việt rất
    # hay gặp, mà app này mặc định người dùng đặt tên bằng tiếng Việt.
    # Thêm gạch dưới thay vì đổi tên khác: hàm giữ được tính lũy đẳng
    # (`_ten_an_toan("_con") == "_con"`), nên tên lấy từ `liet_ke` đưa ngược vào vẫn ra
    # đúng file, không cộng dồn gạch qua mỗi vòng.
    if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", s):
        s = "_" + s
    return s or "khong_ten"


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------
# Ghi/đọc JSON thuần: `_ten_an_toan` (bẫy tên thiết bị Windows — CON, PRN, NUL…) và lối
# ghi nguyên tử. Không hàm nào ở đây mở file ra xem bên trong, nên bộ khối mới dùng lại
# được nguyên xi.


def duong_dan_strategy(ten):
    return os.path.join(thu_muc_strategy(), _ten_an_toan(ten) + ".json")


def liet_ke_strategy():
    try:
        return sorted(f[:-5] for f in os.listdir(thu_muc_strategy())
                      if f.endswith(".json"))
    except Exception:
        return []


def ghi_strategy(ten, doc):
    p = duong_dan_strategy(ten)
    ghi_json_nguyen_tu(p, doc)
    return p


def doc_strategy(ten):
    with open(duong_dan_strategy(ten), encoding="utf-8") as f:
        return json.load(f)


def xoa_strategy(ten):
    p = duong_dan_strategy(ten)
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


# ---------------------------------------------------------------------------
# Di cư từ bố cục cũ
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Bản nháp và bản tự lưu  (chép lối của Jenifer_Studio)
# ---------------------------------------------------------------------------
# HAI TẦNG, KHÁC NHAU HẲN:
#
#   ban_nhap.json          MỘT bản dùng chung cho mọi cỗ máy, ghi liên tục trong lúc
#                          vẽ. Việc đang dở của cửa sổ — kể cả cỗ máy CHƯA TỪNG lưu.
#                          Không đụng tới file cỗ máy nào.
#   "<tên> (tự lưu)"       nằm NGAY CẠNH cỗ máy gốc trong kho, và chỉ đẻ ra khi cỗ máy
#                          ĐÃ lưu ít nhất một lần VÀ nội dung thật sự khác bản trên
#                          đĩa. Mở ra xem mà không sửa gì thì không đẻ bản tự lưu.
#                          Lưu thật (Ctrl+S) xong là xoá nó: việc dở đã thành việc lưu.
TEP_BAN_NHAP = "ban_nhap.json"
HAU_TO_TU_LUU = " (tự lưu)"


def duong_dan_ban_nhap():
    return os.path.join(goc(), TEP_BAN_NHAP)


def ghi_ban_nhap(doc_):
    ghi_json_nguyen_tu(duong_dan_ban_nhap(), doc_)
    return duong_dan_ban_nhap()


def doc_ban_nhap():
    try:
        with open(duong_dan_ban_nhap(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def xoa_ban_nhap():
    p = duong_dan_ban_nhap()
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


def ten_tu_luu(ten):
    """Tên bản tự lưu của một cỗ máy. Đã là bản tự lưu thì giữ nguyên, không chồng đuôi."""
    ten = (ten or "").strip()
    return ten if ten.endswith(HAU_TO_TU_LUU) else ten + HAU_TO_TU_LUU


def ten_goc_cua(ten):
    """Bản tự lưu -> tên cỗ máy GỐC của nó. Không phải bản tự lưu thì trả nguyên."""
    ten = (ten or "").strip()
    return ten[:-len(HAU_TO_TU_LUU)] if ten.endswith(HAU_TO_TU_LUU) else ten


def la_tu_luu(ten):
    return (ten or "").strip().endswith(HAU_TO_TU_LUU)


def di_cu():
    """Chuyển `settings.json` + `templates/strategy/` của bản cũ sang `du_lieu/`.

    Chạy MỘT lần lúc khởi động. Chỉ CHÉP những gì chưa có ở nơi mới — không đè, không
    xoá bản cũ. Người dùng mở lại bản cũ vẫn thấy đủ dữ liệu của họ."""
    da = []
    app = thu_muc_app()
    cu_cai_dat = os.path.join(app, "settings.json")
    moi_cai_dat = os.path.join(goc(), FILE_CAI_DAT)
    if os.path.exists(cu_cai_dat) and not os.path.exists(moi_cai_dat):
        try:
            with open(cu_cai_dat, encoding="utf-8") as f:
                ghi_cai_dat(json.load(f))
            da.append(FILE_CAI_DAT)
        except Exception:
            pass

    # ⚠ BA nguồn đời trước, cả ba chép sang `du_lieu/strategy/`:
    #     templates/strategy/   bản tkinter, nằm ngoài `du_lieu/`
    #     du_lieu/chien_luoc/   kho chiến lược cũ (gỡ ở D-12)
    #     du_lieu/co_may/       bản trước khi tài liệu đổi tên thành Strategy
    #
    # Chỗ này từng GÃY: nó gọi `thu_muc_chien_luoc()` — một hàm đã bị xoá cùng kho
    # chiến lược cũ ở D-12. Máy nào còn thư mục ấy là app NỔ ngay lúc khởi động
    # (`app_web.py` gọi `di_cu` trước khi mở cửa sổ), mà máy đang phát triển thì không
    # có nó nên chẳng ai thấy.
    for cu_tpl in (os.path.join(app, "templates", "strategy"),
                   os.path.join(goc(), "chien_luoc"),
                   os.path.join(goc(), THU_MUC_CU)):
        if not os.path.isdir(cu_tpl):
            continue
        for f in os.listdir(cu_tpl):
            if not f.endswith(".json"):
                continue
            dich = os.path.join(thu_muc_strategy(), f)
            if os.path.exists(dich):
                continue
            try:
                with open(os.path.join(cu_tpl, f), encoding="utf-8") as g:
                    noi_dung = g.read()
                with open(dich, "w", encoding="utf-8") as g:
                    g.write(noi_dung)
                da.append(f"strategy/{f}")
            except Exception:
                pass
    return da


# ---------------------------------------------------------------------------
# Cho hộp thoại "Kho"
# ---------------------------------------------------------------------------


def tom_tat():
    """Kho đang chứa gì — đường dẫn thật + số lượng, để nhìn là biết tìm ở đâu."""
    def dem(d):
        try:
            return len([f for f in os.listdir(d) if not f.startswith(".")])
        except Exception:
            return 0

    return {
        "goc": goc(),
        "muc": [
            {"ten": "Strategy", "duong_dan": thu_muc_strategy(),
             "so_luong": len(liet_ke_strategy()),
             "danh_sach": liet_ke_strategy()},
            {"ten": "Nhật ký chạy", "duong_dan": thu_muc_nhat_ky(),
             "so_luong": dem(thu_muc_nhat_ky()), "danh_sach": []},
        ],
    }
