---
topic: b-roll-identification
---

# B-roll identification

Recipes for finding when b-roll appears, what it shows, and how it's framed.

## Recipe: list every b-roll moment in a clip

**When to use**: you need a b-roll inventory for a chunk.

**Prompt template**:
> A "b-roll moment" is when the video cuts away from the talking-head subject to a different visual (stock footage, screen recording, image, archival clip, animation) before returning. List every b-roll moment in this clip. For each, give: timestamp in (seconds), timestamp out (seconds), what is shown in 5-10 words, layout (fullscreen, pip-bottom-right, pip-top-left, split-left, split-right, overlay-bottom), and a short search query that would help find a real clip to fill this slot. Format each line as `t=<in>-<out> | <layout> | "<short description>" | query="<search query>"`. If the talking head stays visible the entire clip with no cutaways, output the single line `none`.

**What worked**: defining "b-roll moment" up front; closed layout enum; explicit `none` output for empty cases (otherwise Gemini hallucinates).

**What didn't work**:
- Not defining b-roll → Gemini conflated screen text overlays with b-roll cutaways.
- Asking "is there b-roll?" first then "describe it" → second call lost context.

**Sources**: _(none yet)_

## Recipe: describe what a single b-roll clip shows

**When to use**: you've got a known b-roll range and need a search-friendly description.

**Prompt template**:
> From t={start}s to t={end}s in this clip, the video cuts to b-roll. Describe in one sentence ONLY what is shown: subject, action, framing (close-up / medium / wide), lighting (bright / dim / moody), setting. Then on a second line, give a 4-8 word search query suitable for stock footage sites. No other commentary.

**Sources**: _(none yet)_
