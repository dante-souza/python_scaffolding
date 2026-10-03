$RootDir = $PSScriptRoot
$PythonBin = if ($env:PYTHON) { $env:PYTHON } else { "python" }

if (-not (Get-Command $PythonBin -ErrorAction SilentlyContinue)) {
    [Console]::Error.WriteLine("ERROR: Python command not found: $PythonBin")
    [Console]::Error.WriteLine(
        "Activate the intended Conda environment or set PYTHON to its interpreter."
    )
    exit 127
}

$CommandArgs = @($args)

if ($CommandArgs.Count -eq 0) {
    $CommandArgs = @("help")
}

Push-Location $RootDir

try {
    & $PythonBin "scripts/repo.py" @CommandArgs
    $ExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($null -eq $ExitCode) {
    $ExitCode = 0
}

exit $ExitCode
