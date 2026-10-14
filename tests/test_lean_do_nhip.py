"""Đo nhịp LEAN — phần THUẦN của `lean/do_nhip.py`.

File đó chạy trên cloud QuantConnect, máy này không có LEAN. Nên bài này nạp nó với một
`AlgorithmImports` GIẢ (lớp vỏ chỉ cần cái tên `QCAlgorithm` để được định nghĩa), rồi bơm
nến tay vào `NhipD02` — đúng phần quyết định cỡ tải và cỡ nhật ký của lần đo.

Năm thứ được canh:

  1. **MỘT lượt = MỘT bản ghi.** Đếm lượt và đếm dòng nhật ký phải bằng nhau — lệch là
     con số "nhật ký nặng bao nhiêu MB" đo trên cloud vô nghĩa.
  2. **Cổng tính ĐỦ điều kiện**, không ngắt ở cái sai đầu tiên (core.md §12.5b).
  3. **Không có nguồn thì nói "chưa có"**, không bịa số 0 (core.md §12.13).
  4. **Vòng đời lệnh ảo đi đúng sơ đồ mẫu**: đặt → khớp → dời SL hoà vốn → đóng; và
     nhánh huỷ khi nén tan. Trong một nhịp, Manage chạy TRƯỚC Entry.
  5. **Nhật ký là JSON sạch**: không NaN, đếm byte khớp byte thật, chạy lại ra y hệt.

Chạy:  python tests\\test_lean_do_nhip.py
"""
import importlib.util
import io
import json
import os
import sys
import types

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# AlgorithmImports GIẢ — mọi tên khác của QC chỉ được gọi lúc chạy trên cloud.
_gia = types.ModuleType("AlgorithmImports")
_gia.QCAlgorithm = type("QCAlgorithm", (), {})
sys.modules["AlgorithmImports"] = _gia

_spec = importlib.util.spec_from_file_location(
    "do_nhip", os.path.join(GOC, "lean", "do_nhip.py"))
dn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dn)

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def gan(a, b, e=1e-9):
    return a is not None and abs(float(a) - float(b)) <= e


ATR = 0.05      # ở giá 100 → 5 bps < 7: nến NÉN
ATR_TAN = 0.10  # 10 bps ≥ 7: nén TAN


def m5(n, atr=ATR):
    """Một nến M5 đóng (đỉnh 100,05 · đáy 99,95) + nến M1 khép nó, đứng yên ở 100."""
    n.nhan_m5(100.0, 100.05, 99.95, 100.0, atr)
    n.mot_nhip(100.0, 100.0, 100.0, 100.0)


def cuoi(n):
    return json.loads(n.nhat_ky[-1])


def tu(n, k):
    return [json.loads(d) for d in n.nhat_ky[k:]]


def kich_ban_mua():
    """Vùng nén 10 nến → đặt mua → khớp → lãi 1R dời SL → quay về, đóng hoà vốn."""
    n = dn.NhipD02()
    for _ in range(10):
        m5(n)
    n.nhan_m15(100.2, 100.0)
    m5(n)
    m5(n)
    n.mot_nhip(100.0, 100.06, 100.0, 100.06)     # chạm 100,055 → khớp
    n.mot_nhip(100.06, 100.14, 100.06, 100.14)   # lãi 1,13R → dời SL
    n.mot_nhip(100.14, 100.15, 100.10, 100.12)   # SL đã hoà vốn → để yên
    n.mot_nhip(100.12, 100.12, 100.05, 100.06)   # quay về giá vào → đóng
    return n


# ================= 3. không có nguồn =================
print("\n▸ Không có nguồn thì nói 'chưa có'")
n = dn.NhipD02()
n.nhan_m5(100.0, 100.1, 99.9, 100.0, None)
n.mot_nhip(100.0, 100.0, 100.0, 100.0)
r = cuoi(n)
kiem("ATR chưa đủ chu kỳ → hết lượt tại [2], ghi LÝ DO chứ không ghi số",
     r[1] == "E" and r[3] == "1>2" and r[4] == "het" and r[6] == "chua_co_du_lieu")

n = dn.NhipD02()
m5(n, atr=ATR_TAN)
r = cuoi(n)
kiem("chưa có vùng → ba vế vùng là null, không phải 0, và cổng trượt",
     r[5][1][0] is None and r[5][2][0] is None and r[5][3][0] is None and r[4] == "het")

# ================= 2. tính đủ điều kiện =================
print("\n▸ Cổng tính ĐỦ điều kiện")
n = dn.NhipD02()
for _ in range(9):
    m5(n)
r = cuoi(n)
kiem("9 nến nén → trượt ở [2] đúng vì vế 'đủ 10 nến'", r[3] == "1>2" and r[5][1] == [9, 10, False])
kiem("vẫn ghi đủ 4 vế dù vế thứ hai đã sai", len(r[5]) == 4
     and r[5][0][2] is True and r[5][2][2] is True and r[5][3][2] is True)
kiem("bề rộng ghi bằng bội ATR: 0,1 ÷ 0,05 = 2", gan(r[5][2][0], 2.0))
m5(n)
r = cuoi(n)
kiem("đủ vùng mà chưa có MA M15 → hết lượt ở [3B], ghi 'chưa có dữ liệu'",
     r[3] == "1>2>3>3A>3B" and r[6] == "chua_co_du_lieu")

# ================= 4. vòng đời lệnh ảo =================
print("\n▸ Vòng đời lệnh ảo — nhánh MUA")
n = dn.NhipD02()
for _ in range(10):
    m5(n)
n.nhan_m15(100.2, 100.0)
m5(n)
r = cuoi(n)
kiem("xu hướng lên → đi tới [3A.1] đặt mua",
     r[3] == "1>2>3>3A>3A.1" and r[4] == "xong" and r[6].startswith("dat_mua A-0001"))
x = n.lenh[0]
kiem("giá vào = đỉnh vùng + 0,1 × ATR hiện tại", gan(x["vao"], 100.055))
kiem("1R = 1,5 × ATR TRUNG BÌNH cả vùng", gan(x["R"], 0.075))
kiem("SL = vào − 1R · TP = vào + 2R", gan(x["sl"], 99.98) and gan(x["tp"], 100.205))

k = len(n.nhat_ky)
m5(n)
moi = tu(n, k)
kiem("trong một nhịp: Manage TRƯỚC Entry", [d[1] for d in moi] == ["M", "E"])
kiem("lệnh chờ, nén còn → Manage hết lượt ở [1B], ghi đúng id lệnh",
     moi[0][3] == "1>1A>1B" and moi[0][4] == "het" and moi[0][2] == "A-0001")
kiem("vùng đã sinh lệnh → Entry trượt ở [2], đúng vế thứ tư",
     moi[1][3] == "1>2" and moi[1][5][3] == [True, False, False])

n.mot_nhip(100.0, 100.06, 100.0, 100.06)
kiem("giá chạm mức vào → khớp", n.lenh[0]["khop"] is True)
n.mot_nhip(100.06, 100.14, 100.06, 100.14)
r = cuoi(n)
kiem("lãi ≥ 1R → [1B.1] dời SL về giá vào",
     r[3] == "1>1A>1B>1B.1" and r[6] == "sl_hoa_von" and gan(n.lenh[0]["sl"], 100.055))
n.mot_nhip(100.14, 100.15, 100.10, 100.12)
r = cuoi(n)
kiem("SL đã hoà vốn → không dời lần nữa", r[3] == "1>1A>1B" and r[5][2] == [True, False, False])
n.mot_nhip(100.12, 100.12, 100.05, 100.06)
kiem("quay về giá vào → đóng ở hoà vốn, 0R",
     n.lenh == [] and n.so_dong == 1 and gan(n.tong_R, 0.0))

print("\n▸ Vòng đời lệnh ảo — nhánh BÁN và huỷ khi nén tan")
n = dn.NhipD02()
n.nhan_m15(99.8, 100.0)
for _ in range(10):
    m5(n)
r = cuoi(n)
kiem("xu hướng xuống → đi tới [3B.1] đặt bán",
     r[3] == "1>2>3>3A>3B>3B.1" and r[6].startswith("dat_ban A-0001"))
kiem("giá vào = đáy vùng − 0,1 × ATR hiện tại", gan(n.lenh[0]["vao"], 99.945))
k = len(n.nhat_ky)
m5(n, atr=ATR_TAN)
moi = tu(n, k)
kiem("nén tan khi lệnh chưa khớp → [1A.1] huỷ lệnh chờ",
     moi[0][3] == "1>1A>1A.1" and moi[0][6] == "huy_cho" and n.lenh == [])
kiem("cùng nhịp đó Entry thấy nén đã tan → trượt ở [2]",
     moi[1][3] == "1>2" and moi[1][5][0][2] is False)

# ================= 1 + 5. nhật ký =================
print("\n▸ Nhật ký")
n = kich_ban_mua()
kiem("MỘT lượt = MỘT dòng", len(n.nhat_ky) == n.dem["entry"] + n.dem["manage"],
     f"({n.dem['entry']} Entry + {n.dem['manage']} Manage = {len(n.nhat_ky)} dòng)")
chu = n.nhat_ky_jsonl()
kiem("kích thước đếm khớp byte thật", n.so_byte == len(chu.encode("utf-8")))
kiem("mỗi dòng là JSON 7 cột, không có NaN",
     all(len(json.loads(d)) == 7 for d in chu.splitlines()) and "NaN" not in chu)
kiem("chạy lại cùng kịch bản → nhật ký giống hệt từng byte",
     kich_ban_mua().nhat_ky_jsonl() == chu)

# ================= dòng tổng kết =================
print("\n▸ Dòng tổng kết")
kiem("số kiểu Việt: 354.503 · 12,3 · −8,4",
     dn._so(354503) == "354.503" and dn._so(12.34, 1) == "12,3" and dn._so(-8.44, 1) == "−8,4")
s = n.dong_tong_ket(12.34, "được")
kiem("đủ các mục người dùng phải báo lại",
     s.startswith("ĐO NHỊP · XAUUSD 2025") and "chạy 12,3 giây" in s
     and "lưu Object Store: được" in s and "lệnh ảo 1 (đóng 1" in s)
kiem("không có nến nào → nói thẳng KHÔNG CÓ DỮ LIỆU, không in một bảng số 0",
     "KHÔNG CÓ DỮ LIỆU" in dn.NhipD02().dong_tong_ket(1.0, "được"))

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
