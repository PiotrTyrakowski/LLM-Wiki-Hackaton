# Recreation: {{ slug }}

Auto-scaffolded by `recreator remotion {{ slug }} init`.

Source: {{ width }}×{{ height }} @ {{ fps }}fps, {{ durationSec }}s.

## Develop

```sh
bun install
bunx remotion preview     # interactive preview
bunx remotion render      # → out/{{ slug }}.mp4
```

## Where to look

- `../wiki/plan.md` — Claude Code's recreation plan
- `../wiki/observations/` — Gemini observations of the source video
- `../../../placeholders/` — stand-in avatar/b-roll/image assets
- `../../../wiki/prompting/` — how to ask Gemini for what

Replace the stub in `src/Main.tsx` with the real composition.
