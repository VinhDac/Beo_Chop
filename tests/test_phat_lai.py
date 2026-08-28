"""PHÁT LẠI — thứ tự sự kiện, lỗ hổng, và tính TẤT ĐỊNH.

Bài này canh đúng một thứ, và nó là thứ dễ sai nhất trong cả hệ: **chiến lược không
được thấy tương lai**. Sai ở đây thì backtest đẹp lên một cách có hệ thống, live thì
không, và không có dòng lỗi nào cả.

Không chạm mạng, không chạm đĩa thật — mảng dựng tay.

Chạy:  python tests\\test_phat_lai.py
"""
import io
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import nguon_tick as nt  # noqa: E402
from cat_studio import phat_lai as pl  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def so(T, t_ta, bid=None, ask=None):
    a = np.zeros(len(T), dtype=nt.DT_SO)
    a["T"], a["t_ta"] = T, t_ta
    a["u"] = np.arange(len(T)) + 1
    a["bid"] = bid if bid is not None else 2.70
    a["ask"] = ask if ask is not None else 2.71
    a["bid_kl"], a["ask_kl"] = 100.0, 120.0
    return a


def khop(T, t_ta, gia=2.705, kl=5.0, mua=True):
    a = np.zeros(len(T), dtype=nt.DT_KHOP)
    a["T"], a["t_ta"] = T, t_ta
    a["id"] = np.arange(len(T)) + 1
    a["gia"], a["kl"], a["mua_chu_dong"] = gia, kl, mua
    return a


def chay(p):
    """Cả dòng sự kiện thành danh sách `(t, loại)` — để so bằng mắt."""
    ra = []
    while (L := p.buoc()) is not None:
        ra.append((p.t, L))
    return ra


# ================= 1. TRỤC THỜI GIAN LÀ `t_ta` =================
print("\n▸ Trục thời gian là `t_ta`, không phải `T`")

# Cú khớp xảy ra ở sàn TRƯỚC (T=1002 < 1005) nhưng tới tay ta SAU (1210 > 1195).
# Chiến lược phải thấy nó SAU. Xếp theo `T` là cho nó thấy tương lai.
p = pl.PhatLai(so([1000, 1005], [1190, 1195]), khop([1002], [1210]))
ds = chay(p)
kiem("gói tới muộn thì phát muộn, dù ở SÀN nó xảy ra trước",
     [l for _, l in ds] == [pl.SO, pl.SO, pl.KHOP], f"— {ds}")

# Và ngược lại: cùng bộ dữ liệu mà xếp theo `T` sẽ ra thứ tự KHÁC. Chứng minh rằng
# luật này thật sự đổi kết quả, không phải một câu chữ cho đẹp.
theo_T = sorted([(1000, pl.SO), (1005, pl.SO), (1002, pl.KHOP)])
kiem("xếp theo `T` cho thứ tự KHÁC — nên đây là lựa chọn có hậu quả",
     [l for _, l in theo_T] != [l for _, l in ds])

kiem("`tre_ms` là độ trễ của gói vừa phát", p.tre_ms == 1210 - 1002,
     f"— {p.tre_ms} ms")

# ================= 2. SỔ LỆNH CHƯA BIẾT =================
print("\n▸ Sổ lệnh CHƯA BIẾT thì phải nói ra")
p = pl.PhatLai(so([100], [200]), khop([90], [150]))
kiem("trước bản ghi `so` đầu tiên: chưa có sổ", not p.co_so)
kiem("chưa có sổ → `mid` là NaN, không phải 0",
     math.isnan(p.mid) and math.isnan(p.spread))
p.buoc()
kiem("cú khớp KHÔNG dựng được sổ lệnh — nó chỉ nói ai vừa ăn",
     p.loai == pl.KHOP and not p.co_so)
p.buoc()
kiem("bản ghi `so` mới dựng được sổ", p.loai == pl.SO and p.co_so)
kiem("`mid` và `spread` tính đúng",
     abs(p.mid - 2.705) < 1e-12 and abs(p.spread - 0.01) < 1e-12)

# NaN làm mọi phép so TRƯỢT — cổng đọc nhầm lúc mù sẽ không khớp bừa.
kiem("NaN làm mọi phép so trượt, không khớp bừa",
     not (float("nan") < 1) and not (float("nan") > 1))

# ================= 3. LỖ HỔNG LÀ SỰ KIỆN =================
print("\n▸ Lỗ hổng là SỰ KIỆN, không phải khoảng trống")
p = pl.PhatLai(so([100, 400], [110, 410]), khop([]  , []),
               [{"tu": 200, "den": 300, "ms": 100, "vi_sao": "mất kết nối"}])
ds = chay(p)
kiem("một lỗ hổng đẻ ra HAI sự kiện: mở và đóng",
     [l for _, l in ds] == [pl.SO, pl.MO_LO_HONG, pl.DONG_LO_HONG, pl.SO], f"— {ds}")
kiem("mở/đóng nằm đúng mốc thời gian đã ghi",
     ds[1][0] == 200 and ds[2][0] == 300)

# Đi lại và dừng ngay sau khi đóng lỗ hổng — chỗ quan trọng nhất.
p = pl.PhatLai(so([100, 400], [110, 410]), khop([], []),
               [{"tu": 200, "den": 300, "ms": 100, "vi_sao": "x"}])
p.buoc(); p.buoc(); p.buoc()
kiem("ra khỏi vùng mù → sổ lệnh trở lại CHƯA BIẾT",
     p.loai == pl.DONG_LO_HONG and not p.co_so and math.isnan(p.mid))
p.buoc()
kiem("bản ghi `so` kế tiếp mới dựng lại sổ", p.co_so and abs(p.mid - 2.705) < 1e-12)

# ================= 4. TẤT ĐỊNH =================
print("\n▸ Tất định — cùng dữ liệu, cùng thứ tự, mọi lần")
S = so([10, 10, 10, 10], [50, 50, 50, 50])
K = khop([10, 10], [50, 50])
LH = [{"tu": 50, "den": 60, "ms": 10, "vi_sao": "x"}]
mot = chay(pl.PhatLai(S, K, LH))
hai = chay(pl.PhatLai(S, K, LH))
kiem("hoà `t_ta` VÀ hoà `T` → vẫn ra đúng một thứ tự, chạy lại y hệt", mot == hai)
kiem("hoà hết thì SỔ LỆNH đi trước KHỚP LỆNH — thấy giá mới rồi mới thấy ai ăn",
     [l for _, l in mot[:4]] == [pl.SO] * 4 and mot[4][1] == pl.KHOP, f"— {mot}")

# ================= 5. CA BIÊN =================
print("\n▸ Ca biên")
p = pl.PhatLai(so([], []), khop([], []))
kiem("rỗng hoàn toàn → `buoc()` trả None ngay, không nổ", p.buoc() is None)
kiem("rỗng thì `tom_tat` vẫn trả đủ hình dạng",
     p.tom_tat()["so_su_kien"] == 0 and p.tom_tat()["tu"] is None)

p = pl.PhatLai(so([], []), khop([], []),
               [{"tu": 5, "den": 9, "ms": 4, "vi_sao": "x"}])
kiem("CHỈ có lỗ hổng, không có dữ liệu → vẫn bắn ra hai sự kiện",
     [l for _, l in chay(p)] == [pl.MO_LO_HONG, pl.DONG_LO_HONG])

p = pl.PhatLai(so([1, 2], [3, 4]), khop([1], [3]))
n = p.con_lai()
p.buoc()
kiem("`con_lai` đếm lùi đúng", n == 3 and p.con_lai() == 2)

t = pl.PhatLai(so([1, 2], [3, 4]), khop([1], [3]),
               [{"tu": 5, "den": 9, "ms": 4, "vi_sao": "x"}]).tom_tat()
kiem("`tom_tat` đếm đủ ba nguồn và tổng thời gian mù",
     t["so_su_kien"] == 5 and t["so"] == 2 and t["khop"] == 1
     and t["lo_hong"] == 1 and t["ms_lo_hong"] == 4, f"— {t}")

# ================= 6. TỐC ĐỘ =================
print("\n▸ Tốc độ — một ngày thật là ~10 triệu sự kiện")
import time  # noqa: E402

N = 400_000
S = so(np.arange(N) * 10, np.arange(N) * 10 + 207)
K = khop(np.arange(N // 4) * 40, np.arange(N // 4) * 40 + 205)
t0 = time.perf_counter()
p = pl.PhatLai(S, K)
t_tron = time.perf_counter() - t0
t0 = time.perf_counter()
dem = 0
while p.buoc() is not None:
    dem += 1
t_di = time.perf_counter() - t0
tong = N + N // 4
print(f"    trộn {tong:,} sự kiện: {t_tron * 1000:.0f} ms"
      f"  ·  đi hết: {t_di * 1000:.0f} ms  ({dem / t_di / 1e6:.2f} triệu/s)")
print(f"    → một ngày 10 triệu sự kiện ≈ {10e6 / (dem / t_di):.1f} s")
kiem("đi được ít nhất 1 triệu sự kiện/giây", dem / t_di > 1e6,
     f"— {dem / t_di / 1e6:.2f} triệu/s")

print(f"\n{'=' * 56}\n  {dung} đúng, {sai} sai\n{'=' * 56}")
sys.exit(1 if sai else 0)
