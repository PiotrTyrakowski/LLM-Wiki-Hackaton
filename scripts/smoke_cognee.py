"""Smoke test: cognee[redis] remember/recall round-trip with and without session_id.

Run:
    uv run python scripts/smoke_cognee.py
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


async def main() -> None:
    if not os.environ.get("LLM_API_KEY"):
        print("[fatal] LLM_API_KEY missing in .env — paste your OpenAI key from kickoff.", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("REDIS_URL"):
        print("[fatal] REDIS_URL missing in .env.", file=sys.stderr)
        sys.exit(1)

    import cognee

    print(f"[setup] cognee {getattr(cognee, '__version__', '?')}  redis={os.environ['REDIS_URL']}")

    try:
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
        print("[setup] pruned existing data + system")
    except Exception as exc:
        print(f"[setup] prune skipped: {exc!r}")

    print("[1/4] remember (permanent graph)")
    await cognee.remember("Cognee turns documents into AI memory.")

    print("[2/4] remember (session memory -> Redis)")
    await cognee.remember(
        "User prefers dense editing with fast cuts.",
        session_id="smoke_session",
    )

    print("[3/4] recall (permanent)")
    permanent = await cognee.recall("What does Cognee do?")
    print(f"      => {permanent!r}")

    print("[4/4] recall (session)")
    session = await cognee.recall(
        "What does the user prefer?",
        session_id="smoke_session",
    )
    print(f"      => {session!r}")

    print("[ok] smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
