---
topic: animation-behavior
---

# Animation behavior

Recipes for asking Gemini to describe HOW visual elements animate — not just WHEN they appear. Still frames miss zoom punches, scale entrances, slide-in directions, easing feels. These recipes target the *motion grammar* the editor used.

See also [[motion-and-zoom]] for the simpler "where does the camera move" recipe.

## Recipe: per-element animation grammar in a short clip

**When to use**: you've already identified the static beats (cuts/text/b-roll timestamps) and now need to recreate *how* each element entered/exited. Particularly useful when a side-by-side comparison shows the static composition matches but the *feel* is off.

**Prompt template**:
> Watch this {N}-second clip. I'm rebuilding it in motion-graphics code so I need to know how every visible element ENTERS and EXITS — not just when. For each animated element, give me one line in this exact format:
>
> `@<start>s-<end>s :: <element-name> :: enter=<verb><direction?>,<duration_ms>ms,<feel> :: exit=<verb><direction?>,<duration_ms>ms,<feel> :: hold=<what it does between entry and exit>`
>
> Where:
> - `<element-name>` is short and concrete: "speaker shot", "pip card", "pill background", "pill text", "exclamation badge", "title overlay".
> - `<verb>` is one of: cut (instant), fade, slide, scale-up, scale-down, push-in (zoom in), pull-back (zoom out), wipe, rotate-in, bounce-in, drift.
> - `<direction>` for slide/wipe: from-left, from-right, from-top, from-bottom, from-corner-tl, etc. Omit if not directional.
> - `<duration_ms>` is your best estimate in milliseconds (e.g. 200, 400, 800).
> - `<feel>` is one of: linear, ease-out, ease-in, ease-in-out, spring-bouncy, spring-soft, snap.
> - `<hold>` is what happens between entry and exit: "static", "slow push-in", "subtle drift", "looping playback", "color shift", etc. Use `static` if nothing.
>
> Be specific. Estimate timing from the visible motion blur and frame count, not from gut feel. If two elements share a synchronized entry, mention that in `<hold>`.
>
> No prose. No "let me know if you need more." Just the lines.

**What worked**: forcing a CLOSED grammar of verbs prevented prose. Asking for both ENTER and EXIT in one line covered the full lifecycle. Adding `hold` captured the subtle camera push-in / drift that lives between entrances and exits and is the part most often missed.

**What didn't work** (failure modes to remember):
- "Describe how each element animates" → got prose paragraphs that conflated multiple elements.
- Asking for `easing` as a free-text field → Gemini emitted fanciful curves like "elastic-bouncy-medium." Closed enum fixed it.
- Not asking about `hold` separately → Gemini lumped "ease-out + slow push-in" into the entry verb and lost the push-in entirely.
- Asking on chunks longer than ~15s → animation descriptions got noisy because Gemini tried to summarize the average behavior across the clip.

**Cross-check with frames**: this recipe describes motion, which still frames can't fully verify. Always pair with `recreator frame` or `ffmpeg -ss` on the entry+midpoint+exit timestamps to confirm the static endpoints match — then trust Gemini on the path between them.

**Sources**: [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]

## Recipe: confirm a single suspected motion

**When to use**: a side-by-side comparison feels off at a specific timestamp; you have a hypothesis ("there's a zoom punch on the speaker around 1.3s") and want a yes/no plus duration.

**Prompt template**:
> Look at the time range {start}s to {end}s in this clip. Is there a {motion-type} on {element}? Answer with ONE line in this format:
>
> `present=<yes|no> :: starts_at=<seconds-from-clip-start> :: duration_ms=<n> :: magnitude=<subtle|medium|heavy> :: feel=<linear|ease-out|ease-in|ease-in-out|spring-bouncy|spring-soft|snap>`
>
> If `present=no`, set the other fields to `n/a`. No commentary.

**What worked**: bounded yes/no with explicit "n/a" fallback prevented Gemini from over-confirming the hypothesis just to be agreeable.

**Sources**: [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]
