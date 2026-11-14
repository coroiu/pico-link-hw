#!/usr/bin/env bash
# Container entrypoint: run the export pipeline once, serve the result, then
# watch hardware/ and enclosure/ for changes and re-export on the fly --
# without restarting the container.
set -uo pipefail

SITE_DIR="${SITE_DIR:-/preview/site}"
HARDWARE_DIR="${HARDWARE_DIR:-/work/hardware}"
ENCLOSURE_DIR="${ENCLOSURE_DIR:-/work/enclosure}"
PORT="${PORT:-8787}"

/preview/scripts/export.sh

echo "[serve] serving $SITE_DIR on 0.0.0.0:$PORT"
python3 -m http.server "$PORT" --bind 0.0.0.0 --directory "$SITE_DIR" &
HTTP_PID=$!

cleanup() {
  echo "[entrypoint] shutting down"
  kill "$HTTP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[watch] watching $HARDWARE_DIR and $ENCLOSURE_DIR for changes"

# -m: monitor continuously (don't exit after one event).
# -r: recurse (hardware/enclosure may gain subdirectories later).
# close_write/create/delete/move: covers editors that write-in-place and
# ones that write-then-rename.
inotifywait -m -r -e close_write,create,delete,move --format '%w%f' \
    "$HARDWARE_DIR" "$ENCLOSURE_DIR" 2>&1 |
while read -r changed_path; do
  case "$changed_path" in
    *.kicad_pcb | *.scad)
      echo "[watch] change detected: $changed_path"
      /preview/scripts/export.sh
      ;;
    *)
      # Ignore unrelated files (READMEs, .kicad_pro/.kicad_prl siblings, etc).
      ;;
  esac
done

# If inotifywait itself ever exits (e.g. the watched directory was removed),
# fall through here -- keep the HTTP server as the thing keeping the
# container alive rather than exiting immediately.
echo "[watch] watcher loop ended; keeping HTTP server running" >&2
wait "$HTTP_PID"
