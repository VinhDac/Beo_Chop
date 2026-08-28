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


def sau(n, t0=1_787_000_000_000, u0=9000, tre=230):
    """`n` ảnh chụp độ sâu, mỗi cái cách nhau 100 ms. Bid giảm dần, ask tăng dần —
    dựng đúng hình dạng sàn gửi, để bài kiểm không nghiệm được một cuốn sổ vô lý."""
    a = np.zeros(n, dtype=nt.DT_SAU)
    a["T"] = t0 + np.arange(n) * 100
    a["E"] = a["T"] + 1
    a["t_ta"] = a["T"] + tre
    a["u"] = u0 + np.arange(n) * 600      # gộp 100 ms nên nhảy quãng lớn là THƯỜNG
    muc = np.arange(nt.SO_MUC)
    a["bid"] = 2.700 - muc * 0.001
    a["ask"] = 2.701 + muc * 0.001
    a["bid_kl"] = 100.0 + muc
    a["ask_kl"] = 200.0 + muc
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
# 672 = 32 byte đầu + 4 mảng 20 số thực. Ghi con số ra đây để đổi `SO_MUC` mà quên
# hậu quả dung lượng thì bài kiểm nói ngay, chứ không phải sáu tháng sau nhìn ổ đĩa.
kiem("một ảnh độ sâu đúng 672 byte (20 mức mỗi bên)",
     nt.DT_SAU.itemsize == 672 and nt.SO_MUC == 20, f"— {nt.DT_SAU.itemsize}")
kiem("cả BA dtype đều thẳng hàng 8 byte",
     all(d.itemsize % 8 == 0 for d in nt.LUONG.values()),
     f"— {[d.itemsize for d in nt.LUONG.values()]}")
kiem("độ sâu cũng mang đủ BA mốc thời gian",
     all(c in nt.DT_SAU.names for c in ("T", "E", "t_ta")))
# Đây là chỗ luồng mới CÓ THỂ lặng lẽ hỏng: `tom_tat` chọn cột số thứ tự bằng
# `"id" if ten == "khop" else "u"`, nên luồng nào không có `u` là ném lúc chạy thật.
kiem("mọi luồng đều có cột số thứ tự mà `tom_tat` sẽ hỏi tới",
     all(("id" if t == "khop" else "u") in d.names for t, d in nt.LUONG.items()))
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

# ĐỘ SÂU — dtype có MẢNG CON, chỗ duy nhất trong repo. `np.array(danh_sách_tuple)`
# với trường mảng con là thứ dễ tin là chạy mà không kiểm; nếu nó xếp sai thì file vẫn
# đúng kích thước, vẫn đọc lại được, chỉ là giá và khối lượng lẫn vào nhau.
d = sau(120)
with open(nt.duong(MA, NGAY, "sau"), "wb") as f:
    d.tofile(f)
e = nt.doc_ngay(MA, NGAY, "sau")
kiem("đọc lại đủ 120 ảnh độ sâu", len(e) == 120, f"— {len(e)}")
kiem("mỗi ảnh giữ nguyên 20 mức, không lẫn giá sang khối lượng",
     e["bid"].shape == (120, 20) and np.array_equal(e["bid"], d["bid"])
     and np.array_equal(e["ask_kl"], d["ask_kl"]))
kiem("bid xếp giảm dần, ask xếp tăng dần — đúng hình dạng sàn gửi",
     bool((np.diff(e["bid"], axis=1) < 0).all())
     and bool((np.diff(e["ask"], axis=1) > 0).all()))

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
     mine[0]["so_ban_ghi"]["so"] == 800 and mine[0]["so_ban_ghi"]["khop"] == 350
     and mine[0]["so_ban_ghi"]["sau"] == 120,
     f"— {mine[0]['so_ban_ghi']}")
# Hộp thoại Nguồn vẽ thẳng từ đây, nên thiếu một khoá là thiếu một CỘT.
kiem("bảng đếm có đủ MỌI luồng, không sót luồng mới",
     set(mine[0]["so_ban_ghi"]) == set(nt.LUONG))
kiem("gom lỗ hổng của MỌI ngày trong dải", mine[0]["so_lo_hong"] == 2)
kiem("độ trễ đo trên MẪU, ra đúng con số đã dựng", mine[0]["tre_ms"] == 200.0,
     f"— {mine[0]['tre_ms']} ms")

n = nt.xoa(MA)
kiem("xoá trả về số byte đã xoá, và symbol biến mất khỏi bảng",
     n > 0 and not [d for d in nt.liet_ke() if d["symbol"] == MA])

# ================= 9. BỘ GHI — phần thuần, không chạm mạng =================
#
# Bộ ghi là tiến trình chạy 24/7, và trước đợt này nó KHÔNG có bài kiểm nào. Không
# kiểm được vòng WebSocket ở đây (chạm mạng thì bài kiểm hết chạy được offline),
# nhưng ba thứ dưới đây thuần tuý và là đúng ba chỗ một luồng mới có thể hỏng.
print("\n▸ Bộ ghi — phần thuần")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
try:
    import ghi_tick as gt
except SystemExit:                       # thiếu `websockets` — không phải lỗi của repo
    gt = None
    kiem("bỏ qua: chưa cài `websockets`", True)

# Chính lời import này từng giết bài kiểm: `ghi_tick` bọc lại `sys.stdout` cho UTF-8,
# cái bọc cũ bị thu gom và đóng luôn luồng ra bên dưới. Đã sửa ở nguồn — nó chỉ bọc
# khi CHƯA phải UTF-8. Dòng dưới canh đúng chuyện đó, vì nó im lặng và ở xa.
kiem("import bộ ghi KHÔNG cướp mất stdout của người gọi", not sys.stdout.closed)

if gt is not None:
    kiem("đăng ký đủ BA kênh ở sàn", len(gt.KENH) == 3
         and "depth20@100ms" in gt.KENH, f"— {gt.KENH}")
    # Kênh `@depth20` là ẢNH CHỤP; `@depth` trần là BẢN SAI KHÁC và cần dựng lại cả
    # cuốn sổ. Hai tên chỉ khác nhau hai ký tự, nên ghim lại.
    kiem("KHÔNG lấy `@depth` trần — đó là bản sai khác, không phải ảnh chụp",
         "depth" not in gt.KENH and "depth@100ms" not in gt.KENH)
    # Dòng trạng thái in ra theo `nt.LUONG`; thiếu nhãn thì nó rơi về khoá nội bộ và
    # người đọc log thấy "so/khop/sau". Bắt ở đây, không đợi thấy trong log thật.
    kiem("mỗi luồng có nhãn tiếng Anh cho log", set(nt.LUONG) <= set(gt.NHAN_LUONG),
         f"— thiếu {set(nt.LUONG) - set(gt.NHAN_LUONG)}")

    g, k = gt._hai_muoi_muc([["2.70", "100"], ["2.69", "200"]])
    kiem("sổ mỏng → đệm 0, KHÔNG bỏ gói",
         len(g) == 20 and g[:2] == [2.70, 2.69] and g[2:] == [0.0] * 18
         and k[:2] == [100.0, 200.0])
    g, _ = gt._hai_muoi_muc([[str(i), "1"] for i in range(50)])
    kiem("sàn gửi thừa mức → cắt còn đúng 20, không tràn dtype", len(g) == 20)
    kiem("sổ rỗng → 20 số 0, vẫn ghi được một bản ghi",
         gt._hai_muoi_muc([]) == ([0.0] * 20, [0.0] * 20))

    def _dong_cut():
        """Một dòng cụt phải ném IndexError — và vòng bóc gói phải BẮT nó.

        IndexError KHÔNG phải con của KeyError. Bản đầu của vòng bóc gói chỉ bắt
        `(KeyError, ValueError, TypeError)`, nên đúng một dòng méo từ sàn là giết cả
        bộ ghi lúc 3 giờ sáng."""
        try:
            gt._hai_muoi_muc([["2.70"]])
        except IndexError:
            return True
        return False

    kiem("dòng cụt ném IndexError, và vòng bóc gói có bắt IndexError",
         _dong_cut() and "IndexError" in io.open(gt.__file__, encoding="utf-8").read())

    # VÒNG ĐỆM → ĐĨA, đúng hình dạng `chay()` tạo ra: tuple có hai phần tử là LIST.
    TAM2 = tempfile.mkdtemp(prefix="cat-ghi-")
    luu_tru._GOC_MA_NGUON = TAM2
    bg, bk = gt._hai_muoi_muc([["2.70", "10"], ["2.69", "20"]])
    ag, ak = gt._hai_muoi_muc([["2.71", "30"]])
    G = gt.Ghi("THVUSDT")
    kiem("đệm dựng từ `nt.LUONG` — luồng mới tự có chỗ, không phải sửa `Ghi`",
         set(G.dem) == set(nt.LUONG))
    # ⚠ MỐC THẬT, không phải số tròn cho đẹp. Phần trên của bài này đặt TÊN FILE bằng
    # tay, nên nó chưa bao giờ kiểm việc `xa()` TỰ SUY ngày từ dấu thời gian. Đây là
    # chỗ kiểm điều đó, nên hai con số dưới phải đúng là hai bên bờ nửa đêm UTC.
    NUA_DEM = 1787875200000                          # 2026-08-28 00:00:00.000Z
    CUOI_NGAY = 1787961599999                        # 2026-08-28 23:59:59.999Z
    G.them("sau", (NUA_DEM, NUA_DEM + 1, NUA_DEM + 230, 9000, bg, bk, ag, ak))
    # Gói tới ở mili-giây cuối cùng của ngày, mà TA nhận được sau nửa đêm. Phải rơi
    # theo `T` (giờ SÀN đổi sổ), không theo lúc ta nhận, và không theo đồng hồ máy.
    G.them("sau", (CUOI_NGAY, CUOI_NGAY, CUOI_NGAY + 101, 9600, bg, bk, ag, ak))
    G.xa()
    r1 = nt.doc_ngay("THVUSDT", "2026-08-28", "sau")
    r2 = nt.doc_ngay("THVUSDT", "2026-08-29", "sau")
    kiem("cả hai ảnh vào ĐÚNG file 2026-08-28 — cắt theo `T`, không theo lúc ta nhận",
         len(r1) == 2 and len(r2) == 0, f"— {len(r1)}/{len(r2)}")
    kiem("list lồng trong tuple xuống đĩa vẫn đúng chỗ",
         list(r1["bid"][0][:2]) == [2.70, 2.69] and r1["ask_kl"][0][0] == 30.0
         and r1["ask"][0][1] == 0.0)
    kiem("`tong` đếm đủ hai ảnh", G.tong["sau"] == 2, f"— {G.tong}")

    # Cùng bộ đệm, một gói sang ngày mới: LÚC ĐÓ mới phải tách file.
    G.them("sau", (NUA_DEM + 86_400_000, NUA_DEM + 86_400_000,
                   NUA_DEM + 86_400_230, 9700, bg, bk, ag, ak))
    G.xa()
    kiem("gói của ngày sau tách sang file riêng, không nối đuôi file hôm trước",
         len(nt.doc_ngay("THVUSDT", "2026-08-28", "sau")) == 2
         and len(nt.doc_ngay("THVUSDT", "2026-08-29", "sau")) == 1)
    # Trung vị của hai độ trễ đã dựng: 230 ms và 101 ms → 165,5. Ghi rõ ra đây vì
    # con số này là thứ hộp thoại Nguồn hiện lên, và nó phải tính TRÊN FILE — tức
    # trên các bản ghi đã chia theo `T`, chứ không trên cả bộ đệm.
    kiem("`tom_tat` đọc được luồng mới, ra trung vị độ trễ đúng của FILE đó",
         nt.tom_tat("THVUSDT", "2026-08-28")["sau"]["tre_ms_trung_vi"] == 165.5,
         f"— {nt.tom_tat('THVUSDT', '2026-08-28')['sau']['tre_ms_trung_vi']} ms")
    shutil.rmtree(TAM2, ignore_errors=True)
    luu_tru._GOC_MA_NGUON = TAM

shutil.rmtree(TAM, ignore_errors=True)
print(f"\n{'=' * 56}\n  {dung} đúng, {sai} sai\n{'=' * 56}")
sys.exit(1 if sai else 0)
