"""Chạy toàn bộ test.

    python tests\\chay_tat_ca.py

Không mở cửa sổ, không nối mạng thật -> chạy được ở bất cứ đâu, kể cả trên CI.
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BAI = [
    ("test_danh_so.py", "Đánh số phân cấp · ghim số · ba trường hợp gặp lại khối cũ"),
    ("test_may.py", "Cỗ máy 5 trạm — từ điển, chuẩn hoá bất biến, soát lỗi từng trạm, chữ trên khối"),
    ("test_chuoi_nen.py", "Chuỗi nến + chỉ báo tính dần — gộp đúng biên, không nhìn trước, khớp bản tính tay"),
    ("test_bo_may.py", "Bộ máy 5 trạm — lịch, Gom, rủi ro, khớp lệnh, không nhìn trước, xác định"),
    ("test_mau_tram.py", "Mẫu dựng sẵn từng trạm — sạch, chạy được, đúng việc; chữ «vì sao» của nhật ký"),
    ("test_vo_may.py", "Lớp vỏ QC của cỗ máy 5 trạm — bộ file đóng gói chạy trên LEAN giả, lệnh, khởi động"),
    ("test_qc_may.py", "Cỗ máy 5 trạm chạy từ app qua API QC — đóng gói, chạy thật lớp vỏ, tải về, đọc kết quả"),
    ("test_may_api.py", "Cửa API trình vẽ 5 trạm — từ điển theo trạm, soát từng khối, lắp mẫu, lưu/mở"),
    ("test_giao_dien.py", "Biến CSS ma — thứ hỏng LẶNG, build vẫn sạch"),
    ("test_trinh_ve.py", "Trình vẽ 5 trạm — canvas của một trạm: số thứ tự, vị trí, chấm đỏ từng trạm"),
    ("test_o_so.py", "Ô số — gõ TỪNG PHÍM, số thập phân không được nuốt"),
    ("test_qc_api.py", "Nối QC qua API — máy chủ QC giả chạy thật bộ file, khoá không bao giờ lộ"),
]

hong = []
for ten, mo_ta in BAI:
    print(f"\n{'=' * 68}\n▶ {ten}  —  {mo_ta}\n{'=' * 68}")
    r = subprocess.run([sys.executable, os.path.join(HERE, ten)])
    if r.returncode:
        hong.append(ten)

print(f"\n{'=' * 68}")
if hong:
    print(f"  ✘ HỎNG: {', '.join(hong)}")
else:
    print(f"  ✔ {len(BAI)}/{len(BAI)} bài đều qua")
print("=" * 68)
sys.exit(1 if hong else 0)
