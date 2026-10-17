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
import sys
import time
import traceback

from . import chay_lean
from . import core
from . import sinh_ma
from . import bat_dau
from . import hoi
from . import lam
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
        self._cai_dat = core.load_settings()

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
    def sinh_ma(self, ten, steps, edges=None, ghi=False):
        """Sơ đồ -> thuật toán LEAN Python. `ghi` True thì ghi luôn ra file.

        Trả cả `van_de`: có lỗi thì `ok` False và ĐừNG chạy file ấy — nhưng vẫn đưa
        mã ra để người chơi nhìn thấy sơ đồ của mình thành cái gì."""
        kq = sinh_ma.sinh(core.make_process_template(ten, steps, edges))
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
    def chay_backtest(self, ten, steps, edges=None):
        """Vẽ -> sinh -> CHẠY -> đọc, trong một lượt.

        Sinh mã còn lỗi thì DỪNG LẠI: chạy một file sinh từ sơ đồ đã hỏng chỉ ra một
        thông báo của LEAN khó hiểu hơn hẳn bảng Vấn đề."""
        kq = sinh_ma.sinh(core.make_process_template(ten, steps, edges))
        if not kq["ok"]:
            return _ok({"ok": False, "loi": "Sơ đồ còn chỗ chưa diễn đạt hết — xem bảng "
                                            "Vấn đề.", "van_de": kq["van_de"]})
        r = chay_lean.chay(kq["ma"], kq["ten_lop"])
        r["van_de"] = kq["van_de"]
        # TÊN MỐC phải nói thật. LEAN KHÔNG ghi lại nó trong file kết quả, mà để trống
        # thì nó lặng lẽ lấy SPY — biểu đồ ghi "Mốc so sánh" chung chung là giấu mất
        # chuyện cỗ máy vàng đang bị đem so với cổ phiếu Mỹ.
        bd = next((s for s in (steps or []) if core.is_start_step(s)), None)
        m = str(core.o_bat_dau(bd, "moc_so_sanh") or "").strip().upper() if bd else ""
        r["moc_ten"] = m or "SPY — LEAN tự chọn"
        # Gửi kèm luôn MÃ ĐÃ SINH: tab Mã của màn Kết quả phải bày đúng file vừa chạy,
        # chứ không phải sinh lại một bản khác rồi bảo là nó.
        r["ma"] = kq["ma"]
        r["ten_lop"] = kq["ten_lop"]
        return _ok(r)

    @_bat_loi
    def tu_dien_bat_dau(self):
        """Từ điển KHỐI BẮT ĐẦU — sáu ô thiết lập, loại tài sản, nhịp chạy.

        Cùng lý do như hai cửa từ điển kia: giao diện hỏi Python chứ không tự khai."""
        return _ok(bat_dau.tu_dien())

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
            st = core.make_action_step({"type": loai or core.CHECK_COND})
        return _ok({"step": st, "card": core.the_buoc(st)})

    @_bat_loi
    def soat(self, steps, edges=None):
        """Tất cả những gì giao diện cần để vẽ lại sơ đồ sau một thay đổi.

        Gộp làm MỘT cửa chứ không ba: đánh số, soát lỗi và dựng thẻ đều đọc cùng một
        đồ thị, tách ra thì ba lượt gọi có thể thấy ba trạng thái khác nhau."""
        steps = core.ensure_step_ids([s for s in (steps or []) if isinstance(s, dict)])
        edges = core.clean_edges(edges, steps) if edges is not None \
            else core.default_edges(steps)
        kq = core.flow_order(steps, edges)
        # Bảng Vấn đề = lỗi ĐỒ THỊ (nối dây) + lỗi RUỘT từng khối. Gộp ở đây chứ
        # không ở `validate_flow_graph`: cái đó chỉ biết về dây, cố ý vậy.
        van_de = core.validate_flow_graph(steps, edges)
        for s in steps:
            van_de.extend(core.soat_khoi_hoi(s))
            van_de.extend(core.soat_khoi_lam(s))
            van_de.extend(core.soat_khoi_bat_dau(s))
            # Hành động nằm trong một Nhóm cũng phải soát — khối Nhóm không có `type`
            # của riêng nó, nên vòng trên không chạm tới ruột nó.
            for a in core.hanh_dong_cua(s):
                if a is not s:
                    van_de.extend(core.soat_khoi_lam({**a, "id": s["id"]}))
        # Soát CHÉO khối: chạy cả rổ thì mọi khối phải gõ rõ tên mã. Một khối nhìn
        # vào chính nó thì không biết khối Bắt đầu đang chạy kiểu nào.
        van_de.extend(core.soat_ca_ro(steps))
        return _ok({
            "thu_tu": kq["order"],
            "entry": kq["entry"],
            "the": {s["id"]: core.the_buoc(s) for s in steps},
            "van_de": van_de,
            "vong": {a: list(b) for a, b in core.canh_vong(edges, steps).items()},
            "edges": edges,
        })

    @_bat_loi
    def nhan_ban(self, steps, edges=None, giu_hat_nhan=False):
        """Chép một mảng khối, cấp id mới. Đích Quay về trỏ ra ngoài mảng bị để TRỐNG."""
        moi, day, bang = core.clone_steps(steps, edges, giu_hat_nhan)
        return _ok({"steps": moi, "edges": day, "map": bang,
                    "the": {s["id"]: core.the_buoc(s) for s in moi}})

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
            return _loi("Tên mới không được để trống.")
        if moi == cu:
            return _ok({"ten": cu})
        if moi in luu_tru.liet_ke_strategy():
            return _loi(f'Đã có Strategy tên "{moi}". Hãy chọn tên khác.')
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
            return _loi("Tên bản sao không được để trống.")
        if ten_moi in luu_tru.liet_ke_strategy():
            return _loi(f'Đã có Strategy tên "{ten_moi}". Hãy chọn tên khác.')
        doc = core.normalize_process(luu_tru.doc_strategy(ten))
        doc["name"] = ten_moi
        # Cấp id MỚI cho mọi khối: hai bản dùng chung id thì dán khối của bản này sang
        # bản kia là trùng id, và `validate_flow_graph` báo "khối biến mất khỏi sơ đồ".
        moi, day, _ = core.clone_steps(doc["steps"], doc["edges"], giu_hat_nhan=True)
        doc["steps"], doc["edges"] = moi, day
        luu_tru.ghi_strategy(ten_moi, doc)
        return _ok({"ten": ten_moi})

    @_bat_loi
    def luu_strategy(self, ten, steps, edges=None):
        doc = core.make_process_template(ten, steps, edges)
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
    def tu_luu_strategy(self, ten, steps, edges=None):
        """Bản tự lưu nằm cạnh Strategy gốc. CHỈ đẻ ra khi nội dung thật sự khác bản trên
        đĩa — mở ra xem mà không sửa gì thì không đẻ ra file nào."""
        ten = luu_tru.ten_goc_cua(ten)
        if not ten:
            return _ok(None)          # chưa lưu lần nào: bản nháp lo, không phải chỗ này
        doc = core.make_process_template(ten, steps, edges)
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
    def luu_ban_nhap(self, ten, steps, edges=None):
        """Việc đang dở của cửa sổ — kể cả cỗ máy chưa từng lưu. Không đụng file cỗ máy."""
        doc = core.make_process_template(ten or "", steps, edges)
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
    def qc_mo_web(self, url):
        """Mở trang backtest trên quantconnect.com bằng trình duyệt của máy. CHỈ link của QC."""
        url = str(url or "")
        if not url.startswith("https://www.quantconnect.com/"):
            return _loi("Chỉ mở link của quantconnect.com.")
        import webbrowser
        webbrowser.open(url)
        return _ok(True)
