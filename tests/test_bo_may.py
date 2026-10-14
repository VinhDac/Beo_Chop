"""BỘ MÁY CHẠY CỖ MÁY 5 TRẠM — lịch, đi sơ đồ, Gom, mục tiêu, ý định lệnh, nhật ký.  (3b)

Chạy cỗ máy thật trên dữ liệu giả nhiều mã qua SÀN GIẢ (`tests/san_gia.py`) — y như vỏ QC sẽ
nối ở phần 4 — và canh những chỗ hỏng mà vẫn "trông có vẻ chạy":

  1. **Lịch**: ② chạy đúng một lần mỗi nến cho mỗi mã trong rổ; ① "một lần" là một lần; ③
     "khi tín hiệu đổi" không chạy khi tín hiệu chỉ được gia hạn; không trạm nào chạy lúc khởi
     động.
  2. **Gom ③**: ngân sách, trần mỗi mã, chỉ mua, cố định + tương đối, tin cậy, rủi ro ngang.
  3. **④** cắt lỗ + cấm vào lại thật sự giữ mục tiêu ở 0 suốt quãng cấm; «Dừng cả tài khoản»
     dừng hẳn.
  4. **⑤** lệnh giới hạn hết hạn thì huỷ; chia nhỏ đúng tỉ lệ; mục tiêu đổi thì huỷ lệnh chờ.
  5. **Không nhìn trước + tính xác định**: cắt dữ liệu ở T thì mọi thứ trước T y hệt; chạy hai
     lần ra y hệt.

Chạy:  python tests\\test_bo_may.py
"""
import copy
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import may as M  # noqa: E402
from cat_studio import tram as T  # noqa: E402
from cat_studio.bo_may import BoMay, LoiMay, _TinHieu  # noqa: E402
import san_gia as SG  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def dk(trai, phep, phai):
    return {"trai": trai, "phep": phep, "phai": phai}


def xay(m, k, *nhanh, bd=None, gom=None):
    """Trạm `k` = Bắt đầu rẽ ra các nhánh; mỗi nhánh là một chuỗi khối nối thẳng."""
    b = m["tram"][k]["steps"][0]
    b.update(bd or {})
    b["pos"] = [0.0, 0.0]
    steps, edges = [b], []
    for j, chuoi in enumerate(nhanh):
        truoc = b["id"]
        for i, st in enumerate(chuoi):
            st["pos"] = [300.0 * j, 120.0 * (i + 1) + 40.0 * j]
            steps.append(st)
            edges.append({"from": truoc, "to": st["id"], "port": "out"})
            truoc = st["id"]
    m["tram"][k]["steps"], m["tram"][k]["edges"] = steps, edges
    if gom is not None:
        m["tram"][k]["gom"] = gom
    return m


def may_xu_huong(lich3="khi_tin_hieu_doi", lam5=None, rui_ro=None, gom3=None):
    """① mọi mã · ② giá đóng H1 trên/dưới SMA 10 → LÊN / ĐỨNG NGOÀI · ③ chia đều · ⑤ khớp ngay."""
    m = M.may_moi("Theo xu hướng")
    xay(m, T.CHON_MA, [M.khoi_lam("vao_ro")])
    xay(m, T.TIN_HIEU,
        [M.khoi_hoi([dk({"ten": "gia_dong"}, ">", {"ten": "sma", "chu_ky": 10})], "Trên MA?"),
         M.khoi_lam("bao", huong="len", thoi_han=2)],
        [M.khoi_hoi([dk({"ten": "gia_dong"}, "<=", {"ten": "sma", "chu_ky": 10})], "Dưới MA?"),
         M.khoi_lam("bao", huong="dung_ngoai", thoi_han=2)])
    xay(m, T.CHIA_VON, [M.khoi_lam("dat_ty_trong", cach="chia_deu")], bd={"lich": lich3},
        gom=gom3)
    if rui_ro:
        xay(m, T.RUI_RO, *rui_ro)
    xay(m, T.KHOP_LENH, [lam5 or M.khoi_lam("lenh_thi_truong")])
    return m


BD = SG.NGAY + SG.NGAY_S                   # khởi động đúng một ngày (24 nến H1 > SMA 10)
DL = SG.du_lieu({"A": 8.0, "B": -8.0, "C": 0.0}, 6, seed=3, nhieu=0.0005)

# ================= 0. từ chối cỗ máy lỗi =================
print("\n▸ Từ chối cỗ máy còn lỗi")
try:
    BoMay(M.may_moi(), ["A"])
    kiem("cỗ máy trắng → từ chối chạy", False)
except LoiMay as e:
    kiem("cỗ máy trắng → từ chối chạy, câu nói rõ còn mấy lỗi và lỗi gì",
         "còn 4 lỗi" in str(e) and "② Tín hiệu" in str(e), f"— {str(e)[:70]}")

print("\n▸ Cần khởi động bao lâu")
from cat_studio.bo_may import can_khoi_dong  # noqa: E402
_m = may_xu_huong()
kiem("SMA 10 nến H1 → cần 11 nến H1 (10 + một nến dự phòng)", can_khoi_dong(_m) == 11 * SG.GIO,
     f"— {can_khoi_dong(_m) / SG.GIO} giờ")
_m["tham_so"].append({"ten": "dai", "nhan": "", "gia_tri": 200, "don_vi": "", "ghi_chu": ""})
_m["tram"][T.TIN_HIEU]["steps"][1]["conditions"][0]["phai"] = {"ten": "sma", "khung": "D1",
                                                              "chu_ky": "dai", "lui": 2}
kiem("SMA(D1, dai = 200) đọc lùi 2 → 203 ngày (tên tham số đọc ra giá trị)",
     can_khoi_dong(_m) == 203 * SG.NGAY_S, f"— {can_khoi_dong(_m) / SG.NGAY_S} ngày")

# ================= 1. chạy trọn một cỗ máy =================
print("\n▸ Chạy trọn cỗ máy xu hướng trên 3 mã (A lên, B xuống, C đi ngang)")
giu = {"A": [], "B": []}


def ghi_giu(bm, san, t):
    if t >= BD and (t - BD) % SG.GIO == 0:
        tk = san.tk()["giu"]
        for m in giu:
            giu[m].append((tk.get(m) or {}).get("pt", 0.0))


# Dựng MỘT lần rồi dùng lại: mỗi lần dựng, khối nhận mã định danh ngẫu nhiên mới, nên hai
# cỗ máy dựng riêng không bao giờ cho cùng một nhật ký — so chúng là so hai thứ khác nhau.
MAY_XH = may_xu_huong()
bm, san, yd = SG.chay(copy.deepcopy(MAY_XH), DL, bat_dau_t=BD, theo_doi=ghi_giu)
tk = bm.thong_ke()
nk = bm.nhat_ky
r2 = [r for r in nk if r.get("tram") == T.TIN_HIEU and "duong" in r]
kiem("không trạm nào chạy lúc khởi động",
     all(r["t"] >= BD for r in nk if r.get("tram") and "duong" in r))
gio_sau = (DL["A"][-1][0] - BD) // SG.GIO + 1
kiem("② chạy ĐÚNG một lần mỗi nến H1 cho mỗi mã trong rổ",
     all(sum(1 for r in r2 if r["ma"] == m) == gio_sau for m in "ABC"),
     f"— {[sum(1 for r in r2 if r['ma'] == m) for m in 'ABC']} / {gio_sau} nến")
kiem("① «một lần lúc đầu» chạy đúng một lần cho mỗi mã",
     tk["dem_chay"][T.CHON_MA] == 3, f"— {tk['dem_chay'][T.CHON_MA]}")
r1 = next((r for r in r2), None)
kiem("chỉ báo đã đủ dữ liệu ngay lượt ② đầu tiên (nhờ khởi động)",
     r1 and r1["cong"] and r1["cong"][0]["ve"][0]["phai"] is not None)
pA = sum(1 for x in giu["A"] if x > 1) / len(giu["A"])
pB = sum(1 for x in giu["B"] if x > 1) / len(giu["B"])
kiem("A (đi lên) được giữ phần lớn thời gian, B (đi xuống) gần như không",
     pA > 0.6 and pB < 0.3, f"— A {pA:.0%} · B {pB:.0%}")
kiem("có lệnh, có khớp, vốn đổi", tk["so_lenh"] > 0 and tk["so_lenh_khop"] > 0
     and tk["von_cuoi"] != tk["von_dau"], f"— {tk['so_lenh']} lệnh, lãi {tk['lai_pt']:.2f}%")
r3 = [r for r in nk if r.get("tram") == T.CHIA_VON and "gom" in r]
kiem("③ «khi tín hiệu đổi» chạy ÍT hơn hẳn ② (gia hạn tín hiệu không phải là đổi)",
     0 < len(r3) < len(r2) / 3, f"— ③ {len(r3)} lần, ② {len(r2)} lượt")
chia = [r["gom"]["muc_tieu"] for r in r3]
kiem("chia đều: mã có tín hiệu LÊN chia nhau 100%, mã đứng ngoài = 0",
     all(abs(sum(v for v in g.values()) - 100.0) < 1e-6 or not any(g.values())
         for g in chia) and any(len([v for v in g.values() if v]) == 2 for g in chia))
# Lỗi THẬT đã gặp: tới mục tiêu rồi mà giá trôi 0,1% là ⑤ đặt lệnh lắt nhắt ngược chiều liên
# tục (442 lệnh / 2 ngày). Luật QC: mục tiêu đã tới thì xoá; chỉ khi ③/④ phát mục tiêu mới,
# hoặc lệnh cũ bị huỷ, mới giao dịch lại. Nên MỌI lệnh phải có một "cò" ngay trước nó.
co = {}
for r in nk:
    if r.get("tram") == T.CHIA_VON and "gom" in r:
        for m in "ABC":
            co.setdefault(m, []).append(r["t"])
    elif r.get("tram") == T.RUI_RO and r.get("viec"):
        co.setdefault(r["ma"], []).append(r["t"])
for t_, ys in yd:
    for y in ys:
        if y["loai"] == "huy":
            co.setdefault(y["ma"], []).append(t_)
mo_coi = [(t_, y["ma"]) for t_, ys in yd for y in ys if y["loai"] == "dat"
          and not any(0 <= t_ - c <= 3 * SG.PHUT for c in co.get(y["ma"], []))]
kiem("mọi lệnh đều có «cò» ngay trước (③/④ vừa phát mục tiêu, hoặc vừa huỷ lệnh) — giá trôi "
     "không đẻ lệnh lắt nhắt", not mo_coi,
     f"— {len(mo_coi)} lệnh mồ côi / {tk['so_lenh']} lệnh")
the5 = {r["ma"] for r in nk if r.get("tram") == T.KHOP_LENH and "duong" in r}
kiem("⑤ chỉ chạy cho mã còn lệch mục tiêu", the5 and the5 <= {"A", "B", "C"})
boss = sum(DL[m][-1][4] / next(n for n in DL[m] if n[0] == BD)[4] - 1 for m in "ABC") / 3 * 100
kiem("boss = mua đều rồi giữ cả màn, tính từ lúc hết khởi động",
     SG.gan_bang(tk["boss_pt"], boss), f"— {tk['boss_pt']:.3f}% vs {boss:.3f}%")

print("\n▸ Nhật ký")
_ids = {k: {s["id"]: s for s in bm.may["tram"][k]["steps"]} for k in T.TRAM_KEYS}
xau = [r for r in nk if "duong" in r and (
    r["duong"][0] != bm.luong[r["tram"]]["vao"]
    or any(x not in _ids[r["tram"]] for x in r["duong"])
    or any(len(c["ve"]) != len(_ids[r["tram"]][c["khoi"]]["conditions"]) for c in r["cong"]))]
kiem("mỗi lượt: đường đi từ khối Bắt đầu, khối có thật, mỗi cổng ĐỦ vết từng điều kiện",
     not xau, f"— {len(xau)} lượt xấu")
kiem("nhật ký qua được JSON (không NaN lọt vào)", bool(json.dumps(nk, allow_nan=False)))
kiem("lượt đi nhánh 2 vẫn ghi lại cổng nhánh 1 ĐÃ TRƯỢT — trả lời được «thế 1A thì sao»",
     any(r["viec"] for r in r2) and any(len(r["cong"]) == 2 and not r["cong"][0]["khop"]
                                        and r["cong"][1]["khop"] for r in r2))

# ================= 2. Gom ③ =================
print("\n▸ Gom của trạm ③")


def gom3(lam, tin, gom=None, giu_=None, muc=None):
    """Chạy riêng ③ trên trạng thái dựng tay. `lam` = một khối (Bắt đầu → nó), hoặc danh
    sách NHÁNH. `tin` = {mã: (hướng, tin cậy)}; hướng None = không có tín hiệu."""
    m = may_xu_huong(gom3=gom)
    xay(m, T.CHIA_VON, *(lam if isinstance(lam, list) else [[lam]]), gom=gom)
    bm_ = BoMay(m, sorted(tin), 10_000.0)
    bm_.t = SG.NGAY
    bm_.tk = {"von": 10_000.0, "tien_mat": 10_000.0, "giu": giu_ or {}, "lenh_cho": {}}
    bm_.muc_tieu = dict(muc or {})
    for x, (h, c) in tin.items():
        if h is not None:
            bm_.tin_hieu[x] = _TinHieu(h, SG.NGAY + 10_000, c, None, SG.NGAY)
    bm_._chay_chia_von(SG.NGAY)
    return {x: round(v, 6) for x, v in bm_.muc_tieu.items()}, bm_.nhat_ky[-1]["gom"]


LEN4 = {x: (1, None) for x in "ABCD"}
mt, g = gom3(M.khoi_lam("dat_ty_trong", cach="co_dinh", pt=30), LEN4)
kiem("4 mã × cố định 30% = 120% > ngân sách → thu nhỏ đều về 25%",
     mt == {x: 25.0 for x in "ABCD"} and SG.gan_bang(g["thu_nho"], 100 / 120), f"— {mt}")
mt, _ = gom3(M.khoi_lam("dat_ty_trong", cach="co_dinh", pt=30), LEN4,
             gom={"tran_moi_ma_pt": 20})
kiem("trần mỗi mã 20% → 20% mỗi mã, tổng 80%", mt == {x: 20.0 for x in "ABCD"}, f"— {mt}")
mt, _ = gom3(M.khoi_lam("dat_ty_trong", cach="chia_deu"), {"A": (1, None), "B": (1, None)},
             gom={"giu_tien_pt": 50})
kiem("giữ 50% tiền mặt + chia đều 2 mã → 25% mỗi mã", mt == {"A": 25.0, "B": 25.0}, f"— {mt}")
mt, _ = gom3(M.khoi_lam("dat_ty_trong", cach="chia_deu"), {"A": (1, None), "B": (-1, None)})
kiem("chỉ mua: mã báo XUỐNG → 0, mã còn lại nhận trọn ngân sách", mt == {"A": 100.0}, f"— {mt}")
mt, _ = gom3(M.khoi_lam("dat_ty_trong", cach="chia_deu"), {"A": (1, None), "B": (-1, None)},
             gom={"chi_mua": False})
kiem("cho bán khống: XUỐNG → tỷ trọng ÂM", mt == {"A": 50.0, "B": -50.0}, f"— {mt}")
mt, _ = gom3(M.khoi_lam("dat_ty_trong", cach="theo_tin_cay"), {"A": (1, 0.2), "B": (1, 0.6)})
kiem("theo độ tin cậy 0.2 / 0.6 → 25% / 75%", mt == {"A": 25.0, "B": 75.0}, f"— {mt}")
mt, _ = gom3(M.khoi_lam("dat_ty_trong", cach="chia_deu"), {"A": (None, None), "B": (1, None)},
             giu_={"A": {"pt": 40.0, "sl": 1.0, "gia_von": 1.0}})
kiem("mã đang giữ mà hết tín hiệu → mục tiêu 0 (bán ra), mã có tín hiệu nhận trọn",
     mt == {"B": 100.0}, f"— {mt}")
# ③ phải có ít nhất một «Đặt tỷ trọng» mới chạy được, nên «Giữ nguyên» đi một nhánh riêng.
NHANH_GIU = [[M.khoi_hoi([dk({"ten": "huong_tin_hieu"}, "==", {"value": 1})]),
              M.khoi_lam("giu_nguyen")],
             [M.khoi_hoi([dk({"ten": "huong_tin_hieu"}, "==", {"value": 7})]),
              M.khoi_lam("dat_ty_trong", cach="chia_deu")]]
mt, _ = gom3(NHANH_GIU, {"A": (1, None)}, giu_={"A": {"pt": 37.5, "sl": 1.0, "gia_von": 1.0}})
kiem("«Giữ nguyên» → mục tiêu = đúng phần đang giữ", mt == {"A": 37.5}, f"— {mt}")
mt, _ = gom3([[M.khoi_hoi([dk({"ten": "huong_tin_hieu"}, "==", {"value": 5})]),
              M.khoi_lam("dat_ty_trong", cach="chia_deu")]], {"A": (1, None)}, muc={"A": 12.0})
kiem("sơ đồ ③ không ra quyết định nào → GIỮ mục tiêu cũ", mt == {"A": 12.0}, f"— {mt}")

m_ = may_xu_huong()
co = M.khoi_hoi([dk({"ten": "tin_cay"}, ">=", {"value": 0.9})], "Chắc chắn?")
xay(m_, T.CHIA_VON, [co, M.khoi_lam("dat_ty_trong", cach="co_dinh", pt=30)],
    [M.khoi_hoi([dk({"ten": "tin_cay"}, "<", {"value": 0.9})], "Còn lại"),
     M.khoi_lam("dat_ty_trong", cach="chia_deu")])
bm_ = BoMay(m_, ["A", "B", "C"])
bm_.t = SG.NGAY
for x, c in (("A", 0.95), ("B", 0.5), ("C", 0.5)):
    bm_.tin_hieu[x] = _TinHieu(1, SG.NGAY + 10_000, c, None, SG.NGAY)
bm_._chay_chia_von(SG.NGAY)
mt = {x: round(v, 6) for x, v in bm_.muc_tieu.items()}
kiem("cố định lấy trước (A 30%), chia đều chia nhau PHẦN CÒN LẠI (B, C 35%)",
     mt == {"A": 30.0, "B": 35.0, "C": 35.0}, f"— {mt}")

m_ = may_xu_huong()
xay(m_, T.CHIA_VON, [M.khoi_lam("dat_ty_trong", cach="rui_ro_ngang", khung="D1", chu_ky=5)])
bm_ = BoMay(m_, ["A", "B"])
bm_.t = SG.NGAY
for x in "AB":
    bm_.tin_hieu[x] = _TinHieu(1, SG.NGAY + 10_000, None, None, SG.NGAY)
_atr = {"A": 1.0, "B": 2.0}
for khoa in bm_.doc_atr_pt:
    bm_.doc_atr_pt[khoa] = {x: (lambda v: (lambda lui=0: v))(_atr[x]) for x in "AB"}
bm_._chay_chia_von(SG.NGAY)
mt = {x: round(v, 4) for x, v in bm_.muc_tieu.items()}
kiem("rủi ro ngang nhau: ATR% 1 vs 2 → vốn 2 : 1", mt == {"A": 66.6667, "B": 33.3333}, f"— {mt}")

# ================= 3. ④ Rủi ro =================
print("\n▸ Trạm ④: cắt lỗ + cấm vào lại, dừng cả tài khoản")
# A đi lên rồi SẬP 6% trong một phút (ngày 3, 10:30) — trailing «rơi 3% từ đỉnh» phải bắt.
DL4 = SG.du_lieu({"A": 8.0}, 5, seed=5, nhieu=0.0005, sap={"A": (3 * 1440 + 630, -6.0)})
cat = [M.khoi_hoi([dk({"ten": "sut_tu_dinh_pt"}, ">=", {"value": 3})], "Rơi 3% từ đỉnh?"),
       M.khoi_lam("dua_ve_0"), M.khoi_lam("cam_vao_lai", so_nen=6)]
muc_A = []
bm4, san4, yd4 = SG.chay(may_xu_huong(rui_ro=[cat]), DL4, bat_dau_t=BD,
                         theo_doi=lambda b, s, t: muc_A.append((t, b.muc_tieu.get("A", 0.0),
                                                                 b.cam.get("A"))))
r4 = [r for r in bm4.nhat_ky if r.get("tram") == T.RUI_RO and r.get("viec")]
kiem("cú sập → ④ «Đưa về 0» + «Cấm vào lại 6 nến» (trailing rơi 3% từ đỉnh)",
     r4 and [v["loai"] for v in r4[0]["viec"]] == ["dua_ve_0", "cam_vao_lai"],
     f"— {[v['loai'] for v in r4[0]['viec']] if r4 else None}")
if r4:
    t_cat, den = r4[0]["t"], r4[0]["viec"][1]["den"]
    trong = [x for t, x, _ in muc_A if t_cat <= t < den]
    kiem("suốt quãng cấm mục tiêu A = 0 (dù ② vẫn có thể báo LÊN)", trong and not any(trong),
         f"— {len(trong)} bước")
    kiem("cấm đúng 6 nến H1", den - t_cat == 6 * SG.GIO)

dau = [M.khoi_hoi([dk({"ten": "sut_giam_tk_pt"}, ">=", {"value": 2})], "Sụt 2%?"),
       M.khoi_lam("dung_tai_khoan")]
bm5, san5, _ = SG.chay(may_xu_huong(rui_ro=[dau]), DL4, bat_dau_t=BD)
t_dung = next((r["t"] for r in bm5.nhat_ky if r.get("su_kien") == "dung_tai_khoan"), None)
kiem("«Dừng cả tài khoản» bật khi sụt 2%", t_dung is not None and bm5.thong_ke()["dung_tai_khoan"])
kiem("sau khi dừng: ①②③ không chạy nữa, cuối lượt không còn giữ mã nào",
     t_dung and not [r for r in bm5.nhat_ky if r.get("t", 0) > t_dung and "duong" in r
                     and r["tram"] in (T.CHON_MA, T.TIN_HIEU, T.CHIA_VON)]
     and not san5.tk()["giu"])

# ================= 4. ⑤ Khớp lệnh =================
print("\n▸ Trạm ⑤: giới hạn hết hạn, chia nhỏ, đổi mục tiêu")
gh = M.khoi_lam("lenh_gioi_han", lech_pt=5, het_han=3)
bm6, san6, yd6 = SG.chay(may_xu_huong(lam5=gh), DL, bat_dau_t=BD, den_t=BD + 6 * SG.GIO)
dat6 = [y for _, ys in yd6 for y in ys if y["loai"] == "dat"]
huy6 = [y for _, ys in yd6 for y in ys if y["loai"] == "huy"]
_t0 = bm6.lenh[dat6[0]["id"]]["t_dat"] if dat6 else None
_c0 = next((n[4] for n in DL[dat6[0]["ma"]] if n[0] == _t0), None) if dat6 else None
kiem("lệnh giới hạn MUA nằm DƯỚI giá đóng lúc đặt đúng 5%",
     dat6 and dat6[0]["kieu"] == "gioi_han" and dat6[0]["pt"] > 0
     and SG.gan_bang(dat6[0]["gia"], _c0 * 0.95), f"— {dat6[0]['gia']:.4f} vs {_c0:.4f}")
kiem("cách 5% thì không khớp nổi → hết hạn 3 nến là HUỶ, lý do «het_han»",
     huy6 and huy6[0]["ly_do"] == "het_han"
     and next(t for t, ys in yd6 if any(y is huy6[0] for y in ys))
     - bm6.lenh[huy6[0]["id"]]["t_dat"] == 3 * SG.PHUT)
kiem("huỷ xong → ⑤ đặt lại lệnh mới", len(dat6) >= 2)

cn = M.khoi_lam("lenh_thi_truong", phan_pt=50)
bm7, _, yd7 = SG.chay(may_xu_huong(lam5=cn), DL, bat_dau_t=BD, den_t=BD + 2 * SG.GIO)
datA = [y for _, ys in yd7 for y in ys if y["loai"] == "dat" and y["ma"] == "A"]
kiem("chia nhỏ 50%: lệnh sau ≈ một nửa lệnh trước (phần còn lệch giảm một nửa mỗi lượt)",
     len(datA) >= 3 and 0.4 < datA[1]["pt"] / datA[0]["pt"] < 0.6,
     f"— {[round(y['pt'], 2) for y in datA[:3]]}")

doi = [y for _, ys in yd6 for y in ys if y["loai"] == "huy" and y["ly_do"] == "doi_muc_tieu"]
bm8, _, yd8 = SG.chay(may_xu_huong(lam5=M.khoi_lam("lenh_gioi_han", lech_pt=5, het_han=500)),
                      DL, bat_dau_t=BD, den_t=BD + 2 * SG.NGAY_S)
doi = [y for _, ys in yd8 for y in ys if y["loai"] == "huy" and y["ly_do"] == "doi_muc_tieu"]
kiem("lệnh chờ treo lâu mà mục tiêu đổi → huỷ, lý do «doi_muc_tieu»", bool(doi),
     f"— {len(doi)} lần")

# ================= 5. không nhìn trước + xác định =================
print("\n▸ Không nhìn trước, tính xác định")
T_CAT = BD + 2 * SG.NGAY_S + 7 * SG.GIO + 13 * SG.PHUT
bmc, _, ydc = SG.chay(copy.deepcopy(MAY_XH), DL, bat_dau_t=BD, den_t=T_CAT)


def truoc(ds, t):
    return json.dumps([r for r in ds if r.get("t", 0) <= t], sort_keys=True)


kiem("cắt dữ liệu ở T: nhật ký mọi bước ≤ T Y HỆT bản chạy trọn",
     truoc(bmc.nhat_ky, T_CAT) == truoc(bm.nhat_ky, T_CAT))
kiem("…và ý định lệnh mọi bước ≤ T y hệt",
     json.dumps([x for x in ydc if x[0] <= T_CAT]) == json.dumps([x for x in yd if x[0] <= T_CAT]))
bm2, _, yd2 = SG.chay(copy.deepcopy(MAY_XH), copy.deepcopy(DL), bat_dau_t=BD)
kiem("chạy lại cùng dữ liệu → nhật ký, ý định, thống kê y hệt",
     json.dumps(bm2.nhat_ky) == json.dumps(bm.nhat_ky) and yd2 == yd
     and bm2.thong_ke() == bm.thong_ke())

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
