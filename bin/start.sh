#!/usr/bin/env bash
# Start the simulator in Docker, with your history, at http://localhost:8501 (or ACE_PORT).
# If it's already running, it restarts it, which picks up code changes.
#
#   bin/start.sh [--yes] [--no-sync] [--no-open]
#
#   --yes       don't ask before restarting a running simulator (an exam in progress is lost)
#   --no-sync   don't merge data/history.json with the history in Docker
#   --no-open   don't open the browser
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

OPEN=1
for arg in "$@"; do
  case "$arg" in
    --yes|-y) ASSUME_YES=1 ;;
    --no-sync) SYNC=0 ;;
    --no-open) OPEN=0 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown option '$arg'. See bin/start.sh --help." ;;
  esac
done

preflight
take_lock

RESTART=0
if running; then
  say "The simulator is already running. Restarting it loads the latest code and history; an exam in progress is lost."
  confirm "Restart it?"
  RESTART=1
elif (exec 3<>"/dev/tcp/127.0.0.1/$ACE_PORT") 2>/dev/null; then
  die "port $ACE_PORT is already in use by another program. Free it, or run: ACE_PORT=8600 bin/start.sh"
fi

say "Building the image (quick when nothing changed)…"
if ! docker compose build --quiet; then
  image_exists || die "the image couldn't be built. Check your internet connection for the first build."
  say "Warning: the build failed, so the existing image is used. Your latest code changes aren't in it."
fi

# Stop first, so an exam submitted right now can't race the sync's write to the same file.
[ "$RESTART" = 1 ] && docker compose stop
sync_state
docker compose up -d --wait --force-recreate

URL="http://localhost:$ACE_PORT"
say "The simulator is running at $URL. Stop it with bin/stop.sh."
if [ "$OPEN" = 1 ]; then
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true
  fi
fi
