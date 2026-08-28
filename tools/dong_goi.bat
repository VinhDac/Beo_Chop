@echo off
REM ============================================================
REM  Dong goi Cat_Studio -> dist\Cat_Studio\ + dist\Cat_Studio-windows.zip
REM  (moi san pham build deu nam trong dist\, thu muc goc khong giu gi)
REM
REM  Chay tu THU MUC GOC:   tools\dong_goi.bat
REM
REM  DUNG PYTHON TRONG .venv, khong dung Python global: goi
REM  quantconnect-stubs o Python global ship mot thu muc "Microsoft" chiem
REM  namespace .NET. Ma nguon da co _uu_tien_namespace_dotnet() de chua, nhung
REM  dong goi bang moi truong sach thi goi nhe hon va khong keo theo rac.
REM
REM  GIU --onedir (khai trong Cat_Studio.spec): ban gop-1-file giai nen ca cay
REM  DLL .NET vao thu muc tam moi lan mo -> cho vai giay moi thay cua so.
REM  Ban Auto_Clicker con bi Defender bao nham Trojan voi ban onefile.
REM ============================================================
cd /d "%~dp0.."

set PY=.venv\Scripts\python.exe
if not exist %PY% (
    echo *** No .venv found - run this first:
    echo     python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt pyinstaller
    pause
    exit /b 1
)

echo [1/6] Closing the app if it is running...
taskkill /IM Cat_Studio.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul
if exist dist\Cat_Studio rmdir /S /Q dist\Cat_Studio

echo [2/6] Building the web UI (vite)...
pushd webui
call npm run build
if errorlevel 1 (
    popd
    echo *** UI BUILD FAILED ***
    pause
    exit /b 1
)
popd

echo [3/6] Running the test suite before packaging...
%PY% tests\chay_tat_ca.py
if errorlevel 1 (
    echo.
    echo *** TESTS FAILED - NOT packaging. Fix them and run again. ***
    pause
    exit /b 1
)

echo [4/6] Packaging Python...
%PY% -m PyInstaller Cat_Studio.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo *** PACKAGING FAILED ***
    pause
    exit /b 1
)

echo [5/6] Adding the read-me file...
REM ⚠ FILE NÀY LÀ THỨ DUY NHẤT ĐẾN TAY NGƯỜI DÙNG CUỐI, nên nó phải nói ĐÚNG.
REM Bản trước dạy "mo Cai dat, chon symbol va khoang From/To, roi bam Chay - app tu
REM tai phan con thieu tu MT5" — MT5 đã gỡ từ đợt 2, nến đã gỡ, From/To không còn.
REM Tức nó hướng dẫn một sản phẩm KHÔNG TỒN TẠI, mà không ai đọc file này khi sửa mã.
REM
REM Không dấu tiếng Việt: `echo` ghi ra .txt bằng bảng mã hệ thống của máy ĐÓNG GÓI,
REM nên chữ có dấu sẽ vỡ trên máy người nhận.
set D=dist\Cat_Studio\READ-ME-FIRST.txt
> %D% echo CAT STUDIO - draw market-making strategies and backtest them
>> %D% echo ============================================================
>> %D% echo.
>> %D% echo HOW TO RUN: double-click Cat_Studio.exe
>> %D% echo.
>> %D% echo KEEP THIS WHOLE FOLDER TOGETHER - do not pull the .exe out on its own.
>> %D% echo.
>> %D% echo Your data (strategies, recorded ticks, settings) lives in the du_lieu\
>> %D% echo folder next to the .exe. To move to another machine, copy that folder too.
>> %D% echo.
>> %D% echo REQUIRES:
>> %D% echo   - Microsoft Edge WebView2 Runtime (ships with Edge on Windows 10/11)
>> %D% echo   - .NET Framework 4.7.2 or newer
>> %D% echo.
>> %D% echo FIRST RUN - there is no data yet. Open Settings - Data source, add a
>> %D% echo symbol and press Start recording. The recorder streams live ticks to
>> %D% echo disk and must run for a while before there is anything to backtest;
>> %D% echo it keeps running in its own process after you close the app.
>> %D% echo.
>> %D% echo Then press Test to run your diagram over what has been recorded.

REM  Nen bang ZipFile.CreateFromDirectory cua .NET, KHONG dung Compress-Archive:
REM  Compress-Archive gom het vao bo nho truoc khi ghi nen voi goi 211 file / 67 MB thi
REM  no treo - da do that: chay 22 PHUT chua xong, phai kill. Ban .NET ghi thang ra dia:
REM  2,6 GIAY, ra 29,2 MB. (Auto_Clicker dung Compress-Archive duoc vi goi nho hon nhieu.)
echo [6/6] Compressing to .zip for release...
if exist dist\Cat_Studio-windows.zip del /F /Q dist\Cat_Studio-windows.zip
powershell -NoProfile -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory((Resolve-Path 'dist\Cat_Studio').Path, (Join-Path (Get-Location) 'dist\Cat_Studio-windows.zip'), [System.IO.Compression.CompressionLevel]::Optimal, $true)"
if errorlevel 1 (
    echo *** ZIP COMPRESSION FAILED ***
    pause
    exit /b 1
)

REM Don rac trung gian: build\ chi la thu muc lam viec cua PyInstaller, giu lai
REM chi to thu muc goc chu khong dung vao viec gi.
if exist build rmdir /S /Q build

echo.
echo Done!
echo    Folder : dist\Cat_Studio\
echo    Release: dist\Cat_Studio-windows.zip
echo.
pause
