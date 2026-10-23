"""Synthetic PDF tests; no score or copyrighted fixture is distributed."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HAS_PDF_DEPS = all(importlib.util.find_spec(name) for name in ("pypdf", "pdfplumber"))
TOOL = (Path(__file__).resolve().parents[1] / "skills" / "score-source-inspect"
        / "scripts" / "inspect_pdf.py")


@unittest.skipUnless(HAS_PDF_DEPS, "PDF tests require pypdf and pdfplumber")
class InspectPdfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def make_pdf(self, modes):
        from pypdf import PdfWriter
        from pypdf.generic import (
            DecodedStreamObject, DictionaryObject, NameObject, NumberObject,
        )

        writer = PdfWriter()
        for mode in modes:
            page = writer.add_blank_page(width=200, height=300)
            resources = DictionaryObject()
            commands = []
            if mode in ("vector", "mixed"):
                resources[NameObject("/Font")] = DictionaryObject({
                    NameObject("/F1"): DictionaryObject({
                        NameObject("/Type"): NameObject("/Font"),
                        NameObject("/Subtype"): NameObject("/Type1"),
                        NameObject("/BaseFont"): NameObject("/Helvetica"),
                    })
                })
                commands.append(b"BT /F1 12 Tf 20 50 Td (Synthetic marks) Tj ET")
                commands.append(b"10 40 m 180 40 l S")
            if mode in ("raster", "mixed"):
                image = DecodedStreamObject()
                image.set_data(bytes((0, 0, 0)))
                image.update({
                    NameObject("/Type"): NameObject("/XObject"),
                    NameObject("/Subtype"): NameObject("/Image"),
                    NameObject("/Width"): NumberObject(1),
                    NameObject("/Height"): NumberObject(1),
                    NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
                    NameObject("/BitsPerComponent"): NumberObject(8),
                })
                resources[NameObject("/XObject")] = DictionaryObject({
                    NameObject("/Im0"): writer._add_object(image)
                })
                commands.append(b"q 150 0 0 200 10 70 cm /Im0 Do Q")
            page[NameObject("/Resources")] = resources
            stream = DecodedStreamObject()
            stream.set_data(b"\n".join(commands))
            page[NameObject("/Contents")] = writer._add_object(stream)
        source = self.folder / "synthetic.pdf"
        writer.write(source)
        return source

    def run_tool(self, source, output, *extra):
        return subprocess.run(
            [sys.executable, str(TOOL), str(source), "--output", str(output), *extra],
            capture_output=True, text=True, check=False,
        )

    def test_inventory_distinguishes_blank_vector_raster_and_mixed_pages(self):
        source = self.make_pdf(["blank", "vector", "raster", "mixed"])
        original = source.read_bytes()
        output = self.folder / "inventory.json"
        result = self.run_tool(source, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(report["source"]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["page_count"], 4)
        self.assertEqual(report["classification"], "mixed")
        self.assertEqual(
            [page["classification"] for page in report["pages"]],
            ["blank", "vector", "raster", "mixed"],
        )
        page = report["pages"][1]
        self.assertEqual((page["width_points"], page["height_points"]), (200, 300))
        self.assertEqual(page["counts"]["lines"], 1)
        self.assertGreater(page["counts"]["characters"], 0)
        self.assertIn("Helvetica", [font["name"] for font in page["fonts"]])
        self.assertEqual(report["pages"][2]["counts"]["images"], 1)
        self.assertIn("heuristic", report["classification_note"].lower())

    def test_source_cannot_be_overwritten_even_with_force_or_hardlink(self):
        source = self.make_pdf(["vector"])
        original = source.read_bytes()
        for destination in (source, self.folder / "alias.pdf"):
            if destination != source:
                destination.hardlink_to(source)
            result = self.run_tool(source, destination, "--force")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source", result.stderr.lower())
            self.assertEqual(source.read_bytes(), original)

    def test_existing_report_requires_explicit_force(self):
        source = self.make_pdf(["blank"])
        output = self.folder / "inventory.json"
        output.write_text("keep this report")
        result = self.run_tool(source, output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), "keep this report")
        result = self.run_tool(source, output, "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())["classification"], "blank")

    def test_invalid_pdf_returns_actionable_error_without_creating_report(self):
        source = self.folder / "invalid.pdf"
        source.write_bytes(b"This is not a PDF.")
        output = self.folder / "inventory.json"
        result = self.run_tool(source, output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot inspect PDF", result.stderr)
        self.assertFalse(output.exists())

    def test_copied_skill_runs_without_repository_working_directory(self):
        source = self.make_pdf(["mixed"])
        standalone = self.folder / "copied-skill"
        shutil.copytree(TOOL.parents[1], standalone)
        output = self.folder / "standalone.json"
        result = subprocess.run(
            [sys.executable, str(standalone / "scripts" / "inspect_pdf.py"),
             str(source), "--output", str(output)],
            cwd=self.folder, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())["classification"], "mixed")

    def test_creates_nested_report_parent_directory(self):
        source = self.make_pdf(["vector"])
        output = self.folder / "reports" / "nested" / "inventory.json"
        result = self.run_tool(source, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())["classification"], "vector")


if __name__ == "__main__":
    unittest.main()
