"""Op 2c: Karpathy-pattern self-improvement.

For each *skill* with at least one proposal:
  1. Record one SkillRunEntry into cognee with apply=False (proposes a rewrite).
  2. Call improve_skill(...apply=True) when cognee returns a proposal_id.
  3. ALWAYS reconcile the SKILL.md on disk via an OpenAI rewrite that ingests
     ALL proposals for that skill at once (so we get dedup + integration, not
     N duplicate rules).

Batching by skill is critical: when proposals are processed one-at-a-time the
rewriter has no view of prior additions and tends to add the same rule N times.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import UUID

from openai import OpenAI
from rich.console import Console

import cognee
from cognee.memory import SkillRunEntry
from cognee.modules.memify.skill_improvement import improve_skill
from cognee.modules.pipelines.layers.resolve_authorized_user_datasets import resolve_authorized_user_datasets

from .config import COGNEE_DATASET, LLM_API_KEY, LLM_MODEL, RUNS_DIR, SKILLS, SKILLS_DIR
from .redis_use import publish_event
from .wiki import append_log

console = Console()
OPENAI = OpenAI(api_key=LLM_API_KEY) if LLM_API_KEY else None


def _skill_path(skill: str) -> Path:
    return SKILLS_DIR / skill / "SKILL.md"


def _read_skill_text(skill: str) -> str:
    p = _skill_path(skill)
    return p.read_text() if p.exists() else ""


def _write_skill_text(skill: str, text: str) -> None:
    p = _skill_path(skill)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


REWRITE_PROMPT = """You are maintaining a SKILL.md file for a video-editing agent. Integrate the new lessons below into the file.

CRITICAL constraints:
- Preserve the frontmatter (the --- block) EXACTLY.
- Preserve the title (the # heading) and the existing "## Rules" / "## Output contract" sections.
- Preserve existing numbered rules in order, then APPEND new rules continuing the numbering.
- DEDUP: if a new lesson already overlaps with an existing rule, do NOT add it. Instead, optionally strengthen the wording of the existing rule.
- Each new rule must be ONE short imperative sentence with at least one numeric anchor.
- Maximum 3 new rules total. Pick the most distinct and most evidence-backed lessons.
- Preserve the "## Output contract" section verbatim at the end.

Output ONLY the new full file contents — no prose, no markdown fences.
"""


async def _rewrite_skill(skill: str, proposals: list[dict[str, str]]) -> str:
    assert OPENAI is not None
    before = _read_skill_text(skill)
    if not proposals:
        return before
    lesson_block = "\n".join(
        f"- rule: {p.get('rule','').strip()}\n  evidence: {p.get('evidence','').strip()}"
        for p in proposals
    )
    user = (
        f"Skill: {skill}\n\n"
        f"Current SKILL.md:\n```\n{before}\n```\n\n"
        f"New lessons ({len(proposals)} total, dedup as needed, max 3 new rules):\n{lesson_block}\n"
    )
    resp = await asyncio.to_thread(
        OPENAI.chat.completions.create,
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": REWRITE_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    out = (resp.choices[0].message.content or before).strip()
    # Strip any accidental fences
    if out.startswith("```"):
        out = "\n".join(line for line in out.splitlines() if not line.startswith("```"))
    return out + "\n"


async def self_improve(run_slug: str) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_slug
    critique_path = run_dir / "critique.json"
    if not critique_path.exists():
        raise FileNotFoundError(f"critique.json missing — run `llmwiki critique {run_slug}` first")
    critique = json.loads(critique_path.read_text())
    score = float(critique["scores"]["f1"])
    proposals: list[dict[str, str]] = critique.get("proposals", [])
    if not proposals:
        console.print("[self-improve] no proposals — nothing to do")
        return {"changed": 0}

    console.rule(f"[bold magenta]Self-improve {run_slug}  f1={score}")
    publish_event("self_improve_start", {"slug": run_slug, "proposals": len(proposals)})

    # Group by skill — one rewrite per skill, not per proposal.
    by_skill: dict[str, list[dict[str, str]]] = defaultdict(list)
    for p in proposals:
        skill = (p.get("skill") or "").strip()
        if skill in SKILLS:
            by_skill[skill].append(p)
        else:
            console.print(f"[self-improve] skip unknown skill: {skill!r}")
    console.print(f"[self-improve] {sum(len(v) for v in by_skill.values())} proposals across {len(by_skill)} skills")

    # Resolve dataset + user once for cognee improve_skill.
    user = None
    dataset = None
    try:
        rem = await cognee.remember(
            f"Self-improve trigger for run {run_slug}",
            dataset_name=COGNEE_DATASET,
        )
        ds_id = UUID(rem.dataset_id) if hasattr(rem, "dataset_id") else None
        if ds_id:
            user, datasets = await resolve_authorized_user_datasets(ds_id)
            if datasets:
                dataset = datasets[0]
    except Exception as exc:
        console.print(f"[self-improve] dataset resolve skipped: {exc}")

    changes: list[dict[str, Any]] = []

    for skill, props in by_skill.items():
        before = _read_skill_text(skill)
        publish_event("skill_propose", {"skill": skill, "n_proposals": len(props)})

        # --- Record one cognee SkillRunEntry (summary) for this skill ---
        applied_via = "fallback"
        try:
            summary_text = "; ".join(p.get("rule", "") for p in props[:3])
            evidence_text = "; ".join(p.get("evidence", "") for p in props[:3])
            proposal_result = await cognee.remember(
                SkillRunEntry(
                    selected_skill_id=skill,
                    task_text=f"Edit data/demo/source/ to match the human edit (run {run_slug})",
                    result_summary=f"Critique: {summary_text}",
                    success_score=score,
                    feedback=-1.0 if score < 0.7 else 1.0,
                ),
                dataset_name=COGNEE_DATASET,
                session_id=run_slug,
                skill_improvement={
                    "skill_name": skill,
                    "apply": False,
                    "score_threshold": 0.9,
                },
            )
            proposal_id = None
            for item in (getattr(proposal_result, "items", None) or []):
                if isinstance(item, dict) and item.get("kind") == "skill_improvement_proposal":
                    proposal_id = item.get("proposal_id")
                    break
            if proposal_id and dataset is not None and user is not None:
                await improve_skill(
                    skill,
                    dataset=dataset,
                    user=user,
                    proposal_id=proposal_id,
                    apply=True,
                )
                applied_via = "cognee"
        except Exception as exc:
            console.print(f"[self-improve] cognee skill_improvement failed for {skill}: {exc}")

        # --- Batched LLM rewrite of the SKILL.md file (always run for on-disk diff) ---
        new_text = await _rewrite_skill(skill, props)
        if new_text and new_text.strip() != before.strip():
            _write_skill_text(skill, new_text)
            publish_event("skill_apply", {"skill": skill, "via": applied_via, "n_proposals": len(props)})
            changes.append({
                "skill": skill,
                "applied_via": applied_via,
                "n_proposals": len(props),
                "proposals": props,
                "before": before,
                "after": new_text,
            })
        else:
            console.print(f"[self-improve] no on-disk change for {skill}")

    # Persist skill_diff.md
    diff_md = [f"# Skill diff after run {run_slug}",
               f"_F1 = {score} · {sum(len(v) for v in by_skill.values())} proposals integrated across {len(changes)} skills_",
               ""]
    for change in changes:
        diff_md += [
            f"## {change['skill']} (via {change['applied_via']}, {change['n_proposals']} proposals)",
            "",
            "**Sample lessons that drove this rewrite:**",
        ]
        for p in change["proposals"][:3]:
            diff_md.append(f"- _{p.get('rule','')}_ — evidence: `{p.get('evidence','')}`")
        diff_md += [
            "",
            "### Before",
            "```markdown",
            change["before"].strip(),
            "```",
            "",
            "### After",
            "```markdown",
            change["after"].strip(),
            "```",
            "",
        ]
    (run_dir / "skill_diff.md").write_text("\n".join(diff_md) + "\n")
    publish_event("self_improve_done", {"slug": run_slug, "changed": len(changes)})
    append_log(f"self-improve | slug={run_slug} | changed={len(changes)} of {len(by_skill)} skills")

    # Re-ingest the updated my_skills/ into cognee so future recalls see them
    try:
        await cognee.remember(
            str(SKILLS_DIR),
            dataset_name=COGNEE_DATASET,
            content_type="skills",
        )
    except Exception as exc:
        console.print(f"[self-improve] re-ingest skills skipped: {exc}")

    console.rule(f"[bold magenta]Self-improve done  changed={len(changes)}")
    return {"changed": len(changes), "changes": changes}
