param([switch]$PrepareModel)
$ErrorActionPreference = 'Stop'
$backendRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\backend'))
$pythonExe = Join-Path $backendRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) {
    throw 'Ambiente local ausente. Execute scripts/setup-backend.ps1 primeiro.'
}
Push-Location -LiteralPath $backendRoot
$previousPythonUtf8 = $env:PYTHONUTF8
$previousImplicitToken = $env:HF_HUB_DISABLE_IMPLICIT_TOKEN
$previousTelemetry = $env:HF_HUB_DISABLE_TELEMETRY
try {
    $env:PYTHONUTF8 = '1'
    if ($PrepareModel) {
        $env:HF_HUB_DISABLE_IMPLICIT_TOKEN = '1'
        $env:HF_HUB_DISABLE_TELEMETRY = '1'
        & $pythonExe -m ai_stream_editor prepare-model
        if ($LASTEXITCODE -ne 0) { throw 'A preparação do modelo não terminou.' }
    }
    & $pythonExe -m ai_stream_editor serve
    if ($LASTEXITCODE -ne 0) { throw 'O backend terminou com erro.' }
} finally {
    $env:PYTHONUTF8 = $previousPythonUtf8
    $env:HF_HUB_DISABLE_IMPLICIT_TOKEN = $previousImplicitToken
    $env:HF_HUB_DISABLE_TELEMETRY = $previousTelemetry
    Pop-Location
}
