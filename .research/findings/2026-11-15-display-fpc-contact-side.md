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

### 1. FPC contact side: front (display-face) side — confirmed, moderate-high confidence, not an explicit dimensioned callout

Source: Crystalfontz datasheet document 4197 (`CFAF240320A0-024SNDatasheet.pdf`,
cover page states **Revision 1v1, Datasheet Release 2019-11-04**; the
mechanical drawing's own title block reads **Revision 1v0, dated
2019-10-04**, filename `CFAF240320A0024SN_millimeter.pdf`), section 5
("Mechanical Drawing"), isometric render.

The isometric clearly shows the module's **front** (the display surface,
readable marketing text "CFAF240320A0-024SN ... ZIF Connector ...
Crystalfontz") facing the viewer, tilted up and to the left. The FPC tail
exits the bottom edge and curls forward/down, and in that curl its
gold/copper contact-finger surface faces **up, toward the viewer** — the
same half-space as the front/display surface, not the back case. This
directly matches the proposal's existing inference ("the iso render
appears to show the fingers on the display-face side") but was previously
unconfirmed; it's now been inspected at native resolution (cropped and
re-examined at 2x), not just glanced at.

This is still a rendered illustration, not a dimensioned "contact side: X"
text callout — Crystalfontz's own datasheet text never states this in
words anywhere in sections 1-12 (checked the full extracted text of all 11
pages). So call this **confirmed at moderate-high confidence, not
certainty**. The only fully certain check remains physically bending a
real panel's tail and looking (the user's action, per this bead's scope).

**Consistency check against J501:** J501 is confirmed bottom-contact (see
finding 3). A bottom-contact ZIF needs the FPC's exposed conductor face
pointing down into the connector slot. Front-side fingers + a 180deg fold
under the panel put the fingers face-down after the fold — which is
exactly what a bottom-contact ZIF needs. The two facts are consistent with
each other and with the proposal's planned J-fold. If the fingers had
turned out to be on the back face instead, the fold would present them
face-up, which would not mate with a bottom-contact ZIF at all (not even a
placement problem — an electrical one), and the fix would be:
- swap J501 for a top-contact ZIF of the same pitch/position-count (one
  BOM line, same footprint family, same location under the panel), or
- route an S-fold instead of a J-fold, with J501 outboard of the panel
  edge instead of underneath it (worse: the proposal already notes this
  costs ~25mm of width or a slack loop).

Since the evidence points to front-side fingers (matching the existing
plan), **neither fix is needed**, but both remain the documented fallback
if a physical check ever contradicts this.

### 2. FPC lateral offset: ~7.2mm, right of panel centreline (native portrait, FPC side) — confirmed by calibrated pixel measurement, tighter than the original ±0.5mm estimate

Source: same mechanical drawing, the dimensioned front-view outline (not
the isometric).

The front view's stepped outline below the LCD frame has **no step on the
side that becomes the connector's right edge in every section** — the
frame (42mm), the FPC's near-panel section (dimensioned 35.45mm), and the
FPC tail (dimensioned 20.50mm) all have that edge at the same x-position;
all narrowing happens from the other edge only. This was measured
directly in pixels rather than by eye: the drawing's own `42±0.008 Frame`
dimension line spans x=632..940px in the decoded image, giving a
calibration of 7.333 px/mm. Using that scale on the same outline:

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

### 4. FPC minimum bend radius: R = 1.5mm, with a 2mm minimum straight run before the bend — explicit, dimensioned, high confidence

Source: same datasheet, page 11 (the last page), section 12.6 ("Other
Precautions"), final bullet "The limitation of FPC bending:" followed
immediately by a dimensioned figure (decoded the same way as the
mechanical drawing on page 5):

- **R = 1.5mm** minimum bend radius, labelled directly on the figure.
- **Min 2mm**, a separate horizontal dimension on the same figure, for the
  minimum straight (unbent) run of FPC between the rigid display-area
  attachment and the start of the bend.

This is a real, explicit, dimensioned datasheet value — not a render or
an analogy. It **tightens, rather than breaks, the proposal's existing
J-fold feasibility**, but by much less margin than the proposal assumed:

- The proposal's section 2 estimated "the bend radius is about 1.7mm
  (half the 3.4mm gap)" as a *budget*, then used it to size the fold.
  Crystalfontz's actual *minimum* is 1.5mm, which is less than that
  1.7mm budget, so **the fold does fit** — but the vertical space the
  180deg fold itself needs is roughly `2 x R + FPC thickness` =
  `2 x 1.5mm + 0.3mm` = **~3.3mm**, against a 3.4mm gap. That is about
  **0.1mm of spare**, not the comfortable margin the "half the gap" framing
  implied. J501's own 2mm height (finding 3) is a separate, more
  comfortable check (~1.4mm spare) since it occupies a different part of
  the same 3.4mm envelope, not stacked on top of the fold.
- Practical consequence for `pilink-7el.12` (PCB re-placement) and the
  enclosure: the 3.4mm under-panel gap is a tighter constraint for the
  *fold itself* than previously stated. Any stack-up creep (a panel seated
  0.1-0.2mm proud, a PCB thicker than the assumed 1.6mm, an adhesive/foam
  layer under the panel) could make the minimum-radius fold interfere with
  the panel glass. This is worth carrying as an explicit tolerance risk
  into the re-placement work, not just "it fits."
- The "Min 2mm" straight-run requirement also affects exactly where the
  bend can start relative to the panel edge; it's a small additional
  offset (not previously budgeted at all) that the placement rule below
  accounts for only approximately (see Placement rule, margin note).

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
unresolved — **it doesn't affect any finding above**, because the
datasheet's own disclaimer text (page 3, "Crystalfontz has the right to
change the PCB Rev... under the premise of not affecting the electrical
characteristics and external dimensions") is Crystalfontz's explicit
policy that revisions don't change external dimensions, which is exactly
the category of number re-checked here. If the exact pin-table revision
ever matters, that's a separate, narrower question for Crystalfontz
support, not a geometry question.

## Concrete J501 placement rule

Combining the above with the proposal's existing analysis (section 2,
point 2), for **either** FPC exit side:

- J501 orientation: bottom-contact ZIF, long axis parallel to the panel's
  FPC exit edge, opening facing that edge, mounted on the PCB under the
  panel.
- Inset from the panel's FPC edge to J501's insertion face: **~24mm**
  (unchanged from the proposal — the 1.5mm/2mm bend figures refine the
  *fold's* risk margin, not this inset, since ~5.5mm of fold length was
  already budgeted and the actual minimum-radius fold is slightly
  *shorter* than that budget, not longer).
- Lateral offset from the panel centreline: **~7.2mm** (refined from
  ~7.3mm), toward the user if FPC-left, toward the rear if FPC-right (per
  the upright-desk-clock ADR, the chosen layout is **FPC-right**, i.e.
  toward the buttons — so this offset is toward the rear in that ADR's
  geometry).
- Vertical clearance: J501's 2mm body height fits the ~3.4mm gap with
  ~1.4mm spare. The fold itself needs ~3.3mm of the same 3.4mm gap, with
  only ~0.1mm spare — **flag this as a tolerance risk for `pilink-7el.12`**,
  not a clean pass.
- Contact side requirement: works as planned only if the FPC fingers are
  on the display-face side of the tail (finding 1: confirmed,
  moderate-high confidence). If a physical panel ever shows otherwise,
  swap J501 for a top-contact variant (same pitch/position count, same
  location) rather than re-deriving an S-fold.

## What would still need a human

- A physical CFAF240320A0-024SN panel, to confirm contact side by direct
  inspection (bend the tail and look) rather than by isometric render.
- A physical J501 part or its real engineering drawing from Jushuo
  (not available online in a dimensioned form), to confirm "Height Above
  Board: 2mm" to better than catalog-field precision, and to confirm
  whether that 2mm already accounts for the open actuator or just the
  closed/seated state.
- Final DRC/placement check in KiCad once `pilink-7el.12` actually places
  J501 and routes the panel-shadow keep-out — this finding feeds that
  bead's inputs but doesn't replace running DRC on the real board.
