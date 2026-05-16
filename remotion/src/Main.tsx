import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import type { Edl, Overlay, TextOverlay } from "./types";

const sourceUrl = (stem: string, isImage: boolean): string => {
  const ext = isImage ? ".png" : ".mp4";
  return staticFile(`source/${stem}${ext}`);
};

const Avatar: React.FC<{ src: string; in_s: number; fps: number; durationFrames: number }> = ({
  src,
  in_s,
  fps,
  durationFrames,
}) => (
  <AbsoluteFill style={{ background: "#000" }}>
    <OffthreadVideo
      src={sourceUrl(src, false)}
      startFrom={Math.round(in_s * fps)}
      endAt={Math.round(in_s * fps) + durationFrames}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </AbsoluteFill>
);

const BrollLayer: React.FC<{ overlay: Overlay; fps: number }> = ({ overlay, fps }) => {
  const isImage = overlay.kind === "image" || /\.png|image\d/.test(overlay.source);
  return (
    <Sequence
      from={Math.round(overlay.start_s * fps)}
      durationInFrames={Math.max(1, Math.round(overlay.duration_s * fps))}
    >
      <AbsoluteFill style={{ background: "#000" }}>
        {isImage ? (
          <Img
            src={sourceUrl(overlay.source, true)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <OffthreadVideo
            src={sourceUrl(overlay.source, false)}
            startFrom={0}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            muted
          />
        )}
      </AbsoluteFill>
    </Sequence>
  );
};

const TextLayer: React.FC<{ overlay: TextOverlay; fps: number }> = ({ overlay, fps }) => {
  const isCenter = overlay.position === "center";
  const isTop = overlay.position === "top";
  return (
    <Sequence
      from={Math.round(overlay.start_s * fps)}
      durationInFrames={Math.max(1, Math.round(overlay.duration_s * fps))}
    >
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: isCenter ? "center" : isTop ? "flex-start" : "flex-end",
          padding: 64,
        }}
      >
        <div
          style={{
            fontSize: 56,
            fontWeight: 800,
            color: "#fff",
            textAlign: "center",
            textShadow: "0 4px 32px rgba(0,0,0,0.95)",
            fontFamily: "ui-sans-serif, system-ui",
            letterSpacing: "-0.01em",
            padding: "12px 24px",
            background: "rgba(0,0,0,0.45)",
            borderRadius: 12,
            maxWidth: "90%",
          }}
        >
          {overlay.text}
        </div>
      </AbsoluteFill>
    </Sequence>
  );
};

export const Main: React.FC<{ edl?: Edl }> = ({ edl }) => {
  const { fps, durationInFrames } = useVideoConfig();
  if (!edl || !edl.avatar) {
    return (
      <AbsoluteFill style={{ background: "#111", color: "#eee", justifyContent: "center", alignItems: "center" }}>
        <div style={{ fontSize: 28 }}>no EDL provided</div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Avatar
        src={edl.avatar.source}
        in_s={edl.avatar.in_s}
        fps={fps}
        durationFrames={durationInFrames}
      />
      {(edl.overlays ?? []).map((overlay, idx) => (
        <BrollLayer key={`o${idx}`} overlay={overlay} fps={fps} />
      ))}
      {(edl.text_overlays ?? []).map((overlay, idx) => (
        <TextLayer key={`t${idx}`} overlay={overlay} fps={fps} />
      ))}
    </AbsoluteFill>
  );
};
