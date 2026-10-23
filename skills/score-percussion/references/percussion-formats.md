# Percussion format notes

These observations were exercised with alphaTab **1.8.4**, PyGuitarPro **0.11**,
and TuxGuitar **2.1.0**. Recheck behavior when changing versions. They describe
specific import/export paths, rather than guarantees about every GP file or player.

## Musical identity is separate from layout

A source can use a custom percussion clef and staff positions. A high note does
not inherently mean a cymbal, and an ordinary treble/bass pitch calculation does
not identify a drum. Read the source legend, including notehead shapes and open
hi-hat circles. Keep separate names for source notation, kit articulation, and
audible MIDI output. Some custom sounds share a GM output number and lose nuance
when rendered by a GM soundbank.

Keep separate rhythmic voices until their timing is understood. Flattening them
too early can erase a simultaneous snare, invent a rest, or change a kick onset.
Do not discard an entire combined event because one source voice has a rest.

## GP5: note values and string pitches

In the exercised PyGuitarPro-to-TuxGuitar path, a percussion note's value is its
GM drum number, and percussion string open pitches must be zero. Giving that
track ordinary guitar tuning caused TuxGuitar's MIDI generation to add the open
pitch to each drum value. Notes could appear while playback used unrelated or
unmapped percussion pitches.

An internal parser that reports only `note.value` may miss this failure. Verify
the target's actual generated MIDI pitches on channel 10. Do not fix it by
subtracting guitar pitches from the drum note values: fix the drum track encoding.
Audit channel assignment, tuning, and simultaneous-note capacity together.

## GP7: articulation indexes and custom kits

`InstrumentArticulation` selects an articulation by its **zero-based position**
in the track-local flattened sequence:

```text
InstrumentSet/Elements/Element/Articulations/Articulation
```

The selected articulation's `OutputMidiNumber` is the audible output pitch.
For example, articulation index `1` may select a snare with output MIDI `38`.
`InputMidiNumbers`, articulation names, element types, and staff lines do not
replace the output mapping. Preserve the articulation table order.

When exporting a model that uses built-in articulation IDs, build an explicit
track-local articulation table and remap every note to its new index. Copying
raw GM numbers into `InstrumentArticulation` is only valid when a verified table
actually has the intended articulation at every referenced index.

Normalize alphaTab comparisons through the track's articulation table. A GP5
model may use built-in articulation IDs while a GP7 model uses local indexes;
equal raw numbers do not prove equal sound, and different raw numbers can be
musically equivalent.

## TuxGuitar 2.1.0 GP7 importer

Its `GPXDocumentReader.readNotes()` reads legacy note properties including
`Midi/Number`, `Tone/Step` plus `Octave/Number`, and `Element`/`Variation`.
It does not read `InstrumentArticulation`. Its parser can silently omit an
unpitched note when none of its recognized pitch encodings is available.

Adding a matching explicit `Midi/Number` preserves modern kit metadata while
providing that importer an output pitch. This is a compatibility adaptation,
not a repair for an incorrect kit or transcription. Existing encodings must
agree; string/fret properties take precedence and need a separate audit.

In the inspected TuxGuitar 2.1.0 parser, the legacy Tone/Octave calculation is
`Step + 12 * (Octave - 1)`.
This is a format convention, not a universal scientific-pitch octave rule.
Do not derive this encoding with `midi // 12` without checking the convention.
When a legacy Midi property is also present, that importer uses Midi first;
apparently correct audio can therefore conceal an incorrect fallback octave.
ConcertPitch/TransposedPitch placeholders are not a safe substitute for a
percussion output mapping. Legacy Element/Variation uses an importer-specific
table and is outside the bundled patcher's supported layouts.

Official source inspected: [TuxGuitar 2.1.0 GPX reader](https://github.com/helge17/tuxguitar/blob/2c46e2a1cccdfdfa6e6f2692f241bd60bf418129/common/TuxGuitar-gpx/src/app/tuxguitar/io/gpx/GPXDocumentReader.java),
[GPX parser](https://github.com/helge17/tuxguitar/blob/2c46e2a1cccdfdfa6e6f2692f241bd60bf418129/common/TuxGuitar-gpx/src/app/tuxguitar/io/gpx/GPXDocumentParser.java),
and alphaTab's packaged `GpifParser`, `GpifWriter`, and `PercussionMapper` sources
in [alphaTab 1.8.4](https://www.npmjs.com/package/@coderline/alphatab/v/1.8.4).

## Ties and attack counts

A notation note object is not always a new attack. A tied continuation must
retain the individual drum identity; a tied cymbal beside a fresh kick does
not tie the whole chord. Exporter defaults that turn a tied drum into index
zero can silently select another sound.

Recover identity only from a verified per-note tie link or the source model.
The bundled tool refuses missing, conflicting, orphaned, or nonadjacent tie
identity metadata. It also rejects a tied drum changing its chord slot and tied
multi-voice layouts, because target importers may fall back to slot/string
identity. It never uses slot order to manufacture a missing pitch or copies the
previous chord. These restrictions intentionally reject some valid complex scores.
Even accepted tie metadata still requires fresh alphaTab and target-player
playback verification; adding Midi does not encode a stable per-note tie link.

For playback verification, compare timestamped MIDI note-on and note-off events
by output pitch. Synthesize a short sample through the intended soundbank and
check that PCM output is nonzero. This proves an audio path; it does not prove
that every source rhythm or drum choice is correct.
