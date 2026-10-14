# region imports
from AlgorithmImports import *
# endregion
"""LỚP VỎ QuantConnect cho CỖ MÁY 5 TRẠM.  (D-10, phần 4)

KHÔNG CHỨA LUẬT NÀO — luật nằm ở `cat_studio.bo_may`, đúng bộ máy chạy trong bài kiểm. Năm việc:

  1. Đăng ký mã của màn (ngoại hối / CFD qua OANDA, cổ phiếu Mỹ, crypto Coinbase), độ phân giải
     PHÚT, KHÔNG lấp nến (phút nào sàn không có giá thì không có nến, như dữ liệu sàn thật).
  2. Khởi động (`set_warm_up`) đủ lâu cho chỉ báo dài nhất của cỗ máy, theo lịch của thị
     trường (`bo_may.giay_lich_khoi_dong`).
  3. Mỗi phút: gom nến M1 mọi mã (QuoteBar thì lấy giá GIỮA, spread = ask − bid), dựng tài khoản
     từ `portfolio` → `BoMay.buoc` → ý định → lệnh QC. Số lượng do lớp vỏ đổi từ "% vốn" theo
     giá, hệ số hợp đồng, tỉ giá và LÔ của từng mã; khớp, phí, ký quỹ là việc của QC.
  4. QC báo khớp / từ chối → `BoMay.nhan_khop` / `nhan_tu_choi`.
  5. Hết dữ liệu → nhật ký nén vào Object Store dưới khoá app đặt cho RIÊNG lượt này.

Không dán file này lên QC: `cat_studio/goi_qc.dong_goi_may` nhúng nó cùng bộ máy và cỗ máy
vào `main.py`, đặt `CAU_HINH` và `MAY` bên dưới.

Tên API đã đối chiếu với `quantconnect-stubs` (bản 18179): `add_forex/add_cfd/add_equity/
add_crypto`, `market_order/limit_order/stop_market_order(…, tag=…)`, `OrderTicket.cancel /
quantity_remaining`, `transactions.get_order_by_id(…).tag`, `OrderEvent.fill_quantity /
fill_price / order_fee.value.amount`, `SymbolProperties.lot_size / minimum_order_size /
minimum_price_variation / contract_multiplier`, `quote_currency.conversion_rate`.
"""
import base64
import builtins
import gzip
import json
import math
from datetime import datetime, timedelta
# ⚠ `from AlgorithmImports import *` chiếm tên `time` (nó là `datetime.time`).
import time as dong_ho

from cat_studio import bo_may as B
from cat_studio import may as M

#: `main.py` đặt lại hai biến này ngay sau khi nạp module.
CAU_HINH: dict = {"ma": ["EURUSD"], "loai": "forex", "tu": "2024-01-01", "den": "2024-03-31",
                  "von": 10000.0}
MAY: dict | None = None

_GOC_GIO = datetime(1970, 1, 1)


def _giay(dt):
    """Giờ LEAN (datetime không múi giờ, thuật toán đặt UTC) → số giây UTC."""
    return int(round((dt - _GOC_GIO).total_seconds()))


def _them_ma(algo, loai, ma):
    """Đăng ký một mã theo loại thị trường của màn. Trả `Symbol`."""
    if loai == "forex":
        s = algo.add_forex(ma, Resolution.MINUTE, Market.OANDA, fill_forward=False)
    elif loai == "cfd":
        s = algo.add_cfd(ma, Resolution.MINUTE, Market.OANDA, fill_forward=False)
    elif loai == "co_phieu":
        s = algo.add_equity(ma, Resolution.MINUTE, Market.USA, fill_forward=False)
    elif loai == "crypto":
        s = algo.add_crypto(ma, Resolution.MINUTE, Market.COINBASE, fill_forward=False)
    else:
        raise ValueError(f"Loại thị trường «{loai}» chưa nối sang QuantConnect.")
    return s.symbol


class CatStudioMay(QCAlgorithm):

    def initialize(self):
        self._bat_dau = dong_ho.perf_counter()
        if not MAY:
            raise ValueError("Thiếu cỗ máy — hãy chạy bộ file do Cat Studio đóng gói, không "
                             "dán vo_may.py.")
        ch = self._ch = CAU_HINH
        self.set_time_zone(TimeZones.UTC)
        tu = datetime.strptime(ch["tu"], "%Y-%m-%d")
        self.set_start_date(tu)
        self.set_end_date(datetime.strptime(ch["den"], "%Y-%m-%d"))
        self.set_cash(float(ch["von"]))
        loai = ch["loai"]
        if loai in ("forex", "cfd"):
            self.set_brokerage_model(BrokerageName.OANDA_BROKERAGE, AccountType.MARGIN)
        elif loai == "crypto":
            self.set_brokerage_model(BrokerageName.COINBASE, AccountType.CASH)
        self._ma = {ma: _them_ma(self, loai, ma) for ma in ch["ma"]}
        self._ten = {sym: ma for ma, sym in self._ma.items()}
        # Mốc so sánh của QC: mã đầu tiên của màn — để QC không tự kéo thêm SPY vào.
        self.set_benchmark(self._ma[ch["ma"][0]])
        giay = B.giay_lich_khoi_dong(MAY, loai)
        if giay:
            self.set_warm_up(timedelta(seconds=giay))
        self._bm = B.BoMay(MAY, list(ch["ma"]), float(ch["von"]), _giay(tu))
        self._ve = {}                  # id lệnh của bộ máy → OrderTicket
        self._bo_qua = 0               # ý định không thành lệnh (số lượng làm tròn về 0)

    # ------------------------------------------------------------------ mỗi phút
    def on_data(self, data):
        nen = {}
        for ma, sym in self._ma.items():
            q = data.quote_bars[sym] if data.quote_bars.contains_key(sym) else None
            b = data.bars[sym] if data.bars.contains_key(sym) else None
            sp = None
            if q is not None and q.bid is not None and q.ask is not None:
                sp = float(q.ask.close) - float(q.bid.close)
            if b is not None:
                nen[ma] = (float(b.open), float(b.high), float(b.low), float(b.close),
                           float(b.volume), sp)
            elif q is not None:
                # QuoteBar: open/high/low/close là giá GIỮA bid–ask (cách LEAN định nghĩa).
                nen[ma] = (float(q.open), float(q.high), float(q.low), float(q.close), 0.0, sp)
        if not nen:
            return
        for y in self._bm.buoc(_giay(self.time), nen, self._tai_khoan()):
            if y["loai"] == "huy":
                tk = self._ve.get(y["id"])
                if tk is not None:
                    tk.cancel()
            elif not self.is_warming_up:
                self._dat(y)

    def _tai_khoan(self):
        """Tài khoản theo đúng hình dạng `BoMay._nhan_tk` cần — nguồn sự thật là QC."""
        p = self.portfolio
        von = float(p.total_portfolio_value)
        giu = {}
        for ma, sym in self._ma.items():
            h = p[sym]
            if h.quantity:
                giu[ma] = {"pt": float(h.holdings_value) / von * 100.0 if von else 0.0,
                           "gia_von": float(h.average_price), "sl": float(h.quantity)}
        cho = {}
        for lid in list(self._ve):
            tk = self._ve[lid]
            if tk.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                del self._ve[lid]
                continue
            sec = self.securities[tk.symbol]
            con = float(tk.quantity_remaining) * float(sec.price) \
                * float(sec.symbol_properties.contract_multiplier) \
                * float(sec.quote_currency.conversion_rate)
            cho[lid] = {"ma": self._ten[tk.symbol], "pt": con / von * 100.0 if von else 0.0}
        return {"von": von, "tien_mat": float(p.cash), "giu": giu, "lenh_cho": cho}

    def _so_luong(self, sec, pt):
        """% vốn → số lượng, làm tròn VỀ PHÍA 0 theo lô của mã (không bao giờ mua lố)."""
        gia = float(sec.price)
        sp = sec.symbol_properties
        mot = gia * float(sp.contract_multiplier) * float(sec.quote_currency.conversion_rate)
        if mot <= 0:
            return 0.0
        sl = pt / 100.0 * float(self.portfolio.total_portfolio_value) / mot
        lot = float(sp.lot_size) or 1.0
        n = math.floor(abs(sl) / lot + 1e-9) * lot
        if sp.minimum_order_size is not None and n < float(sp.minimum_order_size):
            return 0.0
        return math.copysign(round(n, 10), sl) if n else 0.0

    @staticmethod
    def _gia_lam_tron(sec, gia):
        buoc = float(sec.symbol_properties.minimum_price_variation or 0.0)
        return round(round(gia / buoc) * buoc, 10) if buoc > 0 else gia

    def _dat(self, y):
        sym = self._ma[y["ma"]]
        sec = self.securities[sym]
        sl = self._so_luong(sec, y["pt"])
        if not sl:
            self._bo_qua += 1
            self._bm.nhan_tu_choi(y["id"], "số lượng làm tròn theo lô của mã ra 0")
            return
        if y["kieu"] == "thi_truong":
            tk = self.market_order(sym, sl, tag=y["id"])
        elif y["kieu"] == "gioi_han":
            tk = self.limit_order(sym, sl, self._gia_lam_tron(sec, y["gia"]), tag=y["id"])
        else:
            tk = self.stop_market_order(sym, sl, self._gia_lam_tron(sec, y["gia"]), tag=y["id"])
        if tk.status != OrderStatus.INVALID:
            self._ve[y["id"]] = tk

    def on_order_event(self, e):
        # Lệnh thị trường khớp NGAY trong lúc `market_order` còn chạy — trước khi kịp cất vé.
        # Nên tra id của bộ máy qua NHÃN (tag) của lệnh, không qua bảng vé.
        lid = self.transactions.get_order_by_id(e.order_id).tag
        if e.status == OrderStatus.INVALID:
            self._bm.nhan_tu_choi(lid, f"QuantConnect từ chối: {e.message}")
        elif e.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED) and e.fill_quantity:
            phi = 0.0
            if e.order_fee is not None and e.order_fee.value is not None:
                phi = float(e.order_fee.value.amount)
            self._bm.nhan_khop(lid, _giay(self.time), float(e.fill_quantity),
                               float(e.fill_price), phi)

    # ------------------------------------------------------------------ kết thúc
    def on_end_of_algorithm(self):
        giay = dong_ho.perf_counter() - self._bat_dau
        bm, ch = self._bm, self._ch
        tk = bm.thong_ke()
        meta = {"loai": "meta", "dang": M.DANG, "nguon": "quantconnect",
                "van_tay": M.van_tay(bm.may), "may": bm.may,
                "cau_hinh": {k: ch[k] for k in ("ma", "loai", "tu", "den", "von") if k in ch},
                "thong_ke": tk, "duong_von": bm.duong_von, "gia_dau": bm.gia_dau,
                "gia_cuoi": dict(bm.gia), "giay_chay": round(giay, 1),
                "bo_qua": self._bo_qua, "khoi_dong_giay": B.giay_lich_khoi_dong(MAY, ch["loai"])}
        dong = [json.dumps(meta, ensure_ascii=False)]
        dong += [json.dumps({"loai": "lenh", "lenh": l}, ensure_ascii=False)
                 for l in bm.lenh.values()]
        dong += [json.dumps({"loai": "luot", **r}, ensure_ascii=False) for r in bm.nhat_ky]
        gz = gzip.compress(("\n".join(dong) + "\n").encode("utf-8"))
        luu, loi = self._cat(ch.get("khoa") or f"cat_studio/may-{meta['van_tay']}.jsonl.gz", gz)
        for d in (f"CAT STUDIO · cỗ máy «{bm.may.get('name')}» · {len(ch['ma'])} mã · "
                  f"{ch['tu']} → {ch['den']}",
                  f"CAT STUDIO · lãi {tk['lai_pt']:+.2f}% · boss "
                  + (f"{tk['boss_pt']:+.2f}%" if tk["boss_pt"] is not None else "—")
                  + f" · {tk['so_lenh']} lệnh ({tk['so_lenh_khop']} khớp) · sụt tối đa "
                  f"{tk['sut_giam_max_pt']:.2f}%",
                  f"CAT STUDIO · {len(bm.nhat_ky)} dòng nhật ký · {giay:.0f} giây · lưu: {luu}"):
            self.log(d)
            self.debug(d)
        if loi:
            self.log("CAT STUDIO · lỗi Object Store đầy đủ: " + loi)
            self.debug("CAT STUDIO · lỗi Object Store đầy đủ: " + loi)

    def _cat(self, khoa, du_lieu):
        """Cất nhật ký nén. Trả `(câu ngắn cho dòng tổng kết, lỗi đầy đủ hoặc "")`."""
        mb = f"{len(du_lieu) / 1e6:.2f}".replace(".", ",") + " MB"
        # ⚠ `builtins.Exception`: `from System import *` trong AlgorithmImports có thể để
        #   `Exception` trỏ sang System.Exception của .NET, và khi đó lỗi Python lọt qua.
        try:
            if self.object_store.save_bytes(khoa, du_lieu):
                return f"được ({mb} · {khoa})", ""
            loi = "save_bytes trả về False"
        except builtins.Exception as e:
            loi = f"{type(e).__name__}: {e}"
        try:
            if self.object_store.save(khoa + ".b64",
                                      base64.b64encode(du_lieu).decode("ascii")):
                return f"được, dạng chữ ({mb} · {khoa}.b64)", loi
            loi += " | base64: save trả về False"
        except builtins.Exception as e:
            loi += f" | base64: {type(e).__name__}: {e}"
        return "KHÔNG", loi
