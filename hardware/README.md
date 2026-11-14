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
layout. The other four child sheets remain unverified skeletons.

### RP2350B + Memory subsystem (pilink-7el.3)

`rp2350b_memory.kicad_sch` now has the RP2350B (QFN-80), 12MHz crystal
(Abracon ABM8-272-T3), BOOTSEL + reset buttons, 16MB QSPI NOR flash
(Winbond W25Q128JVS) and 8MB QSPI PSRAM (AP Memory APS6404L-3SQR-ZR), plus
the RP2350B-specific decoupling flagged as out-of-scope at the end of
`power.kicad_sch`'s own notes: the internal 3.3V→1.1V switched-mode core
regulator's inductor/caps (L1, C6/C7/C9, R3) and the ~12 individual 100nF
VDD3V3/IOVDD decouplers. Every value and part choice is cross-checked
against primary sources (Raspberry Pi's own RP2350B minimal reference
design, the RP2350 hardware design guide, Pimoroni's published Pico Plus 2
schematic, and distributor listings for the PSRAM's actual package) — see
the sheet's own text notes for citations, including two corrections to this
bead's own framing (the external LDO's bulk caps don't belong on this
sheet; the PSRAM's `-ZR` suffix is USON-8L, not SOIC-8).

U1's symbol and QFN-80 footprint come from Raspberry Pi's own historical
RP2350B minimal-reference-design KiCad archive (RP-006442-DD-2) — not the
third-party HDR/RP2350_KiCad repo flagged as "untested" in this bead's
acceptance criteria. The footprint is copied into
`hardware/footprints/RP2350_80QFN.pretty/` (registered in `fp-lib-table`);
the RP2350 and PSRAM symbols are also registered as proper project
libraries in `hardware/symbols/` + `sym-lib-table` so KiCad's GUI resolves
them instead of only trusting the schematic's embedded cache.

Every RP2350B GPIO not consumed by this sheet is brought out as a global
label matching its pin name, so the other still-empty child sheets can pick
it up later without hierarchical sheet pins (GPIO47 is the one exception —
it's committed to the PSRAM's chip-select here).

`kicad-cli sch erc --severity-all` on this sheet **alone** reports 2 errors
(`power_pin_not_driven` for `+3V3`/`GND`) and 54 warnings; both are expected
and documented in the sheet's own notes — this sheet doesn't generate
`+3V3`/`GND` (power.kicad_sch does), so a standalone, single-sheet ERC run
can't see that driver, and 51 of the warnings are the intentional
not-yet-connected global labels for sibling sheets that don't exist yet.
`kicad-cli sch erc --severity-all` on the root `pico-link-hw.kicad_sch`
(which flattens the whole hierarchy and does see power.kicad_sch's
regulator) reports **0 errors**, 52 warnings (same justified global-label
and one benign library-cache-staleness notice). The exported PDF (on A2
paper — the 81-pin chip plus all its support circuitry doesn't fit A3) was
visually checked for a sane, non-overlapping layout.

### ESP32 BT coprocessor subsystem (pilink-7el.4)

`esp32_bt.kicad_sch` now has U201 (ESP32-WROOM-32U-N4, KiCad's built-in
`RF_Module:ESP32-WROOM-32U` symbol/footprint, pinout cross-checked pin-by-
pin against Espressif's own datasheet Table 3), EN strapping (R201 10k +
C203 1uF RC delay, per Espressif's Hardware Design Guidelines Schematic
Checklist), GPIO0/BOOT0 strapping (R202 10k pull-up only, no cap, per the
same checklist), and 3V3 decoupling (C201 10uF + C202 100nF). GPIO2 is
left floating (no pull), relying on its internal pull-down for Joint
Download Boot, matching stock ESP32 dev boards. (References here use the
200-299 block under this project's per-sheet reference-numbering scheme
--  power.kicad_sch keeps 1-99 (already merged as U1/C1/C2/C3/#PWR01-09),
rp2350b_memory.kicad_sch gets 100-199, and esp32_bt.kicad_sch gets
200-299 (U201, C201-C203, R201-R202, #PWR201-209) -- so no two sibling
sheets' components can ever merge into the same netlist part. KiCad
merges same-reference parts across sibling sheets into one netlist part,
so without non-overlapping ranges per sheet, reusing references would
silently corrupt the project netlist; see the PR review discussion on
pilink-7el.4 (and the matching fix on pilink-7el.3) for details.)

RP2350 interface: exposed via **global labels** (not hierarchical --
`esp32_bt.kicad_sch` and `rp2350b_memory.kicad_sch` are sibling child
sheets, so a hierarchical label would need root-sheet pin wiring that
doesn't exist yet; a global label joins same-named nets project-wide
without it): `ESP32_EN`, `ESP32_BOOT0`, `ESP32_HCI_TXD/RXD/RTS/CTS`,
`ESP32_FLASH_TXD0/RXD0`. See the sheet's own text notes for the full
rationale and citations. RP2350-side GPIO assignment is pilink-7el.3,
in progress in parallel -- this sheet does not touch
`rp2350b_memory.kicad_sch`.

Flash variant: ESP32-WROOM-32U-**N4** (JLCPCB/LCSC C328062). Sufficient for
an HCI-controller-only firmware image (no Wi-Fi/Bluedroid/display code);
live LCSC stock checked 2026-11-14 in the low thousands of units.

**Risk flag for the user/orchestrator:** Espressif's current datasheet
(v2.8, 2026-09-16) marks ESP32-WROOM-32U "NOT RECOMMENDED FOR NEW DESIGNS
(NRND)" -- not surfaced in the original ADR. Stock is still healthy and the
part is still in production, but Espressif steers new designs toward
ESP32-WROOM-32UE instead. This bead keeps the already-decided U variant
(re-opening that choice is out of scope here) but flags it for a decision
before PCB fab -- tracked as follow-up bead `pilink-8zj`.

Validated with `kicad-cli sch erc --severity-all --exit-code-violations`:
the **root** `pico-link-hw.kicad_sch` (whole-project, the check that
reflects real connectivity) reports 0 errors / 6 warnings, all
`global_label_dangling` on the RP2350-interface labels above -- expected,
since their other end (pilink-7el.3) doesn't exist yet. Checking
`esp32_bt.kicad_sch` **standalone** additionally reports 2
`power_pin_not_driven` errors on +3V3/GND -- an artifact of a single
non-root sheet not seeing power.kicad_sch's real AMS1117/GND driver, not a
real defect (confirmed by testing: adding a local PWR_FLAG to silence it
instead creates a genuine "two Power outputs on one net" conflict at the
root level, since a real driver already exists there). The exported PDF
was reviewed with `kicad-cli sch export pdf`/`export svg` plus the Read
tool for a non-overlapping layout (no pixel-rasterizer -- pdftoppm/
ImageMagick/Ghostscript -- was available in this environment to produce a
bitmap screenshot; the PDF's own text/geometry stream was inspected
instead).

**Blind-authoring caveat (the three still-empty child sheets):** neither
KiCad nor `kicad-cli` was available in the agent environment the project
skeleton was written in. Those files were hand-authored as KiCad 8
S-expression/JSON text, cross-checked against KiCad's own file-format docs
and real KiCad-8-generated project files pulled from public repos — not
written, opened, or validated by the actual KiCad GUI. `kicad-cli` **is**
available now (KiCad 8.0.9) and was used for `power.kicad_sch`,
`rp2350b_memory.kicad_sch`, `esp32_bt.kicad_sch`, and the root sheet's
hierarchy (see above); the same validation still needs to happen for the
three remaining empty child sheets before trusting or building on them. If
anything fails to parse, that's a bug in this skeleton, not a sign the
approach is wrong.

PCB routing, DRC/ERC, and gerber export still need to happen in the KiCad GUI
on a machine that has it installed — same caveat as before, now narrowed to
"the skeleton needs a first open" rather than "nothing exists yet".

`placeholder.kicad_pcb` is a trivial seed file (just a 20x20mm board outline,
no components) for the `preview/` docker-compose service — it proves the
PCB -> GLB export pipeline end-to-end before the real board exists. Delete it
once the real PCB from pilink-7el lands; the preview pipeline picks up
whatever `*.kicad_pcb` file it finds here.
