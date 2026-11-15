# Display alternatives: avoiding OLED, prioritizing contrast ratio

## Question

The current prototype uses a Waveshare Pico-LCD-1.3 (1.3", 240x240, ST7789).
The user's complaint: "backlight is just making everything gray" — a
low-contrast-ratio symptom (poor black depth), not a resolution complaint.
OLED/AMOLED is explicitly ruled out (24/7 near-static content, burn-in
risk). This bead asks: are there real, sourceable LCD-class panels (IPS/VA/
transflective, non-OLED) in the ~1.3"-2.4" class with a **datasheet-
documented** contrast ratio meaningfully better than cheap hobby ST7789
modules, ideally staying in the ST7789/ILI9341/GC9A01 driver family so no
firmware driver rewrite is needed? Compare against the already-selected
1.9" ST7789V, 320x170 baseline (`docs/plans/2026-11-13-custom-hardware-
design.md`).

(Per a mid-task scope correction from the user, this finding does not cover
e-paper/e-ink. That part of the original bead framing was dropped — this is
LCD-vs-LCD only. The bead `pilink-maj`'s acceptance criteria still mention
e-paper coverage; that's a stale artifact of the original framing and has
been noted as a comment on the bead, not edited into its description.)

## Findings

### 1. Why cheap ST7789 hobby panels look "washed out" — and a correction to the first draft's baseline framing

Waveshare does not publish a panel-level (LCM) optical datasheet for the
Pico-LCD-1.3 — only the ST7789VW **controller** datasheet
(`files.waveshare.com/wiki/common/ST7789VW.pdf`, Sitronix), which documents
electrical/timing characteristics of the driver chip, not the physical
panel's contrast ratio or luminance. Contrast ratio is a property of the
LC cell + backlight + polarizers, not the driver IC, so it's simply not in
that document — and the Waveshare wiki/product page for Pico-LCD-1.3 lists
no contrast spec anywhere.

**Correction from the reviewed draft:** the previous version of this finding
claimed no contrast number exists for a panel in the chosen 1.9"/320x170
class, and used that to frame a "~500:1 baseline" from adjacent-but-not-
identical parts. That framing doesn't survive a closer look. Waveshare's own
**"1.9inch Touch LCD" (SKU 31122)** — the same panel also used on Waveshare's
ESP32-S3-LCD-1.9 / ESP32-S3-Touch-LCD-1.9 dev boards — is the *same size,
same resolution, and same driver family* as the project's chosen baseline,
and Waveshare's own spec table for it documents **Contrast Ratio 900:1** at
500 cd/m² brightness. Verified directly in this pass (2026-11-15) via live
fetch of both `waveshare.com/product/displays/lcd-oled/1.9inch-touch-lcd.htm`
and `docs.waveshare.com/ESP32-S3-LCD-1.9` — both independently list the same
figures: Resolution 170×320 (Waveshare's own pages inconsistently also say
172×320 elsewhere), Driver IC ST7789V2, Contrast ratio 900:1, Brightness 500
cd/m². See finding 2 below for the full writeup of this as its own
candidate.

Caveat on that 900:1 figure: it's a vendor spec table for an **assembled
touch breakout module** (onboard voltage translator, SH1.0 + FPC0.5
connectors, pin header), not an LCM-level datasheet for a bare panel, and
it's the ST7789V2 revision rather than plain ST7789V — same Sitronix
command-set family, no firmware-rewrite implication, but not a byte-for-byte
identical part to the bare panel the current design doc specifies.

To get additional real numbers for other, more distant comparison points, I
also pulled datasheets for other same-class modules:

- **Same size/resolution as the project's 1.9" baseline, bare panel:**
  BuyDisplay ER-TFT019-1, 1.9" IPS, 170x320 (also listed as 172x320 on
  BuyDisplay's own spec table — same inconsistency as Waveshare's), ST7789 —
  datasheet states **Contrast Ratio (Typ) 500:1**, **Sunlight Readable: No**.
  The product page URL in the original draft (`.../any-angle-viewing-...`)
  now 404s/403s to a direct fetch; the live page is
  `buydisplay.com/full-viewing-angle-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789`.
- **Same resolution as the old 1.3" Waveshare panel:** Orient Display
  AFL240240A0-1.3INTM-ANO, 1.3" IPS, 240x240, ST7789-family —
  datasheet states **contrast ratio 500:1 at θ=0°**. **Weakly verified**:
  the DigiKey HTML datasheet page is behind Cloudflare and couldn't be
  independently re-fetched in this pass; sibling parts in the same family
  show different numbers (AFR240240A0-1.3INTM: 640/800; AFR240240A0R-
  1.3INTM: 400/600), so treat this 500:1 figure with the same caution
  applied to the Orient AFY figure in finding 4 below, not as solidly
  confirmed as the directly-read Newhaven/EA figures.
- **Not a fair calibration point — flagged, not dropped:** DM-TFT24-383
  (generic 2.4" hobby module) datasheet lists **Contrast Ratio (typ) 300**,
  which the original draft used as a "~300:1 commodity hobby floor"
  anecdote. That datasheet's own header/listing identifies this part as
  **2.4" 240x320 TRANSFLECTIVE**, not transmissive — confirmed via the
  distributor's product listing and datasheet. A transflective panel adds a
  reflective layer tuned for outdoor/no-backlight legibility and is *not* a
  like-for-like comparison against the transmissive IPS panels this research
  is otherwise comparing (see finding 5, which independently found that
  transflective panels trade contrast away, not gain it). The 300:1 number
  is real for this specific part, but it should not be read as "a generic
  transmissive hobby ST7789 panel can be this bad" — it's a different
  display technology entirely. Treat it as a technology-adjacent data point,
  not a load-bearing calibration anecdote.

Net correction: the project's actual *bare-panel* ST7789 IPS baseline in
this size class most plausibly still sits around ~500:1 for the
closest-matching bare panels found (BuyDisplay, Orient Display) — but a
documented, vendor-published **900:1** figure exists for an assembled
module using the exact same size/resolution/driver family as the chosen
baseline (Waveshare SKU 31122). That significantly narrows, and in the
900:1 module's case erases, the contrast gap this research originally set
out to close for the two closest-fit candidates (see findings 2 and 4).

### 2. Strongest same-form-factor candidate: Waveshare 1.9" 170x320 ST7789V2 panel (SKU 31122 / "1.9inch LCD Module" SKU 23822), 900:1

- **Part numbers:** Waveshare SKU 31122 ("1.9inch Touch LCD," with CST816
  capacitive touch) and its non-touch sibling, Waveshare SKU 23822
  ("1.9inch LCD Module"). Both use the same 1.9", 170x320, ST7789V2 panel;
  the same cell is also sold pre-integrated on Waveshare's ESP32-S3-LCD-1.9
  / ESP32-S3-Touch-LCD-1.9 dev boards.
- **Size / resolution:** 1.9", 170x320 — identical to the project's already-
  chosen baseline (`docs/plans/2026-11-13-custom-hardware-design.md`).
- **Driver IC:** ST7789V2 — same Sitronix ST7789 family as the baseline's
  ST7789V; command set is near-identical, expect no firmware driver
  rewrite.
- **Contrast ratio:** **900:1**, 500 cd/m² brightness. Documented on the
  touch variant's (SKU 31122) own spec table, confirmed via direct fetch of
  `waveshare.com/product/displays/lcd-oled/1.9inch-touch-lcd.htm` and
  `docs.waveshare.com/ESP32-S3-LCD-1.9`, 2026-11-15. The non-touch sibling's
  (SKU 23822) own product page does **not** restate a contrast-ratio figure
  — it's reasonable to infer the same LC cell given identical size,
  resolution, and driver IC, but this is an inference, not an independent
  confirmation on the non-touch listing itself. Flagging this honestly
  rather than asserting it.
- **Interface:** 4-wire SPI (SKU 23822 non-touch module lists pins BL, RST,
  DC, CS, CLK, DIN, GND, VCC — i.e. a dedicated D/C pin, matching the
  project's existing 4-wire-SPI firmware). SKU 31122 touch variant adds I2C
  for the CST816 touch controller, usable or ignorable depending on whether
  touch is wanted.
- **Form factor / integration caveat (important):** both SKUs are sold as
  **assembled breakout PCB modules** — onboard voltage translator (3.3V/5V),
  pin header or MX1.25/SH1.0 connector, bundled cable — not as a bare panel
  with just an FPC tail in the style the project's current design doc
  specifies (bare panel + 0.5mm-pitch FPC connector direct to the project
  PCB). No bare-panel-only SKU of this exact cell was found in this
  research. Adopting this candidate most likely means one of: (a) mounting
  Waveshare's breakout module as-is inside the enclosure (simplest, no
  interface change, but the module is a larger assembly — ~27.3x51.2mm with
  an onboard voltage translator — than the bare panel the enclosure design
  doc assumed, so internal mounting depth/volume is affected even if the
  visible window cutout doesn't need to change); (b) desoldering the bare
  panel's FPC tail off the breakout module and discarding the rest (voids
  any warranty, not confirmed physically feasible without the module's own
  schematic); or (c) sourcing the same underlying panel cell bare from
  Waveshare's OEM/panel supplier directly (not identified in this
  research). None of these is free — "zero enclosure change" understates
  the real integration cost to (at least) "zero visible window-cutout
  change, nonzero internal mounting/depth consideration."
- **Stock / price:** both SKUs show "Add to Cart" with per-unit pricing
  (SKU 31122 ~$12.99 list, SKU 23822 ~$11.99 list, with volume breaks) but
  neither product page displays a stock count or lead time — unlike the
  DigiKey-listed candidates below, Waveshare's own storefront doesn't expose
  that number. Get a quote/stock check directly from Waveshare (or a
  distributor carrying this SKU, e.g. Pi Hut, Little Bird Electronics,
  Switch Science) before committing.
- **Tradeoff:** this is the only candidate in this document that needs *no*
  enclosure/cutout change at all (same 1.9"/170x320 panel size/resolution as
  the already-chosen baseline) while still clearing a documented contrast
  figure (900:1) higher than every other same-driver-family candidate
  except the larger Newhaven panel (finding 3, 1500:1 typ). The integration
  cost is the breakout-module-vs-bare-panel mismatch above, not an
  enclosure rework. **This is plausibly the single best, lowest-risk
  recommendation in this document if that connector/mounting question
  resolves cleanly** — but that question was not fully resolved in this
  research pass and is the main open item before treating this as a final
  pick.

### 3. Largest contrast win, needs enclosure rework: Newhaven NHD-2.4-240320AF-CSXP (and siblings)

- **Part number:** NHD-2.4-240320AF-CSXP (non-touch); same family covers
  -CTP (capacitive touch) and -T (resistive touch) suffixed siblings.
- **Size / resolution:** 2.4", 240x320.
- **Driver IC:** ST7789VI — same driver family as the project's ST7789V/
  ST7789VW baseline (Sitronix ST7789 family share a near-identical command
  set; expect at most minor init-sequence tuning, not a rewrite).
- **Interface:** revision-dependent. The original board revision (Rev2A)
  supports **3-wire SPI only** — Newhaven's own transition guide and support
  forum confirm the interface-mode pin strapping on that revision can't be
  configured for 4-wire SPI. A later board revision (Rev2B, per Newhaven's
  June 17, 2025 engineering change notice) **adds 4-wire SPI support** via a
  redesigned FPC and additional interface-mode pin. **This matters directly
  for this project:** the existing firmware uses 4-wire SPI with a dedicated
  D/C pin, so if this candidate is chosen, confirm Rev2B is what ships (via
  the datasheet revision marking or directly with Newhaven/the distributor)
  before committing to it — Rev2A would need either a firmware rework to
  3-wire SPI or a different part.
- **Contrast ratio:** datasheet states **contrast ratio min 800 / typ
  1500:1** (newhavendisplay.com/content/specs/NHD-2.4-240320AF-CSXP.pdf).
  That's still the clearest documented contrast win in this document —
  roughly 1.7x the 900:1 figure found for the same-size-class Waveshare
  candidate in finding 2, and well above the ~500:1 bare-panel baseline.
- **Luminance:** 1200 cd/m² typ, described as "High Brightness/Sunlight
  Readable," normally-black, anti-glare, transmissive.
- **Stock — corrected:** the previous draft of this finding, and the PR
  description, stated "191 units confirmed live" at DigiKey part 22204988.
  That figure was wrong. Re-checked live in this session (2026-11-15) on
  both `digikey.com` and `digikey.de`: **current in-stock quantity is 7
  units**, with an **18-week manufacturer standard lead time** shown on
  both regional pages beyond that on-hand quantity. The "191" figure most
  likely came from a stale search-engine-cached snapshot of the page rather
  than a direct live read — this pass used a direct live fetch of the
  product page itself, not a cached search result, and both regional
  storefronts agree on 7/18-weeks as of today. For any volume beyond
  single-digit prototype quantities, get a quote from Newhaven/DigiKey
  rather than assuming stock will cover it.
- **Tradeoff:** physically bigger than the current 1.3"/1.9" panels (2.4"
  vs 1.9" diagonal) — this means an enclosure cutout/bezel rework, which is
  explicitly out of scope for this research-only bead. If this candidate is
  chosen, that's a new hardware bead.

### 4. Closer-size, same-driver, now a weaker pick given finding 2: Display Visions EA-TFT020-23AINN

- **Part number:** EA-TFT020-23AINN (non-touch); touch sibling
  EA-TFT020-23AITC (optically-bonded capacitive/PCAP touch — a physically
  different, bonded-touch-layer part, not just a firmware option).
- **Size / resolution:** 2.0", 240x320.
- **Driver IC:** ST7789V — the *exact* driver already used in the chosen
  baseline, zero firmware-driver change at all.
- **Interface:** SPI or RGB.
- **Contrast ratio:** family datasheet (EA TFT020-23AI, hosted at
  `lcd-module.com/fileadmin/eng/pdf/grafik/TFT020-23AI.pdf`) states
  **contrast ratio min 640 / typ 800:1**.
- **Corrected framing:** the previous draft presented this as a "~1.6x
  improvement" over the ~500:1 baseline. Given finding 2 — Waveshare's own
  900:1-documented 1.9"/170x320 panel in the *same* driver family, at the
  *same* resolution as the project baseline — this 800:1 typ figure is
  **not actually better** than that same-form-factor alternative. It no
  longer has a clear edge on either contrast or form factor over the
  Waveshare candidate, only a (possibly real, unconfirmed) stock advantage
  on the touch sibling specifically. It's kept here for completeness and
  because its non-touch stock situation is genuinely uncertain (see below),
  but it's no longer the obvious "lower-risk, still-meaningfully-better"
  second pick that the earlier draft framed it as.
- **Stock — corrected, touch/non-touch parts were conflated:** the previous
  draft said "DigiKey/RS Components stock confirmed" without distinguishing
  the two part numbers clearly enough. Re-checked in this session:
  - **EA-TFT020-23AITC** (touch, PCAP-bonded): DigiKey part 10712688
    (1481-EATFT020-23AITC-ND) — confirmed live, **In-Stock: 20**,
    Touchscreen attribute "Capacitive." This is **not** the part being
    recommended here.
  - **EA-TFT020-23AINN** (non-touch, the part actually recommended): RS
    Components stock no. 221-1845. Regional RS snapshots disagree —
    "temporarily out of stock" on the UK and Singapore storefronts in
    recent reads, vs. "in stock, ~5 units" on New Zealand/Norway/Philippines
    storefronts in recent reads. A direct live fetch of the UK listing in
    this session returned a 503 (page unavailable at check time), so this
    pass could not get a single authoritative current number. **Net: the
    non-touch part's stock is genuinely unconfirmed** — don't treat it as
    "confirmed" the way the Newhaven and EA-TFT020-23AITC figures above are;
    get a live quote/stock check before committing to this part.
- **Possible 24/7-static-content concern (unconfirmed in this pass):** the
  PR review flagged that the EA-TFT020-23AI datasheet reportedly warns that
  static/unchanging content can cause image retention ("ghost images").
  This session's attempts to re-extract the PDF text directly (via
  `lcd-module.com`, `lcd-module.de`, and Mouser's hosted copy) were
  unsuccessful — the PDF-text-extraction limitation already disclosed
  elsewhere in this document applied here too, so the exact datasheet
  wording could not be independently re-confirmed. Flagging this as
  reported-but-not-independently-verified rather than omitting it, since
  static-image retention on LCD/IPS panels under 24/7 near-static content
  (this device's actual use case) is a real, known phenomenon regardless of
  this specific datasheet's exact wording, and is worth checking directly
  with the vendor or via a physical sample before committing to this part
  for always-on near-static UI.

### 5. LCSC/JLCPCB-native option, weaker — flagged honestly rather than oversold

- **Part number:** Orient Display AFY240320A0-2.4INTH-R.
- **Size / resolution:** 2.4", 240x320, IPS, ST7789V-family driver (the
  `-C` touch sibling's product page confirms ST7789V for this family).
- **Contrast ratio:** Rev B datasheet (orientdisplay.com/pdf/
  AFY240320A0-2.4INTH.pdf) gives a contrast ratio in roughly the **500-750**
  range at θ=0°, with luminance 800-1000 cd/m² — only a modest, uncertain
  improvement over the ~500:1 bare-panel baseline, and no longer clearly
  better than the Waveshare 900:1 candidate in finding 2 either.
- **Stock:** real part number with a real LCSC listing (LCSC **C20578695**)
  and a real DigiKey listing (2544-AFY240320A0-2.4INTH-R-ND, Active) — but
  the LCSC page showed **0 units on-hand** at check time (2026-11-15). This
  is the most "LCSC/JLCPCB-native" of the candidates researched (relevant
  if a future bead wants automated SMT assembly sourcing specifically
  through LCSC/JLCPCB rather than DigiKey), but given the weak contrast
  number and unconfirmed current stock, it's not recommended as a primary
  choice right now.

### 6. VA and transflective: checked, not recommended

The bead asked to evaluate VA and transflective panels, not just IPS,
seriously. Direct findings:

- Newhaven's own **product transition guide**
  (newhavendisplay.com/content/docs/2.4IPS-CSXP_TransitionGuide.pdf) groups
  their older CF-series 2.4" modules (which includes a TN/MVA-class part,
  NHD-2.4-240320CF-BSXV-F) as the line being **phased out in favor of the
  newer IPS AF-series** (finding 3's candidate) for this exact panel class.
  That's a maker explicitly moving away from VA/MVA toward high-brightness
  IPS + anti-glare treatment as the better answer to "contrast/sunlight
  readability" in this size/driver segment — not researcher bias, their own
  roadmap.
- The older CF-series MVA/TN part's own contrast figure, previously marked
  "not found" in this document, is in fact available: NHD-2.4-240320CF-
  BSXV-F's datasheet lists **contrast ratio min 150 / typ 200:1**
  (mouser.lt/pdfDocs/NHD-24-240320CF-BSXV-F.pdf; DigiKey part 11476257) —
  worse than every IPS candidate in this document, consistent with
  Newhaven's own decision to phase this line out.
- No VA/MVA candidate was found that beats the IPS options above on
  documented contrast ratio with confirmed live distributor stock.
- Transflective panels (which add a reflective layer for no-backlight
  outdoor readability) were checked incidentally, and now with a real,
  sourced example rather than an unsourced claim: DisplayModule
  **DM-TFT20-436**, a 2.0" 240x320 transflective, resistive-touch, ST7789-
  driver TFT module, documents **contrast ratio typ 250:1** at 200 cd/m²
  luminance (displaymodule.com product listing; datasheet hosted at
  cdn.shopify.com/.../DM-TFT20-436_Datasheet.pdf). Only the typ figure is
  confirmed on DM-TFT20-436's own datasheet — a "min 200:1" figure exists
  but belongs to the sibling part DM-TFT20-435, not this one; not repeating
  that misattribution here. 250:1 is still *worse* than every
  transmissive IPS candidate above, consistent with the general pattern
  that transflective trades contrast for sunlight legibility without
  backlight power. Since this device isn't primarily an outdoors/no-
  backlight use case, that tradeoff doesn't fit the stated priority
  (contrast first).

## Recommendation

Three real candidates emerged (sourced from manufacturer datasheets for
Newhaven and the DisplayModule transflective comparison, and from
Waveshare's own vendor spec table rather than a standalone datasheet PDF —
see the per-candidate disclosure above), all ST7789-family (no
firmware driver rewrite), each with a different risk/contrast tradeoff:

- **If minimizing physical and enclosure change matters most, and the
  breakout-module-vs-bare-panel connector question resolves cleanly:**
  Waveshare's 1.9" 170x320 ST7789V2 panel (SKU 31122 touch / SKU 23822
  non-touch) — **900:1 documented contrast**, exactly the project's chosen
  size/resolution/driver family, zero enclosure-cutout change expected. This
  is the strongest "no enclosure rework" candidate found, and plausibly the
  best overall pick, but it ships as an assembled breakout module rather
  than a bare FPC panel, so confirm the connector/mounting approach (or find
  a bare-panel source for the same cell) before treating it as final.
- **If maximizing contrast matters most and a larger panel/enclosure
  rework is acceptable:** Newhaven **NHD-2.4-240320AF-CSXP** — 1500:1 typ /
  800:1 min documented contrast (2.4", ST7789VI, DigiKey part 22204988).
  **Stock is now confirmed at 7 units on-hand with an 18-week lead time**
  (not 191, as an earlier draft wrongly stated from what was likely a stale
  search-engine snapshot) — fine for a couple of prototype units, not for
  assuming volume availability. Also confirm the board revision supports
  4-wire SPI (Rev2B does; the original Rev2A does not) before ordering,
  since the project's firmware uses 4-wire SPI with a dedicated D/C pin.
  This is still the clearest single best-documented contrast number in this
  document, at the cost of a real enclosure/bezel rework.
- **Weaker third option, included for completeness:** Display Visions
  **EA-TFT020-23AINN** — 800:1 typ / 640:1 min documented contrast (2.0",
  exact same ST7789V driver already in use). No longer clearly better than
  the Waveshare candidate above on either contrast or form factor, and its
  actual non-touch-part stock (RS 221-1845) could not be reliably confirmed
  in this pass — regional snapshots disagree, and a live re-check returned
  a server error. Only pick this if the Waveshare connector question turns
  out to be a dead end and the EA stock resolves favorably on a direct
  check.

The Orient Display LCSC-native option (finding 5) remains included for
completeness but not recommended as a first pick — its contrast improvement
over baseline is marginal, it's no longer better than the Waveshare
candidate either, and its live LCSC stock wasn't confirmed at check time.

This is research only; the user makes the actual call (panel size vs.
contrast vs. integration-risk tradeoff) — no `.planning/decisions/` ADR
was written by this bead, per its acceptance criteria.

## Verification performed vs. not performed

- **Performed:** Live WebFetch/WebSearch lookups against manufacturer
  datasheets and product pages (Newhaven, Display Visions/EA, Orient
  Display, BuyDisplay, Waveshare, DisplayModule) and distributor listings
  (DigiKey, Mouser, LCSC, RS Components) on 2026-11-15, cross-checking
  driver IC, resolution, contrast ratio, and luminance figures against
  primary-source text wherever a readable (non-image-compressed) rendering
  was available. The Newhaven stock figure, the Waveshare 900:1 figure, the
  DigiKey 10712688 stock figure, the DM-TFT24-383 transflective
  classification, and the DM-TFT20-436 transflective contrast figure were
  all independently re-verified via direct live fetch/search in this pass,
  not copied from the PR review that flagged them.
- **Not performed / caveats:** Several Orient Display, Newhaven, and
  Display Visions PDFs are image/vector-heavy or Flate-compressed in ways
  this environment's fetch tooling could not text-extract directly (no
  PDF-text tooling available locally, confirmed again in this pass); those
  figures were instead corroborated via search-engine text extraction of
  the same documents, which is a weaker form of verification than a direct
  read — flagged inline above wherever this applies (the Orient Display
  "~500-750" range, the AFL240240A0-1.3INTM-ANO 500:1 figure, and the
  possible EA-TFT020-23AI ghost-image warning, in particular). The
  Waveshare 900:1 figure and the Newhaven 7-units/18-week stock figure, by
  contrast, came from direct HTML fetches of the live pages themselves, not
  PDF extraction or search snippets — higher confidence than the
  PDF-sourced figures. Distributor stock counts are point-in-time reads
  (2026-11-15), not API-confirmed or screenshot-verified, same standard
  caveat this repo already applies to other sourcing findings (see
  `.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md`). No
  physical panel was obtained or bench-tested — this is desk research only,
  as the bead scoped it. Whether Waveshare (or another vendor) sells the
  SKU-31122/23822 panel cell as a bare FPC panel without the breakout PCB
  was not resolved — flagged above as the main open item for that
  candidate.

## Informs

A future `.planning/decisions/` ADR on whether to swap the display panel
(user's call), and if so, a follow-up hardware bead to update the
enclosure cutout/bezel and PCB FPC connector footprint (or, for the
Waveshare candidate, the connector/mounting approach) for whichever
candidate is chosen — out of scope for this research-only bead.

Sources:
- https://files.waveshare.com/wiki/common/ST7789VW.pdf (Waveshare Pico-LCD-1.3's controller datasheet — no panel-level contrast spec)
- https://www.waveshare.com/pico-lcd-1.3.htm (product page, no contrast spec listed)
- https://www.waveshare.com/product/displays/lcd-oled/1.9inch-touch-lcd.htm (Waveshare SKU 31122, "1.9inch Touch LCD," 170x320 ST7789V2 IPS, Contrast Ratio 900:1, Brightness 500 cd/m², confirmed live 2026-11-15)
- https://docs.waveshare.com/ESP32-S3-LCD-1.9 (Waveshare ESP32-S3-LCD-1.9 docs, same panel/spec table, confirms 900:1 contrast, 2026-11-15)
- https://www.waveshare.com/1.9inch-lcd-module.htm (Waveshare SKU 23822, non-touch sibling, same 170x320 ST7789V2 panel, 4-wire SPI, no contrast figure restated on this page)
- https://www.buydisplay.com/full-viewing-angle-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789 (ER-TFT019-1, 1.9" 170x320 ST7789 IPS, Contrast Ratio Typ 500:1, Sunlight Readable: No — current live URL, replaces a dead link in the earlier draft)
- https://www.digikey.dk/en/htmldatasheets/production/8030461/0/0/1/afl240240a0-1-3intm-ano (Orient Display AFL240240A0-1.3INTM-ANO, 1.3" 240x240 IPS, contrast ratio 500:1 at θ=0° — weakly verified, see finding 1)
- https://cdn.shopify.com/s/files/1/0264/7629/files/DM-TFT24-383_Datasheet.pdf (DM-TFT24-383, 2.4" 240X320 TRANSFLECTIVE, Contrast Ratio typ 300 — flagged as a transflective part, not a fair transmissive calibration point)
- https://newhavendisplay.com/content/specs/NHD-2.4-240320AF-CSXP.pdf (finding 3: 2.4" 240x320 IPS, ST7789VI, contrast ratio min 800 / typ 1500:1, 1200 cd/m²)
- https://www.digikey.com/en/products/detail/newhaven-display-intl/NHD-2-4-240320AF-CSXP/22204988 and https://www.digikey.de/en/products/detail/newhaven-display-intl/NHD-2-4-240320AF-CSXP/22204988 (DigiKey part 22204988, **7 units in stock, 18-week lead time**, confirmed live on both regional sites 2026-11-15 — corrects an earlier wrong "191 units" figure)
- https://support.newhavendisplay.com/hc/en-us/articles/32880668716695-06-17-25-NHD-2-4-240320AF-CSXP and https://support.newhavendisplay.com/hc/en-us/community/posts/31645774884503-NHD-2-4-240320AF-CSXP-4-Wire-SPI (Newhaven engineering change notice and support post: Rev2B adds 4-wire SPI support; Rev2A is 3-wire SPI only)
- https://newhavendisplay.com/content/docs/2.4IPS-CSXP_TransitionGuide.pdf (Newhaven's own CF-series-to-AF-series/IPS transition guide — basis for the VA/MVA finding in finding 6)
- https://www.mouser.lt/pdfDocs/NHD-24-240320CF-BSXV-F.pdf and DigiKey part 11476257 (NHD-2.4-240320CF-BSXV-F, the older MVA/TN part, contrast ratio min 150 / typ 200:1 — previously marked "not found," now sourced)
- https://www.mouser.lt/datasheet/2/127/TFT020-23AI-1594147.pdf and https://www.lcd-module.com/fileadmin/eng/pdf/grafik/TFT020-23AI.pdf (Display Visions TFT020-23AI/EA-TFT020-23AI family datasheet, 2.0" 240x320 ST7789V, contrast ratio min 640 / typ 800:1)
- https://www.digikey.com/en/products/detail/display-visions/EA-TFT020-23AITC/10712688 (DigiKey part 10712688 / 1481-EATFT020-23AITC-ND, the **touch** sibling EA-TFT020-23AITC, confirmed live In-Stock: 20, 2026-11-15 — not the non-touch part being recommended)
- https://uk.rs-online.com/web/p/lcd-colour-displays/2211845 (RS 221-1845, the non-touch EA-TFT020-23AINN — stock inconsistent across regional snapshots, could not get an authoritative live read in this pass)
- https://shop.lcd-module.com/2.0-240x320-IPS/TFT020-23AINN (EA-TFT020-23AINN non-touch, direct store listing)
- https://www.orientdisplay.com/pdf/AFY240320A0-2.4INTH.pdf (Orient Display AFY240320A0-2.4INTH Rev B, 2.4" 240x320 IPS, contrast ratio ~500-750 range, luminance 800-1000 cd/m²)
- https://lcsc.com/product-detail/LCD-Screen_Orient-Display-AFY240320A0-2-4INTH-R_C20578695.html (LCSC C20578695, 0 units on-hand at check time 2026-11-15)
- https://www.orientdisplay.com/?p=324361 (AFY240320A0-2.4INTH-C product page, confirms ST7789V driver for this family)
- https://www.displaymodule.com/products/2-inch-tft-display-240x320-transflective-resistive-with-spi-mcu-rgb and https://cdn.shopify.com/s/files/1/0264/7629/files/DM-TFT20-436_Datasheet.pdf (DM-TFT20-436, 2.0" 240x320 transflective, ST7789 driver, contrast ratio typ 250:1 — sources the previously-unsourced "transflective 250:1" claim; a "min 200:1" figure exists but belongs to sibling part DM-TFT20-435, not this one)
- docs/plans/2026-11-13-custom-hardware-design.md (project's already-chosen 1.9" ST7789V 320x170 baseline)
