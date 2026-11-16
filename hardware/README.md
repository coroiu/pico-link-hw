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
  USB-C regardless of the probe. See the schematic's own `J101` text note
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

**Connector and pin table.** J501 is a 40-position, 0.5mm-pitch,
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

`kicad-cli` can run PCB DRC and gerber export headlessly once a real PCB
exists (`kicad-cli pcb drc`, `kicad-cli pcb export gerbers`) — this doesn't
require the GUI, same as the `sch erc` runs already used above. What
genuinely still needs the GUI (or the planned headless `pcbnew` scripting
for placement, see `pilink-7el.9`): the actual routing itself, and a human's
visual/placement sign-off before fab.

`placeholder.kicad_pcb` is a trivial seed file (just a 20x20mm board outline,
no components) for the `preview/` docker-compose service — it proves the
PCB -> GLB export pipeline end-to-end before the real board exists. Delete it
once the real PCB from pilink-7el lands; the preview pipeline picks up
whatever `*.kicad_pcb` file it finds here.
