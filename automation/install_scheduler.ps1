<#
.SYNOPSIS
Installs idempotent Windows Scheduled Tasks aligned to US Audience Prime Times (EST -> local IST):
  1. BabyBeats_Factory_Daily   (11:30 PM IST / 1:00 PM EST)  - Renders upcoming queued English Short(s)
  2. BabyBeats_Upload_Short    (02:00 AM IST / 3:30 PM EST)  - US after-school Short slot
  3. BabyBeats_Upload_Longform (04:30 AM IST / 6:00 PM EST)  - US family evening Long-form slot
  4. BabyBeats_Autopilot_Logon (At Logon)                    - Keeps non-stopping autopilot_loop.ps1 running
#>

$ErrorActionPreference = "Stop"
$AutoDir = "G:\Faceless-Shorts\automation"
$Py = "C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"

function Register-IdempotentTask {
  param(
    [string]$TaskName,
    [Microsoft.Management.Infrastructure.CimInstance]$Trigger,
    [string]$Execute,
    [string]$Arguments
  )
  $action = New-ScheduledTaskAction -Execute $Execute -Argument $Arguments -WorkingDirectory $AutoDir
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 4)
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $Trigger -Settings $settings -Force | Out-Null
  Write-Host "Scheduled task ready: $TaskName"
}

try {
  Register-IdempotentTask -TaskName "BabyBeats_Factory_Daily" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 11:30PM) `
    -Execute $Py `
    -Arguments "`"$AutoDir\auto_short_factory.py`""

  Register-IdempotentTask -TaskName "BabyBeats_Upload_Short" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 2:00AM) `
    -Execute $Py `
    -Arguments "`"$AutoDir\youtube_direct_upload.py`""

  Register-IdempotentTask -TaskName "BabyBeats_Upload_Longform" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 4:30AM) `
    -Execute $Py `
    -Arguments "`"$AutoDir\youtube_direct_upload.py`""

  Register-IdempotentTask -TaskName "BabyBeats_Autopilot_Logon" `
    -Trigger (New-ScheduledTaskTrigger -AtLogOn) `
    -Execute "powershell.exe" `
    -Arguments "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$AutoDir\autopilot_loop.ps1`""
} catch {
  Write-Warning "Task Scheduler registration notice: $_"
}
