"""Op 2a: render the agent's current edit.

The agent (Claude Code) writes/edits `remotion/src/Hero.tsx` between attempts.
This module ONLY renders that file. There is no LLM in the editor path — that
was the whole point: video editing is the human's (or Claude Code's) judgment,
not GPT's.

Flow:
  1. Snapshot the current Hero.tsx into the run dir (so we can diff later).
  2. Snapshot the current SKILL.md state.
  3. Render the Hero composition via Remotion.
  4. Push a "what I edited this run" summary into Redis session memory.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from . import memory
from .config import REMOTION_DIR, RUNS_DIR, SKILLS, SKILLS_DIR, ensure_dirs
from .redis_use import publish_event
from .wiki import append_log, now_iso

console = Console()


def _snapshot_state(run_dir: Path) -> None:
    """Snapshot Hero.tsx and the current SKILL.md state into the run dir."""
    hero = REMOTION_DIR / "src" / "Hero.tsx"
    if hero.exists():
        (run_dir / "Hero.snapshot.tsx").write_text(hero.read_text())
    skills_dest = run_dir / "skills_snapshot"
    skills_dest.mkdir(parents=True, exist_ok=True)
    for name in SKILLS:
        src = SKILLS_DIR / name / "SKILL.md"
        if src.exists():
            (skills_dest / f"{name}.md").write_text(src.read_text())


def _render_remotion(run_dir: Path) -> Path | None:
    out_path = run_dir / "attempt.mp4"
    if not REMOTION_DIR.exists():
        console.print("[render] remotion/ dir missing; skipping render")
        return None
    console.print("[render] starting Remotion render…")
    cmd = [
        "npx", "remotion", "render",
        "src/index.ts", "Hero", str(out_path),
        "--concurrency=2",
        "--jpeg-quality=80",
        "--log=warn",
    ]
    try:
        subprocess.run(cmd, cwd=str(REMOTION_DIR), check=True)
        console.print(f"[render] done -> {out_path}")
        return out_path
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        console.print(f"[render] failed: {exc}")
        return None


async def attempt(
    source_dir: Path | None = None,
    no_lessons: bool = False,  # accepted for CLI parity; no longer relevant
    label: str = "v1",
    target_duration_s: float = 10.0,
) -> str:
    """Render the current Hero.tsx composition as this attempt."""
    ensure_dirs()
    run_slug = f"attempt-{label}-{now_iso()}"
    session_id = run_slug
    console.rule(f"[bold cyan]Attempt {label} (slug={run_slug})")
    publish_event("attempt_start", {"slug": run_slug, "label": label})

    run_dir = RUNS_DIR / run_slug
    run_dir.mkdir(parents=True, exist_ok=True)
    _snapshot_state(run_dir)
    console.print(f"[snapshot] Hero.tsx + skills/ saved to {run_dir.relative_to(run_dir.parent.parent)}")

    rendered = _render_remotion(run_dir)
    if rendered:
        publish_event("render_done", {"slug": run_slug, "out": str(rendered)})

    # Session memory: what the editor (Claude Code) shipped this round.
    await memory.remember_session(
        f"Attempt {label} (slug={run_slug}): the editor rendered the current Hero.tsx.",
        session_id=session_id,
    )

    append_log(f"attempt | slug={run_slug} | label={label}")
    console.rule("[bold cyan]Attempt complete")
    return run_slug
