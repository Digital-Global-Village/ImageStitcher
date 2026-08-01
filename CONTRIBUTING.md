# Contributing

Thanks for helping improve ImageStitcher.

## Development Setup

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Run the GUI with `python image_stitcher_gui.py`.

## Before Opening A Pull Request

Run:

```sh
python -m unittest discover -s tests -v
python -m py_compile stitch_images.py image_stitcher_gui.py
python stitch_images.py --help
```

Keep image processing in `stitch_images.py` so the GUI and CLI share the same behavior. Preserve aspect ratios, avoid unnecessary upscaling, and include a focused test for behavior changes.

Do not commit generated files from `build/`, `dist/`, `dist-windows/`, or local test images.
