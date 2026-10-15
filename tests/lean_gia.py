"""LEAN GIẢ — đóng vai `AlgorithmImports` để chạy CHÍNH lớp vỏ `lean/vo_may.py` ngoài QC.  (D-10, 4a)

Cố ý KHÔNG import gì của repo: bài kiểm chép file này thành `AlgorithmImports.py` trong một thư
mục sạch cạnh bộ file đã đóng gói, rồi chạy trong một Python đã gỡ repo khỏi đường dẫn — y như
QC chạy `main.py`. Nhờ vậy cái được kiểm là ĐÚNG bộ file sẽ gửi lên QC, không phải mã trong repo.

GIẢ ĐỊNH VỀ LEAN, NÓI RÕ RA (đối chiếu tài liệu LEAN; tên API đối chiếu `quantconnect-stubs`):

  · Nến phút: `Slice.time` = giờ ĐÓNG nến. QuoteBar có bid/ask; open/high/low/close của nó là
    giá GIỮA. Cổ phiếu, crypto: TradeBar có khối lượng.
  · Lệnh thị trường đặt trong `on_data` khớp NGAY, ĐỒNG BỘ — `on_order_event` chạy TRƯỚC khi
    `market_order` trả vé (đây là chỗ lớp vỏ phải tra id qua nhãn `tag`). Mua ở giá ask đóng
    cửa, bán ở giá bid (TradeBar: giá đóng).
  · Lệnh giới hạn / chờ stop khớp ở nến SAU khi giá chạm: giới hạn mua khi đáy ≤ giá chờ, ở giá
    chờ hoặc giá mở nếu mở đã tốt hơn; chờ stop mua khi đỉnh ≥ giá chờ, ở giá chờ hoặc giá mở
    nếu mở đã vượt (bán ngược lại).
  · Đang khởi động (`is_warming_up`) thì CẤM đặt lệnh — LEAN trả vé hỏng; ở đây nổ luôn để bài
    kiểm bắt được.
  · Không phí, không trượt giá, một loại tiền (tỉ giá 1).
"""
import datetime as _dt
import itertools as _it

#: `from AlgorithmImports import *` trong lớp vỏ chỉ được thấy đúng những tên LEAN có thật —
#: không để hàm phụ của file này (`chay`, `chay_bo_file`) lọt vào không gian tên của nó.
__all__ = ["Resolution", "Market", "TimeZones", "BrokerageName", "AccountType", "OrderStatus",
           "Symbol", "QuoteBar", "Slice", "QCAlgorithm"]

_GOC = _dt.datetime(1970, 1, 1)


class Resolution:
    MINUTE = "minute"


class Market:
    OANDA, USA, COINBASE = "oanda", "usa", "coinbase"


class TimeZones:
    UTC = "UTC"


class BrokerageName:
    OANDA_BROKERAGE, COINBASE, DEFAULT = "oanda", "coinbase", "default"


class AccountType:
    MARGIN, CASH = "margin", "cash"


class OrderStatus:
    NEW, SUBMITTED, PARTIALLY_FILLED, FILLED = "new", "submitted", "partially_filled", "filled"
    CANCELED, INVALID, NONE = "canceled", "invalid", "none"


#: Lô và bước giá theo loại thị trường — gần với số thật của QC.
LO = {"forex": (1.0, 0.00001), "cfd": (1.0, 0.01), "co_phieu": (1.0, 0.01),
      "crypto": (0.00000001, 0.01)}


class Symbol:
    def __init__(self, value):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, o):
        return isinstance(o, Symbol) and o.value == self.value

    def __repr__(self):
        return self.value


class _Obj:
    def __init__(self, **k):
        self.__dict__.update(k)


class Bar:
    def __init__(self, o, h, l, c, v=0.0):
        self.open, self.high, self.low, self.close, self.volume = o, h, l, c, v


class QuoteBar(Bar):
    def __init__(self, o, h, l, c, spread):
        super().__init__(o, h, l, c)
        nua = spread / 2.0
        self.bid = Bar(o - nua, h - nua, l - nua, c - nua)
        self.ask = Bar(o + nua, h + nua, l + nua, c + nua)


class _Bang(dict):
    def contains_key(self, k):
        return k in self


class Slice:
    def __init__(self, time, quote_bars, bars):
        self.time, self.quote_bars, self.bars = time, _Bang(quote_bars), _Bang(bars)


class Security:
    def __init__(self, sym, loai):
        lot, buoc = LO[loai]
        self.symbol, self.loai = sym, loai
        self.price = 0.0
        self.bid = self.ask = 0.0
        self.symbol_properties = _Obj(lot_size=lot, minimum_order_size=None,
                                      minimum_price_variation=buoc, contract_multiplier=1.0)
        self.quote_currency = _Obj(conversion_rate=1.0)


class Holding:
    def __init__(self, sec):
        self.sec, self.quantity, self.average_price = sec, 0.0, 0.0

    @property
    def holdings_value(self):
        return self.quantity * self.sec.price


class Portfolio:
    def __init__(self, algo):
        self.algo, self.cash, self._h = algo, 0.0, {}

    def __getitem__(self, sym):
        if sym not in self._h:
            self._h[sym] = Holding(self.algo.securities[sym])
        return self._h[sym]

    @property
    def total_portfolio_value(self):
        return self.cash + sum(h.holdings_value for h in self._h.values())


class Order:
    def __init__(self, oid, sym, sl, kieu, gia, tag):
        self.id, self.symbol, self.quantity, self.type = oid, sym, sl, kieu
        self.price, self.tag, self.status, self.filled = gia, tag, OrderStatus.SUBMITTED, 0.0


class OrderTicket:
    def __init__(self, algo, order):
        self._algo, self._o = algo, order
        self.order_id, self.symbol, self.tag = order.id, order.symbol, order.tag

    @property
    def status(self):
        return self._o.status

    @property
    def quantity(self):
        return self._o.quantity

    @property
    def quantity_filled(self):
        return self._o.filled

    @property
    def quantity_remaining(self):
        return self._o.quantity - self._o.filled

    def cancel(self):
        if self._o.status in (OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED):
            self._o.status = OrderStatus.CANCELED
            self._algo.huy.append(self._o.tag)
            self._algo.on_order_event(_Obj(order_id=self._o.id, status=OrderStatus.CANCELED,
                                           fill_quantity=0.0, fill_price=0.0, order_fee=None,
                                           message=""))


class Transactions:
    def __init__(self):
        self.lenh = {}

    def get_order_by_id(self, oid):
        return self.lenh[oid]


class ObjectStore:
    def __init__(self):
        self.kho = {}

    def save_bytes(self, k, v):
        self.kho[k] = bytes(v)
        return True

    def save(self, k, v):
        self.kho[k] = v
        return True


class QCAlgorithm:
    def __init__(self):
        self.securities, self.portfolio = {}, Portfolio(self)
        self.transactions, self.object_store = Transactions(), ObjectStore()
        self.nhat = []                 # log + debug
        self.huy = []                  # nhãn các lệnh đã huỷ
        self.time = None
        self.is_warming_up = False
        self._loai = {}
        self._id = _it.count(1)
        self.warm_up = None
        self.cai = {}

    # ---- khai báo ----
    def set_time_zone(self, tz):
        self.cai["tz"] = tz

    def set_start_date(self, d):
        self.cai["tu"] = d

    def set_end_date(self, d):
        self.cai["den"] = d

    def set_cash(self, v):
        self.portfolio.cash = float(v)

    def set_warm_up(self, td):
        self.warm_up = td

    def set_brokerage_model(self, ten, loai=None):
        self.cai["san"] = (ten, loai)

    def set_benchmark(self, sym):
        self.cai["moc"] = sym

    def _them(self, loai, ma, res, market, fill_forward=True):
        assert res == Resolution.MINUTE and fill_forward is False
        sym = Symbol(ma)
        self.securities[sym] = Security(sym, loai)
        self._loai[ma] = loai
        return _Obj(symbol=sym)

    def add_forex(self, ma, res=None, market=None, fill_forward=True, leverage=None):
        assert market == Market.OANDA
        return self._them("forex", ma, res, market, fill_forward)

    def add_cfd(self, ma, res=None, market=None, fill_forward=True, leverage=None):
        assert market == Market.OANDA
        return self._them("cfd", ma, res, market, fill_forward)

    def add_equity(self, ma, res=None, market=None, fill_forward=True, leverage=None):
        assert market == Market.USA
        return self._them("co_phieu", ma, res, market, fill_forward)

    def add_crypto(self, ma, res=None, market=None, fill_forward=True, leverage=None):
        assert market == Market.COINBASE
        return self._them("crypto", ma, res, market, fill_forward)

    def log(self, s):
        self.nhat.append(str(s))

    debug = log

    # ---- lệnh ----
    def _moi(self, sym, sl, kieu, gia, tag):
        assert not self.is_warming_up, "đặt lệnh lúc đang khởi động — LEAN không cho"
        assert sl != 0, "số lượng 0"
        sec = self.securities[sym]
        lot = sec.symbol_properties.lot_size
        assert abs(round(sl / lot) * lot - sl) < 1e-9 * max(1.0, abs(sl)), f"lẻ lô: {sl}"
        o = Order(next(self._id), sym, float(sl), kieu, gia, tag)
        self.transactions.lenh[o.id] = o
        return o

    def market_order(self, sym, sl, asynchronous=False, tag=""):
        o = self._moi(sym, sl, "thi_truong", None, tag)
        sec = self.securities[sym]
        self._khop(o, sec.ask if sl > 0 else sec.bid)        # ĐỒNG BỘ, như LEAN
        return OrderTicket(self, o)

    def limit_order(self, sym, sl, gia, asynchronous=False, tag=""):
        return OrderTicket(self, self._moi(sym, sl, "gioi_han", float(gia), tag))

    def stop_market_order(self, sym, sl, gia, asynchronous=False, tag=""):
        return OrderTicket(self, self._moi(sym, sl, "cho_stop", float(gia), tag))

    def _khop(self, o, px):
        h = self.portfolio[o.symbol]
        sl, cu = o.quantity - o.filled, h.quantity
        moi = cu + sl
        if cu == 0 or (cu > 0) == (sl > 0):
            h.average_price = (cu * h.average_price + sl * px) / moi if moi else 0.0
        elif moi and (moi > 0) != (cu > 0):
            h.average_price = px
        h.quantity = 0.0 if abs(moi) < 1e-12 else moi
        self.portfolio.cash -= sl * px
        o.filled, o.status = o.quantity, OrderStatus.FILLED
        self.on_order_event(_Obj(order_id=o.id, status=OrderStatus.FILLED, fill_quantity=sl,
                                 fill_price=px, order_fee=_Obj(value=_Obj(amount=0.0)),
                                 message=""))

    def _xet_lenh_cho(self, nen):
        for o in list(self.transactions.lenh.values()):
            if o.status != OrderStatus.SUBMITTED or o.type == "thi_truong":
                continue
            b = nen.get(o.symbol)
            if b is None:
                continue
            mua = o.quantity > 0
            px = None
            if o.type == "gioi_han":
                if mua and b.low <= o.price:
                    px = min(b.open, o.price)
                elif not mua and b.high >= o.price:
                    px = max(b.open, o.price)
            else:
                if mua and b.high >= o.price:
                    px = max(b.open, o.price)
                elif not mua and b.low <= o.price:
                    px = min(b.open, o.price)
            if px is not None:
                self._khop(o, px)

    # ---- móc của thuật toán ----
    def initialize(self):
        pass

    def on_data(self, data):
        pass

    def on_order_event(self, e):
        pass

    def on_end_of_algorithm(self):
        pass


def chay(lop, du_lieu):
    """Chạy thuật toán `lop` trên `du_lieu = {mã: [(t_dong, o, h, l, c, v, spread), …]}`.

    Nạp dữ liệu từ (ngày bắt đầu − khởi động) tới hết ngày kết thúc, phút nào có nến thì một
    Slice. Trả thuật toán đã chạy xong (để soi Object Store, log, lệnh)."""
    a = lop()
    a.initialize()
    tu = int((a.cai["tu"] - _GOC).total_seconds())
    den = int((a.cai["den"] - _GOC).total_seconds()) + 86400
    sau = tu - (int(a.warm_up.total_seconds()) if a.warm_up else 0)
    phut = {}
    for ma, ds in du_lieu.items():
        for n in ds:
            if sau < n[0] <= den:
                phut.setdefault(n[0], {})[ma] = n
    theo_ma = {s.value: s for s in a.securities}
    for t in sorted(phut):
        a.time = _GOC + _dt.timedelta(seconds=t)
        a.is_warming_up = t < tu
        quote, trade, moi = {}, {}, {}
        for ma, n in phut[t].items():
            sym = theo_ma[ma]
            sec = a.securities[sym]
            _, o, h, l, c, v = n[:6]
            sp = n[6] if len(n) > 6 else 0.0
            if sec.loai in ("forex", "cfd"):
                b = QuoteBar(o, h, l, c, sp)
                quote[sym] = b
                sec.bid, sec.ask = b.bid.close, b.ask.close
            else:
                b = Bar(o, h, l, c, v)
                trade[sym] = b
                sec.bid = sec.ask = c
            sec.price = c
            moi[sym] = b
        a._xet_lenh_cho(moi)                 # lệnh chờ đặt từ trước khớp với nến này
        a.on_data(Slice(a.time, quote, trade))
    a.on_end_of_algorithm()
    return a


#: Kịch bản chạy trong thư mục SẠCH: gỡ repo khỏi đường dẫn, nạp `main.py` y như QC nạp, chạy
#: lớp thuật toán qua LEAN giả, ghi kết quả ra `ra.json`.
KICH_BAN = r"""
import base64, json, sys
# «Sạch» là không thấy mã trong repo — nhưng .venv NẰM TRONG repo, nên phải chừa
# site-packages của nó lại, không thì con mất numpy.
sys.path[:] = [p for p in sys.path
               if not p.startswith(GOC) or p.startswith(sys.prefix)]
import AlgorithmImports as L
import main
du = {k: [tuple(x) for x in v] for k, v in json.load(open("du_lieu.json")).items()}
a = L.chay(getattr(main, LOP), du)
ra = {"kho": {k: base64.b64encode(v if isinstance(v, bytes) else v.encode()).decode()
              for k, v in a.object_store.kho.items()},
      "nhat": a.nhat, "huy": a.huy,
      "khoi_dong": a.warm_up.total_seconds() if a.warm_up else 0,
      "cai": {k: str(v) for k, v in a.cai.items()},
      "lenh": [{"tag": o.tag, "trang_thai": o.status, "sl": o.quantity, "da_khop": o.filled,
                "kieu": o.type, "gia": o.price} for o in a.transactions.lenh.values()],
      "von": a.portfolio.total_portfolio_value}
json.dump(ra, open("ra.json", "w"))
"""


def chay_bo_file(files, du_lieu, goc_repo, lop="CatStudioMay", timeout=300):
    """Chạy bộ file đã đóng gói trong một Python SẠCH với file này làm `AlgorithmImports`.
    Trả `(dict kết quả, None)` hoặc `(None, stderr)`."""
    import json as _json
    import os as _os
    import shutil as _sh
    import subprocess as _sp
    import sys as _sys
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        for ten, nd in files.items():
            with open(_os.path.join(td, ten), "w", encoding="utf-8") as f:
                f.write(nd)
        _sh.copy(_os.path.abspath(__file__), _os.path.join(td, "AlgorithmImports.py"))
        with open(_os.path.join(td, "du_lieu.json"), "w", encoding="utf-8") as f:
            _json.dump(du_lieu, f)
        with open(_os.path.join(td, "kich_ban.py"), "w", encoding="utf-8") as f:
            f.write(f"GOC = {goc_repo!r}\nLOP = {lop!r}\n" + KICH_BAN)
        env = {k: v for k, v in _os.environ.items() if k != "PYTHONPATH"}
        # Con nói UTF-8 như trên QC. Windows tiếng Việt cho con cp1252, cha lại đọc
        # utf-8 → vết lỗi tiếng Việt làm luồng đọc chết và `stderr` về None.
        env["PYTHONUTF8"] = "1"
        r = _sp.run([_sys.executable, "kich_ban.py"], cwd=td, env=env, capture_output=True,
                    text=True, encoding="utf-8", timeout=timeout)
        if r.returncode:
            return None, r.stderr[-4000:]
        with open(_os.path.join(td, "ra.json"), encoding="utf-8") as f:
            return _json.load(f), None
