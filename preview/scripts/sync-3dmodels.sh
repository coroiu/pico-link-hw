#!/usr/bin/env bash
# Host-side: copies the 3D models the board actually references from the
# host's KiCad library into preview/.3dmodels/ (gitignored), which
# docker-compose mounts into the container. Snap-confined Docker can't
# bind-mount /usr/share directly, and the full library is ~5GB, so only the
# referenced files are copied. Re-run after adding footprints.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
repo="$(git -C "$here" rev-parse --show-toplevel)"
src="${KICAD_3DMODEL_HOST_DIR:-/usr/share/kicad/3dmodels}"
dst="$here/.3dmodels"

# Referenced names with no model in KiCad's stock library -> nearest
# same-body stand-in, copied under the referenced name.
declare -A ALIAS=(
  [RF_Module.3dshapes/ESP32-WROOM-32UE]=RF_Module.3dshapes/ESP32-WROOM-32U
  [Package_SO.3dshapes/SOIC-8_5.23x5.23mm_P1.27mm]=Package_SO.3dshapes/SOIC-8_5.275x5.275mm_P1.27mm
  [Inductor_SMD.3dshapes/L_Coilcraft_LPS4018]=Inductor_SMD.3dshapes/L_Cenker_CKCS4018
)

mkdir -p "$dst"
grep -ho '(model "[^"]*"' "$repo"/hardware/*.kicad_pcb \
  | sed 's/(model "//; s/"$//; s/^\${[^}]*}\///; s/\.[^.]*$//' \
  | sort -u \
  | while read -r rel; do
      from="${ALIAS[$rel]:-$rel}"
      found=0
      for ext in wrl step; do
        if [[ -f "$src/$from.$ext" ]]; then
          mkdir -p "$dst/$(dirname "$rel")"
          cp -f "$src/$from.$ext" "$dst/$rel.$ext"
          found=1
        fi
      done
      [[ $found == 1 ]] || echo "[sync-3dmodels] no model for $rel" >&2
    done

echo "[sync-3dmodels] $(find "$dst" -type f | wc -l) files in $dst"
