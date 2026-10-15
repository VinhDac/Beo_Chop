"""CẦU NỐI QUANTCONNECT CHO CỖ MÁY 5 TRẠM — lớp vỏ `lean/vo_may.py` + đóng gói.  (D-10, 4a)

Chạy ĐÚNG bộ file sẽ gửi lên QC (đóng gói bằng `goi_qc.dong_goi_may`) trong một Python SẠCH —
repo bị gỡ khỏi đường dẫn — với LEAN giả (`tests/lean_gia.py`) làm `AlgorithmImports`. Canh:

  1. **Đóng gói**: dưới trần file của gói Researcher, cỗ máy lỗi bị chặn tại máy, CẤU HÌNH đọc
     được bằng mắt trong `main.py`.
  2. **Khởi động đúng lịch thị trường** và KHÔNG một lệnh nào trước ngày bắt đầu.
  3. **Lệnh**: số lượng đổi từ % vốn, làm tròn theo lô của mã; lệnh thị trường khớp ĐỒNG BỘ mà
     bộ máy vẫn nhận đúng lệnh nào (qua nhãn); lệnh giới hạn làm tròn theo bước giá, hết hạn
     thì huỷ thật trên sàn.
  4. **Bị từ chối** (cổ phiếu đắt, vốn nhỏ → số lượng về 0): bộ máy được báo, KHÔNG đặt lại
     mỗi phút.
  5. **Nhật ký** nằm trong Object Store dưới đúng khoá app đặt, đọc lại được, dựng chữ được;
     vốn cuối trong nhật ký = vốn của sàn.

Chạy:  python tests\\test_vo_may.py
"""
import base64
import gzip
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(HERE)
sys.path.insert(0, GOC)
sys.path.insert(0, HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bo_may as B  # noqa: E402
from cat_studio import goi_qc  # noqa: E402
from cat_studio import may as M  # noqa: E402
from cat_studio import mau_tram as MT  # noqa: E402
from cat_studio import tram as T  # noqa: E402
from cat_studio.nhat_ky_may import DocNhatKy  # noqa: E402
import lean_gia  # noqa: E402
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


def du_lieu(xu, ngay, seed, spread=0.0, gia0=100.0, kl=None):
    dl = SG.du_lieu(xu, ngay, seed=seed, nhieu=0.0005, gia0=gia0)
    return {m: [list(n) + [spread * n[4]] if kl is None else list(n[:5]) + [kl, 0.0]
                for n in ds] for m, ds in dl.items()}


def doc_kho(ra, khoa):
    gz = base64.b64decode(ra["kho"][khoa])
    dong = [json.loads(x) for x in gzip.decompress(gz).decode("utf-8").splitlines()]
    meta = dong[0]
    lenh = [d["lenh"] for d in dong if d.get("loai") == "lenh"]
    luot = [d for d in dong if d.get("loai") == "luot"]
    return meta, lenh, luot


KHOA = "cat_studio/kiem-vo-may.jsonl.gz"
MAY = MT.may_tu_mau("Theo EMA")

# ================= 1. đóng gói =================
print("\n▸ Đóng gói cỗ máy 5 trạm")
CH = {"ma": ["A", "B", "C"], "loai": "forex", "tu": "2024-01-08", "den": "2024-01-12",
      "von": 10000.0, "khoa": KHOA}
files = goi_qc.dong_goi_may(MAY, CH)
kiem("ra main.py + file phụ, mỗi file dưới trần gói Researcher",
     "main.py" in files and all(len(v.encode()) <= goi_qc.GIOI_HAN_RESEARCHER
                                for v in files.values()), f"— {sorted(files)}")
kiem("khối CẤU HÌNH trong main.py đọc được bằng mắt (mã, loại, ngày, vốn, khoá)",
     '"ma": ["A", "B", "C"],' in files["main.py"] and '"loai": "forex",' in files["main.py"]
     and f'"khoa": "{KHOA}",' in files["main.py"])
kiem("đầu main.py ghi tên cỗ máy và vân tay của nó",
     f"cỗ máy «Theo EMA» · vân tay {M.van_tay(MAY)}" in files["main.py"])
try:
    goi_qc.dong_goi_may(M.may_moi(), CH)
    kiem("cỗ máy còn lỗi → không đóng gói", False)
except ValueError as e:
    kiem("cỗ máy còn lỗi → chặn NGAY tại máy, câu nói rõ lỗi đầu tiên", "còn 4 lỗi" in str(e),
         f"— {str(e)[:60]}")

# ================= 2. chạy ngoại hối =================
print("\n▸ Chạy trên LEAN giả — ngoại hối (giá giữa + spread)")
DL = du_lieu({"A": 8.0, "B": -8.0, "C": 0.0}, 12, seed=21, spread=0.0002)
ra, loi = lean_gia.chay_bo_file(files, DL, GOC)
kiem("bộ file chạy trọn trong Python SẠCH (không repo)", ra is not None, f"— {(loi or '')[-300:]}")
if ra is None:
    print(loi)
    sys.exit(1)
can = B.giay_lich_khoi_dong(MAY, "forex")
kiem("khởi động = thời gian cỗ máy cần theo lịch ngoại hối", ra["khoi_dong"] == can,
     f"— {ra['khoi_dong'] / 86400:.1f} ngày")
kiem("sàn OANDA tài khoản margin, mốc so sánh là mã đầu của màn",
     "oanda" in ra["cai"]["san"] and ra["cai"]["moc"] == "A")
meta, lenh, luot = doc_kho(ra, KHOA)
kiem("nhật ký nằm đúng khoá app đặt, dạng cỗ máy 5 trạm, đúng vân tay",
     meta.get("dang") == "may5" and meta.get("van_tay") == M.van_tay(MAY))
t0 = SG.NGAY + 7 * SG.NGAY_S
kiem("KHÔNG lệnh nào trước ngày bắt đầu (khởi động chỉ để nạp chỉ báo)",
     lenh and all(l["t_dat"] >= t0 for l in lenh), f"— {len(lenh)} lệnh")
qc = {o["tag"]: o for o in ra["lenh"]}
khop_dung = [l for l in lenh if l["khop"]
             and abs(sum(k[1] for k in l["khop"]) - qc[l["id"]]["da_khop"]) < 1e-9]
kiem("mọi lệnh bộ máy thấy khớp = đúng lệnh trên sàn, đúng số lượng (lệnh thị trường khớp đồng "
     "bộ mà vẫn tra đúng qua nhãn)",
     khop_dung and len(khop_dung) == sum(1 for l in lenh if l["khop"]),
     f"— {len(khop_dung)} lệnh khớp")
kiem("số lượng là số nguyên (lô ngoại hối = 1 đơn vị)",
     all(float(o["sl"]).is_integer() for o in ra["lenh"]))
kiem("vốn cuối trong nhật ký = vốn của sàn",
     abs(meta["thong_ke"]["von_cuoi"] - ra["von"]) < 1e-6 * ra["von"],
     f"— {meta['thong_ke']['von_cuoi']:.2f} vs {ra['von']:.2f}")
kiem("dòng tổng kết in ra log của QC", any("CAT STUDIO · lãi" in x for x in ra["nhat"]))
doc = DocNhatKy(meta["may"])
kiem("mọi dòng nhật ký dựng được chữ", all(doc.chu(r) for r in luot), f"— {len(luot)} dòng")

# ================= 3. lệnh giới hạn =================
print("\n▸ Lệnh giới hạn: làm tròn bước giá, hết hạn thì huỷ trên sàn")
mgh = MT.ap_mau(MAY, T.KHOP_LENH, "khop_ngay")
for st in mgh["tram"][T.KHOP_LENH]["steps"]:
    if st.get("type") == "lenh_thi_truong":
        st.update(type="lenh_gioi_han", lech_pt=2, het_han=5)
ra2, loi2 = lean_gia.chay_bo_file(goi_qc.dong_goi_may(mgh, dict(CH, den="2024-01-09")), DL, GOC)
kiem("chạy trọn", ra2 is not None, f"— {(loi2 or '')[-300:]}")
if ra2:
    m2, l2, r2 = doc_kho(ra2, KHOA)
    gh = [o for o in ra2["lenh"] if o["kieu"] == "gioi_han"]
    kiem("lệnh giới hạn mang giá đã làm tròn theo bước giá 0.00001",
         gh and all(abs(round(o["gia"] / 0.00001) * 0.00001 - o["gia"]) < 1e-12 for o in gh))
    het = [r for r in r2 if r.get("su_kien") == "huy_lenh" and r.get("ly_do") == "het_han"]
    kiem("cách 2% thì không khớp nổi → hết 5 nến là HUỶ — và huỷ THẬT trên sàn",
         het and {r["lenh_id"] for r in het} <= set(ra2["huy"]), f"— {len(het)} lần")

# ================= 4. bị từ chối =================
print("\n▸ Cổ phiếu đắt, vốn nhỏ: số lượng về 0 → bộ máy được báo, không đặt lại mỗi phút")
DLCP = du_lieu({"A": 8.0, "B": 8.0}, 14, seed=5, gia0=4000.0, kl=1000.0)
CH3 = {"ma": ["A", "B"], "loai": "co_phieu", "tu": "2024-01-11", "den": "2024-01-13",
       "von": 1000.0, "khoa": KHOA}
m3 = MT.ap_mau(MAY, T.CHIA_VON, "chia_deu")
ra3, loi3 = lean_gia.chay_bo_file(goi_qc.dong_goi_may(m3, CH3), DLCP, GOC)
kiem("chạy trọn", ra3 is not None, f"— {(loi3 or '')[-300:]}")
if ra3:
    m3m, l3, r3 = doc_kho(ra3, KHOA)
    tc = [r for r in r3 if r.get("su_kien") == "tu_choi"]
    r3ch = [r for r in r3 if r.get("tram") == T.CHIA_VON and r.get("gom")]
    kiem("1000$ chia đôi cho mã 4000$ → lệnh bị từ chối và bộ máy GHI lý do",
         tc and "làm tròn theo lô" in tc[0]["ly_do"], f"— {len(tc)} lần")
    kiem("…và KHÔNG đặt lại mỗi phút: số lần từ chối ≤ số lần ③ phát mục tiêu × số mã",
         len(tc) <= 2 * len(r3ch), f"— {len(tc)} từ chối / {len(r3ch)} lần ③")
    kiem("không lệnh nào lọt lên sàn", not ra3["lenh"])

# ================= 5. crypto: lô lẻ =================
print("\n▸ Crypto: lô 0,00000001, sàn Coinbase tài khoản tiền mặt")
DLC = du_lieu({"A": 8.0, "B": -4.0}, 12, seed=8, gia0=40000.0, kl=3.0)
CH4 = {"ma": ["A", "B"], "loai": "crypto", "tu": "2024-01-06", "den": "2024-01-09",
       "von": 5000.0, "khoa": KHOA}
ra4, loi4 = lean_gia.chay_bo_file(goi_qc.dong_goi_may(MAY, CH4), DLC, GOC)
kiem("chạy trọn", ra4 is not None, f"— {(loi4 or '')[-300:]}")
if ra4:
    kiem("Coinbase, tài khoản tiền mặt", "coinbase" in ra4["cai"]["san"]
         and "cash" in ra4["cai"]["san"])
    kiem("số lượng lẻ tới 8 chữ số thập phân, không lệnh nào bị từ chối",
         ra4["lenh"] and any(not float(o["sl"]).is_integer() for o in ra4["lenh"])
         and not [r for r in doc_kho(ra4, KHOA)[2] if r.get("su_kien") == "tu_choi"])
    kiem("khởi động theo lịch crypto (24/7) ngắn hơn ngoại hối",
         ra4["khoi_dong"] == B.giay_lich_khoi_dong(MAY, "crypto") < can)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
