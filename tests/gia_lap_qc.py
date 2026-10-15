"""GIẢ LẬP QuantConnect cho bài kiểm cầu nối — dữ liệu giả + cách LEAN gộp nến.

Không phải bài kiểm (không nằm trong `chay_tat_ca.py`). Cố ý KHÔNG import gì của repo:
`test_cat_lean.py` gọi nó hai lần — một lần với bộ luật trong repo, một lần trong một
Python SẠCH chỉ có gói `dist/lean/` — nên mọi module cần dùng đều được TRUYỀN VÀO.

GIẢ ĐỊNH VỀ LEAN, NÓI RÕ RA
---------------------------
Mỗi khi một nến M1 tới, `QuoteBarConsolidator` làm hai việc, TRƯỚC `on_data`:

  1. `Update`: nến mới thuộc ô sau ô đang gộp → phát ô đang gộp, mở ô mới.
  2. `Scan` ở giờ ĐÓNG của nến M1: ô đang gộp đã hết giờ → phát luôn.

Nếu LEAN thật làm khác (phát SAU `on_data`), mọi lượt Entry trên QC sẽ chạy trễ một nhịp —
và bộ đếm "trễ" trong dòng tổng kết sẽ xấp xỉ số nến trục thay vì vài chục. Giả định này
vì thế không nằm im: lần chạy thật nào cũng tự khai nó đúng hay sai.
"""
import random

#: Đúng `tinh_toan.DTYPE` — chép số chứ không import, vì file này không được chạm repo.
DTYPE = [("t", "<i8"), ("o", "<f8"), ("h", "<f8"), ("l", "<f8"), ("c", "<f8"),
         ("vol", "<i8")]


def du_lieu(np, seed=7, ngay=12):
    """Nến M1 giả, vàng ~2000: xen kẽ yên / động / có xu hướng để sơ đồ mẫu đi đủ nhánh.

    Có nghỉ phiên 21:00–22:00 mỗi ngày, nghỉ cuối tuần, và thủng LẺ từng phút. Không bao
    giờ thủng hai phút liền — để không tạo ca "hai nến trục cùng đóng một nhịp" (ca đó
    có bài riêng, vì bộ cũ và cầu nối CỐ Ý xử lý khác nhau)."""
    rd = random.Random(seed)
    t, gia = 1735776000, 2000.0              # 2025-01-02 00:00 UTC
    che_do, con_lai, xu, bo_truoc = "yen", 0, 0.0, False
    ra = []
    for _ in range(ngay * 1440):
        t += 60
        mo = t - 60                          # nghỉ phiên tính theo giờ MỞ nến
        thu = (mo // 86400 + 3) % 7          # 0 = thứ Hai (1970-01-01 là thứ Năm)
        gio = (mo % 86400) // 3600
        if thu == 5 and gio >= 21 or thu == 6 or (thu == 0 and gio < 22):
            continue                         # cuối tuần
        if gio == 21:
            continue                         # nghỉ giữa phiên
        if rd.random() < 0.004 and not bo_truoc:
            bo_truoc = True
            continue                         # thủng lẻ một phút
        bo_truoc = False
        if con_lai <= 0:
            che_do = rd.choice(["yen", "yen", "dong", "xu"])
            con_lai = rd.randint(40, 240)
            xu = rd.choice([-1, 1]) * rd.uniform(0.05, 0.25)
        con_lai -= 1
        bien = {"yen": 0.12, "dong": 0.9, "xu": 0.35}[che_do]
        d = (xu if che_do == "xu" else 0.0) + rd.gauss(0, bien)
        o, c = gia, gia + d
        h = max(o, c) + abs(rd.gauss(0, bien * 0.6))
        lo = min(o, c) - abs(rd.gauss(0, bien * 0.6))
        ra.append((mo, round(o, 2), round(h, 2), round(lo, 2), round(c, 2), 1))
        gia = c
    return np.array(ra, dtype=DTYPE)


def chay_qc(cl, core, tt, doc, nen1, spread, giu_nhat_ky=True, them=None):
    """Chạy `doc` qua `cl.PhienQC` y như vỏ QC sẽ chạy, với giá trị chỉ báo tính bằng `tt`.

    Chỉ báo lấy từ `tinh_toan` của chính bộ cũ — tức bài này kiểm ỐNG NƯỚC (nhịp, hàng đợi,
    trục, khớp, nhật ký), không kiểm chỉ báo LEAN. Chỉ báo LEAN được soát riêng bằng
    `quantconnect-stubs` và đối chiếu trên QC thật."""
    p = cl.PhienQC(doc, cl.CaiDatQC(), giu_nhat_ky=giu_nhat_ky)
    khoa = list(p.ct._cot)
    khung = sorted(p.ct.khung_can, key=lambda x: core.TF_PHUT[x])
    gt = {}
    for tf in khung:
        n = tt.gop(nen1, tf)
        gt[tf] = (n, {k: tt.tinh(k[0], n, k[2], method=k[3] or "SMA")
                      for k in khoa if k[1] == tf and k[0] in tt.BANG})
    da_phat = {tf: 0 for tf in khung}
    lam = {tf: None for tf in khung}          # ô đang gộp: giờ mở

    def phat(tf):
        n, cot = gt[tf]
        i = da_phat[tf]
        da_phat[tf] += 1
        b = n[i]
        assert int(b["t"]) == lam[tf], (tf, int(b["t"]), lam[tf])
        p.nhan_khung(tf, int(b["t"]), int(b["t"]) + core.TF_PHUT[tf] * 60,
                     float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]),
                     {k: float(v[i]) for k, v in cot.items()})

    for r in nen1:
        t = int(r["t"])
        for tf in khung:                      # 1. Update
            if tf == "M1":
                continue
            b = core.TF_PHUT[tf] * 60
            if lam[tf] is not None and t >= lam[tf] + b:
                phat(tf)
                lam[tf] = None
            if lam[tf] is None:
                lam[tf] = t // b * b
        for tf in khung:                      # 2. Scan lúc nến M1 đóng
            if tf == "M1":
                continue
            b = core.TF_PHUT[tf] * 60
            if lam[tf] is not None and t + 60 >= lam[tf] + b:
                phat(tf)
                lam[tf] = None
        if "M1" in khung:
            lam["M1"] = t
            phat("M1")
            lam["M1"] = None
        c = float(r["c"])
        p.mot_nhip(t + 60, float(r["o"]), float(r["h"]), float(r["l"]), c,
                   spread, c + spread)
    p.ket_thuc(them=them)
    return p
