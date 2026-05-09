$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (!(Test-Path "generated")) {
    New-Item -ItemType Directory -Path "generated" | Out-Null
}

Write-Host "Compiling C++ braking model..."
g++ simulation/braking_model.cpp -std=c++17 -O2 -o generated/braking_model.exe

Write-Host "Running C++ simulation..."
& generated/braking_model.exe
$simulationExit = $LASTEXITCODE
if ($simulationExit -ne 0 -and $simulationExit -ne 2) {
    exit $simulationExit
}

Write-Host "Running Python lifecycle tests..."
python -m unittest discover -s tests

Write-Host "Pipeline finished. Start the dashboard with:"
Write-Host "python backend/server.py"
