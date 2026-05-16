"""Markdown wiki helpers — write observations, append log entries, parse frontmatter."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import WIKI_DIR

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "item"


def write_frontmatter(meta: dict[str, Any], body: str) -> str:
    return f"---\n{yaml.safe_dump(meta, sort_keys=False).strip()}\n---\n\n{body.strip()}\n"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end():]


def write_observation(run_slug: str, kind: str, prompt: str, answer: str) -> Path:
    out_dir = WIKI_DIR / "observations" / run_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{kind}.md"
    body = (
        f"# {kind}\n\n"
        f"## Prompt\n\n{prompt}\n\n"
        f"## Answer\n\n{answer}\n"
    )
    meta = {"run_slug": run_slug, "kind": kind, "created": now_iso()}
    path.write_text(write_frontmatter(meta, body))
    return path


def append_log(line: str) -> None:
    log = WIKI_DIR / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text("# Log\n\n")
    with log.open("a") as f:
        f.write(f"## [{now_iso()}] {line}\n\n")


def read_skill(skill_name: str) -> tuple[dict[str, Any], str]:
    from .config import SKILLS_DIR
    path = SKILLS_DIR / skill_name / "SKILL.md"
    text = path.read_text() if path.exists() else ""
    return parse_frontmatter(text)


def read_all_skills() -> dict[str, tuple[dict[str, Any], str]]:
    from .config import SKILLS
    return {name: read_skill(name) for name in SKILLS}
