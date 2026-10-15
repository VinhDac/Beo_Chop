"""TRÌNH VẼ 5 TRẠM — cầu nối sang bài kiểm JavaScript `webui/kiem/trinh_ve.mjs`.

VÌ SAO PHẢI CÓ
--------------
Canvas vẽ MỘT trạm trong năm, và mỗi trạm có bộ đánh số riêng. Thứ hỏng ở đây không lộ
ra bằng mắt: lấy số thứ tự của trạm khác, đếm chấm đỏ theo cả cỗ máy thay vì theo từng
trạm, hay làm mất vị trí khối lúc đổi trạm — màn hình nào trông cũng "có vẻ đúng".

Bài này chỉ gọi sang đó, để `chay_tat_ca.py` không bỏ sót phía giao diện. Thiếu Node thì
BÁO RÕ và trượt, không lặng lẽ bỏ qua — một bài kiểm tự tắt khi thiếu công cụ là một bài
kiểm nói dối.

Chạy:  python tests\\test_trinh_ve.py
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAI = os.path.join(GOC, "webui", "kiem", "trinh_ve.mjs")

r = subprocess.run(["node", BAI], cwd=GOC, shell=(os.name == "nt"),
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print((r.stdout or "").rstrip())
if r.stderr.strip():
    print(r.stderr.rstrip(), file=sys.stderr)
if r.returncode != 0 and not (r.stdout or "").strip():
    print("  ✘ KHÔNG CHẠY ĐƯỢC node — bài kiểm giao diện chưa được canh.")
sys.exit(r.returncode)
