Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$testsPath = Join-Path $projectRoot "tests"
$resultsDir = Join-Path $projectRoot "test-results"
$logPath = Join-Path $resultsDir "pytest-output.txt"

Write-Host "Project root: $projectRoot"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath
}

Write-Host "Installing the project and its declared test dependencies..."
$projectSpec = "${projectRoot}[dev,testing]"
& $venvPython -m pip install -e $projectSpec --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Dependency installation failed. Tests were not run."
    exit $LASTEXITCODE
}

New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null

Write-Host "Running local tests..."
& $venvPython -m pytest $testsPath -q --tb=short 2>&1 | Tee-Object -FilePath $logPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "Test run failed. View: $logPath"
    exit $LASTEXITCODE
}

Write-Host "Tests passed. Log saved to: $logPath"
