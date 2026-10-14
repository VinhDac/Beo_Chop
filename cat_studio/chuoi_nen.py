"""CHUỖI NẾN + CHỈ BÁO TÍNH DẦN — phần "mắt" của bộ máy 5 trạm.  (D-10, phần 3)

Bộ máy nhận nến M1 từng cây (QuantConnect đưa sang, hoặc sàn giả trong bài kiểm), tự gộp lên
khung lớn và tự tính chỉ báo. Không numpy, không QuantConnect: cùng một file chạy trên máy
lẫn trong `main.py` gửi lên QC, nên con số hai nơi không thể lệch nhau.

HAI LUẬT KHÔNG NHÌN TRƯỚC
-------------------------
1. **Gộp theo BIÊN THỜI GIAN TUYỆT ĐỐI** (giờ UTC): nến H1 là [10:00, 11:00) bất kể bên trong
   có đủ 60 nến M1 hay không. Đếm "60 cây một cụm" thì chỉ cần thiếu một phút là mọi nến sau
   lệch pha khỏi biên thật, và không gì báo cho biết.
2. **Một nến chỉ ĐÓNG khi giờ đã qua hẳn nó** (`dong_neu_toi(t)` với `t ≥ giờ kết thúc`). Chỉ
   báo chỉ cập nhật ở lúc đóng, nên ở thời điểm t không ai đọc được nến chưa kết thúc.

`lui = 0` là nến VỪA ĐÓNG; `lui = 1` là cây trước nó. Chưa đủ dữ liệu thì ra NaN — mọi phép so
với NaN đều sai, nên cổng TRƯỢT chứ không lặng lẽ khớp giữa lúc chưa biết gì.
"""
import math
from collections import deque

NAN = float("nan")

KHUNG_GIAY = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600, "H4": 14400,
              "D1": 86400}


def la_nan(x):
    return x != x


# ---------------------------------------------------------------------------
# Lịch sử giá trị — đọc lùi `lui` cây
# ---------------------------------------------------------------------------
class _LichSu:
    __slots__ = ("ds",)

    def __init__(self, giu):
        self.ds = deque(maxlen=max(1, int(giu)))

    def them(self, v):
        self.ds.append(v)

    def doc(self, lui=0):
        lui = int(lui)
        if lui < 0 or lui >= len(self.ds):
            return NAN
        return self.ds[-1 - lui]


class _Cua:
    """Cửa sổ trượt n giá trị gần nhất, kèm tổng để tính trung bình O(1)."""
    __slots__ = ("n", "ds", "tong")

    def __init__(self, n):
        self.n, self.ds, self.tong = int(n), deque(), 0.0

    def them(self, v):
        self.ds.append(v)
        self.tong += v
        if len(self.ds) > self.n:
            self.tong -= self.ds.popleft()

    def du(self):
        return len(self.ds) >= self.n

    def tb(self):
        return self.tong / self.n if self.du() else NAN


class _TrungBinhMu:
    """EMA (alpha = 2/(n+1)) hoặc RMA/Wilder (alpha = 1/n), MỒI bằng SMA của n giá trị đầu —
    đúng cách QuantConnect và đa số nền tảng làm. Mồi bằng giá trị đầu tiên thì 20 cây đầu
    lệch hẳn, và lệch đó lan rất lâu."""
    __slots__ = ("n", "alpha", "dem", "tong", "gt")

    def __init__(self, n, wilder=False):
        self.n = int(n)
        self.alpha = 1.0 / self.n if wilder else 2.0 / (self.n + 1)
        self.dem, self.tong, self.gt = 0, 0.0, NAN

    def them(self, v):
        if la_nan(v):
            return self.gt
        self.dem += 1
        if self.dem <= self.n:
            self.tong += v
            if self.dem == self.n:
                self.gt = self.tong / self.n
        else:
            self.gt += self.alpha * (v - self.gt)
        return self.gt


def _do_lech(ds):
    """Độ lệch chuẩn TỔNG THỂ (chia n) — như chỉ báo StandardDeviation của QC."""
    n = len(ds)
    tb = sum(ds) / n
    return math.sqrt(max(0.0, sum((x - tb) ** 2 for x in ds) / n))


# ---------------------------------------------------------------------------
# Chỉ báo — mỗi lớp nhận MỘT nến đã đóng, ghi ra một hay vài "đường"
# ---------------------------------------------------------------------------
class ChiBao:
    """Gốc chung. `duong` = tên các đường ghi ra; mỗi đường giữ lịch sử để đọc `lui`."""
    duong = ("gt",)

    def __init__(self, giu):
        self.ls = {d: _LichSu(giu) for d in self.duong}

    def ghi(self, **gt):
        for d in self.duong:
            self.ls[d].them(gt.get(d, NAN))

    def doc(self, duong="gt", lui=0):
        return self.ls[duong].doc(lui)


class _Gia(ChiBao):
    """Giá của chính nến: mở / cao / thấp / đóng / khối lượng / giá trị giao dịch."""
    duong = ("o", "h", "l", "c", "v", "gtgd")

    def cap_nhat(self, n):
        self.ghi(o=n.o, h=n.h, l=n.l, c=n.c, v=n.v, gtgd=n.c * n.v)


class _SMA(ChiBao):
    def __init__(self, giu, chu_ky, nguon="c"):
        super().__init__(giu)
        self.cua, self.nguon = _Cua(chu_ky), nguon

    def cap_nhat(self, n):
        self.cua.them(n.c * n.v if self.nguon == "gtgd" else getattr(n, self.nguon))
        self.ghi(gt=self.cua.tb())


class _EMA(ChiBao):
    def __init__(self, giu, chu_ky, wilder=False):
        super().__init__(giu)
        self.tb = _TrungBinhMu(chu_ky, wilder)

    def cap_nhat(self, n):
        self.ghi(gt=self.tb.them(n.c))


class _WMA(ChiBao):
    def __init__(self, giu, chu_ky):
        super().__init__(giu)
        self.n, self.ds = int(chu_ky), deque(maxlen=int(chu_ky))

    def cap_nhat(self, n):
        self.ds.append(n.c)
        if len(self.ds) < self.n:
            self.ghi(gt=NAN)
            return
        tu = sum((i + 1) * x for i, x in enumerate(self.ds))
        self.ghi(gt=tu / (self.n * (self.n + 1) / 2))


class _ATR(ChiBao):
    """ATR = trung bình của True Range. `kieu = rma` (Wilder, mặc định QC) hoặc `sma`.
    `pt = True` ghi ATR chia giá đóng × 100 — so được giữa các mã giá khác nhau."""

    def __init__(self, giu, chu_ky, kieu="rma", pt=False):
        super().__init__(giu)
        self.tb = _TrungBinhMu(chu_ky, wilder=True) if kieu != "sma" else _Cua(chu_ky)
        self.kieu, self.pt, self.c_truoc = kieu, pt, NAN

    def cap_nhat(self, n):
        tr = n.h - n.l if la_nan(self.c_truoc) else max(
            n.h - n.l, abs(n.h - self.c_truoc), abs(n.l - self.c_truoc))
        self.c_truoc = n.c
        if self.kieu == "sma":
            self.tb.them(tr)
            a = self.tb.tb()
        else:
            a = self.tb.them(tr)
        self.ghi(gt=(a / n.c * 100.0 if n.c else NAN) if self.pt else a)


class _RSI(ChiBao):
    """RSI kiểu Wilder: lãi/lỗ trung bình bằng RMA, mồi bằng SMA của n lần đổi giá đầu."""

    def __init__(self, giu, chu_ky):
        super().__init__(giu)
        self.lai, self.lo = _TrungBinhMu(chu_ky, True), _TrungBinhMu(chu_ky, True)
        self.c_truoc = NAN

    def cap_nhat(self, n):
        if la_nan(self.c_truoc):
            self.c_truoc = n.c
            self.ghi(gt=NAN)
            return
        d = n.c - self.c_truoc
        self.c_truoc = n.c
        a, b = self.lai.them(max(d, 0.0)), self.lo.them(max(-d, 0.0))
        if la_nan(a):
            self.ghi(gt=NAN)
        elif b == 0:
            self.ghi(gt=100.0 if a > 0 else 50.0)
        else:
            self.ghi(gt=100.0 - 100.0 / (1.0 + a / b))


class _MACD(ChiBao):
    duong = ("macd", "tin_hieu", "histogram")

    def __init__(self, giu, nhanh, cham, tin_hieu):
        super().__init__(giu)
        self.f, self.s = _TrungBinhMu(nhanh), _TrungBinhMu(cham)
        self.sig = _TrungBinhMu(tin_hieu)

    def cap_nhat(self, n):
        a, b = self.f.them(n.c), self.s.them(n.c)
        m = a - b if not (la_nan(a) or la_nan(b)) else NAN
        s = self.sig.them(m)
        self.ghi(macd=m, tin_hieu=s, histogram=m - s if not la_nan(s) else NAN)


class _Bollinger(ChiBao):
    duong = ("tren", "giua", "duoi")

    def __init__(self, giu, chu_ky, do_lech):
        super().__init__(giu)
        self.n, self.k, self.ds = int(chu_ky), float(do_lech), deque(maxlen=int(chu_ky))

    def cap_nhat(self, n):
        self.ds.append(n.c)
        if len(self.ds) < self.n:
            self.ghi()
            return
        tb, sd = sum(self.ds) / self.n, _do_lech(self.ds)
        self.ghi(tren=tb + self.k * sd, giua=tb, duoi=tb - self.k * sd)


class _DoLech(ChiBao):
    def __init__(self, giu, chu_ky):
        super().__init__(giu)
        self.n, self.ds = int(chu_ky), deque(maxlen=int(chu_ky))

    def cap_nhat(self, n):
        self.ds.append(n.c)
        self.ghi(gt=_do_lech(self.ds) if len(self.ds) >= self.n else NAN)


class _ROC(ChiBao):
    """Đổi giá %: giá đóng so với giá đóng `chu_ky` cây trước."""

    def __init__(self, giu, chu_ky):
        super().__init__(giu)
        self.ds = deque(maxlen=int(chu_ky) + 1)

    def cap_nhat(self, n):
        self.ds.append(n.c)
        if len(self.ds) < self.ds.maxlen or not self.ds[0]:
            self.ghi(gt=NAN)
        else:
            self.ghi(gt=(n.c / self.ds[0] - 1.0) * 100.0)


class _Donchian(ChiBao):
    """Đỉnh cao nhất / đáy thấp nhất của `chu_ky` cây TRƯỚC cây đang xét — để "giá đóng vượt
    biên trên" là một cú PHÁ KÊNH thật. Tính cả cây đang xét thì giá không bao giờ vượt được."""
    duong = ("tren", "duoi")

    def __init__(self, giu, chu_ky):
        super().__init__(giu)
        self.n = int(chu_ky)
        self.h, self.l = deque(maxlen=self.n + 1), deque(maxlen=self.n + 1)

    def cap_nhat(self, n):
        self.h.append(n.h)
        self.l.append(n.l)
        if len(self.h) <= self.n:
            self.ghi()
            return
        self.ghi(tren=max(list(self.h)[:-1]), duoi=min(list(self.l)[:-1]))


class _ADX(ChiBao):
    """ADX của Wilder: +DM/−DM/TR làm mượt bằng RMA, DX → RMA lần nữa."""

    def __init__(self, giu, chu_ky):
        super().__init__(giu)
        n = int(chu_ky)
        self.tr, self.p, self.m = (_TrungBinhMu(n, True), _TrungBinhMu(n, True),
                                   _TrungBinhMu(n, True))
        self.adx = _TrungBinhMu(n, True)
        self.truoc = None

    def cap_nhat(self, n):
        if self.truoc is None:
            self.truoc = n
            self.ghi(gt=NAN)
            return
        t = self.truoc
        len_, xuong = n.h - t.h, t.l - n.l
        pdm = len_ if len_ > xuong and len_ > 0 else 0.0
        mdm = xuong if xuong > len_ and xuong > 0 else 0.0
        tr = max(n.h - n.l, abs(n.h - t.c), abs(n.l - t.c))
        self.truoc = n
        a, b, c = self.tr.them(tr), self.p.them(pdm), self.m.them(mdm)
        if la_nan(a) or not a:
            self.ghi(gt=NAN)
            return
        pdi, mdi = 100.0 * b / a, 100.0 * c / a
        dx = 100.0 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi else 0.0
        self.ghi(gt=self.adx.them(dx))


class _Stoch(ChiBao):
    """Stochastic nhanh: %K = vị trí giá đóng trong biên độ `chu_ky` cây (0–100), %D = SMA
    `chu_ky_d` của %K. Biên độ bằng 0 (giá đứng im) thì %K = 50 — giữa, không lên không xuống."""
    duong = ("k", "d")

    def __init__(self, giu, chu_ky, chu_ky_d):
        super().__init__(giu)
        n = int(chu_ky)
        self.h, self.l = deque(maxlen=n), deque(maxlen=n)
        self.n, self.d = n, _Cua(chu_ky_d)

    def cap_nhat(self, n):
        self.h.append(n.h)
        self.l.append(n.l)
        if len(self.h) < self.n:
            self.ghi()
            return
        hh, ll = max(self.h), min(self.l)
        k = 50.0 if hh == ll else (n.c - ll) / (hh - ll) * 100.0
        self.d.them(k)
        self.ghi(k=k, d=self.d.tb())


def _so(v):
    return float(v)


def tao_chi_bao(ten, o, giu):
    """Dựng chỉ báo cho đại lượng `ten` với các ô `o` (đã chuẩn hoá — mọi số là số thật).
    Trả (khoá dùng chung, chỉ báo, đường cần đọc). Hai điều kiện hỏi CÙNG chỉ báo cùng ô thì
    dùng chung một bản — khoá do hàm này dựng nên không ai phải nhớ luật."""
    ck = int(_so(o.get("chu_ky", 0) or 0))
    if ten in ("gia_dong", "gia_mo", "gia_cao", "gia_thap", "khoi_luong", "gia_tri_gd"):
        duong = {"gia_dong": "c", "gia_mo": "o", "gia_cao": "h", "gia_thap": "l",
                 "khoi_luong": "v", "gia_tri_gd": "gtgd"}[ten]
        return ("gia",), (lambda: _Gia(giu)), duong
    if ten in ("sma", "kl_tb", "gia_tri_gd_tb"):
        nguon = {"sma": "c", "kl_tb": "v", "gia_tri_gd_tb": "gtgd"}[ten]
        return ("sma", nguon, ck), (lambda: _SMA(giu, ck, nguon)), "gt"
    if ten in ("ema", "rma"):
        return (ten, ck), (lambda: _EMA(giu, ck, wilder=ten == "rma")), "gt"
    if ten == "wma":
        return ("wma", ck), (lambda: _WMA(giu, ck)), "gt"
    if ten in ("atr", "atr_pt"):
        kieu = o.get("kieu") or "rma"
        return (ten, ck, kieu), (lambda: _ATR(giu, ck, kieu, pt=ten == "atr_pt")), "gt"
    if ten == "rsi":
        return ("rsi", ck), (lambda: _RSI(giu, ck)), "gt"
    if ten == "macd":
        a, b, c = int(_so(o["nhanh"])), int(_so(o["cham"])), int(_so(o["tin_hieu"]))
        return ("macd", a, b, c), (lambda: _MACD(giu, a, b, c)), o.get("dong") or "macd"
    if ten == "bollinger":
        k = _so(o["do_lech"])
        return ("boll", ck, k), (lambda: _Bollinger(giu, ck, k)), o.get("dai") or "tren"
    if ten == "do_lech_chuan":
        return ("std", ck), (lambda: _DoLech(giu, ck)), "gt"
    if ten == "roc_pt":
        return ("roc", ck), (lambda: _ROC(giu, ck)), "gt"
    if ten == "donchian":
        return ("donchian", ck), (lambda: _Donchian(giu, ck)), o.get("bien") or "tren"
    if ten == "adx":
        return ("adx", ck), (lambda: _ADX(giu, ck)), "gt"
    if ten == "stoch":
        d = int(_so(o["chu_ky_d"]))
        return ("stoch", ck, d), (lambda: _Stoch(giu, ck, d)), o.get("dong") or "k"
    return None


# ---------------------------------------------------------------------------
# Nến và chuỗi nến
# ---------------------------------------------------------------------------
class Nen:
    __slots__ = ("t", "o", "h", "l", "c", "v")

    def __init__(self, t, o, h, l, c, v=0.0):
        self.t, self.o, self.h, self.l, self.c, self.v = t, o, h, l, c, v

    def __repr__(self):
        return f"Nen(t={self.t}, o={self.o}, h={self.h}, l={self.l}, c={self.c}, v={self.v})"


class ChuoiNen:
    """Nến ĐÃ ĐÓNG của MỘT mã ở MỘT khung, cùng các chỉ báo gắn vào nó.

    `t` của nến là GIỜ MỞ (biên đầu khung). Nến M1 nạp vào mang giờ ĐÓNG — QuantConnect phát
    sự kiện ở lúc nến kết thúc — nên nó thuộc khung chứa phút `t_dong − 60`."""

    def __init__(self, khung, giu=600):
        self.khung, self.p = khung, KHUNG_GIAY[khung]
        self.giu = giu
        self.dang = None          # nến đang gom, CHƯA đóng
        self.so_nen = 0           # đã đóng bao nhiêu cây
        self.cuoi = None          # nến vừa đóng gần nhất
        self.chi_bao = {}         # khoá → ChiBao
        self.gia = _Gia(giu)
        self.chi_bao[("gia",)] = self.gia

    def dang_ky(self, ten, o):
        """Gắn (một lần) chỉ báo cho đại lượng `ten`; trả hàm đọc `(lui) → giá trị`."""
        tao = tao_chi_bao(ten, o, self.giu)
        if tao is None:
            raise KeyError(ten)
        khoa, dung, duong = tao
        cb = self.chi_bao.get(khoa)
        if cb is None:
            cb = self.chi_bao[khoa] = dung()
        return lambda lui=0: cb.doc(duong, lui)

    def nap_m1(self, t_dong, o, h, l, c, v=0.0):
        """Gom một nến M1 vào nến khung đang mở. Sang biên mới thì đóng nến cũ trước."""
        bd = ((int(t_dong) - 60) // self.p) * self.p
        if self.dang is not None and bd != self.dang.t:
            self._dong()
        if self.dang is None:
            self.dang = Nen(bd, o, h, l, c, v)
        else:
            n = self.dang
            n.h, n.l, n.c, n.v = max(n.h, h), min(n.l, l), c, n.v + v

    def dong_neu_toi(self, t):
        """Đóng nến đang gom nếu giờ `t` đã qua hẳn nó. Trả True nếu vừa đóng một cây."""
        if self.dang is not None and self.dang.t + self.p <= int(t):
            self._dong()
            return True
        return False

    def _dong(self):
        n, self.dang = self.dang, None
        self.cuoi = n
        self.so_nen += 1
        for cb in self.chi_bao.values():
            cb.cap_nhat(n)
