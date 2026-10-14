"""CẦU NỐI QuantConnect — bộ luật y hệt, chỉ thay ống nước.  (slice 2a · D-01…D-04)

Sáu thứ được canh:

  1. **ĐỐI CHIẾU**: cùng nến, cùng giá trị chỉ báo → nhật ký, sổ lệnh, bảng tổng kết của
     cầu nối TRÙNG KHÍT bộ chạy cũ, tới từng byte. Ba bộ dữ liệu giả — và bài tự kiểm là
     ba bộ đó đi ĐỦ mọi nhánh của sơ đồ mẫu, không thì "trùng khít" chẳng chứng minh gì.
  2. **Hai nến trục cùng đóng một nhịp** → cầu nối chạy Entry cho CẢ HAI. Bộ cũ bỏ sót
     cây trước — khác biệt CỐ Ý, ghi ở đầu `lean/cat_lean.py`.
  3. **Spread sống**: mọi chỗ đọc spread đọc đúng spread của nến hiện tại.
  4. **Khung H4/D1 bị chặn** TRƯỚC khi chạy, kèm lý do.
  5. **Nhật ký nén** mở lại được bằng chính `nhat_ky.doc_file` của app.
  6. **Gói dán lên QC**: mỗi file dưới trần 32 KB của gói Free; "làm gọn" không đổi code
     và giữ số dòng; nạp trong một Python SẠCH (không có repo) thì bộ luật nhúng cho ra
     ĐÚNG nhật ký như bộ luật trong repo; dán lệch lần đóng gói thì báo ngay.

Chạy:  python tests\\test_cat_lean.py
"""
import ast
import copy
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(TESTS)
sys.path.insert(0, GOC)
sys.path.insert(0, os.path.join(GOC, "lean"))
sys.path.insert(0, os.path.join(GOC, "tools"))
sys.path.insert(0, TESTS)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

import cat_lean as cl  # noqa: E402
import dong_goi_lean as dg  # noqa: E402
import gia_lap_qc as gl  # noqa: E402
from cat_studio import bo_chay as bc  # noqa: E402
from cat_studio import core  # noqa: E402
from cat_studio import mau  # noqa: E402
from cat_studio import nhat_ky as nk  # noqa: E402
from cat_studio import so_lenh as sl  # noqa: E402
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


def gan(a, b, e=1e-9):
    return a is not None and abs(float(a) - float(b)) <= e


def van_tay(x):
    return hashlib.sha1(json.dumps(x, sort_keys=True, ensure_ascii=False)
                        .encode("utf-8")).hexdigest()


DOC = mau.so_do_mau()
CD = bc.CaiDat(spread_diem=20.0, point=0.01)
SPREAD = CD.spread_gia

# ================= 1. đối chiếu =================
print("\n▸ Đối chiếu với bộ chạy cũ — cùng nến, cùng giá trị chỉ báo")
phu = {"viec": set(), "ly_do": set(), "mo_ho": 0, "tre": 0}
p = None
for seed in (1, 3, 7):
    nen1 = gl.du_lieu(np, seed=seed, ngay=12)
    kq = bc.chay(DOC, nen1, CD)
    p = gl.chay_qc(cl, core, tt, DOC, nen1, SPREAD)
    kiem(f"bộ {seed}: nhật ký trùng khít từng lượt",
         van_tay(kq.nhat_ky) == van_tay(p.nhat_ky), f"({len(p.nhat_ky)} lượt)")
    kiem(f"bộ {seed}: sổ lệnh trùng khít",
         [x.tom_tat() for x in kq.so.lenh] == [x.tom_tat() for x in p.so.lenh],
         f"({len(p.so.lenh)} lệnh)")
    kiem(f"bộ {seed}: bảng tổng kết trùng khít", kq.thong_ke == p.thong_ke)
    for r in kq.nhat_ky:
        for v in r["viec"]:
            phu["viec"].add(v["loai"] + ":" + str(v.get("huong") or v.get("che_do") or ""))
    phu["ly_do"] |= {x.ly_do_dong for x in kq.so.lenh}
    phu["mo_ho"] += kq.thong_ke["nen_mo_ho"]
    phu["tre"] += p.dem["entry_tre"]
kiem("ba bộ đi đủ hành động: đặt mua · đặt bán · dời hoà vốn · huỷ lệnh chờ",
     {"lenh_dat:mua", "lenh_dat:ban", "lenh_sua:hoa_von", "lenh_huy:"} <= phu["viec"],
     f"({sorted(phu['viec'])})")
kiem("… đủ cách đóng: chốt lời · cắt lỗ", {"tp", "sl"} <= phu["ly_do"])
kiem("… có nến mơ hồ và Entry chạy trễ (phút cuối ô bị thủng)",
     phu["mo_ho"] > 0 and phu["tre"] > 0, f"(mơ hồ {phu['mo_ho']} · trễ {phu['tre']})")

# ================= 2. hai nến trục cùng đóng =================
print("\n▸ Hai nến trục cùng đóng trong một nhịp M1")
# 09:00–10:29, thủng 10:04–10:08: ô 10:00 mất phút cuối, và phút kế tiếp có mặt là
# 10:09 — phút CUỐI của ô 10:05. Nhịp 10:09 vì thế khép cả hai ô một lúc.
t0 = 1735808400
phut = [m for m in range(90) if not 64 <= m <= 68]
nen1 = np.empty(len(phut), dtype=gl.DTYPE)
nen1["t"] = [t0 + m * 60 for m in phut]
for cot in ("o", "h", "l", "c"):
    nen1[cot] = [2000.0 + 0.01 * (m % 7) for m in phut]
nen1["vol"] = 1
n5 = len(tt.gop(nen1, "M5"))
kq = bc.chay(DOC, nen1, CD)
p2 = gl.chay_qc(cl, core, tt, DOC, nen1, SPREAD)
truc_cu = [r["nen"] for r in kq.nhat_ky if r["tab"] == core.TAB_ENTRY]
truc_moi = [r["nen"] for r in p2.nhat_ky if r["tab"] == core.TAB_ENTRY]
kiem("bộ cũ bỏ sót đúng một nến trục: ô 10:00 (mất phút cuối)",
     sorted(set(range(n5)) - set(truc_cu)) == [12], f"({n5} nến trục)")
kiem("cầu nối chạy Entry ĐÚNG MỘT lượt cho MỌI nến trục, theo thứ tự",
     truc_moi == list(range(n5)))
kiem("ô đó được ghi là chạy trễ", p2.dem["entry_tre"] >= 1)

# ================= 3. spread sống =================
print("\n▸ Spread sống")
p3 = cl.PhienQC(DOC, cl.CaiDatQC())
p3.mot_nhip(t0 + 60, 100.0, 101.0, 99.0, 100.0, 0.37, 100.37)
kiem("spread của nến hiện tại vào đúng cửa `spread_gia`", gan(p3.cd.spread_gia, 0.37))
kiem("Ask là Ask THẬT của nến, Bid là close Bid", gan(p3.ctx.ask, 100.37) and gan(p3.ctx.bid, 100.0))
ban = sl.Lenh("L-0001", None, 0, sl.BAN, "stop", 0.01, 101.0, 102.0, 99.0, 1.0, 0)
p3.so.khop(ban, 101.0, 0)
kiem("lệnh BÁN thoát ở Ask THẬT (`_gia_thoat` đọc cùng một cửa)",
     gan(bc._gia_thoat(ban, p3.ctx.bid, p3.cd), 100.37))
p3.mot_nhip(t0 + 120, 100.0, 100.0, 100.0, 100.0, -0.2, None)
kiem("spread âm (dữ liệu hỏng) bị chặn về 0, Ask = Bid", gan(p3.cd.spread_gia, 0.0)
     and gan(p3.ctx.ask, 100.0))

# ================= 4. khung chưa hỗ trợ =================
print("\n▸ Khung chưa chạy được trên QC — chặn TRƯỚC khi chạy")


def thu(doc):
    try:
        cl.PhienQC(doc)
    except bc.LoiChay as e:
        return str(e)
    return ""


d = copy.deepcopy(DOC)
for st in d["entry"]["steps"]:
    for c in st.get("conditions") or []:
        for o in (c.get("trai"), c.get("phai")):
            if isinstance(o, dict) and o.get("ten") in ("ma", "close"):
                o["tf"] = "H4"
loi = thu(d)
kiem("chỉ báo trên H4 → LoiChay nói rõ vì múi giờ", "múi giờ" in loi, f"({loi[:70]}…)")
d = copy.deepcopy(DOC)
for st in d["entry"]["steps"]:
    if core.is_start_step(st):
        st["nhip"] = "D1"
loi = thu(d)
kiem("nhịp Entry D1 → LoiChay trước khi chạy", "D1" in loi, f"({loi[:70]}…)")

# ================= 5. nhật ký nén =================
print("\n▸ Nhật ký nén mở lại được bằng app")
gz = p.nhat_ky_gz()
with tempfile.TemporaryDirectory() as td:
    duong = os.path.join(td, "qc.jsonl")
    with open(duong, "wb") as f:
        f.write(gzip.decompress(gz))
    meta, lenh, luot = nk.doc_file(duong)
kiem("`nhat_ky.doc_file` đọc được, meta ghi nguồn QuantConnect",
     meta.get("nguon") == "QuantConnect")
kiem("đủ lệnh, đủ lượt", len(lenh) == len(p.so.lenh) and len(luot) == p.so_luot,
     f"({len(lenh)} lệnh · {len(luot)} lượt)")
kiem("lượt đọc lại == lượt đã ghi",
     [{k: v for k, v in r.items() if k != "loai"} for r in luot] == p.nhat_ky)
kiem("meta mang bảng tổng kết và vân tay sơ đồ",
     meta["thong_ke"] == p.thong_ke and meta["van_tay"] == nk._van_tay(p.doc))
kiem("nén nhỏ hơn ít nhất 5 lần", len(gz) * 5 < p.byte_tho,
     f"({p.byte_tho / 1e3:.0f} KB → {len(gz) / 1e3:.0f} KB)")

# ================= 6. gói dán lên QC =================
print("\n▸ Gói dán lên QuantConnect")
files = dg.dong_goi(DOC)
co = {k: len(v.encode("utf-8")) for k, v in files.items()}
kiem("mỗi file dưới trần của gói Free", all(n <= dg.GIOI_HAN for n in co.values()), f"({co})")
loi_cu_phap = []
for ten, nd in files.items():
    try:
        ast.parse(nd)
    except SyntaxError as e:
        loi_cu_phap.append(f"{ten}: {e}")
kiem("file nào cũng đúng cú pháp Python", not loi_cu_phap, str(loi_cu_phap))
files_b = dg.dong_goi(DOC, gioi_han=dg.GIOI_HAN - 2000)    # cùng nguồn, CHIA khác chỗ
kiem("chia khác chỗ → mã gói khác (không ghép nhầm được file của hai lần chia)",
     files_b["main.py"].split('_MA = "')[1][:10] != files["main.py"].split('_MA = "')[1][:10])


def _cay(code, doc_thanh_pass):
    cay = ast.parse(code)
    for n in ast.walk(cay):
        if doc_thanh_pass and isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                             ast.AsyncFunctionDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                b[0] = ast.copy_location(ast.Pass(), b[0])
    return cay


def _dong(cay):
    return [(type(n).__name__.replace("Pass", "Expr"), n.lineno)
            for n in ast.walk(cay) if isinstance(n, ast.stmt)]


nguon = dg.doc_nguon()
kiem("làm gọn KHÔNG đổi code: AST trùng khít (chỉ docstring → pass)",
     all(ast.dump(_cay(v, True)) == ast.dump(_cay(dg.gon(v), False))
         for v in nguon.values()))
kiem("làm gọn GIỮ số dòng mọi câu lệnh — lỗi trên QC chỉ đúng dòng trong repo",
     all(_dong(_cay(v, True)) == _dong(_cay(dg.gon(v), False)) for v in nguon.values()))

KICH_BAN = r'''
import json, sys
sys.path[:] = [p for p in sys.path if not p.startswith(GOC)]
import numpy as np
import AlgorithmImports
import main
import gia_lap_qc as gl
cl = sys.modules["cat_lean"]
vo = sys.modules["vo_qc"]
nen1 = np.array([tuple(r) for r in json.load(open("nen.json"))], dtype=gl.DTYPE)
p = gl.chay_qc(cl, sys.modules["cat_studio.core"], sys.modules["cat_studio.tinh_toan"],
               vo.SO_DO, nen1, SPREAD)
mod = [m for m in sys.modules if m == "cat_lean" or m == "vo_qc" or m.startswith("cat_studio")]
print(json.dumps({
    "tu_goi": all(sys.modules[m].__file__.startswith("<cat_studio>") for m in mod),
    "so_module": len(mod),
    "lop": issubclass(main.CatStudioTrenQC, AlgorithmImports.QCAlgorithm),
    "cau_hinh": vo.CAU_HINH is main.CAU_HINH_NHUNG,
    "so_do": vo.SO_DO, "luot": p.nhat_ky, "lenh": [x.tom_tat() for x in p.so.lenh],
    "thong_ke": p.thong_ke}, ensure_ascii=False))
'''


def chay_sach(td):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run([sys.executable, "kich_ban.py"], cwd=td, capture_output=True,
                          text=True, encoding="utf-8", env=env, timeout=300)


with tempfile.TemporaryDirectory() as td:
    for ten, nd in files.items():
        with open(os.path.join(td, ten), "w", encoding="utf-8") as f:
            f.write(nd)
    shutil.copy(os.path.join(TESTS, "gia_lap_qc.py"), td)
    with open(os.path.join(td, "AlgorithmImports.py"), "w", encoding="utf-8") as f:
        f.write("class QCAlgorithm:\n    pass\n")
    nen1 = gl.du_lieu(np, seed=1, ngay=6)
    with open(os.path.join(td, "nen.json"), "w", encoding="utf-8") as f:
        json.dump(nen1.tolist(), f)
    with open(os.path.join(td, "kich_ban.py"), "w", encoding="utf-8") as f:
        f.write(f"GOC = {GOC!r}\nSPREAD = {SPREAD!r}\n" + KICH_BAN)
    r = chay_sach(td)
    ra = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {}
    if r.returncode:
        print(r.stderr[-1500:])
    p6 = gl.chay_qc(cl, core, tt, DOC, nen1, SPREAD)
    kiem("nạp được trong Python SẠCH — mọi module cat_studio đều lấy từ GÓI, không từ repo",
         ra.get("tu_goi") is True and ra.get("so_module", 0) >= 14,
         f"({ra.get('so_module')} module)")
    kiem("QC thấy đúng một lớp thuật toán, con của QCAlgorithm", ra.get("lop") is True)
    kiem("khối CẤU HÌNH ở đầu main.py đi thẳng vào lớp vỏ", ra.get("cau_hinh") is True)
    kiem("sơ đồ trong gói == sơ đồ đã chuẩn hoá",
         ra.get("so_do") == json.loads(json.dumps(core.normalize_process(DOC))))
    kiem("bộ luật TRONG GÓI cho ra đúng nhật ký như bộ luật trong repo",
         ra.get("luot") == json.loads(json.dumps(p6.nhat_ky)), f"({len(p6.nhat_ky)} lượt)")
    kiem("… đúng sổ lệnh, đúng bảng tổng kết",
         ra.get("lenh") == json.loads(json.dumps([x.tom_tat() for x in p6.so.lenh]))
         and ra.get("thong_ke") == json.loads(json.dumps(p6.thong_ke)))

    # Dán lệch: nguon_1.py của một lần đóng gói khác.
    d1 = os.path.join(td, "nguon_1.py")
    with open(d1, encoding="utf-8") as f:
        nd = f.read()
    with open(d1, "w", encoding="utf-8") as f:
        f.write(nd.replace('MA = "', 'MA = "x', 1))
    r = chay_sach(td)
    kiem("dán lệch lần đóng gói → báo ngay, chỉ đúng file và cách sửa",
         r.returncode != 0 and "nguon_1.py không cùng lần đóng gói" in r.stderr
         and "dán lại CẢ BỘ" in r.stderr)

    # Quên tạo file phụ — lỗi gặp THẬT lần chạy đầu trên QC: câu tiếng Anh "No module
    # named 'nguon_1'" không nói phải làm gì.
    os.remove(d1)
    r = chay_sach(td)
    kiem("thiếu file phụ → báo tiếng Việt: thiếu file nào, đặt tên ra sao, dán gì",
         r.returncode != 0 and "Project THIẾU file nguon_1.py" in r.stderr
         and "đặt tên ĐÚNG" in r.stderr)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
