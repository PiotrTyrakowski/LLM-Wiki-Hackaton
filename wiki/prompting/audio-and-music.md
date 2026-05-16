---
topic: audio-and-music
---

# Audio and music

Music presence, ducking patterns, SFX hits, voiceover dynamics.

_(Seed page — Gemini's audio analysis is variable; document what works as you go.)_

## Starter prompt to refine

> Listen to the audio of this clip. Tell me ONLY: (1) is there background music? yes/no. (2) does the music duck (drop in volume) when the subject speaks? yes/no/no-music. (3) are there discrete sound effects (whoosh, ding, thud, etc.)? If yes, list each as `t=<sec> | <description>`. (4) is there a music change (new track / drop / build) anywhere? If yes, give timestamp and direction. Return as labeled lines: `music=...`, `ducking=...`, `sfx: ...`, `music_change=...`.
