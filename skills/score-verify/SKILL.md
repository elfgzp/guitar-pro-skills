---
name: score-verify
description: Verify exported notation or Guitar Pro scores using structural checks, alphaTab playback events, visual review, listening and source evidence. Use after transcription or when a score renders or sounds wrong.
---

# Verify a score

Use separate evidence for parsing, structure, rendering, audible playback and source fidelity.
A successful import or balanced measure cannot prove that a transcription matches its source.
Honor the requested primary player; use alphaTab by default and other applications as compatibility checks.

## Establish the target

- Identify the exact score file, primary player and intended tracks or range.
- Record file hashes and tool versions before comparing results.
- Preserve the input. Write reports and derived files to separate paths.
- Clarify whether the request concerns file structure, notation, sound or source accuracy.
- Do useful independent checks while any source material or playback environment is unavailable.

## Install the bundled verifier

This skill directory is independently installable; no sibling skill or repository script is required.
Run these commands with this directory as the working directory:

```sh
npm ci
node scripts/audit_alphatab.cjs /path/to/score.gp --json /path/to/report.json
```

Node 18 or newer is required. The lockfile pins alphaTab to the tested version.
The CLI exits 0 for a structural pass, 1 for structural/MIDI errors and 2 for input/output errors.
It refuses report paths that alias the score, including hard links and symbolic links.
Reports are written through a temporary file and atomic rename.

## Check structure and generated MIDI

Read [references/checks.md](references/checks.md) when interpreting the JSON report.

1. Confirm that parsing succeeded and the intended tracks and measures are present.
2. Check each active voice against its meter, treating explicit pickups separately.
3. Exclude truly empty alternate voices; do not exclude a short rest-only voice.
4. Check every tie destination, origin identity, time order and reciprocal link.
5. Resolve percussion indices through the track's custom articulation table.
6. Read actual generated MIDI NoteOn counts and pitches, including per-track percussion output.
7. Investigate discrepancies before treating structural checks as passed.

Do not replace custom-kit indices with GM numbers merely because those numbers look familiar.
Do not silently fix parser defects inside a verification report.
If an older importer loses a percussion tie identity, retain the failure and check the original file independently.

## Inspect and listen

Read [references/review-evidence.md](references/review-evidence.md) for the manual review checklist.
Use a suitable existing player or the bundled local viewer:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

When serving this directory, open `http://127.0.0.1:8765/scripts/viewer.html`.
When serving a repository containing this directory, use its corresponding relative URL.
Select the score locally. Fonts and scripts load from the installed local dependency; no CDN is used.
Select a local SoundFont for playback; no SoundFont or vendor library is distributed with this skill.
Review complete systems and the ending, then listen to each instrument and suspicious transitions.
Record inspected ranges and what was actually heard. Player readiness alone is not listening evidence.

## Compare against the source

Match source page, measure, staff and voice to exported events.
Verify printed durations, tuplets, rests, ties and repeat expansions independently of measure sums.
For a chord, distinguish notes that reattack from notes that continue by ties.
For rhythm slashes, check the printed tie arcs and TAB before deciding whether to rearticulate.
Use explicit source corrections or reference fixtures where available; preserve unresolved observations.

## Deliver the result

Report each evidence layer as passed, failed or not checked, with the file hash and checked range.
Name actual defects and remaining uncertainty in concrete terms.
Keep primary-player validation distinct from optional cross-application compatibility.
Never describe an entire score as source-faithful on the basis of structure or a few checked bars.

For a synthetic smoke test, run `node scripts/make_demo.cjs /path/to/new-demo.gp`.
The generator refuses existing output files. Its original three-bar score contains mixed meter,
triplets, a guitar tie and independent drum-note ties; it contains no third-party music.
Run `npm test` to exercise the verifier, malformed data and input-preservation checks.
