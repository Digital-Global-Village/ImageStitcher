$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot ".pyinstaller-cache"

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $pythonCommand = $python.Source
    $pythonArgs = @()
} else {
    $pythonCommand = "py"
    $pythonArgs = @("-3")
}

& $pythonCommand @pythonArgs -m pip install -r requirements.txt
& $pythonCommand @pythonArgs generate_windows_version.py

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", "ImageStitcher",
    "--version-file", ".build-meta\windows_version_info.txt"
)
if (Test-Path "icon.ico") {
    $pyInstallerArgs += @("--icon", "icon.ico")
}
$pyInstallerArgs += "image_stitcher_gui.py"

& $pythonCommand @pythonArgs @pyInstallerArgs

$isccCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue
$isccPath = if ($isccCommand) { $isccCommand.Source } else { $null }
if (-not $isccPath) {
    $defaultIscc = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
    if (Test-Path $defaultIscc) {
        $isccPath = $defaultIscc
    }
}

if (-not $isccPath) {
    Write-Host ""
    Write-Host "Built portable app: dist\ImageStitcher\ImageStitcher.exe"
    Write-Host "Inno Setup 6 was not found, so the installer was not created."
    Write-Host "Install it from https://jrsoftware.org/isdl.php and run this script again."
    exit 0
}

$version = (Get-Content "VERSION" -Raw).Trim()
& $isccPath "/DAppVersion=$version" "installer_windows.iss"

New-Item -ItemType Directory -Force -Path "dist-windows" | Out-Null
Copy-Item "Output\ImageStitcher-Setup.exe" "dist-windows\ImageStitcher-Setup.exe" -Force

Write-Host ""
Write-Host "Built portable app: dist\ImageStitcher\ImageStitcher.exe"
Write-Host "Built installer: dist-windows\ImageStitcher-Setup.exe"
