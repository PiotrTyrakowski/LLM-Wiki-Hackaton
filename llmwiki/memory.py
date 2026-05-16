"""Cognee wrappers — remember/recall/forget — plus skill-pack ingestion.

Redis-as-session-memory is the hackathon's headline pattern. Everything in this
module either writes to the Redis-backed session (with `session_id=...`) or
the permanent Cognee graph (without `session_id`). Don't bypass.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cognee

from .config import COGNEE_DATASET, SKILLS_DIR
from .redis_use import publish_event


async def remember_session(text: str, session_id: str) -> None:
    """Write a per-run observation/thought to Redis-backed session memory."""
    await cognee.remember(text, session_id=session_id)
    publish_event("session_remember", {"session_id": session_id, "preview": text[:120]})


async def remember_permanent(text: str, *, dataset_name: str | None = None) -> None:
    """Distill into the permanent Cognee graph."""
    if dataset_name:
        await cognee.remember(text, dataset_name=dataset_name)
    else:
        await cognee.remember(text)
    publish_event("graph_remember", {"preview": text[:120]})


async def ingest_skills() -> Any:
    """Push my_skills/ into the graph as skills. Returns the cognee response."""
    publish_event("skill_ingest", {"path": str(SKILLS_DIR)})
    result = await cognee.remember(
        str(SKILLS_DIR),
        dataset_name=COGNEE_DATASET,
        content_type="skills",
    )
    return result


async def ingest_file(path: Path, *, session_id: str | None = None) -> None:
    """Push an observation markdown into session memory or the graph."""
    text = path.read_text()
    if session_id:
        await remember_session(text, session_id=session_id)
    else:
        await remember_permanent(text, dataset_name=COGNEE_DATASET)


async def recall_session(query: str, session_id: str) -> list[Any]:
    return await cognee.recall(query, session_id=session_id)


async def recall_permanent(query: str) -> list[Any]:
    return await cognee.recall(query)


async def reset() -> None:
    """Wipe both stores. Use between demo runs."""
    try:
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
    except Exception as exc:
        print(f"[memory] prune skipped: {exc}")
