---
description: Decide where to place cuts in a video timeline when assembling source clips into a final edit.
allowed-tools: memory_search
---

# cut-detection

Decide where to place cuts in a video timeline when assembling source clips into a final edit.

## Procedure

1. Place cuts at complete sentence endings whenever possible.
2. If the visual topic, referenced object, or on-screen point of interest changes, cut away from the current shot at the exact moment of the topic shift, even if this creates a shorter shot.
3. When a topic shift occurs during speech, prefer a cutaway, b-roll, insert, or relevant visual over staying on the speaker.
4. Keep most shots between 4 and 8 seconds.
5. Hold any single shot for at least 3 seconds unless a topic shift, important gesture, reaction, or required visual alignment demands an earlier cut.
6. Avoid holding one shot longer than 10 seconds; cut to b-roll, a close-up, reaction, or alternate angle.
7. Cut on matching motion when adjacent clips contain similar subject or camera movement.
8. Remove pauses longer than 0.4 seconds when they are not meaningful. Use a hard cut, J-cut, or L-cut as appropriate.
9. Preserve meaningful breaths, emotional pauses, comedic timing, and reactions.
10. Avoid back-to-back wide shots. Insert a close-up, reaction, detail, or b-roll between wide shots.
11. Do not cut in the middle of a word.
12. If a requested or inferred cut time is explicit, use that exact timestamp.

## Output contract

When asked for cuts, return only a list of `{source_clip, in_s, out_s}` tuples. Times are seconds as floats. Do not include prose, explanations, markdown fences, or a JSON wrapper.

<!-- Rewritten by cognee.improve_skill(apply=True). Rationale: The failure evidence indicates the baseline missed a necessary cutaway exactly at a visual topic shift around 1.9s. The revision adds explicit priority for visual topic shifts and exact requested timestamps while preserving the existing timing, sentence, motion, pause, and shot-variety rules. -->
