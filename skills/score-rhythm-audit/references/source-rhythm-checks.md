# Source rhythm checks and regression cases

Use this reference when a structural check and the printed page disagree.
The helper's JSON format is documented separately in [rhythm-json.md](rhythm-json.md).

## Evidence order

Record direct observations before corrections. A useful correction record identifies
source hash, page/region, measure, track, voice, event/note, written duration,
tuplet ratio, expected interval, observed interval, and the reason for changing it.
Keep original observations when manually overriding a transcription.

Read an entire voice through the passage, including its rests. Verify several
independent anchors such as clear quarter-note bass, vocal entries, or a complete
drum voice. A complete total can contain compensating mistakes; validate the
symbols and membership before treating it as a hard constraint.

If the source remains ambiguous, retain alternatives and local uncertainty. Do
not label a geometrically plausible solver result as visually verified. Expand
inspection around every discovered discrepancy rather than extrapolating a small
sample to the whole piece.

## Frequent boundary failures

| Observation | What to inspect |
| --- | --- |
| A voice sums correctly but sounds shifted | Compensating duration errors, wrong tuplet membership, voice assignments, or repeated-bar origins |
| One part drifts at a barline | Meter map, pickup length, duplicate/missing measure, or a tie interpreted as an attack |
| A busy fill acquires tiny subdivisions | Geometric interpolation or a solver satisfying an incorrect anchor |
| Swing becomes straight eighths | The quarter-plus-eighth triplet group's actual bracket/beam evidence |
| Drum notes vanish at a simultaneous rest | Group logic using the first glyph's rest status for the entire column |
| Extra snare hits appear | Rest glyphs or out-of-range staff positions passed through a default drum map |
| A cymbal is struck again under a tie | Event-wide tie flags, dropped per-note state, or attack generation during export |
| One page has strange notes from another part | System boundary and staff-region assignment, not just nearest-staff distance |

## Geometry is supporting evidence

Engravers alter spacing for lyrics, accidentals, TAB fret widths, chord seconds,
clefs, and page justification. Two x gaps do not imply proportional durations.
Use geometry to associate observations with columns, then use notation for time.

Tuplet brackets can slope, split at a label, use only a beam, or continue across
a break. Compare stem tips with the bracket segment at the event's local x
coordinate. A nearby digit or one horizontal y threshold is insufficient.
Avoid fixed absolute offsets copied from another source or page scale.

Small tie arcs matter. An arbitrary minimum arc width can miss ties between close
notes. Associate arc endpoints with the actual notehead shape and local spacing;
then confirm the same note/instrument and origin. Do not attach the same endpoint
to a neighboring earlier head merely because a broad x tolerance admits both.

## Three regression scenarios

1. **Mixed source:** a scan has a vector title and invisible text layer. Expected:
   inspect rendered score regions and identify the usable extraction method;
   character counts alone do not certify source readability or transcription.
2. **Polyphonic TAB/percussion:** an upper chord shares x with a lower rest, and
   one chord member continues a tie. Expected: keep separate voice/rest identities
   and per-note attacks; preserve TAB-to-rhythm alignment and flag unknown symbols.
3. **Crossing triplet:** a quarter/eighth triplet pair spans a beat near a bar or
   system change and the bracket slopes. Expected: preserve the rational ratio,
   voice continuity, and local bracket membership; do not repair it into equal
   eighths merely to satisfy a solver or the bar total.

## Claim only the validation performed

Structural audit: intervals and declared measure lengths are consistent.
Source audit: named source regions and musical decisions were reviewed.
Export audit: a parser/renderer reproduces the intended event model.
Application audit: the named player/version displays and plays the tested passage.

For a new correction, verify the affected events and neighboring boundaries first.
Repeat affected checks when shared extraction logic changes, but avoid repeating
unrelated tests without a new failure or changed assumption.
