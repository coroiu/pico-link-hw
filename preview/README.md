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

- Base image: `kicad/kicad:8.0` (ships `kicad-cli`), plus `openscad`,
  `python3-trimesh` (for STL -> GLB, since OpenSCAD has no native glTF
  export) and `inotify-tools` (file watcher), installed in `Dockerfile`.
- `scripts/export.sh` finds the first `*.kicad_pcb` under `hardware/` and the
  first `*.scad` under `enclosure/`, exports the PCB straight to GLB (and a
  2D SVG render) via `kicad-cli`, and renders the enclosure to STL via
  `openscad` then converts STL -> GLB via `trimesh`. It also finds the root
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

## Seed/placeholder files

`hardware/placeholder.kicad_pcb` was deleted when the real, placed and
routed PCB landed (`pilink-7el.12`); the pipeline now picks up
`hardware/pico-link-hw.kicad_pcb` instead. `enclosure/` still only contains
a placeholder design file (`cube.scad`) -- the real enclosure lands via a
separate epic (`pilink-8hx`). The pipeline picks up whatever matching file
it finds, so no changes are needed here once that lands either.

## Known cosmetic issue

Some `kicad-cli` builds export PCB GLB models with all faces white (copper
layer colors not preserved in the GLB material). This is cosmetic only and
not something this pipeline works around.
