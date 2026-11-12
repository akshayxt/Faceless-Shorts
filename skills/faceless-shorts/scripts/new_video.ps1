<#
.SYNOPSIS
    Creates a new short video project from a style template on Windows.
.DESCRIPTION
    Copies the style example project (engine, shots, script) into a target short directory.
.PARAMETER Style
    The style name (e.g. inside-out, deep-dive, night-file, stick-story, paper-atlas, tall-tale).
.PARAMETER Name
    The project folder name.
.PARAMETER Dir
    Parent folder for projects (defaults to $HOME\faceless-shorts).
.PARAMETER List
    List all available styles.
#>
param(
    [Parameter(Position = 0)]
    [string]$Style,

    [Parameter(Position = 1)]
    [string]$Name,

    [string]$Dir = "$HOME\faceless-shorts",

    [switch]$List
)

$SKILL = Split-Path -Parent $PSScriptRoot
$StylesDir = Join-Path $SKILL "styles"

if ($List -or [string]::IsNullOrWhiteSpace($Style)) {
    Write-Host "Available styles:" -ForegroundColor Cyan
    Get-ChildItem -Directory $StylesDir | ForEach-Object {
        Write-Host "  - $($_.Name)"
    }
    return
}

if ([string]::IsNullOrWhiteSpace($Name)) {
    Write-Error "Usage: .\new_video.ps1 <style> <short-name> [-Dir <parent>]"
    return
}

$Src = Join-Path $StylesDir "$Style\example"
if (-not (Test-Path $Src)) {
    Write-Error "Style '$Style' not found in $StylesDir. Run .\new_video.ps1 -List to see available styles."
    return
}

$Dst = Join-Path $Dir $Name
if (Test-Path $Dst) {
    Write-Error "Destination '$Dst' already exists: pick another name."
    return
}

Write-Host "Creating project in $Dst..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $Dir -Force | Out-Null
Copy-Item -Path $Src -Destination $Dst -Recurse -Force
New-Item -ItemType Directory -Path (Join-Path $Dst "renders") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Dst "review") -Force | Out-Null

$OldNarration = Join-Path $Dst "data\narration.wav"
$OldMix = Join-Path $Dst "data\mix.wav"
if (Test-Path $OldNarration) { Remove-Item $OldNarration -Force }
if (Test-Path $OldMix) { Remove-Item $OldMix -Force }

Write-Host "Project created successfully at: $Dst" -ForegroundColor Green
Write-Host "Style: $Style"
Write-Host "Next: rewrite script.json and src/shots.js, then run the pipeline."
