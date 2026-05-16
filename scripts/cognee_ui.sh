#!/usr/bin/env bash
# scripts/cognee_ui.sh — start | stop | restart | status the Cognee web UI
#
# The Cognee UI holds an exclusive lock on the local ladybug DB, so it must
# be STOPPED while CLI commands write (ingest, attempt, self-improve), then
# STARTED again to view the graph. Use scripts/demo.sh for the orchestration.
#
# Usage:
#   scripts/cognee_ui.sh start      # boot UI + backend
#   scripts/cognee_ui.sh stop       # release DB lock
#   scripts/cognee_ui.sh restart
#   scripts/cognee_ui.sh status
#   scripts/cognee_ui.sh logs       # tail /tmp/cognee_ui.log

set -e
cd "$(dirname "$0")/.."

LOG=/tmp/cognee_ui.log

_load_env() {
  if [ -f .env ]; then set -a; source .env; set +a; fi
}

_port_pid() { lsof -ti :"$1" -sTCP:LISTEN 2>/dev/null | head -1; }

_kill_processes() {
  pkill -f "cognee-cli" 2>/dev/null || true
  pkill -f "cognee.api" 2>/dev/null || true
  pkill -f "next-server" 2>/dev/null || true
  for p in 3000 8000; do
    PID=$(_port_pid "$p")
    [ -n "$PID" ] && kill -9 "$PID" 2>/dev/null || true
  done
  docker ps --filter "name=cognee-mcp" --format "{{.Names}}" | xargs -r docker rm -f 2>/dev/null || true
}

cmd="${1:-status}"
case "$cmd" in
  start)
    _load_env
    if [ -n "$(_port_pid 3000)" ] || [ -n "$(_port_pid 8000)" ]; then
      echo "[cognee_ui] already running on 3000/8000"
    else
      echo "[cognee_ui] starting (logs: $LOG)…"
      nohup uv run cognee-cli -ui > "$LOG" 2>&1 &
      disown $! 2>/dev/null || true
    fi
    # Wait up to ~60s for both ports to bind, polling every 2s.
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
      [ -n "$(_port_pid 3000)" ] && [ -n "$(_port_pid 8000)" ] && break
      sleep 2
    done
    echo "[cognee_ui] frontend pid=$(_port_pid 3000) backend pid=$(_port_pid 8000)"
    echo "[cognee_ui] open http://localhost:3000"
    ;;
  stop)
    echo "[cognee_ui] stopping…"
    _kill_processes
    sleep 1
    echo "[cognee_ui] stopped"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    F=$(_port_pid 3000); B=$(_port_pid 8000)
    echo "frontend (3000): ${F:-down}"
    echo "backend  (8000): ${B:-down}"
    ;;
  logs)
    tail -n 80 "$LOG"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status|logs}"
    exit 2
    ;;
esac
