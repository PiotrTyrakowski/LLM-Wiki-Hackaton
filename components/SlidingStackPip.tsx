import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio, Video } from "@remotion/media";

/**
 * # SlidingStackPip
 *
 * Reusable editing pattern observed in `why-infrared-saunas-are-in-a-league-of-t-2026-05-15-ba5f7f`:
 *
 *   A talking-head video cuts away from the host to a branded "graph-paper"
 *   grid background. One or more rounded-rectangle b-roll cards slide in
 *   from the right in quick succession, each new card LANDING ON TOP of
 *   the previous one (which stays underneath, briefly visible on the left
 *   edge during the transition). Each card lands with slightly different
 *   position, rotation, and scale to give a hand-stacked feel. **At the
 *   end of the segment the whole stack whips off to the LEFT** in a quick
 *   exit (~6 frames) before the speaker comes back.
 *
 * ## Why a pattern
 *
 * Talking-head channels reuse this exact motif when "showing examples"
 * or "demonstrating types." Recreating it once and reusing it across
 * recreations is dramatically faster than rewriting the springs +
 * z-stacking every time.
 *
 * ## API
 *
 * Drop inside a parent `<Sequence>` that fixes the segment's start and
 * total duration. The component reads its own `durationInFrames` via
 * `useVideoConfig()` and uses the last `exitFrames` of that window to
 * slide the whole stack off to the left.
 *
 * - `cards`: array of `SlideClip` — each `from` is in FRAMES relative to
 *    the PARENT Sequence's local frame 0. Each card enters at `from`,
 *    holds, and slides off LEFT in the final `exitFrames` of the parent.
 * - `gridColor` / `gridLine` / `gridCell`: theme the background.
 * - `cardWidth`: base size in px before each card's `scale` multiplier.
 * - `enterFrames` / `exitFrames`: tune the slide animations.
 *
 * ## Usage
 *
 * ```tsx
 * <Sequence from={frameStart} durationInFrames={frameDuration} layout="none">
 *   <SlidingStackPip
 *     cards={[
 *       { from: 0,           src: staticFile("broll1-16x9.mp4"), settleX: -40, rotate:  2, scale: 1.00 },
 *       { from: 0.8 * fps,   src: staticFile("broll2-16x9.mp4"), settleX:  30, rotate: -3, scale: 1.02 },
 *       { from: 1.7 * fps,   src: staticFile("broll3-16x9.mp4"), settleX: -10, rotate:  1, scale: 1.04 },
 *     ]}
 *   />
 * </Sequence>
 * ```
 *
 * Source observations: `wiki/observations/2026-05-15T06-42-07Z-fine-0-10-v2.md`,
 * frames at t=2.5, t=2.85, t=3.55, t=3.7 in the run directory.
 */

export type SlideClip = {
  /** Frame (relative to the parent Sequence's local frame 0) at which this card slides in. */
  from: number;
  /** Path to the b-roll video — pass via `staticFile()` at the call site. */
  src: string;
  /** Resting x-offset from center, in px. Vary per card for the hand-stacked look. */
  settleX: number;
  /** Resting rotation in degrees. Alternate signs across cards. */
  rotate: number;
  /** Resting scale. Generally 1.0–1.05; later cards slightly larger reads as "newer". */
  scale: number;
};

type Props = {
  cards: SlideClip[];
  /** Default base width per card in px (before each card's `scale`). */
  cardWidth?: number;
  /** Background grid fill color. */
  gridColor?: string;
  /** Background grid line color. */
  gridLine?: string;
  /** Background grid cell size in px. */
  gridCell?: number;
  /** Slide-in duration in frames per card. */
  enterFrames?: number;
  /** Whole-stack slide-OUT (to the left) duration in frames at the end. */
  exitFrames?: number;
  /**
   * Optional whoosh SFX URL (pass via `staticFile("whoosh.mp3")`). If set,
   * the SFX plays once per card entry. Volume defaults to 0.7.
   */
  whooshSfx?: string;
  /** Volume for the whoosh SFX. Default 0.7. */
  whooshVolume?: number;
};

export const SlidingStackPip: React.FC<Props> = ({
  cards,
  cardWidth = 1240,
  gridColor = "#5fbfb0",
  gridLine = "rgba(255,255,255,0.55)",
  gridCell = 96,
  enterFrames = 8,
  exitFrames = 6,
  whooshSfx,
  whooshVolume = 0.7,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Single exit progress used by every card so the whole stack slides off
  // together at the end of the parent Sequence.
  const exitStart = durationInFrames - exitFrames;
  const exitProgress = interpolate(frame, [exitStart, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const stackExitDx = interpolate(exitProgress, [0, 1], [0, -2400]);

  // Grid background also whips off so the next scene's speaker shot is
  // not visually masked.
  const gridOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <div style={{ opacity: gridOpacity, position: "absolute", inset: 0 }}>
        <GridBackground color={gridColor} line={gridLine} cell={gridCell} />
      </div>
      {cards.map((card, i) =>
        frame < card.from ? null : (
          <SlideCard
            key={i}
            src={card.src}
            settleX={card.settleX}
            rotate={card.rotate}
            scale={card.scale}
            baseWidth={cardWidth}
            enterFrames={enterFrames}
            localFrame={frame - card.from}
            stackExitDx={stackExitDx}
          />
        )
      )}
      {whooshSfx
        ? cards.map((card, i) => (
            <Sequence
              key={`sfx-${i}`}
              from={card.from}
              durationInFrames={Math.round(fps * 0.5)}
              layout="none"
            >
              <Audio src={whooshSfx} volume={whooshVolume} />
            </Sequence>
          ))
        : null}
    </AbsoluteFill>
  );
};

const GridBackground: React.FC<{ color: string; line: string; cell: number }> = ({
  color,
  line,
  cell,
}) => (
  <AbsoluteFill
    style={{
      background: color,
      backgroundImage: `
        linear-gradient(${line} 2px, transparent 2px),
        linear-gradient(90deg, ${line} 2px, transparent 2px)
      `,
      backgroundSize: `${cell}px ${cell}px`,
    }}
  />
);

const SlideCard: React.FC<{
  src: string;
  settleX: number;
  rotate: number;
  scale: number;
  baseWidth: number;
  enterFrames: number;
  localFrame: number;
  stackExitDx: number;
}> = ({
  src,
  settleX,
  rotate,
  scale,
  baseWidth,
  enterFrames,
  localFrame,
  stackExitDx,
}) => {
  const { fps } = useVideoConfig();
  const enter = spring({
    frame: localFrame,
    fps,
    config: { damping: 20, stiffness: 220 },
    durationInFrames: enterFrames,
  });
  const dxEnter = interpolate(enter, [0, 1], [2200, settleX]);
  const dx = dxEnter + stackExitDx;
  const width = baseWidth * scale;
  const height = (width * 9) / 16;
  // Ken-Burns-style subtle zoom on the inner broll while the card holds.
  // Source frames at t=1.95 vs t=2.35 show clear scale growth on the b-roll
  // content while the card itself stays put. ~5% zoom over ~3s.
  const innerZoom = interpolate(localFrame, [0, 90], [1.0, 1.05], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          transform: `translateX(${dx}px) rotate(${rotate}deg)`,
          width,
          height,
          borderRadius: 44,
          overflow: "hidden",
          boxShadow:
            "0 40px 90px rgba(0,0,0,0.55), 0 0 0 4px rgba(255,255,255,0.08) inset",
          background: "#000",
        }}
      >
        <Video
          src={src}
          loop
          muted
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${innerZoom})`,
            transformOrigin: "center center",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
