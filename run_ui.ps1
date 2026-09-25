# Launch the Culprit demo UI with the right environment.
#   .\run_ui.ps1          -> LIVE mode (real Bob agents + watsonx Granite; spends Bobcoins)
#   .\run_ui.ps1 -Mock    -> MOCK mode (canned data; instant; zero Bobcoins) -- best for tuning the UI
param([switch]$Mock)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# node must be on PATH for `bob`, and BOB_API_KEY must be visible to the server subprocess.
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")
$env:BOB_API_KEY     = [System.Environment]::GetEnvironmentVariable('BOB_API_KEY','User')
$env:GRANITE_MODEL_ID = "ibm/granite-4-h-small"   # correct current watsonx Granite model
$env:PYTHONIOENCODING = "utf-8"

if ($Mock) {
    $env:MOCK_MODE = "1"
    Write-Host "Starting Culprit UI in MOCK mode (free, instant) -> http://127.0.0.1:8000" -ForegroundColor Green
} else {
    $env:MOCK_MODE = "0"
    if (-not $env:BOB_API_KEY) {
        Write-Host "WARNING: BOB_API_KEY not found at User scope. LIVE mode will fail." -ForegroundColor Yellow
        Write-Host "Set it once with: [Environment]::SetEnvironmentVariable('BOB_API_KEY','<key>','User')" -ForegroundColor Yellow
    }
    Write-Host "Starting Culprit UI in LIVE mode (real Bob; spends Bobcoins) -> http://127.0.0.1:8000" -ForegroundColor Cyan
}

python -m ui.server
