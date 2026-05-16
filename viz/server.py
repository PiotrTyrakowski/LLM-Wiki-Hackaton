"""FastAPI viz: before/after SKILL.md panes, run list, Redis stream feed.

Endpoints:
  GET /                 — index, lists runs, shows current SKILL.md
  GET /skills           — current SKILL.md files rendered as cards
  GET /run/<slug>       — critique scores + skill diff + attempt video
  GET /events           — recent Redis stream events (XREVRANGE)
  GET /api/clips        — current Redis vector index entries
  GET /static/...       — serve runs/ and data/ as static files
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

from llmwiki.config import (
    DEMO_TARGET,
    RUNS_DIR,
    SKILLS,
    SKILLS_DIR,
    WIKI_DIR,
)
from llmwiki.redis_use import client as redis_client
from llmwiki.redis_use import read_recent_events
from llmwiki.wiki import parse_frontmatter

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Cinegraph viz")
templates = Jinja2Templates(directory=str(ROOT / "viz" / "templates"))

# Mount static for runs/ (attempt.mp4) and data/ (target/edited.mp4).
app.mount("/runs", StaticFiles(directory=str(RUNS_DIR), check_dir=False), name="runs")
app.mount("/data", StaticFiles(directory=str(ROOT / "data"), check_dir=False), name="data")

md = MarkdownIt("commonmark", {"breaks": True, "html": False})


def _render_skill(skill: str) -> dict[str, Any]:
    path = SKILLS_DIR / skill / "SKILL.md"
    if not path.exists():
        return {"name": skill, "exists": False, "html": "", "raw": ""}
    raw = path.read_text()
    meta, body = parse_frontmatter(raw)
    return {
        "name": skill,
        "exists": True,
        "description": meta.get("description", ""),
        "html": md.render(body),
        "raw": raw,
        "n_rules": sum(1 for line in body.splitlines() if line.strip().startswith(tuple(f"{i}." for i in range(1, 100)))),
    }


def _list_runs() -> list[dict[str, Any]]:
    out = []
    if not RUNS_DIR.exists():
        return out
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        info: dict[str, Any] = {"slug": d.name, "path": str(d)}
        for key, fname in [
            ("attempt_mp4", "attempt.mp4"),
            ("edl_json", "edl.json"),
            ("critique_md", "critique.md"),
            ("critique_json", "critique.json"),
            ("skill_diff_md", "skill_diff.md"),
        ]:
            p = d / fname
            info[key] = p.exists()
        cjson = d / "critique.json"
        if cjson.exists():
            try:
                c = json.loads(cjson.read_text())
                info["f1"] = c.get("scores", {}).get("f1")
                info["n_proposals"] = len(c.get("proposals", []))
            except Exception:
                pass
        out.append(info)
    return out


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "skills": [_render_skill(s) for s in SKILLS],
            "runs": _list_runs(),
            "target_exists": DEMO_TARGET.exists(),
        },
    )


@app.get("/run/{slug}", response_class=HTMLResponse)
async def run_view(request: Request, slug: str) -> HTMLResponse:
    run_dir = RUNS_DIR / slug
    if not run_dir.is_dir():
        return HTMLResponse(f"<h1>run not found: {slug}</h1>", status_code=404)
    critique = None
    cjson = run_dir / "critique.json"
    if cjson.exists():
        critique = json.loads(cjson.read_text())
    skill_diff_html = None
    sd = run_dir / "skill_diff.md"
    if sd.exists():
        skill_diff_html = md.render(sd.read_text())
    critique_html = None
    cm = run_dir / "critique.md"
    if cm.exists():
        critique_html = md.render(cm.read_text())
    return templates.TemplateResponse(
        request,
        "run.html",
        {
            "slug": slug,
            "critique": critique,
            "critique_html": critique_html,
            "skill_diff_html": skill_diff_html,
            "skills": [_render_skill(s) for s in SKILLS],
            "attempt_url": f"/runs/{slug}/attempt.mp4" if (run_dir / "attempt.mp4").exists() else None,
        },
    )


@app.get("/events")
async def events(count: int = 100) -> JSONResponse:
    return JSONResponse(read_recent_events(count=count))


@app.get("/api/clips")
async def clips() -> JSONResponse:
    r = redis_client()
    out = []
    try:
        keys = r.keys("clip:*")
        for k in keys:
            data = r.hgetall(k)
            entry: dict[str, Any] = {"key": k.decode() if isinstance(k, bytes) else k}
            for f, v in data.items():
                fk = f.decode() if isinstance(f, bytes) else f
                if fk == "embedding":
                    continue
                try:
                    entry[fk] = v.decode() if isinstance(v, bytes) else v
                except Exception:
                    entry[fk] = str(v)
            out.append(entry)
    except Exception as exc:
        return JSONResponse({"error": str(exc)})
    return JSONResponse(out)


@app.get("/skills/raw/{skill}")
async def skill_raw(skill: str) -> JSONResponse:
    return JSONResponse(_render_skill(skill))
