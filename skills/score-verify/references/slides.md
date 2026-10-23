# Slide preservation and independent source comparison

The report always includes `slides.ledger`: slide kind, note-level origin and
resolved target, including cross-bar connections. This describes the parsed file;
it does not discover a source marking omitted during transcription. A parser may
also discard a slide whose destination it cannot resolve.

To detect omissions, supply an independently reviewed source inventory:

```sh
node scripts/audit_alphatab.cjs score.gp --expected-slides source-slides.json --json report.json
```

## Reference format

This original synthetic example describes a slide across a measure boundary:

```json
{
  "schemaVersion": 1,
  "ticksPerQuarter": 960,
  "scope": [{"track": 0, "staff": 0, "fromBar": 1, "toBar": 3}],
  "slides": [{
    "kind": "shift",
    "origin": {"track": 0, "staff": 0, "bar": 2, "voice": 0, "onset": 1920, "string": 1, "fret": 3},
    "target": {"track": 0, "staff": 0, "bar": 3, "voice": 0, "onset": 0, "string": 1, "fret": 7}
  }]
}
```

- Track, staff and voice indices start at **0**. Bars start at **1** in written
  order, before playback repeat expansion. `onset` is a nonnegative notated offset
  in the declared tick resolution. The report normalizes to 960 ticks per quarter.
- `string: 1` means the **highest string**. The helper converts alphaTab's reverse
  string numbering. Stringed notes require a fret; non-stringed notes use `pitch`
  (MIDI pitch) instead. This is a musical locator, independent of chord note order.
- `dead: true` means unknown pitch. Use `fret: null` or omit the fret for a dead
  stringed note. Do not supply a fabricated zero fret. Omitted `dead` means false.
- A grace endpoint adds `grace: true, graceIndex: 0`. `graceIndex` is the zero-based
  order among grace beats at the same notated onset in that voice; it defaults to
  0. The main note omits both. A before-beat grace may have negative playback time
  while sharing the main note's display onset; the reference uses display onset.
- Kinds: `shift`, `legato`, `out-up`, `out-down`, `into-from-below`,
  `into-from-above`, `pick-up`, `pick-down`. Shift and legato require a target;
  all other kinds require `target: null` or an omitted target.
- `scope` declares source-inspected **origin** ranges. Destinations may cross a
  range boundary. Every slide originating in these ranges must be listed. An
  inspected range without slides uses an empty `slides` array. Uninspected ranges
  are excluded; a passing subset does not certify the full score. Full-score slide
  coverage requires all requested tracks/staves, including ranges with no slides.

The CLI binds the reference filename/hash to the report. Do not derive expected
slides from the tested export: that would reproduce omissions as a passing
reference. Retain source page/crop evidence separately; the checker cannot prove
how the reference was prepared. `evidence.source` remains `not_checked`.

## Interpret results

`slides.reference` records comparison status, range, expected/actual counts and
missing/extra/wrong-endpoint totals. Any mismatch fails `structural.pass` and the
CLI exits 1. Invalid reference data is an input error (exit 2). Without a reference,
the ledger is still produced, but source omission checking is `not_provided`.

Directed slides must point forward to a note in the same track/staff, with the
same string when both endpoints are stringed, and reciprocal model links. Unsafe
graphs prevent MIDI generation. A same-pitch slide emits `slide_zero_interval`:
inspect whether the effect was attached before a tied continuation instead of
the final held segment. Same display onset is valid for a preceding grace beat.

Inspect rendered lines and pitch-bend playback events or listen to the affected
transition. Counts of notes or NoteOn events alone do not establish slide playback.
Keep primary-player evidence separate from a target application's compatibility;
an importer may collapse slide types or omit effects on tied notes.
