#!/bin/zsh
set -e

cd "$(dirname "$0")"
export PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller-cache"
APP_VERSION=$(tr -d '[:space:]' < VERSION)

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install it from https://www.python.org/downloads/macos/"
  exit 1
fi

python3 -m pip install -r requirements.txt

ICON_ARGS=()
if [[ -f "icon.icns" ]]; then
  ICON_ARGS=(--icon icon.icns)
fi

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name ImageStitcher \
  --osx-bundle-identifier org.imagestitcher.app \
  "${ICON_ARGS[@]}" \
  image_stitcher_gui.py

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "dist/ImageStitcher.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $APP_VERSION" "dist/ImageStitcher.app/Contents/Info.plist"
codesign --force --deep --sign - "dist/ImageStitcher.app"

echo
echo "Built: dist/ImageStitcher.app"
