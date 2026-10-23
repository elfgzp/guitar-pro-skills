# A source-linked event model

Use any format that preserves these distinctions. Do not require a particular
editor's internal representation as the only transcription record.

## Identity, time, and provenance

Identify the score source, track, staff, measure, voice, event, and individual
notes. Store onset and duration as exact fractions in a declared unit. In quarter
units, a measure's nominal length is `numerator * 4 / denominator`; retain the
meter even when a pickup or explicit irregular duration changes that length.
Store tempo events on their musical timeline rather than deriving them from page
spacing. Keep printed order separate from expanded playback order.

Each interpreted event should point to observed source evidence: page/region,
head and stem, flags/beams/dots, rest glyph, tuplet bracket/group, TAB token, and
any relevant legend. Include the reading, confidence, alternative, and reason for
a correction. A later manual correction should retain the earlier observation.

## Tracks and individual notes

A track record can contain name, role, tuning, capo, string order, transposition,
and a percussion flag. A note can contain written pitch, sounding pitch, fret,
string, instrument/articulation, tie origin, and techniques. A rest contains no
notes. Unknown pitch or instrument is an uncertainty, not a normal default value.

For percussion, describe the source instrument before converting to General MIDI
or an editor's articulation ID. Verify whether an API numbers MIDI channels from
zero or one. A track name such as "Drums" does not configure percussion playback.
Preserve valid percussion pitches/articulations independently of guitar tuning.

An editor may force percussion into one rhythmically complete voice. Keep the
source voices in the intermediate model, then merge simultaneous attacks only in
an export adapter. Preserve each note's tie/attack state and original provenance.
Do not lose a simultaneous snare because a lower-voice rest appears first in an
extracted group, or create a snare from an unknown rest position.

## Voices, tuplets, and source geometry

Staff proximity and x alignment supply candidates; stems, beams, rests, and
musical context establish voice membership. A voiced rest can align with another
voice's sounding note. Chord seconds can move heads to opposite sides of a stem.
Normalize these visual offsets without merging independent temporal events.

Tuplet membership changes duration by a rational ratio. Retain both the written
value and that ratio. Follow bracket segments, beam groups, and their stem tips;
compare with the bracket height locally at the note's x coordinate when sloped.
Nested groups, label gaps, line breaks, and brackets crossing beats need explicit
membership. Do not infer a tuplet solely from the presence of a nearby digit.

Check cumulative voice time independently of engraving spacing. A complete voice
with visually confirmed values can anchor another reading. Its total alone is
not evidence of correctness: two wrong values can cancel. Keep competing source
observations visible if a solver cannot satisfy them without changing notation.

## Repeats, ties, slurs, and attacks

- A bar-repeat sign references one or more earlier bars; record exactly which.
- A rhythm slash generally specifies an attack with the previous/current voicing;
  it does not by itself mean sustain. Confirm local notation conventions.
- A tie joins the same note/instrument without another attack. A slur indicates
  phrasing/technique and can connect different pitches. Check geometry and context.
- A chord may mix tied notes and new attacks. Event-wide tie flags cannot express
  that case. Track a tie origin for each affected note, including percussion.
- A dead note is an attack with muted/indeterminate pitch. It is not a rest.
- A grace note is not necessarily a full metrical subdivision. Preserve its
  placement and chosen playback policy rather than silently deleting it.

For an expanded repeated measure, keep provenance linking to the printed source
and the repeat instruction. Recheck ties entering the copy, meter changes, and
first/second endings. A malformed or context-free repeat remains unresolved.

## Handoff checks

Separate four claims: source reading reviewed, model internally consistent,
export parser accepted, and a named application's playback verified. Report the
regions, tracks, versions, and limitations for each. AlphaTab offers a useful
parser/render/MIDI check when available; its agreement with a writer using the
same model is not independent proof of the original notation. TuxGuitar can add
an application-specific check if the user uses it, without becoming mandatory.
