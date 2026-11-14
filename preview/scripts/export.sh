#!/usr/bin/env bash
# Exports hardware/*.kicad_pcb and enclosure/*.scad into GLB models (plus a
# 2D PCB render) under $SITE_DIR, then writes status.json with the export
# timestamp so the web page can show "last updated" and cache-bust models.
#
# Picks the first matching file in each directory (sorted by name) -- today
# that's the placeholder seed file; once the real design files land from
# pilink-7el/pilink-8hx this picks those up with no changes needed here.
set -uo pipefail

SITE_DIR="${SITE_DIR:-/preview/site}"
HARDWARE_DIR="${HARDWARE_DIR:-/work/hardware}"
ENCLOSURE_DIR="${ENCLOSURE_DIR:-/work/enclosure}"

mkdir -p "$SITE_DIR/models" "$SITE_DIR/renders"

export_pcb() {
  local pcb
  pcb=$(find "$HARDWARE_DIR" -maxdepth 1 -name '*.kicad_pcb' 2>/dev/null | sort | head -n1)
  if [[ -z "$pcb" ]]; then
    echo "[export] no .kicad_pcb file found in $HARDWARE_DIR yet"
    return 0
  fi
  echo "[export] PCB source: $pcb"

  if kicad-cli pcb export glb --subst-models -f -o "$SITE_DIR/models/pcb.glb" "$pcb" 2>&1; then
    echo "[export] wrote $SITE_DIR/models/pcb.glb"
  else
    echo "[export] WARNING: kicad-cli glb export failed for $pcb" >&2
  fi

  # Note: unlike `pcb export glb`, `pcb export svg` has no -f/--force flag;
  # it overwrites the output file unprompted, so just remove any stale one
  # first in case a previous run left a directory or unreadable file there.
  rm -f "$SITE_DIR/renders/pcb.svg"
  if kicad-cli pcb export svg --layers "Edge.Cuts,F.Cu,F.SilkS,F.Mask" \
      -o "$SITE_DIR/renders/pcb.svg" "$pcb" 2>&1; then
    echo "[export] wrote $SITE_DIR/renders/pcb.svg"
  else
    echo "[export] WARNING: kicad-cli svg export failed for $pcb" >&2
  fi
}

export_enclosure() {
  local scad tmp_stl
  scad=$(find "$ENCLOSURE_DIR" -maxdepth 1 -name '*.scad' 2>/dev/null | sort | head -n1)
  if [[ -z "$scad" ]]; then
    echo "[export] no .scad file found in $ENCLOSURE_DIR yet"
    return 0
  fi
  echo "[export] enclosure source: $scad"

  tmp_stl="$(mktemp --suffix=.stl)"
  if openscad -o "$tmp_stl" "$scad" 2>&1; then
    if python3 -c "
import sys
import trimesh
trimesh.load(sys.argv[1]).export(sys.argv[2])
" "$tmp_stl" "$SITE_DIR/models/enclosure.glb"; then
      echo "[export] wrote $SITE_DIR/models/enclosure.glb"
    else
      echo "[export] WARNING: trimesh stl->glb conversion failed for $scad" >&2
    fi
  else
    echo "[export] WARNING: openscad render failed for $scad" >&2
  fi
  rm -f "$tmp_stl"
}

export_pcb
export_enclosure

printf '{"last_export": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$SITE_DIR/status.json"
echo "[export] status.json updated: $(cat "$SITE_DIR/status.json")"
