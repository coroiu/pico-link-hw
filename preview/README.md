# Hardware preview service

A local docker-compose service that watches `../hardware/*.kicad_pcb` and
`../enclosure/*.scad` for changes, re-exports both to GLB (plus a 2D PCB
render), and serves a page with Google's `<model-viewer>` web component so
you can check design progress in a browser without asking Claude -- on this
machine or on your phone over the LAN.

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

Edit `hardware/*.kicad_pcb` or `enclosure/*.scad` while the stack is running
and the page updates within a few seconds -- no restart needed.

## How it works

- Base image: `kicad/kicad:8.0` (ships `kicad-cli`), plus `openscad`,
  `python3-trimesh` (for STL -> GLB, since OpenSCAD has no native glTF
  export) and `inotify-tools` (file watcher), installed in `Dockerfile`.
- `scripts/export.sh` finds the first `*.kicad_pcb` under `hardware/` and the
  first `*.scad` under `enclosure/`, exports the PCB straight to GLB (and a
  2D SVG render) via `kicad-cli`, and renders the enclosure to STL via
  `openscad` then converts STL -> GLB via `trimesh`.
- `scripts/entrypoint.sh` runs that export once, starts a plain
  `python3 -m http.server` on `0.0.0.0:$PORT`, then runs `inotifywait` in
  monitor mode against the mounted `hardware/`/`enclosure/` directories and
  re-runs the export whenever a `.kicad_pcb` or `.scad` file changes.
- `site/index.html` polls `/status.json` every 5s for the last export
  timestamp and cache-busts the `<model-viewer>`/image URLs when it changes,
  so the page updates live without a manual refresh (a plain refresh works
  too).

## Seed/placeholder files

`hardware/` and `enclosure/` only contain placeholder design files today
(`placeholder.kicad_pcb`, `cube.scad`) -- the real PCB and enclosure land via
separate epics. The pipeline picks up whatever matching file it finds, so no
changes are needed here once real design files replace the placeholders.

## Known cosmetic issue

Some `kicad-cli` builds export PCB GLB models with all faces white (copper
layer colors not preserved in the GLB material). This is cosmetic only and
not something this pipeline works around.
