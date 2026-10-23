"""CHẠY LEAN TẠI MÁY — bấm một nút là có kết quả backtest.

Đây là đoạn cuối của vòng *vẽ → sinh → CHẠY → đọc → sửa*. Trước nó phải gõ tay ba
bước; file này gói cả ba lại.

KHÔNG TÍNH GÌ CẢ. LEAN chạy xong ghi ra một file JSON đã có sẵn **8 biểu đồ nó tự
dựng, 27 thống kê, danh sách lệnh và danh sách giao dịch khép**. Việc của ta là gọi nó
rồi đọc file — đúng lời hứa D-11 "app chỉ là VỎ".

BA CÁI BẪY, cả ba đã cắn thật:

  1. **ĐỪNG TIN MÃ THOÁT.** pythonnet trên Windows ném
     *"GIL must always be released"* lúc tắt, sau khi kết quả đã ghi xong xuôi. Mã
     thoát khác 0 mà backtest thì hoàn hảo. Luật: **đọc file, đừng đọc mã thoát.**
  2. **PHẢI GỘT SẠCH BIẾN MÔI TRƯỜNG CỦA VENV.** App chạy trong `.venv`, mà venv ấy
     không có pandas. LEAN nạp Python qua `PYTHONNET_PYDLL`; nếu `VIRTUAL_ENV` /
     `PYTHONHOME` / `PYTHONPATH` còn sót lại, nó trỏ vào venv và chết vì thiếu pandas.
  3. **LEAN chạy trong THƯ MỤC CỦA NÓ.** `config.json` nó đọc là file cạnh exe, nên
     phải ghi vào đúng chỗ ấy và đặt `cwd` vào đó.

CÓ MỘT CẤU HÌNH NGƯỜI DÙNG PHẢI ĐIỀN: đường dẫn tới thư mục LEAN. Không đoán hộ —
LEAN là một kho mã mấy trăm MB, nó nằm đâu là việc của người dùng.
"""
import json
import os
import re
import subprocess
import sys
import sysconfig
import threading
import time

from . import cai_dat
from . import luu_tru
from .ngon_ngu import tr

#: Tên cấu hình: thư mục gốc của bản LEAN đã build (chỗ có `Launcher/`).
KHOA_LEAN = cai_dat.KHOA_LEAN

#: Trần thời gian một lượt backtest, MẶC ĐỊNH. Quá thì giết — thà báo "chạy lâu quá"
#: còn hơn treo cả app vô thời hạn.
#:
#: ⚠ Người dùng chỉnh được ở hộp Cài đặt; `_han_gio()` dưới đây mới là con số thật.
#: Đừng đọc thẳng hằng số này — đặt 60 phút trong Cài đặt mà vẫn bị giết ở phút 15
#: thì cái núm ấy là núm giả.
HAN_GIO = 900


def _han_gio():
    """Hạn giờ một lượt chạy (giây), lấy từ Cài đặt."""
    return cai_dat.han_gio_giay(luu_tru.doc_cai_dat())


#: GIAI ĐOẠN — đọc từ dòng TRACE của LEAN.
#:
#: ⚠ LEAN **không in phần trăm** ra màn hình: `BacktestProgressMonitor` chỉ đẩy số ấy
#: vào gói kết quả gửi lên đám mây. Nên ở đây KHÔNG bịa một con số tiến độ — chỉ nói
#: đang ở giai đoạn nào và đã chạy bao lâu. Thanh tiến độ giả còn tệ hơn không có:
#: nó hứa một cái mốc mà không ai giữ được.
#: ⚠ MỐC PHẢI ĐỦ DÀI. Hai lần đầu tôi lấy tên lớp trống không và cả hai đều bắn sớm:
#: `AlgorithmManager` khớp luôn dòng `CreateTokenBucket` — dòng TRACE thứ BA, lúc LEAN
#: còn chưa nạp Python; `BacktestingResultHandler` thì xuất hiện TRƯỚC `AlgorithmManager
#: .Run`. Hậu quả: hộp báo "Chạy backtest" trong khi LEAN mới đang khởi động.
#: Thứ tự thật, đọc từ nhật ký một lượt chạy:
#:   Engine.Main · JobQueue.NextJob · AlgorithmManager.CreateTokenBucket · Engine.Run ·
#:   PythonInitializer · AlgorithmPythonWrapper · LocalObjectStore ·
#:   HistoryProviderManager · BaseSetupHandler.Setup · BacktestingResultHandler ·
#:   AlgorithmManager.Run · … · DataMonitor.GenerateReport · BacktestingResultHandler.Exit
GIAI_DOAN = (
    ("BacktestingResultHandler.Exit", "Dựng kết quả"),
    ("DataMonitor.GenerateReport", "Dựng kết quả"),
    ("AlgorithmManager.Run", "Chạy backtest"),
    ("BaseSetupHandler.Setup", "Chuẩn bị thuật toán"),
    ("HistoryProviderManager", "Chuẩn bị thuật toán"),
    ("LocalObjectStore", "Chuẩn bị thuật toán"),
    ("AlgorithmPythonWrapper", "Nạp thuật toán Python"),
    ("PythonInitializer", "Khởi động Python"),
    ("JobQueue", "Khởi động LEAN"),
    ("Engine.Main", "Khởi động LEAN"),
)

#: Trạng thái lượt chạy ĐANG diễn ra. Một lượt một lúc — chạy hai backtest song song
#: thì chúng ghi đè `config.json` của nhau trong cùng thư mục LEAN.
_KHOA = threading.Lock()
#: `gd_i` = chỉ số giai đoạn trong `GIAI_DOAN` (bảng xếp từ MUỘN tới SỚM), dùng để
#: giai đoạn KHÔNG BAO GIỜ ĐI LÙI. Đã lùi thật: dòng lỗi GIL lúc tắt có chữ
#: `PythonInitializer`, nên sau khi báo "Dựng kết quả" nó nhảy về "Khởi động Python"
#: — người xem tưởng backtest chạy lại từ đầu.
_TRANG_THAI = {"dang_chay": False, "xong": False, "bat_dau": 0.0,
               "giai_doan": "", "gd_i": 99, "dong_cuoi": "", "so_dong": 0,
               "kq": None,
               #: Tiến trình LEAN đang chạy — giữ lại để DỪNG được. Không gửi qua
               #: cầu nối (`trang_thai` gỡ ra), vì một `Popen` không đóng gói JSON.
               "tien_trinh": None,
               #: Người dùng bấm Dừng — để phân biệt "LEAN chết" với "ta giết nó".
               "da_dung": False}


def _dat(**kw):
    with _KHOA:
        _TRANG_THAI.update(kw)


def dung():
    """DỪNG lượt đang chạy. -> {ok, loi}

    Giết thẳng tiến trình LEAN. Vòng `for d in p.stdout` sẽ kết thúc ngay vì ống
    đóng, rồi `chay()` đi tiếp và không tìm thấy file kết quả — nên phải đánh dấu
    `da_dung` để chỗ ấy nói đúng «bạn đã dừng», chứ không phải «LEAN chạy xong mà
    không ghi ra kết quả».

    Không dùng `terminate()`: trên Windows nó cũng là `TerminateProcess`, mà LEAN
    không có trình xử lý tín hiệu nào để dọn dẹp tử tế. Giết là giết."""
    with _KHOA:
        if not _TRANG_THAI["dang_chay"]:
            return {"ok": False, "loi": tr("Không có lượt nào đang chạy.")}
        p = _TRANG_THAI["tien_trinh"]
        _TRANG_THAI["da_dung"] = True
    if p is None:
        # Đã bấm Chạy nhưng LEAN chưa kịp khởi động. Cờ `da_dung` ở trên sẽ chặn
        # ngay khi tiến trình vừa dựng xong.
        return {"ok": True, "loi": ""}
    try:
        p.kill()
    except Exception as e:                          # noqa: BLE001
        return {"ok": False, "loi": tr("Không dừng được: {0}: {1}", type(e).__name__, e)}
    return {"ok": True, "loi": ""}


def trang_thai():
    """Ảnh chụp trạng thái lượt chạy -> giao diện hỏi mỗi nửa giây."""
    with _KHOA:
        t = dict(_TRANG_THAI)
    # `Popen` không đóng gói JSON được — và giao diện cũng chẳng cần nó.
    t.pop("tien_trinh", None)
    t["giay"] = round(time.time() - t["bat_dau"], 1) if t["bat_dau"] else 0
    return t


def _doc_dan(ten_luong, dong):
    """Một dòng LEAN vừa in -> cập nhật giai đoạn. Gọi từ luồng đọc."""
    s = dong.strip()
    if not s:
        return
    for i, (khoa, nhan) in enumerate(GIAI_DOAN):
        if khoa in s:
            with _KHOA:
                # Bảng xếp từ MUỘN tới SỚM, nên chỉ số NHỎ hơn = giai đoạn MUỘN hơn.
                if i <= _TRANG_THAI["gd_i"]:
                    _TRANG_THAI["giai_doan"] = nhan
                    _TRANG_THAI["gd_i"] = i
            break
    with _KHOA:
        _TRANG_THAI["so_dong"] += 1
        # Cắt phần dấu thời gian dài ngoằng ở đầu, giữ phần người đọc hiểu được.
        _TRANG_THAI["dong_cuoi"] = re.sub(r"^\S+\s+TRACE::\s*", "", s)[:160]


def _duong_launcher(goc):
    """-> đường dẫn exe của LEAN, hay "" nếu chưa build / sai thư mục."""
    for kieu in ("Release", "Debug"):
        p = os.path.join(goc, "Launcher", "bin", kieu,
                         "QuantConnect.Lean.Launcher.exe")
        if os.path.isfile(p):
            return p
    return ""


def _got_json(raw):
    """`config.json` của LEAN có chú thích `//` và dấu phẩy thừa — JSON thật không nhận.

    Gột phải BIẾT ĐANG Ở TRONG CHUỖI HAY KHÔNG: một giá trị `https://…` mà cắt từ `//`
    là mất luôn nửa đường dẫn."""
    ra, trong_chuoi, thoat, i = [], False, False, 0
    while i < len(raw):
        c = raw[i]
        if trong_chuoi:
            ra.append(c)
            if thoat:
                thoat = False
            elif c == "\\":
                thoat = True
            elif c == '"':
                trong_chuoi = False
            i += 1
            continue
        if c == '"':
            trong_chuoi = True
            ra.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < len(raw) and raw[i + 1] == "/":
            while i < len(raw) and raw[i] != "\n":
                i += 1
            continue
        ra.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(ra))


def _moi_truong():
    """Môi trường cho tiến trình LEAN — ĐÃ GỘT sạch dấu vết venv.

    Xem bẫy 2 ở đầu file: để sót `VIRTUAL_ENV` là LEAN nạp Python của venv (không có
    pandas) rồi chết, mà thông báo thì chẳng nhắc gì tới venv."""
    e = dict(os.environ)
    for k in ("VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"):
        e.pop(k, None)
    goc_py = sysconfig.get_config_var("installed_base") or sys.base_prefix
    dll = ""
    for ten in (f"python{sys.version_info.major}{sys.version_info.minor}.dll",
                "python3.dll"):
        p = os.path.join(goc_py, ten)
        if os.path.isfile(p):
            dll = p
            break
    if dll:
        e["PYTHONNET_PYDLL"] = dll
    # Bỏ venv khỏi PATH để `python` gõ ra không trỏ nhầm.
    v = os.environ.get("VIRTUAL_ENV")
    if v:
        e["PATH"] = os.pathsep.join(
            x for x in e.get("PATH", "").split(os.pathsep)
            if x and not x.lower().startswith(v.lower()))
    return e, dll


#: Tên thư mục LEAN đặt KÈM app. Tìm cạnh exe (bản đóng gói) hoặc ở gốc dự án.
TEN_LEAN_KEM = "Lean"


def lean_kem():
    """LEAN đặt kèm app, nếu có. -> đường dẫn hay "".

    ⚠ ĐÂY LÀ NỬA MÃ CỦA MỐC M7 (thiết kế §8.1). Muốn người lạ chơi được thì không thể
    bắt họ tự build LEAN rồi vào Cài đặt dán đường dẫn — vài giờ, và chỉ dân lập trình
    qua nổi. Có hàm này thì gói LEAN kèm app chỉ còn là một dòng trong `Cat_Studio.spec`
    (thêm thư mục vào `datas`), không phải sửa mã nữa.
    Đo thật trên bản LEAN đang chạy: máy 115 MB, còn dữ liệu thì chỉ cần phần NGÀY của
    mấy mã trong màn — 320 KB cho ba mã. Tức gói kèm khoảng 120 MB, không phải 1,3 GB.

    ⚠ VÀ BA THỨ CÒN VƯỚNG, không phải chuyện mã: bản build hiện tại cần .NET 10 cài sẵn
    (nó `framework-dependent`, không có `coreclr.dll`); pythonnet cần đúng một
    `python3xx.dll` phải gói kèm; và ĐIỀU KHOẢN DỮ LIỆU thì trong `Data/` không có file
    giấy phép nào — mã nguồn LEAN là Apache-2.0 nhưng không đương nhiên kéo theo dữ
    liệu. Chưa hỏi QuantConnect thì chưa phát hành kèm được."""
    for goc in (luu_tru.thu_muc_app(), luu_tru.thu_muc_goi()):
        d = os.path.join(goc, TEN_LEAN_KEM)
        if os.path.isdir(os.path.join(d, "Launcher")):
            return d
    return ""


def san_sang():
    """LEAN đã sẵn sàng chưa. -> {ok, goc, launcher, dll, loi}

    Thứ tự tìm: đường dẫn người dùng ĐẶT TRONG CÀI ĐẶT trước, rồi mới tới bản đặt kèm.
    Người đã trỏ tay vào một bản LEAN riêng thì phải được tôn trọng — bản kèm chỉ là lối
    cho người chưa có gì."""
    goc = str((luu_tru.doc_cai_dat().get(KHOA_LEAN) or "")).strip() or lean_kem()
    _e, dll = _moi_truong()
    if not goc:
        return {"ok": False, "goc": "", "launcher": "", "dll": dll,
                "loi": tr("Chưa chỉ chỗ đặt LEAN. Mở Cài đặt rồi trỏ vào thư mục LEAN đã build "
                          "(thư mục có `Launcher/`).")}
    if not os.path.isdir(goc):
        return {"ok": False, "goc": goc, "launcher": "", "dll": dll,
                "loi": tr("Không có thư mục «{0}».", goc)}
    exe = _duong_launcher(goc)
    if not exe:
        return {"ok": False, "goc": goc, "launcher": "", "dll": dll,
                "loi": tr("Có thư mục nhưng chưa thấy `QuantConnect.Lean.Launcher.exe` trong "
                          "`Launcher/bin/Release`. LEAN đã build chưa?")}
    if not os.path.isdir(os.path.join(goc, "Data")):
        return {"ok": False, "goc": goc, "launcher": exe, "dll": dll,
                "loi": tr("Không thấy thư mục `Data` của LEAN.")}
    if not dll:
        return {"ok": False, "goc": goc, "launcher": exe, "dll": "",
                "loi": tr("Không tìm ra python3xx.dll — LEAN cần nó để chạy thuật toán Python.")}
    return {"ok": True, "goc": goc, "launcher": exe, "dll": dll, "loi": ""}


def _doc_ket_qua(thu_muc, ten_lop):
    """Đọc file kết quả LEAN vừa ghi. -> (dữ liệu | None, nhật ký)."""
    p = os.path.join(thu_muc, ten_lop + ".json")
    d = None
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = None
    nk = ""
    pl = os.path.join(thu_muc, ten_lop + "-log.txt")
    if os.path.isfile(pl):
        try:
            with open(pl, encoding="utf-8", errors="replace") as f:
                nk = f.read()
        except OSError:
            pass
    return d, nk


#: Dấu mở đầu mỗi dòng VẾT trong nhật ký LEAN.
#:
#: ⚠ CÙNG MỘT CHUỖI VỚI `sinh_ma.DAU_VET`, và `tests/test_vet.py` canh cho hai bên
#: không lệch. Khai lại ở đây chứ không `import sinh_ma`: `chay_lean` cố ý không biết
#: gì về bộ sinh mã (nó chạy được một file Python bất kỳ), mà một dòng `import` chỉ
#: để lấy một chuỗi là buộc hai mô-đun vào nhau vì không gì cả.
DAU_VET = "CAT|"

#: `seriesType` của LEAN -> tên kiểu vẽ. Đọc thẳng từ `Common/BaseSeries.cs`.
#: Giao diện KHÔNG tự khai bảng này — đoán một bảng mã số là sai lặng.
KIEU_DUONG = {0: "duong", 1: "cham", 2: "nen", 3: "cot", 4: "co",
              5: "vung_chong", 6: "tron", 7: "o_vuong", 8: "nhiet", 9: "cham"}

#: Thứ tự bày các bảng. LEAN trả `charts` theo thứ tự tùy hứng; người đọc thì luôn
#: muốn thấy đường vốn trước. Tên nào không có trong đây thì xếp cuối, không bỏ đi.
THU_TU_BANG = ("Strategy Equity", "Benchmark", "Drawdown", "Exposure",
               "Portfolio Turnover", "Portfolio Margin", "Assets Sales Volume",
               "Capacity")

#: Bảng bày sẵn lúc mở màn Kết quả. Sáu bảng cùng lúc thì không ai nhìn cái nào.
BANG_MAC_DINH = ("Strategy Equity", "Drawdown")

#: Trần số điểm MỖI ĐƯỜNG gửi sang giao diện.
#:
#: Vì sao phải có: một lượt chạy nhịp PHÚT trong vài năm đẻ ra hàng trăm nghìn điểm
#: mỗi đường. Gửi hết thì cầu nối nghẹt và trình duyệt treo — mà màn hình rộng
#: chỉ ~1000 điểm ảnh, nên vẽ hơn ngần ấy là vẽ vào chỗ không ai thấy.
TRAN_DIEM = 3000


def _diem(v):
    """Một điểm LEAN ghi -> [giây, …] hay None nếu hỏng.

    LEAN ghi hai kiểu: `{"x":…,"y":…}` cho điểm thường, và mảng
    `[giây, mở, cao, thấp, đóng]` cho nến."""
    if isinstance(v, dict):
        x, y = v.get("x"), v.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return [x, y]
        return None
    if isinstance(v, (list, tuple)) and len(v) >= 2:
        if all(isinstance(t, (int, float)) for t in v):
            return list(v)
    return None


def _thua(ds, la_nen):
    """Bớt điểm xuống dưới `TRAN_DIEM`, bằng cách GỘP chứ không phải nhảy cóch.

    ⚠ Nhảy cách (lấy 1 trong mỗi 10 điểm) làm MẤT ĐỈNH VÀ ĐÁY: một cú sụt 30% gọn
    trong vài nến sẽ biến mất khỏi biểu đồ, mà người xem không hề biết. Gộp thì
    giữ được: nến lấy mở-đầu / cao-nhất / thấp-nhất / đóng-cuối, đường lấy cả đỉnh
    lẫn đáy của mỗi rổ."""
    n = len(ds)
    if n <= TRAN_DIEM:
        return ds
    co = (n + TRAN_DIEM - 1) // TRAN_DIEM
    ra = []
    for i in range(0, n, co):
        ro = ds[i:i + co]
        if la_nen and len(ro[0]) >= 5:
            ra.append([ro[0][0], ro[0][1],
                       max(p[2] for p in ro), min(p[3] for p in ro), ro[-1][4]])
        else:
            # Giữ cả đỉnh lẫn đáy của rổ, theo đúng thứ tự thời gian.
            cao = max(ro, key=lambda p: p[-1])
            thap = min(ro, key=lambda p: p[-1])
            hai = sorted({id(cao): cao, id(thap): thap}.values(),
                         key=lambda p: p[0])
            ra.extend(hai)
    return ra


def _bieu_do(d):
    """Mọi biểu đồ LEAN dựng -> dạng giao diện vẽ được.

    KHÔNG cắt bớt bảng nào: LEAN tự dựng tám cái, bày hết rồi để người chơi bật tắt."""
    ds = d.get("charts") or {}
    thu_tu = {t: i for i, t in enumerate(THU_TU_BANG)}
    ra = []
    for ten in sorted(ds, key=lambda t: (thu_tu.get(t, 99), t)):
        duong = []
        for ten_d, s in (ds[ten].get("series") or {}).items():
            kieu = KIEU_DUONG.get(s.get("seriesType"), "duong")
            diem = [p for p in (_diem(v) for v in (s.get("values") or [])) if p]
            if not diem:
                continue
            duong.append({"ten": ten_d, "kieu": kieu,
                          "don_vi": s.get("unit") or "",
                          "diem": _thua(diem, kieu == "nen")})
        if duong:
            ra.append({"ten": ten, "duong": duong,
                       "hien": ten in BANG_MAC_DINH})
    return ra


def _cuon(d):
    """`rollingWindow` -> bảng Thống kê trượt: mỗi tháng một dòng, bốn cột 1/3/6/12 tháng.

    Khoá của LEAN có dạng `M1_20100131` — cửa sổ mấy tháng, rồi ngày chốt."""
    rw = d.get("rollingWindow") or {}
    bang = {}
    chi_tieu = set()
    for khoa, v in rw.items():
        p = str(khoa).split("_")
        if len(p) != 2 or not p[0].startswith("M"):
            continue
        cua, ngay = p[0][1:], p[1]
        ps = (v.get("portfolioStatistics") or {})
        chi_tieu.update(ps)
        bang.setdefault(ngay, {})[cua] = ps
    return {
        "chi_tieu": sorted(chi_tieu),
        "dong": [{"ngay": ng, "cua": bang[ng]} for ng in sorted(bang)],
    }


#: Mã số LEAN ghi trong file kết quả -> chữ đọc được.
#:
#: ⚠ Đọc THẲNG từ `Common/Orders/OrderTypes.cs`, đừng nhớ theo trí nhớ:
#: `OrderStatus` **không có số 4** (Canceled nhảy thẳng lên 5). Đoán một bảng như thế
#: thì mọi lệnh bị huỷ sẽ hiện sai tên mà chẳng ai thấy.
LOAI_LENH = ("Thị trường", "Giới hạn", "Dừng", "Dừng giới hạn", "Khớp lúc mở",
             "Khớp lúc đóng", "Thực hiện quyền", "Chạm rồi giới hạn", "Combo thị trường",
             "Combo giới hạn", "Combo chân giới hạn", "Dừng trượt")
TRANG_THAI_LENH = {0: "Mới", 1: "Đã gửi", 2: "Khớp một phần", 3: "Đã khớp",
                   5: "Đã huỷ", 6: "Không", 7: "KHÔNG HỢP LỆ", 8: "Đang huỷ",
                   9: "Đang sửa"}


def _ten_ma(x):
    """Khoá `symbol` của LEAN là một object, không phải chuỗi."""
    if isinstance(x, dict):
        return str(x.get("value") or x.get("permtick") or "?")
    return str(x or "?")


def _lenh_gon(o):
    """Một lệnh -> đúng mấy cột bảng cần, chữ đã dịch sẵn."""
    t = o.get("type")
    return {
        "id": o.get("id"),
        "ma": _ten_ma(o.get("symbol")),
        "luc": str(o.get("time") or "")[:19].replace("T", " "),
        "loai": LOAI_LENH[t] if isinstance(t, int) and 0 <= t < len(LOAI_LENH)
                else str(t),
        "so_luong": o.get("quantity"),
        "gia": o.get("price"),
        "trang_thai": TRANG_THAI_LENH.get(o.get("status"), str(o.get("status"))),
        "hop_le": o.get("status") != 7,
        "tag": str(o.get("tag") or ""),
        # KHOẢNG CHỜ của một lệnh: đặt lúc nào, khớp lúc nào. Cửa sổ View vẽ mức giá
        # lệnh chờ lên chart đúng những nến nó còn treo ở đó — mà «còn treo» thì
        # phải có cả hai mốc mới biết. Lệnh khớp ngay (market) thì hai mốc bằng nhau,
        # lệnh chưa bao giờ khớp thì `khop` rỗng.
        "tao": str(o.get("createdTime") or o.get("time") or "")[:19].replace("T", " "),
        "khop": str(o.get("lastFillTime") or "")[:19].replace("T", " "),
    }


def _giao_dich_gon(t):
    ds = t.get("symbols") or []
    return {
        "ma": _ten_ma(ds[0]) if ds else "?",
        "vao_luc": str(t.get("entryTime") or "")[:10],
        "gia_vao": t.get("entryPrice"),
        "ra_luc": str(t.get("exitTime") or "")[:10],
        "gia_ra": t.get("exitPrice"),
        "so_luong": t.get("quantity"),
        "lai_lo": t.get("profitLoss"),
        "phi": t.get("totalFees"),
        "thang": bool(t.get("isWin")),
    }


#: Trần số dòng VẾT gửi sang giao diện.
#:
#: Bộ sinh mã đã có trần của nó (`sinh_ma.VET_TOI_DA`, 20000 dòng ghi ra nhật ký); đây
#: là trần thứ hai, của cái cầu nối. Hai con số khác việc nhau: bên kia giữ cho file
#: nhật ký đừng phình, bên này giữ cho cầu nối đừng nghẹt và WebView2 đừng treo —
#: cùng lý do với `TRAN_DIEM`.
TRAN_VET = 8000


def _doc_vet(nk):
    """Nhật ký LEAN -> mấy dòng VẾT đã tách sẵn. -> ([{luc, ma, cong}], bị cắt?)

    Cỗ máy tự ghi mỗi nhịp một dòng `CAT|<giờ>|<mã>|-1A,1B,-1C` — xem `sinh_ma._vet`:
    dấu trừ là cổng ĐÓNG. Ở đây chỉ việc tách lại, không suy thêm một chữ nào.

    ⚠ ĐỌC TỪ `nk` ĐẦY ĐỦ, không đọc từ `nhat_ky` đã cắt. `_gon` chỉ gửi 60000 ký tự
    CUỐI của nhật ký sang giao diện (một file nhật ký LEAN có thể vài MB) — tách vết
    từ bản đã cắt ấy thì mất hết vết của nửa đầu lượt chạy, mà bảng vẫn trông đầy.

    ⚠ KHÔNG NUỐT DÒNG LẠ. Một dòng mang dấu `CAT|` mà không đủ bốn phần thì bỏ, chứ
    không đoán phần thiếu: thà thiếu một dòng còn hơn bày một mốc giờ bịa ra."""
    ra = []
    cat = False
    for dong in str(nk or "").splitlines():
        i = dong.find(DAU_VET)
        if i < 0:
            continue
        phan = dong[i + len(DAU_VET):].rstrip().split("|")
        if len(phan) != 3 or not phan[0]:
            continue
        if len(ra) >= TRAN_VET:
            cat = True
            break
        cong = [[c.lstrip("-"), not c.startswith("-")]
                for c in phan[2].split(",") if c]
        ra.append({"luc": phan[0], "ma": phan[1], "cong": cong})
    return ra, cat


def _gon(d, nk):
    """Cả đống kết quả -> đúng phần màn Kết quả cần."""
    tp = d.get("totalPerformance") or {}
    vet, vet_cat = _doc_vet(nk)
    return {
        # TÁM Ô SỐ trên đầu — LEAN dựng sẵn đúng tám mục này, không phải ta chọn.
        "o_so": d.get("runtimeStatistics") or {},
        "bieu_do": _bieu_do(d),
        "thong_ke": d.get("statistics") or {},
        "cuon": _cuon(d),
        "may_chu": d.get("serverStatistics") or {},
        "lenh": [_lenh_gon(o) for o in (d.get("orders") or {}).values()],
        "giao_dich": [_giao_dich_gon(t) for t in (tp.get("closedTrades") or [])],
        "nhat_ky": nk[-60000:],
        # VẾT TỪNG NHỊP — cỗ máy tự kể nó dừng ở cổng nào (`sinh_ma._ham_vet`).
        # Rỗng với lượt chạy từ bản cũ, và cửa sổ View nói ra chuyện đó.
        "vet": vet,
        "vet_cat": vet_cat,
    }


#: Thẻ tóm tắt một lượt chạy, ghi cạnh kết quả. Kho lượt chạy đọc THẺ chứ không mở
#: từng file kết quả: một file LEAN nặng vài MB, mà kho chỉ cần năm con số.
TEN_THE = "_the.json"

#: SƠ ĐỒ ĐÃ SINH RA LƯỢT NÀY, ghi cạnh kết quả.
#:
#: ⚠ CHỤP LẠI SƠ ĐỒ, ĐỪNG ĐỌC LẠI SƠ ĐỒ ĐANG VẼ. Cửa sổ View bày «Soi trên sơ đồ»:
#: bấm một dòng nhật ký là thấy lệnh ấy đã đi qua những khối nào. Mà người ta xem lại
#: một lượt chạy TUẦN TRƯỚC, rồi tuần này sơ đồ đã sửa ba lần — soi vào sơ đồ đang vẽ
#: thì vệt sáng chạy trên một cỗ máy khác hẳn cái đã sinh ra mấy cái lệnh ấy, và
#: không gì báo. Mẻ Optimize đã chụp sơ đồ từ lâu (`chay_toi_uu.chay`); backtest thì
#: chưa, nên lối CỨU `api._so_do_theo_ten_lop` phải dò ngược từ tên lớp.
TEN_SO_DO = "_so_do.json"

#: Mấy con số bày trên thẻ. Lấy từ `statistics` của LEAN, tên y nguyên của nó — đổi
#: tên ở đây là tự đẻ một bảng tra thứ hai phải trông coi.
CHI_TIEU_THE = ("Net Profit", "Compounding Annual Return", "Drawdown",
                "Sharpe Ratio", "Total Orders", "Win Rate")


def _ghi_the(thu_muc, kq):
    """Ghi thẻ tóm tắt. Hỏng thì THÔI — mất thẻ chỉ làm kho thiếu một dòng, không
    được phép làm hỏng cả lượt chạy vừa xong."""
    tk = kq.get("thong_ke") or {}
    the = {"id": kq.get("id"), "ten_lop": kq.get("ten_lop"),
           "ma_luot": kq.get("ma_luot"), "luc": time.time(),
           "so": {k: tk[k] for k in CHI_TIEU_THE if k in tk}}
    try:
        luu_tru.ghi_json_nguyen_tu(os.path.join(thu_muc, TEN_THE), the)
    except Exception:                               # noqa: BLE001
        pass


def _ghi_so_do(thu_muc, so_do):
    """Chụp sơ đồ cạnh kết quả. Hỏng thì THÔI — y lý do của `_ghi_the`: mất bản chụp
    chỉ làm «Soi trên sơ đồ» phải dò ngược từ tên lớp, không được phép làm hỏng cả
    lượt chạy vừa xong."""
    if not (so_do or {}).get("steps"):
        return
    try:
        luu_tru.ghi_json_nguyen_tu(
            os.path.join(thu_muc, TEN_SO_DO),
            {"name": so_do.get("name") or "", "steps": so_do.get("steps") or [],
             "edges": so_do.get("edges") or [], "co_may": so_do.get("co_may") or {}})
    except Exception:                               # noqa: BLE001
        pass


def doc_so_do_luot(ma_id):
    """Sơ đồ đã sinh ra lượt `ma_id`. -> doc, hay {} nếu lượt ấy chạy từ bản cũ."""
    d = _thu_muc_luot(ma_id)
    if not d:
        return {}
    try:
        with open(os.path.join(d, TEN_SO_DO), encoding="utf-8") as f:
            sd = json.load(f)
    except (OSError, ValueError):
        return {}
    return sd if isinstance(sd, dict) and sd.get("steps") else {}


def ds_luot_chay():
    """Mọi lượt backtest đã lưu, MỚI NHẤT TRƯỚC. -> [{id, ten_lop, ma_luot, luc, so}]

    Đọc thẻ, không mở file kết quả: kho có thể có hàng trăm lượt, mà mỗi file kết quả
    của LEAN nặng vài MB."""
    goc = luu_tru.thu_muc_ket_qua()
    ra = []
    for ten_lop in sorted(os.listdir(goc)) if os.path.isdir(goc) else []:
        d1 = os.path.join(goc, ten_lop)
        if not os.path.isdir(d1):
            continue
        for ma_luot in os.listdir(d1):
            p = os.path.join(d1, ma_luot, TEN_THE)
            if not os.path.isfile(p):
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    the = json.load(f)
            except (OSError, ValueError):
                continue
            the.setdefault("id", f"{ten_lop}/{ma_luot}")
            ra.append(the)
    ra.sort(key=lambda t: str(t.get("ma_luot") or ""), reverse=True)
    return ra


def _thu_muc_luot(ma_id):
    """`<tên lớp>/<mã lượt>` -> đường dẫn thật, hay None nếu mã bịa.

    ⚠ KHÔNG ghép chuỗi thẳng vào đường dẫn. `"../../.."` trong `ma_id` là một lối
    thoát ra khỏi `du_lieu/`, và cái id ấy đi qua cầu nối từ giao diện."""
    phan = str(ma_id or "").replace("\\", "/").split("/")
    if len(phan) != 2 or not all(phan) or any(p in (".", "..") for p in phan):
        return None
    if any(c in p for p in phan for c in r'\/:*?"<>|'):
        return None
    d = os.path.join(luu_tru.thu_muc_ket_qua(), phan[0], phan[1])
    return d if os.path.isdir(d) else None


def doc_luot_chay(ma_id):
    """Mở lại một lượt đã lưu. -> {ok, loi, ...phần màn Kết quả cần}"""
    d = _thu_muc_luot(ma_id)
    if not d:
        return {"ok": False, "loi": tr("Không có lượt chạy \"{0}\".", ma_id)}
    ten_lop = os.path.basename(os.path.dirname(d))
    dl, nk = _doc_ket_qua(d, ten_lop)
    if dl is None:
        return {"ok": False, "loi": tr("Lượt chạy này không có file kết quả.")}
    return {"ok": True, "loi": "", "ten_lop": ten_lop, "thu_muc": d,
            "ma_luot": os.path.basename(d), "id": f"{ten_lop}/{os.path.basename(d)}",
            **_gon(dl, nk)}


def xoa_luot_chay(ma_id):
    """Xoá hẳn một lượt đã lưu. -> {ok, loi}"""
    d = _thu_muc_luot(ma_id)
    if not d:
        return {"ok": False, "loi": tr("Không có lượt chạy \"{0}\".", ma_id)}
    import shutil
    try:
        shutil.rmtree(d)
    except OSError as e:
        return {"ok": False, "loi": tr("Không xoá được: {0}", e)}
    return {"ok": True, "loi": ""}


def don_kho():
    """Xoá bớt lượt CŨ NHẤT cho đủ giới hạn ở Cài đặt. -> số lượt đã xoá.

    Gọi SAU KHI một lượt chạy xong, không phải lúc mở app: dọn lúc mở thì người dùng
    vừa thấy một lượt trong kho, nháy mắt sau nó biến mất mà chẳng vì hành động nào
    của họ. Dọn sau khi chạy thì đúng nhân quả — thêm một lượt mới, rụng một lượt cũ."""
    gh = cai_dat.gioi_han_kho(cai_dat.KHOA_KHO_BACKTEST, luu_tru.doc_cai_dat())
    ds = ds_luot_chay()                      # đã xếp MỚI NHẤT TRƯỚC
    xoa = 0
    for t in ds[gh:]:
        if xoa_luot_chay(t.get("id") or "")["ok"]:
            xoa += 1
    return xoa


def chay(ma, ten_lop, so_do=None):
    """Chạy một thuật toán đã sinh. -> {ok, loi, ...phần màn Kết quả cần}

    ⚠ Không đọc mã thoát (xem bẫy 1 ở đầu file): có file kết quả là THÀNH CÔNG."""
    sb = san_sang()
    if not sb["ok"]:
        return {"ok": False, "loi": sb["loi"]}

    duong_ma = luu_tru.ghi_ma(ten_lop, ma)
    # MỖI LƯỢT CHẠY MỘT THƯ MỤC RIÊNG, đặt tên theo lúc chạy.
    #
    # ⚠ Bản trước ghi đè thẳng lên `ket_qua/<tên lớp>/` rồi XOÁ SẠCH file cũ trước mỗi
    # lượt. Lý do hồi ấy đúng: còn file cũ thì một lượt chạy hỏng vẫn đọc ra số của
    # lượt trước, và không ai biết mình đang nhìn kết quả của lần nào. Nhưng cách chữa
    # thì quá tay — nó làm mất luôn LỊCH SỬ, mà so hai phiên bản của một chiến thuật
    # chính là việc người ta mở app lên để làm.
    #   Nay mỗi lượt một thư mục, nên không có gì để lẫn: thư mục rỗng = lượt ấy hỏng.
    ma_luot = time.strftime("%Y%m%d-%H%M%S")
    ra_thu_muc = os.path.join(luu_tru.thu_muc_ket_qua(), ten_lop, ma_luot)
    os.makedirs(ra_thu_muc, exist_ok=True)
    # Chụp sơ đồ NGAY, trước khi LEAN chạy: lượt chạy mất vài phút, mà trong lúc ấy
    # người dùng sửa sơ đồ được. Chụp lúc xong là chụp bản đã sửa — xem `TEN_SO_DO`.
    _ghi_so_do(ra_thu_muc, so_do)

    thu_muc_exe = os.path.dirname(sb["launcher"])
    goc_cfg = os.path.join(sb["goc"], "Launcher", "config.json")
    try:
        with open(goc_cfg, encoding="utf-8") as f:
            cfg = json.loads(_got_json(f.read()))
    except (OSError, ValueError) as e:
        return {"ok": False, "loi": tr("Không đọc được config.json của LEAN: {0}", e)}

    cfg.update({
        "algorithm-type-name": ten_lop,
        "algorithm-language": "Python",
        "algorithm-location": duong_ma,
        "data-folder": os.path.join(sb["goc"], "Data"),
        "results-destination-folder": ra_thu_muc,
        "environment": "backtesting",
        # ⚠ NỚI HẠN ĐƯỜNG VẼ. Mặc định `maximum-chart-series` của LEAN là 30 — con số
        # của HẠNG TÀI KHOẢN trên đám mây QuantConnect, không phải giới hạn kỹ thuật.
        # Chạy trên máy mình thì không có hạng nào cả. 30 đường nghe nhiều, nhưng
        # LEAN tự tiêu mất mười cái cho đồ thị của chính nó, và cửa sổ View cần mỗi
        # mã một đường nến cộng mỗi đại lượng một đường: một sơ đồ 8 đại lượng chỉ
        # còn đủ chỗ cho HAI mã, trong khi rổ có năm chục.
        #     Và vượt hạn thì LEAN BỎ IM LẶNG — `BacktestingResultHandler.cs` dòng
        # 726: *"new series will be ignored"*, chỉ một dòng debug. Nên đây không phải
        # chuyện «vẽ được nhiều hơn cho đẹp», mà là chuyện mấy cái chart cuối có tồn
        # tại hay không.
        "maximum-chart-series": 200,
        # ⚠ KHÔNG CÓ DÒNG NÀY THÌ LEAN TREO MÃI. `JobQueue.AcknowledgeJob` chạy xong
        # thì in «Engine.Main(): Press any key to continue.» rồi `Console.Read()` —
        # chờ một phím mà không ai gõ được, vì cửa sổ console của nó bị app nuốt.
        # Vòng đọc `for d in p.stdout` ở dưới chỉ kết thúc khi tiến trình thoát, nên
        # cả lượt chạy đứng im ở giai đoạn cuối cho tới khi người dùng bỏ cuộc.
        #     `close-automatically` là cờ CÓ THẬT của LEAN, đọc thẳng từ
        #     `Queues/JobQueue.cs`: `if (!Config.GetBool("close-automatically"))`.
        # Lắt léo: lúc chạy từ bài kiểm (stdin đã ở EOF) thì `Console.Read()` trả về
        # ngay, nên lỗi này KHÔNG hiện ra khi chạy tự động — chỉ hiện trong app thật.
        "close-automatically": True,
    })
    with open(os.path.join(thu_muc_exe, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    moi_truong, _dll = _moi_truong()
    # ĐỌC TỪNG DÒNG thay vì chờ xong rồi mới đọc một thể: có đọc thì mới nói được
    # «đang nạp thuật toán Python» hay «đang chạy backtest», và người dùng mới biết
    # cái cửa sổ im lìm kia còn sống.
    dong = []
    try:
        p = subprocess.Popen([sb["launcher"]], cwd=thu_muc_exe, env=moi_truong,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             # Khoá thứ HAI cho cùng cái bẫy trên: stdin rỗng thì
                             # `Console.Read()` trả -1 ngay. Cờ config phụ thuộc vào
                             # việc LEAN đọc đúng file ta ghi; cái này thì không.
                             stdin=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace",
                             bufsize=1)
    except OSError as e:
        return {"ok": False, "loi": tr("Không chạy được LEAN: {0}", e)}
    _dat(tien_trinh=p)
    # Bấm Dừng TRONG LÚC LEAN đang khởi động thì lúc ấy chưa có tiến trình để giết —
    # `dung()` chỉ kịp dựng cờ. Kiểm ngay sau khi dựng xong, không thì lượt ấy cứ
    # chạy tiếp như chưa có chuyện gì.
    with _KHOA:
        bo = _TRANG_THAI["da_dung"]
    if bo:
        p.kill()

    han = _han_gio()
    het = time.time() + han
    try:
        for d in p.stdout:
            dong.append(d)
            _doc_dan(ten_lop, d)
            if time.time() > het:
                p.kill()
                return {"ok": False,
                        "loi": tr("LEAN chạy quá {0} phút nên bị dừng. Thử rút ngắn khoảng ngày "
                                  "hoặc đổi nhịp thưa hơn.", han // 60)}
    finally:
        try:
            p.stdout.close()
            p.wait(timeout=20)
        except Exception:
            p.kill()
    man_hinh = "".join(dong)

    with _KHOA:
        if _TRANG_THAI["da_dung"]:
            return {"ok": False, "loi": tr("Bạn đã dừng lượt chạy này.")}

    d, nk = _doc_ket_qua(ra_thu_muc, ten_lop)
    if d is None:
        # Không có file kết quả mới là hỏng thật. Lúc ấy màn hình mới đáng đọc.
        return {"ok": False, "loi": tr("LEAN chạy xong mà không ghi ra kết quả."),
                "nhat_ky": man_hinh[-20000:]}
    kq = {"ok": True, "loi": "", "ten_lop": ten_lop, "thu_muc": ra_thu_muc,
          "ma_luot": ma_luot, "id": f"{ten_lop}/{ma_luot}",
          **_gon(d, nk or man_hinh)}
    _ghi_the(ra_thu_muc, kq)
    don_kho()
    return kq


def bat_dau_chay(ma, ten_lop, so_do=None):
    """Khởi động một lượt backtest trong LUỒNG RIÊNG rồi trả về NGAY.

    Vì sao không chạy thẳng trong cú gọi cầu nối: một lượt backtest mất từ chục giây
    tới vài phút, mà cầu nối chặn thì giao diện không hỏi được tiến độ — nó chỉ ngồi
    im cho tới lúc xong. Nay giao diện gọi hàm này, rồi hỏi `trang_thai()` mỗi nửa
    giây cho tới khi `xong`.

    -> {ok, loi} — mới là "đã khởi động được chưa", chưa phải kết quả backtest."""
    with _KHOA:
        if _TRANG_THAI["dang_chay"]:
            return {"ok": False, "loi": tr("Đang có một lượt chạy rồi — chờ nó xong đã.")}
        _TRANG_THAI.update({"dang_chay": True, "xong": False, "bat_dau": time.time(),
                            "giai_doan": tr("Khởi động LEAN"), "gd_i": 99,
                            "dong_cuoi": "", "so_dong": 0, "kq": None,
                            "tien_trinh": None, "da_dung": False})

    def chay_nen():
        try:
            kq = chay(ma, ten_lop, so_do)
        except Exception as e:                      # noqa: BLE001
            # Luồng nền mà ném thì KHÔNG ai thấy: không có chỗ nào bắt, và giao diện
            # sẽ hỏi tiến độ mãi mãi. Nên gói lại thành một kết quả hỏng tử tế.
            kq = {"ok": False, "loi": f"{type(e).__name__}: {e}"}
        _dat(dang_chay=False, xong=True, kq=kq)

    threading.Thread(target=chay_nen, daemon=True).start()
    return {"ok": True, "loi": ""}
