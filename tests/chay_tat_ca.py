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
    ("test_kho_va_lenh.py", "Kho backend · sổ lệnh (id của ta) · lưu trữ · tham số"),
    ("test_so_do_mau.py", "Sơ đồ mẫu Compress phải mở ra SẠCH"),
    ("test_doi_chieu_d02.py", "ĐỐI CHIẾU từng luật của D_02 — có luật nào rơi không"),
    ("test_tinh_toan.py", "Chỉ báo — đúng công thức D_02, NaN chứ không 0, gộp khung không nhìn trước"),
    ("test_khop_lenh.py", "Khớp lệnh — đường đi 4 điểm, spread quy về Bid, gap"),
    ("test_bo_chay.py", "Bộ chạy — thứ tự trong nhịp, luật lùi, tính xác định"),
    ("test_nhat_ky.py", "Nhật ký — bản ghi rỗng chữ, nhãn dựng lại, ghi/đọc ngược, soi lượt"),
    ("test_zone.py", "Cổng ZONE định nghĩa zone · MỐC NEO của khối Vào lệnh"),
    ("test_dat_ten.py", "Số gõ tay hai chỗ → cảnh báo + nút đặt tên"),
    ("test_giao_dien.py", "Biến CSS ma — thứ hỏng LẶNG, build vẫn sạch"),
    ("test_o_so.py", "Ô số — gõ TỪNG PHÍM, số thập phân không được nuốt"),
    ("test_lean_do_nhip.py", "Đo nhịp LEAN — một lượt một dòng, không ngắt sớm, JSON sạch"),
    ("test_cat_lean.py", "Cầu nối QC — trùng khít bộ cũ, gói dán được, chạy được khi KHÔNG có repo"),
    ("test_qc_api.py", "Nối QC qua API — máy chủ QC giả chạy thật bộ file, khoá không bao giờ lộ"),
    ("test_game_qc.py", "Màn chơi — luật sao/boss/nộp, màn ẩn là ẩn, việc nền, vỏ API cửa sổ"),
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
