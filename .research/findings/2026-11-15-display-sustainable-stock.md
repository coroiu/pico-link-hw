# Sustainably-stocked wide-bar display panel, height >= 240px

## Question

Follow-up to `pilink-ujh`
(`.research/findings/2026-11-15-display-wide-bar-height240-contrast.md`),
whose top two candidates turned out to have thin/unreliable stock when the
user spot-checked them live: the LCSC-native fallback (Orient Display
AFY240320A0-2.4INTH-R, LCSC C20578695) was reported out of stock at
$41.92/unit, and the top pick (Newhaven NHD-2.4-240320AF-CSXP) had only 7
units at DigiKey. Neither is viable for even a small production run.

This bead re-does the search with **stock depth and sourcing
sustainability as a first-class, up-front filter**, not something checked
only after a contrast winner is already picked. Same baseline constraints
as the three prior rounds (`pilink-maj`/`pilink-4mq`/`pilink-ujh`): no OLED
(24/7 near-static content, burn-in risk), no e-ink, height >= 240px
(matching the old Waveshare Pico-LCD-1.3 this project replaces), prefer a
wide/rectangular "bar" aspect over square, prefer ST7789/ST7789V2/
ILI9341-family SPI drivers for firmware reuse, prioritize contrast ratio
against the established baselines (~500:1 general, 900:1 best
170-height, 1500:1 Newhaven best-but-thin-stock).

This finding re-verifies **live, today (2026-11-15)**, every specific part
number carried forward from prior rounds — no previously-reported stock
figure is assumed to still hold — and widens the vendor search to
BuyDisplay, Adafruit, SparkFun, Crystalfontz, Winstar, Tianma, Topway, and
other module houses with a track record of maintained stock.

**Scope clarification applied mid-task (from the user, via the
coordinator):** "LCSC-native" does not require JLCPCB SMT-placeability.
The actual want is narrower and more practical: a real LCSC catalog
listing with genuine stock, so the display can be ordered in the same
LCSC order/shipment as the PCB's other components, even if it ends up
hand-soldered or hand-connected afterward rather than machine-placed. This
finding therefore reports, for **every** candidate below, a dedicated
"Real LCSC listing?" line — separate from, and in addition to, its
DigiKey/Mouser/RS/Crystalfontz-direct stock figures — since a candidate can
be well-stocked at a mainstream distributor and still have no LCSC
presence at all (which turned out to be the common case in this pass).

## Findings

### 1. The two previously-recommended candidates are confirmed thin, not stale — re-verified live, a third and fourth time

**Newhaven NHD-2.4-240320AF-CSXP** (rotated 90 degrees to 320x240,
height=240, ST7789VI, 1500:1 typ/800:1 min contrast — see `pilink-ujh`
finding 2 for the rotation mechanism and full contrast citation): DigiKey
part 22204988, direct live fetch of `digikey.com` (US) today, 2026-11-15:
**In-Stock: 7**, $13.94 at qty 1 ($12.0376 at qty 50), **18-week
manufacturer lead time**, Part Status: Active. A second direct live fetch
of the **Hong Kong** regional DigiKey storefront for the same part number
today independently returned the **same figure: In-Stock 7**, HK$114.75 at
qty 1, 18-week lead — i.e. two different regional DigiKey warehouses,
fetched directly and independently in this pass, agree exactly. This is
now the *fourth* independent live confirmation of "7" across this research
chain (`pilink-maj` found 7 on 2026-11-15; this pass found 7 twice more,
US and HK). Meanwhile, two *different* stale/wrong numbers have now
surfaced from indirect search-snippet paths for this same part across this
research chain: "191" (traced in `pilink-maj` to a stale digikey.lt
search-engine snapshot, and seen again via search snippet in this pass) and
a new one, "**448**," which surfaced in this pass's WebSearch results
citing an Octopart/aggregator-style snapshot — directly contradicted by
this pass's own live fetch of the exact same digikey.hk URL showing 7.
**Every direct page fetch in this entire four-pass research chain, across
multiple dates and multiple regional storefronts, agrees on exactly 7;
every one of the (now two) wrong numbers has come from an indirect
search-snippet or aggregator-cache path, never a direct fetch.** This
part's stock is genuinely, persistently thin — not a data-freshness
problem.
- **Real LCSC listing? No.** A targeted search for this part number plus
  "lcsc.com" returned zero LCSC results in this pass — this part does not
  appear to be sold through LCSC's catalog at all, under this exact
  wording or the `-CTP`/`-T` touch-variant suffixes either.

**Orient Display AFY240320A0-2.4INTH-R**: re-checked live from two angles.
- **LCSC (C20578695):** a direct WebFetch of the live product page today
  returned no price or stock fields in the page content at all — no
  "Add to Cart," no quantity, no price table, just the bare part
  identification (manufacturer, MPN, RoHS/ECCN). A direct machine-readable
  API query was attempted and was blocked by this environment's own access
  controls (flagged honestly as a verification gap, not worked around).
  This empty buy-box is consistent with — not proof of, but not
  contradicting either — an out-of-stock listing: LCSC's site typically
  blanks the normal pricing/quantity widget for parts with zero on-hand
  inventory, which is exactly what both the prior pass's finding ("0 units
  on-hand," 2026-11-15) and the user's own live screenshot (out of stock at
  $41.92/unit) already reported. A closely related sibling part on LCSC,
  AFY240320A1-2.4INTH-R, was found live at **$41.52/unit** for qty 1 — in
  the same price neighborhood as the user's reported $41.92 for the `-R`
  dash variant, circumstantial support that this price point is realistic
  for this LCSC listing family, though it is not independent confirmation
  of the exact $41.92 figure on the exact part.
- **Real LCSC listing? Yes, but out of stock.** This is the one candidate
  in this document with a confirmed real LCSC catalog entry (C20578695) —
  it just has nothing on the shelf, consistent across every check this
  chain has made.
- **DigiKey (part 2544-AFY240320A0-2.4INTH-R-ND, product ID 12560807):** a
  direct live fetch today found **In-Stock: 23**, $15.37/unit at qty 1, no
  volume price breaks shown, Part Status: Active — but the listing is
  explicitly labeled **"MARKETPLACE PRODUCT,"** sold and fulfilled by
  "Orient Display USA Corp," not DigiKey's own warehouse stock, shipping in
  "approximately 5 days" from that third party. A marketplace listing with
  23 units is a materially weaker sustainability signal than DigiKey's own
  inventory would be at the same number — it's one seller's reel, not a
  distributor-held buffer.

**Net: both of `pilink-ujh`'s top candidates are confirmed weak a second
(Newhaven, fourth overall) and first-in-this-pass (Orient) time, from fresh
live checks, not carried-forward assumptions.** This validates exactly the
concern this bead was opened to address. Orient's LCSC listing is real but
empty; Newhaven has no LCSC listing of any kind.

### 2. New top candidate (by mainstream-distributor stock depth): Crystalfontz CFAF240320A0-024SN — 3082 units, direct from the manufacturer, confirmed live today — but no LCSC listing

This is the strongest stock-depth number found across all four research
passes in this chain, and a genuinely new find (Crystalfontz was explicitly
in this bead's "widen the vendor search" list and had not been checked
before).

- **Part number:** CFAF240320A0-024SN (plain, non-touch; touch siblings
  CFAF240320A0-024SR [resistive] and -024SC [capacitive] also exist and
  were not independently stock-checked, since the non-touch part already
  has an excellent confirmed number).
- **Resolution (native / rotated):** 240x320 native; rotated 90 degrees
  using the same MADCTL/MV row-column-exchange mechanism already
  established in `pilink-ujh` finding 2 (that finding corroborated this via
  the Linux kernel's `fb_st7789v.c` driver, which hard-codes this exact
  chip's rotation bit values) -> **320x240, height exactly 240px**, aspect
  **1.33:1**. Same aspect-ratio honesty caveat `pilink-ujh` already raised
  for the rotated Newhaven/EA options applies identically here: this is a
  real, unambiguous rectangle, but noticeably closer to square than the
  project's current 1.9"/1.88:1 baseline look. Whether 1.33:1 still reads
  as a satisfying "bar" is the user's call, stated plainly rather than
  asserted.
- **Driver IC:** Sitronix **ST7789V** — the exact plain driver already
  planned for this project, confirmed directly on Crystalfontz's own
  product page. Zero compatibility-verification risk, unlike the
  ST7789VI/ILI9341V drift flagged for other 240x320-class candidates in
  prior findings.
- **Contrast ratio:** **800:1**, stated directly on Crystalfontz's own
  product page ("...with a contrast ratio of 800:1 and 240x320 pixels"),
  with **850 nits** brightness, described as "Sunlight readable." This
  ties the EA-TFT020-23AINN figure from prior findings and sits below the
  rotated-Newhaven's 1500:1, but comfortably above the ~500:1 general
  baseline.
- **Interface:** SPI (3-wire and 4-wire), plus 8/9/16/18-bit parallel and
  DOT-CLK/Generic RGB options on the same part — the SPI path alone
  suffices for this project's existing 4-wire-SPI firmware.
- **Price:** $16.38 at qty 1, down to $14.20 at qty 1000 ("Pricing is
  subject to change," per the page).
- **Stock — the headline finding:** Crystalfontz's own product page,
  fetched live today (2026-11-15), displays **"3082 Units In-Stock & Ready
  To Ship."** This is a direct, first-party, non-marketplace figure from
  the actual panel manufacturer/distributor, roughly 2 orders of magnitude
  deeper than every other candidate's confirmed figure in this research
  chain. No lead time is quoted because none is needed at this stock
  depth.
- **Real LCSC listing? No.** A targeted search for this exact part number
  plus "lcsc.com," and a broader search for any Crystalfontz TFT part on
  LCSC generally, found no LCSC listing at all for this or any other
  Crystalfontz display part checked. **Under the clarified framing this
  bead now uses, this means the display cannot be added to the same LCSC
  cart/order as the PCB's other components** — it would need a fully
  separate order from Crystalfontz's own store. That is a real, concrete
  downside specific to the user's actual stated want (same-shipment
  convenience), distinct from the general "no second mainstream
  distributor found" caveat already noted below.
- **Sustainability caveat, stated honestly:** a targeted search for this
  exact part number at DigiKey, Mouser, Rutronik24, and Future Electronics
  also found **no listing at any of them** — this part appears to be sold
  only direct through Crystalfontz's own store. That means it does **not**
  clear this bead's "confirmed available from 2+ independent distributors"
  sustainability signal either. What it does have going for it instead:
  Crystalfontz is a 25+-year-established US-based TFT/LCD module
  manufacturer and direct distributor of its own designs (not a reseller
  of someone else's thin reel), and the raw confirmed quantity (3082
  units, today, direct from the maker) is the single deepest stock figure
  found in this entire four-pass research chain. This is a
  **single-source-but-deep** risk profile on two separate axes now (no 2nd
  mainstream distributor, no LCSC presence) — disclosed plainly rather
  than oversold.
- **Physical/mechanical:** not independently re-derived in this pass;
  Crystalfontz publishes a full datasheet (PDF) for this part which was not
  opened in this pass (the live product-page fetch already answered every
  figure needed) — a follow-up hardware bead should pull exact panel/FPC
  dimensions from it before layout.

### 3. Second pick, genuinely improved from "unconfirmed" to confirmed-but-borderline: Display Visions EA-TFT020-23AINN — has a real LCSC listing, but it's out of stock there too

- **Part/driver/contrast:** unchanged from `pilink-maj`/`pilink-ujh` —
  2.0", 240x320 native (rotated: 320x240, height=240, aspect 1.33:1), exact
  plain **ST7789V** driver, **800:1 typ / 640:1 min** contrast
  (mouser.lt/pdfDocs/TFT020-23AI-1594147.pdf, not re-fetched this pass,
  figure unchanged from two prior independent findings).
- **Stock at DigiKey — new this pass:** prior findings could never get an
  authoritative number for the non-touch part (RS Components listings
  disagreed regionally, a live recheck once returned a 503). This pass
  found it a different way: **DigiKey part 10712689**
  (1481-EATFT020-23AINN-ND — note this is a *different* DigiKey product ID
  than 10712688, the touch sibling EA-TFT020-23AITC flagged in earlier
  findings; don't confuse the two). Direct live fetch today: **In-Stock:
  52**, $32.05 at qty 1 (falling to $20.70 at qty 500), **2-week
  manufacturer lead time**, Part Status: Active.
- **Real LCSC listing? Yes — but out of stock there.** LCSC Part #
  **C17560114** is a genuine, real catalog listing for this exact part
  (confirmed manufacturer "Display Visions," MPN "EA TFT020-23AINN,"
  resolution listed as "320x240 dots" on LCSC's own page — LCSC lists the
  rotated orientation by convention, same part). A cached snapshot found
  via search shows it **marked Out of Stock**, with a last-indexed
  reference price around $48.67/unit at qty 1 (falling to ~$19.42 at
  200+) — a live direct WebFetch of the page today returned an empty
  buy-box (same JS-rendering limitation hit on every LCSC page in this
  pass), consistent with, not contradicting, that out-of-stock reading.
  **Net: this part is genuinely orderable from DigiKey (52 units) but its
  specific LCSC channel — the one that would let it ship alongside PCB
  parts in one LCSC order — currently has nothing on the shelf.**
- **Assessment:** DigiKey availability is a real improvement over prior
  findings, but 52 units is only barely above this bead's own 50-unit
  risk-flag threshold, and the LCSC-specific channel the user actually
  cares about for shipment convenience is empty. RS Components' own number
  for this part was not independently re-confirmed in this pass (another
  direct fetch attempt returned HTTP 503, the same failure mode both prior
  findings hit).

### 4. Third pick, re-verified with a part-number caveat: 4D Systems 4DLCD-24320240-IPS — the only 240px candidate with both a non-trivial DigiKey number AND a live LCSC price ladder

- **Driver/contrast:** unchanged from `pilink-ujh` — 2.4", 240x320 IPS,
  **800:1 contrast** per 4D Systems' Rev 1.5 datasheet, **batch-dependent
  driver** (ST7789V on units made before 2021-06-20, ILI9341V from
  2023-07-17 onward — any unit bought new today is very likely ILI9341V,
  not the project's planned ST7789V; budget ordinary new-panel bring-up,
  not a zero-effort swap).
- **Stock at DigiKey — new this pass, with an honest caveat:** DigiKey Hong
  Kong (product ID 15198194), fetched live today: **In-Stock: 56**, HK$210.00
  at qty 1 (~US$27), **8-week manufacturer lead time**, Part Status:
  Active. **Caveat:** the page's own title reads
  "4DLCD-24-240-320-NT-NM-200-M16/S" — a different-looking part string than
  "4DLCD-24320240-IPS" — though the product image filename and description
  both say "4DLCD-24320240-IPS" and the specs (2.4", 240x320, IPS) match
  exactly. This is most likely an internal/ordering-code alias for the same
  physical part, but that was not independently confirmed against 4D
  Systems' own part-numbering scheme in this pass.
- **Real LCSC listing? Yes, and it looks live (not empty like the two
  parts above) — though an exact on-hand quantity could not be extracted.**
  LCSC Part # **C17506419** (manufacturer listed as "4D LCD," MPN
  "4DLCD-24320240-IPS") is a genuine catalog entry, and unlike the Orient
  and EA parts above, this one's page returned an **active price ladder**
  via search-indexed content: **$40.94 at qty 1, down to roughly $16.34 at
  qty 200+**, with a "Full Bag: 50" packaging note — a live, tiered
  pricing structure is a meaningfully different signal than the blank/
  empty-buy-box pages seen for the OOS parts in this document, and
  suggests (without confirming an exact unit count) that this listing is
  not dead. A resistive-touch sibling, 4DLCD-24320240-RTP-IPS, has its own
  separate LCSC listing too (C17451751) — two related LCSC listings for
  this family is itself a modest additional presence signal. A direct
  WebFetch of the LCSC page itself today did not surface a numeric
  quantity (same JS-rendering gap as every LCSC page checked this pass) —
  so the exact LCSC on-hand count remains unconfirmed, but the price-ladder
  evidence is the strongest "this LCSC listing is probably alive" signal
  found for any 240px candidate in this document.
- Search-snippet (not independently fetched live in this pass, after two
  direct Mouser fetch attempts timed out) results suggest Mouser may carry
  deeper stock under part 971-4DLCD24320240IPS — figures seen in different
  cached snapshots ranged from 100 to 213 units — held at low confidence
  since no direct fetch succeeded this pass. RS Components' listing
  (2309319) also could not be fetched (HTTP 503, same failure as the EA
  part above, and RS snippets for this part show "temporarily out of
  stock" in some regions). **Best-confirmed number this pass: 56 units at
  DigiKey HK, direct fetch — plus a live-looking (not confirmed-quantity)
  LCSC price ladder, the best LCSC signal of any 240px candidate here.**

### 5. Checked, still unconfirmable: DisplayModule DM-TFT30-407 — no LCSC listing found either

Unchanged from `pilink-ujh`'s own disclosure: this is a true bare 3.0"
240x400 panel (rotated: 400x240, height=240, aspect 1.67:1 — the most
dramatically "bar"-shaped candidate across this whole chain), ST7796S
driver (true SPI pixel-push, not register-only), **600:1 typical**
contrast per its own datasheet. **Stock could not be checked live in this
pass either** — the displaymodule.com product page returned HTTP 429 (rate
limited) on three separate fetch attempts across two different sessions in
this research chain now. Price ($59) is confirmed via a cached snapshot,
but stock status remains genuinely unknown, not assumed in either
direction. **Real LCSC listing? No** — a targeted search found no LCSC
page for this part number. No other distributor was found carrying this
part at all. Given two consecutive research passes have now failed to get
a live stock read on this part through any channel, and it has no LCSC
presence either, it should not be treated as a viable candidate until
someone gets a direct quote from DisplayModule.

### 6. Widened vendor search: real finds, real dead ends, reported honestly

**Winstar WF24MTLAJDNN0** — a real 2.4"/240x320 panel, datasheet confirms
"Controller ST7789V (or equivalent)," SPI interface. No DigiKey, Mouser,
LCSC, or (checked specifically in this pass) LCSC listing was found
anywhere for this exact part; only small regional electronics distributors
(Unisystem, SOS Electronic, Comet.bg, Texim Europe) host its datasheet, and
none of their pages exposed a stock quantity in this pass. **Not
recommended** — real part, no confirmable sourcing path at all, LCSC or
otherwise.

**Tianma TM024HDH49-00** — sold via RobotShop with a reseller-claimed
500:1 contrast figure; no Tianma primary datasheet for this exact part was
located in this pass, so that contrast number is held at low confidence
(distributor claim, not a cited manufacturer spec) and it does not beat
any already-confirmed candidate above. No LCSC listing was searched for
specifically given the contrast figure was already low-confidence. **Not
recommended.**

**Topway** — no LMT-series 2.4"/240x320 product or datasheet with a
contrast figure was found anywhere in this pass. **Dead end**, noted here
so a future pass doesn't repeat the same search.

**FocusLCDs E24RA-I-FS550-N** — a distributor-indexed search snippet
claims **1500:1 typical** contrast, which would tie the best figure in
this entire research chain, but the actual datasheet PDF
(focuslcds.com/wp-content/uploads/2025/09/E24RA-I-FS550-N_Spec.pdf) could
not be text-extracted in this environment (the same recurring PDF-tooling
gap every finding in this chain has hit) and no stock check was attempted.
**Flagged as an unverified lead for a future pass, not a candidate here** —
the contrast figure is uncited to a readable primary source in this pass.

**Adafruit breakout modules** (2.4" ILI9341, product #2478, 240x320; 2.0"
IPS ST7789, product #4311, 320x240 native) — exactly the kind of part this
bead asked to check on the "breakout modules often have better-sustained
stock" hypothesis. The result does **not** confirm that hypothesis cleanly:
regional reseller snapshots found in this pass actively disagree with each
other for product #2478 — The Pi Hut shows "sold out" on one page and
"only 3 units left" on another, Melopero shows "out of stock," Pakronics
shows 50 units, RS Taiwan/UK show 27-36 units — and Adafruit's own stock
page was not independently fetched live in this pass (only search
snippets were available). Product #4311's own learn-guide page was
indexed as "Out of Stock" in one snapshot. **Mixed, inconclusive signal —
not a clean stock-depth win over the bare-panel candidates above**, and
both are breakout modules (not bare panels), carrying the same
integration-mismatch cost already flagged for the Waveshare 170-height
module in `pilink-maj`/`pilink-4mq`. Not recommended as a primary pick on
this evidence, though worth a fresh direct check against adafruit.com
itself before ruling out entirely. Neither was checked for an LCSC listing
given Adafruit/SparkFun parts are not typically LCSC-distributed consumer
breakout boards.

**SparkFun** — no SparkFun-branded 2.4"/240x320-class ST7789 or ILI9341
product was found at all. SparkFun's closest parts (2.8"/3.2" ILI9341
touchscreens aimed at Teensy, COM-28379/COM-28380) are a different size
class. **Dead end for SparkFun specifically.**

**BuyDisplay** — not re-investigated for height>=240 parts in this pass
beyond what `pilink-maj`/`pilink-4mq`/`pilink-ujh` already found (their
170x320 bare panel, 500:1 contrast, and the 480x272 family, 500:1 typ,
both already documented); BuyDisplay's own product pages continue to
return HTTP 403 to direct fetch, a limitation every prior finding in this
chain has also hit. No new BuyDisplay find this pass.

### 7. Reconsidering the original 170px baseline as a legitimate "stay put" option — also no LCSC listing

The bead asked to honestly surface whether a well-stocked option exists at
the *original* 170px-height baseline, if nothing at 240px is well-stocked
— it should not be avoided just because prior rounds moved past it.

**Waveshare 1.9" 170x320 ST7789V2 module (SKU 23822/31122)** — unchanged
spec from `pilink-maj`/`pilink-4mq` (170x320, exact baseline shape/aspect,
ST7789V2, 900:1 contrast per Waveshare's own spec table). Re-checked live
today: Waveshare's own store and PiShop.us both show a boolean **"IN
STOCK"** (PiShop.us: $16.95, no quantity disclosed), and the part is
independently carried by several regional resellers with their own
inventory (Abra Electronics: $17.70, in stock; Robotshop EU; Botland:
€10.90) — though not all agree (The Pi Hut shows "sold out"; rlx.sk showed
"out of stock" at its snapshot time). **No DigiKey or Mouser listing was
found for this part at all, and a targeted LCSC search found no LCSC
listing either** — this SKU appears to be sold entirely outside both the
DigiKey/Mouser mainstream-distributor channel and LCSC's catalog, through
Waveshare's own store and a scattered set of independent regional
resellers only. Net: broader reseller distribution than any single-SKU
candidate above except Crystalfontz, but with *no* numeric stock figure
ever disclosed anywhere (unlike Crystalfontz's explicit 3082), no LCSC
presence, and a genuinely mixed in-stock/sold-out picture across resellers
rather than one clean confirmed number.

**Xinli TCXD019IBLON-78** (the `pilink-4mq` bare-panel pick at this same
170-height) was not re-checked in this pass: `pilink-4mq` already
established it has **no instant small-quantity purchase path at all**
(no DigiKey/Mouser/LCSC/Alibaba/1688 listing, OEM-catalog-only), which is a
sourcing dead end regardless of today's date — re-checking wouldn't change
that conclusion, and it already confirmed no LCSC listing exists for it.

## Comparison table: this pass vs. `pilink-ujh`'s candidates, including the LCSC-listing signal

| Candidate | Height | Aspect | Driver | Contrast | Mainstream distributor stock (live, this pass unless noted) | Real LCSC listing? |
|---|---|---|---|---|---|---|
| **Crystalfontz CFAF240320A0-024SN, rotated** (new) | **240** | 1.33:1 | **ST7789V** (exact) | 800:1 | **3082 units, direct from Crystalfontz, confirmed live 2026-11-15.** No 2nd mainstream distributor found. | **No — not found on LCSC at all.** |
| EA-TFT020-23AINN, rotated | 240 | 1.33:1 | ST7789V (exact) | 800:1 typ / 640 min | **52 units, DigiKey, confirmed live 2026-11-15, 2-wk lead** (was "unconfirmed" in `pilink-ujh`) | **Yes (C17560114) — but marked Out of Stock there.** |
| 4DLCD-24320240-IPS, rotated | 240 | 1.33:1 | ST7789V (old stock) / ILI9341V (new stock) | 800:1 | 56 units, DigiKey HK, confirmed live 2026-11-15, 8-wk lead (part-number-string caveat, see finding 4) | **Yes (C17506419) — live price ladder found ($40.94 qty1 to ~$16.34 qty200+), exact quantity not confirmed, but the best LCSC signal of any 240px candidate here.** |
| NHD-2.4-240320AF-CSXP, rotated | 240 | 1.33:1 | ST7789VI | 1500:1 typ / 800 min | **Still only 7 units, DigiKey, re-confirmed live a 4th time (US + HK, both direct) 2026-11-15, 18-wk lead. Confirmed weak, not stale.** | **No — not found on LCSC at all.** |
| AFY240320A0-2.4INTH-R | 240 (native) | 1.33:1 | ST7789V | ~500-750 | DigiKey: 23 units but MARKETPLACE listing (3rd-party fulfillment), not DigiKey stock. | **Yes (C20578695) — out of stock, confirmed consistent with user's screenshot.** |
| DM-TFT30-407, rotated | 240 | 1.67:1 | ST7796S | 600:1 typ | Still unconfirmable — HTTP 429 on 3 attempts across 2 passes | **No.** |
| Waveshare 1.9" module (170h, fallback) | 170 | 1.88:1 | ST7789V2 | 900:1 | "In stock" (boolean only) at maker + several independent resellers; no DigiKey/Mouser | **No.** |

**The pattern that stands out:** every candidate with deep, confirmed
mainstream-distributor stock in this document (Crystalfontz's 3082,
Newhaven's... well, not deep, but its DigiKey listing) either has no LCSC
listing at all, or (for the two that do have a real LCSC listing — Orient
and EA) that specific LCSC channel is the one that's out of stock. **The
only 240px candidate with both a non-trivial mainstream-distributor number
and a live-looking LCSC price ladder is the 4D Systems part (finding 4)**
— making it the strongest fit specifically for the user's "orderable from
LCSC's own catalog, same shipment as the PCB" want, even though its raw
DigiKey quantity (56) and Crystalfontz's (3082) aren't in the same league.

## Recommendation

This pass surfaces a real tension the user should weigh directly, because
no single candidate wins on both axes this bead cares about:

- **If maximum confirmed stock depth at a mainstream distributor matters
  most, and a separate LCSC-less order is acceptable:** Crystalfontz
  CFAF240320A0-024SN, rotated 90 degrees (finding 2) — 320x240, height
  exactly 240px, exact ST7789V driver, 800:1 contrast, and a confirmed live
  **3,082-unit** on-hand quantity directly from the manufacturer today —
  roughly two orders of magnitude more margin than every other candidate
  checked in this entire four-pass research chain. Its real gap: **no LCSC
  listing found at all**, and no second mainstream distributor either — a
  genuine single-source-but-deep risk profile, and the display would need
  its own separate order from Crystalfontz, not the same LCSC cart as the
  PCB's other parts.
- **If being orderable through LCSC's own catalog (same order/shipment as
  the PCB) matters most, even at thinner mainstream-distributor stock:**
  **4D Systems 4DLCD-24320240-IPS**, rotated (finding 4) — the only 240px
  candidate in this document with both a confirmed non-trivial DigiKey
  number (56 units) **and** a genuinely live-looking LCSC listing (an
  active $40.94-to-$16.34 price ladder on LCSC part C17506419, exact
  on-hand quantity unconfirmed but clearly not an empty/dead listing the
  way the Orient and EA parts' LCSC pages are). The real caveat: budget for
  an ILI9341V driver on newly-manufactured stock, not the originally-
  planned ST7789V, and the part-number-string mismatch noted in finding 4
  should be resolved with 4D Systems or DigiKey before ordering.
- **Middle option:** Display Visions EA-TFT020-23AINN, rotated — same
  shape/driver/contrast class, a confirmed (if thinner, 52-unit) DigiKey
  number with a 2-week lead time, but its own real LCSC listing
  (C17560114) is specifically out of stock right now — so it only helps if
  DigiKey-only sourcing (not same-shipment LCSC convenience) is
  acceptable.

**Both of `pilink-ujh`'s previous top picks are now confirmed weak for a
second or fourth time from fresh live checks in this pass, not a stale
number**: Newhaven NHD-2.4-240320AF-CSXP sits at 7 units/18-week lead
(four independent live fetches across two regions and two sessions all
agree on exactly 7, while two different wrong numbers — "191" and "448" —
have each separately surfaced only from indirect search-snippet paths),
and has no LCSC listing at all. Orient Display AFY240320A0-2.4INTH-R has a
real LCSC listing but it's empty, and its DigiKey presence is a thin
23-unit third-party marketplace listing, not distributor-held stock —
neither is a sustainable choice for even a small production run, exactly
as this bead's framing anticipated.

**DisplayModule DM-TFT30-407** remains the most dramatically "bar"-shaped
option (1.67:1) with a genuine bare-panel, true-SPI, ST7796S part, but its
stock status has now failed to resolve across two separate research
passes and three fetch attempts (consistent HTTP 429 rate-limiting), and it
has no LCSC listing either — not recommended until someone gets a direct
quote from DisplayModule.

**The original 170px baseline (Waveshare 1.9" ST7789V2 module) remains a
legitimate, honestly-surfaced fallback** if the user decides no 240px
option's sourcing profile is acceptable: it has broader reseller
distribution than any single 240px candidate except Crystalfontz, but no
distributor ever discloses a hard quantity for it, it has no LCSC listing
either, and reseller signals are genuinely mixed (some in stock, some sold
out) rather than cleanly confirmed — a weaker sustainability story than the
new Crystalfontz find on the mainstream-distributor axis, and no better
than any other candidate on the LCSC axis.

This is research only; the user makes the actual call (Crystalfontz at
240px vs. the LCSC-orderable 4D Systems part vs. EA-TFT020-23AINN vs.
staying at the 170px baseline) — no `.planning/decisions/` ADR was written
by this bead, per its acceptance criteria.

## Verification performed vs. not performed

- **Performed:** Direct live WebFetch of DigiKey (US and HK regional
  sites), LCSC, and Crystalfontz product pages on 2026-11-15, re-reading
  stock quantity, price, lead time, and part-status fields directly from
  each page's own content rather than from a search snippet, for:
  NHD-2.4-240320AF-CSXP (DigiKey US 22204988 — 7 units; DigiKey HK,
  independently — also 7 units), AFY240320A0-2.4INTH-R (LCSC C20578695 —
  no buy-box content returned; DigiKey 12560807 — 23 units, marketplace),
  EA-TFT020-23AINN (DigiKey 10712689 — 52 units; LCSC C17560114 — no
  buy-box content returned directly, cached snapshot says Out of Stock),
  4DLCD-24320240-IPS (DigiKey HK 15198194 — 56 units, part-string caveat
  noted; LCSC C17506419 — no buy-box content returned directly, but a
  cached price-ladder snapshot showing $40.94-$16.34 tiers was found),
  CFAF240320A0-024SN (Crystalfontz direct — 3082 units; confirmed no LCSC
  listing exists via targeted search). Also performed: targeted WebSearch
  cross-checks, specifically scoped to lcsc.com, for every single candidate
  in this document (new requirement this pass applied per the
  mid-task scope clarification) — Crystalfontz, Newhaven, DM-TFT30-407, and
  the Waveshare 170-height module all came back with zero LCSC results,
  while EA-TFT020-23AINN, 4DLCD-24320240-IPS, and AFY240320A0-2.4INTH-R all
  have real LCSC catalog entries with distinct C-numbers; live fetches of
  Waveshare's and PiShop.us's own product pages for the 170-height
  fallback; and a fresh vendor-breadth search across BuyDisplay, Adafruit,
  SparkFun, Crystalfontz, Winstar, Tianma, and Topway as the bead required.
- **Not performed / caveats:** LCSC's live stock/price widget could not be
  independently re-extracted via direct WebFetch for *any* LCSC listing
  checked in this pass (the page's dynamic pricing/quantity content simply
  wasn't present in the fetched markup for any of the three real LCSC
  listings found) — exact on-hand quantities for EA-TFT020-23AINN's and
  4DLCD-24320240-IPS's LCSC listings specifically are therefore not
  independently confirmed by a direct fetch of this session's own, only by
  cached search-indexed snapshots (which, unlike the AFY240320A0-2.4INTH-R
  and NHD-2.4-240320AF-CSXP cases, were at least internally consistent with
  "not obviously dead" for the 4D Systems part). A direct machine-readable
  API query to LCSC was blocked by this environment's own permission
  system — this pass could not independently re-derive the user's exact
  reported "$41.92, out of stock" figure for the Orient part from a live
  source of its own, though the empty buy-box and a same-family sibling
  part's $41.52 price are circumstantially consistent with it, and the
  prior pass's own live check ("0 units," 2026-11-15) already independently
  corroborated the out-of-stock claim from a different angle. Three
  separate attempts (across this pass and `pilink-ujh`) to fetch
  displaymodule.com's DM-TFT30-407 page all hit HTTP 429 rate-limiting; its
  stock status is genuinely unknown, not assumed in either direction. Two
  direct Mouser.com fetch attempts for 4DLCD-24320240-IPS timed out;
  Mouser's possible deeper stock (100-213 units per conflicting cached
  search snippets) is reported at low confidence, not independently
  confirmed live. RS Components pages for EA-TFT020-23AINN and
  4DLCD-24320240-IPS both returned HTTP 503 on direct fetch in this pass,
  the same failure mode two prior findings also hit for RS specifically —
  RS Components could not be used as an independent second-distributor
  check for either part in this research chain to date. Crystalfontz's own
  datasheet PDF for CFAF240320A0-024SN was not opened in this pass (the
  live product page already answered every figure needed); exact
  mechanical/FPC dimensions for that part should be pulled from it before
  enclosure/PCB layout. Adafruit's and SparkFun's own storefronts were not
  independently fetched live for product #2478/#4311 — only third-party
  reseller search snippets, which disagreed with each other — a cleaner
  read of adafruit.com/sparkfun.com directly would strengthen or weaken
  that section's "mixed, inconclusive" call, and neither was checked
  against LCSC. The FocusLCDs E24RA-I-FS550-N PDF could not be
  text-extracted (same recurring PDF-tooling gap as every prior finding in
  this chain: no `pdftotext`, no Python PDF library, confirmed again) and,
  unlike several PDFs in prior passes, the PDF-vision image-reading
  workaround that worked on other encrypted PDFs was not attempted on this
  one specifically in this pass — a gap, not a dead end, for a future pass
  to pick up. No physical panel of any candidate was obtained or
  bench-tested anywhere in this four-pass research chain — this remains
  desk research only, as every bead in the chain has scoped it.

## Informs

A future `.planning/decisions/` ADR on which panel to adopt (user's call:
Crystalfontz CFAF240320A0-024SN at 240px for maximum confirmed stock depth,
the LCSC-orderable 4D Systems 4DLCD-24320240-IPS for same-shipment
convenience, EA-TFT020-23AINN as a DigiKey-only middle option, or stay at
the 170px Waveshare baseline) — out of scope for this research-only bead.
Depending on that choice, follow-up beads: (1) if Crystalfontz — pull its
full datasheet for exact panel/FPC mechanical dimensions, plus a hardware
bead for the enclosure cutout/bezel rework and FPC-tail repositioning the
rotation requires (same category of rework `pilink-ujh` already flagged
for the rotated-Newhaven option), and plan for a separate Crystalfontz
order alongside (not merged into) the LCSC-sourced PCB order; (2) if 4D
Systems — the same enclosure-rework bead, plus a firmware bead to verify
the ILI9341V init sequence against newly-manufactured stock, plus
resolving the DigiKey part-number-string discrepancy and getting a live
LCSC quantity quote before committing; (3) if EA-TFT020-23AINN — the same
enclosure-rework bead, ordering via DigiKey since its LCSC channel is
currently empty; (4) if staying at the 170px Waveshare baseline — no
enclosure change needed, but get a hard quantity quote directly from
Waveshare before committing to it as a "sustainable" choice, since no
distributor in this research chain has ever disclosed a numeric stock
figure for that SKU, and it has no LCSC listing either. Out of scope for
this research-only bead.

Sources:
- https://www.digikey.com/en/products/detail/newhaven-display-intl/NHD-2-4-240320AF-CSXP/22204988 (direct live fetch 2026-11-15: In-Stock 7, $13.94 qty1, 18-week lead, Active)
- https://www.digikey.hk/en/products/detail/newhaven-display-intl/NHD-2-4-240320AF-CSXP/22204988 (second, independent direct live fetch 2026-11-15, different region: In-Stock 7, HK$114.75 qty1, 18-week lead — confirms the US figure, debunks a stray "448" search-snippet figure)
- https://findchips.com/search/NHD-2.4-240320AF-CSXP and the digikey.lt search snippet surfaced within it (stale cached "191" figure, traced and rejected as a search-index artifact, not a live read — consistent with `pilink-maj`'s own earlier finding of the same wrong number)
- https://lcsc.com/product-detail/LCD-Screen_Orient-Display-AFY240320A0-2-4INTH-R_C20578695.html (direct live fetch 2026-11-15: no price/stock content returned — consistent with an out-of-stock listing and with the prior pass's "0 units" finding and the user's live screenshot; real LCSC listing confirmed to exist, just empty)
- https://lcsc.com/product-detail/LCD-Screen_Orient-Display-AFY240320A1-2-4INTH-R_C20521982.html (sibling part, $41.52/unit qty1 — circumstantial price-range support for the user's reported $41.92 on the `-R` dash variant)
- https://www.digikey.com/en/products/detail/orient-display/AFY240320A0-2-4INTH-R/12560807 (direct live fetch 2026-11-15: In-Stock 23, $15.37 qty1, explicitly a MARKETPLACE PRODUCT fulfilled by Orient Display USA Corp, not DigiKey's own stock, Active)
- https://crystalfontz.com/product/cfaf240320a0024sn (direct live fetch 2026-11-15: Sitronix ST7789V, 240x320, contrast ratio 800:1, 850 nits sunlight-readable, SPI/parallel/RGB interfaces, $16.38 qty1 to $14.20 qty1000, **"3082 Units In-Stock & Ready To Ship"** — new top candidate this pass; confirmed via targeted search to have no LCSC listing)
- https://www.digikey.com/en/products/detail/display-visions/EA-TFT020-23AINN/10712689 (direct live fetch 2026-11-15: In-Stock 52, $32.05 qty1, 2-week lead, Active — resolves `pilink-maj`/`pilink-ujh`'s previously-unconfirmed non-touch-part stock question)
- https://lcsc.com/product-detail/LCD-Screen_Display-Visions-EA-TFT020-23AINN_C17560114.html (real LCSC listing for this exact part, confirmed via search snippet to be marked Out of Stock, ~$48.67/unit last-indexed reference price; direct fetch returned an empty buy-box, consistent)
- https://www.mouser.lt/pdfDocs/TFT020-23AI-1594147.pdf (Display Visions/EA TFT020-23AI family datasheet, contrast ratio min 640/typ 800:1 — figure carried forward unchanged from `pilink-maj`, not re-fetched this pass)
- https://www.digikey.hk/en/products/detail/4d-lcd-pty-ltd/4DLCD-24320240-IPS/15198194 (direct live fetch 2026-11-15: In-Stock 56, HK$210 qty1, 8-week lead, Active — page's own title string reads "4DLCD-24-240-320-NT-NM-200-M16/S," flagged as a possible SKU-alias, not independently resolved)
- https://lcsc.com/product-detail/LCD-Screen_4D-LCD-4DLCD-24320240-IPS_C17506419.html (real LCSC listing for this exact part; direct fetch returned no stock figure, but a cached search snippet shows a live price ladder, $40.94 qty1 to ~$16.34 qty200+ — the strongest LCSC-presence signal of any 240px candidate in this document)
- https://www.lcsc.com/product-detail/Liquid-Crystal-Display-Screen_4D-LCD-4DLCD-24320240-RTP-IPS_C17451751.html (resistive-touch sibling's separate LCSC listing, additional presence signal for this part family)
- https://www.mouser.com/datasheet/2/451/4DLCD_24320240_IPS_Series_Datasheet_R_1_5-2448899.pdf (4D Systems Rev 1.5 datasheet, 800:1 contrast, ST7789V/ILI9341V batch-dependent driver note — figure carried forward unchanged from `pilink-ujh`)
- https://www.displaymodule.com/products/3-inch-ips-display-240x400-capacitive-with-mcu-spi-rgb and https://cdn.shopify.com/s/files/1/0264/7629/files/DM-TFT30-407_Datasheet.pdf (DM-TFT30-407 — spec/contrast figures carried forward unchanged from `pilink-ujh`; live stock still unconfirmable, HTTP 429 on three attempts across two passes; no LCSC listing found)
- https://download.unisystem.com/LCD-TFT/WF24MTLAJDNN0/WF24MTLAJDNN0.pdf (Winstar WF24MTLAJDNN0 datasheet, confirms "Controller ST7789V or Equivalent" — no DigiKey/Mouser/LCSC listing found, dead end for sourcing)
- https://robotshop.com/products/dualturb-tianma-tm024hdh49-00-24-240x320-industrial-tft-lcd-module (Tianma TM024HDH49-00 via RobotShop — reseller-claimed 500:1 contrast, no primary Tianma datasheet located, low confidence, not recommended)
- https://focuslcds.com/wp-content/uploads/2025/09/E24RA-I-FS550-N_Spec.pdf (FocusLCDs E24RA-I-FS550-N — distributor-indexed 1500:1 typ claim, PDF unreadable in this pass, flagged as an unverified lead for a future pass)
- https://www.adafruit.com/products/2478 and https://www.adafruit.com/product/4311 (Adafruit 2.4" ILI9341 and 2.0" ST7789 breakout modules — mixed/conflicting reseller stock snapshots found, Adafruit's own live page not independently fetched this pass, inconclusive)
- https://www.pishop.us/product/1-9inch-lcd-display-module-170-320-resolution-spi-interface-ips-262k-colors/ (direct live fetch 2026-11-15: Waveshare 1.9" ST7789V2 module, IN STOCK boolean, $16.95, no quantity disclosed — 170px baseline fallback; no LCSC listing found)
- .research/findings/2026-11-15-display-alternatives-contrast.md (pilink-maj — ~500:1 general baseline, original sourcing of Newhaven/EA/Orient candidates)
- .research/findings/2026-11-15-display-wide-bar-aspect-contrast.md (pilink-4mq — 170-height candidates, the 900:1 ceiling, and the MADCTL rotation mechanism's first application in this chain)
- .research/findings/2026-11-15-display-wide-bar-height240-contrast.md (pilink-ujh — the rotation mechanism fully established with Linux-kernel-driver corroboration, and the two now-confirmed-thin candidates this bead re-checks)
- docs/plans/2026-11-13-custom-hardware-design.md (project's already-chosen 1.9" ST7789V 320x170 baseline and "bare panel + 0.5mm-pitch FPC connector" integration pattern)
