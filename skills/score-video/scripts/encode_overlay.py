#!/usr/bin/env python3
"""Turn rendered score tiles and timed x anchors into a transparent scrolling MOV."""
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


@lru_cache(maxsize=8)
def tile_image(path):
    with Image.open(path) as image:
        return image.convert("RGBA")


def make_frame(tiles, width, height, scroll_x, cursor_x):
    frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    left = round(scroll_x)
    for tile in tiles:
        x, y = round(tile["x"]) - left, round(tile.get("y", 0))
        if x >= width or x + tile["width"] <= 0:
            continue
        frame.alpha_composite(tile_image(tile["path"]), (x, y))
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
                    x = position_at(anchors, times, time)
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
                  "audio": "none", "scrollMode": "continuous horizontal, fixed playhead", "timeZero": "first score beat; no count-in",
                  "sha256": digest.hexdigest(), "bytes": args.output.stat().st_size}
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
