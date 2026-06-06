# PCI Operation Optimization - Development Server (PowerShell)
$Host.UI.RawUI.WindowTitle = "PCI Operation Optimization"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PCI Operation Optimization - Dev Server" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot\..

Write-Host "Starting Backend (http://localhost:8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"

Start-Sleep -Seconds 3

Write-Host "Starting Frontend (https://localhost:8080)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Servers Started!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  " -NoNewline; Write-Host "http://localhost:8001" -ForegroundColor Cyan
Write-Host "  API Docs: " -NoNewline; Write-Host "http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "  Frontend: " -NoNewline; Write-Host "https://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "  LAN Access: " -NoNewline; Write-Host "https://10.195.19.225:8080" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close this window (servers keep running)"
