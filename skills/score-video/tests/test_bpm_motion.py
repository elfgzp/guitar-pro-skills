"""Physical timing and subpixel-motion regressions using synthetic score data."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "encode_overlay.py"
SPEC = importlib.util.spec_from_file_location("score_video_bpm_encoder", SCRIPT)
encoder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(encoder)


def constant_tempo_data(ticks=(0, 7680)):
    return {
        "durationSeconds": 2.5,
        "ticksPerQuarter": 960,
        "tempoMap": [{"tick": 0, "bpm": 192}],
        "spacing": {"mode": "proportional", "pixelsPerQuarter": 120, "originX": 30},
        "anchors": [{"tick": tick, "seconds": tick / 3072,
                     "x": 30 + tick / 960 * 120} for tick in ticks],
    }


class BpmMotionTests(unittest.TestCase):
    def test_fixed_bpm_moves_same_distance_every_frame_despite_note_density(self):
        # At 192 quarter-note beats/minute and 120 pixels/beat, speed must be
        # 384 pixels/second: 6.4 pixels at 60 fps, even across long held notes.
        sparse = encoder.build_motion(constant_tempo_data())
        dense = encoder.build_motion(constant_tempo_data(
            (0, 320, 640, 960, 1600, 1920, 3840, 3960, 4080, 7680)))
        for index in range(150):
            seconds = index / 60
            expected = 30 + 384 * seconds
            with self.subTest(frame=index):
                self.assertAlmostEqual(encoder.position_at_time(sparse, seconds), expected, places=8)
                self.assertAlmostEqual(encoder.position_at_time(dense, seconds), expected, places=8)
                self.assertAlmostEqual(
                    encoder.position_at_time(dense, (index + 1) / 60)
                    - encoder.position_at_time(dense, seconds), 6.4, places=8)

    def test_tempo_change_inside_a_held_beat_changes_speed_at_the_tempo_event(self):
        data = {
            "durationSeconds": 2.5,
            "ticksPerQuarter": 960,
            "tempoMap": [{"tick": 0, "bpm": 120}, {"tick": 960, "bpm": 60}],
            "spacing": {"mode": "proportional", "pixelsPerQuarter": 120, "originX": 30},
            # No notation anchor at the tempo change. Interpolating only the
            # two endpoints would incorrectly produce constant 144 px/s.
            "anchors": [{"tick": 0, "seconds": 0, "x": 30},
                        {"tick": 2880, "seconds": 2.5, "x": 390}],
        }
        motion = encoder.build_motion(data)
        for seconds, expected in ((0, 30), (0.25, 90), (0.5, 150),
                                  (1, 210), (2, 330), (2.5, 390)):
            with self.subTest(seconds=seconds):
                self.assertAlmostEqual(encoder.position_at_time(motion, seconds), expected, places=8)
        self.assertAlmostEqual(
            encoder.position_at_time(motion, 0.5) - encoder.position_at_time(motion, 0.25), 60)
        self.assertAlmostEqual(
            encoder.position_at_time(motion, 0.75) - encoder.position_at_time(motion, 0.5), 30)

    def test_rejects_engraving_geometry_instead_of_silently_desynchronizing(self):
        missing = constant_tempo_data()
        del missing["spacing"]
        legacy = constant_tempo_data()
        legacy["spacing"]["mode"] = "engraved"
        wrong_x = constant_tempo_data((0, 960, 7680))
        wrong_x["anchors"][1]["x"] += 25
        for name, data in (("no spacing", missing), ("legacy engraving", legacy),
                           ("anchor inconsistent with musical time", wrong_x)):
            with self.subTest(case=name), self.assertRaises(ValueError):
                encoder.build_motion(data)

    def test_rejects_invalid_physical_spacing(self):
        for key, values in (("pixelsPerQuarter", (0, -1, float("nan"), float("inf"))),
                            ("originX", (float("nan"), float("inf")))):
            for value in values:
                data = constant_tempo_data()
                data["spacing"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    encoder.build_motion(data)

    def test_building_and_sampling_motion_does_not_mutate_inputs(self):
        data = constant_tempo_data((0, 960, 1920, 7680))
        before = copy.deepcopy(data)
        motion = encoder.build_motion(data)
        motion_before = copy.deepcopy(motion)
        for seconds in (2.5, 0.5, 0, 1.75, 0.5):
            encoder.position_at_time(motion, seconds)
        self.assertEqual(data, before)
        self.assertEqual(motion, motion_before)

    def test_inconsistent_timing_and_out_of_score_tempos_are_rejected(self):
        wrong_time = constant_tempo_data((0, 960, 7680))
        wrong_time["anchors"][1]["seconds"] += 0.01
        wrong_end = constant_tempo_data()
        wrong_end["durationSeconds"] += 0.1
        future_tempo = constant_tempo_data()
        future_tempo["tempoMap"].append({"tick": 8640, "bpm": 60})
        missing_zero_tempo = constant_tempo_data()
        missing_zero_tempo["tempoMap"] = [{"tick": 960, "bpm": 192}]
        for name, data in (("wrong onset time", wrong_time), ("wrong score end", wrong_end),
                           ("tempo beyond score", future_tempo),
                           ("no initial tempo", missing_zero_tempo)):
            with self.subTest(case=name), self.assertRaises(ValueError):
                encoder.build_motion(data)

    def test_fractional_scroll_moves_alpha_centroid_without_integer_stutter(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.png"
            image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            image.putpixel((40, 50), (255, 255, 255, 255))
            image.save(path)
            tile = {"path": path, "x": 0, "y": 0, "width": 100, "height": 100}
            original_bytes = path.read_bytes()
            try:
                for offset in (0, 0.25, 0.5, 0.75, 1):
                    frame = encoder.make_frame([tile], 400, 100, offset, 300)
                    # Exclude the cursor and measure the rendered glyph's alpha
                    # centroid. Rounded integer crop positions fail this check.
                    weights = [(x, frame.getpixel((x, 50))[3]) for x in range(35, 45)]
                    mass = sum(alpha for _, alpha in weights)
                    centroid = sum(x * alpha for x, alpha in weights) / mass
                    with self.subTest(offset=offset):
                        self.assertAlmostEqual(centroid, 40 - offset, delta=0.02)
                        self.assertAlmostEqual(mass, 255, delta=2)
                        self.assertEqual(frame.getpixel((0, 0))[3], 0)
                self.assertEqual(path.read_bytes(), original_bytes)
                self.assertEqual(encoder.tile_image(path).tobytes(), image.tobytes())
            finally:
                encoder.tile_image.cache_clear()

    def test_fractional_motion_is_identical_across_tiles_and_negative_offsets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            whole = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
            # A translucent glyph crosses x=100, the synthetic tile boundary.
            # Splitting the raster must have no visible effect after resampling.
            for y in range(40, 61):
                for x in range(90, 111):
                    whole.putpixel((x, y), (235, 180, 91, 64 + (x + y) % 192))
            source = root / "whole.png"
            whole.save(source)
            pieces = []
            for start in (0, 100):
                path = root / f"part-{start}.png"
                whole.crop((start, 0, start + 100, 100)).save(path)
                pieces.append({"path": path, "x": start, "y": 0, "width": 100, "height": 100})
            one = [{"path": source, "x": 0, "y": 0, "width": 200, "height": 100}]
            try:
                for offset in (-99.75, -0.25, 0.25, 98.75, 100.25):
                    with self.subTest(offset=offset):
                        split = encoder.make_frame(pieces, 400, 100, offset, 300)
                        joined = encoder.make_frame(one, 400, 100, offset, 300)
                        self.assertEqual(split.tobytes(), joined.tobytes())
            finally:
                encoder.tile_image.cache_clear()


if __name__ == "__main__":
    unittest.main()
