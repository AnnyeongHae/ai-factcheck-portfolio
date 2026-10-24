@echo off
chcp 65001 > nul

echo ==============================================================================
echo [FactCheck Hub] Daily Local Pure SQL Ranking Pipeline (11:00 / 23:00 KST)
echo ==============================================================================

set "PROJECT_DIR=D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck"
cd /d "%PROJECT_DIR%"

set "PYTHON_EXE=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [*] Running Pure SSOT Spike Scoring and EOD Daily Hot 10 Curation...
"%PYTHON_EXE%" -u tools\daily_2300_local_eod.py
if errorlevel 1 (
    echo [!] Local EOD pipeline encountered an error.
    exit /b 1
)

echo ==============================================================================
echo [FactCheck Hub] Pipeline finished successfully.
echo ==============================================================================
exit /b 0
