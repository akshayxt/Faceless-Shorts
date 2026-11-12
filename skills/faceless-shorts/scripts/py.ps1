<#
.SYNOPSIS
    Runs Python within the faceless-shorts virtual environment.
#>
$FH = if ($env:FACELESS_HOME) { $env:FACELESS_HOME } else { "$HOME\.faceless-shorts" }
$Py = "$FH\venv\Scripts\python.exe"

if (Test-Path $Py) {
    & $Py $args
} else {
    python $args
}
