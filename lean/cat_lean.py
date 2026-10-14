"""CẦU NỐI — bộ luật của Cat Studio chạy trong vòng lặp của LEAN.  (slice 2a · D-01…D-04)

VIỆC CỦA FILE NÀY
-----------------
Cho sơ đồ của Cat Studio chạy trên dữ liệu và chỉ báo của QuantConnect mà KHÔNG viết lại
một dòng luật nào. Bộ luật — đi cổng, rẽ nhánh, luật lùi, nuôi zone, vào/sửa lệnh, nhật
ký — vẫn là `cat_studio.bo_chay` nguyên văn. File này chỉ thay ỐNG NƯỚC:

    bộ chạy cũ (máy bạn)                    cầu nối (QuantConnect)
    -------------------------------------   ---------------------------------------------
    nến M1 từ MT5, tải trước cả năm          nến M1 từ QC, tới từng cây một
    chỉ báo tính trước cả mảng (numpy)       chỉ báo LEAN cập nhật từng nến, ĐẨY vào đây
    spread cố định 20 điểm                   spread THẬT của từng nến (ask − bid)
    khớp lệnh: đường đi 4 điểm               khớp lệnh: VẪN đường đi 4 điểm (slice 2a)

Slice 2a cố ý chỉ đổi DỮ LIỆU. Khớp lệnh đổi sang LEAN ở 2b — mỗi lần đổi một thứ thì số
lệch ở đâu biết ngay vì sao.

KHÔNG import QuantConnect ở đây. Lớp vỏ (`vo_qc.py`) giữ LEAN, đẩy nến và giá trị chỉ
báo vào `PhienQC`. Nhờ vậy file này chạy được ở máy không có LEAN — và
`tests/test_cat_lean.py` đối chiếu nó với bộ chạy cũ trên CÙNG dữ liệu, tới từng bản ghi
nhật ký.

HAI CHỖ KHÁC BỘ CHẠY CŨ, CẢ HAI CỐ Ý
-----------------------------------
1. **Nến trục xếp hàng.** Hai nến trục cùng "đóng" trong một nhịp M1 (dữ liệu nối lại sau
   một lỗ hổng, đúng phút cuối của ô kế tiếp) thì bộ cũ nhảy cóc qua cây trước — nó
   không bao giờ được chạy Entry. Ở đây cây nào cũng chạy đúng một lượt, theo thứ tự:
   đúng ý "mỗi nến trục có ĐÚNG MỘT nhịp" mà chính `ChuongTrinh._dung_truc` đã ghi. Lần
   đo slice 1 mất 243 lượt Entry vì đè nhau ở đúng chỗ này (D-03).
2. **Spread sống.** `CaiDatQC.spread_gia` đổi theo từng nến. Mọi chỗ đọc spread
   (`_gia_thoat`, `Ctx.ask`, `khop_lenh`) vẫn đọc qua đúng một cửa đó — chỉ đổi nguồn.
"""
import json
import math
import zlib
from collections import deque
from datetime import datetime, timezone

from cat_studio import bo_chay as bc
from cat_studio import core
from cat_studio import khop_lenh
from cat_studio import nhat_ky as nk
from cat_studio import so_lenh as sl
from cat_studio import tinh_toan as tt

NAN = float("nan")

#: Khung chạy được trên QC ở slice này: độ dài chia hết một giờ, nên biên nến KHÔNG phụ
#: thuộc múi giờ. H4/D1 thì khác — biên của chúng đặt theo giờ của sàn, mà giờ sàn MT5
#: và giờ dữ liệu QC không trùng nhau: chạy là ra nến H4 khác cây, lệch im lặng.
KHUNG_HO_TRO = ("M1", "M5", "M15", "M30", "H1")

#: Toán hạng giá → cột của nến, y như `ChuongTrinh.COT_GIA`.
COT_GIA = bc.ChuongTrinh.COT_GIA


class CaiDatQC(bc.CaiDat):
    """`CaiDat` với spread SỐNG.

    QC có giá Bid/Ask thật của từng nến, nên spread không còn là một ô nhập cố định.
    `spread_gia` vẫn là cửa DUY NHẤT mọi chỗ đọc — chỉ đổi nguồn, không đổi chỗ đọc."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.spread_hien_tai = 0.0

    @property
    def spread_gia(self):
        return self.spread_hien_tai


class CtxQC(bc.Ctx):
    """`Ctx` đọc giá HIỆN TẠI từ nến M1 vừa tới, thay vì tra mảng nến cả năm."""

    __slots__ = ("bid_hien", "ask_hien")

    def __init__(self, ct, so, ts):
        super().__init__(ct, so, ts)
        self.bid_hien = NAN
        self.ask_hien = NAN

    @property
    def bid(self):
        return self.bid_hien

    @property
    def ask(self):
        return self.ask_hien


class ChuongTrinhQC(bc.ChuongTrinh):
    """`ChuongTrinh` kiểu DÒNG CHẢY.

    Giữ nguyên mọi thứ không dính tới mảng: `so()`, `khoa()`, `doc_cot()`, luồng sơ đồ,
    bảng tham số, engine. Chỉ thay hai chỗ dựng mảng:

      * `_dung_truc` — không còn mảng M1 cả năm; trục quyết định LỚN DẦN từng nến.
      * `_xin_cot` / `_xin_cot_gia` — không TÍNH cột, chỉ GHI DANH khoá cần. LEAN tính,
        lớp vỏ đẩy giá trị vào, cột lớn dần theo trục.

    `doc_cot` của lớp cha đọc `self._cot[k][i]` — với list thay cho mảng numpy, nó chạy
    NGUYÊN VĂN, nên quy ước `shift` (nến[1] = lệch 0) không thể lệch với bộ cũ."""

    def __init__(self, doc, cd):
        super().__init__(doc, None, cd)
        self.khung_can = {k[1] for k in self._cot} | {self.tf5}

    def _dung_truc(self):
        for tab in core.TABS:
            bd = [s for s in (self.doc.get(tab) or {}).get("steps") or []
                  if core.is_start_step(s)]
            self.nhip[tab] = (bd[0].get("nhip") if bd else None) \
                or core.NHIP_MAC_DINH[tab]
            if self.nhip[tab] not in KHUNG_HO_TRO:
                raise bc.LoiChay(
                    f"Nhịp {self.nhip[tab]} của sơ đồ {tab} chưa chạy được trên "
                    f"QuantConnect — chỉ {', '.join(KHUNG_HO_TRO)}.")
        self.tf5 = self.nhip[core.TAB_ENTRY]
        # Trục quyết định: mỗi nến trục ĐÃ ĐÓNG một phần tử. `_thong_ke` đọc `nen5["t"]`,
        # `Ctx.gia_nen` đọc `nen5["h"]`/`["l"]` — cùng hình dạng với mảng của bộ cũ.
        self.nen5 = {"t": [], "o": [], "h": [], "l": [], "c": []}

    def _xin_cot(self, o, tab, st):
        ten = o["ten"]
        if ten in self.COT_GIA:
            return self._xin_cot_gia(o, st)
        if ten not in tt.BANG:
            return                              # toán hạng phi-chỉ-báo, tra lúc chạy
        self._ghi_danh(o, st)

    def _xin_cot_gia(self, o, st):
        self._ghi_danh(o, st)

    def _ghi_danh(self, o, st):
        nhan = f"[{core.step_title(st)}] " if st else ""
        try:
            k = self.khoa(o)
        except (ValueError, KeyError) as e:
            raise bc.LoiChay(f"{nhan}{e}")
        if k[1] not in KHUNG_HO_TRO:
            raise bc.LoiChay(
                f"{nhan}khung {k[1]} chưa chạy được trên QuantConnect — biên nến của nó "
                f"phụ thuộc múi giờ sàn. Dùng {', '.join(KHUNG_HO_TRO)}.")
        self._cot.setdefault(k, [])


def _gia_tri(x):
    """Giá trị chỉ báo đẩy vào → `float`. Chưa sẵn (`None`, NaN, vô cực) → NaN."""
    if x is None:
        return NAN
    x = float(x)
    return x if math.isfinite(x) else NAN


class PhienQC:
    """MỘT lần chạy trên QC — nến tới từng cây, luật y hệt `bo_chay.PhienChay`.

    Lớp vỏ gọi đúng hai cửa:

      * `nhan_khung(tf, …)` — một nến khung `tf` vừa ĐÓNG, kèm giá trị chỉ báo khung đó.
      * `mot_nhip(…)`       — một nến M1 (giá BID) vừa ĐÓNG. Toàn bộ bộ máy nằm ở đây.

    Thứ tự trong một nhịp — y `PhienChay.mot_nhip`, không được đổi:

        1. SÀN: lệnh chờ khớp, SL/TP bị chạm (`khop_lenh`).
        2. Mỗi nến trục vừa đóng → vào trục, mở nến mới cho engine.
        3. MANAGE một lượt cho từng lệnh đang sống (nếu tới nhịp Manage).
        4. ENTRY một lượt.
        5. Cổng zone không được xét tới → zone chết.
    """

    def __init__(self, doc, cd=None, giu_nhat_ky=False):
        cd = cd or CaiDatQC()
        doc = core.normalize_process(doc)
        self.cd, self.doc = cd, doc
        self.ct = ct = ChuongTrinhQC(doc, cd)
        self.so = so = sl.SoLenh()
        self.ctx = CtxQC(ct, so, ct.ts)

        self.tien = {"von": cd.deposit, "dinh": cd.deposit}
        ct.ghi_tien = self.ghi_tien
        ct.drawdown_pt = lambda: (0.0 if not self.tien["dinh"] else
                                  (self.tien["dinh"] - self.tien["von"])
                                  / self.tien["dinh"] * 100.0)

        self.nhip_m = core.TF_PHUT[ct.nhip[core.TAB_MANAGE]]
        self.buoc5 = core.TF_PHUT[ct.tf5] * 60
        self.j = -1
        self.i5 = -1
        self.mo_ho = 0
        self.gia_cuoi = NAN
        self.song, self.n_lenh = [], 0
        #: Nến trục đã đóng, chờ nhịp M1 kế tiếp xử lý: (t_mở, t_đóng, o, h, l, c).
        self.cho_truc = deque()
        #: Mỗi khung: các nến gần nhất `(t_đóng, {khoá: giá trị})`. Đủ dài để một nến trục
        #: đến trễ vài nhịp vẫn tra được giá trị ĐÚNG lúc nó đóng.
        self.moi_nhat = {tf: deque(maxlen=64) for tf in ct.khung_can}
        self.dem = {"m1": 0, "truc": 0, "entry": 0, "manage": 0, "entry_tre": 0}

        # Nhật ký: nén DẦN từng dòng — giữ 120 nghìn bản ghi dạng dict trong bộ nhớ của
        # gói Free là tự chuốc lấy hết RAM. `giu_nhat_ky=True` chỉ để bài kiểm so dict.
        self.nhat_ky = [] if giu_nhat_ky else None
        self.so_luot = 0
        self.byte_tho = 0
        self._nen = zlib.compressobj(6, zlib.DEFLATED, 31)      # 31 = định dạng gzip
        self._gz = []
        self._xong = False

    # ------------------------------------------------------------------ tiền
    def ghi_tien(self, l):
        cd = self.cd
        if l.gia_dong is None or l.gia_khop is None:
            return
        chieu = 1.0 if l.huong == sl.MUA else -1.0
        self.tien["von"] += ((l.gia_dong - l.gia_khop) * chieu * l.lot * cd.contract_size
                             - cd.commission * l.lot)
        self.tien["dinh"] = max(self.tien["dinh"], self.tien["von"])

    # ------------------------------------------------------------------ đầu vào
    def nhan_khung(self, tf, t_mo, t_dong, o, h, l, c, gia_tri=None):
        """Một nến khung `tf` vừa ĐÓNG (giá BID), kèm giá trị chỉ báo của khung đó."""
        if tf in self.moi_nhat:
            gt = {k: _gia_tri(v) for k, v in (gia_tri or {}).items()}
            for ten, cot in COT_GIA.items():
                gt[(ten, tf, None, None)] = float({"o": o, "h": h, "l": l, "c": c}[cot])
            self.moi_nhat[tf].append((t_dong, gt))
        if tf == self.ct.tf5:
            self.cho_truc.append((int(t_mo), int(t_dong), float(o), float(h), float(l),
                                  float(c)))

    def _tra(self, tf, t_dong, k):
        """Giá trị khoá `k` của nến khung `tf` ĐÃ ĐÓNG gần nhất, đóng lúc ≤ `t_dong`.

        Đúng phép `tinh_toan.theo_truc` của bộ cũ, chỉ là làm từng nến một."""
        for t, gt in reversed(self.moi_nhat.get(tf, ())):
            if t <= t_dong:
                return gt.get(k, NAN)
        return NAN

    def _vao_truc(self, nen):
        """Một nến trục vừa đóng → thêm vào trục, chép giá trị mọi cột tại lúc nó đóng."""
        t_mo, t_dong, o, h, l, c = nen
        ct = self.ct
        n5 = ct.nen5
        truoc = n5["t"][-1] if n5["t"] else None
        for cot, v in (("t", t_mo), ("o", o), ("h", h), ("l", l), ("c", c)):
            n5[cot].append(v)
        for k, cot in ct._cot.items():
            cot.append(self._tra(k[1], t_dong, k))
        self.i5 += 1
        self.dem["truc"] += 1
        # Khoảng trống > 2 bước nến trục → chợ đã đóng: zone chết dù cổng vẫn qua.
        return truoc is not None and (t_mo - truoc) > 2 * self.buoc5

    def mot_nhip(self, t_dong, o, h, l, c, spread=0.0, ask=None):
        """Một nến M1 (giá BID) vừa ĐÓNG lúc `t_dong` (giây)."""
        ct, so, ctx, cd = self.ct, self.so, self.ctx, self.cd
        self.j += 1
        self.dem["m1"] += 1
        cd.spread_hien_tai = max(0.0, float(spread))
        ctx.bid_hien = float(c)
        ctx.ask_hien = float(ask) if ask is not None else float(c) + cd.spread_hien_tai
        self.gia_cuoi = float(c)

        # Đồng bộ đầu nến: lệnh sinh ở nhịp TRƯỚC giờ mới được xét khớp.
        if len(so.lenh) != self.n_lenh:
            self.song.extend(so.lenh[self.n_lenh:])
            self.n_lenh = len(so.lenh)
        if self.song:
            self.song[:] = [x for x in self.song if x.con_song]

        san_sang = []
        while self.cho_truc and self.cho_truc[0][1] <= t_dong:
            san_sang.append(self.cho_truc.popleft())
        ctx.j = self.j
        ctx.i = max(self.i5 + len(san_sang), 0)

        # ---- 1. SÀN ----
        nen = {"o": o, "h": h, "l": l, "c": c}
        for x in list(self.song):
            for e in khop_lenh.trong_nen(x, nen, cd.spread_gia):
                if e["loai"] == "khop":
                    so.khop(x, e["gia"], ctx.i, ctx.j)
                else:
                    so.dong(x, e["gia"], ctx.i, e["ly_do"])
                    self.ghi_tien(x)
                    if e.get("mo_ho"):
                        self.mo_ho += 1

        if self.i5 + len(san_sang) < 0:
            return                              # chưa có nến trục nào đóng — chưa quyết gì

        la_nhip_m = self.nhip_m <= 1 or int(t_dong) % (self.nhip_m * 60) == 0
        if not san_sang:
            if la_nhip_m:
                self._manage()
            return

        for so_thu_tu, nen5 in enumerate(san_sang):
            # ---- 2. nến trục mới ----
            co_lo_hong = self._vao_truc(nen5)
            ctx.i = self.i5
            ctx.co_lo_hong = co_lo_hong
            ctx.lenh = None
            ctx.zone_da_xet = False
            ct.engine.moi_nen(ctx)
            if nen5[1] < t_dong:
                self.dem["entry_tre"] += 1
            # ---- 3. MANAGE — đúng một lần mỗi nhịp M1, trước Entry của nến mới nhất ----
            if so_thu_tu == len(san_sang) - 1 and la_nhip_m:
                self._manage()
            # ---- 4. ENTRY ----
            ctx.tab = core.TAB_ENTRY
            self.dem["entry"] += 1
            r = bc._chay_so_do(core.TAB_ENTRY, ctx)
            if r:
                self._ghi_luot(r)
            # ---- 5. cổng zone không được xét tới → zone chết ----
            if not ctx.zone_da_xet and ct.co_cong_zone:
                so.dong_zone()

    def _manage(self):
        ctx = self.ctx
        ctx.tab = core.TAB_MANAGE
        for x in list(self.song):
            if not x.con_song:
                continue                        # vừa bị chính lượt Manage trước đó đóng
            ctx.lenh = x
            self.dem["manage"] += 1
            r = bc._chay_so_do(core.TAB_MANAGE, ctx)
            if r:
                self._ghi_luot(r)
        ctx.lenh = None

    # ------------------------------------------------------------------ nhật ký
    def _ghi_dong(self, d):
        b = (json.dumps(d, ensure_ascii=False, separators=(",", ":"))
             + "\n").encode("utf-8")
        self.byte_tho += len(b)
        self._gz.append(self._nen.compress(b))

    def _ghi_luot(self, r):
        r["seq"] = self.so_luot
        self.so_luot += 1
        if self.nhat_ky is not None:
            self.nhat_ky.append(r)
        self._ghi_dong({"loai": "luot", **r})

    # ------------------------------------------------------------------ kết sổ
    def ket_thuc(self, giay=None):
        """Hết dữ liệu → chốt sổ, ghi lệnh + meta vào nhật ký, trả bảng tổng kết.

        `giay` = thời gian chạy trên cloud, lớp vỏ đo rồi đưa vào — meta mang nó cùng bộ
        đếm, để app đọc về là có đủ những gì dòng tổng kết trên log của QC có.

        Định dạng file y `nhat_ky.ghi` (meta · lệnh · lượt) — `nhat_ky.doc_file` đọc
        theo khoá `loai` của từng dòng nên thứ tự dòng không quan trọng."""
        if self._xong:
            return self.thong_ke
        ct, so, ctx = self.ct, self.so, self.ctx
        for x in list(so.dang_song()):
            so.dong(x, self.gia_cuoi if x.da_khop else None, ctx.i,
                    "het_du_lieu" if x.da_khop else "huy")
            self.ghi_tien(x)
        tk, _ = bc._thong_ke(so, self.cd, ct)
        tk["nen_mo_ho"] = self.mo_ho
        tk["so_luot"] = self.so_luot
        for x in so.lenh:
            self._ghi_dong({"loai": "lenh", "lenh": x.tom_tat()})
        cd = self.cd
        self._ghi_dong({
            "loai": "meta", "phien_ban": core.PHIEN_BAN, "nguon": "QuantConnect",
            "luc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "van_tay": nk._van_tay(self.doc),
            "symbol": cd.symbol, "tf": ct.tf5,
            "so_nen_m1": self.dem["m1"], "so_nen_truc": len(ct.nen5["t"]),
            "spread_diem": "thật (Bid/Ask từng nến)", "point": cd.point,
            "contract_size": cd.contract_size, "deposit": cd.deposit,
            "commission": cd.commission, "thong_ke": tk, "doc": self.doc,
            "dem": dict(self.dem), "giay_chay": giay,
        })
        self._gz.append(self._nen.flush())
        self.thong_ke = tk
        self._xong = True
        return tk

    def nhat_ky_gz(self):
        """Nhật ký đã nén (gzip). Gọi sau `ket_thuc()`."""
        return b"".join(self._gz)

    def ten_file(self):
        """Khoá Object Store — chung một hàm với phía app đọc về (`nhat_ky.khoa_qc`)."""
        return nk.khoa_qc(self.doc)

    def dong_tong_ket(self, nhan, giay, luu):
        """Vài dòng ngắn cho log của QC — mỗi dòng một ý, đủ ngắn để không bị cắt."""
        gz = sum(len(x) for x in self._gz)
        return dong_ket_qua(nhan, self.thong_ke, self.dem, self.ct.tf5, giay) + [
            f"CAT STUDIO · nhật ký {_so(self.so_luot)} lượt = "
            f"{_so(self.byte_tho / 1e6, 1)} MB → nén {_so(gz / 1e6, 2)} MB · "
            f"Object Store: {luu}",
        ]


def dong_ket_qua(nhan, tk, d, tf, giay):
    """Hai dòng kết quả — CHUNG cho log của QC và cho `tools/chay_qc.py` (dựng lại từ meta
    của nhật ký tải về), để hai nơi không thể kể hai câu chuyện khác nhau về một lượt."""
    return [
        f"CAT STUDIO · {nhan} · {_so(tk['so_lenh'])} lệnh ({_so(tk['so_dong'])} đóng · "
        f"{_so(tk['so_huy'])} huỷ) · thắng {tk['thang']}/{tk['thua']} = "
        f"{_so(tk['ty_le_thang'], 1)}% · tổng {_so(tk['tong_R'], 2)}R · "
        f"DD {_so(tk['drawdown_pt'], 2)}% · nến mơ hồ {tk['nen_mo_ho']}",
        f"CAT STUDIO · {_so(d['m1'])} nến M1 · {_so(d['truc'])} nến {tf} · "
        f"lượt Entry {_so(d['entry'])} (trễ {_so(d['entry_tre'])}) · "
        f"lượt Manage {_so(d['manage'])} · chạy {_so(giay or 0, 1)} giây",
    ]


def _so(x, le=0):
    """Số kiểu Việt: 354.503 · 47,3 · −8,4."""
    s = f"{x:,.{le}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return s.replace("-", "−")
