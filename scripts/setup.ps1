# PCI Operation Optimization - Initial Setup (PowerShell)
$Host.UI.RawUI.WindowTitle = "PCI Setup"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PCI Operation Optimization - Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot\..

# Backend setup
Write-Host "[1/4] Setting up backend virtual environment..." -ForegroundColor Yellow
Set-Location backend

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host "[2/4] Backend setup complete." -ForegroundColor Green

# Frontend setup
Write-Host "[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location ..\frontend
npm install

Write-Host "[4/4] Frontend setup complete." -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Check backend\.env and frontend\.env" -ForegroundColor Gray
Write-Host "    2. Run: .\scripts\start-dev.ps1" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit"
