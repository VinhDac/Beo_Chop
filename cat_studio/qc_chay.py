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

from . import bo_may
from . import game
from . import goi_qc
from . import luu_tru
from . import may as M
from . import qc_api
from .ket_qua_may import KetQuaMay


# ---------------------------------------------------------------------------
# Một lượt đã chạy xong — dựng lại từ nhật ký
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


#: Loại thị trường của cỗ máy 5 trạm (D-10) — đúng những loại lớp vỏ QC biết đăng ký.
LOAI_THI_TRUONG = {"forex": "Ngoại hối (OANDA)", "cfd": "CFD (OANDA)",
                   "co_phieu": "Cổ phiếu Mỹ", "crypto": "Crypto (Coinbase)"}
#: Một rổ quá to là một lượt QC chạy cả giờ — trần cho chế độ Sáng tạo.
TRAN_SO_MA = 20


def soat_tu_do_may(tu_do):
    """Đầu vào Sáng tạo cho CỖ MÁY 5 TRẠM → `{ma: [...], loai, tu, den, von}` sạch, hoặc
    `LoiGame` nói rõ. Khác `soat_tu_do` (một symbol): cỗ máy chạy trên cả một RỔ mã."""
    tu_do = tu_do or {}
    ma, thay = [], set()
    for x in tu_do.get("ma") or []:
        x = str(x or "").strip().upper()
        if x and x not in thay:
            if not _RE_SYMBOL.match(x):
                raise game.LoiGame(f"Mã «{x}» không hợp lệ: chữ in hoa / số, 3–20 ký tự.")
            thay.add(x)
            ma.append(x)
    if not ma:
        raise game.LoiGame("Rổ chưa có mã nào — thêm ít nhất một mã, vd. EURUSD.")
    if len(ma) > TRAN_SO_MA:
        raise game.LoiGame(f"Rổ tối đa {TRAN_SO_MA} mã — {len(ma)} mã là một lượt chạy cả giờ.")
    loai = tu_do.get("loai") or "forex"
    if loai not in LOAI_THI_TRUONG:
        raise game.LoiGame(f"Không có loại thị trường «{loai}».")
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
    return {"ma": ma, "loai": loai, "tu": tu.strftime("%Y-%m-%d"),
            "den": den.strftime("%Y-%m-%d"), "von": von}


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
        if not M.la_may(doc):
            raise game.LoiGame("Tài liệu này không phải cỗ máy 5 trạm.")
        return self._bat_dau_may(doc, loai, man_id, tu_do)

    def _bat_dau_may(self, may, loai, man_id, tu_do):
        """Cỗ máy 5 trạm (D-10): Sáng tạo chạy rổ tự chọn, Chiến dịch chạy rổ CỦA MÀN.

        Soát NGAY tại máy những gì soát được — cỗ máy còn lỗi, màn của dạng tài liệu kia,
        nộp mà chưa có vé — rồi mới đóng gói. Đi một vòng lên QC mới biết sai là mất vài
        phút cho một câu đáng lẽ nói ngay được."""
        loi = [p for p in M.soat(may) if p["severity"] == "error"]
        if loi:
            raise game.LoiGame(f"Cỗ máy còn {len(loi)} lỗi, chưa chạy được: {loi[0]['message']}")
        if loai == "tu_do":
            ch, man_id = soat_tu_do_may(tu_do), None
        else:
            m = game.man(man_id)
            if m.get("dang") != M.DANG:
                raise game.LoiGame(f"Màn «{m['ten']}» là màn của sơ đồ cũ, không chạy được "
                                   f"bằng cỗ máy 5 trạm.")
            tu, den = game.khoang(man_id, loai)
            ch = {"ma": game.ro_cua(m), "loai": m["loai"], "tu": tu, "den": den,
                  "von": m["von"]}
            if loai == "nop" and game.ve_nop(man_id, M.van_tay(may)) is None:
                raise game.LoiGame(
                    "Chạy ▶ đầy đủ cỗ máy này trước khi nộp: nộp là chấm cả màn đã thấy "
                    "lẫn màn ẩn. Sửa cỗ máy sau lần ▶ đầy đủ cuối là thành cỗ máy khác.")
        may = M.chuan_hoa(may)
        with self._khoa:
            self._tt = {"dang_chay": True, "loai": loai, "man": man_id,
                        "chu": "Đóng gói cỗ máy", "ti_le": None, "ti_le_chung": 0.0,
                        "bat_dau": time.time(), "xong": None, "loi": None}
        self._luong = threading.Thread(target=self._chay, args=(may, loai, man_id, ch),
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
            xong = self._chay_may(doc, loai, man_id, ch)
        except (qc_api.LoiQC, game.LoiGame, bo_may.LoiMay) as e:
            loi = str(e)
        except Exception as e:  # noqa: BLE001 — lỗi lập trình vẫn phải nói ra, không treo
            loi = f"Lỗi không lường trước ({type(e).__name__}): {e}"
        with self._khoa:
            self._tt.update(dang_chay=False, xong=xong, loi=loi,
                            giay=round(time.time() - self._tt["bat_dau"], 1))
            if xong:
                self._tt["ti_le_chung"] = 1.0

    def _chay_may(self, may, loai, man_id, ch):
        """Một lượt cỗ máy 5 trạm trên QC: đóng gói → chạy → tải nhật ký → đọc → CHẤM.

        Chấm bằng chính `game.cham` của sơ đồ cũ — một định nghĩa "điểm" duy nhất cho cả
        hai dạng. Lượt NỘP chạy trên màn ẩn: chỉ con số tổng về tới giao diện."""
        bat_dau = time.time()
        self._bao("Đóng gói cỗ máy")
        vt = M.van_tay(may)
        khoa = f"cat_studio/may-{vt}-{qc_api.ma_luot()}.jsonl.gz"
        files = goi_qc.dong_goi_may(may, {**ch, "khoa": khoa}, self._gioi_han)
        an = loai == "nop"
        # Tên backtest trên QC: lượt nộp KHÔNG ghi ngày — app giữ màn ẩn (D-06).
        ten_bt = (f"{game.LOAI[loai]} · {len(ch['ma'])} mã {LOAI_THI_TRUONG[ch['loai']]} · "
                  + ("màn ẩn" if an else f"{ch['tu']} → {ch['den']}"))
        kq = qc_api.chay(self._tao_qc(), may, files, ten_bt,
                         self._thu_muc or luu_tru.thu_muc_nhat_ky(), self._bao, khoa=khoa)
        k = KetQuaMay(kq["duong_nhat_ky"], lay_luot=not an)
        c = game.cham(k.meta)
        gon = game.do_gon(may)
        tom = {**k.tom_tat(), "loai": loai, "man": man_id, "an": an, "cham": c,
               "url": kq["url"], "giay_tong": round(time.time() - bat_dau, 1),
               "sao": None, "lan_nop": None}
        if an:
            # Màn ẩn: chỉ con số tổng — không ngày, không link QC (mở ra là thấy hết),
            # không đường vốn, không lượt. Xem từng nến của màn ẩn là học thuộc đề thi.
            tom.update(tu=None, den=None, url=None, duong_von=[], so_luot=None,
                       t_dau=None, t_cuoi=None, gia_dau={}, gia_cuoi={})
            ve = game.ve_nop(man_id, vt)
            tom["sao"] = game.sao(ve, c)
            tom["thay"] = ve
            tom["lan_nop"] = game.ghi_nop(man_id, {
                "dang": M.DANG, "ten": may.get("name"), "van_tay": vt, "sao": tom["sao"],
                "do_gon": gon,
                "thay": {x: ve.get(x) for x in ("lai_pt", "mua_giu_pt", "thang_boss",
                                                "so_dong", "sach")},
                "an": c, "duong_an": kq["duong_nhat_ky"]})
        else:
            if loai == "day_du":
                game.ghi_day_du(man_id, vt, may.get("name"), c, kq["duong_nhat_ky"])
                tom["sao"] = game.sao(c)        # tối đa ⭐⭐ — ⭐⭐⭐ chỉ có khi nộp
            k.them = {x: tom[x] for x in ("loai", "man", "an", "cham", "url", "giay_tong",
                                          "sao", "lan_nop")}
            self.ket_qua = k
        tk = k.thong_ke
        game.ghi_lan({"dang": M.DANG, "loai": loai, "man": man_id, "ten": may.get("name"),
                      "van_tay": vt, "symbol": ", ".join(ch["ma"]),
                      "tu": None if an else ch["tu"], "den": None if an else ch["den"],
                      "an": an, "sao": tom["sao"], "lai_pt": c["lai_pt"],
                      "mua_giu_pt": c["mua_giu_pt"], "so_lenh": tk.get("so_lenh"),
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
        la_may = muc.get("dang") == M.DANG
        try:
            k = KetQuaMay(duong) if la_may else KetQuaQC(duong)
        except OSError:
            raise game.LoiGame("File nhật ký của lượt này không còn trên máy.")
        except ValueError:
            raise game.LoiGame("File nhật ký của lượt này không phải của cỗ máy 5 trạm.")
        if la_may:
            k.them = {"loai": muc.get("loai"), "man": None, "an": False, "url": muc.get("url"),
                      "sao": None, "lan_nop": None}
        else:
            k.them = {x: muc.get(x) for x in ("symbol", "tu", "den", "loai", "man", "url", "sao")}
            k.them["an"] = False
            k.them["cham"] = game.cham(k.meta)
        self.ket_qua = k
        return k.tom_tat()
