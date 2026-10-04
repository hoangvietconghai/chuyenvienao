@echo off
REM =====================================================================
REM Khoi chay He thong Chuyen vien Ao Van phong Dang uy xa Cong Hai
REM =====================================================================

cd /d "%~dp0"
title Chuyen vien Ao - Van phong Dang uy xa Cong Hai

echo =====================================================================
echo    HE THONG CHUYEN VIEN AO VAN PHONG DANG UY XA CONG HAI
echo    Khoi dong may chu Local tai http://127.0.0.1:8000
echo =====================================================================
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    python run.py
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 run.py
    goto end
)

echo [LOI] Khong tim thay Python trong he thong PATH!
echo Vui long cai dat Python 3.10 tro len.
pause
exit /b 1

:end
pause
