"""Op 2b: critique an attempt against the target.

In the layered-EDL model the agent's "cuts" are the moments where an overlay
appears or disappears. We score the agent's transition timestamps against the
target's observed cut timestamps from the latest ingest.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import yaml
from openai import OpenAI
from rich.console import Console

from .config import LLM_API_KEY, LLM_MODEL, RUNS_DIR, WIKI_DIR
from .redis_use import publish_event
from .wiki import append_log, parse_frontmatter

console = Console()
OPENAI = OpenAI(api_key=LLM_API_KEY) if LLM_API_KEY else None

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


def _agent_transitions_from_edl(edl: dict[str, Any]) -> list[float]:
    """Treat each overlay start and end as an agent transition."""
    out: list[float] = []
    for ov in edl.get("overlays", []):
        start = float(ov.get("start_s", 0))
        out.append(start)
        end = start + float(ov.get("duration_s", 0))
        if end > start:
            out.append(end)
    return sorted(set(round(x, 3) for x in out))


JUDGE_PROMPT = """You are an editorial critic. The agent built an edit using placeholder assets to mimic the structure of a human edit.

You are given:
- AGENT_EDL: the agent's overlay schedule (list of {source, start_s, duration_s}).
- TARGET_CUTS: timestamps where the human cut to b-roll/image.
- TARGET_BROLL_OBSERVATIONS: where the human placed b-roll moments.
- TARGET_TEXT_OBSERVATIONS: where the human placed on-screen text.

For each meaningful mismatch, write ONE concrete editing rule the agent should learn. The rule must:
- name the SKILL it belongs to (one of: cut-detection, broll-selection, pacing, transitions, on-screen-text).
- be a short imperative sentence with a numeric anchor (e.g. "Insert a b-roll between 2.0s and 3.5s when the speaker introduces a new concept.").
- cite specific timestamps as evidence.

Output ONLY valid YAML matching this schema (no fences, no prose):
proposals:
  - skill: broll-selection
    rule: "<rule>"
    evidence: "@t=<sec>s human had b-roll but agent stayed on avatar"
  - skill: cut-detection
    rule: "<rule>"
    evidence: "..."
"""


async def _judge(edl: dict[str, Any], target_cuts: list[float], broll_obs: str, text_obs: str) -> list[dict[str, str]]:
    assert OPENAI is not None
    user = (
        f"AGENT_EDL_OVERLAYS={json.dumps(edl.get('overlays', []), indent=2)}\n"
        f"AGENT_EDL_TEXT={json.dumps(edl.get('text_overlays', []), indent=2)}\n"
        f"TARGET_CUTS={target_cuts}\n\n"
        f"TARGET_BROLL_OBSERVATIONS:\n{broll_obs[:1500]}\n\n"
        f"TARGET_TEXT_OBSERVATIONS:\n{text_obs[:1500]}\n"
    )
    resp = await asyncio.to_thread(
        OPENAI.chat.completions.create,
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    text = (resp.choices[0].message.content or "").strip().strip("`")
    if text.startswith("yaml"):
        text = text[4:].lstrip()
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data.get("proposals", []) or []
        return []
    except Exception as exc:
        console.print(f"[judge] yaml parse failed: {exc}; raw=\n{text[:500]}")
        return []


async def critique(run_slug: str) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_slug
    edl_path = run_dir / "edl.json"
    if not edl_path.exists():
        raise FileNotFoundError(f"edl.json missing: {edl_path}")
    edl = json.loads(edl_path.read_text())

    console.rule(f"[bold yellow]Critique {run_slug}")
    publish_event("critique_start", {"slug": run_slug})

    target_cuts = _read_target_cuts()
    if not target_cuts:
        console.print("[critique] no cuts observation found in wiki/observations/ — was ingest run?")
    agent_transitions = _agent_transitions_from_edl(edl)
    scores = cut_f1(agent_transitions, target_cuts)
    console.print(f"[critique] scores: {scores}")

    broll_obs = _read_obs("broll")
    text_obs = _read_obs("text")
    proposals = await _judge(edl, target_cuts, broll_obs, text_obs)
    console.print(f"[critique] {len(proposals)} proposals")

    out = {
        "scores": scores,
        "agent_transitions": agent_transitions,
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
        f"## Agent transitions ({len(agent_transitions)})",
        f"`{agent_transitions}`",
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
