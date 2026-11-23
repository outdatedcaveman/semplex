$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent (Split-Path -Parent $here)
$agda = Join-Path $env:LOCALAPPDATA 'Semplex\Agda\2.9.0\agda.exe'
if (-not (Test-Path $agda)) { throw "Agda binary missing: $agda" }
Push-Location $here
try {
  & $agda --build-library
  if ($LASTEXITCODE -ne 0) { throw "Agda build failed with exit code $LASTEXITCODE" }
  Write-Output 'SEMPLEX CUBICAL LIBRARY BUILD PASSED'
}
finally {
  Pop-Location
}
