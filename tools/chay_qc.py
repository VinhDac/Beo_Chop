"""CHẠY MỘT SƠ ĐỒ TRÊN QUANTCONNECT — một lệnh, không mở web QC.  (slice 3 · D-06)

    tools\\chay_qc.bat                                     sơ đồ mẫu D_02, cả năm 2025
    tools\\chay_qc.bat du_lieu\\chien_luoc\\X.json          một chiến lược đã lưu
    tools\\chay_qc.bat --tu 2025-10-01 --den 2025-12-31    ▶ nhanh (D-03)

Trọn một lượt ▶: đóng gói (`tools/dong_goi_lean.py`) → đẩy lên project «Cat Studio/<tên
sơ đồ>» trên QC → biên dịch → backtest → tải nhật ký về `du_lieu/nhat_ky/` → in tổng kết.
Mọi chuyện nói với QuantConnect nằm ở `cat_studio/qc_api.py`; file này chỉ nối các bước
và in ra.

CẦN (D-06)
----------
* Gói Researcher trở lên — gói Free không có API.
* Khoá API đặt NGOÀI repo: hai biến môi trường QC_USER_ID / QC_API_TOKEN, hoặc file
  `du_lieu/qc_khoa.json` dạng {"user_id": "...", "token": "..."} (`du_lieu/` nằm trong
  .gitignore). Khoá có toàn quyền tài khoản, kể cả live — công cụ này chỉ dùng nó để
  chạy backtest, và không bao giờ in nó ra.
"""
import argparse
import os
import sys
import time
from datetime import datetime

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, "tools"))
import dong_goi_lean as dgl  # noqa: E402  (nó tự thêm gốc repo và lean/ vào sys.path)

import cat_lean  # noqa: E402
from cat_studio import bo_chay, core, goi_qc, luu_tru, qc_api  # noqa: E402
from cat_studio import nhat_ky as nk  # noqa: E402

#: Trần mỗi file của gói Researcher (64 KB, chừa lề) — một chỗ khai, ở bộ đóng gói.
GIOI_HAN_RESEARCHER = goi_qc.GIOI_HAN_RESEARCHER
_so = cat_lean._so


def _hong(loi):
    print(f"\n✘ {loi}", flush=True)
    return 1


def main(argv=None, qc=None, thu_muc_nhat_ky=None):
    """Trả mã thoát: 0 là xong, 1 là hỏng (đã in lý do bằng tiếng Việt).

    `qc`, `thu_muc_nhat_ky` để bài kiểm thay bằng máy chủ giả và thư mục tạm."""
    ap = argparse.ArgumentParser(description="Chạy một sơ đồ Cat Studio trên QuantConnect.")
    ap.add_argument("so_do", nargs="?", help="file chiến lược .json (bỏ trống = sơ đồ mẫu D_02)")
    ap.add_argument("--tu", default=dgl.CAU_HINH_MAC_DINH["tu"], help="ngày bắt đầu YYYY-MM-DD")
    ap.add_argument("--den", default=dgl.CAU_HINH_MAC_DINH["den"], help="ngày kết thúc YYYY-MM-DD")
    ap.add_argument("--symbol", default=dgl.CAU_HINH_MAC_DINH["symbol"])
    ap.add_argument("--gioi-han", type=int, default=GIOI_HAN_RESEARCHER,
                    help="trần mỗi file (byte) — Researcher 62000, Team 126000")
    a = ap.parse_args(argv)
    moc = time.monotonic()

    # Ngày gõ sai thì báo NGAY — để QC báo thì phải chờ đóng gói, đẩy file, dựng máy, rồi
    # nhận về một câu tiếng Anh.
    try:
        tu, den = (datetime.strptime(x, "%Y-%m-%d") for x in (a.tu, a.den))
    except ValueError:
        return _hong(f"Ngày phải dạng YYYY-MM-DD, vd. 2025-10-01 (đang là --tu {a.tu} "
                     f"--den {a.den}).")
    if tu > den:
        return _hong(f"--tu {a.tu} nằm SAU --den {a.den}.")

    # Khoá trước tiên: thiếu khoá thì báo ngay, khỏi chờ đóng gói.
    if qc is None:
        try:
            qc = qc_api.QC(*qc_api.doc_khoa())
        except qc_api.LoiQC as e:
            return _hong(e)
    try:
        doc = dgl.so_do(a.so_do)
    except (OSError, ValueError) as e:
        return _hong(f"Đọc sơ đồ không được: {e}")

    nhan = f"{a.symbol} {a.tu} → {a.den}"
    print(f"Cat Studio → QuantConnect · «{doc.get('name') or 'sơ đồ'}» · {nhan}", flush=True)
    try:
        # Khoá nhật ký RIÊNG cho lượt này — nhúng vào gói, app đọc đúng khoá đó rồi xoá.
        khoa = nk.khoa_qc(core.normalize_process(doc), qc_api.ma_luot())
        files = dgl.dong_goi(doc, {"tu": a.tu, "den": a.den, "symbol": a.symbol,
                                   "khoa": khoa}, a.gioi_han)
    except bo_chay.LoiChay as e:
        return _hong(f"Sơ đồ chưa chạy được: {e}")
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
        kq = qc_api.chay(qc, doc, files, ten_bt,
                         thu_muc_nhat_ky or luu_tru.thu_muc_nhat_ky(), bao, khoa=khoa)
    except qc_api.LoiQC as e:
        return _hong(e)

    meta, tk = kq["meta"], kq["meta"]["thong_ke"]
    print(f"\n✔ XONG sau {_so(time.monotonic() - moc)} giây.")
    for dong in cat_lean.dong_ket_qua(nhan, tk, meta["dem"], meta["tf"], meta.get("giay_chay")):
        print("  " + dong)
    print(f"  Vốn {_so(tk['von_dau'])} → {_so(tk['von_cuoi'])} ({_so(tk['lai_pt'], 2)}%)")
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
