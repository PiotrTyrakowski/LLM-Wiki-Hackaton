"""Op 2b: critique the rendered attempt against the target's observations.

The editor (Claude Code) hand-codes Hero.tsx, so we don't have a JSON EDL to
inspect anymore. Instead we ask Gemini to look at the rendered MP4 and tell us
where its cuts are, then compare to the target's cuts observation. We also use
GPT-4o-mini *only* as a critic — to turn the mismatch into editing-rule
proposals. GPT is never the editor; only the analyst.
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

from . import gemini_vision
from .config import DEMO_TARGET, LLM_API_KEY, LLM_MODEL, RUNS_DIR, WIKI_DIR
from .prompts import CUTS_PROMPT
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


JUDGE_PROMPT = """You are an editorial critic. The agent rendered a video to mimic the structure of a human edit. You will be given:

- AGENT_CUTS: cut timestamps Gemini detected in the agent's rendered video.
- TARGET_CUTS: cut timestamps from the human edit.
- TARGET_BROLL_OBSERVATIONS: where the human placed b-roll moments.
- TARGET_TEXT_OBSERVATIONS: where the human placed on-screen text.

For each meaningful mismatch, write ONE concrete editing rule the agent should learn. Each rule:
- names the SKILL it belongs to (one of: cut-detection, broll-selection, pacing, transitions, on-screen-text).
- is a short imperative sentence with at least one numeric anchor.
- cites specific timestamps as evidence.

Output ONLY valid YAML (no fences, no prose):

proposals:
  - skill: broll-selection
    rule: "Cut to b-roll at 1.5-4.0s when the speaker introduces sauna health claims."
    evidence: "@t=1.5s human cut to b-roll; agent stayed on speaker"
  - skill: on-screen-text
    rule: "Use a turquoise pill with yellow accent on the keyword 'SAUNAS' between 6.9s and 9.3s."
    evidence: "human used 'NOT ALL SAUNAS ARE CREATED EQUAL' pill 6.9-9.3s"
"""


async def _judge(agent_cuts: list[float], target_cuts: list[float], broll_obs: str, text_obs: str) -> list[dict[str, str]]:
    if not OPENAI:
        return []
    user = (
        f"AGENT_CUTS={agent_cuts}\n"
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

    console.rule(f"[bold yellow]Critique {run_slug}")
    publish_event("critique_start", {"slug": run_slug})

    target_cuts = _read_target_cuts()
    console.print(f"[critique] target cuts: n={len(target_cuts)}")
    agent_cuts = await _extract_agent_cuts(attempt_path, run_slug)
    console.print(f"[critique] agent cuts: n={len(agent_cuts)}")

    scores = cut_f1(agent_cuts, target_cuts)
    console.print(f"[critique] scores: {scores}")

    broll_obs = _read_obs("broll")
    text_obs = _read_obs("text")
    proposals = await _judge(agent_cuts, target_cuts, broll_obs, text_obs)
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
