"""Typer CLI: `uv run python -m llmwiki <command>`."""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from . import ingest as ingest_module
from . import memory
from .config import DEMO_TARGET, ensure_dirs

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


@app.command()
def smoke() -> None:
    """Run the cognee remember/recall smoke test."""
    from pathlib import Path as _P
    import subprocess
    script = _P(__file__).resolve().parent.parent / "scripts" / "smoke_cognee.py"
    raise SystemExit(subprocess.call(["uv", "run", "python", str(script)]))


@app.command()
def ingest(target: Path = typer.Option(DEMO_TARGET, help="Target edited video to ingest")) -> None:
    """Op 1: ingest the target edited video into wiki/observations and cognee."""
    ensure_dirs()
    slug = asyncio.run(ingest_module.ingest(target_path=target))
    console.print(f"[bold green]slug={slug}")


@app.command()
def reset() -> None:
    """Wipe cognee data + session memory."""
    asyncio.run(memory.reset())
    console.print("[bold green]reset complete")


@app.command()
def attempt(
    source_dir: Path = typer.Option(None, help="Source clips dir (defaults to data/demo/source)"),
    no_lessons: bool = typer.Option(False, help="Run without retrieving any lessons from cognee"),
    label: str = typer.Option("v1", help="Run label (v1, v2, ...)"),
) -> None:
    """Op 2a: produce an EDL + render attempt.mp4."""
    from . import attempt as attempt_module
    slug = asyncio.run(attempt_module.attempt(source_dir=source_dir, no_lessons=no_lessons, label=label))
    console.print(f"[bold green]attempt slug={slug}")


@app.command(name="critique")
def critique_cmd(run_slug: str) -> None:
    """Op 2b: score the attempt against target; produce critique.md."""
    from . import critique as critique_module
    asyncio.run(critique_module.critique(run_slug))


@app.command(name="self-improve")
def self_improve_cmd(run_slug: str) -> None:
    """Op 2c: SkillRunEntry -> improve_skill(apply=True). Rewrites my_skills/*."""
    from . import self_improve as si_module
    asyncio.run(si_module.self_improve(run_slug))


@app.command()
def lint() -> None:
    """Op 3: health-check the wiki/skill pack; write wiki/_lint_report.md."""
    from . import lint as lint_module
    asyncio.run(lint_module.lint())


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Question to ask Gemini about the target video"),
    start: float = typer.Option(0.0, "--start", help="Start second of the range"),
    duration: float = typer.Option(None, "--duration", help="Duration in seconds (omit for the whole target)"),
) -> None:
    """Editor tool: ask Gemini a free-form question about a slice of the target."""
    from . import editor_tools
    asyncio.run(editor_tools.ask_target(prompt, start_s=start, duration_s=duration))


@app.command()
def frames(
    timestamps: list[float] = typer.Argument(..., help="Timestamps in seconds, e.g. 1.5 3.2 6.8"),
) -> None:
    """Editor tool: extract still frames from the target at given timestamps."""
    from . import editor_tools
    editor_tools.extract_frames(timestamps)


@app.command()
def viz(port: int = 8000) -> None:
    """Start the FastAPI before/after viz server."""
    import uvicorn
    uvicorn.run("viz.server:app", host="127.0.0.1", port=port, log_level="info")


@app.command()
def demo() -> None:
    """Full end-to-end: ingest -> attempt v1 -> critique -> self-improve -> attempt v2."""
    ensure_dirs()
    console.rule("[bold magenta]DEMO START")
    ingest_slug = asyncio.run(ingest_module.ingest(target_path=DEMO_TARGET))
    console.print(f"ingest slug = {ingest_slug}")

    from . import attempt as attempt_module
    v1 = asyncio.run(attempt_module.attempt(label="v1", no_lessons=True))
    console.print(f"v1 attempt slug = {v1}")

    from . import critique as critique_module
    asyncio.run(critique_module.critique(v1))

    from . import self_improve as si_module
    asyncio.run(si_module.self_improve(v1))

    v2 = asyncio.run(attempt_module.attempt(label="v2", no_lessons=False))
    console.print(f"v2 attempt slug = {v2}")
    console.rule("[bold magenta]DEMO COMPLETE — open http://localhost:8000")


if __name__ == "__main__":
    app()
