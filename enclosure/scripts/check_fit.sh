#!/usr/bin/env bash
# Run the CAD-level enclosure fit check (check_fit.py).
#
#   enclosure/scripts/check_fit.sh [check_fit.py args, e.g. --reuse --json out.json]
#
# Host route: used when `openscad` is on PATH and python3 can import pcbnew,
# trimesh, manifold3d, scipy and rtree. Otherwise falls back to the preview
# docker image (has openscad + pcbnew + trimesh) under its own compose
# project, leaving a running `preview` service untouched. Snap docker can only
# bind-mount paths under /home, so run from a checkout under /home. Generated
# STLs go to $FITCHECK_WORK (default a fresh mktemp dir on the host; in the
# container they are throwaway unless FITCHECK_WORK names a directory to
# bind-mount) -- never into the repo. Exit status is non-zero if any check
# FAILs.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
if command -v openscad >/dev/null 2>&1 && \
   python3 -c "import pcbnew, trimesh, manifold3d, scipy, rtree" >/dev/null 2>&1; then
  cd "$ROOT"
  exec python3 enclosure/scripts/check_fit.py --enclosure enclosure \
    --pcb hardware/pico-link-hw.kicad_pcb --work "${FITCHECK_WORK:-$(mktemp -d)}" "$@"
fi
cd "$ROOT/preview"
exec docker compose -p scadcheck run --rm --entrypoint bash \
  -v "$ROOT/enclosure:/work/enclosure:ro" \
  -v "$ROOT/hardware:/work/hardware:ro" \
  ${FITCHECK_WORK:+-v "$FITCHECK_WORK:/fitwork"} \
  preview -c '
set -e
python3 -c "import manifold3d, scipy, rtree" 2>/dev/null || \
  pip install --break-system-packages -q manifold3d scipy rtree 2>&1 | grep -v WARNING || true
cd /work
python3 enclosure/scripts/check_fit.py --enclosure enclosure --pcb hardware/pico-link-hw.kicad_pcb --work "$([ -d /fitwork ] && echo /fitwork || mktemp -d)" "$@"
' bash "$@"
