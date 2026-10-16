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

from . import luu_tru

#: Tên cấu hình: thư mục gốc của bản LEAN đã build (chỗ có `Launcher/`).
KHOA_LEAN = "lean_goc"

#: Trần thời gian một lượt backtest. Quá thì giết — thà báo "chạy lâu quá" còn hơn
#: treo cả app vô thời hạn.
HAN_GIO = 900


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


def san_sang():
    """LEAN đã sẵn sàng chưa. -> {ok, goc, launcher, dll, loi}"""
    goc = str((luu_tru.doc_cai_dat().get(KHOA_LEAN) or "")).strip()
    _e, dll = _moi_truong()
    if not goc:
        return {"ok": False, "goc": "", "launcher": "", "dll": dll,
                "loi": "Chưa chỉ chỗ đặt LEAN. Mở Cài đặt rồi trỏ vào thư mục LEAN "
                       "đã build (thư mục có `Launcher/`)."}
    if not os.path.isdir(goc):
        return {"ok": False, "goc": goc, "launcher": "", "dll": dll,
                "loi": f"Không có thư mục «{goc}»."}
    exe = _duong_launcher(goc)
    if not exe:
        return {"ok": False, "goc": goc, "launcher": "", "dll": dll,
                "loi": "Có thư mục nhưng chưa thấy `QuantConnect.Lean.Launcher.exe` "
                       "trong `Launcher/bin/Release`. LEAN đã build chưa?"}
    if not os.path.isdir(os.path.join(goc, "Data")):
        return {"ok": False, "goc": goc, "launcher": exe, "dll": dll,
                "loi": "Không thấy thư mục `Data` của LEAN."}
    if not dll:
        return {"ok": False, "goc": goc, "launcher": exe, "dll": "",
                "loi": "Không tìm ra python3xx.dll — LEAN cần nó để chạy thuật toán "
                       "Python."}
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


def _gon(d, nk):
    """Cả đống kết quả -> đúng phần màn Kết quả cần."""
    tp = d.get("totalPerformance") or {}
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
    }


def chay(ma, ten_lop):
    """Chạy một thuật toán đã sinh. -> {ok, loi, ...phần màn Kết quả cần}

    ⚠ Không đọc mã thoát (xem bẫy 1 ở đầu file): có file kết quả là THÀNH CÔNG."""
    sb = san_sang()
    if not sb["ok"]:
        return {"ok": False, "loi": sb["loi"]}

    duong_ma = luu_tru.ghi_ma(ten_lop, ma)
    ra_thu_muc = os.path.join(luu_tru.thu_muc_ket_qua(), ten_lop)
    os.makedirs(ra_thu_muc, exist_ok=True)
    # Dọn kết quả cũ: còn file cũ thì một lượt chạy HỎNG vẫn đọc ra số của lượt trước,
    # và không ai biết mình đang nhìn kết quả của lần nào.
    for f in os.listdir(ra_thu_muc):
        try:
            os.remove(os.path.join(ra_thu_muc, f))
        except OSError:
            pass

    thu_muc_exe = os.path.dirname(sb["launcher"])
    goc_cfg = os.path.join(sb["goc"], "Launcher", "config.json")
    try:
        with open(goc_cfg, encoding="utf-8") as f:
            cfg = json.loads(_got_json(f.read()))
    except (OSError, ValueError) as e:
        return {"ok": False, "loi": f"Không đọc được config.json của LEAN: {e}"}

    cfg.update({
        "algorithm-type-name": ten_lop,
        "algorithm-language": "Python",
        "algorithm-location": duong_ma,
        "data-folder": os.path.join(sb["goc"], "Data"),
        "results-destination-folder": ra_thu_muc,
        "environment": "backtesting",
    })
    with open(os.path.join(thu_muc_exe, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    moi_truong, _dll = _moi_truong()
    try:
        r = subprocess.run([sb["launcher"]], cwd=thu_muc_exe, env=moi_truong,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=HAN_GIO)
        man_hinh = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return {"ok": False, "loi": f"LEAN chạy quá {HAN_GIO // 60} phút nên bị dừng. "
                                    f"Thử rút ngắn khoảng ngày hoặc đổi nhịp thưa hơn."}
    except OSError as e:
        return {"ok": False, "loi": f"Không chạy được LEAN: {e}"}

    d, nk = _doc_ket_qua(ra_thu_muc, ten_lop)
    if d is None:
        # Không có file kết quả mới là hỏng thật. Lúc ấy màn hình mới đáng đọc.
        return {"ok": False, "loi": "LEAN chạy xong mà không ghi ra kết quả.",
                "nhat_ky": man_hinh[-20000:]}
    return {"ok": True, "loi": "", "ten_lop": ten_lop, "thu_muc": ra_thu_muc,
            **_gon(d, nk or man_hinh)}
