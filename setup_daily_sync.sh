#!/usr/bin/env bash
set -euo pipefail

# Configuração padrão: rodar todo dia às 03:00.
# Você pode sobrescrever com variáveis:
#   SYNC_HOUR=5 SYNC_MINUTE=30 ./setup_daily_sync.sh

SYNC_HOUR="${SYNC_HOUR:-3}"
SYNC_MINUTE="${SYNC_MINUTE:-0}"

if ! [[ "$SYNC_HOUR" =~ ^([01]?[0-9]|2[0-3])$ ]]; then
  echo "Erro: SYNC_HOUR deve ser entre 0 e 23." >&2
  exit 1
fi

if ! [[ "$SYNC_MINUTE" =~ ^([0-5]?[0-9])$ ]]; then
  echo "Erro: SYNC_MINUTE deve ser entre 0 e 59." >&2
  exit 1
fi

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/playlist_sync.log"
PYTHON_BIN="$(command -v python3)"
MARKER="# youtubemusica-daily-sync"
CRON_CMD="cd $REPO_DIR && $PYTHON_BIN scripts_sync_playlists.py >> $LOG_FILE 2>&1"
CRON_LINE="$SYNC_MINUTE $SYNC_HOUR * * * $CRON_CMD $MARKER"

mkdir -p "$LOG_DIR"

tmpfile="$(mktemp)"
crontab -l 2>/dev/null | sed "/$MARKER/d" > "$tmpfile" || true
printf '%s\n' "$CRON_LINE" >> "$tmpfile"
crontab "$tmpfile"
rm -f "$tmpfile"

echo "Agendado com sucesso: $SYNC_MINUTE $SYNC_HOUR * * *"
echo "Log: $LOG_FILE"
