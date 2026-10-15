"""CHẠY MỘT CỖ MÁY 5 TRẠM TRÊN QUANTCONNECT — một lệnh, không mở app.  (D-10)

    tools\\chay_qc.bat                                   cỗ máy dựng sẵn «Theo EMA»
    tools\\chay_qc.bat --may bat_day_rsi                 một cỗ máy dựng sẵn khác
    tools\\chay_qc.bat du_lieu\\co_may\\X.json            một cỗ máy đã lưu
    tools\\chay_qc.bat --man kim-loai-2024               rổ + ngày của một màn Chiến dịch
    tools\\chay_qc.bat --ma EURUSD,XAUUSD --loai cfd --tu 2025-01-01 --den 2025-06-30

Trọn một lượt ▶: soát cỗ máy tại máy → đóng gói → đẩy lên project trên QC → biên dịch →
backtest → tải nhật ký về `du_lieu/nhat_ky/` → in tổng kết. Mọi chuyện nói với
QuantConnect nằm ở `cat_studio/qc_api.py`; file này chỉ nối các bước và in ra.

KHÔNG chấm sao, không ghi vé nộp: chấm là việc của app (cửa sổ Màn chơi). Đây là lối
chạy cho người muốn thử nhanh bằng dòng lệnh.

CẦN (D-06)
----------
* Gói Researcher trở lên — gói Free không có API.
* Khoá API đặt NGOÀI repo: hai biến môi trường QC_USER_ID / QC_API_TOKEN, hoặc file
  `du_lieu/qc_khoa.json` dạng {"user_id": "...", "token": "..."} (`du_lieu/` nằm trong
  .gitignore). Khoá có toàn quyền tài khoản, kể cả giao dịch thật — công cụ này chỉ dùng
  nó để chạy backtest, và không bao giờ in nó ra.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)

from cat_studio import game  # noqa: E402
from cat_studio import goi_qc  # noqa: E402
from cat_studio import luu_tru  # noqa: E402
from cat_studio import mau_tram  # noqa: E402
from cat_studio import may as M  # noqa: E402
from cat_studio import qc_api  # noqa: E402
from cat_studio import qc_chay  # noqa: E402

#: Trần mỗi file của gói Researcher (64 KB, chừa lề) — một chỗ khai, ở bộ đóng gói.
GIOI_HAN_RESEARCHER = goi_qc.GIOI_HAN_RESEARCHER


def _so(x, lam_tron=0):
    return f"{x:,.{lam_tron}f}" if x is not None else "—"


def _hong(loi):
    print(f"\n✘ {loi}", flush=True)
    return 1


def doc_may(duong, key):
    """Cỗ máy từ file, hoặc một cỗ máy dựng sẵn."""
    if duong:
        with open(duong, encoding="utf-8") as f:
            d = json.load(f)
        if not M.la_may(d):
            raise ValueError(f"«{duong}» không phải cỗ máy 5 trạm.")
        return M.chuan_hoa(d)
    return mau_tram.may_san(key)


def main(argv=None, qc=None, thu_muc_nhat_ky=None):
    """Trả mã thoát: 0 là xong, 1 là hỏng (đã in lý do bằng tiếng Việt).

    `qc`, `thu_muc_nhat_ky` để bài kiểm thay bằng máy chủ giả và thư mục tạm."""
    ap = argparse.ArgumentParser(description="Chạy một cỗ máy 5 trạm trên QuantConnect.")
    ap.add_argument("co_may", nargs="?", help="file cỗ máy .json (bỏ trống = cỗ máy dựng sẵn)")
    ap.add_argument("--may", default=mau_tram.MAY_SAN[0]["key"],
                    help="cỗ máy dựng sẵn: " + " · ".join(m["key"] for m in mau_tram.MAY_SAN))
    ap.add_argument("--man", help="lấy rổ mã, loại thị trường và khoảng ngày của một màn: "
                                  + " · ".join(m["id"] for m in game.MAN
                                               if m.get("dang") == M.DANG))
    ap.add_argument("--ma", default="EURUSD,GBPUSD,USDJPY,AUDUSD",
                    help="rổ mã, cách nhau bằng dấu phẩy")
    ap.add_argument("--loai", default="forex",
                    help="loại thị trường: " + " · ".join(qc_chay.LOAI_THI_TRUONG))
    ap.add_argument("--tu", default="2024-01-01", help="ngày bắt đầu YYYY-MM-DD")
    ap.add_argument("--den", default="2024-12-31", help="ngày kết thúc YYYY-MM-DD")
    ap.add_argument("--von", type=float, default=10_000.0)
    ap.add_argument("--gioi-han", type=int, default=GIOI_HAN_RESEARCHER,
                    help="trần mỗi file (byte) — Researcher 62000, Team 126000")
    a = ap.parse_args(argv)
    moc = time.monotonic()

    try:
        may = doc_may(a.co_may, a.may)
    except (OSError, ValueError, KeyError) as e:
        return _hong(f"Đọc cỗ máy không được: {e}")
    loi = [p for p in M.soat(may) if p["severity"] == "error"]
    if loi:
        return _hong(f"Cỗ máy còn {len(loi)} lỗi, chưa chạy được: {loi[0]['message']}")

    # Rổ + ngày: của một màn Chiến dịch, hoặc gõ tay. Soát bằng CHÍNH bộ soát của app —
    # hai nơi cùng soát là hai luật sẽ lệch nhau.
    try:
        if a.man:
            m = game.man(a.man)
            if m.get("dang") != M.DANG:
                return _hong(f"Màn «{m['ten']}» là màn của sơ đồ cũ.")
            tu, den = game.khoang(a.man, "day_du")
            ch = {"ma": game.ro_cua(m), "loai": m["loai"], "tu": tu, "den": den,
                  "von": m["von"]}
        else:
            ch = qc_chay.soat_tu_do_may({
                "ma": [x for x in a.ma.replace(";", ",").split(",") if x.strip()],
                "loai": a.loai, "tu": a.tu, "den": a.den, "von": a.von})
    except game.LoiGame as e:
        return _hong(e)

    if qc is None:
        try:
            qc = qc_api.QC(*qc_api.doc_khoa())
        except qc_api.LoiQC as e:
            return _hong(e)

    nhan = (f"{len(ch['ma'])} mã {qc_chay.LOAI_THI_TRUONG[ch['loai']]} · "
            f"{ch['tu']} → {ch['den']}")
    print(f"Cat Studio → QuantConnect · «{may.get('name')}» · {nhan}")
    print(f"  rổ: {', '.join(ch['ma'])}", flush=True)

    khoa = f"cat_studio/may-{M.van_tay(may)}-{qc_api.ma_luot()}.jsonl.gz"
    try:
        files = goi_qc.dong_goi_may(may, {**ch, "khoa": khoa}, a.gioi_han)
    except RuntimeError as e:                       # gói vượt trần file
        return _hong(f"Đóng gói không được: {e}")
    print("  gói: " + " · ".join(f"{t} {_so(len(n.encode('utf-8')) / 1024, 1)} KB"
                                 for t, n in files.items()), flush=True)

    da_bao = {"viec": None, "muoi": -1}

    def bao(viec, ti_le=None):
        """Một dòng mỗi bước; riêng backtest thì thêm một dòng mỗi 10% tiến độ."""
        muoi = -1 if ti_le is None else int(ti_le * 10 + 1e-9)
        if viec == da_bao["viec"] and muoi <= da_bao["muoi"]:
            return
        da_bao["viec"], da_bao["muoi"] = viec, muoi
        them = "" if ti_le is None else f" {ti_le * 100:.0f}%"
        print(f"  [{_so(time.monotonic() - moc, 1):>5} s] {viec}{them}", flush=True)

    ten_bt = f"{nhan} · {datetime.now():%H:%M:%S}"
    try:
        kq = qc_api.chay(qc, may, files, ten_bt,
                         thu_muc_nhat_ky or luu_tru.thu_muc_nhat_ky(), bao, khoa=khoa)
    except qc_api.LoiQC as e:
        return _hong(e)

    tk = kq["meta"].get("thong_ke") or {}
    cham = game.cham(kq["meta"])
    print(f"\n✔ XONG sau {_so(time.monotonic() - moc)} giây.")
    print(f"  Vốn {_so(tk.get('von_dau'))} → {_so(tk.get('von_cuoi'))} "
          f"({_so(cham['lai_pt'], 2)}%)")
    print(f"  Boss «mua rồi giữ cả rổ»: {_so(cham['mua_giu_pt'], 2)}% — "
          + ("THẮNG" if cham["thang_boss"] else "chưa thắng"))
    print(f"  Lệnh: {tk.get('so_lenh')} đặt · {tk.get('so_lenh_khop')} khớp · "
          f"{tk.get('so_lenh_huy')} huỷ")
    print(f"  Xem trên QC : {kq['url']}")
    print(f"  Nhật ký     : {kq['duong_nhat_ky']}", flush=True)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):          # in ra file vẫn giữ được dấu tiếng Việt
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nĐã dừng. Backtest đã gửi lên QC (nếu có) vẫn chạy nốt ở đó.")
        sys.exit(130)
