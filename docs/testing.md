# 验证范围 / Verification scope

The utilities are intentionally narrow. Their tests validate concrete invariants,
not a claim that arbitrary PDF music can be transcribed automatically.

## Automated checks

- `tests/test_inspect_pdf.py`: original synthetic PDFs, mixed/vector/raster
  classification hints, source hashes, safe report paths, and invalid input.
- `tests/test_audit_rhythm.py`: exact tuplets, overlapping events despite plausible
  totals, missing rests, explicit pickups, changing meter, independent voices,
  invalid fractions, and different rhythms with identical measure lengths.
- `tests/test_gpif_percussion.py`: synthetic GPIF/ZIP fixtures, per-track
  articulation mappings, MIDI compatibility metadata, unsupported inputs, and
  non-destructive patching.
- `tests/test_alphatab.cjs`: original generated notation, alphaTab parsing,
  structural validation, drum articulation resolution, tie/playback checks,
  malformed input behavior, and the independently installable slide tests.
- `skills/score-verify/tests/test_slides.cjs`: missing/extra slides despite unchanged
  pitch and rhythm, wrong endpoints, cross-bar round trips, unknown dead-note
  origins, open-ended types, grace identity, reference scope/tick units, unsafe
  graphs, and reference-file preservation.
- `tools/check_repository.py`: skill metadata, referenced file existence,
  self-contained resources, and common accidental private-path/secret patterns.
  Pattern scanning is a packaging aid, not a general secret-detection guarantee.

Run the commands in either README. All notation fixtures are generated from
original test data. Proprietary scores are neither required nor included.

## Skill behavior scenarios

These cases exercise decisions that script unit tests cannot establish. A
reviewer or another model should use only the relevant skill and its raw inputs,
without being given the intended solution. Record actual behavior separately
from the automated results.

| Input situation | Required observable behavior |
| --- | --- |
| Scanned music with vector watermark | Inventory remains heuristic; inspect the rendered notes before selecting vector extraction |
| TAB and staff disagree | Check tuning, capo, transposition, accidentals and source geometry; retain an explicit uncertainty |
| Rest and drum note share an x-coordinate | Preserve independent voices and note identities; do not create a default snare or delete a real hit |
| A sloping tuplet bracket is missed | Inspect bracket/stem geometry; compare exact onsets, not only bar sums; search related patterns |
| Source shows a tie into a final chord | Preserve per-note continuation and verify that playback does not add attacks |
| GPIF articulation index differs from GM pitch | Resolve through the track's articulation table; never treat the index as a MIDI number |
| Both exports have the same note count | Compare pitches, onsets, durations and ties; do not infer semantic equivalence from counts |
| A slide label lies between notes across a barline | Inspect line endpoints and the adjacent source system; do not depend on nearest-label distance |
| A dead-note chord leads into fretted notes | Preserve unknown start pitch and connect only source-supported strings; do not apply a beat-wide flag |
| A small grace fret slides into the main note | Preserve grace identity/order at the notated onset without adding an ordinary timed beat |
| A slide points at the next same-fret tied segment | Inspect the printed sustained note and final segment; inspect pitch-bend playback, not only attack counts |
| Exported slides pass internal checks | Compare an independent source inventory and explicit coverage; zero flags cannot establish zero source slides |
| CLI passes, but source/audio were not checked | Report structural evidence only; mark source and audible playback not-run |

## Important limits

Timing JSON contains only the explicitly supplied measures and voices. It
cannot discover omitted source material. GPIF compatibility augmentation cannot
repair missing notation, infer an absent kit map, or establish correct tie
identity. alphaTab parsing, event generation, browser rendering, audible
playback, and source comparison are different checks.

The browser viewer is a manual inspection surface. A click on Play or a nonzero
MIDI count alone is not evidence of audible drums. Use a known local SoundFont,
audition percussion separately, and retain the checked range in your report.

Third-party parser behavior is version-sensitive. The skill's dependency lock
and references document the implementation tested here; rerun the relevant
fixtures after upgrading. Passing alphaTab checks does not certify every Guitar
Pro or TuxGuitar release.

## Initial collection verification

The initial collection was exercised with Python 3.13.7, Node.js 20.20.1,
pdfplumber 0.11.10, and alphaTab 1.8.4. Forty-five Python tests and eleven Node
tests passed. All six skill entrypoints also passed frontmatter validation.
An independent usage pass copied only `score-verify`, installed its dependencies,
and ran its tests without the rest of the repository.

The local browser viewer rendered the original three-measure, two-track demo
into four SVG sections. Visual inspection confirmed tuplets, ties, custom drum
noteheads, and a percussion clef. A valid-score → invalid-file regression check
confirmed that the old notation, track selections, and review-export controls
are cleared; the failed file receives no rendering evidence from the old one.

These are repository/tool checks on synthetic inputs. They do not establish
full-PDF transcription accuracy, audible playback, or TuxGuitar compatibility
for an arbitrary score. Those require the task-specific steps in the skills.

## Slide regression verification

The slide tests were introduced against the earlier verifier: all ten initial
cases failed, including a removed slide with unchanged note pitches and bar
durations. The implementation adds a per-note ledger and independently supplied
source reference, rather than inferring completeness from exported flags. A
separate grace-slide regression failed before grace identity was added. These
synthetic cases include native GP export/reimport. They do not establish that a
user-supplied reference was actually reviewed or that audio was heard.
