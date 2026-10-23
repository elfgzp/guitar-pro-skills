---
name: score-export
description: Use when exporting a checked score model to Guitar Pro, MusicXML, or MIDI while preserving tracks, timing, pitch, ties, lyrics, and percussion identity.
---

# Export a reviewable score

Start from a checked event model. Keep the source and previous deliverables immutable.
This skill can be copied alone; use available libraries and record their versions.
It does not provide a general PDF recognizer or depend on a particular assistant.

## Define the model boundary

Record track identity, instrument, tuning, capo, written versus sounding pitch,
meter, tempo, repeat structure, voices, onset, duration, notes, rests, ties, and
lyrics. Keep uncertainty and source locations alongside the musical data.

- Use exact rational timing or integer ticks with a declared resolution.
- Preserve simultaneous notes and distinguish attacks from tied continuations.
- Reject a sounding event also marked as an unconditional rest.
- Resolve percussion to an explicit kit output mapping, separate from notation.
- Never force durations to fit a bar and call that source transcription verified.

## Choose formats deliberately

1. Use a supported GP binary writer for a compatibility export when appropriate.
2. Use an explicit native GP exporter for `.gp`; renaming `.gp5` is not conversion.
3. Offer MusicXML for interchange and MIDI for playback evidence when useful.
4. Explain which articulation, notation, or instrument details each format loses.

The exercised library path was PyGuitarPro 0.11 for GP5 and alphaTab 1.8.4 for
native GP export and validation. These are optional tools, not required providers.
Consult [format decisions](references/export-formats.md) before reusing that path.

## Export in explicit stages

1. Validate all track measures against their meter and declared voice structure.
2. Encode supported note values, dots, and tuplets without rounding onsets.
3. Split unrepresentable durations only with explicit per-note ties or rests.
4. Preserve tuning/string/fret identity and resolve written/concert pitch once.
5. Assign MIDI programs and channels deliberately; percussion uses channel 10.
6. Preserve lyrics as Unicode and attach syllables to verified note/beat onsets.
7. Export to a new path and retain the exact source/model used for the run.

For GP5 drums, audit zero open-string tuning and actual output pitches.
For GP7 drums, build the track-local articulation table and remap note indexes.
Carry each tied drum's identity through the writer; never tie an entire chord
because only one of its notes continues.

## Primary validation with alphaTab

1. Freshly reimport the output, not a retained pre-export model.
2. Compare tracks, bars, meters, tempo, onsets, durations, and sounding pitches.
3. Normalize percussion through its output articulation mapping.
4. Compare dead notes, per-note tie links, slide types/endpoints, grace identity,
   lyric onsets, and attack counts separately. Include cross-bar transitions.
5. Render the complete score and inspect representative source passages.
6. Generate playback MIDI or a short audio sample for audible-path verification.

Full-score rendering catches issues that a first-page preview misses. Partial
rendering may also need earlier tie origins; diagnose that boundary separately.
Model-to-export equality proves preservation, not accuracy against the source.
Compare a separately source-reviewed slide inventory too: successful imports and
matching note counts cannot expose an effect missing from the original model.

## Optional target application check

When a particular player is requested, open a new copy there and verify its
actual notation and playback. An app can import a file while silently omitting
notes or routing percussion to wrong pitches. Inspect its own generated MIDI
when possible. Keep this evidence separate from the alphaTab checks.

The separate `score-percussion` skill has deeper drum guidance and an optional
metadata patcher. It is not required to use this export skill. A separate
verification workflow can expand source auditing without changing the exporter.

## Deliver with precise limits

Provide only verified output links, a concise format note, and unresolved issues.
State source comparison, format validation, rendering, and playback evidence
individually. Do not describe a draft as exact merely because it opens or each
measure totals correctly. See [verification boundaries](references/export-formats.md#verification-boundaries).
