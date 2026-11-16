#!/usr/bin/env bash
# Exports hardware/*.kicad_pcb and enclosure/*.scad into GLB models (plus a
# 2D PCB render), and the root hardware/*.kicad_sch schematic sheet into a
# PDF, under $SITE_DIR, then writes status.json with the export timestamp so
# the web page can show "last updated" and cache-bust models.
#
# Picks the first matching file in each directory (sorted by name) -- today
# that's the placeholder seed file; once the real design files land from
# pilink-7el/pilink-8hx this picks those up with no changes needed here.
# The schematic is the exception: a KiCad project has one root sheet plus
# several child sheet files (all *.kicad_sch), so picking "first by name"
# would be wrong -- see export_schematic() below for how the root is found.
set -uo pipefail

SITE_DIR="${SITE_DIR:-/preview/site}"
HARDWARE_DIR="${HARDWARE_DIR:-/work/hardware}"
ENCLOSURE_DIR="${ENCLOSURE_DIR:-/work/enclosure}"

mkdir -p "$SITE_DIR/models" "$SITE_DIR/renders"

find_root_schematic() {
  # A KiCad project's root schematic shares its basename with the .kicad_pro
  # project file; every other *.kicad_sch under hardware/ is a child sheet
  # (display.kicad_sch, esp32_bt.kicad_sch, etc). Exporting PDF from the root
  # pulls in all hierarchical child sheets as extra pages in one file, so we
  # must find that specific file rather than picking "first by name".
  local proj
  proj=$(find "$HARDWARE_DIR" -maxdepth 1 -name '*.kicad_pro' 2>/dev/null | sort | head -n1)
  if [[ -n "$proj" ]]; then
    local candidate="${proj%.kicad_pro}.kicad_sch"
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  fi
  # Fallback (no .kicad_pro yet, or no matching sheet): first .kicad_sch by
  # name, with a warning since it may not be the root sheet.
  find "$HARDWARE_DIR" -maxdepth 1 -name '*.kicad_sch' 2>/dev/null | sort | head -n1
}

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
  #
  # Two separate renders, front and back: a single combined render can only
  # show one copper layer's own traces (whichever layer list is passed) --
  # on a 2-layer board, routing on the layer left out is simply absent from
  # the image, not just low-contrast. B.Cu is mirrored so it reads correctly
  # as "looking at the back of the board," matching how B.Cu-mounted parts
  # (e.g. J401) are actually oriented.
  rm -f "$SITE_DIR/renders/pcb-front.svg" "$SITE_DIR/renders/pcb-back.svg"
  if kicad-cli pcb export svg --layers "Edge.Cuts,F.Cu,F.SilkS,F.Mask" \
      -o "$SITE_DIR/renders/pcb-front.svg" "$pcb" 2>&1; then
    echo "[export] wrote $SITE_DIR/renders/pcb-front.svg"
  else
    echo "[export] WARNING: kicad-cli svg export (front) failed for $pcb" >&2
  fi
  if kicad-cli pcb export svg --layers "Edge.Cuts,B.Cu,B.SilkS,B.Mask" --mirror \
      -o "$SITE_DIR/renders/pcb-back.svg" "$pcb" 2>&1; then
    echo "[export] wrote $SITE_DIR/renders/pcb-back.svg"
  else
    echo "[export] WARNING: kicad-cli svg export (back) failed for $pcb" >&2
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

export_schematic() {
  local sch
  sch=$(find_root_schematic)
  if [[ -z "$sch" ]]; then
    echo "[export] no .kicad_sch file found in $HARDWARE_DIR yet"
    return 0
  fi
  echo "[export] schematic source: $sch"

  if kicad-cli sch export pdf -o "$SITE_DIR/renders/schematic.pdf" "$sch" 2>&1; then
    echo "[export] wrote $SITE_DIR/renders/schematic.pdf"
  else
    echo "[export] WARNING: kicad-cli pdf export failed for $sch" >&2
  fi
}

export_pcb
export_enclosure
export_schematic

printf '{"last_export": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$SITE_DIR/status.json"
echo "[export] status.json updated: $(cat "$SITE_DIR/status.json")"
