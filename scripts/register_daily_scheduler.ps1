# scripts/register_daily_scheduler.ps1
# FactCheck Hub 23:00 KST Local Automation Task Scheduler Registration
# Supports missed run catch-up (StartWhenAvailable) for laptops

$TaskName = "FactCheckHub_Daily2300"
$CmdPath = "D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck\scripts\run_daily_pipeline.cmd"
$WorkingDir = "D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " 등록 중: FactCheck Hub 23:00 KST 로컬 자동화 작업 스케줄러" -ForegroundColor Cyan
Write-Host "=================================================================="

# 1. Action definition
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$CmdPath`"" -WorkingDirectory $WorkingDir

# 2. Trigger definition: Daily at 23:00 (11:00 PM)
$Trigger = New-ScheduledTaskTrigger -Daily -At "23:00"

# 3. Settings: StartWhenAvailable (Run as soon as possible if missed due to laptop sleep/off)
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# 4. Register or update task
try {
    # Unregister existing task if present
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily 23:00 KST Local Enrichment & H-V-D Spike Engine with Sleep/Off Missed Catch-up" | Out-Null
    Write-Host "[+] 작업 스케줄러 등록 성공: '$TaskName'" -ForegroundColor Green
    Write-Host "    - 실행 시각: 매일 23:00 KST" -ForegroundColor Green
    Write-Host "    - 절전/종료 대응: StartWhenAvailable 활성화 (노트북이 켜지면 즉시 지연 실행)" -ForegroundColor Green
    Write-Host "    - 실행 대상: $CmdPath" -ForegroundColor Green
} catch {
    Write-Host "[!] 등록 실패: $_" -ForegroundColor Red
}
