#!/usr/bin/env bash
# Run the CAD-level enclosure fit check (check_fit.py).
#
#   enclosure/scripts/check_fit.sh [check_fit.py args, e.g. --reuse --json out.json]
#
# Host route: used when `openscad` is on PATH and python3 can import pcbnew,
# trimesh, manifold3d, scipy and rtree. Otherwise falls back to the preview
# docker image (has openscad + pcbnew + trimesh) under its own compose
# project, leaving a running `preview` service untouched. The first docker
# run builds that image (~3GB, several minutes); the extra python deps
# (manifold3d scipy rtree) are pip-installed ONCE into a host cache dir
# ($FITCHECK_PYDEPS, default ~/.cache/pilink-fitcheck-pydeps) and reused, so
# later runs need no network. The `<project>_default` compose network created
# by `run` is removed on exit. Snap docker can only bind-mount paths under
# /home, so run from a checkout under /home and keep the cache under /home.
# Generated STLs go to $FITCHECK_WORK (default a fresh mktemp dir on the host;
# in the container they are throwaway unless FITCHECK_WORK names a directory
# to bind-mount) -- never into the repo. Exit status is non-zero if any check
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
PYDEPS="${FITCHECK_PYDEPS:-${XDG_CACHE_HOME:-$HOME/.cache}/pilink-fitcheck-pydeps}"
mkdir -p "$PYDEPS"
cleanup() { docker network rm scadcheck_default >/dev/null 2>&1 || true; }
trap cleanup EXIT
cd "$ROOT/preview"
# Not `exec`, so the trap above runs and the network is cleaned up.
# Run as the host user so the pip cache / work dir are not root-owned.
docker compose -p scadcheck run --rm --entrypoint bash \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$ROOT/enclosure:/work/enclosure:ro" \
  -v "$ROOT/hardware:/work/hardware:ro" \
  -v "$PYDEPS:/pydeps" \
  ${FITCHECK_WORK:+-v "$FITCHECK_WORK:/fitwork"} \
  preview -c '
set -e
export PYTHONPATH=/pydeps${PYTHONPATH:+:$PYTHONPATH}
python3 -c "import manifold3d, scipy, rtree" 2>/dev/null || \
  pip install --break-system-packages -q --no-cache-dir --target /pydeps manifold3d scipy rtree 2>&1 | grep -v WARNING || true
cd /work
python3 enclosure/scripts/check_fit.py --enclosure enclosure --pcb hardware/pico-link-hw.kicad_pcb --work "$([ -d /fitwork ] && echo /fitwork || mktemp -d)" "$@"
' bash "$@"
