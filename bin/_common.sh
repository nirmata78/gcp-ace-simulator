# Shared by bin/start.sh and bin/stop.sh; not meant to be run on its own.
# Settings (all optional): ACE_PORT, ACE_VOLUME, COMPOSE_PROJECT_NAME,
# ACE_LOCAL_HISTORY and ACE_LOCAL_REPORTS (where the Python install keeps its files).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
IMAGE="ghcr.io/nirmata78/gcp-ace-simulator:local"
SERVICE="simulator"
export ACE_PORT="${ACE_PORT:-8501}"
export ACE_VOLUME="${ACE_VOLUME:-ace-state}"
LOCAL_HISTORY="${ACE_LOCAL_HISTORY:-$ROOT/data/history.json}"
LOCAL_REPORTS="${ACE_LOCAL_REPORTS:-$ROOT/reports}"
ASSUME_YES=0
SYNC=1

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

preflight() {
  if [ "$(id -u)" -eq 0 ] && [ "${ACE_ALLOW_ROOT:-0}" != 1 ]; then
    die "don't run this as root or with sudo: the files it writes to data/ and reports/ would belong to root.
Add your user to the docker group instead, or set ACE_ALLOW_ROOT=1 if you mean it."
  fi
  command -v docker >/dev/null 2>&1 || die "Docker isn't installed: https://docs.docker.com/get-docker/"
  docker info >/dev/null 2>&1 || die "Docker isn't running. Start Docker Desktop or the Docker service, then try again."
  docker compose version >/dev/null 2>&1 || die "Docker Compose v2 ('docker compose') is missing."
  [ -f compose.yaml ] || die "compose.yaml is missing: run this from a clone of the repository."
  case "$ACE_PORT" in ''|*[!0-9]*) die "ACE_PORT must be a port number, not '$ACE_PORT'." ;; esac
  case "$ACE_VOLUME" in ''|*[!A-Za-z0-9_.-]*) die "ACE_VOLUME must be a plain volume name, not '$ACE_VOLUME'." ;; esac
}

# One start or stop at a time: two syncs racing could each miss the other's attempts.
take_lock() {
  LOCK="$ROOT/.ace-lock"
  mkdir "$LOCK" 2>/dev/null || die "another bin/start.sh or bin/stop.sh is running. If none is, delete $LOCK."
  trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT
}

running() { [ -n "$(docker compose ps -q --status running "$SERVICE" 2>/dev/null)" ]; }
image_exists() { docker image inspect "$IMAGE" >/dev/null 2>&1; }
volume_exists() { docker volume inspect "$ACE_VOLUME" >/dev/null 2>&1; }

confirm() {
  [ "$ASSUME_YES" = 1 ] && return 0
  if [ -t 0 ]; then
    local answer
    read -r -p "$1 [y/N] " answer
    case "$answer" in [Yy]*) return 0 ;; *) say "Nothing changed."; exit 1 ;; esac
  fi
  die "$1 Run again with --yes to confirm."
}

# Merge the volume's history with the Python install's, so both see every attempt, and copy
# reports made in the container into reports/. Adds only; never deletes or overwrites.
sync_state() {
  [ "$SYNC" = 1 ] || { say "Skipping the history sync (--no-sync)."; return 0; }
  image_exists || return 0
  mkdir -p "$(dirname "$LOCAL_HISTORY")" "$LOCAL_REPORTS"
  local input=/dev/null tmp result
  [ -f "$LOCAL_HISTORY" ] && input="$LOCAL_HISTORY"
  tmp="$(mktemp "$LOCAL_HISTORY.sync.XXXXXX")"
  if ! result="$(docker run --rm -i -v "$ACE_VOLUME:/state" "$IMAGE" \
      python -m src.history_sync /state/history.json <"$input" 2>&1 >"$tmp")"; then
    rm -f "$tmp"
    die "the history sync failed and nothing was changed: $result
Fix or move $LOCAL_HISTORY, or run with --no-sync."
  fi
  local to_local to_state total
  to_local="$(sed -n 's/.*to_local=\([0-9]*\).*/\1/p' <<<"$result")"
  to_state="$(sed -n 's/.*to_state=\([0-9]*\).*/\1/p' <<<"$result")"
  total="$(sed -n 's/.*total=\([0-9]*\).*/\1/p' <<<"$result")"
  if [ "${to_local:-0}" -gt 0 ]; then
    [ -f "$LOCAL_HISTORY" ] && cp -p "$LOCAL_HISTORY" "$LOCAL_HISTORY.bak"
    mv "$tmp" "$LOCAL_HISTORY"
  else
    rm -f "$tmp"
  fi
  say "History: ${total:-0} attempts. Copied ${to_state:-0} into Docker and ${to_local:-0} back to $(basename "$LOCAL_HISTORY")."

  local names missing=()
  names="$(docker run --rm -v "$ACE_VOLUME:/state" "$IMAGE" sh -c 'ls -1 /state/reports 2>/dev/null || true')"
  while IFS= read -r name; do
    [[ "$name" =~ ^[A-Za-z0-9._-]+\.pdf$ ]] || continue
    [ -e "$LOCAL_REPORTS/$name" ] || missing+=("$name")
  done <<<"$names"
  if [ "${#missing[@]}" -gt 0 ]; then
    docker run --rm -v "$ACE_VOLUME:/state" "$IMAGE" tar -C /state/reports -cf - -- "${missing[@]}" \
      | tar -xf - -C "$LOCAL_REPORTS"
    say "Reports: copied ${#missing[@]} new PDF(s) to $LOCAL_REPORTS."
  fi
}
