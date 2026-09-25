# Run the live triage repeatedly across all 3 scenarios to generate rich Bob task sessions.
# Usage: .\run_montage.ps1 -Rounds 2
param([int]$Rounds = 2)

Set-Location -Path $PSScriptRoot
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")
$env:BOB_API_KEY      = [System.Environment]::GetEnvironmentVariable('BOB_API_KEY','User')
$env:GRANITE_MODEL_ID = "ibm/granite-4-h-small"
$env:MOCK_MODE        = "0"
$env:BOB_MAX_COST     = "3"
$env:PYTHONIOENCODING = "utf-8"

$scenarios = @("pagination","parsing","tasks")
$log = "$PSScriptRoot\montage_log.txt"
"=== montage start: $Rounds rounds x $($scenarios.Count) scenarios ===" | Out-File $log
for ($r = 1; $r -le $Rounds; $r++) {
  foreach ($s in $scenarios) {
    "----- round $r / scenario $s -----" | Tee-Object -FilePath $log -Append
    python run_demo.py --trace "samples\sample_trace_$s.txt" 2>&1 |
      Select-String -Pattern "winner|CONFIRMED|REJECTED|Bobcoins this run" |
      Tee-Object -FilePath $log -Append
  }
}
"=== montage complete ===" | Tee-Object -FilePath $log -Append
