# Source map and evidence

Use this reference when reading PDF objects or aligning notation with TAB.
The values below are examples of fields, not a required file format.

## Source and layout records

Record the source SHA-256 and a stable source identifier. Keep page numbers
one-based in reports, and explicitly label any zero-based API indexes. A system
record should identify its page region, staff groups, and measure boundaries.
Record how printed measure labels relate to internal measure indexes, including
pickups and repeats. A cover, lyrics sheet, or technique legend is not a music bar.

For each staff group, retain:

- Staff-line positions, local spacing, clef, and instrument/voice association.
- Notation-to-TAB pairing, string count/order, tuning, capo, and transposition.
- Meter, key and accidental state, and any changes inside the system.
- Its vertical region and the adjacent system boundaries.
- A location for any printed percussion key or nonstandard notation legend.

Nearest-staff assignment is only a candidate. A note near the bottom of one system
may belong to the top staff of the next. Check group membership, local staff steps,
stem/beam attachment, and the actual region. Reject or flag impossible positions;
do not assign a default snare, pitch, or rest.

## Coordinates and glyph interpretation

PDF libraries may expose bottom-up PDF coordinates, top-down page coordinates,
transformation matrices, or glyph boxes that include large unused bearings.
Normalize to a documented page convention, retaining the original coordinates.
Derive baselines from the rendering transform when glyph boxes are misleading.
Use local staff spacing rather than fixed pixel/point offsets.

Build an atlas from the exact font resource used in the source. Font names alone
may conceal different subsets or character maps. Store the observed glyph code,
resource/subset identity, rendered appearance, candidate meaning, and supporting
context. Font size can separate grace notes from ordinary notes, but confirm that
distinction visually. Standard Unicode music characters are not guaranteed.

A small atlas should distinguish ordinary and hollow heads, cross heads, rhythm
slashes, full-/partial-measure rests, flags, clefs, accidentals, repeat signs, and
time-signature digits actually present. Add only symbols needed for this source.

## TAB and percussion alignment

Treat a multi-digit fret as one token only when its baseline, spacing, and musical
column agree. Check examples containing both adjacent short notes and two-digit
frets. Distinguish a fret, a string number, a fingering, and a printed measure label.
Dead-note crosses may be vector strokes rather than text. Missing TAB below a head
can indicate a tie, an omitted repeated voicing, or an extraction failure.

Percussion staves can use a bass clef or a custom key. Map visible staff position,
head shape, and open/closed/other marks to an explicitly named instrument first;
then choose the exporter's articulation or MIDI mapping. Do not infer a standard
drum map from the clef or silently map unknown positions to a common instrument.

## Minimum per-note provenance

Retain source hash, page/system/measure, staff and voice, head box/position, stem
direction, beam/flag evidence, tuplet membership, accidental, and TAB token where
available. Keep the relevant rendered crop or a reproducible crop description.
Separate observations, interpretations, and later corrections. An uncertainty
record should say what conflicts and what evidence would resolve it.

## Three useful checks

1. Mixed page: text objects exist, but the score is an embedded scan. Inspect the
   score region before choosing a vector-only method or claiming OMR quality.
2. Polyphonic TAB: a lower-voice rest shares a column with an upper chord. Preserve
   both identities; a rest neither becomes a note nor suppresses the upper chord.
3. Tuplet boundary: a bracket slopes or splits around its label. Follow the bracket
   and stem group instead of using one horizontal label box as a timing boundary.
