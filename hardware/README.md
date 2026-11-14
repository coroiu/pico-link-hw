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

All six child sheets started out intentionally empty — no components, no
nets — so later beads can populate them independently. See "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md)
for subsystem scope, and `.planning/decisions/` for the component choices
already settled (MCU, radio coprocessor, display, memory, and the
2026-11-14 d-pad-instead-of-joystick input decision).

### Power subsystem (pilink-7el.2)

`power.kicad_sch` now has the 3.3V rail: USB-C 5V in (via a `+5V`/`PWR_FLAG`
pair, pending the USB-C sheet, pilink-7el.7) through an AMS1117-3.3 (SOT-223,
JLCPCB Basic part C6186/LCSC C6186) to a single `+3V3` rail, with a 10uF
input bulk cap (C1), a 22uF output bulk cap (C2, per the AMS1117
datasheet's stability requirement), and a 100nF local decoupler (C3) at
the point of load.
Component choice and decoupling values are cross-checked against Raspberry
Pi's own official RP2350B minimal reference design and RP2350 Hardware
Design Guide (RP-008280-DS) — see the citations in the sheet's own text
notes. RP2350B's internal 3.3V→1.1V switched-mode core regulator (inductor,
feedback caps) and its per-pin VDD3V3/IOVDD decoupling belong on the
RP2350B + Memory sheet (pilink-7el.3), not here, matching the same split
used in Raspberry Pi's reference design.

Unlike the rest of this skeleton, this sheet **was** validated with the real
tools: `kicad-cli sch erc --severity-all --exit-code-violations` reports 0
violations on both `power.kicad_sch` and the root `pico-link-hw.kicad_sch`,
and the exported PDF was visually checked for a sane, non-overlapping
layout. The other five child sheets remain unverified skeletons.

**Blind-authoring caveat (the five still-empty child sheets):** neither
KiCad nor `kicad-cli` was available in the agent environment the project
skeleton was written in. Those files were hand-authored as KiCad 8
S-expression/JSON text, cross-checked against KiCad's own file-format docs
and real KiCad-8-generated project files pulled from public repos — not
written, opened, or validated by the actual KiCad GUI. `kicad-cli` **is**
available now (KiCad 8.0.9) and was used for `power.kicad_sch` and the root
sheet's hierarchy (see above); the same validation still needs to happen
for the five remaining empty child sheets before trusting or building on
them. If anything fails to parse, that's a bug in this skeleton, not a
sign the approach is wrong.

PCB routing, DRC/ERC, and gerber export still need to happen in the KiCad GUI
on a machine that has it installed — same caveat as before, now narrowed to
"the skeleton needs a first open" rather than "nothing exists yet".

`placeholder.kicad_pcb` is a trivial seed file (just a 20x20mm board outline,
no components) for the `preview/` docker-compose service — it proves the
PCB -> GLB export pipeline end-to-end before the real board exists. Delete it
once the real PCB from pilink-7el lands; the preview pipeline picks up
whatever `*.kicad_pcb` file it finds here.
