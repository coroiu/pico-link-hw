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
finalized — see the gain comparison on the candidates below.

**Type vs. gain, re-checked against the datasheet's exact wording:** the
testing caveat isn't gain-only. The datasheet's own sentence is "If you
use an external antenna of a different type or gain, additional
testing, such as EMC, may be required" — type and gain are two separate
triggers (joined by "or"), not one. **Resolved in this revision:** the
datasheet *does* state what antenna type Espressif certified the module
with. Section 10.2 ("Dimensions of External Antenna Connector") says,
in a sentence that runs across the page 41/42 break — apparently why an
earlier pass of this finding missed it — "The external antenna used for
ESP32-WROOM-32UE during certification testing is the first generation
monopole antenna, with material code TFPD05H08750011." Confirmed
directly against Espressif's own datasheet PDF (v2.1) in this revision.
That's a monopole, which matches both FPC candidates below **at the
monopole-type level**. One narrower caveat remains: the datasheet
doesn't say whether the certified unit's construction was specifically
FPC (as opposed to some other monopole build), so that construction-level
detail stays unconfirmed — but the type match at the monopole level is
now a primary-source fact, not an open question. A secondhand reference
(an ESP32 forum post describing the module's own FCC/TÜV test report,
not independently opened in this pass — the report PDF 403'd) had
claimed the certification antenna was a **PIFA**; that claim is
**contradicted** by the primary-source datasheet text above and should
be disregarded.

## Candidates

Both are adhesive-backed flexible (FPC) antennas with a thin coax
pigtail terminated in an IPEX/U.FL-class plug — the standard way to
mount an antenna inside a plastic enclosure near the connector, as
opposed to a rigid stick/whip antenna (which needs an external bulkhead
mount this project's "fully internal antenna" requirement rules out) or
a ceramic chip antenna (needs its own PCB keepout + ground-plane cutout
on the module board itself, not a good fit for a late add-on).

### Primary: Kinghelm KH-FPC2.4G-1.13IPEX-240 — LCSC `C4943394`

- **Type:** adhesive-backed FPC monopole antenna, 3M adhesive backing,
  mounts to a non-conductive surface (i.e., the inside of a plastic
  enclosure wall, not metal) — directly matches the "antenna location
  in the top wall" plan in the upright-desk-clock ADR.
- **Element dimensions:** ~45.8 × 6.5mm, confirmed directly on LCSC's
  own product page (`C4943394`, packaging field "SMD, 45.8x6.5mm") —
  fits the same ~35-45 × 8-12mm enclosure niche estimate used in
  `docs/plans/2026-11-15-product-layout-proposal.md`, slightly
  longer/narrower than the alternate below.
- **Cable:** Ø1.13mm coax, IPEX-class plug. The part number's "-240"
  suffix implies a 240mm cable, but LCSC's own listing page does not
  state cable length as its own spec field — treat 240mm as **inferred
  from the part number**, not a confirmed datasheet/listing fact. If
  accurate, that's longer than the 50-120mm target range; the excess
  would be routing slack to be coiled/folded inside the enclosure
  cavity during assembly, not something to trim (re-terminating a U.FL
  pigtail needs crimp tooling this project doesn't have reason to
  assume is available by default). Confirm the actual cable length
  before ordering.
- **Gain:** ~2 dBi peak, confirmed directly on LCSC's own product page
  in this pass — clearly **within** Espressif's 2.33dBi
  certification-safe ceiling (above), with real margin rather than a
  fractional one. This is why it's the default: it needs no
  certification-risk sign-off before use, unlike the alternate below.
- **Stock/source:** LCSC catalog part. A live-site search snapshot
  showed ~86 units in stock, unit price from ~$0.34 at research time
  (2026-11-15) — thin for a default part, flagged explicitly by review.
  Re-checked in this revision: the `jlcpcb-search` MCP tool's local
  database (JLCPCB's SMT pick-and-place catalog) still returns no match
  for this part (confirming the "not a JLCPCB-assembly part" explanation
  below, not a stock signal), and LCSC's own live stock counter is
  rendered client-side on the product page, so it isn't readable
  through the fetch tools available in this pass either. The 86-unit
  figure is therefore still only the original point-in-time snapshot —
  re-check it directly on LCSC immediately before ordering, and don't
  treat it as current.
- Datasheet/product page: LCSC `C4943394` (manufacturer Kinghelm).

### Alternate: MyAntenna AIWF026 — LCSC `C49242188`

- **Type:** adhesive-backed FPC monopole, 3M adhesive backing, mounts to
  a non-conductive surface — same mounting style as the primary.
  **Not** a single-band 2.4GHz part: it's a dual/tri-band antenna
  covering both 2400-2500 MHz (2.4GHz ISM — WiFi/BT/Zigbee-class) *and*
  5100-7200 MHz (5GHz Wi-Fi + 6GHz Wi-Fi 6E/7). This project only uses
  the 2.4GHz band, but the antenna's spec and gain figures have to be
  read band-by-band, not from its tri-band headline.
- **Element dimensions:** 35.2 × 8.5 × 0.2mm — comfortably inside the
  enclosure niche.
- **Cable:** Ø1.13mm coax, ~100mm, terminated IPX1 (IPEX/U.FL-class)
  plug, black jacket. 100mm is mid-range for the ~50-120mm target.
- **RF spec:** 50Ω, VSWR ≤ 2, rated 10W, -40~85°C, ~0.5g.
- **Gain — CORRECTED:** an earlier pass of this finding used the
  manufacturer/LCSC listing's headline **"4.79 dBi peak"** figure and
  compared it directly to Espressif's 2.33dBi ceiling, concluding it was
  "over double" the limit. That headline figure is this antenna's peak
  gain **at 6200 MHz**, inside the 5-7GHz band it also covers — not the
  2.4GHz band this device uses, so it's the wrong number for this
  comparison. The manufacturer's own per-frequency gain table (the
  AIWF026/MyAntenna datasheet, "Peak Gain (dBi)" table on page 3) gives,
  across the actual 2400-2500 MHz band: **1.69 dBi at 2400 MHz, peaking
  at 2.35 dBi at 2450 MHz, and 1.65 dBi at 2500 MHz** — a 1.65-2.35 dBi
  in-band range. **Re-verified directly in this revision:** the
  datasheet PDF (hosted at `datasheet.lcsc.com`, linked from LCSC's own
  `C49242188` product page) has a genuine extractable text layer — it is
  **not** an image/CAD-drawing-only scan, unlike the `C1693673` datasheet
  noted below. These three figures were read directly off that text
  layer's gain table (no OCR/image-rendering tooling needed) and
  cross-checked against the same values restated in the PDF's own
  "Radiation Patterns" section headers (e.g. "2450MHz Gain=2.35dBi"),
  not pulled from a secondary web-search extraction. **Corrected
  conclusion:** the real in-band peak
  (2.35 dBi at 2450 MHz) is **0.02 dB over** Espressif's 2.33dBi
  cert-safe ceiling — essentially at the ceiling, not "over double."
  That's a far smaller gap than the uncorrected figure suggested, but
  it's still *over*, not under: this part is not clearly within the
  cert-safe ceiling, and a 0.02dB margin is well within normal
  manufacturing/measurement tolerance, so real units could land on
  either side of the line. **Before using this part:** confirm that
  margin is an acceptable risk (e.g. against the actual test report's
  measurement uncertainty) or use the Kinghelm primary above instead,
  which has real margin under the ceiling.
- **Stock/source:** LCSC catalog part. Confirmed orderable via LCSC's
  own product page with live pricing tiers visible (e.g. 900+ units ≈
  $0.30/unit, packaged 300/bag) at research time (2026-11-15). Re-checked
  in this revision: still not found in the `jlcpcb-search` MCP tool's
  local JLCPCB database (same reason as the primary — see below), and a
  ~154-unit figure surfaced by a general web search in the earlier pass
  could not be independently confirmed (LCSC's live stock counter is
  client-side and not readable through the fetch tools available here)
  — treat as "confirmed live LCSC catalog item, unconfirmed current
  count," not "154 units in stock today."
- Datasheet: https://www.lcsc.com/datasheet/C49242188.pdf (and LCSC
  product page `C49242188`).

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
  over the primary/alternate above, which both have confirmed element
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
a one-line add. Also still open: the AIWF026 alternate's fractional
gain-margin caveat (0.02dB over the cert-safe ceiling, see above) still
needs an explicit decision if it's ever chosen over the Kinghelm
primary. Recommend a follow-up bead to:

1. Confirm the Kinghelm-primary / AIWF026-alternate ranking above still
   holds (or escalate the AIWF026 gain-margin question to the user if
   it's being considered instead, since being fractionally over the
   cert-safe ceiling is a compliance-risk call even at this small
   margin);
2. Add the chosen part to `hardware/BOM.md` under a new "hand-assembled,
   non-schematic parts" section (or equivalent), with its LCSC number
   and live stock re-checked at that time.

## What wasn't verified

- Live stock *counts* for both candidates still come from LCSC web
  snapshots (search-result/page-fetch), not a live API path. Re-checked
  in this revision: the `jlcpcb-search` MCP tool's local database
  (JLCPCB's SMT pick-and-place catalog, not LCSC's full marketplace)
  returns no match for either `C4943394` or `C49242188` — confirms
  (doesn't newly establish) that this part class is out of that tool's
  scope, not a usable live-stock source for these two parts. LCSC's own
  product pages render stock counts client-side (JavaScript), which
  isn't readable through the fetch tools available in this pass either.
  Both candidates' stock figures are therefore still the original
  point-in-time snapshots from the first research pass — re-check both
  directly on LCSC immediately before ordering, especially the
  Kinghelm's thin ~86-unit figure for a default/primary part.
- The AIWF026's in-band gain figures (1.65-2.35 dBi) were read directly
  off the datasheet PDF's own text layer in this revision (see above,
  and the datasheet-wording note) — the PDF has a genuine text layer,
  not an image-only scan, so this is no longer an open item.
- Resolved in this revision: Espressif's own certification for the
  ESP32-WROOM-32UE used a monopole antenna — datasheet section 10.2
  states this directly (material code TFPD05H08750011) — which matches
  both candidates here at the monopole-type level. One narrower gap
  remains: the datasheet doesn't state whether the certified unit's
  construction was specifically FPC (vs. some other monopole build), so
  that construction-level detail stays unconfirmed. The secondhand
  forum claim of a PIFA certification antenna is contradicted by this
  primary source and should be disregarded.
- No physical fit check against the actual enclosure (no OpenSCAD model
  of the top wall exists yet) — deferred to `pilink-8hx.4` by design.
- No RF/antenna measurement of either candidate — gain figures are
  taken from manufacturer/distributor listings, not independently
  measured.
