---
purpose: how to interrogate video with Gemini for editing analysis
---

# The prompting cookbook

When you (Claude Code) need to ask Gemini something about a video, look here first. Each topic page is a list of recipes — battle-tested phrasings that produced useful answers.

## Recipe shape

```markdown
## Recipe: <short imperative title>

**When to use**: short description of the situation.

**Prompt template**:
> The exact prompt text. Curly braces for variables: `{startSec}`, `{endSec}`.

**What worked**: the insight that made this prompt land.

**What didn't work**: failure modes from earlier attempts.

**Sources**: [[<slug>]], [[<slug>]]
```

## Contribution flow

1. You used a recipe. It worked. **Add a "Sources" backlink** to your run's slug.
2. You needed something not covered. **You asked Gemini, got noise, asked the user, the user fixed your prompt, the new prompt worked.** Now write a new recipe with both the working phrasing AND the failure modes (so the next session understands why this phrasing matters).
3. You found that an existing recipe stopped working (model drift, edge case). **Append a "Caveats" section** rather than deleting; future-you may need to know what changed.

## Topics

- [[cuts-and-transitions]] — finding cut points and labeling their type
- [[on-screen-text]] — captions, kinetic text, callouts, lower thirds
- [[motion-and-zoom]] — zoom punches, pans, parallax, scale animations
- [[animation-behavior]] — how elements enter/exit/hold (the *motion grammar* beyond static timestamps)
- [[zoom-detection]] — finding slow push-ins, Ken-Burns drifts, zoom-punches, pull-backs
- [[sfx-detection]] — whooshes, pops, dings, transition stingers that the editor added on top of voiceover
- [[b-roll-identification]] — when b-roll appears, what it shows, how it's framed
- [[caption-styles]] — karaoke / pop / static, position, timing
- [[audio-and-music]] — music presence, ducking, SFX hits
- [[pacing]] — average shot length, cuts/min, longest static stretch
- [[chunking-strategies]] — meta: how to pick chunk boundaries

## Hard-won truths

- **Gemini hates committing to schemas.** Avoid "return JSON" — ask for a tabular text format like `t=<sec> | <kind> | <note>` instead.
- **Specificity beats verbosity.** "List every cut" > "describe the editing." Prose questions get prose answers.
- **One question per call.** Bundling questions muddles all the answers.
- **Tell it what to ignore.** "Ignore content; only list cut events" reliably suppresses narrative drift.
- **Numeric anchors help.** "At ~12s, what changes on screen?" works better than "what happens in the second third?"
