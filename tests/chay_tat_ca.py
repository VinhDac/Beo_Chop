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
    ("test_so_do.py", "Sơ đồ — Nhóm, Quay về, vòng phải khép, bộ nhớ của cái nút"),
    ("test_hoi.py", "Từ điển XÁC NHẬN — 5 loại câu hỏi, và luật không bịa gì của LEAN"),
    ("test_lam.py", "Từ điển HÀNH ĐỘNG — 8 loại việc, và đường ranh «không nhớ ticket»"),
    ("test_bat_dau.py", "Khối BẮT ĐẦU — nửa «thiết lập», và nó phải sống qua lưu/mở"),
    ("test_sinh_ma.py", "BỘ SINH MÃ — sơ đồ thành thuật toán LEAN Python chạy được"),
    ("test_so_do_api.py", "Cửa sơ đồ — một cửa soát, ba tầng lưu, nhân bản không dính gốc"),
    ("test_giao_dien.py", "Biến CSS ma — thứ hỏng LẶNG, build vẫn sạch"),
    ("test_o_so.py", "Ô số — gõ TỪNG PHÍM, số thập phân không được nuốt"),
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
