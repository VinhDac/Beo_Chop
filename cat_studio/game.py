"""LUẬT CHƠI — chương, màn, boss, sao, giác quan, độ gọn, sổ nộp.  (D-05 · D-06 · D-08 · D-09)

Một chỗ DUY NHẤT biết "điểm" là gì. Không biết QuantConnect, không biết giao diện: nhận
`meta` của một lần chạy (dòng meta trong nhật ký tải về) và trả lời — thắng boss không,
mấy sao, gọn cỡ nào. Bộ chạy nền (`qc_chay`) và giao diện chỉ hỏi ở đây.

CỖ MÁY VẪN LÀ SƠ ĐỒ KHỐI — lời chủ dự án: "vẽ sơ đồ kiểu này vẫn rất hay, đừng bỏ". Game
bọc QUANH việc vẽ sơ đồ, không thay nó.

KHUÔN: OPUS MAGNUM (Zachtronics, 2017) — game lắp cỗ máy  (DECISIONS.md D-09)
----------------------------------------------------------------------------
  Opus Magnum                                 Cat Studio
  ------------------------------------------  ------------------------------------------
  chương truyện, mở/đóng bằng hội thoại        CHUONG — mỗi chương một khách hàng, một
                                               bản đồ (thị trường); truyện mở / đóng
  câu đố: nguyên liệu → sản phẩm               màn: một đoạn thị trường → thắng boss
  mỗi câu đố cho sẵn bộ linh kiện của nó       mỗi màn mở một bộ GIÁC QUAN (toán hạng)
  bàn lục giác + cánh tay + dòng lệnh          SƠ ĐỒ KHỐI (giữ nguyên — xưởng chế tạo)
  chạy thử bao nhiêu lần cũng được             ▶ nhanh / ▶ đầy đủ trên màn ĐÃ THẤY
  ba histogram Cost · Cycles · Area            ba histogram Lãi % · Sụt giảm · Độ gọn
  xong mọi câu đố trong chương mới qua chương  màn sau mở khi màn trước có ★; chương sau
                                               mở khi xong cả chương

Cái Opus Magnum KHÔNG có mà ta có (D-05, D-06): **màn ẩn**. Điểm thật chấm trên đoạn thị
trường cỗ máy chưa từng thấy — chữa bệnh chỉnh tham số tới khi đẹp.

VÒNG CHƠI
---------
chọn màn → vẽ cỗ máy → ▶ nhanh / ▶ đầy đủ → xem máy nghĩ → sửa → NỘP: app chạy cỗ máy
trên MÀN ẨN (khoảng ngày app giữ, người chơi không chọn được) → sao. Nộp đòi một lượt
▶ đầy đủ của ĐÚNG cỗ máy đó (cùng vân tay).

SAO (D-05)
----------
  ★    chạy sạch   — chạy trọn màn đã thấy, có ít nhất MỘT lệnh đóng
  ★★   thắng boss  — và lãi % trên màn đã thấy HƠN boss "Mua rồi giữ" cùng khoảng
  ★★★  vẫn thắng   — và trên MÀN ẨN cũng hơn boss
Mỗi sao cần mọi sao trước nó. Độ gọn = số khối + số tham số — một cột histogram, không
cộng vào sao.

NĂM ĐÃ THẤY VÀ NĂM ẨN KHÔNG BAO GIỜ TRÙNG trong một chương: năm ẩn của màn này mà là năm
đã thấy của màn khác thì chơi màn kia xong, "màn ẩn" của màn này hết ẩn.

SỔ (`du_lieu/game.json`) — ghi bằng `luu_tru.ghi_json_nguyen_tu`, giữ khoá luồng.
"""
import copy
import json
import os
import threading
from datetime import datetime, timezone

from . import core
from . import luu_tru
from . import may_mau
from . import nhat_ky as nk

FILE_SO = "game.json"

# ---------------------------------------------------------------------------
# Nhân vật · chương · màn
# ---------------------------------------------------------------------------
NHAN_VAT = {
    "meo": {"ten": "Mèo Thợ Cả", "vai": "thợ cả của xưởng — người dẫn đường"},
    "ba_tu": {"ten": "Bà Tư", "vai": "chủ tiệm vàng phố cổ"},
}

#: Giác quan (toán hạng) theo nhóm, để màn mở DẦN. Vùng nén (`zone_*`) là đồ nghề nâng
#: cao — chương 1 chưa mở; chế độ Sáng tạo thì có hết (D-07).
_GQ_1 = ("close", "ma", "so_vi_the")
_GQ_2 = _GQ_1 + ("atr", "lenh_da_khop", "lenh_sl_hoa_von", "lenh_lai_R")
_GQ_3 = _GQ_2 + ("open", "high", "low", "so_lenh_cho")

CHUONG = (
    {
        "id": "c1", "so": 1, "ten": "Tiệm vàng nhà Tư", "ban_do": "Vàng",
        "symbol": "XAUUSD", "khach": "ba_tu", "mo_san": True,
        "truyen_mo": [
            ("ba_tu", "Tiệm vàng nhà tôi mở từ thời ông nội. Mấy năm nay giá vàng nhảy "
                      "như con choi choi — mua vào thì sợ, bán ra thì tiếc."),
            ("meo", "Bà cần một cỗ máy. Nó không biết đoán, nhưng nó không sợ, không "
                    "tiếc: làm đúng luật bà dạy, từng nến một."),
            ("ba_tu", "Máy của cậu phải hơn cách của tôi: cứ mua rồi giữ. Hơn được thì "
                      "tôi tin."),
            ("meo", "Luật xưởng: chạy thử trên năm đã qua bao nhiêu lần cũng được. Nhưng "
                    "điểm thật chấm trên năm cỗ máy chưa từng thấy."),
            ("ba_tu", "Vậy bắt đầu từ năm vàng đi ngang. Năm đó tôi mua rồi giữ mà chẳng "
                      "được gì."),
        ],
        "truyen_dong": [
            ("ba_tu", "Bốn mùa vàng, cỗ máy của cậu đều đứng vững. Tiệm tôi giao nó canh "
                      "giá từ mai."),
            ("meo", "Đừng vội. Bốn năm đó chưa có năm nào vàng sập thật sự."),
        ],
    },
    {"id": "c2", "so": 2, "ten": "Mùa sập", "ban_do": "Vàng", "symbol": "XAUUSD",
     "khach": None, "mo_san": False, "sap_ra_mat": True,
     "mo_ta": "Thị trường rơi: boss lỗ — nhưng chỉ đứng ngoài thì chưa đủ ba sao."},
    {"id": "c3", "so": 3, "ten": "Bạc", "ban_do": "Bạc", "symbol": "XAGUSD",
     "khach": None, "mo_san": False, "sap_ra_mat": True,
     "mo_ta": "Bản đồ mới: bạc dao động gấp đôi vàng."},
)


def _man(id_, ten, nam, gq, may, loi_khach, goi_y, gq_moi=()):
    return {
        "id": id_, "chuong": "c1", "ten": ten, "ban_do": "Vàng", "symbol": "XAUUSD",
        "von": 10_000.0,
        "thay": (f"{nam}-01-01", f"{nam}-12-31"),
        "nhanh": (f"{nam}-10-01", f"{nam}-12-31"),
        "an": (f"{nam + 1}-01-01", f"{nam + 1}-12-31"),
        "an_mo_ta": "12 tháng ngay sau năm này",
        "boss": "mua_giu", "giac_quan": gq, "giac_quan_moi": gq_moi,
        "may_goi_y": may, "loi_khach": loi_khach, "goi_y": goi_y,
        # Giữ tên cũ cho phần đã viết trước (thẻ màn của cửa sổ kỹ thuật).
        "loi_dan": loi_khach,
    }


MAN = (
    _man("1-1", "Năm đi ngang", 2021, _GQ_1, "theo_ma",
         "Năm 2021 vàng lên xuống mà chẳng đi tới đâu. Tôi mua đầu năm, giữ cả năm. "
         "Cỗ máy của cậu làm khá hơn được không?",
         "Máy đầu tay đã lắp sẵn. Bấm ▶ đầy đủ trước — thắng hay thua đều được — rồi mở "
         "«Xem máy nghĩ» để thấy nó quyết từng giờ ra sao."),
    _man("1-2", "Cắt lỗ cho kịp", 2018, _GQ_2, "hai_chieu",
         "Năm 2018 vàng trượt dài giữa năm rồi mới hồi. Mua mà không biết cắt thì ôm "
         "lỗ cả mùa hè.",
         "Màn này mở thêm giác quan ATR và «lãi bao nhiêu R». Thử dời SL về hoà vốn "
         "khi lệnh đã lãi đủ 1R.",
         gq_moi=("atr", "lenh_da_khop", "lenh_sl_hoa_von", "lenh_lai_R")),
    _man("1-3", "Biết đứng ngoài", 2016, _GQ_3, None,
         "Năm 2016 vàng bật mạnh nửa đầu năm rồi rơi gần hết. Ai cũng hăng lúc lên, ít "
         "ai biết đứng ngoài lúc rơi.",
         "Bắt đầu từ cỗ máy của màn trước. Giác quan mới: giá mở / cao / thấp của nến.",
         gq_moi=("open", "high", "low", "so_lenh_cho")),
    _man("1-4", "Năm vàng", 2023, _GQ_3, None,
         "Năm 2023 vàng lên đều. Mua rồi giữ là đối thủ mạnh nhất chương này.",
         "Màn trùm của chương. Muốn hơn boss năm tăng, cỗ máy phải ôm lệnh đủ lâu."),
)

BOSS = {
    "mua_giu": {"ten": "Mua rồi giữ",
                "mo_ta": "Mua ở nến đầu tiên, giữ tới nến cuối cùng. Không làm gì khác."},
}

#: Các kiểu chạy. "tu_do" là chế độ Sáng tạo (D-07): mọi symbol, mọi khoảng ngày, không chấm.
LOAI = {
    "nhanh": "▶ nhanh",
    "day_du": "▶ đầy đủ",
    "nop": "Nộp",
    "tu_do": "▶ tự do",
}

#: Giữ bao nhiêu lượt trong lịch sử chạy QC (cũ hơn thì bỏ khỏi sổ, file nhật ký vẫn còn).
GIU_LICH_SU = 200

_khoa = threading.Lock()


class LoiGame(Exception):
    """Một câu tiếng Việt nói vì sao chưa làm được — giao diện in thẳng ra."""


def man(man_id):
    for m in MAN:
        if m["id"] == man_id:
            return m
    raise LoiGame(f"Không có màn «{man_id}».")


def chuong(chuong_id):
    for c in CHUONG:
        if c["id"] == chuong_id:
            return c
    raise LoiGame(f"Không có chương «{chuong_id}».")


def man_cong_khai(m):
    """Thông tin màn cho giao diện — KHÔNG có ngày của màn ẩn (D-06: app giữ màn ẩn)."""
    return {"id": m["id"], "chuong": m["chuong"], "ten": m["ten"], "ban_do": m["ban_do"],
            "symbol": m["symbol"], "von": m["von"], "thay": list(m["thay"]),
            "nhanh": list(m["nhanh"]), "an_mo_ta": m["an_mo_ta"],
            "boss": {"id": m["boss"], **BOSS[m["boss"]]},
            "giac_quan": [{"key": k, "nhan": ten_giac_quan(k), "moi": k in m["giac_quan_moi"]}
                          for k in m["giac_quan"]],
            "may_goi_y": m["may_goi_y"],
            "may_goi_y_ten": may_mau.TEN_MAY.get(m["may_goi_y"]) if m["may_goi_y"] else None,
            "loi_khach": m["loi_khach"], "goi_y": m["goi_y"], "loi_dan": m["loi_dan"]}


def khoang(man_id, loai):
    """`(từ, đến)` của một kiểu chạy trên một màn."""
    m = man(man_id)
    if loai == "nhanh":
        return m["nhanh"]
    if loai == "day_du":
        return m["thay"]
    if loai == "nop":
        return m["an"]
    raise LoiGame(f"Kiểu chạy «{loai}» không thuộc một màn.")


# ---------------------------------------------------------------------------
# Giác quan — màn nào mở giác quan nào
# ---------------------------------------------------------------------------
def giac_quan_dung(doc):
    """Mọi toán hạng cỗ máy đang hỏi (vế trái và vế phải của mọi điều kiện)."""
    ra = set()
    for tab in core.TABS:
        for st in (doc.get(tab) or {}).get("steps") or []:
            for c in st.get("conditions") or []:
                for v in ((c or {}).get("trai"), (c or {}).get("phai")):
                    if isinstance(v, dict) and v.get("ten"):
                        ra.add(v["ten"])
    return ra


def ten_giac_quan(key):
    for t in core.TOAN_HANG:
        if t["key"] == key:
            return t.get("nhan") or key
    return key


def soat_giac_quan(man_id, doc):
    """Cỗ máy chỉ được dùng giác quan màn này đã mở. Dùng quá → `LoiGame` nói rõ cái nào."""
    m = man(man_id)
    thua = sorted(giac_quan_dung(doc) - set(m["giac_quan"]))
    if thua:
        raise LoiGame(
            f"Màn {m['id']} chưa mở giác quan: {', '.join(ten_giac_quan(k) for k in thua)}. "
            "Giác quan mở dần theo màn — chế độ Sáng tạo thì dùng được hết.")


# ---------------------------------------------------------------------------
# Chấm
# ---------------------------------------------------------------------------
def do_gon(doc):
    """Số khối (không tính khối Bắt đầu) + số tham số. Ít hơn là gọn hơn."""
    so_khoi = sum(1 for tab in core.TABS for st in (doc.get(tab) or {}).get("steps") or []
                  if not core.is_start_step(st))
    so_tham_so = len(doc.get("tham_so") or [])
    return {"so_khoi": so_khoi, "so_tham_so": so_tham_so, "tong": so_khoi + so_tham_so}


def cham(meta):
    """Một lần chạy → `{lai_pt, mua_giu_pt, thang_boss, so_dong, sach, sut_giam}`.

    `sach` = chạy trọn và có ít nhất một lệnh đóng: cỗ máy không bao giờ giao dịch thì
    "không thua" chẳng nói lên điều gì. Thiếu giá boss (khoảng ngày không có nến) thì
    không ai thắng ai — `thang_boss` False."""
    tk = meta.get("thong_ke") or {}
    lai = float(tk.get("lai_pt") or 0.0)
    mg = meta.get("mua_giu_pt")
    so_dong = int(tk.get("so_dong") or 0)
    return {"lai_pt": round(lai, 2),
            "mua_giu_pt": None if mg is None else round(float(mg), 2),
            "thang_boss": mg is not None and lai > float(mg),
            "so_dong": so_dong,
            "sach": so_dong >= 1,
            "sut_giam": round(float(tk.get("drawdown_pt") or 0.0), 2)}


def sao(thay, an=None):
    """Số sao từ phần chấm của màn đã thấy (▶ đầy đủ) và, nếu đã nộp, của màn ẩn."""
    if not thay or not thay.get("sach"):
        return 0
    if not thay.get("thang_boss"):
        return 1
    if not an or not an.get("thang_boss"):
        return 2
    return 3


# ---------------------------------------------------------------------------
# Sổ
# ---------------------------------------------------------------------------
def _duong_so():
    return os.path.join(luu_tru.goc(), FILE_SO)


def _doc_so():
    try:
        with open(_duong_so(), encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("man", {})
            d.setdefault("lan_chay", [])
            d.setdefault("da_xem_truyen", [])
            return d
    except (OSError, ValueError):
        pass
    return {"phien_ban": 2, "man": {}, "lan_chay": [], "da_xem_truyen": []}


def _ghi_so(d):
    luu_tru.ghi_json_nguyen_tu(_duong_so(), d)


def _bay_gio():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def ghi_lan(ban_ghi):
    """Một lượt chạy QC vào lịch sử (mới nhất đầu). `ban_ghi` do `qc_chay` dựng."""
    with _khoa:
        d = _doc_so()
        d["lan_chay"].insert(0, {"t": _bay_gio(), **ban_ghi})
        del d["lan_chay"][GIU_LICH_SU:]
        _ghi_so(d)


def ghi_day_du(man_id, van_tay, ten, ket, duong):
    """▶ đầy đủ của một cỗ máy trên một màn — vé để được nộp cỗ máy đó."""
    with _khoa:
        d = _doc_so()
        mm = d["man"].setdefault(man_id, {"day_du": {}, "nop": []})
        mm["day_du"][van_tay] = {"t": _bay_gio(), "ten": ten, **ket, "duong": duong}
        # Giữ 50 cỗ máy gần nhất — đủ để quay lại nộp, không phình sổ.
        if len(mm["day_du"]) > 50:
            for k in sorted(mm["day_du"], key=lambda k: mm["day_du"][k]["t"])[:-50]:
                del mm["day_du"][k]
        _ghi_so(d)


def ve_nop(man_id, van_tay):
    """Phần chấm ▶ đầy đủ của đúng cỗ máy này trên màn này — hoặc None (chưa được nộp)."""
    with _khoa:
        return copy.deepcopy(_doc_so()["man"].get(man_id, {}).get("day_du", {}).get(van_tay))


def ghi_nop(man_id, ban_ghi):
    """Một lần nộp. Trả số thứ tự lần nộp (1, 2, …) — game đếm số lần nộp (D-06)."""
    with _khoa:
        d = _doc_so()
        mm = d["man"].setdefault(man_id, {"day_du": {}, "nop": []})
        mm["nop"].append({"t": _bay_gio(), **ban_ghi})
        _ghi_so(d)
        return len(mm["nop"])


def tien_do_man(man_id):
    """Tóm tắt một màn cho giao diện: số lần nộp, sao cao nhất, lần nộp tốt nhất."""
    with _khoa:
        mm = _doc_so()["man"].get(man_id) or {}
    nop = mm.get("nop") or []
    tot = max(nop, key=lambda x: (x.get("sao", 0), -x.get("do_gon", {}).get("tong", 1e9)),
              default=None)
    return {"so_lan_nop": len(nop), "sao": tot.get("sao", 0) if tot else 0,
            "tot_nhat": tot, "lan_cuoi": nop[-1] if nop else None}


def hoan_thanh(man_id):
    """Màn đã xong = đã nộp ít nhất một lần được ★ (chạy sạch)."""
    return tien_do_man(man_id)["sao"] >= 1


def chuong_mo(chuong_id):
    """Chương 1 mở sẵn; chương sau mở khi xong MỌI màn của chương trước (y Opus Magnum).
    Chương "sắp ra mắt" chưa có màn nào thì luôn khoá."""
    c = chuong(chuong_id)
    if c.get("mo_san"):
        return True
    if c.get("sap_ra_mat"):
        return False
    k = [x["id"] for x in CHUONG].index(chuong_id)
    truoc = CHUONG[k - 1]["id"]
    return all(hoan_thanh(m["id"]) for m in MAN if m["chuong"] == truoc)


def man_mo(man_id):
    """Màn đầu chương mở sẵn (nếu chương mở); màn sau mở khi màn TRƯỚC NÓ đã xong.

    Opus Magnum cho chọn nhiều câu đố trong một chương; ta đi tuần tự vì mỗi màn dạy
    một thứ màn sau cần (giác quan mở dần)."""
    m = man(man_id)
    if not chuong_mo(m["chuong"]):
        return False
    cung = [x for x in MAN if x["chuong"] == m["chuong"]]
    k = cung.index(m)
    return k == 0 or hoan_thanh(cung[k - 1]["id"])


def danh_sach_man(van_tay_may=None):
    """Mọi màn cho giao diện. Có `van_tay_may` (cỗ máy đang mở) thì kèm `ve_nop` — phần
    chấm ▶ đầy đủ của ĐÚNG cỗ máy đó, hoặc None: giao diện bật/tắt nút Nộp theo nó."""
    return [{**man_cong_khai(m), "tien_do": tien_do_man(m["id"]), "mo": man_mo(m["id"]),
             "ve_nop": ve_nop(m["id"], van_tay_may) if van_tay_may else None} for m in MAN]


def danh_sach_chuong(van_tay_may=None):
    """Mọi chương, mỗi chương mang màn của nó — cho màn hình chọn màn."""
    ds = danh_sach_man(van_tay_may)
    ra = []
    for c in CHUONG:
        man_c = [m for m in ds if m["chuong"] == c["id"]]
        ra.append({"id": c["id"], "so": c["so"], "ten": c["ten"], "ban_do": c["ban_do"],
                   "symbol": c["symbol"], "mo": chuong_mo(c["id"]),
                   "sap_ra_mat": bool(c.get("sap_ra_mat")), "mo_ta": c.get("mo_ta", ""),
                   "khach": NHAN_VAT.get(c.get("khach")) if c.get("khach") else None,
                   "khach_id": c.get("khach"),
                   "man": man_c,
                   "sao": sum(m["tien_do"]["sao"] for m in man_c),
                   "sao_toi_da": 3 * len(man_c)})
    return ra


def man_tiep_theo():
    """Màn nên chơi tiếp: màn mở đầu tiên chưa đủ ★★★, không có thì màn mở cuối cùng."""
    mo = [m for m in MAN if man_mo(m["id"])]
    for m in mo:
        if tien_do_man(m["id"])["sao"] < 3:
            return m["id"]
    return mo[-1]["id"] if mo else None


def truyen(chuong_id, phan="mo"):
    """Hội thoại mở / đóng chương: `[{ai, ten, vai, loi}]`."""
    c = chuong(chuong_id)
    return [{"ai": ai, **NHAN_VAT[ai], "loi": loi} for ai, loi in c.get(f"truyen_{phan}", ())]


def da_xem_truyen(khoa):
    with _khoa:
        return khoa in _doc_so()["da_xem_truyen"]


def danh_dau_xem_truyen(khoa):
    with _khoa:
        d = _doc_so()
        if khoa not in d["da_xem_truyen"]:
            d["da_xem_truyen"].append(khoa)
            _ghi_so(d)


def lich_su(n=GIU_LICH_SU):
    with _khoa:
        return copy.deepcopy(_doc_so()["lan_chay"][:n])


def lich_su_man(man_id):
    """Mọi lượt ▶ đầy đủ trên màn này (mới nhất đầu) — chất liệu cho ba histogram."""
    return [x for x in lich_su() if x.get("man") == man_id and x.get("loai") == "day_du"]


def van_tay(doc):
    """Vân tay cỗ máy — cùng hàm với nhật ký, để "đúng cỗ máy đó" là một định nghĩa."""
    return nk._van_tay(core.normalize_process(doc))
