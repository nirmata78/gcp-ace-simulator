#!/usr/bin/env bash
# Stop the simulator, after copying new attempts to data/history.json and new reports to reports/.
# Your history stays in Docker too: this never deletes the ace-state volume.
#
#   bin/stop.sh [--yes] [--no-sync]
#
#   --yes       don't ask before stopping (an exam in progress is lost)
#   --no-sync   don't copy the history and reports out of Docker
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

for arg in "$@"; do
  case "$arg" in
    --yes|-y) ASSUME_YES=1 ;;
    --no-sync) SYNC=0 ;;
    -v|--volumes) die "bin/stop.sh never deletes your history. To delete it on purpose, run: docker compose down -v" ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown option '$arg'. See bin/stop.sh --help." ;;
  esac
done

preflight
take_lock

if running; then
  confirm "Stop the simulator? An exam in progress is lost."
  docker compose down  # first, so the app can't write history while it's being synced
  volume_exists && sync_state
  say "Stopped. Your history is kept; bin/start.sh brings it back."
else
  volume_exists && sync_state
  say "The simulator wasn't running."
fi
