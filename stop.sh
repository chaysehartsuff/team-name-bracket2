#!/usr/bin/env bash

# ─── Load environment ────────────────────────────────────────────
set -a
[ -f .env ] && source .env
set +a

# ─── Ensure bot.pid exists ──────────────────────────────────────
if [ ! -f bot.pid ]; then
  echo "No bot.pid file found. Is the bot running?"
  exit 1
fi

# ─── Read and verify PID ────────────────────────────────────────
PID=$(cat bot.pid)
if ! kill -0 "$PID" 2>/dev/null; then
  echo "Process $PID not running. Removing stale bot.pid"
  rm -f bot.pid
  exit 1
fi

# ─── Terminate bot ──────────────────────────────────────────────
kill "$PID" && echo "Sent TERM to process $PID."
rm -f bot.pid