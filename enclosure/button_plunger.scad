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
// C221872), confirmed from hardware/BOM.md's BOM table (grep
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
// Retention: a flange/shoulder (now a ring, with a relief pocket over
// the actuator -- see FLANGE_DIA/RELIEF_DIA below) wider than the
// Ø8.4mm bore, sitting on the inner-face side, physically cannot pass
// out through the bore. It only stops OUTWARD travel (the switch's
// own spring pushing the cap out the front). INWARD travel is stopped
// by the switch itself; before the back shell/PCB is fitted nothing
// stops the cap falling back into the cavity. The cap must be dropped into the shell cavity from behind
// (inside) before the two shells are joined, since the flange is wider
// than the bore it sits behind -- an assembly-order note, not modeled
// here.
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
   C&K PTS645SK50SMTR92LFS, LCSC C221872. Source: hardware/BOM.md's
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
// this bead's description asks for.
//
// REVIEW FIX (PR #56, NOT APPROVED round 1): the original FLANGE_DIA
// (11.0mm) was too wide on two independent counts, both checked
// against front_shell.scad's (pilink-8hx.2, merged) own geometry:
//   - front_shell.scad's panel_ledge() (front_shell.scad:476-483) is
//     a rectangle PANEL_W + 2*LEDGE_W wide (59 + 2*2 = 63mm) centred
//     on PANEL_CX (board_to_x(57.5) = 59.5mm); its right edge sits at
//     board x = 57.5 + 59/2 + 2.0 = 89.0mm. board_to_x() is a pure
//     +WALL offset, so board-space and shell-space distances are the
//     same. The X button (front_shell.scad BTN_X, board (94,34)) is
//     only 94 - 89 = 5.0mm from that edge -- so the flange radius at
//     that button must stay under 5.0mm. The old Ø11 flange (radius
//     5.5mm) intruded ~0.5mm into the ledge there -- the X cap
//     physically couldn't seat.
//   - the diamond's own button pitch is 8mm in both board X and Y
//     (front_shell.scad BTN_Y/BTN_X/BTN_B/BTN_A), so the diagonal
//     pitch between adjacent buttons (e.g. X to Y, X to A) is
//     hypot(8,8) = 11.3137mm. With Ø11 flanges that left only 0.31mm
//     nominal gap between adjacent flanges -- less than the caps'
//     own BORE_DIA-CAP_DIA = 0.4mm of bore play, so adjacent flanges
//     could touch/bind if both caps shifted toward each other.
// ROUND 3 FIX: FLANGE_DIA = BORE_DIA + 0.6mm (Ø9.0mm, radius 4.5mm;
// 0.3mm radial overlap past the bore edge each side, still a positive
// stop under the ~2.6N switch load). Ledge clearance at the X button
// (5.0mm edge distance): 0.5mm nominal; 0.3mm worst case once the
// cap's 0.2mm radial bore play is included (cap shifted toward the
// ledge). Diagonal gap to the next flange: 11.31 - 9.0 = ~2.3mm
// nominal, ~1.9mm worst case with both caps shifted toward each other
// (0.2mm each) -- far above zero. Retention holds: Ø9.0 > Ø8.4 bore.
FLANGE_DIA = BORE_DIA + 0.6; // 9.0mm, radius 4.5mm

// Thickness: a real structural ring now (not the old fragile 0.2mm
// single-layer disc cantilevered off the stem -- also a review
// finding). Picked from the 1.0-1.4mm range the review suggested,
// sized against the RELIEF_DIA pocket below rather than the tight
// on-axis INNER_FACE_TO_ACTUATOR_GAP budget.
FLANGE_T = 1.2; // mm

// Relief pocket: REVIEW FIX for the "Important" finding that the
// original design applied the full on-axis INNER_FACE_TO_ACTUATOR_GAP
// (0.5mm) budget to the flange EVERYWHERE, when that worst case only
// actually applies directly over the switch's actuator. Off-axis
// (beside the actuator, over the switch's own housing) there's more
// real clearance: the switch housing sits SWITCH_BODY_OFFAXIS_RELIEF
// lower than the actuator's own resting top there, per the review.
// That figure is NOT independently confirmed against this exact SKU's
// own dimensioned drawing in this repo's research (same tier of
// assumption as SWITCH_TRAVEL/SWITCH_ACTUATOR_DIA_ASSUMED above, and
// not tightened further here per the review's own note not to rely on
// anything tighter than what's already flagged) -- it is used as-is,
// giving an off-axis budget of INNER_FACE_TO_ACTUATOR_GAP +
// SWITCH_BODY_OFFAXIS_RELIEF = 0.5 + 1.5 = 2.0mm for the flange RING
// (the part of the flange outside this pocket), with FLANGE_T (1.2mm)
// using well under that (0.8mm to spare).
//
// The pocket itself is a through-void in the flange's centre,
// concentric with the stem, so the stem can pass through the flange's
// thickness unobstructed and keep going to reach the actuator (see
// STEM_LEN below) without the flange's own material bottoming out on
// the actuator first. Diameter kept bigger than both STEM_DIA (3.0mm)
// and SWITCH_ACTUATOR_DIA_ASSUMED (3.5mm), with margin, so neither the
// stem nor the actuator can catch on the ring's inner edge.
SWITCH_BODY_OFFAXIS_RELIEF = 1.5; // mm, per PR #56 code review finding, ASSUMED (not re-confirmed against a dimensioned drawing)
RELIEF_DIA = 4.5; // mm, > STEM_DIA and > SWITCH_ACTUATOR_DIA_ASSUMED

assert(FLANGE_T <= INNER_FACE_TO_ACTUATOR_GAP + SWITCH_BODY_OFFAXIS_RELIEF,
    "FLANGE_T exceeds the off-axis clearance budget -- the flange ring would bottom out on the switch housing beside the actuator");

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
// see the switch section above), and under RELIEF_DIA so it clears
// the flange ring's inner edge as it passes through the pocket.
//
// REVIEW FIX: length is now the full on-axis budget minus only the
// working clearance -- NOT minus FLANGE_T any more. The flange's own
// thickness no longer sits stacked on the stem's on-axis path (it's
// a ring in the relief pocket's off-axis annulus instead, see
// RELIEF_DIA above), so it no longer eats into this length.
STEM_DIA = 3.0; // mm, own choice, < SWITCH_ACTUATOR_DIA_ASSUMED (3.5mm) and < RELIEF_DIA (4.5mm)
STEM_LEN = INNER_FACE_TO_ACTUATOR_GAP - WORKING_CLEARANCE;
// = 0.5 - 0.1 = 0.4mm -- still sub-millimetre and still the highest-
// risk dimension in this file for a real FDM print (double the
// pre-fix 0.2mm, but not generous), more so than the general "not
// rendered" disclaimer that applies to every file in this directory.
// See OPEN ITEMS below for what pilink-8hx.5/.6 needs to verify.

assert(STEM_LEN > 0,
    "STEM_LEN went non-positive -- WORKING_CLEARANCE exceeds the real 0.5mm on-axis depth budget (INNER_FACE_TO_ACTUATOR_GAP), re-check the constants above");

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
        // bore -- cannot pass back through it either direction. Now a
        // RING, not a solid disc: the relief pocket (RELIEF_DIA) is
        // removed from its centre so the stem can pass straight
        // through it to reach the actuator, and so the ring's own
        // thickness only has to clear the switch housing OFF-axis
        // (see RELIEF_DIA/SWITCH_BODY_OFFAXIS_RELIEF above), not the
        // tight on-axis actuator gap.
        translate([0, 0, CAP_HEAD_LEN])
            difference() {
                cylinder(h = FLANGE_T, d = FLANGE_DIA);
                translate([0, 0, -0.5])
                    cylinder(h = FLANGE_T + 1, d = RELIEF_DIA);
            }

        // Stem: narrow, reaches toward the actuator, starting right
        // after the head and passing through the flange's own relief
        // pocket (same start Z as the flange -- they occupy different
        // radii, not different Z ranges, so neither needs to wait for
        // the other to end). Its free (far) end sits WORKING_CLEARANCE
        // short of the actuator's real resting height (ACTUATOR_Z) --
        // see WORKING_CLEARANCE above.
        translate([0, 0, CAP_HEAD_LEN])
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
   2. STEM_LEN (0.4mm) is now only a short boss inside a deeper
      ring (the 1.2mm flange ring surrounds the relief pocket). FLAG
      FOR THE TEST PRINT: check whether the stem is needed at all, or
      whether the cap/ring can press the actuator directly.
      STEM_LEN (0.4mm) is still sub-millimetre, drawing on the
      intentionally tight 0.5mm on-axis depth budget
      (INNER_FACE_TO_ACTUATOR_GAP) that the enclosure's own 5.5mm
      face-to-PCB gap was sized against (5.5mm gap - 5.0mm switch
      height = 0.5mm spare, per proposal 6c). REVIEW FIX (round 2):
      the flange itself no longer shares that same on-axis budget --
      it's now a thicker (1.2mm) ring sitting in a relief pocket
      (RELIEF_DIA) that only has to clear the switch housing OFF-axis
      (a 2.0mm budget, per SWITCH_BODY_OFFAXIS_RELIEF), not stacked on
      top of the stem's own on-axis path. STEM_LEN is still the
      single highest-risk dimension in this file for real FDM
      printing -- more so than the general "not rendered" caveat. If
      a real print shows the stem too fragile/short to reliably
      engage, the two documented mitigations are: (a) trim
      WORKING_CLEARANCE within the same 0.5mm (the only other term in
      STEM_LEN's formula now), which this file's named constants make
      a one-line change; or (b) revisit GAP_FACE_TO_PCB in
      front_shell.scad itself for more depth at the button locations
      specifically -- out of this file's scope (front_shell.scad is a
      separate, already-merged file), filed as a question for a
      human/follow-up bead rather than silently reworked here.
      SWITCH_BODY_OFFAXIS_RELIEF (1.5mm) itself is also unverified
      against a dimensioned drawing (see its own comment) -- the
      relief-pocket fix depends on that figure being roughly right.
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
      landed shell geometry. Per the PR #56 code review, this is filed
      as its own follow-up bead (pilink-ci0, discovered-from
      pilink-8hx.3) rather than fixed here (would require editing
      front_shell.scad, outside this file's scope). This cap's own
      CAP_CHAMFER is a cosmetic edge bevel on the cap only and does not
      address that gap.
   6. This file does NOT cover the encoder (SW303, EC11E18244AU) knob/
      shaft treatment that this bead's acceptance criteria also names.
      Filed as a separate follow-up bead (discovered-from
      pilink-8hx.3) -- see the PR/bead notes for pilink-8hx.3.
*/
