"""Editor tools — the agent (Claude Code) calls these while writing Hero.tsx.

Mirrors the recreator pattern: when stuck on a specific moment, ask Gemini a
free-form question about a range of the target video, or extract still frames
to view directly.
"""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from rich.console import Console

from . import gemini_vision
from .config import DEMO_TARGET, RUNS_DIR

console = Console()


async def ask_target(prompt: str, start_s: float = 0.0, duration_s: float | None = None) -> str:
    """Slice the target to [start_s, start_s+duration_s], upload to Gemini, ask `prompt`."""
    target = DEMO_TARGET
    if not target.exists():
        raise FileNotFoundError(f"target missing: {target}")

    if duration_s is None:
        upload = await gemini_vision.upload_video(target, "_ask")
    else:
        chunk_dir = RUNS_DIR / "_ask" / "chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk = chunk_dir / f"{int(start_s * 1000)}-{int((start_s + duration_s) * 1000)}.mp4"
        if not chunk.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{start_s}", "-t", f"{duration_s}",
                 "-i", str(target),
                 "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart",
                 str(chunk)],
                check=True, capture_output=True,
            )
        upload = await gemini_vision.upload_video(chunk, "_ask")

    answer = await gemini_vision.ask(upload, prompt)
    console.print(f"[ask] uri={upload['uri']}")
    console.print(f"[ask] prompt={prompt[:120]}")
    console.print(f"[ask] answer:\n{answer}")
    return answer


def extract_frames(timestamps: list[float], out_dir: Path | None = None) -> list[Path]:
    """Extract single JPG frames from the target at the given timestamps."""
    target = DEMO_TARGET
    if not target.exists():
        raise FileNotFoundError(f"target missing: {target}")

    dest = out_dir or (RUNS_DIR / "_frames")
    dest.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []
    for t in timestamps:
        out = dest / f"frame-{t:06.3f}s.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{t}", "-i", str(target),
             "-frames:v", "1", "-q:v", "2", str(out)],
            check=True, capture_output=True,
        )
        out_paths.append(out)
        console.print(f"[frame] t={t}s -> {out}")
    return out_paths
