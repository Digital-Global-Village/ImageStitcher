#!/usr/bin/env python3
"""
stitch_images.py

A lightweight image stitching tool for macOS, using Python 3 and Pillow.

Examples:
    python3 stitch_images.py horizontal image1.jpg image2.jpg image3.jpg -o output.png
    python3 stitch_images.py vertical page1.png page2.png page3.png -o combined.png --spacing 20 --background white
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}
MAX_OUTPUT_PIXELS = 120_000_000
MAX_OUTPUT_SIDE = 65_535
UPSCALE_WARNING_FACTOR = 1.5


class StitchError(Exception):
    """Friendly application-level error."""


@dataclass
class StitchOptions:
    direction: str = "horizontal"
    spacing: int = 0
    background: str = "transparent"
    output_format: str = "png"
    quality: int = 95
    smart_match: bool = False
    same_height: bool = False
    same_width: bool = False
    max_width: int | None = None
    max_height: int | None = None
    no_upscale: bool = False
    enhance: str = "none"
    alignment: str = "center"


@dataclass
class PreparedImage:
    path: Path
    image: Any
    original_size: tuple[int, int]
    scale: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stitch multiple images into one image.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("direction", choices=["horizontal", "vertical"], help="Stitch direction.")
    parser.add_argument("images", nargs="+", help="Image files in the exact order to stitch.")
    parser.add_argument("-o", "--output", default=None, help="Output path.")
    parser.add_argument("--spacing", type=int, default=0, help="Spacing between images, in pixels.")
    parser.add_argument(
        "--background",
        default="transparent",
        help="Background: transparent, white, black, or a hex color like #f5f5f5.",
    )
    parser.add_argument("--same-height", action="store_true", help="Resize all images to the same height.")
    parser.add_argument("--same-width", action="store_true", help="Resize all images to the same width.")
    parser.add_argument(
        "--smart-match",
        action="store_true",
        help="Match heights for horizontal stitching or widths for vertical stitching.",
    )
    parser.add_argument("--max-width", type=int, default=None, help="Fit each image within this width.")
    parser.add_argument("--max-height", type=int, default=None, help="Fit each image within this height.")
    parser.add_argument("--quality", type=int, default=95, help="JPG quality from 1 to 100.")
    parser.add_argument("--format", choices=["png", "jpg", "tiff"], default="png", help="Output format.")
    parser.add_argument("--no-upscale", action="store_true", help="Prevent resizing above original size.")
    parser.add_argument(
        "--align",
        choices=["start", "center", "end"],
        default="center",
        help="Align images on the cross axis.",
    )
    parser.add_argument(
        "--enhance",
        choices=["none", "autocontrast", "sharpen", "text"],
        default="none",
        help="Optional gentle enhancement before stitching.",
    )
    parser.add_argument("--preview-info", action="store_true", help="Print estimated output details before saving.")
    return parser.parse_args()


def fail(message: str) -> None:
    raise StitchError(message)


def require_pillow() -> tuple[Any, type[Exception]]:
    try:
        from PIL import Image, UnidentifiedImageError
    except ModuleNotFoundError:
        fail("Pillow is not installed. Run: python3 -m pip install -r requirements.txt")

    return Image, UnidentifiedImageError


def validate_paths(paths: Iterable[str]) -> list[Path]:
    image_paths: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.exists():
            fail(f'File not found: "{path}"')
        if not path.is_file():
            fail(f'Not a file: "{path}"')
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            fail(
                f'Unsupported file type: "{path.name}". '
                "Supported: jpg, jpeg, png, webp, heic, heif, tif, tiff."
            )
        image_paths.append(path)
    return image_paths


def load_source_images(paths: list[Path]) -> list[PreparedImage]:
    Image, UnidentifiedImageError = require_pillow()
    loaded: list[PreparedImage] = []

    for path in paths:
        try:
            image = Image.open(path)
            image.load()
        except UnidentifiedImageError:
            if path.suffix.lower() in {".heic", ".heif"}:
                fail(
                    f'Could not open "{path.name}". HEIC support depends on the installed Pillow build. '
                    "Convert it to PNG/JPG first if it does not open."
                )
            fail(f'Could not identify "{path.name}" as an image.')
        except OSError as exc:
            fail(f'Could not open "{path.name}": {exc}')

        rgba = image.convert("RGBA")
        loaded.append(PreparedImage(path=path, image=rgba, original_size=rgba.size, scale=1.0))

    return loaded


def parse_background(background: str) -> tuple[int, int, int, int]:
    value = background.strip().lower()
    if value == "transparent":
        return (0, 0, 0, 0)
    if value == "white":
        return (255, 255, 255, 255)
    if value == "black":
        return (0, 0, 0, 255)
    if value.startswith("#") and len(value) in {4, 7}:
        if len(value) == 4:
            value = "#" + "".join(ch * 2 for ch in value[1:])
        try:
            return (
                int(value[1:3], 16),
                int(value[3:5], 16),
                int(value[5:7], 16),
                255,
            )
        except ValueError:
            pass
    fail('Background must be transparent, white, black, or a hex color like "#f5f5f5".')


def validate_options(options: StitchOptions) -> None:
    if options.spacing < 0:
        fail("Spacing must be 0 or greater.")
    if options.max_width is not None and options.max_width <= 0:
        fail("--max-width must be greater than 0.")
    if options.max_height is not None and options.max_height <= 0:
        fail("--max-height must be greater than 0.")
    if not 1 <= options.quality <= 100:
        fail("--quality must be between 1 and 100.")
    if options.enhance not in {"none", "autocontrast", "sharpen", "text"}:
        fail("--enhance must be none, autocontrast, sharpen, or text.")
    if options.alignment not in {"start", "center", "end"}:
        fail("--align must be start, center, or end.")
    parse_background(options.background)


def enhance_image(image: Any, mode: str) -> Any:
    if mode == "none":
        return image

    try:
        from PIL import ImageEnhance, ImageOps
    except ModuleNotFoundError:
        fail("Pillow is not installed. Run: python3 -m pip install -r requirements.txt")

    alpha = image.getchannel("A") if image.mode == "RGBA" else None
    rgb = image.convert("RGB")

    if mode == "autocontrast":
        enhanced = ImageOps.autocontrast(rgb, cutoff=1)
    elif mode == "sharpen":
        enhanced = ImageEnhance.Sharpness(rgb).enhance(1.35)
    else:
        enhanced = ImageOps.autocontrast(rgb, cutoff=2)
        enhanced = ImageEnhance.Contrast(enhanced).enhance(1.12)
        enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.2)

    result = enhanced.convert("RGBA")
    if alpha is not None:
        result.putalpha(alpha)
    return result


def resize_with_quality(image: Any, size: tuple[int, int]) -> Any:
    if image.size == size:
        return image
    Image, _ = require_pillow()
    resampling = getattr(Image, "Resampling", Image).LANCZOS
    return image.resize(size, resampling)


def scaled_size(
    size: tuple[int, int],
    target_width: int | None,
    target_height: int | None,
    no_upscale: bool,
) -> tuple[int, int, float]:
    width, height = size
    scale = 1.0

    if target_width is not None and target_height is not None:
        scale = min(target_width / width, target_height / height)
    elif target_width is not None:
        scale = target_width / width
    elif target_height is not None:
        scale = target_height / height

    if no_upscale:
        scale = min(scale, 1.0)

    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))
    return new_width, new_height, scale


def prepare_images(images: list[PreparedImage], options: StitchOptions) -> tuple[list[PreparedImage], list[str]]:
    validate_options(options)
    if not images:
        fail("Please provide at least one image.")

    warnings: list[str] = []
    target_width = options.max_width
    target_height = options.max_height

    same_height = options.same_height or (options.smart_match and options.direction == "horizontal")
    same_width = options.same_width or (options.smart_match and options.direction == "vertical")

    if same_height:
        heights = [item.original_size[1] for item in images]
        target_height = min(heights) if options.no_upscale else max(heights)
    if same_width:
        widths = [item.original_size[0] for item in images]
        target_width = min(widths) if options.no_upscale else max(widths)

    prepared: list[PreparedImage] = []
    for item in images:
        new_width, new_height, scale = scaled_size(
            item.original_size,
            target_width,
            target_height,
            options.no_upscale,
        )
        if scale > UPSCALE_WARNING_FACTOR:
            warnings.append(
                f'"{item.path.name}" is being enlarged to {scale:.1f}x. '
                "It may look pixelated; use --no-upscale or a smaller target size."
            )
        enhanced = enhance_image(item.image, options.enhance)
        resized = resize_with_quality(enhanced, (new_width, new_height))
        prepared.append(
            PreparedImage(path=item.path, image=resized, original_size=item.original_size, scale=scale)
        )

    return prepared, warnings


def output_size(images: list[PreparedImage], options: StitchOptions) -> tuple[int, int]:
    gap_total = max(len(images) - 1, 0) * options.spacing
    if options.direction == "horizontal":
        width = sum(item.image.width for item in images) + gap_total
        height = max(item.image.height for item in images)
    else:
        width = max(item.image.width for item in images)
        height = sum(item.image.height for item in images) + gap_total
    return width, height


def validate_output_size(width: int, height: int) -> None:
    pixels = width * height
    if width <= 0 or height <= 0:
        fail("Output image would be empty.")
    if width > MAX_OUTPUT_SIDE or height > MAX_OUTPUT_SIDE:
        fail(f"Output would be {width} x {height}px, which is too large.")
    if pixels > MAX_OUTPUT_PIXELS:
        fail(f"Output would contain {pixels:,} pixels, which is too large.")


def stitch_prepared_images(images: list[PreparedImage], options: StitchOptions) -> Any:
    width, height = output_size(images, options)
    validate_output_size(width, height)

    Image, _ = require_pillow()
    output = Image.new("RGBA", (width, height), parse_background(options.background))
    cursor = 0

    for item in images:
        image = item.image
        if options.direction == "horizontal":
            x = cursor
            y = cross_axis_offset(height, image.height, options.alignment)
            cursor += image.width + options.spacing
        else:
            x = cross_axis_offset(width, image.width, options.alignment)
            y = cursor
            cursor += image.height + options.spacing
        output.paste(image, (x, y), image)

    return output


def cross_axis_offset(canvas_length: int, image_length: int, alignment: str) -> int:
    if alignment == "start":
        return 0
    if alignment == "end":
        return canvas_length - image_length
    return (canvas_length - image_length) // 2


def stitch_images(paths: list[Path], options: StitchOptions) -> tuple[Any, list[str], tuple[int, int]]:
    sources = load_source_images(paths)
    prepared, warnings = prepare_images(sources, options)
    size = output_size(prepared, options)
    validate_output_size(*size)
    return stitch_prepared_images(prepared, options), warnings, size


def flattened_for_export(image: Any, background: str) -> Any:
    bg = parse_background(background)
    if bg[3] == 0:
        bg = (255, 255, 255, 255)
    Image, _ = require_pillow()
    flattened = Image.new("RGBA", image.size, bg)
    flattened.paste(image, (0, 0), image)
    return flattened.convert("RGB")


def save_image(image: Any, output_path: str | None, options: StitchOptions) -> Path:
    fmt = options.output_format.lower()
    extension = {"png": ".png", "jpg": ".jpg", "tiff": ".tiff"}[fmt]
    path = Path(output_path or f"stitched_output{extension}").expanduser()
    if path.suffix.lower() not in {extension, ".jpeg" if fmt == "jpg" else extension}:
        path = path.with_suffix(extension)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "jpg":
            flattened = flattened_for_export(image, options.background)
            flattened.save(path, format="JPEG", quality=options.quality, optimize=True)
        elif fmt == "tiff":
            image.save(path, format="TIFF")
        else:
            image.save(path, format="PNG", optimize=True)
    except OSError as exc:
        fail(f'Could not save "{path}": {exc}')

    return path.resolve()


def print_preview_info(paths: list[Path], options: StitchOptions) -> list[str]:
    sources = load_source_images(paths)
    prepared, warnings = prepare_images(sources, options)
    width, height = output_size(prepared, options)
    validate_output_size(width, height)
    print(f"Images: {len(paths)}")
    print(f"Estimated output: {width} x {height}px")
    print(f"Format: {options.output_format.upper()}")
    print(f"Background: {options.background}")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return warnings


def main() -> None:
    try:
        args = parse_args()
        paths = validate_paths(args.images)
        options = StitchOptions(
            direction=args.direction,
            spacing=args.spacing,
            background=args.background,
            output_format=args.format,
            quality=args.quality,
            smart_match=args.smart_match,
            same_height=args.same_height,
            same_width=args.same_width,
            max_width=args.max_width,
            max_height=args.max_height,
            no_upscale=args.no_upscale,
            enhance=args.enhance,
            alignment=args.align,
        )

        if args.preview_info:
            print_preview_info(paths, options)

        stitched, warnings, size = stitch_images(paths, options)
        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        saved_path = save_image(stitched, args.output, options)
        print(f"Saved {size[0]} x {size[1]} image to: {saved_path}")
    except StitchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
