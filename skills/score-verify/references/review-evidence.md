# Visual, audio and source evidence

## Visual review

Load the complete score before checking selected excerpts: ties and layout can depend on adjacent bars.
Review every intended track, meter and system boundary, dense passages and the final measure.
Look for implausible percussion ledger lines, missing kit voices, invisible rests, displaced slashes,
wrong clefs or octave notation, clipped tuplets and outgoing ties with no continuation.
Count render errors and record the inspected ranges. An SVG being produced is only rendering evidence.

## Listening

Use a suitable SoundFont and verify the audio output device. Readiness or MIDI counts do not establish audibility.
Listen to each track alone, especially percussion, then listen to the ensemble.
Check the beginning, all section transitions and ending. Compare attack placement, triplet swing,
partial chord reattacks, sustained notes and the absence of a fresh attack at a tied ending.
If the requested player cannot run, say playback was not checked and provide the available event evidence.
Use TuxGuitar or another application when compatibility is requested; keep its results separate from the primary player.

## Source comparison

For every reviewed issue, record source page, measure, staff, voice, printed form and expected events.
Inspect actual noteheads, stems, flags or beams and tuplet boundaries; horizontal spacing alone is weak evidence.
A sloped tuplet bracket can cross different stem heights, and a bracket can continue across a system boundary.
Distinguish a voice's rest from another voice's note at the same horizontal column.
Expand repeats only after establishing their source range and meter.
A rhythm slash normally repeats the voicing as a fresh attack; only an actual tie changes it into continuation.
Blank TAB can accompany a genuine tie but is not proof of one. Track ties per note in a chord or drum stack.

A useful correction record contains:

```json
{"page":2,"measure":7,"staff":"guitar","voice":1,
 "printed":"triplet quarter plus eighth",
 "expected":[{"onset":0,"duration":640},{"onset":640,"duration":320}],
 "ticks_per_quarter":960,"evidence":"reviewed source crop"}
```

Use this as an example shape, not as a score-specific schema or fixed transcription.
Mark source fidelity for the entire score only after the entire intended range has been compared.
Sampling, structural checks and successful compatibility imports remain narrower evidence.
