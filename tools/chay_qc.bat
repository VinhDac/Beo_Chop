@echo off
REM Chay mot so do tren QuantConnect qua API (tools\chay_qc.py). Can goi Researcher
REM va khoa API dat NGOAI repo: bien moi truong QC_USER_ID / QC_API_TOKEN hoac
REM du_lieu\qc_khoa.json. Vi du: tools\chay_qc.bat --tu 2025-10-01 --den 2025-12-31
cd /d "%~dp0.."
.venv\Scripts\python.exe tools\chay_qc.py %*
pause
