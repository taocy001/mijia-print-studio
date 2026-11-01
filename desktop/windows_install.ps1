param([string]$PythonExecutable = '', [switch]$InstallOnly)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$env:PYTHONUTF8 = '1'
$project = Split-Path $PSScriptRoot -Parent
$build = Join-Path $project 'build'
New-Item -ItemType Directory -Force $build | Out-Null
try { $lock = [IO.File]::Open((Join-Path $build 'windows-install.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
catch { throw 'This checkout is in use. Stop its service or wait for setup to finish, then retry.' }
try {
    if (-not $PythonExecutable) {
        if (Get-Command py.exe -ErrorAction SilentlyContinue) {
            foreach ($version in @('-3.12', '-3')) {
                try {
                    $candidate = & py.exe $version -c 'import sys;print(sys.executable)' 2>$null
                    if ($LASTEXITCODE -eq 0) { $PythonExecutable = $candidate; break }
                } catch { }
            }
        }
        $command = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $PythonExecutable -and $command -and $command.Source -notlike '*\Microsoft\WindowsApps\*') {
            try {
                $candidate = & $command.Source -c 'import sys;print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0) { $PythonExecutable = $candidate }
            } catch { }
        }
    }
    if (-not $PythonExecutable -or -not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
        throw 'Install 64-bit Python 3.12+ with Tcl/Tk and pip from https://www.python.org/downloads/windows/, then run this file again.'
    }
    & $PythonExecutable -c "import sys,struct,tkinter;assert sys.platform=='win32' and sys.version_info>=(3,12) and struct.calcsize('P')==8"
    if ($LASTEXITCODE -ne 0) { throw 'Native Windows Python 3.12+ (64-bit), Tcl/Tk and pip are required.' }
    $python = Join-Path $build 'venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        & $PythonExecutable -m venv (Join-Path $build 'venv')
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated environment.' }
    }
    & $python (Join-Path $project 'desktop\windows_dependencies.py')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed. No service was started.' }
} finally { $lock.Dispose() }
if (-not $InstallOnly) {
    & $python (Join-Path $project 'desktop\windows_launcher.py')
    if ($LASTEXITCODE -ne 0) { throw 'Launcher exited with an error.' }
}
