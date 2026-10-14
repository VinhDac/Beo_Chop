"""GAME ĐẦU-CUỐI — cầu nối sang bài kiểm `webui/kiem/game.mjs`.  (D-09)

Bài bên kia mở cửa sổ vẽ THẬT trong Chromium, nối nó với `api.Api` THẬT (qua
`webui/kiem/cau_noi_game.py`) và một QuantConnect GIẢ chạy thật bộ file app đóng gói, rồi
chơi trọn màn 1-1 như người chơi: màn hình chính → khoá → truyện → bản đồ → phiếu → xưởng
→ ▶ đầy đủ nhiều lần → ba histogram → xem máy nghĩ → đấu màn ẩn → mở khoá 1-2.

Vì sao cần nó dù đã có `test_game_qc.py`: lỗi THẬT đầu tiên của giao diện game nằm đúng ở
chỗ hai bên gặp nhau — nút «Lắp máy gợi ý» không đổi gì vì Python trả cỗ máy thiếu thẻ
khối; và máy gợi ý gộp hai kiểu so trong một cổng, bản thô soát qua nhưng bản chuẩn hoá
(đường giao diện đi) thì lỗi. Không bài nào chỉ một phía bắt được hai lỗi đó.

Thiếu Playwright thì bài bên kia tự BỎ QUA (máy người dùng không bắt buộc cài). Thiếu Node
thì BÁO RÕ và trượt — một bài kiểm tự tắt khi thiếu công cụ là một bài kiểm nói dối.

Chạy:  python tests\\test_game_giao_dien.py   (cần `npm run build` trong webui/ trước)
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAI = os.path.join(GOC, "webui", "kiem", "game.mjs")

env = dict(os.environ, PYTHON=sys.executable)
r = subprocess.run(["node", BAI], cwd=GOC, shell=(os.name == "nt"), env=env,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print((r.stdout or "").rstrip())
if r.stderr.strip():
    print(r.stderr.rstrip(), file=sys.stderr)
if r.returncode != 0 and not (r.stdout or "").strip():
    print("  ✘ KHÔNG CHẠY ĐƯỢC node — bài kiểm game đầu-cuối chưa được canh.")
sys.exit(r.returncode)
