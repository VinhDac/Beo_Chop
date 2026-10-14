"""BỘ MÁY CHẠY CỖ MÁY 5 TRẠM.  (D-10, phần 3)

    nến M1 của mọi mã ─┐
    tài khoản (từ QC) ─┼─► BoMay.buoc(t, …) ─► ý định lệnh (đặt / huỷ) ─► QC đổi ra số lượng,
                       │        │                                         đặt lệnh, khớp
                       │        └─► nhật ký: mỗi lượt chạy một bản ghi
    lệnh đã khớp ──────┘

Bộ máy KHÔNG tính số lượng, KHÔNG khớp lệnh, KHÔNG giữ tiền: nó chỉ quyết MỤC TIÊU (% vốn
cho từng mã) và Ý ĐỊNH lệnh (loại lệnh, bao nhiêu % vốn, giá chờ). Số lượng, lô tối thiểu,
ký quỹ, phí, trượt giá là việc của QuantConnect (D-10 ý 2). Nhờ vậy cùng một file chạy được
cả trong `main.py` trên QC lẫn trong bài kiểm với sàn giả.

MỘT BƯỚC (một phút) — thứ tự y khung thuật toán của QC:

    nạp nến M1 → đóng nến khung lớn tới giờ → tài khoản → (còn khởi động thì dừng ở đây)
    → lệnh hết hạn → tín hiệu hết hạn → ① Chọn mã → ② Tín hiệu → ③ Chia vốn → ④ Rủi ro
    → mục tiêu đổi thì huỷ lệnh chờ cũ → ⑤ Khớp lệnh

LUẬT LÙI (y bộ chạy cũ, core.md §12.5a): cổng trượt thì lùi về ngã rẽ gần nhất còn nhánh chưa
thử — trừ khi lượt này đã qua một khối Làm, khi đó hết lượt.

Không nhìn trước: trạm chỉ đọc nến ĐÃ ĐÓNG (`chuoi_nen`), và chạy ở lúc nến khung của nó vừa
đóng. Không ngẫu nhiên, duyệt mã theo thứ tự cố định: chạy lại cùng dữ liệu ra y hệt.
"""
import json
import math
from datetime import datetime, timezone

from . import core
from . import may as M
from . import tram as T
from .chuoi_nen import ChuoiNen, KHUNG_GIAY, NAN, la_nan

#: Lệch giữa mục tiêu và đang giữ dưới ngưỡng này (% vốn) thì coi như đã tới — không đặt lệnh
#: lắt nhắt. Đúng ý `MinimumOrderMarginPortfolioPercentage` (0,1%) của khung QC.
NGUONG_LECH_PT = 0.1

#: Mỗi lượt chạy sơ đồ đi tối đa ngần này bước — chốt chặn vòng lặp nối ngược.
TRAN_BUOC = core.MAX_PROCESS_STEPS


class LoiMay(Exception):
    """Lỗi ném ra cho người chơi đọc — câu tiếng Việt, nói rõ phải sửa gì."""


def _js(x):
    """Số cho nhật ký: NaN/inf không qua nổi JSON, và `None` mới đúng nghĩa "chưa có"."""
    if isinstance(x, bool) or x is None:
        return x
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else round(f, 10)


def _so_sanh(a, phep, b):
    """NaN ở bất kỳ vế nào → False (cổng trượt), không nổ."""
    if la_nan(a) or la_nan(b):
        return False
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b,
            "==": a == b, "!=": a != b}[phep]


def _ngay(t):
    return datetime.fromtimestamp(int(t), tz=timezone.utc)


def _moc_lich(t, lich):
    """Khoá của "kỳ" chứa thời điểm t: đổi khoá = sang kỳ mới = tới lịch chạy."""
    d = _ngay(t)
    if lich == "moi_ngay":
        return (d.year, d.month, d.day)
    if lich == "dau_tuan":
        return tuple(d.isocalendar()[:2])
    if lich == "dau_thang":
        return (d.year, d.month)
    return None


def _so_nen_can(ten, o, so):
    """Một đại lượng cần bao nhiêu nến ĐÃ ĐÓNG mới ra số (không kể `lui`)."""
    ck = int(so(o["chu_ky"])) if "chu_ky" in o else 0
    if ten == "macd":
        return int(so(o["cham"])) + int(so(o["tin_hieu"]))
    if ten in ("roc_pt", "donchian"):
        return ck + 1
    if ten == "rsi":
        return ck + 1
    if ten == "adx":
        return 2 * ck + 1
    if ten == "stoch":
        return ck + int(so(o["chu_ky_d"]))
    return max(ck, 1)


def nen_khoi_dong(may):
    """{khung: số nến ĐÃ ĐÓNG cần có} để MỌI chỉ báo của cỗ máy có số ngay lượt đầu."""
    m = M.chuan_hoa(may)
    ts = M.bang_tham_so(m)

    def so(v):
        return float(ts[v]) if isinstance(v, str) else float(v)

    can = {}
    for k in T.TRAM_KEYS:
        for st in m["tram"][k]["steps"]:
            ds = [c.get("trai") for c in st.get("conditions") or []]
            ds += [c["phai"] for c in st.get("conditions") or []
                   if isinstance(c.get("phai"), dict) and c["phai"].get("ten")]
            if isinstance(st.get("diem"), dict):
                ds.append(st["diem"])
            if st.get("type") == "dat_ty_trong" and st.get("cach") == "rui_ro_ngang":
                ds.append({"ten": "atr_pt", "khung": st["khung"], "chu_ky": st["chu_ky"]})
            for o in ds:
                d = T.TOAN_HANG_THEO_KEY.get((o or {}).get("ten"))
                if not d or "khung" not in d["tham_so"]:
                    continue
                n = _so_nen_can(o["ten"], o, so) + int(so(o.get("lui", 0))) + 1
                can[o["khung"]] = max(can.get(o["khung"], 0), n)
    return can


def can_khoi_dong(may):
    """Cỗ máy cần bao nhiêu GIÂY giao dịch LIÊN TỤC trước lúc bắt đầu — chỉ báo dài nhất ×
    khung của nó, cộng một nến dự phòng. Thị trường có giờ nghỉ: dùng `giay_lich_khoi_dong`."""
    return max([n * KHUNG_GIAY[k] for k, n in nen_khoi_dong(may).items()] or [0])


#: Lịch giao dịch của từng loại thị trường: (số giờ giao dịch mỗi ngày giao dịch, số ngày
#: giao dịch mỗi tuần). Đủ để quy "N nến H1" ra số ngày LỊCH cần lùi lại để khởi động.
LICH_THI_TRUONG = {"forex": (24.0, 5), "cfd": (23.0, 5), "co_phieu": (6.5, 5),
                   "crypto": (24.0, 7)}


def giay_lich_khoi_dong(may, loai):
    """Số GIÂY LỊCH cần lùi lại trước ngày bắt đầu (cho `set_warm_up` của QC), tính theo giờ
    mở cửa của loại thị trường, cộng 50% dự phòng cho ngày lễ và phiên ngắn.

    Cổ phiếu Mỹ chỉ có ~7 nến H1 mỗi ngày: SMA 50 nến H1 cần ~7 ngày giao dịch ≈ 10 ngày lịch
    — tính theo giờ liên tục (≈ 2 ngày) là chỉ báo câm cả tuần đầu."""
    gio, ngay_tuan = LICH_THI_TRUONG.get(loai, (24.0, 5))
    can = 0.0
    for k, n in nen_khoi_dong(may).items():
        if k == "D1":
            ngay_gd = n
        else:
            moi_ngay = max(1, math.ceil(gio * 3600 / KHUNG_GIAY[k]))
            ngay_gd = math.ceil(n / moi_ngay)
        can = max(can, ngay_gd * 7.0 / ngay_tuan * 1.5 * 86400)
    return int(math.ceil(can))


class _TinHieu:
    __slots__ = ("huong", "het_han", "tin_cay", "trong_so", "t")

    def __init__(self, huong, het_han, tin_cay, trong_so, t):
        self.huong, self.het_han, self.tin_cay, self.trong_so, self.t = (
            huong, het_han, tin_cay, trong_so, t)

    def chu_ky(self):
        """Dấu vân tay để biết tín hiệu có ĐỔI không. Phát lại y hệt chỉ để gia hạn thì không
        tính là đổi — nếu tính, trạm ③ cân lại mỗi nến và đặt lệnh lắt nhắt theo giá."""
        return (self.huong, self.tin_cay, self.trong_so)


class BoMay:
    """Chạy MỘT cỗ máy trên MỘT danh sách mã, từ đầu tới cuối một lượt backtest.

    `danh_sach_ma` = mọi mã của màn chơi (phạm vi mặc định của trạm ①).
    `bat_dau_t` = mốc hết khởi động (unix giây): trước mốc này chỉ nạp nến cho chỉ báo đủ dữ
    liệu, không trạm nào chạy và không lệnh nào được đặt — đúng `set_warm_up` của QC."""

    def __init__(self, may, danh_sach_ma, von_dau=10_000.0, bat_dau_t=None):
        loi = [p for p in M.soat(may) if p["severity"] == "error"]
        if loi:
            ds = "\n".join(f"· {T.nhan_tram(p['tram']) + ': ' if p['tram'] else ''}"
                           f"{p['message']}" for p in loi[:4])
            them = f"\n… và {len(loi) - 4} lỗi nữa." if len(loi) > 4 else ""
            raise LoiMay(f"Cỗ máy còn {len(loi)} lỗi, chưa chạy được:\n{ds}{them}")
        self.may = M.chuan_hoa(may)
        self.ts = M.bang_tham_so(self.may)
        self.ma = [str(x) for x in danh_sach_ma]
        if not self.ma:
            raise LoiMay("Màn chơi không có mã nào để chạy.")
        self.von_dau = float(von_dau)
        self.bat_dau_t = int(bat_dau_t) if bat_dau_t is not None else None

        self._dung_luong()
        self._dung_chuoi()

        # ---- trạng thái chạy ----
        self.t = None
        self.da_khoi_dong = False
        self.ro = []                         # rổ hiện tại (thứ tự = thứ tự Gom)
        self.diem = {}
        self.tin_hieu = {}                   # mã → _TinHieu
        self.muc_tieu = {}                   # mã → % vốn (có dấu)
        self.t_doi_muc_tieu = {}
        #: Mã có mục tiêu CHƯA KHỚP XONG — chỉ những mã này ⑤ mới xét. Tới mục tiêu rồi thì
        #: bỏ ra, để giá trôi nhẹ sau đó không đẻ lệnh lắt nhắt ngược chiều liên tục (đúng
        #: luật khung QC: mục tiêu đã tới thì xoá, ③/④ phát mục tiêu mới mới giao dịch lại).
        self.can_khop = set()
        self.cam = {}                        # mã → hết cấm lúc nào (unix)
        self.dung = False                    # ④ «Dừng cả tài khoản» đã bật
        self.ky = {}                         # trạm → khoá kỳ lịch lần chạy trước
        self.vi_the = {}                     # mã → {dau, t_vao, cuc, so_nen}
        self.gia = {}                        # mã → giá đóng M1 gần nhất
        self.spread = {}
        self.gia_dau = {}                    # mã → giá lúc hết khởi động (cho boss)
        self.tk = {"von": self.von_dau, "tien_mat": self.von_dau, "giu": {}, "lenh_cho": {}}
        self.dinh_von = self.von_dau
        self.sut_max_pt = 0.0
        self.duong_von = []                  # [t, vốn, sụt %] — mỗi ngày một điểm
        self._ngay_von = None
        self.lenh = {}                       # id → lệnh (vòng đời đầy đủ)
        self._so_lenh = 0
        self.nhat_ky = []
        self.dem_chay = {k: 0 for k in T.TRAM_KEYS}
        self._da_huy = set()

    # ------------------------------------------------------------------ dựng
    def _dung_luong(self):
        """Đồ thị từng trạm, tra sẵn một lần: khối theo id, thứ tự nhánh, khối Bắt đầu."""
        self.luong = {}
        for k in T.TRAM_KEYS:
            g = self.may["tram"][k]
            theo_id, ke = core.flow_map(g["steps"], g["edges"])
            vao = core.flow_entry(g["steps"], g["edges"])
            self.luong[k] = {"theo_id": theo_id, "ke": ke, "vao": vao,
                             "bd": theo_id.get(vao) or {}}
        self.lich = {k: self.luong[k]["bd"].get("lich") for k in T.TRAM_KEYS}
        self.khung = {k: self.luong[k]["bd"].get("khung") for k in T.TRAM_KEYS}
        self.gom = {k: self.may["tram"][k].get("gom") or {} for k in T.TRAM_KEYS}

    def so(self, v):
        """Ô số → con số. Chuỗi là TÊN tham số (đã soát là có thật)."""
        return float(self.ts[v]) if isinstance(v, str) else float(v)

    def _cac_toan_hang(self):
        """Mọi đại lượng trong cỗ máy (vế trái, vế phải, điểm của rổ)."""
        for k in T.TRAM_KEYS:
            for st in self.may["tram"][k]["steps"]:
                for c in st.get("conditions") or []:
                    yield c.get("trai")
                    if isinstance(c.get("phai"), dict) and c["phai"].get("ten"):
                        yield c["phai"]
                if isinstance(st.get("diem"), dict):
                    yield st["diem"]

    def _khoa_doc(self, o):
        """Khoá của một đại lượng KHÔNG kể lùi và hệ số — hai chỗ đọc cùng chỉ báo dùng chung."""
        d = T.TOAN_HANG_THEO_KEY[o["ten"]]
        o2 = {k: o[k] for k in d["tham_so"] if k != "lui" and k in o}
        o2 = {k: (self.so(v) if T.THAM_SO_TH[k]["loai"] == "so" else v) for k, v in o2.items()}
        return json.dumps([o["ten"], o2], sort_keys=True)

    def _dung_chuoi(self):
        """Chuỗi nến cho từng mã ở từng khung cần dùng, gắn sẵn chỉ báo từ ĐẦU — chỉ báo gắn
        giữa chừng thì phải đợi đủ dữ liệu lại từ đầu, trạm đọc ra NaN suốt quãng đó."""
        cac = list(self._cac_toan_hang())
        lui_max = 0
        for o in cac:
            if "lui" in o:
                lui_max = max(lui_max, int(self.so(o["lui"])))
        self._giu = lui_max + 2
        khung = set()
        for k in (T.TIN_HIEU, T.RUI_RO, T.KHOP_LENH):
            if self.lich[k] == "moi_nen" and self.khung[k]:
                khung.add(self.khung[k])
        for o in cac:
            if "khung" in T.TOAN_HANG_THEO_KEY[o["ten"]]["tham_so"]:
                khung.add(o["khung"])
        for st in self.may["tram"][T.CHIA_VON]["steps"]:
            if st.get("type") == "dat_ty_trong" and st.get("cach") == "rui_ro_ngang":
                khung.add(st["khung"])
        self.cac_khung = sorted(khung, key=lambda x: KHUNG_GIAY[x])
        self.chuoi = {ma: {kh: ChuoiNen(kh, self._giu) for kh in self.cac_khung}
                      for ma in self.ma}
        # Đăng ký chỉ báo: khoá đọc → {mã: hàm đọc(lui)}. `_kd` nhớ khoá của từng đại lượng
        # (theo id) — dựng khoá bằng json mỗi lần đọc thì ⑤ chạy mỗi phút sẽ chậm hẳn.
        self.doc, self._kd = {}, {}
        for o in cac:
            d = T.TOAN_HANG_THEO_KEY[o["ten"]]
            if "khung" not in d["tham_so"]:
                continue
            kd = self._khoa_doc(o)
            if kd in self.doc:
                continue
            o_so = {k: (self.so(o[k]) if T.THAM_SO_TH[k]["loai"] == "so" else o[k])
                    for k in d["tham_so"] if k in o}
            self.doc[kd] = {ma: self.chuoi[ma][o["khung"]].dang_ky(o["ten"], o_so)
                            for ma in self.ma}
        # «Rủi ro ngang nhau» đọc ATR % của chính khung/chu kỳ trên khối.
        self.doc_atr_pt = {}
        for st in self.may["tram"][T.CHIA_VON]["steps"]:
            if st.get("type") == "dat_ty_trong" and st.get("cach") == "rui_ro_ngang":
                khoa = (st["khung"], int(self.so(st["chu_ky"])))
                if khoa not in self.doc_atr_pt:
                    self.doc_atr_pt[khoa] = {
                        ma: self.chuoi[ma][khoa[0]].dang_ky(
                            "atr_pt", {"chu_ky": khoa[1], "kieu": "rma"})
                        for ma in self.ma}

    # ------------------------------------------------------------------ một bước
    def buoc(self, t, nen_m1, tk=None):
        """Một phút. `nen_m1` = {mã: (o, h, l, c, v[, spread])} của những nến M1 vừa ĐÓNG lúc t.
        `tk` = tài khoản lúc t (xem `_nhan_tk`). Trả danh sách ý định lệnh."""
        t = int(t)
        if self.t is not None and t <= self.t:
            raise LoiMay(f"Thời gian đi lùi: bước {t} sau bước {self.t}.")
        self.t = t
        vua_dong = self._nap_nen(t, nen_m1 or {})
        self._nhan_tk(tk)
        self._theo_vi_the(vua_dong)

        if self.bat_dau_t is not None and t < self.bat_dau_t:
            return []
        y_dinh = []
        if not self.da_khoi_dong:
            self.da_khoi_dong = True
            self.gia_dau = dict(self.gia)
            self.dinh_von = self.tk["von"]
            self.nhat_ky.append({"t": t, "tram": None, "ma": None, "su_kien": "bat_dau",
                                 "von": _js(self.tk["von"])})
        self._ghi_von()

        da_huy = self._da_huy = set()
        self._lenh_het_han(t, y_dinh, da_huy)
        doi_th = self._tin_hieu_het_han(t)
        muc_cu = dict(self.muc_tieu)

        if not self.dung:
            if self._toi_lich(T.CHON_MA, t):
                doi_th |= self._chay_chon_ma(t)
            doi_th |= self._chay_tin_hieu(t, vua_dong)
            if self._toi_lich(T.CHIA_VON, t, co_doi=bool(doi_th)):
                self._chay_chia_von(t)
            self._chay_rui_ro(t, vua_dong)
        self._ap_cam(t)

        # Mục tiêu đổi → lệnh chờ cũ của mã đó đã sai hướng/sai cỡ: huỷ, để ⑤ tính lại từ đầu.
        for ma in sorted(set(muc_cu) | set(self.muc_tieu)):
            if abs(muc_cu.get(ma, 0.0) - self.muc_tieu.get(ma, 0.0)) > 1e-9:
                self.t_doi_muc_tieu[ma] = t
                self._huy_lenh_cua(ma, "doi_muc_tieu", y_dinh, da_huy)
        self._chay_khop_lenh(t, vua_dong, y_dinh, da_huy)
        return y_dinh

    # ---- dữ liệu ----
    def _nap_nen(self, t, nen_m1):
        vua_dong = {}
        for ma in self.ma:
            n = nen_m1.get(ma)
            if n is not None:
                o, h, l, c = (float(x) for x in n[:4])
                v = float(n[4]) if len(n) > 4 and n[4] is not None else 0.0
                self.gia[ma] = c
                if len(n) > 5 and n[5] is not None:
                    self.spread[ma] = float(n[5])
            ds = set()
            for kh, cn in self.chuoi[ma].items():
                truoc = cn.so_nen
                if n is not None:
                    cn.nap_m1(t, o, h, l, c, v)
                cn.dong_neu_toi(t)
                if cn.so_nen > truoc:
                    ds.add(kh)
            if ds:
                vua_dong[ma] = ds
        return vua_dong

    def _nhan_tk(self, tk):
        """Tài khoản do bên ngoài (QC / sàn giả) đưa vào — nguồn sự thật DUY NHẤT về tiền:

            {"von": vốn, "tien_mat": tiền mặt,
             "giu": {mã: {"pt": % vốn có dấu, "gia_von": giá vốn, "sl": số lượng}},
             "lenh_cho": {id lệnh: {"ma": mã, "pt": % vốn còn chờ, có dấu}}}"""
        if tk is not None:
            self.tk = {"von": float(tk.get("von", self.tk["von"])),
                       "tien_mat": float(tk.get("tien_mat", self.tk["tien_mat"])),
                       "giu": dict(tk.get("giu") or {}), "lenh_cho": dict(tk.get("lenh_cho") or {})}
        # Lệnh của ta đã khép (khớp hết / huỷ) = không còn trong sổ chờ của sàn.
        for lid, l in self.lenh.items():
            if l["mo"] and lid not in self.tk["lenh_cho"] and l["t_dat"] < self.t:
                l["mo"] = False
                l["t_xong"] = self.t

    def _ghi_von(self):
        """Đỉnh vốn, sụt giảm lớn nhất (theo TỪNG bước, không chỉ cuối ngày) và đường vốn mỗi
        ngày một điểm. Chỉ tính sau khởi động — quãng khởi động không có giao dịch nào."""
        v = self.tk["von"]
        if v > self.dinh_von:
            self.dinh_von = v
        sut = (1.0 - v / self.dinh_von) * 100.0 if self.dinh_von > 0 else 0.0
        self.sut_max_pt = max(self.sut_max_pt, sut)
        ngay = _ngay(self.t).date()
        if self._ngay_von != ngay:
            self.duong_von.append([self.t, v, -sut])
            self._ngay_von = ngay
        else:
            self.duong_von[-1] = [self.t, v, -sut]

    def _theo_vi_the(self, vua_dong):
        """Vị thế từng mã: lúc vào, giá tốt nhất kể từ lúc vào (cho trailing), số nến đã giữ."""
        kh4 = self.khung[T.RUI_RO]
        for ma in self.ma:
            g = self.tk["giu"].get(ma) or {}
            sl = float(g.get("sl") or 0.0)
            dau = (sl > 0) - (sl < 0)
            vt = self.vi_the.get(ma)
            gia = self.gia.get(ma)
            if dau == 0:
                self.vi_the.pop(ma, None)
                continue
            if vt is None or vt["dau"] != dau:
                vt = self.vi_the[ma] = {"dau": dau, "t_vao": self.t, "cuc": gia, "so_nen": 0}
            if gia is not None:
                vt["cuc"] = gia if vt["cuc"] is None else (
                    max(vt["cuc"], gia) if dau > 0 else min(vt["cuc"], gia))
            if kh4 in vua_dong.get(ma, ()):
                vt["so_nen"] += 1

    # ---- lịch ----
    def _toi_lich(self, k, t, co_doi=False):
        """Trạm `k` có tới lịch chạy ở bước này không.

        Lịch theo kỳ (mỗi ngày / đầu tuần / đầu tháng) chạy ở bước ĐẦU TIÊN của mỗi kỳ — kể cả
        kỳ đầu tiên sau khởi động: chọn mã "đầu tháng" mà đợi tới tận đầu tháng sau mới chạy
        lần đầu thì suốt quãng đó rổ rỗng."""
        lich = self.lich[k]
        if lich == "khi_tin_hieu_doi":
            return co_doi
        moc = True if lich == "bat_dau" else _moc_lich(t, lich)
        if moc is None or self.ky.get(k) == moc:
            return False
        self.ky[k] = moc
        return True

    # ------------------------------------------------------------------ đi sơ đồ
    def _chay_so_do(self, k, ma, t):
        """Một LƯỢT chạy sơ đồ của trạm `k` cho mã `ma`. Trả bản ghi nhật ký."""
        L = self.luong[k]
        theo_id, ke, vao = L["theo_id"], L["ke"], L["vao"]
        duong, ngan = [vao], [list(ke.get(vao, []))]
        cham, viec, cong, ket = False, [], [], "het_luot"
        for _ in range(TRAN_BUOC):
            di = None
            while ngan[-1]:
                s = ngan[-1].pop(0)
                st = theo_id[s]
                if core.is_branch_gate(st):
                    khop, ve = self._xet_cong(st, k, ma)
                    cong.append({"khoi": s, "khop": khop, "ve": ve})
                    if not khop:
                        continue
                di = s
                break
            if di is None:
                if cham or len(ngan) == 1:
                    break
                ngan.pop()
                duong.pop()
                continue
            duong.append(di)
            st = theo_id[di]
            if st.get("type") in T.KHOI_LAM:
                cham = True
                viec.append(self._lam(st, k, ma, t))
            ngan.append(list(ke.get(di, [])))
            if not ngan[-1]:
                ket = "xong"
                break
        else:
            raise LoiMay(f"Trạm {T.nhan_tram(k)} chạy quá {TRAN_BUOC} bước cho mã {ma} — có "
                         f"vòng lặp không thoát được.")
        self.dem_chay[k] += 1
        r = {"t": t, "tram": k, "ma": ma, "duong": duong, "ket": ket, "cong": cong,
             "viec": viec}
        self.nhat_ky.append(r)
        return r

    def _xet_cong(self, st, k, ma):
        """Một cổng: LUÔN tính đủ mọi điều kiện (không ngắt ở cái sai đầu) — vết từng điều kiện
        là thứ duy nhất trả lời được "trượt vì con số nào" khi đọc lại nhật ký."""
        ve, khop = [], True
        for c in st.get("conditions") or []:
            a = self._gt(c["trai"], k, ma)
            p = c.get("phai") or {}
            b = self._gt(p, k, ma) if p.get("ten") else self.so(p.get("value", 0.0))
            dat = _so_sanh(a, c["phep"], b)
            ve.append({"trai": _js(a), "phai": _js(b), "dat": dat})
            khop = khop and dat
        return khop, ve

    def _gt(self, o, k, ma):
        """Giá trị một đại lượng cho mã `ma` ở trạm `k`, lúc này."""
        ten = o["ten"]
        d = T.TOAN_HANG_THEO_KEY[ten]
        if "khung" in d["tham_so"]:
            kd = self._kd.get(id(o))
            if kd is None:
                kd = self._kd[id(o)] = (self._khoa_doc(o), int(self.so(o.get("lui", 0))))
            v = self.doc[kd[0]][ma](kd[1])
        else:
            v = self._gt_trang_thai(ten, ma)
        if "he_so" in o:
            v = v * self.so(o["he_so"])
        return v

    def _gt_trang_thai(self, ten, ma):
        t, tk = self.t, self.tk
        von = tk["von"]
        g = tk["giu"].get(ma) or {}
        th = self.tin_hieu.get(ma)
        if ten == "gio":
            return float(_ngay(t).hour)
        if ten == "thu":
            return float(_ngay(t).isoweekday())
        if ten == "von":
            return von
        if ten == "lai_tk_pt":
            return (von / self.von_dau - 1.0) * 100.0
        if ten == "sut_giam_tk_pt":
            return (1.0 - von / self.dinh_von) * 100.0 if self.dinh_von > 0 else 0.0
        if ten == "tien_mat_pt":
            return tk["tien_mat"] / von * 100.0 if von else NAN
        if ten == "so_ma_dang_giu":
            return float(sum(1 for x in tk["giu"].values() if float(x.get("sl") or 0)))
        if ten == "huong_tin_hieu":
            return float(th.huong) if th else 0.0
        if ten == "tin_cay":
            return th.tin_cay if th and th.tin_cay is not None else NAN
        if ten == "trong_so_tin_hieu":
            return th.trong_so if th and th.trong_so is not None else NAN
        if ten == "so_ma_len":
            return float(sum(1 for x in self.tin_hieu.values() if x.huong > 0))
        if ten == "so_ma_xuong":
            return float(sum(1 for x in self.tin_hieu.values() if x.huong < 0))
        if ten == "ty_trong_pt":
            return float(g.get("pt") or 0.0)
        vt = self.vi_the.get(ma)
        gia = self.gia.get(ma)
        if ten == "lai_lo_pt":
            gv = float(g.get("gia_von") or 0.0)
            if not vt or not gv or gia is None:
                return NAN
            return (gia / gv - 1.0) * 100.0 * vt["dau"]
        if ten == "sut_tu_dinh_pt":
            if not vt or not vt["cuc"] or gia is None:
                return NAN
            return ((1.0 - gia / vt["cuc"]) if vt["dau"] > 0 else (gia / vt["cuc"] - 1.0)) * 100.0
        if ten == "so_nen_giu":
            return float(vt["so_nen"]) if vt else 0.0
        if ten == "lech_muc_tieu_pt":
            return self._lech(ma)
        if ten == "spread_pt":
            sp = self.spread.get(ma)
            return sp / gia * 100.0 if sp is not None and gia else 0.0
        if ten == "so_lenh_cho":
            return float(len(self._lenh_cho(ma)))
        if ten == "phut_tu_muc_tieu":
            t0 = self.t_doi_muc_tieu.get(ma)
            return (t - t0) / 60.0 if t0 is not None else NAN
        raise LoiMay(f"Đại lượng «{ten}» chưa được cài trong bộ máy.")

    def _lam(self, st, k, ma, t):
        """Một khối Làm → một VIỆC (dict). Ghi lại đủ để đọc lại không cần sơ đồ."""
        typ = st["type"]
        v = {"loai": typ, "khoi": st["id"]}
        if typ == "vao_ro":
            v["diem"] = _js(self._gt(st["diem"], k, ma)) if st.get("diem") else None
        elif typ == "bao":
            v.update(huong=st["huong"],
                     het_han=t + int(self.so(st["thoi_han"])) * KHUNG_GIAY[self.khung[k]],
                     tin_cay=self.so(st["tin_cay"]) if st.get("tin_cay") not in (None, "")
                     else None,
                     trong_so=self.so(st["trong_so"]) if st.get("trong_so") not in (None, "")
                     else None)
        elif typ == "dat_ty_trong":
            v["cach"] = st["cach"]
            if st["cach"] == "co_dinh":
                v["pt"] = self.so(st["pt"])
            if st["cach"] == "rui_ro_ngang":
                khoa = (st["khung"], int(self.so(st["chu_ky"])))
                v["atr_pt"] = _js(self.doc_atr_pt[khoa][ma](0))
        elif typ == "giam_ve":
            v["pt"] = self.so(st["pt"])
        elif typ == "cam_vao_lai":
            v["den"] = t + int(self.so(st["so_nen"])) * KHUNG_GIAY[self.khung[T.RUI_RO]]
        elif typ in ("lenh_thi_truong", "lenh_gioi_han", "lenh_cho_stop"):
            v["phan_pt"] = self.so(st["phan_pt"])
            if typ != "lenh_thi_truong":
                v["lech_pt"] = self.so(st["lech_pt"])
                v["het_han"] = t + int(self.so(st["het_han"])) * KHUNG_GIAY[self.khung[k]]
        return v

    @staticmethod
    def _quyet(r):
        """Việc QUYẾT ĐỊNH cuối cùng của một lượt (soát lỗi đã chặn hai cái trên một đường)."""
        for v in reversed(r["viec"]):
            if T.KHOI_LAM[v["loai"]]["vai"] == "quyet_dinh":
                return v
        return None

    # ------------------------------------------------------------------ ① Chọn mã
    def _chay_chon_ma(self, t):
        bd = self.luong[T.CHON_MA]["bd"]
        pv = bd.get("pham_vi") or {}
        ung_vien = ([m for m in pv.get("ma") or [] if m in self.chuoi]
                    if pv.get("loai") == "danh_sach" else list(self.ma))
        vao = []
        for ma in ung_vien:
            q = self._quyet(self._chay_so_do(T.CHON_MA, ma, t))
            if q and q["loai"] == "vao_ro":
                vao.append((ma, q.get("diem")))
        gom = self.gom[T.CHON_MA]
        bo = []
        if gom.get("top_n") not in (None, ""):
            n = int(self.so(gom["top_n"]))
            cao = gom.get("xep", "cao") == "cao"
            # Không điểm thì xếp CUỐI dù giữ điểm cao hay thấp — soát lỗi đã cảnh báo.
            vao.sort(key=lambda x: (x[1] is None, -(x[1] or 0.0) if cao else (x[1] or 0.0)))
            vao, bo = vao[:n], [m for m, _ in vao[n:]]
        ro_moi = [m for m, _ in vao]
        cu = set(self.ro)
        roi = [m for m in self.ro if m not in set(ro_moi)]
        self.ro, self.diem = ro_moi, {m: d for m, d in vao}
        self.nhat_ky.append({"t": t, "tram": T.CHON_MA, "ma": None, "gom": {
            "ro": ro_moi, "diem": self.diem, "bo": bo,
            "vao": [m for m in ro_moi if m not in cu], "ra": roi}})
        doi = set()
        for ma in roi:                      # rời rổ thì tín hiệu tắt theo
            if self.tin_hieu.pop(ma, None) is not None:
                doi.add(ma)
                self.nhat_ky.append({"t": t, "tram": T.TIN_HIEU, "ma": ma,
                                     "su_kien": "tat_tin_hieu", "ly_do": "roi_ro"})
        return doi

    # ------------------------------------------------------------------ ② Tín hiệu
    def _chay_tin_hieu(self, t, vua_dong):
        doi = set()
        kh = self.khung[T.TIN_HIEU]
        for ma in self.ro:
            if kh not in vua_dong.get(ma, ()):
                continue
            q = self._quyet(self._chay_so_do(T.TIN_HIEU, ma, t))
            if not q or q["loai"] != "bao":
                continue
            huong = {"len": 1, "xuong": -1}.get(q["huong"], 0)
            moi = _TinHieu(huong, q["het_han"], q["tin_cay"], q["trong_so"], t)
            cu = self.tin_hieu.get(ma)
            if cu is None or cu.chu_ky() != moi.chu_ky():
                doi.add(ma)
            self.tin_hieu[ma] = moi
        return doi

    def _tin_hieu_het_han(self, t):
        doi = set()
        for ma in sorted(self.tin_hieu):
            if self.tin_hieu[ma].het_han <= t:
                del self.tin_hieu[ma]
                doi.add(ma)
                self.nhat_ky.append({"t": t, "tram": T.TIN_HIEU, "ma": ma,
                                     "su_kien": "tat_tin_hieu", "ly_do": "het_han"})
        return doi

    # ------------------------------------------------------------------ ③ Chia vốn
    def _pt_giu(self, ma):
        return float((self.tk["giu"].get(ma) or {}).get("pt") or 0.0)

    def _chay_chia_von(self, t):
        xet = sorted(set(self.tin_hieu) | {m for m in self.ma if self._pt_giu(m)}
                     | {m for m, v in self.muc_tieu.items() if v},
                     key=self.ma.index)
        quyet = {ma: self._quyet(self._chay_so_do(T.CHIA_VON, ma, t)) for ma in xet}
        gom = self.gom[T.CHIA_VON]
        ngan_sach = 100.0 - self.so(gom.get("giu_tien_pt", 0))
        tran = self.so(gom.get("tran_moi_ma_pt", 100))
        chi_mua = bool(gom.get("chi_mua", True))
        muc, tuong_doi, ghi_chu = {}, {}, {}
        for ma, q in quyet.items():
            th = self.tin_hieu.get(ma)
            huong = th.huong if th else 0
            if chi_mua and huong < 0:
                huong = 0
            if q is None:                                # không quyết → giữ mục tiêu cũ
                muc[ma] = self.muc_tieu.get(ma, 0.0)
                ghi_chu[ma] = "giu_cu"
            elif q["loai"] == "ve_0":
                muc[ma] = 0.0
            elif q["loai"] == "giu_nguyen":
                muc[ma] = self._pt_giu(ma)
            elif q["cach"] == "co_dinh":
                muc[ma] = huong * q["pt"]
            elif q["cach"] == "theo_trong_so":
                muc[ma] = huong * (th.trong_so or 0.0) * 100.0 if th else 0.0
            else:
                if q["cach"] == "chia_deu":
                    tho = 1.0
                elif q["cach"] == "theo_tin_cay":
                    tho = th.tin_cay if th and th.tin_cay is not None else 1.0
                else:                                    # rủi ro ngang nhau
                    a = q.get("atr_pt")
                    tho = 1.0 / a if a else NAN
                if huong and tho == tho and tho > 0:
                    tuong_doi[ma] = (tho, huong)
                else:
                    muc[ma] = 0.0
                    if huong and not (tho == tho and tho > 0):
                        ghi_chu[ma] = "chua_du_du_lieu"
        co_dinh = sum(abs(v) for v in muc.values())
        con = max(0.0, ngan_sach - co_dinh)
        tong = sum(x for x, _ in tuong_doi.values())
        for ma, (tho, dau) in tuong_doi.items():
            muc[ma] = dau * con * tho / tong
        chan = []
        for ma in muc:
            if chi_mua and muc[ma] < 0:
                muc[ma] = 0.0
            if abs(muc[ma]) > tran + 1e-12:
                muc[ma] = math.copysign(tran, muc[ma])
                chan.append(ma)
        tong_tt = sum(abs(v) for v in muc.values())
        thu_nho = None
        if tong_tt > ngan_sach + 1e-9:
            thu_nho = ngan_sach / tong_tt
            muc = {m: v * thu_nho for m, v in muc.items()}
        self.can_khop |= set(muc) | set(self.muc_tieu)
        self.muc_tieu = {m: v for m, v in muc.items() if abs(v) > 1e-12}
        self.nhat_ky.append({"t": t, "tram": T.CHIA_VON, "ma": None, "gom": {
            "muc_tieu": {m: _js(v) for m, v in muc.items()}, "ngan_sach": ngan_sach,
            "thu_nho": _js(thu_nho), "chan_tran": chan, "ghi_chu": ghi_chu}})

    # ------------------------------------------------------------------ ④ Rủi ro
    def _chay_rui_ro(self, t, vua_dong):
        kh = self.khung[T.RUI_RO]
        for ma in self.ma:
            if self.dung:
                return
            if not self._pt_giu(ma) or kh not in vua_dong.get(ma, ()):
                continue
            r = self._chay_so_do(T.RUI_RO, ma, t)
            if r["viec"]:
                self.can_khop.add(ma)
            for v in r["viec"]:
                if v["loai"] == "dua_ve_0":
                    self.muc_tieu.pop(ma, None)
                elif v["loai"] == "giam_ve":
                    cu = self.muc_tieu.get(ma, 0.0)
                    if abs(cu) > v["pt"]:
                        self.muc_tieu[ma] = math.copysign(v["pt"], cu)
                elif v["loai"] == "cam_vao_lai":
                    self.cam[ma] = max(self.cam.get(ma, 0), v["den"])
                elif v["loai"] == "dung_tai_khoan":
                    self.dung = True
                    self.can_khop |= set(self.muc_tieu) | {
                        m for m in self.ma if self._pt_giu(m)}
                    self.muc_tieu = {}
                    self.tin_hieu = {}
                    self.nhat_ky.append({"t": t, "tram": T.RUI_RO, "ma": ma,
                                         "su_kien": "dung_tai_khoan"})

    def _ap_cam(self, t):
        for ma in list(self.cam):
            if self.cam[ma] <= t:
                del self.cam[ma]
            elif self.muc_tieu.pop(ma, None) is not None:
                self.can_khop.add(ma)

    # ------------------------------------------------------------------ ⑤ Khớp lệnh
    def _lenh_cho(self, ma):
        """Lệnh còn chờ của mã — trừ những lệnh chính bước này vừa xin huỷ."""
        return [x for lid, x in self.tk["lenh_cho"].items()
                if x.get("ma") == ma and lid not in self._da_huy]

    def _lech(self, ma):
        """Mục tiêu − đang giữ − đang chờ khớp, tính bằng % vốn (có dấu)."""
        cho = sum(float(x.get("pt") or 0.0) for x in self._lenh_cho(ma))
        return self.muc_tieu.get(ma, 0.0) - self._pt_giu(ma) - cho

    def _chay_khop_lenh(self, t, vua_dong, y_dinh, da_huy):
        kh = self.khung[T.KHOP_LENH]
        for ma in self.ma:
            if ma not in self.can_khop or kh not in vua_dong.get(ma, ()) \
                    or self.gia.get(ma) is None:
                continue
            lech = self._lech(ma)
            if abs(lech) < NGUONG_LECH_PT:
                self.can_khop.discard(ma)          # đã tới mục tiêu (tính cả lệnh đang chờ)
                continue
            r = self._chay_so_do(T.KHOP_LENH, ma, t)
            q = self._quyet(r)
            if not q or q["loai"] == "cho":
                continue
            pt = lech * q["phan_pt"] / 100.0
            gia = self.gia[ma]
            y = {"loai": "dat", "ma": ma, "pt": pt, "muc_tieu_pt": self.muc_tieu.get(ma, 0.0)}
            if q["loai"] == "lenh_thi_truong":
                y["kieu"] = "thi_truong"
            else:
                mua = pt > 0
                lech_gia = q["lech_pt"] / 100.0
                if q["loai"] == "lenh_gioi_han":
                    y["kieu"], y["gia"] = "gioi_han", gia * (1 - lech_gia if mua else 1 + lech_gia)
                else:
                    y["kieu"], y["gia"] = "cho_stop", gia * (1 + lech_gia if mua else 1 - lech_gia)
                y["het_han"] = q["het_han"]
            self._so_lenh += 1
            y["id"] = f"L-{self._so_lenh:04d}"
            # Ghi ngược vào VIỆC của lượt vừa chạy (cùng một dict với bản ghi nhật ký): đọc lại
            # thấy ngay lượt đó đặt lệnh nào, bao nhiêu % vốn, ở giá nào.
            q.update(lenh_id=y["id"], kieu=y["kieu"], pt=_js(pt), gia=_js(y.get("gia")))
            self.lenh[y["id"]] = {"id": y["id"], "ma": ma, "kieu": y["kieu"], "pt": pt,
                                  "gia": y.get("gia"), "het_han": y.get("het_han"),
                                  "t_dat": t, "khoi": q["khoi"], "mo": True, "khop": [],
                                  "t_xong": None, "ly_do_huy": None}
            y_dinh.append(y)

    def _lenh_het_han(self, t, y_dinh, da_huy):
        for lid in sorted(self.lenh):
            l = self.lenh[lid]
            if l["mo"] and l.get("het_han") is not None and l["het_han"] <= t \
                    and lid in self.tk["lenh_cho"]:
                self._huy(lid, "het_han", y_dinh, da_huy)

    def _huy_lenh_cua(self, ma, ly_do, y_dinh, da_huy):
        for lid in sorted(self.lenh):
            l = self.lenh[lid]
            if l["mo"] and l["ma"] == ma and lid in self.tk["lenh_cho"] and lid not in da_huy:
                self._huy(lid, ly_do, y_dinh, da_huy)

    def _huy(self, lid, ly_do, y_dinh, da_huy):
        l = self.lenh[lid]
        l["ly_do_huy"] = ly_do
        da_huy.add(lid)
        self.can_khop.add(l["ma"])
        y_dinh.append({"loai": "huy", "id": lid, "ma": l["ma"], "ly_do": ly_do})
        self.nhat_ky.append({"t": self.t, "tram": T.KHOP_LENH, "ma": l["ma"],
                             "su_kien": "huy_lenh", "lenh_id": lid, "ly_do": ly_do})

    # ------------------------------------------------------------------ từ chối (từ sàn)
    def nhan_tu_choi(self, lid, ly_do):
        """Sàn KHÔNG nhận lệnh `lid` (số lượng làm tròn theo lô ra 0, thiếu sức mua, sai
        giá…). Bỏ mã ra khỏi danh sách cần khớp: không thì ⑤ đặt lại đúng lệnh hỏng ấy MỖI
        PHÚT. Mục tiêu đổi (③/④) thì mã tự vào lại danh sách."""
        l = self.lenh.get(lid)
        if l is None:
            return
        l["mo"] = False
        l["ly_do_huy"] = "tu_choi"
        l["t_xong"] = self.t
        self.can_khop.discard(l["ma"])
        self.nhat_ky.append({"t": self.t, "tram": T.KHOP_LENH, "ma": l["ma"],
                             "su_kien": "tu_choi", "lenh_id": lid, "ly_do": str(ly_do)})

    # ------------------------------------------------------------------ khớp (từ sàn)
    def nhan_khop(self, lid, t, sl, gia, phi=0.0):
        """Sàn báo lệnh `lid` vừa khớp `sl` (có dấu) ở giá `gia`."""
        l = self.lenh.get(lid)
        if l is None:
            return
        l["khop"].append([int(t), float(sl), float(gia), float(phi)])
        self.nhat_ky.append({"t": int(t), "tram": T.KHOP_LENH, "ma": l["ma"],
                             "su_kien": "khop", "lenh_id": lid, "sl": float(sl),
                             "gia": float(gia)})

    # ------------------------------------------------------------------ kết quả
    def thong_ke(self):
        v = self.tk["von"]
        gia_cuoi = self.gia
        boss = [(gia_cuoi[m] / self.gia_dau[m] - 1.0) * 100.0
                for m in self.ma if self.gia_dau.get(m) and gia_cuoi.get(m)]
        dat = list(self.lenh.values())
        return {
            "von_dau": self.von_dau, "von_cuoi": v,
            "lai_pt": (v / self.von_dau - 1.0) * 100.0,
            "sut_giam_max_pt": self.sut_max_pt,
            "boss_pt": sum(boss) / len(boss) if boss else None,
            "so_lenh": len(dat),
            "so_lenh_khop": sum(1 for l in dat if l["khop"]),
            "so_lenh_huy": sum(1 for l in dat if l["ly_do_huy"] and not l["khop"]),
            "dem_chay": dict(self.dem_chay),
            "dung_tai_khoan": self.dung,
        }
