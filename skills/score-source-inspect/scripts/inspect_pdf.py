#!/usr/bin/env python3
"""Read-only PDF inventory. Object counts are heuristics, not a music/OCR test."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
import tempfile


CLASSIFICATION_NOTE = (
    "Heuristic based on extracted text, vector objects, and embedded images. "
    "It does not establish whether the score is extractable, readable, or suitable "
    "for optical music recognition. Images may be logos; text may be a watermark "
    "or an invisible OCR layer. Render and inspect representative score regions."
)


def classify(counts):
    """Describe observed PDF object types without inferring their score content."""
    vector = any(counts[key] for key in ("characters", "lines", "rectangles", "curves"))
    if counts["images"]:
        return "mixed" if vector else "raster"
    return "vector" if vector else "blank"


def inspect_pdf(source):
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError(
            "pdfplumber is required; install this skill's requirements.txt"
        ) from exc

    source = Path(source)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    pages = []
    totals = Counter()
    with pdfplumber.open(source) as document:
        for number, page in enumerate(document.pages, 1):
            counts = {
                "characters": len(page.chars),
                "images": len(page.images),
                "lines": len(page.lines),
                "rectangles": len(page.rects),
                "curves": len(page.curves),
            }
            font_counts = Counter(str(char.get("fontname", "unknown")) for char in page.chars)
            fonts = []
            for name, count in sorted(font_counts.items()):
                sizes = sorted({
                    round(float(char["size"]), 4) for char in page.chars
                    if str(char.get("fontname", "unknown")) == name and char.get("size") is not None
                })
                fonts.append({"name": name, "character_count": count, "sizes_points": sizes})
            pages.append({
                "page": number,
                "width_points": float(page.width),
                "height_points": float(page.height),
                "rotation_degrees": page.rotation,
                "classification": classify(counts),
                "counts": counts,
                "fonts": fonts,
            })
            totals.update(counts)
            page.close()
    classes = {page["classification"] for page in pages} - {"blank"}
    classification = "blank" if not classes else next(iter(classes)) if len(classes) == 1 else "mixed"
    return {
        "schema_version": 1,
        "source": {"name": source.name, "bytes": source.stat().st_size, "sha256": digest.hexdigest()},
        "dependencies": {"pdfplumber": version("pdfplumber")},
        "page_count": len(pages),
        "classification": classification,
        "classification_note": CLASSIFICATION_NOTE,
        "totals": dict(totals),
        "pages": pages,
    }


def write_report(report, destination, force=False):
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not force:
        # Exclusive creation also prevents a path appearing after preflight.
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=f".{destination.name}.", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source PDF (opened read-only)")
    parser.add_argument("--output", "-o", type=Path, required=True, help="JSON report path")
    parser.add_argument("--force", action="store_true", help="Replace an existing report")
    args = parser.parse_args(argv)
    source = args.source.resolve()
    destination = args.output.resolve()
    if source == destination or (
        source.exists() and destination.exists() and source.samefile(destination)
    ):
        parser.error("output must not overwrite or alias the source PDF")
    if destination.exists() and not args.force:
        parser.error("output already exists; choose another path or use --force")
    try:
        report = inspect_pdf(source)
    except Exception as exc:
        print(f"cannot inspect PDF: {exc}", file=sys.stderr)
        return 2
    try:
        write_report(report, destination, args.force)
    except OSError as exc:
        print(f"cannot write report: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {report['page_count']}-page PDF inventory to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
