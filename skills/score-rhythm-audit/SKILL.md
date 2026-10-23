---
name: score-rhythm-audit
description: Use when a transcribed or exported score has suspected timing, tuplet, voice, repeat, or cross-bar alignment errors, or needs its rhythm checked against a printed source.
---

# Audit rhythm against the source

Keep source fidelity, internal timing consistency, and application playback as
separate evidence. This skill can audit an existing model without retranscribing
the whole piece or requiring another skill, model, or notation editor.

## Establish what is being compared

1. Record source hash, score/export version, tracks, bar numbering, timing units,
   meter map, pickup/irregular measures, and repeat/playback order.
2. Reproduce the reported passage by musical location and identify its boundaries.
   Include the preceding measure when ties, pickups, or repeats provide context.
3. Obtain event intervals for every relevant voice. Use exact fractions and retain
   source voice identity even when the export merges percussion voices.

## Run a structural check

4. Optionally use the standalone helper provided here:
   `python <skill-dir>/scripts/audit_rhythm.py <rhythm.json> --output <audit.json>`.
   Read [references/rhythm-json.md](references/rhythm-json.md) for its input format.
5. Check onset order, interval gaps/overlaps, positive durations, measure length,
   and missing voices according to the model's declared representation. A pickup
   or cadenza needs an explicit expected duration and explanation.
6. A helper can compare a separately source-reviewed rhythm reference with
   `--reference <reviewed-rhythm.json>`. Preserve reference provenance. Comparing
   two exports derived from the same mistaken model is an internal check only.

## Read the source where timing can be wrong

7. Inspect heads, rests, stems, beams, flags, dots, and tuplet groups on a rendered
   source region. Read each voice cumulatively, including its rests. A rest that
   shares another voice's note column must remain a rest in its own voice.
8. Follow sloping/split brackets and local beam/stem groups. Verify tuplet ratios
   and membership, including groups crossing beats or a system boundary. Recheck
   both sides of a meter change or barline before moving an event.
9. Verify ties per note and distinguish them from slurs and new attacks. A tied
   cymbal can coincide with a new snare; an event-wide tie flag loses that meaning.
10. Verify repeated-bar references and playback expansion. Confirm that copied
    events retain the intended meter, voice, and entering/exiting tie state.

Read [references/source-rhythm-checks.md](references/source-rhythm-checks.md)
for conflict diagnosis, evidence scope, and practical regression cases.

## Resolve conflicts without concealing them

11. Compare source-derived expected intervals with the model and export. Record
    exact bar/track/voice, expected and observed onset/duration, and visual evidence.
    Check independent parts at the same location when one reading is uncertain.
12. Use geometric spacing, quantization, or solvers only to propose candidates or
    expose contradictions. Do not force a bar to fit by stretching rests, changing
    swing to straight eighths, or inventing tiny subdivisions without source proof.
13. Correct the earliest faulty layer, then re-export and recheck the affected
    passage, its repeat copies, and neighboring tie/meter boundaries.

Prefer alphaTab parse/render/MIDI checks for GP-family outputs when available.
If TuxGuitar is the user's player, optionally verify the same passage there and
report that compatibility evidence separately. Silent/missing instruments also
need channel/articulation checks; a rhythm pass does not prove audio is correct.

Deliver the audit report, correction/provenance records, reviewed scope, unresolved
cases, and validation evidence. State sample coverage precisely: equal bar totals,
successful parsing, or a short visual sample does not establish full-score fidelity.
