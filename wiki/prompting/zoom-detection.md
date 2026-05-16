---
topic: zoom-detection
---

# Zoom detection

Recipes for finding zoom-in / zoom-out / Ken-Burns / zoom-punch moments. These motion events are easy to miss because still frames can't show them — you need either Gemini's per-clip analysis or *two* frames at different timestamps within the same shot.

See also [[motion-and-zoom]] and [[animation-behavior]].

## Recipe: exhaustive zoom inventory of a short clip

**When to use**: a side-by-side comparison feels visually flat compared to the source — flat usually means missing slow zooms, not missing cuts.

**Prompt template**:
> List every ZOOM event in this {N}-second clip. A zoom is any visible scale change on any element: a slow push-in on a speaker shot, a zoom-punch on a b-roll card (sudden scale-up), a pull-back at end of a segment, a Ken-Burns drift on b-roll content inside a frame, a quick scale-pop on a text overlay, etc. INCLUDE subtle/slow ones too — they matter as much as dramatic ones.
>
> For each zoom event give ONE line in this exact format:
>
> `@<start>s-<end>s :: <element> :: <direction>,<magnitude>,<feel>`
>
> Where:
> - `<start>s`, `<end>s`: seconds from clip start. Use the END timestamp where the motion settles or the segment cuts.
> - `<element>`: speaker shot | pip card | pip stack | grid background | pill background | pill text | exclamation badge | channel watermark | other:<short description>
> - `<direction>`: zoom-in (scale grows) | zoom-out (scale shrinks)
> - `<magnitude>`: subtle (1-5% scale change) | medium (5-15%) | heavy (15%+)
> - `<feel>`: linear | ease-out | ease-in | ease-in-out | snap
>
> Be exhaustive. Include zooms on b-roll content INSIDE its card (Ken-Burns), and any "punch" zooms at cut boundaries. No prose.

**What worked**: explicit examples of categories (Ken-Burns, push-in, punch, pull-back) primed Gemini to look for the slow ones. Closed `<magnitude>` enum forced commitment instead of vague "some zoom."

**What didn't work**:
- "Are there any zooms?" → got yes/no without timestamps.
- Asking only about the speaker shot → missed b-roll-internal Ken-Burns.
- Not including "subtle" in the magnitude enum → Gemini ignored slow zooms because they didn't seem "worth reporting."

**Verification**: zooms cannot be confirmed by a single still. Either:
1. Extract 2-3 frames at evenly spaced timestamps within the same shot and compare visual size of the subject; OR
2. Use the targeted "confirm a single suspected motion" recipe from [[animation-behavior]] with `<motion-type>=zoom-in` / `zoom-out`.

**Gotchas seen in [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]**:
- Gemini's zoom-event timings on long-held elements (like a pill overlay) drift — it'll report a zoom that *should* be a zoom-pop entry as a long slow zoom. Always cross-check the START timestamp against your independently-verified element entry time.
- On a 10s chunk Gemini caches its analysis and can return stale event lists when re-prompted with a different motion-grammar prompt. Use a fresh chunk (e.g. 0-9.5s) to force re-analysis.

**Sources**: [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]
