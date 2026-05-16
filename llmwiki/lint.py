"""Op 3: Lint — health-check the wiki / skill pack.

Scans the SKILL.md files and the Cognee graph for:
  - Skills with too few rules (under-developed slots).
  - Duplicate or near-duplicate rules across SKILL.md files (cross-skill leak).
  - Cognee SkillImprovementProposal nodes that were never applied.
  - Orphan observation files (in wiki/observations/ but not referenced anywhere).

Output: wiki/_lint_report.md  — human-readable findings, never auto-fix.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rich.console import Console

import cognee

from .config import SKILLS, SKILLS_DIR, WIKI_DIR
from .redis_use import publish_event
from .wiki import append_log, now_iso, parse_frontmatter

console = Console()

RULE_LINE_RE = re.compile(r"^\s*\d+\.\s+\*\*([^*]+)\*\*\s*(.*)$")


def _extract_rules(skill_text: str) -> list[tuple[str, str]]:
    """Return [(rule_headline, rule_body), ...] from a SKILL.md."""
    _, body = parse_frontmatter(skill_text)
    out: list[tuple[str, str]] = []
    for line in body.splitlines():
        m = RULE_LINE_RE.match(line)
        if m:
            out.append((m.group(1).strip().lower(), m.group(2).strip()))
    return out


def _normalize(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def _near_duplicates(rules_per_skill: dict[str, list[tuple[str, str]]]) -> list[dict[str, Any]]:
    """Find rules that share >=4 distinctive words across different skills."""
    flat: list[tuple[str, str, str]] = []
    for skill, rules in rules_per_skill.items():
        for headline, body in rules:
            flat.append((skill, headline, body))
    findings = []
    for i in range(len(flat)):
        si, hi, bi = flat[i]
        tok_i = _normalize(f"{hi} {bi}")
        for j in range(i + 1, len(flat)):
            sj, hj, bj = flat[j]
            if si == sj:
                continue
            tok_j = _normalize(f"{hj} {bj}")
            common = tok_i & tok_j - {"the", "a", "an", "of", "to", "on", "in", "and", "or", "for"}
            if len(common) >= 4:
                findings.append({
                    "kind": "cross_skill_duplicate",
                    "skills": [si, sj],
                    "rule_a": hi,
                    "rule_b": hj,
                    "common_tokens": sorted(common)[:6],
                })
    return findings


async def _unapplied_proposals_from_graph() -> list[dict[str, Any]]:
    """Recall SkillImprovementProposal nodes that haven't been applied yet."""
    try:
        results = await cognee.recall(
            "List all skill improvement proposals that are still in the 'proposed' state and have not yet been applied to any skill.",
        )
        out: list[dict[str, Any]] = []
        for r in results or []:
            txt = getattr(r, "answer", None) or getattr(r, "text", None) or str(r)
            out.append({"summary": (txt or "")[:300]})
        return out
    except Exception as exc:
        console.print(f"[lint] proposals recall failed: {exc}")
        return []


def _orphan_observations() -> list[str]:
    obs_root = WIKI_DIR / "observations"
    if not obs_root.exists():
        return []
    paths = list(obs_root.glob("*/*.md"))
    # Heuristic: observations from older runs without a corresponding attempt run.
    runs = WIKI_DIR.parent / "runs"
    run_slugs = {p.name for p in runs.iterdir()} if runs.exists() else set()
    orphans: list[str] = []
    for p in paths:
        slug = p.parent.name  # ingest-<ts>
        # Any attempt-* run uses the latest ingest, so an ingest is "orphan"
        # if NO attempt run was created after it.
        if not any(s.startswith("attempt-") for s in run_slugs):
            orphans.append(str(p.relative_to(WIKI_DIR.parent)))
    return orphans


async def lint() -> dict[str, Any]:
    console.rule("[bold yellow]Lint")
    publish_event("lint_start", {})

    rules_per_skill: dict[str, list[tuple[str, str]]] = {}
    thin_skills: list[str] = []
    for skill in SKILLS:
        p = SKILLS_DIR / skill / "SKILL.md"
        if not p.exists():
            console.print(f"[lint] missing SKILL.md for {skill}")
            continue
        rules = _extract_rules(p.read_text())
        rules_per_skill[skill] = rules
        if len(rules) < 3:
            thin_skills.append(skill)
    console.print(f"[lint] skills scanned: {len(rules_per_skill)}; thin: {thin_skills}")

    dupes = _near_duplicates(rules_per_skill)
    console.print(f"[lint] cross-skill duplicate candidates: {len(dupes)}")

    proposals = await _unapplied_proposals_from_graph()
    console.print(f"[lint] unapplied proposals (from graph): {len(proposals)}")

    orphans = _orphan_observations()
    console.print(f"[lint] orphan observations: {len(orphans)}")

    report_path = WIKI_DIR / "_lint_report.md"
    md = [
        f"# Lint report — {now_iso()}",
        "",
        "Lint never auto-fixes; treat each item as a suggestion.",
        "",
        "## Skill density",
    ]
    for skill in SKILLS:
        rules = rules_per_skill.get(skill, [])
        warn = " ⚠️ thin" if skill in thin_skills else ""
        md.append(f"- **{skill}**: {len(rules)} rule(s){warn}")

    md += ["", "## Cross-skill duplicate candidates"]
    if not dupes:
        md.append("- ✅ no significant duplicates")
    else:
        for d in dupes:
            md.append(
                f"- between **{d['skills'][0]}** ('{d['rule_a']}') and **{d['skills'][1]}** ('{d['rule_b']}') — common tokens: `{d['common_tokens']}`"
            )

    md += ["", "## Unapplied skill-improvement proposals (Cognee graph)"]
    if not proposals:
        md.append("- ✅ none pending")
    else:
        for p in proposals[:10]:
            md.append(f"- {p['summary']}")

    md += ["", "## Orphan observation files"]
    if not orphans:
        md.append("- ✅ none")
    else:
        for o in orphans[:20]:
            md.append(f"- `{o}`")

    report_path.write_text("\n".join(md) + "\n")
    console.print(f"[lint] wrote {report_path}")

    publish_event("lint_done", {"thin": len(thin_skills), "dupes": len(dupes), "proposals": len(proposals), "orphans": len(orphans)})
    append_log(f"lint | thin={len(thin_skills)} dupes={len(dupes)} proposals={len(proposals)} orphans={len(orphans)}")
    return {
        "thin": thin_skills,
        "dupes": dupes,
        "proposals": proposals,
        "orphans": orphans,
        "report_path": str(report_path),
    }
