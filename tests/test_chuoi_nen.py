"""CHUỖI NẾN + CHỈ BÁO TÍNH DẦN — mắt của bộ máy 5 trạm.  (D-10, phần 3a)

Canh ba thứ hỏng mà vẫn "trông có vẻ chạy":

  1. **Gộp lệch biên** — nến H1 phải là [10:00, 11:00) dù bên trong thiếu phút; giờ nào trống
     hẳn thì KHÔNG có nến giờ đó (không bịa nến rỗng).
  2. **Nhìn trước** — nến khung lớn chỉ đóng khi giờ đã qua hẳn nó; trước đó chỉ báo không
     được biết gì về nó.
  3. **Chỉ báo tính dần lệch bản tính một lèo** — so từng chỉ báo với một bản tính tay độc
     lập ngay trong file này, trên 400 nến ngẫu nhiên.

Chạy:  python tests\\test_chuoi_nen.py
"""
import io
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import chuoi_nen as CN  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


NGAY = 1704067200          # 2024-01-01 00:00 UTC (thứ Hai)
GIO = 3600


def m1(cn, t_dong, c, h=None, l=None, o=None, v=1.0):
    cn.nap_m1(t_dong, c if o is None else o, h if h is not None else c,
              l if l is not None else c, c, v)


# ================= 1. gộp nến =================
print("\n▸ Gộp M1 → H1 theo biên thời gian tuyệt đối")
cn = CN.ChuoiNen("H1")
dong = []
# Giờ 00:00–01:00 đủ 60 phút; giờ 01:00–02:00 chỉ có phút 01:05–01:10; giờ 02 trống HẲN;
# giờ 03 có hai phút.
phut = [NGAY + 60 * (i + 1) for i in range(60)]
phut += [NGAY + GIO + 60 * (i + 1) for i in range(5, 10)]
phut += [NGAY + 3 * GIO + 60, NGAY + 3 * GIO + 120]
gia = {t: 100.0 + (t - NGAY) / 60.0 for t in phut}
for t in phut:
    truoc = cn.so_nen
    m1(cn, t, gia[t], h=gia[t] + 0.5, l=gia[t] - 0.5, v=2.0)
    cn.dong_neu_toi(t)
    if cn.so_nen > truoc:
        dong.append((t, cn.cuoi.t))
cn.dong_neu_toi(NGAY + 4 * GIO)
n1 = cn.gia
kiem("đóng đúng 3 nến: 00h, 01h, 03h — giờ 02 trống hẳn thì KHÔNG có nến bịa",
     cn.so_nen == 3 and [x[1] for x in dong] == [NGAY, NGAY + GIO], f"— {dong}")
kiem("nến 00h: mở = phút đầu, đóng = phút cuối, cao/thấp đúng, khối lượng cộng dồn",
     n1.doc("o", 2) == 101.0 and n1.doc("c", 2) == 160.0 and n1.doc("h", 2) == 160.5
     and n1.doc("l", 2) == 100.5 and n1.doc("v", 2) == 120.0,
     f"— o {n1.doc('o', 2)} c {n1.doc('c', 2)} v {n1.doc('v', 2)}")
kiem("nến 01h THIẾU phút vẫn là một nến, mang đúng biên 01:00",
     dong[1][1] == NGAY + GIO and n1.doc("v", 1) == 10.0)
kiem("nến 00h đóng ĐÚNG lúc 01:00 (phút cuối của nó), không sớm hơn", dong[0][0] == NGAY + GIO)
kiem("nến 01h (dữ liệu thủng) đóng ở phút ĐẦU TIÊN có dữ liệu sau nó (03:01)",
     dong[1][0] == NGAY + 3 * GIO + 60)

print("\n▸ Không nhìn trước")
cn = CN.ChuoiNen("H1")
sma = cn.dang_ky("sma", {"chu_ky": 2})
for i in range(1, 60):
    m1(cn, NGAY + 60 * i, 10.0)
    cn.dong_neu_toi(NGAY + 60 * i)
kiem("giữa giờ (00:59) nến H1 chưa đóng → chỉ báo chưa biết gì", cn.so_nen == 0
     and CN.la_nan(sma(0)))
m1(cn, NGAY + 3600, 20.0)
kiem("phút 01:00 nạp vào nhưng CHƯA gọi đóng → vẫn chưa đóng", cn.so_nen == 0)
cn.dong_neu_toi(NGAY + 3600)
kiem("tới đúng 01:00 → đóng, giá đóng = phút cuối (20)", cn.so_nen == 1
     and cn.gia.doc("c") == 20.0)
cd = CN.ChuoiNen("D1")
for t in (NGAY + 23 * GIO + 3540, NGAY + 24 * GIO + 60):
    m1(cd, t, 5.0)
    cd.dong_neu_toi(t)
kiem("D1 cắt ở 00:00 UTC: nến 23:59 thuộc ngày cũ, 00:01 sang ngày mới",
     cd.so_nen == 1 and cd.cuoi.t == NGAY and cd.dang.t == NGAY + 24 * GIO)

# ================= 2. chỉ báo vs bản tính tay =================
print("\n▸ Chỉ báo tính dần = bản tính tay độc lập")
rd = random.Random(7)
N = 400
C, H, L, V = [], [], [], []
x = 100.0
for i in range(N):
    o_ = x
    x = max(1.0, x * (1 + rd.gauss(0, 0.01)))
    hi = max(o_, x) * (1 + abs(rd.gauss(0, 0.004)))
    lo = min(o_, x) * (1 - abs(rd.gauss(0, 0.004)))
    C.append(x)
    H.append(hi)
    L.append(lo)
    V.append(float(rd.randint(1, 1000)))

cn = CN.ChuoiNen("H1", giu=N)
DK = {
    "sma": cn.dang_ky("sma", {"chu_ky": 20}),
    "ema": cn.dang_ky("ema", {"chu_ky": 20}),
    "wma": cn.dang_ky("wma", {"chu_ky": 10}),
    "rma": cn.dang_ky("rma", {"chu_ky": 14}),
    "atr": cn.dang_ky("atr", {"chu_ky": 14, "kieu": "rma"}),
    "atr_sma": cn.dang_ky("atr", {"chu_ky": 14, "kieu": "sma"}),
    "atr_pt": cn.dang_ky("atr_pt", {"chu_ky": 14, "kieu": "rma"}),
    "rsi": cn.dang_ky("rsi", {"chu_ky": 14}),
    "macd": cn.dang_ky("macd", {"nhanh": 12, "cham": 26, "tin_hieu": 9, "dong": "macd"}),
    "macd_s": cn.dang_ky("macd", {"nhanh": 12, "cham": 26, "tin_hieu": 9, "dong": "tin_hieu"}),
    "macd_h": cn.dang_ky("macd", {"nhanh": 12, "cham": 26, "tin_hieu": 9,
                                  "dong": "histogram"}),
    "bb_t": cn.dang_ky("bollinger", {"chu_ky": 20, "do_lech": 2, "dai": "tren"}),
    "bb_d": cn.dang_ky("bollinger", {"chu_ky": 20, "do_lech": 2, "dai": "duoi"}),
    "std": cn.dang_ky("do_lech_chuan", {"chu_ky": 20}),
    "roc": cn.dang_ky("roc_pt", {"chu_ky": 20}),
    "dc_t": cn.dang_ky("donchian", {"chu_ky": 20, "bien": "tren"}),
    "dc_d": cn.dang_ky("donchian", {"chu_ky": 20, "bien": "duoi"}),
    "adx": cn.dang_ky("adx", {"chu_ky": 14}),
    "st_k": cn.dang_ky("stoch", {"chu_ky": 14, "chu_ky_d": 3, "dong": "k"}),
    "st_d": cn.dang_ky("stoch", {"chu_ky": 14, "chu_ky_d": 3, "dong": "d"}),
    "kl_tb": cn.dang_ky("kl_tb", {"chu_ky": 20}),
    "gtgd_tb": cn.dang_ky("gia_tri_gd_tb", {"chu_ky": 20}),
    "dong": cn.dang_ky("gia_dong", {}),
}
# 23 lời đăng ký nhưng chỉ 18 bản: ba đường MACD, hai dải Bollinger, hai biên Donchian, hai
# đường Stochastic dùng chung bản của mình; giá đóng dùng bản "giá" có sẵn của chuỗi.
kiem("hai điều kiện hỏi CÙNG chỉ báo cùng ô → dùng chung một bản",
     len(DK) == 23 and len(cn.chi_bao) == 18, f"— {len(DK)} lời đăng ký, {len(cn.chi_bao)} bản")
gt = {k: [] for k in DK}
for i in range(N):
    t = NGAY + (i + 1) * GIO
    cn.nap_m1(t, C[i - 1] if i else C[0], H[i], L[i], C[i], V[i])
    cn.dong_neu_toi(t)
    for k, f in DK.items():
        gt[k].append(f(0))


def sma_(xs, n):
    return [sum(xs[i - n + 1:i + 1]) / n if i >= n - 1 else math.nan for i in range(len(xs))]


def mu_(xs, n, alpha):
    ra, tb = [], math.nan
    dem = 0
    for i, x_ in enumerate(xs):
        if x_ != x_:
            ra.append(tb)
            continue
        dem += 1
        if dem < n:
            ra.append(math.nan)
        elif dem == n:
            tb = sum(v for v in xs[i - n + 1:i + 1]) / n
            ra.append(tb)
        else:
            tb = tb + alpha * (x_ - tb)
            ra.append(tb)
    return ra


def ema_(xs, n):
    return mu_(xs, n, 2.0 / (n + 1))


def rma_(xs, n):
    return mu_(xs, n, 1.0 / n)


def std_(xs, n):
    ra = []
    for i in range(len(xs)):
        if i < n - 1:
            ra.append(math.nan)
            continue
        w = xs[i - n + 1:i + 1]
        tb = sum(w) / n
        ra.append(math.sqrt(sum((v - tb) ** 2 for v in w) / n))
    return ra


TR = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))
                      for i in range(1, N)]
D = [math.nan] + [C[i] - C[i - 1] for i in range(1, N)]
lai = rma_([math.nan] + [max(d, 0.0) for d in D[1:]], 14)
lo_ = rma_([math.nan] + [max(-d, 0.0) for d in D[1:]], 14)
rsi = [math.nan if a != a else (100.0 if b == 0 else 100 - 100 / (1 + a / b))
       for a, b in zip(lai, lo_)]
e12, e26 = ema_(C, 12), ema_(C, 26)
mline = [a - b for a, b in zip(e12, e26)]
msig = ema_(mline, 9)
pdm, mdm = [math.nan], [math.nan]
for i in range(1, N):
    u, d_ = H[i] - H[i - 1], L[i - 1] - L[i]
    pdm.append(u if u > d_ and u > 0 else 0.0)
    mdm.append(d_ if d_ > u and d_ > 0 else 0.0)
trs = rma_([math.nan] + TR[1:], 14)
ps, ms = rma_(pdm, 14), rma_(mdm, 14)
dx = []
for a, b, c in zip(trs, ps, ms):
    if a != a:
        dx.append(math.nan)
        continue
    pi, mi = 100 * b / a, 100 * c / a
    dx.append(100 * abs(pi - mi) / (pi + mi) if pi + mi else 0.0)
adx = rma_(dx, 14)
stk = []
for i in range(N):
    if i < 13:
        stk.append(math.nan)
        continue
    hh, ll = max(H[i - 13:i + 1]), min(L[i - 13:i + 1])
    stk.append(50.0 if hh == ll else (C[i] - ll) / (hh - ll) * 100)
std20 = std_(C, 20)
wsum = 55.0
REF = {
    "sma": sma_(C, 20), "ema": ema_(C, 20), "rma": rma_(C, 14),
    "wma": [sum((j + 1) * C[i - 9 + j] for j in range(10)) / wsum if i >= 9 else math.nan
            for i in range(N)],
    "atr": rma_(TR, 14), "atr_sma": sma_(TR, 14),
    "atr_pt": [a / c * 100 for a, c in zip(rma_(TR, 14), C)],
    "rsi": rsi, "macd": mline, "macd_s": msig,
    "macd_h": [a - b for a, b in zip(mline, msig)],
    "bb_t": [m + 2 * s for m, s in zip(sma_(C, 20), std20)],
    "bb_d": [m - 2 * s for m, s in zip(sma_(C, 20), std20)],
    "std": std20,
    "roc": [(C[i] / C[i - 20] - 1) * 100 if i >= 20 else math.nan for i in range(N)],
    "dc_t": [max(H[i - 20:i]) if i >= 20 else math.nan for i in range(N)],
    "dc_d": [min(L[i - 20:i]) if i >= 20 else math.nan for i in range(N)],
    "adx": adx, "st_k": stk, "st_d": [math.nan] * 13 + sma_(stk[13:], 3),
    "kl_tb": sma_(V, 20), "gtgd_tb": sma_([c * v for c, v in zip(C, V)], 20),
    "dong": C,
}


def giong(a, b):
    if a != a or b != b:
        return (a != a) and (b != b)
    return abs(a - b) <= 1e-9 * max(1.0, abs(b))


for k in DK:
    lech = [i for i in range(N) if not giong(gt[k][i], REF[k][i])]
    so_co = sum(1 for v in gt[k] if v == v)
    kiem(f"{k:8s} khớp từng cây", not lech,
         f"— {so_co} giá trị" + (f", lệch từ cây {lech[0]}: {gt[k][lech[0]]} ≠ "
                                 f"{REF[k][lech[0]]}" if lech else ""))

print("\n▸ Ngưỡng sẵn sàng và đọc lùi")
kiem("SMA(20) NaN đúng 19 cây đầu, cây 20 có số",
     all(CN.la_nan(v) for v in gt["sma"][:19]) and not CN.la_nan(gt["sma"][19]))
kiem("Đổi giá %(20) cần 21 cây (so với 20 cây TRƯỚC)", CN.la_nan(gt["roc"][19])
     and not CN.la_nan(gt["roc"][20]))
kiem("Donchian(20) = 20 cây TRƯỚC cây đang xét → cần 21 cây",
     CN.la_nan(gt["dc_t"][19]) and not CN.la_nan(gt["dc_t"][20]))
kiem("lui = 1 đọc đúng cây trước, lui quá xa → NaN",
     DK["sma"](1) == gt["sma"][-2] and CN.la_nan(DK["sma"](N + 5)))
cn2 = CN.ChuoiNen("H1")
r = cn2.dang_ky("rsi", {"chu_ky": 5})
for i in range(30):
    m1(cn2, NGAY + (i + 1) * GIO, 100.0 + i)
    cn2.dong_neu_toi(NGAY + (i + 1) * GIO)
kiem("RSI chuỗi chỉ tăng = 100", r(0) == 100.0, f"— {r(0)}")
cn3 = CN.ChuoiNen("H1")
st = cn3.dang_ky("stoch", {"chu_ky": 5, "chu_ky_d": 3, "dong": "k"})
for i in range(10):
    m1(cn3, NGAY + (i + 1) * GIO, 50.0)
    cn3.dong_neu_toi(NGAY + (i + 1) * GIO)
kiem("Stochastic giá đứng im = 50 (không chia cho 0)", st(0) == 50.0)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
