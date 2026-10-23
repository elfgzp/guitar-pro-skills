# Report interpretation

## Evidence boundaries

`parse.pass` concerns the file importer. `structural.pass` concerns the parsed model and MIDI generation.
`evidence.visual`, `evidence.audio` and `evidence.source` start as `not_checked` and require separate observations.
A parser may normalize or discard malformed constructs, so a clean model is not proof of clean original bytes.
The CLI never edits or normalizes the input score. SHA-256 binds its report to the exact input bytes.

## Voice duration

The verifier checks notated `displayStart` / `displayDuration` rather than using audible note-off times.
Grace beats are excluded from the metric grid; their attacks remain in the generated MIDI evidence.
A full-measure rest is resolved by alphaTab to the current meter.
Only an alternate voice whose beats are all explicitly empty and contain no notes is skipped.
An ordinary rest-only voice still needs the full measure duration.
Explicit anacrusis bars use the largest active voice duration and require the other active voices to agree.
The verifier does not guess an unmarked pickup from a short measure.
Free-time measures are listed as unchecked for duration, not forced onto a regular metrical grid.
Partial or unconventional voices may need a documented musical review instead of automatic acceptance.

## Ties

A destination must have an origin in the same track with the same sounding pitch identity;
stringed notes also keep their string identity. Percussion identity is its effective output GM number.
Time moves forward in notated measure order, and source/destination links must be reciprocal.
Cross-voice or cross-staff ties can be intentional and are warnings requiring source inspection.
A broken tie graph prevents MIDI generation, which might otherwise dereference missing origins or loop.
These checks concern ties, not slurs, hammer-ons or let-ring instructions.
Slides have a separate endpoint ledger and optional source comparison; see
[slides.md](slides.md). A missing slide requires an independent reference to detect.

## Percussion and MIDI

With a custom kit, `note.percussionArticulation` is an array index, not a GM number and not `articulation.id`.
The report resolves `track.percussionArticulations[index].outputMidiNumber` and flags out-of-range indices.
alphaTab can fall back to a built-in legacy ID for some out-of-range numbers; this does not validate an intended custom kit.
For tracks without a custom kit, the helper probes the pinned engine using one synthetic drum note per distinct ID,
so extended legacy articulations are resolved without copying vendor tables or guessing their GM mapping.

MIDI attacks come from `MidiFileGenerator` and `AlphaSynthMidiFileHandler`, not arithmetic on written notes.
The filter uses `MidiEventType.NoteOn` and positive velocity. In the pinned version its enum value is 128;
this enum is not the standard MIDI wire status byte, and testing for 0x90 would count the wrong event type.
Per-track counts reflect playback expansion, ornaments, slides and repeats. Equality with written attack counts
is expected only for simple cases; investigate differences rather than asserting a universal equality.
Generated events prove routing and attacks, not that an audio device or SoundFont produced an audible result.

## CLI and errors

`node scripts/audit_alphatab.cjs SCORE [--json REPORT.json] [--expected-slides SOURCE-SLIDES.json]`
prints its report as JSON. The optional source reference checks the declared ranges.
Exit 0: parsed structure and MIDI checks passed. Exit 1: structural or MIDI checks failed.
Exit 2: invalid arguments, unreadable input or report output failure.
Output errors remain machine-readable on stdout; the source file is preserved.
Do not use the report to overwrite an input score/reference or an alias to either.

The optional local viewer records file hash, selected tracks, rendering state and manual review notes.
It uses installed local fonts and scripts, and reads selected files using the browser File API.
A locally selected SoundFont enables listening; SoundFonts have their own licensing and are not included.
