"""ĐO NHỊP — Cat Studio trên cloud QuantConnect.  (slice 1 · DECISIONS.md D-01, D-02)

VIỆC DUY NHẤT
-------------
Trả lời hai câu TRƯỚC khi xây bộ chạy sơ đồ thật trên LEAN:

  1. Một lần ▶ trên cloud mất bao lâu?  (một năm nến M1 XAUUSD)
  2. Nhật ký "vì sao" của cả năm có cất được vào Object Store của gói Free không?

CÁCH DÙNG
---------
quantconnect.com → tạo project Python mới → dán TOÀN BỘ file này đè lên `main.py` →
bấm Backtest. Cuối log có đúng một dòng bắt đầu bằng `ĐO NHỊP`.

ĐÂY KHÔNG PHẢI CHIẾN LƯỢC
-------------------------
Không gửi lệnh nào ra sàn. File bắt chước NHỊP của sơ đồ mẫu D_02 để tạo đúng cỡ tải
và cỡ nhật ký của bản thật:

    mỗi nến M1   khớp lệnh ẢO → Manage một lượt cho mỗi lệnh ảo đang sống
    mỗi nến M5   nuôi vùng nén → Entry một lượt, tính ĐỦ mọi điều kiện của cổng cuối
    mỗi lượt     đúng MỘT bản ghi nhật ký (core.md §12.8)

Thứ tự trong một nhịp giữ y bộ chạy cũ: khớp → nuôi vùng → Manage → Entry.

Lệnh ảo chỉ để Manage có việc mà chạy. Số lệnh ảo và tổng R in ra để soát cỡ tải có đúng
không (bản cũ trên data MT5: 547 lệnh/năm) — KHÔNG dùng để so kết quả: data khác sàn,
khớp lệnh giản lược (không đường đi 4 điểm, không spread).

MỘT BẢN GHI NHẬT KÝ = một dòng JSON
-----------------------------------
    [i, tab, lenh, duong, ket, ve, viec]

    i      chỉ số nến M1 — khoá để tua
    tab    "E" (Entry) | "M" (Manage)
    lenh   id lệnh ảo mà lượt Manage đang xét, Entry thì null
    duong  các khối đã đi qua, theo thứ tự: "1>2>3>3A>3A.1"
    ket    "xong" (tới khối hành động) | "het" (hết lượt)
    ve     mọi điều kiện của cổng cuối, mỗi cái [vế trái, vế phải, đạt]
    viec   null | việc đã làm | "chua_co_du_lieu"
"""
# region imports
from AlgorithmImports import *
# endregion
import builtins
import json
import math
from datetime import timedelta
# ⚠ `from AlgorithmImports import *` đã chiếm tên `time` (nó là `datetime.time`).
#   Gọi `time.perf_counter()` sẽ chết ngay dòng đầu, nên đồng hồ mang tên riêng.
import time as dong_ho


SYMBOL = "XAUUSD"
NAM = 2025

# Tham số mặc định của D_02 (core.md §7.6) — cùng bộ số với sơ đồ mẫu.
ATR_CHU_KY = 14           # ATR(M5, 14)
NGUONG_BPS = 7.0          # nến nén: ATR/close × 10⁴ < 7
NEN_NEN_TOI_THIEU = 10    # K nến nén liên tiếp
RONG_TOI_DA_ATR = 4.0     # bề rộng vùng ≤ 4 × ATR hiện tại
MA_CHU_KY = 50            # MA(M15, 50) kiểu SMA — chọn hướng
DEM_ATR = 0.10            # đệm vào lệnh = 0,10 × ATR hiện tại
SL_ATR_TB = 1.5           # 1R = 1,5 × ATR trung bình cả vùng
RR = 2.0                  # TP = 2R
BE_R = 1.0                # lãi ≥ 1R → dời SL về hoà vốn
VI_THE_TOI_DA = 3

FILE_NHAT_KY = "cat_studio/do_nhip.jsonl"


def _r(x):
    """Làm tròn 6 chữ số có nghĩa cho nhật ký gọn. `None` giữ nguyên = "chưa có số"."""
    return None if x is None else float(f"{x:.6g}")


def _so(x, le=0):
    """Số kiểu Việt: 354.503 · 47,3 · −8,4."""
    s = f"{x:,.{le}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return s.replace("-", "−")


class NhipD02:
    """Phần THUẦN — không biết QuantConnect tồn tại, nên kiểm được ở máy không có LEAN.

    Lớp vỏ `DoNhipCloud` bên dưới chỉ việc bơm nến và chỉ báo của LEAN vào đây.
    """

    def __init__(self):
        self.i = -1
        self.dem = {"m1": 0, "m5": 0, "entry": 0, "manage": 0}
        self.nhat_ky = []
        self.so_byte = 0
        # vùng nén — engine D_02 giản lược
        self.vung = None
        self.so_vung = 0
        self.atr = None
        self.atr_bps = None
        # khung M15 (cổng hướng)
        self.close_m15 = None
        self.ma_m15 = None
        # nến M5 vừa đóng, chờ tới lượt Entry của nhịp kế
        self.m5_moi = None
        # lệnh ẢO
        self.lenh = []
        self.so_lenh = 0
        self.so_dong = 0
        self.tong_R = 0.0

    # ------------------------------------------------------------------ đầu vào
    def nhan_m15(self, close, ma):
        self.close_m15 = close
        self.ma_m15 = ma if ma is not None and math.isfinite(ma) else None

    def nhan_m5(self, o, h, lo, c, atr):
        self.dem["m5"] += 1
        self.m5_moi = (o, h, lo, c, atr)

    def mot_nhip(self, o, h, lo, c):
        """Một nến M1 ĐÃ ĐÓNG: khớp → nuôi vùng → Manage từng lệnh → Entry (nếu M5 vừa đóng)."""
        self.i += 1
        self.dem["m1"] += 1
        self._khop(h, lo)
        m5 = self.m5_moi
        if m5 is not None:
            self._nuoi_vung(*m5)
        for x in list(self.lenh):
            self._manage(x, c)
        if m5 is not None:
            self.m5_moi = None
            self._entry()

    # ------------------------------------------------------------------ thị trường ẢO
    def _khop(self, h, lo):
        for x in list(self.lenh):
            mua = x["huong"] == "mua"
            if not x["khop"]:
                if (mua and h >= x["vao"]) or (not mua and lo <= x["vao"]):
                    x["khop"] = True        # giản lược: SL/TP xét từ nến sau
                continue
            cham_sl = lo <= x["sl"] if mua else h >= x["sl"]
            cham_tp = h >= x["tp"] if mua else lo <= x["tp"]
            if cham_sl or cham_tp:
                ra = x["sl"] if cham_sl else x["tp"]      # chạm cả hai → tính SL (bi quan)
                self.tong_R += ((ra - x["vao"]) if mua else (x["vao"] - ra)) / x["R"]
                self.so_dong += 1
                self.lenh.remove(x)

    # ------------------------------------------------------------------ engine
    def _nuoi_vung(self, o, h, lo, c, atr):
        if atr is None or not math.isfinite(atr) or atr <= 0 or c <= 0:
            self.atr = self.atr_bps = None
            return
        self.atr = atr
        self.atr_bps = atr / c * 1e4
        if self.atr_bps < NGUONG_BPS:
            v = self.vung
            if v is None or not v["song"]:
                self.so_vung += 1
                v = self.vung = {"id": self.so_vung, "dem": 0, "HH": h, "LL": lo,
                                 "tong_atr": 0.0, "song": True, "da_sinh": False}
            v["dem"] += 1
            v["HH"] = max(v["HH"], h)
            v["LL"] = min(v["LL"], lo)
            v["tong_atr"] += atr
        elif self.vung is not None:
            self.vung["song"] = False                     # nén tan → vùng chết

    # ------------------------------------------------------------------ sơ đồ ENTRY
    def _entry(self):
        self.dem["entry"] += 1
        duong = ["1", "2"]
        atr, bps = self.atr, self.atr_bps
        if atr is None or bps is None:
            return self._ghi("E", None, duong, "het", [], "chua_co_du_lieu")

        # [2] Vùng nén đã xác nhận? — tính ĐỦ bốn điều kiện, không ngắt ở cái sai đầu tiên.
        # Chưa có vùng nào thì ba vế vùng là `null` chứ không phải 0: không có nguồn thì
        # điều kiện TRƯỢT, và nhật ký nói đúng là "chưa có", không bịa ra một con số.
        v = self.vung if self.vung is not None and self.vung["song"] else None
        rong = (v["HH"] - v["LL"]) / atr if v else None
        ve = [[_r(bps), NGUONG_BPS, bps < NGUONG_BPS],
              [v["dem"] if v else None, NEN_NEN_TOI_THIEU,
               v is not None and v["dem"] >= NEN_NEN_TOI_THIEU],
              [_r(rong), RONG_TOI_DA_ATR, rong is not None and rong <= RONG_TOI_DA_ATR],
              [v["da_sinh"] if v else None, False, v is not None and not v["da_sinh"]]]
        if v is None or not all(d[2] for d in ve):
            return self._ghi("E", None, duong, "het", ve)

        # [3] Còn chỗ cho lệnh mới?
        duong.append("3")
        cho = sum(1 for x in self.lenh if not x["khop"])
        vi_the = len(self.lenh) - cho
        ve = [[cho, 0, cho == 0], [vi_the, VI_THE_TOI_DA, vi_the < VI_THE_TOI_DA]]
        if not all(d[2] for d in ve):
            return self._ghi("E", None, duong, "het", ve)

        # [3A] Xu hướng LÊN? → [3A.1] Buy Stop · [3B] Xu hướng XUỐNG? → [3B.1] Sell Stop
        duong.append("3A")
        if self.ma_m15 is None or self.close_m15 is None:
            duong.append("3B")
            return self._ghi("E", None, duong, "het", [], "chua_co_du_lieu")
        c, ma = self.close_m15, self.ma_m15
        if c > ma:
            duong.append("3A.1")
            return self._dat("mua", duong, [[_r(c), _r(ma), True]], v, atr)
        duong.append("3B")
        if c < ma:
            duong.append("3B.1")
            return self._dat("ban", duong, [[_r(c), _r(ma), True]], v, atr)
        return self._ghi("E", None, duong, "het", [[_r(c), _r(ma), False]])

    def _dat(self, huong, duong, ve, v, atr):
        R = SL_ATR_TB * v["tong_atr"] / v["dem"]
        dem = DEM_ATR * atr
        if huong == "mua":
            vao = v["HH"] + dem
            sl, tp = vao - R, vao + RR * R
        else:
            vao = v["LL"] - dem
            sl, tp = vao + R, vao - RR * R
        self.so_lenh += 1
        x = {"id": f"A-{self.so_lenh:04d}", "huong": huong, "vao": vao, "sl": sl, "tp": tp,
             "R": R, "khop": False, "vung": v["id"]}
        self.lenh.append(x)
        v["da_sinh"] = True                               # một cú nén, một lệnh
        return self._ghi("E", None, duong, "xong", ve, f"dat_{huong} {x['id']} @{_r(vao)}")

    # ------------------------------------------------------------------ sơ đồ MANAGE
    def _manage(self, x, c):
        self.dem["manage"] += 1
        duong = ["1", "1A"]
        v = self.vung
        tan = not (v is not None and v["id"] == x["vung"] and v["song"])

        # [1A] Chưa khớp mà nén đã tan? → [1A.1] Huỷ lệnh chờ
        ve = [[x["khop"], False, not x["khop"]], [tan, True, tan]]
        if all(d[2] for d in ve):
            duong.append("1A.1")
            self.lenh.remove(x)
            return self._ghi("M", x["id"], duong, "xong", ve, "huy_cho")

        # [1B] Đã khớp, đủ 1R, SL chưa hoà vốn? → [1B.1] Dời SL về giá vào
        duong.append("1B")
        mua = x["huong"] == "mua"
        lai = ((c - x["vao"]) if mua else (x["vao"] - c)) / x["R"]
        hoa_von = x["sl"] >= x["vao"] if mua else x["sl"] <= x["vao"]
        ve = [[x["khop"], True, x["khop"]], [_r(lai), BE_R, lai >= BE_R],
              [hoa_von, False, not hoa_von]]
        if all(d[2] for d in ve):
            duong.append("1B.1")
            x["sl"] = x["vao"]
            return self._ghi("M", x["id"], duong, "xong", ve, "sl_hoa_von")
        return self._ghi("M", x["id"], duong, "het", ve)

    # ------------------------------------------------------------------ nhật ký
    def _ghi(self, tab, lenh, duong, ket, ve, viec=None):
        dong = json.dumps([self.i, tab, lenh, ">".join(duong), ket, ve, viec],
                          separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        self.nhat_ky.append(dong)
        self.so_byte += len(dong.encode("utf-8")) + 1     # +1 cho dấu xuống dòng

    def nhat_ky_jsonl(self):
        return "".join(d + "\n" for d in self.nhat_ky)

    def dong_tong_ket(self, giay, luu):
        d = self.dem
        if d["m1"] == 0:
            return (f"ĐO NHỊP · KHÔNG CÓ DỮ LIỆU — QuantConnect không trả nến nào cho "
                    f"{SYMBOL} {NAM}. Đổi SYMBOL / NAM ở đầu file rồi chạy lại.")
        return (f"ĐO NHỊP · {SYMBOL} {NAM} · {_so(d['m1'])} nến M1 · {_so(d['m5'])} nến M5 · "
                f"lượt Entry {_so(d['entry'])} · lượt Manage {_so(d['manage'])} · "
                f"chạy {_so(giay, 1)} giây · nhật ký {_so(len(self.nhat_ky))} dòng = "
                f"{_so(self.so_byte / 1e6, 1)} MB · lưu Object Store: {luu} · "
                f"lệnh ảo {_so(self.so_lenh)} (đóng {_so(self.so_dong)}, "
                f"tổng {_so(self.tong_R, 1)}R — chỉ để soát cỡ tải)")


class DoNhipCloud(QCAlgorithm):
    """Lớp vỏ: nến + chỉ báo của LEAN → `NhipD02`. Không chứa luật nào."""

    def initialize(self):
        self._bat_dau = dong_ho.perf_counter()
        self.set_start_date(NAM, 1, 1)
        self.set_end_date(NAM, 12, 31)
        self.set_cash(10000)
        # fill_forward=False: phút nào sàn không có giá thì KHÔNG có nến — như MT5. Để mặc
        # định thì LEAN tự chép nến cũ lấp lỗ, và lỗ hổng (thứ giết vùng nén) biến mất.
        self._xau = self.add_cfd(SYMBOL, Resolution.MINUTE, Market.OANDA,
                                 fill_forward=False).symbol
        self._nhip = NhipD02()

        # ⚠ SIMPLE = SMA của True Range, đúng iATR của MT5. Mặc định của LEAN là Wilder —
        #   để mặc định thì ngưỡng 7 bps (dò trên MT5) mất nghĩa (core.md §12.13).
        self._atr = AverageTrueRange(ATR_CHU_KY, MovingAverageType.SIMPLE)
        self._ma = SimpleMovingAverage(MA_CHU_KY)

        # Chỉ báo được cập nhật TAY trong chính hàm nhận nến, không `register_indicator`:
        # hai bên cùng nghe một sự kiện thì không ai hứa bên nào chạy trước, và đọc
        # ATR của nến TRƯỚC là lệch im lặng.
        m5 = QuoteBarConsolidator(timedelta(minutes=5))
        m5.data_consolidated += self._khi_m5
        self.subscription_manager.add_consolidator(self._xau, m5)
        m15 = QuoteBarConsolidator(timedelta(minutes=15))
        m15.data_consolidated += self._khi_m15
        self.subscription_manager.add_consolidator(self._xau, m15)

    @staticmethod
    def _bid(q):
        """Nến BID (MT5 vẽ nến bằng Bid). Thiếu Bid thì đành đọc giá giữa."""
        return q.bid if q.bid is not None else q

    def _khi_m5(self, _, q):
        b = self._bid(q)
        self._atr.update(TradeBar(q.time, q.symbol, b.open, b.high, b.low, b.close, 0,
                                  q.period))
        atr = self._atr.current.value if self._atr.is_ready else None
        self._nhip.nhan_m5(b.open, b.high, b.low, b.close, atr)

    def _khi_m15(self, _, q):
        b = self._bid(q)
        self._ma.update(q.end_time, b.close)
        self._nhip.nhan_m15(b.close, self._ma.current.value if self._ma.is_ready else None)

    def on_data(self, data):
        if not data.quote_bars.contains_key(self._xau):
            return
        b = self._bid(data.quote_bars[self._xau])
        self._nhip.mot_nhip(b.open, b.high, b.low, b.close)

    def on_end_of_algorithm(self):
        giay = dong_ho.perf_counter() - self._bat_dau
        try:
            luu = ("được" if self.object_store.save(FILE_NHAT_KY, self._nhip.nhat_ky_jsonl())
                   else "KHÔNG (save trả về False)")
        # ⚠ `builtins.` là cố ý: `from System import *` bên trong AlgorithmImports có thể để
        #   `Exception` trỏ sang System.Exception của .NET, và khi đó lỗi Python lọt qua.
        except builtins.Exception as e:                   # noqa: BLE001
            luu = f"KHÔNG ({type(e).__name__}: {str(e)[:160]})"
        dong = self._nhip.dong_tong_ket(giay, luu)
        self.log(dong)
        self.debug(dong)
