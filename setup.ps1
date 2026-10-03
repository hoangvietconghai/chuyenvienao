# setup.ps1
# Script khoi tao moi truong tu dong bang PowerShell
# Ap dung cho: Chuyen vien ao Van phong Dang uy xa Cong Hai

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "   CHUYEN VIEN AO VAN PHONG DANG UY XA CONG HAI, TINH KHANH HOA" -ForegroundColor Cyan
Write-Host "              CHUONG TRINH KHOI TAO MOI TRUONG TU DONG (POWERSHELL)" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiem tra Python
Write-Host "[1/4] Kiem tra moi truong Python tren he thong..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[LOI] Chua tim thay Python tren may tinh." -ForegroundColor Red
    Write-Host "Vui long tai va cai dat Python 3.10+ tu https://www.python.org/ (Nho tich chon Add Python to PATH)." -ForegroundColor White
    exit 1
}
$pyVer = python --version
Write-Host "    -> $pyVer (Hop le)" -ForegroundColor Green
Write-Host ""

# 2. Khoi tao moi truong ao .venv
Write-Host "[2/4] Kiem tra / Thiet lap moi truong ao (.venv)..." -ForegroundColor Yellow
$venvDir = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "    -> Dang tao moi truong ao .venv..." -ForegroundColor Gray
    python -m venv $venvDir
    Write-Host "    -> Tao moi truong ao thanh cong." -ForegroundColor Green
} else {
    Write-Host "    -> Moi truong ao .venv da san sang." -ForegroundColor Green
}
Write-Host ""

# 3. Cai dat dependencies
Write-Host "[3/4] Cai dat cac thu vien can thiet (requirements.txt)..." -ForegroundColor Yellow
$reqFile = Join-Path $PSScriptRoot "requirements.txt"
$pipExe = Join-Path $venvDir "Scripts\pip.exe"
if (Test-Path $pipExe) {
    & $pipExe install -r $reqFile
} else {
    pip install -r $reqFile
}
Write-Host "    -> Thu vien python-docx da san sang." -ForegroundColor Green
Write-Host ""

# 4. Tao thu muc dau ra
Write-Host "[4/4] Khoi tao he thong thu muc luu tru van ban du thao nam 2026..." -ForegroundColor Yellow
$folders = @("Cong_van", "Ke_hoach", "Nghi_quyet", "Quyet_dinh", "Thong_bao", "Ket_luan", "Bao_cao", "To_trinh")
foreach ($f in $folders) {
    $path = Join-Path $PSScriptRoot "van_ban_du_thao\2026\$f"
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}
Write-Host "    -> Da tao day du cac thu muc van_ban_du_thao\2026\..." -ForegroundColor Green
Write-Host ""

# Kiem tra chay demo
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Dang chay thu nghiem Engine sinh van ban Word (export_docx.py)..." -ForegroundColor Yellow
$pyExe = Join-Path $venvDir "Scripts\python.exe"
$scriptPath = Join-Path $PSScriptRoot "scripts\export_docx.py"
if (Test-Path $pyExe) {
    & $pyExe $scriptPath --demo
} else {
    python $scriptPath --demo
}
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""

Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "                   [HOAN TAT CAI DAT THANH CONG!]" -ForegroundColor Green
Write-Host " Chuyen vien ao Van phong Dang uy xa Cong Hai da san sang hoat dong 100%." -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host ""
