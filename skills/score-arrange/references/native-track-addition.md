# Adding a track to a native Guitar Pro file

Use this reference only when editing a supported ZIP/GPIF representation directly.
Other Guitar Pro generations need their own reader/writer. Inspect the actual
container and tested library version; an extension is not a format specification.

## Preserve the original container

Record the source hash and write to a new path. Inventory archive members before
editing. Preserve unrelated members and fields, including instrument data,
percussion articulation tables, compatibility properties, lyrics and automation.
A fresh model export may be musically close while discarding fields its importer
does not understand; compare against the original container too when relying on
those fields.

Prefer a maintained native API when it covers the required metadata. Direct node
cloning is an alternative for a known format, not a general GP conversion method.
Retain unsupported fields rather than rebuilding the entire file from a reduced
model. Do not transplant binary members from an unrelated score.

## Clone the graph, not just the visible notes

A track addition can affect several related structures:

- Track identity, name, tuning, instrument program, routing and playback state.
- Bar references in each master bar and the master track's track ordering.
- Bar → voice → beat → note references, plus rhythms, chords or other resources.
- Track-level and score-level display/part configurations.

Allocate fresh IDs for cloned objects in each applicable ID namespace, and remap
all references to the cloned graph. Share immutable resources only when the
format permits it. Do not alias mutable beat/note objects between source and
arranged tracks. References to track-owned chord diagrams or other resources need
corresponding resources in the new track, not just a copied numeric identifier.

Preserve all voices and technique metadata. Resolve ties/slides after the full
new track exists, and inspect cross-bar endpoints independently. A same-string
“next note” heuristic can connect to the wrong source when tracks alternate.

Assign available melodic MIDI channels and avoid the percussion channel. Account
for primary and effect/secondary channels where the format uses both. Retain the
source track's tuning and transpose relationship; program selection alone does
not define the instrument's sounding pitches.

## Update every track-count-dependent view

Some native GP containers include `PartConfiguration` and `LayoutConfiguration`
archive members in addition to GPIF. Their all-track view and per-part views may
encode track/group counts and visibility flags. Inspect and update the current
schema together with the new track; adding GPIF notes alone can leave a missing
part, stale view or invalid count in another reader.

Do not assume fixed byte offsets, endianness or one binary layout across format
versions. Use a version-aware implementation; preserve unknown trailing data.
Reopen the result and verify both the full score and the newly added single part.

## Compare the declared mutation set

The permitted changes should be small and explicit: appended track/bar graph,
updated part/view references, and optional source-track mute states. Canonicalized
XML or equivalent structural comparison can prove that original musical nodes
were retained. A separate semantic reader should confirm the music as well.

Compare original tracks' note/rest timing, string/fret, techniques, lyrics,
percussion output mapping, tempo and meters. Normalize only known structural ID
changes or declared playback settings. Record every additional difference.

In a target application, test whether saved mute states survive import. Some
TuxGuitar import paths ignore GP `PlaybackState`; that is version-sensitive and
must be checked in the installed version. If source guitars remain audible,
manual muting for audition is a valid documented workaround. It does not justify
removing the original source parts or describing the imported mute state as
verified.
