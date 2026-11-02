@echo off
REM =====================================================================
REM Khoi chay Zalo Bot (Long Polling) - Chuyen vien Ao Dang uy xa Cong Hai
REM =====================================================================

cd /d "%~dp0"
title Zalo Bot - Chuyen vien Ao Van phong Dang uy xa Cong Hai

echo =====================================================================
echo    KHOI CHAY ZALO BOT (LONG POLLING LOCALHOST)
echo    Chuyen vien Ao Van phong Dang uy xa Cong Hai
echo =====================================================================
echo.

REM Uu tien chay bang moi truong ao .venv
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" scripts\run_zalo_bot.py
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python scripts\run_zalo_bot.py
    goto end
)

echo [LOI] Khong tim thay Python trong moi truong ao .venv hoac he thong!
pause
exit /b 1

:end
pause

