$ErrorActionPreference = 'Stop'
$backendRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\backend'))
$venvRoot = Join-Path $backendRoot '.venv'
$pythonExe = Join-Path $venvRoot 'Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) {
    python -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python local.' }
}
& $pythonExe -m pip install --only-binary=:all: -r (Join-Path $backendRoot 'requirements.lock')
if ($LASTEXITCODE -ne 0) { throw 'A instalação das dependências locais não terminou.' }
Write-Host 'Backend preparado. Execute scripts/start-backend.ps1 -PrepareModel para baixar os pesos e iniciar.'
