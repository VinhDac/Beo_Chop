# -*- coding: utf-8 -*-
"""NGÔN NGỮ — phần Python: chữ do Python sinh ra (dòng trên mặt khối, bảng Vấn đề, câu lỗi
lượt chạy, câu gợi ý nối khối) theo tiếng Anh (mặc định) hay tiếng Việt.

Chép cơ chế của Jenifer_Studio (`ma_nguon/ngon_ngu.py` bên ấy). CÙNG MỘT LUẬT với giao diện
web (`webui/src/ngon_ngu.ts`):

  · CÂU TIẾNG VIỆT LÀ KHOÁ. Mã vẫn viết nguyên câu tiếng Việt ngay chỗ nó sinh ra, chỉ bọc
    `tr(…)`; bảng `tieng_anh.py` tra câu ấy ra câu tiếng Anh. Ở tiếng Việt `tr` trả lại đúng
    câu đưa vào — app tiếng Việt y hệt như chưa có bộ dịch.
  · DỊCH Ở NƠI CÂU SINH RA. Câu có chèn biến thì bên nhận không tra bảng được nữa: giao diện
    nhận "RSI(14) lớn hơn 70" thì trong bảng dịch chẳng có khoá nào như thế. Đây KHÔNG phá
    luật "Python khai, giao diện chỉ bày lại" — nó là chính luật ấy: Python khai cả câu, và
    khai bằng đúng thứ tiếng người dùng chọn.
  · THIẾU BẢN DỊCH THÌ HIỆN CÂU TIẾNG VIỆT — không bao giờ trống.

Ô ĐIỀN là `{0}`, `{1}`… theo thứ tự đưa vào, định dạng viết như f-string: `{0:.1f}`, `{1!r}`.
    tr("Đã chạy {0} lượt trong {1:.1f} phút", n, phut)
Bản tiếng Anh được thêm `{0|one|other}` — chọn số ít / số nhiều theo giá trị ô {0}:
    "Ran {0} {0|backtest|backtests} in {1:.1f} min"
Câu KHÔNG kèm giá trị thì trả nguyên văn (không đụng tới ngoặc nhọn hay `%`), nên câu kiểu cũ
vẫn viết được `tr("… %d …") % n`.

NHÃN BẢNG HẰNG (chuỗi đặt ngoài mọi hàm: nhãn ô của `hoi`, `lam`, `bat_dau`, `cai_dat`…)
không bọc được lúc nạp tệp — bọc là chốt cứng một thứ tiếng. Dịch lúc DÙNG: `tr(PHEP_SO[i][1])`.
Nhãn nào đi NGUYÊN sang giao diện thì chính giao diện dịch (`tr(nhãn)`); `tools/nhan_python_dich.py`
kê mấy cửa từ điển ấy ra để cổng bên web đòi bản tiếng Anh của chúng.

KHÔNG CÓ BIẾN MÔI TRƯỜNG như Jenifer. Bên ấy dải trạng thái và overlay là TIẾN TRÌNH PYTHON
RIÊNG, nên ngôn ngữ phải truyền qua `os.environ`. Cat chỉ sinh tiến trình con là LEAN và
`explorer.exe` — cả hai không đọc một chữ nào của ta — còn ba cửa sổ (sơ đồ, Kết quả,
Optimize) nằm chung MỘT tiến trình. Thêm một biến môi trường ở đây là thêm một nơi giữ cùng
một sự thật, mà chẳng ai đọc.

QUY TRÌNH khi thêm hay sửa chữ — mỗi lần, trong cùng lượt sửa:
  1. Viết câu tiếng Việt như thường (f-string cũng được).
  2. `tools\\dich.bat` — tự bọc câu Việt còn trần, thêm chỗ trống cho câu chưa có bản tiếng Anh.
  3. Điền bản tiếng Anh vào `tieng_anh.py` (thuật ngữ: bảng ở đầu `webui/src/tieng_anh.ts`).
     Chạy lại tới khi báo "song ngữ đủ".
`tests/test_ngon_ngu.py` soát y như thế: thiếu một câu là đỏ.

Tên `tr` như bên web. ĐỪNG đặt biến tên `tr` trong tệp có gọi nó — công cụ chặn.
"""
import re
import sys

# Nạp NGAY ở đầu tệp chứ không lười trong hàm: PyInstaller chỉ chắc chắn gói theo module nào
# được nhập thẳng thế này.
from . import tieng_anh

_hien = None          # "en" / "vi"; None = chưa biết — lần đầu `tr` chạy thì hỏi (xem `hien`)
_bang = None          # bài kiểm đặt bảng giả vào đây; None = bảng thật `tieng_anh.TIENG_ANH`
thieu = set()         # câu đã gặp lúc hiện tiếng Anh mà bảng chưa có — bài kiểm soát cái này

_HAI_DAU = re.compile(r"^(\s*)(.*?)(\s*)$", re.S)
_CO_DAU = re.compile("[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.I)
_SO_NHIEU = re.compile(r"\{(\d+)\|([^|{}]*)\|([^{}]*)\}")


def dat(n):
    """Đổi ngôn ngữ. Giá trị lạ (cài đặt cũ, gõ tay vào file) về TIẾNG ANH — cùng luật với
    `core.ngon_ngu`, một chỗ lạ không được làm hai bên lệch nhau."""
    global _hien
    _hien = "vi" if n == "vi" else "en"


def hien():
    """Ngôn ngữ đang hiện. App chốt theo cài đặt lúc dựng (`Api.__init__`), rồi
    `api.cai_dat_ghi` báo sang mỗi lần người dùng lưu. Chưa ai báo (chạy rời, bài kiểm gọi
    thẳng một hàm của `core`) thì tự đọc cài đặt một lần — qua `core` chứ không tự mở file,
    vì `core.ngon_ngu` là CHỖ DUY NHẤT biết khoá ấy tên gì và giá trị lạ thì về đâu."""
    if _hien is None:
        try:
            core = sys.modules.get("cat_studio.core")
            if core is None:
                from . import core
            dat(core.ngon_ngu())
        except Exception:
            dat("en")
    return _hien


def _tieng_anh(chu):
    """Câu tiếng Anh của `chu`, hay chính `chu` nếu bảng chưa có. Khoảng trắng hai đầu giữ
    nguyên, chỉ tra phần giữa: dòng trên mặt khối thụt đầu dòng bằng dấu cách, mà bảng chỉ
    ghi câu."""
    dau, giua, cuoi = _HAI_DAU.match(chu).groups()
    en = (tieng_anh.TIENG_ANH if _bang is None else _bang).get(giua)
    if not en:
        # Chỉ ghi câu CÓ DẤU tiếng Việt: nhãn vốn đã là tiếng Anh ("RSI", "Backtest") đi qua
        # `tr(BIẾN)` thì không thiếu gì cả. Có trần: app chạy cả ngày không phình bộ nhớ.
        if _CO_DAU.search(giua) and len(thieu) < 1000:
            thieu.add(giua)
        return chu
    return dau + en + cuoi


def tr(chu, *bien):
    """Câu theo ngôn ngữ đang hiện, điền `bien` vào `{0}`, `{1}`… Trả chuỗi."""
    if hien() == "en":
        chu = _tieng_anh(chu)
    if not bien:
        return chu
    if "|" in chu:
        chu = _SO_NHIEU.sub(
            lambda m: m[2] if _la_mot(bien[int(m[1])]) else m[3], chu)
    return chu.format(*bien)


def _la_mot(v):
    try:
        return float(v) == 1
    except (TypeError, ValueError):
        return False
