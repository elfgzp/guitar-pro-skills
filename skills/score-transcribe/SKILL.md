---
name: score-transcribe
description: Use when converting a printed score, PDF, notation image, or optical music recognition result into an editable multi-track score, including guitar TAB and percussion.
---

# Transcribe a score into an editable model

Build a source-linked musical model before selecting an export format. Use the
user's chosen tools; this skill does not require a specific model, editor, or OMR
engine. An existing source map is useful, but can be established within this task.

## Set the musical scope

1. Inventory all requested parts, including silent opening measures, vocal parts,
   percussion, and tracks that enter later. Record measure numbering and meter
   changes. Confirm which parts are paired standard notation and TAB.
2. Record tuning, capo, string order, clefs, key changes, transpositions, tempo, and
   percussion legend. Keep written pitch, sounding pitch, fret/string position,
   and export articulation as separate concepts.
3. Work in small source regions with retained visual evidence. Use vector data,
   OMR, or manual entry as appropriate; decoded text is a candidate reading.

## Preserve musical identity during extraction

4. Assign every event to a system, staff, track, measure, and voice. A horizontal
   column is not a voice: opposite stems and simultaneous rests can be independent.
   Build sounding members and rests separately before forming chords.
5. Derive note/rest values from heads, stems, flags, beams, dots, and tuplets. Use
   exact rational timing, for example quarter-note units, with an explicit scale.
   Read sloping/split tuplet brackets locally rather than using label coordinates
   or evenly spaced page geometry as the rhythmic authority.
6. Read TAB tokens against the correct strings and align them to rhythmic heads.
   Distinguish two-digit frets, adjacent notes, dead-note strokes, grace notes, and
   missing extraction. Resolve sounding pitch using the recorded tuning and capo.
7. Apply accidentals according to the source's key, octave, measure, and voice
   conventions. Use notation and TAB as independent cross-checks; flag conflicts.
8. Identify percussion instruments using the source legend. Preserve different
   simultaneous hits, open/closed marks, and note-specific articulations. Unknown
   positions remain unresolved instead of becoming an arbitrary MIDI drum.

Read [references/event-model.md](references/event-model.md) when designing the
intermediate model or handling repeats, voices, ties, and uncertainty.
For slide lines, small grace frets, or a reported missing technique, read
[references/slides.md](references/slides.md) and inventory source endpoints before
encoding effects. A nearby label alone does not identify the affected note.

## Resolve continuation and repetition

9. Distinguish a tie from a slur, a rhythm slash from a repeated-bar sign, and a
   dead note from a rest. Repeated strums need new attacks; a tied continuation
   does not. Missing TAB alone does not prove that a note is tied.
10. Store ties per note with an identifiable origin, especially when a cymbal or
    bass drum is tied while other members of its chord attack. Carry voice and
    tie state across barlines and systems. Grace notes need an explicit policy.
11. Keep printed repeats and playback order distinct. If expanding bar-repeat
    symbols, record the source measure and number of copied measures. Validate
    the surrounding meter, first/second endings, and entering ties.

## Validate and hand off

12. Audit every voice's intervals against the actual measure length, including
    pickups or explicit irregular measures. Do not stretch, truncate, quantize,
    or invent notes merely to make totals match. Solvers can locate conflicts or
    propose readings; they do not establish what the printed source says.
13. Compare representative source regions with the model: a dense passage, a
    polyphonic column, a tuplet, a repeat, and a boundary when present. Expand
    checking where any mismatch appears. Keep unresolved cases explicit.

Deliver the model, source provenance, reviewed regions, and an uncertainty/change
log. Optional next skills are `score-rhythm-audit` and a score export workflow.
For GP-family delivery, prefer alphaTab parse/render/MIDI validation when available;
an optional TuxGuitar check tests that application's compatibility separately.
Neither a successful import nor equal measure totals proves source fidelity.
