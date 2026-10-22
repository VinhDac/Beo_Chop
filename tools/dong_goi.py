# -*- coding: utf-8 -*-
"""Đóng gói Cat Studio cho Windows.

    .venv\\Scripts\\python.exe tools\\dong_goi.py

Ra hai thứ trong `dist/`, cùng một số phiên bản:

    Cat_Studio-<ver>-windows-x64-setup.exe   bản CÀI — một tệp đưa cho người khác
    Cat_Studio-<ver>-windows-x64.zip         bản XÁCH TAY — giải nén chỗ nào cũng chạy

VÌ SAO CÓ BẢN CÀI chứ không chỉ một tệp .zip: một thư mục 112 tệp giải nén ra Desktop
thì không có lối gỡ, không có mục trong Start, không có gì trong «Apps & features», và
người dùng tự xoay xở chỗ để nó. Bản cài lo cả bốn — và vẫn KHÔNG ĐÒI QUYỀN QUẢN TRỊ:
nó đặt vào `%LOCALAPPDATA%\\Programs`, nơi người dùng tự ghi được. Đặt vào
`Program Files` thì vừa phải xin quyền, vừa hỏng thật: app ghi `du_lieu\\` NGAY CẠNH
tệp .exe, mà chỗ ấy thì người dùng thường không có quyền ghi.

⚠ CỔNG CHẶN LÀ PHẦN QUAN TRỌNG NHẤT CỦA TỆP NÀY, không phải mấy lệnh gọi PyInstaller.
Xem `_goi_sach`: nó TỪ CHỐI đóng gói nếu gói mang theo thứ của người build. Khoá
QuantConnect có toàn quyền tài khoản, kể cả giao dịch thật — phát hành nhầm một bản có
`du_lieu\\qc_khoa.json` thì không thu lại được, và không có lỗi nào báo trước.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
DIST = GOC / "dist"
TEN = "Cat_Studio"
TEN_DEP = "Cat Studio"

#: Bộ dựng bản cài. Không có nó thì vẫn ra bản xách tay, chỉ thiếu tệp .exe cài đặt.
ISCC = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe",
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
]

#: ⚠ DẤU VẾT CỦA NGƯỜI BUILD. Tên tệp, và chuỗi nằm TRONG tệp chữ.
RAC_TEN = ("qc_khoa.json", "cai_dat.json", "ban_nhap.json", "so_diem.json",
           "hanh_trinh.json", ".log")
RAC_THU_MUC = ("du_lieu", "ket_qua", "strategy", "__pycache__", ".venv", ".git")


def phien_ban() -> str:
    """Số phiên bản, đọc từ CHỖ DUY NHẤT khai nó."""
    s = (GOC / "cat_studio" / "core.py").read_text(encoding="utf-8")
    return re.search(r'PHIEN_BAN\s*=\s*"([^"]+)"', s).group(1)


def _chay(lenh, **kw) -> int:
    print("  $", " ".join(str(x) for x in lenh))
    return subprocess.call([str(x) for x in lenh], cwd=str(GOC), **kw)


def _goi_sach(thu_muc: Path) -> list[str]:
    """Thứ KHÔNG ĐƯỢC PHÉP có trong gói. -> danh sách đường dẫn bẩn (rỗng là sạch).

    ⚠ BA NGẢ, và ngả thứ ba là ngả không ai nghĩ tới:

      ① TÊN TỆP — `qc_khoa.json` mang khoá QuantConnect có toàn quyền tài khoản, kể cả
         giao dịch thật. `cai_dat.json` mang đường dẫn LEAN trên máy người build.
      ② TÊN THƯ MỤC — `du_lieu/`, `ket_qua/` là chiến thuật và lịch sử chạy của người
         build; `__pycache__/` thì chỉ là rác nhưng rác ấy có thể nhúng đường dẫn tuyệt
         đối trong traceback.
      ③ ĐƯỜNG DẪN THƯ MỤC NHÀ NẰM TRONG TỆP CHỮ. Đây là ngả JobA-Z canh, và nó bắt được
         thứ hai ngả trên bỏ sót: một tệp tên vô hại, nằm chỗ vô hại, mà bên trong có
         `C:\\Users\\<tên thật>` — lộ tên người dùng Windows, và đôi khi lộ cả bố cục
         máy. Người nhận gói mở một tệp chữ bất kỳ ra là thấy.
    """
    nha = str(Path.home()).rstrip("\\/")
    dau = nha.lower().encode()
    ban = []
    for f in thu_muc.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(thu_muc).as_posix()
        if any(p in RAC_THU_MUC for p in rel.split("/")[:-1]):
            ban.append(f"{rel}  (thư mục cấm)")
            continue
        if f.name in RAC_TEN or f.name.endswith(".log"):
            ban.append(f"{rel}  (tên cấm)")
            continue
        if f.suffix.lower() in (".py", ".json", ".txt", ".cmd", ".bat", ".html",
                                ".js", ".css", ".iss", ".md"):
            try:
                if dau in f.read_bytes().lower():
                    ban.append(f"{rel}  (có đường dẫn thư mục nhà)")
            except OSError:
                pass
    return ban


DOC_TRUOC = """CAT STUDIO {ver} - ve so do, LEAN chay no
{gach}

CACH DUNG: bam dup vao {ten}.exe
LUU Y: giu nguyen ca thu muc nay, dung tach rieng file .exe ra.

DU LIEU CUA BAN - so do, ban nhap, lich su chay, so diem - nam trong thu muc
du_lieu\\ ngay canh file .exe. Muon chuyen sang may khac thi chep ca thu muc
do di theo. Go cai dat KHONG xoa thu muc nay.

CAN CO:
  - Microsoft Edge WebView2 Runtime (Windows 10/11 co san cung Edge)
  - Mot ban LEAN tren cung may. Mo Cai dat trong app roi tro vao thu muc goc
    cua no (cho co Launcher\\ va Data\\). App cung tu tim mot thu muc ten Lean\\
    dat ngay canh file .exe, neu ban muon de kem.

KHONG CO LEAN THI SAO: van ve duoc so do, van sinh ra duoc main.py, nhung bam
Backtest se bao chua co LEAN. Mo Cai dat de tro duong dan.

KHOA QUANTCONNECT: neu ban dat khoa trong app, no nam o du_lieu\\qc_khoa.json
tren may ban va khong di dau ca. Khoa do co toan quyen tai khoan - dung chia
cho ai, va dung chep thu muc du_lieu\\ cho nguoi khac.
"""

ISS = """; Bản cài Cat Studio — do `tools/dong_goi.py` sinh ra, đừng sửa tay.
[Setup]
; GUID của bản cài — xem lời dẫn ở chỗ truyền `appid` bên Python.
AppId={appid}
AppName={ten_dep}
AppVersion={ver}
AppPublisher=Cat Studio
DefaultDirName={{localappdata}}\\Programs\\{ten_dep}
DefaultGroupName={ten_dep}
DisableProgramGroupPage=yes
; KHÔNG đòi quyền quản trị: app ghi du_lieu\\ ngay cạnh .exe, nên nó phải nằm ở
; chỗ người dùng tự ghi được. Đặt vào Program Files là vừa xin quyền vừa hỏng.
PrivilegesRequired=lowest
OutputDir={out}
OutputBaseFilename={ten}-{ver}-windows-x64-setup
SetupIconFile={icon}
UninstallDisplayIcon={{app}}\\{ten}.exe
UninstallDisplayName={ten_dep} {ver}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "{nguon}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{ten_dep}"; Filename: "{{app}}\\{ten}.exe"
Name: "{{group}}\\Uninstall {ten_dep}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{ten_dep}"; Filename: "{{app}}\\{ten}.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{ten}.exe"; Description: "Open {ten_dep}"; Flags: nowait postinstall skipifsilent

; ⚠ GỠ CÀI ĐẶT KHÔNG ĐƯỢC XOÁ du_lieu\\. Đó là sơ đồ, bản nháp và sổ điểm của người
; dùng — thứ họ mất là mất hẳn. Inno chỉ xoá những gì nó đã chép vào, nên chỉ cần
; KHÔNG khai thêm gì ở đây; dòng này để lần sau ai định thêm `[UninstallDelete]` thì
; đọc được vì sao đừng.
"""


def main() -> int:
    ver = phien_ban()
    goi = DIST / TEN
    print(f"\n=== Đóng gói {TEN_DEP} {ver} ===\n")

    print("[1/6] Dừng bản đang chạy…")
    subprocess.call(["taskkill", "/IM", f"{TEN}.exe", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(goi, ignore_errors=True)
    # ⚠ DỌN LUÔN BẢN CŨ TRONG dist/. Nếu lượt này bị cổng chặn mà bản lần trước vẫn
    # nằm đó, thư mục dist/ trông y như vừa đóng gói xong — và người ta phát hành đúng
    # cái bản cũ ấy. Xoá trước thì «không có tệp nào» là câu trả lời rõ ràng.
    for cu_ in DIST.glob(f"{TEN}-*-windows-x64*"):
        cu_.unlink(missing_ok=True)

    print("[2/6] Dựng giao diện web…")
    if _chay(["npm", "--prefix", "webui", "run", "build"], shell=True):
        print("\n  *** KHÔNG ĐÓNG GÓI: dựng giao diện hỏng.")
        return 1

    print("[3/6] Chạy cổng…")
    if _chay([sys.executable, "tests/chay_tat_ca.py"]):
        print("\n  *** KHÔNG ĐÓNG GÓI: cổng đỏ. Sửa xong rồi chạy lại.")
        return 1

    print("[4/6] PyInstaller…")
    if _chay([sys.executable, "-m", "PyInstaller", "Cat_Studio.spec",
              "--noconfirm", "--clean"]):
        print("\n  *** KHÔNG ĐÓNG GÓI: PyInstaller hỏng.")
        return 1
    (goi / "DOC-TRUOC-KHI-CHAY.txt").write_text(
        DOC_TRUOC.format(ver=ver, ten=TEN, gach="=" * 42).replace("\n", "\r\n"),
        encoding="ascii", errors="replace")

    print("[5/6] Soát gói có dính gì của máy này không…")
    ban = _goi_sach(goi)
    if ban:
        print("\n  *** KHÔNG PHÁT HÀNH: gói này mang theo thứ của máy build:")
        for x in ban[:20]:
            print("      " + x)
        if len(ban) > 20:
            print(f"      … và {len(ban) - 20} tệp nữa")
        return 1
    print("      sạch.")

    print("[6/6] Bản cài và bản xách tay…")
    DIST.mkdir(exist_ok=True)
    zip_ra = DIST / f"{TEN}-{ver}-windows-x64.zip"
    zip_ra.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_ra, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(goi.rglob("*")):
            if f.is_file():
                z.write(f, f"{TEN}/{f.relative_to(goi).as_posix()}")

    cai_ra = None
    iscc = next((p for p in ISCC if p.is_file()), None)
    if iscc:
        iss = DIST / "cat_studio.iss"
        iss.write_text(ISS.format(
            # ⚠ GUID ĐI NGUYÊN CẢ CẶP NGOẶC TỪ ĐÂY, không ghép ngoặc trong khuôn chữ.
            # Inno đọc ngoặc nhọn là HẰNG của nó, nên AppId bọc một lớp ngoặc là lỗi
            # «Unknown constant»; phải bọc hai lớp, lớp ngoài là dấu ngoặc thật. Mà
            # khuôn chữ của Python cũng ăn ngoặc nhọn, nên ghép ở trong khuôn là hai
            # lớp thoát chồng nhau — đếm nhầm một dấu là hỏng, và đã hỏng thật.
            # ⚠ VÀ GUID NÀY PHẢI ĐỨNG YÊN MÃI MÃI: Windows nhận ra bản cũ để nâng cấp
            # và gỡ bằng chính nó. Đổi nó là mỗi bản mới thành một app riêng, chồng
            # lên nhau trong «Apps & features», gỡ cái này không đụng cái kia.
            appid="{{A6F1C4E2-7B3D-4E55-9C21-CA7570D10B42}",
            ten=TEN, ten_dep=TEN_DEP, ver=ver,
            out=str(DIST), nguon=str(goi),
            icon=str(GOC / "webui" / "public" / "favicon.ico"),
        ), encoding="utf-8")
        if _chay([iscc, str(iss)]):
            print("\n  *** Bản cài hỏng (bản xách tay vẫn có).")
        else:
            cai_ra = DIST / f"{TEN}-{ver}-windows-x64-setup.exe"
        iss.unlink(missing_ok=True)
    else:
        print("      (không thấy Inno Setup — bỏ qua bản cài)")

    shutil.rmtree(GOC / "build", ignore_errors=True)
    mb = lambda p: f"{p.stat().st_size / 1e6:.1f} MB"           # noqa: E731
    print(f"\n  Xong {TEN_DEP} {ver}")
    if cai_ra and cai_ra.is_file():
        print(f"  Bản cài:     {cai_ra}   ({mb(cai_ra)})")
    print(f"  Xách tay:    {zip_ra}   ({mb(zip_ra)})")
    print(f"  Thư mục:     {goi}\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
