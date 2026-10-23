#!/usr/bin/env python3
"""Verify a rendered overlay's duration, frame count, and decoded transparency."""
import argparse
from fractions import Fraction
import io
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image


def audit(video, manifest, limit=None):
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise ValueError("FFmpeg and ffprobe must be available on PATH")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    probe = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]))
    streams = [s for s in probe["streams"] if s["codec_type"] == "video"]
    if len(streams) != 1:
        raise ValueError("expected exactly one video stream")
    stream = streams[0]
    fps = float(Fraction(stream["avg_frame_rate"]))
    duration = float(stream.get("duration", probe["format"]["duration"]))
    expected = min(float(data["durationSeconds"]), limit) if limit is not None else float(data["durationSeconds"])
    frame_count = int(stream["nb_frames"])
    expected_frames = math.ceil(expected * fps - 1e-9)
    samples = []
    for index in sorted(set([0, frame_count // 4, frame_count // 2, frame_count * 3 // 4, frame_count - 1])):
        raw = subprocess.check_output([ffmpeg, "-v", "error", "-ss", f"{index / fps:.9f}", "-i", str(video),
                                       "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-pix_fmt", "rgba", "pipe:1"])
        with Image.open(io.BytesIO(raw)) as image:
            alpha = image.getchannel("A")
            histogram = alpha.histogram()
            extrema = alpha.getextrema()
            samples.append({"frame": index, "seconds": index / fps, "alphaMin": extrema[0], "alphaMax": extrema[1],
                            "transparentPixels": histogram[0], "nontransparentPixels": image.width * image.height - histogram[0]})
    checks = {"frameCount": frame_count == expected_frames, "durationWithinOneFrame": abs(duration - expected) < 1 / fps + 1e-6,
              "silent": not any(s["codec_type"] == "audio" for s in probe["streams"]),
              "decodedTransparency": all(s["alphaMin"] == 0 and s["alphaMax"] > 0 and s["transparentPixels"] > 0 for s in samples)}
    return {"passed": all(checks.values()), "checks": checks, "codec": stream["codec_name"], "profile": stream.get("profile"),
            "pixelFormat": stream["pix_fmt"], "width": stream["width"], "height": stream["height"], "fps": fps,
            "frames": frame_count, "durationSeconds": duration, "expectedSeconds": expected, "samples": samples,
            "visualReview": "not checked by this tool", "musicalFidelity": "not checked by this tool"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--seconds", type=float, help="Expected prototype length")
    parser.add_argument("--json", type=Path, help="New report path")
    args = parser.parse_args()
    if args.json and (args.json.exists() or args.json.is_symlink()):
        parser.error("report path must not already exist")
    report = audit(args.video, args.manifest, args.seconds)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with args.json.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
    print(json.dumps(report))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
