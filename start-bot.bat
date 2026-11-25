@echo off
cd /d "%~dp0"

REM Avoid two instances (Telegram Conflict)
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'bot\\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo Starting bridge bot...
echo Close this window or press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" bot.py
pause
