# 3 воркера — параллельная обработка (пункт ДЗ-10)
Set-Location $PSScriptRoot\..

Write-Host "=== video-transcriber: 3 worker + flower ===" -ForegroundColor Cyan
docker compose down 2>$null
docker compose up --build --scale worker=3
