"""SÀN GIẢ cho bộ máy 5 trạm — đứng vào chỗ QuantConnect trong bài kiểm.  (D-10, phần 3)

Làm đúng phần việc mà trên QC do QC làm: đổi "% vốn" ra số lượng, giữ tiền và vị thế, khớp
lệnh. Cố ý ĐƠN GIẢN và nói rõ giả định — nó không phải mô hình khớp lệnh của game (đó là việc
của QC), chỉ cần đủ thật để bộ máy có một tài khoản biết phản hồi:

  · lệnh thị trường khớp ở giá MỞ của phút kế tiếp (quyết lúc đóng nến, khớp ở phút sau);
  · lệnh giới hạn khớp khi giá chạm mức chờ, ở mức chờ hoặc giá mở nếu mở đã tốt hơn;
  · lệnh chờ stop khớp khi giá chạm mức chờ, ở mức chờ hoặc giá mở nếu mở đã vượt qua;
  · không phí, không trượt giá, số lượng lẻ được (như crypto).

Cũng chứa máy dựng DỮ LIỆU GIẢ (nến M1 nhiều mã, có xu hướng) và vòng `chay(...)` nối sàn với
bộ máy y như vỏ QC sẽ nối ở phần 4.
"""
import math
import random

from cat_studio.bo_may import BoMay

NGAY = 1704067200          # 2024-01-01 00:00 UTC (thứ Hai)
PHUT, GIO, NGAY_S = 60, 3600, 86400


class SanGia:
    def __init__(self, von=10_000.0):
        self.tien = float(von)
        self.giu = {}          # mã → {"sl", "gia_von"}
        self.cho = {}          # id → {"ma", "kieu", "sl", "gia"}
        self.gia = {}          # mã → giá đóng gần nhất

    def von(self):
        return self.tien + sum(g["sl"] * self.gia[m] for m, g in self.giu.items())

    def tk(self):
        v = self.von()
        return {"von": v, "tien_mat": self.tien,
                "giu": {m: {"pt": g["sl"] * self.gia[m] / v * 100.0, "gia_von": g["gia_von"],
                            "sl": g["sl"]} for m, g in self.giu.items() if g["sl"]},
                "lenh_cho": {lid: {"ma": l["ma"], "pt": l["sl"] * self.gia[l["ma"]] / v * 100.0}
                             for lid, l in self.cho.items()}}

    def nhan(self, y):
        if y["loai"] == "huy":
            self.cho.pop(y["id"], None)
            return
        gia = self.gia[y["ma"]]
        sl = y["pt"] / 100.0 * self.von() / gia
        self.cho[y["id"]] = {"ma": y["ma"], "kieu": y["kieu"], "sl": sl, "gia": y.get("gia")}

    def _khop(self, ma, sl, px):
        g = self.giu.setdefault(ma, {"sl": 0.0, "gia_von": 0.0})
        cu = g["sl"]
        moi = cu + sl
        if cu == 0 or (cu > 0) == (sl > 0):                 # mở thêm cùng chiều
            g["gia_von"] = (cu * g["gia_von"] + sl * px) / moi if moi else 0.0
        elif (moi > 0) != (cu > 0) and abs(moi) > 1e-12:    # đảo chiều
            g["gia_von"] = px
        g["sl"] = 0.0 if abs(moi) < 1e-12 else moi
        self.tien -= sl * px

    def khop_phut(self, t, nen):
        """Xét lệnh chờ với nến M1 vừa đóng lúc t; trả [(id, t, sl, giá)] đã khớp."""
        ra = []
        for lid in sorted(self.cho):
            l = self.cho[lid]
            n = nen.get(l["ma"])
            if n is None:
                continue
            o, h, lo = n[0], n[1], n[2]
            mua = l["sl"] > 0
            px = None
            if l["kieu"] == "thi_truong":
                px = o
            elif l["kieu"] == "gioi_han":
                if mua and lo <= l["gia"]:
                    px = min(o, l["gia"])
                elif not mua and h >= l["gia"]:
                    px = max(o, l["gia"])
            else:
                if mua and h >= l["gia"]:
                    px = max(o, l["gia"])
                elif not mua and lo <= l["gia"]:
                    px = min(o, l["gia"])
            if px is not None:
                self._khop(l["ma"], l["sl"], px)
                ra.append((lid, t, l["sl"], px))
                del self.cho[lid]
        for m, n in nen.items():
            self.gia[m] = n[3]
        return ra


def du_lieu(xu_huong, so_ngay, seed=1, gio_bat_dau=NGAY, gia0=100.0, nhieu=0.0008,
            ngay_doi=None, sap=None):
    """Nến M1 24/7 cho mỗi mã. `xu_huong[mã]` = % trôi MỖI NGÀY (âm = giảm).
    `ngay_doi = {mã: (ngày, % mới)}` đổi xu hướng giữa chừng.
    `sap = {mã: (phút thứ mấy, %)}` giá nhảy một phát trong đúng một phút — cú sập cho ④."""
    rd = random.Random(seed)
    ra = {}
    so_phut = so_ngay * 1440
    for ma in sorted(xu_huong):
        p, ds = gia0, []
        for i in range(so_phut):
            tt = xu_huong[ma]
            if ngay_doi and ma in ngay_doi and i >= ngay_doi[ma][0] * 1440:
                tt = ngay_doi[ma][1]
            troi = tt / 100.0 / 1440.0
            o = p
            p = max(0.01, p * (1.0 + troi + rd.gauss(0.0, nhieu)))
            if sap and ma in sap and i == sap[ma][0]:
                p *= 1.0 + sap[ma][1] / 100.0
            h = max(o, p) * (1.0 + abs(rd.gauss(0.0, nhieu / 3)))
            lo = min(o, p) * (1.0 - abs(rd.gauss(0.0, nhieu / 3)))
            ds.append((gio_bat_dau + (i + 1) * PHUT, o, h, lo, p, float(rd.randint(1, 100))))
        ra[ma] = ds
    return ra


def chay(may, dl, von=10_000.0, bat_dau_t=None, den_t=None, theo_doi=None):
    """Chạy cỗ máy trên dữ liệu giả. Trả (bộ máy, sàn, mọi ý định theo bước)."""
    ma = sorted(dl)
    bm = BoMay(may, ma, von, bat_dau_t)
    san = SanGia(von)
    moc = {}
    for m in ma:
        for n in dl[m]:
            if den_t is not None and n[0] > den_t:
                break
            moc.setdefault(n[0], {})[m] = n[1:]
    y_dinh = []
    for t in sorted(moc):
        nen = moc[t]
        for k in san.khop_phut(t, nen):
            bm.nhan_khop(*k)
        ys = bm.buoc(t, nen, san.tk())
        for y in ys:
            san.nhan(y)
        if ys:
            y_dinh.append((t, ys))
        if theo_doi:
            theo_doi(bm, san, t)
    return bm, san, y_dinh


def gan_bang(a, b, sai=1e-6):
    return abs(a - b) <= sai * max(1.0, abs(a), abs(b))


def la_nan(x):
    return isinstance(x, float) and math.isnan(x)
