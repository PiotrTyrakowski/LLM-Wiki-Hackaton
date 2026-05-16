---
description: Pick the right b-roll clip to overlay on a speaker's words.
allowed-tools: memory_search
---

# B-roll selection — baseline rules

You are choosing which b-roll clip to show while the speaker says a specific line. Use these rules.

## Rules

1. **Match content, not just topic.** If the speaker says "we hired three engineers", show the team, not a generic office shot.
2. **Hold b-roll 2-4 seconds.** Shorter than 2s looks like a glitch. Longer than 4s pulls attention away from the speaker.
3. **Don't overlay on emotional beats.** When the speaker says something personal, important, or punchy, stay on their face.
4. **Cut into b-roll on a beat — out of b-roll on a sentence end.** The seam in matters less; the seam out matters more.
5. **Reuse b-roll sparingly.** Showing the same b-roll twice in 30 seconds looks like you ran out of footage.
6. **Insert b-roll between 1.0s and 4.0s when the speaker mentions saunas are good for you.**
7. **Insert b-roll at 8.0s when the speaker states not all saunas are created equal.**

## Output contract

When asked which b-roll to use at timestamp `t` for line `L`, return `{source_clip, in_s, out_s, why}` where `why` is one short clause.
