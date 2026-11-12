param(
  [Parameter(Mandatory=$true)][string]$ProjectDir,
  [string]$OutVideo = "",
  [int]$Fps = 24,
  [switch]$SheetOnly,
  [switch]$ForceVoice
)

if (-not $env:BABYBEATS_TG_PARENT) {
  $pyExe = "C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"
  $tgPy = "G:\Faceless-Shorts\automation\telegram_logger.py"
  if (Test-Path $tgPy) {
    $fwdArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-ProjectDir", $ProjectDir, "-Fps", "$Fps")
    if ($OutVideo) { $fwdArgs += @("-OutVideo", $OutVideo) }
    if ($SheetOnly) { $fwdArgs += "-SheetOnly" }
    if ($ForceVoice) { $fwdArgs += "-ForceVoice" }
    & $pyExe $tgPy --run --tag "PIPELINE_LONGFORM" -- powershell @fwdArgs
    exit $LASTEXITCODE
  }
}

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$py = "C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"
$scriptsDir = "G:\Faceless-Shorts\skills\faceless-shorts\scripts"
$mixTemplate = "G:\Faceless-Shorts\skills\faceless-shorts\styles\inside-out\example\tools\mix.py"

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectDir "data"), (Join-Path $ProjectDir "review"), (Join-Path $ProjectDir "renders") | Out-Null

$wavFile = Join-Path $ProjectDir "data\narration.wav"
if ($ForceVoice -or -not (Test-Path $wavFile)) {
  Write-Host "[1/5] Synthesizing long-form Kokoro narration..."
  & $py "$scriptsDir\voice.py" $ProjectDir
  if ($LASTEXITCODE -ne 0) { throw "voice.py failed ($LASTEXITCODE)" }
} else {
  Write-Host "[1/5] Reusing existing narration.wav (pass -ForceVoice to regenerate)."
}

Write-Host "[2/5] Generating chapter transition cues + mixing music bed..."
$cuesPy = @"
import json, pathlib
P = pathlib.Path(r'$ProjectDir')
lj = json.loads((P / 'data/lines.json').read_text(encoding='utf-8'))
lines = lj['lines']
script = json.loads((P / 'script.json').read_text(encoding='utf-8'))['lines']
cues = []
prev_ch = None
chapters = []
for i, ln in enumerate(lines):
    ch = script[i].get('chapter', '') if i < len(script) else ''
    if ch and ch != prev_ch:
        mm = int(ln['start'] // 60); ss = int(ln['start'] % 60)
        chapters.append({'time': f'{mm:02d}:{ss:02d}', 'label': ch, 'sec': ln['start']})
        cues.append({'t': round(ln['start'], 3), 'type': 'whoosh'})
        cues.append({'t': round(ln['start'] + 0.25, 3), 'type': 'pop', 'gain': 0.5})
        prev_ch = ch
    elif script[i].get('card'):
        cues.append({'t': round(ln['start'] + 0.1, 3), 'type': 'sparkle', 'dur': 0.8})
(P / 'data/cues.json').write_text(json.dumps({'duration': lj['duration'], 'cues': cues}, indent=2), encoding='utf-8')
(P / 'data/chapters.json').write_text(json.dumps(chapters, indent=2), encoding='utf-8')
print('Wrote', len(cues), 'cues &', len(chapters), 'chapters, duration=', lj['duration'], 's')
"@
& $py -c $cuesPy
& $py $mixTemplate $ProjectDir
if ($LASTEXITCODE -ne 0) { throw "mix.py failed ($LASTEXITCODE)" }

$sheetOut = Join-Path (Join-Path $ProjectDir "review") "long_all.jpg"
Write-Host "[3/5] Generating 16:9 QA contact sheet..."
node "G:\Faceless-Shorts\automation\longform_renderer.mjs" sheet $ProjectDir $sheetOut 20 5
if ($LASTEXITCODE -ne 0) { throw "longform sheet failed ($LASTEXITCODE)" }

if (-not $SheetOnly) {
  $mp4Out = if ($OutVideo) { $OutVideo } else { Join-Path (Join-Path $ProjectDir "renders") "longform_final.mp4" }
  Write-Host "[4/5] Rendering 1920x1080 long-form MP4 @ ${Fps}fps -> $mp4Out"
  node "G:\Faceless-Shorts\automation\longform_renderer.mjs" render $ProjectDir $mp4Out $Fps
  if ($LASTEXITCODE -ne 0) { throw "longform render failed ($LASTEXITCODE)" }

  Write-Host "[5/5] Verifying final output via ffprobe..."
  ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -of json $mp4Out
}
