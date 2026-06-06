# PCI Operation Optimization - Backend Only (PowerShell)
$Host.UI.RawUI.WindowTitle = "PCI Backend - Port 8001"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PCI Backend - Port 8001" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot\..\backend

if (-not (Test-Path .venv)) {
    Write-Host "[Error] Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

& .\.venv\Scripts\Activate.ps1

Write-Host "  URL:      " -NoNewline; Write-Host "http://0.0.0.0:8001" -ForegroundColor Cyan
Write-Host "  API Docs: " -NoNewline; Write-Host "http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
