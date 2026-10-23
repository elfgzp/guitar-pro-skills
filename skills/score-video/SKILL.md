---
name: score-video
description: Generate a silent, transparent, continuously scrolling notation or TAB video from a selected Guitar Pro track, with score-derived timing and a fixed playhead, without a video editor or player GUI.
---

# Render a scrolling score overlay

Generate an independent video asset from a reviewed Guitar Pro file. Use a
horizontal score moving beneath a fixed playhead; page changes are a different
presentation. No iMovie, other editing application, screen recording or realtime
playback is required. Keep the score unchanged and write new outputs.

## Establish the output contract

Record the source hash, selected track, displayed staves, dimensions, FPS and
playhead position. Select by track name as well as index. Default to a silent
transparent master, starting at the first score beat at time zero, with no title
card, count-in or hidden offset. Preserve written rests at the start. Document
any requested timing offset or playback-speed change explicitly.

The bundled route uses pinned alphaTab with a headless browser for notation,
Python/Pillow for frame composition, and FFmpeg for encoding. These are replaceable
implementation choices, not a dependency on a particular model or video editor.
Read [references/video-formats.md](references/video-formats.md) for output formats,
alpha verification and timeline limits.

## Run the bundled route

Run from this skill directory. Use Node.js 20+, Python 3.11+, an FFmpeg build with
`prores_ks`, and the bundled dependency manifests. Install Chromium for Playwright
or pass an existing compatible executable through `--chromium`.

```sh
npm ci
npx playwright install chromium
python -m pip install -r requirements.txt
node scripts/render_score.cjs --input input.gp --track 0 --output output/tiles
python scripts/encode_overlay.py output/tiles/manifest.json output/prototype.mov --seconds 10
python scripts/encode_overlay.py output/tiles/manifest.json output/overlay.mov
python scripts/verify_overlay.py output/overlay.mov output/tiles/manifest.json --json output/alpha-check.json
```

Track indices are zero-based. The encoder defaults to 1920 pixels wide, 60 FPS
and a playhead at 20% of frame width; override with `--width`, `--fps` and
`--cursor`. Height comes from the renderer manifest. Use a new path for each
encode. The full encode writes the MOV plus a JSON report and encode log.
A short prototype proves appearance and encoding only, not complete coverage.

## Keep notation and time independent

Use horizontal layout and retain complete musical relationships while rendering.
Export transparent SVG/PNG tiles with their global x/y bounds. Do not independently
render small bar ranges if doing so loses earlier tie/slide origins. Wait for the
actual music fonts and render completion; fallback glyphs can look like missing
notes. Do not bake a background or checkerboard into the master.

Join tile-local glyph/beat coordinates to a common global coordinate space. Keep
bar and beat identities in the manifest, rather than guessing note positions from
regular pixel spacing. A tile boundary is a rendering detail, not a musical jump.

Build playback time from score ticks and the tempo map, including meter changes,
rests and tuplets. Use the playback tick lookup to map time to beats, then map
beats to rendered positions. Interpolate the scroll between verified anchors;
engraving width is not elapsed time. Never assume every bar has the same number
of seconds, or derive the whole song from its opening BPM alone.

Inspect repeats/jumps, swing, grace timing and simultaneous voices before a full
render. Implement their playback-to-layout mapping explicitly or reject them with
named unsupported features. Do not silently flatten or omit them. For repeated
playback, a single notated bar can have multiple timeline occurrences; a smooth
scroll needs an explicit layout strategy for each occurrence.

## Compose and encode

Compose only visible tiles at each frame onto an RGBA canvas, translating their
shared coordinates beneath the fixed playhead. Cache tiles rather than producing
one browser screenshot per frame. Respect transparent edge pixels and inspect
outlines/shadows against both dark and light backgrounds.

Encode a ProRes 4444 MOV with alpha and no audio. Confirm encoder support first;
a `.mov` filename alone does not guarantee transparency. An opaque preview or
optional green-screen MP4 is a separately named derivative, never the master.

## Verify and deliver

- Compare the manifest's complete bar/beat coverage and playback duration with an
  independently derived score timeline. Verify variable-meter/tempo boundaries,
  rests, tuplets and the ending. Frame rounding should be at most one frame.
- Inspect decoded frames at the start, technique passages, tile seams and ending.
  Check fret numbers, rests, slides/ties, fonts, staff-line continuity and cropping.
- Decode actual output pixels and prove background alpha is zero, notation alpha
  is nonzero and antialiased edges survive. Check over light/dark/checkered samples.
  Container metadata and an alpha-capable pixel format alone are insufficient.
- Confirm the source hash is unchanged and report selected track, FPS, dimensions,
  duration, timing origin, audio absence, limitations and checked ranges.

Deliver the transparent master, a convenient preview and concise timing guidance.
Synchronization to a recorded performance needs a known start offset and possibly
a measured tempo/alignment map; matching the GP tempo does not prove alignment to
a human recording. Report source fidelity, video timing, alpha integrity and
editor import compatibility as separate evidence layers.
