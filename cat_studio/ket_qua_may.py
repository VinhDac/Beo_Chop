"""KẾT QUẢ MỘT LƯỢT CỖ MÁY 5 TRẠM — dựng lại từ nhật ký tải về từ QuantConnect.  (D-10, phần 4)

CHỈ ĐỌC. File nhật ký do lớp vỏ `lean/vo_may.py` ghi (dòng đầu là meta, rồi từng lệnh, rồi từng
lượt). Không có nến: kết quả QC không mang chuỗi giá về máy (điều khoản dữ liệu của QC) — mỗi
lượt, mỗi lệnh tự mang giờ của nó, đường vốn nằm sẵn trong meta.

Cùng bề mặt với `qc_chay.KetQuaQC` (tom_tat · lo · lenh · soi) để lớp API của cửa sổ Màn chơi
gọi được cả hai mà không rẽ nhánh.
"""
import json

from . import core
from . import may as M
from . import tram as T
from .nhat_ky_may import DocNhatKy


def doc_file(duong, lay_luot=True):
    """`(meta, lệnh, lượt)`. `lay_luot=False` bỏ qua lượt mà KHÔNG giải mã — nhật ký dài cả
    chục MB, mà màn ẩn chỉ cần meta với lệnh."""
    meta, lenh, luot = {}, [], []
    with open(duong, encoding="utf-8") as f:
        for dong in f:
            if not lay_luot and (dong.startswith('{"loai": "luot"')
                                 or dong.startswith('{"loai":"luot"')):
                continue
            d = json.loads(dong)
            if d.get("loai") == "meta":
                meta = d
            elif d.get("loai") == "lenh":
                lenh.append(d["lenh"])
            elif lay_luot:
                luot.append(d)
    return meta, lenh, luot


class KetQuaMay:

    def __init__(self, duong, lay_luot=True):
        self.duong = duong
        self.meta, self.lenh, self.nhat_ky = doc_file(duong, lay_luot)
        if self.meta.get("dang") != M.DANG:
            raise ValueError("File này không phải nhật ký của cỗ máy 5 trạm.")
        self.may = self.meta.get("may") or {}
        self.thong_ke = self.meta.get("thong_ke") or {}
        self._doc = None
        #: Điều nhật ký không biết mà lượt chạy biết (kiểu chạy, màn, link QC…) — `ViecQC` gắn.
        self.them = {}

    @property
    def doc(self):
        if self._doc is None:
            self._doc = DocNhatKy(self.may)
        return self._doc

    def tom_tat(self):
        m, ch = self.meta, self.meta.get("cau_hinh") or {}
        luot = self.nhat_ky
        return {"dang": M.DANG, "ten": self.may.get("name"), "van_tay": m.get("van_tay"),
                "ma": ch.get("ma") or [], "loai_thi_truong": ch.get("loai"),
                "tu": ch.get("tu"), "den": ch.get("den"), "von": ch.get("von"),
                "t_dau": luot[0].get("t") if luot else None,
                "t_cuoi": luot[-1].get("t") if luot else None,
                "thong_ke": self.thong_ke, "duong_von": m.get("duong_von") or [],
                "gia_dau": m.get("gia_dau") or {}, "gia_cuoi": m.get("gia_cuoi") or {},
                "giay_chay": m.get("giay_chay"), "so_luot": len(luot),
                "so_lenh_bo_qua": m.get("bo_qua"), "duong_nhat_ky": self.duong, **self.them}

    def lo(self, tu=0, so=200, chi_co_viec=True):
        ra = self.doc.lo(self.nhat_ky, int(tu), int(so), bool(chi_co_viec))
        for d in ra["dong"]:
            r = self.nhat_ky[d["i"]]
            d["lenh_id"] = r.get("lenh_id") or next(
                (v.get("lenh_id") for v in r.get("viec") or [] if v.get("lenh_id")), None)
        return ra

    def soi(self, i):
        """Gói SOI một lượt lên sơ đồ: trạm nào, đường đi, cổng đã thử (kèm vết từng điều kiện),
        nhãn khối và câu chữ — để cửa sổ vẽ tô tới đúng dòng điều kiện hỏng."""
        r = self.nhat_ky[int(i)]
        k = r.get("tram")
        if k not in T.TRAM_KEYS or "duong" not in r:
            return {"tram": k, "duong": [], "cong": [], "nhan": {}, "chu": self.doc.chu(r)}
        g = M.chuan_hoa(self.may)["tram"][k]
        nhan = core.flow_order(g["steps"], g["edges"])["order"]
        ids = set(r["duong"]) | {c["khoi"] for c in r.get("cong") or []}
        return {"tram": k, "ma": r.get("ma"), "duong": list(r["duong"]),
                "cong": r.get("cong") or [], "ket": r.get("ket"),
                "nhan": {x: nhan.get(x, "?") for x in ids}, "chu": self.doc.chu(r)}
