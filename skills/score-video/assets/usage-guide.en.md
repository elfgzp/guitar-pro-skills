# {{delivery_title}} — score video guide

<!-- Fill every token from the delivered files and verified reports. Remove
ungenerated file rows and irrelevant sections, including iMovie if no chroma
derivative was delivered. Replace filled artifact filenames with relative
Markdown links, check those links, and remove this comment before delivery. -->

## Choose a file

| File | Use | Size / frame rate / duration | Audio |
| --- | --- | --- | --- |
| `{{master_filename}}` | Transparent master for an editor that supports its alpha channel | {{master_dimensions}} / {{master_fps}} FPS / {{master_duration}} | {{master_audio_state}} |
| `{{preview_filename}}` | Opaque viewing preview; its background is part of the picture | {{preview_dimensions}} / {{preview_fps}} FPS / {{preview_duration}} | {{preview_audio_state}} |
| `{{chroma_filename}}` | Optional green/blue-screen derivative for chroma keying | {{chroma_dimensions}} / {{chroma_fps}} FPS / {{chroma_duration}} | {{chroma_audio_state}} |

Source: `{{source_filename}}`. Selected track: **{{track_name}}** (zero-based
index {{track_index}}). Tempo: **{{tempo_summary}}**. Playback speed:
{{playback_speed}}. Score placement in the delivered frame: {{score_placement}}.

The files were generated independently of a video editor. iMovie is an optional
way to combine a chroma derivative with your performance video.

## Align with your performance

Video time zero represents **{{timing_origin}}**. Count-in: {{count_in}}.
Written opening rests: {{leading_rests}}. First sounding note: {{first_note_time}}.
Applied timing offset: {{timing_offset}}. When the score begins with rests, its
first sounding note occurs after video time zero. Align the same musical event
in both clips using that event's recorded offset.

| Check | Musical event | Score video time |
| --- | --- | --- |
| Start | {{start_event}} | {{start_time}} |
| Middle | {{middle_event}} | {{middle_time}} |
| End | {{end_event}} | {{end_time}} |

Move the score clip so a listed event matches that event in the performance,
then check the other two landmarks. A constant mismatch calls for a start-offset
adjustment. A mismatch that grows or changes over time needs a measured tempo
or timing correction; matching the score's BPM alone does not prove a live
performance stays aligned. Avoid a speed change unless the resulting notation
timing is checked again.

## Use the transparent master

1. Import the performance and transparent master into an editor that supports
   the delivered codec and alpha channel. Put the performance below the score.
2. Preserve the score's aspect ratio and all staff/TAB lines. Position the strip
   as needed; check whether placement is already built into the delivered frame.
3. Align the musical landmarks above. Retain the intended performance audio;
   mute any reference audio listed in the file table if it would play twice.
4. Inspect light and dark portions of the performance for readable numbers and
   intact edges, then export a short test before the complete edit.

A plain video player may display transparency as black. That display alone does
not determine whether alpha is present. Use the decoded-alpha evidence below and
check the imported composite in your editor.

## Optional: iMovie on Mac with the green/blue-screen file

1. Import the performance and `{{chroma_filename}}`. Add the performance to the
   main timeline, then drag the chroma clip **above** it; release at the green +.
2. Select the upper clip. Open **Video Overlay Settings**, choose **Green/Blue
   Screen**, and click **Apply**. Adjust **Softness** sparingly if needed; keep
   thin staff lines and fret numbers intact. [Apple's green-screen guide](https://support.apple.com/guide/imovie/mov82da1338a/mac)
3. Open the clip's cropping controls and choose **Fit** to retain its frame.
   Preserve the delivered placement described above. [Apple's crop guide](https://support.apple.com/guide/imovie/mova56757e7e/mac)
4. Align the start, middle and end landmarks. Use the actual audio states in the
   file table to avoid doubling reference audio over the performance.
5. Choose **File → Share → File**, select **Video and Audio** and the intended
   resolution, then save. Review the exported file for sync, legibility and audio.
   [Apple's export guide](https://support.apple.com/guide/imovie/move6e0cb2ad/mac)

## What was checked

| Evidence layer | Result and checked scope |
| --- | --- |
| Source and selected track | {{source_verification}} |
| Video timing and scrolling | {{timing_verification}} |
| Decoded alpha and visual samples | {{alpha_visual_verification}} |
| Derivative files and audio | {{derivative_verification}} |
| Editor import, compositing and export | {{editor_verification}} |

Reports: `{{verification_reports}}`. Remaining limitations: {{limitations}}.
Editor compatibility is established only for the application/version and actions
actually tested above; general usage instructions are not an editor test result.
