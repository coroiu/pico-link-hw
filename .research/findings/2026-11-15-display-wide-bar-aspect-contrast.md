# Higher-contrast panel in the same wide-bar aspect ratio (320x170 class)

## Question

Follow-up to `pilink-maj`'s finding
(`.research/findings/2026-11-15-display-alternatives-contrast.md`),
which surveyed small TFT panels generally and recommended two candidates
(Newhaven NHD-2.4-240320AF-CSXP, Display Visions EA-TFT020-23AINN) — but
both are 240x320, a portrait-ish ~1.33:1 panel. Wrong shape: the user
deliberately chose the 1.9" ST7789V 320x170 panel to match the wide "bar"
look of the LilyGo T-Embed (~1.88:1 aspect, see
`docs/plans/2026-11-13-custom-hardware-design.md`), and does not want to
lose vertical resolution below 170px. Width can grow freely (320, 360,
400+) since that costs nothing the user cares about; shape (wide bar,
height >= 170) must be respected.

This bead asks: is there a real, sourceable, LCD/IPS-class (not OLED, not
e-ink) panel in the ~1.7-2.0:1 aspect / height>=170 window that documents a
contrast ratio better than the ~500:1 baseline `pilink-maj` established for
this panel class, ideally staying in the ST7789/ST7789V driver family?

## Findings

### 1. The "bar type" TFT market does not live in this aspect window

Vendors (Newhaven, Microtips, Crystalfontz, DWIN/BuyDisplay, Densitron,
BOE, Tianma) all sell a real "bar type" / "stretched bar" product category,
but every part found in it sits well outside the 1.7-2.0:1 / height>=170
target:

- **Too short:** Newhaven's own Bar-Type IPS TFT line
  (digikey.co.za/en/product-highlight/n/newhaven-display/bar-type-ips-tft-displays)
  includes NHD-3.9-480128AF-ASXP (3.9", 480x128, aspect 3.75:1) — height
  128px, below the 170px floor. Crystalfontz's CFAF480128A0-052TN (5.2",
  480x128) and Microtips' AWL-series bar panels found via Mouser
  (mouser.in/en/new/microtips/microtips-awl-bar-type-tft-displays/) are in
  the same 480x128-class bucket.
- **Far wider/taller than needed, aimed at a different product class:**
  Newhaven NHD-2.9-376960AF-ASXP (2.9", 376x960, aspect ~2.55:1, **1,500:1
  contrast per Newhaven's own feature list**) and NHD-6.8-4801280AF-ASXP
  (6.8", 480x1280, ~2.67:1) are built for smart pens/toothbrushes — a
  narrow, tall "bar," not a wide landscape one. BuyDisplay's own bar-type
  catalog (buydisplay.com/bar-type-4-58-inch-320x960-ips-tft-lcd-display-spi-rgb-interface)
  and automotive "stretched bar" dash panels (BOE AV123Z7M-N11, 12.3",
  1920x720, ~2.67:1; Densitron 9.2" 1920x384 bar IPS, contrast 1000:1 per
  distributor copy) land in the same 2.5:1-2.7:1+ aspect zone, nowhere near
  1.7-2.0:1.

None of these match the shape constraint, so none are usable candidates
regardless of their (sometimes genuinely high) contrast numbers — including
the 1,500:1 and 1000:1 figures above, which look attractive but belong to
the wrong-shape "narrow pen/toothbrush bar" and "automotive dash strip"
product classes respectively, not a 1.88:1 landscape bar.

### 2. Wider-at-the-same-height (360-480 x 170-200): no usable candidate found

Direct searches for "360x170", "400x170", "480x170", "480x172", "480x192",
and "390x170" TFT modules returned no matching product from any vendor
checked (Newhaven, BuyDisplay, Orient Display, Display Visions, Ampire,
Topway, Tianma, BOE, Raystar). The nearest adjacent size, 480x272 (4.3",
aspect 1.76:1 — close to the target aspect, but height 272px is a much
bigger jump than the user asked for), turned up a real part (DLC Display
DLC0430BCP12RF-1) with a distributor-indexed figure of "640/800
(min/typ)" contrast — but the primary-source datasheet PDF
(digimax.it/media_import/DISPLAY/DLC%20DISPLAY/TFT%20LCD/DLC0430BCP12RF-1/DLC0430BCP12RF-1_DS_001.pdf)
is encrypted/image-based and could not be verified directly (no
`pdftotext`/PDF-text tooling available in this environment — confirmed via
`which pdftotext`, not installed — same limitation the sibling finding
hit). Given the unverified number and the larger-than-requested height
jump, this is not recommended; width growth did not pay off anywhere in
this research. Say so plainly rather than stretching it.

### 3. Primary recommendation: Waveshare's own 1.9" 170x320 ST7789V2 module — same shape, same resolution, 900:1 contrast

The cleanest find came from staying at the exact baseline size/resolution
and checking whether a more reputable source sells the *same* shape with a
different driver revision, per the bead's framing. This was independently
re-verified against Waveshare's own live pages (not just a search snippet)
after a flag raised during review — see detail below.

- **Part numbers:** Waveshare SKU **23822** (non-touch, "1.9inch LCD
  Module") and SKU **31122** (touch variant, "1.9inch Touch LCD," also the
  panel used on the "ESP32-S3-LCD-1.9" dev board).
- **Resolution / aspect:** 170 x 320 — **identical** to the project's
  chosen baseline, exactly the 1.88:1 ("320/170") aspect ratio the user
  wants. (The touch variant's title/feature-list text says "172x320"
  while its own spec table and selection guide say "170x320" — Waveshare's
  page is internally inconsistent on this by 2px; the spec table/selection
  guide figure, 170x320, is the one that matches the project's baseline
  exactly and is treated as authoritative here.)
- **Driver IC:** **ST7789V2** — Sitronix's revision of the ST7789V already
  planned for this project's display subsystem. Confirmed as the same
  driver IC on all three Waveshare pages checked (non-touch module, touch
  module, and the ESP32-S3-LCD-1.9 board that embeds the same panel).
- **Contrast ratio: 900:1**, confirmed directly from Waveshare's own
  "LCD parameters" spec table, read on two independent Waveshare-owned
  pages (fetched and read directly, not taken from a search summary):
  - waveshare.com/esp32-s3-lcd-1.9.htm — table row "Contrast Ratio |
    900:1", "Brightness | 500 cd/㎡", "Driver IC | ST7789V2", "Resolution |
    170×320". This board is explicitly sold in both touch and non-touch
    variants sharing the same LCD parameters row, with touch broken out
    as a separate "Touch: Supported (Touch Version Only)" line — i.e. the
    900:1 figure describes the shared panel, not something touch-specific.
  - waveshare.com/1.9inch-touch-lcd.htm (SKU 31122) — same spec table:
    "Contrast ratio 900:1", "Brightness 500cd/m²", "Driver IC ST7789V2".
  - The plain non-touch module page (waveshare.com/1.9inch-lcd-module.htm,
    SKU 23822) confirms 170x320/ST7789V2/IPS/SPI but does not itself
    repeat a contrast-ratio row — so 900:1 is directly manufacturer-sourced
    for the touch SKU and the shared-panel board page, and inferred (not
    independently re-stated) for the plain non-touch SKU, which appears to
    be the same base LCD cell without the touch overlay. Noted as a
    caveat below rather than overstated.
  That's **~1.8x the ~500:1 baseline** `pilink-maj` documented for this
  exact panel class (BuyDisplay's own 170x320 ST7789 panel, by contrast,
  documents only 500:1 — see finding 5 below), and it is a real
  manufacturer-published spec, not a reseller guess.
- **Connector:** Non-touch SKU 23822 uses an MX1.25 8-pin cable/connector
  on a small breakout PCB. Touch SKU 31122 offers a choice of "SH1.0
  connector, FPC0.5 connector," ships with an FFC cable — closer to the
  bare-FPC integration pattern, but adds a capacitive touch IC (CST816)
  the project doesn't need.
- **Stock / price (checked 2026-11-15, price tiers re-verified 2026-11-15
  after review flagged an error):** Both pages show a live "Add to Cart"
  with no out-of-stock notice, sold direct from Waveshare. SKU 23822's own
  quantity-price table reads: $11.99 list, $11.59 at qty 1-9, $11.39 at
  10-49, $11.31 at 50-99, and a 100+ tier row that exists on the page but
  shows no price — an earlier version of this finding mis-read $11.31 as
  the 100+ price when it is actually the 50-99 price (the review that
  caught this is correct). SKU 31122 at $12.99 (down to $11.97 at 50-99).
  One third-party reseller link (Abra Electronics) that search results
  surfaced for SKU 23822 returned HTTP 404 on direct re-check — flagged as
  stale/unconfirmed, not relied on; Waveshare's own store page is the
  basis for the stock claim here.

### 4. Driver-family cost: ST7789V2 vs ST7789V — not a rewrite, but not guaranteed byte-identical either

ST7789V2 is Sitronix's later revision in the same ST7789 family already in
this project's display plans — not a different driver family requiring a
new firmware driver. However, no authoritative Sitronix document
enumerating exact V-to-V2 command/register differences was found; the best
evidence is a Newhaven Display support-forum answer
(support.newhavendisplay.com/hc/en-us/community/posts/4424919637399-ST7789V-and-ST7789VI-compatibility)
stating a related variant (ST7789VI) is compatible with ST7789V, and a
separate reply calling ST7789V/ST7789V2 compatibility "very possible" but
recommending the requester test their own init sequence on real hardware
rather than assume. **Honest cost estimate:** expect to reuse the existing
ST7789 driver code as-is, but budget normal new-panel bring-up time to
verify/tune the gamma table and init-sequence register writes against the
real ST7789V2 part — this is ordinary TFT bring-up work, not a driver
rewrite, but it is not zero-risk "no changes needed" either.

### 5. Contrast is a panel/glass property, not a driver-IC property — correction, and baseline re-confirmed

**Correction:** an earlier version of this finding said the Waveshare
panel's 900:1 contrast was "tied specifically to the ST7789V2 variant"
Waveshare uses, and that "the choice of panel/driver pairing... is what
drives the contrast difference." A PR reviewer caught this and it is
wrong. The ST7789/ST7789V/ST7789V2 driver IC drives the glass according to
a gamma/register table it is sent — it does not set contrast ratio.
Contrast ratio is a property of the LC cell, polarizers, and backlight
stack (the glass build), chosen independently of which ST7789 variant
happens to drive it. The Waveshare panel being ST7789V2 is incidental to
its 900:1 figure, not causal, and this finding no longer claims otherwise
anywhere.

The direct counter-evidence, found by review and independently verified
in this revision (see finding 7): **Xinli TCXD019IBLON-78**, a 170x320
panel using the **plain ST7789V** driver (not V2), documents **900:1
typical / 700:1 minimum** contrast in its own primary-source datasheet —
tying or beating the Waveshare ST7789V2 module's figure on the *older*
driver generation the project already plans to use. Shenzhen Yousee's
YX19002A (170x320, ST7789V, reported ~800:1 per a DirectIndustry
distributor listing) points the same direction but could not be
independently verified against Yousee's own full datasheet in this pass
(PDF access blocked — see finding 7's verification notes) and is held to
a lower confidence tier accordingly.

BuyDisplay's own bare-panel 170x320 SKUs (ER-TFT019-1 / ER-TFTM019-1-SPI,
buydisplay.com/full-viewing-angle-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789)
use the plain ST7789 controller and document 500:1 typical contrast, 350
cd/m² — matching `pilink-maj`'s baseline exactly, not beating it. This
panel and the 900:1 Xinli panel use the *same driver IC* (plain ST7789V)
and land roughly 80% apart on contrast — direct proof, within this one
panel class, that the driver IC is not the variable that determines
contrast. What actually varies is glass/polarizer/backlight quality,
panel-to-panel and factory-to-factory, independent of which ST7789
variant is wired to it.

### 6. Integration caveat: breakout module, not a bare FPC panel

The project's design doc calls for a "bare panel + 0.5mm-pitch FPC
connector" soldered directly onto the custom PCB
(`docs/plans/2026-11-13-custom-hardware-design.md`). Waveshare does not
sell the 900:1 ST7789V2 glass as a standalone bare panel — only as a small
breakout module (MX1.25 cable for the non-touch SKU, or FPC0.5/SH1.0 for
the touch SKU). No bare-panel-only listing for this specific ST7789V2/900:1
glass was found from Waveshare or any other distributor searched. Using it
means either (a) mounting Waveshare's small breakout board inside the
enclosure and running a cable/FPC from the main PCB to it (a normal pattern
for dongle-class devices, including — most likely — the T-Embed itself,
which also buys its display as a pre-mounted sub-module), or (b) finding
and qualifying the OEM bare panel behind Waveshare's module directly from
their supply chain, which would need a direct inquiry to Waveshare and
wasn't resolvable from public sourcing alone in this research pass.

### 7. Xinli TCXD019IBLON-78 — verified as a real bare panel with plain ST7789V, 900:1 typ contrast, 0.5mm-pitch 14-pin FPC

Review flagged this part as a bare-panel candidate the original research
pass missed, citing an Avnet/Tria distributor listing it could not verify
against the actual datasheet (the PDF is image-based, and no
`pdftotext`/OCR tooling is installed in this environment — the same
limitation this finding and the sibling `pilink-maj` finding hit
elsewhere). This revision got past that limitation: Claude's PDF-reading
tool can render an image-based PDF's pages visually and read the text off
them, even with no `pdftotext`/`tesseract`/Python PDF library installed
(confirmed again here: no `pip`, no passwordless `sudo` to install
anything). That let the actual Xinli datasheet be read page-by-page
instead of relied on as a distributor snippet. **This method should be
tried on other "encrypted/image-based, unverifiable" PDFs flagged
elsewhere in this research chain (DLC0430BCP12RF-1, Yousee YX19002A's
full datasheet, Tailor Pixels' full TTH019BVS-01 spec) before writing them
off as unverifiable in future passes** — it isn't guaranteed to work on
every PDF (see finding 8, where it didn't), but it worked cleanly here.

**Manufacturer and document:** Zhejiang Xinli Optoelectronics Technology
Co., Ltd (浙江新力光电科技有限公司), a Chinese TFT-LCD/touch-module maker
reported founded in 2008 (per a Made-in-China company listing —
not independently audited beyond that listing), with a TFT-LCD size range
reported from ~0.97" to 21.5", serving automotive/industrial customers.
Datasheet: "SPECIFICATION, PRODUCT NO.: TCXD019IBLON-78, VERSION: Ver 1.2,
ISSUED DATE: 2022-5-20", hosted as a direct PDF (not a shoppable web
product page) inside Avnet Embedded's display-module catalog
(embedded.avnet.com/product/tcxd019iblon-78, 301-redirecting straight to
the PDF). Avnet Embedded is itself rebranding to "Tria Technologies," a
wholly-owned Avnet subsidiary doing embedded-display design/manufacturing
services. **Confidence: high** that this is a genuine OEM datasheet — it
carries full electro-optical test methodology (equipment model, viewing
geometry, five-point uniformity diagram, the contrast-ratio formula
itself), consistent with authentic LCM-vendor documentation and not the
kind of detail a distributor index fabricates.

Full spec, read directly from the datasheet (Section 2 "General
Description and Features", Section 4 "Interface Pin Connection", Sections
7/12 "Electrical/Electro-Optical Characteristics"):

| Spec | Value | Confidence |
|---|---|---|
| Module outsize | 25.8 x 49.72 x 1.43 mm | High — direct from datasheet |
| LCD active area | 22.7 x 42.72 mm | High |
| Dot number | 170 x 3(RGB) x 320 | High — matches project baseline exactly |
| LCD type | TFT Transmissive, IPS (mechanical sheet: "IPS MODULE... NORMAL BLACK") | High |
| Driver IC | **ST7789V (Sitronix)** — plain V, not V2 | High |
| Interface | **FPC 0.5mm-pitch, 14 pin**, SPI | High |
| Power supply | VCC 2.8V typ (2.5-3.3V range); VDDI (logic) 1.65-3.3V, typ 1.8V | High |
| Contrast ratio | **Min 700, Typ 900** | High — primary datasheet electro-optical table, disclosed test method (Topcon BM-7A luminance meter, defined geometry) |
| Surface luminance | Typ 350 cd/m² | High |
| Response time | Typ 30 ms, Max 35 ms | High |
| Viewing angle | 60-80 deg in all 4 directions (CR>10 definition) | High |
| Operating/storage temp | -20 to 70 C / -30 to 80 C | High |
| Backlight | 4-chip white LED, Vf 2.8-3.4V, If 80mA, ~20,000 hr estimated life | High |

**This is a genuine bare panel**, not a breakout module: the 25.8 x 49.72
x 1.43mm "Module Outsize" *is* the glass+FPC+backlight stack — the
mechanical-dimension drawing shows only the LCM glass and a flex tail, no
carrier-PCB silhouette. That directly clears the gap finding 6 flags for
the Waveshare module.

**FPC connector:** 14 pins at 0.5mm pitch, confirmed directly from the
datasheet's pin table and mechanical drawing — matches the project's
0.5mm-pitch FPC assumption on both pitch and pin count. **Not confirmed:**
contact orientation (top-contact vs. bottom-contact / same-side vs.
opposite-side gold fingers) — the extracted drawing has dimensions but no
explicit text label for this, and it determines which physical FPC
connector part is compatible. Verify against the actual mechanical
drawing image or a physical sample before finalizing a connector choice.

**Sourcing — the real open question, disclosed plainly, not papered
over:** the only trace of this part found anywhere is the datasheet PDF
hosted on Avnet Embedded/Tria's display catalog. That catalog page shows
**no price, no stock quantity, no "Add to Cart," and no visible "request a
quote" button** — it is a bare datasheet listing inside a much larger OEM
display-module catalog (hundreds of other Xinli part numbers are hosted
the identical way, e.g. TCXD121IBLON-1, TCXD040IBLON-10, each
301-redirecting straight to its own PDF with no storefront around it).
Targeted searches found **no listing for this exact part number on
Digi-Key, Mouser, LCSC, Alibaba, or 1688** — nothing indicating an instant
small-quantity purchase path exists today. Avnet Embedded/Tria describes
its own business as OEM production-line integration and custom
display design/manufacturing, which in this industry segment typically
means sales-engineering-gated ordering, sometimes with MOQs from the low
hundreds to low thousands of units — but **no actual MOQ, lead time, or
small-quantity price for this specific part was found, in either
direction**. No separate Xinli company website or direct sales channel was
located either (only the Avnet-hosted datasheet and a secondhand
Made-in-China company-profile page). **Confidence: low** on whether this
part is practically orderable in hobbyist/small-batch quantities without
first having a sales conversation with Avnet/Tria (or Xinli directly) —
this is an open question for the next step, not a known-bad or known-good
answer.

**Net:** spec-wise this is a strict improvement over the Waveshare module
on every axis except contrast itself, where the two tie (both 900:1 typ,
on equally solid primary-source evidence): it's a true bare panel (solves
finding 6's integration gap) and uses the exact ST7789V driver already
planned (removes finding 4's V/V2 compatibility-verification risk
entirely). Sourcing is the one real unresolved variable.

### 8. Tailor Pixels TTH019BVS-01 — checked, no contrast figure found

Tailor Pixels (Shenzhen, tailorpixels.com) is a real display-module
manufacturer with a public marketing catalog. Its "Bar Serial" product
table lists **TTH019BVS-01**: diagonal 1.9", resolution 170x320, module
dimensions 25.80 x 49.72 x 1.43mm, active area 22.70 x 42.72mm, luminance
350 cd/m², display type IPS, interface listed simply as "MCU" — read
directly from Tailor Pixels' own catalog PDF
(tailorpixels.com/wp-content/uploads/2023/03/Catalog-TFT-LCDs-for-Smart-Home_Tailor-Pixels.pdf).
Those dimensions are identical, to rounding, to both the Xinli
TCXD019IBLON-78 (finding 7) and the Yousee YX19002A (finding 5) —
circumstantial evidence that several Chinese module houses build 1.9"
170x320 modules around the same OEM glass cell or a shared industry
form factor, not independent confirmation of any one vendor's contrast
figure.

**No contrast ratio was found anywhere for this part** — not in Tailor
Pixels' own marketing catalog (above), nor in DirectIndustry's listing
snippets. The manufacturer's full individual product-specification PDF
for this part
(pdf.directindustry.com/pdf/tailor-pixels-technology-co-ltd/product-specification-model-tth019bvs-01-19-tft-display-module-170-320/245050-1011078.html)
returned HTTP 403 (Cloudflare-blocked) on direct fetch and could not be
read even with the PDF-vision method that worked for Xinli's
Avnet-hosted datasheet (that method needs the PDF bytes served at all;
this one is blocked before that). **This is a real part from a real
manufacturer, but its contrast figure is simply unknown, not
low-confidence** — there is no number to disclose a confidence level
about. Not recommended on current evidence, and not worth re-attempting
with the same access path — noted here so a future pass doesn't repeat
this exact dead end.

## Recommendation

**Updated top recommendation: Xinli TCXD019IBLON-78** (finding 7) — a
true bare 1.9" 170x320 panel, 25.8 x 49.72 x 1.43mm, using the project's
already-planned **plain ST7789V** driver, with a primary-source datasheet
documenting a **900:1 typical / 700:1 minimum** contrast figure, verified
directly from the manufacturer's own specification PDF in this revision
(Zhejiang Xinli Optoelectronics, Ver 1.2, 2022-5-20) — not inferred from a
distributor index. It resolves both open problems the original Waveshare
recommendation carried: it's a bare panel (no breakout-module-vs-bare-panel
integration question, unlike finding 6's Waveshare gap), and it uses the
exact driver IC already planned for this project (no
ST7789-to-ST7789V2 register/init-sequence verification risk, unlike
finding 4's Waveshare caveat). Its FPC connector (0.5mm pitch, 14 pins)
matches the project's pitch assumption on the figures available.

**This recommendation carries one real, unresolved caveat, stated plainly
rather than minimized: sourcing.** No instant small-quantity purchase path
(a Digi-Key/Mouser/LCSC/Alibaba/1688 listing, or a vendor webshop) was
found for this exact part. The only trace is a datasheet hosted inside
Avnet Embedded/Tria Technologies' OEM display-module catalog, with no
price, stock, or quote mechanism visible on the page — consistent with a
sales-engineering-gated OEM channel that may carry a meaningful MOQ,
though no actual MOQ or lead-time figure was found either way. Before
committing PCB layout to this panel, **the next step should be a direct
inquiry to Avnet/Tria (reference part TCXD019IBLON-78) or to Xinli's own
channels** for real small-quantity pricing, MOQ, and lead time — this is
desk research, not a placed order, and that gap is not papered over here.

**Fallback / confirmed-orderable secondary pick: Waveshare 1.9" 170x320
ST7789V2 module** (SKU 23822/31122, finding 3) remains a solid choice if
the Xinli sourcing inquiry above doesn't pan out quickly: identical
shape/resolution to the baseline, a manufacturer-published 900:1 contrast
figure (the same number as Xinli's — a tie, not an improvement, now that
the earlier claim tying contrast to "being V2" has been retracted; see
finding 5) — and, critically, a **live, confirmed, direct-from-manufacturer,
single-unit "Add to Cart" purchase path today** (re-checked 2026-11-15:
$11.99 list, $11.59 at qty 1-9, down to $11.31 at 50-99, no listed 100+
tier). Its tradeoffs stand as documented in findings 3-6: it ships as a
breakout module, not the bare panel the hardware design doc assumes, and
its ST7789V2 driver, while expected to be compatible with the project's
existing ST7789 driver code, has not been confirmed register-identical to
plain ST7789V by any authoritative source.

**Correction from the previous version of this finding:** earlier drafts
stated or implied that the Waveshare panel's 900:1 contrast was
attributable to its ST7789V2 driver specifically, and that a
"driver-revision/panel pairing... drives the contrast difference." That
claim was wrong and is retracted throughout this document (see finding
5). **Contrast ratio is a property of the LC cell, polarizer, and
backlight stack — not something the driver IC sets.** Xinli's
TCXD019IBLON-78 (plain ST7789V, 900:1) and BuyDisplay's ER-TFT019-1 (plain
ST7789, 500:1) use the *same driver generation* and land 80% apart on
contrast — direct proof the driver IC is not the variable that matters.
The Waveshare panel happening to use ST7789V2 is incidental to its
contrast figure, not causal.

**Secondary lead checked and ruled out for now: Tailor Pixels
TTH019BVS-01** (finding 8) — a real bare 1.9" 170x320 panel from a real
manufacturer, dimensionally identical to the Xinli and Yousee parts, but
**no contrast figure could be found anywhere**, including the
manufacturer's own marketing catalog; its individual full spec PDF is
blocked behind Cloudflare and could not be read even with the PDF-vision
method that worked on Xinli's datasheet. Not recommended on current
evidence — flagged here so a future research pass doesn't repeat this
exact dead end without first finding a way past the access block.

As before: nothing in the "bar type" display product category (finding
1), and nothing found wider-than-baseline at the same height (finding 2),
beats — or even matches, with confirmable data — the panels above. Width
growth, while free in principle for this product, did not produce a
usable win in this research pass. The 480x272 DLC Display part (finding
2) is the closest near-miss but its contrast figure is unverified and its
height is a bigger jump than requested.

This is research only; the user makes the actual call (pursue the Xinli
sourcing inquiry, fall back to the Waveshare module now, or stay with the
current baseline) — no `.planning/decisions/` ADR was written, per this
bead's acceptance criteria.

## Verification performed vs. not performed

### Original research pass (2026-11-15)

- **Performed:** Live WebSearch queries and direct WebFetch reads of
  primary manufacturer pages (Waveshare's own product/spec-table pages,
  checked on three separate URLs for internal consistency, specifically
  re-verified after a mid-task flag that this was a strong lead;
  BuyDisplay's own listings; Newhaven's own bar-type product-highlight
  page; distributor pages at DigiKey, Mouser, RobotShop, Pi Hut, Abra
  Electronics) on 2026-11-15.
- **Not performed / caveats:** Several candidate datasheets (DLC
  DLC0430BCP12RF-1, DLC0190ADP04SF-1, CD Tech S019BQ01HN, Chenghao
  170x320) are encrypted or image/vector-heavy PDFs that could not be
  text-extracted in this environment — confirmed no `pdftotext` or
  Python PDF library (`pypdf`/`PyPDF2`/`fitz`) is installed here, the same
  limitation `pilink-maj`'s finding flagged. Those contrast figures are
  marked unverified above rather than used. The Abra Electronics stock
  link that search results surfaced returned 404 on direct re-check and
  was not relied on. The 900:1 figure for the non-touch SKU 23822
  specifically is inferred from the shared panel/driver, not
  independently re-stated on that SKU's own page — flagged above, not
  overstated. Distributor "Add to Cart"/no out-of-stock-notice readings
  are point-in-time (2026-11-15), not API-confirmed. No physical panel was
  obtained, no bare-FPC version of the ST7789V2/900:1 Waveshare panel was
  confirmed to exist — this is desk research only, as the bead scoped it.

### Revision pass (2026-11-15, responding to PR #12 review)

- **Performed:** Fetched Xinli TCXD019IBLON-78's actual datasheet PDF
  (hosted on Avnet Embedded's display catalog, embedded.avnet.com,
  redirecting to a CloudFront-hosted PDF) and read it directly with
  Claude's PDF-reading tool, which renders image-based PDF pages visually
  — this succeeded even though no `pdftotext`/`tesseract`/Python PDF
  library is installed in this environment (confirmed again: no `pip`
  binary, no passwordless `sudo` to `apt install` anything), the same
  tooling gap every PDF-related caveat in this research chain has hit.
  This capability was not tried by earlier passes in this bead chain.
  **Future passes should try reading a flagged "unverifiable/image-based"
  PDF this way before writing it off.** Also performed: searches across
  Digi-Key, Mouser, LCSC, Alibaba, and 1688 for the Xinli part number and
  company name (no listings found on any of them); a direct fetch of
  Avnet Embedded's homepage and several other Xinli-sourced product pages
  on the same site to characterize its business model (OEM display
  catalog, no price/stock/cart visible anywhere checked); a live re-fetch
  of Waveshare SKU 23822's page to correct the $11.31/100+ pricing error
  the review flagged; a fetch and partial read of Tailor Pixels' own
  marketing-catalog PDF (globalsources.com mirror) for TTH019BVS-01;
  confirmation that PR #11 merged and its finding file is now at
  `.research/findings/2026-11-15-display-alternatives-contrast.md` on
  master (checked via `git ls-tree origin/master`), so this finding's
  citation of it is to a file that already exists, not a hoped-for rename.
- **Not performed / caveats:** Xinli's FPC connector *contact orientation*
  (top- vs. bottom-contact) is not labeled in the extracted datasheet text
  — only pitch (0.5mm) and pin count (14) are confirmed; verify against
  the saved mechanical-drawing image or a physical sample before
  finalizing a connector part. No actual MOQ, lead time, or small-quantity
  price was found for the Xinli part from any source — reported as an
  open gap, not assumed in either direction. Shenzhen Yousee's YX19002A
  ~800:1 figure (raised in review) was not independently re-verified
  against Yousee's own full datasheet: the DirectIndustry-hosted PDF
  returned HTTP 403 (Cloudflare-blocked) and could not be fetched at all,
  so even the PDF-vision method couldn't be tried on it; it remains at the
  same distributor-listing-only confidence level the review flagged it
  at. Tailor Pixels' individual full specification PDF for TTH019BVS-01
  was likewise 403-blocked; only its own summary marketing catalog (which
  omits contrast) was readable. No company website or direct sales
  channel was found for Xinli itself, separate from the Avnet-hosted
  datasheet and a secondhand Made-in-China company-profile listing (used
  only for the founding-year/product-range claim, flagged as not
  independently audited). No physical panel of any part in this finding
  was obtained — this remains desk research only.

## Informs

A future `.planning/decisions/` ADR on which panel to adopt (user's call:
Xinli TCXD019IBLON-78, the Waveshare 170x320 ST7789V2 module, or the
current baseline), and depending on that choice, follow-up beads: (1) if
Xinli — a sourcing bead to get real MOQ/pricing/lead time from Avnet/Tria
or Xinli directly, plus a hardware bead to confirm the FPC connector's
contact orientation against the physical part or a cleaner mechanical
drawing before PCB layout; (2) if Waveshare — a hardware bead to resolve
the breakout-module-vs-bare-panel integration question before PCB layout,
and a firmware bead to verify/tune the ST7789V2 init sequence against the
project's existing ST7789 driver code. Out of scope for this
research-only bead.

Sources:
- https://www.digikey.co.za/en/product-highlight/n/newhaven-display/bar-type-ips-tft-displays (Newhaven's own Bar-Type IPS TFT product-highlight page — NHD-3.9-480128AF-ASXP 480x128, NHD-2.9-376960AF-ASXP 376x960/1,500:1 contrast, NHD-6.8-4801280AF-ASXP 480x1280; all wrong-aspect for this bead)
- https://www.mouser.in/en/new/microtips/microtips-awl-bar-type-tft-displays/ (Microtips AWL bar-type series — 400x960, 320x960, 240x960, 280x1424; narrow/tall "pen" bars, wrong shape)
- https://crystalfontz.com/product/cfaf480128a0052tn (Crystalfontz CFAF480128A0-052TN, 5.2" 480x128 bar display — height below 170px floor)
- https://www.buydisplay.com/bar-type-4-58-inch-320x960-ips-tft-lcd-display-spi-rgb-interface (BuyDisplay bar-type catalog, 4.58" 320x960 — wrong aspect)
- https://cnhzlh.en.alibaba.com/product/60800786242-802747290/AV123Z7M_N11_12_3_Stretched_Bar_Long_LCD_12_3_inch_TFT_LCD_Display_Module_1920x720_for_car_dashboard.html (BOE/OEM 12.3" automotive stretched-bar panel, 1920x720, ~2.67:1 — wrong aspect)
- https://densitron.com (Densitron automotive bar-type IPS, 1920x384, contrast 1000:1 per distributor copy — wrong aspect, not independently verified)
- https://www.digimax.it/media_import/DISPLAY/DLC%20DISPLAY/TFT%20LCD/DLC0430BCP12RF-1/DLC0430BCP12RF-1_DS_001.pdf (DLC0430BCP12RF-1, 4.3"/480x272, distributor-indexed 640/800 min/typ contrast — datasheet PDF encrypted/unreadable, unverified)
- https://www.waveshare.com/esp32-s3-lcd-1.9.htm (Waveshare ESP32-S3-LCD-1.9 board page, "LCD parameters" table: 170x320, ST7789V2, Contrast Ratio 900:1, Brightness 500 cd/m², SPI — primary recommendation)
- https://www.waveshare.com/1.9inch-touch-lcd.htm (Waveshare 1.9inch Touch LCD, SKU 31122: same 900:1/500cd/m² spec table, ST7789V2, CST816 touch IC, SH1.0/FPC0.5 connector options, $12.99 — primary recommendation)
- https://www.waveshare.com/1.9inch-lcd-module.htm (Waveshare 1.9inch LCD Module, SKU 23822 non-touch: 170x320, ST7789V2, MX1.25 connector, $11.99, live Add to Cart checked 2026-11-15 — primary recommendation)
- https://www.buydisplay.com/full-viewing-angle-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789 (BuyDisplay ER-TFT019-1/ER-TFTM019-1-SPI, bare 170x320 panel, plain ST7789 driver, Contrast Ratio Typ 500:1 — baseline re-confirmed, not beaten)
- https://support.newhavendisplay.com/hc/en-us/community/posts/4424919637399-ST7789V-and-ST7789VI-compatibility (forum evidence on ST7789V/V2 compatibility — "very possible," recommends hardware testing, no authoritative register-level diff found)
- docs/plans/2026-11-13-custom-hardware-design.md (project's already-chosen 1.9" ST7789V 320x170 baseline and the "bare panel + 0.5mm-pitch FPC connector" integration pattern this bead checks against)
- .research/findings/2026-11-15-display-alternatives-contrast.md (sibling finding — ~500:1 baseline for this panel class, and the wrong-shape 240x320 candidates this bead was launched to correct; renamed from `...-and-eink.md` when PR #11 merged, now on master)
- https://embedded.avnet.com/product/tcxd019iblon-78 (Avnet Embedded/Tria Technologies display catalog listing for Xinli TCXD019IBLON-78 — redirects straight to the datasheet PDF; no price/stock/quote mechanism found on the catalog)
- https://d7rh5s3nxmpy4.cloudfront.net/CMP7377/files/TCXD019IBLON-78_SPEC_V1.2_350cd.pdf (Xinli Optoelectronics' own primary-source datasheet for TCXD019IBLON-78, Ver 1.2, 2022-5-20 — read directly via PDF-vision extraction; source of the 900:1 typ/700:1 min contrast, plain-ST7789V driver, bare-panel outline, and 0.5mm-pitch 14-pin FPC figures in finding 7 — new top recommendation)
- https://www.directindustry.com/prod/shenzhen-yousee-technology-co-ltd/product-4621447-2851370.html and https://pdf.directindustry.com/pdf/shenzhen-yousee-technology-co-ltd/yousee-display-module-tft-lcd-yx19002a/4621447-1146121.html (Shenzhen Yousee YX19002A, 170x320 ST7789V, ~800:1 per distributor listing per review — full datasheet PDF blocked HTTP 403, contrast figure not independently re-verified, held at distributor-listing confidence)
- https://pdf.directindustry.com/pdf/tailor-pixels-technology-co-ltd/product-specification-model-tth019bvs-01-19-tft-display-module-170-320/245050-1011078.html (Tailor Pixels TTH019BVS-01 individual spec PDF — blocked HTTP 403, could not be read)
- https://tailorpixels.com/wp-content/uploads/2023/03/Catalog-TFT-LCDs-for-Smart-Home_Tailor-Pixels.pdf (Tailor Pixels' own marketing catalog — confirms TTH019BVS-01's size/resolution/dimensions but lists no contrast figure, finding 8)
