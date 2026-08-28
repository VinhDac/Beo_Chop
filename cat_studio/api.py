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
import threading
import time
import traceback

from . import core
from . import kho
from . import khung_cua_so
from . import luu_tru
from . import so_lenh


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
# Hành động mặc định
# ---------------------------------------------------------------------------


def _hanh_dong_mac_dinh(loai):
    """Giá trị khởi điểm của một hành động mới.

    Cố ý là những con số DÙNG ĐƯỢC NGAY chứ không phải 0: mặc định của Compress EA
    (ATR 14, ngưỡng 7 bps, SL 1.5×ATR, TP 2R) đã chạy được trên nhiều symbol, nên
    người dùng mới có thứ hợp lý để sửa chứ không phải bịa từ số không."""
    if loai == core.VAO_LENH:
        return {"type": loai, "huong": "mua", "loai": "stop", "lot": 0.01,
                "dem": {"tinh": "atr", "value": 0.1},
                "sl": {"tinh": "atr", "value": 1.5},
                "tp": {"tinh": "R", "value": 2}}
    if loai == core.SUA_LENH:
        return {"type": loai, "che_do": "hoa_von"}
    return {"type": core.CHECK_COND, "conditions": [{
        "trai": {"ten": "atr", "tf": "M5", "period": 14}, "don_vi": "bps",
        "phep": "<", "phai": {"value": 7.0, "tinh": "bps"}}]}


# ---------------------------------------------------------------------------
# Thẻ vẽ lên hộp — NỘI DUNG DO PYTHON SINH
# ---------------------------------------------------------------------------


def _mau_khoi(st):
    """Khoá MÀU của khối — ngữ nghĩa, không phải mã màu. Giao diện tự ánh xạ sang biến
    CSS, nên đổi bảng màu là việc của CSS, không phải sửa Python.

    Suy từ `type` + `huong` — đều là phạm trù của chính app (không phải khái niệm riêng
    của một chiến lược), nên chiến lược nào sau này cũng ra màu đúng."""
    if core.is_start_step(st):
        return "start"
    t = st.get("type")
    if t == core.VAO_LENH:
        return "ban" if st.get("huong") == "ban" else "mua"
    if t == core.SUA_LENH:
        return "sua"
    return "hoi"


def _the_buoc(st, ts=None, tab=None):
    """Một khối -> thẻ để giao diện vẽ.

    Giao diện KHÔNG tự ghép chữ: nếu nó ghép thì sớm muộn nó mô tả khác với thứ lõi
    thực sự hiểu. Nó chỉ chọn ICON theo `type`.

    Chữ trên hộp lấy từ `core.dong_khoi` — dòng NGẮN, mỗi trường một dòng. Câu đầy đủ
    (`core.action_display`) để dành cho tooltip: nhìn hộp thì cần liếc ra ngay, rê chuột
    mới cần biết đủ chi tiết."""
    the = {"id": st.get("id"), "kind": st.get("kind"), "title": core.step_title(st),
           "badges": [], "lines": [], "mo_ta": "", "ghim": bool(st.get("ghim")),
           "la_cong": core.is_branch_gate(st), "mau": _mau_khoi(st)}

    the["lines"] = [{"text": x, "type": st.get("type")}
                    for x in core.dong_khoi(st, ts, tab)]

    if core.is_start_step(st):
        the["badges"] = ["chạy lại từ đây"]
        the["nhip"] = st.get("nhip")
        the["mo_ta"] = ("Điểm neo đánh số. Cả sơ đồ là một vòng lặp — mỗi nến "
                        f"{st.get('nhip')} nó chạy lại từ khối này.")
        return the

    # Bỏ `name` trước khi sinh câu đầy đủ: tiêu đề hộp ĐÃ hiện tên rồi.
    the["mo_ta"] = core.action_display(
        {k: v for k, v in st.items() if k != "name"}, ts)

    if st.get("type") == core.CHECK_COND:
        n = len(st.get("conditions") or [])
        the["badges"].append("cổng rẽ nhánh" if core.is_branch_gate(st) else "kiểm tra")
        # Khối CÓ điều kiện thì chữ tự nói (`Giá đóng cửa(M15) > MA(M15, 50)`), nhưng
        # khối RỖNG ở hai cơ chế nhìn giống hệt nhau — nhãn này là chỗ phân biệt duy nhất.
        if st.get("so_dai_luong"):
            the["badges"].append("so hai đại lượng")
        if n > 1:
            the["badges"].append(f"{n} điều kiện · VÀ")
    return the


def _kem_the(doc):
    """Gắn `cards` vào từng sơ đồ. Chữ trên hộp do Python sinh, JS không ghép lại.

    Truyền cả bảng tham số xuống để dòng chữ hiện `ngưỡng nén = 7` thay vì trơ ra một
    cái tên không ai biết bằng bao nhiêu.

    ⚠ CHUẨN HOÁ NGAY TẠI ĐÂY, chứ không tin từng chỗ gọi nhớ làm. Đây là hàm DUY NHẤT
    chuẩn bị một doc cho giao diện, nên nó phải là chỗ bảo đảm luật *"mọi doc tới tay
    giao diện đều đã chuẩn hoá"*.

    Vì sao gắt thế, có ca thật: `demo_process` từng gọi `_kem_the(_so_do_mau())` — thiếu
    đúng một lời gọi `normalize_process`. Sơ đồ mẫu vì vậy thiếu cờ `so_dai_luong` (cờ
    này chỉ chuẩn hoá mới sinh ra được), nên mở cổng "Xu hướng LÊN?" ra thì hộp thoại
    tưởng là cơ chế "so với giá trị": ô số trắng trơn, cột đơn vị in "giá tuyệt đối".
    Mà CHỮ TRÊN THẺ vẫn đúng — `cond_display` tự SUY từ `phai.ten` chứ không đọc cờ. Hai
    nguồn cho một sự thật, và cái lệch thì im lặng.

    Lỗ đó có từ trước; nó chỉ lộ ra khi `so_dai_luong` thành trường đầu tiên mà giao diện
    KHÔNG suy lại được. Vá dòng 449 thì lần sau ai thêm endpoint mới lại quên tiếp.

    An toàn vì `normalize_process` BẤT BIẾN — chạy hai lần bằng đúng một lần
    (`tests/test_so_do_mau.py` canh chuyện đó), nên mấy chỗ đã chuẩn hoá rồi gọi thêm
    một lần nữa cũng không đổi gì."""
    doc = core.normalize_process(doc)
    ts = core.bang_tham_so(doc)
    for tab in core.TABS:
        g = doc.get(tab) or {"steps": [], "edges": []}
        g["cards"] = [_the_buoc(s, ts, tab) for s in g.get("steps") or []]
        doc[tab] = g
    return doc


# ---------------------------------------------------------------------------
class NenCuaSo:
    """Phần CHUNG của một cửa sổ tự vẽ khung: giữ cửa sổ của CHÍNH MÌNH và vá khung
    của CHÍNH MÌNH.

    ⚠ Vì sao phải tách ra thành lớp nền — ba lỗi đã có thật, không phải giả định:

      1. `_mo_cua_so_tester` truyền `js_api=self`, tức cửa sổ tester dùng CHUNG một
         `Api` với cửa sổ chính, mà `self._window` lại trỏ cửa sổ chính. Bấm ✕ trên
         thanh tiêu đề tự vẽ của tester gọi `cua_so_dong()` → `self._window.destroy()`
         → ĐÓNG CỬA SỔ CHÍNH. Thu nhỏ, phóng to, đổi tiêu đề, hộp thoại file: nhắm
         nhầm cửa sổ y hệt.
      2. `KhungTuVe` giữ đúng MỘT `hwnd` và MỘT bảng vùng-cấm. Kéo thanh tiêu đề của
         tester `PostMessage` vào hwnd cửa sổ chính → kéo nhầm cửa sổ.
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
        giữa chừng.

        ⚠ HIỆN KHÔNG AI GỌI. Hai chỗ gọi cũ (`so_do_moi` đẩy sang cửa sổ tester,
        `soi_luot` đẩy ngược về cửa sổ vẽ) đã đi cùng `ApiTester`/`ApiLive` ở đợt 2.

        Giữ vì đây là ĐƯỜNG DUY NHẤT Python nói được với JS mà không đợi JS hỏi —
        mọi thứ khác trong file này đều là JS gọi xuống. Bộ chạy mới sẽ cần đúng nó để
        đẩy tiến độ và kết quả. Đầu bên kia là `window.__su_kien` khai trong `api.ts`;
        hai đầu phải cùng sống hoặc cùng chết."""
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
        self._khoa = threading.Lock()

    # ------------------------------------------------------------------ cơ bản
    @_bat_loi
    def ping(self):
        return _ok("pong")

    @_bat_loi
    def bootstrap(self):
        """Mọi hằng số giao diện cần, lấy MỘT lần lúc mở app.

        JS không viết cứng danh sách nào — nhãn, khung thời gian, toán hạng, phép so
        đều từ đây. Thêm một toán hạng ở core là giao diện có ngay, không phải sửa JS."""
        return _ok({
            "phien_ban": core.PHIEN_BAN,
            "settings": self._cai_dat,
            "app_dir": core.app_dir(),
            # ⚠ `nguon` và `co_mt5` ĐÃ BỎ — chưa có sàn nào để liệt kê nguồn dữ liệu.
            # Giao diện phải chịu được thiếu chúng; xem `tai_lieu/o_cam_trong.md`.

            "kinds": [core.KIND_START, core.KIND_ACTION],
            "kind_labels": core.KIND_LABELS,

            "tabs": core.TABS,
            "tab_labels": core.TAB_LABELS,
            "action_types": core.ACTION_TYPES,
            "action_labels": core.ACTION_LABELS,
            "action_tabs": {k: list(v) for k, v in core.ACTION_TABS.items()},
            "branch_type": core.CHECK_COND,
            "nhom_lenh_nay": core.NHOM_LENH_NAY,
            "toan_hang_dung_sai": list(core.TOAN_HANG_DUNG_SAI),

            "timeframes": core.TIMEFRAMES,
            "nhip_mac_dinh": core.NHIP_MAC_DINH,
            "ma_methods": core.MA_METHODS,
            # Gửi nguyên dict từ `kho/` — thêm một trường ở đó là giao diện có ngay,
            # không phải nhớ sửa chỗ này.
            "toan_hang": core.TOAN_HANG,
            "phep_so": core.PHEP_SO,
            # ĐƠN VỊ — MỘT bảng cho cả app: điều kiện, SL/TP/đệm, sửa lệnh.
            # Trước đây là hai bảng (`CACH_TINH` + `DON_VI_SS`) trùng nhau ba cặp.
            "don_vi": core.DON_VI,
            "don_vi_ngan": core.DON_VI_NGAN,
            "don_vi_cho": {k: list(v) for k, v in core.DON_VI_CHO.items()},
            "huong": core.HUONG,
            "loai_lenh": core.LOAI_LENH,
            # MỐC NEO của khối Vào lệnh — xem `core.MOC_ENTRY`.
            "moc_entry": core.MOC_ENTRY,
            # MỌI đơn vị, một bảng nhãn — kể cả đơn vị ĐẾM (nến · lệnh · lot).
            # Bảng tham số khai `don_vi` bằng một khoá ở đây, và ô số chỉ mời những
            # tham số có ĐÚNG đơn vị của nó.
            "nhan_don_vi": core.NHAN_DON_VI,
            "don_vi_dem": core.DON_VI_DEM,
            # Toán hạng → đơn vị CỐ ĐỊNH của ô so với nó (`None` = không có vế phải).
            "toan_hang_don_vi": {
                t["key"]: core.don_vi_cua_o("dieu_kien", t["key"])
                for t in kho.TOAN_HANG},
            "toan_hang_loai": core.TOAN_HANG_LOAI,
            "loai_co_don_vi": core.LOAI_CO_DON_VI,
            # Toán hạng nào KHÔNG đo được bằng chính nó (kết quả luôn = 1).
            "don_vi_chinh_no": core.DON_VI_CHINH_NO,
            # Toán hạng nào chỉ có nghĩa khi đã có zone, và đơn vị nào cũng vậy.
            "toan_hang_can_zone": list(core.TOAN_HANG_CAN_ZONE),
            "don_vi_can_zone": list(core.DON_VI_CAN_ZONE),
            "moc_can_zone": list(core.MOC_CAN_ZONE),
            "sua_che_do": core.SUA_CHE_DO,
            "sua_can_gia": list(core.SUA_CAN_GIA),

            "don_vi_o": {k: core.don_vi_cua_o(k) for k in ("chu_ky", "lot")},
            "template_kinds": core.TEMPLATE_KINDS,
            "accent_presets": core.ACCENT_PRESETS,
            "max_process_steps": core.MAX_PROCESS_STEPS,
        })

    # ------------------------------------------------------------------ mô tả
    @_bat_loi
    def describe(self, steps, tham_so=None):
        ts = {t["ten"]: t["gia_tri"] for t in (tham_so or [])}
        return _ok([_the_buoc(s, ts) for s in (steps or []) if isinstance(s, dict)])

    @_bat_loi
    def action_defaults(self, action_type):
        return _ok(_hanh_dong_mac_dinh(action_type))

    @_bat_loi
    def save_action(self, draft, tab=None, tham_so=None):
        """Chuẩn hoá + soát một hành động. Hộp thoại KHÔNG tự soát — nó gửi bản nháp
        thô sang đây, để luật hợp lệ chỉ nằm ở đúng một chỗ."""
        a = core.normalize_action(draft)
        if a is None:
            return {"ok": False, "error": "Loại hành động không hợp lệ."}
        ts = {t["ten"]: t["gia_tri"] for t in (tham_so or [])}
        loi = []
        core.validate_actions([a], lambda m, i=None: loi.append(m), tab, set(ts))
        return _ok({"action": a, "display": core.action_display(a, ts)}, loi=loi)

    # ------------------------------------------------------------------ khối
    @_bat_loi
    def new_step(self, kind="action", action_type=None, tab=None):
        st = (core.make_start_step(
                  "Chạy lại từ đây",
                  core.NHIP_MAC_DINH.get(tab, core.NHIP_MAC_DINH[core.TAB_ENTRY]))
              if kind == core.KIND_START
              else core.make_action_step(
                  _hanh_dong_mac_dinh(action_type or core.CHECK_COND)))
        return _ok({"step": st, "card": _the_buoc(st)})

    @_bat_loi
    def clone_steps(self, steps, tham_so=None):
        """Nhân bản khối: id mới + thẻ chữ.

        ⚠ `tham_so` là bảng tham số của sơ đồ ĐÍCH. Thiếu nó thì thẻ dựng ra ghi
        `nguong_nen_bps = ?` — khối vừa dán/vừa nhập trông như hỏng, trong khi tham số
        vẫn có đủ; chỉ là chỗ dựng chữ không được đưa cho. Ctrl+V dính lỗi này từ đầu,
        chỉ là ít ai để ý vì thường dán ngay trong cùng một sơ đồ."""
        moi, tra = core.clone_steps(steps)
        ts = core.bang_tham_so({"tham_so": tham_so or []})
        return _ok({"steps": moi, "map": tra, "cards": [_the_buoc(s, ts) for s in moi]})

    # ------------------------------------------------------------------ soát
    @_bat_loi
    def validate(self, doc):
        """Nguồn của HUY HIỆU SỐ và của bảng Vấn đề — cho CẢ HAI sơ đồ, một lời gọi.

        Trả về `{value: [vấn đề…], luong: {entry: {...}, manage: {...}}}`. Mỗi vấn đề
        mang khoá `tab` để giao diện gắn nhãn và nhảy đúng chỗ.

        Soát cả hai tab chứ không chỉ tab đang mở: giấu lỗi của tab kia thì bấm ▶ Chạy
        mới lòi ra, mà lúc đó không ai hiểu vì sao."""
        probs = core.validate_process(doc)
        luong = {}
        for tab in core.TABS:
            g = (doc or {}).get(tab) or {}
            st = g.get("steps") or []
            ed = g.get("edges")
            kq = core.flow_order(st, core.default_edges(st) if ed is None else ed)
            luong[tab] = {
                "order": kq["order"],
                "unreachable": kq["unreachable"],
                "quay_lai": [list(c) for c in kq["quay_lai"]],
                "vong_ho": [list(c) for c in kq["vong_ho"]],
                "lech_nhanh": kq["lech_nhanh"],
                # Khối nào đã đi QUA cổng zone — hộp thoại dùng nó để KHÔNG bày ra toán
                # hạng zone và đơn vị `× ATR zone` ở chỗ zone chưa tồn tại. Trả kèm ở
                # đây thay vì thêm một lệnh riêng: sơ đồ đổi là bảng này đổi theo, không
                # có đường nào để hai bên lệch nhau.
                "sau_cong_zone": sorted(core.khoi_sau_cong_zone(
                    st, core.default_edges(st) if ed is None else ed)),
            }
        return _ok(probs,
                   so_loi=sum(1 for p in probs if p["severity"] == "error"),
                   so_canh_bao=sum(1 for p in probs if p["severity"] == "warning"),
                   luong=luong,
                   tham_so_dang_dung=sorted(core._tham_so_dang_dung(doc)))

    # ------------------------------------------------------------------ tài liệu
    @_bat_loi
    def new_process(self):
        return _ok(_kem_the(core.new_process()))

    @_bat_loi
    def demo_process(self):
        """Ổ CẮM TRỐNG — chưa có sơ đồ mẫu.

        Sơ đồ mẫu cũ là chiến lược Compress (D_02): nén biến động rồi phá vùng, dựng
        trên nến M5 và lệnh chờ stop. Nó đi cùng D_02 trong đợt 2 của lần dọn sang
        HFT market maker.

        Trả lỗi chứ KHÔNG trả sơ đồ rỗng: một sơ đồ trắng mở ra trông y hệt "▶ Mẫu"
        vừa chạy xong mà chẳng có gì — người dùng sẽ tưởng nút hỏng. Nói thẳng là chưa
        có thì hơn. Xem `tai_lieu/o_cam_trong.md`."""
        return {"ok": False,
                "error": "Chưa có sơ đồ mẫu — chiến lược cũ đã gỡ cùng MT5."}

    @_bat_loi
    def load_process(self, name):
        return _ok(_kem_the(core.normalize_process(
            core.load_template("strategy", name))))

    @_bat_loi
    def import_steps(self, ten, tab):
        """Khối + đường nối của MỘT tab trong một chiến lược đã lưu, để THÊM CHỒNG lên
        sơ đồ đang mở. Không đụng gì tới sơ đồ hiện tại — việc ghép là của giao diện.

        Hai thứ lọc ở đây, cả hai đều là luật chứ không phải cho gọn:

        * **Bỏ khối Bắt đầu** — sơ đồ đang mở đã có một cái rồi, hai khối Bắt đầu là sơ
          đồ hỏng.
        * **Chỉ một tab** — toán hạng nhóm "Lệnh này" chỉ tồn tại ở Manage, nên bê một
          khối Manage sang Entry là tạo ra khối không soát nổi.

        Và trả kèm **những tham số đám khối đó THẬT SỰ đọc**: khối tham chiếu tham số
        bằng TÊN, nên thiếu một cái là khối trông vẫn bình thường trên canvas nhưng bấm
        ▶ mới ném `"Bảng tham số thiếu …"`. Ai nhập cũng không đoán ra vì sao."""
        d = core.normalize_process(core.load_template("strategy", ten))
        tab = tab if tab in core.TABS else core.TAB_ENTRY
        g = d.get(tab) or {}
        goc = g.get("steps") or []
        buoc = [s for s in goc if not core.is_start_step(s)]
        giu = {s["id"] for s in buoc}
        canh = [e for e in (g.get("edges") or [])
                if e.get("from") in giu and e.get("to") in giu]
        # Dùng LẠI đúng bộ quét của validator, trên một `doc` giả chỉ có đám khối này —
        # viết một bộ quét thứ hai là sớm muộn hai bên hiểu khác nhau.
        dung = core._tham_so_dang_dung({tab: {"steps": buoc}})
        return _ok({
            "steps": buoc, "edges": canh,
            "tham_so": [t for t in (d.get("tham_so") or []) if t["ten"] in dung],
            "bo_start": len(goc) != len(buoc),
            "ten": d.get("name") or ten,
        })

    @_bat_loi
    def save_process(self, doc):
        d = core.normalize_process(doc)
        p = core.save_template("strategy", d["name"], d)
        return _ok({"path": p, "name": d["name"]})

    @_bat_loi
    def list_templates(self, kind="strategy"):
        return _ok(core.list_templates(kind))

    @_bat_loi
    def delete_template(self, kind, name):
        return _ok(core.delete_template(kind, name))

    # -- file ngoài --
    #: ⚠ MỘT CHUỖI, không phải tuple `(mô tả, đuôi)`. pywebview đòi mỗi bộ lọc là một
    #: chuỗi đúng dạng `Mô tả (*.đuôi)` và tự tách lấy đuôi; đưa tuple vào thì
    #: `parse_file_type` ném `TypeError: expected string, got 'tuple'` NGAY, trước cả khi
    #: hộp thoại kịp mở — nên "Mở từ file khác…", "Duyệt file khác…" và "Lưu ra file
    #: khác…" đều bấm mà không thấy gì. Lỗi có được báo, nhưng vào bảng Nhật ký ở dưới,
    #: chỗ người dùng đang không mở.
    _LOC = "Chiến lược Cat_Studio (*.json)"

    @_bat_loi
    def open_process_file(self):
        import webview
        # `FileDialog.OPEN` chứ không phải hằng `OPEN_DIALOG` cũ — pywebview đã đánh dấu
        # bỏ nó ("will be removed in a future version"), cùng giá trị 10.
        r = self._window.create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=False, file_types=(self._LOC,))
        if not r:
            return {"ok": False}          # người dùng bấm Huỷ — KHÔNG phải lỗi
        with open(r[0], encoding="utf-8") as f:
            return _ok(_kem_the(core.normalize_process(json.load(f))))

    @_bat_loi
    def save_process_file(self, doc):
        import webview
        d = core.normalize_process(doc)
        r = self._window.create_file_dialog(
            webview.FileDialog.SAVE, save_filename=f"{d['name']}.json",
            file_types=(self._LOC,))
        if not r:
            return {"ok": False}
        p = r if isinstance(r, str) else r[0]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        return _ok({"path": p})

    # ------------------------------------------------------------------ chạy
    #
    # ⚠ HAI Ổ CẮM TRỐNG. `ApiTester` và `ApiLive` đã bị gỡ trong đợt 2 của lần dọn
    # sang HFT market maker, cùng với `bo_chay` · `khop_lenh` · `nguon_nen` ·
    # `ket_noi` · `gui_lenh` · `phien_live`.
    #
    # GIỮ hai phương thức chứ không xoá, và đó là lựa chọn có lý do: nút ▶ Chạy và
    # ● Live vẫn nằm trên ribbon, `App.tsx` đã sẵn nhánh `if (!r.ok) alert(r.error)`.
    # Trả một câu nói thẳng thì người bấm biết mình đang ở đâu; xoá phương thức đi thì
    # cầu nối ném `AttributeError` qua JS và nút trông như hỏng.
    #
    # Cắm lại: xem `tai_lieu/o_cam_trong.md`.
    @_bat_loi
    def mo_tester(self, doc):
        """▶ Chạy — CHƯA CÓ BỘ CHẠY.

        Vẫn soát sơ đồ trước khi trả lời. Sơ đồ có lỗi thì lỗi đó vẫn là tin có ích,
        và bảng Vấn đề vẫn phải sáng lên — chuyện chưa có bộ chạy không làm cái đó
        bớt đúng."""
        probs = core.validate_process(doc)
        loi = [p for p in probs if p["severity"] == "error"]
        if loi:
            return {"ok": False, "error": "Sơ đồ còn lỗi, chưa chạy được.", "loi": loi}
        return {"ok": False,
                "error": "Chưa có bộ chạy.\n\nStrategy Tester cũ dựng trên nến M1 "
                         "và dữ liệu MT5 — cả hai đã gỡ. Cái thay thế chờ chọn xong "
                         "sàn."}

    @_bat_loi
    def mo_live(self, doc=None):
        """● Live — CHƯA CÓ KẾT NỐI SÀN."""
        return {"ok": False,
                "error": "Chưa có kết nối sàn.\n\n"
                         "Tầng đặt lệnh cũ là MT5 và đã gỡ."}


    # ------------------------------------------------------------------ kho
    @_bat_loi
    def kho_danh_muc(self):
        """Mọi thứ app tính được, đã chia mục — cho hộp thoại "Kho".

        Dữ liệu do `kho/` tự gom từ các module con, nên thêm một engine mới là hộp
        thoại có ngay, không phải sửa gì ở đây."""
        d = kho.danh_muc()
        d["luu_tru"] = luu_tru.tom_tat()
        d["hanh_dong"] = [{"key": k, "nhan": core.ACTION_LABELS[k],
                           "tabs": list(core.ACTION_TABS[k])}
                          for k in core.ACTION_TYPES]
        d["don_vi"] = core.DON_VI
        d["sua_che_do"] = core.SUA_CHE_DO
        d["phep_so"] = core.PHEP_SO
        d["trang_thai_lenh"] = {
            so_lenh.CHO: "Lệnh chờ đang treo",
            so_lenh.MO: "Đã khớp — đang là vị thế",
            so_lenh.DONG: "Đã đóng / đã huỷ",
        }
        d["ly_do_dong"] = so_lenh.LY_DO_DONG
        return _ok(d)

    # ------------------------------------------------------------------ cài đặt
    @_bat_loi
    def save_settings(self, s):
        cd = dict(self._cai_dat)
        if (s or {}).get("symbol"):
            cd["symbol"] = str(s["symbol"]).strip().upper()
        if (s or {}).get("accent"):
            cd["accent"] = str(s["accent"])
        self._cai_dat = core.save_settings(cd)
        return _ok(self._cai_dat)

    @_bat_loi
    def save_ui(self, state):
        """Bố cục bảng dưới.

        PHẢI đi qua Python chứ không dùng `localStorage`: pywebview phục vụ trang trên
        một cổng NGẪU NHIÊN mỗi lần chạy, mà `localStorage` gắn theo origin — nên lần
        sau mở app là origin khác và mọi thứ đã nhớ biến mất."""
        ui = dict(self._cai_dat.get("ui") or {})
        for k in ("panel_cao", "panel_gap"):
            if (state or {}).get(k) is not None:
                ui[k] = state[k]
        self._cai_dat["ui"] = ui
        core.save_settings(self._cai_dat)
        return _ok(ui)

    def dong_app(self):
        """Cửa sổ chính đóng. KHÔNG bọc `_bat_loi`: pywebview gọi nó từ sự kiện
        `closing`, không phải từ JS.

        ⚠ Thân hàm đã RỖNG — trước đây nó dọn cửa sổ Strategy Tester theo. Không còn
        cửa sổ thứ hai nào để dọn.

        Giữ phương thức chứ không xoá: `app_web.py` nối nó vào sự kiện `closing`, và
        ngày có cửa sổ chạy trở lại thì đây là chỗ phải dọn. Xoá đi là ngày đó không ai
        nhớ ra rằng cửa sổ con phải chết theo cửa sổ mẹ."""
