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
| C707317 | TYPE-C-31-D-02 | 6P | Surface Mount, Vertical | 805 | 6P only — GND/VBUS/CC1/CC2, **no D+/D-** — power-only, can't carry USB Audio data — ruled out |
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
  Body footprint: ~7.70mm wide x 4.30mm deep (the datasheet's "8.34mm" figure
  is the shell's outer edge measured along the *same* width axis as the
  7.70mm hole-pattern span, not a second, orthogonal dimension — the two
  were wrongly treated as width x length in an earlier pass of this finding).
- **D-15 / D-16**: same HRO vertical mechanical family, same pin table, but
  sold as a *range* of standoff heights (`D-16` = 8.8mm up through `D-16I`
  = 18.5mm; `D-15` = 8.8mm up through `D-15G` = 15.0mm) — these are meant
  for boards mounted well back from an enclosure's panel face, needing a
  long shell to reach the opening. The *shortest* member of either family
  is still 8.8mm, taller than D-09's 6.5mm, and both have far lower stock
  (442/426 vs. 5,490). Ruled out in favor of D-09.
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
  the ~5mm back cavity figure given in `pilink-0do`'s own bead description
  by about 1.5mm (that ~5mm figure and the "a local back-shell boss is OK"
  allowance both come from the bead description, not from the form-factor
  ADR itself — the ADR doesn't give a cavity depth or mention a boss). Per
  that allowance, a local boss in the back shell to accommodate a taller
  part is acceptable, not a blocker — no shorter comparably-stocked
  full-pinout vertical option exists in this search (the only shorter
  vertical part found, `TYPE-C-31-D-02`/`C707317`, is a 6-pin variant with
  GND/VBUS/CC1/CC2 but no D+/D-, so it's power-only and can't carry USB
  Audio data for this design regardless of height). **`pilink-8hx`'s
  back-shell OpenSCAD work should add a ~1.5-2mm boss around the connector
  cutout** (some margin beyond the bare 1.5mm gap for solder-side clearance
  and tolerance) rather than assume a flush 5mm-deep pocket.
- **Footprint**: ~7.70mm wide x 4.30mm deep on the PCB (see the datasheet
  note above on the 8.34mm figure) — well within the ~118 x 50mm board
  outline; this bead doesn't place it (PCB layout is
  `pilink-8hx`/`pilink-7el.9`'s job), just confirms it physically fits a
  back-side placement near the bottom edge between the two leg mounts, per
  the decision doc's "exiting the rear wall low, between the legs."
- **Through-hole legs protrude through the front of the board, not hidden
  under the shell**: the datasheet's side view gives a pin/leg length of
  **2.10mm** below the shell's mounting reference plane. On this project's
  standard 1.6mm-thick PCB, a 2.10mm leg protrudes roughly **0.5mm out the
  front (component) side** of the board — it does not stay hidden under the
  shell the way an earlier pass of this finding assumed. That front-side
  protrusion plus the shell's footprint creates a **front-side keep-out of
  roughly 8mm x 4.3mm** around the connector that other front-side
  placement (components, silkscreen, routing) needs to respect.
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

**Recommendation: double-sided JLCPCB PCBA (option 1).** This connector has
20 total legs (16 signal + 4 shell/peg). The datasheet's recommended PCB
layout gives the 16 signal pads as **Ø0.70mm** through-holes and the 4
shell/peg pads as **Ø0.90mm**, with a minimum pad-to-pad pitch of about
**1.10mm** in the drawing — not the 0.5mm figure an earlier pass of this
finding assumed (0.5mm pitch is physically impossible for a 0.70mm-diameter
pad in any case, since adjacent pads would overlap). The legs themselves
are **not** hidden under the shell: at **2.10mm** long on a standard
1.6mm-thick board, they protrude roughly **0.5mm out the front (component)
side**, where a THT part's joints are normally soldered with ordinary
front/bottom-side access (wave soldering in production, or hand soldering
with a normal iron) — not a hidden-pad rework case needing selective
soldering or reflow/hot-air.

Given that, the case for professional (JLCPCB) assembly over hand-soldering
rests on **reliability under repeated mechanical load**, not on pad
accessibility: this connector carries the one load on the whole board
that's mechanically repeated and nontrivial (plug insertion/removal
force, rated 3.57kgf insertion / 1.02kgf min removal per the datasheet) —
a cold or bridged joint here is a real functional-failure and ESD/short
risk, not just a cosmetic one. A machine-soldered joint is more
consistently reliable than a hand-soldered one for a part that takes that
kind of repeated load, even though a careful hand-soldered joint is
mechanically accessible and achievable.

**Rough cost delta (flagged estimate, not a live quote):** I did not get an
actual JLCPCB PCBA quote — that needs real Gerbers/BOM/CPL files, which
don't exist yet (PCB layout is `pilink-7el.9`/`pilink-8hx`'s separate,
not-yet-complete work). Based on JLCPCB's generally published PCBA pricing
structure (not verified against a live quote for this board), and
correcting the earlier framing, which wrongly applied SMT stencil+reflow
cost logic to a THT part:
- JLCPCB's assembly service prices **THT (through-hole) parts separately
  from SMT**: THT components are assembled via a distinct per-joint
  through-hole assembly service (hand- or wave-soldered at the factory,
  billed per through-hole joint/pin), not via the stencil-plus-reflow
  pipeline used for SMT parts. There is no "second stencil pass" involved
  for this part regardless of which side it's on — stencils are an SMT
  paste-printing concept and don't apply here.
- JLCPCB's standard assembly service does support "top only / bottom only /
  both sides" as a quote-time option for mixed SMT+THT boards; adding a
  back side with just this one THT part means the quote picks up the
  per-joint THT assembly charge for its ~20 pins/legs, plus (if any other
  back-side SMT parts existed) a possible second SMT pass — but on this
  board the back side carries only J401, so no SMT stencil/reflow pass is
  needed on the back at all, just the THT joint charge. The part's
  Extended-library status (like several others already on this board:
  U501, D501, J501, SW303 per `hardware/BOM.md`) separately carries
  JLCPCB's standard flat per-unique-extended-part handling fee, independent
  of the THT charge.
- Net: the realistic added cost of "also populate the back" at this
  project's scale is a **one-time, low-tens-of-dollars-at-most** THT
  assembly + extended-part handling charge, not a dominant line item next
  to the board's other Extended parts (ESP32, display) — but this is an
  estimate from JLCPCB's known pricing *patterns*, not this board's own
  quote. **Before ordering, run JLCPCB's actual instant-quote tool once
  Gerbers/CPL/BOM exist** (flagging this as the real verification step — an
  agent cannot get a live JLCPCB PCBA quote without files this project
  hasn't produced yet).
- Hand-soldering avoids that charge entirely but trades it for a real
  reliability risk on the one connector that takes repeated mechanical
  load (not a rework-difficulty risk — the joints are front-side
  accessible, as corrected above), plus it's a physical task only a human
  can do (soldering is explicitly called out in `AGENTS.md` as the user's
  own action, not an agent's).

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
  `jlcpcb-search` MCP tool (2026-11-15, re-confirmed during this revision —
  C7463258 stock still 5,490, C22464498/D-16 stock 442); direct reading of
  the actual manufacturer datasheet PDFs (not just the LCSC structured
  fields) for D-09, D-15, D-16, and (added in this revision) D-02/C707317,
  to confirm pin table, orientation, pad sizes/pitch, leg length, and
  height dimension, rather than trusting the LCSC `Mounting Type` field,
  part-number pattern, or an un-rechecked prior reading alone.
- **Not performed** (needs a human or a later bead):
  - No physical/CAD fit check against the actual OpenSCAD back-shell
    model — `pilink-8hx`'s enclosure work doesn't exist yet to check
    against. The ~5mm cavity figure and the "boss is OK" allowance come
    from `pilink-0do`'s own bead description, not from a modeled back-shell
    boss or from the form-factor ADR itself.
  - No live JLCPCB PCBA quote (needs real Gerbers/CPL/BOM — not available
    at this stage of the project).
  - No footprint/symbol creation or schematic edit (explicitly out of
    scope — `pilink-7el.11`).
  - No KiCad ERC/DRC run (nothing in the schematic changed in this bead).

## Informs

`pilink-7el.11` — this finding's chosen part (`TYPE-C-31-D-09`, LCSC
`C7463258`) is what that bead should implement.
