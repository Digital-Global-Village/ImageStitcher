#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller-cache"

APP_VERSION=$(tr -d '[:space:]' < VERSION)
PACKAGE_ARCH=$(dpkg --print-architecture)
PACKAGE_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/imagestitcher-deb.XXXXXX")
trap 'rm -rf "$PACKAGE_ROOT"' EXIT

python3 -m pip install -r requirements.txt
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name ImageStitcher \
  --additional-hooks-dir . \
  image_stitcher_gui.py

INSTALL_ROOT="$PACKAGE_ROOT/opt/imagestitcher"
mkdir -p "$INSTALL_ROOT" "$PACKAGE_ROOT/usr/bin" "$PACKAGE_ROOT/usr/share/applications" "$PACKAGE_ROOT/DEBIAN"
cp -R dist/ImageStitcher/. "$INSTALL_ROOT/"
ln -s /opt/imagestitcher/ImageStitcher "$PACKAGE_ROOT/usr/bin/imagestitcher"

install -m 0644 packaging/linux/imagestitcher.desktop "$PACKAGE_ROOT/usr/share/applications/imagestitcher.desktop"
if [[ -f "icon.png" ]]; then
  mkdir -p "$PACKAGE_ROOT/usr/share/icons/hicolor/256x256/apps"
  install -m 0644 icon.png "$PACKAGE_ROOT/usr/share/icons/hicolor/256x256/apps/imagestitcher.png"
fi

sed \
  -e "s/@VERSION@/$APP_VERSION/g" \
  -e "s/@ARCH@/$PACKAGE_ARCH/g" \
  packaging/linux/control.in > "$PACKAGE_ROOT/DEBIAN/control"

mkdir -p dist-linux
DEB_PATH="dist-linux/imagestitcher_${APP_VERSION}_${PACKAGE_ARCH}.deb"
dpkg-deb --root-owner-group --build "$PACKAGE_ROOT" "$DEB_PATH"

echo
echo "Built Linux installer: $DEB_PATH"
