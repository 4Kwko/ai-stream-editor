param([switch]$StorageOnly, [switch]$NoApi)
$ErrorActionPreference = 'Stop'
$backendRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\backend'))
$pythonExe = Join-Path $backendRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) {
    throw 'Ambiente local ausente. Consulte scripts/setup-backend.ps1; nada foi instalado.'
}
Push-Location -LiteralPath $backendRoot
$previousPythonUtf8 = $env:PYTHONUTF8
try {
    $env:PYTHONUTF8 = '1'
    if ($StorageOnly) {
        & $pythonExe -m ai_stream_editor storage
    } elseif ($NoApi) {
        & $pythonExe -m ai_stream_editor doctor --no-api
    } else {
        & $pythonExe -m ai_stream_editor doctor
    }
    if ($LASTEXITCODE -ne 0) { throw 'O diagnóstico encontrou dependências ou modelo ausentes; consulte checks acima.' }
} finally {
    $env:PYTHONUTF8 = $previousPythonUtf8
    Pop-Location
}
