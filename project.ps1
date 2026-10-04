$RootDir = $PSScriptRoot
$PythonBin = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$PythonResolved = "<not found>"

function Write-BootstrapContext {
    param(
        [string]$ResolvedPython
    )

    $CondaPrefix = if ($env:CONDA_PREFIX) { $env:CONDA_PREFIX } else { "<not set>" }
    $VirtualEnv = if ($env:VIRTUAL_ENV) { $env:VIRTUAL_ENV } else { "<not set>" }

    [Console]::Error.WriteLine("Pre-Python diagnostics:")
    [Console]::Error.WriteLine("  adapter=project.ps1")
    [Console]::Error.WriteLine("  repo_root=$RootDir")
    [Console]::Error.WriteLine("  shell=PowerShell $($PSVersionTable.PSVersion)")
    [Console]::Error.WriteLine("  python_command=$PythonBin")
    [Console]::Error.WriteLine("  python_resolved=$ResolvedPython")
    [Console]::Error.WriteLine("  conda_prefix=$CondaPrefix")
    [Console]::Error.WriteLine("  virtual_env=$VirtualEnv")
}

$PythonCommand = Get-Command $PythonBin -ErrorAction SilentlyContinue | Select-Object -First 1

if ($null -eq $PythonCommand) {
    [Console]::Error.WriteLine("ERROR: Python command not found: $PythonBin")
    Write-BootstrapContext -ResolvedPython $PythonResolved
    [Console]::Error.WriteLine(
        "ACTION: activate the intended Python environment in this shell or set PYTHON to its interpreter."
    )
    exit 127
}

if (($PythonCommand.PSObject.Properties.Name -contains "Path") -and $PythonCommand.Path) {
    $PythonResolved = $PythonCommand.Path
}
elseif ($PythonCommand.Source) {
    $PythonResolved = $PythonCommand.Source
}
elseif ($PythonCommand.Definition) {
    $PythonResolved = $PythonCommand.Definition
}

$ProbeOutput = $null
$ProbeExitCode = 0

try {
    $ProbeOutput = & $PythonBin -c "import sys; print(sys.executable)" 2>&1
    $ProbeExitCode = $LASTEXITCODE
}
catch {
    $ProbeOutput = $_.Exception.Message
    $ProbeExitCode = 126
}

if ($null -eq $ProbeExitCode) {
    $ProbeExitCode = 0
}

if ($ProbeExitCode -ne 0) {
    [Console]::Error.WriteLine(
        "ERROR: Python command was found but could not be started successfully."
    )
    Write-BootstrapContext -ResolvedPython $PythonResolved
    [Console]::Error.WriteLine("  python_probe_exit=$ProbeExitCode")

    $ProbeText = ($ProbeOutput | Out-String).Trim()
    if ($ProbeText) {
        [Console]::Error.WriteLine("  python_probe_output=$ProbeText")
    }

    [Console]::Error.WriteLine(
        "ACTION: activate the intended Python environment in this shell or set PYTHON to a compatible interpreter."
    )
    exit 126
}

$CommandArgs = @($args)

if ($CommandArgs.Count -eq 0) {
    $CommandArgs = @("help")
}

Push-Location $RootDir

try {
    if ($CommandArgs.Count -eq 1 -and $CommandArgs[0] -eq "env-rebuild") {
        # Windows cannot delete .venv while its python.exe is still executing.
        # Resolve a safe authority Python first, let that probe exit, then launch
        # the full rebuild from the external interpreter while PowerShell remains
        # the foreground parent and waits for completion.
        $RebuildPythonOutput = & $PythonBin "scripts/env_rebuild_target.py"
        $TargetExitCode = $LASTEXITCODE

        if ($TargetExitCode -ne 0) {
            $ExitCode = $TargetExitCode
        }
        else {
            $RebuildPython = [string]($RebuildPythonOutput | Select-Object -Last 1)
            $RebuildPython = $RebuildPython.Trim()

            if ([string]::IsNullOrWhiteSpace($RebuildPython)) {
                [Console]::Error.WriteLine(
                    "ERROR: env-rebuild target resolver returned no Python executable."
                )
                $ExitCode = 2
            }
            else {
                & $RebuildPython "scripts/repo.py" @CommandArgs
                $ExitCode = $LASTEXITCODE
            }
        }
    }
    else {
        & $PythonBin "scripts/repo.py" @CommandArgs
        $ExitCode = $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

if ($null -eq $ExitCode) {
    $ExitCode = 0
}

exit $ExitCode
