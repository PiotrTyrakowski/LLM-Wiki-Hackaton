---
description: Decide when to overlay text on the video and what it should say.
allowed-tools: memory_search
---

# on-screen-text

Decide whether to add text overlays to a video segment and specify only timing, position, and text.

## Procedure

1. Add an overlay only when it helps the viewer understand or remember something that is not already obvious from the audio and visuals.
2. Reinforce the spoken content; do not transcribe or repeat the speaker verbatim.
3. Prefer short overlays that surface a key number, name, contrast, label, chapter marker, or concise takeaway.
4. Use at most one overlay at any moment. Do not create overlapping overlays.
5. Hold each overlay for at least 2.0 seconds unless the segment ends sooner.
6. Use `bottom` for context, statistics, names, labels, and chapter markers.
7. Use `center` only for major emphasis, reveals, or very short punchline-style text.
8. Do not specify visual styling, colors, boxes, fonts, animation, bolding, backgrounds, or graphic treatments.
9. Do not use exclamation marks.
10. Keep text concise. Use sentence case unless a proper noun or acronym requires capitalization.
11. If no overlay is clearly useful, return an empty list.

## Output contract

Return only an array of tuples/objects with these fields:

`{start_s, end_s, position: bottom|center, text}`

Do not include critique, rationale, styling instructions, or implementation notes.

<!-- Rewritten by cognee.improve_skill(apply=True). Rationale: The revision directly addresses the failure by forbidding styling requests, background/color instructions, critique text, and exclamation marks while preserving the baseline rules and clarifying the exact output contract. -->
