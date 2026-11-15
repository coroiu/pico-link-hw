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

**Update (2026-11-15, post-review on PR #40):** the first pass at this
finding misread two of the datasheet's own dimensioned figures and reached
conclusions those figures don't actually support — one minor (a
description error with no numeric impact), two load-bearing (contact side
is now unresolved rather than confirmed, and the bend-radius fit is now a
flagged risk rather than a 0.1mm-spare pass). See the "Correction" notes
inline in findings 1, 2 and 4, and the revision-discrepancy section,
below.

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

## Findings

### 1. FPC contact side: UNRESOLVED — isometric and the drawing's own numbered view disagree

**Correction (2026-11-15, post-review):** the previous version of this
finding called this "confirmed, moderate-high confidence" from the
isometric render alone. A PR review on `pilink-0o2` (#40) checked the
datasheet's two-dimensional mechanical views, which this finding had not
compared against each other, and found evidence pointing the other way.
Independently re-decoded the same page-6 raster (same recovery method as
before, re-verified pixel positions directly rather than trusting the
prior transcription) and confirmed the review's reading. This is now
**unresolved**, not settled, and needs physical inspection to close out.

Source: same datasheet document 4197, section 5 ("Mechanical Drawing").
The page actually contains **three** renderings of the module, not one:

1. A **dimensioned outline** (left side of the page) — this is the view
   every other dimension in this finding and in the proposal doc (frame
   42x59mm, AA, FPC widths, tail lateral offset) is measured from. Its
   tail, at the exact same location where the pin-numbered view below has
   solid black hatching, is a **plain unfilled outline with no hatching,
   no fingers, no pin numbers** — confirmed by direct pixel inspection
   (cropped and re-examined at 2.5x; the tail's bottom edge is a single
   flat line, nothing else drawn on it).
2. A **second, undimensioned outline** of the identical shape (same
   notch/tab position, not mirrored) with the tail end filled by fine
   vertical black hatching and labelled **"40 [hatched bar] 1"** — a
   standard drafting convention for "this is the face you're looking at
   when you read the contacts," matching the Pin Function Reference table
   (pin 1 = LED_A ... pin 40 = GND) elsewhere on the same page.
3. An **isometric render** (color, photorealistic) of the assembled
   module and FPC, used by the original version of this finding.

Views 1 and 2 are two different orthographic projections of the *same*
part, one of which is the dimensioned reference every other number in this
finding is built from. If (1) is the front and (2) is the rear — the
natural reading, since a datasheet doesn't normally draw the same outline
twice for no reason, and pin-numbering diagrams are conventionally drawn
looking at the contact face — then **the hatching sits on the back face**,
directly contradicting the isometric-based "front" conclusion. Nothing on
the page carries an explicit "FRONT VIEW" / "REAR VIEW" text label (full
text of all 11 pages was extracted and searched for "view", "front",
"rear", "back" — none found as separate PDF text; if such labels exist
they're baked into the raster and weren't found by visual inspection
either), so which view is "front" is itself an inference, same as before —
but it's now a *conflicting* inference, not a clean confirmation.

Re-examining the isometric itself (the original evidence) also weakens it:
zoomed to 6x, the dark band at the tail end that the original finding read
as "gold/copper contact-finger surface" renders as **solid black with fine
vertical striation**, not a gold/brass color. A rendered gold contact
finger would typically show warm metallic tones; a flat black band with
pitch-matched ribbing is at least as consistent with a **black stiffener**
bonded to the tail for connector-insertion rigidity (common on ZIF/FFC
tails) as with exposed contacts. The isometric does not disambiguate this
on its own.

**This is now an open risk, not a confirmed fact: physical inspection of a
real panel (bending the tail and looking, or probing continuity against
the pin table) is needed to resolve it with certainty** — which this
bead's own scope already anticipated as the fallback for an inconclusive
case; this is now that case.

**Both fallback plans, so `pilink-7el.12` isn't blocked either way:**
- **(a) If front-face is confirmed:** the original plan holds as
  described — a bottom-contact J501 (Jushuo AFC01-S40FCA-00, confirmed
  bottom-contact per finding 3) mates correctly after a 180deg J-fold,
  subject to the bend-radius risk in finding 4 below.
- **(b) If back-face is confirmed:** a bottom-contact ZIF would receive
  the fingers face-up after a J-fold, which does not mate (an electrical
  failure, not just a placement one). Two fixes, either workable:
  - swap J501 for a **top-contact** ZIF of the same pitch/position-count
    (one BOM line, same footprint family, same location under the panel);
    or
  - route an **S-fold** instead of a J-fold, with J501 outboard of the
    panel edge instead of underneath it (costs more board space — the
    proposal already notes ~25mm of width or a slack loop for this
    option).

Neither fallback is committed to in advance; `pilink-7el.12` should check
contact side against a real panel (or get Crystalfontz support to state it
in writing) before finalizing J501's orientation.

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
sections' edge, not the same line. This doesn't change any of the
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

- J501 orientation: bottom-contact ZIF, long axis parallel to the panel's
  FPC exit edge, opening facing that edge, mounted on the PCB under the
  panel.
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
- Contact side requirement: **unresolved** (finding 1) — the datasheet's
  isometric render and its own numbered pinout view point opposite ways.
  Needs physical inspection of a real panel before `pilink-7el.12` commits
  to J501's orientation. If front-face: the plan above holds as-is. If
  back-face: swap J501 for a top-contact variant (same pitch/position
  count, same location), or route an S-fold instead — see finding 1 for
  both fallbacks in full.

## What would still need a human

- A physical CFAF240320A0-024SN panel, to resolve the contact-side
  question (finding 1) by direct inspection (bend the tail and look, or
  probe continuity against the pin table) rather than by conflicting
  drawing interpretations.
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
