@echo off
REM ============================================================
REM  SONG NGU - MOT LENH cho ca app: boc cau Viet con tran vao tr(), them cho trong
REM  cho cau chua co ban tieng Anh (webui\src\tieng_anh.ts + cat_studio\tieng_anh.py),
REM  roi soat ca hai nua.
REM  Chi tiet: tools\dich_python.py  ·  webui\dich\chay.mjs
REM
REM  Chay tu THU MUC GOC:   tools\dich.bat          (them --don de bo khoa thua)
REM ============================================================
cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe tools\dich_python.py %*
