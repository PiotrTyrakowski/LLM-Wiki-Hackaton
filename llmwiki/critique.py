"""Op 2b: critique by having Gemini watch BOTH the target and the agent's
rendered attempt in the same prompt and write editing-rule proposals directly.

No GPT in the editor path; no GPT in the critic path either. Gemini is the
analyst because it can compare the two videos visually in a single call.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import yaml
from google import genai
from google.genai import types as gtypes
from rich.console import Console

from . import gemini_vision
from .config import DEMO_TARGET, GEMINI_API_KEY, GEMINI_MODEL, RUNS_DIR, WIKI_DIR
from .prompts import CUTS_PROMPT
from .redis_use import publish_event
from .wiki import append_log, parse_frontmatter

console = Console()

CUT_LINE_RE = re.compile(r"t\s*=\s*([\d.:]+)")


def _parse_cuts(text: str) -> list[float]:
    out: list[float] = []
    for line in text.splitlines():
        m = CUT_LINE_RE.search(line)
        if not m:
            continue
        raw = m.group(1)
        parts = raw.split(".")
        try:
            if len(parts) == 3:
                m_, s_, ms_ = parts
                out.append(int(m_) * 60 + int(s_) + int(ms_) / 1000.0)
            else:
                out.append(float(raw))
        except Exception:
            continue
    return sorted(set(round(x, 3) for x in out))


def cut_f1(agent: list[float], target: list[float], tol: float = 0.8) -> dict[str, float]:
    matched: set[int] = set()
    tp = 0
    for a in agent:
        for i, g in enumerate(target):
            if i in matched:
                continue
            if abs(a - g) <= tol:
                tp += 1
                matched.add(i)
                break
    p = tp / max(len(agent), 1)
    r = tp / max(len(target), 1)
    f1 = 2 * p * r / max(p + r, 1e-9)
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3),
            "agent_n": len(agent), "target_n": len(target), "matched": tp}


def _read_obs(kind: str) -> str:
    obs_root = WIKI_DIR / "observations"
    if not obs_root.exists():
        return ""
    dirs = [d for d in obs_root.iterdir() if d.is_dir()]
    if not dirs:
        return ""
    latest = max(dirs, key=lambda d: d.stat().st_mtime)
    p = latest / f"{kind}.md"
    if not p.exists():
        return ""
    _, body = parse_frontmatter(p.read_text())
    return body


def _read_target_cuts() -> list[float]:
    return _parse_cuts(_read_obs("cuts"))


JUDGE_PROMPT = """You are watching TWO short videos side by side:

  VIDEO_A = the human-edited target.
  VIDEO_B = an automated agent's recreation attempt, made from placeholder assets.

Both are ~10 seconds. Your job: identify what the AGENT did poorly relative to the human, and write concrete editing rules the agent should learn next time.

For each meaningful mismatch, write ONE rule. Each rule:
- names the SKILL it belongs to (one of: cut-detection, broll-selection, pacing, transitions, on-screen-text).
- is a short imperative sentence with at least one numeric anchor (seconds, count, color, etc.).
- cites specific timestamps as evidence (compare A vs B at @t=...s).

Output ONLY valid YAML (no fences, no prose, no markdown):

proposals:
  - skill: broll-selection
    rule: "Cut to b-roll between 1.9s and 4.3s when the speaker introduces multiple sauna types."
    evidence: "@1.9-4.3s VIDEO_A cuts to stacked b-roll cards on a teal grid; VIDEO_B stays on speaker."
  - skill: on-screen-text
    rule: "Use a turquoise pill with yellow accent on a key noun between 6.9s and 9.3s."
    evidence: "VIDEO_A: 'NOT ALL SAUNAS ARE CREATED EQUAL' pill 6.9-9.3s; VIDEO_B: no styled text."
"""


async def _gemini_dual_critique(target_path: Path, attempt_path: Path, run_slug: str) -> list[dict[str, str]]:
    """Upload both videos to Gemini and ask for editing rules in one call."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    target_upload = await gemini_vision.upload_video(target_path, run_slug)
    attempt_upload = await gemini_vision.upload_video(attempt_path, run_slug)
    parts = [
        gtypes.Part.from_text(text="Below: VIDEO_A is the human target, VIDEO_B is the agent's attempt."),
        gtypes.Part.from_uri(file_uri=target_upload["uri"], mime_type=target_upload["mime_type"]),
        gtypes.Part.from_uri(file_uri=attempt_upload["uri"], mime_type=attempt_upload["mime_type"]),
        gtypes.Part.from_text(text=JUDGE_PROMPT),
    ]
    resp = await asyncio.to_thread(
        client.models.generate_content,
        model=GEMINI_MODEL,
        contents=[gtypes.Content(role="user", parts=parts)],
    )
    text = (resp.text or "").strip().strip("`")
    if text.startswith("yaml"):
        text = text[4:].lstrip()
    (RUNS_DIR / run_slug / "judge_raw.txt").write_text(text)
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data.get("proposals", []) or []
        return []
    except Exception as exc:
        console.print(f"[judge] yaml parse failed: {exc}; raw=\n{text[:500]}")
        return []


async def _extract_agent_cuts(attempt_path: Path, run_slug: str) -> list[float]:
    upload = await gemini_vision.upload_video(attempt_path, run_slug)
    answer = await gemini_vision.ask(upload, CUTS_PROMPT)
    (RUNS_DIR / run_slug / "agent_cuts.md").write_text(answer)
    return _parse_cuts(answer)


async def critique(run_slug: str) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_slug
    attempt_path = run_dir / "attempt.mp4"
    if not attempt_path.exists():
        raise FileNotFoundError(f"attempt.mp4 missing: {attempt_path}")
    target_path = DEMO_TARGET

    console.rule(f"[bold yellow]Critique {run_slug} — Gemini watches BOTH videos")
    publish_event("critique_start", {"slug": run_slug})

    target_cuts = _read_target_cuts()
    console.print(f"[critique] target cuts: n={len(target_cuts)}")
    agent_cuts = await _extract_agent_cuts(attempt_path, run_slug)
    console.print(f"[critique] agent cuts: n={len(agent_cuts)}")
    scores = cut_f1(agent_cuts, target_cuts)
    console.print(f"[critique] scores: {scores}")

    console.print("[critique] asking Gemini to compare both videos…")
    proposals = await _gemini_dual_critique(target_path, attempt_path, run_slug)
    console.print(f"[critique] {len(proposals)} proposals")

    out = {
        "scores": scores,
        "agent_cuts": agent_cuts,
        "target_cuts": target_cuts,
        "proposals": proposals,
    }
    (run_dir / "critique.json").write_text(json.dumps(out, indent=2))

    md = [
        f"# Critique for {run_slug}",
        "",
        f"## Scores",
        f"- precision: **{scores['precision']}**",
        f"- recall: **{scores['recall']}**",
        f"- f1: **{scores['f1']}**",
        f"- matched: {scores['matched']} of {scores['target_n']}",
        "",
        f"## Agent cuts ({len(agent_cuts)})",
        f"`{agent_cuts}`",
        "",
        f"## Target cuts ({len(target_cuts)})",
        f"`{target_cuts}`",
        "",
        f"## Proposals ({len(proposals)})",
        "",
    ]
    for p in proposals:
        md.append(f"- **{p.get('skill','?')}** — {p.get('rule','')}\n  - evidence: {p.get('evidence','')}")
    (run_dir / "critique.md").write_text("\n".join(md) + "\n")

    publish_event("critique_done", {"slug": run_slug, "f1": scores["f1"], "proposals": len(proposals)})
    append_log(f"critique | slug={run_slug} | f1={scores['f1']} | proposals={len(proposals)}")
    return out
