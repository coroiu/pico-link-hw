# Product form factor: upright desk-clock body on two splayed rear legs

## Context

The physical product layout and overall size had never been decided.
Everything up to the PCB layout attempt (`pilink-7el.9`, PR #33) was
component-level work. That PR's 100 x 55 mm outline, with the encoder and
buttons on the right and J501 at the front centre, was a placement-tool
default, not a product decision. The user's only stated constraint was
**rotary knob on the left, screen in the middle, buttons on the right**.

A design proposal
(`docs/plans/2026-11-15-product-layout-proposal.md`) did three things:
- gathered the dimensions that drive the layout, from the actual
  datasheets and footprints:
  - display: 42 x 59 x 2.1 mm frame, 36.72 x 48.96 mm active area,
    asymmetric 7.39 mm chip-on-glass ledge, 33 mm FPC leaving a short edge;
  - encoder: EC11E body 12 x 11.6 mm, 20 mm shaft;
  - buttons: PTS645 6 x 6 mm, 5.0 mm tall;
- offered flat-slab, tilted-wedge and compact options;
- went through two misreadings of a hand sketch from the user (proposal
  sections 6a and 6b, kept for the record).

The user then confirmed the real intent directly: a small, nearly vertical
standing device, like a desk clock or photo frame, propped up by a rear
support. That is proposal section 6c. Its three open questions (press
stability, USB-C, legs) were answered by the user on 2026-11-15.

## Decision

- **Form factor:** an **upright body leaning back about 15 degrees** (face
  about 75 degrees from the table). One front face carries **knob left,
  screen middle, buttons right**.
  - Face about 122 W x 56 H mm.
  - Body about 14 mm thick.
  - About 58 mm tall standing.
  - Footprint about 122 x 50 mm including legs.
  - All figures are approximate; the proposal doc has the derivation.
- **Support:** **two splayed rear legs** (about +/-40 mm, feet about
  45-50 mm behind the front edge) as a fixed, non-hinged printed A-frame
  screwed to the back shell. Not a single strut.
- **PCB:** a single flat main board **standing parallel to the face**, about
  118 x 50 mm. All front-side placement rules from the proposal apply:
  - a panel-shadow keep-out with only low parts under the display;
  - J501 behind the panel with its long axis vertical;
  - the ESP32 upper-left, above the encoder;
  - the knob centre in the lower third of the face.
- **Display FPC exits toward the buttons (right).** It J-folds behind the
  panel into J501.
- **USB-C:** a **vertical-mount receptacle on the back of the PCB**, exiting
  the rear wall low, between the legs. No internal pigtail.
- **Knob:** the existing EC11E18244AU with its 20 mm shaft. A **proud knob
  (about 17 mm above the face) is accepted.** (Corrected from an earlier
  ~12.5 mm figure that misread the Alps catalogue's "7.5 max" dimension as
  a body height — it's a footprint dimension. Real heights above the PCB:
  housing ~4.5 mm, shaft tip ~24.5 mm; against the enclosure's own 7.5 mm
  face-to-PCB depth, the shaft tip lands ~17 mm past the face, with the
  ~7 mm bushing standing about 4 mm proud of the face. See `pilink-g8a`,
  `.research/findings/2026-11-15-encoder-ec11e18244au-specs.md`.)
- **BOOTSEL/RESET (SW101/SW102) stay front-side SMD parts**, with no
  back-side assembly, and are reached by **paperclip pinholes in the top
  edge** of the enclosure. The top edge is the easiest service surface to
  reach on an upright body. A pin entering from the top travels *parallel*
  to the PCB, so it **cannot press the current top-actuated PTS645**
  (its plunger faces the user). These two switches therefore change to a
  **side-actuated (right-angle) SMD tact switch**, still front-side, placed
  at the PCB's top edge in the ~5 mm strip above the panel and pressed
  straight down through about a 1.5 mm pinhole. Part selection is in
  `pilink-7el.10`. **Fallback** if no suitable side-actuated part is stocked:
  keep PTS645 and use two small pinholes in the face's top bezel instead.
  That's mechanically trivial but leaves visible holes on the face.
- **Press stability:** the **default is high-friction rubber/gel feet,
  pending a physical test** of a printed sample. If that proves
  insufficient, the fallbacks are tried in order: (1) weighted base,
  (2) accept two-handed/steadying presses, (3) move press inputs to the top
  edge. None of the fallbacks is committed to before the test.

## Rationale

- **Fits the real usage pattern.** Pico Link sits plugged in and gets
  occasional knob turns and button presses. An upright face is read almost
  head-on from a desk chair (a flat face is seen about 56 degrees off-axis),
  and the device takes very little desk depth.
- **Two legs, not one strut.** Knob turning applies a torque, which tries to
  roll the body over a front corner and a rear foot. Using EC11E18244AU's
  own confirmed detent torque (10±7 mN·m per Alps' own datasheet for this
  exact part, `pilink-g8a`; up to about 17 mN·m worst case) and an estimated
  110 g body:
  - single central strut: about 1.15-1.6x margin;
  - two legs at +/-40 mm: about 3x margin.
  Two legs also give the USB-C cable a clean path down the middle.
- **Vertical USB-C receptacle.** With the board upright, "rear exit" means
  perpendicular to the PCB. A vertical receptacle does that directly and
  avoids an extra cable and panel-mount part.
- **FPC toward the buttons.** During face-down assembly, the panel flips out
  over 5 mm switches instead of the encoder's 20 mm shaft, so latching the
  40-pin ZIF is much less fiddly. It costs about 4 mm of width, and the dead
  ledge sits under the bezel on the button side.
- **Top-edge service pinholes, front-side switches.** Putting the
  BOOTSEL/RESET switches on the back would need back-side assembly just for
  two service buttons. The back faces away from the user and the base sits
  against the table, while the top edge is right there. A right-angle
  switch keeps everything single-sided, and the pinhole stays a straight,
  short, printable channel.
- **Feet first for presses.** Presses push almost horizontally into a light
  upright body:
  - button press: about 2.5 N against about 1.75 N of friction;
  - knob press: about 5.8 N against about 2.6 N.
  Without help the device slides or tips. No leg geometry fixes this.
  Gel/adhesive-grip feet cost almost nothing and may be enough. The heavier
  fixes (a weighted base needs about 200 g of *added* steel for buttons,
  roughly 310 g total device weight, and 500 g+ added / 610 g+ total for
  the knob press; changing the layout) are only worth committing to once a
  physical test shows feet alone fail.

## Alternatives considered

- **Flat desk slab** (proposal Option A, about 118 x 52 x 14 mm) or
  **compact slab** (Option C, about 102 x 50 x 14 mm). Simpler shells, but
  the screen is viewed steeply off-axis. Not what the user wants.
- **20 degree tilted wedge** (Option B, 6a). Better readability than flat,
  but a misreading of the user's sketch.
- **Terraced two-peak shell** (6b). A misreading of the sketch, in which
  the rear leg looked like a second "peak". Rejected.
- **Single rear strut.** Marginal against knob-turning torque unless its
  foot is about 80 mm wide.
- **USB-C pigtail** from an edge-mount J401 to a rear panel socket. Cheap and
  hand-assembled, but an extra cable and part. The user chose the vertical
  receptacle.
- **BOOTSEL/RESET pinholes through the back or bottom.** Back access needs
  back-side SMT, the same cost problem as USB-C. The bottom is the small
  base against the table, which is awkward on an upright body. Rejected
  for the top edge.
- **Top-edge pinhole onto the existing top-actuated PTS645 via a printed
  lever/bell-crank.** That keeps the part, but a tiny printed lever is
  fragile and fussy. Rejected in favour of a right-angle switch.
- **Committing up front to a weighted base, two-handed use or top-edge
  buttons.** Deferred until a physical test.

## Consequences

- **PCB layout: full redesign, not a tweak of PR #33.**
  - PR #33's outline (100 x 55), encoder side, J501 orientation and
    position, missing panel-shadow keep-out and USB-C placement are all
    incompatible with this form factor.
  - The board must be re-placed and re-routed for the ~118 x 50 mm upright
    outline, after the `pilink-kt4` netlist fix.
  - The scripted placement + Freerouting pipeline, the schematic and the
    footprints otherwise carry over.
- **Schematic/BOM: J401 changes part.** The current HRO TYPE-C-31-M-12 is
  horizontal edge-mount. It needs replacing with a vertical-mount USB-C
  receptacle on the board's back side. That means either JLCPCB
  double-sided assembly (cost increase) or a through-hole-legged part
  soldered by hand. Selection is in `pilink-0do`.
- **Schematic/BOM: SW101/SW102 change part** to a side-actuated SMD tact
  switch (`pilink-7el.10`). Same nets, footprint change only. PCB placement:
  at the top edge, above the panel's centre region, clear of the ESP32
  (upper-left) and the button zone (right). The BOOTSEL line is the flash
  `QSPI_SS` net, and putting the switch at the top edge adds about
  20-30 mm of stub on that chip-select. That's fine for a chip select, but
  the re-placement should keep the stub off the QSPI clock/data bundle.
- **Enclosure (`pilink-8hx.*`):** front shell (face, window, button and knob
  openings), back shell (PCB mount, rear USB-C opening, leg bosses), a
  two-leg A-frame, feet pockets sized for gel/rubber pads, and an antenna
  location in the top wall. A weighted base stays possible as a fallback,
  so the base design shouldn't rule out adding a ballast pocket later.
- **Physical test required (the user):** print a sample, fit the feet, and
  check whether button and knob presses stay put. The result decides
  whether any fallback is needed.
- **Open verifications that still apply:**
  - `pilink-0o2`: display FPC contact side and the J501 placement rule;
  - `pilink-g8a`: **resolved** — encoder torque (10±7 mN·m) and push force
    (6 +2.5/-2 N) confirmed from Alps' own EC11E18244AU data, matching the
    figures already used here. Body height was initially misread as
    7.5mm max (that's a footprint dimension); corrected to housing ~4.5mm /
    shaft tip ~24.5mm above the PCB, moving the proud-knob figure above
    from ~12.5mm to ~17mm. See
    `.research/findings/2026-11-15-encoder-ec11e18244au-specs.md`;
  - `pilink-8wx`: antenna part.
  - `pilink-3ob`: **resolved** — re-verified the 6c envelope figures above
    against the corrected ~17 mm knob / ~4 mm bushing proud figures, and
    against the knob cap's own Ø18 mm (9 mm radius) size, not just the
    shaft-axis point. Standing height (~58 mm) and the table-contact
    footprint (~122 x 50 mm) are both unaffected: the knob cap's own top
    rim edge tops out around 31 mm above the floor (axis point ~22.8 mm
    plus 9 mm x cos(15 deg) ≈ 8.7 mm for the cap's radius), well under the
    58 mm body/leg top, and never touches the table. What does change:
    the knob's own forward reach past the body's base front edge. The
    shaft-axis point alone moves from about 7 mm (old, incorrect
    protrusion figure) to about 11.5 mm (corrected protrusion figure); the
    knob cap's lower-front rim edge — the device's true forward-most
    point, 9 mm x sin(15 deg) ≈ 2.3 mm further forward than the axis point
    — reaches about 13.8 mm. That gives a new overall bounding depth (knob
    rim to the back of the feet) of about 64 mm, versus the ~50 mm
    table-footprint depth. The proposal doc's 6c "Dimensions" section has
    the full derivation and the side-profile diagram's knob blob is
    redrawn to match (shifted ~4 mm further from the face, with every
    other diagram element left at its original position).
- **`AGENTS.md`** hardware summary gains a form-factor line pointing here.
