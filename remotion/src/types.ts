export type Overlay = {
  source: string;
  kind?: "broll" | "image" | "pip";
  start_s: number;
  duration_s: number;
};

export type TextOverlay = {
  text: string;
  start_s: number;
  duration_s: number;
  position?: "bottom" | "center" | "top";
};

export type AvatarTrack = {
  source: string;
  in_s: number;
  out_s: number;
};

export type Edl = {
  fps: number;
  width: number;
  height: number;
  duration_s: number;
  avatar: AvatarTrack;
  overlays?: Overlay[];
  text_overlays?: TextOverlay[];
};
