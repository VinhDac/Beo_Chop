"""MẪU DỰNG SẴN + CHỮ "VÌ SAO" của cỗ máy 5 trạm.  (D-10, phần 3c)

  1. **Mọi mẫu mở ra SẠCH** — không lỗi, không cảnh báo — và CHẠY ĐƯỢC trên dữ liệu giả: mẫu
     tín hiệu nào cũng phát được tín hiệu, mẫu khớp lệnh nào cũng ra được lệnh.
  2. **Đổi mẫu không vặn lại núm** — tham số người chơi đã chỉnh giữ nguyên giá trị.
  3. **Mẫu làm đúng việc của nó** — N mã thanh khoản giữ đúng N mã, N mã mạnh nhất bỏ mã đi
     xuống, trailing/cầu dao bật khi sập.
  4. **Chữ nhật ký** — dòng có việc, dòng trượt nói đúng điều kiện sai kèm con số, dòng Gom,
     dòng sự kiện; đúng từng chữ.

Chạy:  python tests\\test_mau_tram.py
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
from cat_studio import mau_tram as MT  # noqa: E402
from cat_studio.bo_may import can_khoi_dong  # noqa: E402
from cat_studio.nhat_ky_may import DocNhatKy  # noqa: E402
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


BD = SG.NGAY + 3 * SG.NGAY_S          # khởi động 3 ngày: đủ cho EMA 50 nến H1
DL = SG.du_lieu({"A": 8.0, "B": -8.0, "C": 0.0}, 6, seed=11, nhieu=0.0005)

# ================= 1. mọi mẫu sạch + chạy được =================
print("\n▸ Mọi mẫu mở ra sạch")
mm = MT.may_tu_mau()
kiem("cỗ máy mẫu (đủ năm trạm từ mẫu) — không lỗi, không cảnh báo", not M.soat(mm),
     f"— {[p['message'][:50] for p in M.soat(mm)]}")
goc = json.dumps(mm, sort_keys=True)
#: Hai mẫu ③ chia theo thứ mà trạm ② phải ĐẶT (độ tin cậy, trọng số). Lắp cạnh mẫu ② giao
#: cắt EMA (không đặt thứ đó) thì bộ soát PHẢI cảnh báo — đó là đúng, không phải bẩn.
CAN_TU_2 = {"theo_tin_cay": "tin_cay", "theo_trong_so": "trong_so"}
ban, canh_dung = [], []
for k, ds in MT.MAU.items():
    for d in ds:
        m = MT.ap_mau(mm, k, d["key"])
        vd = M.soat(m)
        if k == T.CHIA_VON and d["key"] in CAN_TU_2:
            canh_dung.append(len(vd) == 1 and vd[0]["severity"] == "warning"
                             and "trạm ② Tín hiệu" in vd[0]["message"])
            for st in m["tram"][T.TIN_HIEU]["steps"]:
                if st.get("type") == "bao":
                    st[CAN_TU_2[d["key"]]] = 0.5
            vd = M.soat(m)
        if vd:
            ban.append((k, d["key"], vd[0]["message"][:70]))
kiem(f"từng mẫu ({sum(len(x) for x in MT.MAU.values())} mẫu) lắp vào cỗ máy mẫu — sạch hết",
     not ban, f"— {ban[:2]}")
kiem("③ theo tin cậy / trọng số cạnh ② không đặt thứ đó → đúng MỘT cảnh báo giữa hai trạm; "
     "② đặt vào là sạch", canh_dung == [True, True])
kiem("mẫu nào cũng có tên, mô tả, và trỏ về mô hình QC tương ứng",
     all(d["ten"] and d["mo_ta"] and d["qc"] for ds in MT.MAU.values() for d in ds))
kiem("lắp mẫu KHÔNG sửa cỗ máy truyền vào (lắp 22 lần, bản gốc y nguyên)",
     json.dumps(mm, sort_keys=True) == goc)

print("\n▸ Đổi mẫu không vặn lại núm")
m = MT.ap_mau(M.may_moi(), T.TIN_HIEU, "giao_cat_ema")
for t in m["tham_so"]:
    if t["ten"] == "ema_nhanh":
        t["gia_tri"] = 9.0
m2 = MT.ap_mau(m, T.TIN_HIEU, "giao_cat_ema")
kiem("lắp lại cùng mẫu: ema_nhanh người chơi chỉnh = 9 vẫn là 9",
     {t["ten"]: t["gia_tri"] for t in m2["tham_so"]}.get("ema_nhanh") == 9.0)
kiem("tham số của mẫu thêm vào bảng, không trùng tên",
     len({t["ten"] for t in m2["tham_so"]}) == len(m2["tham_so"]) == 2)

print("\n▸ Mỗi mẫu tín hiệu phát được tín hiệu, mỗi mẫu khớp lệnh ra được lệnh")
khong_tin_hieu, _dl = [], {}
for d in MT.MAU[T.TIN_HIEU]:
    m = MT.ap_mau(mm, T.TIN_HIEU, d["key"])
    # Khởi động đúng bằng thứ cỗ máy CẦN (SMA 200 nến H1 cần hơn 8 ngày) — đặt cứng 3 ngày là
    # mẫu «Giá trên MA» câm suốt lượt: lỗi thật đã gặp.
    ngay = -(-can_khoi_dong(m) // SG.NGAY_S)
    if ngay not in _dl:
        _dl[ngay] = SG.du_lieu({"A": 8.0, "B": -8.0, "C": 0.0}, ngay + 3, seed=11, nhieu=0.0005)
    bm, _, _ = SG.chay(m, _dl[ngay], bat_dau_t=SG.NGAY + ngay * SG.NGAY_S)
    bao = [v for r in bm.nhat_ky if r.get("tram") == T.TIN_HIEU for v in r.get("viec") or []]
    if not bao:
        khong_tin_hieu.append(d["key"])
kiem("6 mẫu tín hiệu đều phát được tín hiệu trên dữ liệu giả", not khong_tin_hieu,
     f"— câm: {khong_tin_hieu}")
khong_lenh = []
for d in MT.MAU[T.KHOP_LENH]:
    bm, _, yd = SG.chay(MT.ap_mau(mm, T.KHOP_LENH, d["key"]), DL, bat_dau_t=BD)
    if not bm.thong_ke()["so_lenh_khop"]:
        khong_lenh.append(d["key"])
kiem("4 mẫu khớp lệnh đều ra được lệnh và được khớp", not khong_lenh, f"— không lệnh: {khong_lenh}")
khong_chay = []
for k in (T.CHON_MA, T.CHIA_VON, T.RUI_RO):
    for d in MT.MAU[k]:
        try:
            bm, _, _ = SG.chay(MT.ap_mau(mm, k, d["key"]), DL, bat_dau_t=BD)
        except Exception as e:          # noqa: BLE001 — bài kiểm phải nói mẫu nào hỏng
            khong_chay.append((d["key"], str(e)[:60]))
kiem("mọi mẫu ① ③ ④ chạy trọn không lỗi", not khong_chay, f"— {khong_chay}")

# ================= 2. mẫu làm đúng việc =================
print("\n▸ Mẫu làm đúng việc của nó")
DLTK = SG.du_lieu({"A": 0.0, "B": 0.0, "C": 0.0}, 25, seed=2, nhieu=0.0004)
for i, n in enumerate(DLTK["B"]):          # B giao dịch dày gấp 10 lần
    DLTK["B"][i] = n[:5] + (n[5] * 10,)
mtk = MT.ap_mau(mm, T.CHON_MA, "thanh_khoan")
for t in mtk["tham_so"]:
    if t["ten"] == "so_ma":
        t["gia_tri"] = 1.0
bm, _, _ = SG.chay(mtk, DLTK, bat_dau_t=SG.NGAY + 21 * SG.NGAY_S)
g1 = [r["gom"] for r in bm.nhat_ky if r.get("tram") == T.CHON_MA and r.get("gom")]
kiem("N mã thanh khoản nhất (N = 1) → rổ chỉ có B, mã giao dịch dày nhất",
     g1 and all(g["ro"] == ["B"] for g in g1), f"— {[g['ro'] for g in g1]}")
DLM = SG.du_lieu({"A": 6.0, "B": -6.0, "C": 2.0}, 70, seed=4, nhieu=0.0004)
bm, _, _ = SG.chay(MT.ap_mau(mm, T.CHON_MA, "manh_nhat"), DLM, bat_dau_t=SG.NGAY + 62 * SG.NGAY_S)
g1 = [r["gom"] for r in bm.nhat_ky if r.get("tram") == T.CHON_MA and r.get("gom")]
kiem("N mã mạnh nhất → có A (lên mạnh) và C, KHÔNG có B (đang xuống), A đứng đầu",
     g1 and g1[0]["ro"][:1] == ["A"] and "B" not in g1[0]["ro"] and "C" in g1[0]["ro"],
     f"— {g1[0]['ro'] if g1 else None}")

DL4 = SG.du_lieu({"A": 8.0}, 6, seed=5, nhieu=0.0005, sap={"A": (4 * 1440 + 630, -12.0)})
bm, san, _ = SG.chay(MT.ap_mau(mm, T.RUI_RO, "cau_dao"), DL4, bat_dau_t=BD)
kiem("cầu dao tài khoản bật khi cú sập 12% kéo tài khoản sụt quá 10%",
     bm.thong_ke()["dung_tai_khoan"] and not san.tk()["giu"])
bm, _, _ = SG.chay(MT.ap_mau(mm, T.RUI_RO, "khong"), DL4, bat_dau_t=BD)
kiem("không quản rủi ro → ④ không chạy ra việc gì",
     not [r for r in bm.nhat_ky if r.get("tram") == T.RUI_RO and r.get("viec")])

# ================= 3. chữ nhật ký =================
print("\n▸ Chữ «vì sao»")
bm, _, _ = SG.chay(copy.deepcopy(mm), DL, bat_dau_t=BD, den_t=BD + SG.NGAY_S)
doc = DocNhatKy(bm.may)
dong = [doc.chu(r) for r in bm.nhat_ky]
kiem("mọi bản ghi đều dựng được chữ", len(dong) == len(bm.nhat_ky) and all(dong))
r_bao = next(r for r in bm.nhat_ky if r.get("tram") == T.TIN_HIEU and r.get("viec"))
c = doc.chu(r_bao)
kiem("dòng ② có việc: giờ · trạm · mã · đường đi · báo hướng · hạn",
     c.startswith("01-04 ") and "② " in c
     and ("[1]→[1A]→[1A.1]" in c or "[1]→[1B]→[1B.1]" in c)
     and "báo " in c and "hạn tới" in c, f"— {c}")
# Giao cắt EMA có hai nhánh BÙ nhau nên hầu như không lượt nào trượt cả hai — dựng một lượt
# trượt từ lượt thật đã đi nhánh 2: giữ đúng cổng 1A đã trượt (vết thật, con số thật).
r_b = next(r for r in bm.nhat_ky if r.get("tram") == T.TIN_HIEU and len(r.get("cong") or []) == 2
           and not r["cong"][0]["khop"])
r_tr = dict(r_b, viec=[], cong=r_b["cong"][:1], duong=r_b["duong"][:1], ket="het_luot")
c = doc.chu(r_tr)
_v = r_b["cong"][0]["ve"][0]
kiem("dòng ② trượt: «hết lượt tại [1A]» + điều kiện sai kèm con số hai vế",
     "hết lượt tại [1A] · EMA(H1, 20) = " in c and "không > EMA(H1, 50) = " in c
     and f"{_v['trai']:.2f}" in c,
     f"— {c}")
r_g3 = next(r for r in bm.nhat_ky if r.get("tram") == T.CHIA_VON and r.get("gom"))
kiem("dòng Gom ③ liệt kê mục tiêu từng mã", "Gom · mục tiêu:" in doc.chu(r_g3),
     f"— {doc.chu(r_g3)}")
r_g1 = next(r for r in bm.nhat_ky if r.get("tram") == T.CHON_MA and r.get("gom"))
kiem("dòng Gom ① nói rổ gồm gì, mã nào mới vào",
     doc.chu(r_g1).endswith("Gom · rổ: A, B, C · vào: A, B, C"), f"— {doc.chu(r_g1)}")
r_d5 = next(r for r in bm.nhat_ky if r.get("tram") == T.KHOP_LENH and r.get("viec"))
kiem("dòng ⑤ nói đặt lệnh nào, loại gì, bao nhiêu % vốn",
     "đặt L-0001 thị trường +" in doc.chu(r_d5) and "% vốn" in doc.chu(r_d5),
     f"— {doc.chu(r_d5)}")
kiem("dòng khớp lệnh", any("khớp L-0001" in x for x in dong))
lo = doc.lo(bm.nhat_ky, 0, 50, chi_viec=True)
r2_gia_han = [r for r in bm.nhat_ky if r.get("tram") == T.TIN_HIEU and r.get("doi") is False
              and r.get("viec")]
kiem("lô «chỉ dòng có việc» bỏ lượt trượt VÀ lượt ② chỉ gia hạn tín hiệu cũ",
     r2_gia_han and lo["tong"] == sum(
         1 for r in bm.nhat_ky if (r.get("viec") or r.get("gom") or r.get("su_kien"))
         and not (r.get("tram") == T.TIN_HIEU and r.get("doi") is False))
     and all(d["co_viec"] for d in lo["dong"]) and len(lo["dong"]) <= 50,
     f"— {len(r2_gia_han)} lượt gia hạn bị lọc")
kiem("lượt gia hạn khi xem đủ thì ghi rõ «giữ nguyên, gia hạn»",
     doc.chu(r2_gia_han[0]).endswith("(giữ nguyên, gia hạn)"))
r_dn = {"t": SG.NGAY, "tram": T.RUI_RO, "ma": "A", "su_kien": "dung_tai_khoan"}
kiem("dòng sự kiện «dừng cả tài khoản»",
     doc.chu(r_dn) == "01-01 00:00  ④ A  DỪNG CẢ TÀI KHOẢN — bán sạch, thôi giao dịch")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
