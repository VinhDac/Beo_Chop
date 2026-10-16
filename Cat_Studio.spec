# -*- mode: python ; coding: utf-8 -*-
"""Đóng gói Cat_Studio bằng PyInstaller.

    python -m PyInstaller Cat_Studio.spec --noconfirm

CHỌN onedir CHỨ KHÔNG onefile — quyết định, không phải mặc định:

  · onefile giải nén TOÀN BỘ gói (numpy + cây DLL .NET của pythonnet) vào
    một thư mục tạm ở MỖI LẦN MỞ. Với payload cỡ này là vài giây chờ trước khi thấy cửa
    sổ, lần nào cũng vậy — ấn tượng đầu tiên tệ mà chẳng đổi lại được gì.
  · onedir mở gần như tức thì, và nhìn vào thư mục là thấy ngay có gì trong đó.

DỮ LIỆU NGƯỜI DÙNG (`du_lieu/`) nằm CẠNH .exe, không nằm trong gói: `luu_tru.thu_muc_app`
trả `dirname(sys.executable)` khi đóng gói. Còn giao diện đã build thì đi TRONG gói và
đọc qua `luu_tru.thu_muc_goi()`. Trộn hai chỗ là hoặc mất dữ liệu, hoặc không thấy
giao diện — xem chú thích ở hai hàm đó.

`console=False`: bản đóng gói không có cửa sổ console, nên mọi lỗi lúc khởi động đã được
`app_web` báo bằng MessageBox thay vì print.
"""

a = Analysis(
    ["app_web.py"],
    pathex=[],
    binaries=[],
    # Giao diện đã build. Không có nó thì app mở ra một cửa sổ trắng.
    # Và NGUỒN .py của gói `cat_studio`: đường chạy QuantConnect gửi code lên QC dưới
    # dạng CHỮ, mà bản đóng gói chỉ giữ bytecode — không khai ở đây thì ▶ QC sẽ hỏng
    # "không thấy file". Đường chạy mới (D-11) chưa dựng, nhưng nó cũng sẽ cần đúng thế.
    # ⚠ D-12: đã bỏ `lean/` và `cat_studio/kho/` khỏi đây — hai thư mục ấy không còn,
    # mà PyInstaller báo lỗi NGAY khi một đường dẫn trong `datas` không tồn tại.
    datas=[("webui/dist", "webui/dist"),
           ("cat_studio/*.py", "cat_studio")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Bỏ thứ không dùng cho nhẹ gói. `tkinter` từng là giao diện cũ, giờ đã bỏ hẳn.
    excludes=["tkinter", "matplotlib", "PIL", "pytest", "IPython"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Cat_Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # UPX hay bị antivirus báo nhầm — không đáng đổi lấy vài MB
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="webui/public/favicon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Cat_Studio",
)
