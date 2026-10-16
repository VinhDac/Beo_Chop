"""LUẬT CHƠI — màn, boss, sao, độ gọn, sổ nộp.  (DECISIONS.md D-05 · D-06 · D-08)

Một chỗ DUY NHẤT biết "điểm" là gì. Không biết QuantConnect, không biết giao diện: nhận
`meta` của một lần chạy (dòng meta trong nhật ký tải về) và trả lời — thắng boss không,
mấy sao, gọn cỡ nào. Bộ chạy nền (`qc_chay`) và giao diện chỉ hỏi ở đây.

VÒNG CHƠI (D-05)
----------------
chọn màn → lắp máy → ▶ nhanh / ▶ đầy đủ trên MÀN ĐÃ THẤY → xem vì sao → sửa → NỘP:
app chạy cỗ máy trên MÀN ẨN — khoảng ngày do app giữ, người chơi không chọn được (D-06)
— rồi chấm sao. Muốn nộp phải có một lượt ▶ đầy đủ của ĐÚNG cỗ máy đó (cùng vân tay):
nộp một cỗ máy chưa từng chạy trọn màn đã thấy thì ⭐ và ⭐⭐ lấy gì mà chấm.

SAO (D-05; chi tiết đo ở D-08)
------------------------------
  ⭐    chạy sạch   — chạy trọn màn đã thấy, có ít nhất MỘT lệnh đóng
  ⭐⭐   thắng boss  — và lãi % trên màn đã thấy HƠN boss "Mua rồi giữ" cùng khoảng
  ⭐⭐⭐  vẫn thắng   — và trên MÀN ẨN cũng hơn boss
Mỗi sao cần mọi sao trước nó. Độ gọn = số khối + số tham số (ít hơn là gọn hơn) — ghi kèm
mỗi lần nộp, không cộng vào sao.

SỔ (`du_lieu/game.json`)
------------------------
Ghi bằng `luu_tru.ghi_json_nguyen_tu`, giữ khoá luồng: bộ chạy nền ghi, giao diện đọc.
"""
import copy
import json
import os
import threading
from datetime import datetime, timezone

from . import core
from . import luu_tru

FILE_SO = "game.json"

#: Màn của chế độ Chiến dịch. `an` KHÔNG BAO GIỜ ra tới giao diện (`man_cong_khai`).
MAN = (
    {
        "id": "ro-ngoai-hoi-2024",
        "ten": "Bộ bốn ngoại hối · 2024",
        "ban_do": "Ngoại hối",
        "ro": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
        "loai": "forex",
        "von": 10_000.0,
        "thay": ("2024-01-01", "2024-12-31"),
        "nhanh": ("2024-10-01", "2024-12-31"),
        "an": ("2025-01-01", "2025-12-31"),
        "an_mo_ta": "12 tháng ngay sau màn này",
        "boss": "mua_giu_deu",
        "loi_dan": ("Bốn cặp tiền đi ngang nhiều hơn đi xu hướng, nên «Mua rồi giữ cả rổ» "
                    "là đối thủ yếu — nhưng đừng mừng vội: vào lệnh đều đều là nộp tiền "
                    "cho spread. Màn này thưởng cỗ máy biết ĐỨNG NGOÀI."),
    },
    {
        "id": "kim-loai-2024",
        "ten": "Vàng và bạc · 2024",
        "ban_do": "Kim loại",
        "ro": ["XAUUSD", "XAGUSD"],
        "loai": "cfd",
        "von": 10_000.0,
        "thay": ("2024-01-01", "2024-12-31"),
        "nhanh": ("2024-10-01", "2024-12-31"),
        "an": ("2025-01-01", "2025-12-31"),
        "an_mo_ta": "12 tháng ngay sau màn này",
        "boss": "mua_giu_deu",
        "loi_dan": ("Năm vàng tăng rất mạnh, nên «Mua rồi giữ cả rổ» là đối thủ khó. Rổ chỉ "
                    "hai mã nên trạm ① gần như không phải chọn: trận này là của trạm ② và "
                    "④ — biết lúc nào ôm và lúc nào cắt."),
    },
    {
        "id": "co-phieu-my-2024",
        "ten": "Bốn ông lớn · 2024",
        "ban_do": "Cổ phiếu Mỹ",
        "ro": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "loai": "co_phieu",
        "von": 10_000.0,
        "thay": ("2024-01-01", "2024-12-31"),
        "nhanh": ("2024-10-01", "2024-12-31"),
        "an": ("2025-01-01", "2025-12-31"),
        "an_mo_ta": "12 tháng ngay sau màn này",
        "boss": "mua_giu_deu",
        "loi_dan": ("Cả bốn đều tăng trong năm, nên hơn «Mua rồi giữ cả rổ» nghĩa là phải "
                    "chọn ĐÚNG mã và dồn vốn vào nó: màn của trạm ① và ③."),
    },
)

BOSS = {
    "mua_giu": {"ten": "Mua rồi giữ",
                "mo_ta": "Mua ở nến đầu tiên, giữ tới nến cuối cùng. Không làm gì khác."},
    # Boss của một RỔ: lãi % trung bình của mọi mã trong rổ kể từ lúc hết khởi động —
    # đúng bằng lãi của một danh mục chia đều vốn, mua một lần rồi để yên. Từ D-11 con
    # số này do QuantConnect tính, app chỉ so.
    "mua_giu_deu": {"ten": "Mua rồi giữ cả rổ",
                    "mo_ta": "Chia đều vốn cho mọi mã trong rổ ngay khi đủ dữ liệu, rồi giữ "
                             "tới hết. Không chọn mã, không cắt lỗ, không làm gì khác."},
}

#: Các kiểu chạy. "tu_do" là chế độ Sáng tạo (D-07): mọi symbol, mọi khoảng ngày, không chấm.
LOAI = {
    "nhanh": "▶ nhanh",
    "day_du": "▶ đầy đủ",
    "nop": "Nộp",
    "tu_do": "▶ tự do",
}

#: Giữ bao nhiêu lượt trong lịch sử chạy QC (cũ hơn thì bỏ khỏi sổ, file nhật ký vẫn còn).
GIU_LICH_SU = 100

_khoa = threading.Lock()


class LoiGame(Exception):
    """Một câu tiếng Việt nói vì sao chưa làm được — giao diện in thẳng ra."""


# ---------------------------------------------------------------------------
# Màn
# ---------------------------------------------------------------------------
def man(man_id):
    for m in MAN:
        if m["id"] == man_id:
            return m
    raise LoiGame(f"Không có màn «{man_id}».")


def ro_cua(m):
    """Rổ mã của một màn."""
    return list(m.get("ro") or [])


def man_cong_khai(m):
    """Thông tin màn cho giao diện — KHÔNG có ngày của màn ẩn (D-06: app giữ màn ẩn)."""
    return {"id": m["id"], "ten": m["ten"], "ban_do": m["ban_do"],
            "ro": ro_cua(m), "loai": m.get("loai"),
            "von": m["von"], "thay": list(m["thay"]), "nhanh": list(m["nhanh"]),
            "an_mo_ta": m["an_mo_ta"], "boss": {"id": m["boss"], **BOSS[m["boss"]]},
            "loi_dan": m["loi_dan"]}


def khoang(man_id, loai):
    """`(từ, đến)` của một kiểu chạy trên một màn."""
    m = man(man_id)
    if loai == "nhanh":
        return m["nhanh"]
    if loai == "day_du":
        return m["thay"]
    if loai == "nop":
        return m["an"]
    raise LoiGame(f"Kiểu chạy «{loai}» không thuộc một màn.")


# ---------------------------------------------------------------------------
# Chấm
# ---------------------------------------------------------------------------
def cham(meta):
    """Một lần chạy → `{lai_pt, mua_giu_pt, thang_boss, so_dong, sach}`.

    `sach` = chạy trọn và có ít nhất một lệnh đóng: cỗ máy không bao giờ giao dịch thì
    "không thua" chẳng nói lên điều gì. Thiếu giá boss (khoảng ngày không có nến) thì
    không ai thắng ai — `thang_boss` False.

    Nhận meta của CẢ HAI dạng nhật ký. Cỗ máy 5 trạm đo bằng chính con số bộ máy đã tính:
    `boss_pt` (mua giữ chia đều cả rổ) và số lệnh ĐÃ KHỚP — ở đó không còn khái niệm "lệnh
    đóng", vì vị thế là một TỶ TRỌNG và đóng chỉ là đưa tỷ trọng ấy về 0."""
    tk = meta.get("thong_ke") or {}
    lai = float(tk.get("lai_pt") or 0.0)
    if meta.get("dang") == M.DANG:
        mg = tk.get("boss_pt")
        so_dong = int(tk.get("so_lenh_khop") or 0)
    else:
        mg = meta.get("mua_giu_pt")
        so_dong = int(tk.get("so_dong") or 0)
    return {"lai_pt": round(lai, 2),
            "mua_giu_pt": None if mg is None else round(float(mg), 2),
            "thang_boss": mg is not None and lai > float(mg),
            "so_dong": so_dong,
            "sach": so_dong >= 1}


def sao(thay, an=None):
    """Số sao từ phần chấm của màn đã thấy (▶ đầy đủ) và, nếu đã nộp, của màn ẩn."""
    if not thay or not thay.get("sach"):
        return 0
    if not thay.get("thang_boss"):
        return 1
    if not an or not an.get("thang_boss"):
        return 2
    return 3


# ---------------------------------------------------------------------------
# Sổ
# ---------------------------------------------------------------------------
def _duong_so():
    return os.path.join(luu_tru.goc(), FILE_SO)


def _doc_so():
    try:
        with open(_duong_so(), encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("man", {})
            d.setdefault("lan_chay", [])
            return d
    except (OSError, ValueError):
        pass
    return {"phien_ban": 1, "man": {}, "lan_chay": []}


def _ghi_so(d):
    luu_tru.ghi_json_nguyen_tu(_duong_so(), d)


def _bay_gio():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def ghi_lan(ban_ghi):
    """Một lượt chạy QC vào lịch sử (mới nhất đầu). `ban_ghi` do `qc_chay` dựng."""
    with _khoa:
        d = _doc_so()
        d["lan_chay"].insert(0, {"t": _bay_gio(), **ban_ghi})
        del d["lan_chay"][GIU_LICH_SU:]
        _ghi_so(d)


def ghi_day_du(man_id, van_tay, ten, ket, duong):
    """▶ đầy đủ của một cỗ máy trên một màn — vé để được nộp cỗ máy đó."""
    with _khoa:
        d = _doc_so()
        mm = d["man"].setdefault(man_id, {"day_du": {}, "nop": []})
        mm["day_du"][van_tay] = {"t": _bay_gio(), "ten": ten, **ket, "duong": duong}
        # Giữ 50 cỗ máy gần nhất — đủ để quay lại nộp, không phình sổ.
        if len(mm["day_du"]) > 50:
            for k in sorted(mm["day_du"], key=lambda k: mm["day_du"][k]["t"])[:-50]:
                del mm["day_du"][k]
        _ghi_so(d)


def ve_nop(man_id, van_tay):
    """Phần chấm ▶ đầy đủ của đúng cỗ máy này trên màn này — hoặc None (chưa được nộp)."""
    with _khoa:
        return copy.deepcopy(_doc_so()["man"].get(man_id, {}).get("day_du", {}).get(van_tay))


def ghi_nop(man_id, ban_ghi):
    """Một lần nộp. Trả số thứ tự lần nộp (1, 2, …) — game đếm số lần nộp (D-06)."""
    with _khoa:
        d = _doc_so()
        mm = d["man"].setdefault(man_id, {"day_du": {}, "nop": []})
        mm["nop"].append({"t": _bay_gio(), **ban_ghi})
        _ghi_so(d)
        return len(mm["nop"])


def tien_do_man(man_id):
    """Tóm tắt một màn cho giao diện: số lần nộp, sao cao nhất, lần nộp tốt nhất."""
    with _khoa:
        mm = _doc_so()["man"].get(man_id) or {}
    nop = mm.get("nop") or []
    tot = max(nop, key=lambda x: (x.get("sao", 0), -x.get("do_gon", {}).get("tong", 1e9)),
              default=None)
    return {"so_lan_nop": len(nop), "sao": tot.get("sao", 0) if tot else 0,
            "tot_nhat": tot, "lan_cuoi": nop[-1] if nop else None}


def danh_sach_man(van_tay_may=None):
    """Màn cho giao diện. Có `van_tay_may` (cỗ máy đang mở) thì kèm `ve_nop` — phần chấm
    ▶ đầy đủ của ĐÚNG cỗ máy đó, hoặc None: giao diện bật/tắt nút Nộp theo nó.

    """
    return [{**man_cong_khai(m), "tien_do": tien_do_man(m["id"]),
             "ve_nop": ve_nop(m["id"], van_tay_may) if van_tay_may else None}
            for m in MAN]


def lich_su(n=GIU_LICH_SU):
    with _khoa:
        return copy.deepcopy(_doc_so()["lan_chay"][:n])
