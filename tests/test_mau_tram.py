"""MẪU DỰNG SẴN — 22 mẫu từng trạm và 4 cỗ máy dựng sẵn.  (D-10)

Canh: mẫu nào mở ra cũng SẠCH (không lỗi, không cảnh báo), lắp mẫu không vặn lại núm
người chơi đã chỉnh, và bốn cỗ máy dựng sẵn là bốn cỗ máy KHÁC NHAU thật.

⚠ Phần "mẫu có chạy ra lệnh không" đã bỏ cùng bộ mô phỏng tại máy (D-11): từ nay chỉ
QuantConnect chạy, nên câu hỏi đó chỉ trả lời được bằng một lượt chạy thật trên QC.
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

dung = sai = 0


def bat_loi(f, *a):
    try:
        f(*a)
    except Exception as e:          # noqa: BLE001
        return e
    return None


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")



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

print("\n▸ Bốn cỗ máy dựng sẵn của chương 1 (D-10, phần 6)")
ban_san = []
for d in MT.MAY_SAN:
    ms = MT.may_san(d["key"])
    vd = M.soat(ms)
    if vd:
        ban_san.append((d["key"], vd[0]["message"][:60]))
kiem("mọi cỗ máy dựng sẵn mở ra SẠCH — không lỗi, không cảnh báo", not ban_san,
     f"— {ban_san}")
kiem("bốn ý tưởng KHÁC NHAU: không hai cỗ máy nào trùng vân tay",
     len({M.van_tay(MT.may_san(d["key"])) for d in MT.MAY_SAN}) == len(MT.MAY_SAN),
     f"({len(MT.MAY_SAN)} cỗ máy)")
kiem("mỗi cái có tên và một câu nói đúng việc nó làm",
     all(d["ten"] and len(d["mo_ta"]) > 40 for d in MT.MAY_SAN))
kiem("cỗ máy dựng sẵn không có → KeyError gọi tên khoá",
     isinstance(bat_loi(MT.may_san, "khong-co"), KeyError))

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

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
