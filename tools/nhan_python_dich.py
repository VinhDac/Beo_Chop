# -*- coding: utf-8 -*-
"""Nhãn Python mà GIAO DIỆN dịch bằng `tr(nhãn)` lúc hiện ra — in ra một mảng JSON.

Bộ công cụ song ngữ (`webui/dich/soat.mjs`) gọi file này để biết bảng dịch còn thiếu
nhãn nào. Chỉ ĐỌC: không ghi gì, không mở cửa sổ, không đọc file cài đặt.

VÌ SAO PHẢI CÓ FILE NÀY. Luật nền của Cat_Studio là "Python khai, giao diện chỉ bày
lại": nhãn ô, câu gợi ý, tên loại khối đều nằm trong `cat_studio/hoi.py`, `lam.py`,
`bat_dau.py`, `cai_dat.py`, `toi_uu.py` — không một câu nào trong TypeScript. Nên bộ
soát bên web quét hết `webui/src/` cũng KHÔNG thấy chúng, và bản tiếng Anh thiếu nhãn
nào thì không bài kiểm nào kêu. File này mở đúng mấy cửa từ điển ấy ra cho nó thấy.

Chép cách làm của Jenifer_Studio (`tools/nhan_python_dich.py` bên ấy). Khác một chỗ:
Jenifer có MỘT cửa `bootstrap` gom hết, Cat không — nên ở đây liệt kê từng cửa từ điển.
⚠ Thêm một từ điển mới cho giao diện mà quên ghi vào đây là bản tiếng Anh hiện nhãn ấy
bằng tiếng Việt mà cổng vẫn xanh.

Chữ Python DỰNG ĐỘNG (dòng trên mặt khối, bảng Vấn đề, câu lỗi lượt chạy…) không nằm ở
đây: Python tự dịch ở nơi câu sinh ra — `cat_studio/ngon_ngu.py`, bảng
`cat_studio/tieng_anh.py`, công cụ `tools/dich_python.py`. Nhãn nào có ở cả hai bảng thì
công cụ ấy soát hai bản tiếng Anh phải giống hệt.
"""
import json
import os
import sys
import tempfile

# .pyc ra thư mục tạm: file này chạy ở MỌI lần `npm run build` / `npm run dich`, không
# đẩy ra là `cat_studio/__pycache__` mọc lại trong kho.
sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "cat-studio-pyc")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)
sys.stdout.reconfigure(encoding="utf-8")

from cat_studio import bat_dau        # noqa: E402
from cat_studio import cai_dat        # noqa: E402
from cat_studio import chay_lean      # noqa: E402
from cat_studio import hoi            # noqa: E402
from cat_studio import lam            # noqa: E402
from cat_studio import toi_uu         # noqa: E402

nhan = []


def gom(x):
    """Mọi chuỗi trong `x`, mọi tầng — khoá lẫn giá trị; soat.mjs tự lọc lấy chữ Việt."""
    if isinstance(x, str):
        nhan.append(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            gom(k)
            gom(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            gom(v)


# NĂM TỪ ĐIỂN — nguồn của gần hết chữ trong mấy hộp thoại khối: nhãn ô, câu gợi ý dưới
# ô, tên và mô tả từng loại khối, nhãn phép so / phép ghép, nhãn nhóm Cài đặt.
for td in (hoi.tu_dien(), lam.tu_dien(), bat_dau.tu_dien(), cai_dat.tu_dien(),
           toi_uu.tu_dien()):
    gom(td)

# BẢNG LỆNH của trang Kết quả. Python tra bảng rồi gửi sang MỘT CHUỖI (`doc_luot_chay`
# → `dong_lenh`), nên giao diện nhận một chữ trần và dịch bằng `tr(l.loai)` —
# bảng dịch phải có sẵn cả hai bảng này.
gom(chay_lean.LOAI_LENH)
gom(chay_lean.TRANG_THAI_LENH)

print(json.dumps(sorted(set(nhan)), ensure_ascii=False))
