# Hardware preview service

A local docker-compose service that watches `../hardware/*.kicad_pcb`,
`../hardware/*.kicad_sch` and `../enclosure/*.scad` for changes, re-exports
the PCB to GLB (plus a 2D render) and the root schematic sheet to PDF, and
serves a page with Google's `<model-viewer>` web component so you can check
design progress in a browser without asking Claude -- on this machine or on
your phone over the LAN.

## Run it

```sh
cd preview
docker compose up --build
```

Then visit `http://<this-machine's-LAN-IP>:8788/` (or `http://localhost:8788/`).
The port is bound on `0.0.0.0`, so it's reachable from other devices on the
same network. (Host port is 8788, not 8787, to dodge a clash with something
else already using 8787 on the host; change the left side of the `ports:`
mapping in `docker-compose.yml` if 8788 is also taken on your machine.)

Edit `hardware/*.kicad_pcb`, any `hardware/*.kicad_sch` sheet, or
`enclosure/*.scad` while the stack is running and the page updates within a
few seconds -- no restart needed.

## How it works

- Base image: `kicad/kicad:10.0` (ships `kicad-cli`), plus `openscad`,
  `trimesh` (pip; for STL -> GLB, since OpenSCAD has no native glTF
  export) and `inotify-tools` (file watcher), installed in `Dockerfile`.
- `scripts/export.sh` finds the first `*.kicad_pcb` under `hardware/` and
  exports it straight to GLB (and a 2D SVG render) via `kicad-cli`. It then
  runs `scripts/export_enclosure.py`, which renders every enclosure part
  (front shell, back shell + base strip, both legs, knob, button plunger,
  antenna mount) to STL via `openscad` (in parallel), converts them with
  `trimesh` into one coloured GLB per part plus `assembly.glb` -- every part
  in its assembled position, with the PCB placed using the .scad files' own
  face mapping (`X = board_x + 2`, `Q = 52 - board_y`, PCB front surface
  7.5mm behind the outer face) and the 15 degree lean -- and a
  `parts.json` manifest the page's part picker is built from. Each GLB is
  meshopt-compressed like the PCB one. It also finds the root
  schematic sheet (the `*.kicad_sch` whose basename matches the project's
  `*.kicad_pro` file -- the project's child sheets are separate `.kicad_sch`
  files that would sort first alphabetically, so a name match against the
  `.kicad_pro` is used to pick the root rather than picking the first file by
  name) and exports it to a single PDF via `kicad-cli sch export pdf`, which
  pulls in every hierarchical child sheet as extra pages.
- The PCB GLB (copper tracks, pads, vias and zones/GND pours included) is
  post-processed with `gltf-transform optimize` (meshopt compression, no
  simplification): the raw `kicad-cli` export is ~13.5MB in ~17k separate
  primitives, which lags in the browser; optimized it's ~1.1MB in 3 draw
  calls with identical geometry. `site/index.html` points `<model-viewer>`
  at the vendored meshopt decoder.
- `scripts/entrypoint.sh` runs that export once, starts a plain
  `python3 -m http.server` on `0.0.0.0:$PORT`, then runs `inotifywait` in
  monitor mode against the mounted `hardware/`/`enclosure/` directories and
  re-runs the export whenever a `.kicad_pcb`, `.kicad_sch` or `.scad` file
  changes.
- `site/index.html` polls `/status.json` every 5s for the last export
  timestamp and cache-busts the `<model-viewer>`/image/PDF URLs when it
  changes, so the page updates live without a manual refresh (a plain
  refresh works too).

## Adding enclosure parts

`export_enclosure.py` has an explicit part list (`PARTS` plus each part's
placement) rather than globbing `enclosure/*.scad`, because each file uses
its own frame and some need a `-D PART=...` flag or a wrapper. A new part
file needs an entry there to show up.

## Known cosmetic issue

Some `kicad-cli` builds export PCB GLB models with all faces white (copper
layer colors not preserved in the GLB material). This is cosmetic only and
not something this pipeline works around.
