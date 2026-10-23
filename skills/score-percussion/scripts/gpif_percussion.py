#!/usr/bin/env python3
"""Audit GP7 GPIF percussion metadata; optionally add legacy Midi properties.

This deliberately supports one staff per track and immediate, per-pitch ties.
It does not infer pitches, repair tie identities, or validate source notation.
Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
from collections import Counter
import io
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


GPIF_MEMBER = "Content/score.gpif"
MAX_XML_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
PERCUSSION_CHANNEL = 9  # MIDI channel 10, numbered from zero in GPIF.
MIDI_MAX = 127
MAX_ISSUE_EXAMPLES = 20


class UnsupportedScore(ValueError):
    """The requested narrow transformation cannot be proven safe."""


def integer(text: str | None, label: str) -> int:
    if text is None or re.fullmatch(r"-?\d+", text.strip()) is None:
        raise UnsupportedScore(f"{label}: expected an integer")
    return int(text)


def midi_number(text: str | None, label: str) -> int:
    value = integer(text, label)
    if not 0 <= value <= MIDI_MAX:
        raise UnsupportedScore(f"{label}: MIDI number must be 0..127")
    return value


def identifiers(node: ET.Element, child: str) -> list[str]:
    return (node.findtext(child) or "").split()


def table(root: ET.Element, container: str, child: str) -> dict[str, ET.Element]:
    parent = root.find(container)
    if parent is None:
        raise UnsupportedScore(f"missing {container}")
    result = {}
    for element in parent:
        if element.tag != child:
            raise UnsupportedScore(f"unexpected element in {container}")
        key = element.get("id")
        if key is None or key in result:
            raise UnsupportedScore(f"missing or duplicate {child} id")
        result[key] = element
    return result


def reference(items: dict[str, ET.Element], key: str, label: str) -> ET.Element:
    try:
        return items[key]
    except KeyError as exc:
        raise UnsupportedScore(f"{label}: unknown id {key}") from exc


def properties(note: ET.Element) -> dict[str, ET.Element]:
    result = {}
    parents = note.findall("Properties")
    if len(parents) > 1:
        raise UnsupportedScore("multiple Properties containers")
    if not parents:
        return result
    for prop in parents[0]:
        name = prop.get("name")
        if prop.tag != "Property" or name is None:
            raise UnsupportedScore("malformed note property")
        # Duplicate display pitches occur in some exporters. They are not GM pitches.
        if name in result and name not in {"ConcertPitch", "TransposedPitch"}:
            raise UnsupportedScore(f"duplicate {name} property")
        result[name] = prop
    return result


def articulation_map(track: ET.Element) -> list[int]:
    """GP7 InstrumentArticulation indexes the flattened, track-local kit."""
    result = []
    for element in track.findall("InstrumentSet/Elements/Element"):
        for articulation in element.findall("Articulations/Articulation"):
            result.append(midi_number(articulation.findtext("OutputMidiNumber"),
                                      "kit OutputMidiNumber"))
    return result


def note_pitch(note: ET.Element, kit: list[int]) -> tuple[int, bool]:
    props = properties(note)
    if {"String", "Fret"}.intersection(props):
        raise UnsupportedScore("string/fret percussion requires a separate tuning audit")
    if {"Element", "Variation"}.intersection(props):
        raise UnsupportedScore("legacy Element/Variation mapping is outside this GP7 patch")
    candidates = {}
    if "Midi" in props:
        candidates["Midi"] = midi_number(props["Midi"].findtext("Number"), "Midi/Number")
    if {"Tone", "Octave"}.intersection(props):
        if not {"Tone", "Octave"}.issubset(props):
            raise UnsupportedScore("Tone and Octave must both be present")
        tone = integer(props["Tone"].findtext("Step"), "Tone/Step")
        octave = integer(props["Octave"].findtext("Number"), "Octave/Number")
        if not 0 <= tone < 12:
            raise UnsupportedScore("Tone/Step must be 0..11")
        # Legacy GPIF convention used by TuxGuitar 2.1.0: octave 1 starts at MIDI 0.
        candidates["Tone/Octave"] = midi_number(str(tone + 12 * (octave - 1)),
                                                  "Tone/Octave result")
    articulations = note.findall("InstrumentArticulation")
    if len(articulations) > 1:
        raise UnsupportedScore("multiple InstrumentArticulation values")
    if articulations:
        index = integer(articulations[0].text, "InstrumentArticulation")
        if not 0 <= index < len(kit):
            raise UnsupportedScore("InstrumentArticulation index outside track-local kit")
        candidates["InstrumentArticulation"] = kit[index]
    if not candidates:
        raise UnsupportedScore("no explicit MIDI pitch or resolvable articulation index")
    if len(set(candidates.values())) != 1:
        raise UnsupportedScore(f"conflicting percussion pitches: {candidates}")
    return next(iter(candidates.values())), "Midi" in props


def tie_flags(note: ET.Element) -> tuple[bool, bool]:
    ties = note.findall("Tie")
    if len(ties) > 1:
        raise UnsupportedScore("multiple Tie elements")
    if not ties:
        return False, False
    tie = ties[0]
    if set(tie.attrib) - {"origin", "destination"}:
        raise UnsupportedScore("unrecognized tie identity metadata")
    if any(value not in {"true", "false"} for value in tie.attrib.values()):
        raise UnsupportedScore("tie flags must be true or false")
    return tie.get("origin") == "true", tie.get("destination") == "true"


def parse_xml(data: bytes) -> ET.Element:
    if len(data) > MAX_XML_BYTES:
        raise UnsupportedScore("GPIF XML exceeds size limit")
    # Reject declarations before parsing; ElementTree does not fetch external resources.
    # Reject non-UTF-8 encodings too, so declaration checks cannot be bypassed by NULs.
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UnsupportedScore("only UTF-8 GPIF XML is supported") from exc
    if re.search(r"<!\s*(DOCTYPE|ENTITY)\b", text, re.IGNORECASE):
        raise UnsupportedScore("DTD and entity declarations are unsupported")
    if "\x00" in text:
        raise UnsupportedScore("NUL bytes in GPIF XML")
    declaration = re.match(r"\s*<\?xml[^?]*encoding\s*=\s*['\"]([^'\"]+)", text)
    if declaration and declaration.group(1).lower() not in {"utf-8", "utf8"}:
        raise UnsupportedScore("only UTF-8 GPIF XML is supported")
    try:
        root = ET.fromstring(text, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    except ET.ParseError as exc:
        raise UnsupportedScore(f"malformed GPIF XML: {exc}") from exc
    if root.tag != "GPIF":
        raise UnsupportedScore("expected an unnamespaced GPIF root")
    if any(isinstance(e.tag, str) and e.tag.startswith("{") for e in root.iter()):
        raise UnsupportedScore("namespaced GPIF layouts are unsupported")
    return root


def load_source(source: Path) -> tuple[ET.Element, bool, bytes]:
    if not source.is_file():
        raise UnsupportedScore("source is not a regular file")
    if source.stat().st_size > MAX_ARCHIVE_BYTES:
        raise UnsupportedScore("source exceeds size limit")
    snapshot = source.read_bytes()
    if len(snapshot) > MAX_ARCHIVE_BYTES:
        raise UnsupportedScore("source exceeds size limit")
    if zipfile.is_zipfile(io.BytesIO(snapshot)):
        with zipfile.ZipFile(io.BytesIO(snapshot)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise UnsupportedScore("duplicate ZIP member names")
            if GPIF_MEMBER not in names:
                raise UnsupportedScore(f"ZIP has no {GPIF_MEMBER}")
            if sum(item.file_size for item in archive.infolist()) > MAX_ARCHIVE_BYTES:
                raise UnsupportedScore("expanded ZIP exceeds size limit")
            if archive.getinfo(GPIF_MEMBER).file_size > MAX_XML_BYTES:
                raise UnsupportedScore("GPIF XML exceeds size limit")
            try:
                return parse_xml(archive.read(GPIF_MEMBER)), True, snapshot
            except (RuntimeError, zipfile.BadZipFile) as exc:
                raise UnsupportedScore(f"cannot read GPIF ZIP member: {exc}") from exc
    return parse_xml(snapshot), False, snapshot


class Audit:
    def __init__(self, root: ET.Element):
        self.root = root
        self.issues: list[dict[str, Any]] = []
        self.issue_counts: Counter[str] = Counter()
        self.patches: dict[str, int] = {}
        self.used_notes: dict[str, str] = {}
        self.tracks: list[dict[str, Any]] = []

    def issue(self, code: str, detail: str, **location: Any) -> None:
        self.issue_counts[code] += 1
        if len(self.issues) < MAX_ISSUE_EXAMPLES:
            self.issues.append({"code": code, "detail": detail, **location})

    def run(self) -> dict[str, Any]:
        try:
            self.inspect()
        except UnsupportedScore as exc:
            self.issue("unsupported-layout", str(exc))
        counts = Counter()
        for track in self.tracks:
            counts.update({key: track[key] for key in
                           ("note_occurrences", "attacks", "tie_destinations", "rests")})
        return {"schema_version": 1, "supported": not self.issues,
                "summary": dict(counts), "tracks": self.tracks,
                "planned_midi_properties": len(self.patches),
                "issue_counts": dict(self.issue_counts),
                "issues": self.issues,
                "limits": ["metadata audit only; no source-score or audible-playback proof",
                           "ties require matching per-pitch metadata on adjacent voice beats",
                           "no pitch, tuning, timing, articulation, or tie repairs"]}

    def inspect(self) -> None:
        tracks = table(self.root, "Tracks", "Track")
        order = identifiers(self.root, "MasterTrack/Tracks")
        if len(order) != len(set(order)) or set(order) != set(tracks):
            raise UnsupportedScore("MasterTrack/Tracks must list each track exactly once")
        for track in tracks.values():
            if len(track.findall("Staves/Staff")) != 1:
                raise UnsupportedScore("only one staff per track is supported")
        bars = table(self.root, "Bars", "Bar")
        voices = table(self.root, "Voices", "Voice")
        beats = table(self.root, "Beats", "Beat")
        self.notes = table(self.root, "Notes", "Note")
        master_bars = self.root.find("MasterBars")
        if master_bars is None or not list(master_bars):
            raise UnsupportedScore("missing or empty MasterBars")
        timelines: dict[str, list[list[list[ET.Element]]]] = {key: [] for key in order}
        for master in master_bars:
            bar_ids = identifiers(master, "Bars")
            if master.tag != "MasterBar" or len(bar_ids) != len(order):
                raise UnsupportedScore("master-bar staff slots do not match track order")
            for track_id, bar_id in zip(order, bar_ids):
                bar = reference(bars, bar_id, "master-bar Bars")
                voice_ids = identifiers(bar, "Voices")
                if not voice_ids:
                    raise UnsupportedScore("bar has no voice slots")
                timeline = []
                for voice_id in voice_ids:
                    sequence = []
                    if voice_id != "-1":
                        voice = reference(voices, voice_id, "bar Voices")
                        sequence = [reference(beats, bid, "voice Beats")
                                    for bid in identifiers(voice, "Beats")]
                        for beat in sequence:
                            for note_id in identifiers(beat, "Notes"):
                                reference(self.notes, note_id, "beat Notes")
                                if note_id in self.used_notes:
                                    raise UnsupportedScore("shared/reused note definitions are unsupported")
                                self.used_notes[note_id] = track_id
                    timeline.append(sequence)
                timelines[track_id].append(timeline)
        for track_id in order:
            track = tracks[track_id]
            is_percussion = track.findtext("InstrumentSet/Type") == "drumKit"
            channel = track.findtext("MidiConnection/PrimaryChannel")
            if not is_percussion:
                if channel == str(PERCUSSION_CHANNEL):
                    self.issue("ambiguous-track-type", "channel 10 without a drumKit InstrumentSet",
                               track_id=track_id)
                continue
            self.inspect_track(track_id, track, timelines[track_id])

    def inspect_track(self, track_id: str, track: ET.Element,
                      timeline: list[list[list[ET.Element]]]) -> None:
        report = {"track_id": track_id, "note_occurrences": 0, "attacks": 0,
                  "tie_destinations": 0, "rests": 0, "midi_pitches": {}}
        self.tracks.append(report)
        try:
            kit = articulation_map(track)
            for channel in ("PrimaryChannel", "SecondaryChannel"):
                if track.findtext(f"MidiConnection/{channel}") != str(PERCUSSION_CHANNEL):
                    raise UnsupportedScore("explicit primary/secondary MIDI channel 10 required")
            staff = track.find("Staves/Staff")
            tuning = properties(staff).get("Tuning")
            capacity = 6
            if tuning is not None:
                pitches = identifiers(tuning, "Pitches")
                if not pitches or len(pitches) > capacity:
                    raise UnsupportedScore("percussion tuning needs one to six explicit zero pitches")
                if any(integer(p, "drum tuning") != 0 for p in pitches):
                    raise UnsupportedScore("nonzero percussion string tuning requires separate repair")
                capacity = len(pitches)
        except UnsupportedScore as exc:
            self.issue("unsupported-track", str(exc), track_id=track_id)
            return
        midi_counts: Counter[int] = Counter()
        pending: dict[int, set[int]] = {}
        pending_slots: dict[int, dict[int, int]] = {}
        multiple_voices = any(sum(bool(sequence) for sequence in bar) > 1 for bar in timeline)
        for bar_index, bar in enumerate(timeline, 1):
            for voice_index in sorted(set(pending).union(range(len(bar)))):
                sequence = bar[voice_index] if voice_index < len(bar) else []
                active = pending.get(voice_index, set())
                active_slots = pending_slots.get(voice_index, {})
                if not sequence and active:
                    self.issue("unsupported-tie", "tie crosses an empty/missing voice",
                               track_id=track_id, bar=bar_index, voice=voice_index)
                    active = set()
                for beat_index, beat in enumerate(sequence):
                    location = {"track_id": track_id, "bar": bar_index,
                                "voice": voice_index, "beat": beat_index}
                    note_ids = identifiers(beat, "Notes")
                    if not note_ids:
                        report["rests"] += 1
                    if note_ids and (beat.find("Rest") is not None or
                                     beat.find('Properties/Property[@name="Rest"]/Enable') is not None):
                        self.issue("mixed-rest-notes", "beat contains notes and an explicit rest flag", **location)
                    if len(note_ids) > capacity:
                        self.issue("unsupported-voicing", "percussion beat exceeds available zero-tuned strings", **location)
                    destinations, origins = set(), set()
                    destination_slots, origin_slots = {}, {}
                    resolved = []
                    for slot, note_id in enumerate(note_ids):
                        report["note_occurrences"] += 1
                        note = self.notes[note_id]
                        try:
                            midi, explicit_midi = note_pitch(note, kit)
                            origin, destination = tie_flags(note)
                            resolved.append(midi)
                            midi_counts[midi] += 1
                            report["tie_destinations"] += int(destination)
                            report["attacks"] += int(not destination)
                            if destination:
                                destinations.add(midi)
                                destination_slots[midi] = slot
                            if origin:
                                origins.add(midi)
                                origin_slots[midi] = slot
                            if multiple_voices and (origin or destination):
                                self.issue("unsupported-tie-layout", "tied multi-voice percussion needs a target-specific identity audit",
                                           note_id=note_id, **location)
                            if not explicit_midi:
                                self.patches[note_id] = midi
                        except UnsupportedScore as exc:
                            self.issue("unsupported-note", str(exc), note_id=note_id, **location)
                    if len(resolved) != len(set(resolved)):
                        self.issue("ambiguous-drum-identity", "duplicate MIDI pitches on one beat", **location)
                    if active != destinations:
                        self.issue("unsupported-tie", "adjacent per-pitch tie origins/destinations do not match",
                                   expected=sorted(active), actual=sorted(destinations), **location)
                    if active == destinations and active_slots != destination_slots:
                        self.issue("unsupported-tie-slot", "tied drum changes chord slot; legacy fallback identity is ambiguous",
                                   **location)
                    active = origins
                    active_slots = origin_slots
                pending[voice_index] = active
                pending_slots[voice_index] = active_slots
        if any(pending.values()):
            self.issue("unsupported-tie", "tie origin has no adjacent destination at end of track",
                       track_id=track_id)
        report["midi_pitches"] = dict(sorted(midi_counts.items()))


def audit_file(source: str | Path) -> dict[str, Any]:
    root, _, _ = load_source(Path(source))
    return Audit(root).run()


def output_path(source: Path, output: Path) -> None:
    if source.resolve() == output.resolve():
        raise UnsupportedScore("output must differ from source")
    if output.exists() or output.is_symlink():
        raise UnsupportedScore("output already exists; choose a new path")
    if not output.parent.is_dir():
        raise UnsupportedScore("output parent directory does not exist")


def write_atomic(source: Path, output: Path, xml: bytes, archive_bytes: bytes | None) -> None:
    output_path(source, output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".gpif-", dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            if archive_bytes is None:
                handle.write(xml)
            if archive_bytes is not None:
                with zipfile.ZipFile(io.BytesIO(archive_bytes)) as original, zipfile.ZipFile(handle, "w") as patched:
                    patched.comment = original.comment
                    for member in original.infolist():
                        data = xml if member.filename == GPIF_MEMBER else original.read(member.filename)
                        patched.writestr(member, data)
            handle.flush()
            os.fsync(handle.fileno())
        # Publishing by hard link is atomic and refuses an output created during the write.
        # Filesystems without hard links fail closed instead of exposing a partial output.
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def patch_file(source: str | Path, output: str | Path) -> dict[str, Any]:
    source, output = Path(source), Path(output)
    output_path(source, output)
    root, is_zip, original_bytes = load_source(source)
    audit = Audit(root)
    report = audit.run()
    if not report["supported"]:
        raise UnsupportedScore("audit failed; no output written: " + json.dumps(report["issues"]))
    for note_id, midi in audit.patches.items():
        note = audit.notes[note_id]
        props = note.find("Properties")
        if props is None:
            props = ET.SubElement(note, "Properties")
        prop = ET.SubElement(props, "Property", name="Midi")
        ET.SubElement(prop, "Number").text = str(midi)
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    post_patch = Audit(parse_xml(xml)).run()
    if not post_patch["supported"] or post_patch["planned_midi_properties"]:
        raise UnsupportedScore("post-patch metadata audit failed; no output written")
    if source.read_bytes() != original_bytes:
        raise UnsupportedScore("source changed during audit; no output written")
    write_atomic(source, output, xml, original_bytes if is_zip else None)
    report["written_midi_properties"] = len(audit.patches)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="GP ZIP or raw UTF-8 GPIF XML")
    parser.add_argument("--patch", action="store_true", help="opt in to writing a separate copy")
    parser.add_argument("--output", type=Path, help="new path; existing files are never overwritten")
    args = parser.parse_args()
    if args.patch != bool(args.output):
        parser.error("--patch and --output must be supplied together")
    try:
        report = patch_file(args.source, args.output) if args.patch else audit_file(args.source)
        print(json.dumps(report, indent=2))
        return 0 if report["supported"] else 2
    except (UnsupportedScore, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"supported": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
