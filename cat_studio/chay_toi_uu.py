"""BỘ CHẠY OPTIMIZE — gọi `QuantConnect.Optimizer.Launcher.exe` của LEAN.

CÙNG KHUÔN VỚI `chay_lean`, cố ý: dựng config cạnh exe, chạy nền trong một luồng,
giao diện hỏi `trang_thai()` nửa giây một lần. Khác đúng ba chỗ, và cả ba đều vì
optimizer là một chương trình KHÁC:

  1. Nó KHÔNG tự chạy backtest. Nó đẻ một tiến trình LEAN cho mỗi lượt, nên config
     phải chỉ cho nó chỗ của launcher backtest — `lean-binaries-location`, và trỏ
     vào file **.dll** chứ không phải .exe (đọc `ConsoleLeanOptimizer.RunLean`).
  2. Kết quả KHÔNG nằm một chỗ. Mỗi lượt một thư mục con mang tên id của nó, và
     file kết quả là `<id>/<id>.json` — đọc thẳng từ `RunLean`.
  3. Vì thế ta đọc được kết quả NGAY TRONG LÚC CHẠY: lượt nào xong thì file của nó
     đã nằm đó. Bảng xếp hạng và plot đầy dần, không phải chờ hết mẻ.

⚠ CÁI BẪY ĐÃ DÍNH Ở `chay_lean` VẪN CÒN Ở ĐÂY. LEAN treo chờ một phím nếu không có
`close-automatically`; bản optimizer gọi cờ ấy là `optimizer-close-automatically` và
nó TỰ TRUYỀN XUỐNG cho từng tiến trình LEAN con (`--close-automatically`). Thiếu nó
là cả mẻ đứng im mà không ai biết vì sao.

KHÔNG TÍNH GÌ Ở ĐÂY. Xếp hạng, lọc ràng buộc, chọn cái tốt nhất — LEAN làm hết. App
chỉ đọc file rồi bày ra (D-11).
"""
import glob
import json
import os
import subprocess
import threading
import time

from . import chay_lean
from . import luu_tru
from . import toi_uu

#: Thẻ tóm tắt ghi cạnh kết quả, để màn Kho đọc được mà không phải mở từng file.
TEN_THE = "_the.json"

_KHOA = threading.Lock()
_TRANG_THAI = {
    "dang_chay": False, "xong": False, "bat_dau": 0.0, "dong_cuoi": "",
    "kq": None, "tien_trinh": None, "da_dung": False, "thu_muc": "",
    "so_luot": 0, "xong_may": 0, "ten_num": (),
}


def _dat(**kw):
    with _KHOA:
        _TRANG_THAI.update(kw)


def thu_muc_goc():
    """Chỗ mọi mẻ Optimize nằm. `luu_tru` quyết, không phải file này."""
    return luu_tru.thu_muc_toi_uu()


def dung():
    """Giết mẻ đang chạy. Optimizer tự giết đám LEAN con khi nó chết."""
    with _KHOA:
        _TRANG_THAI["da_dung"] = True
        p = _TRANG_THAI.get("tien_trinh")
    if p is not None:
        try:
            p.kill()
        except Exception:                               # noqa: BLE001
            pass
    return {"ok": True}


def trang_thai():
    with _KHOA:
        t = dict(_TRANG_THAI)
    t.pop("tien_trinh", None)
    t["giay"] = round(time.time() - t["bat_dau"], 1) if t["bat_dau"] else 0
    # ĐỌC LẠI THƯ MỤC MỖI LẦN HỎI: lượt nào xong là file của nó đã nằm đó, nên bảng
    # xếp hạng đầy dần ngay trong lúc chạy chứ không đợi hết mẻ.
    t["ket_qua"] = doc_luot(t.get("thu_muc") or "", t.get("ten_num") or ())
    t["xong_may"] = len(t["ket_qua"])
    return t


def _exe_optimizer(goc):
    for kieu in ("Release", "Debug"):
        p = os.path.join(goc, "Optimizer.Launcher", "bin", kieu,
                         "QuantConnect.Optimizer.Launcher.exe")
        if os.path.isfile(p):
            return p
    return ""


def san_sang():
    """Có chạy Optimize được không. -> {ok, loi, exe, lean_dll}."""
    sb = chay_lean.san_sang()
    if not sb["ok"]:
        return {"ok": False, "loi": sb["loi"], "exe": "", "lean_dll": ""}
    exe = _exe_optimizer(sb["goc"])
    if not exe:
        return {"ok": False, "exe": "", "lean_dll": "",
                "loi": "Chưa thấy QuantConnect.Optimizer.Launcher.exe — bản LEAN ở "
                       "máy chưa build phần Optimizer."}
    # Optimizer gọi LEAN qua FILE .DLL, không phải .exe.
    dll = os.path.splitext(sb["launcher"])[0] + ".dll"
    if not os.path.isfile(dll):
        return {"ok": False, "exe": exe, "lean_dll": "",
                "loi": f"Chưa thấy {os.path.basename(dll)} — optimizer cần file .dll "
                       f"của launcher backtest để chạy từng lượt."}
    return {"ok": True, "loi": "", "exe": exe, "lean_dll": dll, "goc": sb["goc"]}


def _cau_hinh(cai, ten_lop, duong_ma, ra_thu_muc, sb):
    """Cài đặt của hộp Optimize -> đúng khuôn config LEAN nhận."""
    tham_so = []
    for ten, k in sorted((cai.get("tham_so") or {}).items()):
        tham_so.append({"name": ten, "min": float(k.get("tu", 0)),
                        "max": float(k.get("den", 0)),
                        "step": float(k.get("buoc", 1))})
    rang_buoc = [{"target": toi_uu.duong_chi_tieu(r.get("chi_tieu", "")),
                  "operator": r.get("phep", "greater"),
                  "target-value": float(r.get("gia_tri", 0))}
                 for r in (cai.get("rang_buoc") or []) if r.get("chi_tieu")]
    cach = cai.get("cach_tim") or toi_uu.MAC_DINH["cach_tim"]
    cfg = {
        "algorithm-type-name": ten_lop,
        "algorithm-language": "Python",
        "algorithm-location": duong_ma,
        "data-folder": os.path.join(sb["goc"], "Data"),
        "results-destination-folder": ra_thu_muc,
        "lean-binaries-location": sb["lean_dll"],
        # ⚠ Thiếu dòng này là mọi tiến trình LEAN con đứng chờ một phím. Xem đầu file.
        "optimizer-close-automatically": True,
        "optimization-strategy": cach,
        "optimization-strategy-settings": {
            "$type": "QuantConnect.Optimizer.Strategies."
                     "StepBaseOptimizationStrategySettings, QuantConnect.Optimizer",
            "default-segment-amount": int(cai.get("chia_doan") or 10),
        },
        "optimization-criterion": {
            "target": toi_uu.duong_chi_tieu(cai.get("muc_tieu")
                                            or toi_uu.MAC_DINH["muc_tieu"]),
            "extremum": cai.get("huong") or "max",
        },
        "constraints": rang_buoc,
        "parameters": tham_so,
    }
    if int(cai.get("cung_luc") or 0) > 0:
        cfg["maximum-concurrent-backtests"] = int(cai["cung_luc"])
    return cfg


def doc_luot(thu_muc, ten_num=None):
    """Mọi lượt backtest đã xong trong một mẻ -> [{id, tham_so, chi_tieu}].

    Mỗi lượt một thư mục con mang id của nó, file kết quả là `<id>/<id>.json`.

    ⚠ `ten_num` KHÔNG PHẢI tuỳ chọn cho vui. `algorithmConfiguration.parameters`
    trong file kết quả mang CẢ mấy tham số mặc định của chính LEAN — `ema-fast`,
    `ema-slow`, `intrinio-username`, `intrinio-password` — vì config ta ghi kế thừa
    từ `config.json` gốc của nó. Không lọc thì bảng xếp hạng mọc thêm bốn cột vô
    nghĩa, lẫn vào giữa mấy cột núm thật. ĐÃ DÍNH THẬT, và chỉ lộ ra khi nhìn ảnh
    chụp — vì mã vẫn chạy đúng, bảng vẫn hiện, chỉ là nó bày nhầm.
    Rỗng/None = lấy hết, cho lúc chưa biết mẻ quét những núm nào."""
    loc = set(ten_num or ())
    ra = []
    if not thu_muc or not os.path.isdir(thu_muc):
        return ra
    for d in sorted(os.listdir(thu_muc)):
        f = os.path.join(thu_muc, d, f"{d}.json")
        if not os.path.isfile(f):
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        ac = doc.get("algorithmConfiguration") or {}
        ts = dict(ac.get("parameters") or {})
        ra.append({"id": d,
                   "tham_so": {k: v for k, v in ts.items() if k in loc} if loc else ts,
                   "chi_tieu": dict(doc.get("statistics") or {})})
    return ra


def chay(ma, ten_lop, cai):
    """Chạy một mẻ Optimize. -> {ok, loi, thu_muc, ket_qua}."""
    sb = san_sang()
    if not sb["ok"]:
        return {"ok": False, "loi": sb["loi"]}

    uoc = toi_uu.uoc_luong(cai.get("tham_so") or {}, cai.get("cung_luc") or 0)
    if uoc["thieu"]:
        return {"ok": False,
                "loi": f'Mấy núm này chưa khai nổi một khoảng quét: '
                       f'{", ".join(uoc["thieu"])}.'}
    if not uoc["so_luot"]:
        return {"ok": False, "loi": "Chưa ghim núm nào để quét."}

    duong_ma = luu_tru.ghi_ma(ten_lop, ma)
    ma_luot = time.strftime("%Y%m%d-%H%M%S")
    ra_thu_muc = os.path.join(thu_muc_goc(), ten_lop, ma_luot)
    os.makedirs(ra_thu_muc, exist_ok=True)
    _dat(thu_muc=ra_thu_muc, so_luot=uoc["so_luot"],
         ten_num=tuple(sorted((cai.get("tham_so") or {}))))

    thu_muc_exe = os.path.dirname(sb["exe"])
    cfg = _cau_hinh(cai, ten_lop, duong_ma, ra_thu_muc, sb)
    with open(os.path.join(thu_muc_exe, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    moi_truong, _dll = chay_lean._moi_truong()
    dong = []
    try:
        p = subprocess.Popen([sb["exe"]], cwd=thu_muc_exe, env=moi_truong,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace",
                             bufsize=1)
    except OSError as e:
        return {"ok": False, "loi": f"Không chạy được optimizer: {e}"}
    _dat(tien_trinh=p)
    with _KHOA:
        if _TRANG_THAI["da_dung"]:
            p.kill()

    try:
        for d in p.stdout:
            dong.append(d)
            s = d.strip()
            if s:
                _dat(dong_cuoi=s[-160:])
    finally:
        try:
            p.stdout.close()
            p.wait(timeout=30)
        except Exception:                               # noqa: BLE001
            p.kill()

    with _KHOA:
        da_dung = _TRANG_THAI["da_dung"]
    ket_qua = doc_luot(ra_thu_muc, (cai.get("tham_so") or {}))
    if not ket_qua:
        return {"ok": False, "thu_muc": ra_thu_muc, "ket_qua": [],
                "loi": ("Bạn đã dừng mẻ này." if da_dung else
                        "Optimizer chạy xong mà không lượt nào ghi ra kết quả."),
                "nhat_ky": "".join(dong)[-20000:]}
    kq = {"ok": True, "loi": "", "ten_lop": ten_lop, "thu_muc": ra_thu_muc,
          "ma_luot": ma_luot, "id": f"{ten_lop}/{ma_luot}",
          "cai": cai, "ket_qua": ket_qua,
          "da_dung": da_dung, "so_luot": _TRANG_THAI["so_luot"]}
    _ghi_the(ra_thu_muc, kq)
    return kq


def _ghi_the(thu_muc, kq):
    the = {k: kq.get(k) for k in ("ten_lop", "ma_luot", "id", "cai", "so_luot")}
    the["luc"] = time.time()
    the["so_xong"] = len(kq.get("ket_qua") or [])
    try:
        with open(os.path.join(thu_muc, TEN_THE), "w", encoding="utf-8") as f:
            json.dump(the, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def ds_me():
    """Mọi mẻ Optimize đã lưu, MỚI NHẤT TRƯỚC."""
    ra = []
    for f in glob.glob(os.path.join(thu_muc_goc(), "*", "*", TEN_THE)):
        try:
            with open(f, encoding="utf-8") as fh:
                ra.append(json.load(fh))
        except (OSError, ValueError):
            continue
    return sorted(ra, key=lambda t: t.get("luc") or 0, reverse=True)


def doc_me(ma_id):
    """Một mẻ đã lưu -> {ok, ...} cho cửa sổ Optimize mở lại."""
    ten_lop, _, ma_luot = str(ma_id or "").partition("/")
    d = os.path.join(thu_muc_goc(), ten_lop, ma_luot)
    if not ten_lop or not ma_luot or not os.path.isdir(d):
        return {"ok": False, "loi": "Không có mẻ này."}
    the = {}
    try:
        with open(os.path.join(d, TEN_THE), encoding="utf-8") as fh:
            the = json.load(fh)
    except (OSError, ValueError):
        pass
    return {"ok": True, "loi": "", "thu_muc": d, **the,
            "ket_qua": doc_luot(d, ((the.get("cai") or {}).get("tham_so") or {}))}


def bat_dau_chay(ma, ten_lop, cai):
    """Khởi động một mẻ trong luồng riêng rồi trả về NGAY. Xem `chay_lean`."""
    with _KHOA:
        if _TRANG_THAI["dang_chay"]:
            return {"ok": False, "loi": "Đang có một mẻ chạy rồi — chờ nó xong đã."}
        _TRANG_THAI.update({"dang_chay": True, "xong": False, "bat_dau": time.time(),
                            "dong_cuoi": "", "kq": None, "tien_trinh": None,
                            "da_dung": False, "thu_muc": "", "so_luot": 0,
                            "ten_num": ()})

    def chay_nen():
        try:
            kq = chay(ma, ten_lop, cai)
        except Exception as e:                          # noqa: BLE001
            kq = {"ok": False, "loi": f"{type(e).__name__}: {e}"}
        _dat(dang_chay=False, xong=True, kq=kq)

    threading.Thread(target=chay_nen, daemon=True).start()
    return {"ok": True, "loi": ""}
