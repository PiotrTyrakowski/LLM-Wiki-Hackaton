"""Central config: env vars, paths, model IDs."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Storage paths
WIKI_DIR = ROOT / "wiki"
SKILLS_DIR = ROOT / "my_skills"
DATA_DIR = ROOT / "data" / "demo"
RUNS_DIR = ROOT / "runs"
COMPONENTS_DIR = ROOT / "components"
REMOTION_DIR = ROOT / "remotion"

# Demo data
DEMO_SOURCE_DIR = DATA_DIR / "source"
DEMO_TARGET = DATA_DIR / "target" / "edited.mp4"

# Keys & providers
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-5.5")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6380")

# Cognee
COGNEE_DATASET = os.environ.get("COGNEE_DATASET", "yt-editor-wiki")

# Skill names
SKILLS = [
    "cut-detection",
    "broll-selection",
    "pacing",
    "transitions",
    "on-screen-text",
]

# Streams + pubsub channels
REDIS_STREAM_EVENTS = "llmwiki:events"
REDIS_PUBSUB_CHANNEL = "llmwiki:live"
REDIS_VECTOR_INDEX = "llmwiki:clip-vectors"


def ensure_dirs() -> None:
    for d in (WIKI_DIR / "observations", WIKI_DIR / "decisions", RUNS_DIR, DATA_DIR / "source", DATA_DIR / "target"):
        d.mkdir(parents=True, exist_ok=True)
