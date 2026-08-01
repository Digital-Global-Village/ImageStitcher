#!/bin/zsh

cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found."
  echo "Install Python 3 from https://www.python.org/downloads/macos/"
  read -r "?Press Return to close."
  exit 1
fi

echo "ImageStitcher"
echo
echo "If this is your first time running it, install dependencies with:"
echo "python3 -m pip install -r requirements.txt"
echo
echo "Choose mode:"
echo "1) GUI app window"
echo "2) CLI guided stitch"
echo
read -r "?Mode [1]: " mode
mode=${mode:-1}

if [[ "$mode" == "1" ]]; then
  python3 image_stitcher_gui.py
  exit $?
fi

read -r "?Direction (horizontal/vertical) [horizontal]: " direction
direction=${direction:-horizontal}

read -r "?Spacing in pixels [0]: " spacing
spacing=${spacing:-0}

echo
echo "Resize mode:"
echo "1) Smart Match (recommended)"
echo "2) Original sizes"
echo "3) Match heights"
echo "4) Match widths"
read -r "?Resize mode [1]: " resize_mode
resize_mode=${resize_mode:-1}

RESIZE_ARGS=()
case "$resize_mode" in
  1) RESIZE_ARGS=(--smart-match --no-upscale) ;;
  3) RESIZE_ARGS=(--same-height --no-upscale) ;;
  4) RESIZE_ARGS=(--same-width --no-upscale) ;;
esac

read -r "?Alignment (start/center/end) [center]: " alignment
alignment=${alignment:-center}

read -r "?Background (transparent/white/black/#hex) [transparent]: " background
background=${background:-transparent}

read -r "?Format (png/jpg/tiff) [png]: " format
format=${format:-png}

read -r "?Enhance (none/autocontrast/sharpen/text) [none]: " enhance
enhance=${enhance:-none}

quality=95
if [[ "$format" == "jpg" ]]; then
  read -r "?JPG quality 1-100 [95]: " quality
  quality=${quality:-95}
fi

read -r "?Output file name [stitched_output.$format]: " output
output=${output:-stitched_output.$format}

echo
echo "Drag image files into this window, then press Return."
read -r "?Images: " image_line

if [[ -z "$image_line" ]]; then
  echo "No images provided."
  read -r "?Press Return to close."
  exit 1
fi

python3 stitch_images.py "$direction" ${(z)image_line} -o "$output" --spacing "$spacing" --background "$background" --format "$format" --quality "$quality" --enhance "$enhance" --align "$alignment" "${RESIZE_ARGS[@]}"

echo
read -r "?Done. Press Return to close."
