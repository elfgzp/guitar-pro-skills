---
name: score-arrange
description: Combine existing guitar parts into a playable arrangement using an explicit lead-priority policy, and optionally add the derived part to a band score while preserving the source tracks.
---

# Arrange existing guitar parts

Start from reviewed source tracks. This skill selects and adapts existing music;
it does not establish that the source transcription matches its PDF. Keep the
source score immutable and write a separately named arrangement.

## Establish the musical rule

Identify the lead and rhythm tracks by role, not just track number. Record tuning,
capo, meter, tempo, repeat structure, intended instrument and difficulty. Clarify
whether the result is a standalone part or an additional track in the band score.
Use the user's stated selection unit; these two policies produce different music:

- **Whole-bar lead priority:** if the lead contains any note in a bar, select that
  entire lead bar, including its rests. Use the entire rhythm bar only when the
  lead bar is empty of notes. Never fill rests inside a selected lead bar.
- **Gap filling:** retain lead phrases and fill suitable gaps with rhythm material.
  This permits within-bar mixing, but requires an explicit request or agreed
  arrangement policy and a review of timing, sustain, fingering and playability.

Neither policy is a universal default. A request for continuous playing does not
by itself settle whether phrase rests should remain. If the policy is unresolved,
prepare a short representative comparison before committing the full arrangement.
Do not call score selection an audio bounce; bouncing normally renders or mixes
recorded audio. Use a descriptive name such as “Lead-Rhythm Guitar”.

## Select whole bars without erasing musical content

Inspect every staff and voice belonging to the lead part. A note counts as content
when it is pitched, a dead note, a tied continuation or a grace note; do not use
MIDI NoteOn counts or “audible pitch” as the emptiness predicate. A held note can
be present without a new attack. Explicit rests, empty voices and text alone do
not count as notes.

Resolve bar-repeat symbols and instructions such as unison or “sim.” from the
source before treating an apparently empty bar as silent. Distinguish notation
bars from repeated playback occurrences. Both inputs must share the same timeline;
a missing measure is not an empty measure.

For each bar, record the selected source track and bar, why it was selected and
any declared adaptation. Copy all voices, rests, note lengths, fingering, dynamics,
techniques and attached musical instructions. Do not copy only sounding intervals
or re-quantize a copied bar. If both sources rest, retain the selected full-bar rest.
Preserve meters, tempo changes, repeats and the ending on the shared timeline.

Review every source-switch boundary. A tie or connected slide can cross it; its
destination must resolve to the intended note in the new track. Do not redirect
to an unrelated next note merely because it uses the same string. If exact bar
selection produces a broken connection, report the conflict and use an explicitly
agreed adaptation; do not conceal it with added attacks or rhythm fill.

## Add a track without rewriting the band

Retain the original music and track order unless the user requests replacement.
Give the new track a distinct name, compatible tuning/program and non-conflicting
MIDI routing. Declare the allowed mutation set, such as adding one track and
muting the two source guitars for audition; mute choices are not notation edits.

A general import/export round trip can discard opaque instrument or compatibility
metadata. Choose a writer that preserves it, or make a narrowly scoped native
edit when the format is understood. For modern GP ZIP/GPIF edits, read
[references/native-track-addition.md](references/native-track-addition.md).
Do not modify an installed player to compensate for score errors.

## Verify the complete result

Freshly import the exported file, preferably with an independent reader. Use
alphaTab as the default primary verifier when available; the workflow is not tied
to a particular library or assistant.

1. Check every output bar against the selection rule, not just reported problem
   bars. Record source provenance for the entire requested range.
2. Compare the selected source and derived bar semantically: voices, rests,
   onsets, durations, pitches, string/fret, dead flags, grace identity, dynamics,
   ties and slide types/endpoints. Normalize object IDs and track indices, not
   musical differences. Compare to the source input, not an intermediate that
   might share the arranging bug. List permitted adaptations separately.
3. Compare all original tracks before and after, excluding only declared
   metadata changes. Include percussion articulation mappings and actual MIDI
   pitches, lyrics and track-level settings; equal note counts are insufficient.
4. Check connection endpoints across bars and source switches, full-score
   rendering, representative playing positions and the final sustained notes.
5. Inspect the target player's actual imported tracks, routing and mute/solo
   state. A saved GP playback state does not prove that an importer applied it.
   If it ignores mute flags, give explicit audition instructions; distinguish
   this compatibility limit from changed notation.

Deliver the score, rule, track name, provenance and change ledger, plus separate
structure/render/playback/target-compatibility results. Avoid claiming an
arrangement is source-faithful or physically playable from structural checks
alone. The original guitars may need manual muting to audition the combined part
with the rest of the band without doubling it.
