$ErrorActionPreference = 'Stop'
$backendRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\backend'))
$pythonExe = Join-Path $backendRoot '.venv\Scripts\python.exe'
$testRoot = Join-Path $backendRoot '.test-data'
$baseTemp = [IO.Path]::GetFullPath((Join-Path $testRoot ('pytest-' + [guid]::NewGuid().ToString('N'))))
if (!$baseTemp.StartsWith($backendRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'O diretório temporário de teste precisa ficar dentro de backend.'
}
New-Item -ItemType Directory -Path (Join-Path $testRoot 'temp') -Force | Out-Null
$oldTemp = $env:TEMP
$oldTmp = $env:TMP
$previousPythonUtf8 = $env:PYTHONUTF8
Push-Location -LiteralPath $backendRoot
try {
    $env:TEMP = Join-Path $testRoot 'temp'
    $env:TMP = $env:TEMP
    $env:PYTHONUTF8 = '1'
    & $pythonExe -m pytest -q --basetemp $baseTemp
    if ($LASTEXITCODE -ne 0) { throw 'Verificações do backend falharam.' }
} finally {
    $env:TEMP = $oldTemp
    $env:TMP = $oldTmp
    $env:PYTHONUTF8 = $previousPythonUtf8
    Pop-Location
}
