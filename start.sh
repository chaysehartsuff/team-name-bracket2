#!/usr/bin/env bash

# ─── Ensure ‘nohup’ is available ──────────────────────────────────
if ! command -v nohup >/dev/null 2>&1; then
  echo "Error: 'nohup' not found. Please install coreutils." >&2
  exit 1
fi

# ─── Load environment ────────────────────────────────────────────
set -a
[ -f .env ] && source .env
set +a

# ─── Check for existing bot process ──────────────────────────────
if [ -f bot.pid ]; then
  EXISTING_PID=$(cat bot.pid)
  if kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "Bot is already running with PID $EXISTING_PID. Exiting start script."
    exit 0
  else
    echo "Found stale bot.pid (PID $EXISTING_PID not running). Cleaning up."
    rm -f bot.pid
  fi
fi

# ─── Prepare logs directory ──────────────────────────────────────
mkdir -p logs

# ─── Launch bot in background ───────────────────────────────────
nohup python bot.py > logs/bot.log 2>&1 &

# ─── Record new PID ──────────────────────────────────────────────
echo $! > bot.pid

echo "Bot started with PID $(cat bot.pid). Logs: logs/bot.log"