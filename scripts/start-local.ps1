param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$backendRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\backend'))
$pythonExe = Join-Path $backendRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) {
    throw 'Ambiente local ausente. Execute scripts/setup-backend.ps1 primeiro.'
}
Push-Location -LiteralPath $backendRoot
$previousPythonUtf8 = $env:PYTHONUTF8
try {
    $env:PYTHONUTF8 = '1'
    if ($CheckOnly) {
        & $pythonExe -m ai_stream_editor.local --check-only
    } else {
        & $pythonExe -m ai_stream_editor.local
    }
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível iniciar o ambiente local. Consulte a mensagem acima.' }
} finally {
    $env:PYTHONUTF8 = $previousPythonUtf8
    Pop-Location
}
