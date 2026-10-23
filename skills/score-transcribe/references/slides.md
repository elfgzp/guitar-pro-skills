# Read slides from source evidence

A slide is a note-level relationship or an open-ended gesture, not a label on an
entire beat. Count source markings before inspecting export flags: an omitted
mark cannot be discovered by auditing only the slides already present in a file.

## Inventory and resolve

1. Inspect every requested fretted part for slide lines and the source's own
   technique labels/legend. Include small grace frets, dead-note heads, opening
   pickups, final bars, repeats, and both sides of bar/system/page boundaries.
2. Follow each line from its actual start to its end. A label may lie between two
   notes or across a barline; a nearest-text x-window can attach it to the wrong
   event or miss it. Keep line segments, label, source region and endpoints as
   separate evidence. Do not interpret every diagonal line as a slide.
3. Record track, staff, voice, printed measure, onset, string, start/end fret, and
   type. Distinguish a known fretted destination from an unpitched slide-in/out or
   pick slide. Determine shift versus legato from notation and the source legend;
   `s`, `g`, a slur, or line shape alone is not a universal encoding rule.
4. For chords, identify each connected string. Do not copy one beat-wide slide
   flag to all notes. Preserve a dead `X` as unknown pitch; a writer's zero fret
   placeholder is not evidence that an open string was printed or sounded.
5. Small fretted grace notes can slide into a main note at the same notated onset.
   Preserve their grace status and order. Do not remove them as stray TAB digits
   or turn them into extra ordinary beats to make a connection possible.
6. When a note is split by ties, follow the printed slide through the full held
   note. A format may require the effect on the last tied segment before the new
   fret; the first segment's automatic target may be the same-fret continuation.
   Keep the source relationship and its export segment mapping separately.

Build a source-reviewed inventory independently of the generated score, including
the inspected track/bar ranges where no slides were found. After finding one
missed pattern, inspect all matching boundaries, labels, dead-note groups and
grace-note shapes. State the covered ranges and unresolved classifications;
absence of exported flags is not evidence of absence in the source.

## Handoff

Provide per-note origin/destination identities, technique type, grace/dead-note
status, source regions, repeat provenance, and uncertainties. Carry this inventory
through the intermediate model and every export. Compare both missing and extra
effects, as well as endpoints and types; equal technique counts can still hide a
wrong attachment. Never generate the expected inventory from the same export
that it is meant to validate.
