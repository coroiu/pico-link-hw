# Selecting the external 2.4GHz antenna for the ESP32-WROOM-32UE

**Bead:** `pilink-8wx` · **Status:** Current

## Question

No U.FL/IPEX antenna part exists anywhere in this repo (`hardware/BOM.md`
has no antenna line). The ESP32-WROOM-32UE (confirmed BT coprocessor per
`.planning/decisions/2026-11-15-esp32-wroom-32ue-swap.md`) needs an
external antenna connected via its antenna connector. Need: confirm the
connector type against the 32UE's own datasheet (don't assume U.FL vs
MHF1/MHF4), then pick a primary + fallback 2.4GHz antenna with
dimensions, ground-plane/clearance guidance, a cable length that fits a
small enclosure (~50-120mm), and live stock/source.

## Connector type — confirmed from the primary datasheet

Read directly (Espressif "ESP32-WROOM-32E / ESP32-WROOM-32UE Datasheet",
v2.1, section 10.2 "Dimensions of External Antenna Connector"):

> ESP32-WROOM-32UE uses the first generation external antenna connector...
> This connector is compatible with the following connectors:
> - U.FL Series connector from Hirose
> - MHF I connector from I-PEX
> - AMC connector from Amphenol

So it is **not** MHF4 (a physically different, smaller connector family
used on newer modules) — it's the older/larger "U.FL-class" footprint,
and Hirose U.FL, I-PEX MHF1, and Amphenol AMC mating connectors/pigtails
are all mechanically interchangeable with it. Any antenna pigtail
described as "U.FL", "IPEX"/"IPX1", or "MHF1" on its LCSC/manufacturer
listing is the right connector family for this module. (Module overall
size independently confirmed: 18.0 × 19.2 × 3.2mm, matching the figure
already in the ESP32-WROOM-32UE swap ADR.)

The same datasheet section gives Espressif's own antenna-selection
guidance, which both candidates below should be checked against:

- 2.4GHz band, 50Ω impedance
- **Max gain should not exceed 2.33 dBi** — the gain of the antenna
  Espressif used for the module's own FCC/IC certification. Using a
  higher-gain external antenna than this is explicitly flagged by
  Espressif as potentially requiring **additional EMC/certification
  testing** beyond the module's existing antenna test reports.
- Connector matching the Figure 12 mechanical spec (confirmed above).

This 2.33dBi ceiling is a real constraint for the certification path
this project is relying on (ESP32 modular approval) and should be
treated as a hard requirement, not a nice-to-have, when the antenna is
finalized — see the caveat on the primary candidate below.

## Candidates

Both are adhesive-backed flexible (FPC) antennas with a thin coax
pigtail terminated in an IPEX/U.FL-class plug — the standard way to
mount an antenna inside a plastic enclosure near the connector, as
opposed to a rigid stick/whip antenna (which needs an external bulkhead
mount this project's "fully internal antenna" requirement rules out) or
a ceramic chip antenna (needs its own PCB keepout + ground-plane cutout
on the module board itself, not a good fit for a late add-on).

### Primary: MyAntenna AIWF026 — LCSC `C49242188`

- **Type:** adhesive-backed FPC monopole, 3M adhesive backing, mounts to
  a non-conductive surface (i.e., the inside of a plastic enclosure
  wall, not metal) — directly matches the "antenna location in the top
  wall" plan in the upright-desk-clock ADR.
- **Element dimensions:** 35.2 × 8.5 × 0.2mm — comfortably inside the
  ~35-45 × 8-12mm estimate already used in
  `docs/plans/2026-11-15-product-layout-proposal.md`.
- **Cable:** Ø1.13mm coax, ~100mm, terminated IPX1 (IPEX/U.FL-class)
  plug, black jacket. 100mm is mid-range for the ~50-120mm target.
- **RF spec:** 2.4GHz (ISM — WiFi/BT/Zigbee-class), 50Ω, VSWR ≤ 2, rated
  10W, -40~85°C, ~0.5g.
- **Gain — CAVEAT:** the LCSC/manufacturer listing states **4.79 dBi
  peak**. That's over double Espressif's 2.33dBi certification-safe
  ceiling (above). This doesn't rule the part out — small FPC monopoles'
  advertised "peak" gain figures are frequently optimistic/direction-
  dependent compared to the isotropic-averaged figure certification
  testing cares about, and plenty of ESP32 projects use similar adhesive
  antennas without incident — but **it needs an explicit decision before
  production**, not a silent pass-through: either confirm the real
  (not datasheet-peak) gain is within tolerance, accept the
  recertification/compliance risk knowingly, or swap to a antenna
  with a documented gain at or under ~2.3dBi (see fallback). Filing this
  as part of the BOM-gap follow-up below rather than resolving it here,
  since it's a certification-strategy call, not a sourcing one.
- **Stock/source:** LCSC catalog part (not found in the local
  `jlcpcb-search` MCP database — see note below on why that's expected
  for this part class). Confirmed orderable via LCSC's own product page
  with live pricing tiers visible (e.g. 900+ units ≈ $0.30/unit,
  packaged 300/bag) at research time (2026-11-15). Exact current unit
  count wasn't machine-readable from the page in this pass — treat as
  "confirmed live LCSC catalog item," not "confirmed N units in stock
  today."
- Datasheet: https://www.lcsc.com/datasheet/C49242188.pdf (and LCSC
  product page `C49242188`).

### Fallback: Kinghelm KH-FPC2.4G-1.13IPEX-240 — LCSC `C4943394`

- **Type:** adhesive-backed FPC antenna, same mounting style as the
  primary.
- **Element dimensions:** ~45.8 × 6.5mm (per Kinghelm's own published
  spec) — fits the same enclosure niche, slightly longer/narrower than
  the primary.
- **Cable:** Ø1.13mm coax, **240mm**, IPEX-class plug. Longer than the
  50-120mm target range — the excess is routing slack to be coiled/
  folded inside the enclosure cavity during assembly, not something to
  trim (re-terminating a U.FL pigtail needs crimp tooling this project
  doesn't have reason to assume is available by default).
- **Gain:** ~2 dBi per Kinghelm's published spec — **within** the
  2.33dBi Espressif certification ceiling, which is why this is the
  fallback to reach for if the primary's gain figure can't be resolved
  satisfactorily.
- **Stock/source:** LCSC catalog part. A live-site search snapshot at
  research time showed ~86 units in stock, unit price from ~$0.34 — low
  stock relative to the primary, and, like the primary, not present in
  the local `jlcpcb-search` MCP database. Treat the 86-unit figure as a
  point-in-time snapshot, not a guarantee; re-check before ordering.
- Datasheet/product page: LCSC `C4943394` (manufacturer Kinghelm).

### Why these didn't show up well in the `jlcpcb-search` MCP tool

The `jlcpcb-search` MCP server's local database (JLCPCB's SMT
pick-and-place parts catalog, refreshed 2026-11-15, 390,031 components)
did surface two IPEX-connector antennas directly
(`C1693673`/`HJ-2.4G-IPEX1-L=80mm`, 397 units live stock; and
`C1693678`/`HJ-2.4G-IPEX-1.13-PCB-L85MM`, 40 units, delisted from LCSC's
own site at research time) — see "other candidates considered" below —
but neither had a datasheet that would actually render as text (LCSC's
PDF for `C1693673` is an image/CAD-drawing-only scan with no extractable
text), so their physical form (adhesive FPC vs. something else) and gain
couldn't be confirmed from the primary source, only from the catalog's
terse spec fields (connector: IPEX; 2.45GHz; VSWR 2; 50Ω).

More broadly: a cable-and-connector antenna like this **can't be placed
by JLCPCB's pick-and-place line** (no SMD pads — it is hand-assembled
after the board comes back from fab, plugging into the module's U.FL
receptacle by hand). That's consistent with these parts' absence from
JLCPCB's own assembly-oriented component database even though they're
live, orderable LCSC catalog items — the two tools cover different
scopes (JLCPCB SMT assembly catalog vs. LCSC's full parts marketplace),
and "not found in `jlcpcb-search`" should not be read as "not sourceable
from LCSC."

### Other candidates considered, not recommended

- `C1693673` (HJ-2.4G-IPEX1-L=80mm): live JLCPCB-catalog stock (397
  units) confirmed via the `jlcpcb-search` tool, but its form factor
  (adhesive FPC vs. rigid stick) and gain couldn't be confirmed from any
  readable source in this pass — not enough information to recommend
  over the primary/fallback above, which both have confirmed element
  dimensions and gain.
- `C1693678` (HJ-2.4G-IPEX-1.13-PCB-L85MM): only 40 units in the JLCPCB
  snapshot, and the part no longer resolves on LCSC's own product site
  (404) at research time — likely delisted; not recommended.

## Clearance / ground-plane guidance

Espressif's module-level guidance (datasheet §11.2, "Module Placement
for PCB Design") only covers the *module's own* antenna keepout zone,
which is moot for the -32UE variant (it explicitly has **no** keepout
zone on the module itself, since the antenna moves off-module to the
U.FL connector — confirmed from the datasheet's pin-layout note). The
relevant clearance for this project is for the **external antenna
element** itself, once sited: standard practice for an adhesive FPC
antenna (not covered in the 32UE's own datasheet, which doesn't ship an
antenna) is to keep the flexible element itself clear of metal/ground
plane/battery within roughly its own element length on the radiating
side, and to route its coax pigtail away from running parallel to other
high-speed/noisy traces. Concretely for this enclosure: mounting the
element adhesive-side against the inner top-wall plastic (per the
upright-desk-clock ADR's "antenna location in the top wall") keeps it
away from the PCB's ground plane and the ESP32 module's own copper by
design, which is the right default. The exact placement/clearance check
against the real enclosure geometry is explicitly **out of scope** for
this bead — that's `pilink-8hx.4` (internal U.FL antenna mount).

## BOM gap — follow-up needed

`hardware/BOM.md` has no antenna line for either candidate. Not added
here: the BOM's existing six schematic-derived sections
(`power`/`rp2350b_memory`/`esp32_bt`/`display`/`input`/`usb_c`) are
compiled directly from placed `.kicad_sch` symbols with a specific,
carefully-documented stock-check methodology (see the BOM's own header
and `hardware/README.md`) — but the antenna is **not a schematic
component** (no symbol/footprint, hand-assembled via the U.FL pigtail
after fab, no net to connect in KiCad), so it doesn't fit that
methodology and adding it correctly means deciding how BOM.md should
represent non-schematic hand-assembly items at all, which is bigger than
a one-line add. Also still open: the gain-vs-certification caveat on the
primary candidate above needs a decision before the antenna could be
treated as "selected" for BOM purposes. Recommend a follow-up bead to:

1. Decide primary vs. fallback (or escalate the gain/certification
   question to the user, since it's a compliance-risk call);
2. Add the chosen part to `hardware/BOM.md` under a new "hand-assembled,
   non-schematic parts" section (or equivalent), with its LCSC number
   and live stock re-checked at that time.

## What wasn't verified

- Live stock *counts* for both candidates come from LCSC web snapshots
  (search-result/page-fetch), not the `jlcpcb-search` MCP tool's live
  JLCPCB API path (which doesn't carry these LCSC-only parts) — re-check
  immediately before ordering.
- No physical fit check against the actual enclosure (no OpenSCAD model
  of the top wall exists yet) — deferred to `pilink-8hx.4` by design.
- No RF/antenna measurement of either candidate — gain figures are
  taken from manufacturer/distributor listings, not independently
  measured.
