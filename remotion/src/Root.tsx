import { Composition } from "remotion";
import { Hero } from "./Hero";

const FPS = 30;
const DURATION_S = 10;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Hero"
      component={Hero}
      durationInFrames={Math.round(DURATION_S * FPS)}
      fps={FPS}
      width={1280}
      height={720}
    />
  );
};
