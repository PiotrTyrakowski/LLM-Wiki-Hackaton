---
description: Pick the right b-roll clip to overlay on a speaker's words.
allowed-tools: memory_search
---

# broll-selection

## Procedure

When asked which b-roll to use at timestamp `t` for spoken line `L`, select one existing b-roll clip to overlay on the speaker.

1. Use only provided source clips. Do not invent footage, composites, grids, layouts, colors, graphics, or visual treatments.
2. Return a selection, not a critique or editing concept.
3. Match the literal content of `L` as closely as possible.
   - If `L` mentions a person, product, place, action, number, or object, prefer footage showing that exact thing.
   - If no exact match exists, choose the closest semantically related clip.
   - If no useful match exists, return `source_clip: null`.
4. Do not place b-roll over emotional, personal, climactic, or punchline moments. Return `source_clip: null` for those beats.
5. Keep the b-roll duration between 2 and 4 seconds whenever possible.
6. Start b-roll on a natural beat near `t`.
7. End b-roll at a sentence or phrase boundary when possible.
8. Avoid reusing the same clip if it was used within the last 30 seconds, unless it is clearly the best or only match.
9. Do not recommend multi-shot montages unless a montage clip is already provided as a single source clip.
10. Output only this JSON object:

```json
{"source_clip":"clip_id or null","in_s":0.0,"out_s":0.0,"why":"short clause"}
```

Set `in_s` and `out_s` to `null` when `source_clip` is `null`. Keep `why` to one short clause.

<!-- Rewritten by cognee.improve_skill(apply=True). Rationale: The revision prevents the observed failure by forbidding invented custom composites and critiques, requiring selection from existing clips only, and clarifying null behavior when no suitable b-roll exists. -->
