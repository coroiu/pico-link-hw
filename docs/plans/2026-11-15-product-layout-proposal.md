# Pico Link product layout and size: proposal and decision record

Status: **decided 2026-11-15: section 6c (upright desk-clock body on two splayed rear legs), recorded in `.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`.** Sections 4-6b are earlier options and misreadings, kept for the record. Tracked by decision bead `pilink-1nh` ("Pick product layout option").

Fixed starting point (user requirement): **rotary knob on the left, screen
in the middle, buttons on the right.** USB-C exits the rear (already decided
in `AGENTS.md`). Look and feel is already fixed by
`.planning/decisions/2026-11-15-enclosure-aesthetic-direction.md`: minimalist,
hidden fasteners, single colour, flush low-profile controls.

Until now nobody had decided anything about the physical product layout. The
100 x 55 mm outline on PR #33 (`pilink-7el.9`) was a placement-tool default.
Section 5 covers what that means for the PR.

---

## 1. Confirmed dimensions of the parts that drive the layout

### 1.1 Display: Crystalfontz CFAF240320A0-024SN

Source: Crystalfontz datasheet PDF, document 4197
(`https://www.crystalfontz.com/products/document/4197/CFAF240320A0-024SNDatasheet.pdf`).
Figures come from section 4, "Mechanical Data", and the section 5 mechanical
drawing (drawing rev 1v0, 2019-10-04), which I rendered and read directly.
**Caveat:** that URL served the 2019-11-04 release of the datasheet. The
README for `hardware/` cites Rev 1v2 (2021-03-26) for the pin table.
Crystalfontz says rev changes don't affect external dimensions. Re-checking
the drawing against 1v2 is part of the `pilink-0o2` verification spike.

All values are in the panel's **native portrait** orientation (W = short
side, H = long side). Tolerance is +/-0.3 mm unless stated.

| Item | Value |
|---|---|
| Frame outline | **42.0 W x 59.0 H x 2.1 D** mm |
| LCD glass | 39.72 x 52.16 mm |
| Active area (AA) | **36.72 W x 48.96 H** mm (0.153 mm dot pitch) |
| AA inset from frame: left / right | 2.64 / 2.64 mm (symmetric) |
| AA inset from frame: top | 2.65 mm |
| AA inset from frame: **bottom (chip-on-glass ledge)** | **7.39 mm** (59 - 2.65 - 48.96). The panel is **not symmetric** along its long axis |
| FPC exit edge | **Native bottom short edge**, under the COG ledge |
| FPC length | 33.05 +/-0.5 mm from frame bottom edge to tail end (an 11 mm wide section, then a 20 mm tail) |
| FPC widths | 35.45 mm near the panel, then a 20.50 mm tail ending in 40 contacts at 0.5 mm pitch |
| FPC thickness | 0.3 +/-0.05 mm |
| Tail lateral offset | Tail spans about 18.0 to 38.45 mm from the frame's left edge (front view), so its centre is **about 7.2 mm right of the panel centreline**. There's still no explicit dimension for this on the drawing, but `pilink-0o2` re-measured it with a pixel-calibrated reading of the drawing's own 42 mm frame dimension (not eyeballing a thumbnail), tightening the uncertainty to about +/-0.2 mm |
| Contact side | **Back-face is the working assumption, pending physical confirmation** -- `pilink-0o2` found the datasheet's dimensioned front view and its separate pin-numbered view are an exact mirror of each other (confirmed by pixel-for-pixel comparison), which means the pin-numbered/hatched view is the *rear* view -- putting the numbered contacts on the back face, not the front. The isometric render's apparent front-face "finger" band re-reads as a black stiffener on closer inspection, not gold contacts. Not 100% certain without a real panel, but no longer a neutral toss-up (see `.research/findings/2026-11-15-display-fpc-contact-side.md`) |

In **landscape** (panel rotated 90 degrees, as the firmware assumes):

- Panel footprint **59.0 wide x 42.0 deep**, AA **48.96 x 36.72**.
- The FPC comes out of the **left or right** short edge, whichever way the
  panel is physically turned. Firmware rotation (MADCTL MV/MX/MY) only
  remaps memory. It does not change which physical edge the cable leaves
  from, and either physical orientation costs the firmware the same.
- The visible window sits **2.37 mm off the panel centre**, away from the
  FPC edge: (7.39 - 2.65) / 2. The enclosure should centre the *window* on
  the face, not the panel.

### 1.2 Rotary encoder: Alps EC11E18244AU (SW303)

| Item | Value | Source |
|---|---|---|
| Family / size | EC11E, "11 mm size", vertical, push switch, 18 pulses / 36 detents | Alps product page `tech.alpsalpine.com/e/products/detail/EC11E18244AU/` |
| Shaft | 6 mm, flat (D) | same |
| Shaft ("actuator") length | **20 mm** | same; KiCad footprint name `..._Vertical_H20mm` |
| Push travel | 0.5 +/-0.3 mm | same |
| Body outline | **12.0 x 11.6 mm** (shaft centred) | KiCad stock footprint F.Fab, `RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm` |
| PCB courtyard | **17.5 x 14.2 mm** (the 17.5 includes the A/B/C and S1/S2 pin rows) | same |
| Housing height above PCB | **~4.5 mm** (corrected; see note below) | Alps' own current EC11E Series catalogue, Drawing No. 2 for EC11E18244AU; `pilink-g8a` spike, `.research/findings/2026-11-15-encoder-ec11e18244au-specs.md` |
| Bushing top above PCB | **~11.5-12 mm** | same |
| Shaft tip above PCB | **~24.5 mm** (= ~4.5 mm housing + 20 mm shaft, measured from the housing top) | same |
| Through-hole leads | Stick out below the PCB. Allow about 3 mm under-board clearance in that area | standard THT |

**Correction (PR #36 review):** this table previously listed "Body height
above PCB: 7.5 mm max — confirmed." That was a misread of the Alps
drawing's "7.5 max" dimension, which is actually a **footprint** dimension
(shaft centreline to the A/C/B pin row, viewed down the shaft), not a
height above the PCB. The real heights are in the three rows above.

**Conflict with the aesthetic ADR:** with the face at about 7.5 mm above the
PCB (section 2 — a separate, coincidentally identical figure from the
*enclosure's* own stack, not the encoder spec), the shaft tip (~24.5 mm
above the PCB) leaves **about 17 mm of shaft above the face** (24.5 - 7.5),
with the ~7 mm bushing itself standing about 4 mm proud of the face
(11.5 - 7.5) before the bare shaft begins. Any knob on it stands well
proud, which doesn't fit "flush, low-profile". Fixes include a
shorter-shaft EC11E variant, a recessed knob well, or simply accepting a
proud knob. See `pilink-g8a`. This isn't a blocker for choosing a layout.

### 1.3 Face buttons A/B/X/Y: C&K PTS645SK50SMTR92LFS (SW305-SW308)

| Item | Value | Source |
|---|---|---|
| Body | 6.0 x 6.0 mm, SMD gull-wing | `hardware/BOM.md` (LCSC C221872); C&K PTS645 series |
| Height | **5.0 mm** off the PCB ("50" in the part code) | distributor listings plus the C&K part-number key |
| PCB courtyard | **10.1 x 6.8 mm** (pads at +/-3.98, +/-2.25) | KiCad `Button_Switch_SMD:SW_SPST_PTS645` |
| Implied pitch | Minimum about 10.2 mm along the pad axis and 7.0 mm across it. Rotating a switch 90 degrees swaps these |

SW101/SW102 (BOOTSEL/RESET) are the same part. I propose they **stay off
the face**: pinhole access through the bottom shell, used with a paperclip.
That's cheap, and nobody presses them by accident.

### 1.4 Other envelope drivers (already in the repo)

- **ESP32-WROOM-32UE**: 18.0 x 19.2 x 3.2 mm
  (`.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md`). The tallest
  SMD part after the switches. Because it's 3.2 mm tall it **can't sit under
  the display** (see below).
- **J501** (Jushuo AFC01-S40FCA-00, bottom-contact flip-lock ZIF): body
  24.4 x 5.35 mm, courtyard 25.4 x 6.9 mm, per the repo footprint
  `hardware/footprints/Connector_FPC.pretty/AFC01-S40FCA-00.kicad_mod`.
  Height **confirmed 2.0 mm above board**, from JLCPCB's structured
  catalog data for this exact LCSC part (Jushuo's own hosted datasheet
  turned out to have no dimensioned drawing at all). Leaves about 1.4 mm
  of spare in the ~3.4 mm under-panel gap (`pilink-0o2`, see
  `.research/findings/2026-11-15-display-fpc-contact-side.md`).
- **J401** USB-C (HRO TYPE-C-31-M-12), about 3.3 mm tall, was assumed here
  sitting edge-mount at the PCB's rear edge. **Superseded by section 6c /
  the ADR**: the chosen upright form factor needs a vertical-mount
  receptacle on the PCB's back face instead (part TBD, `pilink-0do`/
  `pilink-7el.11`), since an edge-mount part can't face rearward off a
  vertical board.
- **U.FL antenna: no part selected yet** (it isn't in `hardware/BOM.md`).
  Typical adhesive 2.4 GHz FPC antennas are around 35-45 x 8-12 mm
  (`pilink-8wx`).

---

## 2. Shared geometry (applies to every option)

**Vertical stack (side section)**, as heights above the desk:

```
 face outer surface ........ ~14.1   (face plate 2.0 thick)
 face inner surface ........ ~12.1   <- display glass sits against this
 button actuator top ....... ~11.6   (PCB top + 5.0)
 panel underside ........... ~10.0   (12.1 - 2.1)  => ~3.4 mm gap above PCB
 PCB top ...................  6.6
 PCB bottom ................  5.0   (1.6 mm board)
 under-board clearance .....  2.0-5.0 (3 mm for encoder THT leads)
 floor .....................  0-2.0 (2.0 mm wall)
```

So the body comes out at about **14 mm tall**, before knob and feet.
Practical rules that follow:

1. **Panel shadow keep-out.** The 59 x 42 mm area under the panel has about
   3.4 mm clearance. J501 (about 2 mm) plus the folded FPC (0.3 mm) fit. So
   do the RP2350B QFN, flash, PSRAM, crystal, LDO and display boost parts
   (all 1.8 mm or less). **The ESP32 module (3.2 mm, too tight), the USB-C
   receptacle, the switches and the encoder do not fit.** This is good news:
   most of the logic can sit under the screen, so only the knob, buttons,
   ESP32 and USB-C need space of their own.
2. **FPC routing: J-fold under the panel -- open mechanical risk, not a
   confirmed fit.** The tail leaves the panel's left/right edge, makes a
   180 degree fold down past the panel edge, and runs back *under* the
   panel into J501. Crystalfontz's own datasheet gives a dimensioned bend
   figure (`pilink-0o2`), but it's a generic precautions sketch, not scale
   drawn, and it's genuinely ambiguous on two points that matter: whether
   **R = 1.5 mm** is an *inner* radius (the conventional reading for
   bend-radius specs) or a *centerline* radius, and exactly where inside
   the panel's own 2.10 mm thickness the FPC's rigid-to-flex transition
   sits before the fold even starts (its "Min 2 mm" dimension turns out to
   be the fold's own protrusion past the rigid display area, not a
   straight run before the bend, so it doesn't resolve this). Worked both
   ways: the inner-radius reading puts the fold's own height at
   `2 x 1.5 mm + 2 x 0.3 mm FPC thickness` = **~3.6 mm**, which **exceeds**
   the 3.4 mm gap; the centerline reading gives `2 x 1.5 mm + 0.3 mm` =
   **~3.3 mm**, which fits with about **0.1 mm of spare**. Which is correct
   isn't resolvable from the sketch alone. **Treat the fold as a real
   tolerance/fit risk for `pilink-7el.12` and `pilink-8hx`, not a settled
   pass** -- the gap may need to grow (raise the panel standoff, thin the
   PCB), the fold style may need to change (a looser S-fold, or a
   larger-radius fold routed partly outside the panel's footprint instead
   of a tight 180-degree J-fold), or J501 may need to move to change how
   much free FPC length is available before the bend. The fold's *planned*
   length budget (about 5.5 mm of FPC, leaving about 27.5 mm running back
   under the panel) is **not directly driven by the bend-radius number
   itself**, but it isn't fully independent of the risk either: if the
   under-panel gap has to grow (raised panel standoff, thinner PCB) or the
   fold ends up needing a larger radius or a looser shape than currently
   assumed, that consumes more FPC length for the same fold and would
   shift the ~24 mm inset below, not just the fold's height. Treat the
   24 mm inset as provisional until finding 4's risk is resolved, not as a
   number the bend-radius question can't touch. J501 therefore sits:
   - **under the panel**, with its long axis **parallel to the FPC edge**
     (front-to-back) and its opening facing that edge;
   - with its insertion face about **24 mm in from the panel's FPC edge**
     (centre about 26.5 mm in, so about 3 mm toward the FPC side of the
     panel centre). Slack in the fold allows about +/-2 mm;
   - offset **about 7.2 mm front-to-back** from the panel centreline
     (refined from a pixel-calibrated re-measurement of the drawing,
     `pilink-0o2`; was ~7.3 mm eyeballed). It goes toward the user if the
     FPC is on the left, toward the rear if the FPC is on the right (the
     native-right side of the module maps there after rotation).
   - A **~3 mm bend strip** beside the panel's FPC edge must stay clear of
     the encoder body and switches.
   - J501's own body height is confirmed **2.0 mm** (JLCPCB catalog data
     for this exact part), leaving a comfortable ~1.4 mm of the 3.4 mm gap
     spare for the connector itself -- this part of the stack-up is a clean
     pass, separate from the fold-height risk above.
   This only works if the FPC contacts face the PCB after the fold. The
   current bottom-contact J501 only mates correctly if the fingers are on
   the display-face side of the tail -- and **`pilink-0o2` found the
   datasheet's own drawing evidence now favors the opposite (back-face)
   reading**: the datasheet's dimensioned front view and its separate
   pin-numbered view are an exact mirror of each other (confirmed by
   pixel-for-pixel comparison, not just eyeballing), which makes the
   pin-numbered/hatched view the *rear* view -- putting the numbered
   contacts on the back face. The isometric's apparent front-face "finger"
   band re-reads as a black stiffener, not gold contacts, on closer
   inspection. Full certainty still needs a physical panel, but
   **back-face is now the working assumption for the PCB re-place, not an
   even coin flip**. The preferred fix works either way, in the original
   J-fold geometry, with no width penalty: swap J501's current part (LCSC
   `C262674`) for the candidate **dual-contact** ZIF `FC-05B40P21H20`
   (LCSC `C23398824`, JLCPCB Extended part, 2,635 units in stock as of
   2026-11-15 -- same 2mm height above board as the current part), which
   mates with the FPC fingers facing either direction and removes this
   question as a design dependency entirely.

   If that swap doesn't work out, which fix applies depends on which side
   the contacts actually turn out to be on, and on whether the J-fold or
   an outboard S-fold is used -- a single tight J-fold bend flips which
   face ends up toward the PCB, while an S-fold's two bends net to no
   flip:
   - **Front-face:** J-fold + current bottom-contact part (no change), or
     outboard S-fold + a top-contact swap.
   - **Back-face** (the working assumption): J-fold + a confirmed
     top-contact swap (`HC-FPC-0.5-40P-CSH20`, LCSC `C19273956`, 16,755
     units in stock), or outboard S-fold + **no part change at all** (the
     current bottom-contact part already works once the fold doesn't flip
     which face points at the PCB) -- at the cost of roughly 28-35 mm of
     added board width beyond the panel's edge for the S-fold (re-derived
     from the ~33 mm of free FPC cable and J501's own depth, not from its
     25.4 mm length, which stays parallel to the panel edge either way),
     vs. none for the J-fold.
   - Note `AFC01-S40FCC-00`/LCSC `C262282`, despite the similar part
     number, is *also* bottom-contact per its own JLCPCB catalog entry and
     is not a valid top-contact substitute.

   **Whichever part replaces J501, check its pin-1 location against the
   current part's before treating it as a drop-in footprint swap** -- if
   pin-1 lands at the opposite tail end, the schematic's J501 pin mapping
   must be reversed, not just the footprint. See
   `.research/findings/2026-11-15-display-fpc-contact-side.md` finding 1
   for the full placement-rule matrix and detail on all of this.
3. **Which edge the FPC leaves from (any option can use either):**
   - **FPC-left (toward the knob).** The panel's 7.39 mm dead ledge sits on
     the knob side, where clearance is needed anyway for the knob overhanging
     the encoder body. The device ends up **about 4 mm narrower**. But during
     assembly the panel has to be held flipped out *over the encoder*, whose
     20 mm shaft gets in the way of plugging in the FPC.
   - **FPC-right (toward the buttons).** Assembly is easier: the panel flips
     out over 5 mm-tall switches, so it can lie nearly flat while you latch
     the ZIF. Costs about 4 mm of width.
   - Both are purely mechanical choices. Electrically they're identical, and
     the firmware just picks a different MADCTL value.
4. **USB-C** can't sit behind the panel unless the depth grows by about
   8 mm. This rule 4 described edge-mount J401 for the flat-slab options
   (A/B/C); **superseded by section 6c / the ADR**, which instead uses a
   vertical-mount receptacle on the PCB's back, exiting the rear wall
   directly.

---

## 3. Usage pattern: what the ergonomics are for

Pico Link is a USB dongle. It stays plugged into a computer or phone, sits
still, and gets touched **occasionally**: turn the knob for volume, press it
to mute, now and then use a button or open a menu. It is tethered by a cable
out of the rear, so it is **not** held in two hands like a game controller.
The realistic modes are:

- **On a desk, face up or tilted**: by far the main case.
- In a bag between uses: pocketability is nice to have, not a requirement.

Ergonomic consequences:

- The device has to **stay put while the knob turns**. A printed shell plus
  PCB weighs roughly 40-60 g. EC11-class detent torque and the friction of a
  light body on rubber feet are in the same ballpark, so a light flat slab
  may twist when turned one-handed. I haven't checked this numerically; the
  encoder's rotational-torque spec is part of `pilink-g8a`. Mitigations:
  wide rubber feet, a printed-in steel or coin ballast pocket, or the user
  steadying it with the other hand.
- With the knob on the left, a right-handed user turns it with their left
  hand or reaches across. That's the user's explicit choice, noted here so
  it isn't mistaken for an oversight.
- Viewed at a desk from about 50-70 cm, a 2.4" panel lying flat is seen at a
  steep angle. The panel is rated 160 degrees and 800:1, so it stays legible,
  but a tilted face reads noticeably better.

---

## 4. Options

Each option keeps the knob on the left, the screen in the middle and the
buttons on the right. Dimensions are external, with 2.0 mm walls, and
exclude the knob and feet. The PCB outline is about the outer outline minus
5-6 mm in each direction. Sketch scale is about 2 mm per column and 4 mm per
row. Front (user side) is at the bottom. All sketches show **FPC-left**;
FPC-right mirrors the hatched strip and J501 to the other side of the panel.

### Option A: Desk slab, generous (about 118 x 52 x 14 mm)

A flat minimalist slab with comfortable spacing: about a Ø18 mm knob,
buttons in a diamond, wide margins around the window.

```
 rear  [USB-C]                                  (antenna on inner rear/left wall)
 +-----------------------------------------------------------+
 |  [ESP32 ]  ::+-----------------------------+              |
 |  [18x19 ]  ::|                             |     ( X )    |
 |            ::|      active 49 x 37         |              |
 |   .---.    ::|   [J501]  (under panel)     | ( Y )   ( A )|
 |  ( knob)   ::|                             |              |
 |   '---'    ::|                             |     ( B )    |
 |  encoder   ::+-----------------------------+              |
 +-----------------------------------------------------------+
 front (user)         :: = FPC fold strip + 7.4 mm COG ledge under bezel
```

- **Width build-up (FPC-left):** wall 2 + margin 5 + knob radius 9 = 16;
  knob centre to window edge 16.4 (encoder body clearance plus bend strip
  plus ledge); window 48.96; window to button cap edge 6; diamond 24 (caps
  Ø8, centres +/-8 mm, which clears the courtyards); margin 5 + wall 2.
  Total **about 118 mm** (about 122 mm with FPC-right).
- **Depth:** panel 42 + fit clearance 0.6 + bezel 3 per side + walls 2 per
  side. Total **about 52 mm**.
- **Height:** about 14 mm body. The knob stands about 17 mm proud with the
  current 20 mm shaft (section 1.2; corrected from an earlier ~12 mm figure
  that misread the Alps body-height dimension — see `pilink-g8a`).
- **Internal zoning:** knob zone (about 20 x 46 mm inside) holds the encoder
  (17.5 deep) and the ESP32 behind it (19.2 deep), 36.7 mm total. USB-C sits
  rear-right behind the button diamond. RP2350B, memory and power all sit
  under the panel. The PCB is about **112 x 46 mm**.
- **Antenna:** on the inside of the rear wall or left end wall, behind the
  ESP32. That's at least 10 mm from the panel's metal frame and away from
  the USB-C. Inside height is only about 10 mm, so a narrow FPC antenna
  (about 8 mm) is needed. Feasible but tight.
- **Trade-offs:** + the most comfortable controls, the visually balanced
  "TE-style" proportions the aesthetic ADR asks for, and an easy layout.
  - the widest option, not really pocketable, and a flat screen viewed at
  an angle. It may slide when the knob turns unless feet or ballast are added.

### Option B: Tilted desk wedge (about 118 x 56 x 13-31 mm)

The **same PCB and plan layout as A**, mounted in a shell whose face tilts
about 20 degrees toward the user. The rear is tall and the front is low.

```
 side view                                   plan view = Option A
              ________________ rear ~31 mm
   face 20°  /               |
  __________/  PCB (tilted)  | [USB-C] exits rear face, cable away from user
 |___________________________|   front ~13 mm
  <---------- ~56 mm -------->
```

- **Footprint:** about 118 x 56 mm. Height is about 13 mm at the front and
  about 31 mm at the rear (52 mm deep slab tilted 20 degrees).
- **Trade-offs:** + the screen faces the user (the best readability at a
  desk), and the knob and buttons are reached naturally from the front. The
  wedge under the PCB gives **real volume for the antenna**, high on the
  rear wall and away from the desk surface and the user's hand. It also has
  room for a **ballast pocket**, which addresses knob-turn stability. The
  PCB is identical to A, so the PCB doesn't depend on choosing between A
  and B. - Bulkiest in a bag, uses more print material and time, and the
  shell takes more modelling effort (tilted bosses, angled USB-C cutout).
  Hidden fasteners still work from underneath.
- **Variant:** a 5-10 degree tilt cuts the rear height to about 19-23 mm and
  keeps most of the readability gain.

### Option C: Compact slab (about 102 x 50 x 14 mm)

The minimum honest envelope: knob about Ø14 mm, buttons in a tight 2x2
grid, narrow margins.

```
 rear [USB-C]                                         [ESP32]
 +---------------------------------------------------+
 |        ::+-----------------------------+  (X) (Y)  |
 |  .-.   ::|                             |           |
 | (knb)  ::|     active 49 x 37          |  (A) (B)  |
 |  '-'   ::|  [J501]                     |           |
 |        ::+-----------------------------+           |
 +---------------------------------------------------+
 front
```

- **Width build-up (FPC-left):** wall 2 + margin 3 + knob radius 7 = 12;
  knob centre to window 16.4; window 48.96; gap 4.5; 2x2 grid 15.5 (switches
  rotated 90 degrees, pitch 8.5 x 10.5 mm, caps Ø7); margin 3 + wall 2.
  Total **about 102 mm** (about 106 mm with FPC-right).
- **Depth:** about 50 mm. **Height:** about 14 mm. **PCB:** about 96 x 44 mm.
- **Internal zoning:** USB-C rear-left behind the encoder, ESP32 rear-right
  behind the button grid (about 25 mm of depth there), antenna on the inner
  right or rear wall.
- **Trade-offs:** + the smallest and most bag-friendly option, and the
  closest envelope to the old stacked boards' spirit. - Cramped controls:
  7 mm caps at about 8.5 mm pitch are fine for occasional presses but not
  for gloves or blind use. A Ø14 knob gives less fine volume control. Very
  little ballast or antenna volume, and the most likely to twist when the
  knob turns. Visually it reads "small gadget" rather than "desk object".

### Reference: the old form factor does not fit

The old stack was a Pico-class board (about 51 x 21 mm) under a 65 x 30 mm
LCD HAT. The new panel **by itself** (59 x 42 mm) is wider than that HAT is
tall, and the active area alone is 49 x 37 mm. No layout with the knob on
the left and buttons on the right gets under about 100 mm wide with this
panel. The old form factor is not a target any more.

### Side-by-side

| | A: Desk slab | B: Wedge | C: Compact |
|---|---|---|---|
| External L x W x H | ~118 x 52 x 14 | ~118 x 56 x 13-31 | ~102 x 50 x 14 |
| PCB outline | ~112 x 46 | same as A | ~96 x 44 |
| Knob / buttons | Ø18 / Ø8 diamond | Ø18 / Ø8 diamond | Ø14 / Ø7 2x2 |
| Screen readability at desk | ok (flat) | best (tilted) | ok (flat) |
| Stability when turning knob | needs feet/ballast | best (ballast room) | weakest |
| Antenna room | tight (~10 mm inner height) | generous | tight |
| USB-C rear exit | fine | fine (angled face) | fine |
| Bag-friendliness | fair | poor | good |
| Enclosure modelling effort | low | medium | low |

---

## 5. Compatibility with the PR #33 PCB (`pilink-7el.9`)

What PR #33 has, read from `hardware/pico-link-hw.kicad_pcb` on branch
`feat/pilink-7el9-pcb-layout`:

- A 100 x 55 mm board.
- The encoder (SW303) is at the **upper right**, and the four buttons form a
  diamond on the right.
- The ESP32 (U201) is at the **left**.
- J401 USB-C is at the rear centre.
- J501 is at the **front centre at 0 degrees**, so its long axis runs
  left-right.
- Nothing is placed with a 59 x 42 mm display shadow or its height limit in
  mind.

**None of A, B or C is compatible with it.** The board needs re-placing and
re-routing, not tweaking:

- The encoder is on the wrong side (right instead of left), and the ESP32
  sits where the knob has to go.
- J501 is rotated 90 degrees the wrong way for a panel whose FPC leaves a
  left or right edge, and it's in the wrong place. It belongs under the
  panel, about 24 mm in from the FPC edge and offset about 7 mm front or
  back (section 2).
- The outline is too deep and too narrow for A/B (112 x 46). For C it's
  roughly the right area (96 x 44 vs 100 x 55) but the wrong aspect ratio.
- No panel-shadow keep-out exists, so nothing guarantees the 3.4 mm under
  the panel stays clear.

What carries over unchanged: the schematic, netlist, BOM and footprints, and
the scripted placement plus Freerouting pipeline, which re-runs cheaply.
Suggestion for the orchestrator/user: treat PR #33 as a routing-feasibility
proof (how dense the board is, how many layers it needs), not the final
layout. Re-place once the option is chosen. That re-place should start from
the `pilink-kt4` netlist fix anyway.

---

## 6. Recommendation (the user's call)

My lean is **A's PCB, with A or B as the shell, FPC-right**:

- A and B share one PCB, so committing to the ~112 x 46 mm board doesn't
  force the flat-vs-tilted decision yet. B can come later as a different
  bottom shell.
- FPC-right costs about 4 mm of width and makes hand assembly (latching a
  40-pin ZIF with the panel flipped out) clearly less fiddly. That counts
  for more on a hobby build than 4 mm does.
- Pick C only if bag-friendliness matters more than knob comfort and
  readability. Given that this is a desk-tethered dongle, I don't think it
  does, but that's a product priority, not an engineering fact.

Questions for the user:

1. **A, B or C** (or the A-PCB with the shell choice deferred)?
2. **FPC-left (narrower) or FPC-right (easier assembly)?**
3. **Knob height:** accept a proud knob, or pursue a shorter shaft or a
   recessed well to match the "flush" ADR (`pilink-g8a`)?

## 6a. [SUPERSEDED: misread of the user's sketch, see 6c] Chosen configuration: side profile

**The user's choice:** Option B shell (about 20 degree wedge) on Option A's
PCB (about 112 x 46 mm), with the **FPC exiting toward the buttons (right)**
and the **proud knob accepted as-is** (no shorter shaft and no recessed well
for now). The ADR will formalise this. The profile below works out the
details. Where it refines Option B's rough numbers above, these numbers
supersede them.

**Geometry conventions.** Heights are measured from the desk and **include
1.7 mm feet** (2.5 mm silicone bumpers sitting in 0.8 mm recesses).
"d" means depth measured perpendicular to the face. The PCB, panel and
controls all sit **parallel to the face**, so the internal stack from section
2 carries over unchanged, just tilted. The wedge volume sits *under* the PCB.

**Envelope:** about **118 W x 54 D** mm footprint. The front edge is **14.7 mm**
high and the rear top edge **32.8 mm**. The knob top reaches about **35 mm**
and is the highest point.

### Left-side exterior (knob side), to scale: 1 column = 1 mm, 1 row = 2 mm, user on the left

```
 y mm
 36                   ##                                      <- knob Ø18, ~17 mm proud (corrected, pilink-g8a), axis
 34             #########                                        perpendicular to face, top leans
 32        ######       ##                        /////\         toward the user (highest point ~35)
 30   ######             #                  ///////    \\
 28   ##                 ##            //////           \\    <- rear facet, perpendicular to face:
 26    ##                 ##     ///////                 \\      USB-C exits here at ~y 27
 24     #                  #//////                        \
 22     ##            ///////                             \|  <- face, 20 deg
 20      ##      //////                                    |
 18       #///////                                         |
 16   //////                                               |
 14  |/                                                    |  <- front edge 14.7
 12  |                                                     |
 10  |                                                     |
  8  |                                                     |
  6  |                                                     |
  4  |                                                     |
  2  _______________________________________________________  <- floor plate
  0     ooo                                           ooo     <- feet Ø10, cover the screws
     0         10        20        30        40        50   x mm (user on the left)
```

The knob is drawn at its real position: the lower-front of the left zone,
centred about 15 mm up the face from the front edge. (Note: this section is
superseded by 6c; the knob-proud annotation above is corrected to ~17 mm
per `pilink-g8a`, but the diagram's pixel scale for the knob blob itself was
not redrawn to match.)

### Section through the screen centre (front-to-back), same scale

```
 y mm
 32                                               /////\      <- rear top 32.8
 30                                           ...//#   \\
 28                                      ......#####    \\
 26                                .......####     UUUUU \\   U = USB-C J401 (rear-right, projected)
 24                           ......#####      JUUUU====  \   J = J501 under panel (projected)
 22                     ......#####      JJJ=======       \|  = = PCB, parallel to face
 20                ......#####      JJJ======           A  |  A = U.FL antenna, inner rear wall
 18        ///......####      JJJ=======                A  |  # = panel, . = visible glass
 16   //////#######         ======                      A  |  / = face plate (window cut out)
 14  |/     #         =======                           A  |
 12  |           ======                                 A  |
 10  |     =======                                      A  |
  8  |                                                  A  |
  6  |               %%%%%%%%%%%%%%%%%%%%%%%            A  |  % = ballast pocket, ~35 g steel
  4  | --------------%%%%%%%%%%%%%%%%%%%%%%%-------------- |  - = floor inner surface
  2  _______________________________________________________
  0     ooo                                           ooo
     0         10        20        30        40        50   x mm (user on the left)
```

### Stack-up perpendicular to the face (section 2 adapted to the tilt)

Drawn in the face's own frame: rotate 20 degrees to get the real orientation.

```
 d mm
  0.0  ----------+                                  +-----------  face outer (2.0 plate)
  0.5            +\  chamfer      window            /+
  1.2  ===========#==== glass top: face thinned to 1.2 over panel ===#========
                  #####  panel 42 x 59 x 2.1 (landscape: 59 wide)   #####
  3.3  -----------##### panel back -------------------------------- #####
  ~3.6                 FPC J-fold returns under panel (0.3) ---------)  <- fold at RIGHT
  5.5                        [ J501, ~2 tall ]------------------------    panel edge,
                             RP2350B / flash / PSRAM / LDO (<=1.8)        3 mm bend strip
  7.5  =========================== PCB top ====================================
  9.1  =========================== PCB bottom =================================
 12.1  - - - - - - - - - 3 mm minimum clearance (encoder THT leads) - - - - - -
       ...then the wedge cavity to the floor: about 2.6 mm at the PCB's
          front edge, growing to about 19 mm at its rear edge
 Buttons: actuator top at d 2.5 (PCB + 5.0); caps flush at d 0, flange under the plate.
 Knob:    shaft tip at d -17 (shaft tip 24.5 mm above PCB [4.5 mm housing + 20 mm shaft], PCB seated at d 7.5, so d 7.5 - 24.5 = -17; pilink-g8a corrected); knob base 0.8 above face.
```

### Notes and decisions made for this profile (reversible, for the ADR to adopt or change)

- **Display:** the glass sits **1.2 mm below the face**. The plate is
  thinned to 1.2 mm over the panel area only, with a small chamfer around
  the window, so at the desk viewing angle there's a crisp shadow line
  rather than a deep well. A flush 1 mm clear lens is a later option. The
  panel sits in a printed pocket in the top shell and is pressed against
  the face by foam pads or ribs. That follows the datasheet's "fasten the
  external housing, don't stress the glass" guidance. The FPC J-folds at the
  **right** panel edge into J501 under the panel. J501's long axis runs
  front-to-back, offset about 7 mm **toward the rear** of the panel
  centreline, and its exact rule is pending `pilink-0o2`.
- **Knob:** at the **lower-front of the left zone** (about 15 mm up the face
  from the front edge). That puts it closest to the user's hand, and it
  frees the rear-left of the zone for the ESP32 (encoder about s 8-22 mm,
  ESP32 behind it). Its axis is perpendicular to the face, so it leans 20
  degrees toward the user. Its top rear edge (about 35 mm) is a little
  higher than the rear of the case (32.8 mm), which is fine visually and
  for grip.
- **USB-C:** the receptacle (J401) sits on the PCB's rear edge, **rear-right**
  in plan (behind the button zone). It exits through an **upper rear facet
  perpendicular to the face**, so the plug goes in square. The cable
  therefore leaves pointing about 20 degrees upward, at about 27 mm above
  the desk, then droops. A right-angle or flexible cable is kinder to the
  receptacle. The alternative, a fully vertical rear wall, saves about
  4 mm of depth but makes the plug enter at 20 degrees through an elongated
  cutout. I rejected that.
- **Antenna:** on the inner **rear wall, rear-left**, in the tall wedge
  cavity *below* the PCB rear edge. That's about 17 mm of usable height,
  away from the desk surface and the user's hands, and about 60 mm
  laterally from the USB-C. Ground-plane and metal clearance still need
  checking against the selected part (`pilink-8wx`).
- **Ballast:** a pocket moulded into the floor, centre-front, under the
  display/button zones and not under the encoder leads. Sized for a
  steel bar about 60 x 22 x 3.5 mm (**about 35 g**), glued in. That roughly
  doubles a ~50-60 g device's resistance to twisting when the knob is
  turned. It's kept at least 14 mm from the antenna. Optional: leave the
  pocket empty if the device turns out stable enough without it.
- **Feet and fasteners:** four Ø10 silicone bumpers at the corners sit in
  0.8 mm recesses and **cover the screw heads**. Screws (M2.5/M3) go up
  through the floor plate into heat-set inserts in the top-shell bosses.
  That's the "hidden fasteners" requirement of the aesthetic ADR.
- **Shell split:** the **top shell** is the face plus all four side walls,
  and the PCB mounts to bosses on its underside perpendicular to the face.
  That way the display, buttons and knob are all referenced to the part
  they show through. The **bottom shell** is a flat floor plate (feet,
  ballast pocket, screw holes). Print the top shell face-down for the best
  face finish. The front, side and rear walls then overhang no more than
  20 degrees from vertical relative to the bed, which prints fine.
- **Under-board rule for the PCB re-place:** keep 3 mm clear below the PCB
  near the front edge (encoder leads). Elsewhere the wedge gives at least
  2.6 mm, growing toward the rear. Above the PCB, thinning the face plate
  over the panel raises the gap under it from 3.4 mm (section 2) to about
  **4.2 mm**. Keep the same panel-shadow rule anyway: only parts 2.5 mm tall
  or less, plus J501 and the FPC, under the panel. The ESP32, USB-C,
  switches and encoder stay outside it.

## 6b. [SUPERSEDED: misread of the user's sketch, see 6c] Terraced two-peak profile

**Status: this supersedes 6a's uniform wedge, pending the two clarifications
below.** The user sent a hand-drawn profile instead of refining 6a. The
coordinator relayed it as follows: a **tall raised section on the left** with
a steep rising face and the knob mounted partway up that sloped face; a
**valley** in the middle (the screen); a **shorter raised section on the
right** with a cable drawn coming out and running down to the table; the
whole thing on a flat "table". I have not seen the sketch, only that
description.

### Reading used here, and the two ambiguities that need the user

The left peak / valley / right peak order only matches "knob left, screen
middle, buttons right" if the sketch is a **front elevation** (seen from the
user's seat, x = width). I've drawn it that way. Two things follow from that
reading, and both need the user to confirm:

1. **Which way does the knob lean?** In a front elevation, the sloped
   face of the left peak faces the **screen (right)**, not the user. A knob
   mounted on it has its axis tilted *toward the centre*. If the user meant
   the knob tilts *toward the user*, the sloped face is the pod's **front**
   face. That only shows as a slope in a *side* view, so the sketch would be
   a side elevation (front pod / screen / rear pod), and that contradicts
   "knob left / buttons right". **Ask: does the knob face lean toward the
   screen or toward the user?** (Both are possible, and so is both at once:
   a 45 degree inward flank on a body tilted toward the user gives a compound
   lean.)
2. **Which cable is it, and where does it exit?** The only cable is USB-C
   (J401). The antenna lead is internal and the panel FPC is internal.
   - **Reading (a), side exit:** USB-C leaves the **right end wall**, low,
     about 8 mm above the table, so the cable runs straight down to the table
     as drawn. That **changes the rear-exit decision recorded in
     `AGENTS.md`**. It's workable: J401 goes on the main PCB's right edge,
     beside the button diamond in the front-back direction. But it's a real
     architecture change and needs explicit sign-off.
   - **Reading (b), rear exit:** USB-C still leaves the rear, behind the
     right pod, and the sketch just shows it dropping to the table. No
     change to settled decisions.
   **Ask: right side or rear?** The diagram shows (a) as a projection
   (`U`) because that's the literal reading.

### Front elevation (section at mid-depth), to scale: 1 col = 1.5 mm, 1 row = 2 mm, flat base (no front-back tilt)

```
 42
 40                 KK                                                                     K = knob Ø18 on 45° flank (axis tilts toward screen)
 38               KKKKK
 36              KK   KKK                                                                  E/= = encoder on its own angled daughterboard
 34  _______\\  KK      KK
 32  |       \\KK        KK
 30  |        \\K         KKK
 28  |         \\\          KK
 26  |    == EEEE\\K       KKK
 24  |   ====EEEEE\\K     KK
 22  |     ===EEEEE\\\   KK                                       _______________________| <- right pod top 22.3 (buttons)
 20  |      ====EEEEE\\KKK                                        |      :          :    |
 18  |       ====EEEE \\                                          |      :          :    |
 16  |         ===EE   \\\                                        |      :          :    |
 14  |          ====     ____..................................___|#     :          :    | <- valley face 14.3; window 49 wide, glass 1.2 below
 12  |           ====       #######################################))  SS:SSSSSSS SS:SS  | # = panel; ) = FPC J-fold at its RIGHT edge
 10  |             =        #######################################))) SSSSSSSSSS SSSSSUU|
  8  |                                        JJJJJ               ))   SSSSSSSSSS SSSSSUU| J = J501 under panel   S = switch, : = plunger
  6  | =======================================JJJJJ====================SSSSSSSSSS=SSSSS=U| = = main PCB (flat)   U = USB-C, side exit (projected)
  4  |                                                                                   |
  2  _____________________________________________________________________________________
  0     oo                                                                           oo    feet
     0         15        30        45        60        75        90        105       120        x mm
```

**Envelope (flat base):** about **126 W x 52 D** mm. The valley face is at
14.3 mm, the right pod top at 22.3 mm and the left pod peak at 34.3 mm. The
knob's highest point is about **40 mm**. All heights are from the table and
include 1.7 mm feet. The stack under the valley is section 2's: floor 2.0,
1.5 mm gap (the main board no longer has through-hole parts), PCB 1.6, 5.5 mm
to the face's inner surface, then the face. Glass is 1.2 mm below the valley
face.

### Can the EC11 mount on an angled face? Not on the main board: it needs a daughterboard

- The EC11E18244AU is a vertical through-hole part. Its shaft is
  perpendicular to the board it's soldered to, and there's no threaded
  bushing to panel-mount it. If it stays on the flat main PCB, the shaft
  points straight up. It **cannot** come out of a 45 degree flank.
- **To get an angled knob,** put the encoder on a small **daughterboard**
  (about 20 x 20 mm) mounted parallel to the flank inside the left pod,
  with the same local stack as before: seat 7.5 mm below the flank face;
  shaft tip 24.5 mm above the board (4.5 mm housing + 20 mm shaft) leaves
  about 17 mm proud (24.5 - 7.5, corrected, `pilink-g8a`). Through-hole leads need about 3 mm
  behind the board. A 5-6 wire cable (A, B, C, S1, S2, GND) plugs into a
  small wire-to-board connector on each board. The debounce RCs stay on the
  main board, so the daughterboard is just the encoder plus a connector.
  Costs:
  - a second PCB design. At JLCPCB that's a separate small order or a
    multi-design panel (extra fee, still cheap);
  - a schematic change to `input.kicad_sch` (SW303 becomes a connector);
  - one cable to plug in during assembly;
  - printed ribs and screws behind the daughterboard, because pressing the
    knob (mute/select) pushes on the board at 45 degrees.
  This is a sound, buildable approach, not a hack, but it is more parts and
  more design than one board.
- **One-board alternative:** keep the encoder on the main PCB with the
  shaft vertical, and put the knob on the **flat top** of the left pod
  instead of its flank. The pod top at about 18-20 mm puts the shaft tip
  (PCB top + 24.5 = 31.3 mm — corrected: 4.5 mm housing + 20 mm shaft
  above the PCB, not PCB + 20; `pilink-g8a`) about 11-13 mm above the pod
  top (31.3 - 20 to 31.3 - 18). That makes a **lower knob** than 6a's
  ~17 mm proud one (corrected, `pilink-g8a`), though closer to it than
  previously thought, which happens to suit the "flush" aesthetic ADR
  somewhat better. The pod keeps its sculpted sloped flank, just without
  the knob on it.
- Either way, the main board loses its only through-hole part.

### Screen in the valley: the valley does not fix viewing angle, so tilt is still a separate choice

- The valley walls are to the screen's **left and right**. They have no
  effect on the **front-to-back** viewing angle, which is what makes a flat
  screen look washed out from a desk chair. With the eye about 40 cm above
  the desk and 60 cm back, a flat screen is seen about **56 degrees off its
  normal**. The panel is rated 160 degrees, so it's legible, but contrast
  drops.
- Sinking the screen does protect it and frames it nicely. It doesn't
  reduce glare from overhead lights.
- **Tilt is independent of the terrace shape:** the terrace is the front
  elevation, and a tilt is the side elevation. Tilting the base front to
  back by θ raises everything at the rear by about 52 x tan θ:

| Base tilt θ | Screen off-normal (seated) | Rear valley face | Rear right-pod top | Rear left-pod peak |
|---|---|---|---|---|
| 0 degrees (drawn) | ~56 degrees | 14.3 | 22.3 | 34.3 |
| 10 degrees | ~46 degrees | ~23.5 | ~31.5 | ~43.5 |
| 20 degrees (6a's tilt) | ~36 degrees | ~33 | ~41 | ~53 |

  20 degrees on top of the terraces makes the rear-left corner over 5 cm
  tall, which is a lot of plastic. **10 degrees is the sensible middle**
  if the user still wants the tilt. A flat base reads cleanest as a
  sculpture. **Third question for the user:** flat, 10 degrees or 20
  degrees?

### What stays the same from 6a / section 2

- The panel J-fold toward the **right** (buttons) is still correct: the
  dead ledge and FPC fold sit hidden **under the right pod's flank**, so
  the valley only needs about 6 mm bezels around the 49 mm window. J501
  sits under the panel, long axis front-to-back, about 26 mm in from the
  panel's right edge (rule pending `pilink-0o2`).
- Buttons stay on the main PCB under the right pod. The pod top sits 8 mm
  above the valley face, so the printed plungers are about 10.5 mm long in
  guide bores. That's fine for FDM. Caps sit flush with the pod top.
- **ESP32** moves to the **rear half of the left pod**, on the main PCB, so
  it doesn't clash with the daughterboard's leads in the front half.
  **Antenna:** high in the left pod's rear (the tallest internal volume,
  well above the ground plane) or the right pod's rear. Check against the
  part chosen in `pilink-8wx`.
- **Main PCB** becomes a flat board about **121 x 46 mm**. That's still
  incompatible with PR #33, and also different from 6a's 112 x 46.
- Feet cover the screws, the floor plate holds the ballast pocket, and
  the top shell carries the PCB. All unchanged.

## 6c. Corrected concept: upright "desk clock" body on rear legs (confirmed by the user, 2026-11-15)

**This is the current concept. Sections 6a and 6b misread the user's hand
sketch and are kept only for the record.** The user confirmed the intent
directly:

- a small, nearly vertical standing device (desk clock or photo frame);
- the body leans back about 15 degrees from vertical, so the face is at
  about 75 degrees to the table;
- one front face carrying knob left / screen middle / buttons right;
- a support strut behind it;
- USB-C exiting the rear, low, with the cable running down by the strut to
  the table.

### Side profile, to scale: 1 col = 1 mm, 1 row = 2 mm, user on the left

```
  60
                                                                        <- top ~58 incl. feet
                                 \\\\
                                 /  \\\\\\\\
                                //      == \\\\/                        body 14 thick, leaning back 15 deg (75 deg from table)
  50                            /      ====   //
                               //###   ===    /
                               /####  ====   //
                              //###   ===    /                          / = front face (glass behind it), # = panel
                              /###   ===    //
  40                         //###   ===    /                           = = PCB, parallel to the face
                             /###   ===    //
                            /####   ===    \\                           \ = rear legs (pair, splayed +/-40 mm; only one visible)
                           //###   ===    //\\
             KKKKK         /####   ===    /  \\                         + = estimated centre of mass
  30         K   KKKKKKKKK//###   ===    /    \\\
            KK           K/####   ===   //      \\
            K            //###   +==    /        \\                     K = knob, ~17 mm proud (corrected, pilink-g8a; centre ~19 mm up the face)
           KK            /####EEE===   //         \\
          KK            //###EEE===eee /           \\\                  E/e = encoder body / THT leads behind PCB
  20      K             /####EE====ee //             \\
         KK            //###EEE===eee /               \\
         K             /###EEE===eee //                \\               U = USB-C exits rear, low; cable runs down between the legs
         KKKKKKK      //###EEE===eee /                   \\
               KKKKKKK/### EE===eee UUU                   \\
  10                 //###   ===    / UUUUUUUU             \\
                    //###   ===    //        UUUUUUUUU      \\\
                    /       ===    /                 UUUUUUU  \\
                   //      ===    //                           \\
                   ________________                            ______   o = feet
   0                ooooooooooooo                              ooooo
         -10       0         10        20        30        40        50          x mm (user on the left)```

### Front elevation (face-true), to scale: 1 col = 1.5 mm, 1 row = 2.5 mm

```
                                                                                          <- top of face (56 along the face, ~58 standing)
     __________________________________________________________________________________
     |                                                                                |
  50 |                                                                                |
     |    WWWWWWWWWWWWW-----------------------------------------                      |   W = ESP32 (behind face), U.FL up top -> antenna in top wall
     |    WWWWWWWWWWWWW: ..................JJJJJ...........    :                      |
     |    WWWWWWWWWWWWW: ..................JJJJJ...........    : )                    |
  40 |    WWWWWWWWWWWWW: ..................JJJJJ...........    : )      oooo          |
     |    WWWWWWWWWWWWW: ..................JJJJJ...........    : )     oo   o         |   . = visible window 49 x 36.7
     |    WWWWWWWWWWWWW: ..................JJJJJ...........    : )     o  X o         |
     |    WWWWWWWWWWWWW: ..................JJJJJ...........    : )  oo  ooooo  o      |   - : = panel outline 59 x 42 (hidden)
  30 |    WWWWWWWWWWWWW: ..................JJJJJ...........    : )oo  oo    ooo ooo   |
     |       OOOOOO    : ..................JJJJJ...........    : )o Y  o    o  A  o   |   ) = FPC J-fold at the panel RIGHT edge
     |     OO      OO  : ..................JJJJJ...........    : )oo  oo    ooo ooo   |
     |    O          O : ..................JJJJJ...........    : )  oo  ooooo  o      |   J = J501 behind panel, long axis vertical
  20 |    O          OO: ..................................    : )     o  B o         |
     |    O     +     O: ..................................    : )     oo   o         |   O = knob Ø18 (centre 16, 19)
     |    O          O : ..................................    : )      oooo          |
     |     OO       OO : ..................................    : )                    |   o = A/B/X/Y caps Ø8, diamond +/-8 mm
  10 |       OOOOOOO   : ..................................    :                      |
     |                 -----------------------------------------                      |   U = USB-C on the back (hidden)
     |                                    UUUUUUUU                                    |
     |             #                      UUUUUUUU                      #             |   # = rear legs at x 21 and 101 (behind)
   0 ______________#____________________________________________________#______________
     0         15        30        45        60        75        90        105       120        x mm```

### Dimensions (from the real part stack)

- **Face:** about **122 W x 56 H** mm along the face. The width budget is
  the same as Option A with FPC-right. The height is the 42 mm panel plus
  bezels and walls, and leaves room for the ESP32 above the encoder.
- **Body thickness:** about **14 mm**. That's face 2.0, 5.5 mm to the PCB
  (5.0 mm switches, 3.3 mm panel stack, J501 about 2 mm), PCB 1.6, 3 mm
  behind the PCB for the encoder's through-hole leads, and a 2.0 mm back
  wall. The knob adds about **17 mm** in front (corrected from an earlier
  ~13 mm figure that misread the Alps body-height dimension; see
  `pilink-g8a`). This ~4 mm increase is a direct correction of the knob's
  own protrusion; it has not been re-propagated into the other
  depth/footprint figures below (e.g. "Standing" and the front-to-back
  envelope numbers derived from the 6c diagrams), which should be
  re-verified against the corrected knob protrusion in a follow-up pass.
- **Standing:** about **58 mm tall** including feet. The body alone is
  about 28 mm front-to-back at the base. With legs, the footprint is about
  **122 W x 50 D** mm, and the feet sit about 46 mm behind the front edge.
  So the device is roughly 4x taller and has about the same depth as the
  flat options, which is genuinely small on a desk.
- **Mass estimate:** about **110 g** (+/-30%). That's roughly 60 g of PLA
  shell, 10 g of legs, 16 g of PCB, the 10.9 g panel, about 10 g of parts
  and about 5 g of knob. No ballast assumed. This number drives everything
  in the stability section below.

### Stability: turning is fine with two splayed legs; *pressing* is the real problem

Inputs:
- **Detent torque:** 10 +/-7 mN·m, **confirmed for EC11E18244AU
  specifically** (`pilink-g8a`, against Alps' own EC11 catalogue
  product-line table, not just a series-wide figure) — 17 mN·m worst case,
  unchanged.
- **Encoder push force:** 6 (+2.5/-2) N for the 0.5 mm-travel EC11 variant,
  **confirmed for EC11E18244AU specifically** (`pilink-g8a`; also matches
  Alps' own product page and catalogue switch-spec table).
- **Tact switch force:** 2.6 N (260 gf), per the LCSC/Future listings for
  PTS645SK50SMTR92LFS.
- **Weight:** about 1.08 N. Silicone feet μ is about 1.

1. **Turning the knob applies a torque (a couple), and the knob's height
   doesn't change its effect.** The coordinator's "longer lever arm"
   worry doesn't apply to pure turning torque. What matters is whether the
   torque can roll the device over one front corner and a rear foot.
   - **Single central strut:** the tipping line runs from a front corner
     to the single foot. With the centre of mass about 14 mm behind the
     front edge, the resisting moment is about **20 mN·m with the foot
     35 mm back** (only **1.15x** the worst-case detent) and about
     **27 mN·m with it 45 mm back** (1.6x).
   - **Two splayed legs** at +/-40 mm, 45 mm back: about **53 mN·m
     (3.1x)**.
   - Real fingers also push sideways while turning. **So a single strut is
     marginal and two splayed legs (or one leg with a foot at least 80 mm
     wide) are the right call.** The two-leg frame also gives the USB-C
     cable a clean path down the middle.
2. **Pressing the knob (mute/select) or the buttons pushes almost
   horizontally into a light, near-vertical body, and it will move.**
   - The push is perpendicular to the face, so about 97% of it is
     horizontal. Sliding friction available is μ x (weight + the push's
     downward share).
   - **Button press:** about 2.5 N horizontal against about 1.75 N of
     friction, so **it slides**.
   - **Knob press:** about 5.8 N against about 2.6 N, so **it slides**,
     and its line of action passes far behind the feet, so it can also
     **tip back**.
   - **No strut geometry fixes this.** It's a mass/friction problem. A
     face would only be self-locking with grippy feet at about 45 degrees
     or flatter (μ >= cot φ), which is the old wedge.
   - Resisting a knob press one-handed would take about 0.5-0.6 kg of
     device.
   This is a **real finding for the user, not a detail**. Realistic
   options, cheapest first:
   - **(a) Two-handed or steadying presses:** thumb on the top edge or
     behind, as you would with a photo-frame clock. Turning, the main
     action, stays one-handed.
   - **(b) Reusable nano-gel / adhesive pads under the feet.** Shear grip
     comes from adhesion, not weight, so buttons should be fine and the
     knob press probably fine. This needs a quick physical test (user).
   - **(c) A weighted base:** a steel insert in the base or legs. About
     200 g of *added* steel (bringing the ~110 g body to roughly 310 g
     total) makes button presses reliable without gel; about 500 g+ of
     *added* steel (roughly 610 g+ total) is needed for the knob press.
   - **(d) Lower-force A/B/X/Y switches:** `PTS645SM50SMTR92LFS` (LCSC
     C221881, 1.6 N, same footprint as the current part) **checked and
     available**, but only 44 units in live stock as of `pilink-g8a`
     (recheck before ordering); `PTS645SL50SMTR92LFS` (LCSC C221877, 1.3 N,
     same footprint, 4,043 in stock) is the better-stocked fallback. Either
     is a partial help only — it lowers the *button* press force, not the
     knob press, which is a different (encoder) switch.
   - **(e) Move press inputs to the top edge:** pressing down is
     inherently stable, which is why desk clocks put buttons there. This
     changes the user's layout, so it's his call.

### PCB orientation and what it changes

- The main PCB stands **parallel to the face**, at about 75 degrees.
  Gravity is irrelevant to the electronics. Assembly happens with the body
  lying face-down on the bench, exactly as before, so everything on the
  front of the board stays: panel shadow, switches, encoder, J501, ESP32.
- **Knob placement:** centre about **19 mm up the face** (lower third),
  not at mid-height. That's because the knob zone (about 26 mm wide) can't
  hold the 14.2 mm encoder courtyard and the 19.2 mm ESP32 side by side
  vertically unless the knob is low. Low is also better for the press
  problem above, because it shortens the tipping moment.
- **ESP32:** upper-left, with the U.FL near the top edge, so the **antenna
  goes inside the top wall**. That's RF-ideal: highest point, away from the
  table, above the ground plane. Clearance still needs checking against
  the part from `pilink-8wx`.
- **USB-C: this is a real problem.** "Rear exit" now means *perpendicular
  to the PCB*, but J401 (HRO TYPE-C-31-M-12) is a horizontal, edge-mount
  receptacle. On an upright board's edge it would point down or sideways,
  not rearward. Options:
  - **(i)** A **vertical-mount USB-C receptacle on the PCB's back side**,
    low and centred, exiting the back wall about 15 mm up between the legs.
    It needs a different part (with a stock check), **back-side assembly**
    (JLCPCB double-sided assembly costs more, or a through-hole-legged part
    hand-soldered), and a local back boss, because the receptacle is taller
    than the 5 mm back cavity.
  - **(ii)** Keep J401 at the PCB's bottom edge and add a short internal
    **USB-C pigtail to a rear panel-mount socket**. Cheap, hobby-standard
    and hand-assembled, but adds a cable and a part.
  - Edge exit downward is not an option (the plug can't fit under a 14 mm
    base), and edge exit sideways contradicts the confirmed rear exit.
  This was filed as investigation spike `pilink-0do`. **Decided: option (i),
  vertical receptacle on the PCB back.**
- **Legs:** a fixed (non-hinged) printed A-frame screwed to bosses on the
  back shell at about 40 mm up the face. A hinged kickstand would be
  gold-plating. Feet cover the screws. The body's own bottom is a
  horizontal strip about 14.5 mm deep with feet, so it doesn't stand on
  its front edge.

### Display FPC in the upright orientation: unchanged except the risks carried over from section 2

- The panel is a ZIF-latched 0.3 mm FPC, so gravity doesn't matter. The
  J-fold behind the panel into J501 on the PCB's front works exactly as in
  section 2, rotated with the board -- including both of section 2's open
  risks (the fold-height fit against the 3.4 mm gap, and the unresolved
  contact side), which are orientation-independent and carry over
  unchanged.
- **FPC toward the buttons (right) is still the better choice.** Assembly
  is still done face-down, and the panel flips out over 5 mm switches
  rather than the 20 mm encoder shaft. The 7.4 mm dead ledge and fold sit
  under the bezel between the window and the buttons.
- **J501:** long axis **vertical** (parallel to the panel's right edge),
  about 26 mm in from that edge, and offset about 7 mm **upward** of the
  panel centreline. The old "toward the rear" becomes "up" when the slab
  stands up. Exact numbers, the fold-height risk, and the contact-side
  question are all pending `pilink-7el.12` acting on `pilink-0o2`'s
  findings.

### PCB outline consequence

The main board is about **118 x 50 mm**, standing (inside a 122 x 56 face
with 2 mm walls). PR #33's 100 x 55 board is still incompatible: wrong
side for the encoder, wrong J501, no panel-shadow keep-out, and no plan for
the USB-C.

### Decisions (user, 2026-11-15): recorded in `.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`

1. **Press stability.** The **default is high-friction rubber/gel feet,
   pending a physical test** of a printed sample (the user's action). If the
   test shows that isn't enough, the fallbacks are tried in this order:
   weighted base (steel insert), then accepting two-handed/steadying
   presses, then moving press inputs to the top edge. None of the fallbacks
   is committed to in advance.
2. **USB-C: settled.** A **vertical-mount receptacle on the back of the
   PCB**, exiting the rear wall low, between the legs. No pigtail. Part
   selection and the back-side assembly approach are in `pilink-0do`.
3. **Rear legs: settled.** **Two splayed legs** (about +/-40 mm, feet about
   45-50 mm behind the front edge), not a single strut.

Also settled: FPC exits toward the buttons (right), and the proud knob is
accepted as-is.

4. **BOOTSEL/RESET (SW101/SW102):** these stay **front-side SMD** (no
   back-side assembly) and are reached by **paperclip pinholes in the top
   edge**. This replaces the section 1.3 suggestion of bottom-shell
   pinholes, which doesn't suit an upright body. **Caveat checked:** a pin
   coming down from the top moves parallel to the upright PCB, but PTS645
   is top-actuated, with its plunger facing the user. A vertical channel
   therefore **can't press the current part**.
   - **Fix:** change SW101/SW102 to a **side-actuated (right-angle) SMD
     tact switch** at the PCB's top edge. It still goes on the front side.
     Its actuator points up out of the board edge, under about a 1.5 mm
     top-wall pinhole.
   - **Where it fits:** the ~5 mm strip between the panel's top edge and the
     inner top wall (face 56 mm, panel 42 mm, 2 mm walls). Put it laterally
     over the panel's centre, near the RP2350B/flash cluster, which sits
     under the panel. That keeps it clear of the ESP32 (upper-left) and the
     button zone (right).
   - **Electrical cost:** about 20-30 mm of extra stub on the BOOTSEL /
     `QSPI_SS` chip-select net. Acceptable, but keep it away from the QSPI
     clock and data lines.
   - **Part selection:** `pilink-7el.10`.
   - **Fallback** if no stocked side-actuated part fits: keep PTS645 and use
     two small pinholes in the face's top bezel. Simple, but visible on the
     face.

## 7. Open verifications (filed as beads)

- `pilink-0o2`: FPC contact side, the J-fold with the bottom-contact J501,
  J501 height, a recheck against datasheet Rev 1v2, and the bend-radius
  guidance. This decides whether the J501 placement rule in section 2 holds.
- `pilink-g8a`: Encoder body height, shaft-length options and rotational
  torque. This covers the flush-knob conflict and knob-turn stability.
- `pilink-8wx`: Select the U.FL antenna part. Its size sets the antenna
  pocket in each option.
- `pilink-0do`: rear-facing USB-C for the upright body (vertical receptacle
  on the PCB back vs an internal pigtail to a rear panel socket).
- Note: `pilink-g8a` was retargeted. The proud knob is accepted, so it now
  confirms the detent torque and push force that the section 6c stability
  numbers depend on.
