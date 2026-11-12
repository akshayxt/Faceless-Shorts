param(
  [Parameter(Mandatory=$true)][string]$ProjectDir,
  [string]$OutVideo = "",
  [int]$SheetStep = 1,
  [int]$SheetCols = 8,
  [switch]$SkipRender
)

if (-not $env:BABYBEATS_TG_PARENT) {
  $pyExe = "C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"
  $tgPy = "G:\Faceless-Shorts\automation\telegram_logger.py"
  if (Test-Path $tgPy) {
    $fwdArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-ProjectDir", $ProjectDir, "-SheetStep", "$SheetStep", "-SheetCols", "$SheetCols")
    if ($OutVideo) { $fwdArgs += @("-OutVideo", $OutVideo) }
    if ($SkipRender) { $fwdArgs += "-SkipRender" }
    & $pyExe $tgPy --run --tag "PIPELINE_SHORT" -- powershell @fwdArgs
    exit $LASTEXITCODE
  }
}

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$py = "C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"
$scriptsDir = "G:\Faceless-Shorts\skills\faceless-shorts\scripts"

if (-not (Test-Path $ProjectDir)) {
  throw "Project directory not found: $ProjectDir"
}

$exampleDir = "G:\Faceless-Shorts\skills\faceless-shorts\styles\inside-out\example"
$propsTemplate = "G:\Faceless-Shorts\automation\templates\cartoon_props.js"
if (-not (Test-Path (Join-Path $ProjectDir "tools\capture.mjs"))) {
  Copy-Item (Join-Path $exampleDir "tools") (Join-Path $ProjectDir "tools") -Recurse -Force
}
if (-not (Test-Path (Join-Path $ProjectDir "fonts"))) {
  Copy-Item (Join-Path $exampleDir "fonts") (Join-Path $ProjectDir "fonts") -Recurse -Force
}
if (-not (Test-Path (Join-Path $ProjectDir "index.html")) -and (Test-Path (Join-Path $exampleDir "index.html"))) {
  Copy-Item (Join-Path $exampleDir "index.html") (Join-Path $ProjectDir "index.html") -Force
}
if (-not (Test-Path (Join-Path $ProjectDir "src\core"))) {
  Copy-Item (Join-Path $exampleDir "src\core") (Join-Path $ProjectDir "src\core") -Recurse -Force
}
if (-not (Test-Path (Join-Path $ProjectDir "src\main.js"))) {
  Copy-Item (Join-Path $exampleDir "src\main.js") (Join-Path $ProjectDir "src\main.js") -Force
}
if (-not (Test-Path (Join-Path $ProjectDir "src\cartoon_props.js")) -and (Test-Path $propsTemplate)) {
  Copy-Item $propsTemplate (Join-Path $ProjectDir "src\cartoon_props.js") -Force
}

Write-Host "[1/6] Voice synthesis (Kokoro TTS)..."
& $py "$scriptsDir\voice.py" $ProjectDir
if ($LASTEXITCODE -ne 0) { throw "voice.py failed ($LASTEXITCODE)" }

Write-Host "[2/6] Word alignment (Whisper / line fallback)..."
& $py "$scriptsDir\words.py" $ProjectDir
if ($LASTEXITCODE -ne 0) { throw "words.py failed ($LASTEXITCODE)" }

Push-Location $ProjectDir
try {
  Write-Host "[3/6] Chrome boot & caption/shot check..."
  node tools/capture.mjs check
  if ($LASTEXITCODE -ne 0) { throw "capture.mjs check failed ($LASTEXITCODE)" }

  Write-Host "[4/6] Exporting cue timeline..."
  node tools/capture.mjs cues
  if ($LASTEXITCODE -ne 0) { throw "capture.mjs cues failed ($LASTEXITCODE)" }

  Write-Host "[5/6] Mixing narration + SFX + music bed..."
  & $py tools/mix.py .
  if ($LASTEXITCODE -ne 0) { throw "mix.py failed ($LASTEXITCODE)" }

  New-Item -ItemType Directory -Force -Path "review","renders" | Out-Null
  Write-Host "[6/6] Rendering QA contact sheet..."
  node tools/capture.mjs sheet "review/all.jpg" $SheetStep $SheetCols
  if ($LASTEXITCODE -ne 0) { throw "capture.mjs sheet failed ($LASTEXITCODE)" }

  if (-not $SkipRender) {
    $targetMp4 = if ($OutVideo) { $OutVideo } else { Join-Path (Join-Path $ProjectDir "renders") "final.mp4" }
    Write-Host "[RENDER] Building final MP4 -> $targetMp4"
    node tools/capture.mjs video $targetMp4
    if ($LASTEXITCODE -ne 0) { throw "capture.mjs video failed ($LASTEXITCODE)" }
    ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -of json $targetMp4
  }
} finally {
  Pop-Location
}
