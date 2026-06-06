# PCI Operation Optimization - Frontend Only (PowerShell)
$Host.UI.RawUI.WindowTitle = "PCI Frontend - Port 8080"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PCI Frontend - Port 8080 (HTTPS)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot\..\frontend

Write-Host "  Local:    " -NoNewline; Write-Host "https://localhost:8080" -ForegroundColor Cyan
Write-Host "  Network:  " -NoNewline; Write-Host "https://10.195.19.225:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

npm run dev
