@echo off
chcp 65001 > nul
echo [FactCheck Hub] 작업 스케줄러 등록 스크립트 실행 중...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_daily_scheduler.ps1"
pause
