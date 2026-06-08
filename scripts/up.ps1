# Остановить (если запущено): Ctrl+C в терминале VS Code
Set-Location $PSScriptRoot\..

Write-Host "=== video-transcriber: полный стек (web + worker + redis + flower) ===" -ForegroundColor Cyan
docker compose down 2>$null
docker compose up --build
