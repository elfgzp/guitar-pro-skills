# Timing interchange for the optional checker

This small JSON format carries **written voice timing**, not an entire musical
score. Keep pitches, ties, ornaments, source crops and editorial decisions in your
working representation. Convert into this format only for a structural timing
check or a comparison against independently reviewed timing.

Units are quarter notes, as integers or exact rational strings. An eighth-note
triplet is `"1/3"`; a quarter-note triplet is `"2/3"`. Do not round them to decimal
floats or choose a tick grid that cannot represent the actual tuplet ratio.

```json
{
  "schema": "guitar-pro-skills/rhythm-v1",
  "measures": [{
    "number": 1,
    "meter": [4, 4],
    "voices": [{
      "track": "guitar",
      "voice": "upper",
      "events": [
        {"onset": "0", "duration": "2/3", "kind": "note"},
        {"onset": "2/3", "duration": "1/3", "kind": "note"},
        {"onset": "1", "duration": "3", "kind": "rest"}
      ]
    }]
  }]
}
```

Each note/chord or rest is one event; simultaneous chord tones do **not** create
overlapping events in one voice. Different voices have separate event arrays.
Array order is immaterial: explicit onsets determine temporal order, and the
checker sorts them before checking intervals or comparing a reference.
The checker expects full explicit coverage of each supplied voice, including
rests; adapt omitted implicit rests deliberately. Omit an unused alternate voice,
not a sounding voice or a missing bar. Grace notes have no independent metrical
duration here: exclude them from this timing view and audit their playback in the
notation model. Tied continuations retain written duration and `kind: "note"`.

`number` is a unique nonnegative integer. For a pickup, cadenza, or partial-bar
excerpt, set `expected_duration` and a nonempty `duration_reason` on the measure,
for example `"expected_duration": "1", "duration_reason": "source pickup"`.
Do not use this override merely to make a broken bar pass. Meter changes belong
on each affected measure. Additive meters can use the total numerator; grouping
and accent patterns need a separate visual/music audit.

```sh
python scripts/audit_rhythm.py timing.json --output timing-report.json
python scripts/audit_rhythm.py timing.json --reference reviewed-timing.json --output comparison.json
```

Run those commands from this skill directory, or use the script's full location.
No third-party dependency is needed. Exit status: `0` supplied structure passes
and any reference matches, `1` validation mismatch, `2` input/output error.
The report records input hashes, not local absolute paths. Report writes are
atomic and cannot overwrite an input (including a hard-link alias).

A matching reference is meaningful only if someone checked it against the
source. The checker cannot detect omitted tracks or measures that are absent
from both inputs. `source_verified` deliberately remains false.
