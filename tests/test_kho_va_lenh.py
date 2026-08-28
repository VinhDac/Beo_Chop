"""Cơ chế KHO và cơ sở lưu trữ.

  kho/       phân loại theo NGUỒN. Bài này canh **cơ chế**, không canh nội dung: đếm
             đúng tám toán hạng là ràng buộc sai — thêm `microprice` vào là bài đỏ dù
             chẳng có gì hỏng. Cái phải canh là những thứ hỏng LẶNG.
             Quan trọng nhất là `_soat_trung` — trùng khoá giữa hai module là lỗi im
             lặng tệ nhất (hai engine cùng khai `atr` với hai nghĩa thì mọi chiến lược
             dùng nó đều sai mà không báo gì), nên nó phải nổ NGAY LÚC IMPORT chứ
             không đợi tới lúc chạy.
  luu_tru.py mọi đường dẫn ở đúng MỘT chỗ, có di cư từ bố cục cũ.

⚠ HAI MỤC ĐÃ ĐI. **Sổ lệnh** (~55 dòng) canh `so_lenh.py`: lệnh mang id CỦA TA
(`L-0001`) chứ không mượn ticket MT5, nhờ vậy "vùng này đã sinh lệnh" là một phép tra
bảng chứ không phải cờ ẩn — và cái bug đoán mò `HasOpenPosition()` của D_02 không thể
tái diễn. **Bảng tham số** (~60 dòng) đi cùng từ vựng.

Cả hai là NỢ ĐỘ PHỦ, ghi ở `tai_lieu/o_cam_trong.md`.
Lấy lại: `git show f1c90fb:tests/test_kho_va_lenh.py`.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import kho  # noqa: E402
from cat_studio import luu_tru  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


# ================= 1. KHO =================
print("\n▸ Kho backend — cơ chế, không phải nội dung")
d = kho.danh_muc()
kiem("`danh_muc()` trả đủ hình dạng, mọi module đều khai đủ ba khoá bắt buộc",
     bool(d["module"]) and all(m.get("ma_so") and m.get("ten") is not None
                               and m.get("mo_ta") is not None for m in d["module"]))
kiem("`_gom` gắn `nguon` vào TỪNG mục — thiếu nó thì hộp thoại không chia mục được",
     bool(kho.TOAN_HANG) and all(t.get("nguon") for t in kho.TOAN_HANG))
kiem("bảng tra nhanh khớp với danh sách, và khoá lạ rơi về chính nó",
     kho.TOAN_HANG_KEYS == [t["key"] for t in kho.TOAN_HANG]
     and len(kho.THEO_KEY) == len(kho.TOAN_HANG)
     and kho.nhan("khong_co") == "khong_co" and kho.tham_so("khong_co") == [])

# MỖI TOÁN HẠNG PHẢI KHAI ĐỦ THỨ `core` SẼ ĐỌC. Thiếu `loai` thì ô đơn vị suy sai;
# thiếu `don_vi` trên một đại lượng ĐẾM thì `bid_kl` và `ton_kho` gộp chung đơn vị và
# nút chọn tham số mời nhầm. Cả hai đều KHÔNG nổ — chúng chỉ cho ra một câu vô nghĩa
# mà vẫn chạy, đúng loại lỗi bài này sinh ra để chặn.
LOAI = ("muc_gia", "khoang_cach", "dem", "dung_sai")
thieu = [t["key"] for t in kho.TOAN_HANG if t.get("loai") not in LOAI]
kiem("mọi toán hạng khai `loai` hợp lệ", not thieu, f"— thiếu: {thieu}")
thieu = [t["key"] for t in kho.TOAN_HANG
         if t.get("loai") == "dem" and not t.get("don_vi")]
kiem("đại lượng ĐẾM nào cũng nói rõ đếm bằng gì", not thieu, f"— thiếu: {thieu}")
thieu = [t["key"] for t in kho.TOAN_HANG
         if (t.get("loai") == "dung_sai") != bool(t.get("dung_sai"))]
kiem("cờ `dung_sai` và `loai` không nói ngược nhau", not thieu, f"— lệch: {thieu}")


# TRÙNG KHOÁ PHẢI NỔ NGAY — phép quan trọng nhất của cả bài.
#
# ⚠ Trước đợt 3, phép này va một module GIẢ vào kho THẬT (`kho._gom("TOAN_HANG")`) để
# đụng khoá `close`. Kho rỗng rồi thì không còn gì để va vào, và phép so lặng lẽ trở
# thành "không nổ" — tức nó sẽ báo XANH mãi mãi trong khi cơ chế có hỏng cũng không ai
# biết. Đúng loại chết im lặng mà `_soat_trung` sinh ra để chặn, chỉ là xảy ra với
# chính bài kiểm nó.
#
# Nên giờ dựng đủ HAI module giả và cho chúng đụng nhau. Phép kiểm vì thế không còn
# phụ thuộc kho có gì — nó kiểm đúng cái cơ chế, và sẽ vẫn đúng khi kho đầy trở lại.
class _EngineA:
    MA_SO, TEN, MO_TA = "gia_a", "Giả A", ""
    CHI_BAO = BANG_TRANG_THAI = []
    TOAN_HANG = [{"key": "mid", "nhan": "Giá giữa", "nhom": "Giá", "tham_so": []}]


class _EngineB:
    MA_SO, TEN, MO_TA = "gia_b", "Giả B", ""
    CHI_BAO = BANG_TRANG_THAI = []
    TOAN_HANG = [{"key": "mid", "nhan": "Đụng hàng", "nhom": "Giá", "tham_so": []}]


try:
    kho._soat_trung([dict(x, nguon=m.MA_SO) for m in (_EngineA, _EngineB)
                     for x in m.TOAN_HANG], "toán hạng")
    kiem("trùng khoá giữa hai module → nổ ngay lúc import", False, "— không nổ")
except RuntimeError as e:
    kiem("trùng khoá giữa hai module → nổ ngay lúc import",
         "mid" in str(e) and "gia_a" in str(e) and "gia_b" in str(e))

print("\n▸ Cơ sở lưu trữ")
kiem("mọi thứ nằm dưới đúng MỘT thư mục gốc",
     os.path.basename(luu_tru.goc()) == "du_lieu")
kiem("chiến lược có thư mục riêng, tên đúng nghĩa",
     os.path.basename(luu_tru.thu_muc_chien_luoc()) == "chien_luoc")
kiem("tên file bị chặn thoát ra ngoài thư mục",
     os.path.dirname(luu_tru.duong_dan_chien_luoc("../../hack"))
     == luu_tru.thu_muc_chien_luoc(),
     f"— {luu_tru.duong_dan_chien_luoc('../../hack')}")
tt = luu_tru.tom_tat()
kiem("tóm tắt kho nói rõ đường dẫn thật", tt["goc"] and len(tt["muc"]) == 3)

# ================= 4. BẢNG THAM SỐ — Ổ CẮM TRỐNG =================
#
# Cả mục (~60 dòng) đã đi ở đợt 2. Nó dựng trên `api.demo_process()` — sơ đồ mẫu
# Compress (D_02) — rồi đếm thẳng vào nội dung của nó: đủ 11 tham số,
# `nguong_nen_bps` phải được hỏi ở CẢ HAI sơ đồ, không hằng số gõ tay nào lặp lại.
#
# HAI PHÉP CUỐI MẤT THEO LÀ ĐÁNG TIẾC, và phải nói ra: "bỏ một tham số đang dùng
# → báo lỗi" và "khai tham số không ai dùng → cảnh báo" kiểm CƠ CHẾ của bảng tham
# số, không kiểm D_02. Cơ chế ấy còn sống nguyên trong `core.py` nhưng giờ KHÔNG
# CÓ ĐỘ PHỦ NÀO. Ghi ở `tai_lieu/o_cam_trong.md` — đó là nợ, không phải dọn xong.
#
# Lấy lại: `git show f1c90fb:tests/test_kho_va_lenh.py`.

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
