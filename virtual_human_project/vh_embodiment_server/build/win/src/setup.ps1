param(
    [ValidateSet('cpu','gpu')][string]$Profile = 'cpu',
    [ValidateSet('cpu','auto')][string]$VoiceDevice = 'cpu',
    [ValidateSet('cpu','auto')][string]$TranscriptionDevice = 'cpu',
    [switch]$Yes,
    [switch]$Plan
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot
$setupRoot = Join-Path $PSScriptRoot '.setup'
New-Item -ItemType Directory -Path $setupRoot -Force | Out-Null
$pythonPath = Join-Path $PSScriptRoot '.python\python.exe'
# Reuse an existing 3.12 interpreter when possible; never install into its environment.
if (-not (Test-Path -LiteralPath $pythonPath)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $candidate = & py -3.12 -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and $candidate) { $pythonPath = $candidate.Trim() }
        } catch { Write-Output 'Python 3.12 not found: preparing a local copy.' }
    }
}
if (-not (Test-Path -LiteralPath $pythonPath)) {
    $driveRoot = [System.IO.Path]::GetPathRoot($PSScriptRoot)
    if (([System.IO.DriveInfo]::new($driveRoot)).AvailableFreeSpace -lt 1GB) {
        throw 'At least 1 GB of free space is required to prepare Python. Choose another drive.'
    }
    $installer = Join-Path $setupRoot 'python-3.12.10-amd64.exe'
    if (-not (Test-Path -LiteralPath $installer)) {
        Write-Output 'Preparing Python 3.12 (about 26 MB), required only during first setup…'
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile ($installer + '.part') -UseBasicParsing
        Move-Item -LiteralPath ($installer + '.part') -Destination $installer -Force
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        throw 'Invalid Python installer signature: installation stopped.'
    }
    Write-Output 'Installing Python in the application folder…'
    $pythonHome = Join-Path $PSScriptRoot '.python'
    $arguments = "/quiet InstallAllUsers=0 TargetDir=`"$pythonHome`" Include_launcher=0 Include_test=0 Include_doc=0 Include_pip=1 PrependPath=0 Shortcuts=0 AssociateFiles=0"
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
    if ($process.ExitCode -notin 0,3010) { throw "Python installation failed ($($process.ExitCode))." }
    $pythonPath = Join-Path $pythonHome 'python.exe'
}
& $pythonPath -c 'import sys; sys.exit(0 if sys.version_info[:2]==(3,12) and sys.maxsize>2**32 else 1)'
if ($LASTEXITCODE -ne 0) { throw '64-bit Python 3.12 is required.' }
$installArguments = @((Join-Path $PSScriptRoot 'install.py'), '--profile', $Profile,
    '--voice-device', $VoiceDevice, '--transcription-device', $TranscriptionDevice)
if ($Yes) { $installArguments += '--yes' }
if ($Plan) { $installArguments += '--plan' }
& $pythonPath @installArguments
exit $LASTEXITCODE