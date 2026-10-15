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
import sys
import threading
import time
import traceback

from . import core
from . import mau_tram
from . import may as M
from . import tram as T
if sys.platform == "win32":
    from . import khung_cua_so
else:
    # Không phải Windows thì chỉ có BÀI KIỂM chạy tới đây (Linux/CI). Khung tự vẽ là chuyện
    # của Win32 — `khung_cua_so` gọi `ctypes.windll` ngay lúc nạp — nên thay bằng bản
    # rỗng cho `api.py` nạp được. Trên Windows không đổi gì.
    from . import khung_rong as khung_cua_so
from . import game
from . import qc_api
from . import qc_chay
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


class Api(NenCuaSo):
    """Mọi phương thức công khai ở đây thành `window.pywebview.api.<tên>` bên JS."""

    def __init__(self):
        super().__init__()
        self._qc = None              # cửa sổ Màn chơi (chạy trên QuantConnect)
        self._api_qc = None
        self._doc_qc = None
        #: Việc chạy QC sống ở CỬA SỔ CHÍNH, không ở cửa sổ Màn chơi: đóng cửa sổ lúc đang
        #: chạy rồi mở lại vẫn thấy đúng lượt đó, không mất tiến độ hay kết quả.
        self._viec_qc = None
        self._cai_dat = core.load_settings()
        self._khoa = threading.Lock()

    # ------------------------------------------------------------------ cơ bản
    @_bat_loi
    def ping(self):
        return _ok("pong")

    # ------------------------------------------------ cỗ máy 5 trạm (D-10)
    #: Trình vẽ 5 trạm. Các cửa `may_*` KHÔNG dùng chung với các cửa sơ đồ cũ
    #: (`validate`, `describe`, `save_process`…): hai dạng tài liệu khác hẳn nhau, và
    #: nhập nhằng một cửa cho cả hai là đường ngắn nhất tới chỗ mở chiến lược cũ ra
    #: thành một cỗ máy trắng mà không ai hay.
    _LOC_MAY = "Cỗ máy Cat_Studio (*.json)"

    @_bat_loi
    def may_boot(self):
        """Từ điển 5 trạm — lấy MỘT lần lúc mở trình vẽ.

        Giao diện không viết cứng danh sách nào: thêm một khối Làm, một đại lượng hay một
        mẫu ở `tram.py` / `mau_tram.py` là trình vẽ có ngay. Mẫu trả về CHỈ phần nhãn —
        hàm dựng sơ đồ (`dung`) ở lại Python, việc lắp là của `may_ap_mau`."""
        return _ok({
            "dang": M.DANG,
            "phien_ban": M.PHIEN_BAN,
            "tram": T.TRAM,
            "tram_keys": T.TRAM_KEYS,
            "lich": T.LICH,
            "khung": T.KHUNG,
            "khung_phut": T.KHUNG_PHUT,
            "hoi": T.HOI,
            "nhan_hoi": T.NHAN_HOI,
            "phep_so": T.PHEP_SO,
            "don_vi": T.DON_VI,
            "tham_so_th": T.THAM_SO_TH,
            "toan_hang": T.TOAN_HANG,
            # Đại lượng nào đọc được ở trạm nào — hộp thoại Hỏi chỉ bày ra đúng bộ của
            # trạm đang mở, chứ không bày hết rồi báo lỗi sau.
            "toan_hang_cua_tram": {k: [x["key"] for x in T.toan_hang_cua_tram(k)]
                                   for k in T.TRAM_KEYS},
            "khoi_lam": T.KHOI_LAM,
            "khoi_lam_cua_tram": {k: T.khoi_lam_cua_tram(k) for k in T.TRAM_KEYS},
            "can_co": {k: list(v) for k, v in T.CAN_CO.items()},
            "gom": T.GOM,
            "huong_tin_hieu": T.HUONG_TIN_HIEU,
            "cach_chia": T.CACH_CHIA,
            "cach_tuong_doi": list(T.CACH_TUONG_DOI),
            "mau": {k: [{"key": m["key"], "ten": m["ten"], "qc": m["qc"],
                         "mo_ta": m["mo_ta"]} for m in (mau_tram.MAU.get(k) or [])]
                    for k in T.TRAM_KEYS},
            "may_mau": dict(mau_tram.MAY_MAU),
            # Cỗ máy dựng sẵn của chương 1 — chỉ phần nhãn; dựng là việc của `may_mo_san`.
            "may_san": [{"key": m["key"], "ten": m["ten"], "mo_ta": m["mo_ta"]}
                        for m in mau_tram.MAY_SAN],
        })

    @_bat_loi
    def may_moi(self, ten=None):
        """Cỗ máy trắng: năm trạm, mỗi trạm đúng một khối Bắt đầu."""
        return _ok(M.kem_the(M.may_moi(str(ten).strip() if ten else "Cỗ máy mới")))

    @_bat_loi
    def may_mo_mau(self, chon=None, ma=None):
        """Cỗ máy mẫu — đủ năm trạm, sạch lỗi, chạy được ngay."""
        return _ok(M.kem_the(mau_tram.may_tu_mau(chon=chon, ma=ma)))

    @_bat_loi
    def may_mo_san(self, key, ma=None):
        """Một cỗ máy dựng sẵn của chương 1 — bốn ý tưởng khác hẳn nhau, cái nào mở ra
        cũng SẠCH và chạy được ngay."""
        return _ok(M.kem_the(mau_tram.may_san(key, ma)))

    @_bat_loi
    def may_kem_the(self, doc):
        """Chuẩn hoá + đánh số + chữ trên khối.

        Mọi thay đổi cấu trúc (thêm/xoá khối, nối dây, sửa Gom) gửi CẢ cỗ máy sang đây rồi
        vẽ lại từ cái trả về: chữ trên khối do Python dựng, giao diện không ghép một mẩu
        nào — y luật của sơ đồ cũ."""
        return _ok(M.kem_the(doc))

    @_bat_loi
    def may_soat(self, doc):
        """Nguồn của CHẤM ĐỎ trên dải 5 trạm và của bảng Vấn đề — một lời gọi, cả cỗ máy.

        Soát cả năm trạm chứ không riêng trạm đang mở: giấu lỗi của trạm kia thì bấm ▶ mới
        lòi ra, mà lúc đó không ai hiểu vì sao."""
        ds = M.soat(doc)
        d = M.chuan_hoa(doc)
        tram = {}
        for k in T.TRAM_KEYS:
            g = d["tram"][k]
            kq = core.flow_order(g["steps"], g["edges"])
            cua = [p for p in ds if p.get("tram") == k]
            tram[k] = {
                "order": kq["order"],
                "unreachable": kq["unreachable"],
                "quay_lai": [list(c) for c in kq["quay_lai"]],
                "vong_ho": [list(c) for c in kq["vong_ho"]],
                "lech_nhanh": kq["lech_nhanh"],
                "so_loi": sum(1 for p in cua if p["severity"] == "error"),
                "so_canh_bao": sum(1 for p in cua if p["severity"] == "warning"),
            }
        return _ok(ds,
                   so_loi=sum(1 for p in ds if p["severity"] == "error"),
                   so_canh_bao=sum(1 for p in ds if p["severity"] == "warning"),
                   tram=tram, van_tay=M.van_tay(d))

    @_bat_loi
    def may_khoi_moi(self, tram, kind="action", loai=None, tham_so=None):
        """Khối mới cho trạm `tram`: Bắt đầu, Hỏi, hay một khối Làm của chính trạm đó.

        Ô của khối Làm nhận MẶC ĐỊNH của từ điển (hạn 24 nến, chu kỳ 20…) chứ không phải
        0 — người chơi có thứ hợp lý để sửa, không phải bịa từ số không. Khối Hỏi mới mang
        sẵn một điều kiện «Giá đóng > SMA(20)»: hai vế cùng đơn vị giá và đọc được ở MỌI
        trạm, nên khối vừa tạo đã sạch lỗi, không phải một khối đỏ chờ gõ."""
        tram = tram if tram in T.TRAM_KEYS else T.TRAM_KEYS[0]
        if kind == core.KIND_START:
            st = M.khoi_bat_dau(tram)
        elif loai in T.KHOI_LAM:
            st = M.khoi_lam(loai)
        else:
            st = M.khoi_hoi([{"trai": {"ten": "gia_dong"}, "phep": ">",
                              "phai": {"ten": "sma", "chu_ky": 20}}])
        return self.may_luu_khoi(tram, st, tham_so)

    @_bat_loi
    def may_luu_khoi(self, tram, draft, tham_so=None):
        """Chuẩn hoá + soát MỘT khối. Hộp thoại không tự soát gì — nó gửi bản nháp thô
        sang đây, để luật hợp lệ chỉ nằm ở đúng một chỗ (y như `save_action` của sơ đồ cũ).
        """
        tram = tram if tram in T.TRAM_KEYS else T.TRAM_KEYS[0]
        st, loi = M.soat_khoi(draft, tram, tham_so)
        if st is None:
            return _loi("Khối không đọc được.")
        ts = M.bang_tham_so({"tham_so": tham_so or []})
        return _ok({"step": st, "card": M.the_khoi(st, tram, ts)}, loi=loi)

    @_bat_loi
    def may_ap_mau(self, doc, tram, mau_key, ma=None):
        """Lắp một mẫu dựng sẵn vào MỘT trạm. Tham số của mẫu được thêm vào bảng, tên nào
        đã có thì GIỮ giá trị người chơi đã chỉnh — lắp mẫu không được lặng lẽ đặt lại núm
        vặn đã vặn."""
        goc = doc if M.la_may(doc) else M.may_moi()
        return _ok(M.kem_the(mau_tram.ap_mau(goc, tram, mau_key, ma)))

    # -- kho cỗ máy trên đĩa --
    @_bat_loi
    def may_ds(self):
        return _ok(luu_tru.liet_ke_co_may())

    @_bat_loi
    def may_luu(self, doc):
        d = M.chuan_hoa(doc)
        p = luu_tru.ghi_co_may(d["name"], d)
        return _ok({"path": p, "name": d["name"], "van_tay": M.van_tay(d)})

    @_bat_loi
    def may_mo(self, ten):
        return self._mo_may(luu_tru.doc_co_may(ten), ten)

    @_bat_loi
    def may_xoa(self, ten):
        return _ok(luu_tru.xoa_co_may(ten))

    def _mo_may(self, d, nguon):
        """Một chỗ duy nhất mở cỗ máy từ đĩa — KHÔNG bọc `_bat_loi` (không phải cửa JS).

        Chặn tài liệu không phải cỗ máy NGAY: `may.chuan_hoa` của một chiến lược cũ trả về
        một cỗ máy TRẮNG hợp lệ, nên mở lầm file thì không có lỗi nào, chỉ là năm trạm
        trống trơn — rồi lưu lại là mất hẳn chiến lược đó."""
        if not M.la_may(d):
            return _loi(f"«{nguon}» không phải cỗ máy 5 trạm — mở ở Chiến lược chứ không "
                        f"phải ở đây.")
        return _ok(M.kem_the(d))

    @_bat_loi
    def may_mo_file(self):
        import webview
        r = self._window.create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=False, file_types=(self._LOC_MAY,))
        if not r:
            return {"ok": False}          # người dùng bấm Huỷ — KHÔNG phải lỗi
        with open(r[0], encoding="utf-8") as f:
            return self._mo_may(json.load(f), os.path.basename(r[0]))

    @_bat_loi
    def may_luu_file(self, doc):
        import webview
        d = M.chuan_hoa(doc)
        r = self._window.create_file_dialog(
            webview.FileDialog.SAVE, save_filename=f"{d['name']}.json",
            file_types=(self._LOC_MAY,))
        if not r:
            return {"ok": False}
        p = r if isinstance(r, str) else r[0]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        return _ok({"path": p})

    # ------------------------------------------------------------------ chạy
    @_bat_loi
    def mo_qc(self, doc):
        """◆ Màn chơi — mở cửa sổ chạy cỗ máy trên QuantConnect (D-03 · D-05 · D-06).

        Chặn TRƯỚC nếu sơ đồ còn lỗi: mở cửa sổ ra để nó báo lại đúng mấy lỗi mà bảng Vấn
        đề đã hiện sẵn là bắt người chơi đi hai vòng cho một thông tin.

        CỬA SỔ CÒN SỐNG THÌ GIỮ, chỉ nạp sơ đồ mới và kéo lên trước: vòng chơi thật là
        *sửa → chạy → so*, huỷ rồi tạo lại mỗi lần là mất lượt đang xem, mất bộ lọc nhật ký.

        Chặn TRƯỚC nếu cỗ máy còn lỗi — mở cửa sổ ra để nó báo lại đúng mấy lỗi mà bảng
        Vấn đề đã hiện sẵn là bắt người chơi đi hai vòng cho một thông tin."""
        if not M.la_may(doc):
            return _loi("Tài liệu này không phải cỗ máy 5 trạm.")
        loi = [p for p in M.soat(doc) if p["severity"] == "error"]
        if loi:
            return {"ok": False, "error": "Cỗ máy còn lỗi, chưa chạy được.", "loi": loi}
        d = M.chuan_hoa(doc)
        self._doc_qc = d
        if self._qc is not None:
            self._qc.set_title(f"{d['name']} — Màn chơi")
            self._api_qc._ban("so_do_moi", d)
            self._api_qc._khung.keo_len_truoc()
            return _ok({"da_mo": True})

        import webview
        # Trang giao diện chắc chắn đã có: thiếu nó thì cửa sổ chính đã không mở lên được
        # (`app_web.main`), nên ở đây không có nhánh "chưa build".
        #
        # ⚠ KHÔNG được viết `file:///{trang}`. pywebview coi mọi url mở đầu `file://` là
        # KHÔNG phải local url nên không dựng http server cho cửa sổ đó, mà trang build ra
        # là ES module → origin "null" → Chromium chặn → TRANG TRẮNG. Truyền đường dẫn cục
        # bộ TRẦN thì pywebview tự phục vụ qua http.
        trang = luu_tru.trang_giao_dien()
        self._api_qc = ApiQC(self)
        self._qc = webview.create_window(
            f"{d['name']} — Màn chơi",
            url=f"{trang.replace(os.sep, '/')}?qc=1",
            js_api=self._api_qc,              # ⚠ KHÔNG phải `self` — xem `NenCuaSo`
            width=1180, height=800, min_size=(900, 600),
            background_color="#202020",
            frameless=True, easy_drag=False)
        self._api_qc._gan_window(self._qc)

        def quen_di():
            self._qc = None
            self._api_qc = None

        self._qc.events.closed += quen_di
        # Vá khung phải đợi cửa sổ được map xong — `_va_khung` tự thử lại. Khớp theo
        # "— Màn chơi" chứ không theo tên chiến lược: tên có thể chứa bất cứ chữ gì, kể cả
        # "Cat Studio", và khớp nhầm là vá lên cửa sổ chính.
        aq = self._api_qc
        threading.Thread(target=lambda: aq._va_khung("— Màn chơi"), daemon=True).start()
        return _ok({"da_mo": True})

    # ------------------------------------------------------------------ kho
    @_bat_loi
    def kho_danh_muc(self):
        """App đang có những gì — cho hộp thoại "Kho".

        Gom thẳng từ TỪ ĐIỂN 5 TRẠM (`tram.py`) và bộ mẫu (`mau_tram.py`), nên thêm một
        khối Làm hay một đại lượng ở đó là hộp thoại có ngay, không phải sửa gì ở đây."""
        return _ok({
            "tram": [{"so": t["so"], "ten": t["ten"], "qc": t["qc"], "hoi": t["hoi"],
                      "cho_ai": t["cho_ai"], "ra": t["ra"],
                      "so_khoi_lam": len(T.khoi_lam_cua_tram(t["key"])),
                      "so_dai_luong": len(T.toan_hang_cua_tram(t["key"])),
                      "so_mau": len(mau_tram.MAU.get(t["key"]) or [])}
                     for t in T.TRAM],
            "khoi_lam": [{"key": k, "nhan": v["nhan"], "tram": T.nhan_tram(v["tram"]),
                          "vai": v["vai"], "mo_ta": v["mo_ta"]}
                         for k, v in T.KHOI_LAM.items()],
            "toan_hang": [{"key": t["key"], "nhan": t["nhan"], "nhom": t["nhom"],
                           "don_vi": T.DON_VI.get(t["don_vi"], t["don_vi"]),
                           "tram": ("mọi trạm" if t["tram"] is None
                                    else " · ".join(T.nhan_tram(x) for x in t["tram"])),
                           "mo_ta": t["mo_ta"]}
                          for t in T.TOAN_HANG],
            "may_san": [{"ten": m["ten"], "mo_ta": m["mo_ta"]} for m in mau_tram.MAY_SAN],
            "luu_tru": luu_tru.tom_tat(),
        })

    def dong_app(self):
        """Cửa sổ chính đóng — dọn cửa sổ Màn chơi theo. KHÔNG bọc `_bat_loi`: pywebview
        gọi nó từ sự kiện `closing`, không phải từ JS."""
        try:
            if self._qc:
                self._qc.destroy()
        except Exception:
            pass



# ---------------------------------------------------------------------------
class ApiQC(NenCuaSo):
    """Bề mặt của cửa sổ MÀN CHƠI — chạy cỗ máy trên QuantConnect (D-05 · D-06 · D-07).

    Vỏ MỎNG: luật chơi ở `game`, việc chạy ở `qc_chay`, nói chuyện với QC ở `qc_api`. Ở đây
    chỉ nối chúng với JS và đổi lỗi thành câu. Không nến, không chart nến: kết quả QC không
    mang chuỗi giá về máy (điều khoản dữ liệu của QC) — mỗi lượt tự mang giờ của nó."""

    _HAU_TO = "Màn chơi"

    def __init__(self, cha):
        super().__init__()
        self._cha = cha          # `Api` của cửa sổ chính — giữ sơ đồ và việc chạy QC

    def _viec(self):
        if self._cha._viec_qc is None:
            self._cha._viec_qc = qc_chay.ViecQC()
        return self._cha._viec_qc

    def _ds_man(self):
        """Màn CỦA ĐÚNG DẠNG tài liệu đang mở. Chưa có tài liệu thì bày màn của cỗ máy 5
        trạm — đó là thứ duy nhất app còn vẽ được (D-10, phần 5)."""
        doc = self._cha._doc_qc
        dang = "so_do" if (doc and not M.la_may(doc)) else M.DANG
        return game.danh_sach_man(game.van_tay(doc) if doc else None, dang)

    @_bat_loi
    def ping(self):
        return _ok("pong")

    @_bat_loi
    def qc_boot(self):
        """Mọi thứ cửa sổ Màn chơi cần lúc mở."""
        cd = self._cha._cai_dat or {}
        doc = self._cha._doc_qc
        return _ok({
            "phien_ban": core.PHIEN_BAN,
            "accent": cd.get("accent"),
            "doc": doc,
            # Dạng tài liệu đang chạy: cửa sổ Màn chơi bày ô RỔ mã cho cỗ máy 5 trạm và ô
            # một symbol cho sơ đồ cũ. Hỏi Python chứ không đoán từ hình dạng `doc` bên JS.
            "dang": M.DANG if M.la_may(doc) else "so_do",
            "man": self._ds_man(),
            "loai": game.LOAI,
            "khoa": qc_api.trang_thai_khoa(),
            "do_gon": game.do_gon(doc or {}),
            "tu_do": {"symbol": cd.get("symbol") or "XAUUSD", "tu": "2025-10-01",
                      "den": "2025-12-31", "von": 10_000.0},
            # Chế độ Sáng tạo của cỗ máy 5 trạm: một RỔ mã, kèm loại thị trường (lớp vỏ
            # đăng ký mã theo loại — ngoại hối/CFD qua OANDA, cổ phiếu Mỹ, crypto).
            "tu_do_may": {"ma": [cd.get("symbol") or "XAUUSD"], "loai": "cfd",
                          "tu": "2025-10-01", "den": "2025-12-31", "von": 10_000.0},
            "loai_thi_truong": qc_chay.LOAI_THI_TRUONG,
            "tran_so_ma": qc_chay.TRAN_SO_MA,
            "trang_thai": self._viec().trang_thai(),
            "co_ket_qua": self._viec().ket_qua is not None,
        })

    # ------------------------------------------------------------------ khoá
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

    # ------------------------------------------------------------------ chạy
    @_bat_loi
    def qc_chay(self, loai, man_id=None, tu_do=None):
        """▶ nhanh / ▶ đầy đủ / Nộp / ▶ tự do — chạy NỀN, trả về ngay; JS hỏi `qc_trang_thai`."""
        doc = self._cha._doc_qc
        if not doc:
            return _loi("Chưa có sơ đồ — bấm ◆ Màn chơi ở cửa sổ vẽ.")
        try:
            qc_api.doc_khoa()                   # thiếu khoá thì báo NGAY, chưa đóng gói gì
            self._viec().bat_dau(doc, loai, man_id, tu_do)
        except (qc_api.LoiQC, game.LoiGame, bo_chay.LoiChay) as e:
            return _loi(str(e))
        return _ok(True)

    @_bat_loi
    def qc_trang_thai(self):
        return _ok(self._viec().trang_thai())

    # ------------------------------------------------------------------ xem kết quả
    def _ket_qua(self):
        k = self._viec().ket_qua
        if k is None:
            raise game.LoiGame("Chưa có lượt nào để xem — bấm ▶ trước.")
        return k

    @_bat_loi
    def qc_ket_qua(self):
        k = self._viec().ket_qua
        return _ok(k.tom_tat() if k is not None else None)

    @_bat_loi
    def qc_nhat_ky(self, tu=0, so=200, chi_viec=True):
        try:
            return _ok(self._ket_qua().lo(tu, so, chi_viec))
        except game.LoiGame as e:
            return _loi(str(e))

    @_bat_loi
    def qc_lenh(self):
        """Mọi lệnh của lượt đang xem — mỗi lệnh mang giờ đặt/khớp/đóng."""
        try:
            return _ok(self._ket_qua().lenh)
        except game.LoiGame as e:
            return _loi(str(e))

    @_bat_loi
    def qc_soi_luot(self, i):
        """SOI một lượt TRÊN SƠ ĐỒ: bắn sang cửa sổ vẽ để nó tô đường lượt `i` đã đi —
        tới tận dòng điều kiện hỏng — rồi kéo cửa sổ vẽ lên trước. Bắn TRƯỚC rồi mới kéo:
        kéo trước thì cửa sổ hiện ra trong một nhịp còn chưa có gì được tô, nhìn như hụt."""
        try:
            k = self._ket_qua()
        except game.LoiGame as e:
            return _loi(str(e))
        i = int(i)
        if not (0 <= i < len(k.nhat_ky)):
            return _ok({"da_ban": False})
        self._cha._ban("soi_luot", k.soi(i))
        self._cha._khung.keo_len_truoc()
        return _ok({"da_ban": True})

    @_bat_loi
    def qc_man(self):
        return _ok(self._ds_man())

    @_bat_loi
    def qc_lich_su(self):
        return _ok(game.lich_su())

    @_bat_loi
    def qc_mo_lai(self, duong):
        try:
            return _ok(self._viec().mo_lai(duong))
        except game.LoiGame as e:
            return _loi(str(e))

    @_bat_loi
    def qc_mo_web(self, url):
        """Mở trang backtest trên quantconnect.com bằng trình duyệt của máy. CHỈ link của QC."""
        url = str(url or "")
        if not url.startswith("https://www.quantconnect.com/"):
            return _loi("Chỉ mở link của quantconnect.com.")
        import webbrowser
        webbrowser.open(url)
        return _ok(True)

