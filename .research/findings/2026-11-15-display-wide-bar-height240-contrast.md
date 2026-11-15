# Wide-bar display panels with height >= 240px (no height loss vs. the old panel)

## Question

Follow-up to `pilink-4mq`'s finding
(`.research/findings/2026-11-15-display-wide-bar-aspect-contrast.md`), which
found two good 170-height candidates (Xinli TCXD019IBLON-78 bare panel and
Waveshare's 1.9" 170x320 ST7789V2 module, both 900:1 contrast) but kept the
project's already-chosen baseline's 170px height. The user has clarified the
real constraint: height must be **>= 240px**, matching the OLD Waveshare
Pico-LCD-1.3 panel (240x240) this project replaces — the 170px height of the
1.9"/320x170 baseline was an accepted tradeoff in the original hardware
design doc, not a floor to keep re-litigating downward. The user explicitly
does **not** want a return to a square 240x240 panel either — they like the
wide/rectangular "bar" look, just with no vertical-resolution loss versus
the old panel. Width is free to grow (300, 320, 360, 400, 480+ all fine).

This finding searches for real, sourceable, LCD/IPS-class (not OLED, not
e-ink) panels at width x height>=240 that read as a genuine wide/rectangular
bar, prioritizing ST7789/ILI9341-family SPI compatibility where possible,
and disclosing honestly if the best height>=240 options need a different
driver or interface entirely. Contrast is compared against both baselines
already established: ~500:1 (general baseline, `pilink-maj`) and 900:1 (best
170-height candidates, `pilink-4mq`).

## Findings

### 1. Why no genuine 400x240 / 480x240 ST7789-family SPI panel exists

Sitronix's ST7789/ST7789V/ST7789V2 family has a fixed internal GRAM/addressing
capacity of 240 x 320 pixels (76,800 px) — every real ST7789-driven product
found anywhere in this research chain and its predecessors tops out at
240x320 (or 320x240 when read out rotated — see finding 2). Searches for
"400x240 ST7789", "480x240 ST7796", and "480x240 ILI9488" SPI modules
returned no matching product from any vendor checked (BuyDisplay, Orient
Display, Newhaven, DisplayModule, Elecrow, 4D Systems, Crystalfontz). The
two Sitronix/ILI chips with larger native capacity both cap out at 320x480
(portrait) / 480x320 (landscape), not 480x240 or 400x240:

- ST7796S datasheet: "320RGB x 480 dot format"
  (dl.espressif.com/dl/schematics/ST7796S_SPEC_V1.0.pdf).
- ILI9488 datasheet: "320(RGB) x 480 Resolution... With Internal GRAM"
  (elecrow.com/download/product/DLS24035B/ILI9488%20Data%20Sheet.pdf).

Every real ST7796S/ILI9488 SPI module found (Elecrow 4.0" 480x320, various
3.5" 320x480 IPS modules) is landscape-480x320 or portrait-320x480 — a
bigger jump in both dimensions than this bead asked for, not a 480x240 or
400x240 part. **No vendor sells a genuine 400x240 or 480x240 bare/SPI panel
in the ST7789/ST7796/ILI9341/ILI9488 family** — this is a real gap, not an
oversight in searching.

### 2. Primary recommendation: physically rotate a 240x320 ST7789-family panel 90 degrees to get 320x240, height=240 exactly

**The key mechanism, verified:** ST7789/ILI9341-family controllers (and the
whole MIPI-DCS lineage they implement) support a Memory Data Access Control
(MADCTL) register with a Row/Column-Exchange bit (commonly called "MV")
that swaps which physical axis is read out as rows vs. columns — this is
how the exact same 240-wide x 320-tall glass can be addressed in firmware as
a 320-wide x 240-tall display, with the panel **physically mounted rotated
90 degrees** in the enclosure. This is standard, widely-used behavior, not
a theory: the Linux kernel's `fb_st7789v.c` framebuffer driver (for this
exact chip) hard-codes the MV/MX/MY bit combinations for 0/90/180/270-degree
rotation
(elixir.bootlin.com/linux/v4.4/source/drivers/staging/fbtft/fb_st7789v.c;
mirrored at sources.debian.org and several other kernel source trees).
Direct extraction of the bit table from the Sitronix ST7789V PDF itself
was not possible in this environment (same PDF-text-extraction limitation
flagged throughout this research chain), so this is corroborated via a real,
shipping driver implementation for this specific chip rather than the raw
datasheet text — a reasonable confidence level for a MIPI-DCS-standard
feature, not a speculative claim.

**What this means for the bead:** every 240x320 ST7789-family candidate the
sibling finding already surveyed and rejected for being "portrait-ish"
can instead be physically rotated 90 degrees in the enclosure, giving a true
320x240 **landscape** panel with **height exactly 240px** — matching the old
Pico-LCD-1.3's height with zero loss, while still reading as a rectangular
(non-square) bar. The only costs are mechanical, not electrical: the FPC
tail moves from what was a short edge to a different position relative to
the enclosure cutout (a layout consideration, not a new part), and the
panel is physically bigger than the current 1.9"/320x170 baseline (2.0"-2.4"
diagonal vs. 1.9"), meaning an enclosure/bezel rework either way.

**Top pick: Newhaven NHD-2.4-240320AF-CSXP, Rev2B — 1500:1 typ / 800:1 min contrast**

This part was already found and sourced by the sibling finding
`pilink-maj` (`.research/findings/2026-11-15-display-alternatives-contrast.md`,
finding 3) as the single best-documented contrast figure across all prior
research passes — it was previously set aside only because its native
240x320 shape read as "portrait-ish," not because of any flaw in the part
itself. Rotated 90 degrees, it becomes exactly what this bead asks for:

- **Resolution (rotated):** 320 x 240, height exactly at the 240px floor.
- **Driver IC:** ST7789VI — same Sitronix ST7789 family already planned.
- **Contrast ratio: 1500:1 typical / 800:1 minimum**
  (newhavendisplay.com/content/specs/NHD-2.4-240320AF-CSXP.pdf) — roughly
  **3x the general ~500:1 baseline** and **~1.7x the best 170-height figure
  (900:1)** found anywhere in this research chain. This is the strongest
  contrast number found across all three findings in this bead chain.
- **Luminance:** 1200 cd/m2 typ, "High Brightness/Sunlight Readable,"
  normally-black, anti-glare, transmissive.
- **Interface revision caveat (re-confirmed from the sibling finding, still
  applies):** the original board revision (Rev2A) is 3-wire SPI only; a
  later Rev2B (per Newhaven's 2025-06-17 engineering change notice) adds
  4-wire SPI support, matching the project's existing 4-wire-SPI firmware
  with a dedicated D/C pin. Confirm Rev2B specifically before ordering.
- **Stock (re-checked from sibling finding, point-in-time 2026-11-15, not
  re-verified live in this pass):** DigiKey part 22204988 — 7 units
  on-hand, 18-week manufacturer lead time. Fine for a couple of prototype
  units, not for assuming volume availability without a direct quote.
- **Physical size / enclosure impact:** 2.4" diagonal, meaningfully bigger
  than the 1.9" baseline — this candidate requires an enclosure cutout/bezel
  rework, not a drop-in swap. That rework is out of scope for this
  research-only bead (a follow-up hardware bead, as the sibling finding
  already noted).

**Aspect-ratio honesty check:** 320:240 = 1.33:1. This is a real,
unambiguous rectangle (clearly wider than tall), but it is noticeably closer
to square than the project's chosen 1.9"/320x170 baseline (1.88:1) or the
LilyGo T-Embed look that originally motivated the "bar" preference. It is
NOT dramatically "bar"-like the way 1.7-1.9:1 reads. Whether 1.33:1 still
satisfies the user's stated preference for a rectangular bar (vs. feeling
too close to the old 240x240 square) is a genuine judgment call for the
user — this finding states the number plainly rather than asserting it
clearly passes.

**Alternative with zero driver-revision risk: Display Visions EA-TFT020-23AINN**

Also previously found by the sibling finding (same doc, finding 4) and also
rejected only for shape. Rotated 90 degrees: 320x240, **exact plain
ST7789V** driver (identical to the project's baseline driver, not even a
V-to-V2 or V-to-VI compatibility question), **800:1 typ / 640:1 min**
contrast (mouser.lt/pdfDocs/TFT020-23AI-1594147.pdf) — still clearly above
both the 500:1 and (tied with) the 900:1 baselines. Smaller panel (2.0"
diagonal) than the Newhaven option, a smaller enclosure-rework jump. Main
open issue, unchanged from the sibling finding: the non-touch part's
(EA-TFT020-23AINN, RS Components 221-1845) stock could not be confirmed —
regional RS listings disagreed and a live recheck returned a server error
in that pass; this was not independently re-verified in this pass either.

**Checked and flagged as a mid-confidence option, not relied on: 4D Systems 4DLCD-24320240-IPS**

New in this pass. 2.4", 240x320, IPS, **800:1 contrast** per 4D Systems'
own Revision 1.5 datasheet
(mouser.com/datasheet/2/451/4DLCD_24320240_IPS_Series_Datasheet_R_1_5-2448899.pdf),
320 cd/m2 luminance, 80-degree viewing angle, real RS Components stock
listing (RS 2309319). **Driver IC is batch-dependent, confirmed from the
same datasheet:** ST7789V on IPS units manufactured from 2021-06-20, but
**ILI9341V on all IPS units from 2023-07-17 onward** — meaning any unit
ordered new today is very likely ILI9341V, not ST7789V. ILI9341 is still a
well-supported SPI/MIPI-DCS-family driver with the same MADCTL rotation
mechanism (finding 2's rotation trick applies equally), so this is not a
disqualifying problem, but it is not the "identical driver family, zero
porting" option it might first appear to be — budget the same kind of
bring-up effort as porting to a new-but-related chip, not zero effort.
Stock/price were not re-checked live in this pass.

### 3. Wider/more dramatic bar, still a real SPI-pixel-capable bare panel: DisplayModule DM-TFT30-407 (3.0", 240x400, ST7796S), rotated to 400x240

This is a new find in this pass, verified directly against its own
primary-source datasheet (read page-by-page via PDF-vision extraction after
the file's raw text was unreadable in this environment — the same tooling
gap `pilink-4mq` already documented and the same workaround it found).

- **Part number:** DisplayModule DM-TFT30-407, "3.0\" 240 x 400 Display
  Panel with Capacitive Touch - SPI, MCU, RGB."
- **Driver IC: ST7796S** — Sitronix's larger-capacity sibling to the
  project's planned ST7789V, confirmed directly in the datasheet's "Main
  Features" table ("Controller IC: ST7796S").
- **Interface — confirmed to be true pixel-data-capable SPI, not
  register-only:** Section 6.5.2 ("3-SPI Serial Interface Timing
  Characteristics") and 6.5.3 ("4-SPI Serial Interface Timing
  Characteristics") both document full command-and-pixel-data transfer over
  3-wire or 4-wire SPI (the 4-SPI table explicitly labels its serial-clock
  rows "write command & data ram" / "read command & data ram") — this is
  the same GRAM-push model as ST7789, not the register-only SPI + mandatory
  parallel-RGB-stream pattern found in finding 4 below. A real alternate
  option for this panel: 8/9/16/18-bit MCU or RGB interfaces also exist on
  the same chip, but are not required — the SPI path alone can drive it.
- **Resolution (native):** 240(RGB) x 400 — portrait. Rotated 90 degrees
  (finding 2's mechanism, which applies to ST7796S the same way, part of
  the same MIPI-DCS MADCTL convention): **400 x 240, height exactly at the
  240px floor**, aspect **1.67:1** — visibly more "bar"-like than the
  rotated-240x320 options above, closer to (though still short of) the
  1.88:1 baseline look.
- **Contrast ratio: 600:1 typical**, confirmed directly from the
  datasheet's Section 6.1 Optical Characteristics table ("Contrast Ratio
  CR - 600 - -"). This beats the ~500:1 general baseline, but is below
  both the 900:1 (170-height) and the 1500:1 rotated-Newhaven figures above.
- **Physical form factor:** active area 38.88 x 64.8mm, panel dimension
  45.04 x 77 x 3.85mm (datasheet Section 2) — a true bare panel with an FPC
  tail (45-pin), matching the project's "bare panel + FPC connector"
  integration pattern, not a breakout-module mismatch like the Waveshare
  170x320 candidate carried in the sibling finding.
- **Touch:** bundled FT6336G capacitive touch controller over I2C — not
  required by the project, but present; can be left unconnected.
- **Luminance:** 350 cd/m2 typ (4-chip white LED backlight, Section 6.4).
- **Price / stock:** $59 (capacitive-touch SKU) per DisplayModule's own
  product page; the page did not return current stock/availability in this
  pass (a repeat request hit an HTTP 429 rate limit) — **stock is
  unconfirmed, flagged honestly rather than assumed either way**.
- **Driver-porting cost, stated honestly:** ST7796S is a related but
  distinct Sitronix chip from ST7789V/V2/VI — not a register-identical
  drop-in. Expect comparable bring-up work to porting to the ILI9341V 4D
  Systems candidate above (new init sequence, gamma table, and
  command-table verification against the existing ST7789 driver code) —
  real work, but an ordinary new-panel bring-up, not an architecture
  change (unlike finding 4's RGB-interface panels, which would be).

### 4. Checked and not recommended on current evidence: the 480x272 RGB-parallel family

480x272 is a well-established small-TFT resolution and real parts exist in
roughly the target shape (1.76:1, height 272px, clears the 240px floor) —
but every one checked uses a driver IC that is fundamentally **not** a
drop-in SPI-pixel-push part like ST7789, and this distinction is confirmed
directly from the controller's own datasheet in this pass, not assumed.

**Sitronix SC7283** (the driver behind the Newhaven NHD-4.3-480272EF-ASXP
and the Displaytech DT043CTFT-IPS, among others) was read directly from its
own Sitronix datasheet
(orientdisplay.com/pdf/SC7283.pdf, via its mirrored copy, read with the
PDF-vision method after the raw file proved unreadable as text):

- Its "3-Wire SPI / I2C Interface Pins" (CS, SDA, SCL, SPI_I2C_SEL) are a
  **separate pin group** from its "Input Interface Pins" (DR[7:0], DG[7:0],
  DB[7:0], DCLK, HSYNC, VSYNC, DE) — confirmed directly from Section 6.1's
  pin table.
- The SPI pins only reach the chip's **Register List** (Section 8):
  contrast, brightness, gamma, and power-supply trim registers — there is
  **no SPI pixel-data path**. Actual image content must arrive continuously
  over the RGB interface pins, in either 24-bit parallel or 8-bit "serial
  RGB" mode (Section 7.3) — and even the 8-bit "serial" mode still requires
  DCLK, HSYNC, VSYNC, and DE as separate, continuously-clocked signals
  (Section 7.3.5's own timing table: Fclk 24-30MHz for the 480x272
  resolution), not a single SPI bus carrying a full frame into an on-glass
  frame buffer.
- **This chip has no internal frame memory to hold a static image** — unlike
  ST7789 (which has a GRAM you push a frame into once and it holds the
  image with no further bus traffic), SC7283-class RGB-interface
  controllers require the host to **continuously stream the frame** for as
  long as the display is on. For this device's 24/7 near-static-content use
  case, that is a real, ongoing bus/power/CPU cost difference from the
  project's planned SPI approach, not just a different one-time init
  sequence.
- **DigiKey's own "Interface: SPI" label on the Displaytech DT043CTFT-IPS
  listing is misleading in this light** — it almost certainly refers to the
  SC7283's register-configuration SPI pins, not a pixel-data SPI path; this
  finding does not take that distributor field at face value, per the
  verification standard this research chain has held itself to since the
  sibling findings' review rounds.

**Integration cost on RP2350, stated honestly:** the RP2350 has no
dedicated parallel-RGB/DPI display peripheral (confirmed via Waveshare's
own RP2350 RGB-panel dev boards — e.g. RP2350-Touch-LCD-2.8C and
RP2350-Touch-LCD-2.1, both RGB-interface panels driven via the RP2350's PIO
state machines, not a hardware RGB controller). Driving a 480x272
RGB-interface panel from this project's RP2350B would mean either:
(a) bit-banging the RGB bus via PIO — a real GPIO cost (12+ pins for 8-bit
serial RGB with sync lines, 24+ for full parallel RGB, versus the ~4-6 pins
a 4-wire-SPI ST7789 panel needs today) plus continuous PIO/DMA bandwidth
for the life of the display, a nontrivial firmware undertaking; or
(b) adding an external RGB-to-SPI/parallel bridge chip (e.g. RA8875,
SSD1963) as a new BOM part with its own driver — a real cost and complexity
increase, not merely "a different init sequence." This is categorically
different from, and larger than, the ST7789-to-ST7789V2/ILI9341/ST7796S
bring-up costs disclosed in findings 2 and 3 above.

**Contrast numbers in this class, for completeness:**

- Newhaven NHD-4.3-480272EF-ASXP: **640 min / 800 typ** contrast,
  480x272, IPS, SC7283, 24-bit parallel RGB
  (mouser.com/datasheet/2/291/NHD_4_3_480272EF_ASXP-2953309.pdf — figure
  read from a search-indexed table extract of this PDF, not an independent
  direct fetch in this pass; held at a correspondingly lower confidence
  than the directly-read DM-TFT30-407 and SC7283 figures above). Real
  DigiKey stock confirmed live: part 16577946, **1,419 units in stock**
  (digikey.com/en/products/detail/newhaven-display-intl/NHD-4-3-480272EF-ASXP/16577946).
- Displaytech DT043CTFT-IPS: same 640/800 contrast figures (Mouser-hosted
  datasheet 3371708), same SC7283 driver, 480x272, confirmed live DigiKey
  stock: part 22229627, **23 units in stock**, ~$27/unit at qty 1.
- BuyDisplay ER-TFT043A4-3 family: **500:1 typ** (ties, does not beat, the
  general baseline) — BuyDisplay's own product page lists multiple
  interface variants (SPI/I2C/parallel) for this 480x272 IPS panel but does
  not clearly state the controller IC on the page itself ("IC or
  Equivalent: N/A"); given the product class, it most likely follows the
  same register-only-SPI-plus-mandatory-RGB-data pattern as the parts
  above, but this specific BuyDisplay SKU's controller was not
  independently confirmed in this pass.
- Sibling-finding context, re-stated for comparison: this 800:1 ceiling in
  the 480x272 class is **below** the 1500:1 rotated-Newhaven figure (finding
  2) and only barely above the already-available 900:1 figure at 170px
  height (`pilink-4mq`) — the 480x272 family does not offer a contrast win
  large enough to justify its real interface-architecture cost, on the
  evidence gathered here.

## Recommendation

**Primary: physically mount a 240x320 ST7789-family panel rotated 90
degrees — Newhaven NHD-2.4-240320AF-CSXP, Rev2B (finding 2).** This is the
strongest result in this entire research chain: **1500:1 typical / 800:1
minimum contrast** (3x the general baseline, ~1.7x the best 170-height
figure found anywhere), on the exact Sitronix ST7789 driver family already
planned, at **exactly 240px height — zero loss versus the old Pico-LCD-1.3
panel**. The real costs, stated plainly: (1) it is a 2.4" panel, bigger than
today's 1.9" baseline, so this is an enclosure/bezel rework, not a drop-in;
(2) current stock is thin (7 units/18-week lead per the sibling finding's
live check) — fine for prototypes, needs a real quote for volume; (3) its
rotated aspect ratio, 1.33:1, is a real but modest bar — noticeably closer
to square than the project's chosen 1.88:1 look, and the user should judge
for themselves whether that still satisfies "rectangular bar, not square."
Display Visions EA-TFT020-23AINN (also rotated, finding 2) is a smaller,
lower-contrast (800:1 typ) fallback with the advantage of using the exact
plain ST7789V driver already in use, if the Newhaven stock/lead-time or
size increase is a dealbreaker.

**Secondary, if a more dramatic/visibly-wider bar matters more than
maximum contrast: DisplayModule DM-TFT30-407, rotated 240x400 -> 400x240
(finding 3).** Real bare panel (matches the project's FPC-tail integration
plan), genuinely SPI-pixel-capable (full frame over 3- or 4-wire SPI, not
register-only), **height exactly 240px**, aspect **1.67:1** — a clearly
wider, more "bar"-reading shape than the rotated-320x240 option, approaching
the baseline's 1.88:1 look. Contrast is more modest: **600:1 typical**,
confirmed directly from its own datasheet — beats the ~500:1 general
baseline but sits below both the 900:1 (170-height) and 1500:1
(rotated-Newhaven) figures. Its driver, ST7796S, is a related-but-distinct
Sitronix chip from the project's planned ST7789V — expect a normal new-panel
bring-up (init sequence, gamma table) comparable to the ILI9341V porting
effort already disclosed for the 4D Systems candidate, not an architecture
change. Stock was not confirmed live in this pass (a repeat fetch hit a
rate limit) — check before committing.

**Not recommended: the 480x272 RGB-parallel family (finding 4)**, despite
being real, in-stock (Newhaven ASXP: 1,419 units; Displaytech: 23 units),
and landing in a genuinely wide-bar aspect (1.76:1) with height clearing the
floor (272px). Its best confirmed contrast (800:1) does not beat the
170-height class's existing 900:1 figure and sits well below the
rotated-Newhaven option's 1500:1 — while its integration cost is real and
categorically larger than a driver swap: these SC7283-class controllers
have no on-glass frame buffer and require continuously-streamed RGB pixel
data, which the RP2350 can only provide via PIO-bitbanged GPIO (a much
larger pin/firmware commitment than 4-wire SPI) or an added RGB-bridge chip.
Given a same-or-better contrast number is available at height=240 (the
rotated Newhaven option) without that interface cost, this family is not
worth its tradeoff on current evidence.

**No genuine 400x240 or 480x240 bare/SPI panel exists in the
ST7789/ST7796/ILI9341/ILI9488 family (finding 1)** — say this plainly rather
than stretching a near-miss. The two realistic paths to height>=240 with a
wide-bar shape are: rotate an existing portrait SPI panel 90 degrees
(findings 2-3, recommended above), or accept a parallel/serial-RGB
controller and its firmware cost (finding 4, not recommended here).

This is research only; the user makes the actual call (rotated-240x320 vs.
rotated-240x400 vs. staying at the 170-height baseline vs. accepting the
480x272 RGB-interface cost) — no `.planning/decisions/` ADR was written by
this bead, per its acceptance criteria.

### Comparison against the 170-height candidates (`pilink-4mq`)

| Candidate | Height | Aspect | Driver / interface | Contrast | Stock (point-in-time) |
|---|---|---|---|---|---|
| Xinli TCXD019IBLON-78 (170h) | 170 | 1.88:1 | plain ST7789V, SPI, bare panel | 900:1 typ / 700 min | No instant-buy channel found; OEM-catalog only |
| Waveshare 1.9" module (170h) | 170 | 1.88:1 | ST7789V2, SPI, breakout module | 900:1 | Confirmed live "Add to Cart," $11.99+ |
| **Newhaven NHD-2.4, rotated (this bead)** | **240** | **1.33:1** | **ST7789VI, SPI (Rev2B), bare-ish panel** | **1500:1 typ / 800 min** | **7 units, 18-wk lead (DigiKey)** |
| EA-TFT020-23AINN, rotated (this bead) | 240 | 1.33:1 | plain ST7789V, SPI | 800:1 typ / 640 min | Unconfirmed (regional disagreement) |
| 4D Systems 4DLCD-24320240-IPS, rotated (this bead) | 240 | 1.33:1 | ST7789V (old stock) / ILI9341V (new stock), SPI | 800:1 | Live RS listing, not re-checked this pass |
| **DM-TFT30-407, rotated (this bead)** | **240** | **1.67:1** | **ST7796S, true SPI (3/4-wire)** | **600:1 typ** | **Unconfirmed (rate-limited this pass)** |
| NHD-4.3-480272EF-ASXP (this bead) | 272 | 1.76:1 | SC7283, parallel/serial RGB only, no frame buffer | 640 min / 800 typ | 1,419 units (DigiKey) |

**Net tradeoff:** going from 170px to 240px height does not have to cost
contrast — the rotated Newhaven option *gains* contrast (1500:1 vs. 900:1)
at the price of a bigger enclosure cutout and thinner current stock. Going
wider still (400x240, 1.67:1) costs some of that contrast back (600:1) in
exchange for a visibly more dramatic bar shape. Going to a genuinely wide
native-landscape 480-class panel (480x272, 1.76:1) costs a real interface
architecture change (RGB streaming, no frame buffer) for a contrast number
that doesn't even clearly beat the rotated-240x320 pick.

## Verification performed vs. not performed

- **Performed:** Live WebSearch queries across BuyDisplay, Orient Display,
  Newhaven, DisplayModule, Elecrow, 4D Systems, Crystalfontz, Waveshare,
  DigiKey, Mouser, and RS Components for 400x240/480x240/480x272/320x240
  resolutions in the ST7789/ST7796/ILI9341/ILI9488/SC7283 driver families,
  2026-11-15. Direct WebFetch/PDF-vision reads of primary-source datasheets:
  the Sitronix SC7283 datasheet (orientdisplay.com mirror, read page-by-page
  after raw-text extraction failed, same tooling gap documented in
  `pilink-4mq`) confirming its RGB-interface-only pixel-data path; the
  DisplayModule DM-TFT30-407 datasheet (cdn.shopify.com, same PDF-vision
  method) confirming its ST7796S driver, true SPI pixel-data path, 600:1
  contrast, and physical dimensions; a direct DigiKey fetch of the
  Displaytech DT043CTFT-IPS listing (driver IC, interface label, 23-unit
  stock, price) and a direct DigiKey fetch for the NHD-4.3-480272EF-ASXP
  listing (driver, interface, 1,419-unit stock). The ST7789/ILI9341 MADCTL
  row/column-exchange (MV bit) rotation mechanism was corroborated via the
  Linux kernel's `fb_st7789v.c` driver source, which hard-codes this exact
  chip's MV/MX/MY bit values for 0/90/180/270-degree rotation — a real
  shipping implementation for this chip, not a generic claim.
- **Not performed / caveats:** The raw ST7789V/ST7789VI/ILI9341/ST7796S
  datasheet PDFs could not be text-extracted directly in this environment
  (confirmed again: no `pdftotext`, `pdftoppm`, or Python PDF library
  installed, the same limitation every prior finding in this chain has
  hit) — the MADCTL/MV-bit claim rests on the Linux kernel driver
  implementation rather than a direct read of the Sitronix datasheet's own
  register table; this is corroborating evidence from a real deployed
  driver for the specific chip, not a primary manufacturer document, and is
  flagged at that confidence level. The Newhaven NHD-2.4-240320AF-CSXP and
  Display Visions EA-TFT020-23AINN contrast/stock figures are carried
  forward from `pilink-maj`'s live checks on 2026-11-15, not independently
  re-verified live in this pass — point-in-time stock numbers in particular
  should be re-checked before ordering. The NHD-4.3-480272EF-ASXP's exact
  640/800 contrast figure came from a WebSearch-indexed extract of its
  Mouser-hosted PDF rather than a direct fetch of that specific document in
  this pass (the direct fetch of that URL timed out); its DigiKey stock
  figure, by contrast, was independently re-confirmed via a direct live
  fetch. DisplayModule's own product page for DM-TFT30-407 could not be
  re-fetched for live stock status in this pass (HTTP 429 rate limit on a
  second request) — price ($59) came from a WebSearch snippet of the same
  page, not a direct fetch; stock status is genuinely unknown, not assumed.
  The BuyDisplay ER-TFT043A4-3 family's exact driver IC was not confirmed
  from a primary datasheet in this pass (BuyDisplay's own product pages
  return HTTP 403 to direct fetch, consistent with prior findings' notes on
  this vendor) — its RGB-interface-only characterization is an inference
  from the product class, flagged as such, not a confirmed fact for that
  specific SKU. No physical panel of any part in this finding was obtained,
  and no rotated-mounting of any of these panels was physically tested —
  this is desk research only, as the bead scoped it. The 4D Systems
  4DLCD-24320240-IPS candidate's current live stock/price was not
  re-checked in this pass (carried forward only as a shape/driver data
  point from its own datasheet).

## Informs

A future `.planning/decisions/` ADR on which panel/orientation to adopt
(user's call: stay at the 170-height baseline, the rotated-320x240 Newhaven
option, the rotated-400x240 DM-TFT30-407 option, or accept the 480x272
RGB-interface cost) — out of scope for this research-only bead. Depending
on that choice, follow-up beads: (1) if a rotated ST7789-family panel is
chosen — an enclosure bead to redesign the display cutout/bezel around the
new physical size and the FPC tail's new edge position, and a firmware bead
to confirm the MADCTL rotation bits against the real hardware (this
research found strong corroborating evidence the feature exists and works
for this chip family, but it was not bench-tested here); (2) if
DM-TFT30-407 (ST7796S) is chosen — a firmware bead to port/verify the
ST7796S init sequence and gamma table against the project's existing
ST7789 driver code, plus a sourcing check for its actual current stock;
(3) if the 480x272 RGB-interface family is chosen despite the cost flagged
here — a hardware/firmware bead to scope the PIO-bitbang-vs-bridge-chip
decision and its GPIO/BOM impact before committing PCB layout. Out of scope
for this research-only bead.

Sources:
- https://dl.espressif.com/dl/schematics/ST7796S_SPEC_V1.0.pdf (Sitronix ST7796S datasheet cover/features page — confirms 320RGB x 480 dot native format, used to establish why no 480x240/400x240 native panel exists in this family)
- https://www.elecrow.com/download/product/DLS24035B/ILI9488%20Data%20Sheet.pdf (ILI9488 datasheet — confirms 320(RGB) x 480 native resolution with internal GRAM, same point as above)
- https://elixir.bootlin.com/linux/v4.4/source/drivers/staging/fbtft/fb_st7789v.c and https://sources.debian.org/src/linux/4.19.194-1/drivers/staging/fbtft/fb_st7789v.c (Linux kernel ST7789V framebuffer driver source — hard-codes MADCTL MV/MX/MY bit values for 0/90/180/270-degree rotation on this exact chip; basis for finding 2's rotation mechanism)
- https://newhavendisplay.com/content/specs/NHD-2.4-240320AF-CSXP.pdf (Newhaven NHD-2.4-240320AF-CSXP datasheet, contrast ratio min 800 / typ 1500:1, 1200 cd/m2 — primary recommendation when rotated; figure carried forward from `pilink-maj`)
- https://www.digikey.com/en/products/detail/newhaven-display-intl/NHD-2-4-240320AF-CSXP/22204988 (DigiKey part 22204988, 7 units in stock / 18-week lead, per `pilink-maj`'s 2026-11-15 live check, not re-verified live in this pass)
- https://support.newhavendisplay.com/hc/en-us/articles/32880668716695-06-17-25-NHD-2-4-240320AF-CSXP (Newhaven engineering change notice: Rev2B adds 4-wire SPI support, required for this project's firmware)
- https://www.mouser.lt/pdfDocs/TFT020-23AI-1594147.pdf (Display Visions/EA TFT020-23AI family datasheet, 2.0" 240x320 ST7789V, contrast ratio min 640 / typ 800:1 — rotated alternative, exact baseline driver)
- https://www.mouser.com/datasheet/2/451/4DLCD_24320240_IPS_Series_Datasheet_R_1_5-2448899.pdf (4D Systems 4DLCD-24320240-IPS Rev 1.5 datasheet — 800:1 contrast, and the ST7789V-pre-2021-06-20 vs. ILI9341V-post-2023-07-17 driver IC note)
- https://cdn.shopify.com/s/files/1/0264/7629/files/DM-TFT30-407_Datasheet.pdf (DisplayModule DM-TFT30-407 primary datasheet, read directly via PDF-vision extraction in this pass — source of the ST7796S driver ID, true 3-/4-wire SPI pixel-data interface, 600:1 typ contrast, and physical/active-area dimensions)
- https://www.displaymodule.com/products/3-inch-ips-display-240x400-capacitive-with-mcu-spi-rgb (DisplayModule DM-TFT30-407 product page — $59 price point via search snippet; live stock not confirmed, direct fetch rate-limited in this pass)
- https://www.orientdisplay.com/pdf/SC7283.pdf (Sitronix SC7283 datasheet, read directly via PDF-vision extraction in this pass — source of the register-only-SPI / mandatory-continuous-RGB-data-path finding underpinning finding 4's "not recommended" call)
- https://www.mouser.com/datasheet/2/291/NHD_4_3_480272EF_ASXP-2953309.pdf (Newhaven NHD-4.3-480272EF-ASXP datasheet — 640 min / 800 typ contrast figure, via search-indexed extract, not independently re-fetched directly in this pass)
- https://www.digikey.com/en/products/detail/newhaven-display-intl/NHD-4-3-480272EF-ASXP/16577946 (DigiKey part 16577946, 1,419 units in stock, confirmed live 2026-11-15)
- https://www.mouser.com/datasheet/2/1015/DT043CTFT_IPS_Displaytech_Spec-3371708.pdf and https://www.digikey.co.uk/en/products/detail/displaytech/DT043CTFT-IPS/22229627 (Displaytech DT043CTFT-IPS, SC7283 driver, 480x272, 640 min/800 typ contrast, DigiKey part 22229627 confirmed live, 23 units in stock, ~GBP 26.86/unit)
- https://www.buydisplay.com/low-cost-ips-4-3-inch-lcd-display-arduino-spi-i2c-tft-touchscreen-480x272 and https://www.buydisplay.com/ips-4-3-inch-480x272-tft-lcd-display-with-optl-capacitive-touch-screen (BuyDisplay ER-TFT043A4-3 family, 480x272 IPS, 500:1 typ contrast per search-indexed page copy; driver IC not confirmed from this vendor's pages, which return HTTP 403 to direct fetch)
- https://www.waveshare.com/rp2350-touch-lcd-2.8c.htm and https://www.waveshare.com/product/raspberry-pi/boards-kits/rp2350-touch-lcd-2.1.htm (Waveshare RP2350 RGB-interface display dev boards — basis for confirming RP2350 has no native parallel-RGB/DPI peripheral and that RGB-interface panels on this MCU are driven via PIO state machines)
- .research/findings/2026-11-15-display-wide-bar-aspect-contrast.md (sibling finding — 170-height candidates and the ~900:1 ceiling this bead compares against)
- .research/findings/2026-11-15-display-alternatives-contrast.md (sibling finding — ~500:1 general baseline, and the original sourcing of the Newhaven NHD-2.4-240320AF-CSXP and Display Visions EA-TFT020-23AINN candidates re-used, rotated, in this finding)
- docs/plans/2026-11-13-custom-hardware-design.md (project's already-chosen 1.9" ST7789V 320x170 baseline and the "bare panel + 0.5mm-pitch FPC connector" integration pattern this bead checks candidates against)
