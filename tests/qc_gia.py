"""MÁY CHỦ QUANTCONNECT GIẢ trên 127.0.0.1 — dùng chung cho các bài kiểm đường API.

Nói đúng giao thức mà LEAN CLI nói (xác thực bằng băm, `success / errors`, biên dịch →
backtest → Object Store trả link tải zip), và CHẠY THẬT bộ file được đẩy lên trong một
Python sạch như QC chạy, rồi cất nhật ký vào Object Store dưới đúng khoá cầu nối tự chọn.
"""
import base64
import hashlib
import io
import json
import os
import re
import shutil
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

from cat_studio import qc_api  # noqa: E402

#: Mở URL KHÔNG qua proxy — máy chủ giả nằm ở 127.0.0.1, proxy của máy (nếu có) không
#: được chen vào giữa.
_MO = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def mo(req, timeout):
    return _MO.open(req, timeout=timeout)


class QCGia:
    """Máy chủ QuantConnect GIẢ trên 127.0.0.1 — đúng những điểm API mà app dùng."""

    UID, TOK, ORG = "424242", "khoa-bi-mat-0123456789abcdef", "org-cat"
    GHI = {"projects/create", "files/create", "files/update", "files/delete",
           "compile/create", "backtests/create", "object/get", "object/delete"}

    def __init__(self, du_lieu_may=None):
        """`du_lieu_may(cau_hinh)`: `{mã: [(t, o, h, l, c, v, spread)…]}` cho rổ mã trong
        khối CẤU HÌNH của `main.py`. Bộ file đẩy lên chạy CHÍNH lớp vỏ `vo_may` trên LEAN
        giả (`tests/lean_gia.py`), không phải một bản mô phỏng của nó — và seed theo khoảng
        ngày thì màn đã thấy với màn ẩn ra hai kết quả khác nhau như thật."""
        self.du_lieu_may = du_lieu_may
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
        if diem == "authenticate":
            return ok()
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
        if diem == "object/delete":
            if ts.get("organizationId") != self.ORG or ts.get("key") not in self.object_store:
                return loi(f"Key {ts.get('key')} not found")
            del self.object_store[ts["key"]]
            return ok()
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
        return self._chay_may(dict(py), ma)


def cau_hinh_main(main_py):
    """Đọc khối CẤU HÌNH của `main.py` cỗ máy 5 trạm: mỗi dòng `    "khoá": <json>,`."""
    ch, trong = {}, False
    for dong in main_py.splitlines():
        if dong.startswith("CAU_HINH_NHUNG = {"):
            trong = True
        elif trong and dong == "}":
            break
        elif trong:
            k, _, v = dong.strip().rstrip(",").partition(": ")
            ch[json.loads(k)] = json.loads(v)
    return ch


def _chay_may(self, py, ma):
    if ma not in self._cache:
        import lean_gia
        ch = cau_hinh_main(py["main.py"])
        ra, loi = lean_gia.chay_bo_file(py, self.du_lieu_may(ch), GOC)
        if ra is None:
            self._cache[ma] = (None, loi)
        else:
            k = ch["khoa"]
            self._cache[ma] = (k, base64.b64decode(ra["kho"][k]))
    return self._cache[ma]


QCGia._chay_may = _chay_may


def qc_cho(gia, uid=None, tok=None, ngu=None, gio=None):
    return qc_api.QC(uid or gia.UID, tok or gia.TOK, goc=gia.goc, mo=mo,
                     ngu=ngu or (lambda s: None), gio=gio or time.time, timeout=300)
