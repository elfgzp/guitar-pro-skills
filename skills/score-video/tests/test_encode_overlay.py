"""Synthetic regression checks; require Pillow, never FFmpeg or a real score."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "encode_overlay.py"
SPEC = importlib.util.spec_from_file_location("score_video_encoder", SCRIPT)
encoder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(encoder)


class EncoderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(encoder.tile_image.cache_clear)
        self.root = Path(self.temporary.name)
        self.directory = self.root / "assets"
        self.directory.mkdir()
        self.tile = self.directory / "tile.png"
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        image.putpixel((40, 50), (255, 255, 255, 255))
        image.putpixel((41, 50), (255, 255, 255, 128))
        image.save(self.tile)
        self.manifest = self.directory / "manifest.json"
        self.data = {
            "durationSeconds": 1.0,
            "height": 100,
            "anchors": [
                {"seconds": 0.0, "x": 40.0},
                {"seconds": 0.25, "x": 90.0},
                {"seconds": 1.0, "x": 150.0},
            ],
            "tiles": [{"file": "tile.png", "x": 0, "y": 0, "width": 100, "height": 100}],
        }

    def load(self, data=None):
        self.manifest.write_text(json.dumps(data if data is not None else self.data), encoding="utf-8")
        return encoder.load_manifest(self.manifest)

    def test_exact_anchor_positions_and_interpolation(self):
        _, anchors, times, _ = self.load()
        before = copy.deepcopy(anchors)
        # Unequal beat lengths must not turn into equal-time spacing.
        for seconds, expected in [(0, 40), (0.125, 65), (0.25, 90), (0.625, 120), (1, 150)]:
            with self.subTest(seconds=seconds):
                self.assertAlmostEqual(encoder.position_at(anchors, times, seconds), expected)
        self.assertEqual(anchors, before)

    def test_background_alpha_scroll_and_input_preservation(self):
        _, _, _, tiles = self.load()
        tile_before = self.tile.read_bytes()
        manifest_before = self.manifest.read_bytes()
        cached_before = encoder.tile_image(tiles[0]["path"]).tobytes()
        original = encoder.make_frame(tiles, 400, 100, 0, 300)
        scrolled = encoder.make_frame(tiles, 400, 100, 10, 300)
        self.assertEqual(original.mode, "RGBA")
        self.assertEqual(original.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(original.getpixel((40, 50)), (255, 255, 255, 255))
        self.assertEqual(original.getpixel((41, 50))[3], 128)
        self.assertEqual(scrolled.getpixel((30, 50)), (255, 255, 255, 255))
        self.assertEqual(scrolled.getpixel((40, 50)), (0, 0, 0, 0))
        self.assertGreater(scrolled.getpixel((300, 50))[3], 0)
        self.assertEqual(self.tile.read_bytes(), tile_before)
        self.assertEqual(self.manifest.read_bytes(), manifest_before)
        self.assertEqual(encoder.tile_image(tiles[0]["path"]).tobytes(), cached_before)

    def test_rejects_blank_or_opaque_rendered_tiles(self):
        # A cursor on blank notation would still pass video alpha checks.
        for alpha in (0, 255):
            with self.subTest(alpha=alpha):
                Image.new("RGBA", (100, 100), (255, 255, 255, alpha)).save(self.tile)
                with self.assertRaisesRegex(ValueError, "notation and a transparent background"):
                    self.load()

    def test_rejects_tile_path_escape(self):
        outside = self.root / "outside.png"
        outside.write_bytes(self.tile.read_bytes())
        for filename in ("../outside.png", str(outside)):
            with self.subTest(filename=filename):
                data = copy.deepcopy(self.data)
                data["tiles"][0]["file"] = filename
                with self.assertRaisesRegex(ValueError, "within the manifest directory"):
                    self.load(data)

    def test_rejects_symlink_tile_escape(self):
        outside = self.root / "outside.png"
        outside.write_bytes(self.tile.read_bytes())
        link = self.directory / "link.png"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("This platform does not permit test symlinks")
        self.data["tiles"][0]["file"] = "link.png"
        with self.assertRaisesRegex(ValueError, "within the manifest directory"):
            self.load()

    def test_rejects_nonchronological_or_nonfinite_times(self):
        for middle in (0.0, -0.25, 1.25, float("nan"), float("inf")):
            with self.subTest(middle=middle):
                data = copy.deepcopy(self.data)
                data["anchors"][1]["seconds"] = middle
                with self.assertRaisesRegex(ValueError, "strictly increasing"):
                    self.load(data)

    def test_rejects_missing_start_or_end_anchor(self):
        for first, last in ((0.1, 1.0), (0.0, 0.9), (0.0, 1.1)):
            with self.subTest(first=first, last=last):
                data = copy.deepcopy(self.data)
                data["anchors"][0]["seconds"] = first
                data["anchors"][-1]["seconds"] = last
                with self.assertRaisesRegex(ValueError, "time zero through the exact score end"):
                    self.load(data)

    def test_rejects_backward_scroll_and_repeat_navigation(self):
        for alteration in ({"x": 20}, {"jumpBefore": True}):
            with self.subTest(alteration=alteration):
                data = copy.deepcopy(self.data)
                data["anchors"][1].update(alteration)
                with self.assertRaisesRegex(ValueError, "jumps are not supported"):
                    self.load(data)

    def test_existing_output_is_not_replaced_or_encoded(self):
        self.load()
        output = self.root / "existing.mov"
        output.write_bytes(b"original synthetic media")
        with patch("sys.argv", [str(SCRIPT), str(self.manifest), str(output)]), \
                patch.object(encoder.subprocess, "Popen") as process, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
            encoder.main()
        self.assertEqual(failure.exception.code, 2)
        process.assert_not_called()
        self.assertEqual(output.read_bytes(), b"original synthetic media")


if __name__ == "__main__":
    unittest.main()
