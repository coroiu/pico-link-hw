# Display FPC contact side, J-fold geometry, and J501 placement rule

## Context

`docs/plans/2026-11-15-product-layout-proposal.md` section 2 assumes the
CFAF240320A0-024SN's 40-pin FPC tail J-folds 180deg under the panel into
J501 (Jushuo AFC01-S40FCA-00, a bottom-contact ZIF), and that this only
works if the FPC's exposed contact fingers are on the display-face
(front) side of the tail. That was an inference from an isometric render,
not a dimensioned fact, and three other numbers fed into the same
geometry (the ~7.3mm tail lateral offset, the FPC bend radius, and J501's
mated height) were either eyeballed off a drawing or assumed by
component-class analogy. This finding re-checks all four against primary
sources: the Crystalfontz datasheet's actual mechanical drawings (decoded
directly, see Method) and JLCPCB's structured catalog data for J501.

**Update (2026-11-15, post-review on PR #40, round 2):** the first pass at
this finding misread two of the datasheet's own dimensioned figures and
reached conclusions those figures don't actually support — one minor (a
description error with no numeric impact), two load-bearing (contact side
is now unresolved rather than confirmed, and the bend-radius fit is now a
flagged risk rather than a 0.1mm-spare pass). See the "Correction" notes
inline in findings 1, 2 and 4, and the revision-discrepancy section,
below.

**Update (2026-11-15, post-review on PR #40, round 3):** round 2's own
contact-side writeup was itself wrong on a specific, checkable claim — it
said the datasheet's dimensioned outline and its pin-numbered outline have
"the same notch/tab position, not mirrored." They are an exact mirror,
confirmed this round by independently re-rendering and comparing both
outlines pixel-for-pixel. That flips the conclusion: the drawing evidence
now **favors back-face contacts** as the working assumption, not an even
front-vs-back toss-up. This round also names concrete replacement
connector parts (a preferred dual-contact ZIF that removes the risk
entirely, plus a confirmed top-contact fallback), adds the pin-1-mapping
caution either swap needs, gives the S-fold fallback rough placement
numbers, and reconciles a small (~0.15mm) rounding discrepancy between two
measurements of the same frame-to-FPC gap. See the updated finding 1 and
the "Concrete J501 placement rule" / "What would still need a human"
sections below.

## Method note

No PDF rasterizer (`pdftoppm`/poppler, ImageMagick, Ghostscript) or Python
PDF library (`pypdf`, `pymupdf`, `pdfplumber`) is installed in this
environment, and installing one wasn't authorized for this task. The
Crystalfontz datasheet's two mechanical-drawing pages are plain RGB
bitmaps stored as `/Filter /FlateDecode` image XObjects (not JPEG/DCT), so
they could be recovered with the Python standard library alone: locate
each `stream...endstream` object with the matching `/Width`/`/Height`,
`zlib.decompress` it, and re-wrap the raw RGB bytes in a hand-built PNG
(IHDR/IDAT/IEND chunks, `zlib.crc32` for the chunk CRCs) for the Read
tool. This made the datasheet's two drawing pages, and specific
sub-crops of them, directly viewable. Page text (revision, pin table,
precautions) was separately recovered by decompressing each page's
content stream and parsing its `(...) Tj`/`TJ` text-show operators —
again, no external tool, pure `zlib` + a small hand-rolled tokenizer.
Pixel-level measurements below used the same decompressed RGB array,
calibrated against the drawing's own dimensioned 42mm frame width.

**Round 3 addition:** this environment does have Python's `PIL`/`Pillow`
library (confirmed present this round, unlike a PDF rasterizer or a
page-layout-aware PDF text library), so the hand-rolled PNG reconstruction
above could be cropped, scaled and horizontally flipped with it for direct
visual overlay comparison of the two page-6 outlines, in addition to the
raw pixel-array measurements. For the dual-contact connector candidate's
own datasheet (a different, vector-CAD-exported PDF), the same `zlib`
image-recovery approach found only one small raster (a component photo);
the drawing text itself is vector with glyph-indexed font encoding that
this environment's toolchain (plain `zlib` plus a hand-rolled `Tj`/`TJ`
tokenizer, no `ToUnicode` CMap parsing) could not decode into readable
characters, and no PDF rasterizer was available to render it as an image
either — so that part's mated-height and pin-1-location dimensions could
only be sourced from JLCPCB's structured catalog fields and product-page
text, not read directly off its own CAD drawing. This is flagged inline
where it applies (finding 1's fallback plan A).

## Findings

### 1. FPC contact side: drawing evidence now favors BACK-FACE contacts — working assumption for planning, pending physical confirmation

**Correction (2026-11-15, third review round on PR #40):** the second
version of this finding called the drawing's two outlines "the same
notch/tab position, not mirrored" and left front-vs-back as an even,
unresolved coin flip. That description was **factually wrong**. A second
review pass measured both outlines in pixels and found the pin-numbered
view is an **exact mirror** of the dimensioned view, feature for feature.
This finding was reworked a third time to independently check that claim
from scratch — not by re-reading the prior transcription, but by
re-rendering both page-6 outlines as PNGs from the PDF's own raw image
stream (same recovery method as before: locate the Flate-compressed image
XObject, `zlib.decompress`, hand-wrap as PNG) and comparing them visually
and by direct pixel measurement, using a Python/PIL toolchain available in
this environment (still no PDF rasterizer or page-layout-aware PDF
library). The mirror claim is **confirmed**, and it changes the
conclusion: the drawing evidence now points toward back-face contacts, not
a neutral toss-up.

Source: same datasheet document 4197, section 5 ("Mechanical Drawing").
The page contains **three** renderings of the module:

1. A **dimensioned outline** (left side of the page) — the view every
   other dimension in this finding and the proposal doc (frame 42x59mm,
   AA, FPC widths, tail lateral offset) is measured from. Its tail is a
   **plain unfilled outline with no hatching, no fingers, no pin
   numbers**. In this view, the step/notch in the tail profile sits on the
   tail's **left** side (small tab near the top of the step, narrowing
   happens from the left), and the **right** edge runs straight down,
   flush with the frame's own right edge, all the way to the tail end.
2. A **second, undimensioned outline** of the identical part, tail end
   filled with fine vertical black hatching and labelled **"40 [hatched
   bar] 1"** — matching the Pin Function Reference table (pin 1 = LED_A
   ... pin 40 = GND) elsewhere on the same page. **Re-examined directly:
   this outline's step/notch sits on the tail's right side, with the left
   edge running straight down** — the mirror image of view 1, not a
   repeat of it. Flipping this view horizontally and overlaying it against
   view 1 reproduces view 1's outline feature-for-feature (same step
   heights, same tab position, same flush edge, now on the matching side).
3. An **isometric render** (color, photorealistic) of the assembled
   module and FPC, used by the original version of this finding and
   re-examined again below.

**Why a mirror means "rear view," and why that matters:** a left-right
mirror of an orthographic outline is, by construction, the same part seen
from the *other* side — it is not a second drawing of the front. Since
view 1 is the dimensioned front reference (every other number in this
finding is built from it) and view 2 is its mirror, **view 2 is the rear
view**. Pin-numbering diagrams are conventionally drawn looking at the
contact face, which is exactly what view 2 is — and it is the mirrored
(rear) view, not view 1. **That puts the hatched, numbered contacts on the
back face, not the front/display-face side.** This is the datasheet's own
drawing evidence pointing the opposite way from the original isometric
based read, not an ambiguous or neutral result. Nothing on the page
carries an explicit "FRONT VIEW" / "REAR VIEW" text label (checked again
this round: full text of all 11 pages extracted and searched for "view",
"front", "rear", "back" — none found as separate PDF text), so which view
is drawn "looking from the front" vs "looking from the back" is still an
inference from drafting convention, not a labelled fact — but it is now a
*one-sided* inference (both the mirroring and the conventional
pin-numbering-shows-the-contact-face reading agree), not a coin flip
between two equally weighted readings.

Re-examining the isometric itself (the original evidence) again, at higher
resolution than before: the visible face of the tail in the isometric is
continuous with, and in the same orientation as, the display's own front
(viewer-facing) surface — i.e. this is the display's front side, unbent.
That face shows only the printed Crystalfontz logo and part number; the
dark band right at the tail end renders as **solid black with fine
vertical striation**, not a gold/brass color. A flat black band with
pitch-matched ribbing is at least as consistent with a **black stiffener**
bonded to the tail for connector-insertion rigidity (common on ZIF/FFC
tails) as with exposed gold contacts, and the branding being printed on
this same face is itself mildly more consistent with this being the
*non-contact* face (manufacturers commonly reserve the contact face for
bare copper/gold fingers and print branding on the back). **The isometric
does not show front-face contacts; if anything, re-reading it now leans
the same direction as the mirror evidence.**

**Bottom line — status and working assumption:** this is still not
100%-certain without inspecting a real panel (a flat 2D drawing read
alongside a photorealistic render always leaves some room for a
mis-projected isometric or an unconventional drafting choice), so it stays
flagged as **needs physical confirmation**, not a closed fact. But the
balance of drawing evidence no longer supports treating front-face and
back-face as equally likely. **`pilink-7el.12` should plan around
back-face contacts as the default/working assumption**, with front-face as
the (less likely) fallback if a real panel or Crystalfontz support says
otherwise — the reverse of this finding's original framing.

**Fallback plan A (preferred): swap J501 for a dual-contact ZIF, which
removes the front/back dependency entirely.**

A connector that accepts the FPC with its fingers facing either direction
makes this whole question moot for the BOM/footprint, regardless of how
the physical-inspection question above is eventually resolved. Searched
JLCPCB's component database (`jlcpcb-search` MCP) for 40-position, 0.5mm
pitch FPC/FFC ZIF connectors and checked contact-type fields directly
(not by name alone, since name codes aren't a reliable guide — see the
AFC01-S40FCC-00 case below):

- **`FC-05B40P21H20`, LCSC `C23398824`, manufacturer BXCONN** (JLCPCB
  Extended part, confirmed via both the `jlcpcb-search` MCP tool and a
  direct fetch of the JLCPCB part page): **Contact Type: "Double-sided
  contacts, top and bottom entry."** 40 positions, 0.5mm pitch, SMD
  right-angle, Flip-Top lock, gold-plated copper-alloy contacts, 0.3mm
  FFC/FPC thickness (matches this panel's FPC), 50V rated, -25..+85°C,
  **Height Above Board: 2mm** (same catalog field, same value, as the
  current AFC01-S40FCA-00 — see finding 3), "Forward Foot / Back Foot: No
  polarity." **Stock: 2,635 units** as of 2026-11-15 (live stock, recheck
  before ordering). This is the strongly preferred fix: it eliminates the
  contact-side risk as a design dependency rather than betting on one
  reading of an ambiguous drawing.
  - **What this does *not* confirm:** mated height is sourced from the
    same class of catalog field as finding 3's AFC01 height (not a primary
    CAD drawing — this part's own datasheet PDF is a vector CAD export
    with glyph-indexed text that couldn't be decoded with this
    environment's toolchain, same limitation noted in the Method note
    above; no PDF rasterizer or ToUnicode-aware text extractor is
    available here), and **pin-1's physical location on this part's
    footprint was not independently verified**. See the pin-1 note below —
    this must be checked before `pilink-7el.12`/`pilink-7el.11` commits to
    it as a footprint swap.

**Fallback plan B (if plan A doesn't pan out): a confirmed single-sided
top-contact part.**

- **`HC-FPC-0.5-40P-CSH20`, LCSC `C19273956`, manufacturer Hong Cheng**
  (JLCPCB Extended part): **Contact Type: "Top Contact"** (confirmed via
  `jlcpcb-search`), Slide Lock, 40P, 0.5mm pitch, SMD right-angle, 0.3mm
  FFC thickness, copper contacts, -25..+85°C. **Stock: 16,755 units** as
  of 2026-11-15. This is a genuine opposite-contact-type swap for the
  current bottom-contact AFC01-S40FCA-00.
- **Checked and ruled out:** `AFC01-S40FCC-00` (LCSC `C262282`), the
  obvious same-family alternative suffix to the current part, is **also
  "Bottom Contact"** per JLCPCB's own structured catalog field (confirmed
  independently here via `jlcpcb-search`, not just taken on the prior
  reviewer's word) — it is not a usable top-contact substitute. Don't use
  it for this purpose.

**Pin-1 orientation — a real design consideration, not a footnote, for
either fallback:** a ZIF connector's pin-1 end is a physical feature of
its own footprint, independent of its contact-type (top/bottom/dual). If
either replacement part's pin-1 end turns out to be at the **opposite**
tail end from AFC01-S40FCA-00's, then swapping only the footprint while
keeping J501's existing net/pin assignments in the schematic would
silently cross-wire every signal (DB17-0, SDA, DOTCLK, HSYNC/VSYNC, RD/WR,
RS, CS, RESET, IMx, power/ground — see the Pin Function Reference table).
**`pilink-7el.11`/`pilink-7el.12` must check the replacement part's pin-1
location against AFC01-S40FCA-00's before finalizing either swap, and
reverse J501's pin mapping in the schematic (not just drop in a new
footprint) if the two parts' pin-1 ends don't match.** This applies
whether plan A (dual-contact) or plan B (top-contact) is used — it was not
checked for either part in this pass, for the same PDF-rendering-tooling
reason noted above.

**Fallback plan C (if no connector swap is acceptable): route an S-fold
instead of a J-fold**, with J501 outboard of the panel edge instead of
underneath it. Rough placement numbers (not previously given):
- **Orientation:** same rule as the J-fold — J501's long axis parallel to
  the panel's FPC exit edge, opening facing that edge.
- **Position:** instead of sitting **under** the panel, inset ~24mm in
  from the FPC edge (the J-fold plan), J501 moves to just **outside** the
  panel's own footprint, beside its FPC edge. That consumes roughly
  **25-28mm of additional PCB width beyond the panel's edge** — J501's own
  ~25.4mm courtyard length plus a few mm of clearance for the fold itself
  — board area the J-fold plan doesn't need at all (it tucks entirely
  under the panel). This matches the proposal's existing rough "~25mm of
  width" figure, now attached to a reason.
- **Lateral/front-back offset:** unchanged, about 7.2mm from the panel
  centreline — that number comes from the tail's own position on the
  panel (finding 2), not from the fold style.
- **Vertical:** the S-fold's two bends happen in open space beside the
  panel rather than squeezed into the 3.4mm under-panel gap, so it
  sidesteps finding 4's bend-radius fit risk entirely — at the cost of the
  extra width above, and of whatever contact-type part it's paired with
  (an S-fold still needs the fingers to end up facing the PCB at the
  connector, so it only sidesteps the *bend-radius height* risk in finding
  4, not the contact-side question in this finding, unless also paired
  with a dual-contact part).

None of the three fallbacks is committed to in advance. `pilink-7el.12`
should still check contact side against a real panel (or get Crystalfontz
support to state it in writing) if the schedule allows, but should not
block PCB re-placement on that confirmation now that plan A (dual-contact)
removes the dependency.

### 2. FPC lateral offset: ~7.2mm, right of panel centreline (native portrait, FPC side) — confirmed by calibrated pixel measurement, tighter than the original ±0.5mm estimate

Source: same mechanical drawing, the dimensioned front-view outline (not
the isometric).

The front view's stepped outline below the LCD frame has **no step on the
side that becomes the connector's right edge across the FPC's own
sections** — the FPC's near-panel section (dimensioned 35.45mm) and the
FPC tail (dimensioned 20.50mm) share one edge; all narrowing happens from
the other edge only.

**Correction (2026-11-15, post-review):** the previous version of this
finding also said the 42mm frame shares that same right edge. Direct pixel
measurement (scanning dark-pixel runs at several y-rows, not eyeballing)
shows that's wrong: the frame's own outline right edge sits at x=939-940px,
while the FPC sections' shared right edge sits at x=914-915px — the
frame's edge is about 25px, i.e. **~3.4mm, further out** than the FPC
sections' edge, not the same line.

**Reconciliation (2026-11-15, third review round):** this ~3.4mm figure
(a direct pixel-difference calculation, 25px / 7.333px/mm) doesn't quite
match the frame-vs-tail gap implied by the mm-calibrated tail span given
two paragraphs below (tail spans "18.0mm to 38.45mm" against a 42mm-wide
frame, which puts the tail's right edge 42 - 38.45 = **3.55mm** short of
the frame's right edge). The two numbers (~3.4mm vs ~3.55mm) differ by
about 0.15mm, i.e. about 1px at this drawing's resolution — within the
same antialiasing/line-thickness uncertainty already noted below (+/-1-2px,
+/-0.15-0.3mm) for measurements off this raster. The discrepancy comes
from two different computation paths (direct pixel subtraction of raw
edge positions, vs. subtracting two separately-calibrated mm values) that
don't round identically, not from an error in either value. It doesn't
change the qualitative point this paragraph makes (the frame's edge sits
measurably further out than the FPC sections' edge, they are not the same
line), and it doesn't change any of the
offset/dimension numbers below (those were already computed from the
frame's own `42±0.008` calibration and the FPC sections' own pixel spans,
not from an assumed shared edge) — it's a correction to the description
only. This was measured directly in pixels rather than by eye: the
drawing's own `42±0.008 Frame` dimension line spans x=632..940px in the
decoded image, giving a calibration of 7.333 px/mm. Using that scale on
the same outline:

- 35.45mm section: x=654.5..914px -> 35.4mm (matches the dimensioned
  35.45mm to 0.05mm — validates the calibration).
- 20.50mm tail: x=764..914px -> 20.46mm (matches the dimensioned 20.50mm
  to 0.04mm).
- Tail spans **18.0mm to 38.45mm** from the frame's left edge (vs. the
  proposal's eyeballed "18.0 to 38.6mm"). Tail centre = 28.2mm. Frame
  centre = 21.0mm. **Offset = +7.2mm**, essentially exactly the proposal's
  "~7.3mm" estimate, now backed by a calibrated pixel measurement instead
  of eyeballing a thumbnail.

Remaining uncertainty is from line thickness/antialiasing at this
resolution (~1-2px, i.e. ±0.15-0.3mm) — tighter than the proposal's
original ±0.5mm, but still not a substitute for the drawing's own
(nonexistent) explicit offset dimension. **No change needed to the
proposal's number; the uncertainty band can be tightened to roughly
±0.2mm.**

### 3. J501 mated/body height: 2mm above board — confirmed from JLCPCB's structured catalog data, not Jushuo's own PDF

Jushuo's own datasheet for this exact part, as hosted by LCSC
(`https://www.lcsc.com/datasheet/C262674.pdf`, linked from both LCSC's and
JLCPCB's part pages) is confirmed — independently, via a fresh fetch — to
be a generic company reliability/process-spec booklet (salt-spray,
vibration, reflow profile, SOP) with no dimensioned CAD drawing in it at
all. This matches what the footprint file's own authoring note already
found when sourcing pad geometry (`hardware/footprints/Connector_FPC.pretty/AFC01-S40FCA-00.kicad_mod`,
descr field). There is no primary-source drawing to read a height off.

The best available source is JLCPCB's own structured part-catalog page
for this exact LCSC part (`C262674`, jlcpcb.com/partdetail/AFC01-S40FCA-00/C262674),
which lists discrete spec fields (not a datasheet quote):

| Field | Value |
|---|---|
| Package | SMD, P=0.5mm, Surface Mount, Right Angle |
| Contact Type | **Bottom Contact** |
| **Height Above Board** | **2mm** |
| FFC/FPC Thickness | 0.3mm |
| Locking Feature | Flip-Top |
| Number of Contacts | 40P |
| Current / Voltage rating | 500mA / 50V max |

"Height Above Board" is JLCPCB's catalog field for the assembled
connector's height off the PCB surface, i.e. its mated/seated height for
BOM/fit purposes, not a momentary open-actuator height. **This confirms
the proposal's "about 2mm is typical for this class" placeholder as an
actual spec for this exact part** (not just a guess by analogy), and it
leaves about 1.4mm of spare in the ~3.4mm under-panel gap (2.0mm connector
+ comfortable margin).

### 4. FPC minimum bend radius: R = 1.5mm — dimensioned but ambiguous enough to be a real fit risk, not a 0.1mm-spare pass

**Correction (2026-11-15, post-review):** the previous version of this
finding misread the datasheet's own bend-limitation figure on two points
and, as a result, understated the risk. Re-decoded the figure directly
(same page-11 raster, re-cropped and re-examined at 4x rather than
transcribed from memory) to re-check both misreadings before rewriting
this section.

Source: same datasheet, page 11 (the last page), section 12.6 ("Other
Precautions"), final bullet "The limitation of FPC bending:" followed
immediately by a dimensioned figure. The figure shows a rigid "Display
area" (downward arrow pointing at a flat attached section), which bends
180 degrees and runs back the other way. Two dimensions are given:

- **"Min 2mm"**, a horizontal double-headed arrow. Measured directly in
  pixels: its left end sits exactly at the right edge of the rigid
  "Display area" section (where the flex region starts), and its right end
  sits at the outermost point of the curved fold (the apex of the bend,
  the farthest the fold extends past that edge). **This is how far the
  fold must stick out past the rigid/display-area edge before curling
  back — not a straight, unbent run of FPC before the bend starts**, which
  is what the previous version of this finding claimed. (It's also a
  generic precautions illustration about a rigid-mount-to-flex transition
  in general, not a drawing of this specific J-fold-under-the-panel
  scheme — so "Min 2mm" is best read as a general minimum clearance the
  fold needs beyond wherever its rigid attachment ends, not a dimension
  with an obvious direct line to this layout's existing numbers.)
- **"R = 1.5mm"**, a vertical double-headed arrow at the fold's outermost
  point. Measured directly in pixels: it spans from the top leg's height
  down to the bottom leg's height — i.e. **the whole visible fold height,
  top tangent to bottom tangent, not a line from a center point to one
  edge**. That means the sketch alone does not disambiguate whether R is
  an *inner* radius (radius to the inside/concave surface of the bend) or
  a *centerline* radius (radius to the material's mid-plane) — both are
  consistent with "an arrow spanning the visible loop," which is a common
  (if imprecise) way to dimension a bend radius regardless of which
  convention the number itself uses.

**Why this matters, worked both ways:** bend-radius specs in cable/FPC
datasheets conventionally mean the *inner* radius, not the centerline —
that's the industry-standard reading, and the safer one to design to
absent a contrary statement. The two readings give different answers
against the proposal's 3.4mm under-panel gap:

- **Inner-radius reading (the conventional one):** the fold's total
  outer-to-outer height is `2 x R + 2 x t` = `2 x 1.5mm + 2 x 0.3mm` =
  **~3.6mm**. Against a 3.4mm gap, that **does not fit** — it overshoots
  by about 0.2mm, not a pass.
- **Centerline-radius reading (what the previous version of this finding
  assumed, without stating the assumption):** total height is
  `2 x R + t` = `2 x 1.5mm + 0.3mm` = **~3.3mm**, which fits the 3.4mm gap
  with about 0.1mm spare — barely, and only under this less-conventional
  reading.

**A second, independent problem with the comparison itself:** both
readings above compare the fold's *own* height against the *full* 3.4mm
panel-to-PCB gap, as if the fold starts exactly at the panel's underside
(where that 3.4mm gap begins) and has the whole gap free to use. That's
not quite right either. The FPC's rigid-to-flex transition — the point
where it stops being bonded to the display assembly and starts being free
to bend — is physically up inside the panel's own 2.10mm thickness, not
at the panel's bottom/back face. The datasheet's dimensioned side view
(same page-5/6 drawing) shows the panel's 2.10mm thickness and the FPC's
0.3mm thickness as two separate, stacked dimensions, but doesn't give an
explicit z-offset for exactly where within that stack the FPC's flex point
sits. So "the fold's own height vs. the 3.4mm gap" is not a clean
apples-to-apples comparison in either direction: depending on where inside
the panel's thickness the transition actually is, the fold may have
*less* than the full 3.4mm to work with (if the transition is high up in
the stack, nearer the display glass), making both readings above
optimistic, not just the inner-radius one.

**Bottom line: this is now a real identified mechanical risk, not a
confirmed pass.** Depending on which radius convention applies and exactly
where the fold's rigid-to-flex transition sits within the panel's
thickness, the fold may not fit the 3.4mm gap as currently assumed, or may
fit with much less margin than "0.1mm spare" suggested. Flag this
explicitly for:
- **`pilink-7el.12`** (PCB re-placement): don't treat the 3.4mm gap as
  settled for the fold. Options if it doesn't fit: grow the gap (raise the
  panel standoff, thin the PCB), change the fold style (e.g. a looser
  S-fold or a larger-radius fold routed partly outside the panel's
  footprint instead of a tight 180deg J-fold), or relocate J501 to change
  how much of the FPC's free length is available before the bend.
- **`pilink-8hx`** (enclosure): the same 3.4mm figure feeds the enclosure's
  internal stack-up; if the gap needs to grow to accommodate the fold,
  that's a body-height change, not just a PCB layout change.
- J501's own 2mm height (finding 3) is unaffected by this — it's a
  separate, more comfortable check (~1.4mm spare) since it occupies a
  different part of the same 3.4mm envelope, not stacked on top of the
  fold.

## Revision discrepancy (unresolved, does not affect dimensions)

`hardware/README.md` cites "Crystalfontz's own datasheet (Rev 1v2,
2021-03-26)" for the pin table. The only document this research (or the
original `pilink-7el.5` work) could actually fetch is document 4197,
whose cover states **Revision 1v1, 2019-11-04**, and whose mechanical
drawing title block states **Revision 1v0, 2019-10-04**. A web search for
a 1v2/2021-03-26 revision of this exact datasheet found nothing —
Crystalfontz's own product page for CFAF240320A0-024SN links back to the
same document 4197. A newer revision may exist without being indexed, or
the "1v2" citation may be a mis-transcription from elsewhere. This is left
unresolved.

**Correction (2026-11-15, post-review):** the previous version of this
finding cited the "revisions don't change dimensions" disclaimer as being
on page 3 and covering datasheet revisions generally. Re-extracted the
PDF's text directly to check the citation: the actual text is on **page 9,
section 12.1 ("Modules")**, part of the LCD Module Precautions, and it
reads "Crystalfontz have the right to change the PCB Rev. (In order to
satisfy the supplying stability, management optimization and the best
product performance, etc., under the premise of not affecting the
electrical characteristics and external dimensions, Crystalfontz has the
right to modify the version.)". That's narrower than what was previously
claimed on two counts: it's about **PCB Rev** (the physical module's own
board revision) specifically, not datasheet document revisions in general;
and it's on page 9, not page 3. It still supports the same point — a PCB
Rev change (which is plausibly what the README's "1v2" vs. this document's
1v1/1v0 numbers reflect) isn't expected to change external dimensions —
but it doesn't fully resolve the Rev 1v1/1v0-vs-1v2 discrepancy itself,
since it says nothing about *datasheet document* revisions. If the exact
pin-table revision ever matters, that's still a separate, narrower
question for Crystalfontz support, not a geometry question.

## Concrete J501 placement rule

Combining the above with the proposal's existing analysis (section 2,
point 2), for **either** FPC exit side:

- J501 orientation: long axis parallel to the panel's FPC exit edge,
  opening facing that edge, mounted on the PCB under the panel. The
  current BOM part is bottom-contact; see the contact-side requirement
  below for why a **dual-contact** part is now the preferred choice here.
- Inset from the panel's FPC edge to J501's insertion face: **~24mm**
  (unchanged from the proposal — this inset isn't directly driven by the
  bend-radius figure; the fold's own vertical risk is tracked separately
  below).
- Lateral offset from the panel centreline: **~7.2mm** (refined from
  ~7.3mm), toward the user if FPC-left, toward the rear if FPC-right (per
  the upright-desk-clock ADR, the chosen layout is **FPC-right**, i.e.
  toward the buttons — so this offset is toward the rear in that ADR's
  geometry).
- Vertical clearance: J501's 2mm body height fits the ~3.4mm gap with
  ~1.4mm spare — that part is a comfortable pass. **The fold itself is an
  open risk, not a pass**: depending on bend-radius convention (inner vs.
  centerline, ambiguous from the datasheet's own sketch — finding 4), the
  fold's own height is somewhere between ~3.3mm (fits, ~0.1mm spare) and
  ~3.6mm (does not fit, overshoots by ~0.2mm), and the comparison itself is
  further weakened by not knowing exactly where inside the panel's
  thickness the fold's rigid-to-flex transition sits. **Flag this as a
  real fit risk for `pilink-7el.12` and `pilink-8hx`**, with the fallbacks
  listed in finding 4 (grow the gap, change fold style, or relocate J501),
  not a clean pass.
- Contact side requirement: **drawing evidence favors back-face, not
  front-face** (finding 1, reworked this round) — the datasheet's
  dimensioned outline and its pin-numbered outline are an exact mirror of
  each other, which means the pin-numbered (hatched/contact) view is the
  *rear* view, putting the numbered contacts on the back face. Treat
  **back-face as the working assumption** for `pilink-7el.12`, not a
  coin-flip, though it's not 100% certain without a physical panel.
  **Preferred fix regardless of which face turns out correct: swap J501
  for the dual-contact `FC-05B40P21H20` (LCSC `C262674` -> `C23398824`)**,
  which mates with either orientation and removes the dependency on
  resolving this question at all. If a dual-contact part isn't usable,
  fall back to the confirmed top-contact `HC-FPC-0.5-40P-CSH20` (LCSC
  `C19273956`) or an S-fold with J501 outboard of the panel edge (now with
  rough placement numbers) — see finding 1 for all three fallbacks, the
  required pin-1-orientation check for whichever part is chosen, and why
  `AFC01-S40FCC-00` (LCSC `C262282`) is **not** a valid top-contact
  substitute despite the name.

## What would still need a human

- A physical CFAF240320A0-024SN panel, to resolve the contact-side
  question (finding 1) with full certainty by direct inspection (bend the
  tail and look, or probe continuity against the pin table) — though this
  is no longer blocking, since the dual-contact J501 fallback works either
  way.
- A physical `FC-05B40P21H20` part or its dimensioned CAD drawing (this
  part's own datasheet is a vector PDF whose text uses glyph-indexed
  fonts this environment's toolchain couldn't decode — no ToUnicode-aware
  PDF text extractor or rasterizer was available, same limitation as the
  Method note above), to confirm its pin-1 physical location against
  AFC01-S40FCA-00's before `pilink-7el.11`/`pilink-7el.12` treats this as
  a drop-in footprint swap rather than a pin-mapping change.
- A physical J501 part or its real engineering drawing from Jushuo
  (not available online in a dimensioned form), to confirm "Height Above
  Board: 2mm" to better than catalog-field precision, and to confirm
  whether that 2mm already accounts for the open actuator or just the
  closed/seated state.
- Either a real FPC sample (to measure actual achievable bend radius/height
  against the 3.4mm gap directly) or confirmation from Crystalfontz support
  of which radius convention (inner vs. centerline) its "R = 1.5mm" spec
  uses and where the fold's rigid-to-flex transition sits relative to the
  panel's 2.10mm thickness — finding 4's risk can't be fully closed from
  the datasheet sketch alone.
- Final DRC/placement check in KiCad once `pilink-7el.12` actually places
  J501 and routes the panel-shadow keep-out — this finding feeds that
  bead's inputs but doesn't replace running DRC on the real board.
