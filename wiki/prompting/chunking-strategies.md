---
topic: chunking-strategies
---

# Chunking strategies

Meta-page: how to pick chunk boundaries when watching a long video. The hard cap on `recreator ask` is 120s (configurable). The default chunk is 60s.

## Default: 60s grid

Simplest. Use it unless you have reason not to. `recreator chunk <slug> --length 60` precomputes all chunks; `ask` lazily slices as needed.

> **STRONG caveat from [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]:** the 60s default is **unfit for editing reconstruction**. Building a Main.tsx from 60s observations produced a recreation the user called "totally different" from the source — Gemini merges adjacent cuts, hallucinates layouts (especially when given closed enums), and reorders events. **Use 5-10s chunks** for any inventory whose output will drive Remotion timestamps:
>
> - **10s chunks** — default for cuts / b-roll / on-screen text / motion inventory.
> - **5s chunks** — for nailing micro-events (zoom punches, text in/out, transition kind).
> - **60s** — only for *one* high-level vibe/pacing/narrative-beats pass. Never for timestamps.
>
> The first call to a fresh chunk pays the upload cost; asking 2-4 questions of the same slice is then nearly free. Don't economize on call count at the cost of timestamp accuracy.

## Overlap for cut detection

A cut landing exactly on a chunk boundary will be missed (or double-counted). For dedicated cut-detection passes, use overlapping ranges:

```sh
recreator ask <slug> --range 0-60   --prompt "..."
recreator ask <slug> --range 55-115 --prompt "..."
recreator ask <slug> --range 110-170 --prompt "..."
```

Cuts in the 55-60s and 110-115s overlaps will appear in both calls — dedupe by timestamp.

## Section-aligned chunking

If you've already identified narrative sections (hook / point 1 / point 2 / outro), align chunks to section boundaries instead of a 60s grid. Each chunk becomes a coherent semantic unit, so questions about "what changes between this section and the next" land better.

## Silence-aligned chunking (post-MVP)

Future: `recreator chunk <slug> --silence` would use `ffmpeg silencedetect` to break on speech pauses. Until then, eyeball it.

## When to use long chunks (90-120s)

For high-level overview passes: "summarize what happens in this clip in 3 bullet points." Detailed timestamp questions get worse as chunks grow — Gemini's temporal precision degrades past ~60s.

## When to use short chunks (15-30s)

For micro-analysis: "exactly when does the subject's avatar shrink to PiP?" Use `recreator frame` (post-MVP) for sub-second precision.
