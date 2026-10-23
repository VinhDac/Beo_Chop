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
    ("test_chay_lean.py", "BỘ CHẠY LEAN — đọc file chứ đừng đọc mã thoát, và gột sạch venv"),
    # ĐỨNG SAU hai bài trên vì nó soi CHỖ GIỮA chúng: `sinh_ma` ghi dấu, `chay_lean`
    # dò dấu, mà hai mô-đun cố ý không import nhau — lệch một ký tự là cửa sổ View bày
    # một lượt chạy im lặng, không lỗi, không cảnh báo.
    ("test_vet.py", "VẾT TỪNG NHỊP — cỗ máy tự kể nó dừng ở cổng nào, và dòng vết "
                    "phải mang GIỜ CỦA NHỊP CŨ"),
    ("test_so_do_api.py", "Cửa sơ đồ — một cửa soát, ba tầng lưu, nhân bản không dính gốc"),
    ("test_giao_dien.py", "Biến CSS ma — thứ hỏng LẶNG, build vẫn sạch"),
    ("test_cai_dat.py", "Cài đặt app — cái núm phải NỐI VÀO ĐÂU ĐÓ, không phải núm giả"),
    ("test_o_so.py", "Ô số — gõ TỪNG PHÍM, số thập phân không được nuốt"),
    ("test_cua_man.py", "CỬA MÀN — chơi xong một màn thì màn kế PHẢI mở"),
    ("test_trang.py", "TRANG GIỚI THIỆU — đường dẫn, cỡ ảnh, tên lớp, và CON SỐ "
                      "trang khoe có bằng con số app đếm"),
    # ĐỨNG SAU mấy bài kia vì nó gọi cả bộ công cụ song ngữ (Node + một lượt Python
    # riêng) nên chậm nhất; và nó là bài DUY NHẤT đi qua cả hai thứ tiếng.
    ("test_ngon_ngu.py", "SONG NGỮ — mặc định tiếng Anh, và KHÔNG SÓT chữ nào"),
    # ĐỨNG CUỐI vì nó soi NGANG qua tất cả những bài trên: mấy bài kia soi từng bảng
    # với chính nó, bài này soi chỗ hai bảng phải khớp nhau. Dựng lại ví dụ 1 lôi ra
    # tám lỗi trong một buổi, và cả tám đều nằm ở mối nối chứ không nằm trong hộp.
    ("test_moi_noi.py", "MỐI NỐI — hai bảng phải dài bằng nhau, mà không ai đứng so"),
    # VÀ CUỐI CÙNG, một bậc cao hơn nữa: `test_moi_noi` soi hai bảng CỦA TA với nhau,
    # bài này soi bảng của ta với KỆ CỦA LEAN. Nó vào danh sách hôm nay, khi đã xanh —
    # nối một bài biết trước là đỏ thì ba ngày nữa không ai còn đọc cổng.
    ("test_du_lean.py", "ĐỦ LEAN — app có bày hết những gì LEAN cho, hay chỉ bày "
                        "theo ví dụ vừa gặp"),
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
