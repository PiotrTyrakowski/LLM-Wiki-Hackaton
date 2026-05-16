"""Gemini vision: upload video chunks via Files API, ask free-text prompts, SHA1-cache results.

Lifted in spirit from the recreator's TS implementation.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types as gtypes

from .config import GEMINI_API_KEY, GEMINI_MODEL, RUNS_DIR


def _client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _upload_cache_path(run_slug: str, sha1: str) -> Path:
    p = RUNS_DIR / run_slug / "uploads" / f"{sha1}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


async def upload_video(path: Path, run_slug: str) -> dict[str, Any]:
    """Upload a video file to Gemini Files API. Returns {name, uri, mime_type, sha1, uploaded_at}.

    Caches result on disk so re-runs hit the cache (24h TTL).
    """
    sha1 = _sha1(path)
    cache = _upload_cache_path(run_slug, sha1)
    if cache.exists():
        meta = json.loads(cache.read_text())
        if (time.time() - meta.get("uploaded_at_epoch", 0)) < 23 * 3600:
            return meta

    client = _client()
    uploaded = await asyncio.to_thread(client.files.upload, file=str(path))
    # Poll until ACTIVE
    deadline = time.time() + 120
    while uploaded.state.name != "ACTIVE":
        if time.time() > deadline:
            raise TimeoutError(f"Gemini file did not become ACTIVE in 120s: {uploaded.state}")
        await asyncio.sleep(2)
        uploaded = await asyncio.to_thread(client.files.get, name=uploaded.name)

    meta = {
        "name": uploaded.name,
        "uri": uploaded.uri,
        "mime_type": uploaded.mime_type or "video/mp4",
        "sha1": sha1,
        "uploaded_at_epoch": int(time.time()),
    }
    cache.write_text(json.dumps(meta, indent=2))
    return meta


async def ask(video_meta: dict[str, Any], prompt: str) -> str:
    """Send (video_uri, prompt) to Gemini, return raw text."""
    client = _client()
    parts: list[Any] = [
        gtypes.Part.from_uri(file_uri=video_meta["uri"], mime_type=video_meta["mime_type"]),
        gtypes.Part.from_text(text=prompt),
    ]
    resp = await asyncio.to_thread(
        client.models.generate_content,
        model=GEMINI_MODEL,
        contents=[gtypes.Content(role="user", parts=parts)],
    )
    return (resp.text or "").strip()
