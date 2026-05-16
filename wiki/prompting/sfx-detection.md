---
topic: sfx-detection
---

# SFX detection

Sound effects (whooshes, pops, dings, snaps) are part of the *editing*, not the asset acquisition — an editor added them on top of the voiceover. Detecting them is part of recreator's job, and the recreations should wire them in via `<Audio>` placed at the same frame the matching visual event fires.

See also [[audio-and-music]] for music/voice/ducking recipes.

## Recipe: SFX hit inventory of a short clip

**When to use**: a side-by-side comparison feels visually right but lifeless — you almost always need SFX at every card entry, text reveal, badge pop, transition stinger.

**Prompt template**:
> List every discrete SOUND EFFECT in this {N}-second clip — short, non-musical, non-voice sounds that an editor added on top of the voiceover. Examples: whoosh (card slides in), swoosh, ding, pop (text appears), thud, click, snap, riser, transition-stinger. EXCLUDE: the speaker's voice, continuous background music, ambient room sound.
>
> For each SFX give ONE line in this exact format:
>
> `@<sec>s :: <kind> :: <one-line description of what it accompanies>`
>
> Where `<sec>` is the timestamp (in seconds from clip start) of the SFX's hit/peak — not its duration. `<kind>` from: whoosh | swoosh | swish | pop | ding | thud | click | snap | riser | stinger | other:<short>.
>
> Be exhaustive. If there are NO SFX (only voice + music), output the single line `none`. No prose.

**What worked**: explicit "EXCLUDE voice/music/ambient" prevented Gemini from listing the host's speech as percussive hits. Closed `<kind>` enum prevented invented sound categories.

**What didn't work**:
- "What sounds do you hear?" → got transcripts of the speaker.
- Not asking for HIT timestamp (asked for "duration" instead) → Gemini gave ranges that lined up with the visual element's full duration, not the SFX peak.
- Asking on chunks longer than ~15s → Gemini "rounded" SFX into coarse seconds and missed small hits.

**Gotchas seen in [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]**:
- Gemini's SFX timestamps tend to be 0.5-1s EARLY for fast-cadence card transitions — verify by lining the reported `@<sec>s` against your independently-known visual entry frames, and prefer the visual timestamp if they disagree.
- Gemini calls almost everything `pop` or `whoosh` regardless of what it actually sounds like — the kind enum reads more as "categories I'd accept" than "what I heard." Treat the timing as the signal, kind as a hint.

**Wiring into Remotion**:

```tsx
<Sequence from={visualEntryFrame} durationInFrames={Math.round(fps * 0.5)} layout="none">
  <Audio src={staticFile("whoosh.mp3")} volume={0.7} />
</Sequence>
```

Reuse the same `<Audio>` file across multiple SFX hits — `<Sequence>` plays the audio from frame 0 each time it activates. Common placeholder files live in `placeholders/`:
- `whoosh.mp3` — card slide-ins, page wipes, large element entries
- `pop.mp3` — text reveals, badge pops, small UI element snaps

Reusable patterns that ship with SFX support (see `recreator/components/`):
- `SlidingStackPip` — takes a `whooshSfx` prop and plays it at each card's entry frame.

**Sources**: [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]
