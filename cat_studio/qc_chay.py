"""ĐẦU VÀO MỘT LƯỢT CHẠY TRÊN QUANTCONNECT — rổ mã, loại thị trường, ngày, vốn.

Trước đây file này còn giữ cả việc chạy nền: đóng gói bộ máy, đẩy lên QC, tải nhật ký,
chấm điểm. **D-11 bỏ hết phần đó**: app chỉ là VỎ của QuantConnect, nên đường chạy mới sẽ
sinh thẳng một thuật toán QC từ sơ đồ, không có bộ máy nào chạy tại máy nữa.

Còn lại đúng những thứ KHÔNG phải mô phỏng: loại thị trường lớp vỏ đăng ký được, trần số
mã một rổ, và phép soát đầu vào của chế độ Sáng tạo — soát tại máy để người chơi biết sai
ngay, chứ không đi một vòng lên cloud rồi mới nghe một câu tiếng Anh.
"""
import re
from datetime import datetime

from . import game


_RE_SYMBOL = re.compile(r"^[A-Z0-9]{3,20}$")

#: Loại thị trường của cỗ máy 5 trạm (D-10) — đúng những loại lớp vỏ QC biết đăng ký.
LOAI_THI_TRUONG = {"forex": "Ngoại hối (OANDA)", "cfd": "CFD (OANDA)",
                   "co_phieu": "Cổ phiếu Mỹ", "crypto": "Crypto (Coinbase)"}
#: Một rổ quá to là một lượt QC chạy cả giờ — trần cho chế độ Sáng tạo.
TRAN_SO_MA = 20


def soat_tu_do_may(tu_do):
    """Đầu vào Sáng tạo cho CỖ MÁY 5 TRẠM → `{ma: [...], loai, tu, den, von}` sạch, hoặc
    `LoiGame` nói rõ. Khác `soat_tu_do` (một symbol): cỗ máy chạy trên cả một RỔ mã."""
    tu_do = tu_do or {}
    ma, thay = [], set()
    for x in tu_do.get("ma") or []:
        x = str(x or "").strip().upper()
        if x and x not in thay:
            if not _RE_SYMBOL.match(x):
                raise game.LoiGame(f"Mã «{x}» không hợp lệ: chữ in hoa / số, 3–20 ký tự.")
            thay.add(x)
            ma.append(x)
    if not ma:
        raise game.LoiGame("Rổ chưa có mã nào — thêm ít nhất một mã, vd. EURUSD.")
    if len(ma) > TRAN_SO_MA:
        raise game.LoiGame(f"Rổ tối đa {TRAN_SO_MA} mã — {len(ma)} mã là một lượt chạy cả giờ.")
    loai = tu_do.get("loai") or "forex"
    if loai not in LOAI_THI_TRUONG:
        raise game.LoiGame(f"Không có loại thị trường «{loai}».")
    try:
        tu = datetime.strptime(str(tu_do.get("tu") or ""), "%Y-%m-%d")
        den = datetime.strptime(str(tu_do.get("den") or ""), "%Y-%m-%d")
    except ValueError:
        raise game.LoiGame("Ngày phải dạng YYYY-MM-DD, vd. 2025-10-01.")
    if tu > den:
        raise game.LoiGame("Ngày bắt đầu nằm SAU ngày kết thúc.")
    try:
        von = float(tu_do.get("von") or 10_000)
    except (TypeError, ValueError):
        raise game.LoiGame("Vốn phải là một con số.")
    if not von > 0:
        raise game.LoiGame("Vốn phải lớn hơn 0.")
    return {"ma": ma, "loai": loai, "tu": tu.strftime("%Y-%m-%d"),
            "den": den.strftime("%Y-%m-%d"), "von": von}


