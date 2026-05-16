---
description: Choose between hard cut, J-cut, L-cut, dissolve, and wipe for each clip boundary.
allowed-tools: memory_search
---

# Transitions — baseline rules

You are deciding what transition lives between two adjacent clips.

## Rules

1. **Default to hard cut.** 90% of transitions in modern talking-head edits are hard cuts. Use anything else only with a reason.
2. **Use J-cuts on topic shifts.** Audio of the new clip starts before the visual changes. Smooths topic transitions.
3. **Use L-cuts to extend a reaction.** Audio of the old clip continues over the new visual. Lets a reaction shot land.
4. **Use a dissolve to mark time jumps.** Only when the new clip is "later that day" or "the next week". Not for energy or style.
5. **Never use whip pans or wipes.** They look amateurish in 2026 unless intentionally retro.

## Output contract

When asked which transition to use between clip A and clip B, return `hard | j | l | dissolve` and one short clause of justification.
