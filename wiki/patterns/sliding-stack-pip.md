---
pattern: sliding-stack-pip
status: implemented
component: ../../components/SlidingStackPip.tsx
sources:
  - why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f
addedAt: 2026-05-15
---

# Sliding-stack PiP

**What it is**: a talking-head video cuts away to a branded "graph-paper" grid background, then rounded-rectangle b-roll cards slide in from the right in quick succession. Each new card lands on top of the previous one (which stays underneath, briefly visible on the left edge during the transition). At the end of the segment the whole stack whips off to the left in a quick exit before the speaker returns.

**Why it's a pattern**: talking-head channels reuse this motif anywhere they need to show "examples of X" or "types of Y" — the hand-stacked feel reads as "here's a montage of options" without committing to a full b-roll cutaway.

**Implementation**: see [../../components/SlidingStackPip.tsx](../../components/SlidingStackPip.tsx).

**API sketch**:

```tsx
<Sequence from={segmentStart} durationInFrames={segmentDuration} layout="none">
  <SlidingStackPip
    cards={[
      { from: 0,             src: staticFile("broll1-16x9.mp4"), settleX: -40, rotate:  2, scale: 1.00 },
      { from: 0.8 * fps,     src: staticFile("broll2-16x9.mp4"), settleX:  30, rotate: -3, scale: 1.02 },
      { from: 1.7 * fps,     src: staticFile("broll3-16x9.mp4"), settleX: -10, rotate:  1, scale: 1.04 },
    ]}
  />
</Sequence>
```

**Key visual decisions** (from frame analysis of source):

- Grid is `#5fbfb0` teal with white 96px-cell lines at ~55% opacity.
- Cards are 16:9, rounded corners ~44px, slight per-card rotation alternating sign (~±2-3°), slight scale increase on later cards.
- Card slide-in is a spring with `damping: 20, stiffness: 220` over ~8 frames.
- Exit (whole stack) is linear, ~6 frames, translateX to roughly -2.5× viewport-width.
- Grid fades out in sync with the exit so the next scene's speaker isn't masked.

**Failure modes seen during development** (worth remembering):

- Giving each sub-clip its own animating `<PipCard>` with its own spring creates a **black-flash gap** at every sub-clip boundary (the new card's opacity-from-0 entry briefly hides everything). Fix: cards must PERSIST from their entry until segment end and stack via z-order, not get swapped.
- Letting a single card swap its inner `<Video src>` produces a clean visual but is wrong — the source clearly has two cards overlapping during transitions (see source frame at t=3.55s of the sauna video).
- The "layout enum" anti-pattern from [[b-roll-identification]] cookbook applies: don't ask Gemini "is this PiP or fullscreen" — describe the actual motion ("a rounded card on a grid background") and verify with frames.

**Sources**: [[why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f]]
