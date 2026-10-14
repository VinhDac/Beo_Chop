# region imports
from AlgorithmImports import *
# endregion
"""LỚP VỎ QuantConnect cho cầu nối Cat Studio.  (slice 2a · DECISIONS.md D-01…D-04)

KHÔNG CHỨA LUẬT NÀO. Ba việc:

  1. Dựng nến cho mỗi khung sơ đồ cần (`QuoteBarConsolidator`) và một chỉ báo LEAN cho
     mỗi khoá chỉ báo mà `ChuongTrinhQC` ghi danh.
  2. Mỗi nến khung đóng → cập nhật chỉ báo → đẩy vào `PhienQC.nhan_khung`.
     Mỗi nến M1 → `PhienQC.mot_nhip` với giá Bid và spread THẬT của nến đó.
  3. Hết dữ liệu → chốt sổ, nén nhật ký, cất vào Object Store, in vài dòng tổng kết.

Không dán file này lên QC. Dán bộ file do `tools/dong_goi_lean.py` sinh ra — nó nhúng
module này cùng bộ luật và cầu nối, đặt `CAU_HINH` và `SO_DO` bên dưới, rồi khai trong
`main.py` một lớp con rỗng của `CatStudioTrenQC` để QC nhận ra thuật toán. File này để
riêng là để soát được tên lệnh bằng `quantconnect-stubs`.
"""
import base64
import builtins
from datetime import datetime, timedelta
# ⚠ `from AlgorithmImports import *` chiếm tên `time` (nó là `datetime.time`).
import time as dong_ho

import cat_lean as cl
from cat_studio import core

#: `main.py` đặt lại hai biến này ngay sau khi nạp module — `CAU_HINH` lấy từ khối CẤU
#: HÌNH ở đầu `main.py` (▶ nhanh là thu khoảng ngày lại), `SO_DO` lấy từ khối nén.
CAU_HINH: dict = {"symbol": "XAUUSD", "tu": "2025-01-01", "den": "2025-12-31", "von": 10000.0}
SO_DO: dict | None = None

_GOC_GIO = datetime(1970, 1, 1)


def _giay(dt):
    """Giờ của nến LEAN (datetime không múi giờ) → số giây UTC.

    Thuật toán đặt múi giờ UTC (`initialize`), nên `dt` là giờ UTC — số giây ra đây là
    epoch thật, app in thẳng ra được. Bộ luật thì chỉ dùng HIỆU giữa hai mốc và phép chia
    lấy dư theo 60/300/900 giây: múi giờ nào lệch nguyên giờ cũng cho cùng biên nến."""
    return int(round((dt - _GOC_GIO).total_seconds()))


def _bid(q):
    """Nến BID — MT5 vẽ nến bằng Bid, cả bộ luật cũng nghĩ bằng Bid."""
    return q.bid if q.bid is not None else q


def _tao_chi_bao(k):
    """Khoá `(tên, khung, chu kỳ, kiểu)` của `ChuongTrinh.khoa` → chỉ báo LEAN."""
    ten, _, chu_ky, kieu = k
    n = int(chu_ky)
    if ten == "atr":
        # ⚠ SIMPLE = SMA của True Range, đúng iATR của MT5. Mặc định của LEAN là Wilder —
        #   để mặc định thì ngưỡng 7 bps dò trên MT5 mất nghĩa (core.md §12.13).
        return AverageTrueRange(n, MovingAverageType.SIMPLE)
    if ten == "ma":
        kieu = (kieu or "SMA").upper()
        if kieu == "SMA":
            return SimpleMovingAverage(n)
        if kieu == "EMA":
            return ExponentialMovingAverage(n)
        if kieu == "SMMA":
            return WilderMovingAverage(n)
        if kieu == "LWMA":
            return LinearWeightedMovingAverage(n)
    raise ValueError(f"Chỉ báo {ten} ({kieu}) chưa nối sang LEAN.")


class CatStudioTrenQC(QCAlgorithm):

    def initialize(self):
        self._bat_dau = dong_ho.perf_counter()
        doc = SO_DO
        if not doc:
            raise ValueError("Thiếu sơ đồ — hãy dán bộ file do tools/dong_goi_lean.py "
                             "sinh ra, không dán vo_qc.py.")
        ch = self._ch = CAU_HINH
        # UTC: giờ trên nhật ký là giờ thật, đọc ra được. Mặc định của LEAN là New York.
        self.set_time_zone(TimeZones.UTC)
        self._phien = cl.PhienQC(doc, cl.CaiDatQC(symbol=ch["symbol"],
                                                  deposit=float(ch["von"])))
        self.set_start_date(datetime.strptime(ch["tu"], "%Y-%m-%d"))
        self.set_end_date(datetime.strptime(ch["den"], "%Y-%m-%d"))
        self.set_cash(float(ch["von"]))
        # fill_forward=False: phút nào sàn không có giá thì KHÔNG có nến — như MT5. Để mặc
        # định thì LEAN chép nến cũ lấp lỗ, và lỗ hổng (thứ giết vùng nén) biến mất.
        self._ma = self.add_cfd(ch["symbol"], Resolution.MINUTE, Market.OANDA,
                                fill_forward=False).symbol
        self._spread = 0.0

        ct = self._phien.ct
        self._chi_bao: dict = {}
        for k in ct._cot:
            if k[0] not in cl.COT_GIA:
                self._chi_bao.setdefault(k[1], []).append((k, _tao_chi_bao(k)))
        # Chỉ báo cập nhật TAY trong chính hàm nhận nến, không `register_indicator`: hai
        # bên cùng nghe một sự kiện thì không ai hứa bên nào chạy trước, và đọc ATR của
        # nến TRƯỚC là lệch im lặng.
        for tf in sorted(ct.khung_can, key=lambda x: core.TF_PHUT[x]):
            if tf == "M1":
                continue                        # nến M1 tới thẳng `on_data`
            gop = QuoteBarConsolidator(timedelta(minutes=core.TF_PHUT[tf]))
            gop.data_consolidated += self._nghe(tf)
            self.subscription_manager.add_consolidator(self._ma, gop)

    def _nghe(self, tf):
        def nghe(_, q):
            self._khi_khung(tf, q)
        return nghe

    def _khi_khung(self, tf, q):
        b = _bid(q)
        gia_tri = {}
        for k, cb in self._chi_bao.get(tf, ()):
            if k[0] == "atr":
                cb.update(TradeBar(q.time, q.symbol, b.open, b.high, b.low, b.close, 0,
                                   q.period))
                # MT5 bỏ TR của nến đầu (nó cần close của nến trước), nên ATR đầu tiên nằm
                # ở nến thứ chu_kỳ+1. LEAN tính luôn TR nến đầu = high − low và sẵn sớm một
                # nến. Chờ thêm đúng một nến thì cửa sổ trượt trùng khít MT5.
                san = cb.is_ready and cb.samples > k[2]
            else:
                cb.update(q.end_time, b.close)
                san = cb.is_ready
            gia_tri[k] = float(cb.current.value) if san else None
        self._phien.nhan_khung(tf, _giay(q.time), _giay(q.end_time), float(b.open),
                               float(b.high), float(b.low), float(b.close), gia_tri)

    def on_data(self, data):
        if not data.quote_bars.contains_key(self._ma):
            return
        q = data.quote_bars[self._ma]
        if "M1" in self._phien.ct.khung_can:
            self._khi_khung("M1", q)
        b = _bid(q)
        ask = float(q.ask.close) if q.ask is not None else None
        if ask is not None:
            self._spread = ask - float(b.close)
        self._phien.mot_nhip(_giay(q.end_time), float(b.open), float(b.high),
                             float(b.low), float(b.close), self._spread, ask)

    def on_end_of_algorithm(self):
        giay = dong_ho.perf_counter() - self._bat_dau
        ch = self._ch
        self._phien.ket_thuc(giay, them=cl.meta_cau_hinh(ch))
        # Khoá do app đặt cho RIÊNG lượt này (`CAU_HINH["khoa"]`): app chỉ đọc đúng khoá đó,
        # nên không bao giờ nhặt nhầm nhật ký cũ của lượt trước khi lượt này lưu hỏng.
        luu, loi = self._cat(cl.khoa_luu(ch, self._phien), self._phien.nhat_ky_gz())
        for dong in self._phien.dong_tong_ket(f"{ch['symbol']} {ch['tu']} → {ch['den']}",
                                              giay, luu):
            self.log(dong)
            self.debug(dong)
        if loi:
            # Dòng riêng, không cắt: lần đo slice 1 chỉ còn đọc được chữ "Invalid…".
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
        # Đường lùi: cất dạng chữ base64 — to hơn một phần ba, nhưng không phụ thuộc cách
        # LEAN đổi `bytes` của Python sang mảng byte của .NET.
        try:
            if self.object_store.save(khoa + ".b64",
                                      base64.b64encode(du_lieu).decode("ascii")):
                return f"được, dạng chữ ({mb} · {khoa}.b64)", loi
            loi += " | base64: save trả về False"
        except builtins.Exception as e:
            loi += f" | base64: {type(e).__name__}: {e}"
        return "KHÔNG", loi
