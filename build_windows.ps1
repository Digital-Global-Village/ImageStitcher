$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot ".pyinstaller-cache"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonArgs = @("-3")
    $pythonCommand = "py"
} else {
    $pythonCommand = "python"
    $pythonArgs = @()
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

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $defaultIscc = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
    if (Test-Path $defaultIscc) {
        $iscc = Get-Item $defaultIscc
    }
}

if (-not $iscc) {
    Write-Host ""
    Write-Host "Built portable app: dist\ImageStitcher\ImageStitcher.exe"
    Write-Host "Inno Setup 6 was not found, so the installer was not created."
    Write-Host "Install it from https://jrsoftware.org/isdl.php and run this script again."
    exit 0
}

$version = (Get-Content "VERSION" -Raw).Trim()
& $iscc.FullName "/DAppVersion=$version" "installer_windows.iss"

New-Item -ItemType Directory -Force -Path "dist-windows" | Out-Null
Copy-Item "Output\ImageStitcher-Setup.exe" "dist-windows\ImageStitcher-Setup.exe" -Force

Write-Host ""
Write-Host "Built portable app: dist\ImageStitcher\ImageStitcher.exe"
Write-Host "Built installer: dist-windows\ImageStitcher-Setup.exe"
