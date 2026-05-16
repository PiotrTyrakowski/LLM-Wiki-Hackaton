"""Pydantic EDL schema — layered composition (recreator-style).

The agent never re-uses the target's pixels. It composes a fresh edit from
placeholder assets:
  - avatar-16x9.mp4 — the speaker stand-in (always playing on track "avatar")
  - broll1-16x9.mp4 / broll2 / broll3 — cutaway clips that cover the avatar
  - image1-16x9.png / image2 / image3 — full-frame slides that cover the avatar

Tracks render bottom-to-top: avatar < image_slide < broll < text.
Overlays have a start_s + duration_s; outside that range, the layer below shows through.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Overlay(BaseModel):
    """A timed layer placed on top of the avatar."""
    source: str = Field(description="Filename stem under data/demo/source/, e.g. 'broll1-16x9' or 'image1-16x9'")
    kind: Literal["broll", "image", "pip"] = "broll"
    start_s: float = Field(ge=0, description="When the overlay enters")
    duration_s: float = Field(ge=0.1, description="How long it stays on screen")


class TextOverlay(BaseModel):
    text: str
    start_s: float = Field(ge=0)
    duration_s: float = Field(ge=0.1)
    position: Literal["bottom", "center", "top"] = "bottom"


class AvatarTrack(BaseModel):
    """The base avatar layer that fills the whole composition timeline."""
    source: str = "avatar-16x9"
    in_s: float = 0.0
    out_s: float = 10.0


class Edit(BaseModel):
    fps: int = 30
    width: int = 1280
    height: int = 720
    duration_s: float = 10.0
    avatar: AvatarTrack = Field(default_factory=AvatarTrack)
    overlays: list[Overlay] = Field(default_factory=list)
    text_overlays: list[TextOverlay] = Field(default_factory=list)

    @property
    def total_duration_s(self) -> float:
        return self.duration_s
