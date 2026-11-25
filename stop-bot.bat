@echo off
cd /d "%~dp0"
echo Stopping bridge bot...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'bot\\.py' } | ForEach-Object { Write-Host ('Stopping PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }"
echo Done.
pause
