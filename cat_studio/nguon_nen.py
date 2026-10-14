"""Kho nến trên máy — đọc những bộ nến M1 ĐÃ CÓ trong `du_lieu/nen/`.

App KHÔNG tải nến nữa (DECISIONS.md D-09: app chỉ phục vụ QuantConnect, mà dữ liệu của
QC không được mang về máy). Module này chỉ còn ĐỌC và XOÁ những bộ nến đã nằm sẵn trên
máy, cho Strategy Tester chạy tại máy. Mọi module khác chỉ thấy một mảng numpy.

BA LUẬT CỦA KHO
---------------
1. **Chỉ có M1.** M5 / M15 / H1 gộp từ M1 (`tinh_toan.gop`). M1 cũng là nền mô phỏng:
   giá đi tới đâu, lệnh khớp lúc nào đều xét theo nến M1.

2. **Một symbol là ĐÚNG MỘT DẢI LIỀN** (một file `.npy` + một file meta `.json`). Dữ
   liệu vụn thành nhiều mảnh là mời gọi một lớp lỗi rất khó thấy: backtest chạy qua chỗ
   thủng mà không biết.

3. **`t` là giờ của nguồn đã dựng nến** (giờ server của sàn), không phải UTC. Đừng "sửa
   cho đúng UTC" — biên nến M5, phiên, cuối tuần đều phải theo đúng cái đồng hồ đã dựng
   nến, nếu không biên nến sẽ lệch và vùng nén đếm sai.

Không lưu spread từng nến: mô hình đã chốt là spread một con số trong Cài đặt (§12.3);
meta có sẵn `spread_tb` (trung vị lúc dựng bộ nến) để gợi ý con số đó.
"""
import json
import os
from datetime import datetime, timezone

import numpy as np

from . import luu_tru


#: Một nến M1. 48 byte — một năm XAUUSD (~374k nến) khoảng 18 MB.
#: `t` = epoch giây, giờ của nguồn. `vol` = tick volume.
DTYPE = np.dtype([("t", "<i8"), ("o", "<f8"), ("h", "<f8"),
                  ("l", "<f8"), ("c", "<f8"), ("vol", "<i8")])


# ---------------------------------------------------------------------------
# Thời điểm — nhận datetime / chuỗi ISO / epoch, trả về epoch giây
# ---------------------------------------------------------------------------
def thoi_diem(x):
    """Chuẩn hoá về epoch giây (int). Trả None nếu không hiểu được.

    Nhận nhiều kiểu vì nó nằm ngay ranh giới với giao diện: JS gửi chuỗi `"2025-01-01"`,
    Python nội bộ dùng `datetime`, còn mảng nến dùng epoch."""
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return int(x)
    if isinstance(x, datetime):
        d = x if x.tzinfo else x.replace(tzinfo=timezone.utc)
        return int(d.timestamp())
    if isinstance(x, str):
        s = x.strip().replace("/", "-")
        for dinh in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(s[:len(dinh) + 2].strip(), dinh)
                           .replace(tzinfo=timezone.utc).timestamp())
            except ValueError:
                continue
    return None


def _ngay(epoch):
    """Epoch -> chuỗi `YYYY-MM-DD HH:MM` để hiện cho người đọc."""
    if epoch is None:
        return "—"
    return datetime.fromtimestamp(int(epoch), timezone.utc).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Chỗ cất
# ---------------------------------------------------------------------------
def _ten_file(symbol):
    """Tên file an toàn. Symbol của sàn có thể mang hậu tố lạ (`XAUUSD.m`, `XAUUSD#`)."""
    return luu_tru._ten_an_toan(str(symbol).strip().upper()) or "SYMBOL"


def _duong(symbol):
    goc = luu_tru.thu_muc_nen()
    ten = _ten_file(symbol)
    return (os.path.join(goc, ten + ".npy"), os.path.join(goc, ten + ".json"))


def doc_meta(symbol):
    """Meta của một bộ nến trên máy. None nghĩa là chưa có gì."""
    _, mj = _duong(symbol)
    try:
        with open(mj, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def doc(symbol, tu=None, den=None):
    """Mảng nến M1 trên máy, cắt theo [tu, den]. Chưa có thì trả mảng RỖNG đúng dtype.

    Trả mảng rỗng chứ không None: chỗ gọi cứ `len()` và cắt lát như thường, không phải
    rải `if is None` khắp bộ chạy."""
    mn, _ = _duong(symbol)
    try:
        a = np.load(mn, allow_pickle=False)
    except Exception:
        return np.empty(0, dtype=DTYPE)
    if a.dtype != DTYPE:                                 # file của bản cũ / hỏng
        return np.empty(0, dtype=DTYPE)
    t0, t1 = thoi_diem(tu), thoi_diem(den)
    if t0 is not None:
        a = a[a["t"] >= t0]
    if t1 is not None:
        a = a[a["t"] <= t1]
    return a


def _mb(duong):
    try:
        return round(os.path.getsize(duong) / (1024 * 1024), 2)
    except OSError:
        return 0.0


def liet_ke():
    """Mọi bộ nến đang giữ — cho bảng nguồn dữ liệu trong Cài đặt.

    Mỗi dòng đủ để trả lời ba câu người dùng hỏi: có dữ liệu từ ngày nào tới ngày nào,
    bao nhiêu nến, và **chiếm bao nhiêu MB** (để quyết định có xoá không)."""
    goc = luu_tru.thu_muc_nen()
    ra = []
    try:
        ds = sorted(f for f in os.listdir(goc) if f.endswith(".npy"))
    except OSError:
        return ra
    for f in ds:
        sym = f[:-4]
        m = doc_meta(sym) or {}
        mn, mj = _duong(sym)
        ra.append({
            "symbol": m.get("symbol", sym),
            "tu": m.get("tu"), "den": m.get("den"),
            "tu_chu": _ngay(m.get("tu")), "den_chu": _ngay(m.get("den")),
            "so_nen": int(m.get("so_nen") or 0),
            "mb": round(_mb(mn) + _mb(mj), 2),
            "digits": m.get("digits"), "point": m.get("point"),
            "contract_size": m.get("contract_size"),
            "spread_tb": m.get("spread_tb"),
            "tai_luc": m.get("tai_luc"),
        })
    return ra


def xoa(symbol):
    """Xoá hẳn một bộ nến. Trả True nếu có xoá được cái gì."""
    da = False
    for p in _duong(symbol):
        try:
            os.remove(p)
            da = True
        except OSError:
            pass
    return da


# ---------------------------------------------------------------------------
# Còn thiếu những khoảng nào
# ---------------------------------------------------------------------------
def file_du(symbol, m):
    """File `.npy` có thật sự chứa đủ số nến mà meta khai không?

    Meta và mảng nến là HAI file. Một `.npy` cụt (antivirus, đồng bộ đám mây xén, ghi dở)
    vẫn để meta nguyên vẹn — mà `doc()` bắt mọi lỗi rồi lặng lẽ trả mảng RỖNG, còn
    `khoang_thieu()` nếu chỉ nhìn meta sẽ khẳng định "đủ rồi". File cụt phải bị coi như
    không có, để người dùng được báo thiếu nến thay vì chạy trên mảng rỗng.

    Chỉ một lệnh `stat`, không đọc file, nên gọi mỗi lần bấm ▶ cũng không tốn gì."""
    try:
        return os.path.getsize(_duong(symbol)[0]) >= int(m["so_nen"]) * DTYPE.itemsize
    except (OSError, KeyError, TypeError, ValueError):
        return False


def khoang_thieu(symbol, tu, den):
    """Những phần của [tu, den] mà kho trên máy KHÔNG phủ tới — `[(từ, đến), …]`.

    Một symbol là một dải liền, nên nhiều nhất là hai khoảng: phần trước dải và phần sau
    dải. Chưa có bộ nến nào (hoặc file cụt) thì thiếu trọn khoảng xin. Trả `[]` nghĩa là
    đủ — và cả khi mốc không đọc được: chỗ gọi phải tự chặn mốc rỗng trước."""
    t0, t1 = thoi_diem(tu), thoi_diem(den)
    if t0 is None or t1 is None or t1 <= t0:
        return []
    m = doc_meta(symbol)
    if not m or not m.get("so_nen") or not file_du(symbol, m):
        return [(t0, t1)]
    a, b = int(m["tu"]), int(m["den"])
    if t1 <= a or t0 >= b:                 # rời hẳn dải đang có
        return [(t0, t1)]
    ra = []
    if t0 < a:
        ra.append((t0, a))
    if t1 > b:
        ra.append((b, t1))
    return ra


# ---------------------------------------------------------------------------
# Soát chất lượng — thứ bộ chạy PHẢI biết trước khi tin vào dữ liệu
# ---------------------------------------------------------------------------
def lo_hong(symbol, tu=None, den=None, nguong_phut=2):
    """Những chỗ THỦNG trong chuỗi nến M1: (bắt đầu, kết thúc, số phút).

    Vì sao phải có: luật vùng nén đếm "nến LIÊN TIẾP", mà cuối tuần và giờ sàn nghỉ để
    lại những khoảng trống dài. Bộ chạy dùng danh sách này để cho vùng nén CHẾT khi vắt
    qua một lỗ (core.md §12.6b) thay vì đếm xuyên 48 giờ chợ đóng cửa như không có gì.

    `nguong_phut=2` nghĩa là hai nến cách nhau quá 2 phút thì tính là lỗ."""
    a = doc(symbol, tu, den)
    if len(a) < 2:
        return []
    d = np.diff(a["t"])
    idx = np.nonzero(d > nguong_phut * 60)[0]
    return [(int(a["t"][i]), int(a["t"][i + 1]), int(d[i] // 60)) for i in idx]


def tom_tat(symbol, tu=None, den=None):
    """Một dòng sự thật về dữ liệu đang có — cho bảng Cài đặt và cho nhật ký lần chạy."""
    a = doc(symbol, tu, den)
    lh = lo_hong(symbol, tu, den)
    m = doc_meta(symbol) or {}
    return {
        "symbol": m.get("symbol", symbol),
        "so_nen": int(len(a)),
        "tu_chu": _ngay(int(a["t"][0])) if len(a) else "—",
        "den_chu": _ngay(int(a["t"][-1])) if len(a) else "—",
        "so_lo_hong": len(lh),
        "lo_hong_dai_nhat": max((x[2] for x in lh), default=0),
        "digits": m.get("digits"), "point": m.get("point"),
        "contract_size": m.get("contract_size"), "spread_tb": m.get("spread_tb"),
    }
