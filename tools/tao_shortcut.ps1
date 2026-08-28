# Tạo shortcut "Cat Studio" ra Desktop và cạnh mã nguồn.
#
# ⚠ FILE NÀY PHẢI LƯU KÈM BOM (UTF-8 with BOM). Windows PowerShell 5.1 đọc .ps1 theo
# bảng mã ANSI của hệ thống khi không thấy BOM, nên mọi chữ tiếng Việt vỡ thành ký tự
# lạ — dấu nháy trong chuỗi bị hiểu sai và script gãy ngay dòng đầu tiên có dấu.
#
# Dùng `pythonw.exe` chứ không phải `python.exe`: python.exe kèm theo một cửa sổ
# console đen nằm suốt bên cạnh app. Đổi lại, pythonw không có stderr để nhìn — nên
# `app_web.py` báo mọi lỗi khởi động bằng HỘP THOẠI Windows.

$goc  = Split-Path -Parent $PSScriptRoot
$icon = Join-Path $goc "assets\logo.ico"

# ƯU TIÊN .venv, nhưng LÙI VỀ PYTHON HỆ THỐNG nếu chưa dựng venv.
#
# Bản trước chết thẳng với "Chạy tools\setup.bat trước đã" — đúng luật nhưng vô ích với
# người đã có sẵn pywebview trong Python global và chỉ muốn mở app xem thử. Vẫn ưu tiên
# venv (README giải thích: `quantconnect-stubs` trong Python global chiếm namespace
# `Microsoft` và giết pywebview lúc khởi động), chỉ là không còn chặn đường.
$exe = Join-Path $goc ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $exe)) {
    # ⚠ HỎI THẲNG PYTHON NÓ NẰM ĐÂU, đừng tin `Get-Command pythonw.exe`.
    #
    # Đã dính bẫy thật ngay lần chạy đầu: `Get-Command` trả về
    #     C:\Users\<tên>\AppData\Local\Microsoft\WindowsApps\pythonw.exe
    # tức cái STUB của Microsoft Store, không phải Python thật — nó nằm trước trong
    # PATH. Stub đó có thể mở Store thay vì chạy app, và shortcut thì im lặng không
    # nói vì sao. `sys.executable` luôn trả về trình thông dịch ĐANG CHẠY, không đoán.
    $that = $null
    foreach ($ten in @("python.exe", "py.exe")) {
        $c = Get-Command $ten -ErrorAction SilentlyContinue
        if (-not $c) { continue }
        try { $that = & $c.Source -c "import sys;print(sys.executable)" 2>$null } catch { }
        if ($that -and (Test-Path $that) -and $that -notlike "*WindowsApps*") { break }
        $that = $null
    }
    if ($that) { $exe = Join-Path (Split-Path $that) "pythonw.exe" }
    if (-not $that -or -not (Test-Path $exe)) {
        Write-Host "No real pythonw.exe found (the WindowsApps stub was skipped)." -ForegroundColor Red
        Write-Host "Run tools\setup.bat first." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "! No .venv yet - falling back to system Python:" -ForegroundColor Yellow
    Write-Host "  $exe"
    Write-Host "  (a separate .venv is recommended - see README)"
}

# Kiểm cả `webui\dist`: thiếu nó thì app mở ra một cửa sổ TRẮNG và không nói vì sao.
$thieu = @($icon,
           (Join-Path $goc "app_web.py"),
           (Join-Path $goc "webui\dist\index.html")) |
         Where-Object { -not (Test-Path $_) }
if ($thieu) {
    Write-Host "Missing:" -ForegroundColor Red
    $thieu | ForEach-Object { Write-Host "  $_" }
    Write-Host "`nRun tools\setup.bat (or tools\build_ui.bat) first." -ForegroundColor Yellow
    exit 1
}

$sh = New-Object -ComObject WScript.Shell
$dich = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) "Cat Studio.lnk"),
    (Join-Path $goc "Cat Studio.lnk")
)

foreach ($d in $dich) {
    $lnk = $sh.CreateShortcut($d)
    $lnk.TargetPath       = $exe
    $lnk.Arguments        = "app_web.py"
    $lnk.WorkingDirectory = $goc          # bắt buộc: app_web.py tìm webui\dist theo đây
    $lnk.IconLocation     = "$icon,0"
    # KHÔNG dấu tiếng Việt ở đây: WScript.Shell ghi trường mô tả của .lnk bằng ANSI,
    # nên mọi ký tự ngoài bảng mã hệ thống biến thành "?" — đã đo. Tên file shortcut
    # thì lưu Unicode bình thường, chỉ riêng trường này.
    $lnk.Description      = "Cat Studio - trading strategy diagram editor"
    $lnk.WindowStyle      = 1
    $lnk.Save()
    Write-Host "OK  $d" -ForegroundColor Green
}

Write-Host ""
Write-Host "Target: $exe" -ForegroundColor DarkGray
