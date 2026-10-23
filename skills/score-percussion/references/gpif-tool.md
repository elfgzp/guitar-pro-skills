# GPIF percussion metadata tool

`scripts/gpif_percussion.py` is a Python 3.10+ standard-library utility.
It audits a GP ZIP containing `Content/score.gpif`, or raw UTF-8 GPIF XML.
It does not read GP3/4/5 binary files or compressed GP6 GPX containers.

## Commands and results

Run commands relative to the copied `score-percussion` skill directory:

```sh
python scripts/gpif_percussion.py input.gp
python scripts/gpif_percussion.py input.gp --patch --output new-compatible.gp
```

Audit emits JSON and never creates a score. Exit 0 means the supported metadata
layout was resolved; exit 2 means malformed/unsupported input or a write error.
`planned_midi_properties` counts missing legacy MIDI properties, not drum attacks.
`attacks` excludes explicitly tied destinations; `note_occurrences` includes them.
An unsupported score's partial counts must not be used as completeness evidence.
`issue_counts` includes all detected issues; `issues` contains at most 20 examples.

The opt-in patch adds only `Properties/Property name="Midi"/Number` where absent.
It resolves each drum note through its own track's kit index and output MIDI
mapping, or through an existing explicit legacy pitch. It preserves existing
MIDI properties, articulation indexes, tie flags, and all non-GPIF ZIP member
contents. XML serialization may change whitespace, namespace-free syntax, CDATA
representation, or declaration formatting; byte-for-byte XML equality is not
promised. Musical semantics outside the added properties are not intentionally
changed. Always reimport and compare with alphaTab afterwards.

## Supported subset

- Unnamespaced UTF-8 GPIF, one staff per track, explicit complete track order.
- Resolvable master-bar, bar, voice, beat, and unique note references.
- Drum tracks explicitly identified by `InstrumentSet/Type` equal to `drumKit`.
- Explicit primary and secondary MIDI channel `9` (human channel 10).
- No nonzero drum string tuning, no string/fret percussion note properties.
- Track-local flattened articulation indexes with valid output MIDI 0..127.
- Existing `Midi/Number`, and legacy `Tone/Step` plus `Octave/Number`, if consistent.
- Adjacent voice-beat ties whose origin/destination pitches and chord slots match.
- No tied multi-voice percussion; no duplicate output-pitch identity on a beat.
- At most six notes per beat, within any explicitly declared zero-tuning capacity.

Unknown/missing references, reused note definitions, multiple staves, conflicting
pitch encodings, Element/Variation, missing tie pitches, duplicate same-pitch
chords, dangling ties, and mixed explicit rest/note flags block the whole patch.
The tool never fills missing tie identities or manufactures drum sounds.
`supported: true` means this restricted metadata graph resolved. It does not
establish stable tie identity inside alphaTab or a target player: explicit
Midi is a pitch fallback, not a per-note tie-link encoding. Fresh import and
MIDI note-on/off comparisons are still required, particularly for partial ties.

These restrictions are conservative. Some rejected scores are musically valid
and need a format-aware editor or an extension with independent regression cases.
Do not remove checks merely to obtain an output file.

## File handling

The source is never written. The output must have a new path; existing files,
source aliases, hard links, and symlinks are refused. A completed temporary file
is published using an atomic, exclusive hard link. Filesystems without hard-link
support fail closed. A failure during audit or temporary writing leaves no new
output. The containing directory must already exist.

The tool does not extract ZIP contents. It rejects duplicate member names, DTD
or entity declarations, namespaced layouts, XML larger than 32 MiB, and expanded
archives larger than 256 MiB. It does not treat document contents as instructions.

## What success does not mean

It does not prove source-score fidelity, correct kit selection, tempo, rhythm,
measure totals, repeat expansion, complete note recovery, accurate drum soundbank
rendering, or successful desktop playback. A fresh alphaTab import/render/MIDI
comparison remains the primary validation; an actual TuxGuitar import and MIDI
export is optional target-specific evidence.
