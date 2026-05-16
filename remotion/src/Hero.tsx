import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio, Video } from "@remotion/media";
import { SlidingStackPip } from "./components/SlidingStackPip";

/**
 * Cinegraph Hero — the agent's recreation of the first 10s of
 * "Why Infrared Saunas Are in a League of Their Own" by Doc Q,
 * rendered entirely from placeholder assets.
 *
 * Style notes the wiki currently encodes (and that I, the editor,
 * applied here):
 *  - Persistent Q+ channel watermark, bottom-right, always on top.
 *  - Speaker has a subtle continuous push-in zoom (scale 1.00 -> 1.06).
 *  - 1.9-4.3s PiP segment: turquoise grid background with three b-roll
 *    cards sliding in stacked, slight rotation/scale variance, whip off
 *    left at the end.
 *  - 6.9-9.5s lower-left attention pill — "NOT ALL SAUNAS ARE CREATED
 *    EQUAL" — turquoise pill, yellow accent on "SAUNAS", red exclamation
 *    badge pops in late, pop SFX synced.
 *
 * Between attempts, self-improve writes new lessons into
 * my_skills/<skill>/SKILL.md. The editor re-reads them and rewrites this
 * file.
 */

const FPS = 30;
const s = (sec: number) => Math.round(sec * FPS);

const TURQUOISE = "#5fbfb0";
const TURQUOISE_DEEP = "#3a9c8d";
const TEXT_WHITE = "#ffffff";
const ACCENT_YELLOW = "#fff14d";
const ACCENT_RED = "#ed2a2a";

const ChannelWatermark: React.FC = () => (
  <div
    style={{
      position: "absolute",
      right: 40,
      bottom: 40,
      width: 130,
      height: 130,
      background: "#ffffff",
      borderRadius: 22,
      boxShadow: "0 8px 24px rgba(0,0,0,0.25)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      fontFamily: "Inter, system-ui, sans-serif",
      fontWeight: 900,
      fontSize: 88,
      color: TURQUOISE_DEEP,
      letterSpacing: -4,
    }}
  >
    Q
    <span
      style={{
        position: "absolute",
        top: 18,
        right: 26,
        fontSize: 28,
        color: "#1d3aa7",
        fontWeight: 900,
      }}
    >
      +
    </span>
  </div>
);

const SpeakerShot: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.06], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      >
        <Video
          src={staticFile("avatar-16x9.mp4")}
          loop
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
    </AbsoluteFill>
  );
};

const PillOverlay: React.FC<{ prefix: string; accent: string; suffix: string }> = ({
  prefix,
  accent,
  suffix,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const boxEnter = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 220 },
    durationInFrames: 10,
  });
  const dy = interpolate(boxEnter, [0, 1], [80, 0]);
  const boxScale = interpolate(boxEnter, [0, 1], [0.85, 1]);
  const boxOpacity = interpolate(frame, [0, 4], [0, 1], { extrapolateRight: "clamp" });
  const textOpacity = interpolate(frame, [10, 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bangEnter = spring({
    frame: frame - 16,
    fps,
    config: { damping: 8, stiffness: 260 },
    durationInFrames: 8,
  });
  const bangScale = interpolate(bangEnter, [0, 1], [0, 1]);
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "flex-start",
        paddingLeft: 100,
        paddingBottom: 140,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          opacity: boxOpacity,
          transform: `translateY(${dy}px) scale(${boxScale})`,
          transformOrigin: "left bottom",
          position: "relative",
          display: "inline-block",
          maxWidth: 1000,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: -34,
            left: -6,
            color: ACCENT_RED,
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 900,
            fontSize: 84,
            lineHeight: 1,
            transform: `scale(${bangScale})`,
            transformOrigin: "left bottom",
            textShadow: "0 4px 14px rgba(0,0,0,0.4)",
          }}
        >
          !
        </div>
        <div
          style={{
            background: TURQUOISE,
            color: TEXT_WHITE,
            padding: "22px 36px",
            borderRadius: 18,
            boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 900,
            fontSize: 76,
            lineHeight: 1.05,
            letterSpacing: 0.5,
            textShadow: "0 3px 0 rgba(0,0,0,0.15)",
            display: "inline-block",
          }}
        >
          <div style={{ opacity: textOpacity }}>
            {prefix}
            <span style={{ color: ACCENT_YELLOW }}> {accent}</span>
          </div>
          <div style={{ opacity: textOpacity }}>{suffix}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Hero: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence from={s(0)} durationInFrames={s(1.9)} layout="none">
        <SpeakerShot />
      </Sequence>

      <Sequence from={s(1.9)} durationInFrames={s(2.4)} layout="none">
        <SlidingStackPip
          cards={[
            { from: s(0), src: staticFile("broll1-16x9.mp4"), settleX: -40, rotate: 2, scale: 1.0 },
            { from: s(0.8), src: staticFile("broll2-16x9.mp4"), settleX: 30, rotate: -3, scale: 1.02 },
            { from: s(1.7), src: staticFile("broll3-16x9.mp4"), settleX: -10, rotate: 1, scale: 1.04 },
          ]}
          whooshSfx={staticFile("whoosh.mp3")}
        />
      </Sequence>

      <Sequence from={s(4.3)} durationInFrames={s(10.0 - 4.3)} layout="none">
        <SpeakerShot />
      </Sequence>

      <Sequence from={s(6.9)} durationInFrames={s(9.5 - 6.9)} layout="none">
        <PillOverlay prefix="NOT ALL" accent="SAUNAS" suffix="ARE CREATED EQUAL" />
      </Sequence>

      <Sequence from={s(6.9) + 16} durationInFrames={Math.round(FPS * 0.25)} layout="none">
        <Audio src={staticFile("pop.mp3")} volume={0.8} />
      </Sequence>

      <ChannelWatermark />
    </AbsoluteFill>
  );
};
