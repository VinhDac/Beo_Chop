# -*- coding: utf-8 -*-
"""LUẬT CHƠI — màn ẩn, boss, ba sao, độ gọn, sổ điểm.

Một chỗ DUY NHẤT biết "điểm" là gì. Không biết giao diện, không biết LEAN chạy ra sao:
nhận kết quả một lượt đã chạy và trả lời — thắng boss không, mấy sao, gọn cỡ nào.

Chép luật từ `game.py` ở nhánh `main` (D-05 · D-06 · D-08), đổi đúng hai chỗ cho hợp
với Cat hôm nay — xem ⚠ bên dưới.

VÒNG CHƠI
---------
chọn màn → vào Xưởng lắp máy → ▶ chạy trên MÀN ĐÃ THẤY → xem lại ở màn Chạy máy → sửa
→ NỘP: app chạy đúng cỗ máy ấy trên MÀN ẨN — khoảng ngày app giữ, người chơi không bao
giờ thấy — rồi chấm sao.

SAO
---
  ⭐    chạy sạch   — chạy trọn màn đã thấy, có ít nhất MỘT lệnh đóng
  ⭐⭐   thắng boss  — và lãi % trên màn đã thấy HƠN boss cùng khoảng ấy
  ⭐⭐⭐  vẫn thắng   — và trên MÀN ẨN cũng hơn boss
Mỗi sao cần mọi sao trước nó.

⚠ VÌ SAO ⭐ ĐÒI MỘT LỆNH ĐÓNG. Cỗ máy không bao giờ giao dịch thì "không thua" chẳng
nói lên điều gì — nó chỉ ngồi im. Mà đúng luật ấy kéo theo một chuyện: MÀN 0 KHÔNG CHẤM
được. Màn 0 bảo người chơi dựng «Mua rồi giữ», mà mua rồi giữ thì không đóng lệnh nào —
nên nó mãi mãi 0 sao. Màn 0 vì thế khai `khong_cham`, và bản đồ nói rõ ra.

⚠ BOSS LÀ ĐƯỜNG BENCHMARK CỦA CHÍNH LEAN — đây là chỗ Cat khác `main`.
Bản cũ đọc lãi của boss từ một dòng meta do bộ chạy riêng ghi. Cat không có bộ chạy
riêng (D-11), và cũng KHÔNG cần: mỗi màn ép `moc_so_sanh` về đúng mã của nó, nên đường
`Benchmark` trong kết quả LEAN CHÍNH LÀ mua-rồi-giữ mã ấy, do LEAN tính. Ta chỉ lấy hai
đầu đường ấy chia cho nhau. Không tự tính lại một con số nào — chạy một lượt backtest
thứ hai chỉ để biết mua-giữ lãi bao nhiêu là làm cái việc LEAN đã làm sẵn.
"""
import json
import os

from . import core
from . import luu_tru
from .ngon_ngu import tr

FILE_SO = "so_diem.json"

#: Boss của mọi màn hiện nay. Để thành bảng vì thiết kế §3 có màn cuối đổi boss.
BOSS = {
    "mua_giu": {
        "ten": "Mua rồi giữ",
        "mo_ta": "Mua ở nến đầu tiên, giữ tới nến cuối cùng. Không làm gì khác.",
    },
}


# ---------------------------------------------------------------------------
# Chấm một lượt
# ---------------------------------------------------------------------------
def _lai_pt(kq):
    """Lãi % của cỗ máy, lấy từ `statistics` của LEAN. -> float hay None."""
    tk = (kq or {}).get("thong_ke") or {}
    for khoa in ("Net Profit", "Net Profit %"):
        if khoa in tk:
            try:
                return float(str(tk[khoa]).replace("%", "").replace(",", "").strip())
            except (TypeError, ValueError):
                return None
    return None


def boss_pt(kq):
    """Lãi % của BOSS — hai đầu đường `Benchmark` mà LEAN dựng. -> float hay None.

    Mỗi màn ép `moc_so_sanh` về mã của nó (xem `ap_man`), nên đường ấy là mua-rồi-giữ
    đúng mã ấy, đúng khoảng ấy, do LEAN tính. Thiếu đường (khoảng ngày không có nến)
    thì trả None — và lúc ấy KHÔNG AI THẮNG AI, chứ không phải người chơi thắng."""
    for bang in (kq or {}).get("bieu_do") or []:
        if bang.get("ten") != "Benchmark":
            continue
        for duong in bang.get("duong") or []:
            diem = [d for d in (duong.get("diem") or []) if d]
            if len(diem) < 2:
                continue
            dau, cuoi = _gt(diem[0]), _gt(diem[-1])
            if dau in (None, 0) or cuoi is None:
                continue
            return (cuoi - dau) / dau * 100.0
    return None


def _gt(diem):
    """Một điểm của biểu đồ -> giá trị. Nhận cả `[giờ, giá]` lẫn `{"y": giá}`."""
    if isinstance(diem, dict):
        v = diem.get("y", diem.get("gia_tri"))
    elif isinstance(diem, (list, tuple)) and len(diem) >= 2:
        v = diem[1]
    else:
        v = diem
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cham(kq):
    """Một lượt đã chạy -> {lai_pt, boss_pt, thang_boss, so_dong, sach}.

    `sach` = chạy trọn VÀ có ít nhất một lệnh đóng. `thang_boss` False khi thiếu số của
    boss: không có gì để so thì không ai thắng ai."""
    lai = _lai_pt(kq)
    bp = boss_pt(kq)
    so_dong = len((kq or {}).get("giao_dich") or [])
    return {
        "lai_pt": None if lai is None else round(lai, 2),
        "boss_pt": None if bp is None else round(bp, 2),
        "thang_boss": lai is not None and bp is not None and lai > bp,
        "so_dong": so_dong,
        "sach": bool((kq or {}).get("ok")) and so_dong >= 1,
    }


def sao(thay, an=None):
    """Số sao, từ phần chấm của màn ĐÃ THẤY và — nếu đã nộp — của màn ẨN."""
    if not thay or not thay.get("sach"):
        return 0
    if not thay.get("thang_boss"):
        return 1
    if not an or not an.get("thang_boss"):
        return 2
    return 3


def do_gon(steps):
    """Số khối (không tính Bắt đầu) + số núm đã ghim. Ít hơn là gọn hơn.

    Máy càng ít khối, càng ít núm thì càng khó bị quá khớp — nên huy chương gọn và màn
    ẩn dạy CÙNG MỘT bài học từ hai phía."""
    so_khoi = sum(1 for s in (steps or []) if not core.is_start_step(s))
    so_num = len(core.ds_tham_so([core.chuan_hoa_khoi(x) for x in (steps or [])]))
    return {"so_khoi": so_khoi, "so_num": so_num, "tong": so_khoi + so_num}


# ---------------------------------------------------------------------------
# Ép màn lên sơ đồ
# ---------------------------------------------------------------------------
def _ds_ma(man):
    """Mã của màn -> danh sách. Nhận cả một chuỗi lẫn một tuple."""
    sym = man.get("symbol")
    if isinstance(sym, str):
        return [sym]
    return list(sym or ())


def ap_man(doc, man, loai):
    """Ép mã · khoảng ngày · vốn · mốc so sánh của MÀN lên sơ đồ. -> doc mới.

    ⚠ ÉP Ở PYTHON, LÚC CHẠY — không phải dán vào ô rồi tin người chơi không sửa. Màn
    chơi mà người chơi đổi được khoảng ngày thì chẳng còn là màn nào cả, và một ô khoá
    trong giao diện chỉ là lời đề nghị: ai mở tệp sơ đồ ra sửa tay cũng qua được.
    Chặn ở đây thì không có cửa nào vòng qua.

    `loai` là "thay" (màn đã thấy) hay "an" (màn ẩn). Ngày của màn ẩn CHỈ đi qua hàm
    này — nó không bao giờ ra tới giao diện (xem `hanh_trinh.cong_khai`)."""
    khoang = man["an"] if loai == "an" else man["thay"]
    d = dict(doc or {})
    d["steps"] = [dict(s) for s in (d.get("steps") or [])]
    for s in d["steps"]:
        if not core.is_start_step(s):
            continue
        # BA DẠNG SÂN: một mã, nhiều mã, hoặc một RỔ. Khối Bắt đầu nhận cả ba ở cùng
        # một ô `ma`, nên ép ở đây là xong — không cần ba đường riêng.
        if man.get("ro"):
            s["ma"] = {"ro": man["ro"]}
        else:
            s["ma"] = [{"ma": x, "loai": man["loai_ma"]} for x in _ds_ma(man)]
        s["khoang"] = {"tu": khoang[0], "den": khoang[1]}
        s["von"] = float(man["von"])
    # MỐC SO SÁNH = mã của màn. Đây là thứ biến đường `Benchmark` của LEAN thành đúng
    # con boss — xem `boss_pt`. Thiếu nó thì LEAN lặng lẽ lấy SPY, và người chơi bị đem
    # so với cổ phiếu Mỹ trong một màn chơi vàng.
    may = dict(d.get(core.KHOA_CO_MAY) or {})
    # MỐC SO SÁNH khi màn có NHIỀU mã: lấy mã đầu, trừ khi màn tự khai `moc`. Mua-giữ
    # một rổ thì LEAN không có khái niệm ấy — phải chọn MỘT đường để làm boss, và chọn
    # cái nào thì màn phải nói rõ trong lời dặn.
    may["moc_so_sanh"] = man.get("moc") or _ds_ma(man)[0]
    d[core.KHOA_CO_MAY] = may
    return d


# ---------------------------------------------------------------------------
# Sổ điểm
# ---------------------------------------------------------------------------
def _duong_so():
    return os.path.join(luu_tru.goc(), FILE_SO)


def doc_so():
    """Sổ điểm. Hỏng hay chưa có thì coi như chưa chơi màn nào — KHÔNG ném: mất sổ chỉ
    nên làm mất tiến trình, không được chặn người ta vào trò chơi."""
    try:
        with open(_duong_so(), encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("man", {})
            return d
    except (OSError, ValueError):
        pass
    return {"phien_ban": 1, "man": {}}


def ghi_man(ma, thay=None, an=None, gon=None, qua=False):
    """Ghi kết quả một màn vào sổ. Sao tính lại từ hai phần chấm, không nhận sao gửi
    sẵn: để nơi gọi tự tính sao là mở cửa cho hai bản luật.

    GIỮ SAO CAO NHẤT. Chơi lại tệ hơn không được lấy mất sao đã ăn — không thì không ai
    dám thử một cỗ máy gọn hơn."""
    so = doc_so()
    cu = so["man"].get(ma) or {}
    s = sao(thay, an)
    so["man"][ma] = {
        "sao": max(int(cu.get("sao") or 0), s),
        "sao_lan_nay": s,
        "thay": thay or cu.get("thay"),
        "an": an or cu.get("an"),
        "gon": gon or cu.get("gon"),
        # ĐÃ CHẠY QUA. Màn không chấm không có `thay` và mãi mãi 0 sao, nên nếu
        # không có dấu này thì bản đồ không bao giờ biết nó đã xong — xem
        # `hanh_trinh.da_qua`.
        "qua": bool(qua) or bool(cu.get("qua")),
    }
    try:
        luu_tru.ghi_json_nguyen_tu(_duong_so(), so)
    except Exception:                               # noqa: BLE001
        pass
    return so["man"][ma]


def ten_boss(ma_boss):
    b = BOSS.get(ma_boss) or BOSS["mua_giu"]
    return {"ma": ma_boss, "ten": tr(b["ten"]), "mo_ta": tr(b["mo_ta"])}
