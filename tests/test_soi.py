"""SOI MỘT LƯỢT — chụp lại đúng những gì sơ đồ đã làm tại một thời điểm.

Bài này canh hai thứ, và cái thứ nhất là lý do bài tồn tại:

  1. **HAI BẢN PHẢI KHÔNG BAO GIỜ LỆCH NHAU.** `bo_chay.mot_luot` (chạy mười triệu lần
     một ngày, ngắt sớm ở điều kiện sai đầu tiên) và `mot_luot_ghi` (chạy mỗi lần bấm
     chuột, tính đủ mọi điều kiện và ghi lại) là MỘT NGUỒN SỰ THẬT BỊ CHÉP LÀM HAI —
     đúng thứ cả repo này vẫn cảnh báo ở mọi chỗ khác.

     Chép làm hai là cố ý, nhưng cái giá phải trả bằng phép kiểm: chạy CẢ HAI trên hàng
     nghìn sơ đồ ngẫu nhiên với hàng nghìn trạng thái ngẫu nhiên, so từng ô báo giá.
     Lệch một ô là soi nói dối — mà soi nói dối thì tệ hơn không có soi, vì người ta
     mở nó ra đúng lúc đang không hiểu chuyện gì xảy ra.

  2. **Nhật ký phải kể ĐỦ CHUYỆN**, kể cả nhánh đã thử rồi bỏ. Không thấy nhánh trượt
     thì người dùng tưởng nó chưa bao giờ được xét tới.

⚠ Và `soi_luot` phải JSON hoá được TRONG MỌI CA. `json.dumps` phun `NaN` trần — không
phải JSON hợp lệ — nên một ô chưa đặt là đủ làm vỡ cả lời gọi qua cầu nối, mà lỗi hiện
ra lại là "không đọc được phản hồi".
"""
import io
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import api  # noqa: E402
from cat_studio import bo_chay as B  # noqa: E402
from cat_studio import core  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


TICK = 0.001
SO_HANG_GIA = ("cong_bang", "bien", "bien_mua", "bien_ban", "lech")
SO_HANG_LOT = ("lot", "lot_mua", "lot_ban")
TOAN_HANG_SO = ("bid", "ask", "mid", "spread", "ton_kho", "bid_kl", "ask_kl")


def _dieu_kien(r):
    """Một điều kiện ngẫu nhiên nhưng HỢP LỆ — soi chỉ nhận sơ đồ chạy được."""
    if r.random() < 0.25:
        return {"trai": {"ten": "co_so"},
                "phep": r.choice(["la_dung", "la_sai"])}
    ten = r.choice(["ton_kho", "spread", "bid_kl", "mid"])
    loai = core.TOAN_HANG_LOAI[ten]
    if loai == "dem":
        tinh = core.TOAN_HANG_DON_VI[ten]
    elif loai == "muc_gia":
        tinh = "gia"
    else:
        tinh = r.choice(["tick", "spread", "bps"])
    return {"trai": {"ten": ten}, "phep": r.choice([">=", ">", "<=", "<", "==", "!="]),
            "phai": {"value": round(r.uniform(-8, 12), 3), "tinh": tinh}}


def _so_hang(r, sid, y, x):
    """Một số hạng ngẫu nhiên nhưng HỢP LỆ với đích của nó."""
    if r.random() < 0.4:
        dich = r.choice(SO_HANG_LOT)
        phep = r.choice(["=", "+=", "*="])
        luong = {"he_so": round(r.uniform(0, 6), 2), "don_vi": "lot"}
        if r.random() < 0.3:
            luong["toan_hang"] = r.choice(["ton_kho", "bid_kl", "ask_kl"])
    else:
        dich = r.choice(SO_HANG_GIA)
        phep = r.choice(["=", "+="])
        if r.random() < 0.35:
            # Nhân với một đại lượng GIÁ — đại lượng tự mang đơn vị, không thước đo.
            th = "mid" if (dich == "cong_bang" and phep == "=") else "spread"
            luong = {"he_so": round(r.uniform(0.1, 2), 2), "toan_hang": th}
        else:
            dv = "gia" if (dich == "cong_bang" and phep == "=") else \
                r.choice(["tick", "spread", "bps"])
            luong = {"he_so": round(r.uniform(0, 40 if dv == "gia" else 4), 3),
                     "don_vi": dv}
    ra = {"id": sid, "kind": core.KIND_ACTION, "type": core.SO_HANG,
          "dich": dich, "phep": phep, "luong": luong, "pos": [x, y]}
    if r.random() < 0.3:
        ra["khi"] = _dieu_kien(r)
    return ra


def so_do_ngau_nhien(r):
    """Một sơ đồ ngẫu nhiên: chuỗi có rẽ nhánh, có cổng, có `khi`."""
    steps = [dict(core.make_start_step("BĐ"), id="s0", pos=[0.0, 400.0])]
    canh = []
    hang = [("s0", 0)]            # (id cha, độ sâu)
    n = 0
    while hang and n < 14:
        cha, sau = hang.pop(0)
        for nhanh in range(1 if r.random() < 0.65 or sau > 2 else 2):
            n += 1
            sid = f"s{n}"
            y = 400.0 + (nhanh * 2 - 1) * 90 * (3 - min(sau, 2)) + r.uniform(-8, 8)
            x = 200.0 + sau * 240
            if r.random() < 0.35:
                steps.append({"id": sid, "kind": core.KIND_ACTION,
                              "type": core.CHECK_COND, "pos": [x, y],
                              "conditions": [_dieu_kien(r)
                                             for _ in range(r.randint(1, 3))]})
            else:
                steps.append(_so_hang(r, sid, y, x))
            canh.append((cha, sid))
            if r.random() < 0.75:
                hang.append((sid, sau + 1))
    return {"schema": core.SCHEMA, "type": "strategy", "name": "t", "symbol": "X",
            "tham_so": [], core.TAB_BAO_GIA: {
                "steps": steps,
                "edges": [{"from": a, "to": b, "port": "out"} for a, b in canh]}}


def nhin_ngau_nhien(r):
    nh = B.Nhin()
    if r.random() < 0.12:
        nh.bid = nh.ask = B.NAN            # đang MÙ
        nh.bid_kl = nh.ask_kl = 0.0
        nh.co_so = False
    else:
        nh.bid = round(9.0 + r.uniform(-0.5, 0.5), 3)
        nh.ask = round(nh.bid + TICK * r.randint(1, 5), 3)
        nh.bid_kl = round(r.uniform(0, 3000), 1)
        nh.ask_kl = round(r.uniform(0, 3000), 1)
        nh.co_so = True
    nh.ton_kho = round(r.uniform(-9, 9), 2)
    return nh


# ================= 1. HAI BẢN PHẢI KHÔNG BAO GIỜ LỆCH =================
print("\n▸ `mot_luot` và `mot_luot_ghi` — một sự thật, hai bản cài đặt")

r = random.Random(4242)
SO_SO_DO, SO_TRANG_THAI = 120, 25
lech = []
so_luot = 0
co_re_nhanh = co_lui = co_khi_truot = co_mu = 0

for _ in range(SO_SO_DO):
    doc = so_do_ngau_nhien(r)
    try:
        lenh, dau, khoi = B.bien_dich(doc)
    except B.LoiChay:
        continue                            # sơ đồ ngẫu nhiên lỡ sinh ra thứ không chạy
    co_re_nhanh += any(len(x[2]) > 1 for x in lenh)
    for _ in range(SO_TRANG_THAI):
        nh = nhin_ngau_nhien(r)
        co_mu += not nh.co_so
        so_luot += 1

        a = list(B.NHAP_GOC)
        B.mot_luot(lenh, dau, nh, TICK, a)
        b, nk = B.mot_luot_ghi(lenh, dau, khoi, nh, TICK)

        co_lui += any(g.get("bo") for g in nk)
        co_khi_truot += any(g.get("ap_dung") is False for g in nk)
        # So từng ô. NaN == NaN là False nên phải so riêng — mà `cong_bang` chưa đặt
        # thì ĐÚNG là NaN, tức ca này gặp thường xuyên chứ không phải hiếm.
        if any(not (x == y or (x != x and y != y)) for x, y in zip(a, b)):
            lech.append((doc, nh, a, b))

kiem(f"{so_luot:,} lượt trên {SO_SO_DO} sơ đồ ngẫu nhiên — KHÔNG lệch ô nào",
     not lech, f"— lệch {len(lech)} lượt" if lech else "")
if lech:
    doc, nh, a, b = lech[0]
    print(f"      ví dụ: bid={nh.bid} ask={nh.ask} tồn kho={nh.ton_kho}")
    print(f"      mot_luot     {a}")
    print(f"      mot_luot_ghi {b}")

# Bộ sinh ngẫu nhiên PHẢI thật sự chạm được mọi đường đi, nếu không phép so trên chỉ
# chứng minh hai bản giống nhau ở phần dễ.
kiem("bộ sinh có chạm RẼ NHÁNH", co_re_nhanh > 10, f"— {co_re_nhanh} sơ đồ")
kiem("bộ sinh có chạm LUẬT LÙI", co_lui > 20, f"— {co_lui} lượt")
kiem("bộ sinh có chạm `khi` TRƯỢT", co_khi_truot > 20, f"— {co_khi_truot} lượt")
kiem("bộ sinh có chạm ca MẤT SỔ LỆNH", co_mu > 50, f"— {co_mu} lượt")


# ================= 2. NHẬT KÝ PHẢI KỂ ĐỦ CHUYỆN =================
print("\n▸ Nhật ký — kể cả nhánh đã thử rồi bỏ")

MAU = api.Api().demo_process()["value"]


def soi(ton_kho=0.0, co_so=True, bid=9.499, ask=9.501):
    return B.soi_luot(MAU, {"bid": bid, "ask": ask, "bid_kl": 800.0, "ask_kl": 600.0,
                            "co_so": co_so, "ton_kho": ton_kho}, TICK)


s = soi()
theo_id = {k["id"]: k for k in s["khoi"]}
kiem("cổng TRƯỢT vẫn nằm trong nhật ký — không thấy nó thì tưởng chưa xét tới",
     "s_mu" in theo_id and theo_id["s_mu"]["qua"] is False)
kiem("và cổng trượt KHÔNG bị gắn nhãn 'bỏ' — nó là NGUYÊN NHÂN lùi, không phải nạn nhân",
     not theo_id["s_mu"].get("bo"))
kiem("mọi khối của chuỗi chính đều chạy", all(theo_id[i]["qua"] for i in
     ("s_cb", "s_bien", "s_lech", "s_lot")))

kiem("mỗi điều kiện mang CON SỐ hai vế, không chỉ đạt/trượt",
     "trai" in theo_id["s_mu"]["dieu_kien"][0])
kiem("phép đúng/sai thì vế phải là None — nó vốn không có vế phải",
     theo_id["s_mu"]["dieu_kien"][0]["phai"] is None)

s5 = soi(ton_kho=6.0)
t5 = {k["id"]: k for k in s5["khoi"]}
kiem("`khi` khớp → số hạng được áp dụng, có ghi TRƯỚC và SAU",
     t5["s_tran"]["ap_dung"] and t5["s_tran"]["sau"] == [0.0])
kiem("`khi` trượt → ghi rõ là KHÔNG áp dụng, và không có `luong`",
     not t5["s_san"]["ap_dung"] and "luong" not in t5["s_san"])
kiem("điều kiện của `khi` cũng mang con số",
     t5["s_san"]["khi"]["trai"] == 6.0 and t5["s_san"]["khi"]["phai"] == -5.0)

sm = soi(co_so=False, bid=B.NAN, ask=B.NAN)
tm = {k["id"]: k for k in sm["khoi"]}
kiem("MẤT SỔ: cổng `co_so là SAI` khớp, nhánh rút chạy",
     tm["s_mu"]["qua"] and "s_rut" in tm)
kiem("và chuỗi chính KHÔNG chạy — không có khối nào của nó trong nhật ký",
     "s_cb" not in tm, f"— {sorted(tm)}")
kiem("báo giá rỗng cả hai phía", sm["bao_gia"]["mua_lot"] == 0
     and sm["bao_gia"]["ban_lot"] == 0)


# ================= 3. BÁO GIÁ ĐÃ LÀM TRÒN =================
print("\n▸ Báo giá — con số SẼ GỬI ĐI, không phải con số trong đầu sơ đồ")
s = soi(ton_kho=0.0)
kiem("giá mua/bán là bội của tick",
     abs(round(s["bao_gia"]["mua_gia"] / TICK) * TICK - s["bao_gia"]["mua_gia"]) < 1e-9)
kiem("bản nháp giữ số THÔ để so được với giá đã tròn",
     s["nhap"]["cong_bang"] == 9.5)
kiem("`nhin` mang cả mid và spread đã tính sẵn",
     abs(s["nhin"]["mid"] - 9.5) < 1e-9 and s["nhin"]["spread"] is not None)
kiem("mất sổ thì mid/spread là None, KHÔNG phải 0",
     sm["nhin"]["mid"] is None and sm["nhin"]["spread"] is None)


# ================= 4. JSON HOÁ ĐƯỢC TRONG MỌI CA =================
print("\n▸ JSON — `NaN` trần làm vỡ `JSON.parse` bên trình duyệt")
xau = []
r2 = random.Random(99)
for _ in range(200):
    nh = nhin_ngau_nhien(r2)
    d = B.soi_luot(MAU, {"bid": nh.bid, "ask": nh.ask, "bid_kl": nh.bid_kl,
                         "ask_kl": nh.ask_kl, "co_so": nh.co_so,
                         "ton_kho": nh.ton_kho}, TICK)
    j = json.dumps(d)
    if "NaN" in j or "Infinity" in j:
        xau.append(nh)
kiem("200 trạng thái ngẫu nhiên — không ca nào sinh `NaN`/`Infinity`", not xau,
     f"— {len(xau)} ca" if xau else "")

kiem("sơ đồ chưa đặt giá công bằng → ô đó là None, phân biệt được với 0",
     B.soi_luot({"schema": core.SCHEMA, core.TAB_BAO_GIA: {"steps": [], "edges": []}},
                {"bid": 9.5, "ask": 9.51, "co_so": True}, TICK)["nhap"]["cong_bang"]
     is None)

# XÁC ĐỊNH: soi là hàm THUẦN, nên bấm lại đúng mốc đó phải ra đúng một kết quả.
kiem("soi hai lần cùng một trạng thái → kết quả Y HỆT",
     json.dumps(soi(ton_kho=3.0)) == json.dumps(soi(ton_kho=3.0)))


print("\n" + "=" * 58)
print(f"  {dung} đúng, {sai} sai")
print("=" * 58)
sys.exit(1 if sai else 0)
