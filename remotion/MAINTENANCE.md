# Scaffold template maintenance

These `.tmpl` files are written by `recreator remotion <slug> init` (see `src/commands/remotion.ts`) into `runs/<slug>/remotion/`. They are intentionally a minimal hand-maintained subset of what `bun create video` would produce, NOT a copy of it.

## Why we don't shell out to `create-video`

Considered and rejected (2026-05-15):

- `create-video` is interactive; non-interactive flag-piping is brittle (template names change).
- It produces example components we'd just delete — recreator's `Main.tsx` is always replaced by Claude Code.
- We'd still need post-processing to inject slug / composition id / duration from `probe.json`.
- Project boilerplate (Root.tsx / index.ts / package.json shape) has been stable across Remotion 4.x. The API drift risk lives in *runtime imports* (`<Sequence>`, `<Video>`, `interpolate`, etc.) — that's covered by the `remotion-best-practices` skill, not by the scaffolder.

## Drift check (run quarterly, or when a recreation fails on a fresh `bun install`)

```sh
# In a scratch directory:
bun create video drift-check --template=blank --no-install --no-git
# or: npx create-video@latest drift-check --template=blank --no-install --no-git

# Diff the shape:
diff -r drift-check/ /path/to/recreator/src/remotion/scaffold/ \
  --exclude='node_modules' \
  --exclude='*.tmpl'   # our files have .tmpl suffix; theirs don't
```

What to look at:

- `package.json` deps. If `remotion` / `@remotion/cli` major bumped, decide whether to bump our `^4.0.0` ranges and re-test a recreation end-to-end.
- `Root.tsx` shape. If the official starter switched the API (e.g. new `registerRoot` shape, `<Composition>` props renamed), update `Root.tsx.tmpl`.
- `tsconfig.json` compilerOptions. Usually safe to ignore, but watch for `moduleResolution` changes.
- `src/index.ts` — has been a one-liner for years; flag any change.

Ignore:
- Example component files (`HelloWorld.tsx` etc.) — we don't ship those.
- README content — we have our own.

## When in doubt

If a fresh recreation fails with a Remotion API error, the fix is usually in **the Main.tsx Claude writes**, not in the scaffold templates. Re-read the relevant `remotion-best-practices` rule first before touching `.tmpl` files.
