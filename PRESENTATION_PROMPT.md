# Presentation Prompt for Claude in Canva (or any AI deck generator)

Paste this prompt into Claude inside Canva, or into any presentation generator.

---

## The prompt

Build me a 9-slide presentation for a 3-minute hackathon demo. Hackathon is **Cognee × Redis "AI-Memory Hackathon: Building your own Agent LLM Wiki"** in San Francisco. Prize pool $1,500. Judges are Cognee + Redis founders and Pebblebed VC.

Design system: dark mode (background `#0a0a0f`), accent purple/violet (`#7c5cff`), accent red for Redis (`#dc382d`), white for cognee (`#ffffff`). Mono font for code (`JetBrains Mono`), bold sans-serif for titles (`Inter`). Big, confident type. Lots of negative space. Every slide has a one-line title at top and one big visual or pull-quote, never both. No corporate gradients. No stock images. Diagrams should look like neat ASCII / Mermaid / box-and-line — geometric, clean.

Project name: **Cinegraph** (working title — feel free to suggest 2 alternatives in a speaker-notes section: candidates are "Cinegraph", "ReelMind", "Maestro", "MimicCut", "Reelearn"). Throughout the deck, use **Cinegraph**.

### Slide deck spec

**Slide 1 — Title.**
- Title (huge, centered): **Cinegraph**
- Subtitle: *An editor agent that learns from the videos it tries to imitate.*
- Footer: Cognee × Redis Hackathon · SF · 2026-05-16

**Slide 2 — The problem in one line.**
- Pull-quote, huge: *"Most video editor agents replay one good prompt. They never get better."*
- Below: 3 bullets in small mono type:
  - You can't compress "good editing" into a single prompt.
  - You can't teach it via examples in context — too many cuts, too much rhythm.
  - You need an editor that *remembers* what it learned from the last edit.

**Slide 3 — The insight.**
- Title: *Video editing is an RL environment in disguise.*
- Diagram, centered:
  ```
  source clips ─►  agent  ─►  edited video
                                  │
                          ▼ compare to ▼
                          human-edited target
                                  │
                          ▼ writes lessons ▼
                          [Cinegraph wiki]
                                  │
                          fed back into next attempt
  ```
- One-line caption: *"The feedback signal is the actual human-edited video. The action space is the edit."*

**Slide 4 — Architecture.**
- Title: *Wiki, not weights.*
- Two-column diagram:

  Left column (red `#dc382d`): **Redis — session memory**
    - per-run observations
    - intermediate agent thoughts
    - live event stream for the demo viz
    - vector index over source clips

  Right column (white): **Cognee — permanent graph**
    - distilled lessons (SKILL.md files)
    - skill-improvement proposals
    - cross-run knowledge
    - `cognee.remember()` / `cognee.recall()` / `improve_skill()`

  Arrow between them labeled *"distillation"*.

- Footer caption: *"What Redis stores: the agent's working memory. What Cognee stores: what it actually learned."*

**Slide 5 — Demo setup (REMOTION VIDEO PLACEHOLDER — left side of screen).**
- Title: *The same source clips. Two different edits.*
- Left half of slide: large placeholder labeled **"Human edit (target)"** with a play button overlay
- Right half: large placeholder labeled **"Cinegraph attempt v1"** with a play button overlay
- Below, a score row in mono: `cut F1 = 0.39 · pacing Δ = 1.8s · b-roll P = 0.25`

**Slide 6 — The wiki updates itself (THE MONEY SHOT).**
- Title: *Self-improvement is a SKILL.md rewrite.*
- Side-by-side `diff` block — left "before", right "after":

  Before (gray):
  ```
  Cut detection — baseline:
    1. Prefer end-of-sentence cuts over mid-sentence.
    2. Keep shots 4–8 seconds.
  ```

  After (green for new, yellow for changed):
  ```
  Cut detection — after run v1:
    1. Prefer end-of-sentence cuts over mid-sentence.
    2. Keep shots 4–8 seconds.
    3. NEW: When the speaker pauses >0.6s mid-sentence,
       cut to b-roll, not a hard cut. (learned: run v1)
    4. CHANGED: Drop shot length to 2s during music drops,
       not just energy peaks.
  ```
- Caption: *"This file was rewritten by `cognee.improve_skill(apply=True)`."*

**Slide 7 — Demo result (REMOTION VIDEO PLACEHOLDER — second attempt).**
- Title: *Attempt v2 — same agent, smarter wiki.*
- Left half: large placeholder labeled **"Human edit (target)"**
- Right half: large placeholder labeled **"Cinegraph attempt v2"**
- Score row in mono, with delta: `cut F1 = 0.71  (↑ 0.32)`

**Slide 8 — How Redis specifically pulled its weight.**
- Title: *Four things Redis did that nobody else could.*
- 2x2 grid of cards:
  - **Session memory.** Cognee `session_id=` writes go straight to Redis. Hot, per-run scratchpad.
  - **Vector search.** RediSearch HNSW index over source clip descriptions — agent does sub-ms semantic clip retrieval.
  - **Streams.** Every `SkillRunEntry` event becomes a Redis Stream entry. The full self-improvement timeline is `XRANGE`-able.
  - **Pub/Sub.** Live demo viz subscribes to `llmwiki:live` channel; events animate as the agent works.

**Slide 9 — Close.**
- Pull-quote, huge: *"Wiki, not weights. Same agent, smarter every run."*
- Below: GitHub repo URL placeholder + team name placeholder.

### Speaker notes (please include under each slide)

For each slide, write a 2-sentence speaker note that maps to a 3-minute demo. Target time budget: slide 1+2+3 = 25s setup, 4 = 20s, 5 = 40s (play v1 video), 6 = 45s (read one rule aloud), 7 = 30s (play v2), 8 = 30s, 9 = 10s close.

### What I want you to produce in Canva

- A deck with the 9 slides above, in the design system specified.
- A speaker-notes panel on each slide.
- A title slide cover image option in two variants — one minimalist (just typography), one with a single geometric ribbon motif (suggesting a video timeline).

### What I do NOT want

- Stock photography of laptops or pixel-art faces.
- Anything pastel.
- Bullet-pointed walls of text.
- A reveal-style "click-to-expand" sequence — judges will see the static frames.
- Any AI-generated photorealistic illustration.
- The word "synergy" anywhere. Strike it on sight.

---

## Name suggestions to surface to the user

If you (Claude in Canva) want to push back on the name **Cinegraph**, present these alternatives on a "naming options" appendix slide:

| Name | Vibe |
|---|---|
| **Cinegraph** | Cinema + knowledge graph. Hat-tip to Cognee. |
| **ReelMind** | Film reel + a mind that remembers. Catchy. |
| **Maestro** | Conducting an edit. Confident. |
| **MimicCut** | On-the-nose: it mimics human editing. Memorable. |
| **Reelearn** | Reel + learn + relearn. Cute. |

Default to **Cinegraph** unless the user picks one.
