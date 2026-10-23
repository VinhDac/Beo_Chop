"""XEM THỬ GIAO DIỆN TRONG TRÌNH DUYỆT — cầu nối giả thay pywebview.

    .venv\\Scripts\\python.exe tools\\xem_thu.py          ->  http://127.0.0.1:8777
    .venv\\Scripts\\python.exe tools\\xem_thu.py 9000     ->  cổng khác

KHÔNG phải lối chạy của app. Lối đó là `tools\\chay.bat` — cửa sổ pywebview thật, khung
tự vẽ, hộp thoại file của Windows. Cái này chỉ để NHÌN và SOI giao diện bằng trình duyệt
(DevTools, ảnh chụp, bài kiểm tự động): cùng bundle trong `webui/dist`, cùng `api.py`
THẬT, chỉ thay đường vận chuyển — `fetch` thay cho pywebview.

Vì sao cần: không có nó thì cách duy nhất để xem một màn vừa sửa là mở cả app lên, mà
trong cửa sổ pywebview thì không chụp được ảnh, không đọc được console, không có cách nào
cho máy bấm thử. Ba thứ ấy là cách duy nhất canh được giao diện mà không mở mắt ra nhìn.

Chỉ nghe trên 127.0.0.1.

⚠ KHUNG XEM THỬ KHÔNG VẼ THÌ PHÉP ĐO NÓI DỐI. Trang chỉ chạy nhịp vẽ khi cửa sổ thật sự
hiện ra; cửa sổ bị che là trình duyệt bỏ nhịp ấy. Mà `ResizeObserver` — thứ React Flow
dùng để đo cỡ từng khối — CHỈ bắn trong nhịp vẽ. Hậu quả: đọc DOM bằng JavaScript thì
thấy đủ khối nhưng KHÔNG một đường nối nào, vì chưa đo được cỡ thì chưa tính nổi chỗ
cắm dây. Đã mất một buổi truy bản React Flow, bản React, StrictMode và CSS trước khi
nhận ra không có lỗi nào cả.
   Luật: muốn tin phép đo thì CHỤP ẢNH một nhát trước (ảnh ép trang vẽ), rồi mới đo.

⚠ BÀI HỌC D-12 — ĐỪNG DỰNG LẠI HAI BỀ MẶT. Bản trước phục vụ `Api` và `ApiQC` cùng lúc,
tự định tuyến mọi tên `qc_*` sang `ApiQC`. Thành ra hộp Khoá bấm NGON trong trình duyệt
mà trong app thật thì báo «api.py không có hàm qc_khoa» — vì cửa sổ chính chỉ có `Api`.
Cầu nối giả nói dối một chỗ là cả bài kiểm bằng mắt mất giá trị. Nay `api.py` chỉ còn
MỘT bề mặt, và file này cũng vậy.
"""
import io
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ⚠ In tiếng Việt vào một chỗ BỊ CHUYỂN HƯỚNG (log, bài kiểm, việc nền) thì Windows cho
# stdout bảng mã cp1252 và câu đầu tiên đã chết vì UnicodeEncodeError. Trong một cửa sổ
# console thật thì không sao — nên lỗi này chỉ lộ ra đúng lúc chạy tự động.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from cat_studio import api as api_mod  # noqa: E402
from cat_studio import luu_tru  # noqa: E402

DIST = os.path.join(luu_tru.thu_muc_goi(), "webui", "dist")

KIEU = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
        ".ico": "image/x-icon", ".png": "image/png", ".woff2": "font/woff2",
        ".json": "application/json; charset=utf-8", ".map": "application/json"}

#: Vỏ `window.pywebview` giả. Khai ĐÚNG danh sách hàm mà `api.py` có, vì `cho_cau_noi`
#: của giao diện chờ một HÀM CÓ THẬT xuất hiện (xem `webui/src/api.ts`).
#:
#: ⚠ GỬI KÈM THAM SỐ URL. App thật đưa mỗi CỬA SỔ một js_api khác nhau — cửa sổ chính
#: được `Api`, cửa sổ Kết quả và cửa sổ View được `ApiKetQua`, cửa sổ Optimize được
#: `ApiToiUu` — và ba lớp sau cố ý có BỀ MẶT HẸP (xem docstring `NenCuaSo`). Bản trước
#: của file này phục vụ `Api` cho mọi vai, nên nó NÓI DỐI đúng kiểu bài học D-12 ở trên
#: kể lại: một cửa bấm ngon trong trình duyệt mà app thật báo «không có hàm». Nay vai
#: nào thì bề mặt ấy, và tham số URL là thứ quyết định vai (y `webui/src/main.tsx`).
SHIM = """
window.pywebview = { api: {} };
(async () => {
  const q = window.location.search || '';
  const ten = await (await fetch('/_ten' + q)).json();
  for (const t of ten) {
    window.pywebview.api[t] = async (...a) => {
      const r = await fetch('/_goi/' + t + q, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(a),
      });
      return await r.json();
    };
  }
  console.log('[xem_thu] cầu nối giả sẵn sàng — ' + ten.length + ' cửa');
})();
"""


API = api_mod.Api()


def _api_cua_vai(truy_van):
    """Tham số URL -> js_api của ĐÚNG cửa sổ ấy, y app thật.

    Cùng bảng định tuyến với `webui/src/main.tsx`: `?kq=` và `?view=` là cửa sổ phụ bày
    một lượt chạy, `?tu=` là cửa sổ Optimize, không tham số nào là cửa sổ chính."""
    t = parse_qs(truy_van or "")
    ma = (t.get("view") or t.get("kq") or [None])[0]
    if ma:
        # `goi_chinh` ở app thật gọi `evaluate_js` sang cửa sổ chính. Ở đây không có
        # cửa sổ chính nào, nên in ra — «Soi lượt» bấm vào vẫn thấy nó đã gọi tới đâu.
        return api_mod.ApiKetQua(
            ma, lambda chu: sys.stderr.write(f"  [soi_luot] {chu}\n"))
    me = (t.get("tu") or [None])[0]
    if me:
        return api_mod.ApiToiUu(me, lambda d: sys.stderr.write(f"  [bao_chinh] {d}\n"))
    return API


class Tay(BaseHTTPRequestHandler):
    @property
    def api(self):
        return _api_cua_vai(self.path.partition("?")[2])

    def _tra(self, ma, kieu, body):
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(body)))
        # Giao diện nạp như một ES module, nên phải là http thật và không được cache
        # bản cũ sau mỗi lần `npm run build`.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        duong = self.path.split("?")[0]
        if duong == "/_gia.js":
            return self._tra(200, KIEU[".js"], SHIM.encode("utf-8"))
        if duong == "/_ten":
            ten = sorted(n for n in dir(self.api)
                         if not n.startswith("_") and callable(getattr(self.api, n)))
            return self._tra(200, KIEU[".json"],
                             json.dumps(ten).encode("utf-8"))
        if duong in ("/", "/index.html"):
            with open(os.path.join(DIST, "index.html"), encoding="utf-8") as f:
                html = f.read()
            # Chèn vỏ giả TRƯỚC bundle: nó phải có mặt từ khung hình đầu tiên.
            html = html.replace("<head>", '<head>\n  <script src="/_gia.js"></script>', 1)
            return self._tra(200, KIEU[".html"], html.encode("utf-8"))
        # Chặn thoát ra ngoài dist/ — đường dẫn gõ tay không được đọc file khác của máy.
        p = os.path.normpath(os.path.join(DIST, duong.lstrip("/")))
        if not p.startswith(DIST) or not os.path.isfile(p):
            return self._tra(404, "text/plain; charset=utf-8", b"khong co")
        with open(p, "rb") as f:
            return self._tra(200, KIEU.get(os.path.splitext(p)[1], "application/octet-stream"),
                             f.read())

    def do_POST(self):
        if not self.path.startswith("/_goi/"):
            return self._tra(404, "text/plain; charset=utf-8", b"khong co")
        # ⚠ CẮT THAM SỐ URL RA KHỎI TÊN HÀM. Vỏ giả gửi kèm `?view=…` để biết phục vụ
        # bề mặt của cửa sổ nào (xem `SHIM`), nên không cắt thì tên hàm thành
        # «doc_luot_chay?view=…» và mọi cửa báo "api.py không có hàm".
        ten = self.path[len("/_goi/"):].partition("?")[0]
        n = int(self.headers.get("Content-Length") or 0)
        args = json.loads(self.rfile.read(n) or b"[]")
        ham = getattr(self.api, ten, None)
        if ten.startswith("_") or not callable(ham):
            ra = {"ok": False, "error": f"api.py không có hàm «{ten}»"}
        else:
            try:
                ra = ham(*args)
            except Exception as e:                  # cửa nào cũng đã bọc, đây là lưới cuối
                ra = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        self._tra(200, KIEU[".json"],
                  json.dumps(ra, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt, *a):
        # Chỉ in lời gọi api, không in từng file tĩnh — log tĩnh làm chìm mất cái cần xem.
        if "/_goi/" in (a[0] if a else ""):
            sys.stderr.write("  %s\n" % (fmt % a))


def main():
    cong = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    if not os.path.isfile(os.path.join(DIST, "index.html")):
        print("Chưa build giao diện — chạy tools\\build_ui.bat trước.")
        return 1
    print(f"Xem thử ở  http://127.0.0.1:{cong}   (Ctrl+C để thôi)")
    ThreadingHTTPServer(("127.0.0.1", cong), Tay).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
