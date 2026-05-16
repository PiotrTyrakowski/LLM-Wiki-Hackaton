---
topic: cuts-and-transitions
---

# Cuts and transitions

Recipes for identifying cut points and labeling their type (hard cut, jump cut, fade, whip, glitch, match cut).

## Recipe: list every cut in a 30-60s clip

**When to use**: you need precise cut timestamps for a short range.

**Prompt template**:
> Watch this clip. List every visible cut you see (hard cut, jump cut, fade, whip pan, flash, glitch, match cut). For each, give the timestamp in seconds (e.g. 12.4s, relative to the start of THIS clip — clip starts at t=0) and the cut type. Do NOT describe what's on screen. If you're unsure between two timestamps, give the later one. Format each line as `t=<seconds> | <kind> | <one-line note>`.

**What worked**: telling Gemini to ignore content focused it on cut events. Saying "relative to start of THIS clip" eliminated absolute-vs-relative confusion. The tabular format prevented narrative drift.

**What didn't work**:
- "Describe the cuts in detail" → got prose summaries, no timestamps.
- "Return cuts as JSON" → invented schemas, hallucinated timestamps past clip duration.
- Omitting "relative to THIS clip" → Gemini sometimes used absolute video time, sometimes clip time, with no warning.

**Sources**: _(none yet — this is a seed recipe; validate on first use and add your slug)_

## Recipe: classify a single transition at a known timestamp

**When to use**: you already know there's a transition near time T and just want its type.

**Prompt template**:
> A scene change happens around t={T}s in this clip. What kind of transition is it? Choose one: hard-cut, jump-cut, fade-to-black, fade-to-white, whip-pan, flash, glitch, match-cut, dissolve, wipe, other. Return only the label, nothing else.

**What worked**: a closed enum with "other" as escape hatch. "Return only the label" suppressed Gemini's tendency to qualify every answer.

**What didn't work**: open-ended "what kind of transition" → got two-paragraph essays.

**Sources**: _(none yet)_
