$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultFosunEnv = Join-Path (Join-Path $HOME ".workbuddy\star-wealth-openapi") "fosun.env"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DefaultFosunEnv) | Out-Null
if (-not $env:FOSUN_ENV_PATH) { $env:FOSUN_ENV_PATH = $DefaultFosunEnv }

function Pick([string]$Name, [string]$FallbackName, [string]$Default) {
    $value = [Environment]::GetEnvironmentVariable($Name)
    if (-not $value -and $FallbackName) { $value = [Environment]::GetEnvironmentVariable($FallbackName) }
    if (-not $value) { $value = $Default }
    return $value
}

$VenvDir = Pick "FW_TRADE_VENV" "MONI_VENV" (Join-Path $SkillRoot ".venv")
$PinPythonVersion = Pick "FW_TRADE_PYTHON_VERSION" "MONI_PYTHON_VERSION" "3.13"
$SdkVersion = Pick "FW_TRADE_SDK_VERSION" "MONI_SDK_VERSION" "v1.2.0"
$SdkZipUrlPrimary = Pick "FW_TRADE_SDK_URL" "MONI_SDK_URL" "https://openapi-docs.fosunxcz.com/download/sdk/openapi-python-sdk-1.2.0.zip"
$SdkZipUrlFallback = Pick "FW_TRADE_SDK_FALLBACK_URL" "MONI_SDK_FALLBACK_URL" "https://github.com/fosunwealth/openapi-python-sdk/archive/refs/tags/v1.2.0.zip"
$SdkZipSha256 = Pick "FW_TRADE_SDK_SHA256" "MONI_SDK_SHA256" "bfba27b338c7811e5c7ded57c03d901904d92f8339183b5c45714e81c4b52771"
$DefaultCache = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "fw-trade-skill\cache" } else { Join-Path $HOME ".cache\fw-trade-skill" }
$SdkCacheRoot = Pick "FW_TRADE_CACHE_DIR" "MONI_CACHE_DIR" $DefaultCache
$SdkCacheDir = Join-Path $SdkCacheRoot "openapi-python-sdk-$SdkVersion"
$UvInstallerVersion = Pick "FW_TRADE_UV_VERSION" "" "0.12.11"
$UvInstallerUrl = "https://astral.sh/uv/$UvInstallerVersion/install.ps1"
$UvInstallerSha256 = Pick "FW_TRADE_UV_SHA256" "" "5c9ee4bdde929f86e65d71165685f90c933746765b0765451f6c5851fa14f862"

function Log([string]$msg) { Write-Host "[fw-trade] $msg" -ForegroundColor Cyan }
function Fail([string]$msg) { Write-Host "[fw-trade ERROR] $msg" -ForegroundColor Red; exit 1 }
function Get-Sha256([string]$Path) { (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Https([string]$Url) {
    if ($Url -notlike "https://*") { Fail "Refusing a non-HTTPS download URL: $Url" }
}

function Ensure-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Log "uv found: $((Get-Command uv).Source)"
        return
    }
    Log "uv not found. Installing pinned uv $UvInstallerVersion (official URL, SHA256 checked)..."
    Require-Https $UvInstallerUrl
    $UvInstallerPath = Join-Path ([System.IO.Path]::GetTempPath()) ("uv-installer-" + $UvInstallerVersion + ".ps1")
    try { Invoke-WebRequest -Uri $UvInstallerUrl -OutFile $UvInstallerPath }
    catch { Fail "Could not download the uv installer. Install uv by hand: https://docs.astral.sh/uv/getting-started/installation/" }
    $ActualSha = Get-Sha256 $UvInstallerPath
    if ($ActualSha -ne $UvInstallerSha256.ToLowerInvariant()) {
        Fail "uv installer SHA256 mismatch (expected $UvInstallerSha256, got $ActualSha). Stopping so a tampered installer is not run."
    }
    Log "uv installer SHA256 ok."
    & $UvInstallerPath
    Remove-Item -Force -ErrorAction SilentlyContinue $UvInstallerPath
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { Fail "uv install failed. Install uv by hand and rerun." }
    Log "uv installed: $((Get-Command uv).Source)"
}

Ensure-Uv

$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Log "Creating the shared environment (uv downloads Python $PinPythonVersion if needed): $VenvDir"
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $VenvDir) | Out-Null
    uv venv --python $PinPythonVersion "$VenvDir"
} else {
    Log "Reusing the shared environment: $VenvDir"
}
if (-not (Test-Path $VenvPy)) { Fail "Shared environment was not created. Interpreter missing: $VenvPy" }

$SdkReady = $false
try {
    & $VenvPy -c "import fsopenapi" 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $SdkCacheDir)) { $SdkReady = $true }
} catch { $SdkReady = $false }
if ($SdkReady) {
    Log "SDK is already installed and the cache is present. Skipping download (to reinstall, delete $SdkCacheDir and rerun)."
} else {
    $TmpBuildDir = Join-Path ([System.IO.Path]::GetTempPath()) ("fw-trade-build-" + [guid]::NewGuid().ToString("N"))
    $SdkZipPath = Join-Path $TmpBuildDir "openapi-python-sdk.zip"
    $SdkExtractDir = Join-Path $TmpBuildDir "src"
    New-Item -ItemType Directory -Force -Path $SdkExtractDir | Out-Null
    try {
        Require-Https $SdkZipUrlPrimary
        if ($env:FW_TRADE_SDK_URL -or $env:MONI_SDK_URL) {
            Log "Custom SDK URL is set. SHA256 is still checked."
        }
        Log "Downloading the SDK (primary URL, HTTPS, SHA256 checked): $SdkZipUrlPrimary"
        $SdkDownloaded = $false
        $SdkZipUrl = $SdkZipUrlPrimary
        try {
            Invoke-WebRequest -Uri $SdkZipUrlPrimary -OutFile $SdkZipPath
            if ((Get-Sha256 $SdkZipPath) -eq $SdkZipSha256.ToLowerInvariant()) {
                Log "SDK zip SHA256 ok."
                $SdkDownloaded = $true
            } else { Log "Primary SHA256 did not match. Trying the official GitHub archive..." }
        } catch { Log "Primary download failed. Trying the official GitHub archive..." }
        if (-not $SdkDownloaded) {
            if (-not $SdkZipUrlFallback -or $SdkZipUrlFallback -eq $SdkZipUrlPrimary) {
                Fail "Primary URL failed and no fallback is configured. Set FW_TRADE_SDK_URL / FW_TRADE_SDK_FALLBACK_URL / FW_TRADE_SDK_SHA256 and rerun."
            }
            Require-Https $SdkZipUrlFallback
            Invoke-WebRequest -Uri $SdkZipUrlFallback -OutFile $SdkZipPath
            if ((Get-Sha256 $SdkZipPath) -ne $SdkZipSha256.ToLowerInvariant()) {
                Fail "SDK zip SHA256 mismatch (expected $SdkZipSha256, got $((Get-Sha256 $SdkZipPath))). Stopping so a tampered package is not installed."
            }
            Log "SDK zip SHA256 ok (official fallback)."
            $SdkZipUrl = $SdkZipUrlFallback
        }
        Log "Unpacking the SDK zip"
        Expand-Archive -Path $SdkZipPath -DestinationPath $SdkExtractDir -Force
        $SdkExtractedDir = Get-ChildItem -Path $SdkExtractDir -Recurse -File |
            Where-Object { $_.Name -in @("setup.py", "pyproject.toml") } |
            Select-Object -First 1 |
            ForEach-Object { $_.Directory.FullName }
        if (-not $SdkExtractedDir) { Fail "setup.py / pyproject.toml not found in the unpacked SDK" }
        New-Item -ItemType Directory -Force -Path $SdkCacheRoot | Out-Null
        if (Test-Path $SdkCacheDir) { Remove-Item -Recurse -Force $SdkCacheDir }
        Copy-Item -Path $SdkExtractedDir -Destination $SdkCacheDir -Recurse
        Log "SDK cache: $SdkCacheDir"
        Log "Installing the fsopenapi SDK (editable, official PyPI)"
        uv pip install --python "$VenvPy" --reinstall --editable "$SdkCacheDir"
        if ($LASTEXITCODE -ne 0) { Fail "Install from https://pypi.org failed. Check that this machine can reach it, then rerun install.ps1." }
        Log "Installing QR dependencies (qrcode and Pillow) from official PyPI"
        uv pip install --python "$VenvPy" "qrcode[pil]>=7.4"
        if ($LASTEXITCODE -ne 0) { Fail "Install from https://pypi.org failed. Check that this machine can reach it, then rerun install.ps1." }
    } finally {
        if (Test-Path $TmpBuildDir) { Remove-Item -Recurse -Force $TmpBuildDir }
    }
}

Log "Checking import fsopenapi"
& $VenvPy -c "import fsopenapi; print('  fsopenapi @', fsopenapi.__file__)"
Log "Checking import qrcode and PIL"
& $VenvPy -c "import qrcode; from PIL import Image; print('  qrcode + Pillow OK')"
Write-Host "Install finished."
Write-Host "Python: $VenvPy"
Write-Host "Skill root: $SkillRoot"
Write-Host "Shared credential: $($env:FOSUN_ENV_PATH)"
