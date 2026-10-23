# scripts/register_daily_scheduler.ps1
# FactCheck Hub 11:00 & 23:00 KST Local Automation Task Scheduler Registration
# Supports missed run catch-up (StartWhenAvailable) for laptops

$CmdPath = "D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck\scripts\run_daily_pipeline.cmd"
$WorkingDir = "D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " 등록 중: FactCheck Hub 1일 2회 (11:00, 23:00 KST) 로컬 자동화 작업 스케줄러" -ForegroundColor Cyan
Write-Host "=================================================================="

# 1. Action definition
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$CmdPath`"" -WorkingDirectory $WorkingDir

# 2. Settings: StartWhenAvailable (Run as soon as possible if missed due to laptop sleep/off)
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$Schedules = @(
    @{ Name = "FactCheckHub_Daily1100"; Time = "11:00"; Desc = "Daily 11:00 KST Morning Local Pipeline with Catch-up" },
    @{ Name = "FactCheckHub_Daily2300"; Time = "23:00"; Desc = "Daily 23:00 KST EOD Local Pipeline with Catch-up" }
)

foreach ($sched in $Schedules) {
    $TaskName = $sched.Name
    $TaskTime = $sched.Time
    $TaskDesc = $sched.Desc
    $Trigger = New-ScheduledTaskTrigger -Daily -At $TaskTime

    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description $TaskDesc | Out-Null
        Write-Host "[+] 작업 스케줄러 등록 성공: '$TaskName'" -ForegroundColor Green
        Write-Host "    - 실행 시각: 매일 $TaskTime KST" -ForegroundColor Green
        Write-Host "    - 절전/종료 대응: StartWhenAvailable 활성화 (노트북 켜지면 즉시 지연 실행)" -ForegroundColor Green
        Write-Host "    - 실행 대상: $CmdPath" -ForegroundColor Green
    } catch {
        Write-Host "[!] '$TaskName' 등록 실패: $_" -ForegroundColor Red
    }
}
