# Export format decisions and verification boundaries

Exercised versions: **PyGuitarPro 0.11**, **alphaTab 1.8.4**, and optional
**TuxGuitar 2.1.0**. Record versions for a new run; format behavior can change.
These notes preserve observed boundaries rather than promise universal support.

## Guitar Pro formats

PyGuitarPro writes GP3/4/5 binary formats; a GP5 file is not a native modern
`.gp` ZIP. alphaTab's `Gp7Exporter` provides a native GP export path. Reimport
its bytes and inspect the actual ZIP/GPIF structure, track count, and model.
Do not assume that a successful writer call proves interoperability.

Keep a deliberate intermediate model. A pipeline that imports GP5 and then
exports GP7 can carry importer defaults into the new format. Inspect tied notes,
percussion articulation identity, notation settings, tuning, and channel changes
at that boundary. Native GP playback equivalence may require remapping raw
percussion IDs to local articulation table indexes.

Some importer paths omit a tied percussion destination's pitch while retaining
its tie-origin link. Restore the individual note's articulation only when that
origin link is verified. Do not copy the whole previous beat or infer identity
from chord order. Keep placeholders out of the final articulation table.

Dead-note flags, fret positions, bends, grace notes, slides, hammer-ons, dynamics,
and vocal syllables each need explicit representation. A text label is not the
same as a playable technique. Report approximations instead of silently dropping
or inventing them.

## Slides, ties and grace notes

Preserve technique type, affected note/string, and resolved endpoints through each
format boundary. Incoming/outgoing and pick slides are open-ended; shift/legato
slides have a destination. A dead-note origin has unknown pitch even if an encoder
requires a numeric fret placeholder. Keep that distinction in the source model.

In alphaTab 1.8.4, a shift/legato flag may resolve to the next note on the same
string, including a same-fret tied continuation; an unresolved flag can disappear
during model finishing. Inspect fresh-import endpoints, not only raw flag counts.
When the source slide follows a sustained tied note, the effect may belong on its
last encoded tie segment. A zero-interval target warrants source review. Compare
pitch-bend playback events or audition the passage; NoteOn counts alone cannot
prove a slide sounded.

A GP5 grace transition can import as a separate alphaTab grace beat with a legato
slide. Before-beat grace playback may start before the main note, including a
negative local playback offset at a bar boundary. Use notated display onset and
zero metric grace duration for structural comparisons, while retaining grace
order/type. Do not force playback offsets into the ordinary rhythm grid. Verify
grace playback durations separately; the pinned importer can normalize them.

Headless checks of TuxGuitar 2.1.0 found its imported slide model retains a boolean
slide rather than every GP slide type, and its MIDI path can omit effects attached
to tied destinations. Its dead-note and slide setters are mutually exclusive:
the exercised GP5 path cleared dead-note state, while the native GP path cleared
the slide. The native GP grace importer could also shorten the preceding beat by
reusing its duration object. Compare imported dead flags, techniques and durations
as well as note counts. Keep the semantically correct primary file and report the
tested compatibility loss. Do not add attacks, change source durations, or remove
correct ties/dead-note markings to hide a player's limitation. Recheck these
behaviors after upgrades.

When testing cross-bar slides in a target renderer, inspect the actual line and
both endpoint symbols. Preserved flags can still produce a short unconnected
line if the renderer only searches the current measure. Preserve original slide
types before repairing endpoint lookup: a boolean slide flag cannot distinguish
a connected slide from an open-ended slide-out. Changing serialization order
does not bypass an application's mutually exclusive note-effect model.

## Adding a derived track to an existing band file

Preserve original tracks and opaque instrument/compatibility metadata unless the
requested arrangement changes them. A general import/export cycle can lose fields
its model does not represent. For a direct native GP edit, clone and remap the
new track's complete object graph and update master-bar, part and layout references;
track-count-dependent configuration may live outside GPIF. Reimport both the band
view and the new individual part. Do not assume binary layouts are identical
across format versions.

Declare allowed changes such as adding one part and muting its source guitars for
audition. Compare every original track against the source file, excluding only
those explicit changes. Check the target player's actual mute/solo state: some
TuxGuitar native GP import paths ignore `PlaybackState`. Preserve the music and
provide manual audition instructions when the installed version does so. A saved
mute field is not evidence that the target app honored it.

## Written pitch, tuning, and MusicXML

A standard staff may show written pitch an octave away from sounding guitar or
bass pitch. A TAB staff supplies string/fret information. Decide which is the
authority for the event model and record tuning/capo/transpose explicitly.

For a concert-pitch MusicXML interchange export, write the actual sounding
pitch and avoid adding a second transposition or octave-clef adjustment that
shifts it again. If retaining TAB technical string/fret metadata, include the
matching staff tuning and verify the destination importer honors both. A
notation-only interchange file can omit technical TAB metadata, but its loss
must be stated. Do not generalize one importer's transpose behavior to all editors.

Validate MusicXML against the applicable schema, then independently import it.
Schema validation checks the format; it cannot prove pitch, rhythms, ties, or
correct lyric alignment. Preserve accidental meaning and spelling separately.
A printed `x` notehead may look muted without generating the same dead-note
playback as a GP note flag.

## Rhythm and durations

Use exact onsets and durations with a declared tick resolution. Select actual
supported straight, dotted, and tuplet values. Do not round a tuplet to the nearest
display duration or redistribute rests to make the measure sum look correct.

If a sustained note must be split into representable pieces, maintain per-note
tie identity and continue the same pitch/string as appropriate. Percussion
usually needs a new attack only at its original onset; additional encoding
pieces must not invent hits. A mixed chord can contain both continuations and
new attacks. Never reduce that distinction to one whole-event boolean.

Flattening independent voices changes notation and may change audible behavior.
If the target format requires flattening, document the conversion and compare
all resulting onsets and note durations. Preserve pickups, empty voices, short
meters, repeat starts/ends, and expanded repeats deliberately.

## Lyrics and metadata

Keep Unicode text. A lyric offset is not enough when the track begins with rests
or has ties; attach syllables to checked sounding note/beat positions and reimport
them. Confirm that counts, language characters, and visible line breaks survive.
Do not substitute font glyph codes from a PDF for decoded words.

## MIDI and audio

Compare output note-on and note-off timestamps, program/channel routing, pitches,
velocities, and tie continuation behavior. Count attacks separately from note
objects. Normalize per-track channel reassignment when it preserves meaning.

For drums, ensure output is on MIDI channel 10 with intended GM/custom-kit pitches.
Visible noteheads can coexist with empty or incorrect MIDI output. An actual
target-importer MIDI export is stronger interoperability evidence than a second
pass through the same writer library.

Offline synthesis through a known soundbank can prove the audio path without
microphone capture. A nonzero RMS proves non-silence, not the correct instrument,
musical fidelity, or the desktop application's current device configuration.

## Verification boundaries

Keep these distinct in the delivery report:

1. **Source fidelity:** compared notation, pitches, rhythm, voices, and techniques
   against source passages, with unresolved cases listed.
2. **Model consistency:** checked duration totals, references, pitch ranges, tie
   identities, lyric placement, and track structure.
3. **Format preservation:** fresh output import matches the checked model.
4. **Rendered notation:** complete output renders and selected pages were inspected.
5. **Playback:** MIDI/audio output contains the intended attacks and instruments.
6. **Target application:** the requested editor/player was exercised separately.

Passing one layer does not establish the next. In particular, comparing multiple
formats exported from the same erroneous model cannot establish source fidelity.
