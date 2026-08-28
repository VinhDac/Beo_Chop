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
from . import kho
from . import khung_cua_so
from . import luu_tru
from . import do_thi_truong
from . import nguon_tick


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

    Nguyên tắc: trả về thứ DÙNG ĐƯỢC NGAY, không phải một khối rỗng bắt người dùng
    bịa từ số không. Nhưng "dùng được ngay" ở đây KHÔNG có nghĩa là đoán ý:

      · `số hạng` mặc định `công bằng = mid` — câu đầu tiên của mọi market maker, và
        là số hạng duy nhất mà đặt nhầm chỗ cũng không gây hại;
      · `kiểm tra điều kiện` mặc định RỖNG. Bịa sẵn một điều kiện là bịa một ngưỡng,
        mà ngưỡng sai thì nhìn không ra — `validate_actions` sẽ nhắc ngay là cổng rỗng
        thì luôn khớp, và đó là lời nhắc đúng."""
    if loai == core.SO_HANG:
        return {"type": loai, "dich": "cong_bang", "phep": "=",
                "luong": {"he_so": 1, "toan_hang": "mid"}}
    return {"type": loai if loai in core.ACTION_TYPES else core.CHECK_COND,
            "conditions": []}


# ---------------------------------------------------------------------------
# Thẻ vẽ lên hộp — NỘI DUNG DO PYTHON SINH
# ---------------------------------------------------------------------------


def _mau_khoi(st):
    """Khoá MÀU của khối — ngữ nghĩa, không phải mã màu. Giao diện tự ánh xạ sang biến
    CSS, nên đổi bảng màu là việc của CSS, không phải sửa Python.

    Suy từ `type` + `đích` — đều là phạm trù của chính app (không phải khái niệm riêng
    của một chiến lược), nên chiến lược nào sau này cũng ra màu đúng.

    ⚠ Không tô theo MUA/BÁN nữa, vì một market maker đứng cả hai phía cùng lúc — chia
    màu theo hướng là chia một thứ không chia được. Thứ đáng phân biệt bằng mắt bây
    giờ là số hạng này động vào GIÁ hay động vào KHỐI LƯỢNG: nhìn cả chuỗi là thấy
    ngay phần nào dựng mức treo, phần nào dựng cỡ lệnh."""
    if core.is_start_step(st):
        return "start"
    if st.get("type") == core.SO_HANG:
        return "lot" if core.DICH_KIEU.get(st.get("dich")) == "lot" else "gia"
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
        # ⚠ `nhip` đã đi cùng khung thời gian (đợt 3), nên câu mô tả không còn nói
        # "mỗi nến M5" được nữa. Cái nó KHẲNG ĐỊNH thì không đổi và vẫn là điều quan
        # trọng nhất của khối này: cả sơ đồ là một vòng lặp.
        the["mo_ta"] = ("Điểm neo đánh số. Cả sơ đồ là một vòng lặp — mỗi lượt nó chạy "
                        "lại từ khối này.")
        return the

    # Bỏ `name` trước khi sinh câu đầy đủ: tiêu đề hộp ĐÃ hiện tên rồi.
    the["mo_ta"] = core.action_display(
        {k: v for k, v in st.items() if k != "name"}, ts)

    if st.get("type") == core.CHECK_COND:
        # Huy hiệu "N điều kiện · VÀ" và "so hai đại lượng" đã đi cùng điều kiện.
        the["badges"].append("cổng rẽ nhánh" if core.is_branch_gate(st) else "kiểm tra")
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
# ---------------------------------------------------------------------------
# Sơ đồ mẫu
# ---------------------------------------------------------------------------


def _so_do_mau():
    """Market maker sơ cấp — xem `Api.demo_process` để biết vì sao đúng bảy khối.

    Dựng bằng dict thô chứ không bằng hàm dựng: đây là DỮ LIỆU, phải giống hệt thứ
    người dùng tự vẽ ra rồi lưu. Ngày nào file mẫu lệch khỏi file người dùng là ngày
    "▶ Mẫu" hết dùng được làm chuẩn đối chiếu."""

    def so_hang(sid, y, dich, phep, he_so, toan_hang=None, don_vi=None, khi=None, x=340.0):
        luong = {"he_so": he_so}
        if toan_hang:
            luong["toan_hang"] = toan_hang
        if don_vi:
            luong["don_vi"] = don_vi
        ra = {"id": sid, "kind": core.KIND_ACTION, "type": core.SO_HANG,
              "dich": dich, "phep": phep, "luong": luong, "pos": [x, y]}
        if khi:
            ra["khi"] = khi
        return ra

    def han_muc(phep, gt):
        return {"trai": {"ten": "ton_kho"}, "phep": phep,
                "phai": {"value": gt, "tinh": "lot"}}

    # Nhánh MÙ nằm CAO HƠN nhánh chính, và đó không phải chuyện thẩm mỹ: thứ tự thử
    # nhánh lấy từ VỊ TRÍ trên canvas (`core._khoa_nhanh`), nên cổng phải ở trên thì
    # mới được thử trước. Kéo nó xuống dưới là đổi ngữ nghĩa.
    Y, DY = 300.0, 116.0
    steps = [
        dict(core.make_start_step("Mỗi sự kiện"), id="s_bd", pos=[90.0, Y + DY * 2]),

        # Cổng DUY NHẤT của sơ đồ. Không có vế phải — `co_so` vốn đã đúng/sai.
        {"id": "s_mu", "kind": core.KIND_ACTION, "type": core.CHECK_COND,
         "name": "Mất sổ lệnh?", "pos": [340.0, Y - DY],
         "conditions": [{"trai": {"ten": "co_so"}, "phep": "la_sai"}]},
        so_hang("s_rut", Y - DY, "lot", "=", 0, don_vi="lot", x=620.0),

        so_hang("s_cb", Y, "cong_bang", "=", 1, "mid"),
        so_hang("s_bien", Y + DY, "bien", "=", 1, "spread"),
        # Dấu của `ton_kho` làm hết việc: ôm hàng mua (dương) thì lệch dương, tức cả
        # hai chân dịch XUỐNG. Không cần nhánh nào cho hai chiều.
        so_hang("s_lech", Y + DY * 2, "lech", "+=", 0.5, "ton_kho", "tick"),
        so_hang("s_lot", Y + DY * 3, "lot", "=", 500, don_vi="lot"),
        so_hang("s_tran", Y + DY * 4, "lot_mua", "=", 0, don_vi="lot",
                khi=han_muc(">=", 2000)),
        so_hang("s_san", Y + DY * 5, "lot_ban", "=", 0, don_vi="lot",
                khi=han_muc("<=", -2000)),
    ]
    # Khối Bắt đầu rẽ HAI nhánh: cổng "mất sổ lệnh" và chuỗi chính. Nhánh mù đi sang
    # phải rồi DỪNG — rút hết là hết lượt, không còn gì để tính.
    canh = [("s_bd", "s_mu"), ("s_mu", "s_rut"),
            ("s_bd", "s_cb"), ("s_cb", "s_bien"), ("s_bien", "s_lech"),
            ("s_lech", "s_lot"), ("s_lot", "s_tran"), ("s_tran", "s_san")]
    return {
        "schema": core.SCHEMA, "type": "strategy",
        "name": "Market maker sơ cấp", "symbol": "BTCUSDT", "tham_so": [],
        core.TAB_BAO_GIA: {
            "steps": steps,
            "edges": [{"from": a, "to": b, "port": "out"} for a, b in canh]},
    }




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
            "huong": core.HUONG,

            # ---- TỪ VỰNG. Hợp đồng: **JS không viết cứng danh sách nào.** ----
            #
            # Mười chín khoá của thế giới nến đã đi ở đợt 3 (`moc_entry`, `sua_che_do`,
            # `don_vi_can_zone`, `timeframes`, `ma_methods`…). Cái thay chúng ít hơn
            # hẳn về số lượng, vì từ vựng market maker vốn nhỏ hơn — nhưng cùng một
            # hợp đồng: thả một module vào `kho/MODULE` là dropdown toán hạng có ngay,
            # không sờ vào JS.
            "toan_hang": core.TOAN_HANG,
            "toan_hang_loai": core.TOAN_HANG_LOAI,
            "toan_hang_don_vi": core.TOAN_HANG_DON_VI,
            "toan_hang_dung_sai": list(core.TOAN_HANG_DUNG_SAI),
            "phep_so": core.PHEP_SO,
            "phep_dung_sai": list(core.PHEP_DUNG_SAI),
            "don_vi": core.DON_VI,
            "don_vi_ngan": core.DON_VI_NGAN,
            "don_vi_dem": core.DON_VI_DEM,
            "nhan_don_vi": core.NHAN_DON_VI,
            # Loại đại lượng nào ĐƯỢC chọn đơn vị, và loại nào có đơn vị CỐ ĐỊNH. Hai
            # bảng này quyết ô thước đo mờ hay sáng — luật nằm ở Python, JS chỉ đọc.
            "loai_co_don_vi": core.LOAI_CO_DON_VI,
            "loai_don_vi": core.LOAI_DON_VI,

            # ---- SỐ HẠNG ----
            "dich": core.DICH,
            "dich_kieu": core.DICH_KIEU,
            "dich_ca_hai": {k: list(v) for k, v in core.DICH_CA_HAI.items()},
            "phep_gan": core.PHEP_GAN,
            # Đích nào nhận phép nào — hộp thoại xổ đúng những phép hợp lệ thay vì bày
            # cả ba rồi để `validate_actions` mắng sau.
            "phep_cho_dich": {k: list(v) for k, v in core.PHEP_CHO_DICH.items()},

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
        st = (core.make_start_step("Chạy lại từ đây")
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
                # ⚠ `sau_cong_zone` đã đi cùng cơ chế cổng zone (đợt 3). Nó nói khối
                # nào đã đi QUA cổng zone, để hộp thoại KHÔNG bày toán hạng zone ở chỗ
                # zone chưa tồn tại. Cách trả kèm ở đây — thay vì một lệnh riêng — thì
                # đáng giữ khi cơ chế tương đương quay lại: sơ đồ đổi là bảng đổi theo,
                # không có đường nào để hai bên lệch nhau.
            }
        return _ok(probs,
                   so_loi=sum(1 for p in probs if p["severity"] == "error"),
                   so_canh_bao=sum(1 for p in probs if p["severity"] == "warning"),
                   luong=luong)

    # ------------------------------------------------------------------ tài liệu
    @_bat_loi
    def new_process(self):
        return _ok(_kem_the(core.new_process()))

    @_bat_loi
    def demo_process(self):
        """Sơ đồ MẪU — market maker sơ cấp nhất còn chạy đúng.

        Bảy khối, và không khối nào bỏ được. Đây là bài kiểm tra thật của cả bộ từ
        vựng: nếu một chiến lược market maker tối thiểu mà đã phải thêm động từ hay
        thêm loại khối, thì ngữ pháp sai chứ không phải chiến lược thiếu.

            [1] Mỗi sự kiện
             ├─ [1A] cổng   có thấy sổ lệnh là SAI
             │        └─ [1A.1]  lot        =  0            → rút hết
             └─ [1B] (mặc định)
                    [2]  công bằng  =  mid
                    [3]  biên       =  1 × spread
                    [4]  lệch      +=  tồn kho × 0,5 tick/lot
                    [5]  lot        =  500 lot
                    [6]  lot mua    =  0 lot   khi  tồn kho ≥  2000
                    [7]  lot bán    =  0 lot   khi  tồn kho ≤ −2000

        Đọc theo BA TẦNG, và ba tầng đó chính là ba việc một market maker làm:

        [1A] MÙ THÌ RÚT. Cổng, không phải số hạng — vì nó không góp một số hạng nào
             vào báo giá, nó VỨT cả báo giá. Đây là chỗ duy nhất trong sơ đồ cần rẽ
             nhánh, và nó rẽ vì trạng thái "không nhìn thấy sổ lệnh" loại trừ mọi thứ
             còn lại, chứ không phải vì ta muốn hai kiểu hành xử.

        [2][3] BÁO GIÁ GỐC. Treo quanh `mid`, cách nửa spread mỗi phía. Ngây thơ có
             chủ ý: nó KHÔNG kiếm ra tiền trên một symbol có phí maker chuẩn — treo
             ngay ở bid/ask hiện tại thì phần lớn thời gian là đứng cuối hàng đợi và
             chỉ khớp khi giá sắp đi ngược. Nhưng nó là mốc số 0 đúng đắn: mọi thứ
             tinh vi hơn sau này đều là SỬA hai con số này, và có mốc thì mới đo được
             sửa ấy đáng bao nhiêu.

        [4] LỆCH THEO TỒN KHO — số hạng quan trọng nhất trong sơ đồ, và là lý do cả
             ngữ pháp này tồn tại. Ôm 1000 lot mua thì `lệch` = +500 tick, tức CẢ HAI
             chân dịch xuống nửa nghìn tick: giá mua của ta xấu đi nên ít bị nhồi
             thêm, giá bán của ta đẹp lên nên dễ xả bớt. Không có nó, tồn kho đi lang
             thang cho tới khi một cú giá quét sạch tài khoản — market maker chết vì
             tồn kho chứ không chết vì spread hẹp.

             ⚠ `+=` chứ không phải `=`. Ở sơ đồ này hai phép cho cùng kết quả (chưa ai
             cộng vào `lệch` trước đó), nhưng viết `=` là dựng sẵn một cái bẫy: số
             hạng lệch thứ hai thêm vào sau sẽ lặng lẽ bị xoá. `_soat_ghi_de` bắt đúng
             trường hợp đó.

        [5] CỠ LỆNH cố định — chỗ nông nhất của chiến lược này, và cố ý để nông. Cỡ
             lệnh đúng phải nhìn hàng đợi (`bid_kl`) và biến động; cả hai đều là số
             hạng thêm vào chuỗi, không phải sửa cấu trúc.

        [6][7] HẠN MỨC TỒN KHO, làm bằng `khi` chứ không bằng cổng — và đây là điều
             người dùng chốt khi bảo *gắn điều kiện lên chính khối số hạng*. Làm bằng
             cổng thì hai hạn mức là bốn nhánh, thêm một điều kiện nữa là tám. Làm
             bằng `khi` thì mỗi điều kiện là MỘT dòng, và chuỗi vẫn thẳng.

             Chú ý nó chỉ TẮT một phía chứ không đóng vị thế: quá hạn mức mua thì
             ngừng mua thêm, còn phía bán vẫn treo để xả dần. Đóng chủ động cần một
             lệnh taker — một động từ thứ ba mà ngữ pháp này chưa có, và chưa cần.

        Không có SL, không có TP, không có "thoát lệnh": rủi ro nằm ở [4] và [6][7],
        tức ở mức TỒN KHO. Xem `kho/nen_tang.py`.

        ⚠ Số trong sơ đồ (0,5 tick/lot · 500 lot · 2000 lot) là số MINH HOẠ đọc được
        bằng mắt, không phải số đã đo trên symbol nào. Chúng sẽ thành tham số có tên
        khi bảng tham số quay lại — xem `tai_lieu/o_cam_trong.md`."""
        return _ok(_kem_the(_so_do_mau()))

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

        ⚠ Bản cũ còn trả kèm **những tham số đám khối đó THẬT SỰ đọc**, quét bằng
        `core._tham_so_dang_dung` — cố ý dùng LẠI đúng bộ quét của validator, vì viết
        một bộ quét thứ hai là sớm muộn hai bên hiểu khác nhau. Lý do phải có: khối
        tham chiếu tham số bằng TÊN, nên nhập thiếu một cái là khối trông vẫn bình
        thường trên canvas nhưng bấm ▶ mới ném `"Bảng tham số thiếu …"`, và ai nhập
        cũng không đoán ra vì sao.

        Bảng tham số đi ở đợt 3, nên `tham_so` giờ luôn rỗng. Cả hai luật lọc phía
        trên thì không đổi — chúng là luật về CẤU TRÚC. Xem `tai_lieu/o_cam_trong.md`."""
        d = core.normalize_process(core.load_template("strategy", ten))
        tab = tab if tab in core.TABS else core.TAB_BAO_GIA
        g = d.get(tab) or {}
        goc = g.get("steps") or []
        buoc = [s for s in goc if not core.is_start_step(s)]
        giu = {s["id"] for s in buoc}
        canh = [e for e in (g.get("edges") or [])
                if e.get("from") in giu and e.get("to") in giu]
        return _ok({
            "steps": buoc, "edges": canh,
            "tham_so": [],
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
        # ⚠ `don_vi` · `sua_che_do` · `phep_so` · `trang_thai_lenh` · `ly_do_dong` đã
        # bỏ cùng từ vựng và cùng `so_lenh.py` (đợt 3). Hộp thoại Kho giờ chỉ còn ba
        # danh sách RỖNG từ `kho.danh_muc()` cộng bảng hành động — nó phải NÓI RA rằng
        # kho đang trống, chứ không vẽ một bảng không giải thích.
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

    # ---------------------------------------------------------- NGUỒN DỮ LIỆU
    #
    # ⚠ APP KHÔNG SỞ HỮU BỘ GHI. Nó là một tiến trình riêng phải sống 24/7, kể cả khi
    # app đóng — đúng bài học mà cửa sổ Live cũ đã trả giá: "đóng cửa sổ không được
    # dừng phiên". App chỉ NHÌN (qua nhịp tim) và XIN (qua cờ dừng).
    #
    # Vì thế `dong_app` không đụng gì tới bộ ghi, và đó là chủ ý chứ không phải quên.
    @_bat_loi
    def nguon_liet_ke(self):
        """Đang có dữ liệu gì, và bộ ghi còn sống không.

        Trả cả hai trong MỘT lời gọi: hộp thoại luôn cần cả hai cùng lúc, mà hai lời
        gọi thì có lúc lệch nhau nửa giây và bảng nói một đằng, đèn báo một nẻo."""
        return _ok({"ds": nguon_tick.liet_ke(),
                    "ghi": nguon_tick.trang_thai_ghi(),
                    "cai_dat": nguon_tick.cai_dat(),
                    "thu_muc": nguon_tick.goc_tick()})

    @_bat_loi
    def nguon_bat_dau(self, symbols):
        """Mở bộ ghi trong một TIẾN TRÌNH RỜI.

        `DETACHED_PROCESS` chứ không phải tiến trình con: tiến trình con chết theo cha,
        mà cha ở đây là một app người ta đóng vào mở ra suốt ngày. Dữ liệu thì không
        chấp nhận chuyện đó.

        stdout đổ vào `_ghi.log` — tiến trình rời không có console, nên không hứng thì
        mọi lời than của nó rơi vào hư không, kể cả câu giải thích vì sao nó chết."""
        syms = [str(x).strip().upper() for x in (symbols or []) if str(x).strip()]
        if not syms:
            return _loi("Chưa chọn symbol nào.")
        tt = nguon_tick.trang_thai_ghi()
        if tt["song"]:
            return _loi(f"Bộ ghi đang chạy rồi (pid {tt['pid']}, "
                        f"{', '.join(tt['symbols'])}). Dừng nó trước.")
        if getattr(sys, "frozen", False):
            return _loi("Bản đóng gói chưa mở được bộ ghi — nó cần Python. "
                        f"Chạy tay:  python tools/ghi_tick.py {' '.join(syms)}")

        import subprocess
        goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kich_ban = os.path.join(goc, "tools", "ghi_tick.py")
        if not os.path.exists(kich_ban):
            return _loi(f"Không thấy {kich_ban}")
        nguon_tick.xoa_co_dung()
        thu_muc = nguon_tick.goc_tick()
        os.makedirs(thu_muc, exist_ok=True)
        log = open(os.path.join(thu_muc, "_ghi.log"), "a", encoding="utf-8")
        co = 0
        if os.name == "nt":
            co = 0x00000008 | 0x00000200      # DETACHED_PROCESS | NEW_PROCESS_GROUP
        subprocess.Popen([sys.executable, kich_ban, *syms],
                         cwd=goc, stdout=log, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, creationflags=co, close_fds=True)
        # NHỚ danh sách symbol. Bộ ghi khởi động lại thì phải biết ghi gì — bắt gõ
        # tay mỗi lần thì một lần quên là mất cả ngày dữ liệu.
        self._luu_nguon({"symbols": syms})
        return _ok({"symbols": syms})

    @_bat_loi
    def nguon_dung(self):
        """XIN bộ ghi dừng — đặt cờ, không giết.

        Giết bằng `taskkill /F` là cắt ngang giữa chừng, mất đúng phần đệm chưa xả.
        Cờ thì bộ ghi thấy ở nhịp kế, xả hết rồi mới thoát. Đổi lại mất tối đa vài
        giây — rẻ hơn nhiều so với một lỗ hổng tự tay tạo ra."""
        tt = nguon_tick.trang_thai_ghi()
        if not tt["song"]:
            return _loi("Bộ ghi không chạy.")
        nguon_tick.xin_dung()
        return _ok({"da_xin": True, "pid": tt["pid"]})

    def _luu_nguon(self, moi):
        """Trộn vào mục `nguon` của cài đặt rồi ghi. Trộn chứ không đè: chỗ gọi chỉ gửi
        khoá nó quan tâm, và mấy khoá kia không được biến mất theo."""
        cd = dict(self._cai_dat)
        ng = dict(luu_tru.CAI_DAT_MAC_DINH["nguon"])
        ng.update(cd.get("nguon") or {})
        ng.update(moi)
        cd["nguon"] = ng
        self._cai_dat = core.save_settings(cd)
        return ng

    @_bat_loi
    def nguon_luu_cai_dat(self, cd):
        """Bốn con số của nguồn. CHỈ bốn — mọi thứ khác về nguồn đều đo được, và hỏi
        một thứ đo được là mời người ta gõ một con số sai rồi tin nó.

        ⚠ Đổi `thu_muc` KHÔNG dời dữ liệu cũ. Cố ý: dời vài chục GB ngầm sau lưng người
        dùng là việc không được phép làm im lặng, và nếu nửa chừng hết đĩa thì hỏng cả
        hai đầu. Giao diện phải nói ra điều đó."""
        cd = cd or {}
        ra = {}
        if "symbols" in cd:
            ra["symbols"] = [str(x).strip().upper() for x in (cd["symbols"] or [])
                             if str(x).strip()]
        if "thu_muc" in cd:
            ra["thu_muc"] = str(cd["thu_muc"] or "").strip()
        for k, kieu, nho_nhat in (("giu_ngay", int, 0), ("im_lang_giay", float, 5.0),
                                  ("giay_xa", float, 0.2)):
            if k in cd:
                try:
                    v = kieu(cd[k])
                except (TypeError, ValueError):
                    return _loi(f'"{k}" phải là một con số.')
                if v < nho_nhat:
                    return _loi(f'"{k}" không được nhỏ hơn {nho_nhat:g}.')
                ra[k] = v
        ng = self._luu_nguon(ra)
        # Ghi xong mới báo bộ ghi biết: ngưỡng và nhịp xả chỉ có tác dụng ở LẦN CHẠY
        # SAU của bộ ghi, vì nó đọc cài đặt lúc khởi động. Nói ra chứ đừng để người
        # dùng tưởng vừa đổi là ăn ngay.
        return _ok({"cai_dat": ng,
                    "can_khoi_dong_lai": nguon_tick.trang_thai_ghi()["song"]})

    @_bat_loi
    def nguon_do_thi_truong(self, kl_toi_thieu=200.0, phi=None):
        """Quét sàn: `spread ÷ (2 × phí maker)`. Điều kiện CẦN của cả hệ.

        Cùng lõi với `tools/do_spread.py` — một nguồn sự thật, không hai bản chép tay.
        Chậm (vài chục giây, hỏi bốn sàn), nên giao diện phải hiện trạng thái chờ."""
        du, hong = do_thi_truong.do(None, float(kl_toi_thieu),
                                    None if phi is None else float(phi))
        return _ok({"ds": du[:60], "so": len(du), "hong": hong,
                    "phi_dang_dung": dict(do_thi_truong.PHI_MAKER)})

    @_bat_loi
    def nguon_xoa(self, symbol):
        """Xoá HẲN dữ liệu một symbol. Giao diện PHẢI hỏi trước — xoá là không lùi được."""
        tt = nguon_tick.trang_thai_ghi()
        if tt["song"] and str(symbol).upper() in tt["symbols"]:
            return _loi(f"{symbol} đang được ghi. Dừng bộ ghi trước khi xoá.")
        byte = nguon_tick.xoa(symbol)
        return _ok({"mb": round(byte / 1e6, 1), "ds": nguon_tick.liet_ke()})

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
