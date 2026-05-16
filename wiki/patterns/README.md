---
purpose: editing patterns observed across recreations
---

# Patterns

Generic editing techniques cataloged across multiple recreations. Pages live as `<topic>.md` (e.g. `hook-structures.md`, `b-roll-cadence.md`).

## Page shape

```markdown
---
topic: hook-structures
sources: [<slug>, <slug>]
---

# Hook structures

## Pattern: question-then-payoff
...description...
**Examples**: [[<slug>#hook]], [[<slug>#hook]]
```

Add new pages liberally; merge duplicates during cross-video session wrap-up. Link to per-video wikis with `[[<slug>]]`.

## Implemented vs. documented patterns

Some patterns have **runnable TSX implementations** in [`../../components/`](../../components/). Those pages should set `component: ../../components/<Name>.tsx` in frontmatter so future recreations can find both the doc and the code together. Components are copied into each `runs/<slug>/remotion/src/patterns/` automatically by `recreator remotion <slug> init`.

## Catalog (implemented)

- [[sliding-stack-pip]] — turquoise-grid + rounded cards sliding in from the right, stacking, then whip-exit left. From [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]].
