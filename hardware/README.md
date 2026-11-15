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
- `input.kicad_sch` — d-pad + buttons + volume encoder (pilink-7el.6, amended by pilink-cmn)
- `usb_c.kicad_sch` — USB-C connector (pilink-7el.7)

All six child sheets started out intentionally empty — no components, no
nets — so later beads can populate them independently. See "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md)
for subsystem scope, and `.planning/decisions/` for the component choices
already settled (MCU, radio coprocessor, display, memory, the 2026-11-14
d-pad-instead-of-joystick input decision, and the 2026-11-15
rotary-encoder-for-volume amendment).

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
regulator's inductor/caps (L101, C103/C104/C105, R104) and the ~12
individual 100nF VDD3V3/IOVDD decouplers. Every value and part choice is
cross-checked against primary sources (Raspberry Pi's own RP2350B minimal
reference design, the RP2350 hardware design guide, Pimoroni's published
Pico Plus 2 schematic, and distributor listings for the PSRAM's actual
package) — see the sheet's own text notes for citations, including two
corrections to this bead's own framing (the external LDO's bulk caps don't
belong on this sheet; the PSRAM's `-ZR` suffix is USON-8L, not SOIC-8).

U101's symbol and QFN-80 footprint come from Raspberry Pi's own historical
RP2350B minimal-reference-design KiCad archive (RP-006442-DD-2) — not the
third-party HDR/RP2350_KiCad repo flagged as "untested" in this bead's
acceptance criteria. (U101 is this sheet's RP2350B; `power.kicad_sch`'s
AMS1117 regulator is U1 — an earlier review round found the two had been
confused via a cross-sheet reference collision, fixed by renumbering this
whole sheet into the 100-199 block: U101-U103, C101-C121, R101-R105,
SW101-SW102, L101, Y101, with power.kicad_sch keeping 1-99 and
esp32_bt.kicad_sch taking 200-299; a netlist export confirms no reference
collides anywhere in the project hierarchy.) The footprint is copied into
`hardware/footprints/RP2350_80QFN.pretty/` (registered in `fp-lib-table`);
the RP2350 and PSRAM symbols are also registered as proper project
libraries in `hardware/symbols/` + `sym-lib-table` so KiCad's GUI resolves
them instead of only trusting the schematic's embedded cache.

Every RP2350B GPIO not consumed by this sheet is brought out as a global
label matching its pin name, so the other still-empty child sheets can pick
it up later without hierarchical sheet pins (GPIO47 is the one exception —
it's committed to the PSRAM's chip-select here).

`kicad-cli sch erc --severity-all` on this sheet **alone** reports 2 errors
(`power_pin_not_driven` for `+3V3`/`GND`, expected and documented in the
sheet's own notes — this sheet doesn't generate `+3V3`/`GND`,
`power.kicad_sch` does, so a standalone single-sheet ERC run can't see that
driver) and 53 warnings: 51 are the intentional not-yet-connected global
labels for sibling sheets that don't exist yet, and 2 are a pre-existing,
unrelated "library not configured" notice for this project's own custom
symbol libraries. `kicad-cli sch erc --severity-all` on the root
`pico-link-hw.kicad_sch` (which flattens the whole hierarchy — now
including `esp32_bt.kicad_sch` — and does see `power.kicad_sch`'s
regulator) reports **0 errors**, 57 warnings, all `global_label_dangling`
(51 from this sheet's own not-yet-wired GPIO/interface labels, 6 from
`esp32_bt.kicad_sch`'s — both expected until the remaining sibling sheets
exist). The stale "Symbol has been modified in library" notice from an
earlier round no longer appears; it was fixed by re-syncing the embedded
flash symbol to the stock library part.

Schematic connectivity (the netlist export and both ERC runs above) is
verified clean. The visual layout went through two review rounds of
reported cosmetic text/label overlaps — a text note overlapping nearby
component labels, a power-flag symbol sitting on top of a note, and a
couple of reference labels landing on top of net labels; none of these
affect the netlist or ERC results. Every overlap reported across both
rounds has now been moved into clear canvas space, and the sheet was
re-exported to SVG and visually re-checked after the fixes; none remain
as of this revision. This is still an agent-driven check against a
rendered export, not a human sign-off in the KiCad GUI, so treat it as a
good-faith check rather than a final layout approval.

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

### Input subsystem (pilink-7el.6, amended by pilink-cmn)

`input.kicad_sch` originally had the d-pad + button switches: 4 discrete
tact switches in a cross (UP/DOWN/LEFT/RIGHT) plus 4 discrete tact buttons
(A/B/X/Y) — no center-press switch, per
[`.planning/decisions/2026-11-14-dpad-instead-of-joystick.md`](../.planning/decisions/2026-11-14-dpad-instead-of-joystick.md)
(firmware must remap select/OK onto one of A/B/X/Y itself; that's
`pico-link`'s job, not this repo's). A 2026-11-15 amendment
([`.planning/decisions/2026-11-15-rotary-encoder-for-volume.md`](../.planning/decisions/2026-11-15-rotary-encoder-for-volume.md),
bead `pilink-cmn`) then replaced the LEFT/RIGHT pair with a single EC11-class
rotary encoder dedicated to volume (rotate = adjust, press = mute/toggle),
based on usage data showing LEFT/RIGHT went unused on the prototype. The
sheet now has **7 inputs**: UP/DOWN + A/B/X/Y (6 discrete tact switches,
unchanged) + 1 rotary encoder.

UP/DOWN/A/B/X/Y each still get their own external 10k pull-up
(R301/R302/R305-R308, `Resistor_SMD:R_0402_1005Metric`) from `+3V3` to their
GPIO node, with the switch itself (SW301/SW302/SW305-SW308, the same
`Switch:SW_Push`/`Button_Switch_SMD:SW_SPST_PTS645` part
`rp2350b_memory.kicad_sch` uses for BOOTSEL/reset) pulling that node to
`GND` when pressed — active-low. Unlike SW101/SW102 (which rely on the
boot-ROM's own `QSPI_SS` handling and `RUN`'s internal pull-up, and fit no
external pull-up), ordinary GPIOs have no such guaranteed default pull
state, hence the explicit external resistor on all of these switches.

**Rotary encoder (SW303):** Alps Alpine **EC11E18244AU** (JLCPCB/LCSC
`C202365`, Extended-library part — standard extended-part handling fee,
not a sourcing-availability risk). Verified against Alps' own published
datasheet (hosted copy at `lcsc.com/datasheet/C202365.pdf`): vertical
structure, flat actuator, 20mm actuator length, 36 detents / 18 pulses,
two-phase incremental output (terminals A, B, common C), integrated
push-on switch (SPST, 0.5mm travel, 0.1A/5V DC rating, datasheet terminals
D/E mapped onto this sheet's S1/S2), 10mA/5V DC max overall rating, **no
internal pull resistors**. Symbol: stock KiCad library
`Device:RotaryEncoder_Switch` (5 pins: A, B, C, S1, S2 — an exact match for
this part's A/B/C/D/E pinout). Footprint: stock KiCad library
`Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm` — purpose-built
for an Alps EC11E + integrated switch + vertical mount + 20mm shaft, i.e.
this specific part family/variant, not a generic stand-in. Live stock
cross-checked 2026-11-15 across two independent sources (JLCPCB's own part
page confirming Extended-library class, and a third-party LCSC data mirror
showing roughly 3.2k units in stock).

Because the datasheet specifies no internal pull resistors, the encoder
follows the same external-pull-up convention as the discrete switches for
all 3 of its signals: quadrature channels A and B are each externally
pulled up to `+3V3` (R303, R304) and pulled toward `GND` through the
encoder's internal mechanical contact against its common pin C (wired
directly to `GND`); the integrated push-switch is wired the same way — S2
pulled up to `+3V3` through R309, S1 wired directly to `GND` (S1/S2 are an
unpolarized SPST pair, so which terminal is pulled up is an arbitrary,
documented choice, not a functional constraint).

GPIO net assignment: `GPIO20`/`GPIO21`/`GPIO24`-`GPIO27` unchanged (UP=20,
DOWN=21, A=24, B=25, X=26, Y=27), picked from the generic bidirectional
GPIO pool `rp2350b_memory.kicad_sch` exposes as global labels for every
RP2350B GPIO not already committed elsewhere. The encoder reuses the two
GPIOs freed by removing LEFT/RIGHT (`GPIO22` → channel A, `GPIO23` →
channel B) and claims one additional GPIO (`GPIO28`, the next free pin in
the pool) for its push-switch — confirmed free by grepping all 4 populated
sheets (power, rp2350b_memory, esp32_bt, input) for every GPIO/`ESP32_*`
global label before finalizing. Each switch/signal's firmware-facing
logical name (UP/DOWN/A/B/X/Y, `VOL_A`/`VOL_B`/`VOL_SW` for the encoder) is
drawn as a plain, non-connected text caption under/beside it, not a second
schematic label on the same net: a global label and a local label both
landing on one net connect fine electrically, but ERC reports it as
`multiple_net_names`, so the logical name stays informational-only
graphical text here instead.

**Flag for firmware integration (out of scope for this bead):** firmware's
current `PL_INPUT_PIN_*` pin *numbers* (2/18/16/20/15/17/19/21) are the old
Waveshare board's GPIO map and do not match this schematic's GPIO
assignment — only the logical *names* were cross-checked here.
`PL_INPUT_PIN_LEFT`/`PL_INPUT_PIN_RIGHT` go away entirely in favor of a new
quadrature-decode + push-button read path for the encoder. Firmware will
need its own remap once real hardware integration happens; tracked as
follow-up bead `pilink-otf` (pin remap) plus the not-yet-filed encoder
firmware work flagged in the 2026-11-15 ADR.

References use this project's `300`-`399` block (`power.kicad_sch`: 1-99,
`rp2350b_memory.kicad_sch`: 100-199, `esp32_bt.kicad_sch`: 200-299). The
amendment retired `SW304` (the old RIGHT switch — left as an intentional
gap, not reused) and repurposed `SW303` for the new rotary encoder, reusing
`R303`/`R304` as its two quadrature pull-ups and adding `R309` as the
push-switch's pull-up; `#PWR305`/`#PWR307` (both freed `+3V3`) and
`#PWR306`/`#PWR308` (both freed `GND`) are reused for the encoder's pull-up
supplies and direct GND returns, with one new `#PWR317` (`+3V3`) added for
the third pull-up. UP/DOWN/A/B/X/Y keep their original `SW301`/`SW302`/
`SW305`-`SW308`, `R301`/`R302`/`R305`-`R308`, and
`#PWR301`-`#PWR304`/`#PWR309`-`#PWR316` unchanged. No `PWR_FLAG` on this
sheet, same reasoning as the other two populated child sheets — this sheet
doesn't generate `+3V3`/`GND`, `power.kicad_sch` does.

Validated with `kicad-cli sch erc --severity-all --exit-code-violations`:
the **root** `pico-link-hw.kicad_sch` reports 0 errors / 48 warnings, all
`global_label_dangling` on GPIO/ESP32 labels still waiting for their other
end on the display/USB-C sheets (down from 49 before this amendment —
`GPIO28` is no longer dangling now that the encoder's push-switch consumes
it). Checking `input.kicad_sch` **standalone** reports 2
`power_pin_not_driven` errors on `+3V3`/`GND` — expected, the same
non-root-sheet artifact already documented for the other two populated
child sheets — and 0 warnings. A project-wide netlist export (`kicad-cli
sch export netlist` on the root sheet) confirms all 59 real components
across the whole merged project (unchanged from before the amendment: one
fewer switch, one more resistor) have a unique reference designator, with
zero collisions. The exported SVG was rasterized with `cairosvg` (no system
rasterizer available in this environment) and visually checked: no
overlapping text, labels, reference designators, or components, and the
long text notes at the right of the sheet were re-spaced to fit the page
after this amendment lengthened them (an earlier draft had the last note
running past the sheet's bottom border before this fix).

**Blind-authoring caveat (the two still-empty child sheets):** neither
KiCad nor `kicad-cli` was available in the agent environment the project
skeleton was written in. Those files were hand-authored as KiCad 8
S-expression/JSON text, cross-checked against KiCad's own file-format docs
and real KiCad-8-generated project files pulled from public repos — not
written, opened, or validated by the actual KiCad GUI. `kicad-cli` **is**
available now (KiCad 8.0.9) and was used for `power.kicad_sch`,
`rp2350b_memory.kicad_sch`, `esp32_bt.kicad_sch`, `input.kicad_sch`, and the
root sheet's hierarchy (see above); the same validation still needs to
happen for the two remaining empty child sheets (`display.kicad_sch`,
`usb_c.kicad_sch`) before trusting or building on them. If anything fails
to parse, that's a bug in this skeleton, not a sign the approach is wrong.

PCB routing, DRC/ERC, and gerber export still need to happen in the KiCad GUI
on a machine that has it installed — same caveat as before, now narrowed to
"the skeleton needs a first open" rather than "nothing exists yet".

`placeholder.kicad_pcb` is a trivial seed file (just a 20x20mm board outline,
no components) for the `preview/` docker-compose service — it proves the
PCB -> GLB export pipeline end-to-end before the real board exists. Delete it
once the real PCB from pilink-7el lands; the preview pipeline picks up
whatever `*.kicad_pcb` file it finds here.
