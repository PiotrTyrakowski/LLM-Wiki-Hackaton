"""Op 1: Ingest target video. Run 5 Gemini prompts -> wiki/observations -> Redis session -> graph distillation."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from rich.console import Console

from . import gemini_vision, memory
from .config import COGNEE_DATASET, DEMO_TARGET, SKILLS_DIR, ensure_dirs
from .prompts import INGEST_PROMPTS
from .redis_use import publish_event
from .wiki import append_log, now_iso, write_observation

console = Console()


async def ingest(target_path: Path | None = None, run_slug: str | None = None) -> str:
    target = Path(target_path) if target_path else DEMO_TARGET
    if not target.exists():
        raise FileNotFoundError(f"Target video not found: {target}")

    ensure_dirs()
    run_slug = run_slug or f"ingest-{now_iso()}"
    session_id = run_slug

    console.rule(f"[bold green]Ingest {target.name} (slug={run_slug})")
    publish_event("ingest_start", {"slug": run_slug, "target": str(target)})

    # 1. Upload to Gemini Files API
    console.print(f"[upload] {target.name}")
    upload = await gemini_vision.upload_video(target, run_slug)
    console.print(f"[upload] ready: {upload['uri']}")

    # 2. Fire all 5 prompts in parallel
    async def _ask_and_write(kind: str, prompt: str) -> str:
        console.print(f"[gemini→{kind}] asking…")
        answer = await gemini_vision.ask(upload, prompt)
        path = write_observation(run_slug, kind, prompt, answer)
        console.print(f"[wrote] {path.relative_to(path.parent.parent.parent)}")
        # Per-observation session-memory write -> Redis
        console.print(f"[session→redis] {kind}.md")
        await memory.remember_session(answer, session_id=session_id)
        publish_event("observation", {"kind": kind, "preview": answer[:200]})
        return answer

    results = await asyncio.gather(*[
        _ask_and_write(kind, prompt) for kind, prompt in INGEST_PROMPTS.items()
    ])

    # 3. Distill a summary to the permanent graph
    distilled = (
        f"Target video {target.name} editing analysis. "
        f"Observations across cuts/pacing/broll/motion/text — see wiki/observations/{run_slug}/."
    )
    console.print("[graph←distill] summary")
    await memory.remember_permanent(distilled, dataset_name=COGNEE_DATASET)

    # 4. Push skill pack (idempotent)
    console.print("[graph←distill] my_skills/ as skills")
    try:
        await memory.ingest_skills()
    except Exception as exc:
        console.print(f"[warn] skill ingest: {exc}")

    append_log(f"ingest | slug={run_slug} | observations={len(results)} | target={target.name}")
    publish_event("ingest_done", {"slug": run_slug, "observations": len(results)})
    console.rule("[bold green]Ingest complete")
    return run_slug
