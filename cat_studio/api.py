"""Cat_Studio — bề mặt DUY NHẤT giao diện web gọi tới.

    JS  →  window.pywebview.api.<tên>()  →  api.py  →  core.py

Hai luật của file này:

1. **KHÔNG BAO GIỜ ném lỗi qua cầu nối.** Mọi hàm công khai bọc `@_bat_loi`, luôn trả
   `{"ok": bool, "value": …, "error": str, "trace": str}`. Một exception lọt qua là
   promise bên JS treo vĩnh viễn, không có thông báo gì.

2. **Mọi thuộc tính không-callable trên `Api` PHẢI bắt đầu bằng `_`.**
   pywebview duyệt `dir(js_api)` để liệt kê hàm; gặp một thuộc tính là đối tượng
   Window, nó đọc trúng property `width`/`title`… mà mấy property đó lại quay về
   UI thread đang bị chặn → app treo "Not Responding" vĩnh viễn.
"""
import functools
import inspect
import json
import os
import subprocess
import sys
import threading
import time
import traceback

from . import cai_dat
from . import chay_lean
from . import chay_toi_uu
from . import core
from . import hanh_trinh
from . import sinh_ma
from . import bat_dau
from . import hoi
from . import lam
from . import ngon_ngu
from . import toi_uu
from .ngon_ngu import tr
if sys.platform == "win32":
    from . import khung_cua_so
else:
    # Không phải Windows thì chỉ có BÀI KIỂM chạy tới đây (Linux/CI). Khung tự vẽ là chuyện
    # của Win32 — `khung_cua_so` gọi `ctypes.windll` ngay lúc nạp — nên thay bằng bản
    # rỗng cho `api.py` nạp được. Trên Windows không đổi gì.
    from . import khung_rong as khung_cua_so
from . import qc_api
from . import luu_tru


def _bat_loi(fn):
    """Bọc một phương thức: không bao giờ ném lỗi qua cầu nối.

    ⚠ `__signature__` KHÔNG được quên. pywebview dựng hàm JS bằng
    `inspect.getfullargspec(attr).args[1:]` (webview/util.py, `get_functions`), và
    `getfullargspec` KHÔNG lần theo `__wrapped__` của `functools.wraps`. Một wrapper
    `(*a, **kw)` trần vì thế khai báo ra hàm JS KHÔNG THAM SỐ NÀO — mọi đối số bên JS
    gửi đi đều bị vứt IM LẶNG, và lỗi hiện ra ở tận đâu đâu ("khối rỗng", "sơ đồ mất
    dây") chứ không phải ở chỗ gọi.
    Gán `__signature__` là cách duy nhất bắt `getfullargspec` thấy đúng tham số thật."""
    @functools.wraps(fn)
    def bao(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}",
                    "trace": traceback.format_exc(limit=6)}
    bao.__signature__ = inspect.signature(fn)
    return bao


def _doc_ma_luot(ma):
    """`20261017-143005` -> `17/10 14:30`. Tiêu đề cửa sổ phải đọc được bằng mắt khi
    có bốn cái xếp cạnh nhau, không phải một chuỗi số."""
    t = str(ma or "")
    if len(t) == 15 and t[8] == "-":
        return f"{t[6:8]}/{t[4:6]} {t[9:11]}:{t[11:13]}"
    return t


def _ok(v=None, **them):
    ra = {"ok": True, "value": v}
    ra.update(them)
    return ra


def _loi(chu):
    """Thất bại CÓ LÝ DO ĐỌC ĐƯỢC — khác với ngoại lệ. Cùng hình dạng với `_bat_loi` trả
    về, nên phía JS chỉ có một chỗ để kiểm tra."""
    return {"ok": False, "error": chu}


# ---------------------------------------------------------------------------
class NenCuaSo:
    """Phần CHUNG của một cửa sổ tự vẽ khung: giữ cửa sổ của CHÍNH MÌNH và vá khung
    của CHÍNH MÌNH.

    ⚠ Vì sao phải tách ra thành lớp nền — ba lỗi đã có thật, không phải giả định (gặp ở
    cửa sổ thứ hai đầu tiên của app, Strategy Tester, nay đã bỏ — cửa sổ Màn chơi y vậy):

      1. Mở cửa sổ thứ hai với `js_api=self`, tức nó dùng CHUNG một `Api` với cửa sổ
         chính, mà `self._window` lại trỏ cửa sổ chính. Bấm ✕ trên thanh tiêu đề tự vẽ
         của cửa sổ thứ hai gọi `cua_so_dong()` → `self._window.destroy()` → ĐÓNG CỬA SỔ
         CHÍNH. Thu nhỏ, phóng to, đổi tiêu đề, hộp thoại file: nhắm nhầm cửa sổ y hệt.
      2. `KhungTuVe` giữ đúng MỘT `hwnd` và MỘT bảng vùng-cấm. Kéo thanh tiêu đề của
         cửa sổ thứ hai `PostMessage` vào hwnd cửa sổ chính → kéo nhầm cửa sổ.
      3. Hai cửa sổ ghi đè vùng cấm của nhau, nên chỗ có nút bấm ở cửa sổ này lại
         thành chỗ kéo được ở cửa sổ kia.

    Mỗi cửa sổ một thể hiện của lớp này là hết cả ba, và không phải nhớ kỷ luật gì."""

    #: Hậu tố tiêu đề. Lớp con đổi cái này chứ không viết lại `set_title`.
    _HAU_TO = "Cat Studio"

    def __init__(self):
        # Gạch dưới hết — xem chú thích đầu file.
        self._window = None
        self._khung = khung_cua_so.KhungTuVe()

    # ------------------------------------------------------- ngôn ngữ
    @_bat_loi
    def khoi_dong(self):
        """CỬA ĐẦU TIÊN mọi cửa sổ gọi — trả thứ phải biết TRƯỚC khi vẽ khung hình đầu.

        Hôm nay đúng một thứ: ngôn ngữ. Đặt ở lớp NỀN nên cả ba cửa sổ (sơ đồ, Kết quả,
        Optimize) cùng có, và `api.ts` chỉ phải gọi một chỗ — xem `cho_cau_noi`. Thiếu
        cửa này thì cửa sổ nào cũng vẽ bằng mặc định rồi mới đổi tiếng: người chọn tiếng
        Việt thấy một nháy tiếng Anh mỗi lần mở app."""
        return _ok({"ngon_ngu": core.ngon_ngu()})

    # -- gắn cửa sổ (Python gọi, không phải JS) --
    def _gan_window(self, w):
        self._window = w

    def _va_khung(self, chua_chuoi, cho=4.0, nhip=0.15):
        """Tìm hwnd theo tiêu đề rồi vá khung. THỬ LẠI cho tới `cho` giây.

        ⚠ Phải thử lại chứ không hẹn giờ một phát: `webview.create_window` trả về NGAY,
        còn việc dựng cửa sổ thật thì đẩy sang UI thread. Đo được — hẹn 0,45 s thì
        `tim_hwnd` chạy lúc cửa sổ chưa `IsWindowVisible`, không thấy gì, và cửa sổ mở
        ra frameless mà KHÔNG kéo được: trông y như lỗi của `khung_cua_so`.

        Vá hỏng thật thì cửa sổ vẫn dùng được, chỉ là không kéo/giãn được — thà vậy còn
        hơn không mở nổi."""
        het = time.monotonic() + cho
        while time.monotonic() < het:
            h = khung_cua_so.tim_hwnd(chua_chuoi)
            if h and self._khung.va(h):
                return True
            time.sleep(nhip)
        return False

    #: Cửa sổ kết quả đang mở: {mã lượt: (window, ApiKetQua)}. Giữ lại vì HAI lẽ —
    #: bấm hai lần vào cùng một lượt thì ĐƯA CỬA SỔ CŨ LÊN chứ không đẻ cái thứ hai,
    #: và phải giữ tham chiếu tới `ApiKetQua` để Python đừng thu gom mất cái js_api
    #: đang sống trong cửa sổ ấy.
    _cua_so_kq: dict = {}
    #: Cùng vai với `_cua_so_kq`, cho cửa sổ Optimize.
    _cua_so_tu: dict = {}

    def _ban(self, ten, du_lieu):
        """Đẩy sự kiện sang JS của CHÍNH cửa sổ này. Nuốt lỗi: cửa sổ có thể đã đóng
        giữa chừng."""
        if not self._window:
            return
        try:
            self._window.evaluate_js(
                f"window.__su_kien && window.__su_kien("
                f"{json.dumps(ten)}, {json.dumps(du_lieu, ensure_ascii=False)})")
        except Exception:
            pass

    # ------------------------------------------------------- khung cửa sổ
    # Xem `khung_cua_so.py`: kéo/giãn PHẢI do web khởi động, vì WebView2 là cửa sổ con
    # phủ kín cửa sổ cha nên cha không bao giờ nhận được chuột.
    @_bat_loi
    def vung_khong_keo(self, vung, cao):
        self._khung.dat_vung_cam(vung, cao)
        return _ok(True)

    @_bat_loi
    def keo_cua_so(self, ht):
        return _ok(self._khung.bat_dau_keo(ht))

    @_bat_loi
    def cua_so_thu_nho(self):
        self._window.minimize()
        return _ok(True)

    @_bat_loi
    def cua_so_phong_to(self):
        self._khung.phong_to_hay_khoi_phuc(self._window)
        return _ok(self._khung.dang_phong_to())

    @_bat_loi
    def cua_so_dang_phong_to(self):
        return _ok(self._khung.dang_phong_to())

    @_bat_loi
    def cua_so_dong(self):
        self._window.destroy()
        return _ok(True)

    @_bat_loi
    def set_title(self, ten):
        if self._window:
            self._window.set_title(f"{ten} — {self._HAU_TO}" if ten else self._HAU_TO)
        return _ok(True)


class ApiKetQua(NenCuaSo):
    """js_api của MỘT CỬA SỔ KẾT QUẢ — mỗi cửa sổ một thể hiện.

    Bề mặt hẹp CÓ CHỦ Ý: cửa sổ này chỉ đọc một lượt đã chạy rồi bày ra. Nó không
    sửa sơ đồ, không chạy backtest, không đụng tới Strategy nào — nên nó cũng không
    cần cửa nào của `Api`. Đưa cả `Api` cho nó là đưa luôn `xoa_strategy` và
    `qc_luu_khoa` vào một cửa sổ chẳng có lý do gì chạm tới chúng.

    Phần cửa sổ (✕, thu nhỏ, phóng to, kéo thanh tiêu đề) thừa kế từ `NenCuaSo`, nên
    mỗi cửa sổ tự nhắm vào CHÍNH MÌNH — xem docstring lớp ấy, ba lỗi nó kể đều đã
    xảy ra thật."""

    def __init__(self, ma_id):
        super().__init__()
        self._ma_id = str(ma_id)

    @_bat_loi
    def ping(self):
        return _ok("pong")

    @_bat_loi
    def doc_luot_chay(self, ma_id=None):
        """Lượt chạy của cửa sổ này. Bỏ qua mã JS gửi lên — cửa sổ nào thì lượt ấy,
        không để một cửa sổ đọc sang lượt của cửa sổ khác."""
        kq = chay_lean.doc_luot_chay(self._ma_id)
        return _ok(kq) if kq["ok"] else _loi(kq["loi"])


def _so_do_theo_ten_lop(ten_lop):
    """Dò trong kho Strategy ra sơ đồ sinh đúng lớp `ten_lop`. -> doc, hay {}.

    Lối CỨU cho mấy mẻ chạy trước khi mẻ biết giữ sơ đồ. Không phải đoán mò: phép
    tên-chiến-thuật -> tên-lớp là `sinh_ma.ten_lop`, xác định và một chiều, nên dò
    ngược bằng cách chạy xuôi trên từng chiến thuật đã lưu là ra đúng cái cần.

    Trùng tên lớp thì lấy cái đầu — hai chiến thuật ra cùng một tên lớp vốn đã là
    chuyện nên tránh, và ở đây lấy nhầm cũng chỉ mở ra một sơ đồ gần giống."""
    ten_lop = str(ten_lop or "").strip()
    if not ten_lop:
        return {}
    try:
        ds = luu_tru.liet_ke_strategy()
    except OSError:
        return {}
    for ten in ds:
        try:
            doc = core.normalize_process(luu_tru.doc_strategy(ten))
        except (OSError, ValueError):
            continue
        if sinh_ma.ten_lop(doc.get("name") or ten) == ten_lop:
            return doc
    return {}


class ApiToiUu(NenCuaSo):
    """js_api của MỘT CỬA SỔ OPTIMIZE. Cùng lý do bề mặt hẹp như `ApiKetQua`.

    Khác một điểm: cửa sổ này còn mở TRONG LÚC MẺ ĐANG CHẠY, nên nó hỏi `tien_do`
    để bảng và plot đầy dần. Một mẻ hàng trăm lượt mà bắt nhìn màn trống tới lúc
    xong thì không ai biết nó còn sống hay đã treo."""

    def __init__(self, ma_id, bao_chinh=None):
        super().__init__()
        self._ma_id = str(ma_id)
        # HÀM GỌI NGƯỢC về cửa sổ chính, KHÔNG phải cả `Api`. Giữ nguyên lý do bề
        # mặt hẹp: cửa sổ này chỉ cần nói được một câu — "đặt bộ số này vào sơ đồ".
        self._bao_chinh = bao_chinh

    @_bat_loi
    def ping(self):
        return _ok("pong")

    @_bat_loi
    def ap_num(self, tham_so=None):
        """Bấm đúp một dòng xếp hạng -> MỞ ĐÚNG SƠ ĐỒ ẤY với bộ số ấy.

        ⚠ Lấy sơ đồ từ CHÍNH MẺ NÀY, không hỏi canvas đang vẽ gì. Canvas có thể
        đang trống, đang vẽ một chiến thuật khác, hay mẻ này chạy từ tuần trước —
        cả ba trường hợp đều phải ra đúng sơ đồ đã sinh ra bảng xếp hạng này. Đó là
        lý do mẻ giữ cả sơ đồ trong thẻ.

        Đặt số xong ở ĐÂY rồi mới đẩy sang: cửa sổ chính chỉ việc nạp một tài liệu
        đã sẵn sàng, khỏi phải biết luật «con số nằm ở đâu trong khối»."""
        if not self._bao_chinh:
            return _loi(tr("Không nối được tới cửa sổ sơ đồ."))
        me = chay_toi_uu.doc_me(self._ma_id)
        sd = (me.get("so_do") or {}) if me.get("ok") else {}
        if not sd.get("steps"):
            # MẺ CŨ, chạy trước khi mẻ biết giữ sơ đồ. Vẫn cứu được: tên lớp suy ra
            # TỪ tên chiến thuật bằng `sinh_ma.ten_lop`, và phép suy ấy xác định —
            # nên dò ngược trong kho Strategy là tìm đúng sơ đồ, không phải đoán.
            sd = _so_do_theo_ten_lop(me.get("ten_lop") or "")
        if not sd.get("steps"):
            return _loi(tr("Mẻ này chạy từ bản cũ nên không lưu sơ đồ, mà kho Strategy cũng không "
                           "còn cái nào sinh ra lớp \"{0}\". Chạy lại một mẻ mới thì bấm đúp sẽ mở "
                           "được.", me.get("ten_lop") or "?"))
        ds, dat = core.dat_tham_so(sd.get("steps") or [], tham_so or {})
        if not dat:
            # ĐẶT ĐƯỢC 0 NÚM = mở ra cũng chẳng đổi gì, mà lại ghi đè sơ đồ đang vẽ.
            # Gặp khi sơ đồ dò được từ kho Strategy chưa ghim núm nào — bản đã lưu
            # cũ hơn lúc ghim. Nói thẳng, đừng mở một sơ đồ y hệt rồi để người dùng
            # ngồi tìm xem con số nào vừa đổi.
            return _loi(tr("Sơ đồ của mẻ này không còn ô nào ghim {0} — bản đã lưu cũ hơn lúc "
                           "ghim. Mở sơ đồ ra ghim lại rồi chạy một mẻ mới, mẻ ấy sẽ bấm đúp được.",
                           ", ".join(sorted(tham_so or {})) or tr("núm nào")))
        self._bao_chinh({"name": sd.get("name") or me.get("ten_lop") or "",
                         "steps": ds, "edges": sd.get("edges") or [],
                         "dat": dat})
        return _ok({"dat": dat})

    @_bat_loi
    def doc_me(self, ma_id=None):
        """Mẻ của CỬA SỔ NÀY. Bỏ qua mã JS gửi lên — cửa sổ nào thì mẻ ấy."""
        kq = chay_toi_uu.doc_me(self._ma_id)
        return _ok(kq) if kq["ok"] else _loi(kq["loi"])

    @_bat_loi
    def tien_do(self):
        """Mẻ đang tới đâu — cửa sổ hỏi trong lúc nó còn chạy."""
        return _ok(chay_toi_uu.trang_thai())

    @_bat_loi
    def tu_dien_toi_uu(self):
        return _ok(toi_uu.tu_dien())


class Api(NenCuaSo):
    """Mọi phương thức công khai ở đây thành `window.pywebview.api.<tên>` bên JS."""


    @_bat_loi
    def mo_cua_so_ket_qua(self, ma_id):
        """Mở MỘT CỬA SỔ RIÊNG cho một lượt backtest đã lưu.

        VÌ SAO LÀ CỬA SỔ THẬT, không phải một hộp thoại nữa: người ta mở app lên để
        SO HAI PHIÊN BẢN của cùng một chiến thuật. So thì phải nhìn cùng lúc, mà hộp
        thoại thì mỗi lần một cái và nó còn che mất sơ đồ. Cửa sổ thật thì kéo sang
        màn hình khác được, Aero Snap được, xếp cạnh nhau được.

        Cửa sổ mới nạp CHÍNH trang ấy với `?kq=<mã lượt>` — `main.tsx` thấy tham số
        này thì dựng trang Kết quả thay cho sơ đồ. Một bundle, hai vai; không có
        trang thứ hai để lệch khỏi trang thứ nhất.
        """
        import webview
        kq = chay_lean.doc_luot_chay(ma_id)
        if not kq["ok"]:
            return _loi(kq["loi"])

        cu = self._cua_so_kq.get(ma_id)
        if cu is not None:
            try:                      # còn sống thì nâng lên, đừng mở cái nữa
                cu[0].restore()
                return _ok({"id": ma_id, "moi": False})
            except Exception:         # noqa: BLE001 — đã đóng, mở lại bình thường
                self._cua_so_kq.pop(ma_id, None)

        # ⚠ js_api RIÊNG, không phải `self`. Xem docstring `NenCuaSo`: mở cửa sổ thứ
        # hai với `js_api=self` là ba lỗi cùng lúc — ✕ của nó đóng CỬA SỔ CHÍNH, và
        # `KhungTuVe` dùng chung làm hai cửa sổ ghi đè WndProc gốc của nhau, dẫn tới
        # một cửa sổ bị dọn HAI LẦN: `del BrowserView.instances[uid]` của pywebview
        # ném `KeyError('child_…')` ra thẳng hộp thoại .NET. Đã dính thật.
        phu = ApiKetQua(ma_id)
        tieu_de = tr("Kết quả · {0} · {1}", kq['ten_lop'], _doc_ma_luot(kq['ma_luot']))
        w = webview.create_window(
            tieu_de, url=f"{self._window.get_current_url().split('?')[0]}?kq={ma_id}",
            js_api=phu,
            width=1180, height=800, min_size=(900, 600),
            background_color="#202020",
            # Cùng kiểu khung với cửa sổ chính: Windows 10 không cho đổi màu thanh
            # tiêu đề gốc, nên không bỏ khung thì cửa sổ kết quả đội một dải trắng.
            frameless=True, easy_drag=False,
        )
        phu._gan_window(w)
        self._cua_so_kq[ma_id] = (w, phu)
        w.events.closed += lambda: self._cua_so_kq.pop(ma_id, None)
        # Vá khung ở LUỒNG RIÊNG: `_va_khung` thử lại trong bốn giây, mà cú gọi này
        # đi qua cầu nối nên chặn ở đây là đóng băng giao diện ngần ấy lâu.
        # `phu._va_khung` chứ không `self._va_khung`: mỗi cửa sổ vá KHUNG CỦA MÌNH.
        def va_va_bao():
            # VÁ HỤT THÌ NÓI. Không vá được là cửa sổ ấy không kéo, không giãn, không
            # Aero Snap — mà nhìn vào thì y hệt một cửa sổ bình thường. Im lặng ở đây
            # là để người dùng ngồi thử đi thử lại một dải tiêu đề đã chết.
            if not phu._va_khung(tieu_de):
                print(f"[cửa sổ kết quả] KHÔNG vá được khung «{tieu_de}» — "
                      f"cửa sổ này sẽ không kéo/giãn được", file=sys.stderr)

        threading.Thread(target=va_va_bao, daemon=True).start()
        return _ok({"id": ma_id, "moi": True})

    @_bat_loi
    def hanh_trinh(self):
        """CẢ HÀNH TRÌNH — 9 hồi, 26 màn, màn nào đang mở, màn nào mấy sao.

        Giao diện KHÔNG khai lại một màn nào: bản đồ hỏi cửa này rồi vẽ. Hai nơi cùng
        giữ danh sách màn thì sớm muộn lệch nhau, mà cái lệch ấy chỉ lộ ra ở hồi ít
        người chơi tới nhất."""
        return _ok(hanh_trinh.tu_dien())

    @_bat_loi
    def ds_luot_chay(self):
        """Kho lượt backtest đã lưu, mới nhất trước."""
        return _ok(chay_lean.ds_luot_chay())

    @_bat_loi
    def doc_luot_chay(self, ma_id):
        """Mở lại một lượt đã lưu — trang Kết quả trong cửa sổ riêng gọi cửa này."""
        kq = chay_lean.doc_luot_chay(ma_id)
        return _ok(kq) if kq["ok"] else _loi(kq["loi"])

    @_bat_loi
    def xoa_luot_chay(self, ma_id):
        """Xoá hẳn một lượt đã lưu."""
        r = chay_lean.xoa_luot_chay(ma_id)
        return _ok(True) if r["ok"] else _loi(r["loi"])

    def __init__(self):
        super().__init__()
        self._cai_dat = core.load_settings()
        # CHỐT NGÔN NGỮ NGAY ĐÂY, trước khi một câu nào của Python được dựng. `ngon_ngu.hien`
        # có lối tự đọc cài đặt khi chưa ai báo, nhưng đó là lưới an toàn cho lúc chạy rời —
        # đường chính phải là một lời khai rõ ràng, ở chỗ app bắt đầu.
        ngon_ngu.dat(core.ngon_ngu(self._cai_dat))

    # ------------------------------------------------------------------ cơ bản
    @_bat_loi
    def ping(self):
        return _ok("pong")

    # ------------------------------------------------------------------ kho
    @_bat_loi
    def kho_danh_muc(self):
        """App đang có gì trên đĩa. Từ điển khối đã xoá cùng khối cũ (D-12) — mục này
        dựng lại khi có bộ khối mới."""
        return _ok({"luu_tru": luu_tru.tom_tat()})

    # --------------------------------------------------------------- sơ đồ
    # MỘT CỬA SOÁT DUY NHẤT. Giao diện gọi `soat` sau MỖI thay đổi và vẽ lại cái nhận
    # về — nó không tự tính số thứ tự, không tự ghép chữ trên thẻ, không tự soát luật
    # nào. Nhờ vậy huy hiệu trên khối không thể nói khác thứ lõi hiểu.

    @_bat_loi
    def tu_dien_hoi(self):
        """Từ điển XÁC NHẬN — năm loại câu hỏi và kho đại lượng của từng loại.

        Giao diện KHÔNG tự khai danh sách này: nó hỏi Python. Hai nơi cùng giữ một
        bảng thì sớm muộn lệch nhau, và lúc ấy hộp thoại bày ra một đại lượng mà bộ
        sinh mã không biết viết."""
        return _ok(hoi.tu_dien())

    @_bat_loi
    def sinh_ma(self, ten, steps, edges=None, ghi=False, co_may=None):
        """Sơ đồ -> thuật toán LEAN Python. `ghi` True thì ghi luôn ra file.

        Trả cả `van_de`: có lỗi thì `ok` False và ĐừNG chạy file ấy — nhưng vẫn đưa
        mã ra để người chơi nhìn thấy sơ đồ của mình thành cái gì."""
        kq = sinh_ma.sinh(core.make_process_template(ten, steps, edges, co_may))
        if ghi and kq["ma"]:
            kq["duong"] = luu_tru.ghi_ma(kq["ten_lop"], kq["ma"])
        return _ok(kq)

    @_bat_loi
    def lean_san_sang(self):
        """LEAN đã trỏ đúng chỗ chưa — để màn Chạy nói rõ thiếu gì trước khi bấm."""
        return _ok(chay_lean.san_sang())

    @_bat_loi
    def lean_dat_goc(self, duong):
        """Trỏ chỗ đặt LEAN. Trả luôn trạng thái sau khi đặt."""
        s = luu_tru.doc_cai_dat()
        s[chay_lean.KHOA_LEAN] = str(duong or "").strip()
        luu_tru.ghi_cai_dat(s)
        return _ok(chay_lean.san_sang())

    @_bat_loi
    def cai_dat_tu_dien(self):
        """Từ điển CÀI ĐẶT — hộp Cài đặt hỏi, không tự khai danh sách ô."""
        return _ok(cai_dat.tu_dien())

    @_bat_loi
    def cai_dat_doc(self):
        """Giá trị đang lưu, đã rơi về mặc định cho ô thiếu."""
        return _ok(cai_dat.doc(luu_tru.doc_cai_dat()))

    @_bat_loi
    def cai_dat_ghi(self, gia_tri):
        """Lưu cài đặt. Trả về giá trị ĐÃ ĐỌC LẠI, không phải thứ vừa gửi lên —
        ô gõ bậy đã rơi về mặc định ở `cai_dat.doc`, và giao diện phải thấy điều đó.

        Trả kèm trạng thái LEAN: đổi thư mục xong thì câu trả lời «đã đúng chưa»
        phải tới ngay, không bắt người dùng bấm Chạy rồi mới biết."""
        # ⚠ GỘP TRƯỚC RỒI MỚI CHUẨN HOÁ, không chuẩn hoá riêng phần vừa gửi lên.
        #
        # ĐÃ MẤT DỮ LIỆU THẬT VÌ CHỖ NÀY. `cai_dat.doc()` luôn dựng một dict ĐỦ MỌI Ô,
        # ô nào không có trong thứ đưa vào thì lấy MẶC ĐỊNH. Nên `doc({"ngon_ngu":"vi"})`
        # trả về một bản cài đặt đầy đủ với `lean_goc` RỖNG, và `s.update(...)` đem cái
        # rỗng ấy đè lên đường dẫn LEAN thật. Người dùng chỉ đổi mỗi thứ tiếng, mà mất
        # luôn chỗ trỏ LEAN — không một lời báo nào, và chỉ lộ ra ở lần bấm Backtest sau.
        #
        # Hộp Cài đặt cũ gửi lên ĐỦ mọi ô nên không lộ. Ô đổi tiếng ở màn Mở máy chỉ gửi
        # một ô, và nó làm bay đường dẫn LEAN ngay lần bấm đầu tiên.
        s = luu_tru.doc_cai_dat()
        s = cai_dat.doc({**s, **(gia_tri or {})})
        luu_tru.ghi_cai_dat(s)
        # Đổi tiếng thì PHÍA PYTHON phải biết ngay, không đợi mở lại app: mặt khối và bảng
        # Vấn đề do Python dựng, mà giao diện vẽ lại chúng ngay sau khi hộp Cài đặt đóng.
        ngon_ngu.dat(core.ngon_ngu(s))
        return _ok({"gia_tri": cai_dat.doc(s), "lean": chay_lean.san_sang()})

    @_bat_loi
    def chay_backtest(self, ten, steps, edges=None, co_may=None):
        """Vẽ -> sinh -> KHỞdI ĐỘNG backtest, rồi trả về NGAY.

        KHÔNG chờ chạy xong: một lượt mất từ chục giây tới vài phút, mà cầu nối chặn
        thì giao diện không hỏi được tiến độ — nó chỉ ngồi im cho tới lúc xong, và
        người dùng tưởng app treo. Giao diện gọi cửa này rồi hỏi `tien_do_backtest`.

        Sinh mã còn lỗi thì DỪNG LẠI: chạy một file sinh từ sơ đồ đã hỏng chỉ ra một
        thông báo của LEAN khó hiểu hơn hẳn bảng Vấn đề."""
        kq = sinh_ma.sinh(core.make_process_template(ten, steps, edges, co_may))
        if not kq["ok"]:
            return _ok({"ok": False, "van_de": kq["van_de"],
                        "loi": tr("Sơ đồ còn chỗ chưa diễn đạt hết — xem bảng Vấn đề.")})
        # TÊN MỐC phải nói thật. LEAN KHÔNG ghi lại nó trong file kết quả, mà để trống
        # thì nó lặng lẽ lấy SPY — biểu đồ ghi "Mốc so sánh" chung chung là giấu mất
        # chuyện cỗ máy vàng đang bị đem so với cổ phiếu Mỹ.
        m = str(core.o_may(core.chuan_hoa_co_may(co_may, steps),
                           "moc_so_sanh") or "").strip().upper()
        # Những thứ chỉ LÚC SINH mới biết, giữ lại để gắn vào kết quả lúc xong.
        self._kem = {"van_de": kq["van_de"], "ma": kq["ma"],
                     "ten_lop": kq["ten_lop"],
                     "moc_ten": m or tr("SPY — LEAN tự chọn")}
        return _ok(chay_lean.bat_dau_chay(kq["ma"], kq["ten_lop"]))

    @_bat_loi
    def tu_dien_toi_uu(self):
        """Từ điển Optimize — cách tìm, phép so, 27 chỉ tiêu, mặc định."""
        return _ok(toi_uu.tu_dien())

    @_bat_loi
    def num_cua_so_do(self, steps=None):
        """Mấy núm sơ đồ đang ghim -> hộp Optimize bày đúng danh sách này.

        ĐỌC THẲNG TỪ SƠ ĐỒ, không giữ bảng riêng: bảng riêng thì sớm muộn trỏ vào
        một ô đã bị xoá, và optimizer lặng lẽ quét một tham số không ai đọc."""
        return _ok(core.ds_tham_so(
            [core.chuan_hoa_khoi(s) for s in (steps or [])]))

    @_bat_loi
    def chay_toi_uu(self, ten, steps, edges=None, cai=None, co_may=None):
        """Vẽ -> sinh -> KHỞI ĐỘNG một mẻ Optimize, rồi trả về NGAY.

        Cùng lý do không chờ như `chay_backtest`, chỉ là nặng hơn hẳn: một mẻ là
        HÀNG TRĂM lượt backtest."""
        doc = core.make_process_template(ten, steps, edges, co_may)
        kq = sinh_ma.sinh(doc)
        if not kq["ok"]:
            return _ok({"ok": False, "van_de": kq["van_de"],
                        "loi": tr("Sơ đồ còn chỗ chưa diễn đạt hết — xem bảng Vấn đề.")})
        # SƠ ĐỒ đi theo mẻ: bấm đúp một dòng xếp hạng sau này phải mở lại ĐÚNG sơ đồ
        # ấy, kể cả khi canvas đang trống hay đang vẽ chiến thuật khác.
        return _ok(chay_toi_uu.bat_dau_chay(kq["ma"], kq["ten_lop"], cai or {}, doc))

    @_bat_loi
    def dung_toi_uu(self):
        r = chay_toi_uu.dung()
        return _ok(True) if r["ok"] else _loi(r["loi"])

    @_bat_loi
    def tien_do_toi_uu(self):
        return _ok(chay_toi_uu.trang_thai())

    @_bat_loi
    def ds_me_toi_uu(self):
        return _ok(chay_toi_uu.ds_me())

    @_bat_loi
    def xoa_me_toi_uu(self, ma_id):
        r = chay_toi_uu.xoa_me(ma_id)
        return _ok(True) if r["ok"] else _loi(r["loi"])

    @_bat_loi
    def mo_cua_so_toi_uu(self, ma_id):
        """Mở MỘT CỬA SỔ RIÊNG cho một mẻ Optimize. Cùng lối `mo_cua_so_ket_qua`:
        một bundle hai vai, `?tu=<mã mẻ>`, js_api RIÊNG (xem docstring cửa kia —
        dùng chung `self` đã từng ném `KeyError('child_…')` ra hộp thoại .NET)."""
        import webview
        kq = chay_toi_uu.doc_me(ma_id)
        if not kq["ok"]:
            return _loi(kq["loi"])
        cu = self._cua_so_tu.get(ma_id)
        if cu is not None:
            try:
                cu[0].restore()
                return _ok({"id": ma_id, "moi": False})
            except Exception:                           # noqa: BLE001
                self._cua_so_tu.pop(ma_id, None)
        def _bao(ts):
            # Đẩy sang JS của cửa sổ chính, rồi ĐƯA NÓ LÊN TRƯỚC HẲN.
            #
            # ⚠ `restore()` KHÔNG ĐỦ: nó chỉ bỏ trạng thái thu nhỏ. Cửa sổ sơ đồ
            # đang nằm DƯỚI cửa sổ Optimize thì `restore()` chẳng đổi gì — người
            # dùng bấm đúp, sơ đồ đổi thật, mà họ vẫn đang nhìn bảng xếp hạng nên
            # tưởng không có gì xảy ra. Phải nâng bằng Win32.
            self._ban("mo_so_do", ts)
            try:
                self._window.restore()
            except Exception:                           # noqa: BLE001
                pass
            # Tiêu đề cửa sổ chính LUÔN kết thúc bằng hậu tố ấy (`set_title`), còn
            # cửa sổ Kết quả và Optimize thì không — nên chuỗi này chỉ khớp đúng một
            # cửa sổ: cửa sổ sơ đồ.
            khung_cua_so.dua_len_truoc(khung_cua_so.tim_hwnd(self._HAU_TO))

        phu = ApiToiUu(ma_id, _bao)
        tieu_de = (f"Optimize · {kq.get('ten_lop', '')} · "
                   f"{_doc_ma_luot(kq.get('ma_luot') or '')}")
        w = webview.create_window(
            tieu_de,
            url=f"{self._window.get_current_url().split('?')[0]}?tu={ma_id}",
            js_api=phu, width=1180, height=800, min_size=(900, 600),
            background_color="#202020", frameless=True, easy_drag=False)
        phu._gan_window(w)
        self._cua_so_tu[ma_id] = (w, phu)
        w.events.closed += lambda: self._cua_so_tu.pop(ma_id, None)

        # ⚠ BẢN TRƯỚC GỌI `phu._va_khung` KHÔNG THAM SỐ — mà nó đòi `chua_chuoi`.
        # Luồng nền ném `TypeError` rồi chết IM, nên khung cửa sổ Optimize không bao
        # giờ được vá: thanh tiêu đề không kéo, không giãn, không Aero Snap, mà nhìn
        # vào thì y hệt một cửa sổ bình thường. Đúng lỗi đã dính ở cửa sổ Kết quả.
        def va_va_bao():
            if not phu._va_khung(tieu_de):
                print(f"[cửa sổ Optimize] KHÔNG vá được khung «{tieu_de}» — "
                      f"cửa sổ này sẽ không kéo/giãn được", file=sys.stderr)

        threading.Thread(target=va_va_bao, daemon=True).start()
        return _ok({"id": ma_id, "moi": True})

    @_bat_loi
    def dung_backtest(self):
        """DỪNG lượt backtest đang chạy — giết thẳng tiến trình LEAN."""
        r = chay_lean.dung()
        return _ok(True) if r["ok"] else _loi(r["loi"])

    @_bat_loi
    def tien_do_backtest(self):
        """Lượt chạy đang tới đâu — giao diện hỏi mỗi nửa giây.

        ⚠ KHÔNG CÓ PHẦN TRĂM, và đó là cố ý: LEAN không in tiến độ ra màn hình
        (`BacktestProgressMonitor` chỉ đẩy số ấy vào gói gửi lên đám mây). Bịa một con
        số còn tệ hơn không có — nó hứa một cái mốc mà không ai giữ được."""
        t = chay_lean.trang_thai()
        kq = t.pop("kq", None)
        if t["xong"] and isinstance(kq, dict):
            t["ket_qua"] = {**kq, **getattr(self, "_kem", {})} if kq.get("ok") else kq
        return _ok(t)

    @_bat_loi
    def tu_dien_bat_dau(self):
        """Từ điển KHỐI BẮT ĐẦU — sáu ô thiết lập, loại tài sản, nhịp chạy.

        Cùng lý do như hai cửa từ điển kia: giao diện hỏi Python chứ không tự khai."""
        return _ok(bat_dau.tu_dien())

    @_bat_loi
    def khai_bat_dau(self, gia_tri=None):
        """Mấy câu LEAN khối Bắt đầu ĐANG khai -> [câu]. Hỏi sau MỖI thay đổi.

        KHÔNG gộp vào `tu_dien_bat_dau`: từ điển là bảng TĨNH, gửi một lần lúc mở
        app, còn mấy câu này đổi theo đúng thứ người dùng đang gõ trong hộp thoại
        (nhịp, độ phân giải, rổ nào, lấy mấy mã). Cùng lối với cửa `soat`: gọi sau
        mỗi thay đổi rồi bày lại cái nhận về.

        Vì sao phải có cửa này: giao diện BÀY LẠI, không tự ghép. Hai nơi cùng ghép
        một câu thì sớm muộn chúng tả khác nhau, mà cái khác ấy không gây lỗi nào
        nên không ai thấy — xem docstring `core.mo_ta_lam`."""
        return _ok(bat_dau.khai(gia_tri))

    @_bat_loi
    def tu_dien_lam(self):
        """Từ điển HÀNH ĐỘNG — tám loại việc, và các ô của từng loại.

        Cùng lý do như `tu_dien_hoi`: giao diện hỏi Python chứ không tự khai danh
        sách, để hộp thoại không bao giờ bày ra một ô mà lõi chẳng biết là gì."""
        return _ok(lam.tu_dien())

    @_bat_loi
    def khoi_moi(self, kind, loai=None):
        """Một khối mới + thẻ vẽ của nó."""
        if kind == core.KIND_GROUP:
            st = core.make_group_step()
        elif kind == core.KIND_START:
            st = core.make_start_step()
        elif loai == core.QUAY_VE:
            st = core.make_quay_ve_step()
        elif hoi.la_loai_hoi(loai):
            st = core.make_hoi_step(loai)
        elif lam.la_loai_lam(loai):
            st = core.make_lam_step(loai)
        else:
            # ⚠ KHÔNG RƠI VỀ `CHECK_COND` NỮA — nó là loại của BỘ KHỐI ĐÃ CHẾT (D-12).
            # «Thêm Khối lẻ» trong menu chuột phải gọi thẳng vào nhánh này, nên mỗi
            # lần bấm là đẻ ra một khối KHÔNG từ điển nào nhận: bấm đúp vào nó không
            # mở hộp nào, Build thì sinh ra `pass`. Hỏng ngay từ lúc sinh, mà chẳng
            # gì báo — `soat_loai_la` nay bắt được, và đây là chỗ chặn từ gốc.
            #     Rơi về HỎI THỊ TRƯỜNG: `check_cond` xưa nay là CỔNG rẽ nhánh
            # (`is_branch_gate`), mà cổng của bộ khối đang sống chính là khối Hỏi.
            st = core.make_hoi_step(hoi.HOI_THI_TRUONG)
        return _ok({"step": st, "card": core.the_buoc(st)})

    @_bat_loi
    def goi_y_ke(self, steps, edges=None, chon=None):
        """NỐI THÔNG MINH: sau khối đang chọn thì thường là gì. -> [khối mờ]

        Cửa RIÊNG chứ không đi kèm `soat`: nó đổi theo thứ đang CHỌN, mà chọn thì đổi
        mỗi cú bấm chuột — nhét vào `soat` là mỗi lần bấm một khối lại chạy cả lượt
        đánh số, soát lỗi và dựng thẻ cho cả sơ đồ."""
        return _ok(core.goi_y_ke(steps, edges, chon))

    @_bat_loi
    def gom_nhom(self, steps, ten=None):
        """Mấy khối Hành động đang chọn -> MỘT Nhóm (Ctrl+G)."""
        nhom, loi = core.gom_nhom(steps, ten)
        if loi:
            return _loi(loi)
        return _ok({"step": nhom, "card": core.the_buoc(nhom)})

    @_bat_loi
    def ra_nhom(self, step):
        """Một Nhóm -> từng khối Hành động (Ctrl+Shift+G)."""
        ds, loi = core.ra_nhom(step)
        if loi:
            return _loi(loi)
        return _ok({"steps": ds, "the": [core.the_buoc(s) for s in ds]})

    @_bat_loi
    def soat(self, steps, edges=None, co_may=None):
        """Tất cả những gì giao diện cần để vẽ lại sơ đồ sau một thay đổi.

        Gộp làm MỘT cửa chứ không ba: đánh số, soát lỗi và dựng thẻ đều đọc cùng một
        đồ thị, tách ra thì ba lượt gọi có thể thấy ba trạng thái khác nhau."""
        steps = core.ensure_step_ids([s for s in (steps or []) if isinstance(s, dict)])
        edges = core.clean_edges(edges, steps) if edges is not None \
            else core.default_edges(steps)
        kq = core.flow_order(steps, edges)
        # HỒ SƠ CỖ MÁY — giao diện gửi kèm; thiếu thì lôi từ khối Bắt đầu (file cũ).
        may = core.chuan_hoa_co_may(co_may, steps)
        # Bảng Vấn đề = lỗi ĐỒ THỊ (nối dây) + lỗi RUỘT từng khối. Gộp ở đây chứ
        # không ở `validate_flow_graph`: cái đó chỉ biết về dây, cố ý vậy.
        van_de = core.validate_flow_graph(steps, edges)
        for s in steps:
            van_de.extend(core.soat_khoi_hoi(s))
            van_de.extend(core.soat_khoi_lam(s))
            van_de.extend(core.soat_khoi_bat_dau(s, may))
            # Hành động nằm trong một Nhóm cũng phải soát — khối Nhóm không có `type`
            # của riêng nó, nên vòng trên không chạm tới ruột nó.
            for a in core.hanh_dong_cua(s):
                if a is not s:
                    van_de.extend(core.soat_khoi_lam({**a, "id": s["id"]}))
        # Soát CHÉO khối: chạy cả rổ thì mọi khối phải gõ rõ tên mã. Một khối nhìn
        # vào chính nó thì không biết khối Bắt đầu đang chạy kiểu nào.
        van_de.extend(core.soat_loai_la(steps))
        van_de.extend(core.soat_ca_ro(steps))
        van_de.extend(core.soat_ro_dong(steps))
        van_de.extend(core.soat_day_chuyen(steps, may))
        # Bảng TÊN ô nhớ — khai ở khối Bắt đầu, mà thẻ cần vẽ ở khối Ghi nhớ.
        _tn = core.ten_nho_cua(may)
        return _ok({
            "thu_tu": kq["order"],
            "entry": kq["entry"],
            "the": {s["id"]: core.the_buoc(s, _tn) for s in steps},
            # CỖ MÁY LEAN — mấy chữ cho viên thuốc ở góc phải canvas, và hồ sơ
            # đã chuẩn hoá (giao diện dùng nó để mở hộp Cỗ máy, và để lưu). Đi CÙNG
            # cửa soát chứ không thành cửa riêng: tách ra là mời hai lượt gọi thấy
            # hai trạng thái khác nhau.
            "co_may": may,
            "tom_tat_co_may": core.tom_tat_co_may(may),
            "van_de": van_de,
            "vong": {a: list(b) for a, b in core.canh_vong(edges, steps).items()},
            "edges": edges,
        })

    @_bat_loi
    def nhan_ban(self, steps, edges=None, giu_hat_nhan=False, co_may=None):
        """Chép một mảng khối, cấp id mới. Đích Quay về trỏ ra ngoài mảng bị để TRỐNG."""
        moi, day, bang = core.clone_steps(steps, edges, giu_hat_nhan)
        _tn = core.ten_nho_cua(core.chuan_hoa_co_may(co_may, steps))
        return _ok({"steps": moi, "edges": day, "map": bang,
                    "the": {s["id"]: core.the_buoc(s, _tn) for s in moi}})

    # -------------------------------------------------------- lưu / mở Strategy
    @_bat_loi
    def ds_strategy(self):
        """Kho có những gì, và dòng nào là BẢN TỰ LƯU.

        Python nói ra, không để giao diện tự đoán theo đuôi tên: quy ước đặt tên bản
        tự lưu là của `luu_tru`, mà hai nơi cùng biết một quy ước thì sớm muộn lệch."""
        return _ok([{"ten": t, "tuLuu": luu_tru.la_tu_luu(t)}
                    for t in luu_tru.liet_ke_strategy()])

    @_bat_loi
    def doi_ten_strategy(self, cu, moi):
        """Đổi tên một Strategy. Tên mới trùng cái đã có thì KHÔNG đè — báo lỗi.

        Đổi tên là thao tác không hoàn tác được ở mức file, nên thà bắt chọn tên khác
        còn hơn lặng lẽ nuốt mất một bản."""
        cu = (cu or "").strip()
        moi = (moi or "").strip()
        if not moi:
            return _loi(tr("Tên mới không được để trống."))
        if moi == cu:
            return _ok({"ten": cu})
        if moi in luu_tru.liet_ke_strategy():
            return _loi(tr("Đã có Strategy tên \"{0}\". Hãy chọn tên khác.", moi))
        doc = core.normalize_process(luu_tru.doc_strategy(cu))
        doc["name"] = moi
        luu_tru.ghi_strategy(moi, doc)
        luu_tru.xoa_strategy(cu)
        # Bản tự lưu của tên CŨ không còn chủ — xoá theo, không để lại một file mồ côi
        # mang tên một Strategy không còn tồn tại.
        luu_tru.xoa_strategy(luu_tru.ten_tu_luu(cu))
        return _ok({"ten": moi})

    @_bat_loi
    def nhan_ban_strategy(self, ten, ten_moi):
        """Chép một Strategy sang tên khác. Không đè bản đã có."""
        ten_moi = (ten_moi or "").strip()
        if not ten_moi:
            return _loi(tr("Tên bản sao không được để trống."))
        if ten_moi in luu_tru.liet_ke_strategy():
            return _loi(tr("Đã có Strategy tên \"{0}\". Hãy chọn tên khác.", ten_moi))
        doc = core.normalize_process(luu_tru.doc_strategy(ten))
        doc["name"] = ten_moi
        # Cấp id MỚI cho mọi khối: hai bản dùng chung id thì dán khối của bản này sang
        # bản kia là trùng id, và `validate_flow_graph` báo "khối biến mất khỏi sơ đồ".
        moi, day, _ = core.clone_steps(doc["steps"], doc["edges"], giu_hat_nhan=True)
        doc["steps"], doc["edges"] = moi, day
        luu_tru.ghi_strategy(ten_moi, doc)
        return _ok({"ten": ten_moi})

    @_bat_loi
    def luu_strategy(self, ten, steps, edges=None, co_may=None):
        doc = core.make_process_template(ten, steps, edges, co_may)
        p = luu_tru.ghi_strategy(doc["name"], doc)
        # Lưu thật xong thì bản tự lưu hết việc — việc dở đã thành việc lưu.
        luu_tru.xoa_strategy(luu_tru.ten_tu_luu(doc["name"]))
        return _ok({"ten": doc["name"], "duong": p})

    @_bat_loi
    def mo_strategy(self, ten):
        return _ok(core.normalize_process(luu_tru.doc_strategy(ten)))

    @_bat_loi
    def xoa_strategy(self, ten):
        return _ok(luu_tru.xoa_strategy(ten))

    @_bat_loi
    def tu_luu_strategy(self, ten, steps, edges=None, co_may=None):
        """Bản tự lưu nằm cạnh Strategy gốc. CHỈ đẻ ra khi nội dung thật sự khác bản trên
        đĩa — mở ra xem mà không sửa gì thì không đẻ ra file nào."""
        ten = luu_tru.ten_goc_cua(ten)
        if not ten:
            return _ok(None)          # chưa lưu lần nào: bản nháp lo, không phải chỗ này
        doc = core.make_process_template(ten, steps, edges, co_may)
        try:
            cu = core.normalize_process(luu_tru.doc_strategy(ten))
            if cu["steps"] == doc["steps"] and cu["edges"] == doc["edges"]:
                return _ok(None)
        except Exception:
            pass
        doc["name"] = luu_tru.ten_tu_luu(ten)
        return _ok({"ten": doc["name"], "duong": luu_tru.ghi_strategy(doc["name"], doc)})

    # ------------------------------------------------------------- bản nháp
    @_bat_loi
    def luu_ban_nhap(self, ten, steps, edges=None, co_may=None):
        """Việc đang dở của cửa sổ — kể cả cỗ máy chưa từng lưu. Không đụng file cỗ máy."""
        doc = core.make_process_template(ten or "", steps, edges, co_may)
        return _ok(luu_tru.ghi_ban_nhap(doc))

    @_bat_loi
    def doc_ban_nhap(self):
        d = luu_tru.doc_ban_nhap()
        return _ok(core.normalize_process(d) if d else None)

    @_bat_loi
    def xoa_ban_nhap(self):
        return _ok(luu_tru.xoa_ban_nhap())

    def dong_app(self):
        """Cửa sổ chính đóng. KHÔNG bọc `_bat_loi`: pywebview gọi nó từ sự kiện `closing`,
        không phải từ JS. Hiện không phải dọn gì — cửa sổ thứ hai đã gỡ cùng D-12 — nhưng
        giữ chỗ vì `app_web.py` đã nối sự kiện vào đây."""
        return None

    # ------------------------------------------------------------------ khoá QC
    # D-12: bốn cửa này trước ở `ApiQC` — bề mặt của cửa sổ Màn chơi. Cửa sổ đó đã gỡ
    # cùng bộ khối cũ, mà hộp Khoá thì vẫn phải mở được, nên chúng về ĐÚNG chỗ: cửa sổ
    # chính. Bản xem thử (`tools/xem_thu.py`) từng che lỗi này vì nó tự định tuyến mọi
    # tên `qc_*` sang `ApiQC`; nay cả hai cùng một bề mặt nên không che được nữa.
    @_bat_loi
    def qc_khoa(self):
        return _ok(qc_api.trang_thai_khoa())

    @_bat_loi
    def qc_luu_khoa(self, user_id, token):
        """Lưu khoá từ ô nhập trong app vào `du_lieu/qc_khoa.json`. Không trả lại token."""
        try:
            return _ok(qc_api.luu_khoa(user_id, token))
        except qc_api.LoiKhoa as e:
            return _loi(str(e))

    @_bat_loi
    def qc_xoa_khoa(self):
        return _ok(qc_api.xoa_khoa())

    @_bat_loi
    def qc_kiem_khoa(self):
        """Hỏi thử QC khoá có dùng được không (vài trăm mili giây)."""
        try:
            qc_api.QC(*qc_api.doc_khoa()).kiem_khoa()
        except qc_api.LoiQC as e:
            return _loi(str(e))
        return _ok(True)

    @_bat_loi
    def mo_thu_muc(self, loai="goc"):
        """Mở một thư mục dữ liệu bằng Explorer của Windows.

        VÌ SAO CÓ CỬA NÀY: app ghi Strategy, mã sinh ra, kết quả backtest và nhật ký
        vào `du_lieu/`, mà người dùng thì không có đường nào tới đó ngoài việc tự đi
        tìm xem app nằm ở ổ nào. Chép một file kết quả cho người khác xem, hay thả
        một Strategy ai gửi vào — hai việc rất thường, và cả hai đang phải làm vòng.

        ⚠ CHỈ MỞ MẤY THƯ MỤC KHAI SẴN. `loai` tới từ giao diện; ghép thẳng vào đường
        dẫn là mở bất cứ chỗ nào trên máy."""
        bang = {
            "goc": luu_tru.goc,
            "strategy": luu_tru.thu_muc_strategy,
            "ma": luu_tru.thu_muc_ma,
            "ket_qua": luu_tru.thu_muc_ket_qua,
        }
        f = bang.get(str(loai or "goc"))
        if not f:
            return _loi(tr("Không có thư mục \"{0}\".", loai))
        d = f()
        if not os.path.isdir(d):
            return _loi(tr("Chưa có thư mục {0}.", d))
        # `explorer.exe` trả mã thoát 1 KỂ CẢ KHI MỞ ĐƯỢC — đừng đọc mã thoát của nó.
        subprocess.Popen(["explorer.exe", os.path.normpath(d)])
        return _ok(True)

    @_bat_loi
    def qc_mo_web(self, url):
        """Mở trang backtest trên quantconnect.com bằng trình duyệt của máy. CHỈ link của QC."""
        url = str(url or "")
        if not url.startswith("https://www.quantconnect.com/"):
            return _loi(tr("Chỉ mở link của quantconnect.com."))
        import webbrowser
        webbrowser.open(url)
        return _ok(True)
