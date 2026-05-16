"""Op 2a: produce a layered EDL from a fixed placeholder palette + Gemini
observations of the human edit. Render via Remotion. The agent NEVER touches
the target's source pixels — it composes a fresh edit from avatar + b-roll +
image placeholders, structured to mimic the human edit's pacing/cuts.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from openai import OpenAI
from rich.console import Console

import cognee

from . import memory, sources
from .config import (
    COGNEE_DATASET,
    DEMO_SOURCE_DIR,
    LLM_API_KEY,
    LLM_MODEL,
    REMOTION_DIR,
    RUNS_DIR,
    SKILLS,
    SKILLS_DIR,
    WIKI_DIR,
    ensure_dirs,
)
from .edl import Edit
from .redis_use import publish_event
from .wiki import append_log, now_iso, parse_frontmatter

console = Console()
OPENAI = OpenAI(api_key=LLM_API_KEY) if LLM_API_KEY else None


def _load_skill_bodies() -> str:
    out = []
    for name in SKILLS:
        path = SKILLS_DIR / name / "SKILL.md"
        if path.exists():
            out.append(f"\n=== SKILL: {name} ===\n{path.read_text()}")
    return "\n".join(out)


def _load_latest_observations() -> dict[str, str]:
    obs_root = WIKI_DIR / "observations"
    if not obs_root.exists():
        return {}
    dirs = [d for d in obs_root.iterdir() if d.is_dir()]
    if not dirs:
        return {}
    latest = max(dirs, key=lambda d: d.stat().st_mtime)
    out: dict[str, str] = {}
    for f in latest.glob("*.md"):
        _, body = parse_frontmatter(f.read_text())
        out[f.stem] = body.strip()
    return out


async def _retrieve_lessons(query: str, session_id: str) -> str:
    pieces: list[str] = []
    try:
        sess = await cognee.recall(query, session_id=session_id)
        for r in sess or []:
            text = getattr(r, "answer", None) or getattr(r, "text", None) or str(r)
            pieces.append(f"[session] {text}")
    except Exception as exc:
        console.print(f"[recall-session] {exc}")
    try:
        perm = await cognee.recall(query)
        for r in perm or []:
            text = getattr(r, "answer", None) or getattr(r, "text", None) or str(r)
            pieces.append(f"[graph] {text}")
    except Exception as exc:
        console.print(f"[recall-graph] {exc}")
    return "\n".join(pieces[:8])


SYSTEM_PROMPT = """You are Cinegraph, a video-editing agent. You produce JSON Edit Decision Lists (EDLs) that the Remotion renderer turns into a finished video.

You are RECREATING THE STRUCTURE of a human-edited target video, but you may ONLY use placeholder assets — never the target's footage. Available placeholders:

PRIMARY (always playing, fills the canvas):
- avatar-16x9 — the speaker stand-in. Duration is long enough to cover the whole edit.

OVERLAYS (covers the avatar during their time range):
- broll1-16x9, broll2-16x9, broll3-16x9 — three short b-roll cutaways. Use to break long avatar-only stretches and at moments where the human used b-roll.
- image1-16x9, image2-16x9, image3-16x9 — three slide images. Use for diagrams, callouts, or moments where the human switched to a graphic.

TEXT OVERLAYS:
- Short on-screen text to reinforce key words. 2-6 words max each.

You will be given:
- The target duration in seconds (~10s).
- Observations extracted from the human edit (cuts, b-roll moments, on-screen text).
- Your current SKILL.md content.
- Optionally: lessons retrieved from your memory.

Produce a SINGLE JSON object matching this schema (no prose, no markdown fences):

{
  "fps": 30,
  "width": 1280,
  "height": 720,
  "duration_s": 10.0,
  "avatar": { "source": "avatar-16x9", "in_s": 0.0, "out_s": 10.0 },
  "overlays": [
    { "source": "broll1-16x9", "kind": "broll", "start_s": 2.5, "duration_s": 1.5 },
    { "source": "image1-16x9", "kind": "image", "start_s": 5.0, "duration_s": 2.0 }
  ],
  "text_overlays": [
    { "text": "infrared sauna", "start_s": 0.0, "duration_s": 2.0, "position": "bottom" }
  ]
}

Rules:
- Times in seconds. `start_s + duration_s` must be ≤ duration_s for every overlay.
- Overlays may overlap with text overlays, but two video overlays should NOT overlap each other.
- Place b-roll/image overlays at the timestamps the observations call out, when possible.
- Use 2-4 video overlays and 1-3 text overlays for a 10s edit.
- Use only the placeholder source ids listed above. NEVER reference anything else.
- Reply with ONLY the JSON.
"""


async def _call_llm(user_prompt: str) -> str:
    assert OPENAI is not None
    resp = await asyncio.to_thread(
        OPENAI.chat.completions.create,
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.35,
    )
    return resp.choices[0].message.content or "{}"


async def _generate_edl(observations: dict[str, str], skill_bodies: str, lessons: str, duration_s: float) -> Edit:
    obs_block = "\n".join(
        f"--- OBSERVATION: {kind} ---\n{text[:1500]}" for kind, text in observations.items()
    ) or "(no observations available; the agent has to infer structure)"
    user_prompt = (
        f"Target duration: {duration_s:.1f}s\n\n"
        f"Observations from the human edit:\n{obs_block}\n\n"
        f"Your current SKILL.md content:\n{skill_bodies}\n\n"
        f"Retrieved lessons (may be empty):\n{lessons or '(none)'}\n\n"
        f"Now produce the JSON EDL."
    )
    raw = await _call_llm(user_prompt)
    try:
        data = json.loads(raw)
        return Edit.model_validate(data)
    except Exception as exc:
        console.print(f"[edl-parse] first attempt failed: {exc}; retrying once")
        retry_prompt = user_prompt + f"\n\nYour previous answer failed validation: {exc}. Try again, JSON only."
        raw2 = await _call_llm(retry_prompt)
        data = json.loads(raw2)
        return Edit.model_validate(data)


def _write_run_files(run_slug: str, edit: Edit, clip_meta: list[dict[str, Any]], duration_s: float) -> Path:
    run_dir = RUNS_DIR / run_slug
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "edl.json").write_text(edit.model_dump_json(indent=2))
    (run_dir / "run.json").write_text(json.dumps({
        "slug": run_slug,
        "created_at": now_iso(),
        "duration_s": duration_s,
        "clip_meta": clip_meta,
    }, indent=2))
    return run_dir


def _render_remotion(run_slug: str) -> Path | None:
    run_dir = RUNS_DIR / run_slug
    edl_path = run_dir / "edl.json"
    out_path = run_dir / "attempt.mp4"
    if not REMOTION_DIR.exists():
        console.print("[render] remotion/ dir missing; skipping render")
        return None
    console.print("[render] starting Remotion render (720p, jpeg-quality 70)…")
    cmd = [
        "npx", "remotion", "render",
        "src/index.ts", "Main", str(out_path),
        f"--props={edl_path}",
        "--concurrency=2",
        "--jpeg-quality=70",
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
    no_lessons: bool = False,
    label: str = "v1",
    target_duration_s: float = 10.0,
) -> str:
    ensure_dirs()
    run_slug = f"attempt-{label}-{now_iso()}"
    session_id = run_slug
    console.rule(f"[bold cyan]Attempt {label} (slug={run_slug}, duration={target_duration_s}s)")
    publish_event("attempt_start", {"slug": run_slug, "label": label, "no_lessons": no_lessons})

    console.print("[catalog] inspecting placeholder palette (also indexed in Redis)…")
    clip_meta = await sources.catalog(source_dir or DEMO_SOURCE_DIR, embed=True)
    console.print(f"[catalog] {len(clip_meta)} placeholders indexed (Redis HNSW vector)")

    skill_bodies = _load_skill_bodies()
    observations = _load_latest_observations()
    console.print(f"[wiki] loaded {len(observations)} observation kinds from latest ingest")
    lessons = ""
    if not no_lessons:
        console.print("[recall] pulling lessons from cognee (session + graph)…")
        lessons = await _retrieve_lessons("editing rules for cuts pacing transitions broll on-screen text", session_id=session_id)
    else:
        console.print("[recall] skipped (--no-lessons)")

    console.print(f"[llm] {LLM_MODEL} -> generating EDL")
    edit = await _generate_edl(observations, skill_bodies, lessons, target_duration_s)
    console.print(f"[edl] overlays={len(edit.overlays)} text={len(edit.text_overlays)} duration={edit.duration_s}s")

    run_dir = _write_run_files(run_slug, edit, clip_meta, target_duration_s)
    publish_event("edl_ready", {"slug": run_slug, "overlays": len(edit.overlays), "text": len(edit.text_overlays)})

    await memory.remember_session(
        f"Attempt {label} produced an EDL: {len(edit.overlays)} video overlays, {len(edit.text_overlays)} text overlays, {edit.duration_s}s.",
        session_id=session_id,
    )

    rendered = _render_remotion(run_slug)
    if rendered:
        publish_event("render_done", {"slug": run_slug, "out": str(rendered)})

    append_log(f"attempt | slug={run_slug} | label={label} | no_lessons={no_lessons} | overlays={len(edit.overlays)}")
    console.rule("[bold cyan]Attempt complete")
    return run_slug
