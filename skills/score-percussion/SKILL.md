---
name: score-percussion
description: Use when transcribing or checking drum parts, resolving GP percussion articulations, or diagnosing an empty or silent percussion track.
---

# Percussion transcription and playback

Keep the source immutable. Work on a separate score copy and retain the original.
This skill works independently; a particular model, editor, or assistant is not required.

## Establish the drum vocabulary

1. Read the score's own percussion legend before assigning any MIDI pitches.
2. Record staff positions, noteheads, open/closed markers, cymbals, and tom names.
3. Resolve that vocabulary to the intended kit or General MIDI output numbers.
4. Preserve simultaneous hits and independent voices; a rest in one voice does not
   cancel notes in another voice or imply an empty combined beat.
5. Record ambiguous positions for review. Do not silently replace them with snare.

## Preserve rhythm and identity

- Separate note attacks, tied continuations, rests, and grace notes in the model.
- Keep each drum's identity through ties, including partially tied chords.
- Check percussion onsets against the source independently of pitched instruments.
- Resolve mixed note/rest flags explicitly before writing any format.
- Check fills, pickups, meter changes, repeats, and endings against source notation.
- Matching measure totals proves duration consistency; it does not prove rhythm.

## Export and verify with alphaTab

Use alphaTab as the primary import/render/playback validation path when available.
Record its exact version; normalize to audible output MIDI numbers for comparison.

1. Reimport the exported score and compare every drum onset and output pitch.
2. Count new attacks separately from tied destinations and notation note objects.
3. Compare per-instrument attack counts and tie identity, not only total notes.
4. Render the complete score and inspect a groove, a fill, a meter change, and the end.
5. Verify percussion MIDI routing, then synthesize or play a short drum-only sample.
6. Treat audible output as separate evidence from notation and from source fidelity.

GP7 `InstrumentArticulation` is a track-local articulation index. Resolve it through
the kit's flattened articulation table to `OutputMidiNumber`. It is not generally
a General MIDI number. Read [format notes](references/percussion-formats.md).

## Optional TuxGuitar compatibility

Use the target application's actual importer and MIDI exporter for this extra check.
It supplements alphaTab validation and is not required when TuxGuitar is not targeted.

- GP5 percussion strings must have zero open-string pitches in the verified path.
- GP7 unpitched notes may need explicit `Midi/Number` for older importers.
- Do not add MIDI values by copying articulation indexes or visual staff positions.
- Verify the resulting MIDI output pitches and attacks, then the soundbank output.

## Narrow GPIF metadata tool

The bundled tool uses Python 3.10+ and the standard library. From this skill directory:

```sh
python scripts/gpif_percussion.py input.gp
python scripts/gpif_percussion.py input.gp --patch --output compatible.gp
```

Audit is the default and writes no score. An explicit patch writes a new copy only.
JSON `supported: false` or exit code 2 requires review; do not bypass it.

The patch only adds missing legacy MIDI properties when existing metadata resolves
unambiguously. It keeps kit indexes, musical data, ties, and other ZIP assets.
It does not transcribe notes, repair tuning, choose drum sounds, reconstruct tie
origins, establish rhythm, or prove audible output.

See [tool limits](references/gpif-tool.md) before using it on another export layout.

## Report evidence precisely

State which source passages were checked and which validation layers passed.
If only a renderer or a metadata tool was used, say so. Keep unresolved musical
questions distinct from import compatibility and audio-device configuration.
