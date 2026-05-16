import React from "react";
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import { Video } from "@remotion/media";

/**
 * Cinegraph Hero — the agent's current edit.
 *
 * This file is REWRITTEN by the agent (Claude Code) between attempts.
 * v1 = what I produce with no wiki to draw on: a sparse, "junior editor"
 * composition. After self-improve writes lessons into my_skills/*/SKILL.md,
 * I rewrite this file applying those lessons for v2.
 */

const FPS = 30;
const s = (sec: number) => Math.round(sec * FPS);

const SpeakerShot: React.FC = () => (
  <AbsoluteFill style={{ overflow: "hidden" }}>
    <Video
      src={staticFile("avatar-16x9.mp4")}
      loop
      muted
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </AbsoluteFill>
);

export const Hero: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* Speaker fills the whole 10s. No b-roll, no watermark, no zoom. */}
      <SpeakerShot />

      {/* Single plain text caption around the "infrared sauna" beat. */}
      <Sequence from={s(2)} durationInFrames={s(3)} layout="none">
        <AbsoluteFill
          style={{
            justifyContent: "flex-end",
            alignItems: "center",
            paddingBottom: 60,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              fontFamily: "system-ui",
              fontSize: 42,
              color: "#fff",
              background: "rgba(0,0,0,0.55)",
              padding: "10px 20px",
              borderRadius: 6,
            }}
          >
            infrared sauna
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
