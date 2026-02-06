param(
    [int]$MaxIter = 5,
    [string]$Tests = "pytest -q",
    [switch]$DryRun,
    [ValidateSet("auto","manual")]
    [string]$ApproveMode = "auto",
    [string]$PrdPath = "prd.json",
    [string]$ProgressPath = "progress.txt",
    [int]$TailLines = 60
)

$cmd = @(
    "python", "-m", "app.cli", "ralph-loop",
    "--max-iter", $MaxIter,
    "--tests", $Tests,
    "--approve-mode", $ApproveMode,
    "--prd-path", $PrdPath,
    "--progress-path", $ProgressPath,
    "--tail-lines", $TailLines
)

if ($DryRun) {
    $cmd += "--dry-run"
}

Write-Host ("Running Ralph loop: " + ($cmd -join " "))
& $cmd
