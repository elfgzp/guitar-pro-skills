#!/usr/bin/env python3
"""Turn proportional score tiles and a tempo map into a transparent scrolling MOV."""
import argparse
import bisect
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw


def load_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    duration = float(data["durationSeconds"])
    anchors = data["anchors"]
    times = [float(a["seconds"]) for a in anchors]
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("durationSeconds must be finite and positive")
    if len(anchors) < 2 or times[0] != 0 or abs(times[-1] - duration) > 1e-6:
        raise ValueError("anchors must cover time zero through the exact score end")
    if any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("anchor times must be finite and strictly increasing")
    if any(not math.isfinite(float(a["x"])) for a in anchors):
        raise ValueError("anchor x coordinates must be finite")
    if any(a.get("jumpBefore") for a in anchors) or any(float(b["x"]) < float(a["x"]) for a, b in zip(anchors, anchors[1:])):
        raise ValueError("repeat/navigation jumps are not supported by this encoder")
    if not math.isfinite(float(data["height"])) or not 1 <= data["height"] <= 2160 or not data["tiles"]:
        raise ValueError("nonempty tiles and a valid strip height are required")
    tiles = []
    for tile in data["tiles"]:
        if any(not math.isfinite(float(tile.get(k, 0))) for k in ("x", "y")):
            raise ValueError("tile positions must be finite")
        source = (path.parent / tile["file"]).resolve()
        if not source.is_relative_to(path.parent.resolve()):
            raise ValueError("tile paths must remain within the manifest directory")
        with Image.open(source) as image:
            if image.size != (tile["width"], tile["height"]) or image.mode != "RGBA":
                raise ValueError(f"tile dimensions/mode do not match: {tile['file']}")
            low, high = image.getchannel("A").getextrema()
            if low != 0 or high == 0:
                raise ValueError(f"tile must contain notation and a transparent background: {tile['file']}")
        tiles.append({**tile, "path": source})
    return data, anchors, times, tiles


def position_at(anchors, times, seconds):
    index = max(0, min(len(anchors) - 2, bisect.bisect_right(times, seconds) - 1))
    a, b = anchors[index:index + 2]
    fraction = max(0.0, min(1.0, (seconds - times[index]) / (times[index + 1] - times[index])))
    return float(a["x"]) + fraction * (float(b["x"]) - float(a["x"]))


def build_motion(data):
    """Validate proportional geometry and integrate step tempos independently of notes."""
    spacing = data.get("spacing", {})
    if spacing.get("mode") != "proportional":
        raise ValueError("proportional spacing is required; re-render legacy engraved tiles")
    pixels = float(spacing.get("pixelsPerQuarter", 0))
    origin = float(spacing.get("originX", math.nan))
    tpq = float(data.get("ticksPerQuarter", 0))
    duration = float(data.get("durationSeconds", 0))
    if not all(math.isfinite(v) for v in (pixels, origin, tpq, duration)) or min(pixels, tpq, duration) <= 0:
        raise ValueError("finite origin, positive pixelsPerQuarter, ticksPerQuarter and duration are required")
    tempos = {}
    for entry in data.get("tempoMap", []):
        tick, bpm = float(entry["tick"]), float(entry["bpm"])
        if not all(math.isfinite(v) for v in (tick, bpm)) or tick < 0 or bpm <= 0:
            raise ValueError("tempo ticks must be nonnegative and BPM must be positive")
        tempos[tick] = bpm
    if not tempos or min(tempos) != 0:
        raise ValueError("tempoMap must begin at tick zero")
    segments = []
    elapsed = 0.0
    previous_tick = 0.0
    previous_bpm = tempos[0]
    for tick, bpm in sorted(tempos.items()):
        elapsed += (tick - previous_tick) / tpq * 60 / previous_bpm
        segments.append({"seconds": elapsed, "tick": tick, "bpm": bpm})
        previous_tick, previous_bpm = tick, bpm
    ticks = [segment["tick"] for segment in segments]
    anchors = data.get("anchors", [])
    if len(anchors) < 2:
        raise ValueError("at least two proportional anchors are required")
    last_tick, last_time = -1.0, -1.0
    for anchor in anchors:
        tick, seconds, x = (float(anchor[key]) for key in ("tick", "seconds", "x"))
        if not all(math.isfinite(v) for v in (tick, seconds, x)) or tick <= last_tick or seconds <= last_time:
            raise ValueError("anchor ticks and times must be finite and strictly increasing")
        segment = segments[max(0, bisect.bisect_right(ticks, tick) - 1)]
        expected_time = segment["seconds"] + (tick - segment["tick"]) / tpq * 60 / segment["bpm"]
        if abs(x - (origin + tick / tpq * pixels)) > 1e-5:
            raise ValueError("anchor x does not match proportional beat spacing")
        if abs(seconds - expected_time) > 1e-6:
            raise ValueError("anchor time does not match the integrated tempo map")
        last_tick, last_time = tick, seconds
    if float(anchors[0]["tick"]) != 0 or float(anchors[0]["seconds"]) != 0 or abs(last_time - duration) > 1e-6:
        raise ValueError("anchors must cover tick zero through the exact score duration")
    if ticks[-1] > last_tick:
        raise ValueError("tempoMap contains an event beyond the score end")
    return {"tempoSegments": segments, "segmentTimes": [s["seconds"] for s in segments],
            "ticksPerQuarter": tpq, "pixelsPerQuarter": pixels, "originX": origin,
            "durationSeconds": duration}


def position_at_time(motion, seconds):
    seconds = float(seconds)
    if not math.isfinite(seconds):
        raise ValueError("frame time must be finite")
    seconds = max(0.0, min(motion["durationSeconds"], seconds))
    index = max(0, bisect.bisect_right(motion["segmentTimes"], seconds) - 1)
    segment = motion["tempoSegments"][index]
    tick = segment["tick"] + (seconds - segment["seconds"]) * segment["bpm"] / 60 * motion["ticksPerQuarter"]
    return motion["originX"] + tick / motion["ticksPerQuarter"] * motion["pixelsPerQuarter"]


@lru_cache(maxsize=8)
def tile_image(path):
    with Image.open(path) as image:
        return image.convert("RGBA")


def make_frame(tiles, width, height, scroll_x, cursor_x):
    # Assemble before resampling so fractional translations cannot expose tile seams.
    whole = math.floor(scroll_x)
    fraction = scroll_x - whole
    left = whole - 2
    canvas = Image.new("RGBA", (width + 4, height), (0, 0, 0, 0))
    for tile in tiles:
        x, y = round(tile["x"]) - left, round(tile.get("y", 0))
        if x >= canvas.width or x + tile["width"] <= 0:
            continue
        canvas.alpha_composite(tile_image(tile["path"]), (x, y))
    # Pillow resamples RGBA through premultiplied RGBa, preserving alpha edges.
    frame = canvas.transform((width, height), Image.Transform.AFFINE,
                             (1, 0, 2 + fraction, 0, 1, 0), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(frame)
    # Magenta survives a green-screen compatibility conversion.
    draw.line((cursor_x, 36, cursor_x, height - 28), fill=(239, 70, 154, 240), width=3)
    draw.polygon([(cursor_x - 8, 27), (cursor_x + 8, 27), (cursor_x, 37)], fill=(255, 91, 174, 255))
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path, help="New transparent .mov output")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--cursor", type=float, default=0.20, help="Playhead fraction of width")
    parser.add_argument("--seconds", type=float, help="Export a short prototype from time zero")
    args = parser.parse_args()
    data, anchors, times, tiles = load_manifest(args.manifest.resolve())
    if args.output.suffix.lower() != ".mov" or args.output.exists():
        parser.error("output must be a new .mov path")
    if not 1 <= args.fps <= 120 or args.width < 320 or args.width % 2 or not 0 < args.cursor < 1:
        parser.error("invalid frame rate, even width, or cursor position")
    motion = build_motion(data)
    duration = min(data["durationSeconds"], args.seconds) if args.seconds is not None else data["durationSeconds"]
    if not math.isfinite(duration) or duration <= 0:
        parser.error("prototype duration must be finite and positive")
    height = math.ceil(data["height"] / 2) * 2
    frames = math.ceil(duration * args.fps - 1e-9)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("FFmpeg must be installed and available on PATH")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(prefix=".score-video-", suffix=".mov", dir=args.output.parent, delete=False)
    temporary = Path(handle.name)
    handle.close()
    log_path = args.output.with_suffix(".encode.log")
    report_path = args.output.with_suffix(".json")
    if log_path.exists() or report_path.exists():
        temporary.unlink()
        parser.error("output report/log already exists")
    command = [ffmpeg, "-hide_banner", "-loglevel", "warning", "-y", "-f", "rawvideo", "-pixel_format", "rgba",
               "-video_size", f"{args.width}x{height}", "-framerate", str(args.fps), "-i", "pipe:0", "-an",
               "-c:v", "prores_ks", "-threads", "8", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
               "-alpha_bits", "16", "-vendor", "apl0", "-movflags", "+faststart", str(temporary)]
    try:
        with log_path.open("xb") as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
            try:
                for index in range(frames):
                    time = index / args.fps
                    x = position_at_time(motion, time)
                    frame = make_frame(tiles, args.width, height, x - args.width * args.cursor, round(args.width * args.cursor))
                    process.stdin.write(frame.tobytes())
                    if index % (args.fps * 15) == 0:
                        print(f"Encoded input {index}/{frames} frames ({time:.1f}s)", flush=True)
                process.stdin.close()
                if process.wait() != 0:
                    raise RuntimeError(f"FFmpeg failed; inspect {log_path.name}")
            except BaseException:
                process.kill()
                process.wait()
                raise
        # Hard-link install is atomic and refuses replacing an existing destination.
        args.output.hardlink_to(temporary)
        temporary.unlink()
        digest = hashlib.sha256()
        with args.output.open("rb") as exported:
            for chunk in iter(lambda: exported.read(1024 * 1024), b""):
                digest.update(chunk)
        report = {"sourceSha256": data.get("sourceSha256"), "trackIndex": data.get("trackIndex"),
                  "scoreDurationSeconds": data["durationSeconds"], "requestedDurationSeconds": duration,
                  "videoDurationSeconds": frames / args.fps, "frames": frames, "fps": args.fps,
                  "width": args.width, "height": height, "alpha": "ProRes 4444 / 16-bit alpha requested; decode verification required",
                  "audio": "none", "scrollMode": "BPM-integrated proportional spacing, fixed playhead, subpixel translation",
                  "motion": motion, "timeZero": "first score beat; no count-in",
                  "sha256": digest.hexdigest(), "bytes": args.output.stat().st_size}
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
