# =====================================================================
# Script khởi chạy Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải (PowerShell)
# =====================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location $PSScriptRoot

if (Get-Command python -ErrorAction SilentlyContinue) {
    python run.py
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 run.py
} else {
    Write-Host "[LỖI] Không tìm thấy Python trong hệ thống PATH!" -ForegroundColor Red
    pause
}
