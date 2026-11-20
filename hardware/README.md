# Hardware

KiCad project goes here: schematic, PCB layout, footprints, and a BOM with
JLCPCB/LCSC part numbers.

## Project skeleton (pilink-7el.1)

`pico-link-hw.kicad_pro` / `pico-link-hw.kicad_sch` is the root KiCad 8
project. The root sheet holds one hierarchical sheet symbol per subsystem,
each pointing at its own (currently empty) child `.kicad_sch`:

- `power.kicad_sch` — power subsystem (pilink-7el.2)
- `rp2350b_memory.kicad_sch` — RP2350B + flash/PSRAM (pilink-7el.3)
- `esp32_bt.kicad_sch` — ESP32-WROOM-32UE BT coprocessor (pilink-7el.4, amended by pilink-wot)
- `display.kicad_sch` — ST7789V display (pilink-7el.5)
- `input.kicad_sch` — buttons + volume/menu encoder (pilink-7el.6, amended by pilink-cmn then pilink-3rm)
- `usb_c.kicad_sch` — USB-C connector (pilink-7el.7)

All six child sheets started out intentionally empty — no components, no
nets — so later beads can populate them independently. See "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md)
for subsystem scope, and `.planning/decisions/` for the component choices
already settled (MCU, radio coprocessor, display, memory, the 2026-11-14
d-pad-instead-of-joystick input decision, and the two 2026-11-15
rotary-encoder amendments that first replaced LEFT/RIGHT and then
UP/DOWN).

### Power subsystem (pilink-7el.2)

`power.kicad_sch` now has the 3.3V rail: USB-C 5V in (via a `+5V`/`PWR_FLAG`
pair, pending the USB-C sheet, pilink-7el.7) through U1, a SOT-223 LDO, to
a single `+3V3` rail, with a 10uF input bulk cap (C1), a 22uF output bulk
cap (C2), and a 100nF local decoupler (C3) at the point of load.
Component choice and decoupling values are cross-checked against Raspberry
Pi's own official RP2350B minimal reference design and RP2350 Hardware
Design Guide (RP-008280-DS) — see the citations in the sheet's own text
notes. RP2350B's internal 3.3V→1.1V switched-mode core regulator (inductor,
feedback caps) and its per-pin VDD3V3/IOVDD decoupling belong on the
RP2350B + Memory sheet (pilink-7el.3), not here, matching the same split
used in Raspberry Pi's reference design.

U1 was originally an AMS1117-3.3 (bipolar NPN-pass, JLCPCB Basic part
C6186/LCSC C6186). `pilink-ddq` found its near-fixed ~1.2-1.3V dropout
offset left too little margin against USB VBUS's worst-case floor once a
tripped VBUS PTC fuse (F401, see the USB-C sheet below) was counted in, and
swapped it for AP2114H-3.3TRG1 (BCD Semiconductor/Diodes Incorporated,
LCSC `C150716`, 10,090 units in stock) — a genuinely CMOS-process LDO
whose real datasheet guarantees 450mV (typ)/750mV (max) dropout at 1A and
>=1.0A (min) guaranteed output current, pin-compatible with the AMS1117 it
replaces (same SOT-223-3_TabPin2 footprint, 1=GND/2=VOUT/3=VIN) so no
layout rework was needed. C1/C2 (10uF/22uF ceramic) already exceed this
part's own 4.7uF-ceramic stability requirement, so neither cap needed to
change. See `power.kicad_sch`'s own U1 note for the full resolved margin
math.

**U1 thermal check and bring-up flags (pilink-mxx).** Neither is a
regression from the AMS1117 (same SOT-223 exposure); both were left open
by `pilink-ddq` and are recorded here so they are not assumed fine:

- *Thermal (layout time).* AP2114H-3.3TRG1's datasheet gives roughly
  128°C/W junction-to-ambient for the bare SOT-223, a 150°C maximum
  junction temperature and a ~160°C thermal shutdown. Dissipation is
  (VIN - 3.3V) x I. Sustained worst case, 5.25V VIN at 0.65A: 1.27W, a
  162°C rise on the bare package -- over the 150°C limit even from 0°C.
  Realistic case, 5.0V at ~0.2A average (RP2350B, display, and an ESP32
  average of ~80mA -- an estimate, not an Espressif datasheet figure):
  ~0.34W, a ~44°C rise, comfortable. The 0.65A figure is the ESP32
  TX-burst *peak* (ms-scale), not a sustained load, so the real exposure
  sits between those two. To hold the 150°C limit under the sustained
  worst case at 40°C ambient the layout would need junction-to-ambient
  below ~87°C/W (~99°C/W at 25°C), about a third below the bare package.
  The PCB design adds a +3V3 heat-spreader pour around U1's VOUT tab on
  both layers (`zones.py`) stitched with a via grid (once PR #72 merges:
  36 vias, ~270mm^2 filled), but no datasheet-backed number for the
  resulting junction-to-ambient exists, so this stays a **bench
  measurement**: record case temperature of U1 on the first board under
  the worst sustained load available before trusting the margin.
- *Bring-up (bench).* AP2114H-3.3's datasheet limits short-circuit current
  to ~50mA (foldback) and says input must be applied before a
  current-source load is connected. Verify on the first board that +3V3
  starts cleanly into the full rail and its bulk capacitance (C2 22uF
  plus the per-pin decouplers), with no latch-up in a slow or stalled
  ramp; scope the +3V3 rise at power-up and after an F401 PTC trip/reset.

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
it up later without hierarchical sheet pins. GPIO47 is withheld from this
pool (committed to the PSRAM's chip-select here), and so are 8 more GPIOs
(GPIO0/1/4/5/6/7/20/21) whose `GPIOn` label was replaced, in place, by the
matching `ESP32_*` name — see the "ESP32 BT coprocessor subsystem" section
below for that assignment (`pilink-kt4`).

`kicad-cli sch erc --severity-all` on this sheet **alone** (KiCad
10.0.8) reports 2 errors (`power_pin_not_driven` for `+3V3`/`GND`,
expected and documented in the sheet's own notes — this sheet doesn't
generate `+3V3`/`GND`, `power.kicad_sch` does, so a standalone
single-sheet ERC run can't see that driver) and 54 warnings: 51
`isolated_pin_label` ("Label connected to only one pin") for GPIO labels
whose other end lives on a sibling sheet this standalone, single-sheet
check can't see — this now includes the 8 `ESP32_*` labels too, for the
same reason the pre-existing +3V3/GND check can't see `power.kicad_sch`
in isolation, not a new defect — plus 1 `footprint_link_issues` and 2
`lib_symbol_issues` notices, pre-existing and unrelated to this change
(this project's custom footprint/symbol libraries aren't registered in
the global table this standalone invocation uses).

`kicad-cli sch erc --severity-all --exit-code-violations` on the **root**
`pico-link-hw.kicad_sch` (which flattens the whole hierarchy and does see
every sibling sheet, the check that reflects real connectivity) reports
**0 errors, 26 warnings**, all `isolated_pin_label` on `GPIOn` labels this
project genuinely hasn't assigned to anything yet (GPIO2/3/8-19/35-39/
42-46) plus the pre-existing `SWD`/`SWCLK` labels — none of the 8
`ESP32_*` labels remain in this list, confirming `pilink-kt4`'s fix; see
the ESP32 section below for the before/after numbers and root cause. The
stale "Symbol has been modified in library" notice from an earlier round
no longer appears; it was fixed by re-syncing the embedded flash symbol to
the stock library part.

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

### ESP32 BT coprocessor subsystem (pilink-7el.4, amended by pilink-wot)

`esp32_bt.kicad_sch` now has U201 (ESP32-WROOM-32UE-N4, KiCad's built-in
`RF_Module:ESP32-WROOM-32UE` symbol/footprint, pinout cross-checked pin-by-
pin against Espressif's own datasheet Table 3 -- originally against the
32D/32U datasheet in pilink-7el.4, re-confirmed identical against the
32E/32UE datasheet by research bead pilink-8zj), EN strapping (R201 10k +
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
rationale and citations.

**RP2350-side GPIO assignment (`pilink-kt4`):** these 8 global labels
previously had no RP2350-side counterpart at all --
`rp2350b_memory.kicad_sch` only exposed its pins as generic `GPIOn`
labels, so every `ESP32_*` net was single-ended (one pad, `U201` only)
in the exported netlist, and ERC never caught it because a standalone
global label is legal. Fixed by replacing 8 of that sheet's `GPIOn`
global labels, in place, with these `ESP32_*` names, picked from the
[RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
section 9.4, "GPIO Bank 0 Functions" (RP2350B has exactly 2 UART
peripherals, UART0/UART1, confirmed from that section, not assumed;
cited by section rather than table number since table numbering has
shifted across datasheet revisions):

| Net | RP2350 GPIO (pin) | Function |
| --- | --- | --- |
| `ESP32_HCI_RXD` | GPIO4 (pin 1) | UART1 TX (F2) |
| `ESP32_HCI_TXD` | GPIO5 (pin 2) | UART1 RX (F2) |
| `ESP32_HCI_RTS` | GPIO6 (pin 3) | UART1 CTS (F2) |
| `ESP32_HCI_CTS` | GPIO7 (pin 4) | UART1 RTS (F2) |
| `ESP32_FLASH_RXD0` | GPIO0 (pin 77) | UART0 TX (F2) |
| `ESP32_FLASH_TXD0` | GPIO1 (pin 78) | UART0 RX (F2) |
| `ESP32_EN` | GPIO20 (pin 20) | plain GPIO (bit-banged) |
| `ESP32_BOOT0` | GPIO21 (pin 21) | plain GPIO (bit-banged) |

UART1 (GPIO4-7) carries the HCI link as a full 4-wire group with
hardware flow control, matching the "4-wire HCI UART, not optional"
requirement in
[`.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`](../.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md);
RTS/CTS cross modem-style (ESP32's RTS output lands on RP2350's CTS
input, and vice versa). UART0 (GPIO0/1) carries only the esptool
bridge-flashing link, which needs no flow control. GPIO20/21 (freed
back into the generic pool by `pilink-3rm`'s d-pad-to-encoder swap) are
plain bit-banged outputs for EN/BOOT0 strapping -- no peripheral
function needed. All 8 GPIOs were confirmed free by grepping every
populated sheet's actual `global_label`/`label` usage (not just their
absence as a generic `GPIOn` label on this one sheet) before picking
them.

Flash variant: ESP32-WROOM-32UE-**N4** (JLCPCB/LCSC `C701344`). Sufficient
for an HCI-controller-only firmware image (no Wi-Fi/Bluedroid/display
code); live LCSC stock checked 2026-11-14 (research bead pilink-8zj) at
~3,321 units, comfortably above any realistic build quantity. (Before the
`pilink-wot` swap below, this was ESP32-WROOM-32U-**N4**, JLCPCB/LCSC
`C328062`, with stock in the low thousands of units.)

**Risk flag resolved (`pilink-wot`):** Espressif's datasheet (v2.8,
2026-09-16) marked ESP32-WROOM-32U "NOT RECOMMENDED FOR NEW DESIGNS
(NRND)" -- not surfaced in the original ADR, and flagged as a follow-up
risk by bead `pilink-8zj`. Stock was still healthy and the part was still
in production, but Espressif steers new designs toward ESP32-WROOM-32UE
instead. Research bead `pilink-8zj`
([`.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md`](../.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md))
confirmed ESP32-WROOM-32UE is pin-for-pin identical (all 39 pins, diffed
directly against both datasheets), same package envelope, not itself
NRND/EOL, with comparable LCSC/JLCPCB stock in the same N4 variant, and
that KiCad 8.0.9's stock `RF_Module` library already ships a ready-made
ESP32-WROOM-32UE symbol/footprint pair. The user approved the swap
([`.planning/decisions/2026-11-15-esp32-wroom-32ue-swap.md`](../.planning/decisions/2026-11-15-esp32-wroom-32ue-swap.md))
and `pilink-wot` implemented it: U201 is now `RF_Module:ESP32-WROOM-32UE`
/ `ESP32-WROOM-32UE-N4`, with no GPIO/net/pin changes. One residual item
is **not** resolved by this swap and still needs a human DRC/courtyard
check before fab: the two footprints' pad positions differ by a small,
consistent offset between the KiCad library files (~0.155mm in Y on the
side pads, ~0.38mm on the central ground/thermal pad-39 cluster) despite
identical pad numbering, pad count, and pitch -- same standard caveat
this project already applies to every footprint, since there is no GUI
tool in this agent environment to run DRC.

Validated with `kicad-cli sch erc --severity-all --exit-code-violations`:
the **root** `pico-link-hw.kicad_sch` (whole-project, the check that
reflects real connectivity) reported 0 errors / 6 warnings at the time
this paragraph was first written, all `isolated_pin_label` ("Label
connected to only one pin") on the 8 RP2350-interface labels above --
expected, since their other end (then pilink-7el.3, i.e.
`rp2350b_memory.kicad_sch`) hadn't wired them up yet.

**Update (`pilink-kt4`):** now that `rp2350b_memory.kicad_sch` actually
ties the 8 `ESP32_*` nets to real RP2350 GPIOs (see above), re-running
the same command reports **0 errors / 26 warnings**, and none of the 26
are on an `ESP32_*` net anymore -- confirming the fix. The remaining 26
are all the same `isolated_pin_label` check, one per still-genuinely-free
`GPIOn` label this project hasn't assigned to anything yet (GPIO2/3/8-19/
35-39/42-46) plus the pre-existing `SWD`/`SWCLK` labels, which really do
reach no debug header or test pad yet (tracked as `pilink-2ar`, along
with U103's unconnected pad 9/centre pad and J501 MP1/MP2 + SW303's
unconnected mounting/shield pads -- same single-pad-net root cause
class, out of this bead's scope) -- not a
regression, just more of the same check firing on more labels because
KiCad 10's `kicad-cli` flags every singly-connected global label, not
only the ones this bead happened to fix. Checking `esp32_bt.kicad_sch`
**standalone** additionally reports 2
`power_pin_not_driven` errors on +3V3/GND -- an artifact of a single
non-root sheet not seeing power.kicad_sch's real U1/GND driver, not a
real defect (confirmed by testing: adding a local PWR_FLAG to silence it
instead creates a genuine "two Power outputs on one net" conflict at the
root level, since a real driver already exists there). The exported PDF
was reviewed with `kicad-cli sch export pdf`/`export svg` plus the Read
tool for a non-overlapping layout (no pixel-rasterizer -- pdftoppm/
ImageMagick/Ghostscript -- was available in this environment to produce a
bitmap screenshot; the PDF's own text/geometry stream was inspected
instead).

**Update (`pilink-2ar`):** fixed the four single-pad-net items flagged
above as out of `pilink-kt4`'s scope:

- **SWD/SWCLK** now reach a real 3-pin, 2.54mm-pitch debug header, `J101`
  on `rp2350b_memory.kicad_sch` (stock `Connector_Generic:Conn_01x03` +
  `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical`): pin 1
  SWCLK, pin 2 GND, pin 3 SWDIO. Pitch corrected in PR #43 review (was
  1.27mm, LCSC `C22438100`): Raspberry Pi's Debug Probe docs
  (`raspberrypi/documentation` repo) list its three bundled cables as
  JST-SH-to-JST-SH, and JST-SH-to-0.1in (2.54mm) header in both male and
  female, with the latter explicitly recommended ("solder a male
  connector to the SWCLK, GND, and SWDIO header pins") for boards without
  an onboard JST-SH connector, same as this one -- none of those cables
  fit a 1.27mm header directly. 2.54mm was chosen over an onboard JST-SH
  connector or a 1.27mm-plus-adapter note as the simplest fix needing no
  extra part and no adapter, with nothing else on the board forcing
  1.27mm pitch. Same SWCLK/GND/SWDIO order as the Debug Probe's own
  SC/GND/SD pins, so the bundled cable plugs in directly. No
  VTref/target-power-sense pin: this board is always target-powered over
  USB-C regardless of the probe. **`pilink-cto`: `J101` is DNP** (pads
  only) -- the real part stands 8.5mm (2.5 plastic + 6 pin) above the
  PCB and would pierce the 2mm front face plate; see `hardware/BOM.md`.
  Hand-fit a header or wires for bring-up with the shell open. See the schematic's own `J101` text note
  for the full rationale (kept out of the symbol's `Description` field so
  the embedded `Conn_01x03` cache stays byte-identical to the real stock
  library symbol -- editing a stock symbol's own properties is exactly
  the "modified in library" trap this project's `W25Q128JVS` note already
  documents).
- **U103 (PSRAM) pin 9/"EP"** -- the footprint's real copper
  exposed/thermal pad (`Winbond_USON-8-1EP`'s pad `"9"`, not the
  project's hand-authored part number) -- added to the project-local
  `APS6404L-3SQR-ZR` symbol and tied to GND, the standard default for an
  exposed thermal/die-attach pad on this package class. AP Memory's own
  datasheet PDF wasn't text-extractable in this agent environment (no
  poppler-utils) and Mouser-hosted mirrors of the APS6404L family
  datasheet timed out on fetch, so this isn't datasheet-confirmed for
  this exact `-3SQR-ZR` part -- flagged for human re-verification before
  fab, same caveat class as the existing footprint-match flag on this
  part. The footprint's *other* unlabeled centre pad is paste-only
  (`F.Paste` layer only, no `F.Cu`) and was deliberately left with no
  net: it carries no copper at all, so it cannot be part of any KiCad net
  -- not a defect.
- **J501 (display FPC) MP1/MP2** -- the connector's two side
  mounting/reinforcement pads -- added as two new passive pins on the
  project-local `CFAF240320A0_FPC40` symbol and tied to GND, standard
  practice for an otherwise-floating mechanical tab (grounded is safer
  than floating for ESD/EMI). Jushuo's `AFC01-S40FCA-00` datasheet PDF
  resolves to an HTML viewer on LCSC, not an extractable PDF, in this
  agent environment -- same already-documented gap as this part's
  footprint-dimension caveat -- so this is the standard-practice default,
  not a datasheet-confirmed spec; flagged for human re-verification.
- **SW303 (rotary encoder) mounting/shield pads** -- the footprint's two
  thru-hole pads both named `"MP"` (one schematic pin binds both, KiCad's
  standard multi-pad-per-pin behavior) -- added to a new project-local
  symbol, `pico_link_custom:RotaryEncoder_Switch_EC11E_MP`, copied from
  the stock `Device:RotaryEncoder_Switch` graphics/pins plus the one new
  `MP` pin, rather than editing the stock symbol in place (same
  "modified in library" reasoning as J101 above). Tied to GND by routing
  into `SW303`'s existing `C`-pin GND wire rather than a new standalone
  `#PWR` symbol: a new standalone power symbol wired in immediately next
  to `SW303` made this build of `kicad-cli` (10.0.8) misreport the
  *unrelated* `S1`/`S2` pins on the same part as `pin_not_connected` --
  reusing an already-connected point avoided it. Alps' `EC11E18244AU`
  datasheet has the same no-pdftotext extraction gap as above, so this
  is standard mounting-tab practice, not a datasheet-confirmed spec.

Re-running `kicad-cli sch erc --severity-all --exit-code-violations` on
the root sheet after this fix reports **0 errors / 24 warnings** (down
from 26) -- exactly the `SWD`/`SWCLK` `isolated_pin_label` warnings
dropping out, with every other label unchanged; the PSRAM/J501/SW303 pad
fixes were never themselves flagged by ERC (power/mechanical pads with no
schematic pin at all don't appear in ERC's checks), so they hold the
warning count steady rather than reducing it further. Verified with the
`kicad` MCP server's `get_schematic_pin_locations`/`get_net_connections`
tools against the raw `.kicad_sch` pin math while building this fix (a
symbol's pin position is in *library* space, +Y up; placing it in a
schematic, +Y down, flips the pin's Y sign -- but not a symbol *field's*
position, which doesn't flip). Not independently re-run: `kicad-cli pcb
drc` (no PCB layout exists yet -- `pilink-7el.12`, which this bead
blocks, hasn't started) and anything needing the KiCad GUI (silkscreen/
footprint visual sanity, the still-open footprint-dimension caveats
above).

### Display subsystem (pilink-7el.5)

`display.kicad_sch` now has J501 (the display's 40-pin FPC connector), U501
(the backlight boost driver) and its L501/C501/C502/R501/D501 support parts,
for the Crystalfontz **CFAF240320A0-024SN** panel (240x320 native, rotated
90deg to 320x240 in firmware via ST7789V MADCTL/MV). Why this panel was
chosen over the originally-assumed 24-pin part is recorded in
`.planning/decisions/2026-11-15-display-panel-crystalfontz-cfaf240320a0.md`,
plus `pilink-7el.5`'s own bead comments (Crystalfontz product page fetch
confirming the 40-pin 0.5mm ZIF FPC connector, full pin table from the
official datasheet).

**UPDATE (`pilink-4b6`, 2026-11-16): J501 was swapped from the
bottom-contact `AFC01-S40FCA-00` described below to the dual-contact
`FC-05B40P21H20` (LCSC `C23398824`) — see the "Known gaps" item 3 update
further down and `BOM.md`'s `pilink-4b6` addendum for why (required
pre-fab fix) and what was found and fixed on review (pin-1 numbering was
backwards between the two parts; footprint/symbol pin numbers corrected,
net assignments by physical location unchanged; cable-entry-side vs. the
old part remains unconfirmed). The narrative below is kept for
history/context on the original part choice and is otherwise still
accurate (pin table sourcing, symbol rationale).**

**Connector and pin table.** J501 was originally a 40-position, 0.5mm-pitch,
bottom-contact, flip-top-lock SMT FPC/ZIF connector — LCSC `C262674`
(Jushuo `AFC01-S40FCA-00`), confirmed directly from its own LCSC spec table
(pitch/position-count/contact-style/locking-feature all match the panel's
own "40 Position, 0.50mm Pitch ZIF connector" spec; its 500mA/50V rating is
comfortably above this interface's actual currents). No stock KiCad symbol
or footprint exists for this exact part, so both were hand-authored for
this bead: the symbol (`pico_link_custom:CFAF240320A0_FPC40` in
`symbols/pico_link_custom.kicad_sym`) and the footprint
(`Connector_FPC:AFC01-S40FCA-00` in `footprints/Connector_FPC.pretty/`,
registered in `fp-lib-table`). All 40 pin *numbers* and *names* are copied
directly from Crystalfontz's own datasheet (Rev 1v2, 2021-03-26), section
6, SPI-mode column — the symbol's single-column pin layout is a schematic
drawing convenience, not a physical pinout diagram, so only the numbers
matter for the netlist. The footprint's pad geometry went through two
review rounds: an earlier claim of having "rendered Jushuo's mechanical
drawing to an image and read it directly" turned out to be mis-transcribed
(wrong row orientation, wrong mounting-pad offset) — re-checked by
downloading the actual LCSC-hosted datasheet PDF for this exact part
(`https://www.lcsc.com/datasheet/C262674.pdf`) and extracting its text
directly, which showed it is a generic company reliability/process spec
book (electrical ratings, salt-spray/vibration test conditions, reflow
profile, SOP) with no per-position dimensioned CAD drawing in it at all —
there was never a "page 2 dimension drawing" to read numbers from. The
corrected geometry instead comes from the authoritative EasyEDA/JLCPCB
official library footprint for this exact LCSC part (`C262674`,
`FPC-SMD_AFC01-S40FCA-00`, fetched via easyeda.com's public component API):
0.50mm pad pitch, 0.30x1.30mm pads, 19.50mm span across all 40 pads
(pads at -9.75mm to +9.75mm) — unchanged from the prior revision, since
those numbers were already correct. The two mounting/fitting-nail pads are
2.00x1.60mm, centered 1.70mm beyond pad-1/pad-40 in X (also unchanged) but
now correctly offset 2.68mm from the signal pad row in Y, with the signal
row on the opposite side from the mounting pads (the prior revision had
them on the same side, 1.4mm apart, which also put pin 1 on the wrong pad).
A round-4 review caught a follow-on bug from the Y-offset fix above: the
pad row moved, but the body outline (F.Fab), courtyard (F.CrtYd),
silkscreen lines, pin-1 marker and `REF**` text were left at their old
coordinates, so they collided with the moved pads — the courtyard no
longer enclosed pads 1-40, and the silkscreen/fab lines, pin-1 dot ran
straight through the pad row. Fixed by re-deriving the body/courtyard/
silkscreen geometry from the same EasyEDA footprint's non-pad shapes
(`ComponentShape`/`3DModel`/`TopSilk` layers, same `easyeda.com` API
fetch), converting EasyEDA's internal units to mm with the 0.254mm/unit
scale factor (cross-checked against the known 0.5mm pin pitch): F.Fab body
outline x=±12.20mm, y=-2.33..3.02mm (asymmetric — the housing legitimately
overhangs the pad footprints on the actuator side, same as the real part);
F.CrtYd x=±12.70mm, y=-3.60..3.30mm, enclosing the body outline and all 42
pads with ≥0.25mm margin; silkscreen lines and the pin-1 dot repositioned
clear of every pad's Y range. Still a simplified axis-aligned approximation
of the connector's true stepped housing shape, not a literal trace of it.
Worth a human KiCad-GUI visual cross-check and DRC run before PCB fab, same
caveat class this project already applies to the RP2350 QFN-80 and PSRAM
USON-8 hand-authored footprints.

Per the datasheet: SDO (pin 4) and TE (pin 5) are no-connect (write-only
use, no tearing-effect sync needed). DB0-17 (pins 6-23), DOTCLK (26),
ENABLE (28), VSYNC (29), HSYNC (30) and RD (31) are all tied to `GND` per
the datasheet's explicit "fix low if not used" guidance for the unused
parallel-bus/RGB-interface pins — not left floating. IM0 (36) is tied `GND`
and IM1/IM2 (37/38) tied `+3V3` for the 4-wire SPI mode strap (per the
datasheet's mode table). VCC (3) and VCI (39) both go to `+3V3`.

**GPIO assignment.** `GPIO29` (CS), `GPIO30` (SCK/RS), `GPIO31` (MOSI/SDA),
`GPIO32` (D-C/WR), `GPIO33` (RESET), `GPIO34` (backlight CTRL/enable) —
chosen (not just "picked from the free pool") to match the RP2350B's own
hardware SPI1 function-select table (RP2350 datasheet section 9.4, the
QFN-80/RP2350B-specific GPIO function rows): GPIO29=SPI1 CSn, GPIO30=SPI1
SCK, GPIO31=SPI1 TX — confirmed directly against the datasheet after an
earlier version of this sheet put SCK/MOSI/CS on the wrong three of these
pins (29/30/31 in SCK/MOSI/CS order), which would have forced firmware onto
bit-banged PIO instead of the real SPI1 peripheral. D/C, RESET and the
backlight enable don't need a hardware-SPI-capable pin, so GPIO32-34 (plain
GPIO/SIO function) are fine for them —
picked from the generic bidirectional GPIO pool `rp2350b_memory.kicad_sch`
exposes as global labels for every RP2350B GPIO not already committed
elsewhere. Confirmed free by grepping all of `hardware/*.kicad_sch` for
every `GPIOx` global label before picking (2026-11-15): `input.kicad_sch`
claims only `GPIO22`-`GPIO28` (A/B/X/Y + the volume encoder's 3 signals,
per the two 2026-11-15 rotary-encoder ADRs); `esp32_bt.kicad_sch` uses named
`ESP32_*` global labels, not `GPIOx`; `usb_c.kicad_sch` (merged as
`pilink-7el.7` while this bead was in progress — re-checked live against
`origin/master` before finalizing this sheet's own GPIO picks) uses
`USB_DP`/`USB_DM` only, no `GPIOx` claims. `GPIO29`-`GPIO34` were untouched
by all of the above. Each label
keeps the generic pool name as its real net identity (required for it to
actually join the same-named label on `rp2350b_memory.kicad_sch`) with a
plain, non-connected text caption underneath for the logical function name
— same convention `input.kicad_sch` uses for A/B/X/Y/VOL_\*. The labels use
shape `output` (RP2350 drives all six as outputs — SPI master signals plus
the backlight enable/PWM pin), matching the convention `esp32_bt.kicad_sch`
already established for its own RP2350-driven labels.

**Backlight driver.** The panel's `LED_A`/`LED_K` backlight string needs
~9V (VF 8.1-9.9V typ 9.0V) at 40mA per the datasheet's section 11.1 — not
achievable from the 3.3V/5V rails directly. This was originally Diodes
**AP3036BKTR-G1** (SOT-23-6 boost LED driver; pin1=CTRL, pin2=VOUT, pin3=VIN,
pin4=SW, pin5=GND, pin6=FB), copied directly from Crystalfontz's own "LED
Backlight Reference Schematic" (datasheet section 11.2), but AP3036BKTR-G1
(LCSC `C526368`) was found to be at 0 stock with no restock date — confirmed
twice independently (`pilink-7el.5`'s own investigation, then re-checked live
again for this bead, `pilink-av8`). U501 is now Diodes **AP3031KTR-G1**
(LCSC `C82636`, 11,130 units in stock, re-confirmed live via `jlcpcb-search`
MCP 2026-11-15) — same SOT-23-6 package and boost topology, **not**
pin-compatible: pin1=SW, pin2=GND, pin3=FB, pin4=CTRL, pin5=OV, pin6=VIN, per
the real AP3031 datasheet's own Pin Description table. That table was
independently re-extracted for this bead via a local zlib-inflate+regex PDF
text extractor (no `pdftotext`/poppler-utils or `pypdf` available in this
environment, `pip`/`apt` installs blocked by the sandbox's auto-mode
classifier) run against the LCSC-hosted datasheet PDF for `C82636`. That PDF
carries a "Rev 1.6, Dec 2012, BCD Semiconductor Manufacturing Limited"
letterhead rather than a "DS41442" Diodes-branded doc number — BCD
Semiconductor's LED-driver line was acquired by Diodes Incorporated, which
now sells this exact silicon as AP3031KTR-G1 (LCSC/JLCPCB list it under the
Diodes brand; the pin table, electricals and application-circuit numbers
match regardless of letterhead).

Three concrete circuit differences from the old AP3036B layout, both symbol
and external parts:

1. **AP3031 has no internal Schottky/VOUT pin.** Pin1 (SW)'s own datasheet
   text reads "Connect external inductor and Schottky", so a new Schottky
   diode, **D501**, was added from the SW node to the VOUT node — a part
   the AP3036B circuit didn't need. Picked **B5819W** (LCSC `C64885`,
   SOD-123, 40V/1.5A, Vf 600mV@1A — comfortably above the panel's ~9V/40mA
   operating point in both reverse-voltage margin and forward current),
   confirmed in stock (525,050 units live via `jlcpcb-search` MCP
   2026-11-15) and checked against its own LCSC spec sheet, not assumed
   from the part number.
2. **AP3031 adds pin5, OV** (Over-voltage Protection Input; datasheet:
   "Connect to the output directly. On OVP condition, the output voltage
   will be clamped"). The hand-authored symbol places OV at the exact pin
   slot/wire the old VOUT pin occupied, so OV lands on the VOUT net (shared
   with C502, `LED_A` and D501's cathode) without a separately drawn wire —
   electrically identical to "wire OV to VOUT", just inherited from the
   existing node rather than a new segment.
3. **L501 is 4.7uH (was 22uH) and C502 is 0.47uF (was 1uF)**, per the AP3031
   datasheet's own "Typical Application" circuit (Figure 24, 3×13 WLEDs for
   an LCD backlight, 1MHz switching) — not AP3036B's values, which were
   tuned for a different IC. C501 (10uF VIN bypass) already matched that
   same reference circuit's `C_IN` and needed no change.

R501 (FB-GND) stays **5.1R unchanged** — AP3031's FB reference voltage is
200mV, identical to AP3036B's, so ILED = VFB/RFB = 200mV/5.1R ≈ 39.2mA still
matches the panel's 40mA spec exactly. VIN comes from this project's `+3V3`
rail (within AP3031's 2.7V-16V input range, the same margin as before).
CTRL goes to `GPIO34`; tied high enables the driver, or firmware can PWM the
same pin for brightness dimming per AP3031's "High Frequency Dimming
Control" feature (the same behavior AP3036B's CTRL had) — both are valid
with this circuit, and which one firmware uses is out of scope for this
schematic.

The bead-named fallback, AW9364DNR (LCSC `C401007`, 11,060 units in stock),
was independently checked against its own datasheet and rejected: it is
Awinic's "4-Channel 1-wire Dimming LED Driver", a linear constant-current
LED **sink** (VIN 2.8V-5.5V, up to 4 LEDs, 20mA/channel sink current, no
inductor, no boost stage), **not** a boost converter — it cannot produce
this backlight's required ~9V output from a 3.3V input at all, an
architecture mismatch rather than a pinout difference. A further search of
JLCPCB's "LED Drivers" category for other in-stock single-cell boost LED
drivers at this input voltage found none sharing AP3036B's topology
(PT4115: buck-only, needs 6-30V input; AL1692: AC-DC mains flyback, 8.5-20V
input; NSI450xx: passive 2-terminal CCRs) — AP3031KTR-G1, found separately,
is the genuine topology-equivalent, in-stock substitute. See bead
`pilink-av8` (discovered-from `pilink-7el.5`) for the full sourcing
investigation and the independent re-verification against AP3031's real
datasheet text.

References use `500`-`599` for this sheet (`power.kicad_sch`: 1-99,
`rp2350b_memory.kicad_sch`: 100-199, `esp32_bt.kicad_sch`: 200-299,
`input.kicad_sch`: 300-399, `usb_c.kicad_sch`: 400-499 — `usb_c.kicad_sch`'s
own README section above already called `500`-`599` for whenever this
sheet got populated, so this isn't a new reservation): J501, U501, L501,
C501, C502, R501, D501, `#PWR501`-`#PWR536`. Checked directly against
`origin/master` via a project-wide netlist export: all 65 real components
project-wide have a unique reference, zero collisions.

Validated with `kicad-cli sch erc --severity-all --exit-code-violations`
(this sandbox does have `kicad-cli` 10.0.8, even though the GUI/DRC are
not available): the **root** `pico-link-hw.kicad_sch` reports **0 errors**
/ 148 warnings, up from 144 on `origin/master` immediately before this
bead (`pilink-av8`). The +4 is `endpoint_off_grid` on D501's own new
coordinates — the same warning class already present at 102 (now 106)
other points project-wide, nearly all in this exact backlight subcircuit
(several of its coordinates were already off KiCad's default connection
grid before this bead touched it; purely cosmetic, does not affect netlist
correctness). `isolated_pin_label` is unchanged at 42. Checking
`display.kicad_sch` **standalone** additionally reports 2
`power_pin_not_driven` and 6 `pin_not_driven` errors — the same
non-root-sheet artifact already documented for every other populated child
sheet (this sheet's `+3V3`/`GND` aren't driven by `power.kicad_sch` in a
single-sheet view, and the 6 SPI/backlight-CTRL `GPIOxx` labels have no
driver until `rp2350b_memory.kicad_sch` — which already exposes them in
its generic pool — is loaded alongside this sheet); both resolve to 0 at
the root level, unchanged by this bead. A project-wide netlist export
(`kicad-cli sch export netlist` on the root sheet) was used to directly
verify every net by hand, in particular the redrawn backlight loop:
`D501.2`/`L501.1`/`U501.1(SW)` on one node, `C502.2`/`D501.1`/
`J501.1(LED_A)`/`U501.5(OV)` on another, `J501.2(LED_K)`/`R501.2`/
`U501.3(FB)` on a third (unchanged from before), plus `U501.6(VIN)` on
`+3V3`, `U501.2(GND)` on `GND` and `U501.4(CTRL)` on `GPIO34` — all resolve
exactly as intended, confirming the AP3031 pin remap and D501 addition
didn't silently miswire anything.

**Implementation note for future edits to this sheet:** this file was
generated programmatically (not hand-typed). Two things worth knowing if
this sheet is edited by hand or regenerated: (1) a symbol's local Y offset
in its pin `(at ...)` entry is *negated* relative to its placed world
position — i.e. a pin's world Y = the symbol's placed Y *minus* the pin's
local Y, not plus. This isn't a quirk, it's standard KiCad convention
(symbol libraries are drawn Y-up, schematics are laid out Y-down), but it's
easy to get backwards when computing pin positions by hand, which is
exactly what caused the backlight-driver miswiring this bead's review
round caught and fixed (see the backlight driver section above) — do the
Y-negation deliberately, not by trial and error, when placing wires against
a symbol's pin coordinates. (2) An earlier draft of this note claimed a
wire could silently drop from the netlist depending on file ordering
relative to its symbol's placement block; that could not be reproduced
under `kicad-cli` 10.0.8 during this bead's review round, so treat it as
unconfirmed rather than a real KiCad behavior to code around.

### Input subsystem (pilink-7el.6, amended by pilink-cmn then pilink-3rm)

`input.kicad_sch` originally had the d-pad + button switches: 4 discrete
tact switches in a cross (UP/DOWN/LEFT/RIGHT) plus 4 discrete tact buttons
(A/B/X/Y) — no center-press switch, per
[`.planning/decisions/2026-11-14-dpad-instead-of-joystick.md`](../.planning/decisions/2026-11-14-dpad-instead-of-joystick.md)
(firmware must remap select/OK onto one of A/B/X/Y itself; that's
`pico-link`'s job, not this repo's). A 2026-11-15 amendment
([`.planning/decisions/2026-11-15-rotary-encoder-for-volume.md`](../.planning/decisions/2026-11-15-rotary-encoder-for-volume.md),
bead `pilink-cmn`) replaced the LEFT/RIGHT pair with a single EC11-class
rotary encoder dedicated to volume (rotate = adjust, press = mute/toggle),
based on usage data showing LEFT/RIGHT went unused on the prototype. A
second 2026-11-15 amendment
([`.planning/decisions/2026-11-15-rotary-encoder-replaces-full-dpad.md`](../.planning/decisions/2026-11-15-rotary-encoder-replaces-full-dpad.md),
bead `pilink-3rm`) then removed UP/DOWN as well, on the clarified intent
that the rotary encoder should replace the *entire* d-pad, not just
LEFT/RIGHT — it's now the device's sole directional control, serving
double duty by firmware context (volume or menu up/down on rotation,
mute/toggle or select on press). The sheet now has **5 inputs**: A/B/X/Y
+ 1 rotary encoder, down from the original 8-switch layout.

A/B/X/Y each still get their own external 10k pull-up
(R305-R308, `Resistor_SMD:R_0402_1005Metric`) from `+3V3` to their
GPIO node (the encoder's own pull-ups use a different value — see below),
with the switch itself (SW305-SW308, `Switch:SW_Push`/
`Button_Switch_SMD:SW_SPST_PTS645` — same part family `rp2350b_memory.kicad_sch`
originally used for BOOTSEL/reset) pulling that node to `GND` when pressed
— active-low. Unlike SW101/SW102 (which rely on the boot-ROM's own
`QSPI_SS` handling and `RUN`'s internal pull-up, and fit no external
pull-up), ordinary GPIOs have no such guaranteed default pull state, hence
the explicit external resistor on all of these switches. Per
`pilink-7el.10`, SW101/SW102 were swapped to a side-actuated/right-angle
SMD part (`Button_Switch_SMD:SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010`,
LCSC `C110293`) for top-edge pinhole access on the upright form factor —
SW305-SW308 (A/B/X/Y, front-face buttons) are unaffected and stay PTS645.

**Rotary encoder (SW303):** Alps Alpine **EC11E18244AU** (JLCPCB/LCSC
`C202365`, Extended-library part — standard extended-part handling fee,
not a sourcing-availability risk). Verified against Alps' own published
datasheet (hosted direct-PDF copy at
`datasheet.lcsc.com/datasheet/pdf/00ace576d31da40a390056171db2037f.pdf` —
LCSC's `lcsc.com/datasheet/C202365.pdf` link resolves to an HTML viewer
page rather than the PDF itself, so both the symbol's Datasheet field and
this citation use the direct PDF URL instead): vertical structure, flat
actuator, 20mm actuator length, 36 detents / 18 pulses, two-phase
incremental output (terminals A, B, common C), integrated push-on switch
(SPST, 0.5mm travel, 0.1A/5V DC rating, datasheet terminals D/E mapped
onto this sheet's S1/S2), 10mA max / 1mA min contact current rating,
10mA/5V DC max overall rating, **no internal pull resistors**. Symbol:
stock KiCad library `Device:RotaryEncoder_Switch` (5 pins: A, B, C, S1,
S2 — an exact match for this part's A/B/C/D/E pinout). Footprint: stock
KiCad library `Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm`
— purpose-built for an Alps EC11E + integrated switch + vertical mount +
20mm shaft, i.e. this specific part family/variant, not a generic
stand-in. Live stock re-checked 2026-11-15 directly against LCSC's own
C202365 product page: approximately 2,482 units in stock at check time —
this is a live-changing figure (a repeat search the same day turned up
other recent snapshots in the 2,500-4,300 range depending on
cache/mirror), so treat this as a point-in-time reading, not a
guaranteed-current one.

Because the datasheet specifies no internal pull resistors, the encoder
follows the same external-pull-up convention as the discrete switches for
all 3 of its signals, but with a different resistor value: the discrete
switches' 10k pull-ups would only pass ~0.33mA at `+3V3`, under this
part's own 1mA-min contact-current spec, so R303/R304/R309 are **3.3k**
instead (3.3V / 3.3k ≈ 1.0mA, clearing the 1mA minimum while staying well
under the 10mA max). Quadrature channels A and B are each externally
pulled up to `+3V3` (R304, R303) and pulled toward `GND` through the
encoder's internal mechanical contact against its common pin C (wired
directly to `GND`); the integrated push-switch is wired the same way — S2
pulled up to `+3V3` through R309, S1 wired directly to `GND` (S1/S2 are an
unpolarized SPST pair, so which terminal is pulled up is an arbitrary,
documented choice, not a functional constraint).

GPIO net assignment: `GPIO24`-`GPIO27` unchanged (A=24, B=25, X=26, Y=27),
picked from the generic bidirectional GPIO pool `rp2350b_memory.kicad_sch`
exposes as global labels for every RP2350B GPIO not already committed
elsewhere. The first 2026-11-15 amendment (`pilink-cmn`) reused the two
GPIOs freed by removing LEFT/RIGHT (`GPIO22` → channel A, `GPIO23` →
channel B) and claimed one additional GPIO (`GPIO28`, the next free pin in
the pool) for the encoder's push-switch — confirmed free by grepping all 4
populated sheets (power, rp2350b_memory, esp32_bt, input) for every
GPIO/`ESP32_*` global label before finalizing. The second 2026-11-15
amendment (`pilink-3rm`) removed UP/DOWN entirely, freeing `GPIO20`/`GPIO21`
back into that same pool — no new net claims them. Each switch/signal's
firmware-facing logical name (A/B/X/Y, `VOL_A`/`VOL_B`/`VOL_SW` for the
encoder) is drawn as a plain, non-connected text caption under/beside it,
not a second schematic label on the same net: a global label and a local
label both landing on one net connect fine electrically, but ERC reports
it as `multiple_net_names`, so the logical name stays informational-only
graphical text here instead.

**Flag for firmware integration (out of scope for this bead):** firmware's
current `PL_INPUT_PIN_*` pin *numbers* (2/18/16/20/15/17/19/21) are the old
Waveshare board's GPIO map and do not match this schematic's GPIO
assignment — only the logical *names* were cross-checked here.
`PL_INPUT_PIN_LEFT`/`PL_INPUT_PIN_RIGHT`/`PL_INPUT_PIN_UP`/`PL_INPUT_PIN_DOWN`
all go away entirely in favor of a new quadrature-decode + push-button read
path for the encoder, now the device's sole directional control. Firmware
will need its own remap once real hardware integration happens; tracked as
follow-up bead `pilink-otf` (pin remap) plus the not-yet-filed encoder
firmware work flagged in both 2026-11-15 rotary-encoder ADRs.

References use this project's `300`-`399` block (`power.kicad_sch`: 1-99,
`rp2350b_memory.kicad_sch`: 100-199, `esp32_bt.kicad_sch`: 200-299). The
first 2026-11-15 amendment (`pilink-cmn`) retired `SW304` (the old RIGHT
switch — left as an intentional gap, not reused) and repurposed `SW303`
for the new rotary encoder, reusing `R303`/`R304` as its two quadrature
pull-ups and adding `R309` as the push-switch's pull-up;
`#PWR305`/`#PWR307` (both freed `+3V3`) and `#PWR306`/`#PWR308` (both freed
`GND`) are reused for the encoder's pull-up supplies and direct GND
returns, with one new `#PWR317` (`+3V3`) added for the third pull-up. The
second 2026-11-15 amendment (`pilink-3rm`) retired `SW301`/`SW302`,
`R301`/`R302`, and `#PWR301`-`#PWR304` the same way — intentional gaps in
the numbering, not reused. A/B/X/Y keep their original `SW305`-`SW308`,
`R305`-`R308`, and `#PWR309`-`#PWR316` unchanged. No `PWR_FLAG` on this
sheet, same reasoning as the other two populated child sheets — this sheet
doesn't generate `+3V3`/`GND`, `power.kicad_sch` does.

Validated with `kicad-cli sch erc --severity-all --exit-code-violations`:
the **root** `pico-link-hw.kicad_sch` reports 0 errors / 50 warnings, all
`global_label_dangling` on GPIO/ESP32 labels still waiting for their other
end on the display/USB-C sheets, or (for `GPIO20`/`GPIO21`) back in the
generic free-GPIO pool now that UP/DOWN are gone — up from 48 before this
amendment, exactly the 2 labels freed by this change. Checking
`input.kicad_sch` **standalone** reports 2 `power_pin_not_driven` errors on
`+3V3`/`GND` — expected, the same non-root-sheet artifact already
documented for the other two populated child sheets — and 0 warnings. A
project-wide netlist export (`kicad-cli sch export netlist` on the root
sheet) confirms all 55 real components across the whole merged project
(down from 59: `SW301`, `SW302`, `R301`, `R302` removed) have a unique
reference designator, with zero collisions. The exported SVG was inspected
by parsing its text/geometry directly (no system rasterizer — cairosvg,
rsvg-convert, ImageMagick, Ghostscript — available in this environment):
no leftover geometry or captions remain in the old UP/DOWN area, no
dangling wire stubs, and all 4 long text notes still fit within the
sheet's border with margin to spare after this amendment's edits.

### USB-C connector subsystem (pilink-7el.7)

**Update (2026-11-17 audit fixes):** the sheet now also has U401
(USBLC6-2SC6 ESD array on D+/D-/VBUS) and D401 (SMF5.0A TVS on +5V after
F401), the RP2350B sheet has the 27R series resistors R106/R107, and J401's
signal drill is 0.5mm. See "2026-11-17 audit fixes" at the end of this file.

`usb_c.kicad_sch` now has J401, a device-only (UFP), USB-2.0-only USB-C
receptacle wired per the bead's own investigation comment (pin table read
directly off the connector's own datasheet drawing, not guessed). Rear-exit
placement (cable runs straight back out of the enclosure, per the user's
requirement) is a PCB-layout-stage concern, not something this schematic
sheet encodes.

**J401:** LCSC `C165948` (`TYPE-C-31-M-12`, mfr Hroparts/HRO), a generic
16-pin SMD USB-C receptacle, 514,015 units in stock at research time,
Extended-library part (standard extended-part handling fee, not a
sourcing-availability risk). KiCad 8.0.9's stock `Connector:` library
already ships both an exact-match symbol (`USB_C_Receptacle_USB2.0_16P`,
pin-for-pin identical to the bead's own verified pin table, including the
A1/A12/B1/B12 GND and A4/A9/B4/B9 VBUS pins already stacked onto one
graphical point each) and an exact-match footprint for this specific
manufacturer part number (`USB_C_Receptacle_HRO_TYPE-C-31-M-12`) — no
custom symbol/footprint needed for this bead, unlike the PSRAM/flash parts
on `rp2350b_memory.kicad_sch`.

**Wiring:** DP1/DP2 (A6/B6, both datasheet D+) tied together to the
`USB_DP` global label; DN1/DN2 (A7/B7, both D-) tied together to `USB_DM` —
both global labels reused exactly as already declared on
`rp2350b_memory.kicad_sch` (grepped before use, same text/case). CC1/CC2
each get their own 5.1kΩ pulldown to GND (R401/R402, Rd per the USB-C
spec's UFP/sink role). SBU1/SBU2 are left unconnected (no alt-mode in this
design). The SHIELD pin (S1 — the connector's metal shell/mounting-tab
contacts, not one of the spec's 16 signal/power pins, and not covered by
the bead's own pin-table investigation) is tied directly to GND, the
standard chassis-to-signal-ground tie most USB-C reference designs use for
a single-ground-plane board like this one.

**F401, VBUS overcurrent protection (pilink-imx):** a first attempt here
(LCSC `C269104`, Brightking `SMD0805B050TF`, 500mA hold) was removed on
review because its hold current didn't cover this project's own worst-case
draw and its series resistance was never checked against the AMS1117's
dropout margin. F401 is now LCSC `C269106` (Brightking `SMD0805B100TFT`), an
0805 PTC resettable fuse, 1A hold / 1.95A trip / 6V max / R@25°C=40mΩ
(initial, 25°C), 5,460 units in stock at research time (lower than its
siblings but not zero — worth rechecking at order time). Placed in series
between the connector's VBUS and the `+5V` net `power.kicad_sch` expects
from this sheet, same position the earlier attempt used.

Sizing: worst-case peak current (not steady — see `power.kicad_sch`'s U1
note for the full budget derivation) re-derived from `power.kicad_sch`'s
own budget (RP2350B tens of mA +
ESP32-WROOM-32U up to 500mA per Espressif's TX-burst spec + display
~50-100mA incl. backlight) = ~0.6-0.65A. The 1A hold variant (`C269106`)
was picked over the 750mA sibling (`C269105`, R@25°C=90mΩ) because 0.65A
is 65% of a 1A hold rating vs 87% of a 750mA rating — 65% leaves headroom
for the ambient-temperature hold-current derating all PTC fuses exhibit
once enclosed (this family's own derating curve is a scanned,
non-text-extractable image in its datasheet, so this uses the general
≤75-80%-of-rated guideline for this part class as a flagged assumption,
not read off this datasheet's own curve).

Series-resistance-vs-dropout check: the LCSC/JLCPCB listing gives both an
initial R@25°C=40mΩ and an R1(max) post-trip resistance of 230mΩ — the
figure that actually applies after any trip event or under worse-case
conditions, not just at first power-up. At the 0.65A worst case that's a
26mV (40mΩ) to 150mV (230mΩ) added drop, not a flat 26mV. This was
originally checked against U1's AMS1117 dropout margin and found to
narrow it further (tracked as `pilink-ddq`); `pilink-ddq` subsequently
swapped U1 to a CMOS LDO (AP2114H-3.3TRG1) specifically because the
AMS1117's margin was too thin once this fuse's post-trip resistance was
counted. With the new part, even the 150mV post-trip-worst-case addition
from this fuse is already folded into `power.kicad_sch`'s own U1 note and
still leaves hundreds of mV of margin — see that note for the full math.

No `PWR_FLAG` is added on this sheet's own `+5V`/`GND` nets:
`power.kicad_sch` already carries both (`#FLG01` on `+5V`, `#FLG02` on
`GND`), satisfying ERC project-wide regardless of what else drives those
nets downstream, and the connector's own VBUS/GND pins are "passive"-type
(not "power_out"), so wiring them in here does not create a second driver
or an ERC "conflicting power outputs" error — same reasoning
`esp32_bt.kicad_sch`'s own notes already give for not adding a redundant
local flag once a real upstream driver/flag exists.

References use a new `400`-`499` block for this sheet (`power.kicad_sch`:
1-99, `rp2350b_memory.kicad_sch`: 100-199, `esp32_bt.kicad_sch`: 200-299,
`input.kicad_sch`: 300-399): J401, F401, R401-R404, `#PWR401`-`#PWR405`.
`display.kicad_sch` took the planned `500`-`599` block when `pilink-7el.5`
populated it.

**R403/R404, CC1/CC2 voltage-sense tap (`pilink-1sj`):** two 10kΩ
series-protection resistors tapping CC1 (off R401's pulldown node) and CC2
(off R402's) out to `GPIO40_ADC0`/`GPIO41_ADC1` — two of RP2350B's
previously-unused ADC-capable GPIOs (`rp2350b_memory.kicad_sch` U101 pins
49/52; `GPIO47_ADC7` is the only other ADC pin already spoken for, reused
as the PSRAM's second QMI chip-select). Not a divider: RP2350B's ADC input
draws no DC current while sampling, once firmware disables that pin's
default pull-down and input buffer per the RP2350-E9 erratum — so 10kΩ in
series doesn't perturb the R401/R402 Rd pulldown voltage it taps — it only
limits fault current into
the GPIO's ESD clamp if a non-compliant source ever drives CC outside its
normal ≲3.3V range. Both CC lines are sensed, not just one, because a
Type-C cable's orientation determines which of CC1/CC2 the host's Rp
actually lands on — the other reads ~0V through its own idle Rd — so
reading only one would misread "no advertisement" on every other cable
flip.

**What this tap actually buys (corrected from this bead's first-pass
note — see `.research/findings/2026-11-15-usb-c-default-power-compliance.md`
for the full correction):** USB-C's 1.5A/3A current-advertisement tiers are
set purely by the host's Rp value, read directly off CC voltage —
independent of USB data speed. Only the Default tier (500mA vs 900mA)
depends on USB generation. So this tap lets firmware legitimately draw the
~0.65A worst-case peak (documented above and on `power.kicad_sch`'s U1
note) **today**, on any host whose Rp advertises 1.5A or 3A — common on
real Type-C ports — with no BC1.2/PD hardware needed. On a host that only
advertises Default (500mA), this device still only has a 500mA
entitlement; firmware should throttle its real peak (e.g. don't let ESP32
TX-burst and max backlight coincide) specifically when Default is sensed.
That firmware logic is out of this repo's scope — the hardware here is
sufficient to support it without a further schematic respin. Full analysis
and decision: `pilink-1sj`.

**ERC note:** three of this sheet's nets (CC1→R401→R403, CC2→R402→R404,
and the raw VBUS→F401 leg) are legitimate passive/bidirectional nets with no
power-type pin directly on them (the GND/+5V power pin is one hop further,
past the resistor/fuse). `kicad-cli sch erc` flags a plain, unlabelled net
shaped like that as `wire_dangling` even when both ends are verifiably
correct — confirmed by checking each endpoint against an isolated
single-component ERC run first, then bisecting the false positive down to
"no label and no power-type pin anywhere on this specific net." Fixed by
adding a local `(label ...)` on each of the three nets (`CC1`, `CC2`,
`VBUS_RAW`) — the same plain-label convention `rp2350b_memory.kicad_sch`
already uses for its own bus signals (`QSPI_SS`/`QSPI_SD0-3`/etc.), not a
workaround invented just for this tool.

Validated with `kicad-cli sch erc --severity-all --exit-code-violations`:
`usb_c.kicad_sch` checked standalone reports 2 errors (`power_pin_not_driven`
for `+5V`/`GND` — expected, the same non-root-sheet artifact already
documented for every other populated child sheet). The figures in this
paragraph have gone stale more than once as the project grew (see git
history if the exact prior counts matter) — as of the `pilink-1sj`
R403/R404 addition, the **root** `pico-link-hw.kicad_sch` reports 0 errors
and 40 warnings, all `isolated_pin_label` (down from 42: adding R403/R404
gave two previously-orphaned labels, `GPIO40_ADC0`/`GPIO41_ADC1`, a second
connection each, resolving those two). `display.kicad_sch`'s former 102
`endpoint_off_grid` warnings were fixed separately (`pilink-o55`). A project-wide netlist
export confirms J401's GND/VBUS/CC1/CC2/D+/D- nets merge as expected and no
reference designator collides with any other sheet. The exported SVG was
reviewed via its raw
text/geometry stream (no system rasterizer available in this environment,
same caveat as every other sheet) for a non-overlapping layout; this is an
agent-driven check against a rendered export, not a human sign-off in the
KiCad GUI.

**Blind-authoring caveat (all six child sheets now populated):** neither
KiCad nor `kicad-cli` was available in the agent environment the project
skeleton was written in. `display.kicad_sch` was hand-authored as KiCad 8
S-expression/JSON text at that time, cross-checked against KiCad's own
file-format docs and real KiCad-8-generated project files pulled from
public repos — not written, opened, or validated by the actual KiCad GUI.
`kicad-cli` **is** available now (KiCad 8.0.9) and was used for
`power.kicad_sch`, `rp2350b_memory.kicad_sch`, `esp32_bt.kicad_sch`,
`input.kicad_sch`, `usb_c.kicad_sch`, and (by `pilink-7el.5`, after this
sheet's own `usb_c.kicad_sch` section was written) `display.kicad_sch` too
— see that bead's own section above for its sheet-standalone and
root-level ERC numbers. If anything fails to parse, that's a bug in this
skeleton, not a sign the approach is wrong.

**JLCPCB assembly exports must pass `--exclude-dnp`** (verified flag on both subcommands): `kicad-cli sch export bom --exclude-dnp ...` and `kicad-cli pcb export pos --exclude-dnp ...`. Without it the DNP J101 (`pilink-cto`) stays in the BOM and position file and JLCPCB will place it; confirm J101 is absent from both outputs before upload. `kicad-cli` can run PCB DRC and gerber export headlessly once a real PCB
exists (`kicad-cli pcb drc`, `kicad-cli pcb export gerbers`) — this doesn't
require the GUI, same as the `sch erc` runs already used above. What
genuinely still needs the GUI (or the planned headless `pcbnew` scripting
for placement, see `pilink-7el.9`): the actual routing itself, and a human's
visual/placement sign-off before fab.

`placeholder.kicad_pcb` (the 20x20mm seed file for the `preview/`
docker-compose service) was deleted when the real board landed
(`pilink-7el.12`); the preview pipeline picks up `pico-link-hw.kicad_pcb`
instead.

## PCB layout (pilink-7el.12, upright desk-clock form factor)

`pico-link-hw.kicad_pcb` is a placed, fully routed 2-layer board, 122.5 x
50mm, 1.6mm, standing parallel to the enclosure's ~122 x 56mm face per
[`.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`](../.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md)
and
[`docs/plans/2026-11-15-product-layout-proposal.md`](../docs/plans/2026-11-15-product-layout-proposal.md)
section 6c. This **replaces** `pilink-7el.9`'s PR #33 outright, not a tweak
of it: that board's 100 x 55mm flat-slab outline, encoder-on-the-right,
ESP32-at-the-left, front-centre 0-degree J501 and missing panel-shadow
keep-out are all incompatible with the upright form factor and were never
merged (the branch is kept only as a routing-feasibility reference).

### How it is built

The board is generated, not hand-drawn. From `hardware/`, in this order:

| Step | Script | What it does |
|---|---|---|
| 1 | `scripts/place.py` | Outline, 4 M2 mounting holes, design-rule minimums, net classes, every footprint position |
| 1b | `scripts/antenna_reroute.py` | (library) antenna-strip track/via keepout for `route.py`, and `check_strip()` which `zones.py` runs: exits non-zero if any track/via is under the antenna element other than the documented +3V3 B.Cu run (`pilink-kiw`; it replaced the old position-matching GPIO25/HCI_TXD reroute that silently no-oped after a re-route) |
| 1c | `scripts/sw_keepout.py` | (library, not run directly) Alps SKRTLAE010 no-copper rule areas; called by `route.py` and `zones.py` |
| 1d | `scripts/preroute.py` | Locked hand pre-route of USB D+/D- (J401 -> U401 ESD -> R106/R107 27R -> U101, since the 2026-11-17 audit fixes), the crystal, the backlight feedback pair, the SW101/SW102 BOOTSEL/RESET + GND escapes (`pilink-a8i`: the SKRTLAE010 keepout boxes those pads in, so Freerouting leaves them unconnected), the QSPI/VREG cluster (`pilink-2wq`), U201's decoupling/EN links and the 0.8mm +3V3 trunk U1 -> U201 (`pilink-fvz`/`yt5`), the VREG block to RP2350 DS 6.3.8.1 (`pilink-2x7`) and, last, a GND via beside every SMD GND pad (`gnd_fanout.py`, `pilink-r1h`). Run after `place.py`, before `route.py`; idempotent, also on a routed board: it removes and re-adds only its own *locked* items on its nets, never the router's unlocked copper |
| 2 | `scripts/route.py` | Freerouting autoroute of every net except GND and the pre-routed ones (Specctra DSN/SES round-trip); exports the SW101/102 no-copper areas, the antenna strip (board x 54..106, y 0..3), the locked GND copper and the B.Cu plane areas (`plane_keepout.py`) as keepouts. Runs several net-order seeds at once (`--jobs`) and keeps the first routing with no unconnected signal and no GND island a trial pour cannot join; prints the seed (`--seed N --tries 1` reproduces it) |
| 3 | `scripts/widen.py` | Widens +3V3/VBUS_RAW (0.8 -> 0.6 -> 0.4 -> 0.3mm tiers) and +1V1/VREG_LX (0.4 -> 0.3mm) wherever DRC allows (`+5V` is routed at 0.8mm by its own `Supply` net class) |
| 4 | `scripts/zones.py` | GND pours on both layers, +3V3 heat spreader and stitching vias at U1 (grid points nudged to stay legal), USB stub cleanup; splits locked segments at router T-joins and prunes redundant locked tails; GND via beside C502 and GND stitching vias in every non-main GND polygon, along the fast nets and on a 4mm grid; joins any GND island left to the main ground with a track (`gnd_repair.py`); then a per-polygon GND report and the ground-plane gate (exits non-zero if any GND copper is not one connected ground, a GND fragment has no via, or a capacitor GND pad has no via within 1mm) (`pilink-r1h`), and the GND path gate (`gnd_paths.py`: exits non-zero if the regulator's ground or a gated U101 decoupler reaches the exposed pad only by a copper path over its limit, `pilink-93a`/`pilink-xy5`) |
| check | `scripts/gnd_paths.py` | Prints the copper path length (and layer changes) from each U101 decoupler / VREG GND pad to the exposed pad and the gate result; also run by `zones.py` and `route.py` |
| check | `scripts/drc_summary.py -v` | `kicad-cli pcb drc` with schematic parity, summarised |
| check | `scripts/netlist_check.py` | Pin-for-pin diff of board nets against a fresh schematic netlist |
| check | `scripts/net_resistance.py` | DC resistance of the routed power paths (VBUS_RAW, +5V, +3V3 trunk, U201 decoupling/EN) from the track/via copper; pours ignored, so an upper bound (`pilink-yt5`) |

Each script is safe to re-run (each removes what it added before adding it
again), but a later step's output is discarded by re-running an earlier
one, so after any change run from that step to the end. After a schematic
change, first update the board from the schematic (KiCad's F8, or the KiCad
MCP server's `sync_schematic_to_board`), add any new part to the table in
`place.py`, then run all four.

`route.py` needs a Freerouting jar and either Java 21+ or Docker. Use
Freerouting **v2.0.1**: v2.1.0 ignored the pass limit here and could loop
without writing a result whenever a connection stayed unrouted. Even v2.0.1
occasionally exited early without writing `board.ses` (an empty 0-byte
file, no error in its own log) on this machine. Freerouting is
deterministic: the same DSN gives the same routing every time, so
re-running a DSN that failed is useless. `route.py` therefore gives each
attempt its own net order (`shuffle_nets`, seeded), runs `--jobs` of them
at once, and abandons a run 5 passes past `--passes`.

The board file was created with the KiCad MCP server's
`create_board_from_schematic` (69 footprints, 106 nets, 387 pads synced
straight from the schematic, including `pilink-kt4`'s ESP32-RP2350 wiring,
`pilink-2ar`'s SWD header, `pilink-7el.10`'s SW101/102 swap and
`pilink-7el.11`'s J401 swap). Its `autoroute` tool is still not used here:
on a machine with snap-packaged Docker it stages the DSN in the system temp
directory, which the container cannot see, so Freerouting starts with no
input and hangs -- `route.py` does the same DSN/SES round-trip with the
work directory beside the board instead.

### Placement rules applied (coordinates in board-local mm, origin at the
board's top-left corner, x right, y down -- so "N mm up the face" in the
ADR/proposal means `y = 50 - N`)

**Board-to-face mapping, clarified:** the board (50mm tall) is 6mm shorter
than the enclosure face it stands parallel to (~56mm tall, per the ADR/
proposal 6c). `y = 50 - N` treats "N mm up the face" as exactly "N mm up
the board" -- i.e. it implicitly assumes the board's bottom edge lines up
with the face's bottom edge, with that whole 6mm difference taken up
somewhere above the board's top edge. That assumption was never checked
against the actual back-shell boss/standoff design (which doesn't exist
yet): if the enclosure instead centres the board in the face, or offsets
it some other way, every "N mm up the face" coordinate in this table (the
knob centre, SW101/SW102's top-edge strip, the panel-shadow window) would
need re-deriving against the real offset. Flagged for `pilink-8hx.1`/`.2`
to confirm once the back-shell's own board-mounting geometry is designed,
not re-derived here.

| Rule (ADR / proposal 6c) | Applied as |
|---|---|
| Outline 122.5 x 50mm, parallel to the face (`pilink-4qc`: widened from 118) | `BOARD_W, BOARD_H = 122.5, 50.0` |
| **`pilink-4qc` (2026-11-16, user decision) -- supersedes every pre-4qc x/y coordinate for the items below in the rows that follow (those rows are kept as history).** Visible ACTIVE AREA, knob and diamond centred on the face | Board widened 118 -> **122.5**, board centre x = **61.25**. Panel outline (59x42) placed so the active area (insets L 2.65 / R 7.39 / T,B 2.64 -> centre 27.13 from the panel's left edge, 21 from its top) is centred at **(61.25, 25)**: panel **x:[34.12, 93.12] y:[4, 46]** (was x:[28,87] y:[5,47]). Knob shaft **(14.25, 25)** (anchor SW303 **(6.75, 22.5)**), diamond centre **(108.25, 25)**: both exactly 47.0 from the active-area centre. Diamond keeps the 8mm pitch: Y (108.25,17), X (100.25,25), B (116.25,25), A (108.25,33). X-flange vs front-shell ledge: ledge outer edge = panel right + 2.0 = 95.12, X flange (R4.5) left edge 95.75 -> **0.63mm nominal, 0.43mm worst case** after the 0.2mm radial bore play (requirement >=0.5 nominal / >=0.3 worst). Width chosen so SW306 and the knob courtyard keep >=1.0mm to the board edge. J501 moved with the panel (+6.12, -1): anchor **(65.52, 18)** rot 270, insertion face still 24mm in from the panel's right edge, centre still 7.0mm above the panel's centreline. J401 re-centred in x: **(61.25, 37)**, B.Cu. Mounting holes **(10,44), (116.5,6), (116.5,44), (29,2.5)**: the panel top is now y=4, so H4's 4.0mm head at (59,2.5) (reaching y=4.5) would overlap the 3.3mm panel stack and there is no room to go higher, so H4 moved left of the panel (head reaches x=31, 3.1mm clear of x=34.12). Backlight boost cluster (C501/L501/D501/U501/C502/R501) moved with J501 (+6.12, -1) and F401/R401-404 +6.12 in x (keeps the `backlight_sw_vs_fb` FB geometry; `preroute.py` hand-routes `Net-(J501-LED_K)` and `Net-(D501-K)` because Freerouting alone failed that rule). U201 + its B.Cu passives, R305-308, SW101/102 and the RP2350B cluster did not move; parts newly under the panel (x 87-93: C201/C202/R201/C203 on B.Cu, R305-308 0402) are low |
| Knob (SW303) centred near the board's true vertical middle (`pilink-2yw`, 2026-11-16 -- supersedes the original "lower third, ~19mm up the face" rule below, which was only a consequence of sharing a column with U201, not a deliberate target) | Shaft/knob centre at **(16, 25)** -- exactly board-vertical-centre (50/2), no compromise needed once U201 left this column. Footprint anchor is pad A, not the shaft (local offset (7.5, 2.5) from anchor), so the placed anchor is **(8.5, 22.5)**. Re the README's own board-to-face mapping caveat below, with the two conventions kept straight (a code-review correction to this cell, `pilink-2yw`, 2026-11-16 -- the arithmetic below previously had them swapped): under the README's stated (unverified) **bottom-aligned** default (board's bottom edge flush with the face's bottom edge), the face's own vertical centre (28mm up the ~56mm face) falls at **board y=22**, so this placement (board y=25) sits **3mm below** the face's centre under that convention -- not exactly centred on it. If instead the face is **centred on the board** (6mm of slack split evenly top/bottom), the face's visual centre reads as **board y=25**, exactly matching this placement -- "exactly centred" is only true under that second convention. Which of the two is real is still open, per the caveat below, for `pilink-8hx.1`/`.2` to confirm against the actual boss geometry. Either reading is a real improvement over the old placement (board y=31), which was **9mm** below face-centre under the bottom-aligned convention or **6mm** under the centred one -- there was never a single "~12mm-ish" figure. **Unchanged by `pilink-hdl`** (2026-11-16): the knob was already exactly on y=25; this bead's job was getting the diamond (below) onto y=25 too, at the same time, without re-opening the knob's own placement |
| ~~Knob centre in the lower third of the left zone, ~19mm up the face~~ (superseded above) | ~~Shaft/knob centre at (16, 31), anchor (8.5, 28.5)~~ -- was only this low because U201 shared the column (see below); not a target worth preserving |
| ESP32 (U201) relocated to the **BACK side (B.Cu)** (`pilink-hdl`, 2026-11-16 -- supersedes the `pilink-2yw` front-side pocket above the diamond, below). Anchor still **(99, 11.6)**, now on B.Cu (`place.py` table says rot 0, but the board **stores orientation 180** -- that is what KiCad's `Flip(LEFT_RIGHT)` produces for a rot-0 footprint on B.Cu, i.e. a plain left-right mirror: pin 1 lands at (107.75, 3.19), pin 38 at (90.25, 3.19)) | `pilink-2yw` moved U201 off the knob's column into a front-side pocket above the A/B/X/Y diamond, which freed the knob to centre on y=25 but forced the diamond 9mm off board-centre as a side effect (see the superseded row below). Andreas rejected that compromise: both the knob **and** the diamond need to sit on y=25 at once. A feasibility scan (this bead's own read-only investigation) confirmed no front-side-only arrangement achieves that: centring the diamond at (102,25) leaves only ~13.1mm clear above/below it to the board edge, short of U201's real courtyard (measured off this board: 19.55 x 20.25mm) by ~6-7mm in every front-side column tried. The only arrangement that works is moving U201 off the front side entirely. Checked before committing to it (not assumed): **(1) back-side obstructions** -- every other populated front-side footprint in this project is pure SMD (pad attribute + 0mm drill, confirmed by reading every pad on the board) except SW303 (encoder, THT leads at x:[8.5,23] y:[19.4,30.6], well inside its own 17.55x14.25mm F.CrtYd), J401 (already B.Cu) and J101 (THT, at (20,46)) -- none of which overlap this spot, so the whole top-right quadrant is genuinely free on B.Cu, same XY the front-side pocket already occupied (H2 at (112,6) clears U201's courtyard here by >=3.2mm, same geometry `pilink-2yw` already DRC-verified clean on the front -- the layer change doesn't alter the XY footprint or the H2/edge clearances it already passed). **(2) back-shell cavity depth** -- the real check this bead specifically asked for, same class as J401's own boss precedent (PR #52): ESP32-WROOM-32UE's real datasheet-confirmed envelope (external-antenna variant; both the 32D/U and 32E/UE datasheets agree, `.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md` point 3) is **18.0 x 19.2 x 3.2mm** -- matching the footprint's own F.Fab outline (18 x 19.2mm) exactly, confirming 3.2mm is the real mounted height, not a guess. `enclosure/back_shell.scad`'s `REAR_CLEARANCE` (the flat cavity depth behind the PCB before the back wall) is 3.0mm -- U201 overhangs the bare cavity by **0.2mm**, the same class of problem J401 had (which needed its own 2.0mm boss for a 1.5mm overhang), smaller *for the module body alone*. **That 0.2mm understates the real envelope** -- see Known gap 8: the mated U.FL plug and pigtail also face the back shell, and the cable has to exit and bend inside the same 3.0mm cavity. **This is a real, non-zero finding, not a false alarm**: U201 needs its own local relief on B.Cu at this spot -- flagged as a concrete follow-up for `back_shell.scad` (new bead, discovered-from `pilink-hdl`), not fixed in this PCB-only bead. U201's decoupling/strap network (C201/C202/R201/C203/R202) moved to B.Cu with it, same XY `pilink-2yw` already placed them at, so traces to U201's pads stay direct rather than crossing layers. Re-ran place -> route -> widen -> zones -> DRC -> netlist-check: **86 violations (8 pre-existing errors), 0 unconnected, 0 schematic parity** -- *fewer* warnings than the current master baseline (91/8/0/0 at the time of this check; see Verification below), zero regressions. Whether the U.FL->antenna-mount run still makes sense from the back of the board is `pilink-8hx.4`'s own geometry to re-check, not re-derived here |
| ~~ESP32 (U201) relocated off the knob's column, to a front-side pocket above the A/B/X/Y diamond (`pilink-2yw`)~~ (superseded above by `pilink-hdl`'s back-side move) | ~~Anchor (99, 11.6), rot 0, F.Cu~~ -- freed the knob's column but forced the diamond 9mm off board-centre as a side effect; Andreas rejected that trade-off (see above) |
| ~~ESP32 (U201) upper-left, U.FL toward the top edge~~ (superseded above) | ~~Anchor (14, 12.5)~~ -- confirmed from the stock `ESP32-WROOM-32UE` footprint's own F.Fab outline: the antenna end is the short edge beyond pins 1/38 (local y=-9.6), opposite the single pad row 15-24 (local y=+9.35); rotation 0 puts that end toward y=0 |
| Display panel shadow 59 x 42mm centred on the face window; only parts <=2.5mm tall under it | Treated as **x:[28,87] y:[5,47]** on the board (`PANEL` in `place.py`; this is the one number this project previously stated two different ways -- `place.py`'s own comment said x:[27,86], an off-by-one against the real geometry, while this README table and the real J501/RP2350B placement math were always x:[28,87] -- fixed so `place.py`'s comment and `PANEL` constant now agree with this table). Drawn on the board itself as a 59x42mm rectangle on **User.Comments** (`place.py`'s `main()`), so there is one queryable source for where the window sits, not just this prose. The RP2350B cluster (U101, its decoupling ring, flash/PSRAM, crystal) and the backlight boost (C501/L501/D501/U501/C502/R501) sit under it -- all comfortably under 2.5mm. The encoder, buttons, J501's own 2mm body (compliant) and ESP32 (not compliant, 3mm+) sit outside it in XY. **J401's through-hole legs are an exception worth flagging**: J401 itself is back-side (B.Cu), but its anchor (59, 45.5) falls inside the panel's own x/y shadow, so any through-hole pin it has protrudes on the *front* side inside the panel area -- needs trimming to <=2.5mm (or confirming it has no through-hole pins at all) before assembly; flagged for `pilink-8hx.1`/enclosure, not resolved here |
| J501 under the panel, long axis vertical, ~24mm in from the panel's right edge to its insertion face (refined figure from `pilink-0o2`'s merged finding, superseding the ADR summary's "~26mm"), ~7.2mm up from the panel's vertical centreline | Rotated 270 deg (puts the 40-pin row along board Y and the pad-row/insertion side toward +X, facing the panel's right edge). Anchor **(59.4, 19)** -- the anchor's actual measured offset from the panel's centreline (y=26) is **7.0mm**, not 7.2mm; right at the edge of `pilink-0o2`'s own +/-0.2mm tolerance band around its 7.2mm figure, not a mismatch, but stating the real built number rather than the finding's number as if it were hit exactly |
| A/B/X/Y diamond on the right, caps Ø8mm at +/-8mm centres, clear of the FPC bend strip | **Restored (`pilink-hdl`, 2026-11-16):** centre **(102, 25)** -- exactly board-vertical-centre, same target as the knob above, now that U201 has moved to B.Cu (see U201's row above) and no longer needs any front-side room above or beside this diamond. Y top (102,17), X left (94,25), B right (110,25), A bottom (102,33). SW305-308 <-> physical position is still a layout choice (not schematic-constrained; firmware maps GPIO24-27 separately, `pilink-otf`), documented, not inferred. The diamond's own pull-up resistors (R305-308) restored too, to their pre-`pilink-2yw` spot, anchors **(90, 6.0/7.6/9.2/10.8)** -- the sliver U201's old front-side footprint used to occupy there is free again. Both the knob and the diamond now sit on board y=25 at once, which is what this bead was asked to achieve -- flagged for `pilink-8hx.2` (front shell) and `pilink-8hx.4` (antenna mount) to re-check their own geometry against this restored position, same as `pilink-2yw`'s own move had to be flagged when it shifted the diamond away from here |
| ~~A/B/X/Y diamond shifted down 9mm to centre (102, 34) to clear U201's front-side pocket (`pilink-2yw`)~~ (superseded above by `pilink-hdl`'s restore) | ~~Y top (102,26), X left (94,34), B right (110,34), A bottom (102,42); pull-ups at (115.5, 5/7/9/11)~~ -- real, visible side effect Andreas rejected once he saw it; see the U201 row above |
| J401 vertical receptacle on the back side, centred between the rear legs (+/-40mm), plug exiting ~15mm up the back (proposal 6c) | **Raised (`pilink-hdl`, user decision 2026-11-16):** anchor **(59, 37)**, B.Cu (flipped via `FOOTPRINT.Flip`), was (59, 45.5). With the *then-current* face mapping Qface = 52 - board_y (**superseded by `pilink-6lz`: the mapping is now Q = 53 - board_y, `QTOP` in `enclosure/common.scad`, which is authoritative; at board y=37 that gives Q = 16, and the board anchor x is now 61.25 per `pilink-4qc`**), the plug centreline goes from Qface 6.5 to **15.0** -- the proposal's ~15mm. Board centre is x=59, so legs stay at x=19/99. Real clearance probe (every footprint's bounding box, 1mm margin around J401's 9.05x5.35mm courtyard, x:[54.47,63.53] y:[34.32,39.68] at the new anchor): nothing within 1mm on either layer; the nearest neighbour is J501 (courtyard bottom y=31.53), 2.8mm above J401's courtyard -- deliberately not pushed higher (y=35 would give Qface 17 but only 0.8mm to J501, and the FPC fold/bend lives there). U201's B.Cu footprint (x>=89) and all 4 mounting holes are nowhere near. **Not resolved by the move: the front-side THT-leg flag** (see the panel-shadow row above and Known gap 6) -- x=59, y=37 is still inside the panel shadow x:[28,87] y:[5,47]; only moving J401 past x=87 or below y=47 would take its legs out from under the glass, and neither fits the "centred between the legs" intent. USB D+/D- got *better*: 34.8/34.6mm track (2 vias each, 0.2mm skew) vs 48.9/38.0mm (3/2 vias, 10.9mm skew) before the move |
| F401/R401-404 (USB-C ESD/CC pocket), right of the backlight cluster | **Superseded for F401 (`pilink-yt5`, 2026-11-17): F401 is at (55.0, 37.0), on J401's west side, with D401 below it and U401 on B.Cu above J401; R401-R404 stay put. See "2026-11-17 audit fixes" below.** **Restored (`pilink-hdl`):** back to the pre-`pilink-2yw` coordinates (undoing the +9mm-in-Y rigid-group shift, now that U201 no longer occupies any front-side pocket near here) -- F401 **(84, 36)**, R401 **(84, 32)**, R402 **(84, 30)**, R403 **(88, 32)**, R404 **(88, 30)** |
| SW101/SW102 side-actuated, top edge, above the panel centre, clear of ESP32 and the button zone | SW101 **(42, 2.7)**, SW102 **(52, 2.7)** -- in the 5mm strip above the panel (y<5), laterally over the RP2350B/flash cluster |
| Mounting holes for back-shell bosses | 4 holes: **(10,44), (116.5,6), (116.5,44), (29,2.5) after `pilink-4qc`** (was (10,44), (112,6), (112,44), (59,2.5); H4 moved from (59,4) by `pilink-8ag`, see below) -- not at the bare board corners; placed in the genuinely free pockets instead. *(Historical rationale, kept for history rather than deleted: this was originally "since the ESP32 and encoder courtyards already claim the whole left edge," which was true before `pilink-2yw` moved U201 out to a pocket above the A/B/X/Y diamond and put the 3V3 LDO cluster in its old column -- the left edge is no longer claimed by ESP32+encoder courtyards specifically, though the holes themselves weren't re-derived and still land in free pockets.)* **H4 (59,4) is worth a clearance flag:** its centre sits only 1mm above the panel-shadow's own top edge (y=5); an M2 screw head of a typical ~3.8mm diameter (1.9mm radius) would reach y=5.9, i.e. about **0.9mm under the panel's top edge** -- not itself a DRC-visible problem (the hole is on the board, the panel line is a drawing on User.Comments), but worth the enclosure bead checking it doesn't foul the display window or its bezel. **Resolved by `pilink-8ag`:** the CAD fit check (`enclosure/scripts/check_fit.sh`) confirmed the overlap (M2 pan head d4.0 x 1.6 vs the panel envelope, y>=5), so H4 moved from (59,4) to **(59,2.5)** -- head edge now reaches y=4.5, 0.5mm clear of the panel. The hole edge is 1.4mm from the board edge (the 0.8mm figure is the pad/courtyard, not the hole); the `GPIO27` B.Cu run that hugged y=1.7 got a 0.8mm jog up to y=0.9 around x=55-63 to keep >=0.2mm hole clearance; `zones.py` re-run. DRC after: 78 violations / 0 errors / 0 unconnected / 0 parity (same as before the move). `back_shell.scad` boss moved to match. **Superseded by `pilink-4qc` (current state): H4 is at (29, 2.5)**, left of the display panel (which now starts at x=34.12), not (59, 2.5); hole edge still 1.4mm from the board edge, head reaches x=31, 3.1mm clear of the panel. The (59, 2.5) description above is history. **Since `pilink-8hx.7` the shell screws go in from the back** (heads in back-shell counterbores, heat-set inserts in front-shell standoffs), so there is no screw head on the front and the head-vs-panel concern above no longer applies; see `enclosure/README.md`, "Shell fasteners and assembly". |
| ~3mm clearance behind the board for the encoder's leads | Enclosure-side (Z-axis) concern, not a PCB XY placement; carried forward as a note for `pilink-8hx.1`/`.2`, not re-verified here |
| 3V3 LDO + bulk caps (U1/C1/C2/C3) | Anchor **(14, 10)**, unchanged by `pilink-hdl`. `pilink-2yw` moved this cluster here (from its own original pocket below the diamond, 90-106,42-47.5) to make room for U201's then-front-side move. `pilink-hdl` leaves it here rather than moving it back a second time -- it's still clear of the recentred encoder (>=1.3mm gap, unchanged) and U201 no longer needs any front-side column at all, so there's no placement reason to move it again |

U201's own full reasoning, and every other component's, is in
`scripts/place.py`'s comments -- read that file alongside this table for
the "why", not just the numbers.

### Verification (2026-11-16, KiCad 10.0.8)

**Note (`pilink-2yw`, later the same day):** the "0 schematic-parity
issues" figure below is now stale -- it predates `pilink-4b6`'s J501
footprint swap (same day, PR #47), which changed the schematic's footprint
reference for J501 but never re-synced the board (no "Update PCB from
Schematic" / `sync_schematic_to_board` run since). Confirmed by running
`drc_summary.py -v` against the unmodified `master` board before touching
anything: it already reports 20 schematic-parity issues (2
`footprint_symbol_mismatch` + 18 `net_conflict`, all on J501), independent
of this bead's placement changes. See the `pilink-2yw` verification entry
below for current numbers; this entry is kept for history, not as a
current statement.

- `kicad-cli pcb drc --severity-all --schematic-parity`: **86 violations (8
  errors), 0 unconnected items, 0 schematic-parity issues, 78 warnings**.
  - All 8 errors are `hole_clearance` on SW101/SW102's own `SKRTLAE010`
    footprint (its mechanical "MP" pads and pin-1 pad sit 0.0993-0.15mm from
    its own NPTH, under this project's 0.2mm hole-clearance design rule) --
    intrinsic to that footprint's own geometry, independent of placement
    (same error, same magnitude, regardless of where SW101/SW102 are
    placed on the board). Filed as a follow-up bead; not something
    `place.py` can fix.
  - The 78 warnings are silkscreen only (`silk_over_copper` 44,
    `silk_overlap` 32, `silk_edge_clearance` 2) -- reference designators
    overlapping copper/pads/each other in the denser clusters. Needs a GUI
    silkscreen-declutter pass before fab, same caveat class as PR #33's 84
    silkscreen warnings.
- `scripts/netlist_check.py`: **334 schematic pins compared, 0 mismatches**.
  The 24 single-pad nets listed are all genuinely-unassigned spare GPIOs
  (documented in the RP2350B + Memory section above), not missed
  connections.
- Final board: **995 track segments, 96 vias**, both front and back
  copper used (J401 is back-side).
- No 3D render / GUI visual pass was done this round (no display in this
  agent environment) -- a human visual/placement sign-off in the KiCad GUI
  is still needed before fab, on top of the numbers above.

### Verification (2026-11-16, `pilink-2yw` re-placement, KiCad 10.0.8)

Full re-run after relocating U201/the diamond/the LDO cluster and
re-centring SW303 (see the placement table above). Compared directly
against the unmodified `master` board (checked out to a scratch copy and
run through the same scripts), not against the stale numbers in the
verification entry above:

- `kicad-cli pcb drc --severity-all --schematic-parity`: **91 violations (8
  errors), 0 unconnected items, 20 schematic-parity issues, 83 warnings**
  -- vs `master`'s real current baseline of **86 violations (8 errors), 0
  unconnected, 20 schematic-parity issues, 78 warnings** (not the stale
  "0 schematic-parity" figure in the entry above). Delta: **+5 warnings,
  zero new errors, zero new unconnected items, zero new schematic-parity
  issues.**
  - The 8 errors are the same pre-existing SW101/SW102 `hole_clearance`
    defect noted above, unrelated to this bead.
  - The 20 schematic-parity issues are the same pre-existing J501
    footprint desync noted above (confirmed identical on `master` before
    any of this bead's changes) -- not caused by, or fixed by, this bead.
  - The +5 warnings are all `silk_over_copper`: SW308's silkscreen
    reference field (it points toward -Y, i.e. toward U201, for the
    diamond's top button) now sits close enough to U201's relocated pads
    to clip them on F.Cu. Same warning *category* already present 44
    times on `master` (silkscreen reference labels overlapping nearby
    copper; the `silk_overlap` warnings are a separate category, 32 more
    on `master`, not part of this 44 figure) and already flagged project-wide as needing a GUI
    silkscreen-declutter pass before fab -- not a new class of problem,
    just 5 more instances of the existing one, worth the GUI pass fixing
    (e.g. moving SW308's reference field to the opposite side) alongside
    the rest.
  - Two intermediate issues were caught and fixed before this result,
    not left in: Freerouting initially left 2 nets with a sub-mm air gap
    (`unconnected_items`) after `widen.py` -- resolved by nudging U201's
    anchor 0.6mm for silkscreen clearance (below) and re-running the full
    pipeline; and `zones.py`'s `+3V3` heat-spreader zone (hardcoded around
    U1's *old* position) showed up as `isolated_copper` after U1 moved --
    fixed by re-centring `SPREADER` in `zones.py` on U1's new anchor.
- `scripts/netlist_check.py`: **334 schematic pins compared, 18
  mismatches** -- identical set, same 18 J501 pins, confirmed against the
  unmodified `master` board before any changes here. **Zero netlist
  regressions**; the mismatches are the same pre-existing J501 desync as
  above, not a consequence of this bead's placement/route changes. The
  same 24 single-pad spare-GPIO nets as before, unmarried.
- Final board: **1021 track segments, 89 vias** (vs `master`'s 995/96) --
  more segments from the longer stubs to the relocated diamond pull-ups
  and USB pocket; fewer vias isn't significant (route-to-route variance
  between Freerouting runs, not a placement effect).
- No 3D render / GUI visual pass was done this round either, same caveat
  as above -- this specifically needs a human look given how much
  silkscreen-dense real estate (U201, the diamond, its pull-ups) just
  moved.

### Verification (2026-11-16, `pilink-hdl` re-placement, KiCad 10.0.8)

Full re-run after moving U201 (and its decoupling network) to B.Cu and
restoring the diamond/pull-ups/USB pocket to their pre-`pilink-2yw`
coordinates (see the placement table above). Done on top of current
`master` **after** `pilink-dya` (PR #59, J501 footprint sync) merged --
this bead's branch was rebased onto that merge before this run, not before
it, so the numbers below reflect that baseline, not the stale "20
schematic-parity issues" figure in the two verification entries above
(both predate `pilink-dya`). Compared directly against the unmodified
`master` board (checked out to a scratch copy and run through the same
scripts):

- `kicad-cli pcb drc --severity-all --schematic-parity`: **86 violations (8
  errors), 0 unconnected items, 0 schematic-parity issues, 78 warnings** --
  vs `master`'s real current baseline of **91 violations (8 errors), 0
  unconnected, 0 schematic-parity issues, 83 warnings**. Delta: **-5
  warnings, zero new errors, zero new unconnected items, zero new
  schematic-parity issues** -- fewer violations than `master`, not more.
  - The 8 errors are the same pre-existing SW101/SW102 `hole_clearance`
    defect noted above, unrelated to this bead.
  - 0 schematic-parity issues on both sides: `pilink-dya` (merged ahead of
    this bead, see the coordinator note worked into this branch) already
    resolved the J501 desync that the two verification entries above were
    carrying.
  - The -5 warnings are all `silk_over_copper`: `pilink-2yw` had introduced
    them when SW308's silkscreen reference field ended up close enough to
    U201's then-front-side pads to clip them. Moving U201 to B.Cu removes
    that front-side proximity entirely, so those 5 warnings simply go away
    -- not a new fix, just the side effect `pilink-2yw` caused no longer
    existing once U201 isn't on F.Cu near SW308 any more.
- `scripts/netlist_check.py`: **334 schematic pins compared, 0
  mismatches** -- identical to the unmodified `master` board (also 0,
  confirmed separately). **Zero netlist regressions.** Same 24 single-pad
  spare-GPIO nets as before, unmarried.
- **Addendum, same PR (user decision, 2026-11-16): J401 raised (59, 45.5) -> (59, 37)** (see its row in the placement table) and the pipeline re-run from the committed board. Result: **86 violations (8 pre-existing errors), 0 unconnected, 0 schematic-parity, 78 warnings** (identical to the U201-only numbers) and `netlist_check.py` 0 mismatches of 334 pins. Final board: **1062 track segments, 116 vias**. A first re-run exposed a `place.py` idempotency bug (re-applying `SetOrientationDegrees(0)` to an already-flipped B.Cu part turned U201 round 180 deg, which made its thermal-via pad clip SW308: clearance + shorting_items + solder_mask_bridge errors) -- fixed so already-back-side parts only get their position re-applied; the numbers above are from the fixed script.
- Final board (U201-only run, before the J401 addendum): **1136 track segments, 120 vias** (vs `master`'s 1021/111)
  -- more of both: every one of U201's real signal nets now needs at least
  one via to cross from B.Cu (U201) to F.Cu (the RP2350B cluster, J501,
  etc.), where before U201 and everything it talks to were both on F.Cu.
  Expected, not a red flag.
- Freerouting (`route.py`): v2.0.1's documented 0-byte-`board.ses` quirk
  (see "How it is built" above) hit on the first attempt this round --
  re-running it, as the README already says to do, produced a normal
  result on the second try. No other quirk encountered.
- No 3D render / GUI visual pass was done this round either, same caveat
  as the two entries above -- needs a human look, especially now that
  U201 sits on the opposite side of the board from where every previous
  render/photo would show it.

### Known gaps / deviations from the ideal rules

1. **RESOLVED (`pilink-rqd`): hand pre-route restored.** `scripts/preroute.py`
   (adapted from PR #33) lays locked tracks/vias for USB D+/D- and the
   crystal before `route.py`; `route.py` and `zones.py` keep them (they
   keep locked tracks/vias on those nets only). USB D+/D- are now a
   45-degree B.Cu parallel pair under U101, 2 vias each: 26.4mm / 24.9mm
   (was 34.8 / 34.6mm autorouted) -- shorter, but the skew grew from
   0.15mm to ~1.4mm (irrelevant at USB full-speed; not impedance-controlled
   either way). XIN/XOUT drop through the gap between C110/C117.
2. **RESOLVED (`pilink-rqd`): backlight SW/FB keepout enforced.**
   `pico-link-hw.kicad_dru` rule `backlight_sw_vs_fb` requires
   `Net-(D501-A)` >=1.2mm from `Net-(J501-LED_K)`; the current layout
   passes it with 0 violations (confirmed live: tightening it to 5mm
   produces violations). It is not hand-guided -- Freerouting just
   happens to satisfy it with this placement, so a re-run or a placement
   change can break it and DRC will say so.
3. **UPDATE (`pilink-4b6`, 2026-11-16): the required J501 part swap below
   has landed on the schematic/BOM side.** J501 is now the dual-contact
   `FC-05B40P21H20` (LCSC `C23398824`, BXCONN) instead of the bottom-
   contact-only `AFC01-S40FCA-00` -- see `display.kicad_sch`'s own J501
   notes and `BOM.md`'s `pilink-4b6` addendum for the full rationale and
   sourcing. This placement's own coordinates (insertion-face inset,
   ~24mm; vertical offset, ~7.2mm; rotation) were **not** changed by that
   bead (schematic/BOM scope only) and were not independently re-verified
   against the new footprint's actual pad geometry in a live board
   context -- its overall width (DIMB, 24.02mm) is close to but not
   identical to the old footprint's (24.4mm), so a human KiCad-GUI pass
   should re-confirm this placement still clears the panel-shadow keepout
   and the 3.4mm under-panel gap once the new footprint's real dimensions
   are checked. **The pin-1-concordance risk described below is now
   RESOLVED** (fix round, 2026-11-16): `C23398824`'s pin 1 and
   `C262674`'s pin 1 land at **opposite** physical ends of the connector,
   confirmed independently via JLCPCB's own assembly-library footprint
   data for both parts (`easyeda.com/api/products/<LCSC>/components` --
   answers a plain `curl GET` with no WAF block, unlike the easyeda.com
   website itself), agreeing with the BXCONN drawing's own NO.1 marker.
   Fix applied: since the ZIF contacts are straight-through, each physical
   pad position keeps the same net it always had -- only the pad/pin
   *number labels* were backwards. The footprint's 40 signal pads and the
   symbol's 40 signal pins were both mirror-renumbered (pin/pad `k` ->
   `41-k`) so every signal still lands on the same physical pad position
   as before; verified via an exported-netlist diff showing J501's
   physical pin-to-net mapping is unchanged. Separately, whether the two
   parts' FPC cables enter from the same side relative to the pad row
   could **not** be confirmed (no entry-side field in JLC's parametric
   data or the LCSC product photos, and `C262674` still has no dimensioned
   drawing) -- flagged as a remaining open item for a human with physical
   samples before fab. The original note is kept below for
   history/context.
3a. **Original note (now superseded by the update above, kept for
   history): J501 is still the bottom-contact `AFC01-S40FCA-00`, and under
   this project's own back-face working assumption that part is
   INCOMPATIBLE as placed -- this is a required pre-fab fix, not an
   optional evaluation.**
   An earlier version of this note said J501's placement here "follows the
   back-face working assumption" as if that made the current part fine.
   That was wrong: `pilink-0o2`'s merged finding
   (`.research/findings/2026-11-15-display-fpc-contact-side.md`)'s own
   placement-rule matrix says a J-fold (this layout's geometry -- J501
   under the panel, ~24mm inset) only mates a **bottom-contact** part like
   the current one when the panel's FPC contacts are **front-face**.
   Under **back-face** (the working assumption this project has adopted as
   its default, not a coin-flip), a J-fold needs a **top-contact** part
   instead; only an outboard S-fold (not what's built here, and not what
   this placement uses) would let the current bottom-contact part keep
   working. So, as currently placed and sourced, this board will **not**
   correctly mate the display cable under this project's own stated
   assumption.
   The required fix is a schematic/BOM part swap (out of this
   placement-only bead's scope, same pattern as `pilink-7el.10`/
   `pilink-7el.11`): preferably to the **dual-contact**
   `FC-05B40P21H20` (LCSC `C23398824`), which the finding says mates
   either orientation with no change to this proven J-fold geometry --
   removing the dependency on resolving contact side at all -- or, if
   back-face is later physically confirmed, a **top-contact** swap to
   `HC-FPC-0.5-40P-CSH20` (LCSC `C19273956`). Either way, **this is not
   guaranteed to be a footprint-only change**: the finding explicitly
   flags that neither replacement part's pin-1 location has been checked
   against the current part's pin-1 end (finding lines ~261-275,
   ~649-656); if they land at opposite tail ends, J501's pin mapping in
   the schematic must be *reversed*, not just the footprint swapped, or
   every signal on the connector cross-wires. This placement's own
   coordinates (insertion-face inset, vertical offset) are unaffected by
   which part/pin-mapping is used and remain reusable once the swap lands.
   Tracked by `pilink-4b6`, raised from an "evaluate" framing to a
   required pre-fab fix accordingly.
4. **Encoder-lead depth clearance (~3mm) and the J501 fold-height risk
   (`pilink-0o2` finding 4) are enclosure/Z-axis concerns**, not visible to
   PCB-level DRC -- still open for `pilink-8hx.1`/`.2`/`.4` to check
   against the real part stack.
5. **SW101/SW102's `SKRTLAE010` footprint has an internal hole-clearance
   defect** (see Verification above) -- flagged as a new bead, not fixed
   here (fixing it means re-sourcing/re-authoring the footprint, a
   different bead's scope).
6. **Two more assembly/enclosure flags, raised but not resolved here**
   (PCB XY placement only, same class as item 4): **H4** (was (59,4), moved to (59,2.5) by `pilink-8ag` -- resolved), one of
   the four back-shell mounting holes, sits only 1mm above the panel
   shadow's own top edge -- a typical M2 screw head would reach about
   0.9mm under that line, worth the enclosure bead checking against the
   real window/bezel. *(Moot since `pilink-8hx.7`: the screws now go in from the back, no head on the front.)* **J401**'s anchor (now (59, 37) after `pilink-hdl`, was (59, 45.5);
   still inside the shadow either way) falls inside the
   panel's own x/y shadow even though the connector itself is back-side
   (B.Cu); its through-hole legs (confirmed non-zero drill on this
   footprint, not just assumed) protrude on the *front* side inside that
   area and need trimming to <=2.5mm (or confirming the part has no
   through-hole pins at all) before assembly. Both noted in the placement
   table above; see `pilink-8hx.1`.
7. **`pilink-2yw`'s U201/knob/diamond re-placement cascaded into three
   enclosure beads; `pilink-hdl` (2026-11-16) changed the placement again,
   so all three need a FRESH re-check, not just the `pilink-2yw`-era one
   described below (kept for history):**
   - ~~`pilink-8hx.1` (back shell, PR #52): about PCB mounting bosses/legs
     and the rear USB-C opening, not U201/knob/diamond XY -- likely not
     affected~~ -- **now affected for a new reason**: `pilink-hdl` moved
     U201 to B.Cu, and its real mounted height (3.2mm) exceeds this file's
     `REAR_CLEARANCE` (3.0mm) by 0.2mm, needing its own shallow local boss
     (same class as J401's own, just much smaller) -- see item 9 below.
   - `pilink-8hx.2` (front shell, PR #50): the knob/diamond window
     positions it needs to match have changed AGAIN -- the diamond is back
     at board-centre (102,25) (not `pilink-2yw`'s (102,34)), matching
     where this PR's own "lower third" assumption was already wrong about
     the knob. Needs a fresh re-check against the restored coordinates in
     the placement table above, not just the `pilink-2yw`-era delta.
   - `pilink-8hx.4` (antenna mount, PR #48): U201's U.FL end is now on the
     **back** of the board entirely, not just in a different front-side
     column -- whatever antenna-mount geometry that PR is converging on
     (derived against a front-side U201, first upper-left then above the
     diamond) needs re-deriving against a back-side U.FL connector, a
     bigger change than either previous re-check.
8. **U201's new B.Cu spot needs real local relief in `back_shell.scad`
   (module + mated U.FL plug + cable bend), NOT a 0.2mm boss
   (`pilink-hdl`, 2026-11-16) -- not fixed here (placement-only scope),
   tracked in `pilink-3ym`.** Module body alone: 3.2mm (datasheet, see the
   U201 row) vs. `REAR_CLEARANCE` 3.0mm = 0.2mm over. But U201's U.FL
   receptacle and the antenna pigtail now face the back shell too, and
   that is the governing envelope: per Hirose
   ([U.FL plug vs. U.FL-V plug](https://support.hirose.com/en/support/solutions/articles/68000029798-what-is-the-difference-between-u-fl-plug-and-u-fl-v-plug-))
   a U.FL-LP-066 plug mated on a U.FL-R-SMT receptacle is **max 2.5mm**
   high above the receptacle's mounting surface (the module's own PCB top;
   verified from that page). The module PCB sits ~0.8mm above the host PCB
   (inferred as 3.2mm total minus an assumed ~2.4mm shield can -- *not*
   verified, measure it), so the plug top lands at roughly **3.3mm above
   the host PCB**, ~0.3mm past the 3.0mm cavity, before any cable. The
   Ø1.13mm coax then has to leave the plug and bend inside the same 3.0mm
   gap (no minimum bend radius verified here; the plug's cable exit
   direction is not stated on that page either). So the required relief is
   a local pocket/boss sized to at least the connector + a cable-bend
   channel, over a footprint covering both the module (board-local
   x:[89.22,108.78] y:[1.72,21.97], face coordinates via `board_to_face()`)
   and the U.FL end, with the exact depth taken from a measured/CAD
   mated-plug height rather than from the 0.2mm figure. Also see the
   `pilink-58z` statement below: the pigtail's route from this connector to
   the antenna mount is a new, back-side route.
   **`pilink-58z` (antenna RF clearance) re-check, explicit:** 58z's
   figures (~9mm to the panel frame, ~4mm to the top edge, vs. the ~46mm
   guidance) are properties of where the antenna *element* sits in the
   top wall (`antenna_mount.scad`), not of where U201 sits, and this bead
   moves neither the element nor the mount -- so those numbers are **not
   invalidated** by the PCB change. What did change: the pigtail now leaves
   U201's U.FL on the BACK of the board, toward the back shell, instead of
   the front, so it has to run behind the PCB (in the 3.0mm cavity, and
   around/over the new relief above) before reaching the top wall; the
   ~240mm pigtail has plenty of length margin (58z's own note), but the
   route is longer/different and is `pilink-3ym`'s to re-derive. U201's
   shielded module (metal) is now behind the board rather than beside the
   diamond; whether that matters for the element's pattern is part of the
   same open RF risk and is not quantified here. Option 3 in 58z (move the
   antenna to the upper rear wall) got *easier*, since U201's connector
   now already faces that wall.
   **Antenna-edge GND pull-back (`pilink-a4u`, user decision on 58z):**
   `scripts/zones.py` adds pour-only rule areas `KO_ANT_F`/`KO_ANT_B`
   (board x 54.0..106.0, y 0..3.0, both layers). The element spans face X
   59.25..105.05 = board x 56.75..102.55 (face X = board X + 2.5; land
   58.25..106.05 less 1.0mm assembly clearance each end) and sits ~1.0mm
   above the board's top edge (Q 54 vs board edge Q 53). GPIO25 and
   ESP32_HCI_TXD were moved off the B.Cu top-edge runs onto F.Cu lanes at
   y=3.29 and y=3.78; only the +3V3 B.Cu run (y~2.4, x 86..109) stays in
   the strip. **`pilink-kiw`:** that move is now committed board state, not
   a script step; `route.py` exports the strip as a Freerouting track/via
   keepout and `zones.py` fails loudly (`antenna_reroute.check_strip`) if
   copper is under the element (x 56.75..102.55, y<2.95) other than +3V3
   B.Cu. A full re-route with the keepout (place -> preroute -> route ->
   widen -> zones, Docker Freerouting) left the strip empty (+3V3 even
   moved out to y 4.46) but produced 82 violations / 3 errors
   (`copper_edge_clearance`: RESET_NODE diagonal 0.17mm from the top edge
   at x~52, outside the strip), so the committed board was kept
   (78/0/0/0, netlist 334/0). Measured with pcbnew (in-plane distance from the element
   line at 1.0mm above the edge; was, on master): nearest GND pour ~3.1mm
   (was 1.7mm), nearest copper of any net ~3.1mm (was ~1.9mm, the GPIO25
   via), nearest pad ~3.7mm (SW102 pad 1; was the same). Pour depth is
   limited to 3.0 by U201 pad 38 / C201 pad 2; the panel's metal frame
   starts at board y 4.0. The ~46mm guidance stays unmet by design pending
   a range test. DRC 78/0 errors/0 unconnected/0 parity, netlist_check
   334/0.
9. **J401's low anchor (59, 45.5) vs. the product-layout proposal's "~15mm
   up" rear-USB-C intent (section 6c) -- investigated, not resolved as a
   simple accept (`pilink-8ry`).** **UPDATE (`pilink-hdl`, 2026-11-16): J401
   was raised to (59, 37), plug centreline Qface 15.0 (was 6.5), by user
   decision -- every table-clearance number in the rest of this item (and in
   `enclosure/README.md`'s `pilink-8ry` section) was computed for the old
   Qface 6.5 and must be RECOMPUTED for the new height; they are kept below
   as history, not as current figures. `back_shell.scad`'s USB-C boss/cutout
   (`J401_FACE`) still points at the old position until `pilink-3ym` lands.** A zero-thickness-line check of the
   merged `enclosure/back_shell.scad` geometry (board_to_face Y-mapping
   fix + USB-C boss-pad clamp both already merged) first suggested a
   comfortable margin, but redoing it with a real mated-cable boot
   (sourced real example: Anker 515 cable, 6.3mm-thick plug head cover)
   found a materially worse result. Two base-strip positions matter: the
   placeholder in `back_shell.scad` (back edge Z=-8.125mm) is hit by
   every boot at or above ~4.93mm diameter (the crossover is where the
   boot's radius exceeds the 2.465mm perpendicular clearance), ~3-6mm out;
   the design-decision position (back edge Z~-0.88mm, 2.25mm in front of
   the plug, never under the cable) is not hit at all, and then every
   5.0-6.5mm boot hits the **table** ~10.6-13.4mm out along the cable
   (6.3mm Anker boot: ~11mm along, ~9.8mm horizontal), versus the
   original, wrong ~22.8mm. Table contact is independent of any strip
   notch; it only goes away if the plug's rigid moulded end is shorter
   than ~11mm (unsourced), the body is raised (roughly 1-5mm for a
   15-30mm rigid end), or J401 is moved higher on the PCB -- all still
   open. Not a confirmed collision (no cable is chosen) and
   `back_shell.scad` is untouched (investigation only). Carried forward
   in `pilink-q03` (table contact first; strip only if the placeholder
   position ships; plus whether the boot can enter the 10x5mm cutout
   tunnel). Full numbers and reasoning: `enclosure/README.md`'s "USB-C
   cable-vs-table clearance (`pilink-8ry`)" section.

10. **`pilink-xzs` (post-#71 script cleanup), 2026-11-16.** `preroute.py`
    now ends the XIN path on Y101 pad 1's centre (it stopped 0.57mm short
    and the router finished it); `zones.py` matches the J401 shell pads as
    `"S1"` only (all four are numbered `S1`, so the old `S2-S4` entries
    never matched), removes the sub-5um USB stubs the router leaves at
    U101 pins 66/67, and nudges each blocked +3V3 stitching-via grid point
    to the nearest legal spot (up to 0.7mm per axis, ~1mm diagonal) instead of dropping it: **36**
    vias, up from 13 after the `pilink-rqd` re-route (24 before it). Via
    thermal sanity check: one 0.3mm-drill via is a ~0.024mm^2 copper
    barrel through 1.6mm of board, about 175K/W; 36 in parallel are
    ~5K/W, small next to the SOT-223's ~128K/W, so the vias are not the
    bottleneck -- the spreader pour area is. Pipeline run end to end
    (`place` -> `preroute` -> `route` -> `widen` -> `zones`).
    `sw_reroute.py` is **retired** (it now aborts with a message): on this
    routing it caused a GPIO27/RESET_NODE short and ~11 clearance errors.
    Keepout-clean copper on re-runs is guaranteed because `route.py` adds
    the `sw_keepout.py` F.Cu rule areas before exporting the DSN
    (Freerouting treats them as keepouts), and DRC enforces them. One new
    local fix: U103 pad 4 (GND) is solid-connected in `zones.py` because
    this routing left it with one thermal spoke (`starved_thermal`).
    Result: `kicad-cli pcb drc --severity-all --schematic-parity
    --refill-zones` = **78 violations (0 errors, all warnings), 0
    unconnected, 0 parity** (same as before), `netlist_check.py` 0
    mismatches of 334 pins.

### SW101/SW102 hole-clearance rule (`pilink-ge9`)

The 8 `hole_clearance` errors on the Alps SKRTLAE010 are the part's real
geometry, not a footprint bug: KiCad's stock footprint and JLCPCB/EasyEDA's
own C110293 footprint have the same pad/peg coordinates. KiCad's rounded
pads give 0.0993mm (pin 1) / 0.15mm (MP tabs) to the 0.9mm NPTH pegs;
EasyEDA's square pad-1 corners make the real gap about 0.075mm. No override
footprint is warranted. `pico-link-hw.kicad_dru` relaxes `hole_clearance` to
0.09mm only for pad-to-pad pairs inside the same SW101/SW102 footprint
(`A.Type=='Pad' && B.Type=='Pad'`, same footprint), so pours, tracks and
vias still get the full 0.2mm (zones refilled; they pull back to 0.2mm).

Risk, stated plainly: JLCPCB's NPTH position tolerance is about +/-0.075mm,
about equal to the real ~0.075mm gap, so a drill can clip the edge of pad 1.
JLCPCB's published "NPTH to Track 0.2mm" covers tracks, not SMD pads. What
mitigates it: the hole is a mechanical locating peg, pad 1 is a 0.75x1.8mm
switch tab (a clipped corner leaves the bulk of the solder area), and
JLCPCB's own library footprint ships with this geometry. Confirm in the
JLCPCB DFM check at order time. No STEP model exists on EasyEDA for this
part (only an embedded outline), so 3D is unchanged.

Alps' no-copper area under the switch body: taken from the Alps SKRT
catalog land-pattern drawing ("Prohibited area of copper tracks"): 2.0mm
wide centred on pad 2, 1.2mm tall, lower edge flush with the MP pads' outer
edge, i.e. footprint-local x -1.0..+1.0, y +0.3..+1.5. `scripts/sw_keepout.py`
adds it as an F.Cu rule area (no tracks, vias or pours) per switch; `zones.py`
and `route.py` both call it so it survives pipeline re-runs and Freerouting
sees it. B.Cu is not covered (far side of the board; the drawing's note is on
the mounting layer). The pad-2 GND and pad-1 BOOTSEL/RESET routing that ran
through it was replaced locally (by the now-retired `scripts/sw_reroute.py`;
fresh `route.py` runs avoid the keepout themselves, see item 10): GND leaves pad 2 through a via above its top edge to the B.Cu pour;
the two pad-1 lands are tied by a B.Cu bar via a via beside each, with a B.Cu
trunk to a via at the pull-up resistor. Pad 1's two lands are therefore
joined on B.Cu, not F.Cu.

After: 78 violations (0 errors, all warnings), 0 unconnected, 0 parity
(master: 86 / 8 errors).

### 2026-11-17 audit fixes (`pilink-8rz`, `e63`, `912`, `brf`, `fvz`, `yt5`)

Six findings from the 2026-11-17 whole-board audit, done in one pipeline
re-run. The ground-plane strategy (`pilink-r1h`) and the VREG topology
(`pilink-2x7`) are a separate PR. Coordinates are board-local mm.

- **USB series termination (`pilink-8rz`).** R106 (D-) / R107 (D+), 27R
  0402 (`C25100`), required by RP2350 datasheet 1.2.2 and the hardware
  design guide 5.1. They sit on **B.Cu under U101**: each pin drops through
  a via inside the pin ring, and the resistor is next to that via. F.Cu has
  no room: C114/C115/C103, the locked VREG_FB run (pin 65) and the VREG GND
  via at pin 62 fill the strip above pins 66/67. Measured copper from pin to
  resistor pad: D+ 2.47mm, D- 4.19mm (D- jogs right under the body on F.Cu
  so that D+ stays the north-east track of the pair).
- **USB ESD (`pilink-e63`).** U401 USBLC6-2SC6 (`C7519`, ST) on B.Cu 3mm
  above J401's B-row, rot 90 so D-/D+ run straight through its pad pairs
  (pins 3->4 and 1->6) with no stubs; its GND pin has its own via between
  J401's shell slots, its VBUS pin goes by via to VBUS_RAW. D401 SMF5.0A
  (`C193402`) on +5V directly after F401: a TVS behind the PTC means a
  sustained overvoltage trips F401 rather than burning the TVS. Neither part
  can hold +5V under U1's 6.5V absolute maximum in a large surge (SMF5.0A:
  Vbr 6.4-7.0V, Vc 9.2V at 21.7A); they handle ESD and hot-plug ringing.
  The whole connector-to-resistor run is now B.Cu with one via per line at
  U101 (was two): D+ 27.4 + 2.5mm, D- 23.9 + 4.2mm, ~1.8mm skew (FS USB).
- **J401 annular ring (`pilink-912`).** The 16 signal PTHs go from 0.90/0.70
  (0.10mm ring) to 0.95/0.55mm (0.20mm ring, JLCPCB minimum 0.18). That is
  the largest hole the 0.18mm ring allows at the 1.10mm pitch; the in-row
  pad gap is 0.15mm, JLCPCB's listed pad-to-pad minimum (`.kicad_dru` rule
  `j401_pad_gap`). **No authoritative contact cross-section was found** (the
  HRO drawing has none; EasyEDA's library footprint, 0.50mm hole, is not a
  manufacturer source). With JLCPCB's -0.08mm hole tolerance the hole can
  finish at 0.47mm, enough for a ~0.30 x 0.28mm contact with ~0.06mm to
  spare. **Caliper a real J401 contact before ordering**; if its diagonal
  is over ~0.40mm, go back to the datasheet's 0.70mm and accept a DFM query
  (details in the footprint's `descr`). The rows now sit 0.5mm from the
  shell slots, too tight for Freerouting, so `preroute.py` lays VBUS_RAW
  through those strips by hand: 0.18mm F.Cu bars north and south of the
  rows joining both VBUS columns and running on to F401 at 0.4mm, plus a
  B.Cu bar on the south side. `place.py` now
  reloads J401 (and L101) from the project library when the board copy
  drifts, comparing pads in board coordinates. A new `.kicad_dru` rule holds
  every through-hole pad except U101's EP thermal vias to a 0.18mm ring:
  with the old 0.7mm drill it reports 16 `annular_width` errors.
- **Test pads (`pilink-brf`).** 11 bare 1.0mm SMD pads on B.Cu (reachable on
  the bench and with the back shell off; nothing to assemble, `in_bom no`,
  footprints excluded from BOM and CPL). TP201-TP206 in one 2.54mm column at
  x 86.5 beside U201's UART0/IO0 pins, top to bottom GND, 3V3, TXD0, RXD0,
  EN, IO0, for flashing U201 with esptool directly (hold the RP2350 in reset
  so GPIO0/1/20/21 float). TP1/TP2/TP3 (+5V/+3V3/GND) below U1 at y 17;
  TP101/TP102 (+1V1/GND) at (56, 12/14.5), east of the VREG block and clear
  of the QSPI/USB copper. B.SilkS carries the signal name beside each pad.
- **U201 decoupling and EN (`pilink-fvz`).** C202 (100nF), C201 (10uF),
  C203 (1uF) and R201 (10k) moved from the far side of the module to its
  right edge on B.Cu, next to pins 2 (3V3), 3 (EN) and 1 (GND), with two
  GND vias. Measured: U201.2 -> C202 0.9 mOhm, -> C201 3.6 mOhm (were 35.9
  and 44.9), U201.3 -> C203 3.2 mOhm (was 74.5). C201 lies above C202
  rather than beside it: beside it, its courtyard came within 0.22mm of the
  back shell's H2 boss (OD 7.0). These parts were already on B.Cu, so the
  order stays double-sided as before; their silk references are hidden (no
  free spot; still on B.Fab and in the CPL). Not done: no extra 22uF bulk
  (the bead's "consider"); C201 stays 10uF.
- **Power paths (`pilink-yt5`).** F401 moved from x 90 to J401's west side
  (55, 37), so the unfused VBUS_RAW run is millimetres instead of ~28mm.
  `+5V` has its own `Supply` net class (0.8mm, routed at that width). A
  locked 0.8mm F.Cu +3V3 trunk runs from U1's tab along the empty strip
  above the panel (y 6, then y 4 past the SW101/SW102 vias and under the
  antenna keepout) to two vias at C202. `widen.py` now steps 0.8 -> 0.6 ->
  0.4 -> 0.3mm, so segments that cannot take 0.4 still gain width. U1 was
  not moved: next to J401 it would put the LDO and its +3V3 heat-spreader
  pour under the display and into the B.Cu ground area, for a shorter +5V
  but an equally long +3V3 run to the ESP32.

`scripts/net_resistance.py` (new) measured the routed copper, master ->
this PR (tracks and vias only, pours ignored, so upper bounds):

| Path | master | now |
|---|---|---|
| VBUS_RAW J401.B9 -> F401 | 88.4 mOhm | 4.1 mOhm |
| VBUS_RAW J401.A9 -> F401 | 72.0 mOhm | 21.6 mOhm |
| +5V F401 -> U1 VIN | 107.1 mOhm | 48.6 mOhm |
| +3V3 U1 -> U201.2 | 208.5 mOhm | 61.6 mOhm |
| +3V3 U1 -> U501.6 (backlight boost) | 187.0 mOhm | 98.5 mOhm |
| +3V3 U1 -> U101.64 | 112.7 mOhm | 73.2 mOhm |

(A9 reaches F401 through the 0.18mm north bar, the only way past J401's
shell slots on that side; the plug ties all four VBUS contacts together, so
most of the current takes the 4.1 mOhm west column.)

At the 0.65A peak the input side (VBUS_RAW + F401 -> U1) drops ~35mV; the
`power.kicad_sch` U1 note now cites these figures in place of its
"unquantified, well under 100mV" assumption. The boost feed still has a
~17mm 0.3mm segment beside J501's pin row (`pilink-e4b`). The two +5V
layer changes are single 0.8/0.4mm router vias (~1.2 mOhm each), not
doubled. +5V still runs mostly on B.Cu, as on master (65mm at 0.8mm vs
81mm at 0.5mm), something for `pilink-r1h` to look at.

**Ground, compared with master** (`zones.py` prints this per-polygon report
on every run; "mm^2/n" = polygon area / GND vias + PTH pads in it):

| | master | this PR |
|---|---|---|
| GND_F total / largest polygon | 4413 / 3962 mm^2 | 4303 / 3867 mm^2 |
| GND_F polygons / with no via or PTH | 16 / 8 (all <= 2 mm^2) | 16 / 6 (7.6 mm^2 + five <= 1.3 mm^2) |
| GND_B total / largest polygon | 3929 / 3497 mm^2 | 4353 / 3188 mm^2 |
| GND_B polygons / with no via or PTH | 5 / 0 | 9 / 0 |
| GND vias | 13 | 32 (17 of them `zones.py` stitching vias) |

The locked +3V3 trunk (y 4-6) cuts a 351 mm^2 GND_F fragment off the main
F.Cu plane (board x 52-76, y 5-37, beside J501). On the first version of
this PR it had no via at all and C502.1, the AP3031 boost's output-cap
return, reached ground only through two 0.2mm traces (PR #102 review).
`zones.py` now puts a GND via 1.5mm from C502.1 whatever the fill does
(C502.1 now sits in the main F.Cu polygon), and stitches every GND polygon
other than each layer's main plane to the other layer, at one via per
40 mm^2: that fragment has 12, and the B.Cu fragments of 525, 409 and
156 mm^2 have 14, 16 and 12. Still unstitched (no legal via spot): the
7.6 mm^2 pocket round R401/R402's GND pads (the CC pull-downs, no current)
and five slivers of 1.3 mm^2 or less round pads. The largest B.Cu polygon is
smaller than master's because this routing splits B.Cu into more, but
stitched, pieces; the B.Cu ground strategy is `pilink-r1h`'s. The VREG
return vias (pin 62, C103, C104, the two L101 anchors) are still in one
GND_B fill polygon.

**Verification, final committed run** (place -> preroute -> route -> widen
-> zones). Freerouting is not deterministic, so several runs were needed.
The first PR version was its third run. This revision took 11 more runs:
- the first seven found and fixed bugs in the new `zones.py` code (a T-join
  split that broke chains, a missing C502 via spot, CC1/CC2 escapes, and
  doubled stitching vias);
- then four runs with the final scripts: one clean, two with one router
  unconnected item each, one Freerouting timeout.

The clean one is committed:

- `kicad-cli pcb drc --severity-all --schematic-parity --refill-zones`:
  **71 violations, 0 errors, 0 unconnected, 0 parity**; all silkscreen
  (39 `silk_over_copper`, 30 `silk_overlap`, 2 `silk_edge_clearance`),
  the same counts as master (master also shows 1 `lib_footprint_mismatch`
  for its J401 copy; gone now that `place.py` reloads J401).
- `kicad-cli sch erc --severity-all`: **0 errors, 24 warnings**, the same
  24 `isolated_pin_label` spare-GPIO labels as before.
- `netlist_check.py`: **357 pins, 0 mismatches** (334 + 23 new pads).
  Footprints with a schematic path: **83** (68 + 15).
- Antenna strip clean (`check_strip`), SW101/SW102 keepouts and the
  `backlight_sw_vs_fb` 1.2mm rule pass in DRC, and the locked QSPI, VREG
  (FB/LX/+1V1), crystal and backlight pre-routes have the same geometry as
  on master (compared after merging collinear pieces: 150 vs 152 merged
  segments, the 2 extra being sub-micron stubs left where a router T-join
  lands within ~1um of a locked segment's end; vias identical).
- `zones.py` T-join split now handles every T-join on a locked segment
  (18 this run) and leaves no `track_dangling`; one redundant locked
  pre-route item was pruned.
- `enclosure/scripts/check_fit.sh`: **55 OK, 0 FAIL, 0 WARN, 6 INFO**
  (same as master); B-side component to back shell minimum ~1.07mm (was
  ~2.16; C201 near the H2 boss, and the test pads, modelled at the 1.0mm
  default height).

Still needs a human: a KiCad GUI look at the new B.Cu clusters (U401 by
J401, R106/R107 under U101, the U201 decoupling block) and at the silk; a
caliper measurement of a real J401 signal contact against the 0.55mm hole (0.47mm worst case finished) before ordering; scope/meter
checks at bring-up (VBUS ringing at hot-plug with D401 fitted, the +3V3
droop at U201 during TX bursts, and ESP32 flashing through TP201-TP206).

### Ground plane and VREG (`pilink-r1h`, `pilink-2x7`)

Two audit findings, one pipeline re-run. Coordinates are board-local mm.

**What the bead asked for and what was possible.** `pilink-r1h` proposed
reserving B.Cu as a GND plane, with signals on F.Cu and only short B.Cu
hops. That did not work with this placement and Freerouting 2.0.1:

- Per-layer trace costs in the DSN do not keep signals off B.Cu. With the
  B.Cu cost at 50 (F.Cu 1), B.Cu still carried ~52% of the signal track.
- B.Cu track keepouts are the only lever. One under U101, even one only over
  the exposed pad, never finished (Freerouting kept running past the pass
  limit, or wrote no session). The same happened with the whole VREG block
  plus a channel down to the EP: the ESP32 UART nets (U101 pins 1-4 -> U201)
  run on B.Cu between L101 and the top pin row, and with that corridor
  closed they stayed unrouted. A locked B.Cu GND spine from the EP to the
  VREG area did the same thing.
- What does route: a keepout under the crystal (Y101, load caps, R101) and
  one under the VREG hot loop (C103/C104/the PGND island vias, from L101's
  bottom edge to the pins; B.Cu under L101 itself was already kept clear
  by `l101_keepout.py`), extended by `pilink-93a` over the strip under the
  top pin row (x 43.7-51.6) down to the exposed pad, see "VREG ground to
  the EP" below.

So B.Cu is still a signal layer (1454mm of signal track; master 1394mm),
and the work went into making the ground one connected, well-stitched net:

- **GND is not routed.** `route.py` takes GND out of the DSN and gives the
  router the locked GND copper as keepouts. No more 0.2mm GND traces
  (master's EP bridge, U1's 7mm GND trace).
- **A via at every SMD GND pad** (`gnd_fanout.py`, laid by `preroute.py`
  before routing): every capacitor, IC and connector GND pad on either
  layer gets its own via. U1 and the bulk/boost caps get 2-3. The 0.5mm
  pitch J501 GND runs get a bar with vias beyond it. U201's B.Cu GND pads
  are included, because B.Cu carries signals and a trial routing boxed
  U201.15 into a 2.7 mm^2 pocket.
- **U1's GND in the pour.** The +3V3 heat spreader is notched at U1 pin 1
  and at C2/C3's GND pads.
- **Stitching** (`zones.py`): at least one via per 40 mm^2 in every GND
  fragment, vias every 2mm along both sides of the USB, QSPI and display
  SPI tracks where both layers have GND, and a 4mm grid wherever both
  layers have GND.
- **Connectivity is checked, not assumed.** `zones.gnd_components()` builds
  the GND copper graph (fills, tracks, vias, pads). If anything is left
  outside the main ground, `gnd_repair.py` looks for a legal GND track to
  join it (a raster maze search over both layers). `zones.py`'s gate exits
  non-zero if anything is still unjoined, a GND fragment has no via, or a
  capacitor GND pad has no via within 1mm. `route.py` runs the same trial
  pour on each candidate routing and rejects one that would fail the gate.
  The committed routing needed no repair track.
- **Re-runs give a new routing.** Freerouting is deterministic per DSN. A
  failed DSN fails the same way every time, so the previous retry loop only
  repeated the failure. `route.py` now shuffles the net order per attempt
  (seeded) and runs 4 attempts at once.

**VREG topology (`pilink-2x7`, DS 6.3.8.1).** All locked in
`preroute.py`, see BOM.md flag 2 for the layout:

- The C_IN loop is on F.Cu. PGND + C103.2 + C104.2 form an F.Cu island the
  pour is kept off, and it joins the plane at one point with 2 adjacent
  vias.
- C105 (C_FILT) has its own GND via.
- VREG_FB is a dedicated trace into C104.1. DVDD leaves the L101 pad 2
  node separately via C118 and an F.Cu ring under the package to pins
  10/32/51. +1V1 has one via: the locked TP101 test-pad link at (55.05,
  12.00), with 0.95mm of B.Cu to TP101 on the back. The rail itself has
  no B.Cu.
- C104 (C_OUT) is not at L101's +1V1 pad. Its +1V1 pad reaches L101.2 by
  a 10.5mm, 0.4/0.3mm run down L101's west side; master had a 3.3mm direct
  link. DVDD is fed from the L101.2 end, so C_OUT hangs on that run (about
  8nH by the usual 1nH/mm rule of thumb for a trace over a plane; not
  measured). Why it stays: the stack is pins -> C103 -> C104 -> L101 with
  L101's LX pad at the bottom, so the LX run (pin 63 straight up between
  the two caps) is 4.4mm with no via, the C_IN loop is 1.2mm, and C104's
  GND pad sits on the PGND island next to pin 62. That keeps the phase-2
  loop (L101 -> C_OUT -> PGND) at about the same area as master (11.4 vs
  12.3mm^2, review figure). Moving C104 to L101.2 (above L101) moves its
  GND off the PGND island and stretches FB past L101 to ~8mm. Flipping
  L101 (pad 2 at the bottom) doubles the LX run. Either one is a placement
  change with its own trade-off, so it is left for a human decision.
  (`pilink-7sb`: with the smaller Abracon L101 this run is now 7.5mm and
  the LX run 3.56mm; L101's polarity fixes which pad is at the bottom. See
  "L101: Abracon AOTA-B201610" below.)
- Checked from the copper (BFS over +1V1 from pin 65, joins at the C104.1
  pad treated as the star point): the FB run is 4 segments, 2.97mm, no via,
  and no pad but pin 65 and C104.1.
- R104's +3V3 end got a locked link down into C113.1. Inside the DVDD run
  the router could almost never get it out, which was one cause of the
  unfinished runs.
- Bug fixes found on the way:
  - `zones.py` crashed in the zone filler. `ZONE.SetOutline()` took
    ownership of a Python-owned outline.
  - It also laid 0 heat-spreader vias, because
    `SHAPE_POLY_SET.SquaredDistance(..., True)` is unsupported in KiCad 10.
  - `prune_dangling_locked()` deleted live +1V1/GPIO41 pre-route copper that
    a router track joined part-way, which left 3 unconnected items.

**VREG ground to the EP (`pilink-93a`, PR #103 review).** In the first
version of this PR the router ran PSRAM_CS on B.Cu along y 19.6 under pins
61-70. That cut the B.Cu under the regulator (364mm^2) off from the EP's,
and the regulator's ground reached the EP only round the board: ~105mm of
copper by the measure below (the review's straight-line lower bound was
39mm). Changes:

- `plane_keepout.py` `VREG_PINS_B`: the VREG hot-loop keepout now also
  covers the strip under the top pin row (x 43.7-51.6) down to the EP's
  top edge, so no B.Cu signal crosses between the regulator and the EP.
- PSRAM_CS is a locked pre-route (`preroute.py`, ~33mm). It runs from the
  pin 58 hop up F.Cu east of the DVDD run, west over the VREG block on
  F.Cu at y 9.9, then takes one short B.Cu hop under QSPI_SCLK into U103
  pin 1. R105 (pull-up) stays with the router. Total 47.1mm / 5 vias
  (master 49.2/4, first version 42.7/3). Left to the router with the strip
  kept out, it ran under the exposed pad, or ~70mm round the west side, or
  stayed unrouted. A B.Cu run over the VREG block boxed U103's GND vias
  in. A locked +3V3 drop to U103.8 (tried) boxed C121's.
- `gnd_paths.py` (new) measures the copper path from a GND pad to U101's
  EP. Both layers are rasterised at 0.1mm (fills, GND tracks, pads; vias
  and plated holes link the layers) and a geodesic distance is grown from
  the EP, so a path goes round signal tracks, not through them. The gate
  runs in `zones.py`'s `gnd_gate` and in `route.py`'s `accept()`. Limits:
  PGND pin 62 / C103 / C104 / C105 at most 12mm and 1 via; C113 / C115
  at most 15mm; C111 / C112 / C118 at most 30mm (see below).
- `zones.via_ok()` judged a track by its bounding box. A long diagonal's
  box covers a whole triangle of free pour, so B.Cu slivers between
  diagonals got no stitching via and the gate failed. It now uses the
  real distance to the segment. GND stitching vias: 247 (was 186 on the
  same routing).
- `zones.pour_and_join()` stitches again after a `gnd_repair` join.
  `gnd_repair.py` keeps a new via 0.35mm (hole edge to hole edge) from
  every existing via and plated hole, GND ones included.
- C111.2 gets 2 fan-out vias (`gnd_fanout.EXTRA`). With one, it landed in
  a pocket on 3 of 12 trials.

GND path to the U101 EP along copper (`gnd_paths.py`, all three boards
re-filled and measured the same way; vias = layer changes on that path):

| From | master 2b621ca | first version ebb6685 | now |
|---|---|---|---|
| PGND island vias (48.30, 17.00 / 17.75) | (no island) | 105.5 / 105.2 mm | **7.1 / 6.8 mm, 0** |
| U101.62 (PGND pin) | 6.1 mm, 1 | 106.9 mm, 7 | **8.2 mm, 1** |
| C103.2 (C_IN) | 8.3 mm, 1 | 106.1 mm, 7 | **7.3 mm, 1** |
| C104.2 (C_OUT) | 8.7 mm, 1 | 106.4 mm, 7 | **7.6 mm, 1** |
| C105.2 (C_FILT) | 12.5 mm, 1 | 103.7 mm, 7 | **8.7 mm, 1** |
| C113.2 | 9.8 mm | 101.6 mm | **9.9 mm** |
| C115.2 | 9.5 mm | 110.3 mm | **7.2 mm** |
| C111.2 | 8.0 mm | 102.3 mm | 25.0 mm |
| C112.2 | 6.3 mm | 106.8 mm | 24.8 mm |
| C118.2 | 7.9 mm | 105.7 mm | 24.9 mm |
| C106.2 / C107.2 / C108.2 / C116.2 | 12.3 / 8.3 / 8.2 / 10.3 mm | 14.8 / 7.2 / 9.2 / 6.8 mm | 14.8 / 7.2 / 7.7 / 6.8 mm |
| C109.2 / C110.2 / C117.2 | 55.9 / 57.7 / 58.7 mm | 50.2 / 51.3 / 54.2 mm | 43.6 / 45.2 / 48.1 mm |
| C114.2 | 22.5 mm | 25.2 mm | 21.9 mm |

Master's figures go through its 0.2mm GND traces, so a short path there is
not a low-impedance one. The regulator group is now as close as master or
closer, on copper planes. Still open (follow-up bead):

- C111/C112/C118 sit in the B.Cu boxed in by the east pin row's escapes,
  the PSRAM_CS/GPIO41 B.Cu hops and the USB pair. That B.Cu reaches the
  EP the long way round, ~25mm against master's 6-8mm. Their gate limit
  (30mm) catches an ebb6685-style failure, not that gap.
- C109/C110/C117 (south) were 50-59mm on both earlier boards for the same
  reason (the B.Cu round U101 is cut by its own fan-out). They are not
  gated.

**Measured, master (2b621ca) -> this PR** (`zones.py` report, the
`gnd_paths.py` / copper scripts above, DRC):

| | master | this PR |
|---|---|---|
| GND_F polygons / largest | 16 / 3867 mm^2 | 15 / 3631 mm^2 |
| GND_B polygons / largest | 9 / 3188 mm^2 | 17 / 3393 mm^2 |
| GND copper not joined to the main ground | 0 (but via 0.2mm traces) | 0 (gate; 1 `gnd_repair` via at U103) |
| GND vias | 32 | 328 |
| U101 EP thermal vias in the main B.Cu polygon | 0 / 9 | 9 / 9 |
| B.Cu signal track, whole board | 1394 mm | 1454 mm |
| C103 (C_IN) GND -> PGND pin 62 | 7.01 mm, 2 vias | 1.21 mm, 0 vias |
| PGND pin 62 -> C104 (C_OUT) GND | 7.98 mm, 2 vias | 2.23 mm, 0 vias |
| VREG_FB pin 65 -> C104.1 | 5.39 mm, 0 vias | 2.97 mm, 0 vias |
| VREG_LX pin 63 -> L101.1 | 4.06 mm | 4.43 mm |
| L101.2 -> C104.1 (C_OUT) | 3.3 mm | 10.5 mm (see above) |

The C_IN / FB / LX / C_OUT rows come from locked pre-route copper that
this round did not change. The reference-plane coverage (USB / QSPI /
display SPI) and the crystal-keepout rows of the first version were not
re-measured.

Notes:

- The GND_B polygon count went up because B.Cu is still cut by signals.
  Every fragment of 1mm^2 or more has a via, and the whole net is one
  connected ground.

**Verification, committed run.** place -> preroute -> route -> widen ->
zones with the final scripts. Six script configurations went through
about 68 Freerouting runs in this round. None passed every `route.py`
gate as it stood at the time. Most failures were an unrouted ESP32 UART,
+3V3 U103.8 or R105 connection, a GND pocket at U103/C121 or C111, or no
session file. The committed routing is seed 0 of the last 16-seed run on
the final pre-route. It had every signal routed and no unjoinable GND
island. `route.py` rejected it only on the C111/C112/C118 path limit,
which was 25mm then, with 28.4mm, >40mm and >40mm. That was before the
`via_ok` fix: the stitching vias the fix adds bring the three to 25.0,
24.8 and 24.9mm. The
routing was then finished by hand from that attempt's import (copied to
the board, then `widen.py` and `zones.py`), and `zones.py`'s gate,
including the path gate, passes on it. The session is committed as
`routing/accepted.ses`. Freerouting results depend on the exported item
order, so a fresh run will not reproduce this routing; re-import the
session instead.

Other checks:

- QSPI (SCLK 19.26mm/0 vias, SD0 16.54/2, SD1 26.39/4, SD2 33.48/2, SD3
  27.83/3, SS 38.19/2) and USB (D+ 27.42 + 2.47mm, D- 23.85 + 4.19mm) are
  the same as master.
- `net_resistance.py`, PR #102 -> now:

  | Path | PR #102 | now |
  |---|---|---|
  | VBUS_RAW J401.B9 -> F401 | 4.1 | 4.9 mOhm |
  | VBUS_RAW J401.A9 -> F401 | 21.6 | 23.6 mOhm |
  | +5V F401 -> U1 | 48.6 | 39.9 mOhm |
  | +3V3 U1 -> U201.2 | 61.6 | 62.3 mOhm |
  | +3V3 U1 -> U501.6 | 98.5 | **149.0** mOhm |
  | +3V3 U1 -> U101.64 | 73.2 | 83.2 mOhm |
  | U201.2 -> C202 | 0.9 | 1.5 mOhm |
  | U201.2 -> C201 | 3.6 | 4.7 mOhm |
  | U201.3 -> C203 | 3.2 | 3.2 mOhm |

  These are routed paths only (tracks; pours ignored). The widths come
  from the same `widen.py` tiers.

- `kicad-cli pcb drc --severity-all --schematic-parity --refill-zones`:
  **76 violations, 0 errors, 0 unconnected, 0 parity**, all silkscreen
  warnings (40 `silk_over_copper`, 34 `silk_overlap`, 2
  `silk_edge_clearance`). Master had 39/30/2; the extra ones are vias
  under silk.
- `kicad-cli sch erc --severity-all`: **0 errors, 24 warnings**, the same
  `isolated_pin_label` spare GPIOs.
- `netlist_check.py`: **357 pins, 0 mismatches**.
- `enclosure/scripts/check_fit.sh`: **55 OK, 0 FAIL, 0 WARN, 6 INFO**, the
  same as master.
- The antenna strip check (`check_strip`) passes. The SW101/SW102 keepouts,
  the `backlight_sw_vs_fb` 1.2mm rule, the J401 rules and `vreg_lx_neck` all
  pass in DRC (0 errors).

Still needs a human:

- A KiCad GUI look at the VREG block and the new via field round U101.
- Deciding whether B.Cu has to become a real plane. That means moving the
  ESP32 UART lanes, or the placement, which is a follow-up bead.
- Deciding on C104's position (C_OUT on a 10.5mm run from L101.2, see
  above).
- A bring-up scope check of the 1.1V core rail ripple with this layout.

### PCB follow-ups (`pilink-xy5`, `pilink-uqt`, `pilink-e4b`, `pilink-9on`)

Four follow-ups to the ground-plane PR, done in one pipeline re-run.
Coordinates are board-local mm.

- **U101 east/south decouplers to the EP (`pilink-xy5`).** Two more B.Cu
  track keepouts in `plane_keepout.py`, from the exposed pad to the
  decouplers' GND vias: `EP_E` under the spare east-row pins 45-48 to C111's
  vias and a new C112 via, and `EP_S` under pins 29-32 (+3V3, XIN, XOUT,
  +1V1, none of which need B.Cu) down to a band under the C109/C110/C117
  vias, which meets the crystal keepout. C112's GND via is now fixed at
  (51.45, 25.6) (`gnd_fanout.PREFER`), west of the USB pair's D- diagonal
  (0.24mm clear). C118's GND pad sits east of the D+ diagonal with no room
  for a via west of the pair, so a locked 0.4mm F.Cu link joins it to
  C112's GND pad 1.5mm below (`gnd_fanout.LINKS`). `gnd_paths.py` now gates
  all six at 9mm. The cost: E-W B.Cu traffic under U101's south row (+5V,
  BOOT0, EN, GPIO24-27) now goes round the crystal or on F.Cu (+5V runs on
  F.Cu along y 39), which makes the routing harder (see the run count
  below). Under U101 these keepouts route, unlike the full-body ones tried
  for `pilink-r1h`.
- **Cost of `EP_S`: a west GND_F fragment.** With +5V pushed off B.Cu,
  it now runs about 20mm on F.Cu through x 11-37, y 30-40 (master 0mm).
  That cuts a 269 mm^2 / 23-via GND_F fragment off the main F.Cu plane
  around U1/U102 (x 11.5-36.3, y 6.7-39.0), new compared with master. Other
  new F.Cu fragments: 62 mm^2/4 vias over U201, 28 mm^2/4 east of U101,
  27 mm^2/4 at Y101. Every fragment is stitched, the gate passes, and
  B.Cu is the plane that matters, so it is accepted, not fixed.
  (Reviewer's refilled master figures: main GND_F 3569 mm^2, main GND_B
  3333 mm^2; mine were unrefilled.)
- **C104 (C_OUT) re-evaluated, not moved.** The trade-off above (FB and the
  PGND island against the 10.5mm L101.2 run) is unchanged by these
  channels, so it is still not a clear win either way.
- **C401, 100nF on U401 VBUS (`pilink-uqt`).** ST DocID 11265 Rev 5,
  Figure 18. 0402 (`C880604`) on F.Cu at (61.05, 28.9), right over U401,
  pad 1 on the VBUS via that drops from pin 5 (1.1mm of B.Cu, then ~1.2mm
  of 0.3mm F.Cu). B.Cu has no room: U401's courtyard and the USB pair's
  lanes box the via in. Its GND pad has its own fan-out via. Schematic:
  `usb_c.kicad_sch`; BOM.md row added.
- **+3V3 feed to the backlight boost (`pilink-e4b`).** A locked branch off
  the trunk (`preroute.py`): 0.6mm 45 degrees down from the trunk at x 59
  and level under J501's body into pin 38 (+3V3), out of its outer end at
  0.3mm beside LED_A (the router's own geometry there), then 0.8mm straight
  down at x 71.1 (east of J501's GND via column) into L501 pad 2, and 0.6mm
  on to C501 pad 2. LED_K/LED_A wrap J501's top and run diagonally to the
  boost, so any F.Cu way into the boost from the trunk passes pin 38. The
  router also ties J501 pins 2-4 to the branch. The branch splits the F.Cu
  pour east of J501 off as before (206 mm^2 GND_F fragment, 17 vias, x
  71.7-82.4; master had the same one at 231 mm^2, 18 vias).
- **No signal copper under U201 (`pilink-9on`).** `plane_keepout.NOVIA_B`:
  a B.Cu track and via keepout over the module body inset clear of the pad
  rows (x 91.4-106.6, y 3.0-19.8), exported to Freerouting only. ESP32_EN
  now goes round the bottom pad row.

**Measured, master (e668777) -> this PR** (`gnd_paths.py`, refilled, and
`net_resistance.py`; tracks and vias only, pours ignored):

| From (GND path to the U101 EP) | master | now |
|---|---|---|
| C111.2 | 25.0 mm, 1 via | **8.0 mm, 1** |
| C112.2 | 24.8 mm, 3 | **6.4 mm, 1** |
| C118.2 | 24.9 mm, 3 | **8.0 mm, 1** |
| C109.2 / C110.2 / C117.2 | 43.6 / 45.2 / 48.1 mm, 5 | **7.4 / 7.3 / 7.0 mm, 1** |
| PGND island vias / U101.62 / C103.2 / C104.2 / C105.2 | 6.8-7.1 / 8.2 / 7.3 / 7.6 / 8.7 mm | same |
| C113.2 / C115.2 | 9.9 / 7.2 mm | same |
| C106.2 / C114.2 (not gated) | 14.8 / 21.9 mm | 11.5 / 22.5 mm |

| Path | master | now |
|---|---|---|
| +3V3 U1 -> U501.6 (boost) | 149.0 mOhm | **83.3 mOhm** |
| +3V3 U1 -> U101.64 | 83.2 mOhm | 89.8 mOhm |
| +3V3 U1 -> U201.2 | 62.3 mOhm | 62.3 mOhm |
| +5V F401 -> U1 | 39.9 mOhm | 37.1 mOhm |
| VBUS_RAW J401.B9 / A9 -> F401 | 4.9 / 23.6 mOhm | same |
| U201.2 -> C202 / C201, U201.3 -> C203 | 1.5 / 4.7 / 3.2 mOhm | same |

| | master | now |
|---|---|---|
| B.Cu signal track under U201's body | 32.7 mm (EN 17.4, BOOT0 15.3), 2 EN vias | 0 mm, 0 vias |
| B.Cu signal track, whole board | 1454 mm | 1427 mm |
| GND vias | 328 | 345 |
| GND_F polygons / largest | 19 / 3569 mm^2 (15 of 1 mm^2 or more) | 18 / 3360 mm^2 |
| GND_B polygons / largest | 17 / 3333 mm^2 | 15 / 3691 mm^2 |
| U101 EP thermal vias in the main B.Cu polygon | 9 / 9 | 9 / 9 |

**Verification, committed run.** place -> preroute -> route -> widen ->
zones. 48 Freerouting attempts: 12 with an abandoned C121 rotation (it
took U102 pin 8's only +3V3 way out), 36 with the final scripts. Failures
were the usual ones (an ESP32 UART, U103.8, a GND pocket at U103/C114, no
session, overrun) plus south-row nets (RUN, SWD/SWCLK, GPIO24-27) the new
`EP_S` wall pushes round the crystal. The committed routing is seed 211 of
the last run, accepted by `route.py` with every gate passing (no
unconnected signal, no unjoinable GND island, the GND path gate at its new
limits); no hand finishing. `zones.py` joined one GND pocket at U103 with a
`gnd_repair` via, as before. The session is `routing/accepted.ses`.

- `kicad-cli pcb drc --severity-all --schematic-parity --refill-zones`:
  **77 violations, 0 errors, 0 unconnected, 0 parity**, all silkscreen
  warnings (40 `silk_over_copper`, 35 `silk_overlap`, 2
  `silk_edge_clearance`; master 40/34/2, the extra one at C401).
- `kicad-cli sch erc --severity-all`: **0 errors, 24 warnings**, the same
  `isolated_pin_label` spare GPIOs.
- `netlist_check.py`: **359 pins, 0 mismatches** (357 + C401's 2).
  84 footprints with a schematic path (83 + C401).
- QSPI (SCLK 19.26mm/0 vias, SD0 16.54/2, SD1 26.39/4, SD2 33.48/2, SD3
  27.83/3, SS 38.19/2), USB (D+ 27.42 + 2.47mm, D- 23.85 + 4.19mm) and the
  locked +1V1 / VREG_LX / VREG_AVDD copper are identical to master.
  PSRAM_CS 47.32mm / 5 vias (master 47.12; the locked part is unchanged,
  R105's router link differs).
- Antenna strip check passes; SW101/SW102 keepouts, `backlight_sw_vs_fb`,
  the J401 rules and `vreg_lx_neck` pass in DRC.

Still needs a human: a KiCad GUI look at C401 over U401, the boost branch
beside J501 and the new B.Cu channels round U101; a bring-up check of
VBUS at hot-plug with C401 fitted and of the boost input droop.

GUI and bring-up checklist additions (from review of this PR):
- ESP32_BOOT0 leaves U201's pad (90.25, 19.7) diagonally to (92.54, 21.99),
  so about 1.7mm of it runs under the module's bottom-left body corner
  (body x 90-108, y 2-21.2), outside the `NOVIA_B` keepout box. It is the
  pad-ring corner, not the GND pad area. Look at it in the GUI.
- The +3V3 boost branch passes through J501 pad 38 (a 0.35mm FPC pad, 0.3mm
  track into both ends), so that pad is part of the supply path. Inspect
  that solder joint after assembly.
- C401's reference designator overlaps J501's silkscreen (the one new
  `silk_overlap`); move or hide it before fab.

### L101: Abracon AOTA-B201610 (`pilink-7sb`)

JLCPCB's order check flagged L101 (DMBJ CXP0420, no polarity mark, BOM.md
assembly flag 2's accepted deviation). The part RP2350 DS 6.3.8.2
recommends, Abracon `AOTA-B201610S3R3-101-T` (`C42411119`, 2.0 x 1.6mm,
polarity dot), is back in JLCPCB stock, so L101 is now that part. BOM.md
flag 2 has the part data and the orientation evidence; in short:

- **Polarity: dot on +1V1.** DS 6.3.8.2: "The inductor must be marked for
  polarity (see Figure 28) and placed on the layout as indicated in
  Figure 26." In Figure 26's vector geometry the "orientation indicator"
  dot sits in the inductor pad whose copper runs to C_OUT and VOUT; the
  other pad runs to VREG_LX. Raspberry Pi's KiCad layouts (RP2350B minimal
  RP-006442-DD-2, RP2350A minimal R4-S1) agree. New footprint
  `Inductor_SMD_Custom:L_Abracon_AOTA-B201610` (Abracon datasheet
  "Recommended Land Pattern": 1.00 x 1.60mm pads, 1.00mm gap): pad 2 is
  the dot end, with a silkscreen dot beside it; on the board pad 2 is
  +1V1, pad 1 VREG_LX, the schematic pins as before.
- **CPL rotation.** The EasyEDA/JLCPCB footprint for C42411119 has the
  same pads at 0 degrees with its dot beside pad 2 at +X, so JLCPCB's
  rotation is KiCad's: L101 is `90` in the CPL (dot toward board -Y, the
  +1V1 pad at the top). `preview/scripts/export_fab.py` now lists
  `Inductor_SMD_Custom` as a custom library, so L101 is in the
  "double-check in JLCPCB's preview" list.
- **Placement** (`place.py`): rot 90 as before, centred on the LX column
  (x 47.0, was 47.95) with its courtyard bottom where the DMBJ part's was,
  so it sits right above C104. `l101_keepout.py` now reads the keepout
  areas from the footprint's pads and body; the F.Cu GND pour is held
  `POUR_MARGIN` = 1.0mm off the pads (DS 6.3.8.1: cut copper back near
  VREG_LX), since the old 4.4mm body no longer does that by itself.
- **Pre-route** (`preroute.py`): unchanged topology. The +1V1 run down
  L101's west side stays at x 45.55; DVDD turns east at the new pad-2 level
  and reaches the TP101 link by a 45-degree jog; all VREG_LX copper is now
  this script's (it deletes router copper on VREG_LX too: the router's
  stub into the old pad would have been left dangling, and that wire is
  removed from `routing/accepted.ses`).

Measured from the copper, DMBJ layout (master `a5c3816`) -> now:

| | master | now |
|---|---|---|
| VREG_LX copper, pin 63 -> L101.1 | 4.98 mm (incl. 1.14 mm router stub into the pad), 0 vias | **3.56 mm, 0 vias** |
| VREG_LX, pin 63 centre -> LX pad edge | 3.09 mm | 3.06 mm |
| VREG_LX copper to nearest F.Cu GND fill | 0.96 mm | 1.00 mm |
| +1V1 L101.2 -> C104.1 (C_OUT) | 10.48 mm | **7.50 mm** |
| +1V1 L101.2 -> C118.1 (DVDD) | 19.80 mm | 18.73 mm |
| VREG_FB pin 65 -> C104.1 | 2.97 mm | 2.97 mm |
| GND paths to the EP (`gnd_paths.py`) | as in the table above | identical, gate passes |

**Verification.** place -> preroute -> widen -> zones on the committed
routing. **Freerouting was not re-run (0 runs):** the swap only shrinks
L101 and changes locked VREG pre-route copper inside the area the old part
covered, and a fresh routing would have needed the dozens of attempts the
last two rounds took. Copper diff against master: only the locked
+1V1/VREG_LX pre-route around L101, the router's VREG_LX stub, and one GND
stitching via `zones.py` re-placed beside L101, (50.6, 14.0) -> (50.0,
14.0); every other track and via is unchanged. A second full pipeline run
reproduced the board except one stitching via at (59.4, 30.1), which
`zones.py` places at one of two spots from run to run (also on master's
scripts; unrelated to L101).

- `kicad-cli pcb drc --severity-all --schematic-parity --refill-zones`:
  **77 violations, 0 errors, 0 unconnected, 0 parity**, the same 77
  silkscreen warnings as master, item for item (40 `silk_over_copper`, 35
  `silk_overlap`, 2 `silk_edge_clearance`). `vreg_lx_neck` passes.
- `kicad-cli sch erc --severity-all`: **0 errors, 24 warnings** (the same
  `isolated_pin_label` spare GPIOs as master).
- `netlist_check.py`: **359 pins, 0 mismatches**.
- `zones.py` ground-plane gate and `gnd_paths.py` gate pass; GND_F 18
  polygons / largest 3360 mm^2, GND_B 15 / 3691 mm^2, as master.
- Fab outputs (`preview/scripts/export_fab.py`): BOM row `3.3uH, L101,
  L_Abracon_AOTA-B201610, C42411119`; CPL `L101, 147.0000, -114.5400, Top,
  90`; 73 placed parts, none without an LCSC number, J101 absent.

Still needs a human: a look at L101 in JLCPCB's placement preview (dot
toward the top of the board, on the pad that joins the trace to C104's
left pad and the DVDD run, not the one joining U101 pin 63); a KiCad GUI
look at the VREG block; a glance at Figure 26 if in doubt about the
orientation; the bring-up scope check of the 1.1V rail.
