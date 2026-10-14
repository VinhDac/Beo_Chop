"""CẦU NỐI cho bài kiểm game đầu-cuối (`webui/kiem/game.mjs`).

Một máy chủ HTTP nhỏ làm hai việc:
  · phục vụ `webui/dist` (giao diện đã build) cho Chromium;
  · nhận `POST /goi/chinh {ten, args}` và gọi THẲNG hàm đó trên `api.Api` THẬT — đúng thứ
    pywebview làm trên máy người dùng. Giao diện tưởng mình đang nói với app thật.

Phía QuantConnect là máy chủ GIẢ (`tests/qc_gia.py`) chạy thật bộ file mà app đóng gói,
trên nến giả (`tests/gia_lap_qc.py`). Nến giả theo NĂM của khoảng ngày (cùng năm → cùng nến,
nên kết quả tất định) và được DỜI GIỜ về đúng năm đó — để giờ trong "xem máy nghĩ" khớp
năm của màn.

Không đụng gì của máy thật: sổ game, nhật ký, khoá đều nằm trong một thư mục tạm; biến
môi trường QC_USER_ID / QC_API_TOKEN bị gỡ khỏi tiến trình này.

Chạy:  python webui/kiem/cau_noi_game.py [cổng]     (0 = tự chọn; in "san_sang <cổng>")
"""
import calendar
import json
import os
import sys
import tempfile
import types
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [GOC, os.path.join(GOC, "lean"), os.path.join(GOC, "tests")]
TD = tempfile.mkdtemp(prefix="cat_game_")
for k in ("QC_USER_ID", "QC_API_TOKEN"):
    os.environ.pop(k, None)


# pywebview giả: không có màn hình, cửa sổ phụ chỉ là một vỏ rỗng.
class _SuKien:
    def __iadd__(self, f):
        return self


class _CuaSo:
    def __init__(self, *a, **k):
        self.events = types.SimpleNamespace(closed=_SuKien(), closing=_SuKien())

    def set_title(self, t):
        pass

    def destroy(self):
        pass

    def evaluate_js(self, js):
        pass


_wv = types.ModuleType("webview")
_wv.create_window = lambda *a, **k: _CuaSo(*a, **k)
sys.modules["webview"] = _wv

import numpy as np  # noqa: E402

from cat_studio import luu_tru  # noqa: E402

luu_tru.goc = lambda: TD
os.makedirs(os.path.join(TD, "nhat_ky"), exist_ok=True)
luu_tru.thu_muc_nhat_ky = lambda: os.path.join(TD, "nhat_ky")

from cat_studio import api, bo_chay as bc, qc_api  # noqa: E402
import gia_lap_qc as gl  # noqa: E402
import qc_gia  # noqa: E402

#: Mốc giờ của `gia_lap_qc.du_lieu` (2025-01-02 00:00 UTC).
_MOC = 1735776000
_TUAN = 7 * 86400
_NEN = {}


def chon_nen(ch):
    """Nến giả theo năm của `tu`, dời về đúng khoảng đó (bội 7 ngày — giữ thứ trong tuần,
    nên nghỉ cuối tuần vẫn rơi đúng thứ Bảy). ▶ nhanh (quý 4) ngắn hơn ▶ đầy đủ."""
    tu = ch.get("tu") or "2025-01-02"
    nhanh = tu[5:7] == "10"
    khoa = (tu, nhanh)
    if khoa not in _NEN:
        a = gl.du_lieu(np, seed=int(tu[:4]) % 97, ngay=8 if nhanh else 20).copy()
        dich = calendar.timegm(datetime.strptime(tu, "%Y-%m-%d").timetuple()) - _MOC
        dich = -((-dich) // _TUAN) * _TUAN if dich < 0 else -(-dich // _TUAN) * _TUAN
        a["t"] += dich
        _NEN[khoa] = a
    return _NEN[khoa]


_spread = bc.CaiDat(spread_diem=20.0, point=0.01).spread_gia
GIA = qc_gia.QCGia(chon_nen({}), _spread, chon_nen=chon_nen)
_QC_GOC = qc_api.QC
qc_api.QC = lambda uid, tok, **k: _QC_GOC(uid, tok, goc=GIA.goc, mo=qc_gia.mo, timeout=300)

CHA = api.Api()
CHA._ban = lambda ten, d: None

_DIST = os.path.join(GOC, "webui", "dist")
_KIEU = {".html": "text/html", ".js": "text/javascript", ".css": "text/css",
         ".svg": "image/svg+xml", ".ico": "image/x-icon", ".png": "image/png"}


class _XuLy(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _tra(self, ma, than, kieu="application/json"):
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(than)))
        self.end_headers()
        self.wfile.write(than)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/_khoa_gia":
            # Khoá của máy chủ QC GIẢ — để bài kiểm gõ vào hộp khoá như người dùng.
            return self._tra(200, json.dumps({"uid": GIA.UID, "tok": GIA.TOK}).encode())
        f = os.path.join(_DIST, p.lstrip("/") or "index.html")
        if not os.path.isfile(f):
            return self._tra(404, b"")
        with open(f, "rb") as fh:
            self._tra(200, fh.read(), _KIEU.get(os.path.splitext(f)[1], "application/octet-stream"))

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        f = getattr(CHA, d["ten"], None) if not d["ten"].startswith("_") else None
        kq = f(*d["args"]) if callable(f) else {"ok": False, "error": f"không có hàm {d['ten']}"}
        self._tra(200, json.dumps(kq, ensure_ascii=False, default=str).encode("utf-8"))


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 0), _XuLy)
    print("san_sang", srv.server_address[1], flush=True)
    srv.serve_forever()
