"""ĐÓNG GÓI SANG QUANTCONNECT ra đĩa — để dán tay lên quantconnect.com.

    python tools/dong_goi_lean.py                           sơ đồ mẫu D_02, cả năm 2025
    python tools/dong_goi_lean.py du_lieu/chien_luoc/X.json  một chiến lược đã lưu
    python tools/dong_goi_lean.py --tu 2025-10-01 --den 2025-12-31     ▶ nhanh (D-03)

Ra thư mục `dist/lean/`: `main.py` + `nguon_1.py` (+ `nguon_2.py`… nếu cần). Trên
quantconnect.com: tạo project Python, dán `main.py` đè lên file main.py có sẵn, thêm
từng file `nguon_*.py` với ĐÚNG tên đó, rồi bấm Backtest.

Có gói Researcher thì khỏi dán: `tools/chay_qc.bat` hay nút ▶ trong app tự gửi lên.
Toàn bộ cách đóng gói nằm ở `cat_studio/goi_qc.py` — file này chỉ là vỏ dòng lệnh.
"""
import argparse
import os
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)
sys.path.insert(0, os.path.join(GOC, "lean"))

from cat_studio.goi_qc import (  # noqa: E402,F401  (tên cũ — bài kiểm và chay_qc dùng)
    CAU_HINH_MAC_DINH, GIOI_HAN, GOI, NGUON, doc_nguon, dong_goi, gon, nen_goi, so_do, soat)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Đóng gói một sơ đồ Cat Studio sang QuantConnect.")
    ap.add_argument("so_do", nargs="?", help="file chiến lược .json (bỏ trống = sơ đồ mẫu D_02)")
    ap.add_argument("--tu", default=CAU_HINH_MAC_DINH["tu"], help="ngày bắt đầu YYYY-MM-DD")
    ap.add_argument("--den", default=CAU_HINH_MAC_DINH["den"], help="ngày kết thúc YYYY-MM-DD")
    ap.add_argument("--symbol", default=CAU_HINH_MAC_DINH["symbol"])
    ap.add_argument("--gioi-han", type=int, default=GIOI_HAN,
                    help="trần mỗi file (byte) — Free 30000, Researcher 62000")
    ap.add_argument("--ra", default=os.path.join(GOC, "dist", "lean"))
    a = ap.parse_args(argv)
    files = dong_goi(so_do(a.so_do), {"tu": a.tu, "den": a.den, "symbol": a.symbol},
                     a.gioi_han)
    os.makedirs(a.ra, exist_ok=True)
    for cu in os.listdir(a.ra):                    # bỏ phần phụ của lần đóng gói trước
        if cu.startswith("nguon_") and cu.endswith(".py"):
            os.remove(os.path.join(a.ra, cu))
    for ten_file, noi_dung in files.items():
        with open(os.path.join(a.ra, ten_file), "w", encoding="utf-8", newline="\n") as f:
            f.write(noi_dung)
        print(f"  {ten_file:12s} {len(noi_dung.encode('utf-8')) / 1024:5.1f} KB")
    print(f"Đã đóng gói vào {a.ra}. Trên quantconnect.com: tạo project Python → dán "
          f"main.py đè lên main.py có sẵn → thêm "
          + ", ".join(t for t in files if t != "main.py")
          + " với đúng tên đó → bấm Backtest.")
    return files


if __name__ == "__main__":
    main()
