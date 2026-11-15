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
| **C7463258** | **TYPE-C-31-D-09** | **16P (full)** | **Through Hole** | **5,651** | **6.50mm** |
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
LCSC page) for the three real contenders (D-09, D-15, D-16). For D-09, the
PDF was re-rendered to an image and measured pixel-for-pixel against its
own labeled dimension lines for this revision (rather than re-transcribing
a prior pass's reading), to settle pad/drill/slot geometry and footprint
size definitively:
- **D-09**: pin table is `A1 GND / A4 VBUS / A5 CC1 / A6 DP1 / A7 DN1 /
  A8 SBU1 / A9 VBUS / A12 GND` and the mirrored B-side — an exact match for
  KiCad's stock `Connector:USB_C_Receptacle_USB2.0_16P` symbol (the same
  symbol already used for J401), so no new symbol is needed, only a new
  footprint. Recommended PCB layout is a plated-through-hole pattern: 16
  round signal PTHs plus 4 oval plated-*slot* PTHs for the shell/mounting
  pegs (exact pad/drill/slot sizes in "Footprint" below) — genuine
  through-hole shell retention, not SMT tabs. Overall body height above
  the PCB: 6.50mm. The 8.34mm x 2.56mm figure directly labeled on the
  datasheet's mating-face view is the **connector opening** (the slot the
  USB-C plug's shell inserts into, dimensioned at the shell's inner wall —
  within rounding error of the industry-standard ~8.4mm x 2.6mm USB-C
  receptacle opening common to virtually every USB-C part regardless of
  manufacturer, which is itself a strong corroborating signal that this is
  the mating-interface opening, not this specific part's own outer body
  size), **not** the shell's outer body outline. The shell's own outer
  body is larger: approximately **9.0mm x 3.2mm** (see "Footprint" below
  for how this was measured and how it relates to the copper/keep-out
  size). The 7.70mm and 4.30mm figures used elsewhere for the hole pattern
  are pin-to-pin/slot-to-slot spans (signal-row width and peg-slot-row
  pitch), not the outline either — see "Footprint" below for the actual
  copper/keep-out size.
- **D-15 / D-16**: same HRO vertical mechanical family, same pin table, but
  sold as a *range* of standoff heights (`D-16` = 8.8mm up through `D-16I`
  = 18.5mm; `D-15` = 8.8mm up through `D-15G` = 15.0mm) — these are meant
  for boards mounted well back from an enclosure's panel face, needing a
  long shell to reach the opening. The *shortest* member of either family
  is still 8.8mm, taller than D-09's 6.5mm, and both have far lower stock
  (442/426 vs. D-09's 5,651). Ruled out in favor of D-09.
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
- **Mounting / retention**: through-hole — 16 round signal pins plus 4 oval
  shell/peg pegs all go into drilled, plated holes (the pegs into plated
  *slots*, not round holes) per the recommended PCB layout in the
  datasheet. This satisfies the "through-hole shell pegs preferred over
  SMT-only tabs" requirement directly, for both the signal pins and the
  mechanical shell.
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
- **Footprint**: the datasheet's recommended PCB layout gives two
  through-hole patterns:
  - **16 round signal PTHs**, Ø0.70mm drill inside a Ø0.90mm pad (both
    dimension leader lines point at the *same* hole — Ø0.90 is the copper
    annulus, Ø0.70 is the hole through it), on a 1.10mm pad pitch, spanning
    7.70mm center-to-center from the outermost column on one side to the
    outermost column on the other.
  - **4 oval shell/peg plated slots**, a 0.60mm x 1.30mm drilled slot
    inside a 1.00mm x 1.70mm pad, on a 4.30mm center-to-center pitch from
    the top slot-row to the bottom slot-row.
  7.70mm and 4.30mm are hole-pattern spans, **not the part's outline**.
  Adding each pad's own size to its hole-span gives the actual copper/pad
  extent: **~8.60mm x ~5.30mm** (7.70mm hole-pitch + 0.90mm signal-pad
  diameter on the long axis — the round signal pads are the outermost
  copper there; 4.30mm hole-pitch + 1.00mm peg-pad width on the short
  axis — the oval peg pads are the outermost copper there).

  The 8.34mm x 2.56mm figure labeled on the datasheet's mating-face view
  is **not** the shell's own outline either — it's the **connector
  opening** (the mating slot itself, dimensioned at the inner wall of the
  shell, matching the industry-standard ~8.4mm x 2.6mm USB-C receptacle
  opening common to virtually every USB-C part). Re-measured directly
  against the datasheet's own mating-face-view drawing for this revision
  (pixel measurement of the drawing's actual outer-contour tangent points,
  locally calibrated against that same view's own 8.34mm dimension line,
  since the page is not rendered to one uniform physical scale): the
  shell's true outer body is **larger** than both the opening and the
  ~8.60mm copper extent on the long axis — approximately **9.0mm** long
  (independently re-measured here at ~9.2mm from the datasheet drawing,
  consistent with a separate reviewer measurement of 8.97–9.00mm) by
  approximately **3.16mm** on the short axis — independently confirmed by
  a reviewer's own pixel measurement of the same drawing, taken at
  columns clear of the mounting-peg tabs, directly measuring the figure
  rather than inferring it from consistency with the opening/copper-extent
  range.
  **Correction from the prior revision of this finding, which had this
  backwards**: the shell is **larger** than the copper/pad extent, not
  "slightly smaller." This matters for both downstream beads:
  - `pilink-7el.11` (schematic/footprint swap) needs a **back-side
    courtyard of about 9.0mm x 5.3mm** — the larger of the shell-body
    envelope (~9.0mm x 3.2mm) and the copper/pad extent (~8.60mm x
    5.30mm) on each axis, plus normal clearance — not the smaller figure
    this finding previously implied.
  - `pilink-8hx` (enclosure) needs its **rear-wall cutout sized to clear a
    shell of about 9.0mm x 3.2mm**, not the smaller 8.34mm x 2.56mm
    opening figure.

  Either way it's well within the ~118 x 50mm board outline; this bead
  doesn't place it (PCB layout is `pilink-8hx`/`pilink-7el.9`'s job), just
  confirms it physically fits a back-side placement near the bottom edge
  between the two leg mounts, per the decision doc's "exiting the rear
  wall low, between the legs."
- **Two separate keep-outs — front (legs) and back (shell) — not one
  combined "footprint"**: this is a back-side-mounted connector (the shell
  itself sits on the PCB's back, which is where the connector mounts), but
  its through-hole legs poke all the way through to the front. These are
  two distinct clearance zones on two different sides of the board:
  - **Front-side keep-out, from the protruding legs**: the datasheet's
    side view gives a pin/leg length of **2.10mm** below the shell's
    mounting reference plane. On this project's standard 1.6mm-thick PCB,
    a 2.10mm leg protrudes roughly **0.5mm out the front (component)
    side** of the board — it does not stay hidden under the shell. That
    front-side protrusion needs a keep-out on the front, for other
    front-side placement (components, silkscreen, routing), across the
    same **~8.6mm x ~5.3mm copper/pad extent** computed under "Footprint"
    above (the legs exit at the same hole positions as the pads).
  - **Back-side courtyard, from the shell body itself**: the shell
    physically sits on the back of the board, and its own outer body is
    **~9.0mm x ~3.2mm** (see "Footprint" above). But the through-hole pads
    and mounting-peg tabs also sit on the back side, and on the short axis
    they exceed the shell body (5.3mm vs. 3.2mm). So the back-side
    courtyard that other back-side placement needs to respect is **~9.0mm
    x ~5.3mm**, not the shell-body figure alone: the shell sets the
    long-axis figure (9.0mm, since the shell's long axis exceeds the
    copper/pad extent's ~8.6mm there), while the pads/peg-tabs set the
    short-axis figure (5.3mm, since they exceed the shell's 3.2mm short
    axis there). This matches the ~9.0mm x ~5.3mm courtyard already given
    under "Footprint" above, not the 8.34mm x 2.56mm opening figure.
- **Stock**: 5,651 units, live-checked via JLCPCB's public parts API at
  review time (2026-11-15) — an Extended-library part like J401 already is
  (standard per-part assembly handling fee, not a sourcing-availability
  risk at this project's prototype quantities). Far below J401's own
  509,865-unit stock, but not a low-stock part either. Note: the
  `jlcpcb-search` MCP tool's local database reports 5,490 for this same
  part as of the same date — that tool's figure is a periodically-
  refreshed snapshot, not a true live read, so don't lean on it for
  currency. Recheck actual live stock at order time regardless of which
  number is quoted here (same caveat already flagged for F401 and the
  display panel in other findings).
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
layout specifies, for the 16 signal positions, a **Ø0.70mm drill inside a
Ø0.90mm pad** (both leader lines point at the same hole — Ø0.90 is the
copper annulus, Ø0.70 is the hole through it), on a **1.10mm** pad pitch —
a normal THT pitch, not a fine-pitch part. The 4 shell/peg positions are
not round pads at all: they're **oval plated slots**, a 0.60mm x 1.30mm
drilled slot inside a 1.00mm x 1.70mm pad. The legs themselves are **not**
hidden under the shell: at **2.10mm** long on a standard 1.6mm-thick board,
they protrude roughly **0.5mm out the front (component) side**, where a
THT part's joints are normally soldered with ordinary front/bottom-side
access (wave soldering in production, or hand soldering with a normal
iron) — not a hidden-pad rework case needing selective soldering or
reflow/hot-air.

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
unless cost pressure at order time says otherwise, given the load-bearing
nature of this specific part (not pad-pitch difficulty — 1.10mm is a
normal THT pitch, not fine-pitch).

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

- **Performed**: JLCPCB/LCSC stock and part-detail lookups via the
  `jlcpcb-search` MCP tool (2026-11-15) — that tool's own database reports
  C7463258 at 5,490 units as of this revision, which does not match a
  direct JLCPCB public-API check at review time (5,651 units); treat the
  MCP tool's figure as a periodic snapshot, not true live stock
  (C22464498/D-16 stock 442 is from the same MCP tool and wasn't
  independently cross-checked). Direct reading of the actual manufacturer
  datasheet PDFs (not just the LCSC structured fields) for D-09, D-15,
  D-16, and D-02/C707317, to confirm pin table, orientation, pad sizes/
  pitch, leg length, and height dimension, rather than trusting the LCSC
  `Mounting Type` field or part-number pattern alone. For D-09
  specifically, the PDF was re-rendered to an image and measured
  pixel-for-pixel against its own labeled dimension lines (pad diameters,
  drill/slot sizes, hole pitches) across multiple revisions of this
  finding, most recently to correctly distinguish the datasheet's labeled
  8.34mm x 2.56mm figure — the connector **opening**, matching the
  industry-standard USB-C mating-interface size — from the shell's own,
  larger outer body (~9.0mm x ~3.2mm). An earlier revision of this finding
  had that backwards, calling 8.34mm the "shell outline" and describing
  the shell as smaller than the copper/pad extent rather than larger; see
  "Footprint" above for the corrected figures and reasoning.
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
