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
LCD-vs-LCD only.)

## Findings

### 1. Why cheap ST7789 hobby panels look "washed out" — baseline contrast, confirmed from real datasheets

Waveshare does not publish a panel-level (LCM) optical datasheet for the
Pico-LCD-1.3 — only the ST7789VW **controller** datasheet
(`files.waveshare.com/wiki/common/ST7789VW.pdf`, Sitronix), which documents
electrical/timing characteristics of the driver chip, not the physical
panel's contrast ratio or luminance. Contrast ratio is a property of the
LC cell + backlight + polarizers, not the driver IC, so it's simply not in
that document — and the Waveshare wiki/product page for Pico-LCD-1.3 lists
no contrast spec anywhere. Same situation for the chosen 1.9" ST7789V
320x170 baseline: no public LCM-level datasheet with a contrast number has
been found for the specific panel in the current design doc.

To get a real number, I pulled datasheets for closely comparable modules —
same panel class/resolution, same driver family, hobby/distributor-grade —
and the contrast ratios cluster in a narrow, confirmable band:

- **Same size/resolution as the project's new 1.9" baseline:** BuyDisplay
  ER-TFT019-1, 1.9" IPS, 170x320, ST7789 — datasheet states **Contrast
  Ratio (Typ) 500:1**, **Sunlight Readable: No**
  (buydisplay.com/any-angle-viewing-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789).
- **Same resolution as the old 1.3" Waveshare panel:** Orient Display
  AFL240240A0-1.3INTM-ANO, 1.3" IPS, 240x240, ST7789-family —
  datasheet states **contrast ratio 500:1 at θ=0°**
  (digikey.dk/en/htmldatasheets/production/8030461/0/0/1/afl240240a0-1-3intm-ano).
- **Low end of this market, for calibration:** DM-TFT24-383 (generic 2.4"
  hobby module) datasheet lists **Contrast Ratio (typ) 300**
  (cdn.shopify.com/.../DM-TFT24-383_Datasheet.pdf) — this is the exact
  number the bead's "~300:1 anecdote" was hedging on, and it is real for at
  least one commodity panel, just not necessarily *this* project's specific
  parts.

So: the project's actual baseline panels most plausibly sit around
**~500:1**, with some commodity panels in this market as low as 300:1 — not
a documented spec for the exact Waveshare/current part, but a real,
sourced range for the class of panel it belongs to. 500:1 (and definitely
300:1) is mediocre by LCD standards — plenty of "high brightness/sunlight
readable" IPS modules in the same size/driver class document 2-3x that,
which is the open door this research chases.

### 2. Primary recommendation: Newhaven NHD-2.4-240320AF-CSXP (and siblings)

- **Part number:** NHD-2.4-240320AF-CSXP (non-touch); same family covers
  -CTP (capacitive touch) and -T (resistive touch) suffixed siblings.
- **Size / resolution:** 2.4", 240x320.
- **Driver IC:** ST7789VI — same driver family as the project's ST7789V/
  ST7789VW baseline (Sitronix ST7789 family share a near-identical command
  set; expect at most minor init-sequence tuning, not a rewrite).
- **Interface:** 3-wire SPI, or 8/16-bit 8080-II parallel — SPI usable
  as-is.
- **Contrast ratio:** datasheet states **contrast ratio min 800 / typ
  1500:1** (newhavendisplay.com/content/specs/NHD-2.4-240320AF-CSXP.pdf).
  That's 2-3x the baseline's documented ~500:1, and 5x the 300:1 low end.
- **Luminance:** 1200 cd/m² typ, described as "High Brightness/Sunlight
  Readable," normally-black, anti-glare, transmissive.
- **Stock:** DigiKey part **22204988** (NHD-2.4-240320AF-CSXP) — confirmed
  live, **191 units in stock** on DigiKey's Germany storefront (checked
  2026-11-15); listed Active across DigiKey's regional sites. One regional
  page separately shows an ~18-week manufacturer lead time for restock
  beyond on-hand quantity — fine for prototyping, but a production-volume
  buy should get a quote from Newhaven/DigiKey first rather than assuming
  the 191 on-hand figure scales.
- **Tradeoff:** physically bigger than the current 1.3"/1.9" panels (2.4"
  vs 1.9" diagonal) — this means an enclosure cutout/bezel rework, which is
  explicitly out of scope for this research-only bead. If this candidate is
  chosen, that's a new hardware bead.

### 3. Closer-size, same-driver, more modest improvement: Display Visions EA-TFT020-23AINN

- **Part number:** EA-TFT020-23AINN (non-touch); touch sibling EA-TFT020-23AITC.
- **Size / resolution:** 2.0", 240x320.
- **Driver IC:** ST7789V — the *exact* driver already used in the chosen
  baseline, zero firmware-driver change at all.
- **Interface:** SPI or RGB.
- **Contrast ratio:** datasheet (TFT020-23AI, hosted at
  mouser.lt/datasheet/2/127/TFT020-23AI-1594147.pdf) states **contrast
  ratio min 640 / typ 800:1**.
- **Stock:** touch sibling EA-TFT020-23AITC confirmed live at DigiKey, part
  10712688 (~20 units in stock, checked via search 2026-11-15); non-touch
  EA-TFT020-23AINN listed at RS Components (stock no. 221-1845) and
  directly orderable from lcd-module.com's shop.
- **Tradeoff:** ~1.6x the baseline's documented contrast — a real,
  meaningfully-better number, but well short of the Newhaven candidate's
  1500:1. In exchange, it's much closer to the current 1.9"/2.0" form
  factor (smaller enclosure delta than the 2.4" option) and needs no
  driver change whatsoever.

### 4. LCSC/JLCPCB-native option, weaker — flagged honestly rather than oversold

- **Part number:** Orient Display AFY240320A0-2.4INTH-R.
- **Size / resolution:** 2.4", 240x320, IPS, ST7789V-family driver (the
  `-C` touch sibling's product page confirms ST7789V for this family).
- **Contrast ratio:** Rev B datasheet (orientdisplay.com/pdf/
  AFY240320A0-2.4INTH.pdf) gives a contrast ratio in roughly the **500-750**
  range at θ=0°, with luminance 800-1000 cd/m² — only a modest, uncertain
  improvement over the ~500:1 baseline, not clearly better than the
  Display Visions option above.
- **Stock:** real part number with a real LCSC listing (LCSC **C20578695**)
  and a real DigiKey listing (2544-AFY240320A0-2.4INTH-R-ND, Active) — but
  the LCSC page showed **0 units on-hand** at check time (2026-11-15). This
  is the most "LCSC/JLCPCB-native" of the candidates researched (relevant
  if a future bead wants automated SMT assembly sourcing specifically
  through LCSC/JLCPCB rather than DigiKey), but given the weak contrast
  number and unconfirmed current stock, it's not recommended as a primary
  choice right now.

### 5. VA and transflective: checked, not recommended

The bead asked to evaluate VA and transflective panels, not just IPS,
seriously. Direct findings:

- Newhaven's own **product transition guide**
  (newhavendisplay.com/content/docs/2.4IPS-CSXP_TransitionGuide.pdf) groups
  their older CF-series 2.4" modules (which includes a TN/MVA-class part,
  NHD-2.4-240320CF-BSXV-F) as the line being **phased out in favor of the
  newer IPS AF-series** (the family candidate #2 above belongs to) for this
  exact panel class. That's a maker explicitly moving away from VA/MVA
  toward high-brightness IPS + anti-glare treatment as the better answer to
  "contrast/sunlight readability" in this size/driver segment — not
  researcher bias, their own roadmap.
- No VA/MVA candidate was found that beats the IPS options above on
  documented contrast ratio with confirmed live distributor stock. The one
  VA-adjacent part checked in detail (NHD-2.4-240320CF-BSXV-F) had an
  unreliable/typo'd contrast figure in distributor listings and no clean
  datasheet contrast number recoverable.
- Transflective panels (which add a reflective layer for no-backlight
  outdoor readability) were checked incidentally: the one transflective
  2.0" ST7789 module surfaced during this research documented **250:1
  contrast** — *worse* than the IPS baseline, not better. Transflective
  trades contrast for sunlight legibility without backlight power; since
  this device isn't primarily an outdoors/no-backlight use case, that
  tradeoff doesn't fit the stated priority (contrast first).

## Recommendation

Two real, datasheet-backed, live-stocked candidates, both ST7789-family
(no firmware driver rewrite):

- **If maximizing contrast matters most and a larger panel/enclosure
  rework is acceptable:** Newhaven **NHD-2.4-240320AF-CSXP** — 1500:1 typ /
  800:1 min documented contrast (2.4", ST7789VI, DigiKey part 22204988,
  191 units confirmed in stock 2026-11-15). This is the clearest, best-
  documented contrast win found.
- **If minimizing physical/enclosure change matters more than squeezing
  out the absolute best contrast number:** Display Visions
  **EA-TFT020-23AINN** — 800:1 typ / 640:1 min documented contrast (2.0",
  exact same ST7789V driver already in use, DigiKey/RS Components stock
  confirmed). Real, meaningful (~1.6x) improvement with the lowest
  integration risk of the three candidates.

The Orient Display LCSC-native option (#4) is included for completeness
but not recommended as a first pick — its contrast improvement over
baseline is marginal and its live LCSC stock wasn't confirmed at check
time.

This is research only; the user makes the actual call (panel size vs.
contrast tradeoff, enclosure rework cost) — no `.planning/decisions/` ADR
was written by this bead, per its acceptance criteria.

## Verification performed vs. not performed

- **Performed:** Live WebSearch/WebFetch lookups against manufacturer
  datasheets (Newhaven, Display Visions/EA, Orient Display, BuyDisplay)
  and distributor listings (DigiKey, Mouser, LCSC, RS Components) on
  2026-11-15, cross-checking driver IC, resolution, contrast ratio, and
  luminance figures against the primary-source datasheet text wherever a
  readable (non-image-compressed) PDF or HTML datasheet rendering was
  available.
- **Not performed / caveats:** Several Orient Display and Newhaven PDFs
  are image/vector-heavy and could not be text-extracted directly in this
  environment (no PDF-text tooling available locally); those contrast
  figures were instead corroborated via search-engine text extraction of
  the same documents, which is a weaker form of verification than a direct
  read — flagged inline above wherever this applies (the Orient Display
  "~500-750" range in particular). Distributor stock counts are point-in-
  time reads (2026-11-15), not API-confirmed or screenshot-verified, same
  standard caveat this repo already applies to other sourcing findings
  (see `.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md`).
  No physical panel was obtained or bench-tested — this is desk research
  only, as the bead scoped it.

## Informs

A future `.planning/decisions/` ADR on whether to swap the display panel
(user's call), and if so, a follow-up hardware bead to update the
enclosure cutout/bezel and PCB FPC connector footprint for whichever
candidate is chosen — out of scope for this research-only bead.

Sources:
- https://files.waveshare.com/wiki/common/ST7789VW.pdf (Waveshare Pico-LCD-1.3's controller datasheet — no panel-level contrast spec)
- https://www.waveshare.com/pico-lcd-1.3.htm (product page, no contrast spec listed)
- https://www.buydisplay.com/any-angle-viewing-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789 (ER-TFT019-1, 1.9" 170x320 ST7789 IPS, Contrast Ratio Typ 500:1, Sunlight Readable: No)
- https://www.digikey.dk/en/htmldatasheets/production/8030461/0/0/1/afl240240a0-1-3intm-ano (Orient Display AFL240240A0-1.3INTM-ANO, 1.3" 240x240 IPS, contrast ratio 500:1 at θ=0°)
- https://cdn.shopify.com/s/files/1/0264/7629/files/DM-TFT24-383_Datasheet.pdf (DM-TFT24-383, Contrast Ratio typ 300, calibration point for the "~300:1 hobby tier" anecdote)
- https://newhavendisplay.com/content/specs/NHD-2.4-240320AF-CSXP.pdf (primary recommendation: 2.4" 240x320 IPS, ST7789VI, contrast ratio min 800 / typ 1500:1, 1200 cd/m²)
- https://www.digikey.de/en/products/detail/newhaven-display-intl/NHD-2-4-240320AF-CSXP/22204988 (DigiKey part 22204988, 191 units in stock, checked 2026-11-15)
- https://newhavendisplay.com/content/docs/2.4IPS-CSXP_TransitionGuide.pdf (Newhaven's own CF-series-to-AF-series/IPS transition guide — basis for the VA/MVA finding in section 5)
- https://www.mouser.lt/datasheet/2/127/TFT020-23AI-1594147.pdf (Display Visions TFT020-23AI/EA-TFT020-23AI family datasheet, 2.0" 240x320 ST7789V, contrast ratio min 640 / typ 800:1)
- https://shop.lcd-module.com/2.0-240x320-IPS/TFT020-23AINN (EA-TFT020-23AINN non-touch, direct store listing)
- https://shop.lcd-module.com/2.0-240x320-IPS/TFT020-23AITC and DigiKey part 10712688 (touch sibling, confirmed live DigiKey stock)
- https://www.orientdisplay.com/pdf/AFY240320A0-2.4INTH.pdf (Orient Display AFY240320A0-2.4INTH Rev B, 2.4" 240x320 IPS, contrast ratio ~500-750 range, luminance 800-1000 cd/m²)
- https://lcsc.com/product-detail/LCD-Screen_Orient-Display-AFY240320A0-2-4INTH-R_C20578695.html (LCSC C20578695, 0 units on-hand at check time 2026-11-15)
- https://www.orientdisplay.com/?p=324361 (AFY240320A0-2.4INTH-C product page, confirms ST7789V driver for this family)
- docs/plans/2026-11-13-custom-hardware-design.md (project's already-chosen 1.9" ST7789V 320x170 baseline)
