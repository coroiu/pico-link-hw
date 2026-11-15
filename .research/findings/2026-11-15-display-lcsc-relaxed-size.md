# Best LCSC-stocked display panel, with the height>=240px constraint relaxed

## Question

Follow-up to `pilink-rub`
(`.research/findings/2026-11-15-display-sustainable-stock.md`), whose two
LCSC-native candidates at height>=240px (Orient Display
AFY240320A0-2.4INTH-R, 4D Systems 4DLCD-24320240-IPS) are now confirmed
out of stock or thin on LCSC specifically. The user has said they are
willing to relax the height>=240px constraint entirely and accept the
project's original 170px-height baseline — or any other size — if doing so
gets a genuinely LCSC-native, well-stocked part: buying the display through
the same LCSC order/shipment as the PCB's other components matters enough
to trade back vertical resolution for it.

This bead searches LCSC's own catalog and search engine directly and
broadly, with the height/aspect constraint fully open (1.8"-3", square or
rectangular both acceptable), for ST7789/ST7789V2/ILI9341/ILI9342-family
SPI TFT panels with: (1) a real, currently-in-stock LCSC listing (hundreds+
ideally, flag anything under 50 as risky), (2) a contrast ratio with a
cited primary source (not inferred from the driver IC alone — a mistake
this research chain corrected early on, see `pilink-4mq` finding 5), (3)
a bare panel + FPC connector matching the project's integration pattern
where possible (breakout modules acceptable if nothing bare-panel-shaped
is found, flagged as such). It also specifically checks whether the
project's own already-chosen 320x170/170x320 baseline size has any real
LCSC-stocked instance from any vendor — a question no prior round has
directly answered (only the Xinli and Waveshare parts were checked at this
size, and neither has an LCSC listing).

Baseline facts inherited from the four prior rounds (`pilink-maj`,
`pilink-4mq`, `pilink-ujh`, `pilink-rub`), not re-derived here: contrast
ratio is a property of the LC cell/polarizer/backlight stack, not the
driver IC (`pilink-4mq` finding 5); the MADCTL/MV row-column-exchange bit
lets any ST7789/ILI9341-family panel be mounted rotated 90 degrees without
a new part; established contrast baselines are ~500:1 (general bare-panel
floor), ~900:1 (best confirmed at 170px height: Xinli TCXD019IBLON-78 and
the Waveshare 1.9" ST7789V2 module, neither with an LCSC listing), and
~800:1 (best confirmed at 240px height with real-but-thin LCSC presence:
Orient AFY240320A0-2.4INTH-R and 4D Systems 4DLCD-24320240-IPS); every
part number already checked across all four rounds (Xinli
TCXD019IBLON-78, Waveshare 1.9" module SKU 23822/31122, Newhaven
NHD-2.4-240320AF-CSXP, Display Visions EA-TFT020-23AINN, Orient Display
AFY240320A0-2.4INTH-R, 4D Systems 4DLCD-24320240-IPS, Crystalfontz
CFAF240320A0-024SN, DisplayModule DM-TFT30-407, Tailor Pixels
TTH019BVS-01) is not re-checked here except where this pass's LCSC-specific
search surfaced new information about it.

## Findings

### 1. LCSC's own buy-box (stock/price) cannot be read by direct fetch in this environment — same limitation every prior round hit, re-confirmed here

Every direct `WebFetch` of an `lcsc.com` product-detail page in this pass
returned the static spec-table fields (MPN, driver IC, resolution,
category, datasheet URL) but never the dynamic stock-quantity/price
widget — consistent with `pilink-rub`'s identical finding. A same-origin
API probe (`lcsc.com/api/products/detail`) and an alternate regional mirror
(`fat.lcsc.com`) were both blocked by this environment's own access
controls before a request could even be attempted; a Jina-reader proxy
fetch of the same URLs returned only the page's datasheet-adjacent content,
not the buy-box either. **This pass's live stock checks are therefore,
like every prior round's, built from WebSearch-indexed snapshots of the
rendered page** (Google/Bing's crawler executes the page's JS, which this
environment's own fetch tooling cannot), cross-checked across multiple
independent snapshots per part to separate a stable number from a stale
or conflicting one, exactly as `pilink-rub` did for the Newhaven/Orient/EA/
4D Systems parts. This is disclosed plainly as the verification method,
not asserted as better than it is.

### 2. Best LCSC stock-depth find this pass: LCKFB-st7789-2.0inch-screen (LCSC C53184555) — ~1,500-1,600 units, but contrast and even resolution/driver are unconfirmed on LCSC's own listing

- **Part number / brand:** `LCKFB-st7789-2.0inch-screen`, LCSC Part #
  **C53184555**, manufacturer listed as **"LCSC-boards"** — this is LCSC's
  own in-house development-board brand (LCKFB, "立创开发板"), not a
  third-party panel maker's part sold through LCSC's catalog. Category:
  Development Boards, Kits, Programmers / Evaluation Boards.
- **Resolution / driver — not confirmed on LCSC's own page:** LCSC's own
  spec table for this exact listing, read directly via WebFetch today
  (2026-11-15) and independently via the Chinese-language sister site
  `item.szlcsc.com/56199684.html`, states **no resolution and no driver
  IC** — the `item.szlcsc.com` page's own parameter table literally reads
  "参数完善中" ("parameters being completed"). The 240x320 / ST7789V2 figures
  commonly associated with this board come only from a third-party source:
  LCKFB's own wiki page for the matching "ColorEasyDuino" kit
  (`wiki.lckfb.com/en/coloreasyduino/module/screen/2-0-color-screen.html`,
  also mirrored at `openkits-wiki.easyeda.com`), which states Driver Chip
  ST7789V2, Resolution 240(H) x 320(V) RGB, module dimensions 36 x 63.2mm —
  but that wiki page is not itself an electro-optical datasheet and carries
  at least one internal inconsistency already flagged by a WebSearch
  extract (a code comment reading "240x280" next to a `tft.init(240, 320)`
  call), so treat the 240x320/ST7789V2 identification as **probable but
  not LCSC-confirmed**, not as settled.
- **Touch:** the `item.szlcsc.com` page explicitly describes this exact
  listing as "带触摸" (with touch) — a detail the LCKFB wiki's English page
  for the same nominal "2-inch" screen does not mention, a further sign
  this LCSC listing and the wiki's board description may not be perfectly
  the same hardware revision.
- **Contrast ratio: not found anywhere.** No contrast figure exists on
  LCSC's own listing, on `item.szlcsc.com`, or on either LCKFB wiki page
  checked. Per this research chain's own standard (do not infer contrast
  from the driver IC alone), **this candidate's contrast is honestly
  unknown, not assumed to tie the 900:1 Waveshare/Xinli figure just
  because a third-party source says "ST7789V2."**
- **Interface / form factor:** sold as an assembled development board
  (breakout PCB with connector), not a bare FPC panel — the same
  integration-pattern mismatch flagged for the Waveshare 170-height module
  in `pilink-maj`/`pilink-4mq`.
- **Stock — the strongest LCSC-specific number found in this entire
  five-round research chain:** two independent WebSearch-indexed snapshots
  of this exact LCSC listing, taken at different crawl times, show **1,588
  units** and **1,591 units** respectively — a near-exact agreement between
  snapshots (unlike the declining-trend pattern seen for other parts below),
  consistent with a part that is being actively restocked rather than sold
  down to zero. Reference price **$7.6682** at qty 1, packaging "Bag,"
  minimum order 1.
- **Net:** this is the one candidate in this pass that cleanly clears the
  bead's "hundreds+ units, healthy" stock bar on LCSC itself — but it comes
  with two real, disclosed gaps: no confirmed contrast figure from any
  primary source, and no LCSC-confirmed resolution/driver IC (only a
  third-party wiki's claim). It is a breakout module, not a bare panel.

### 3. Real contrast citation, exact driver match, but too small for this bead's stated size range: Wisevision N114-2413THBIG01-H13 (LCSC C2890618)

- **Part number:** N114-2413THBIG01-H13 (also seen under the alias brands
  "Shenzhen Allvision Tech" and "Newvisio" across different LCSC page
  snapshots/mirrors — same LCSC Part # C2890618 in every case).
- **Size / resolution:** **1.14"**, **240x135** dot pixels — confirmed
  directly from LCSC's own official spec table (read via direct WebFetch
  today, 2026-11-15): "Size: 1.14," "Resolution (dot pixels): 240x135."
- **Driver IC:** **ST7789V** — confirmed directly on LCSC's own spec table
  as "Controller Type: ST7789V." This is the exact plain driver already
  planned for this project, the same confidence level as the Xinli and
  EA-TFT020-23AINN exact-driver matches in prior rounds.
- **Interface:** SPI, confirmed on LCSC's own page.
- **Contrast ratio: 640 min / 800 typ**, per its own manufacturer datasheet
  (Shenzhen Allvision Tech, Rev A, dated 2020-05-08) — found via a
  WebSearch-indexed excerpt of the actual datasheet PDF
  (`fatwmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2109031030_Shenzhen-Allvision-Tech-N114-2413THBIG01-H13_C2890618.pdf`),
  not a distributor guess. Two direct-fetch attempts on this exact PDF (the
  CloudFront-style mirror URL and LCSC's own `lcsc.com/datasheet/...pdf`
  mirror) both failed to return document text in this environment — the
  same recurring PDF-tooling gap this entire research chain has hit
  repeatedly — so this figure sits at the "search-indexed excerpt of a
  genuine primary datasheet" confidence tier (the same tier `pilink-rub`
  used for the 4D Systems LCSC price-ladder signal), not an independently
  re-verified direct read. It ties the EA-TFT020-23AINN figure from prior
  rounds and clears the ~500:1 general baseline comfortably.
- **Stock:** four independent WebSearch-indexed snapshots of this LCSC
  listing disagree on the exact figure but all show real, nonzero stock:
  **320 units** (one snapshot, "Standard Packaging: 48"), **84 units**,
  **65 units**, and **60 units** across the others. Reference price from
  ~$2.53 to ~$2.77 at qty 1. This is a real, apparently-recurring LCSC
  listing, not a one-off dead reel — but the spread (320 down to 60 across
  snapshots) means it should be treated as "tens to low hundreds," not
  confidently "hundreds+," until checked live at order time.
- **Why this isn't recommended despite the clean driver/contrast match:**
  this bead's own framing asks for "1.8"-3", square or rectangular" — this
  part is 1.14", well under that floor, and its 135px dimension is smaller
  than even the 170px-height fallback the user said they'd accept. It is
  reported here because it is a genuine, LCSC-confirmed, well-sourced find
  with the best contrast/driver evidence of anything found in this pass —
  but it does not fit the size the bead asked for, and that is stated
  plainly rather than stretched.

### 4. Real, LCSC-native, but weak-contrast and declining stock: HS280S030RX (LCSC C5329584)

- **Part number:** HS280S030RX, manufacturer "HS" (a generic Asian-brands
  LCM house on LCSC, distinct from Newhaven/Display Visions/4D Systems).
- **Size / resolution:** 2.8", 320x240 — confirmed on LCSC's own spec
  table via direct WebFetch today.
- **Driver IC:** listed as **ST7789** on LCSC's spec table, but the actual
  datasheet PDF (read via a Jina-reader proxy fetch after direct WebFetch
  returned only the page title) names the controller as **ST7789T3**
  specifically, while its own sample init code elsewhere references
  ST7789V — an internally inconsistent document, flagged rather than
  resolved.
- **Contrast ratio: min 280 / typ 300**, read directly from the datasheet
  via the same Jina-reader proxy fetch (test method: BM-7A luminance meter,
  center-point measurement). **This is below the ~500:1 general baseline**
  this research chain established in `pilink-maj` — a real number, not a
  distributor guess, but a weak one.
- **Stock — declining across snapshots, not merely noisy:** five
  WebSearch-indexed snapshots of this listing, apparently from different
  crawl dates, show **463 -> 198 -> 92 (split across regional warehouses,
  with 0 in two of three) -> 32 -> 15** units in a roughly monotonic
  downward sequence. Unlike the LCKFB board's near-matching repeat
  snapshots (finding 2) or the N114 part's noisy-but-real-each-time
  snapshots (finding 3), this pattern reads as **stock being sold down
  without restocking**, not just differently-timed consistent reads — a
  meaningfully weaker sustainability signal even though every individual
  snapshot shows real, nonzero stock.
- **Net:** a genuine LCSC-native ST7789-family panel, but both axes this
  bead cares about (contrast, sustained stock) are weak. Not recommended.

### 5. Checked and ruled out: HS32B01A (LCSC C19632786)

3.2", 320x240, listed as "ST7789" on LCSC's spec table and sold as "SPI" —
but its actual datasheet (read via Jina-reader proxy after direct fetch
returned only the title) tells a different story on every axis that
matters for this project: **contrast ratio is literally "TBD"** in the
datasheet's own electro-optical table (no min/typ figure is published at
all); the datasheet's own Features table names ST7789 but **Section 10.3
instead refers to the ILI9341 technical manual for commands** — an
internally contradictory document, not a confirmed driver; and the
**interface is a 24-pin, 16-bit parallel data bus** (DB0-DB15), not the
4-wire SPI the project's firmware uses, despite LCSC's own listing labeling
it "SPI." Stock is also thin (9-10 units across two snapshots). **Not
recommended on any axis** — flagged here so a future pass doesn't repeat
this exact dead end.

### 6. Checked and ruled out: Displaytech DT028ATFT-TS (LCSC C20510378)

2.8", 320x240, **ILI9341**-family driver (Ilitek ILI9341 or compatible, per
LCSC's own spec table and corroborated by RS Components/Datasheets.com
listings of the same part). Contrast ratio **500:1** at 200 cd/m2,
confirmed via RS Online and Datasheets.com listings of this exact part
(not independently re-fetched from Displaytech's own PDF in this pass) —
this exactly ties, not beats, the ~500:1 general baseline. Its LCSC listing
shows a reference price near **$81/unit at qty 1** in the one snapshot
found, with no stock quantity ever appearing in any snapshot checked —
a price at that level with no visible stock figure is consistent with a
non-stocked "request a quote" style listing rather than a genuinely
on-the-shelf part. **Not recommended** — ties, not beats, the baseline on
contrast, and stock could not be confirmed as real at any level.

### 7. Newhaven's own documented-high-contrast AF-series does appear on LCSC under several part numbers, but every variant checked is confirmed Out of Stock there

Newhaven's AF-series IPS panels are the family already carrying this
research chain's best-documented contrast figures (NHD-2.4-240320AF-CSXP:
800 min/1500 typ, `pilink-maj` finding 3). This pass found that Newhaven
sells several AF-series and related parts directly through LCSC's own
catalog — a new fact this round surfaced, not previously checked — but
every one checked is out of stock there specifically:

- **NHD-2.8-240320AF-CSXP-FT** (LCSC C17684343, ST7789Vi, 320x240,
  parallel 8/16-bit RGB interface, *not* SPI): LCSC listing confirmed **Out
  of Stock** (stock-notification button in place of Add to Cart), $86.84/
  unit reference price at qty 1 in the one snapshot found. JLCPCB's mirror
  of the same LCSC part independently shows 0 units too.
- **NHD-2.8-240320AF-CSXP-F** (LCSC C17340756, the non-touch sibling, same
  AF-series/ST7789Vi family): also confirmed **Out of Stock** on LCSC in
  this pass's snapshot, while DigiKey and Octopart list the same MPN as
  "Active"/"in production" with a 16-18 week manufacturer lead time —
  the same "real part, real distributor presence elsewhere, empty on LCSC
  specifically" pattern `pilink-rub` already established for the Orient
  Display and plain Newhaven NHD-2.4-240320AF-CSXP parts.
- **NHD-2.4-240320CF-CTXI#-F / -FT and -CSXN-F/-FT** (various LCSC C-numbers
  found): these are Newhaven's older **CF-series**, which `pilink-maj`
  finding 6 already established Newhaven is phasing out in favor of the
  AF-series specifically because of its lower contrast (CF-series sibling
  NHD-2.4-240320CF-BSXV-F: 150 min/200 typ) — not re-checked individually
  for contrast here since the family's weakness is already established,
  but worth noting several CF-series LCSC listings also show Out of Stock
  or no-stock-figure snapshots.
- **DLC Display DLC0240AWM04CB-1** (LCSC C17224827, 2.4", 320x240,
  ST7789V confirmed on LCSC's own spec table): also confirmed **Out of
  Stock** on LCSC in this pass, $39.04/unit reference price at qty 1,
  sold in boxes of 480. Its sibling DLC0240AAM06CB-2 (C17630459) is
  likewise Out of Stock.

**Net pattern, now confirmed across five research rounds and a widened
LCSC-specific search in this one:** every bare-panel ST7789/ILI9341-family
part with a *good, documented* contrast figure that this chain has found
anywhere (Newhaven AF-series, DLC Display, Orient Display, 4D Systems) is
either absent from LCSC entirely or present on LCSC and confirmed out of
stock there. The only LCSC listings with confirmed healthy stock in this
entire chain — the LCKFB board (finding 2) and, at a smaller scale, the
N114 1.14" part (finding 3) and the declining-but-real HS280S030RX
(finding 4) — are exactly the ones without a strong documented contrast
figure, or (HS280S030RX) with a weak one. No candidate in this chain
clears both bars on LCSC specifically.

### 8. The project's own 320x170/170x320 baseline: no real LCSC listing found at any size, from any vendor — question now directly answered, not just carried forward

This bead's acceptance criteria specifically asked whether the project's
own already-chosen 320x170 size has any real LCSC-stocked instance — a
question `pilink-maj`/`pilink-4mq` raised but never resolved (they only
checked Xinli and Waveshare at this size, neither LCSC-listed). This pass
ran multiple fresh, differently-worded searches targeting this exact
resolution directly against LCSC (`"170x320"` and `"320x170"` combined with
`ST7789`/`ST7789V2`, a `site:lcsc.com` search, and a dedicated LCKFB-wiki
check for the matching "1.9-inch Color Screen" kit page). **Result: no
LCSC product-detail page for a 170x320 or 320x170 panel was found by any
search in this pass.** The LCKFB wiki does document a matching "1.9-Inch
Color Screen" (170x320, driver chip listed as **ST7789V3**) as part of the
same ColorEasyDuino kit family as the C53184555 board in finding 2 — but
unlike the 2.0" screen, **no LCSC C-number was found for it anywhere**;
the wiki's own purchase link points to Taobao, not LCSC's catalog. This is
now a directly-answered negative, not an inference: **the project's exact
170px-height baseline resolution has no confirmed LCSC-native source from
any vendor**, Chinese-market generic LCM houses included.

## Comparison table

| Candidate | Size / resolution | Driver | Contrast (cited) | LCSC stock (point-in-time, this pass) | Bare panel or module | Fits this bead's size ask? |
|---|---|---|---|---|---|---|
| **LCKFB-st7789-2.0inch-screen (C53184555)** | 2.0", 240x320 (third-party-wiki claim, not LCSC-confirmed) | ST7789V2 (same caveat) | **Not found anywhere** | **~1,588-1,591 units** (2 consistent snapshots) — best in this whole 5-round chain | Breakout module | Yes (1.8-3" range) |
| Wisevision N114-2413THBIG01-H13 (C2890618) | **1.14"**, 240x135 | ST7789V (LCSC-confirmed) | **640 min/800 typ** (own datasheet, search-indexed) | 320 / 84 / 65 / 60 units across snapshots (noisy, real) | Module (small) | **No — below 1.8" floor and 170px height floor** |
| HS280S030RX (C5329584) | 2.8", 320x240 | ST7789 / ST7789T3 (datasheet-inconsistent) | **280 min/300 typ** — below general baseline | 463->198->92->32->15, declining | Module | Yes, but weak on both axes |
| HS32B01A (C19632786) | 3.2", 320x240 | Conflicting (ST7789 features table vs. ILI9341 command refs); **16-bit parallel, not SPI** | **TBD — not published** | 9-10 units | Module | No — wrong interface, no contrast |
| DT028ATFT-TS (C20510378) | 2.8", 320x240 | ILI9341 | 500:1 (ties baseline) | Unconfirmed; one snapshot ~$81/unit, no stock figure ever seen | Module | Ties baseline only |
| Newhaven AF-series on LCSC (C17684343, C17340756) | 2.8", 320x240 | ST7789Vi | 600 min/800 typ (sibling FCTP datasheet) | **Confirmed Out of Stock** on LCSC | Module, parallel RGB interface | Best contrast, zero LCSC stock |
| DLC0240AWM04CB-1 (C17224827) | 2.4", 320x240 | ST7789V (LCSC-confirmed) | Not independently found this pass | **Confirmed Out of Stock** on LCSC | Not confirmed | OOS |
| Project's 320x170/170x320 baseline, any vendor | 1.9", 170x320 | ST7789/V2/V3 | 900:1 best (Xinli/Waveshare, prior rounds) | **No LCSC listing found at all, any vendor** | N/A | Confirmed absent from LCSC |

## Recommendation

No candidate in this pass clears every bar the bead asked for at once. The
honest tradeoff, stated plainly:

- **If the user's priority is truly "real LCSC stock in the hundreds,
  whatever the contrast cost":** **LCKFB-st7789-2.0inch-screen (LCSC
  C53184555)** is the only candidate in this entire five-round research
  chain with a confirmed, consistent, hundreds-plus (actually ~1,500+)
  LCSC stock figure. The real cost: its contrast ratio is **not documented
  anywhere** (not on LCSC's own listing, not on the LCKFB wiki, not in any
  datasheet found), and even its resolution/driver IC are only a
  third-party wiki's claim, not confirmed on LCSC's own official spec
  table. It ships as a breakout dev board, not a bare panel. Buying this
  means accepting an LCD of genuinely unknown contrast quality sight
  unseen, on the theory that it's probably a normal commodity ST7789V2
  panel like dozens of others in this research chain — a real, disclosed
  gamble, not a verified win.
- **If documented contrast and exact driver match matter more than the
  hundreds-plus stock bar, and a much smaller panel is acceptable:**
  **Wisevision N114-2413THBIG01-H13 (LCSC C2890618)** is the
  best-evidenced LCSC-native find in this pass — real ST7789V driver, real
  SPI interface, a primary-source 640/800 contrast figure, and real
  (if noisy, tens-to-low-hundreds) stock. Its disqualifying problem is
  size: 1.14"/240x135 is smaller than this bead's own stated 1.8" floor
  and shorter than even the 170px fallback height the user said they'd
  accept. Not recommended as a serious pick given the bead's own framing,
  but reported in full because it's the cleanest LCSC evidence trail found.
- **Every bare-panel ST7789/ILI9341-family part in this entire 5-round
  research chain that has a strong, well-documented contrast figure
  (Newhaven AF-series, 4D Systems, Orient Display, DLC Display) is either
  absent from LCSC's catalog entirely, or present and confirmed Out of
  Stock there.** This is not a gap in searching — this round specifically
  widened the search to LCSC's own catalog, multiple part-number families,
  and multiple Chinese-market generic LCM houses (HS, DLC Display,
  Wisevision/Allvision) precisely to close that gap, and it did not find a
  counter-example.
- **The project's own already-chosen 320x170 baseline has no LCSC-native
  instance from any vendor, confirmed directly in this pass** (finding 8)
  — relaxing height alone, without also relaxing width/resolution, does
  not open an LCSC path at the original size either.

**Put plainly: across five research rounds now, "well-stocked on LCSC
specifically" and "good, documented contrast in the ST7789/ILI9341
family" have never co-occurred in a single real part.** The closest this
round gets is the LCKFB board (real stock, unknown contrast) versus the
Newhaven/4D Systems/Orient parts from prior rounds (real contrast,
thin-to-zero stock). The user's actual decision is which gap to accept:
buy the LCKFB board's unknown-contrast panel for same-shipment LCSC
convenience and genuinely deep stock, accept one of the prior rounds'
documented-contrast-but-thin-stock parts and place a separate small order
outside LCSC, or decide that neither axis is worth compromising and keep
sourcing the display entirely outside LCSC (Crystalfontz's 3,082-unit
240px part from `pilink-rub`, or the Waveshare/Xinli 170-height parts from
earlier rounds, none of which are LCSC-native either).

This is research only; the user makes the actual call — no
`.planning/decisions/` ADR was written by this bead, per its acceptance
criteria.

## Verification performed vs. not performed

- **Performed:** Direct `WebFetch` reads of LCSC's own product-detail
  pages (static spec-table fields only — MPN, driver IC, resolution,
  category, HTS/ECCN codes, datasheet URL) for C53184555, C5329584,
  C19632786, C20510378, C20581161, C18198243, C17684343, C17224827, and
  C2890618, all on 2026-11-15. A direct `WebFetch` of `item.szlcsc.com`
  (LCSC's Chinese-language sister site) for C53184555, independently
  confirming the "parameters being completed" gap on that mirror too. A
  Jina-reader-proxy fetch of two datasheet PDFs (HS280S030RX, HS32B01A)
  that returned only a title via direct WebFetch, successfully extracting
  contrast-ratio and driver-IC text from both (280/300 for HS280S030RX,
  "TBD" plus the ST7789/ILI9341 internal contradiction for HS32B01A) — the
  same PDF-vision-style workaround `pilink-4mq` first used, applied here to
  two PDFs that direct fetch alone could not read. Multiple independent
  WebSearch queries (varying phrasing, Chinese and English) cross-checking
  live-stock snapshots for every candidate above against at least two
  independent crawl snapshots where available, specifically to distinguish
  a stable number (LCKFB board: 1588 vs. 1591, agreeing) from a declining
  one (HS280S030RX: 463->198->92->32->15) from a noisy-but-real one (N114
  part: 320/84/65/60) rather than taking any single snapshot at face
  value. A dedicated, multiply-reworded search for any LCSC listing at the
  project's exact 170x320/320x170 baseline resolution, finding none.
- **Not performed / caveats:** LCSC's own dynamic stock/price widget could
  not be read by direct fetch for any part in this pass — every stock
  figure in this finding comes from WebSearch-indexed snapshots of the
  rendered page, not a live API read or a screenshot taken at this exact
  moment, the same limitation (and the same mitigation — cross-checking
  multiple independent snapshots) `pilink-rub` already disclosed. A direct
  machine-readable LCSC API probe and an alternate regional mirror
  (`fat.lcsc.com`) were both blocked by this environment's own permission
  system before any request could be attempted — not a dead end this
  research chose, a capability gate it hit. The N114-2413THBIG01-H13's
  640/800 contrast figure could not be independently re-confirmed by a
  direct fetch of its own datasheet PDF in this pass (two attempts, two
  different mirror URLs, both returned no document text) — it rests on a
  WebSearch-indexed excerpt of that PDF, not a direct read, and is flagged
  at that confidence tier rather than treated as settled. The LCKFB
  board's actual underlying LCD panel/cell was not identified — no
  schematic, BOM, or EasyEDA public project exposing the specific panel
  part behind this board was found, despite a dedicated search attempt;
  its true contrast ratio therefore remains genuinely unknown, not merely
  uncited. The Newhaven AF-series/DLC Display Out-of-Stock readings in
  finding 7 come from single snapshots each (not cross-checked against a
  second independent snapshot the way the three candidates in findings
  2-4 were) — treated as consistent with, not independently proof against,
  prior rounds' identical findings for closely related Newhaven/Orient
  parts, but not re-verified to the same two-snapshot standard this pass
  otherwise applied. No physical panel of any part in this finding was
  obtained or bench-tested — this remains desk research only, as every
  bead in this five-round chain has scoped it.

## Informs

A future `.planning/decisions/` ADR on which display sourcing path to
accept (user's call: the LCKFB board's deep-but-unverified-contrast LCSC
stock, a documented-contrast part from this or a prior round sourced
outside LCSC, or staying with the current baseline sourced outside LCSC
entirely) — out of scope for this research-only bead. Depending on that
choice, follow-up beads: (1) if the LCKFB board — a sourcing bead to get a
physical sample or a direct answer from LCKFB/LCSC about the underlying
panel's contrast spec before committing, plus a hardware bead for the
breakout-module-vs-bare-panel integration question already flagged for
the structurally similar Waveshare candidate in `pilink-maj`; (2) if a
documented-contrast part from this or a prior round — a sourcing bead to
place that order outside LCSC and confirm it doesn't blow up the
assembly-order consolidation the user is trying to achieve; (3) either
way — nothing in this chain has found a part that's both well-stocked on
LCSC and well-documented on contrast, so a future round could usefully
check back on LCSC's Newhaven/DLC Display/4D Systems listings
periodically for restocks, since the parts themselves (not just their
LCSC presence) are already fully researched and ready to re-adopt the
moment LCSC stock resolves. Out of scope for this research-only bead.

Sources:
- https://www.lcsc.com/product-detail/C53184555.html and https://item.szlcsc.com/56199684.html (LCKFB-st7789-2.0inch-screen, LCSC C53184555 — direct fetch of both LCSC's English and Chinese-language sister-site pages, confirming manufacturer "LCSC-boards"/LCKFB, touch-enabled per the Chinese page, and the "parameters being completed" gap on resolution/driver/contrast)
- https://wiki.lckfb.com/en/coloreasyduino/module/screen/2-0-color-screen.html and https://openkits-wiki.easyeda.com/en/coloreasyduino/module/screen/2-0-color-screen.html (LCKFB's own wiki for the matching "2-Inch Color Screen" kit — third-party-to-the-LCSC-listing source of the 240x320/ST7789V2 claim, not independently confirmed on LCSC's own page)
- https://wiki.lckfb.com/en/coloreasyduino/module/screen/1-9-color-screen.html and https://openkits-wiki.easyeda.com/en/coloreasyduino/module/screen/1-9-color-screen.html (LCKFB's "1.9-Inch Color Screen," 170x320, ST7789V3 — real part, Taobao-only purchase link, no LCSC C-number found anywhere; basis for finding 8's negative result)
- https://www.lcsc.com/product-detail/C2890618.html (Wisevision/Shenzhen Allvision Tech N114-2413THBIG01-H13, LCSC C2890618 — direct fetch confirming 1.14", 240x135, ST7789V, SPI on LCSC's own spec table)
- https://fatwmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2109031030_Shenzhen-Allvision-Tech-N114-2413THBIG01-H13_C2890618.pdf (primary datasheet for the same part, source of the 640 min/800 typ contrast figure, read via a WebSearch-indexed excerpt after two direct-fetch attempts failed)
- https://www.lcsc.com/product-detail/C5329584.html and its datasheet (https://www.lcsc.com/datasheet/C5329584.pdf, read via Jina-reader proxy) (HS HS280S030RX, LCSC C5329584 — 2.8" 320x240, driver ST7789/ST7789T3 inconsistency, contrast min 280/typ 300, declining stock across 5 snapshots)
- https://www.lcsc.com/product-detail/C19632786.html and its datasheet (https://www.lcsc.com/datasheet/C19632786.pdf, read via Jina-reader proxy) (HS HS32B01A, LCSC C19632786 — 3.2" 320x240, contrast "TBD," driver-claim inconsistency, 16-bit parallel interface despite an "SPI" label on LCSC's listing)
- https://www.lcsc.com/product-detail/C20510378.html (Displaytech DT028ATFT-TS, LCSC C20510378 — ILI9341, 320x240, 500:1 contrast per RS/Datasheets.com listings of this exact part, no confirmed LCSC stock figure, one snapshot at ~$81/unit)
- https://www.lcsc.com/product-detail/C17684343.html and https://www.lcsc.com/product-detail/lcd-screen_newhaven-display-newhaven-display-international-nhd-2-8-240320af-csxp-f_C17340756.html (Newhaven NHD-2.8-240320AF-CSXP-FT and -F, LCSC C17684343/C17340756 — AF-series/ST7789Vi, confirmed Out of Stock on LCSC in this pass despite Active/in-production status at DigiKey/Octopart)
- https://www.lcsc.com/product-detail/C17224827.html (DLC Display DLC0240AWM04CB-1, LCSC C17224827 — 2.4" 320x240 ST7789V per LCSC's own spec table, confirmed Out of Stock on LCSC in this pass)
- .research/findings/2026-11-15-display-alternatives-contrast.md (pilink-maj — ~500:1 general baseline, MADCTL rotation background, original sourcing of the Newhaven/EA/Orient candidates referenced here)
- .research/findings/2026-11-15-display-wide-bar-aspect-contrast.md (pilink-4mq — 900:1 170-height ceiling, the driver-IC-is-not-contrast correction, Xinli TCXD019IBLON-78's no-LCSC-listing finding)
- .research/findings/2026-11-15-display-wide-bar-height240-contrast.md (pilink-ujh — the MADCTL rotation mechanism fully corroborated, the 1500:1 Newhaven figure's original sourcing)
- .research/findings/2026-11-15-display-sustainable-stock.md (pilink-rub — the Crystalfontz 3082-unit find, the Orient/4D Systems/EA LCSC-listing-but-thin-or-OOS findings this bead's search strategy follows directly)
- docs/plans/2026-11-13-custom-hardware-design.md (project's already-chosen 1.9" ST7789V 320x170 baseline and "bare panel + 0.5mm-pitch FPC connector" integration pattern)
