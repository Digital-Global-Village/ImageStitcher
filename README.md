# ImageStitcher

A lightweight cross-platform image-stitching app with a Tkinter GUI and command-line interface.

It preserves aspect ratios, offers Smart Match resizing for uneven images, previews results, and exports PNG, JPG, or TIFF. No Xcode, Swift, Homebrew, or paid tools are required.

## Downloads

GitHub Actions produces two installable artifacts:

- `ImageStitcher.dmg` for macOS.
- `ImageStitcher-Setup.exe` for 64-bit Windows.

Builds are currently unsigned. On macOS, right-click the app and choose `Open` the first time. On Windows, SmartScreen may ask you to confirm the locally built installer.

## Run From Source

Install Python 3.11 or newer from <https://www.python.org/downloads/>. On Windows, select `Add Python to PATH` during installation.

Check Python:

```sh
python3 --version
```

On Windows, use `python --version` or `py -3 --version`.

## Install Dependencies

```sh
cd PythonImageStitcher
python3 -m pip install -r requirements.txt
```

Dependencies:

- `Pillow` for image processing.
- `PyInstaller` for building the `.app`.

## Run The GUI Directly

```sh
cd PythonImageStitcher
python3 image_stitcher_gui.py
```

The GUI includes:

- Add Images
- Remove Selected
- Clear All
- Move Up / Move Down
- A cleaner image table with pixel sizes
- Horizontal / Vertical stitching
- Spacing
- Background: transparent, white, black
- Output format: PNG, JPG, TIFF
- JPG quality
- Scale modes
- Smart Match resizing, which automatically matches heights for horizontal stitches and widths for vertical stitches
- Start, center, or end alignment for mixed-size images
- Presets for receipts, tickets, screenshots, and PDF page images
- Gentle enhancement modes: none, autocontrast, sharpen, text
- Preview
- Estimated output dimensions
- Save As

In-window drag/drop is not included because built-in Tkinter does not provide reliable native macOS file drop support without extra packages. You can drag files onto the packaged app icon and macOS may pass them into the app.

## Run The CLI

Horizontal:

```sh
python3 stitch_images.py horizontal image1.jpg image2.jpg image3.jpg -o output.png
```

Vertical with spacing:

```sh
python3 stitch_images.py vertical page1.png page2.png page3.png -o combined.png --spacing 20 --background white
```

Advanced examples:

```sh
python3 stitch_images.py horizontal *.png -o strip.jpg --format jpg --quality 92 --background white
```

```sh
python3 stitch_images.py vertical page1.png page2.png --same-width --no-upscale --format tiff -o pages.tiff
```

```sh
python3 stitch_images.py horizontal a.jpg b.jpg --max-height 900 --preview-info -o output.png
```

Automatically normalize uneven image sizes while preserving proportions:

```sh
python3 stitch_images.py horizontal a.jpg b.jpg --smart-match --no-upscale --align center -o matched.png
```

Text enhancement:

```sh
python3 stitch_images.py vertical receipt1.jpg receipt2.jpg --same-width --no-upscale --enhance text --background white -o receipts.png
```

CLI options:

```sh
python3 stitch_images.py --help
```

## Output Location

If you use:

```sh
-o output.png
```

the file is saved in the current Terminal folder.

If you use:

```sh
-o "/Users/you/Desktop/output.png"
```

the file is saved exactly there.

If you omit `-o`, the script saves:

- `stitched_output.png` for PNG
- `stitched_output.jpg` for JPG
- `stitched_output.tiff` for TIFF

## Double-Click Launcher

The launcher is:

```sh
stitch_images.command
```

It can start either:

- GUI mode
- CLI guided mode

Make it executable if needed:

```sh
chmod +x stitch_images.command
```

Then double-click it in Finder.

## Build The macOS .app

```sh
cd PythonImageStitcher
./build_app.sh
```

Output:

```sh
dist/ImageStitcher.app
```

The build command uses:

```sh
pyinstaller --windowed --name ImageStitcher image_stitcher_gui.py
```

## App Icon

Optional: place platform icons in the repository root:

```sh
icon.icns
icon.ico
```

The macOS build uses `icon.icns`; the Windows build and installer use `icon.ico`. Builds use default icons when those files are absent.

## Build The DMG

```sh
cd PythonImageStitcher
./build_dmg.sh
```

Output:

```sh
ImageStitcher.dmg
```

The DMG script uses macOS `hdiutil`, which is built into macOS. It builds the app first if `dist/ImageStitcher.app` is missing.

## Build The Windows App And Installer

Windows builds must run on Windows; PyInstaller cannot cross-compile a Windows executable from macOS.

1. Install Python 3 from <https://www.python.org/downloads/windows/>.
2. Install Inno Setup 6 from <https://jrsoftware.org/isdl.php>.
3. Open Command Prompt in the project folder.
4. Run:

```bat
build_windows.bat
```

Outputs:

```text
dist\ImageStitcher\ImageStitcher.exe
dist-windows\ImageStitcher-Setup.exe
```

If Inno Setup is absent, the script still creates the portable PyInstaller app and explains how to finish the installer.

## Tests

```sh
python3 -m unittest discover -s tests -v
python3 stitch_images.py --help
```

On Windows, replace `python3` with `python` or `py -3`.

## GitHub Repository And Releases

The repository includes:

- `.gitignore` for Python and package outputs.
- Tests for Smart Match resizing and JPG transparency flattening.
- A cross-platform test workflow for macOS, Windows, and Linux.
- An installer workflow that builds macOS DMG and Windows Setup EXE artifacts.

Create a repository and push it:

```sh
git init
git add .
git commit -m "Initial ImageStitcher release"
git branch -M main
git remote add origin https://github.com/YOUR-NAME/ImageStitcher.git
git push -u origin main
```

To build installers manually on GitHub, open `Actions`, choose `Build Installers`, and select `Run workflow`.

To trigger versioned installer builds, update `VERSION`, commit it, then create and push a matching tag. The macOS bundle, Windows executable, and Windows installer all read this version:

```sh
git tag v1.0.0
git push origin v1.0.0
```

Manual workflow runs place installers in the workflow's `Artifacts` section. Pushing a `v*` tag also creates a GitHub Release and attaches both installers automatically. Code signing can be added later once Apple and Windows signing certificates are available.

Local macOS packages use the architecture of the Python/Pillow installation that builds them. The included local DMG is Apple-silicon (`arm64`). Build on an Intel Mac or the GitHub macOS runner when an Intel package is needed.

## Image Quality Notes

ImageStitcher never stretches images unnaturally. It preserves aspect ratio and uses Pillow LANCZOS resizing for clean downscaling.

`Smart Match` is recommended for mixed-size images. For horizontal stitching it makes every image the same height; for vertical stitching it makes every image the same width. With `Do not upscale` enabled, the app matches to the smallest relevant image, avoiding added pixelation.

Enhancement modes are intentionally conservative:

- `none`: preserve the original look.
- `autocontrast`: improve low-contrast scans or dull screenshots.
- `sharpen`: gentle sharpening after resize.
- `text`: mild contrast plus sharpening for receipts, tickets, and document images.

For best results:

- Receipts: vertical, same width, white background, PNG or JPG quality 92.
- Tickets: horizontal or vertical depending on layout, original size, white background.
- Screenshots: original size or same width, PNG, transparent or white background.
- PDF page images: vertical, same width, PNG or TIFF, use `--no-upscale`.

To reduce pixelation:

- Avoid enlarging small images.
- Turn on `Do not upscale` in the GUI.
- Use `--no-upscale` in the CLI.
- Prefer making large images smaller instead of small images larger.
- Use PNG/TIFF for screenshots and text-heavy images.
- Use JPG only for photo-like images.

## Transparency Rules

- PNG and TIFF can preserve transparent backgrounds.
- JPG cannot store transparency.
- If exporting JPG with transparent background, ImageStitcher flattens onto white.
- For JPG exports, choose white or black background intentionally.

## Supported Images

Accepted extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.heic`
- `.heif`
- `.tif`
- `.tiff`

JPG, PNG, TIFF, and WEBP usually work with Pillow. HEIC depends on the installed Pillow/macOS image libraries. If HEIC does not open, convert it to PNG or JPG first.

## Common Issues

`ModuleNotFoundError: No module named 'PIL'`

Run:

```sh
python3 -m pip install -r requirements.txt
```

`pyinstaller: command not found`

Use:

```sh
python3 -m PyInstaller --version
```

or reinstall:

```sh
python3 -m pip install -r requirements.txt
```

macOS says the app cannot be opened because it is from an unidentified developer.

This is normal for a locally built unsigned app. Right-click the app, choose `Open`, then confirm.

The output is too large.

Use fewer images, add `--max-width`, add `--max-height`, or turn on `--no-upscale`.

Windows cannot find Inno Setup.

Install Inno Setup 6 and rerun `build_windows.bat`. The portable app in `dist\ImageStitcher` remains usable even without the installer.

## License

ImageStitcher is available under the MIT License. See `LICENSE`.
