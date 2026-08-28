"""NGUỒN TICK — định dạng, đường dẫn, dò mất gói, sổ lỗ hổng.

KHÔNG chạm mạng. Dữ liệu dựng tay, nên bài này chạy được ở bất cứ đâu và không phụ
thuộc sàn còn sống hay không — cùng luật với mọi bài kiểm khác trong repo.

Thứ đáng canh nhất ở đây là **mất gói và lỗ hổng**. Một bộ ghi mất 40 giây mà không để
lại dấu thì bộ chạy sau này phát qua chỗ đó như thể thị trường liền mạch, và mọi con số
sau đó sai mà không có dấu vết. Nên hai cơ chế ấy phải có bài kiểm riêng, không được
tin vào việc "chắc nó chạy đúng".

Chạy:  python tests\\test_nguon_tick.py
"""
import io
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import luu_tru  # noqa: E402
from cat_studio import nguon_tick as nt  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


# Đổi thư mục dữ liệu sang chỗ tạm — bài kiểm KHÔNG được đụng vào dữ liệu thật.
TAM = tempfile.mkdtemp(prefix="cat-tick-")
luu_tru._GOC_MA_NGUON = TAM
NGAY = "2026-08-28"
MA = "THUUSDT"


def so(n, t0=1_787_000_000_000, u0=1000, tre=200):
    """`n` bản ghi sổ lệnh, mỗi cái cách nhau 10 ms."""
    a = np.zeros(n, dtype=nt.DT_SO)
    a["T"] = t0 + np.arange(n) * 10
    a["E"] = a["T"] + 1
    a["t_ta"] = a["T"] + tre
    a["u"] = u0 + np.arange(n)
    a["bid"], a["bid_kl"] = 2.70, 100.0
    a["ask"], a["ask_kl"] = 2.71, 120.0
    return a


def khop(n, t0=1_787_000_000_000, id0=500):
    a = np.zeros(n, dtype=nt.DT_KHOP)
    a["T"] = t0 + np.arange(n) * 30
    a["E"] = a["T"]
    a["t_ta"] = a["T"] + 210
    a["id"] = id0 + np.arange(n)
    a["gia"], a["kl"] = 2.705, 12.0
    a["mua_chu_dong"] = np.arange(n) % 2 == 0
    return a


# ================= 1. ĐỊNH DẠNG =================
print("\n▸ Định dạng")
kiem("một bản ghi sổ lệnh đúng 64 byte", nt.DT_SO.itemsize == 64,
     f"— {nt.DT_SO.itemsize}")
# 56 chứ không phải 49: xếp tự nhiên ra số LẺ, mỗi bản ghi lệch hàng một kiểu. Xem
# chú thích ở `DT_KHOP`.
kiem("một cú khớp đúng 56 byte, thẳng hàng 8",
     nt.DT_KHOP.itemsize == 56 and nt.DT_KHOP.itemsize % 8 == 0,
     f"— {nt.DT_KHOP.itemsize}")
kiem("cả hai dtype đều thẳng hàng 8 byte",
     nt.DT_SO.itemsize % 8 == 0 and nt.DT_KHOP.itemsize % 8 == 0)
kiem("BA mốc thời gian, không phải một",
     all(c in nt.DT_SO.names for c in ("T", "E", "t_ta")))
kiem("`mua_chu_dong` là ĐÚNG/SAI — hướng của bên CHỦ ĐỘNG, không phải của maker",
     nt.DT_KHOP["mua_chu_dong"] == np.dtype("?"))
def _luong_la():
    """Tên luồng lạ phải NÉM, không được âm thầm tạo một file rác `<ngày>.abc.bin` mà
    sau này không ai đọc nổi."""
    try:
        nt.duong(MA, NGAY, "khong_co")
        return False
    except ValueError:
        return True


kiem("luồng lạ → ném ValueError, không tạo file rác", _luong_la())

# ================= 2. GHI RỒI ĐỌC LẠI =================
print("\n▸ Ghi rồi đọc lại")
a = so(500)
with open(nt.duong(MA, NGAY, "so"), "wb") as f:
    a.tofile(f)
b = nt.doc_ngay(MA, NGAY, "so")
kiem("đọc lại đúng số bản ghi", len(b) == 500, f"— {len(b)}")
kiem("không mất một chữ số nào", np.array_equal(a["T"], b["T"]) and
     np.array_equal(a["bid_kl"], b["bid_kl"]))

# NỐI THÊM — bộ ghi xả nhiều lần trong một ngày, file phải cộng dồn chứ không đè.
with open(nt.duong(MA, NGAY, "so"), "ab") as f:
    so(300, t0=1_787_000_005_000, u0=1500).tofile(f)
kiem("xả lần hai NỐI THÊM, không đè lên lần một",
     len(nt.doc_ngay(MA, NGAY, "so")) == 800)

kiem("chưa có file → mảng RỖNG đúng dtype, không phải None",
     len(nt.doc_ngay(MA, "2020-01-01", "khop")) == 0
     and nt.doc_ngay(MA, "2020-01-01", "khop").dtype == nt.DT_KHOP)

# ================= 3. MẤT GÓI =================
print("\n▸ Mất gói — suy từ SỐ THỨ TỰ, không từ thời gian")
k = khop(100)
kiem("chuỗi liền mạch → không báo mất gói nào", nt.do_mat_goi(k, "id") == [])

k2 = np.concatenate([khop(50), khop(50, t0=1_787_000_010_000, id0=560)])
mat = nt.do_mat_goi(k2, "id")
# id nhảy 549 → 560, tức MẤT 550..559 = 10 cú khớp. (Bản đầu của bài này ghi 9 —
# lệch một, và cái sai đó nằm ở BÀI KIỂM chứ không ở mã. Ghi lại vì đếm hàng đợi mà
# lệch một thì không ai thấy.)
kiem("nhảy từ 549 sang 560 → báo đúng MỘT chỗ, mất đúng 10 cú khớp",
     len(mat) == 1 and mat[0][1] == 10, f"— {mat}")

# Đây là ca mà THỜI GIAN không phân biệt được: hai bản ghi cách nhau xa, nhưng id
# liền nhau → thị trường lặng, KHÔNG mất gì.
lang = np.concatenate([khop(5), khop(5, t0=1_787_000_600_000, id0=505)])
kiem("cách nhau 10 phút nhưng id liền → thị trường LẶNG, không phải mất gói",
     nt.do_mat_goi(lang, "id") == [])

# `u` của bookTicker nhảy quãng là BÌNH THƯỜNG (nó là updateId chung của cả sổ lệnh).
nhay = np.concatenate([so(5), so(5, t0=1_787_000_001_000, u0=9000)])
kiem("`u` nhảy tiến → KHÔNG báo, vì updateId vốn không tăng đều",
     nt.do_mat_goi(nhay, "u") == [])
lui = np.concatenate([so(5, u0=9000), so(5, t0=1_787_000_001_000, u0=1000)])
kiem("`u` GIẢM → báo, vì đó là sai thứ tự / nối lại nhầm",
     len(nt.do_mat_goi(lui, "u")) == 1)

# ================= 4. SỔ LỖ HỔNG =================
print("\n▸ Sổ lỗ hổng")
kiem("chưa ghi gì → sổ rỗng", nt.doc_lo_hong(MA, NGAY) == [])
nt.ghi_lo_hong(MA, NGAY, 1_787_000_000_000, 1_787_000_040_000, "mất kết nối")
nt.ghi_lo_hong(MA, NGAY, 1_787_000_100_000, 1_787_000_102_500, "im lặng quá 45s")
lh = nt.doc_lo_hong(MA, NGAY)
kiem("hai lần đứt → hai dòng, NỐI THÊM chứ không đè", len(lh) == 2, f"— {len(lh)}")
kiem("mỗi dòng nói rõ dài bao lâu và vì sao",
     lh[0]["ms"] == 40_000 and lh[1]["vi_sao"].startswith("im lặng"))

with open(nt.duong_lo_hong(MA, NGAY), "a", encoding="utf-8") as f:
    f.write("{ dòng hỏng không phải json\n")
kiem("một dòng hỏng KHÔNG giết cả sổ — hai dòng tốt vẫn đọc được",
     len(nt.doc_lo_hong(MA, NGAY)) == 2)

# ================= 5. TÓM TẮT =================
print("\n▸ Tóm tắt một ngày")
with open(nt.duong(MA, NGAY, "khop"), "wb") as f:
    khop(200).tofile(f)
t = nt.tom_tat(MA, NGAY)
kiem("đếm đúng bản ghi cả hai luồng",
     t["so"]["so_ban_ghi"] == 800 and t["khop"]["so_ban_ghi"] == 200)
kiem("ĐỘ TRỄ là số ĐO ĐƯỢC, không phải ô người dùng gõ",
     t["so"]["tre_ms_trung_vi"] == 200.0 and t["khop"]["tre_ms_trung_vi"] == 210.0,
     f"— sổ {t['so']['tre_ms_trung_vi']} ms · khớp {t['khop']['tre_ms_trung_vi']} ms")
kiem("tóm tắt mang theo cả sổ lỗ hổng — không tách hai chỗ", len(t["lo_hong"]) == 2)

# ================= 6. GHÉP NHIỀU NGÀY =================
print("\n▸ Ghép nhiều ngày")
with open(nt.duong(MA, "2026-08-29", "khop"), "wb") as f:
    khop(150, t0=1_787_086_400_000, id0=700).tofile(f)
g = nt.doc(MA, NGAY, "2026-08-29", "khop")
kiem("ghép hai ngày liền", len(g) == 350, f"— {len(g)}")
kiem("thời gian TĂNG DẦN sau khi ghép", bool(np.all(np.diff(g["T"]) > 0)))
kiem("ngày ở giữa rỗng vẫn ghép được, không nổ",
     len(nt.doc(MA, NGAY, "2026-08-31", "khop")) == 350)
kiem("`_dai_ngay` gồm CẢ HAI đầu",
     nt._dai_ngay("2026-08-28", "2026-08-30")
     == ["2026-08-28", "2026-08-29", "2026-08-30"])

# ================= 7. NHỊP TIM + CỜ DỪNG =================
print("\n▸ Nhịp tim và cờ dừng — app NHÌN bộ ghi, không SỞ HỮU nó")
import time  # noqa: E402

kiem("chưa có nhịp nào → coi như bộ ghi đã chết",
     nt.trang_thai_ghi()["song"] is False)

nt.dap_nhip(["AUSDT", "BUSDT"], 1_787_000_000_000)
tt = nt.trang_thai_ghi()
kiem("vừa đập → còn sống, và nói rõ đang ghi gì",
     tt["song"] and tt["symbols"] == ["AUSDT", "BUSDT"] and tt["pid"] == os.getpid())

# NHỊP CŨ = ĐÃ CHẾT. Đây là phép quan trọng nhất của cả mục: nếu `song` suy từ việc
# pid có tồn tại hay không thì hệ điều hành cấp lại pid cho tiến trình khác là app
# báo "còn sống" trên một tiến trình chẳng ghi gì cả.
import json as _json  # noqa: E402
with open(nt._duong_nhip(), encoding="utf-8") as f:
    d = _json.load(f)
d["nhip"] = time.time() - nt.NHIP_QUA_HAN - 1
luu_tru.ghi_json_nguyen_tu(nt._duong_nhip(), d)
kiem("nhịp quá hạn → CHẾT, dù pid vẫn tồn tại thật",
     nt.trang_thai_ghi()["song"] is False)

kiem("chưa xin dừng → cờ không có", not nt.da_xin_dung())
nt.xin_dung()
kiem("xin dừng → bộ ghi thấy cờ", nt.da_xin_dung())
nt.xoa_co_dung()
kiem("dọn cờ → hết. Cờ cũ sót lại sẽ giết lần chạy sau ngay khi vừa mở",
     not nt.da_xin_dung())

# ================= 8. LIỆT KÊ =================
print("\n▸ Liệt kê — rẻ có chủ ý, không đọc hết file nào")
ds = nt.liet_ke()
mine = [d for d in ds if d["symbol"] == MA]
kiem("thấy symbol đã ghi, kèm số ngày và dải", len(mine) == 1
     and mine[0]["so_ngay"] == 2 and mine[0]["tu_ngay"] == NGAY, f"— {mine}")
kiem("đếm bản ghi từ KÍCH THƯỚC FILE, không mở file",
     mine[0]["so_ban_ghi"]["so"] == 800 and mine[0]["so_ban_ghi"]["khop"] == 350,
     f"— {mine[0]['so_ban_ghi']}")
kiem("gom lỗ hổng của MỌI ngày trong dải", mine[0]["so_lo_hong"] == 2)
kiem("độ trễ đo trên MẪU, ra đúng con số đã dựng", mine[0]["tre_ms"] == 200.0,
     f"— {mine[0]['tre_ms']} ms")

n = nt.xoa(MA)
kiem("xoá trả về số byte đã xoá, và symbol biến mất khỏi bảng",
     n > 0 and not [d for d in nt.liet_ke() if d["symbol"] == MA])

shutil.rmtree(TAM, ignore_errors=True)
print(f"\n{'=' * 56}\n  {dung} đúng, {sai} sai\n{'=' * 56}")
sys.exit(1 if sai else 0)
