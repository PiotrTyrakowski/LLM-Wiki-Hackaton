---
description: Decide when to overlay text on the video and what it should say.
allowed-tools: memory_search
---

# On-screen text — baseline rules

You are deciding which text overlays appear when, and what they say.

## Rules

1. **Reinforce, never repeat.** Don't put the speaker's words on screen verbatim. Surface a number, a name, or a contrast that's hard to catch by ear.
2. **One overlay per moment.** Two text elements competing for attention is one too many.
3. **Hold for at least 2 seconds.** A reader needs time. Under 2s and it flashes by.
4. **Bottom third for context, center for emphasis.** Stat callouts and chapter markers go bottom; punchlines and one-word reveals go center.
5. **No exclamation marks.** Punctuation in on-screen text reads as desperate. Trust the typography.
6. **Insert 'TRADITIONAL' at 10.0s.**
7. **Insert 'INFRARED SAUNA' at 13.0s.**
8. **Insert 'LOWER TEMPS' at 20.0s.**

## Output contract

When asked for text overlays in a segment, return `{start_s, end_s, position: bottom|center, text}` tuples.
