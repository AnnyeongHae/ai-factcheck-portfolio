@echo off
chcp 65001 > nul
setlocal

echo ======================================================================
echo 🌙 [AI FactCheck Hub] Nightly 23:00 KST Local Automation Runner
echo ======================================================================

cd /d "d:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH!
    pause
    exit /b 1
)

python -u tools/daily_2300_local_eod.py

echo ======================================================================
echo Execution complete.
echo ======================================================================
endlocal
