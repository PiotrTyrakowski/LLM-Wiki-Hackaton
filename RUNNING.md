# Where everything is — Cinegraph runtime dashboard

## Live URLs

| URL | What |
|-----|------|
| **http://localhost:3000** | **Cognee's official web UI** — the knowledge graph viewer. Inspect every node `cognee.remember()` created, including the skills, observations, and self-improvement events. |
| **http://localhost:8000** | Cognee's API backend (used by the UI above; no direct browsing needed). |
| **http://localhost:8002** | **Our before/after wiki viz** — SKILL.md cards, run table with F1 scores, live Redis event stream. **Refresh after each command** to see state change. |
| **http://localhost:8002/run/`<slug>`** | Drill-in page for one attempt — side-by-side `target` vs `attempt.mp4`, scores, SKILL.md diff. |

## Background services (don't kill these)

| Service | Port(s) | How it was started |
|---|---|---|
| Redis Stack (Cognee session memory + RediSearch + streams + pub/sub) | 6379 (internal mapping unused) → **6380** (host) | `docker run -d --name llmwiki-redis -p 6380:6379 redis/redis-stack-server:latest` |
| Cognee UI frontend (Next.js) | 3000 | `uv run cognee-cli -ui` |
| Cognee UI backend (FastAPI) | 8000 | started by `cognee-cli -ui` automatically |
| Cinegraph viz (our FastAPI) | 8002 | `uv run uvicorn viz.server:app --port 8002` |

Logs:
- Cognee UI: `/tmp/cognee_ui.log`
- Our viz: `/tmp/viz.log`
- Cognee debug logs: `/Users/piotrtyrakowski/.cognee/logs/*`

## Filesystem map — where the artifacts live

```
/Users/piotrtyrakowski/repos/LLM-Wiki-Hackaton/
├── data/demo/
│   ├── source/                 # placeholder assets the agent edits with
│   └── target/edited.mp4       # 10s human edit — the ground truth
├── my_skills/                  # 5 SKILL.md files = the compounding wiki
│   ├── cut-detection/SKILL.md
│   ├── broll-selection/SKILL.md
│   ├── pacing/SKILL.md
│   ├── transitions/SKILL.md
│   └── on-screen-text/SKILL.md
├── wiki/
│   ├── observations/<slug>/    # raw Gemini answers per ingest
│   ├── log.md                  # append-only operation log
│   └── prompting/, patterns/   # lifted recreator cookbook
├── runs/<attempt-slug>/
│   ├── Hero.snapshot.tsx       # Hero.tsx at the moment of this attempt
│   ├── skills_snapshot/        # SKILL.md state at this attempt
│   ├── attempt.mp4             # rendered 720p output
│   ├── critique.json/.md       # Gemini dual-video critique
│   └── judge_raw.txt           # raw Gemini judge YAML
├── remotion/
│   ├── src/Hero.tsx            # the agent's CURRENT edit. Rewritten between attempts.
│   ├── src/components/SlidingStackPip.tsx
│   └── public/                 # Remotion staticFile() root
├── llmwiki/                    # Python pipeline
│   ├── cli.py                  # `python -m llmwiki <command>`
│   ├── attempt.py              # render Hero -> attempt.mp4 + snapshot state
│   ├── critique.py             # dual-video Gemini critique
│   ├── self_improve.py         # SkillRunEntry -> improve_skill -> rewrite SKILL.md
│   ├── editor_tools.py         # `ask` + `frames` — editor tools for me (Claude Code)
│   ├── ingest.py               # Gemini observations of target
│   ├── memory.py               # cognee.remember/recall wrappers
│   ├── redis_use.py            # streams, pub/sub, vector index
│   └── ...
└── viz/server.py               # the http://localhost:8002 server
```

## CLI cheat sheet

Always run from the project root, with the venv activated implicitly via `uv run`.

```bash
cd /Users/piotrtyrakowski/repos/LLM-Wiki-Hackaton
set -a && source .env && set +a

# Wipe Cognee + Redis state
uv run python -m llmwiki reset

# Ingest the target — Gemini extracts cuts/broll/pacing/text observations
uv run python -m llmwiki ingest

# Render the current Hero.tsx as an attempt
uv run python -m llmwiki attempt --label v1

# Score the latest attempt — Gemini watches BOTH videos in one call
uv run python -m llmwiki critique <slug>

# Apply the critique: SkillRunEntry -> improve_skill rewrites SKILL.md files
uv run python -m llmwiki self-improve <slug>

# Editor tools (used by Claude Code while writing Hero.tsx)
uv run python -m llmwiki ask "What is happening at t=2.5s?" --start 2.0 --duration 2.0
uv run python -m llmwiki frames 1.5 3.2 6.8

# Inspect Redis state
docker exec llmwiki-redis redis-cli DBSIZE
docker exec llmwiki-redis redis-cli --scan --pattern 'agent_sessions:*' | head
docker exec llmwiki-redis redis-cli XREVRANGE llmwiki:events + - COUNT 20
docker exec llmwiki-redis redis-cli FT.INFO llmwiki:clip-vectors | head -20
```

## The full demo loop (what you'd run live)

```bash
# 1. Fresh slate
uv run python -m llmwiki reset

# 2. Watch the target with Gemini
uv run python -m llmwiki ingest

# 3. Render the current Hero.tsx as v1 (the agent's first attempt)
uv run python -m llmwiki attempt --label v1
SLUG_V1=$(ls -t runs/ | head -1)

# 4. Critique — Gemini sees both videos side by side
uv run python -m llmwiki critique $SLUG_V1

# 5. Wiki self-improves — SKILL.md files get new rules
uv run python -m llmwiki self-improve $SLUG_V1

# 6. (Optional, demo theatre) Claude Code rewrites Hero.tsx using the new rules
#    -> for the demo, the rewrite is the diff between commits in remotion/src/Hero.tsx

# 7. Render v2 with the new Hero.tsx
uv run python -m llmwiki attempt --label v2
SLUG_V2=$(ls -t runs/ | head -1)
uv run python -m llmwiki critique $SLUG_V2

# 8. Show the viz
open http://localhost:8002
open http://localhost:3000
```

## Who edits what (the architecture rule)

| Role | Who |
|---|---|
| **Editor** (writes Hero.tsx) | **Claude Code (me)** — never GPT, never automated. |
| **Vision** (watches videos) | **Gemini 3.1 Flash Lite Preview** |
| **Critic** (compares attempt to target) | **Gemini** (dual-video prompt — sees both at once) |
| **Lesson integration** (rewrites SKILL.md) | Cognee `SkillRunEntry` → `improve_skill(apply=True)`, with **GPT-5.5** as the rewriter (no longer 4o). |
| **Memory** | Redis (session, streams, pub/sub, vector index) → Cognee (permanent graph). |
