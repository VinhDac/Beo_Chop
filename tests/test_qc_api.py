"""NỐI QUANTCONNECT QUA API — trên một máy chủ QC GIẢ: không mạng, không khoá thật.

Máy chủ giả nói đúng giao thức mà LEAN CLI nói (công cụ dòng lệnh chính thức của QC, mã
nguồn mở): xác thực bằng băm, `success / errors`, biên dịch → backtest → Object Store trả
link tải một file zip. Và nó CHẠY THẬT bộ file được đẩy lên, trong một Python sạch như QC
chạy, rồi cất nhật ký vào Object Store dưới đúng khoá mà app tự đặt. Nên "tải về được" ở
đây chứng minh hai điều: bộ file đẩy lên là bộ chạy được, và app với lớp vỏ thống nhất
tên khoá.

Sáu thứ được canh:

  1. **Khoá**: đọc từ biến môi trường, rồi tới `du_lieu/qc_khoa.json`; thiếu hay hỏng →
     một câu tiếng Việt chỉ cách sửa.
  2. **Khoá không bao giờ lộ**: không nằm trong yêu cầu nào gửi đi (chỉ có băm), không
     trong repr, không trong câu lỗi; link tải ký sẵn không nhận header xác thực.
  3. **Một lượt ▶ trọn vẹn**: tạo project → đẩy file → biên dịch → backtest (chờ qua cả
     lúc "xong mà chưa có thống kê") → tải nhật ký qua job → đọc lại được.
  4. **Lượt sau**: dùng lại project, cập nhật file, xoá `nguon_*.py` thừa của lần trước.
  5. **Hỏng chỗ nào nói chỗ đó**: biên dịch, backtest lỗi, lỗi trên cloud về tới người
     dùng nguyên văn, thiếu nhật ký, nhật ký hiện ra trễ, chỉ có bản `.b64`, 5xx một lần
     (thử lại), 500 hai lần, khoá sai, User ID sai, mất mạng, chờ quá hạn.
  6. **`tools/chay_qc.py`**: in tổng kết + boss + link + đường dẫn nhật ký; khoá thiếu
     hay sai → mã thoát 1, một câu tiếng Việt, không traceback; cỗ máy hỏng hay rổ sai →
     báo trước khi gửi gì lên QC.

Chạy:  python tests\\test_qc_api.py
"""
import contextlib
import io
import json
import os
import shutil
import socket
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(TESTS)
sys.path.insert(0, GOC)
sys.path.insert(0, os.path.join(GOC, "lean"))
sys.path.insert(0, os.path.join(GOC, "tools"))
sys.path.insert(0, TESTS)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import chay_qc  # noqa: E402
import qc_gia  # noqa: E402
import san_gia as SG  # noqa: E402
from qc_gia import QCGia, mo  # noqa: E402
from cat_studio import goi_qc  # noqa: E402
from cat_studio import ket_qua_may as KQ  # noqa: E402
from cat_studio import luu_tru  # noqa: E402
from cat_studio import mau_tram as MT  # noqa: E402
from cat_studio import may as M  # noqa: E402
from cat_studio import qc_api  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def bat(f, *a, **k):
    """Lỗi mà `f` ném ra, hoặc None."""
    try:
        f(*a, **k)
    except Exception as e:  # noqa: BLE001
        return e
    return None


XU = {"EURUSD": 6.0, "GBPUSD": -6.0, "USDJPY": 1.0, "AUDUSD": 3.0}


def du_lieu_may(ch):
    """"QC" có dữ liệu cho bất kỳ rổ nào, đủ dài cho khởi động."""
    dl = SG.du_lieu({m: XU.get(m, 0.0) for m in ch["ma"]}, 13, seed=5, nhieu=0.0005)
    return {m: [list(n) + [0.0002 * n[4]] for n in ds] for m, ds in dl.items()}


MAY = MT.may_san("theo_ema")
VT = M.van_tay(MAY)
CH = {"ma": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"], "loai": "forex",
      "tu": "2024-01-08", "den": "2024-01-12", "von": 10_000.0}
#: Khoá MẶC ĐỊNH (không có khoá riêng của lượt) — đường dán tay.
KHOA_NK = f"cat_studio/may-{VT}.jsonl.gz"
TEN_NK_MAC_DINH = os.path.basename(KHOA_NK)[:-len(".gz")]
#: Trần gói Free → HAI file (main.py + nguon_1.py): lượt đầu đi được cả nhánh "chưa có
#: file → create". Lượt sau dùng trần Researcher (một file) — đúng cảnh nâng gói.
FILES = goi_qc.dong_goi_may(MAY, CH, goi_qc.GIOI_HAN)
KHOA_K = f"cat_studio/may-{VT}-{qc_api.ma_luot()}.jsonl.gz"
FILES_K = goi_qc.dong_goi_may(MAY, {**CH, "khoa": KHOA_K}, goi_qc.GIOI_HAN)
CLI = ["--ma", "EURUSD,GBPUSD,USDJPY,AUDUSD", "--loai", "forex",
       "--tu", CH["tu"], "--den", CH["den"]]


def qc_cho(gia, **k):
    return qc_gia.qc_cho(gia, **k)


def cli(argv, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ma = chay_qc.main(argv, **k)
    return ma, buf.getvalue()


# ================= 1. khoá =================
print("\n▸ Khoá: biến môi trường → du_lieu/qc_khoa.json → câu tiếng Việt")
with tempfile.TemporaryDirectory() as td:
    kiem("biến môi trường thắng, bỏ khoảng trắng thừa",
         qc_api.doc_khoa({"QC_USER_ID": " 7 ", "QC_API_TOKEN": "t\n"}, td) == ("7", "t"))
    duong = os.path.join(td, "qc_khoa.json")
    with open(duong, "w", encoding="utf-8") as f:
        json.dump({"user_id": 8, "token": "u"}, f)
    kiem("không có biến môi trường → đọc file", qc_api.doc_khoa({}, td) == ("8", "u"))
    kiem("biến môi trường thiếu một nửa → đọc file, không ghép nửa nọ nửa kia",
         qc_api.doc_khoa({"QC_USER_ID": "7"}, td) == ("8", "u"))
    with open(duong, "w", encoding="utf-8-sig") as f:      # Notepad đời cũ: có BOM
        json.dump({"user_id": "9", "token": "v"}, f)
    kiem("file lưu bằng Notepad (UTF-8 có BOM) vẫn đọc được",
         qc_api.doc_khoa({}, td) == ("9", "v"))
    with open(duong, "w", encoding="utf-8") as f:
        f.write("{hỏng")
    e = bat(qc_api.doc_khoa, {}, td)
    kiem("file hỏng → LoiKhoa chỉ đúng file và dạng đúng",
         isinstance(e, qc_api.LoiKhoa) and "qc_khoa.json" in str(e) and '"user_id"' in str(e))
    os.remove(duong)
    e = bat(qc_api.doc_khoa, {}, td)
    kiem("thiếu khoá → nói đặt ở đâu, và đừng đưa vào git hay chat",
         isinstance(e, qc_api.LoiKhoa) and all(
             s in str(e) for s in ("QC_USER_ID", "QC_API_TOKEN", "qc_khoa.json", "git")))

with open(os.path.join(GOC, ".gitignore"), encoding="utf-8") as f:
    kiem("du_lieu/ (nơi đặt qc_khoa.json) nằm trong .gitignore",
         "du_lieu/" in f.read().split())

# ================= 2. một lượt ▶ trọn vẹn =================
print("\n▸ Một lượt ▶ trọn vẹn trên QC giả (máy chủ chạy THẬT bộ file đẩy lên)")
gia = QCGia(du_lieu_may=du_lieu_may)
qc = qc_cho(gia)
tien_do = []
TD = tempfile.mkdtemp()
try:
    kq = qc_api.chay(qc, MAY, FILES_K, "lượt thử", TD,
                     lambda v, x: tien_do.append((v, x)), khoa=KHOA_K)
except qc_api.LoiQC as e:
    print(f"    (lỗi: {e})")
    kq = None
kiem("chạy trọn không lỗi", kq is not None)
kq = kq or {"meta": {}, "duong_nhat_ky": "", "url": "", "thong_ke_qc": {}}
p = gia.projects[0] if gia.projects else {}
pid = p.get("projectId")
bid = next(iter(gia.backtests), None)
ten_mong = "Cat Studio/" + " ".join(MAY["name"].split())
kiem("tạo project «Cat Studio/<tên cỗ máy>», ngôn ngữ Python",
     len(gia.projects) == 1 and p.get("name") == ten_mong
     and gia.goi("projects/create")[0].get("language") == "Py", f"({p.get('name')})")
fp = gia.files.get(pid, {})
kiem("đẩy đủ bộ file, đúng nội dung; notebook có sẵn của QC để yên",
     {k: v for k, v in fp.items() if k.endswith(".py")} == FILES_K and "research.ipynb" in fp,
     f"({', '.join(FILES_K)})")
kiem("main.py có sẵn → update; nguon_1.py chưa có → create",
     [x["name"] for x in gia.goi("files/update")] == ["main.py"]
     and [x["name"] for x in gia.goi("files/create")] == [k for k in FILES_K if k != "main.py"])
kiem("đọc bằng GET, ghi bằng POST — đúng như LEAN CLI (máy giả từ chối nếu sai)",
     all(pt == ("POST" if d in QCGia.GHI else "GET") for pt, d, _ in gia.nhat))
kiem("backtest mang đúng tên lượt",
     [x.get("backtestName") for x in gia.goi("backtests/create")] == ["lượt thử"])
td_bt = [x for v, x in tien_do if v == "Chạy backtest"]
kiem("báo tiến độ backtest tăng dần tới 100%",
     len(td_bt) >= 3 and td_bt == sorted(td_bt) and td_bt[-1] == 1.0,
     f"({' → '.join(f'{x:.0%}' for x in td_bt)})")
kiem("chờ qua nhịp «completed mà thống kê chưa ghi xong» — không về tay không",
     kq["thong_ke_qc"].get("Total Orders") == "0" and len(gia.goi("backtests/read")) >= 4)
kiem("Object Store bắt chờ job → hỏi lại tới khi có link",
     len([x for x in gia.goi("object/get") if "jobId" in x]) == gia.so_lan_job)
kiem("link tải ký sẵn: KHÔNG gửi kèm header xác thực", gia.auth_tai == [None])
meta = kq["meta"] or {}
duong_nk = kq["duong_nhat_ky"] or ""
kiem("nhật ký nằm trong thư mục nhật ký, tên mang mã RIÊNG của lượt",
     os.path.isfile(duong_nk) and os.path.dirname(duong_nk) == TD
     and os.path.basename(duong_nk) == os.path.basename(KHOA_K)[:-len(".gz")],
     f"({os.path.basename(duong_nk)})")
kiem("khoá riêng: tải xong thì XOÁ khỏi Object Store — cloud không đầy dần",
     KHOA_K not in gia.object_store
     and [x.get("key") for x in gia.goi("object/delete")] == [KHOA_K, KHOA_K + ".b64"])
meta_f, lenh, luot = KQ.doc_file(duong_nk) if os.path.isfile(duong_nk) else ({}, [], [])
kiem("đọc lại được: nguồn QuantConnect, đúng vân tay CỖ MÁY, đủ lượt và lệnh",
     meta_f.get("nguon") == "quantconnect" and meta_f.get("van_tay") == VT
     and len(luot) > 10 and len(lenh) > 0, f"({len(luot)} lượt · {len(lenh)} lệnh)")
k = KQ.KetQuaMay(duong_nk) if os.path.isfile(duong_nk) else None
kiem("dựng được kết quả: thống kê có lãi, boss cả rổ, số lệnh",
     k is not None and "lai_pt" in k.thong_ke and k.thong_ke.get("boss_pt") is not None,
     f"(lãi {k.thong_ke['lai_pt']:+.2f}% · boss {k.thong_ke['boss_pt']:+.2f}%)" if k else "")
kiem("trả link backtest trên web QC",
     bid is not None and kq["url"] == f"https://www.quantconnect.com/project/{pid}/{bid}")

# ================= 3. khoá không lộ =================
print("\n▸ Khoá không bao giờ lộ")
kiem("mọi yêu cầu API đều qua xác thực của máy giả",
     gia.sai_xac_thuc == 0 and len(gia.nhat) > 10, f"({len(gia.nhat)} yêu cầu)")
kiem("token KHÔNG nằm trong yêu cầu nào gửi đi — chỉ có băm của nó",
     all(QCGia.TOK.encode() not in r for r in gia.tho))
kiem("repr(QC) không mang token", QCGia.TOK not in repr(qc) and QCGia.UID in repr(qc))

# ================= 4. lượt sau =================
print("\n▸ Lượt sau (đã nâng Researcher): dùng lại project, dọn file thừa")
FILES_1 = goi_qc.dong_goi_may(MAY, CH, chay_qc.GIOI_HAN_RESEARCHER)
kiem("trần 64 KB của Researcher: cả gói vừa MỘT file main.py", list(FILES_1) == ["main.py"],
     f"({len(FILES_1['main.py'].encode('utf-8')) / 1024:.1f} KB)")
gia.files.setdefault(pid, {})["nguon_2.py"] = "# phần của một lần đóng gói cũ, to hơn\n"
gia.nhat.clear()
e = bat(qc_api.chay, qc, MAY, FILES_1, "lượt hai", TD)
kiem("chạy lại không lỗi", e is None, f"({e})" if e else "")
kiem("không tạo project thứ hai", len(gia.projects) == 1 and not gia.goi("projects/create"))
kiem("file đã có → update, không create",
     [x["name"] for x in gia.goi("files/update")] == ["main.py"]
     and not gia.goi("files/create"))
kiem("nguon_*.py của các lần trước bị xoá hết; file không phải của ta để yên",
     [x["name"] for x in gia.goi("files/delete")] == ["nguon_1.py", "nguon_2.py"]
     and sorted(gia.files[pid]) == ["main.py", "research.ipynb"])

# ================= 5. hỏng chỗ nào nói chỗ đó =================
print("\n▸ Hỏng chỗ nào nói chỗ đó")
gia.bien_dich_hong = True
e = bat(qc_api.chay, qc, MAY, FILES, "x", TD)
gia.bien_dich_hong = False
kiem("biên dịch hỏng → LoiQC kèm mấy dòng log cuối của QC",
     isinstance(e, qc_api.LoiQC) and "biên dịch KHÔNG được" in str(e)
     and "invalid syntax" in str(e))

gia.backtest_loi = ("Runtime Error: division by zero",
                    "Traceback (most recent call last):\n  File \"main.py\", line 9\n"
                    "ZeroDivisionError: division by zero")
e = bat(qc_api.chay, qc, MAY, FILES, "x", TD)
gia.backtest_loi = None
kiem("backtest lỗi → LoiQC: lời lỗi, đuôi vết lỗi, link xem đủ",
     isinstance(e, qc_api.LoiQC) and "Backtest LỖI" in str(e) and "division by zero" in str(e)
     and "line 9" in str(e) and "https://www.quantconnect.com/project/" in str(e))

thieu = {"main.py": FILES["main.py"]}         # quên nguon_1.py → thuật toán chết trên cloud
e = bat(qc_api.chay, qc, MAY, thieu, "x", TD)
kiem("lỗi xảy ra TRÊN CLOUD về tới người dùng nguyên văn tiếng Việt",
     isinstance(e, qc_api.LoiQC) and "Project THIẾU file nguon_1.py" in str(e),
     f"({str(e).splitlines()[0][:60]}…)" if e else "")

ngu = []
gia.chay_that = False
gia.object_store.clear()
qc_ngu = qc_cho(gia, ngu=ngu.append)
gia.nhat.clear()
e = bat(qc_api.chay, qc_ngu, MAY, FILES, "x", TD)
kiem("không có nhật ký → LoiQC nêu khoá, lời QC, link log",
     isinstance(e, qc_api.LoiQC) and KHOA_NK in str(e) and "not found" in str(e)
     and "quantconnect.com/project/" in str(e))
cho = [x for x in ngu if x >= 2]                # nghỉ của hỏi-lại-nhật-ký
kiem("… sau khi đã hỏi lại vài lần, thưa dần (nhật ký có khi hiện ra trễ)",
     cho == [2, 4, 8] and len(gia.goi("object/get")) == 8, f"(nghỉ {cho} giây)")
gia.chay_that = True

ngu.clear()
gia.object_tre = 3
e = bat(qc_api.chay, qc_ngu, MAY, FILES, "x", TD)
kiem("nhật ký hiện ra trễ → chờ rồi vẫn lấy được", e is None and gia.object_tre == 0
     and [x for x in ngu if x >= 2] == [2, 4], f"({e})" if e else "")

gia.object_store.clear()
gia.chi_b64 = True
TD2 = tempfile.mkdtemp()
e = bat(qc_api.chay, qc, MAY, FILES, "x", TD2)
gia.chi_b64 = False
kiem("chỉ có bản chữ .b64 (save_bytes hỏng trên QC) → vẫn ra đúng nhật ký",
     e is None and list(gia.object_store) == [KHOA_NK + ".b64"]
     and len(KQ.doc_file(os.path.join(TD2, TEN_NK_MAC_DINH))[2]) == len(luot))

gia.ma_loi["projects/read"] = [503]
gia.nhat.clear()
e = bat(qc.tim_project, "không có")
kiem("5xx một lần → thử lại đúng một lần, êm", e is None
     and len(gia.goi("projects/read")) == 2)
gia.ma_loi["projects/read"] = [500, 500]
e = bat(qc.tim_project, "không có")
kiem("500 hai lần liền → LoiKhoa (LEAN CLI coi đó là khoá sai)",
     isinstance(e, qc_api.LoiKhoa) and "500" in str(e))
gia.ma_loi["projects/read"] = [502, 502]
e = bat(qc.tim_project, "không có")
kiem("5xx khác hai lần → LoiQC nêu mã, không đổ cho khoá",
     isinstance(e, qc_api.LoiQC) and not isinstance(e, qc_api.LoiKhoa) and "502" in str(e))

GIA_MAO = "tok-gia-mao-987654"
kiem("kiem_khoa: khoá đúng → được; sai → LoiKhoa, không lộ token",
     qc.kiem_khoa() is True
     and isinstance(bat(qc_cho(gia, tok=GIA_MAO).kiem_khoa), qc_api.LoiKhoa)
     and GIA_MAO not in str(bat(qc_cho(gia, tok=GIA_MAO).kiem_khoa)))
e = bat(qc_api.chay, qc_cho(gia, tok=GIA_MAO), MAY, FILES, "x", TD)
kiem("token sai → LoiKhoa tiếng Việt, câu lỗi không chứa token",
     isinstance(e, qc_api.LoiKhoa) and "Khoá QuantConnect SAI" in str(e)
     and GIA_MAO not in str(e))
e = bat(qc_api.chay, qc_cho(gia, uid="999"), MAY, FILES, "x", TD)
kiem("User ID sai → LoiKhoa nói đúng là User ID",
     isinstance(e, qc_api.LoiKhoa) and "User ID" in str(e))

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    cong_chet = s.getsockname()[1]
q = qc_api.QC("1", "t", goc=f"http://127.0.0.1:{cong_chet}/api/v2", mo=mo, timeout=5)
e = bat(q.get, "projects/read")
kiem("mất mạng → LoiQC «Không kết nối được», không phải traceback",
     isinstance(e, qc_api.LoiQC) and not isinstance(e, qc_api.LoiKhoa)
     and "Không kết nối được" in str(e))

dong_ho = [0.0]
q = qc_cho(gia, ngu=lambda s: dong_ho.__setitem__(0, dong_ho[0] + s), gio=lambda: dong_ho[0])
gia.bien_dich_treo = True
gia.nhat.clear()
e = bat(q.bien_dich, pid, han_giay=60)
gia.bien_dich_treo = False
n_hoi = len(gia.goi("compile/read"))
kiem("chờ quá hạn → LoiQC nói chờ gì, bao lâu",
     isinstance(e, qc_api.LoiQC) and "biên dịch quá 1 phút" in str(e))
kiem("… và hỏi thưa dần như LEAN CLI, không dội máy chủ", 20 < n_hoi < 40,
     f"({n_hoi} lần trong 60 giây)")

# ================= 6. công cụ dòng lệnh =================
print("\n▸ tools/chay_qc.py — chạy một cỗ máy bằng dòng lệnh")
gia.nhat.clear()
ma, ra = cli(CLI, qc=qc, thu_muc_nhat_ky=TD)
kiem("chạy xong → mã thoát 0, in «XONG»", ma == 0 and "✔ XONG" in ra, ra[-200:] if ma else "")
kiem("in rổ mã, vốn đầu–cuối, boss cả rổ và số lệnh",
     all(s in ra for s in ("rổ: EURUSD, GBPUSD", "Vốn ", "Boss «mua rồi giữ cả rổ»",
                           "Lệnh:")))
kiem("in từng bước, có tiến độ backtest",
     all(s in ra for s in ("Tìm project", "Tải file lên QC", "Biên dịch",
                           "Chạy backtest 100%", "Tải nhật ký về")))
duong_in = ra.split("Nhật ký     : ")[-1].strip() if "Nhật ký     : " in ra else ""
kiem("in link QC và đường dẫn nhật ký (khoá riêng của lượt, đã tải về)",
     "Xem trên QC : https://www.quantconnect.com/project/" in ra
     and os.path.dirname(duong_in) == TD and os.path.isfile(duong_in)
     and duong_in != os.path.join(TD, TEN_NK_MAC_DINH))
kiem("không in token", QCGia.TOK not in ra)

ma, ra = cli(["--man", "ro-ngoai-hoi-2024"], qc=qc, thu_muc_nhat_ky=TD)
kiem("--man lấy đúng rổ và khoảng ngày của màn Chiến dịch",
     ma == 0 and "rổ: EURUSD, GBPUSD, USDJPY, AUDUSD" in ra and "2024-01-01 → 2024-12-31" in ra)

ma, ra = cli(CLI, qc=qc_cho(gia, tok=GIA_MAO), thu_muc_nhat_ky=TD)
kiem("khoá sai → mã thoát 1, một câu tiếng Việt, không traceback, không lộ khoá",
     ma == 1 and "✘ Khoá QuantConnect SAI" in ra and "Traceback" not in ra
     and GIA_MAO not in ra)

cu_mt = {k: os.environ.pop(k) for k in ("QC_USER_ID", "QC_API_TOKEN") if k in os.environ}
cu_goc = luu_tru.goc
with tempfile.TemporaryDirectory() as td:
    luu_tru.goc = lambda: td
    try:
        ma, ra = cli(CLI)
    finally:
        luu_tru.goc = cu_goc
        os.environ.update(cu_mt)
kiem("thiếu khoá → mã thoát 1, chỉ cách đặt khoá, chưa đóng gói gì",
     ma == 1 and "Chưa có khoá QuantConnect" in ra and "gói:" not in ra)

gia3 = QCGia(du_lieu_may=du_lieu_may)
with tempfile.TemporaryDirectory() as td:
    duong = os.path.join(td, "trang.json")
    with open(duong, "w", encoding="utf-8") as f:
        json.dump(M.may_moi("Cỗ máy trắng"), f, ensure_ascii=False)
    ma, ra = cli([duong] + CLI, qc=qc_cho(gia3), thu_muc_nhat_ky=td)
    kiem("cỗ máy còn lỗi → báo ngay trên máy, CHƯA gửi gì lên QC",
         ma == 1 and "Cỗ máy còn" in ra and "lỗi" in ra and gia3.nhat == [])
    duong2 = os.path.join(td, "khong_phai.json")
    with open(duong2, "w", encoding="utf-8") as f:
        json.dump({"name": "sơ đồ cũ", "entry": {"steps": []}}, f, ensure_ascii=False)
    ma, ra = cli([duong2] + CLI, qc=qc_cho(gia3), thu_muc_nhat_ky=td)
    kiem("file không phải cỗ máy 5 trạm → nói thẳng, không đoán",
         ma == 1 and "không phải cỗ máy 5 trạm" in ra)
ma, ra = cli([os.path.join(TD, "khong_co.json")] + CLI, qc=qc_cho(gia3), thu_muc_nhat_ky=TD)
kiem("file không có → nói đọc không được", ma == 1 and "Đọc cỗ máy không được" in ra)
ma, ra = cli(["--tu", "2025-13-01"], qc=qc_cho(gia3), thu_muc_nhat_ky=TD)
ma2, ra2 = cli(["--tu", "2025-03-01", "--den", "2025-02-01"], qc=qc_cho(gia3),
               thu_muc_nhat_ky=TD)
ma3, ra3 = cli(["--ma", "EUR USD"], qc=qc_cho(gia3), thu_muc_nhat_ky=TD)
kiem("ngày gõ sai, từ-sau-đến, mã sai dạng → báo ngay, CHƯA gửi gì lên QC",
     ma == 1 and "YYYY-MM-DD" in ra and ma2 == 1 and "SAU" in ra2
     and ma3 == 1 and "không hợp lệ" in ra3 and gia3.nhat == [])

for g in (gia, gia3):
    g.dong()
shutil.rmtree(TD, ignore_errors=True)
shutil.rmtree(TD2, ignore_errors=True)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
