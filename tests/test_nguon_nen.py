"""Kho nến trên máy — đọc đúng, báo thiếu đúng, không tin file cụt.

App không tải nến nữa (DECISIONS.md D-09): kho chỉ còn đọc những bộ nến đã có sẵn trong
`du_lieu/nen/` cho Strategy Tester. Ba thứ đáng sợ nhất, đều được canh ở đây:

  1. **Báo đủ khi đang thiếu.** Tester chạy trên một khoảng ngắn hơn khoảng đã đặt mà
     không ai biết — người dùng tưởng mình thử từ 2015 trong khi thật ra từ 2016.
  2. **Tin vào file cụt.** Meta nói 300 nến, file `.npy` chỉ còn một nửa → `doc()` trả
     rỗng mà phép kiểm thiếu lại bảo "đủ rồi".
  3. **Lỗ hổng cuối tuần không được nhận ra.** Luật vùng nén dựa vào nó (core.md §12.6b).

Chạy:  python tests\\test_nguon_nen.py
"""
import io
import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import luu_tru  # noqa: E402
from cat_studio import nguon_nen as nn  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def nen(t_dau, so, buoc=60):
    """Một dãy nến M1 giả, giá tăng đều — chỉ cần đúng cột `t` là đủ cho mọi luật ở đây."""
    a = np.empty(so, dtype=nn.DTYPE)
    a["t"] = np.arange(t_dau, t_dau + so * buoc, buoc, dtype=np.int64)[:so]
    for k in ("o", "h", "l", "c"):
        a[k] = np.arange(so, dtype=np.float64)
    a["vol"] = 1
    return a


# ================= 1. thời điểm =================
print("\n▸ Đọc thời điểm")
kiem("chuỗi ngày, chuỗi ngày-giờ, epoch, None — đều hiểu",
     nn.thoi_diem("2025-01-01") == 1735689600
     and nn.thoi_diem("2025-01-01 00:00:00") == 1735689600
     and nn.thoi_diem(1735689600) == 1735689600
     and nn.thoi_diem(None) is None)
kiem("rác thì trả None chứ không ném lỗi qua cầu nối",
     nn.thoi_diem("hôm qua") is None and nn.thoi_diem("") is None)

# ================= 2. còn thiếu khoảng nào =================
print("\n▸ Kho có phủ hết khoảng xin không")
GIO = 3600
DA_CO = {"symbol": "T", "tu": 1000 * GIO, "den": 2000 * GIO, "so_nen": 5}
that_meta, that_file_du = nn.doc_meta, nn.file_du
# Mục này soát riêng phần SỐ HỌC KHOẢNG, nên thay luôn phép kiểm file: bản thật đọc kích
# thước `.npy` trên đĩa để bắt file cụt (mục 5 có bài riêng), mà ở đây làm gì có file.
nn.file_du = lambda s, m: True

nn.doc_meta = lambda s: None
kiem("chưa có bộ nến nào → thiếu trọn khoảng xin",
     nn.khoang_thieu("T", 10 * GIO, 20 * GIO) == [(10 * GIO, 20 * GIO)])
nn.doc_meta = lambda s: DA_CO
kiem("nằm gọn trong dải đã có → không thiếu gì",
     nn.khoang_thieu("T", 1200 * GIO, 1800 * GIO) == [])
kiem("thò ra bên phải → thiếu đúng phần thò",
     nn.khoang_thieu("T", 1500 * GIO, 2200 * GIO) == [(2000 * GIO, 2200 * GIO)])
kiem("thò ra bên trái → thiếu đúng phần thò",
     nn.khoang_thieu("T", 800 * GIO, 1500 * GIO) == [(800 * GIO, 1000 * GIO)])
kiem("bọc cả hai đầu → hai khoảng",
     nn.khoang_thieu("T", 800 * GIO, 2200 * GIO)
     == [(800 * GIO, 1000 * GIO), (2000 * GIO, 2200 * GIO)])
kiem("rời hẳn bên phải → thiếu trọn khoảng xin (không bịa ra phần ở giữa)",
     nn.khoang_thieu("T", 3000 * GIO, 3500 * GIO) == [(3000 * GIO, 3500 * GIO)])
kiem("rời hẳn bên trái → thiếu trọn khoảng xin",
     nn.khoang_thieu("T", 100 * GIO, 500 * GIO) == [(100 * GIO, 500 * GIO)])
kiem("khoảng ngược đời (đến < từ) → không nổ",
     nn.khoang_thieu("T", 2000 * GIO, 1000 * GIO) == [])
nn.doc_meta, nn.file_du = that_meta, that_file_du

# ================= 3. lỗ hổng =================
print("\n▸ Nhận ra lỗ hổng (cuối tuần)")
lien = nen(0, 60)
sau = nen(60 * 60 + 48 * 3600, 60)                  # cách 48 giờ = cuối tuần
mau = np.concatenate([lien, sau])
_doc = nn.doc
nn.doc = lambda s, tu=None, den=None: mau
lh = nn.lo_hong("T")
kiem("thấy đúng MỘT lỗ", len(lh) == 1, f"— {len(lh)}")
kiem("đo đúng độ dài (~48 giờ)", lh and 2870 < lh[0][2] < 2890, f"— {lh[0][2] if lh else 0} phút")
nn.doc = lambda s, tu=None, den=None: lien
kiem("chuỗi liền mạch → không báo lỗ nào", nn.lo_hong("T") == [])
nn.doc = _doc

# ================= 4. hình dạng dữ liệu =================
print("\n▸ Hình dạng dữ liệu")
kiem("một nến đúng 48 byte — một năm ≈ 18 MB", nn.DTYPE.itemsize == 48)
kiem("KHÔNG lưu spread từng nến (mô hình đã chốt là một con số ở Cài đặt)",
     "spread" not in (nn.DTYPE.names or ()))
kiem("chưa có gì → trả mảng RỖNG đúng dtype, không phải None",
     isinstance(nn.doc("__khong_ton_tai__"), np.ndarray)
     and nn.doc("__khong_ton_tai__").dtype == nn.DTYPE)
kiem("kho KHÔNG còn đường tải nến nào (D-09: chỉ phục vụ QuantConnect)",
     not any(hasattr(nn, x) for x in ("tai", "kiem_ket_noi", "uoc_tinh")))

# ================= 5. đọc từ đĩa, file cụt, liệt kê, xoá =================
print("\n▸ Đọc bộ nến trên đĩa — và không tin file cụt")
_tam = tempfile.mkdtemp(prefix="catstudio_test_")
_that_goc = luu_tru.goc
luu_tru.goc = lambda: _tam
try:
    _n = 300
    _a = nen(0, _n)
    _mn, _mj = nn._duong("ZZ")
    os.makedirs(os.path.dirname(_mn), exist_ok=True)
    np.save(_mn, _a, allow_pickle=False)
    with open(_mj, "w", encoding="utf-8") as f:
        json.dump({"symbol": "ZZ", "tu": 0, "den": (_n - 1) * 60, "so_nen": _n}, f)

    kiem("đọc lại được nguyên vẹn, cắt được theo khoảng",
         len(nn.doc("ZZ")) == _n and len(nn.doc("ZZ", 0, 59 * 60)) == 60)
    kiem("dữ liệu đủ → khoang_thieu trả rỗng",
         nn.khoang_thieu("ZZ", 0, (_n - 1) * 60) == [])
    ds = nn.liet_ke()
    kiem("liệt kê: một bộ ZZ, đúng số nến", len(ds) == 1 and ds[0]["symbol"] == "ZZ"
         and ds[0]["so_nen"] == _n, f"— {ds}")
    tt = nn.tom_tat("ZZ")
    kiem("tóm tắt: số nến + khoảng có thật", tt["so_nen"] == _n and tt["tu_chu"] != "—")

    with open(_mn, "r+b") as _f:                     # cắt cụt như một lần ghi dở
        _f.truncate(os.path.getsize(_mn) - 500)
    kiem("file .npy CỤT → coi như thiếu trọn khoảng, không kẹt ở 'đã đủ'",
         nn.khoang_thieu("ZZ", 0, (_n - 1) * 60) == [(0, (_n - 1) * 60)])
    kiem("xoá → hết hẳn khỏi danh sách", nn.xoa("ZZ") and nn.liet_ke() == [])
finally:
    luu_tru.goc = _that_goc
    shutil.rmtree(_tam, ignore_errors=True)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
