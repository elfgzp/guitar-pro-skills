# Video formats, timing and transparency

## Primary asset and optional derivatives

Use a **ProRes 4444 MOV** as the transparent editing master. In FFmpeg, inspect
`ffmpeg -h encoder=prores_ks` for the installed build and use the 4444 profile,
an alpha-capable pixel format such as `yuva444p10le`, and a nonzero `alpha_bits`.
The bundled encoder handles these settings and preserves the RGBA frame input.
A normal H.264 MP4 is an opaque delivery or preview format, not an alpha master.
See the [FFmpeg encoder reference](https://www.ffmpeg.org/ffmpeg-codecs.html#ProRes)
and [Apple ProRes format description](https://www.apple.com/final-cut-pro/docs/Apple_ProRes.pdf).

Keep the master independent of the eventual editor. If a chosen editor cannot
composite the alpha master, a chroma-key derivative is optional: composite the
same frames over a flat unused key color and encode an opaque MP4. An HD canvas
with the notation strip positioned near the bottom may be convenient for such
editors, but padding and placement belong to that derivative. Green background
is not transparency, and keying can degrade thin notation edges.

Provide previews with clearly identified baked backgrounds. Do not bake a
checkerboard into a file labeled transparent. Test the actual target app only
when compatibility is requested; importing in one editor does not certify others.

## Rendering and timeline contract

The bundled notation adapter is pinned to alphaTab 1.8.4. Its
[horizontal layout](https://docs.alphatab.net/docs/reference/types/layoutmode/)
places bars along one long row. Preserve this continuous layout when rasterizing
manageable tiles; splitting the source into independent page renders can lose
cross-bar musical marks. Keep tile position, image size, beat bounds and source
identity in a manifest so frame composition does not infer positions from pixels.

The adapter uses version-specific layout internals to produce proportional
spacing. Reject unsupported layout shapes or changed engine contracts explicitly;
do not silently fall back to ordinary engraving. Verify fixtures and visual
relationships before changing the dependency pin. Another notation engine is
valid if it satisfies the same geometry, timing and transparency contract.

[Rendered bounds](https://docs.alphatab.net/docs/reference/api/boundslookup) locate
notation, while [MIDI tick lookup](https://www.alphatab.net/docs/reference/types/midi/miditicklookup/)
locates playback events. They serve different purposes. For a constant-tempo
segment, elapsed seconds are `delta_ticks / ticks_per_quarter * 60 / BPM`; sum
segments at every tempo event. Compare event times and total duration against an
independent extraction, including changed meters, pickups, rests and tuplets.

Ordinary engraving allocates more width to dense notes and technique marks. A
camera interpolating between those note positions changes speed despite constant
BPM; a camera moving at constant speed over that unchanged layout misses the
notes. Instead, give every quarter note the same horizontal distance:

```text
notation x = origin + score_tick / ticks_per_quarter * pixels_per_quarter
camera x(t) = origin + playback_tick(t) / ticks_per_quarter * pixels_per_quarter
speed within each tempo segment = pixels_per_quarter * BPM / 60
```

The renderer defaults to `--pixels-per-quarter 120`. Its `--scale 1.6` controls
glyph size separately, so changing temporal spacing must not horizontally stretch
noteheads or text. Place rests, barlines and tuplet subdivisions on the same tick
grid; retain the correct endpoints and shapes of beams, slides and ties. If dense
notation collides, increase spacing and rerender rather than varying speed by
engraving width. `manifest.spacing.mode` must be `"proportional"`; the encoder
rejects older nonproportional assets, which must be rendered again.

Integrate all tempo events, including events inside a held note or rest. A step
tempo change causes a speed change at its exact time; do not smooth that change
or interpolate only between note onsets. At constant BPM the camera moves at
constant speed regardless of note density or meter. Keep fractional positions
through frame composition: integer rounding causes small steps at low speeds.
Resample transparent pixels without creating opaque edges or gaps between tiles.

For repeats/jumps, first map playback occurrences to the intended visual sequence.
A note's first notated occurrence is not its only playback time. Swing can alter
performed subdivisions, grace notes can have distinct playback offsets, and
multiple voices can have independent onset grids. The current simple route must
reject constructs it does not implement and report them by location. Supporting
a library's rendering of a symbol does not establish a correct scrolling clock.

Time zero is the beginning of the score's first beat, even if it contains rests.
The default silent asset includes no soundbank, lead-in or synchronization marker.
For a performance recording, align a known musical onset and then check later
landmarks for drift. Adjust offset or a measured time map explicitly; don't hide
retiming behind a claimed tempo match.

## Validate the encoded result

Check a short prototype before a full render. Record encoder versions and exact
settings, and retain the machine-readable manifest and encode report. After a
successful encode:

1. Probe codec/profile, width/height, FPS, duration and stream types. Confirm no
   audio stream when the contract is silent. Confirm the full timeline was encoded,
   not an earlier prototype. Expected frame count derives from duration and FPS.
2. Decode representative frames to RGBA. Measure the alpha channel: untouched
   background must remain zero; visible notation must include opaque/nonzero
   pixels. Inspect partially transparent edge pixels where antialiasing exists.
   An alpha-capable codec with every pixel opaque fails the overlay requirement.
3. Composite decoded frames over light and dark backgrounds and a checkerboard.
   Inspect halos, premultiplied/straight-alpha handling, thin staff lines, fret
   numbers, ties/slides and shadows. A black media-player canvas may simply be its
   transparency display; judge decoded alpha, not that appearance alone.
4. Check a sequence around tile seams and bar boundaries, not only single frames.
   Look for dropped or doubled columns, changing vertical baselines and jumps
   caused by mixing global and tile-local bounds. Check the last sounding note and
   final held/rest interval for premature cutoff.
5. Compare every beat origin with the proportional tick grid and camera positions
   with an independently integrated tempo map. At constant BPM, compare successive
   frame displacements through sparse and dense passages. Include a tempo change
   inside a held note, a meter change and movement below one pixel per frame;
   total duration and matching note-onset times alone do not prove smooth motion.

These checks establish video timing and alpha integrity for the inspected scope.
They do not establish that the GP transcription matches an original PDF, that a
performance was heard, or that a particular editor preserved transparency.
