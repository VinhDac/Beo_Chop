"""NỐI QUANTCONNECT QUA API — trên một máy chủ QC GIẢ: không mạng, không khoá thật.  (slice 3 · D-06)

Máy chủ giả nói đúng giao thức mà LEAN CLI nói (công cụ dòng lệnh chính thức của QC, mã
nguồn mở): xác thực bằng băm, `success / errors`, biên dịch → backtest → Object Store trả
link tải một file zip. Và nó CHẠY THẬT bộ file được đẩy lên, trong một Python sạch như QC
chạy, rồi cất nhật ký vào Object Store dưới đúng khoá mà CẦU NỐI tự đặt. Nên "tải về
được" ở đây chứng minh hai điều: bộ file đẩy lên là bộ chạy được, và app với cầu nối
thống nhất tên khoá.

Sáu thứ được canh:

  1. **Khoá**: đọc từ biến môi trường, rồi tới `du_lieu/qc_khoa.json`; thiếu hay hỏng →
     một câu tiếng Việt chỉ cách sửa.
  2. **Khoá không bao giờ lộ**: không nằm trong yêu cầu nào gửi đi (chỉ có băm), không
     trong repr, không trong câu lỗi; link tải ký sẵn không nhận header xác thực.
  3. **Một lượt ▶ trọn vẹn**: tạo project → đẩy file → biên dịch → backtest (chờ qua cả
     lúc "xong mà chưa có thống kê") → tải nhật ký qua job → mở bằng `nhat_ky.doc_file`,
     đúng từng lượt như chạy cầu nối ngay tại máy.
  4. **Lượt sau**: dùng lại project, cập nhật file, xoá `nguon_*.py` thừa của lần trước.
  5. **Hỏng chỗ nào nói chỗ đó**: biên dịch, backtest lỗi, lỗi trên cloud về tới người
     dùng nguyên văn, thiếu nhật ký, nhật ký hiện ra trễ, chỉ có bản `.b64`, 5xx một lần
     (thử lại), 500 hai lần, khoá sai, User ID sai, mất mạng, chờ quá hạn.
  6. **`tools/chay_qc.py`**: in tổng kết + link + đường dẫn nhật ký; khoá thiếu hay sai →
     mã thoát 1, một câu tiếng Việt, không traceback; sơ đồ hỏng → báo trước khi gửi gì.

Chạy:  python tests\\test_qc_api.py
"""
import base64
import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TESTS = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(TESTS)
sys.path.insert(0, GOC)
sys.path.insert(0, os.path.join(GOC, "lean"))
sys.path.insert(0, os.path.join(GOC, "tools"))
sys.path.insert(0, TESTS)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

import cat_lean as cl  # noqa: E402
import chay_qc  # noqa: E402
import dong_goi_lean as dg  # noqa: E402
import gia_lap_qc as gl  # noqa: E402
from cat_studio import bo_chay as bc  # noqa: E402
from cat_studio import core  # noqa: E402
from cat_studio import luu_tru  # noqa: E402
from cat_studio import mau  # noqa: E402
from cat_studio import nhat_ky as nk  # noqa: E402
from cat_studio import qc_api  # noqa: E402
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


def bat(f, *a, **k):
    """Lỗi mà `f` ném ra, hoặc None."""
    try:
        f(*a, **k)
    except Exception as e:  # noqa: BLE001
        return e
    return None


DOC = mau.so_do_mau()
SPREAD = bc.CaiDat(spread_diem=20.0, point=0.01).spread_gia
NEN1 = gl.du_lieu(np, seed=1, ngay=4)
DOC_CHUAN = core.normalize_process(DOC)
KHOA_NK = nk.khoa_qc(DOC_CHUAN)
TU_DEN = ["--tu", "2025-01-02", "--den", "2025-01-06"]

#: Kịch bản "QC chạy thuật toán": Python sạch — repo bị gỡ khỏi sys.path, chỉ còn bộ file
#: của project — nạp `main.py` y như QC nạp, chạy cầu nối trên nến giả, cất nhật ký.
KICH_BAN = r'''
import json, sys
sys.path[:] = [p for p in sys.path if not p.startswith(GOC)]
import numpy as np
import main
import gia_lap_qc as gl
cl = sys.modules["cat_lean"]
vo = sys.modules["vo_qc"]
nen1 = np.array([tuple(r) for r in json.load(open("nen.json"))], dtype=gl.DTYPE)
p = gl.chay_qc(cl, sys.modules["cat_studio.core"], sys.modules["cat_studio.tinh_toan"],
               vo.SO_DO, nen1, SPREAD)
with open("ra.gz", "wb") as f:
    f.write(p.nhat_ky_gz())
print(p.ten_file())
'''

#: Mở URL KHÔNG qua proxy — máy chủ giả nằm ở 127.0.0.1, proxy của máy (nếu có) không
#: được chen vào giữa.
_MO = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def mo(req, timeout):
    return _MO.open(req, timeout=timeout)


class QCGia:
    """Máy chủ QuantConnect GIẢ trên 127.0.0.1 — đúng những điểm API mà app dùng."""

    UID, TOK, ORG = "424242", "khoa-bi-mat-0123456789abcdef", "org-cat"
    GHI = {"projects/create", "files/create", "files/update", "files/delete",
           "compile/create", "backtests/create", "object/get"}

    def __init__(self):
        self.projects, self.files, self.compiles, self.backtests = [], {}, {}, {}
        self.object_store, self.tai_ve, self.jobs = {}, {}, {}
        self.nhat = []                  # (phương thức, điểm, tham số) mọi yêu cầu API
        self.tho = []                   # bytes thô mọi yêu cầu: dòng đầu + header + thân
        self.auth_tai = []              # header Authorization mà link tải nhận được
        self.sai_xac_thuc = 0
        self.ma_loi = {}                # điểm → các mã HTTP trả TRƯỚC khi trả thật
        self.bien_dich_hong = self.bien_dich_treo = False
        self.backtest_loi = None        # (error, stacktrace)
        self.chay_that = True           # backtest có chạy bộ file và cất nhật ký không
        self.chi_b64 = False            # cất nhật ký dạng chữ `<khoá>.b64`
        self.object_tre = 0             # mấy lần object/get đầu tiên chưa thấy file
        self.so_lan_job = 2             # object/get: hỏi job mấy lần mới có link
        self._id, self._cache = 1000, {}
        gia = self

        class XuLy(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                gia._xu_ly(self, "GET")

            def do_POST(self):
                gia._xu_ly(self, "POST")

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), XuLy)
        self.cong = self.srv.server_address[1]
        self.goc = f"http://127.0.0.1:{self.cong}/api/v2/"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def dong(self):
        self.srv.shutdown()
        self.srv.server_close()

    def goi(self, diem, pt=None):
        return [ts for p, d, ts in self.nhat if d == diem and (pt is None or p == pt)]

    def _moi_id(self):
        self._id += 1
        return self._id

    # ------------------------------------------------------------------ HTTP
    def _tra(self, h, ma, than, kieu="application/json"):
        h.send_response(ma)
        h.send_header("Content-Type", kieu)
        h.send_header("Content-Length", str(len(than)))
        h.end_headers()
        h.wfile.write(than)

    def _xu_ly(self, h, pt):
        u = urllib.parse.urlsplit(h.path)
        n = int(h.headers.get("Content-Length") or 0)
        than = h.rfile.read(n) if n else b""
        self.tho.append(h.requestline.encode() + b"\n" + str(h.headers).encode() + than)
        if u.path.startswith("/tai/"):
            self.auth_tai.append(h.headers.get("Authorization"))
            goi = self.tai_ve.get(u.path[len("/tai/"):])
            return self._tra(h, 200 if goi else 404, goi or b"", "application/zip")
        diem = u.path[len("/api/v2/"):]
        if pt == "GET":
            ts = dict(urllib.parse.parse_qsl(u.query))
            if than:
                return self._tra(h, 400, b"GET khong co than")
        else:
            if h.headers.get("Content-Type") != "application/json":
                return self._tra(h, 415, b"can JSON")
            ts = json.loads(than or b"{}")
        self.nhat.append((pt, diem, ts))
        if self.ma_loi.get(diem):
            return self._tra(h, self.ma_loi[diem].pop(0), b"<html>loi</html>", "text/html")
        d = self._xac_thuc(h) or self._api(pt, diem, ts)
        self._tra(h, 200, json.dumps(d).encode("utf-8"))

    def _xac_thuc(self, h):
        moc = h.headers.get("Timestamp") or ""
        kieu, _, b64 = (h.headers.get("Authorization") or "").partition(" ")
        try:
            uid, _, bam = base64.b64decode(b64).decode("utf-8").partition(":")
        except ValueError:
            uid = bam = ""
        if kieu != "Basic" or uid != self.UID:
            self.sai_xac_thuc += 1
            return {"success": False, "errors": ["UserID not valid."]}
        if not moc.isdigit() or abs(int(moc) - time.time()) > 300 or \
                bam != hashlib.sha256(f"{self.TOK}:{moc}".encode("utf-8")).hexdigest():
            self.sai_xac_thuc += 1
            return {"success": False, "errors": ["Hash doesn't match."]}
        return None

    # ------------------------------------------------------------------ API
    def _api(self, pt, diem, ts):
        def ok(**k):
            return {"success": True, **k}

        def loi(s):
            return {"success": False, "errors": [s]}

        if (pt == "POST") != (diem in self.GHI):
            return loi(f"Sai phương thức {pt} cho {diem}")
        if diem == "projects/read":
            return ok(projects=list(self.projects))
        if diem == "projects/create":
            if ts.get("language") != "Py":
                return loi("Language must be Py")
            if any(p["name"] == ts.get("name") for p in self.projects):
                return loi("Project name already exists")
            p = {"projectId": self._moi_id(), "organizationId": self.ORG, "name": ts["name"]}
            self.projects.append(p)
            # Project mới trên QC có sẵn main.py mẫu và một notebook nghiên cứu.
            self.files[p["projectId"]] = {
                "main.py": "# region imports\nfrom AlgorithmImports import *\n# endregion\n",
                "research.ipynb": "{}"}
            return ok(projects=[p])
        pid = int(ts.get("projectId") or 0)
        if diem.startswith("files/"):
            f = self.files.get(pid)
            if f is None:
                return loi("Project not found")
            ten = ts.get("name")
            if diem == "files/read":
                return ok(files=[{"name": k, "content": v} for k, v in f.items()])
            if (diem == "files/create") == (ten in f):
                return loi("File already exists" if ten in f else "File not found")
            if diem == "files/delete":
                del f[ten]
            else:
                f[ten] = ts["content"]
            return ok()
        if diem == "compile/create":
            cid = f"c-{self._moi_id()}"
            self.compiles[cid] = {"pid": pid, "anh": dict(self.files[pid]), "lan": 0,
                                  "state": "InQueue"}
            return ok(compileId=cid, state="InQueue")
        if diem == "compile/read":
            c = self.compiles[ts["compileId"]]
            c["lan"] += 1
            if c["lan"] >= 2 and not self.bien_dich_treo:
                c["state"] = "BuildError" if self.bien_dich_hong else "BuildSuccess"
            logs = (["Build started", "main.py(14,5): error: invalid syntax",
                     "Build failed"] if c["state"] == "BuildError" else ["Build Success"])
            return ok(compileId=ts["compileId"], state=c["state"], logs=logs)
        if diem == "backtests/create":
            c = self.compiles.get(ts.get("compileId"))
            if not c or c["state"] != "BuildSuccess" or c["pid"] != pid:
                return loi("Compile not found or failed")
            bt = {"backtestId": f"b-{self._moi_id()}", "projectId": pid,
                  "name": ts.get("backtestName"), "lan": 0, "loi": self.backtest_loi}
            if self.chay_that and not bt["loi"]:
                khoa, kq = self._chay(c["anh"])
                if khoa is None:                # thuật toán chết trên "cloud"
                    bt["loi"] = (kq.strip().splitlines()[-1], kq)
                elif self.chi_b64:
                    self.object_store[khoa + ".b64"] = base64.b64encode(kq)
                else:
                    self.object_store[khoa] = kq
            self.backtests[bt["backtestId"]] = bt
            return ok(backtest=self._xem(bt))
        if diem == "backtests/read":
            bt = self.backtests[ts["backtestId"]]
            bt["lan"] += 1
            return ok(backtest=self._xem(bt))
        if diem == "object/get":
            if ts.get("organizationId") != self.ORG:
                return loi("Organization not found")
            if "jobId" in ts:
                j = self.jobs[ts["jobId"]]
                j["con"] -= 1
                return ok(jobId=ts["jobId"], url=self._link(j["keys"]) if j["con"] <= 0 else "")
            keys = ts.get("keys") or []
            if self.object_tre > 0:
                self.object_tre -= 1
                return loi(f"Key {keys[0]} not found")
            thieu = [k for k in keys if k not in self.object_store]
            if thieu:
                return loi(f"Key {thieu[0]} not found")
            if self.so_lan_job:
                job = f"job-{self._moi_id()}"
                self.jobs[job] = {"keys": keys, "con": self.so_lan_job}
                return ok(jobId=job, url="")
            return ok(url=self._link(keys))
        return loi(f"Không có điểm {diem}")

    def _xem(self, bt):
        """Trạng thái backtest theo số lần đã hỏi — có một nhịp "completed nhưng thống kê
        chưa ghi xong" (QC làm vậy thật; LEAN CLI chờ qua nó)."""
        lan = bt["lan"]
        d = {"backtestId": bt["backtestId"], "projectId": bt["projectId"], "name": bt["name"],
             "status": "Running", "completed": False, "progress": min(0.35 * lan, 0.9),
             "error": None, "stacktrace": None, "runtimeStatistics": None,
             "statistics": None}
        if bt["loi"] and lan >= 2:
            d.update(status="Runtime Error", completed=True, progress=0.5,
                     error=bt["loi"][0], stacktrace=bt["loi"][1])
        elif lan == 3:
            d.update(completed=True, progress=1.0, statistics=[])
        elif lan >= 4:
            d.update(status="Completed.", completed=True, progress=1.0,
                     runtimeStatistics={"Equity": "$10,000.00"},
                     statistics={"Total Orders": "0", "Net Profit": "0%"})
        return d

    def _link(self, keys):
        ma = hashlib.sha1(f"{keys}{self._moi_id()}".encode()).hexdigest()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for k in keys:
                z.writestr(k, self.object_store[k])
        self.tai_ve[ma] = buf.getvalue()
        return f"http://127.0.0.1:{self.cong}/tai/{ma}"

    def _chay(self, anh):
        """Chạy bộ file của project như QC chạy. Trả `(khoá, gz)` hoặc `(None, stderr)`."""
        py = sorted((k, v) for k, v in anh.items() if k.endswith(".py"))
        ma = hashlib.sha1(json.dumps(py).encode("utf-8")).hexdigest()
        if ma not in self._cache:
            with tempfile.TemporaryDirectory() as td:
                for ten, nd in py:
                    with open(os.path.join(td, ten), "w", encoding="utf-8") as f:
                        f.write(nd)
                shutil.copy(os.path.join(TESTS, "gia_lap_qc.py"), td)
                with open(os.path.join(td, "AlgorithmImports.py"), "w", encoding="utf-8") as f:
                    f.write("class QCAlgorithm:\n    pass\n")
                with open(os.path.join(td, "nen.json"), "w", encoding="utf-8") as f:
                    json.dump(NEN1.tolist(), f)
                with open(os.path.join(td, "kich_ban.py"), "w", encoding="utf-8") as f:
                    f.write(f"GOC = {GOC!r}\nSPREAD = {SPREAD!r}\n" + KICH_BAN)
                env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
                r = subprocess.run([sys.executable, "kich_ban.py"], cwd=td, env=env,
                                   capture_output=True, text=True, encoding="utf-8",
                                   timeout=300)
                if r.returncode:
                    self._cache[ma] = (None, r.stderr[-3000:])
                else:
                    with open(os.path.join(td, "ra.gz"), "rb") as f:
                        self._cache[ma] = (r.stdout.strip().splitlines()[-1], f.read())
        return self._cache[ma]


def qc_cho(gia, uid=None, tok=None, ngu=None, gio=None):
    return qc_api.QC(uid or gia.UID, tok or gia.TOK, goc=gia.goc, mo=mo,
                     ngu=ngu or (lambda s: None), gio=gio or time.time, timeout=300)


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
    kiem("file lưu bằng Notepad (UTF-8 có BOM) vẫn đọc được", qc_api.doc_khoa({}, td) == ("9", "v"))
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
    kiem("du_lieu/ (nơi đặt qc_khoa.json) nằm trong .gitignore", "du_lieu/" in f.read().split())

# ================= 3. một lượt ▶ trọn vẹn =================
print("\n▸ Một lượt ▶ trọn vẹn trên QC giả (máy chủ chạy THẬT bộ file đẩy lên)")
CH = {"tu": "2025-01-02", "den": "2025-01-06"}
# Trần gói Free → HAI file (main.py + nguon_1.py): lượt đầu đi được cả nhánh "file chưa có
# → create". Lượt sau dùng trần Researcher (một file) — đúng cảnh người dùng nâng gói.
FILES = dg.dong_goi(DOC, CH, dg.GIOI_HAN)
REF = gl.chay_qc(cl, core, tt, dg.soat(DOC), NEN1, SPREAD)
gia = QCGia()
qc = qc_cho(gia)
tien_do = []
TD = tempfile.mkdtemp()
try:
    kq = qc_api.chay(qc, DOC, FILES, "lượt thử", TD, lambda v, x: tien_do.append((v, x)))
except qc_api.LoiQC as e:
    print(f"    (lỗi: {e})")
    kq = None
kiem("chạy trọn không lỗi", kq is not None)
kq = kq or {"meta": {}, "duong_nhat_ky": "", "url": "", "thong_ke_qc": {}}
p = gia.projects[0] if gia.projects else {}
pid = p.get("projectId")
bid = next(iter(gia.backtests), None)
ten_mong = "Cat Studio/" + " ".join(DOC_CHUAN["name"].split())
kiem("tạo project «Cat Studio/<tên sơ đồ>», ngôn ngữ Python",
     len(gia.projects) == 1 and p.get("name") == ten_mong
     and gia.goi("projects/create")[0].get("language") == "Py", f"({p.get('name')})")
fp = gia.files.get(pid, {})
kiem("đẩy đủ bộ file, đúng nội dung; notebook có sẵn của QC để yên",
     {k: v for k, v in fp.items() if k.endswith(".py")} == FILES and "research.ipynb" in fp,
     f"({', '.join(FILES)})")
kiem("main.py có sẵn → update; nguon_1.py chưa có → create",
     [x["name"] for x in gia.goi("files/update")] == ["main.py"]
     and [x["name"] for x in gia.goi("files/create")] == [k for k in FILES if k != "main.py"])
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
kiem("nhật ký nằm trong thư mục nhật ký, đuôi .jsonl",
     os.path.isfile(duong_nk) and os.path.dirname(duong_nk) == TD
     and duong_nk.endswith(".jsonl"), f"({os.path.basename(duong_nk)})")
_, lenh, luot = nk.doc_file(duong_nk) if os.path.isfile(duong_nk) else ({}, [], [])
kiem("`nhat_ky.doc_file` mở được: nguồn QuantConnect, đúng vân tay sơ đồ",
     meta.get("nguon") == "QuantConnect" and meta.get("van_tay") == nk._van_tay(DOC_CHUAN))
kiem("nhật ký tải về == chạy cầu nối ngay tại máy: từng lượt, từng lệnh, bảng tổng kết",
     [{k: v for k, v in r.items() if k != "loai"} for r in luot]
     == json.loads(json.dumps(REF.nhat_ky))
     and lenh == json.loads(json.dumps([x.tom_tat() for x in REF.so.lenh]))
     and meta.get("thong_ke") == json.loads(json.dumps(REF.thong_ke)),
     f"({len(luot)} lượt · {len(lenh)} lệnh)")
kiem("meta mang bộ đếm — đủ để in lại dòng tổng kết của QC", meta.get("dem") == REF.dem)
kiem("trả link backtest trên web QC",
     bid is not None and kq["url"] == f"https://www.quantconnect.com/project/{pid}/{bid}")

# ================= 2. khoá không lộ =================
print("\n▸ Khoá không bao giờ lộ")
kiem("mọi yêu cầu API đều qua xác thực của máy giả",
     gia.sai_xac_thuc == 0 and len(gia.nhat) > 10, f"({len(gia.nhat)} yêu cầu)")
kiem("token KHÔNG nằm trong yêu cầu nào gửi đi — chỉ có băm của nó",
     all(QCGia.TOK.encode() not in r for r in gia.tho))
kiem("repr(QC) không mang token", QCGia.TOK not in repr(qc) and QCGia.UID in repr(qc))

# ================= 4. lượt sau =================
print("\n▸ Lượt sau (đã nâng Researcher): dùng lại project, dọn file thừa")
FILES_1 = dg.dong_goi(DOC, CH, chay_qc.GIOI_HAN_RESEARCHER)
kiem("trần 64 KB của Researcher: cả gói vừa MỘT file main.py", list(FILES_1) == ["main.py"],
     f"({len(FILES_1['main.py'].encode('utf-8')) / 1024:.1f} KB)")
gia.files.setdefault(pid, {})["nguon_2.py"] = "# phần của một lần đóng gói cũ, to hơn\n"
gia.nhat.clear()
e = bat(qc_api.chay, qc, DOC, FILES_1, "lượt hai", TD)
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
e = bat(qc_api.chay, qc, DOC, FILES, "x", TD)
gia.bien_dich_hong = False
kiem("biên dịch hỏng → LoiQC kèm mấy dòng log cuối của QC",
     isinstance(e, qc_api.LoiQC) and "biên dịch KHÔNG được" in str(e)
     and "invalid syntax" in str(e))

gia.backtest_loi = ("Runtime Error: division by zero",
                    "Traceback (most recent call last):\n  File \"main.py\", line 9\n"
                    "ZeroDivisionError: division by zero")
e = bat(qc_api.chay, qc, DOC, FILES, "x", TD)
gia.backtest_loi = None
kiem("backtest lỗi → LoiQC: lời lỗi, đuôi vết lỗi, link xem đủ",
     isinstance(e, qc_api.LoiQC) and "Backtest LỖI" in str(e) and "division by zero" in str(e)
     and "line 9" in str(e) and "https://www.quantconnect.com/project/" in str(e))

thieu = {"main.py": FILES["main.py"]}         # quên nguon_1.py → thuật toán chết trên cloud
e = bat(qc_api.chay, qc, DOC, thieu, "x", TD)
kiem("lỗi xảy ra TRÊN CLOUD về tới người dùng nguyên văn tiếng Việt",
     isinstance(e, qc_api.LoiQC) and "Project THIẾU file nguon_1.py" in str(e),
     f"({str(e).splitlines()[0][:60]}…)" if e else "")

ngu = []
gia.chay_that = False
gia.object_store.clear()
qc_ngu = qc_cho(gia, ngu=ngu.append)
gia.nhat.clear()
e = bat(qc_api.chay, qc_ngu, DOC, FILES, "x", TD)
kiem("không có nhật ký → LoiQC nêu khoá, lời QC, link log",
     isinstance(e, qc_api.LoiQC) and KHOA_NK in str(e) and "not found" in str(e)
     and "quantconnect.com/project/" in str(e))
cho = [x for x in ngu if x >= 2]                # nghỉ của hỏi-lại-nhật-ký (hỏi trạng thái < 2 s)
kiem("… sau khi đã hỏi lại vài lần, thưa dần (nhật ký có khi hiện ra trễ)",
     cho == [2, 4, 8] and len(gia.goi("object/get")) == 8, f"(nghỉ {cho} giây)")
gia.chay_that = True

ngu.clear()
gia.object_tre = 3
e = bat(qc_api.chay, qc_ngu, DOC, FILES, "x", TD)
kiem("nhật ký hiện ra trễ → chờ rồi vẫn lấy được", e is None and gia.object_tre == 0
     and [x for x in ngu if x >= 2] == [2, 4], f"({e})" if e else "")

gia.object_store.clear()
gia.chi_b64 = True
TD2 = tempfile.mkdtemp()
e = bat(qc_api.chay, qc, DOC, FILES, "x", TD2)
gia.chi_b64 = False
ten_nk = os.path.basename(duong_nk)
kiem("chỉ có bản chữ .b64 (save_bytes hỏng trên QC) → vẫn ra đúng nhật ký",
     e is None and list(gia.object_store) == [KHOA_NK + ".b64"]
     and nk.doc_file(os.path.join(TD2, ten_nk))[2] == luot)

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
e = bat(qc_api.chay, qc_cho(gia, tok=GIA_MAO), DOC, FILES, "x", TD)
kiem("token sai → LoiKhoa tiếng Việt, câu lỗi không chứa token",
     isinstance(e, qc_api.LoiKhoa) and "Khoá QuantConnect SAI" in str(e)
     and GIA_MAO not in str(e))
e = bat(qc_api.chay, qc_cho(gia, uid="999"), DOC, FILES, "x", TD)
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
print("\n▸ tools/chay_qc.py")
gia.nhat.clear()
ma, ra = cli(TU_DEN, qc=qc, thu_muc_nhat_ky=TD)
kiem("chạy xong → mã thoát 0, in «XONG»", ma == 0 and "✔ XONG" in ra)
kiem("in đúng hai dòng tổng kết như log của QC",
     all(d in ra for d in cl.dong_ket_qua("XAUUSD 2025-01-02 → 2025-01-06", REF.thong_ke,
                                          REF.dem, REF.ct.tf5, None)))
kiem("in từng bước, có tiến độ backtest",
     all(s in ra for s in ("Tìm project", "Tải file lên QC", "Biên dịch", "Chạy backtest 100%",
                           "Tải nhật ký về")))
kiem("in link QC và đường dẫn nhật ký", "Xem trên QC : https://www.quantconnect.com/project/"
     in ra and f"Nhật ký     : {os.path.join(TD, ten_nk)}" in ra)
kiem("không in token", QCGia.TOK not in ra)

ma, ra = cli(TU_DEN, qc=qc_cho(gia, tok=GIA_MAO), thu_muc_nhat_ky=TD)
kiem("khoá sai → mã thoát 1, một câu tiếng Việt, không traceback, không lộ khoá",
     ma == 1 and "✘ Khoá QuantConnect SAI" in ra and "Traceback" not in ra
     and GIA_MAO not in ra)

cu_mt = {k: os.environ.pop(k) for k in ("QC_USER_ID", "QC_API_TOKEN") if k in os.environ}
cu_goc = luu_tru.goc
with tempfile.TemporaryDirectory() as td:
    luu_tru.goc = lambda: td
    try:
        ma, ra = cli(TU_DEN)
    finally:
        luu_tru.goc = cu_goc
        os.environ.update(cu_mt)
kiem("thiếu khoá → mã thoát 1, chỉ cách đặt khoá, chưa đóng gói gì",
     ma == 1 and "Chưa có khoá QuantConnect" in ra and "gói:" not in ra)

hong = copy.deepcopy(DOC)
for st in hong["entry"]["steps"]:
    if core.is_start_step(st):
        st["nhip"] = "D1"
gia3 = QCGia()
with tempfile.TemporaryDirectory() as td:
    duong = os.path.join(td, "hong.json")
    with open(duong, "w", encoding="utf-8") as f:
        json.dump(hong, f, ensure_ascii=False)
    ma, ra = cli([duong] + TU_DEN, qc=qc_cho(gia3), thu_muc_nhat_ky=td)
kiem("sơ đồ hỏng → báo ngay trên máy, CHƯA gửi gì lên QC",
     ma == 1 and "Sơ đồ chưa chạy được" in ra and "D1" in ra and gia3.nhat == [])
ma, ra = cli([os.path.join(TD, "khong_co.json")], qc=qc_cho(gia3), thu_muc_nhat_ky=TD)
kiem("file sơ đồ không có → nói đọc không được", ma == 1 and "Đọc sơ đồ không được" in ra)
ma, ra = cli(["--tu", "2025-13-01"], qc=qc_cho(gia3), thu_muc_nhat_ky=TD)
ma2, ra2 = cli(["--tu", "2025-03-01", "--den", "2025-02-01"], qc=qc_cho(gia3),
               thu_muc_nhat_ky=TD)
kiem("ngày gõ sai, hay từ-sau-đến → báo ngay, CHƯA gửi gì lên QC",
     ma == 1 and "YYYY-MM-DD" in ra and ma2 == 1 and "nằm SAU" in ra2 and gia3.nhat == [])

for g in (gia, gia3):
    g.dong()
shutil.rmtree(TD, ignore_errors=True)
shutil.rmtree(TD2, ignore_errors=True)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
