#!/usr/bin/env bash
# scripts/demo.sh — run the full Cinegraph loop end-to-end.
#
# Cognee's local DB is exclusive-locked when its UI is running, so this
# script automatically stops the UI before writes and starts it back after.
#
# Usage:
#   scripts/demo.sh           # full loop: reset + ingest + attempt + critique + self-improve
#   scripts/demo.sh --no-reset # skip the cognee + redis wipe
#   scripts/demo.sh --no-ui   # don't restart the UI at the end

set -e
cd "$(dirname "$0")/.."

NO_RESET=0
NO_UI=0
LABEL="v1"
for arg in "$@"; do
  case "$arg" in
    --no-reset) NO_RESET=1 ;;
    --no-ui)    NO_UI=1 ;;
    --label=*)  LABEL="${arg#--label=}" ;;
  esac
done

# Load env
if [ -f .env ]; then set -a; source .env; set +a; fi

echo "==> stopping cognee UI to release DB lock"
./scripts/cognee_ui.sh stop > /dev/null 2>&1 || true

if [ "$NO_RESET" = "0" ]; then
  echo "==> hard reset (cognee state + redis FLUSHDB)"
  rm -rf .venv/lib/python3.12/site-packages/cognee/.cognee_system 2>/dev/null || true
  rm -rf .venv/lib/python3.12/site-packages/cognee/.cognee_data 2>/dev/null || true
  docker exec llmwiki-redis redis-cli FLUSHDB > /dev/null
  rm -rf runs/* wiki/observations/*
  echo "# Log" > wiki/log.md && echo "" >> wiki/log.md
  uv run python -m llmwiki reset 2>&1 | tail -3
fi

echo ""
echo "==> ingest (Gemini watches the target)"
uv run python -m llmwiki ingest 2>&1 | grep -vE "^\[2m" | grep -E "(Ingest|wrote|gemini|graph|session|skill|warn)" | tail -15

echo ""
echo "==> attempt $LABEL (renders the current Hero.tsx)"
uv run python -m llmwiki attempt --label "$LABEL" 2>&1 | grep -vE "^\[2m" | grep -E "(Attempt|render|snapshot|session)" | tail -10
SLUG=$(ls -t runs/ | grep "^attempt-$LABEL" | head -1)
echo "    slug=$SLUG"

echo ""
echo "==> critique (Gemini watches BOTH videos)"
uv run python -m llmwiki critique "$SLUG" 2>&1 | grep -vE "^\[2m" | grep -E "(Critique|scores|proposals|target|agent)" | tail -10

echo ""
echo "==> self-improve (cognee.improve_skill(apply=True) rewrites SKILL.md)"
uv run python -m llmwiki self-improve "$SLUG" 2>&1 | grep -vE "^\[2m" | grep -E "(Self-improve|skill|propose|rewritten|apply|change|missing)" | tail -15

echo ""
echo "==> lint (Op 3: health-check the wiki)"
uv run python -m llmwiki lint 2>&1 | grep -vE "^\[2m" | grep -E "(Lint|skill|dup|orph|proposal|wrote)" | tail -8

echo ""
echo "==> demo artifacts:"
echo "    runs/$SLUG/attempt.mp4       (rendered video)"
echo "    runs/$SLUG/critique.md       (scores + proposals)"
echo "    runs/$SLUG/skill_diff.md     (before/after wiki state)"

if [ "$NO_UI" = "0" ]; then
  echo ""
  echo "==> restarting cognee UI for inspection"
  ./scripts/cognee_ui.sh start
fi

echo ""
echo "==> done"
echo "    http://localhost:3000          (Cognee graph UI)"
echo "    http://localhost:8002          (our before/after viz)"
echo "    http://localhost:8002/run/$SLUG (drill-in)"
