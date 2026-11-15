# Higher-contrast panel in the same wide-bar aspect ratio (320x170 class)

## Question

Follow-up to `pilink-maj`'s finding
(`.research/findings/2026-11-15-display-alternatives-contrast-and-eink.md`),
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
- **Stock / price (checked 2026-11-15):** Both pages show a live "Add to
  Cart" with no out-of-stock notice, sold direct from Waveshare: SKU 23822
  at $11.99 (bulk pricing down to $11.31 at the 50-99 tier; a 100+ tier
  row exists on the page but shows no price), SKU 31122 at $12.99
  (down to $11.97 at 50-99). One third-party reseller link (Abra
  Electronics) that search results surfaced for SKU 23822 returned HTTP
  404 on direct re-check — flagged as stale/unconfirmed, not relied on;
  Waveshare's own store page is the basis for the stock claim here.

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

### 5. Baseline re-confirmed, and where it doesn't improve

BuyDisplay's own bare-panel 170x320 SKUs (ER-TFT019-1 / ER-TFTM019-1-SPI,
buydisplay.com/full-viewing-angle-spi-1-9-inch-ips-tft-lcd-display-panel-170x320-st7789)
use the plain **ST7789** controller (not V2) and document **500:1**
typical contrast, 350 cd/m² — matching `pilink-maj`'s baseline exactly, not
beating it. This confirms the 900:1 figure is tied specifically to the
ST7789V2 variant Waveshare uses, not something every 170x320 panel in this
market offers — the choice of panel/driver pairing, not just the shape,
is what drives the contrast difference.

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

## Recommendation

**Waveshare 1.9" 170x320 ST7789V2 module** is the clearest find and the
top recommendation: identical shape and resolution to the already-chosen
baseline (170x320, 1.88:1 — exactly the look the user wants), same driver
family, and a manufacturer-published **900:1** contrast ratio — about 1.8x
the ~500:1 documented for the plain-ST7789 version of this same
panel/resolution class. Live, directly-orderable stock from Waveshare,
checked 2026-11-15: SKU 31122 (touch, $12.99) carries the 900:1 figure
directly on its own spec table and on the shared ESP32-S3-LCD-1.9 board
page; SKU 23822 (non-touch, $11.99) is the same panel/driver without the
touch overlay but doesn't independently restate the contrast number on its
own page — treat 900:1 as confirmed for the touch SKU/shared panel and
very likely (not independently re-confirmed) for the non-touch SKU.

The one real gap: it ships as a breakout module, not the bare FPC panel
the hardware design doc assumes — that integration question (sub-module
vs. true bare panel) needs resolving before PCB layout, and is a natural
follow-up hardware bead if this panel is chosen.

As secondary/stretch options: nothing in the "bar type" display product
category, and nothing found wider-than-baseline at the same height
(360-480 x 170-200ish), beats — or even matches, with confirmable data —
this result. Say so plainly: width growth, while free in principle for
this product, did not produce a usable win in this research pass. The
480x272 DLC Display part (finding 2) is the closest near-miss but its
contrast figure is unverified and its height is a bigger jump than
requested. The contrast win came from a better driver-revision/panel
pairing at the *same* already-chosen size, not from changing shape or
size.

This is research only; the user makes the actual call (adopt this
module, pursue a bare-panel version directly with Waveshare, or stay with
the current baseline) — no `.planning/decisions/` ADR was written, per
this bead's acceptance criteria.

## Verification performed vs. not performed

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

## Informs

A future `.planning/decisions/` ADR on whether to adopt the Waveshare
170x320 ST7789V2 module (user's call), and if so, two follow-up beads:
(1) a hardware bead to resolve the breakout-module-vs-bare-panel
integration question with Waveshare before PCB layout, and (2) a firmware
bead to verify/tune the ST7789V2 init sequence against the project's
existing ST7789 driver code. Out of scope for this research-only bead.

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
- .research/findings/2026-11-15-display-alternatives-contrast-and-eink.md (sibling finding — ~500:1 baseline for this panel class, and the wrong-shape 240x320 candidates this bead was launched to correct)
