# ESP32-WROOM-32U -> ESP32-WROOM-32UE: is the NRND swap worth it before fab?

## Question

The merged `esp32_bt.kicad_sch` (bead `pilink-7el.4`) uses ESP32-WROOM-32U
(`RF_Module:ESP32-WROOM-32U`, Value `ESP32-WROOM-32U-N4`). That bead's
implementer found Espressif's own datasheet marks the part **NOT
RECOMMENDED FOR NEW DESIGNS** and flagged ESP32-WROOM-32UE as the module
Espressif steers new designs toward, without confirming pin-for-pin
equivalence. This bead (`pilink-8zj`) settles: is 32UE a real drop-in, is
it itself healthy to design around, and should the schematic change before
PCB fab?

## Findings

**1. NRND status reconfirmed directly from Espressif.**
`documentation.espressif.com/esp32-wroom-32d_esp32-wroom-32u_datasheet_en.html`
(fetched 2026-11-14): cover page reads "NOT RECOMMENDED FOR NEW DESIGNS
(NRND)", document version **2.8**, revision dated **2026-09-16**. The
datasheet's own "Datasheet Versioning" section defines NRND status as
"updated less frequently" — not a sourcing/EOL statement by itself. The
datasheet does not itself name a replacement part. Espressif's product
catalog page (`espressif.com/en/products/modules`, fetched 2026-11-14)
shows no NRND/EOL badge on either the 32D/32U or 32E/32UE listings and
does not link one to the other — the NRND signal lives specifically in the
32D/32U datasheet document, not the product catalog.

**2. ESP32-WROOM-32UE pin-for-pin cross-check, done directly, not via a
"pin layout equivalence" footnote.** Fetched the full Table 3 "Pin
Definitions" from both datasheets directly
(`esp32-wroom-32d_esp32-wroom-32u_datasheet_en.html` and
`esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.html`, both
documentation.espressif.com, 2026-11-14) and diffed them pin-by-pin for
all 39 positions (38 numbered pins + pin 39 ground/thermal pad). Result:
**identical pin/net assignment on every pin** — same GPIO numbers, same
alternate-function lists (ADC/touch/RTC/SPI/UART/EMAC), same 4x GND
(1/15/38/39), same single NC (pin 32), same EN/3V3 pins. The *only*
difference is cosmetic labeling: the 32D/32U table names pins 17-22 by
their flash-SPI signal names (SHD/SD2, SWP/SD3, SCS/CMD, SCK/CLK, SDO/SD0,
SDI/SD1, all GPIO6-11), while the 32E/32UE table just calls the same six
pins "NC (GPIO6-11 are tied to the internal flash)". Both datasheets agree
these six pins are internal-flash-connected and "not recommended for other
uses" — this project's schematic already leaves them unconnected
(confirmed in `esp32_bt.kicad_sch`'s own notes), so the labeling
difference has zero effect on this design. **Pin-for-pin equivalence is
confirmed from primary sources, not assumed from the package-size
footnote the original bead text flagged as unconfirmed.**

**3. Package is the same footprint family, confirmed from the datasheets
directly, not just dimension text.** Both datasheets list the external
antenna variant at **18.0 x 19.2 x 3.2mm**, identical. Note: the 32UE
datasheet text itself only states "the pin layout of ESP32-WROOM-32UE is
the same as that of ESP32-WROOM-32E" (same-family PCB-antenna sibling) —
it never mentions "32U" by name. The pin-for-pin equivalence to 32U
specifically had to be established independently by diffing both full pin
tables (point 2), not by trusting that one cross-reference sentence.

**4. What "U" -> "UE" / "D" -> "E" actually changed: chip silicon revision,
not flash vendor or certification.** The 32D/32U datasheet names the
embedded chip as plain **ESP32-D0WD** (only mentions "chip revision v3.0
or higher" in passing, in the boot-config section — implying modules could
ship with mixed/earlier silicon revisions). The 32E/32UE datasheet names
the embedded chip as **ESP32-D0WD-V3** explicitly, and its KiCad symbol
description string says the same: "RF Module, ESP32-D0WD-V3 SoC, without
PSRAM". Corroborating secondary sources (LCSC's own blog comparing
32D vs 32E, an Espressif forum thread) describe the E-suffix rename as
Espressif consolidating production onto ECO V3 silicon, which carries
hardware-level fixes over V1 silicon that could ship in D/U-labelled
modules. Neither datasheet documents a different flash vendor or a
different regulatory/certification scope for the E/UE suffix — the
"E" is a silicon-revision guarantee, not a sourcing or certification
change. This matters here only indirectly: nothing in this project's
ESP32 usage (HCI-over-UART controller firmware, no PSRAM, no Wi-Fi
app code) is known to depend on any V1-vs-V3 errata, but a guaranteed-V3
part is strictly a known-good superset of what a mixed-revision 32U could
ship.

**5. ESP32-WROOM-32UE is not itself NRND or EOL.** No NRND/EOL watermark
appears in the extracted text of its datasheet (v2.1, dated 2026-08-05,
`documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.html`),
unlike the 32D/32U datasheet where the same extraction method clearly
surfaced the banner. Caveat: a cover-page watermark rendered as an image
rather than text could in principle be missed by text extraction — this
wasn't cross-checked against a rendered page image (no PDF renderer
available in this environment; see Verification section). Espressif's own
product catalog lists 32E/32UE alongside 32D/32U with no differing
lifecycle badge either way. On balance, the evidence supports 32UE being
Espressif's current, actively-recommended part in this module family, not
just "not NRND" by omission.

**6. JLCPCB/LCSC stock and part number for ESP32-WROOM-32UE-N4 (matching
the project's already-chosen N4/4MB-flash variant).** LCSC part
**C701344**, manufacturer part number **ESP32-WROOM-32UE-N4**,
JLCPCB-listed as an **Extended** part (same library tier as the 32U-N4
part already used, `C328062` — an extended-part handling fee, not a
sourcing-availability flag). Stock snapshots (LCSC product page text,
cross-checked against an independent distributor aggregator) show
**~3,321 units**, consistent across sources checked 2026-11-14 — the same
order of magnitude as the 32U-N4 stock figure pilink-7el.4 already
recorded (2,944-3,383 units), comfortably above any realistic build
quantity for this project. This is a live-site text read, not a
screenshot-verified number (see Verification section) — treat the exact
count as indicative, not precise, same caveat that already applies to the
32U-N4 figure in the merged schematic's notes.

**7. KiCad library check — corrects an assumption in the bead's acceptance
criteria.** The bead's AC text says "RF_Module library may need a 32UE
symbol added, since KiCad 8's stock RF_Module library does not ship one."
Checked directly against the KiCad 8.0.9 install in this environment
(`kicad-symbols 8.0.9-0~ubuntu22.04.1`, `kicad-footprints
8.0.9~ubuntu22.04.1`): **this is already shipped.**
`/usr/share/kicad/symbols/RF_Module.kicad_sym` contains a symbol literally
named `ESP32-WROOM-32UE` (extends `ESP32-WROOM-32E`'s graphics/pins, same
pattern KiCad uses for the U/D pair), with its `Footprint` property
pre-set to `RF_Module:ESP32-WROOM-32UE` and `Datasheet` property pre-set
to the correct 32E/32UE datasheet URL. The footprint
`RF_Module.pretty/ESP32-WROOM-32UE.kicad_mod` also already exists, with a
matching 3D model (`.step`/`.wrl`). **No new symbol/footprint authoring
is needed to swap** — this removes what the bead framed as the main
up-front implementation cost of swapping.

**8. Footprint-level diff: pad numbering/net assignment is identical, pad
*positions* differ by a small, consistent offset.** Diffed
`ESP32-WROOM-32U.kicad_mod` against `ESP32-WROOM-32UE.kicad_mod` directly.
Both have 60 pad entries: pins 1-38 (same numbering, same net-relevant
positions) plus a cluster of small pads/vias all numbered "39" (the
castellated module's center ground/thermal pad, broken into a checkerboard
pattern — a common technique for a large central SMD pad). Side pads
15-24 (top edge) are pixel-identical between the two footprints. Pads
1-14 and 25-38 (the two side columns) are shifted by a consistent **~0.155mm**
in Y between the two files; the central pad-39 cluster is shifted by
**~0.38mm**. Net/pad numbering, pad count, and pad pitch (1.27mm) are
identical — this is not a different pinout or a different package size,
but the two footprints were evidently drawn/maintained as separate KiCad
library files rather than one being copied from the other, so they are
not byte-identical land patterns. This is a normal "re-run DRC/footprint
check" item, not a redesign: swapping the lib_id is enough to pull in the
correct, already-matching-pin-numbers footprint, but the actual pad
geometry should get a human DRC pass against the 32UE datasheet's
mechanical drawing before fab, same as any new footprint would need.

## Recommendation: swap now

Swap `esp32_bt.kicad_sch`'s `U1` from `RF_Module:ESP32-WROOM-32U`
(Value `ESP32-WROOM-32U-N4`) to `RF_Module:ESP32-WROOM-32UE` (Value
`ESP32-WROOM-32UE-N4`) before any PCB layout work consumes the current
footprint. Reasoning:

- The risk this bead was created to evaluate — "is 32UE actually a
  drop-in, or does swapping reopen real design work" — resolves to
  **yes, drop-in**: identical pin/net assignment (point 2), identical
  package envelope (point 3), and the KiCad symbol/footprint Espressif's
  module needs already exists in the stock library (point 7), contrary to
  what the bead's acceptance criteria assumed. The only follow-up work is
  updating `U1`'s `lib_id`/`Value`/`Footprint`/`Datasheet` properties on
  the existing schematic sheet and a human DRC/footprint-geometry check
  (point 8) — not new symbol authoring, not a net/pinout rework, and not a
  firmware change (the HCI-over-UART architecture and GPIO pin assignments
  this project depends on, documented in
  `.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`, are
  unaffected either way).
- 32UE is Espressif's actively-maintained part in this module family
  (point 5) with comparable, healthy JLCPCB/LCSC stock in the exact N4
  variant this project already settled on (point 6) — swapping doesn't
  trade a sourcing risk for a different one.
- The underlying reason Espressif pushes new designs to the E/UE suffix is
  a guaranteed chip silicon revision (ESP32-D0WD-V3, point 4) rather than
  a cosmetic rename — a strict superset of what the NRND 32U might ship,
  with no known downside for this project's use case (no PSRAM, no Wi-Fi
  app code, HCI controller firmware only).
- Cost of swapping is lowest right now: no PCB layout exists yet (only the
  schematic sheet), so there's no routed board, no generated fab
  artifacts, and no gerbers to redo. Deferring the swap to "later" only
  makes it more expensive (if layout/routing starts around the U
  footprint's land pattern) for no corresponding benefit — there's no
  version of "swap later" here that's cheaper than "swap now," since the
  equivalence findings above remove the uncertainty a "wait and see" might
  have been hedging against.

The one real residual risk: the ~0.155mm/~0.38mm footprint-geometry offset
in point 8 should get a human DRC/courtyard check in KiCad against the
32UE datasheet's own mechanical drawing before fab — same standard
caveat this repo already applies to every footprint (no GUI tool in this
agent environment to run DRC).

## Verification performed vs. not performed

- **Performed, from primary sources:** NRND banner text and version/date
  on both datasheets; full Table 3 pin definitions on both datasheets,
  diffed pin-by-pin; module dimensions on both datasheets; chip
  part-number string on both datasheets; Espressif product catalog page
  lifecycle badges; local KiCad 8.0.9 symbol library and footprint library
  file contents, diffed directly.
- **Not performed / caveats:** No PDF renderer was available in this
  environment (no `poppler-utils`/`pdftotext`, no `pip`/`pypdf`) to
  visually confirm the 32E/32UE datasheet's cover page has no NRND
  watermark rendered as an image rather than text — relied on
  Espressif's own HTML-rendered documentation page instead, where no such
  watermark appears anywhere in the page. JLCPCB/LCSC stock figures are a
  live-site text read at a point in time (2026-11-14), not a
  screenshot-verified or API-confirmed number — same caveat already
  present in pilink-7el.4's existing 32U-N4 stock note. No KiCad DRC/ERC
  was run (no human/GUI pass in this environment) — the footprint-geometry
  observation in finding 8 is from reading the `.kicad_mod` file text, not
  from a rendered footprint or DRC report.

## Informs

A decision in `.planning/decisions/` on whether to update `U1` in
`esp32_bt.kicad_sch` — that decision, and the actual schematic edit if the
user agrees, are out of this bead's scope (research-only). If the swap is
accepted, implementation is a small follow-up bead scoped to: (1) change
`U1`'s `lib_id` to `RF_Module:ESP32-WROOM-32UE`, Value to
`ESP32-WROOM-32UE-N4`, and Datasheet property to
`https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf`;
(2) update the BOM/part-number references and the sheet's own
RISK FLAG text block; (3) flag the footprint-geometry DRC check from
finding 8 for the human KiCad pass that already gates this project's
PCB work.

Sources:
- https://documentation.espressif.com/esp32-wroom-32d_esp32-wroom-32u_datasheet_en.html (NRND banner, v2.8, 2026-09-16, full Table 3 pin definitions, module dimensions, chip part number)
- https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32d_esp32-wroom-32u_datasheet_en.pdf (canonical PDF, same content)
- https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.html (v2.1, 2026-08-05, full Table 3 pin definitions, module dimensions, chip part number, 32UE-vs-32E pin-layout statement)
- https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf (canonical PDF, same content)
- https://www.espressif.com/en/products/modules (product catalog, no lifecycle badges on either pair)
- https://www.lcsc.com/product-detail/C701344.html (ESP32-WROOM-32UE-N4, LCSC part C701344)
- https://www.lcsc.com/blog/esp32-wroom-32d-vs-32e-which-module-should-you-select-for-your-next-design/ (secondary source corroborating the D0WD vs D0WD-V3/ECO-revision distinction between the D/U and E/UE lines)
- https://esp32.com/viewtopic.php?p=81330 (Espressif forum thread corroborating the same ECO V3 distinction)
- Local KiCad 8.0.9 install (`kicad-symbols`/`kicad-footprints` 8.0.9-0~ubuntu22.04.1): `/usr/share/kicad/symbols/RF_Module.kicad_sym`, `/usr/share/kicad/footprints/RF_Module.pretty/ESP32-WROOM-32U.kicad_mod`, `/usr/share/kicad/footprints/RF_Module.pretty/ESP32-WROOM-32UE.kicad_mod` (symbol/footprint existence and pin/pad diff)
- `hardware/esp32_bt.kicad_sch` (current merged schematic, for what would need to change)
