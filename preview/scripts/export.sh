#!/usr/bin/env bash
# Exports hardware/*.kicad_pcb and enclosure/*.scad into GLB models (plus a
# 2D PCB render), and the root hardware/*.kicad_sch schematic sheet into a
# PDF, under $SITE_DIR, then writes status.json with the export timestamp so
# the web page can show "last updated" and cache-bust models.
#
# The PCB is the first *.kicad_pcb by name. The enclosure is every part --
# export_enclosure.py knows the part list and how each is placed. The
# schematic is picked specially too: a KiCad project has one root sheet plus
# several child sheet files (all *.kicad_sch), so picking "first by name"
# would be wrong -- see export_schematic() below for how the root is found.
set -uo pipefail

SITE_DIR="${SITE_DIR:-/preview/site}"
HARDWARE_DIR="${HARDWARE_DIR:-/work/hardware}"
ENCLOSURE_DIR="${ENCLOSURE_DIR:-/work/enclosure}"

mkdir -p "$SITE_DIR/models" "$SITE_DIR/renders"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

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

  # --include-{tracks,pads,zones} are off by default (board body + 3D
  # component models only) -- without them copper, pads, vias and the GND
  # pours are invisible in the GLB, not just low-contrast.
  #
  # The raw export is heavy for a browser (~13.5MB, ~17k separate primitives
  # -- one per track segment/pad/via/zone fragment; the draw-call count, not
  # the ~210k triangles, is what made it lag on phones). gltf-transform
  # `optimize` joins same-material meshes (-> 3 draw calls) and applies
  # meshopt compression (-> ~1.1MB). --simplify false keeps geometry exact so
  # thin traces aren't distorted; it only saved ~0.3MB anyway. --instance
  # false because model-viewer frames the camera on the un-instanced mesh
  # bounds with EXT_mesh_gpu_instancing, so the board showed up as a speck.
  # If optimize fails for any reason, fall back to serving the raw export.
  # The raw export is kept in $WORK_DIR for export_enclosure's assembly view
  # (trimesh can't read the meshopt-compressed copy).
  local raw_glb="$WORK_DIR/pcb-raw.glb"
  if kicad-cli pcb export glb --subst-models -f \
      --include-tracks --include-pads --include-zones \
      -o "$raw_glb" "$pcb" 2>&1; then
    if gltf-transform optimize "$raw_glb" "$SITE_DIR/models/pcb.glb" \
        --compress meshopt --texture-compress false --simplify false \
        --instance false 2>&1; then
      echo "[export] wrote $SITE_DIR/models/pcb.glb (optimized)"
    else
      echo "[export] WARNING: gltf-transform optimize failed; serving raw GLB" >&2
      cp -f "$raw_glb" "$SITE_DIR/models/pcb.glb"
    fi
  else
    echo "[export] WARNING: kicad-cli glb export failed for $pcb" >&2
    rm -f "$raw_glb"
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
  # Renders every enclosure part (not just one .scad file) and builds one
  # GLB per part plus assembly.glb (all parts in place, with the PCB when
  # $WORK_DIR/pcb-raw.glb exists) -- see export_enclosure.py for the frames
  # and placements. Each GLB is then meshopt-compressed the same way as
  # pcb.glb. Built in a staging dir and swapped in at the end so the page
  # never sees a half-written set.
  if ! find "$ENCLOSURE_DIR" -maxdepth 1 -name '*.scad' 2>/dev/null | grep -q .; then
    echo "[export] no .scad file found in $ENCLOSURE_DIR yet"
    return 0
  fi
  local stage="$WORK_DIR/enclosure" out="$SITE_DIR/models/enclosure" pcb f
  mkdir -p "$stage/raw" "$stage/opt"
  pcb=$(find "$HARDWARE_DIR" -maxdepth 1 -name '*.kicad_pcb' 2>/dev/null | sort | head -n1)
  if ! python3 /preview/scripts/export_enclosure.py "$ENCLOSURE_DIR" "$stage/raw" \
      "$WORK_DIR/pcb-raw.glb" "$pcb" 2>&1; then
    echo "[export] WARNING: some enclosure parts failed to render (see above)" >&2
  fi
  [[ -f "$stage/raw/parts.json" ]] || return 0
  cp -f "$stage/raw/parts.json" "$stage/opt/parts.json"
  for f in "$stage"/raw/*.glb; do
    [[ -e "$f" ]] || continue
    # --simplify false keeps printed-part geometry exact; --instance false
    # for the same model-viewer framing reason as pcb.glb.
    if ! gltf-transform optimize "$f" "$stage/opt/$(basename "$f")" \
        --compress meshopt --texture-compress false --simplify false \
        --instance false >/dev/null 2>&1; then
      echo "[export] WARNING: gltf-transform optimize failed for $(basename "$f"); serving raw" >&2
      cp -f "$f" "$stage/opt/"
    fi
  done
  rm -rf "$out.old"
  [[ -d "$out" ]] && mv -f "$out" "$out.old"
  mv -f "$stage/opt" "$out" && rm -rf "$out.old"
  echo "[export] wrote $(ls "$out" | grep -c '\.glb$') enclosure GLBs to $out"
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

export_fab() {
  # JLCPCB fab files (Gerber zip, BOM, CPL) + enclosure STLs -- see
  # export_fab.py. Runs after export_enclosure so the STLs it rendered
  # (kept in $WORK_DIR/enclosure/raw/stl) are available. Staged, then swapped.
  # Sets FAB_STATUS (ok | failed | skipped), shown on the page: a failed run
  # keeps serving the previous files, so the page must be told they are stale.
  # site/fab is a symlink to site/fab.d/<timestamp>, swapped with an atomic
  # rename, so a download never sees a half-written or missing directory.
  local pcb sch bom_md="$HARDWARE_DIR/BOM.md" ts new
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  new="$SITE_DIR/fab.d/$ts"
  pcb=$(find "$HARDWARE_DIR" -maxdepth 1 -name '*.kicad_pcb' 2>/dev/null | sort | head -n1)
  sch=$(find_root_schematic)
  if [[ -z "$pcb" || -z "$sch" || ! -f "$bom_md" ]]; then
    echo "[export] no PCB/schematic/BOM.md yet; skipping fab files"
    FAB_STATUS=skipped
    return 0
  fi
  # Source commit: the compose file mounts ../.git read-only at /work/gitdir
  # (a file, not a dir, in a git worktree -> commit stays "unknown").
  local commit="unknown" dirty=""
  if [[ -d /work/gitdir ]]; then
    local g=(git --git-dir=/work/gitdir --work-tree=/work -c safe.directory='*')
    commit=$("${g[@]}" rev-parse --short=10 HEAD 2>/dev/null || echo unknown)
    # --porcelain with untracked files listed: modified, staged and new files
    # under hardware/ and enclosure/ all count as "uncommitted changes".
    if [[ -n "$("${g[@]}" --no-optional-locks status --porcelain --untracked-files=all -- hardware enclosure 2>/dev/null)" ]]; then
      dirty=" (+ uncommitted changes)"
    fi
  fi
  mkdir -p "$SITE_DIR/fab.d"
  if FAB_SOURCE_COMMIT="$commit$dirty" python3 /preview/scripts/export_fab.py \
      "$pcb" "$sch" "$bom_md" "$WORK_DIR/enclosure/raw" "$new" 2>&1; then
    # ln + rename over the old symlink is atomic (rename(2)); a pre-existing
    # real fab/ directory from an older version is removed once.
    [[ -d "$SITE_DIR/fab" && ! -L "$SITE_DIR/fab" ]] && rm -rf "$SITE_DIR/fab"
    ln -s "fab.d/$ts" "$SITE_DIR/fab.tmp" && mv -T "$SITE_DIR/fab.tmp" "$SITE_DIR/fab"
    # Keep only the two newest generations (the previous one may still be
    # mid-download).
    ls -1d "$SITE_DIR"/fab.d/*/ 2>/dev/null | sort -r | tail -n +3 | xargs -r rm -rf
    FAB_STATUS=ok
    echo "[export] wrote fab files to $new"
  else
    rm -rf "$new"
    FAB_STATUS=failed
    echo "[export] WARNING: fab file export failed (see above); the previous files stay served and are marked stale" >&2
  fi
}

FAB_STATUS=skipped
export_pcb
export_enclosure
export_schematic
export_fab

printf '{"last_export": "%s", "fab_status": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$FAB_STATUS" > "$SITE_DIR/status.json"
echo "[export] status.json updated: $(cat "$SITE_DIR/status.json")"
