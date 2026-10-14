"""CHẠY TRÊN QUANTCONNECT TỪ TRONG APP — một việc nền, giao diện hỏi tiến độ.  (D-03 · D-06)

`ViecQC.bat_dau(...)` soát đầu vào rồi trả NGAY; một luồng nền làm trọn một lượt:

    đóng gói (`goi_qc`) → `qc_api.chay` (project · file · biên dịch · backtest · nhật ký
    về máy) → dựng `KetQuaQC` từ nhật ký → chấm (`game`) → ghi sổ

và ghi tiến độ vào `trang_thai()`. Giao diện hỏi vài lần mỗi giây, Python không đẩy gì
sang.

Không biết giao diện, không biết pywebview — `api.ApiQC` chỉ là lớp vỏ mỏng gọi vào đây,
nên mọi thứ ở đây kiểm được trên máy chủ QC giả (`tests/test_game_qc.py`).
"""
import json
import re
import threading
import time
from datetime import datetime

from . import bo_chay
from . import core
from . import game
from . import goi_qc
from . import luu_tru
from . import qc_api
from . import nhat_ky as nk


# ---------------------------------------------------------------------------
# Một lượt đã chạy xong — dựng lại từ nhật ký
# ---------------------------------------------------------------------------
def doc_nhat_ky(duong, lay_luot=True):
    """`(meta, lệnh, lượt)` của một file nhật ký. `lay_luot=False`: bỏ qua lượt mà KHÔNG
    giải mã — nhật ký một năm cỡ chục MB, mà màn ẩn chỉ cần meta với lệnh."""
    meta, lenh, luot = {}, [], []
    with open(duong, encoding="utf-8") as f:
        for dong in f:
            if not lay_luot and (dong.startswith('{"loai":"luot"')
                                 or dong.startswith('{"loai": "luot"')):
                continue
            d = json.loads(dong)
            loai = d.get("loai")
            if loai == "meta":
                meta = d
            elif loai == "lenh":
                lenh.append(d["lenh"])
            elif lay_luot:
                luot.append(d)
    return meta, lenh, luot


class KetQuaQC:
    """Một lượt chạy trên QC, dựng lại từ nhật ký đã tải về. CHỈ ĐỌC — vai của `KetQua`.

    Không có nến (không mang chuỗi giá của QC về máy — điều khoản dữ liệu): mỗi lượt và
    mỗi lệnh tự mang giờ (`t`, `t_dat`…), đường vốn nằm sẵn trong meta. `nen5 = None` là
    để `nhat_ky.dung_lo` / `dong_chu` dùng thẳng được — chúng đọc giờ trên bản ghi."""

    nen5 = None

    def __init__(self, duong, lay_luot=True):
        self.duong = duong
        self.meta, self.lenh, self.nhat_ky = doc_nhat_ky(duong, lay_luot)
        self.doc = self.meta.get("doc") or {}
        self.thong_ke = self.meta.get("thong_ke") or {}
        #: Điều nhật ký KHÔNG biết mà lượt chạy biết: kiểu chạy, màn, phần chấm, link QC,
        #: sao… `ViecQC` gắn vào sau khi chạy (hoặc lấy từ lịch sử khi mở lại). Gộp vào
        #: `tom_tat`, để mọi đường hỏi kết quả trả về CÙNG một bộ khoá.
        self.them = {}

    def tom_tat(self):
        m = self.meta
        nhip = {tab: st.get("nhip") for tab in core.TABS
                for st in (self.doc.get(tab) or {}).get("steps") or [] if core.is_start_step(st)}
        luot = self.nhat_ky
        return {"ten": self.doc.get("name"), "van_tay": m.get("van_tay"),
                # Giờ lượt đầu / lượt cuối — khoảng THẬT có nến (khoảng đã yêu cầu là tu/den).
                "t_dau": luot[0].get("t") if luot else None,
                "t_cuoi": luot[-1].get("t") if luot else None, "nhip": nhip,
                "symbol": m.get("symbol"), "tu": m.get("tu"), "den": m.get("den"),
                "tf": m.get("tf"), "thong_ke": self.thong_ke,
                "duong_von": m.get("duong_von") or [],
                "gia_dau": m.get("gia_dau"), "gia_cuoi": m.get("gia_cuoi"),
                "mua_giu_pt": m.get("mua_giu_pt"), "dem": m.get("dem") or {},
                "giay_chay": m.get("giay_chay"), "so_luot": len(self.nhat_ky),
                "duong_nhat_ky": self.duong, "do_gon": game.do_gon(self.doc), **self.them}

    def lo(self, tu=0, so=200, chi_co_viec=True):
        return nk.dung_lo(self, int(tu), int(so), bool(chi_co_viec))

    def soi(self, i):
        """Bản soi một lượt cho cửa sổ vẽ (`nhat_ky.ban_soi`)."""
        return nk.ban_soi(self.doc, self.nhat_ky[int(i)])


# ---------------------------------------------------------------------------
# Việc nền
# ---------------------------------------------------------------------------
_RE_SYMBOL = re.compile(r"^[A-Z0-9]{3,20}$")

#: Tỉ trọng từng bước trong thanh tiến độ chung — backtest là phần dài nhất.
_BUOC = (("Đóng gói", 0.00), ("Tìm project", 0.05), ("Tải file lên QC", 0.08),
         ("Biên dịch", 0.12), ("Chạy backtest", 0.20), ("Tải nhật ký về", 0.90))


def _ti_le_chung(viec, ti_le):
    """Một con số 0…1 cho cả lượt, từ tên bước và tiến độ trong bước (nếu có)."""
    for k, (ten, moc) in enumerate(_BUOC):
        if viec.startswith(ten):
            ke = _BUOC[k + 1][1] if k + 1 < len(_BUOC) else 1.0
            return moc + (ke - moc) * (ti_le or 0.0)
    return None


def soat_tu_do(tu_do):
    """Đầu vào chế độ Sáng tạo → `{symbol, tu, den, von}` sạch, hoặc `LoiGame` nói rõ."""
    tu_do = tu_do or {}
    sym = str(tu_do.get("symbol") or "").strip().upper()
    if not _RE_SYMBOL.match(sym):
        raise game.LoiGame("Symbol phải là chữ in hoa / số, 3–20 ký tự, vd. XAUUSD.")
    try:
        tu = datetime.strptime(str(tu_do.get("tu") or ""), "%Y-%m-%d")
        den = datetime.strptime(str(tu_do.get("den") or ""), "%Y-%m-%d")
    except ValueError:
        raise game.LoiGame("Ngày phải dạng YYYY-MM-DD, vd. 2025-10-01.")
    if tu > den:
        raise game.LoiGame("Ngày bắt đầu nằm SAU ngày kết thúc.")
    try:
        von = float(tu_do.get("von") or 10_000)
    except (TypeError, ValueError):
        raise game.LoiGame("Vốn phải là một con số.")
    if not von > 0:
        raise game.LoiGame("Vốn phải lớn hơn 0.")
    return {"symbol": sym, "tu": tu.strftime("%Y-%m-%d"), "den": den.strftime("%Y-%m-%d"),
            "von": von}


class ViecQC:
    """MỘT lượt chạy QC tại một thời điểm, chạy trong luồng nền.

    `tao_qc`: hàm trả một `qc_api.QC` — mặc định đọc khoá lúc BẮT ĐẦU mỗi lượt, nên lưu
    khoá mới trong app là có hiệu lực ngay, không phải mở lại. Bài kiểm thay bằng máy giả."""

    def __init__(self, tao_qc=None, thu_muc_nhat_ky=None,
                 gioi_han=goi_qc.GIOI_HAN_RESEARCHER):
        self._tao_qc = tao_qc or (lambda: qc_api.QC(*qc_api.doc_khoa()))
        self._thu_muc = thu_muc_nhat_ky
        self._gioi_han = gioi_han
        self._khoa = threading.Lock()
        self._tt = {"dang_chay": False, "xong": None, "loi": None}
        self._luong = None
        #: Lượt đang XEM trong cửa sổ (lượt đã thấy gần nhất, hoặc lượt mở từ lịch sử).
        self.ket_qua = None

    def trang_thai(self):
        with self._khoa:
            tt = dict(self._tt)
        if tt.get("dang_chay") and tt.get("bat_dau"):
            tt["giay"] = round(time.time() - tt["bat_dau"], 1)
        return tt

    def cho(self, han=None):
        """Chờ luồng nền xong — cho bài kiểm và công cụ dòng lệnh."""
        if self._luong is not None:
            self._luong.join(han)

    def bat_dau(self, doc, loai, man_id=None, tu_do=None):
        """Soát NGAY những gì soát được tại máy (lỗi trả thẳng về giao diện), rồi chạy nền."""
        with self._khoa:
            if self._tt.get("dang_chay"):
                raise game.LoiGame("Đang có một lượt chạy — chờ nó xong đã.")
        if loai not in game.LOAI:
            raise game.LoiGame(f"Không có kiểu chạy «{loai}».")
        doc = core.normalize_process(doc)
        # Soát sơ đồ NGAY (vài chục ms): thiếu tham số, khung chưa chạy được trên QC… báo
        # liền cho giao diện, chứ không để luồng nền đi một vòng rồi mới nói.
        goi_qc.soat(doc)
        if loai == "tu_do":
            ch, man_id = soat_tu_do(tu_do), None
        else:
            m = game.man(man_id)
            tu, den = game.khoang(man_id, loai)
            ch = {"symbol": m["symbol"], "tu": tu, "den": den, "von": m["von"]}
            if loai == "nop" and game.ve_nop(man_id, game.van_tay(doc)) is None:
                raise game.LoiGame(
                    "Chạy ▶ đầy đủ cỗ máy này trước khi nộp: nộp là chấm cả màn đã thấy "
                    "lẫn màn ẩn. Sửa sơ đồ sau lần ▶ đầy đủ cuối là thành cỗ máy khác.")
        with self._khoa:
            self._tt = {"dang_chay": True, "loai": loai, "man": man_id, "chu": "Đóng gói cỗ máy",
                        "ti_le": None, "ti_le_chung": 0.0, "bat_dau": time.time(),
                        "xong": None, "loi": None}
        self._luong = threading.Thread(target=self._chay, args=(doc, loai, man_id, ch),
                                       daemon=True)
        self._luong.start()

    # ------------------------------------------------------------------ luồng nền
    def _bao(self, viec, ti_le=None):
        with self._khoa:
            self._tt["chu"] = viec
            self._tt["ti_le"] = ti_le
            chung = _ti_le_chung(viec, ti_le)
            if chung is not None:
                self._tt["ti_le_chung"] = max(self._tt.get("ti_le_chung") or 0.0, chung)

    def _chay(self, doc, loai, man_id, ch):
        xong, loi = None, None
        try:
            xong = self._chay_that(doc, loai, man_id, ch)
        except (qc_api.LoiQC, game.LoiGame, bo_chay.LoiChay) as e:
            loi = str(e)
        except Exception as e:  # noqa: BLE001 — lỗi lập trình vẫn phải nói ra, không treo
            loi = f"Lỗi không lường trước ({type(e).__name__}): {e}"
        with self._khoa:
            self._tt.update(dang_chay=False, xong=xong, loi=loi,
                            giay=round(time.time() - self._tt["bat_dau"], 1))
            if xong:
                self._tt["ti_le_chung"] = 1.0

    def _chay_that(self, doc, loai, man_id, ch):
        bat_dau = time.time()
        self._bao("Đóng gói cỗ máy")
        khoa = nk.khoa_qc(doc, qc_api.ma_luot())
        files = goi_qc.dong_goi(doc, {**ch, "khoa": khoa}, self._gioi_han)
        qc = self._tao_qc()
        an = loai == "nop"
        # Tên backtest trên QC: lượt nộp KHÔNG ghi ngày — app giữ màn ẩn (D-06).
        ten_bt = (f"{game.LOAI[loai]} · {ch['symbol']} · màn ẩn" if an
                  else f"{game.LOAI[loai]} · {ch['symbol']} {ch['tu']} → {ch['den']}")
        kq = qc_api.chay(qc, doc, files, ten_bt,
                         self._thu_muc or luu_tru.thu_muc_nhat_ky(), self._bao, khoa=khoa)

        k = KetQuaQC(kq["duong_nhat_ky"], lay_luot=not an)
        c = game.cham(k.meta)
        vt = nk._van_tay(doc)
        gon = game.do_gon(doc)
        # Khoảng ngày / symbol lấy từ CHÍNH yêu cầu của app — không tin vào meta cho việc này.
        tom = {**k.tom_tat(), "symbol": ch["symbol"], "tu": ch["tu"], "den": ch["den"],
               "loai": loai, "man": man_id, "an": an, "cham": c,
               "url": kq["url"], "giay_tong": round(time.time() - bat_dau, 1),
               "sao": None, "lan_nop": None}
        if an:
            # Màn ẩn: chỉ con số tổng — không ngày, không link QC (mở ra là thấy hết), không
            # đường vốn, không lượt, không lệnh. Xem từng nến của màn ẩn là học thuộc đề thi.
            tom.update(tu=None, den=None, url=None, duong_von=[], so_luot=None,
                       t_dau=None, t_cuoi=None, gia_dau=None, gia_cuoi=None)
            ve = game.ve_nop(man_id, vt)
            tom["sao"] = game.sao(ve, c)
            tom["thay"] = ve
            tom["lan_nop"] = game.ghi_nop(man_id, {
                "ten": doc.get("name"), "van_tay": vt, "sao": tom["sao"], "do_gon": gon,
                "thay": {x: ve.get(x) for x in ("lai_pt", "mua_giu_pt", "thang_boss",
                                                "so_dong", "sach")},
                "an": c, "duong_an": kq["duong_nhat_ky"]})
        else:
            if loai == "day_du":
                game.ghi_day_du(man_id, vt, doc.get("name"), c, kq["duong_nhat_ky"])
                tom["sao"] = game.sao(c)        # tối đa ⭐⭐ — ⭐⭐⭐ chỉ có khi nộp
            k.them = {x: tom[x] for x in ("symbol", "tu", "den", "loai", "man", "an", "cham",
                                          "url", "giay_tong", "sao", "lan_nop")}
            self.ket_qua = k
        game.ghi_lan({"loai": loai, "man": man_id, "ten": doc.get("name"), "van_tay": vt,
                      "symbol": ch["symbol"], "tu": None if an else ch["tu"],
                      "den": None if an else ch["den"],
                      "an": an, "sao": tom["sao"], "lai_pt": c["lai_pt"],
                      "mua_giu_pt": c["mua_giu_pt"], "so_lenh": k.thong_ke.get("so_lenh"),
                      "url": None if an else kq["url"], "duong": kq["duong_nhat_ky"]})
        return tom

    # ------------------------------------------------------------------ xem lại
    def mo_lai(self, duong):
        """Mở một lượt cũ từ lịch sử để xem — đọc file nhật ký, không chạy lại gì.

        Lượt màn ẩn thì không mở: xem từng nến của màn ẩn là học thuộc đề thi."""
        for x in game.lich_su():
            if x.get("duong") == duong:
                muc = x
                if x.get("an"):
                    raise game.LoiGame("Lượt nộp chạy trên màn ẩn — chỉ xem được điểm, "
                                       "không xem được từng nến.")
                break
        else:
            raise game.LoiGame("Lượt này không có trong lịch sử.")
        try:
            k = KetQuaQC(duong)
        except OSError:
            raise game.LoiGame("File nhật ký của lượt này không còn trên máy.")
        k.them = {x: muc.get(x) for x in ("symbol", "tu", "den", "loai", "man", "url", "sao")}
        k.them["an"] = False
        k.them["cham"] = game.cham(k.meta)
        self.ket_qua = k
        return k.tom_tat()
