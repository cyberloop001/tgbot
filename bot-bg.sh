#!/usr/bin/env bash
# Background control for the Telegram bridge bot on Ubuntu.
# Usage: ./bot-bg.sh start|stop|restart|status|logs

set -euo pipefail
cd "$(dirname "$0")"

PID_FILE=".bot.pid"
LOG_FILE="bot.log"
PYTHON=".venv/bin/python"

is_running() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  # Fallback: find by process command line
  pgrep -f "[.]venv/bin/python bot.py" >/dev/null 2>&1
}

current_pid() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "$pid"
      return 0
    fi
  fi
  pgrep -f "[.]venv/bin/python bot.py" | head -n1 || true
}

cmd_start() {
  if [[ ! -x "$PYTHON" ]]; then
    echo "Virtualenv missing. Run ./setup-ubuntu.sh first."
    exit 1
  fi
  if [[ ! -f .env ]]; then
    echo "Missing .env — copy .env.example and fill in the values."
    exit 1
  fi
  if is_running; then
    echo "Bot already running (PID $(current_pid))."
    exit 0
  fi

  # Clear stale pid / stray processes
  pkill -f "[.]venv/bin/python bot.py" 2>/dev/null || true
  rm -f "$PID_FILE"

  nohup "$PYTHON" bot.py >>"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE"
  sleep 1

  if is_running; then
    echo "Bot started in background (PID $(current_pid))."
    echo "Logs: tail -f $LOG_FILE"
  else
    echo "Start failed. Check $LOG_FILE"
    exit 1
  fi
}

cmd_stop() {
  local pid
  pid="$(current_pid)"
  if [[ -z "${pid:-}" ]]; then
    pkill -f "[.]venv/bin/python bot.py" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Bot was not running."
    return 0
  fi

  kill "$pid" 2>/dev/null || true
  sleep 1
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null || true
  fi
  pkill -f "[.]venv/bin/python bot.py" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "Bot stopped."
}

cmd_restart() {
  cmd_stop
  cmd_start
}

cmd_status() {
  if is_running; then
    echo "Bot is running (PID $(current_pid))."
  else
    echo "Bot is stopped."
    exit 1
  fi
}

cmd_logs() {
  touch "$LOG_FILE"
  tail -n 50 -f "$LOG_FILE"
}

usage() {
  echo "Usage: $0 {start|stop|restart|status|logs}"
  exit 1
}

case "${1:-}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_restart ;;
  status) cmd_status ;;
  logs) cmd_logs ;;
  *) usage ;;
esac
