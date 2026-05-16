"""Inspect data/demo/source/ — produce a metadata catalog the agent can reason over.

For each source clip: duration via ffprobe; one-sentence description via Gemini (cached).
Optionally embed the description and upsert into Redis vector index.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from openai import OpenAI

from . import gemini_vision
from .config import DEMO_SOURCE_DIR, LLM_API_KEY, RUNS_DIR
from .redis_use import ensure_clip_index, upsert_clip

OPENAI = OpenAI(api_key=LLM_API_KEY) if LLM_API_KEY else None

CLIP_DESC_PROMPT = (
    "Describe this short video clip in ONE sentence focused on what an editor would care about: "
    "who/what is visible, what they are doing, and the emotional/energetic tone. "
    "Do NOT mention timestamps. 25 words max."
)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def _cache_path(path: Path) -> Path:
    p = RUNS_DIR / "_source_cache" / f"{path.stem}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


async def _describe(path: Path) -> str:
    cache = _cache_path(path)
    if cache.exists():
        return json.loads(cache.read_text())["description"]
    if not path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}:
        desc = f"Asset {path.name}"
    else:
        try:
            upload = await gemini_vision.upload_video(path, "_source_cache")
            desc = (await gemini_vision.ask(upload, CLIP_DESC_PROMPT)).strip()
        except Exception as exc:
            desc = f"{path.name} (description unavailable: {exc})"
    cache.write_text(json.dumps({"description": desc}))
    return desc


def _embed(text: str) -> np.ndarray:
    if not OPENAI:
        return np.zeros(1536, dtype=np.float32)
    r = OPENAI.embeddings.create(model="text-embedding-3-small", input=text)
    return np.asarray(r.data[0].embedding, dtype=np.float32)


async def catalog(source_dir: Path | None = None, *, embed: bool = True) -> list[dict[str, Any]]:
    src = Path(source_dir) if source_dir else DEMO_SOURCE_DIR
    paths = sorted(p for p in src.iterdir() if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"})
    if embed:
        ensure_clip_index(dim=1536)

    out = []
    sem = asyncio.Semaphore(3)

    async def _one(p: Path) -> dict[str, Any]:
        async with sem:
            duration = ffprobe_duration(p)
            description = await _describe(p)
            kind = "broll" if "broll" in p.stem.lower() else "primary"
            if embed:
                vec = _embed(description)
                upsert_clip(
                    clip_id=p.stem,
                    name=p.name,
                    kind=kind,
                    duration=duration,
                    description=description,
                    embedding=vec,
                )
            return {
                "id": p.stem,
                "path": str(p),
                "relpath": str(p.relative_to(src.parent)),
                "name": p.name,
                "kind": kind,
                "duration_s": duration,
                "description": description,
            }

    out = await asyncio.gather(*[_one(p) for p in paths])
    return list(out)
