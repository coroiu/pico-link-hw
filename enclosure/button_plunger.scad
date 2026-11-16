// =================================================================
// Pico Link -- A/B/X/Y button plunger/cap
// Bead: pilink-8hx.3 (button-plunger portion only -- see "Scope" below)
//
// NOT RENDERED, NOT DIMENSION-CHECKED. OpenSCAD is not installed in
// the environment this file was authored in (see enclosure/README.md
// / AGENTS.md's "quality gates" section) -- no fit check has been
// run. Every dimension below is cited to a source doc or to
// enclosure/front_shell.scad's own already-merged constants; anything
// with no real source is explicitly marked as this file's own
// assumption. A human with OpenSCAD still needs to open this (ideally
// test-fit against a real front_shell.scad print and a real PTS645
// part) -- that's pilink-8hx.5/.6, not done here.
//
// SCOPE: this file designs the plunger/cap that sits IN the four
// Ø8.4mm button bores enclosure/front_shell.scad (pilink-8hx.2,
// merged) already cuts for A/B/X/Y -- not the bores themselves, which
// are out of scope here (front_shell.scad is an already-merged
// enclosure file; this bead only adds the part that occupies its
// holes). The encoder's own knob/shaft treatment, also named in this
// bead's acceptance criteria, is NOT covered by this file -- see the
// "Encoder knob" note at the bottom of this comment block.
//
// ============================== Why this geometry ==============================
//
// Real switch: SW305-SW308 are C&K PTS645SK50SMTR92LFS (LCSC
// C221872), confirmed from hardware/README.md's BOM table (grep
// "SW305" there). This is a 6x6mm SMD tactile switch, "PTS645"
// family. Per C&K's own PTS645 ordering key (decoded against this
// exact part number in
// .research/findings/2026-11-15-encoder-ec11e18244au-specs.md's
// "Lower-force PTS645 mitigation options" section): the force letter
// is "K" (2.6N actuation force), and the trailing digits "50" encode
// the part's overall height above the PCB mounting surface -- 5.0mm,
// "matching the current footprint/courtyard exactly". That 5.0mm
// figure is this file's SWITCH_HEIGHT_ABOVE_PCB below.
//
// Switch travel: NOT independently confirmed against this exact LCSC
// SKU's own dimensioned drawing in this repo's research -- no finding
// here measures PTS645SK50SMTR92LFS's travel specifically. Using the
// well-documented generic figure for the whole PTS645 "5x" sub-family
// (C&K's own PTS645 series datasheet, ckswitches.com, states 0.25mm
// nominal travel across its standard-travel variants): SWITCH_TRAVEL
// = 0.25mm below is therefore flagged as THIS FILE'S ASSUMPTION, not
// an independently re-verified figure, per this bead's own
// instructions.
//
// Depth budget: enclosure/front_shell.scad's own FACE_T (2.0mm plate
// thickness) and FRONT_SHELL_DEPTH (7.5mm outer-face-to-PCB depth) are
// restated below with the same values and the same citation (the
// upright-desk-clock ADR / product-layout-proposal 6c). Combined with
// the switch height above, this reproduces a number the proposal
// *already* explains deliberately: section 6c's body-thickness
// breakdown is "face 2.0, 5.5mm to the PCB (5.0mm switches, 3.3mm
// panel stack, J501 about 2mm)" -- i.e. the 5.5mm inner-face-to-PCB
// gap was *sized* against the switches' own 5.0mm height, leaving
// exactly 0.5mm of spare depth at the button locations. That 0.5mm
// (INNER_FACE_TO_ACTUATOR_GAP below) is this file's real, tight,
// *intentional* design budget for the whole retention-shoulder +
// stem + working-clearance stack -- not a bug, but still worth
// flagging loudly: 0.5mm split three ways leaves sub-millimetre
// features that are genuinely tight for FDM. See "OPEN ITEMS" at the
// bottom.
//
// Retention: a single flange/shoulder wider than the Ø8.4mm bore,
// sitting on the inner-face side, physically cannot pass back out
// through the bore in either direction -- it is what stops the cap
// both from popping out the front (switch's own dome pushing back) and
// from being pushed/falling all the way through into the cavity. The
// cap must be dropped into the shell cavity from behind (inside) before
// the two shells are joined, since the flange is wider than the bore
// it sits behind -- an assembly-order note, not modeled here.
//
// Encoder knob: this bead's own acceptance criteria also names the
// EC11E18244AU encoder's knob/shaft treatment ("confirmed against the
// actual encoder part's datasheet, not assumed"). That is a
// genuinely separate design problem (a knob press-fit or screwed onto
// a 6mm D-shaft, not a plunger through a bore) and is NOT designed in
// this file -- out of the task scope this file was written against.
// Filed as a follow-up bead (discovered-from pilink-8hx.3) rather than
// silently left undone; see that bead for the open AC gap this
// creates against pilink-8hx.3 as a whole.
// =================================================================

$fn = 48;

/* ====================== Shell geometry (restated, cited) ======================
   Values copied from enclosure/front_shell.scad (pilink-8hx.2, merged)
   rather than `include`d, to keep this file's own units self-
   contained and independently readable -- re-derive/cross-check
   against that file's own constants if either ever changes. */

// Face-plate thickness. Source: front_shell.scad's FACE_T (== WALL,
// 2.0mm), itself from docs/plans/2026-11-15-product-layout-proposal.md
// section 6c, "Body thickness": "face 2.0 ...".
FACE_T = 2.0;

// Outer-face-to-PCB depth. Source: front_shell.scad's
// FRONT_SHELL_DEPTH (== FACE_T + GAP_FACE_TO_PCB = 2.0 + 5.5 = 7.5mm),
// itself from proposal 6c: "5.5 mm to the PCB (5.0 mm switches, 3.3 mm
// panel stack, J501 about 2 mm)" -> 2.0 + 5.5 = 7.5mm.
FRONT_SHELL_DEPTH = 7.5;

// Button bore diameter actually cut in front_shell.scad
// (BUTTON_BORE_DIA = BUTTON_CAP_DIA + BUTTON_BORE_CLEARANCE = 8.0 +
// 0.4 = 8.4mm). Restated here, not re-derived -- this file's cap must
// fit the bore front_shell.scad already committed to.
BORE_DIA = 8.4;

/* ============================ Switch (SW305-308) ============================
   C&K PTS645SK50SMTR92LFS, LCSC C221872. Source: hardware/README.md's
   BOM table row for SW305-SW308, and
   .research/findings/2026-11-15-encoder-ec11e18244au-specs.md's
   decode of this exact part's ordering-key suffix. */

// Overall switch height above the PCB mounting surface, at rest
// (actuator top). Source: the "50" suffix in PTS645SK50SMTR92LFS, per
// the research finding above -- "the digits after the force letter
// (50) are the 5.0mm actuator height, matching the current
// footprint/courtyard exactly".
SWITCH_HEIGHT_ABOVE_PCB = 5.0;

// Switch travel (how far the actuator depresses before bottoming out).
// ASSUMPTION, not confirmed against this exact SKU's own datasheet in
// this repo -- using C&K's generic published PTS645-series figure
// (ckswitches.com PTS645 datasheet, standard-travel variants: 0.25mm
// nominal). Flagged per this bead's own instructions; informational
// only below (used for the optional "pressed" preview, not consumed by
// the resting-position geometry).
SWITCH_TRAVEL = 0.25; // mm, ASSUMED generic PTS645 figure, not SKU-specific

// Actuator's own round contact-button diameter. NOT confirmed from any
// dimensioned PTS645SK50SMTR92LFS drawing read for this bead --
// ASSUMED conservatively small (most 6x6mm PTS645-family actuator caps
// are roughly 3.1-4.3mm across) so this file's narrow stem (below)
// reliably lands within the real button's area regardless of the
// exact figure.
SWITCH_ACTUATOR_DIA_ASSUMED = 3.5; // mm, ASSUMED

/* ========================== Depth budget (derived) ========================== */

// Distance from the outer face to the actuator's resting top surface.
ACTUATOR_Z = FRONT_SHELL_DEPTH - SWITCH_HEIGHT_ABOVE_PCB; // 7.5 - 5.0 = 2.5mm

// Spare depth between the plate's inner face and the actuator's
// resting top -- this is the ENTIRE budget available for this file's
// retention flange + stem + working clearance. Matches proposal 6c's
// own "5.5mm to PCB (5.0mm switches...)" breakdown (5.5 - 5.0 = 0.5mm
// spare) almost exactly -- not a coincidence, the enclosure's own
// depth stack-up was sized against this switch height.
INNER_FACE_TO_ACTUATOR_GAP = ACTUATOR_Z - FACE_T; // 2.5 - 2.0 = 0.5mm

/* ============================== Plunger geometry ============================== */

// Cap diameter: matches front_shell.scad's own BUTTON_CAP_DIA (8.0mm),
// the figure its BORE_DIA was itself built around.
CAP_DIA = 8.0;

// Per-side clearance to the bore -- (BORE_DIA - CAP_DIA)/2 = 0.2mm,
// inside the bead's own suggested 0.15-0.2mm/side FDM clearance range.
CAP_CLEARANCE_PER_SIDE = (BORE_DIA - CAP_DIA) / 2; // 0.2mm

// Head (shaft) length: fills the ENTIRE bore depth (FACE_T, 2.0mm) for
// a long, non-wobbly guided fit and a flush outer face at rest -- own
// choice, not independently sourced beyond matching FACE_T.
CAP_HEAD_LEN = FACE_T;

// Small cosmetic bevel on the cap's outer (visible) edge only -- own
// styling choice, not sourced, same spirit as front_shell.scad's
// CORNER_RADIUS ("own styling choice ... easy to retune in a later
// styling pass"). Purely a surface chamfer on material that stays
// above the bore -- does not change the fit inside the bore itself.
CAP_CHAMFER = 0.3;

// Retention flange/shoulder: wider than the bore so it cannot pass
// back through in either direction -- the "simple retention feature"
// this bead's description asks for. Diameter is this file's own
// choice (comfortably wider than the 8.4mm bore for a solid printed
// shoulder under light tact-switch loads, ~2.6N per the BOM part);
// thickness is deliberately thin because it has to share the tiny
// 0.5mm INNER_FACE_TO_ACTUATOR_GAP budget with the stem below.
FLANGE_DIA = 11.0; // mm, own choice (>BORE_DIA for a positive stop)
FLANGE_T   = 0.2;  // mm, own choice -- thin disk, stop-only, no load-bearing need

// Working clearance: the stem is deliberately built a touch SHORT of
// the actuator's exact resting height, so ordinary print tolerance
// (over-extrusion, first-layer squish) is more likely to leave a tiny
// DEAD-TRAVEL gap than to PRELOAD the switch (i.e. hold it
// permanently, marginally pressed) -- preload is the worse failure
// mode for a tact switch. Own choice, not sourced.
WORKING_CLEARANCE = 0.1; // mm

// Stem: the narrow part that actually reaches the actuator. Diameter
// kept at/under SWITCH_ACTUATOR_DIA_ASSUMED so it lands within the
// real button's own contact area regardless of the surrounding
// housing's exact height (unconfirmed from a dimensioned drawing --
// see the switch section above). Length is whatever is left of the
// 0.5mm budget after the flange and the working clearance.
STEM_DIA = 3.0; // mm, own choice, < SWITCH_ACTUATOR_DIA_ASSUMED (3.5mm)
STEM_LEN = INNER_FACE_TO_ACTUATOR_GAP - FLANGE_T - WORKING_CLEARANCE;
// = 0.5 - 0.2 - 0.1 = 0.2mm -- GENUINELY TIGHT. See OPEN ITEMS below;
// this is the single most important thing pilink-8hx.5/.6 needs to
// verify on a real print, more so than the general "not rendered"
// disclaimer that applies to every file in this directory.

assert(STEM_LEN > 0,
    "STEM_LEN went non-positive -- FLANGE_T + WORKING_CLEARANCE exceeds the real 0.5mm depth budget, re-check the constants above");

/* ============== Optional preview: cap depressed by SWITCH_TRAVEL ==============
   Purely informational -- shifts the whole plunger back by
   SWITCH_TRAVEL + WORKING_CLEARANCE to show how far the flush cap
   face recesses below the outer face at full press. Not used for the
   resting-position geometry above; does not change CAP/FLANGE/STEM
   sizing. */
PREVIEW_PRESSED = false;
preview_offset = PREVIEW_PRESSED ? (SWITCH_TRAVEL + WORKING_CLEARANCE) : 0;

/* ================================ Geometry ================================ */

// One A/B/X/Y plunger, modeled with Z=0 at the outer (visible) face
// and Z increasing INTO the enclosure, matching front_shell.scad's own
// convention. The resting position (PREVIEW_PRESSED = false) has the
// cap's outer face exactly flush with Z=0.
module button_plunger() {
    translate([0, 0, preview_offset]) {
        // Head: fills the bore (Z 0 .. CAP_HEAD_LEN), flush outer face,
        // small cosmetic chamfer on the visible top edge only.
        translate([0, 0, CAP_CHAMFER])
            cylinder(h = CAP_HEAD_LEN - CAP_CHAMFER, d = CAP_DIA);
        cylinder(h = CAP_CHAMFER, d1 = CAP_DIA - 2 * CAP_CHAMFER, d2 = CAP_DIA);

        // Retention flange: right behind the head, wider than the
        // bore -- cannot pass back through it either direction.
        translate([0, 0, CAP_HEAD_LEN])
            cylinder(h = FLANGE_T, d = FLANGE_DIA);

        // Stem: narrow, reaches toward the actuator. Its free (far)
        // end sits WORKING_CLEARANCE short of the actuator's real
        // resting height (ACTUATOR_Z) -- see WORKING_CLEARANCE above.
        translate([0, 0, CAP_HEAD_LEN + FLANGE_T])
            cylinder(h = STEM_LEN, d = STEM_DIA);
    }
}

// Four identical plungers laid out on a flat print plate for
// convenience (A/B/X/Y all share this same geometry -- only their
// bore position on the real board differs, which is front_shell.scad's
// concern, not this part's). Spacing is an arbitrary, generous pitch
// for slicer clearance between prints, not a reference to the
// diamond's real board-space geometry.
PRINT_PITCH = 16; // mm, own choice, print-plate spacing only
module button_plungers_x4() {
    for (ix = [0, 1]) for (iy = [0, 1])
        translate([ix * PRINT_PITCH, iy * PRINT_PITCH, 0])
            button_plunger();
}

button_plungers_x4();

/* ================================ Open items ================================
   1. No OpenSCAD render/fit check was possible -- not installed in
      this environment. Needs a human with OpenSCAD AND, ideally, a
      real printed sample test-fitted against a real
      PTS645SK50SMTR92LFS part and a real front_shell.scad print
      (pilink-8hx.5/.6).
   2. STEM_LEN (0.2mm) and FLANGE_T (0.2mm) are both sub-millimetre,
      splitting an intentionally tight 0.5mm total depth budget
      (INNER_FACE_TO_ACTUATOR_GAP) that the enclosure's own 5.5mm
      face-to-PCB gap was sized against (5.5mm gap - 5.0mm switch
      height = 0.5mm spare, per proposal 6c). This is the single
      highest-risk dimension in this file for real FDM printing --
      more so than the general "not rendered" caveat. If a real print
      shows the stem too fragile/short to reliably engage, the two
      documented mitigations are: (a) rebalance FLANGE_T/STEM_LEN/
      WORKING_CLEARANCE within the same 0.5mm (e.g. thinner flange,
      longer stem), which this file's named constants make a one-line
      change; or (b) revisit GAP_FACE_TO_PCB in front_shell.scad
      itself for more depth at the button locations specifically --
      out of this file's scope (front_shell.scad is a separate,
      already-merged file), filed as a question for a human/follow-up
      bead rather than silently reworked here.
   3. SWITCH_TRAVEL (0.25mm) is a generic PTS645-family figure, not
      independently confirmed against PTS645SK50SMTR92LFS's own
      dimensioned drawing in this repo's research -- flagged per the
      task brief's own instruction. Informational only; does not drive
      the resting-position geometry.
   4. SWITCH_ACTUATOR_DIA_ASSUMED (3.5mm) and the derived STEM_DIA
      (3.0mm) are this file's own assumption -- no PTS645SK50SMTR92LFS
      dimensioned drawing confirming the real actuator button diameter
      was found. If the real button is smaller than assumed, the stem
      may not land centered on it; confirm against a real part or a
      C&K mechanical drawing before finalizing.
   5. The bore itself (front_shell.scad, merged, out of scope here) is
      a straight-cut cylinder with no entry chamfer, even though this
      bead's own original description mentions "chamfered bores" --
      noted as a discrepancy between the bead text and the already-
      landed shell geometry, not fixed here (would require editing
      front_shell.scad, outside this file's scope). This cap's own
      CAP_CHAMFER is a cosmetic edge bevel on the cap only and does not
      address that gap.
   6. This file does NOT cover the encoder (SW303, EC11E18244AU) knob/
      shaft treatment that this bead's acceptance criteria also names.
      Filed as a separate follow-up bead (discovered-from
      pilink-8hx.3) -- see the PR/bead notes for pilink-8hx.3.
*/
