import { Composition, getInputProps } from "remotion";
import { Main } from "./Main";
import type { Edl } from "./types";

const props = getInputProps() as Partial<Edl>;

const fps = props.fps ?? 30;
const width = props.width ?? 1280;
const height = props.height ?? 720;
const duration_s = props.duration_s ?? 10;
const durationInFrames = Math.max(1, Math.round(duration_s * fps));

const edl: Edl = {
  fps,
  width,
  height,
  duration_s,
  avatar: props.avatar ?? { source: "avatar-16x9", in_s: 0, out_s: duration_s },
  overlays: props.overlays ?? [],
  text_overlays: props.text_overlays ?? [],
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main as any}
      durationInFrames={durationInFrames}
      fps={fps}
      width={width}
      height={height}
      defaultProps={{ edl }}
    />
  );
};
