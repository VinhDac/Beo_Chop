"""Chạy toàn bộ test.

    python tests\\chay_tat_ca.py

Không mở cửa sổ, không nối MT5 -> chạy được ở bất cứ đâu, kể cả trên CI.
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ⚠ ĐỢT 1 của lần dọn sang HFT market maker đã BỎ 7 bài, và không bài nào được
#    "tạm treo" cả — chúng kiểm những thứ đã bị xoá khỏi repo:
#
#      test_so_do_mau · test_doi_chieu_d02   sơ đồ mẫu D_02
#      test_nguon_nen · test_tinh_toan       nguồn nến M1 + chỉ báo theo nến
#      test_khop_lenh                        đường đi 4 điểm trong một nến
#      test_gui_lenh                         tầng đặt lệnh MT5
#      test_zone                             cổng ZONE + mốc neo của D_02
#
#    Một bài kiểm không còn đối tượng thì không phải "độ phủ đang giảm", nó là rác.
#    Lấy lại bất cứ lúc nào: `git checkout f1c90fb -- tests/`.
#
# ⚠ Bảy bài CÒN LẠI chưa sạch. `test_bo_chay` / `test_kho_va_lenh` / `test_dat_ten`
#    vẫn dựng nến giả và zone giả, `test_danh_so` vẫn trộn bài kiểm đồ thị với bài
#    kiểm từ vựng. Chúng còn xanh vì backend chưa bị đụng tới — đợt 3 sẽ tách.
# ⚠ ĐỢT 2 bỏ thêm 3 bài, và cái giá phải nói to: cả ba đều dựng fixture bằng
#    `bo_chay.chay()` — một lần chạy backtest thật trên nến giả.
#
#      test_bo_chay    thứ tự trong nhịp · luật lùi · tính xác định
#      test_nhat_ky    bản ghi rỗng chữ · nhãn dựng lại · ghi/đọc ngược
#      test_dat_ten    số gõ tay hai chỗ → cảnh báo + nút đặt tên
#
#    Hai bài sau kiểm những thứ CÒN SỐNG (`nhat_ky.py`, cơ chế bảng tham số) — chỉ
#    cái máy đẻ ra dữ liệu cho chúng là chết. Nghĩa là hai module đó giờ KHÔNG CÓ ĐỘ
#    PHỦ NÀO, và đó là nợ, không phải dọn xong. Ghi ở `tai_lieu/o_cam_trong.md`.
#
#    Giữ một `bo_chay` rỗng ruột chỉ để nuôi fixture thì đuôi vẫy được cả con chó.
BAI = [
    ("test_danh_so.py", "Đánh số phân cấp · ghim số · ba trường hợp gặp lại khối cũ"),
    ("test_kho_va_lenh.py", "Kho backend · sổ lệnh (id của ta) · lưu trữ · tham số"),
    ("test_nguon_tick.py", "Nguồn tick — định dạng, mất gói, sổ lỗ hổng (không chạm mạng)"),
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
