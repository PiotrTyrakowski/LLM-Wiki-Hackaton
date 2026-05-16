# `components/` — shared editing-pattern library

This directory holds **reusable Remotion editing-pattern components** discovered across recreations. It's a first-class output of the recreator workflow: building this library is part of the job, not a side-effect.

## How it works

- `recreator remotion <slug> init` copies every `.tsx` here into `runs/<slug>/remotion/src/patterns/`. Each run gets a snapshot of the library at scaffold time.
- The run's `src/Main.tsx` imports from `./patterns/<Component>` and uses it like any local component.
- When a recreation produces a new pattern OR improves an existing one, **promote the refined version back here at session close** so the next recreation inherits it.

## Why a snapshot per run, not a shared import path

Each `runs/<slug>/` is a reproducible artifact — checked into git, rendered months later, etc. A live shared import would break old runs every time a pattern is refactored. Snapshot-on-scaffold means: old recreations stay rendering, new recreations get the latest patterns.

## How to add a pattern

1. Build it inside `runs/<slug>/remotion/src/patterns/<Name>.tsx` first — discover it in real recreation context, not in isolation.
2. Once the side-by-side comparison in that run looks right, copy the file here.
3. Update the corresponding wiki entry at `recreator/wiki/patterns/<name>.md` to link to the source run and the implementation.
4. Note the canonical version in the file's header docblock.

## Naming + API conventions

- One pattern per file. Default-exported or named export — both fine.
- The component should be **stateless w.r.t. media** — pass `staticFile()` URLs in via props rather than hardcoding asset names. This lets each run wire its own placeholders.
- Take `cards` / `clips` / `items` arrays where the pattern naturally repeats, with each item carrying its `from` (frames), `src`, and per-item visual variations.
- Read `useVideoConfig()` for parent duration; don't require the caller to pass total length when they already wrap you in a `<Sequence durationInFrames={...}>`.
- Document the source run + observation file paths at the top of the file. The "where this came from" trail matters.

## Catalog

| Component | Pattern | Source run |
|---|---|---|
| `SlidingStackPip.tsx` | Turquoise grid + rounded b-roll cards sliding in from the right, stacking, then whip-exit left | [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]] |
