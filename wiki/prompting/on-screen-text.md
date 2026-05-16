---
topic: on-screen-text
---

# On-screen text

Recipes for finding captions, kinetic text, callouts, lower thirds, titles.

## Recipe: list every on-screen text occurrence in a clip

**When to use**: you need a text inventory for a chunk.

**Prompt template**:
> List every piece of text that appears ON SCREEN in this clip (captions, titles, callouts, lower thirds, kinetic text — but NOT text inside b-roll footage like signs or shop names). For each, give: timestamp it appears (seconds, relative to clip start), timestamp it disappears, the verbatim text, and a category (caption, callout, title, lower-third, kinetic). Format each line as `t=<in>-<out> | <category> | "<verbatim text>"`. If a caption changes word-by-word (karaoke style), give the first appearance and last disappearance only and add `karaoke` to the category.

**What worked**: explicitly excluding b-roll text suppressed irrelevant noise. The tabular format kept it disciplined.

**What didn't work**:
- "What text is on screen?" → got a single paragraph summary.
- Not excluding b-roll text → got transcriptions of every store sign and book cover.

**Sources**: _(none yet)_

## Recipe: identify caption style

**When to use**: you've established captions are present and want to nail down the style.

**Prompt template**:
> Look at the captions in this clip. Tell me ONLY: (1) style — choose one of: karaoke (one word highlighted at a time), pop (whole phrase appears at once), static (full sentence visible the whole time), word-by-word (one word visible at a time, no highlight). (2) position — top, center, bottom. (3) approximate font weight — thin, regular, bold, extra-bold. Return as `style=<x>; position=<y>; weight=<z>`. Nothing else.

**What worked**: closed enums everywhere; rigid output format.

**Sources**: _(none yet)_
