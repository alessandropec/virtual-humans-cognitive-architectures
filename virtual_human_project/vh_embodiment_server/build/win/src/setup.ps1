param(
    [ValidateSet('cpu','gpu')][string]$Profile = 'cpu',
    [ValidateSet('cpu','auto')][string]$VoiceDevice = 'cpu',
    [ValidateSet('cpu','auto')][string]$TranscriptionDevice = 'cpu',
    [ValidateSet('yes','no')][string]$TranscriptionModels = 'yes',
    [ValidateSet('yes','no')][string]$VoiceModels = 'yes',
    [switch]$Yes,
    [switch]$Plan
)
# Output stays ASCII: Windows PowerShell 5.1 may read this file with the ANSI code page.
$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = '1'

# Local Python comes from the official NuGet package (a plain ZIP published by the Python
# release team). Unlike the python.org .exe installer it never touches the Windows registry,
# so a previous or deleted Python 3.12 installation cannot make setup skip the copy.
$PythonVersion = '3.12.10'
$PackageUrl = "https://www.nuget.org/api/v2/package/python/$PythonVersion"
$PackageSha256 = '0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8'

function Say([string]$message) { [Console]::Out.WriteLine($message); [Console]::Out.Flush() }

function Fail([string]$message) {
    Say "ERROR: $message"
    exit 1
}

function Test-Python312([string]$path) {
    if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
    try {
        & $path -c 'import sys; sys.exit(0 if sys.version_info[:2]==(3,12) and sys.maxsize>2**32 else 1)' 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Install-LocalPython([string]$setupRoot, [string]$pythonHome) {
    $driveRoot = [System.IO.Path]::GetPathRoot($PSScriptRoot)
    if (([System.IO.DriveInfo]::new($driveRoot)).AvailableFreeSpace -lt 1GB) {
        Fail "At least 1 GB of free space is required on $driveRoot to prepare Python. Free some space or choose another folder, then click Retry."
    }
    $package = Join-Path $setupRoot "python-$PythonVersion.nupkg"
    if (Test-Path -LiteralPath $package) {
        if ((Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ne $PackageSha256) {
            Remove-Item -LiteralPath $package -Force
        }
    }
    if (-not (Test-Path -LiteralPath $package)) {
        Say "Download Python $PythonVersion (about 14 MB), required only during first setup..."
        $ProgressPreference = 'SilentlyContinue'
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        try {
            Invoke-WebRequest $PackageUrl -OutFile ($package + '.part') -UseBasicParsing
        } catch {
            Fail "Download incomplete: Python $PythonVersion could not be downloaded from nuget.org ($($_.Exception.Message)). Check the internet connection, proxy or firewall, then click Retry."
        }
        if ((Get-FileHash -LiteralPath ($package + '.part') -Algorithm SHA256).Hash -ne $PackageSha256) {
            Remove-Item -LiteralPath ($package + '.part') -Force
            Fail "The downloaded Python package is damaged or was altered (checksum mismatch). It has been deleted: click Retry to download it again. If this repeats, a proxy or antivirus is modifying downloads."
        }
        Move-Item -LiteralPath ($package + '.part') -Destination $package -Force
    }

    Say "Installing Python $PythonVersion in the application folder..."
    $staging = $pythonHome + '.tmp'
    foreach ($folder in $staging, $pythonHome) {
        if (Test-Path -LiteralPath $folder) {
            try { Remove-Item -LiteralPath $folder -Recurse -Force }
            catch { Fail "The folder $folder is in use and cannot be replaced. Close any running Virtual Human or Python window, then click Retry." }
        }
    }
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($package, $staging)
        Move-Item -LiteralPath (Join-Path $staging 'tools') -Destination $pythonHome
        Remove-Item -LiteralPath $staging -Recurse -Force
    } catch {
        Fail "Python could not be extracted into $pythonHome ($($_.Exception.Message)). An antivirus or a sync tool (OneDrive, Dropbox) may be blocking the files: pause it or move the application to a local folder such as C:\VirtualHuman, then click Retry."
    }

    $pythonExe = Join-Path $pythonHome 'python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        Fail "python.exe is missing from $pythonHome after extraction. An antivirus probably quarantined it: check its history, allow the file, then click Retry."
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $pythonExe
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        Remove-Item -LiteralPath $pythonHome -Recurse -Force -ErrorAction SilentlyContinue
        Fail "The extracted python.exe is not signed by the Python Software Foundation (status: $($signature.Status)). Installation stopped for safety."
    }
    return $pythonExe
}

Say 'PROGRESS 1'
try {
    Set-Location -LiteralPath $PSScriptRoot
    $setupRoot = Join-Path $PSScriptRoot '.setup'
    New-Item -ItemType Directory -Path $setupRoot -Force | Out-Null
    $pythonHome = Join-Path $PSScriptRoot '.python'
    $pythonPath = Join-Path $pythonHome 'python.exe'

    if (-not (Test-Python312 $pythonPath)) {
        # Reuse an existing 3.12 interpreter when possible; never install into its environment.
        $pythonPath = $null
        if (Get-Command py -ErrorAction SilentlyContinue) {
            try {
                $candidate = & py -3.12 -c 'import sys; print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0 -and $candidate -and (Test-Python312 $candidate.Trim())) { $pythonPath = $candidate.Trim() }
            } catch { }
        }
        if ($pythonPath) {
            Say "Using the Python 3.12 already installed: $pythonPath"
        } else {
            Say 'Python 3.12 not found: preparing a local copy.'
            $pythonPath = Install-LocalPython $setupRoot $pythonHome
        }
    }

    if (-not (Test-Python312 $pythonPath)) {
        Fail "Python at $pythonPath does not start or is not 64-bit Python 3.12. An antivirus may be blocking it: allow the application folder, then click Retry."
    }
} catch {
    Fail "Python setup failed: $($_.Exception.Message)"
}

$installArguments = @((Join-Path $PSScriptRoot 'install.py'), '--profile', $Profile,
    '--voice-device', $VoiceDevice, '--transcription-device', $TranscriptionDevice,
    '--transcription-models', $TranscriptionModels, '--voice-models', $VoiceModels)
Say 'PROGRESS 3'
if ($Yes) { $installArguments += '--yes' }
if ($Plan) { $installArguments += '--plan' }
& $pythonPath @installArguments
exit $LASTEXITCODE
