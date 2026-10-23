"""Handcrafted GPIF metadata cases; no real scores or private files."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "score-percussion" /
          "scripts" / "gpif_percussion.py")
SPEC = importlib.util.spec_from_file_location("gpif_percussion", SCRIPT)
gpif = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gpif)


def note(note_id, articulation=None, properties="", tie=""):
    art = "" if articulation is None else f"<InstrumentArticulation>{articulation}</InstrumentArticulation>"
    return f'<Note id="{note_id}"><Properties>{properties}</Properties>{art}{tie}</Note>'


def fixture(notes=None, beats=None, outputs=(36, 38), pitched=False):
    notes = notes if notes is not None else [note("n0", 1)]
    beats = beats if beats is not None else ["n0"]
    arts = "".join(f"<Articulation><OutputMidiNumber>{m}</OutputMidiNumber></Articulation>"
                   for m in outputs)
    track = (f'<Track id="d"><InstrumentSet><Type>drumKit</Type><Elements><Element>'
             f'<Articulations>{arts}</Articulations></Element></Elements></InstrumentSet>'
             '<MidiConnection><PrimaryChannel>9</PrimaryChannel><SecondaryChannel>9</SecondaryChannel>'
             '</MidiConnection><Staves><Staff><Properties/></Staff></Staves></Track>')
    order, master_slots = "d", "bd"
    extra_bar = extra_voice = extra_beat = extra_note = ""
    if pitched:
        track += ('<Track id="p"><InstrumentSet><Type>electricGuitar</Type></InstrumentSet>'
                  '<Staves><Staff><Properties/></Staff></Staves></Track>')
        order, master_slots = "d p", "bd bp"
        extra_bar = '<Bar id="bp"><Voices>vp</Voices></Bar>'
        extra_voice = '<Voice id="vp"><Beats>beatp</Beats></Voice>'
        extra_beat = '<Beat id="beatp"><Notes>np</Notes></Beat>'
        extra_note = note("np", 99, '<Property name="Midi"><Number>64</Number></Property>')
    beat_nodes = "".join(f'<Beat id="b{i}"><Notes>{ids}</Notes></Beat>'
                         for i, ids in enumerate(beats))
    beat_ids = " ".join(f"b{i}" for i in range(len(beats)))
    return (f'<GPIF><MasterTrack><Tracks>{order}</Tracks></MasterTrack><Tracks>{track}</Tracks>'
            f'<MasterBars><MasterBar><Bars>{master_slots}</Bars></MasterBar></MasterBars>'
            f'<Bars><Bar id="bd"><Voices>vd</Voices></Bar>{extra_bar}</Bars>'
            f'<Voices><Voice id="vd"><Beats>{beat_ids}</Beats></Voice>{extra_voice}</Voices>'
            f'<Beats>{beat_nodes}{extra_beat}</Beats><Notes>{"".join(notes)}{extra_note}</Notes></GPIF>')


class GPIFPercussionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.source = self.base / "source.gp"
        self.output = self.base / "patched.gp"

    def write(self, xml):
        with zipfile.ZipFile(self.source, "w") as archive:
            archive.writestr(gpif.GPIF_MEMBER, xml)
            archive.writestr("Content/opaque.bin", b"\x00\x01unchanged")

    def output_xml(self):
        with zipfile.ZipFile(self.output) as archive:
            return ET.fromstring(archive.read(gpif.GPIF_MEMBER))

    def assert_blocked(self, xml):
        self.write(xml)
        report = gpif.audit_file(self.source)
        self.assertFalse(report["supported"], report)
        with self.assertRaises(gpif.UnsupportedScore):
            gpif.patch_file(self.source, self.output)
        self.assertFalse(self.output.exists())
        return report

    def test_custom_index_maps_to_output_midi_and_source_is_immutable(self):
        self.write(fixture())  # index 1 is MIDI 38, not MIDI 1.
        before = self.source.read_bytes()
        audit = gpif.audit_file(self.source)
        self.assertTrue(audit["supported"])
        self.assertEqual(audit["tracks"][0]["midi_pitches"], {38: 1})
        self.assertFalse(self.output.exists())
        result = gpif.patch_file(self.source, self.output)
        self.assertEqual(result["written_midi_properties"], 1)
        self.assertEqual(self.output_xml().findtext(
            './/Note/Properties/Property[@name="Midi"]/Number'), "38")
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(gpif.audit_file(self.output)["planned_midi_properties"], 0)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("Content/opaque.bin"), b"\x00\x01unchanged")

    def test_articulation_index_out_of_range_blocks_output(self):
        self.assert_blocked(fixture([note("n0", 38)]))

    def test_output_midi_out_of_range_blocks_output(self):
        self.assert_blocked(fixture(outputs=(36, 128)))

    def test_pitched_note_and_articulation_are_preserved(self):
        xml = fixture(pitched=True)
        self.write(xml)
        before = ET.fromstring(xml).find('.//Note[@id="np"]')
        gpif.patch_file(self.source, self.output)
        after = self.output_xml().find('.//Note[@id="np"]')
        self.assertEqual(ET.tostring(before), ET.tostring(after))
        self.assertEqual(after.findtext("InstrumentArticulation"), "99")

    def test_explicit_midi_already_compatible_is_preserved(self):
        props = '<Property name="Midi"><Number>38</Number></Property>'
        self.write(fixture([note("n0", 1, props)]))
        report = gpif.patch_file(self.source, self.output)
        self.assertEqual(report["written_midi_properties"], 0)
        self.assertEqual(len(self.output_xml().findall('.//Property[@name="Midi"]')), 1)

    def test_explicit_midi_can_be_audited_without_articulation(self):
        props = '<Property name="Midi"><Number>42</Number></Property>'
        self.write(fixture([note("n0", properties=props)]))
        report = gpif.audit_file(self.source)
        self.assertTrue(report["supported"])
        self.assertEqual(report["tracks"][0]["midi_pitches"], {42: 1})

    def test_legacy_tone_octave_uses_documented_octave_convention(self):
        props = ('<Property name="Tone"><Step>2</Step></Property>'
                 '<Property name="Octave"><Number>4</Number></Property>')
        self.write(fixture([note("n0", 1, props)]))  # 2 + 12*(4-1) = 38.
        gpif.patch_file(self.source, self.output)
        self.assertEqual(self.output_xml().findtext(
            './/Property[@name="Midi"]/Number'), "38")

    def test_conflicting_midi_metadata_blocks_output(self):
        props = '<Property name="Midi"><Number>1</Number></Property>'
        self.assert_blocked(fixture([note("n0", 1, props)]))

    def test_missing_tie_destination_pitch_is_not_inferred(self):
        notes = [note("n0", 1, tie='<Tie origin="true"/>'),
                 note("n1", tie='<Tie destination="true"/>')]
        self.assert_blocked(fixture(notes, ["n0", "n1"]))

    def test_per_drum_tie_identity_and_attack_count(self):
        notes = [note("n0", 1, tie='<Tie origin="true"/>'),
                 note("n1", 1, tie='<Tie destination="true"/>'),
                 note("n2", 0)]
        self.write(fixture(notes, ["n0", "n1 n2"]))
        report = gpif.patch_file(self.source, self.output)
        self.assertEqual(report["summary"]["attacks"], 2)
        self.assertEqual(report["summary"]["tie_destinations"], 1)
        self.assertEqual(self.output_xml().find('.//Note[@id="n1"]/Tie').get("destination"), "true")

    def test_tie_to_different_drum_is_unsupported(self):
        notes = [note("n0", 1, tie='<Tie origin="true"/>'),
                 note("n1", 0, tie='<Tie destination="true"/>')]
        self.assert_blocked(fixture(notes, ["n0", "n1"]))

    def test_partial_tie_changing_chord_slot_is_not_claimed_compatible(self):
        notes = [note("n0", 0), note("n1", 1, tie='<Tie origin="true"/>'),
                 note("n2", 1, tie='<Tie destination="true"/>'), note("n3", 0)]
        report = self.assert_blocked(fixture(notes, ["n0 n1", "n2 n3"]))
        self.assertIn("unsupported-tie-slot", report["issue_counts"])

    def test_duplicate_same_pitch_chord_identity_is_unsupported(self):
        self.assert_blocked(fixture([note("n0", 1), note("n1", 1)], ["n0 n1"]))

    def test_nonzero_drum_tuning_and_string_properties_block_output(self):
        xml = fixture().replace('<Staff><Properties/>', '<Staff><Properties>'
                              '<Property name="Tuning"><Pitches>64 59</Pitches></Property></Properties>')
        self.assert_blocked(xml)
        props = '<Property name="String"><String>0</String></Property>'
        self.assert_blocked(fixture([note("n0", 1, props)]))

    def test_zero_tuning_capacity_must_fit_the_beat(self):
        xml = fixture([note("n0", 0), note("n1", 1)], ["n0 n1"])
        xml = xml.replace('<Staff><Properties/>', '<Staff><Properties>'
                          '<Property name="Tuning"><Pitches>0</Pitches></Property></Properties>')
        self.assert_blocked(xml)

    def test_multiple_staves_and_mixed_rest_note_block_output(self):
        self.assert_blocked(fixture().replace('</Staff></Staves>', '</Staff><Staff/></Staves>'))
        self.assert_blocked(fixture().replace('<Notes>n0</Notes>', '<Notes>n0</Notes><Rest/>'))

    def test_collision_never_overwrites_source_existing_or_hardlink(self):
        self.write(fixture())
        before = self.source.read_bytes()
        with self.assertRaises(gpif.UnsupportedScore):
            gpif.patch_file(self.source, self.source)
        self.output.write_bytes(b"keep")
        with self.assertRaises(gpif.UnsupportedScore):
            gpif.patch_file(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep")
        self.output.unlink()
        self.output.hardlink_to(self.source)
        with self.assertRaises(gpif.UnsupportedScore):
            gpif.patch_file(self.source, self.output)
        self.assertEqual(self.source.read_bytes(), before)

    def test_malformed_xml_unknown_references_and_entities_are_rejected(self):
        for xml in ("<GPIF>", '<!DOCTYPE GPIF [<!ENTITY a "b">]><GPIF/>',
                    fixture().replace('<Notes>n0</Notes>', '<Notes>missing</Notes>')):
            self.write(xml)
            try:
                report = gpif.audit_file(self.source)
            except gpif.UnsupportedScore:
                report = {"supported": False}
            self.assertFalse(report["supported"])
            with self.assertRaises(gpif.UnsupportedScore):
                gpif.patch_file(self.source, self.output)
            self.assertFalse(self.output.exists())

    def test_raw_utf8_gpif_is_supported(self):
        source = self.base / "score.gpif"
        output = self.base / "patched.gpif"
        source.write_text(fixture(), encoding="utf-8")
        gpif.patch_file(source, output)
        self.assertEqual(ET.parse(output).findtext('.//Property[@name="Midi"]/Number'), "38")

    def test_failed_atomic_publication_leaves_no_output_or_temporary(self):
        self.write(fixture())
        before = self.source.read_bytes()
        with patch.object(gpif.os, "link", side_effect=OSError("no hard-link support")):
            with self.assertRaises(OSError):
                gpif.patch_file(self.source, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.base.glob(".gpif-*")), [])
        self.assertEqual(self.source.read_bytes(), before)

    def test_duplicate_zip_members_block_output(self):
        with zipfile.ZipFile(self.source, "w") as archive:
            archive.writestr(gpif.GPIF_MEMBER, fixture())
            with self.assertWarns(UserWarning):
                archive.writestr(gpif.GPIF_MEMBER, fixture())
        with self.assertRaises(gpif.UnsupportedScore):
            gpif.patch_file(self.source, self.output)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
