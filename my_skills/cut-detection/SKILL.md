---
description: Decide where to place cuts in a video timeline when assembling source clips into a final edit.
allowed-tools: memory_search
---

# Cut detection — baseline rules

You are placing cuts in a video edit. Use these rules to decide where every cut goes.

## Rules

1. **Sentence end rule.** Prefer cuts at the end of a complete sentence over mid-sentence cuts. End-of-sentence cuts feel natural; mid-sentence cuts feel jarring unless deliberate.
2. **Stay around 4-8 seconds per shot.** Hold a single shot for at least 3 seconds. Beyond 10 seconds, cut to b-roll or another angle.
3. **Cut on motion.** When subjects in two adjacent clips are moving in similar directions, cut on motion to hide the seam.
4. **Tighten pauses.** If the speaker pauses for more than 0.4 seconds without a meaningful breath, cut the silence out (J-cut or hard cut).
5. **Avoid back-to-back wide shots.** Two wide shots in a row signal "nothing interesting happened" — break with a close-up or b-roll between them.

## Output contract

When asked for cuts, return a list of `{source_clip, in_s, out_s}` tuples. Times are seconds, floats. No prose, no JSON wrapper.
