# Hardware

KiCad project goes here: schematic, PCB layout, footprints, and a BOM with
JLCPCB/LCSC part numbers.

## Project skeleton (pilink-7el.1)

`pico-link-hw.kicad_pro` / `pico-link-hw.kicad_sch` is the root KiCad 8
project. The root sheet holds one hierarchical sheet symbol per subsystem,
each pointing at its own (currently empty) child `.kicad_sch`:

- `power.kicad_sch` — power subsystem (pilink-7el.2)
- `rp2350b_memory.kicad_sch` — RP2350B + flash/PSRAM (pilink-7el.3)
- `esp32_bt.kicad_sch` — ESP32-WROOM-32U BT coprocessor (pilink-7el.4)
- `display.kicad_sch` — ST7789V display (pilink-7el.5)
- `input.kicad_sch` — d-pad + buttons (pilink-7el.6)
- `usb_c.kicad_sch` — USB-C connector (pilink-7el.7)

All six child sheets are intentionally empty — no components, no nets — so
later beads can populate them independently. See "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md)
for subsystem scope, and `.planning/decisions/` for the component choices
already settled (MCU, radio coprocessor, display, memory, and the
2026-11-14 d-pad-instead-of-joystick input decision).

**Blind-authoring caveat:** neither KiCad nor `kicad-cli` is available in the
agent environment these files were written in. They were hand-authored as
KiCad 8 S-expression/JSON text, cross-checked against KiCad's own file-format
docs and real KiCad-8-generated project files pulled from public repos — not
written, opened, or validated by the actual KiCad GUI. **Open this project in
real KiCad 8 and confirm it loads cleanly (and run ERC) before trusting it or
building on it.** If anything fails to parse, that's a bug in this skeleton,
not a sign the approach is wrong.

PCB routing, DRC/ERC, and gerber export still need to happen in the KiCad GUI
on a machine that has it installed — same caveat as before, now narrowed to
"the skeleton needs a first open" rather than "nothing exists yet".

`placeholder.kicad_pcb` is a trivial seed file (just a 20x20mm board outline,
no components) for the `preview/` docker-compose service — it proves the
PCB -> GLB export pipeline end-to-end before the real board exists. Delete it
once the real PCB from pilink-7el lands; the preview pipeline picks up
whatever `*.kicad_pcb` file it finds here.
