param(
  [int]$MaxPrebuildPerDay = 30,
  [int]$SleepSeconds = 60
)

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$AutoDir = "G:\Faceless-Shorts\automation"
$LogDir = Join-Path $AutoDir "logs"
$CredsDir = Join-Path $AutoDir "creds"
$LogFile = Join-Path $LogDir "autopilot.log"
$AllLogFile = Join-Path $LogDir "all_processes.log"
$PidFile = Join-Path $LogDir "autopilot.pid"
$StopFile = Join-Path $LogDir "STOP_AUTOPILOT"
$PauseUploadFile = Join-Path $LogDir "PAUSE_UPLOADS"
$Py = "C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"
$TgPy = Join-Path $AutoDir "telegram_logger.py"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path $CredsDir | Out-Null

# Single-instance guard so multiple daemons don't collide
if (Test-Path $PidFile) {
  $oldPid = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($oldPid -and ($oldPid -match '^\d+$')) {
    $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
    if ($proc -and ($proc.Id -ne $PID)) {
      Write-Host "Autopilot already running under PID $oldPid. Exiting duplicate launch."
      exit 0
    }
  }
}
Set-Content -Path $PidFile -Value "$PID" -Encoding UTF8

function Write-Log {
  param(
    [string]$Msg,
    [string]$Tag = "AUTOPILOT"
  )
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$ts IST] $Msg"
  Add-Content -Path $LogFile -Value $line -Encoding UTF8
  Add-Content -Path $AllLogFile -Value "[$ts IST] [$Tag] $Msg" -Encoding UTF8
  Write-Host $line
  if (Test-Path $TgPy) {
    & $Py $TgPy --tag $Tag --message $Msg 2>&1 | Out-Null
  }
}

Write-Log "=== BABYBEATS RHYMO AUTOPILOT LOOP STARTED (PID=$PID) ==="

$cycle = 0
$lastSeoSyncUtc = [datetime]::MinValue
while ($true) {
  if (Test-Path $StopFile) {
    Write-Log "STOP_AUTOPILOT sentinel detected. Exiting cleanly."
    Remove-Item $PidFile -ErrorAction SilentlyContinue
    break
  }

  $cycle++
  try {
    $qJson = Get-Content (Join-Path $AutoDir "data\30day_topic_queue.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $pendingCount = @($qJson.topics | Where-Object { $_.status -eq "pending" }).Count
    $readyCount = @($qJson.topics | Where-Object { $_.status -eq "ready_for_upload" }).Count

    $uqJson = Get-Content (Join-Path $AutoDir "data\upload_queue.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $totalUploads = @($uqJson.items).Count
    $uploadedCount = @($uqJson.items | Where-Object { ($_.status -in @("UPLOADED", "SCHEDULED")) -or $_.youtube_video_id }).Count
    $remainingUploads = [Math]::Max(0, $totalUploads - $uploadedCount)

    Write-Log "Cycle #$cycle heartbeat: rendered_topics=$readyCount/$($qJson.topics.Count) uploaded=$uploadedCount/$totalUploads remaining_uploads=$remainingUploads pending_renders=$pendingCount"

    # 1. Produce next queued video if buffer < MaxPrebuildPerDay and no longform build is active
    $longBusy = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*longform_renderer*" -or $_.CommandLine -like "*build_longform*" }
    if ($longBusy) {
      Write-Log "Long-form 1080p render active; yielding CPU this cycle before queuing next Short."
    } elseif ($pendingCount -gt 0 -and $readyCount -lt $MaxPrebuildPerDay) {
      $nextTopic = $qJson.topics | Where-Object { $_.status -eq "pending" } | Select-Object -First 1
      Write-Log "Producing queued Short: $($nextTopic.id) - $($nextTopic.title)"
      & $Py $TgPy --run --tag "FACTORY[$($nextTopic.id)]" --log-file $LogFile -- $Py (Join-Path $AutoDir "auto_short_factory.py") --topic-id $nextTopic.id
    }

    # 2. Continuously refresh real-time US trending SEO across pending uploads (on Cycle 1 & every 10m)
    $nowUtc = [datetime]::UtcNow
    if ($remainingUploads -gt 0 -and (($nowUtc - $lastSeoSyncUtc).TotalSeconds -ge 600)) {
      Write-Log "Refreshing real-time US trending SEO (YouTube Suggest + US Trends) for $remainingUploads pending uploads..." "REALTIME_SEO"
      & $Py $TgPy --run --tag "REALTIME_SEO" --log-file $LogFile -- $Py (Join-Path $AutoDir "realtime_seo.py") --all
      $lastSeoSyncUtc = [datetime]::UtcNow
    }

    # 3. Non-stop upload & schedule loop until remaining_uploads == 0
    $secretPath = Join-Path $CredsDir "client_secrets.json"
    $tokenPath = Join-Path $CredsDir "youtube_token.json"
    if (Test-Path $PauseUploadFile) {
      Write-Log "Upload paused (PAUSE_UPLOADS active) — remaining_uploads=$remainingUploads." "UPLOADER"
    } elseif ($remainingUploads -eq 0) {
      Write-Log "ALL_UPLOADS_COMPLETE: $uploadedCount/$totalUploads videos uploaded or scheduled on YouTube." "UPLOADER"
    } elseif ((Test-Path $tokenPath) -or (Test-Path $secretPath)) {
      Write-Log "Starting real-time SEO upload batch ($remainingUploads remaining)..." "UPLOADER"
      & $Py $TgPy --run --tag "UPLOADER" --log-file $LogFile -- $Py (Join-Path $AutoDir "youtube_direct_upload.py") --all
    } else {
      Write-Log "Upload loop armed ($uploadedCount/$totalUploads scheduled; $remainingUploads remaining — Zapier hit 5/24h upload throttle; upgrade Zapier, resume after 24h via Zapier tunnel, or drop client_secrets.json in creds\)." "UPLOADER"
    }

    # 4. Sync analytics & refresh dashboards with live Telegram process logs
    & $Py $TgPy --run --tag "ANALYTICS" --log-file $LogFile -- $Py (Join-Path $AutoDir "analytics_sync.py")
    & $Py $TgPy --run --tag "DASHBOARD" --log-file $LogFile -- $Py (Join-Path $AutoDir "refresh_dashboard.py")

  } catch {
    Write-Log "ERROR in Cycle #${cycle}: $($_.Exception.Message)" "AUTOPILOT_ERROR"
  }

  Start-Sleep -Seconds $SleepSeconds
}
