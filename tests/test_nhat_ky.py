"""NHẬT KÝ — bản ghi rỗng chữ, nhãn dựng lại, ghi/đọc ngược không mất gì.

Người dùng nói đây là phần quan trọng nhất, vì debug và nâng cấp model là ở hết đây.
Nên bài này canh đúng những chỗ hỏng mà vẫn "trông có vẻ chạy":

  1. **Bản ghi không chứa chữ.** Chữ dựng lúc hiển thị, cho lô đang nhìn.
  2. **Nhãn `[3A.1]` KHÔNG được lưu** — kéo một khối đi chỗ khác là nhãn đổi, mà nhật ký
     cũ vẫn phải trỏ đúng khối.
  3. **Ghi rồi đọc ngược không mất gì** — kể cả khi một khoá của lệnh trùng tên nhãn dòng.
  4. **Vân tay** đổi khi LOGIC đổi, không đổi khi chỉ kéo khối.
  5. Phân biệt "chưa có số" với "so xong thấy không đạt".
  6. **Soi một lượt trên sơ đồ**: mỗi cổng mang đúng một vết cho mỗi điều kiện.
  7. Chiến lược TRẮNG (chỉ có khối Bắt đầu) không làm vỡ lô nhật ký.

Chạy:  python tests\\test_nhat_ky.py
"""
import io
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bo_chay as bc  # noqa: E402
from cat_studio import core  # noqa: E402
from cat_studio import nhat_ky as nk  # noqa: E402
from cat_studio import tinh_toan as tt  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


# --------------------------------------------------------------------------
# Một lần chạy nhỏ trên dữ liệu giả — đủ để có cả lượt CÓ VIỆC lẫn lượt HẾT LƯỢT.
def nen_m1(gia):
    g = np.asarray(gia, dtype=float)
    a = np.empty(len(g), dtype=tt.DTYPE)
    a["t"] = np.arange(0, len(g) * 60, 60, dtype=np.int64)[:len(g)]
    for k in ("o", "h", "l", "c"):
        a[k] = g
    a["vol"] = 1
    return a


bd = core.make_start_step("bắt đầu", "M5")
bd["pos"] = [0.0, 0.0]
g = core.make_action_step({
    "type": core.CHECK_COND, "name": "giá > 100",
    "conditions": [{"trai": {"ten": "close"}, "phep": ">",
                    "phai": {"value": 100.0}}]})
g["pos"] = [0.0, 0.0]
v = core.make_action_step({
    "type": core.VAO_LENH, "name": "mua", "huong": "mua", "loai": "market",
    "lot": 0.01, "sl": {"tinh": "gia", "value": 1.0},
    "tp": {"tinh": "R", "value": 2.0}})
v["pos"] = [0.0, 0.0]
d = core.normalize_process({
    "name": "thử nhật ký", "symbol": "X",
    "tham_so": [{"ten": "nguong_nen_bps", "nhan": "", "gia_tri": 1e9, "don_vi": "bps"},
                {"ten": "chu_ky_atr", "nhan": "", "gia_tri": 3, "don_vi": "nến"}],
    "entry": {"steps": [bd, g, v],
              "edges": [{"from": bd["id"], "to": g["id"], "port": "out"},
                        {"from": g["id"], "to": v["id"], "port": "out"}]},
    "manage": {"steps": [], "edges": []}})

cd = bc.CaiDat(symbol="X", point=1.0, contract_size=1.0, spread_diem=0.0)
kq = bc.chay(d, nen_m1([90.0] * 30 + [110.0] * 30), cd)

# ================= 1. bản ghi rỗng chữ =================
print("\n▸ Bản ghi RỖNG CHỮ")
r = kq.nhat_ky[0]
kiem("bản ghi chỉ có số, id và nhãn kỹ thuật — không câu tiếng Việt nào",
     not any(isinstance(x, str) and " " in x
             for x in (r["tab"], r["ket"], *(r["duong"]))),
     f"— {sorted(r)}")
kiem("lưu id khối, KHÔNG lưu nhãn [3A.1]",
     all(k in {s["id"] for s in d["entry"]["steps"]} for k in r["duong"]))

# ================= 2. nhãn dựng lại =================
print("\n▸ Nhãn dựng lại, không lưu")
nhan = nk.nhan_khoi(d)
kiem("dựng được nhãn cho mọi khối", nhan.get(bd["id"]) == "1" and nhan.get(g["id"]),
     f"— {list(nhan.values())}")
# Kéo khối đi chỗ khác → nhãn có thể đổi, nhưng nhật ký vẫn trỏ đúng khối vì nó giữ id.
d2 = json.loads(json.dumps(d))
for st in d2["entry"]["steps"]:
    st["pos"] = [st["pos"][0] + 500, st["pos"][1] + 500]
kiem("kéo khối đi chỗ khác — nhật ký cũ vẫn trỏ đúng khối (vì giữ id, không giữ nhãn)",
     set(nk.nhan_khoi(d2)) == set(nhan))

# ================= 3. dựng chữ theo lô =================
print("\n▸ Dựng chữ theo lô")
lo = nk.dung_lo(kq, 0, 5, chi_co_viec=True)
kiem("lô chỉ-có-việc: mọi dòng đều có việc", lo["dong"] and all(x["co_viec"] for x in lo["dong"]))
kiem("dòng chữ nêu rõ đã đặt lệnh nào",
     "đặt Mua L-0001" in lo["dong"][0]["chu"], f"— {lo['dong'][0]['chu']}")
het = nk.dung_lo(kq, 0, 5, chi_co_viec=False)
kiem("lô mọi-lượt nhiều hơn hẳn lô chỉ-có-việc", het["tong"] > lo["tong"],
     f"— {het['tong']} vs {lo['tong']}")
kiem("lượt trượt nêu rõ CỔNG nào và HAI VẾ bằng bao nhiêu",
     "hết lượt tại" in het["dong"][0]["chu"] and "90.00" in het["dong"][0]["chu"],
     f"— {het['dong'][0]['chu']}")
kiem("chỉ dựng chữ cho lô xin, không dựng cả 100% nhật ký",
     len(het["dong"]) == 5 and het["tong"] == len(kq.nhat_ky))

# "chưa có số" KHÁC HẲN "so xong thấy không đạt" — trộn hai thứ là debug đi nhầm hướng.
g_atr = core.make_action_step({
    "type": core.CHECK_COND, "name": "ATR < 999",
    "conditions": [{"trai": {"ten": "atr", "period": 5}, "phep": "<",
                    "phai": {"value": 999.0}}]})
g_atr["pos"] = [0.0, 0.0]
d3 = core.normalize_process(dict(
    d, entry={"steps": [bd, g_atr, v],
              "edges": [{"from": bd["id"], "to": g_atr["id"], "port": "out"},
                        {"from": g_atr["id"], "to": v["id"], "port": "out"}]}))
kq3 = bc.chay(d3, nen_m1([100.0] * 30), cd)
chu = nk.dung_lo(kq3, 0, 1, chi_co_viec=False)["dong"][0]["chu"]
kiem("chưa đủ dữ liệu → \"chưa có dữ liệu\", KHÔNG phải \"= 0, không < 999\"",
     "chưa có dữ liệu" in chu, f"— {chu}")

# ================= 4. ghi / đọc ngược =================
print("\n▸ Ghi ra đĩa rồi đọc ngược")
p = nk.ghi(kq, cd, ten="__test_nhat_ky__")
meta, lenh, luot = nk.doc_file(p)
# `Lenh.tom_tat()` có sẵn khoá `loai` (stop/limit/market). Trải phẳng nó vào bản ghi là
# ĐÈ MẤT nhãn dòng, và đọc ngược sẽ nhận nhầm lệnh thành lượt — ghi vẫn "thành công".
kiem("đọc lại ĐỦ số lệnh (khoá `loai` của lệnh không đè mất nhãn dòng)",
     len(lenh) == len(kq.so.lenh), f"— {len(lenh)}/{len(kq.so.lenh)}")
kiem("đọc lại đủ số lượt", len(luot) == len(kq.nhat_ky), f"— {len(luot)}/{len(kq.nhat_ky)}")
kiem("meta giữ NGUYÊN BẢN sơ đồ đã chạy — để mở lại lần chạy cũ",
     meta["doc"]["entry"]["steps"][0]["id"] == bd["id"])
kiem("meta giữ điều kiện chạy (spread, vốn, phí)",
     meta["spread_diem"] == cd.spread_diem and meta["deposit"] == cd.deposit)
os.remove(p)

# ================= 5. vân tay =================
print("\n▸ Vân tay — đổi khi LOGIC đổi")
kiem("kéo khối đi chỗ khác KHÔNG đổi vân tay", nk._van_tay(d) == nk._van_tay(d2))
d4 = json.loads(json.dumps(d))
d4["entry"]["steps"][1]["conditions"][0]["phai"] = 999.0
kiem("đổi một ngưỡng thì ĐỔI vân tay", nk._van_tay(d) != nk._van_tay(d4))
d5 = json.loads(json.dumps(d))
d5["entry"]["edges"] = []
kiem("đổi cách NỐI DÂY cũng đổi vân tay — cùng bộ khối mà nối khác là chiến lược khác",
     nk._van_tay(d) != nk._van_tay(d5))
d6 = json.loads(json.dumps(d))
d6["tham_so"][0]["gia_tri"] = 123.0
kiem("đổi một THAM SỐ cũng đổi vân tay", nk._van_tay(d) != nk._van_tay(d6))

# ================= 6. soi một lượt trên sơ đồ =================
#
# `nk.ban_soi` dựng gói bắn sang CỬA SỔ VẼ để nó tô đường lượt đó đã đi (cửa sổ Màn chơi
# gọi nó qua `KetQuaQC.soi`). Giao diện tô tới tận DÒNG điều kiện hỏng, và nó làm được
# điều đó chỉ nhờ một giả định: `ve` có đúng một phần tử cho mỗi điều kiện của cổng, ĐÚNG
# THỨ TỰ các dòng trong hộp. Giả định đó không nằm ở đâu ngoài đây — lệch một cái là giao
# diện tô đỏ nhầm dòng, mà nhìn vẫn "có vẻ chạy". Bài này giữ nó.
print("\n▸ Soi một lượt trên sơ đồ")

# Lệnh CHỜ thật (đặt xong còn treo mấy nến rồi mới khớp) để có cả lượt có việc lẫn lượt
# hết lượt ở cổng.
# MỐC NEO = giá hiện tại, CỐ Ý: sơ đồ thử này không có cổng zone nào, nên không có
# zone để neo vào. Trước đây một cỗ máy ẩn dựng sẵn zone cho mọi sơ đồ nên chỗ này
# không phải khai gì — chính cái ẩn đó là thứ vừa bị bỏ.
v8 = core.make_action_step({
    "type": core.VAO_LENH, "name": "mua chờ", "huong": "mua", "loai": "stop",
    "lot": 0.01, "dem": {"tinh": "gia", "value": 5.0},
    "entry": {"moc": "gia_hien_tai"},
    "sl": {"tinh": "gia", "value": 1.0},
    "tp": {"tinh": "R", "value": 2.0}})
v8["pos"] = [0.0, 0.0]
bdm8 = core.make_start_step("theo dõi", "M1")
bdm8["pos"] = [0.0, 0.0]
# Cổng HAI điều kiện, cố ý. Cổng một điều kiện không soi được hợp đồng "một vết cho mỗi
# điều kiện": ngắt sớm ở cái sai đầu tiên vẫn ra đúng một vết, nên bài kiểm sẽ mù.
# Điều kiện 1 sai ở đoạn giá 90, điều kiện 2 luôn đúng — nên nếu ai đó cho `_xet_cong`
# ngắt sớm thì vết cụt đi và bài kiểm dưới bắt được ngay.
g8 = core.make_action_step({
    "type": core.CHECK_COND, "name": "giá trong khoảng",
    "conditions": [{"trai": {"ten": "close"}, "phep": ">",
                    "phai": {"value": 100.0}},
                   {"trai": {"ten": "close"}, "phep": "<",
                    "phai": {"value": 1000.0}}]})
g8["pos"] = [0.0, 0.0]
d8 = core.normalize_process({
    "name": "thử soi", "symbol": "X", "tham_so": d["tham_so"],
    "entry": {"steps": [bd, g8, v8],
              "edges": [{"from": bd["id"], "to": g8["id"], "port": "out"},
                        {"from": g8["id"], "to": v8["id"], "port": "out"}]},
    "manage": {"steps": [bdm8], "edges": []}})
kq8 = bc.chay(d8, nen_m1([90.0] * 20 + [110.0] * 12 + [116.0] * 15), cd)

khoi6 = {s["id"]: s for s in d8["entry"]["steps"] + d8["manage"]["steps"]}

k_truot = next(k for k, r in enumerate(kq8.nhat_ky) if r["ket"] == "het_luot" and r["cong"])
goi = nk.ban_soi(kq8.doc, kq8.nhat_ky[k_truot], kq8.nen5)   # ⚠ KHÔNG đặt tên `d`
kiem("mang đủ đường đi, cổng đã thử và nhãn để gọi tên khối",
     goi["duong"] and goi["cong"] and goi["chu"]
     and all(k in goi["nhan"] for k in goi["duong"]))

# ĐÂY là hợp đồng: mỗi cổng có đúng một vết cho mỗi điều kiện, đúng thứ tự.
lech = [c["khoi"] for c in goi["cong"]
        if len(c["ve"]) != len(khoi6[c["khoi"]].get("conditions") or [])]
kiem("mỗi cổng: số VẾT khớp đúng số ĐIỀU KIỆN — giao diện tô theo chỉ số này",
     not lech, f"— {len(lech)} cổng lệch")

xau = [c for c in goi["cong"] if not c["khop"]]
kiem("cổng trượt có ít nhất một điều kiện `dat = False` để tô đỏ",
     xau and all(any(not v["dat"] for v in c["ve"]) for c in xau),
     f"— {len(xau)} cổng trượt")
kiem("cổng ĐỖ thì mọi điều kiện đều đạt — không có cái nào lọt",
     all(all(v["dat"] for v in c["ve"]) for c in goi["cong"] if c["khop"]))

# Lượt CÓ VIỆC: đường đi phải dài hơn một khối, và mọi cổng trên đường đều có nhãn.
k_viec = next(k for k, r in enumerate(kq8.nhat_ky) if r["viec"])
dv = nk.ban_soi(kq8.doc, kq8.nhat_ky[k_viec], kq8.nen5)
kiem("lượt có việc: đi qua nhiều khối, mọi cổng đã thử đều có nhãn",
     len(dv["duong"]) > 1 and all(c["khoi"] in dv["nhan"] for c in dv["cong"]),
     f"— {len(dv['duong'])} khối")

# ================= 7. chiến lược trắng =================
print("\n▸ CHIẾN LƯỢC TRẮNG phải chạy được, không vỡ lô nhật ký")
#
# Lỗi thật: `cuoi = r.get("cong") and r["cong"][-1]["khoi"]` — trong Python `[] and x`
# trả về `[]`, KHÔNG phải `False`. Lượt nào không có cổng nào thì `cuoi` thành một list,
# rồi `nhan.get(list)` ném TypeError và vỡ cả lô nhật ký.
#
# Ca đó không hề hiếm: `File → Mới` cho ra đúng hai khối Bắt đầu, không cổng nào. Thêm
# `chu_ky_atr` cho đủ tham số là soát tĩnh 0 lỗi, backtest chạy ngon — bấm ▶ mới nổ.
d7 = core.new_process()
d7["tham_so"] = [core.make_tham_so("chu_ky_atr", "", 14, "nen")]
d7 = core.normalize_process(d7)
kiem("chiến lược trắng đi qua soát tĩnh sạch",
     not [p for p in core.validate_process(d7) if p["severity"] == "error"])
kq7 = bc.chay(d7, nen_m1([100.0] * 200), cd)
_rong7 = [r for r in kq7.nhat_ky if not r["viec"] and not r["cong"]]
kiem("và sinh ra lượt KHÔNG việc KHÔNG cổng (đúng ca làm vỡ)",
     bool(_rong7), f"— {len(_rong7)}/{len(kq7.nhat_ky)} lượt")
try:
    _lo7, _loi7 = nk.dung_lo(kq7, 0, 200, False), ""
except Exception as e:          # đúng thứ bài này canh: vỡ thì phải ra chữ đỏ, không treo
    _lo7, _loi7 = None, f"{type(e).__name__}: {e}"
kiem("dựng lô nhật ký KHÔNG vỡ, mọi dòng đều có chữ",
     bool(_lo7) and all(x["chu"] for x in _lo7["dong"]), _loi7 and f"— {_loi7[:70]}")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
