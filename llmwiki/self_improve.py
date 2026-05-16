"""Op 2c: Karpathy-pattern self-improvement, Cognee-pure.

The ONLY thing that rewrites the SKILL.md files on disk is
`cognee.improve_skill(apply=True)`. No OpenAI fallback. No belt-and-
suspenders LLM rewrite. If Cognee's pipeline fails to produce a proposal
or fails to apply it, we log loudly and leave the file untouched.

The video editor is Claude Code (the human-in-the-loop on this codebase).
This module never touches Hero.tsx.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import UUID

from rich.console import Console

import cognee
from cognee.memory import SkillRunEntry
from cognee.modules.memify.skill_improvement import improve_skill
from cognee.modules.pipelines.layers.resolve_authorized_user_datasets import resolve_authorized_user_datasets

from .config import COGNEE_DATASET, RUNS_DIR, SKILLS, SKILLS_DIR
from .redis_use import publish_event
from .wiki import append_log


console = Console()


def _skill_path(skill: str) -> Path:
    return SKILLS_DIR / skill / "SKILL.md"


def _read_skill_text(skill: str) -> str:
    p = _skill_path(skill)
    return p.read_text() if p.exists() else ""


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

    console.rule(f"[bold magenta]Self-improve {run_slug}  f1={score}  (Cognee-pure)")
    publish_event("self_improve_start", {"slug": run_slug, "proposals": len(proposals)})

    # Group proposals by skill so each skill gets ONE SkillRunEntry per run.
    by_skill: dict[str, list[dict[str, str]]] = defaultdict(list)
    for p in proposals:
        skill = (p.get("skill") or "").strip()
        if skill in SKILLS:
            by_skill[skill].append(p)
        else:
            console.print(f"[self-improve] skip unknown skill: {skill!r}")

    # Resolve user + dataset once (needed by improve_skill).
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
        console.print(f"[self-improve] dataset={getattr(dataset,'id',None)}, user={getattr(user,'id',None)}")
    except Exception as exc:
        console.print(f"[self-improve] dataset resolve failed: {exc}")

    changes: list[dict[str, Any]] = []

    for skill, props in by_skill.items():
        before = _read_skill_text(skill)
        publish_event("skill_propose", {"skill": skill, "n_proposals": len(props)})

        summary = "; ".join(p.get("rule", "") for p in props[:3])
        evidence = "; ".join(p.get("evidence", "") for p in props[:3])

        proposal_id = None
        proposal_payload: dict[str, Any] | None = None
        try:
            proposal_result = await cognee.remember(
                SkillRunEntry(
                    selected_skill_id=skill,
                    task_text=f"Edit data/demo/source/ to match the human edit (run {run_slug})",
                    result_summary=f"Critique: {summary}",
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
            items = getattr(proposal_result, "items", None) or []
            # Dump every item so we can inspect what cognee actually stores.
            try:
                (run_dir / f"_cognee_items_{skill}.json").write_text(
                    json.dumps([i if isinstance(i, dict) else str(i) for i in items], indent=2, default=str)
                )
            except Exception:
                pass
            for item in items:
                if isinstance(item, dict) and item.get("kind") == "skill_improvement_proposal":
                    proposal_id = item.get("proposal_id")
                    proposal_payload = item
                    break
            console.print(f"[self-improve] {skill}: SkillRunEntry sent; proposal_id={proposal_id}")
        except Exception as exc:
            console.print(f"[self-improve] SkillRunEntry failed for {skill}: {exc}")
            continue

        if not proposal_id:
            console.print(f"[self-improve] {skill}: no proposal_id returned (score above threshold? skipping).")
            continue
        if dataset is None or user is None:
            console.print(f"[self-improve] {skill}: missing dataset/user; cannot apply.")
            continue

        try:
            await improve_skill(
                skill,
                dataset=dataset,
                user=user,
                proposal_id=proposal_id,
                apply=True,
            )
        except Exception as exc:
            console.print(f"[self-improve] improve_skill(apply=True) failed for {skill}: {exc}")
            continue

        after_disk = _read_skill_text(skill)

        # Cognee 1.1's improve_skill commits to the graph but doesn't
        # always rewrite the file on disk. Pull the post-improve graph
        # state via recall so the viz can show "before (disk) vs after
        # (cognee graph)".
        after_graph = ""
        try:
            recall_results = await cognee.recall(
                f"What are the current rules in the '{skill}' editing skill, in full?",
            )
            chunks: list[str] = []
            for r in recall_results or []:
                t = getattr(r, "answer", None) or getattr(r, "text", None) or str(r)
                if t:
                    chunks.append(t)
            after_graph = "\n\n".join(chunks).strip()
        except Exception as exc:
            console.print(f"[self-improve] recall after improve failed for {skill}: {exc}")

        # Persist the cognee proposal payload alongside the run.
        if proposal_payload:
            try:
                (run_dir / f"_cognee_proposal_{skill}.json").write_text(
                    json.dumps(proposal_payload, indent=2, default=str)
                )
            except Exception:
                pass

        disk_changed = after_disk.strip() != before.strip()
        graph_changed = bool(after_graph) and after_graph.strip() != before.strip()

        if disk_changed or graph_changed:
            publish_event("skill_apply", {"skill": skill, "via": "cognee", "disk_changed": disk_changed, "graph_changed": graph_changed})
            changes.append({
                "skill": skill,
                "applied_via": "cognee",
                "n_proposals": len(props),
                "proposals": props,
                "before": before,
                "after_disk": after_disk,
                "after_graph": after_graph,
                "disk_changed": disk_changed,
                "graph_changed": graph_changed,
            })
            console.print(
                f"[self-improve] {skill}: disk_changed={disk_changed} graph_changed={graph_changed}"
            )
        else:
            console.print(f"[self-improve] {skill}: improve_skill ran but no visible change (disk or graph)")

    # Persist skill_diff.md — sources both "after_disk" and "after_graph".
    diff_md = [f"# Skill diff after run {run_slug}",
               f"_F1 = {score} · {sum(len(v) for v in by_skill.values())} proposals integrated across {len(changes)} skill(s) — all via `cognee.improve_skill(apply=True)`_",
               ""]
    for change in changes:
        diff_md += [
            f"## {change['skill']}  ·  disk={'changed' if change['disk_changed'] else 'unchanged'}  ·  graph={'changed' if change['graph_changed'] else 'unchanged'}",
            "",
            f"_{change['n_proposals']} proposal(s) from the critique:_",
        ]
        for p in change["proposals"][:3]:
            diff_md.append(f"- _{p.get('rule','')}_ — evidence: `{p.get('evidence','')}`")
        diff_md += [
            "",
            "### Before (SKILL.md seed)",
            "```markdown",
            change["before"].strip(),
            "```",
            "",
            "### After — Cognee graph (what improve_skill committed)",
            "```",
            (change.get("after_graph") or "(empty graph response)").strip(),
            "```",
            "",
            "### After — SKILL.md on disk",
            "```markdown",
            change.get("after_disk", "").strip(),
            "```",
            "",
        ]
    (run_dir / "skill_diff.md").write_text("\n".join(diff_md) + "\n")
    publish_event("self_improve_done", {"slug": run_slug, "changed": len(changes)})
    append_log(f"self-improve | slug={run_slug} | changed={len(changes)} of {len(by_skill)} skills (cognee-pure)")

    # Re-ingest the updated my_skills/ as skills so future recalls see them
    try:
        await cognee.remember(
            str(SKILLS_DIR),
            dataset_name=COGNEE_DATASET,
            content_type="skills",
        )
    except Exception as exc:
        console.print(f"[self-improve] re-ingest skills skipped: {exc}")

    # Push each changed SKILL.md as a separate document so the Datasets UI
    # lists it as a file (cognee Skills view + Datasets view are different).
    for change in changes:
        skill_path = SKILLS_DIR / change["skill"] / "SKILL.md"
        if skill_path.exists():
            try:
                await cognee.remember(str(skill_path), dataset_name=COGNEE_DATASET)
            except Exception as exc:
                console.print(f"[self-improve] doc push for {change['skill']}: {exc}")

    console.rule(f"[bold magenta]Self-improve done  changed={len(changes)}")
    return {"changed": len(changes), "changes": changes}
