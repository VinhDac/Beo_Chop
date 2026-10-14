"""NHẬT KÝ CỖ MÁY 5 TRẠM — dựng chữ "vì sao" từ bản ghi của bộ máy.  (D-10, phần 3)

Bộ máy (`bo_may`) chỉ ghi số và id — không một chữ nào lúc chạy. Chữ được DỰNG Ở ĐÂY, chỉ cho
lô đang nhìn, và từ chính cỗ máy đã chạy: nhãn đánh số `[2A.1]` dựng lại từ đồ thị, không lưu
trong nhật ký (kéo một khối đi chỗ khác là nhãn đổi, nhật ký cũ vẫn phải trỏ đúng khối).

Một dòng:  `01-03 10:00  ② EURUSD  [1]→[1A]→[1A.1]  báo LÊN · hạn tới 01-03 12:00`
Lượt trượt: `… hết lượt tại [1B] · Giá đóng(H1) = 98.2 không > SMA(H1, 10) = 99.1`

Chữ do PYTHON sinh, giao diện không ghép một mẩu nào (luật #2 của app).
"""
from datetime import datetime, timezone

from . import core
from . import may as M
from . import tram as T

KIEU_LENH = {"thi_truong": "thị trường", "gioi_han": "giới hạn", "cho_stop": "chờ stop"}
LY_DO = {"het_han": "hết hạn", "doi_muc_tieu": "mục tiêu đổi", "roi_ro": "rời rổ"}
PHEP_PHU_DINH = {"<": "<", "<=": "≤", ">": ">", ">=": "≥", "==": "=", "!=": "≠"}


def gio(t):
    return datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%m-%d %H:%M")


def _so(x, chu_so=4):
    if x is None:
        return "—"
    x = float(x)
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{chu_so}g}" if abs(x) < 1 else f"{x:.{max(1, chu_so - len(str(int(abs(x)))))}f}"


def _pt(x):
    return f"{float(x):+.2f}%" if x is not None else "—"


def co_viec(r):
    """Dòng này có CHUYỆN không (lọc "chỉ dòng có việc"): làm gì đó, Gom, hay sự kiện."""
    return bool(r.get("viec") or r.get("gom") or r.get("su_kien"))


class DocNhatKy:
    """Đọc nhật ký của MỘT cỗ máy. Dựng một lần cho mỗi lượt xem (tra nhãn, tra khối)."""

    def __init__(self, may):
        self.may = M.chuan_hoa(may)
        self.ts = M.bang_tham_so(self.may)
        self.nhan, self.khoi = {}, {}
        for k in T.TRAM_KEYS:
            g = self.may["tram"][k]
            self.nhan[k] = core.flow_order(g["steps"], g["edges"])["order"]
            self.khoi[k] = {s["id"]: s for s in g["steps"]}

    def _dau(self, r):
        so = T.TRAM_THEO_KEY[r["tram"]]["so"] if r.get("tram") else "◆"
        ma = r.get("ma") or ""
        return f"{gio(r['t'])}  {so} {ma}".rstrip()

    def _nhan(self, k, sid):
        return self.nhan[k].get(sid, "?")

    def vi_sao(self, r):
        """Cổng CUỐI đã trượt → những điều kiện sai, kèm con số hai vế."""
        k = r["tram"]
        truot = [c for c in r.get("cong") or [] if not c["khop"]]
        if not truot:
            return ""
        c = truot[-1]
        st = self.khoi[k].get(c["khoi"]) or {}
        phan = []
        for dk_, ve in zip(st.get("conditions") or [], c["ve"]):
            if ve["dat"]:
                continue
            if ve["trai"] is None or ve["phai"] is None:
                phan.append(f"{M.toan_hang_chu(dk_.get('trai'), self.ts)} chưa có dữ liệu")
                continue
            p = dk_.get("phai") or {}
            phai = (M.toan_hang_chu(p, self.ts) if p.get("ten")
                    else M._so_hoac_ten(p.get("value"), self.ts))
            phan.append(f"{M.toan_hang_chu(dk_.get('trai'), self.ts)} = {_so(ve['trai'])} "
                        f"không {PHEP_PHU_DINH.get(dk_.get('phep'), '?')} {phai}"
                        + (f" = {_so(ve['phai'])}" if p.get("ten") else ""))
        return " · ".join(phan)

    def _viec(self, v):
        t = v["loai"]
        if t == "vao_ro":
            return "vào rổ" + (f" · điểm {_so(v['diem'])}" if v.get("diem") is not None else "")
        if t == "loai_ro":
            return "không vào rổ"
        if t == "bao":
            phu = ""
            if v.get("tin_cay") is not None:
                phu += f" · tin cậy {_so(v['tin_cay'])}"
            if v.get("trong_so") is not None:
                phu += f" · trọng số {_so(v['trong_so'])}"
            return (f"báo {T.HUONG_TIN_HIEU.get(v.get('huong'), '?')} · hạn tới "
                    f"{gio(v['het_han'])}{phu}")
        if t == "dat_ty_trong":
            s = f"tỷ trọng: {T.CACH_CHIA.get(v.get('cach'), '?')}"
            if v.get("cach") == "co_dinh":
                s = f"tỷ trọng: cố định {_so(v.get('pt'))}%"
            if v.get("cach") == "rui_ro_ngang":
                s += f" · ATR % = {_so(v.get('atr_pt'))}"
            return s
        if t == "ve_0":
            return "mục tiêu = 0"
        if t == "giu_nguyen":
            return "giữ nguyên phần đang giữ"
        if t == "dua_ve_0":
            return "ĐƯA VỀ 0"
        if t == "giam_ve":
            return f"giảm về tối đa {_so(v.get('pt'))}% vốn"
        if t == "cam_vao_lai":
            return f"cấm vào lại tới {gio(v['den'])}"
        if t == "dung_tai_khoan":
            return "DỪNG CẢ TÀI KHOẢN"
        if t == "cho":
            return "chờ — chưa đặt lệnh"
        if t.startswith("lenh_"):
            if not v.get("lenh_id"):
                return "không đặt lệnh"
            s = f"đặt {v['lenh_id']} {KIEU_LENH.get(v.get('kieu'), '?')} {_pt(v.get('pt'))} vốn"
            if v.get("gia") is not None:
                s += f" @ {_so(v['gia'], 6)}"
            return s
        return t

    def chu(self, r):
        """MỘT bản ghi → MỘT dòng chữ."""
        if r.get("su_kien"):
            return self._su_kien(r)
        if r.get("gom") is not None:
            return self._gom(r)
        k = r["tram"]
        duong = "→".join(f"[{self._nhan(k, x)}]" for x in r.get("duong") or [])
        if r.get("viec"):
            duoi = " · ".join(self._viec(v) for v in r["viec"])
        else:
            cong = r.get("cong") or []
            cuoi = f"[{self._nhan(k, cong[-1]['khoi'])}]" if cong else duong.split("→")[-1]
            vs = self.vi_sao(r)
            duoi = f"hết lượt tại {cuoi}" + (f" · {vs}" if vs else "")
        return f"{self._dau(r)}  {duong}  {duoi}"

    def _gom(self, r):
        g = r["gom"]
        if r["tram"] == T.CHON_MA:
            s = f"{self._dau(r)}  Gom · rổ: {', '.join(g.get('ro') or []) or '(rỗng)'}"
            if g.get("vao"):
                s += f" · vào: {', '.join(g['vao'])}"
            if g.get("ra"):
                s += f" · ra: {', '.join(g['ra'])}"
            if g.get("bo"):
                s += f" · quá số mã, bỏ: {', '.join(g['bo'])}"
            return s
        muc = {m: v for m, v in (g.get("muc_tieu") or {}).items() if v}
        s = f"{self._dau(r)}  Gom · mục tiêu: " + (
            " · ".join(f"{m} {v:.1f}%" for m, v in muc.items()) if muc else "không giữ mã nào")
        if g.get("thu_nho") is not None:
            s += f" · vượt ngân sách {_so(g.get('ngan_sach'))}%, thu nhỏ ×{_so(g['thu_nho'])}"
        if g.get("chan_tran"):
            s += f" · chặn trần: {', '.join(g['chan_tran'])}"
        return s

    def _su_kien(self, r):
        sk = r["su_kien"]
        if sk == "bat_dau":
            return f"{self._dau(r)}  BẮT ĐẦU · vốn {_so(r.get('von'))}"
        if sk == "tat_tin_hieu":
            return f"{self._dau(r)}  tắt tín hiệu — {LY_DO.get(r.get('ly_do'), r.get('ly_do'))}"
        if sk == "huy_lenh":
            return (f"{self._dau(r)}  huỷ {r.get('lenh_id')} — "
                    f"{LY_DO.get(r.get('ly_do'), r.get('ly_do'))}")
        if sk == "khop":
            return (f"{self._dau(r)}  khớp {r.get('lenh_id')} {float(r['sl']):+g} @ "
                    f"{_so(r.get('gia'), 6)}")
        if sk == "tu_choi":
            return f"{self._dau(r)}  sàn TỪ CHỐI {r.get('lenh_id')} — {r.get('ly_do')}"
        if sk == "dung_tai_khoan":
            return f"{self._dau(r)}  DỪNG CẢ TÀI KHOẢN — bán sạch, thôi giao dịch"
        return f"{self._dau(r)}  {sk}"

    def lo(self, nhat_ky, tu=0, so=200, chi_viec=True):
        """Một LÔ dòng cho giao diện: chỉ dựng chữ cho đúng lô đang nhìn."""
        ds = [i for i, r in enumerate(nhat_ky) if not chi_viec or co_viec(r)]
        return {"tong": len(ds), "tu": tu,
                "dong": [{"i": i, "t": nhat_ky[i]["t"], "tram": nhat_ky[i].get("tram"),
                          "ma": nhat_ky[i].get("ma"), "co_viec": co_viec(nhat_ky[i]),
                          "chu": self.chu(nhat_ky[i])} for i in ds[tu:tu + so]]}
