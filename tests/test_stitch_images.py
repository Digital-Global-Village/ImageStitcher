import tempfile
import unittest
from pathlib import Path

from PIL import Image

from stitch_images import StitchOptions, load_source_images, prepare_images, save_image, stitch_prepared_images


class StitchImagesTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
