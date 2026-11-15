# Vertical-mount USB-C receptacle for the PCB back side (`pilink-0do`)

## Question

`.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md` decided
the rear USB-C on the upright body uses a **vertical-mount receptacle
soldered to the back of the PCB**, not a pigtail to an edge-mount part — the
PCB stands parallel to the front face, so "out the back of the enclosure"
means the connector's mating axis has to run perpendicular to the PCB
plane, not in-plane the way the current J401 (`TYPE-C-31-M-12`, a
horizontal edge-mount part) is wired. This bead picks the actual
replacement part. The schematic/footprint swap itself is a separate bead,
`pilink-7el.11`; this is research/selection only.

Constraints from the bead and the decision doc:
- USB 2.0 only — no SS/TX/RX pins needed (`usb_c.kicad_sch`'s own note:
  "USB 2.0 only — RP2350B has no USB3 PHY"; confirmed again here against
  the current schematic text).
- LCSC/JLCPCB part with live stock.
- Mounting height checked against the enclosure's ~5mm back cavity — a
  local back-shell boss to fit a taller part is acceptable, don't force a
  bad part to fit.
- Mechanical retention preferably via **through-hole shell pegs** (stronger
  against plug-insertion/removal force than SMT-only tabs) — insertion
  force is a real repeated load on this connector, unlike most other parts
  on the board.
- Assembly-approach recommendation with a rough cost delta: JLCPCB
  double-sided PCBA (both sides machine-populated) vs. hand-soldering a
  THT-legged variant onto the back after JLCPCB populates the front only.

## Method

Searched JLCPCB's component database via the `jlcpcb-search` MCP tool.
Plain keyword search (`"USB Type-C vertical"`, `"vertical receptacle"`,
etc.) returned nothing — the local database's search only matches on part
name/number tokens, not on structured mounting-orientation text, so those
terms don't appear in any part's *name*. Worked around this by searching
on the HRO part-number family already in use (`TYPE-C-31-*`, the same
manufacturer as the current J401) and pulling `get_component_details` on
each hit, which **does** return a `Mounting Type` field (`Surface Mount,
Right Angle` / `Through Hole` / `Surface Mount,Vertical`) even though the
search index doesn't. Cross-checked the shortlisted candidates' actual
mechanical drawings (official HRO datasheet PDFs, downloaded and read
directly — not assumed from the LCSC field alone) to confirm real
orientation, pin table, and the height dimension this bead needs.

## Candidates checked

All are Korean Hroparts Elec (`krhro.com`) parts — same manufacturer as
the current J401, whose `TYPE-C-31-M-xx` numbering is the *horizontal*
edge-mount family. HRO's `TYPE-C-31-D-xx` numbering is the mechanically
distinct **vertical** family (datasheet-confirmed below), and that's where
every real "vertical, cable mates perpendicular to the PCB" option lives in
this manufacturer's lineup on JLCPCB.

| LCSC | Part | Pins | Mounting (LCSC field) | Stock (research time) | Datasheet-confirmed height above PCB |
|---|---|---|---|---|---|
| **C7463258** | **TYPE-C-31-D-09** | **16P (full)** | **Through Hole** | **5,490** | **6.50mm** |
| C22464498 | TYPE-C-31-D-16 | 16P | Through Hole | 442 | 8.8mm (`H` column in its own datasheet's size table) |
| C22464480 | TYPE-C-31-D-15 | 16P | Surface Mount, Vertical | 426 | 8.8mm (same `H`-table scheme as D-16) |
| C22464422 | TYPE-C-31-D-06A | 16P | Surface Mount, Vertical | 145 | not checked (low stock ruled it out early) |
| C223908 | TYPE-C-31-M-15 | 14P | Through Hole | 2,464 | **horizontal** family (M-prefix) despite "Through Hole" mounting — wrong orientation, ruled out |
| C707317 | TYPE-C-31-D-02 | 6P | Surface Mount, Vertical | 805 | 6P only (no CC pins in a usable 6-pin layout for this design) — ruled out |
| C22464507 | TYPE-C-31-D-17 | 14P | Through Hole | 594 | drops 2 of the 16 standard pins — ruled out in favor of the full-pinout D-09 |

(Full search results and every `get_component_details` call behind this
table are reproducible from the `jlcpcb-search` MCP tool; not re-pasted
here in full.)

Datasheet drawings were pulled directly (`krhro.com` PDFs, linked from each
LCSC page) for the three real contenders (D-09, D-15, D-16):
- **D-09**: pin table is `A1 GND / A4 VBUS / A5 CC1 / A6 DP1 / A7 DN1 /
  A8 SBU1 / A9 VBUS / A12 GND` and the mirrored B-side — an exact match for
  KiCad's stock `Connector:USB_C_Receptacle_USB2.0_16P` symbol (the same
  symbol already used for J401), so no new symbol is needed, only a new
  footprint. Recommended PCB layout is a plated-through-hole pattern (16
  signal PTHs + 4 larger shell/peg PTHs), confirming genuine through-hole
  shell retention, not SMT tabs. Overall body height above the PCB: 6.50mm.
  Body footprint: 8.34mm wide x ~7.7mm long.
- **D-15 / D-16**: same HRO vertical mechanical family, same pin table, but
  sold as a *range* of standoff heights (`D-16` = 8.8mm up through `D-16I`
  = 18.5mm; `D-15` = 8.8mm up through `D-15G` = 15.0mm) — these are meant
  for boards mounted well back from an enclosure's panel face, needing a
  long shell to reach the opening. The *shortest* member of either family
  is still 8.8mm, taller than D-09's 6.5mm, and both have far lower stock
  (422/426 vs. 5,490). Ruled out in favor of D-09.
- **M-15** (`C223908`) looked promising from the LCSC field alone
  ("Mounting Type: Through Hole") but its own part-number prefix (`M-`,
  not `D-`) is HRO's horizontal-family prefix, same as the current J401
  (`M-12`) — "through hole" there almost certainly describes through-hole
  *shell pegs on an otherwise horizontal edge-mount part* (a mechanically
  stronger horizontal variant), not a vertical orientation. Not opened in
  detail once the D-09 datasheet confirmed a better-stocked, shorter,
  genuinely-vertical, full-pinout alternative existed — flagging this as
  an assumption from the naming convention, not a datasheet check, in case
  a future bead wants the through-hole-but-horizontal option for some
  other reason.

## Chosen part: TYPE-C-31-D-09, LCSC `C7463258`

- **Manufacturer**: Korean Hroparts Elec (same manufacturer as the current
  J401 `TYPE-C-31-M-12`, so the same general quality/sourcing profile).
- **Mechanical**: genuinely vertical — mating face perpendicular to the
  PCB, cable inserts by approaching straight into/out of the board's
  normal direction, not along the board edge. This is exactly what "exits
  the rear wall, PCB parallel to the face" needs.
- **Pinout**: full 16-pin (A1/A12/B1/B12 GND, A4/A9/B4/B9 VBUS, A5/B5
  CC1/CC2, A6/B6 DP1/DP2, A7/B7 DN1/DN2, A8/B8 SBU1/SBU2) — identical to
  KiCad's stock `Connector:USB_C_Receptacle_USB2.0_16P` symbol already in
  use for J401, so the schematic-side pin mapping `pilink-7el.11` will do
  (DP/DM to the existing `USB_DP`/`USB_DM` global labels, CC1/CC2 to
  R401/R402 + the R403/R404 sense taps, VBUS through F401, GND/SHIELD to
  ground) carries over unchanged. Only the footprint changes.
- **Mounting / retention**: through-hole — 16 signal pins plus 4 larger
  shell/peg pins all go into drilled, plated holes per the recommended PCB
  layout in the datasheet. This satisfies the "through-hole shell pegs
  preferred over SMT-only tabs" requirement directly, for both the signal
  pins and the mechanical shell.
- **Height above PCB**: **6.50mm**, datasheet-confirmed. This **exceeds**
  the ~5mm back cavity from the form-factor decision by about 1.5mm. Per
  that decision doc, a local boss in the back shell to accommodate a
  taller part is an accepted option, not a blocker — no shorter
  comparably-stocked full-pinout vertical option exists in this search (the
  only shorter vertical part found, `TYPE-C-31-D-02`/`C707317`, is a 6-pin
  power-only variant with no usable CC pins for this design's existing
  CC-sense-tap circuitry). **`pilink-8hx`'s back-shell OpenSCAD work should
  add a ~1.5-2mm boss around the connector cutout** (some margin beyond
  the bare 1.5mm gap for solder-side clearance and tolerance) rather than
  assume a flush 5mm-deep pocket.
- **Footprint**: 8.34mm shell width x ~7.7mm body length on the PCB — well
  within the ~118 x 50mm board outline; this bead doesn't place it (PCB
  layout is `pilink-8hx`/`pilink-7el.9`'s job), just confirms it physically
  fits a back-side placement near the bottom edge between the two leg
  mounts, per the decision doc's "exiting the rear wall low, between the
  legs."
- **Stock**: 5,490 units at research time (2026-11-15) — an Extended-
  library part like J401 already is (standard per-part assembly handling
  fee, not a sourcing-availability risk at this project's prototype
  quantities). Far below J401's own 509,865-unit stock, but not a
  low-stock part either; worth re-checking at order time the way this
  project already re-checks every part before ordering (same caveat
  already flagged for F401 and the display panel in other findings).
- **Datasheet**: https://datasheet.lcsc.com/datasheet/pdf/26cf9302eb505927cdbd9bd7e2981be6.pdf?productCode=C7463258
- **JLCPCB listing**: https://jlcpcb.com/partdetail/C7463258

## Assembly-approach recommendation

Two real options once a through-hole vertical connector is on the back:

1. **JLCPCB standard double-sided PCBA** (JLCPCB machine-populates both
   sides; the back side carries only this one part, J401).
2. **JLCPCB single-sided PCBA (front only)**, then hand-solder the
   THT-legged D-09 onto the back after the boards arrive.

**Recommendation: double-sided JLCPCB PCBA (option 1).** This connector's
20 total legs (16 signal + 4 shell/peg) are fine-pitch (0.5mm signal pitch,
standard for any USB-C receptacle) and largely **hidden under the shell
once mounted** — the inner rows of pins on a vertical THT Type-C connector
are not visually accessible with an iron the way a THT header's pins are.
Hand-soldering this reliably needs selective soldering or a reflow/hot-air
process the way SMT does, not a casual iron-and-flux job, and this
connector carries the one load on the whole board that's mechanically
repeated and nontrivial (plug insertion/removal force) — a cold or bridged
joint here is a real functional-failure and ESD/short risk, not just a
cosmetic one. Given that, the reliability case for professional assembly
on this specific part is stronger than for most other components on the
board.

**Rough cost delta (flagged estimate, not a live quote):** I did not get an
actual JLCPCB PCBA quote — that needs real Gerbers/BOM/CPL files, which
don't exist yet (PCB layout is `pilink-7el.9`/`pilink-8hx`'s separate,
not-yet-complete work). Based on JLCPCB's generally published PCBA
pricing structure (not verified against a live quote for this board):
- JLCPCB's standard assembly service supports "top only / bottom only /
  both sides" as a quote-time option for mixed SMT+THT boards; adding the
  back side is a **one-time setup charge** (stencil + a second
  placement/solder pass), not a significant per-unit-scaling cost at
  hobbyist quantities (low units to tens of boards). The component itself
  being an Extended-library part (like several others already on this
  board: U501, D501, J501, SW303 per `hardware/BOM.md`) carries JLCPCB's
  standard flat per-unique-extended-part handling fee regardless of which
  side it's on — that fee is **not** specific to the double-sided choice.
  THT parts on a JLCPCB assembly order typically add a modest per-part or
  per-joint handling charge on top of the baseline SMT fee, independent of
  side.
- Net: the realistic added cost of "also populate the back" at this
  project's scale is a **one-time, low-tens-of-dollars-at-most** setup
  charge once, not a dominant line item next to the board's other
  Extended parts (ESP32, display) — but this is an estimate from JLCPCB's
  known pricing *patterns*, not this board's own quote. **Before ordering,
  run JLCPCB's actual instant-quote tool once Gerbers/CPL/BOM exist**
  (flagging this as the real verification step — an agent cannot get a
  live JLCPCB PCBA quote without files this project hasn't produced yet).
- Hand-soldering avoids that setup charge entirely but trades it for a
  real reliability/rework risk on the one connector that takes repeated
  mechanical load, plus it's a physical task only a human can do (soldering
  is explicitly called out in `AGENTS.md` as the user's own action, not an
  agent's).

This is ultimately a small-money, physical-assembly decision — ordering
PCBA is the user's call per `AGENTS.md`, not something to decide here. This
finding's job is to make that call well-informed: pick double-sided PCBA
unless cost pressure at order time says otherwise, given the fine-pitch,
load-bearing nature of this specific part.

## Open items for `pilink-7el.11` (the schematic/footprint swap bead, not this one)

- Create/import a KiCad footprint for `TYPE-C-31-D-09` (no stock KiCad
  library footprint matches this specific manufacturer part — same
  situation the RP2350B/PSRAM parts were in on `rp2350b_memory.kicad_sch`,
  resolved there by adding a project-local footprint library).
- Update `J401`'s `Value`/`Footprint`/`Datasheet` properties on
  `usb_c.kicad_sch` and the `hardware/BOM.md` J401 row (currently lists
  `TYPE-C-31-M-12` / `C165948` — neither touched by this bead).
- Re-run `kicad-cli sch erc` after the swap (the symbol/pinout is
  unchanged, so no ERC-relevant behavior is expected to change, but this
  should still be verified, not assumed).

## Verification performed vs. not performed

- **Performed**: live JLCPCB/LCSC stock and part-detail lookups via the
  `jlcpcb-search` MCP tool (2026-11-15); direct reading of the actual
  manufacturer datasheet PDFs for the three real vertical-family
  candidates (D-09, D-15, D-16) to confirm pin table, orientation, and
  height dimension, rather than trusting the LCSC `Mounting Type` field or
  part-number pattern alone.
- **Not performed** (needs a human or a later bead):
  - No physical/CAD fit check against the actual OpenSCAD back-shell
    model — `pilink-8hx`'s enclosure work doesn't exist yet to check
    against. The ~5mm cavity figure comes from the form-factor decision
    doc's approximate figures, not a modeled back-shell boss.
  - No live JLCPCB PCBA quote (needs real Gerbers/CPL/BOM — not available
    at this stage of the project).
  - No footprint/symbol creation or schematic edit (explicitly out of
    scope — `pilink-7el.11`).
  - No KiCad ERC/DRC run (nothing in the schematic changed in this bead).

## Informs

`pilink-7el.11` — this finding's chosen part (`TYPE-C-31-D-09`, LCSC
`C7463258`) is what that bead should implement.
