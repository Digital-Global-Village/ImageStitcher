#!/bin/zsh
set -e

cd "$(dirname "$0")"

APP_PATH="dist/ImageStitcher.app"
DMG_NAME="ImageStitcher.dmg"
STAGING_DIR=$(mktemp -d "${TMPDIR:-/tmp}/imagestitcher-dmg.XXXXXX")
trap 'rm -rf "$STAGING_DIR"' EXIT

if [[ ! -d "$APP_PATH" ]]; then
  echo "App not found. Building dist/ImageStitcher.app first..."
  ./build_app.sh
fi

cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

hdiutil create -volname "ImageStitcher" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_NAME"

echo
echo "Built: $DMG_NAME"
