@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==============================================================================
echo [FactCheck Hub] Daily 23:00 KST Local Enrichment ^& Trend Analysis Pipeline
echo Timestamp: %DATE% %TIME%
echo ==============================================================================

set "PROJECT_DIR=D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck"
cd /d "%PROJECT_DIR%"

set "PYTHON_EXE=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo.
echo [*] Running Nightly 23:00 KST Consolidated Local EOD Pipeline...
"%PYTHON_EXE%" -u tools\daily_2300_local_eod.py
if %ERRORLEVEL% neq 0 (
    echo [!] Local EOD pipeline encountered an error (code: %ERRORLEVEL%).
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================================
echo [FactCheck Hub] Pipeline finished successfully at %DATE% %TIME%
echo ==============================================================================
exit /b 0
