import tempfile
import unittest
from pathlib import Path

from PIL import Image

from drag_drop import parse_drop_paths
from stitch_images import (
    StitchError,
    StitchOptions,
    load_source_images,
    prepare_images,
    save_image,
    stitch_prepared_images,
    validate_paths,
)
from version import __version__


class StitchImagesTests(unittest.TestCase):
    def test_displayed_version_matches_release_version(self) -> None:
        version_file = Path(__file__).resolve().parents[1] / "VERSION"
        self.assertEqual(__version__, version_file.read_text(encoding="utf-8").strip())

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)
        self.first = self.folder / "first.png"
        self.second = self.folder / "second.png"
        Image.new("RGBA", (120, 80), (255, 0, 0, 255)).save(self.first)
        Image.new("RGBA", (90, 120), (0, 0, 255, 180)).save(self.second)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_smart_match_horizontal_preserves_proportions(self):
        options = StitchOptions(direction="horizontal", smart_match=True, no_upscale=True)
        prepared, warnings = prepare_images(load_source_images([self.first, self.second]), options)
        output = stitch_prepared_images(prepared, options)

        self.assertEqual([item.image.size for item in prepared], [(120, 80), (60, 80)])
        self.assertEqual(output.size, (180, 80))
        self.assertEqual(warnings, [])

    def test_smart_match_vertical_preserves_proportions(self):
        options = StitchOptions(direction="vertical", smart_match=True, no_upscale=True, spacing=5)
        prepared, _warnings = prepare_images(load_source_images([self.first, self.second]), options)
        output = stitch_prepared_images(prepared, options)

        self.assertEqual([item.image.size for item in prepared], [(90, 60), (90, 120)])
        self.assertEqual(output.size, (90, 185))

    def test_jpg_export_flattens_transparency(self):
        options = StitchOptions(direction="horizontal", background="transparent", output_format="jpg")
        prepared, _warnings = prepare_images(load_source_images([self.second]), options)
        output = stitch_prepared_images(prepared, options)
        saved = save_image(output, str(self.folder / "output.jpg"), options)

        with Image.open(saved) as exported:
            self.assertEqual(exported.mode, "RGB")

    def test_drop_parser_preserves_paths_with_spaces_and_order(self):
        values = ("/tmp/first image.png", "/tmp/second.png")
        paths = parse_drop_paths("ignored by test splitter", lambda _data: values)

        self.assertEqual(paths, [Path(values[0]), Path(values[1])])

    def test_pdf_pages_expand_in_order_between_images(self):
        pdf_path = self.folder / "sample pages.pdf"
        first_page = Image.new("RGB", (72, 72), (255, 0, 0))
        second_page = Image.new("RGB", (72, 72), (0, 0, 255))
        first_page.save(pdf_path, format="PDF", save_all=True, append_images=[second_page])

        paths = validate_paths([str(self.first), str(pdf_path), str(self.second)])
        sources = load_source_images(paths, pdf_dpi=72)

        self.assertEqual(len(sources), 4)
        self.assertEqual([item.display_name for item in sources], [
            None,
            "sample pages.pdf - page 1 of 2",
            "sample pages.pdf - page 2 of 2",
            None,
        ])
        red = sources[1].image.getpixel((20, 20))[:3]
        blue = sources[2].image.getpixel((20, 20))[:3]
        self.assertGreater(red[0], 250)
        self.assertLess(max(red[1:]), 5)
        self.assertGreater(blue[2], 250)
        self.assertLess(max(blue[:2]), 5)

    def test_pdf_dpi_is_limited(self):
        pdf_path = self.folder / "sample.pdf"
        Image.new("RGB", (72, 72), "white").save(pdf_path, format="PDF")

        with self.assertRaisesRegex(StitchError, "PDF DPI"):
            load_source_images([pdf_path], pdf_dpi=600)


if __name__ == "__main__":
    unittest.main()
