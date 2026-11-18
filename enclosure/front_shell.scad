// =================================================================
// Pico Link -- front shell (bezel / face plate)
// Bead: pilink-8hx.2
//
// NOT RENDERED, NOT DIMENSION-CHECKED. OpenSCAD is not installed in
// the environment this file was authored in (see enclosure/README.md
// / AGENTS.md's "quality gates" section) -- no fit check has been
// run. Every dimension below is cited to a source doc in the comment
// next to it; cross-reference before trusting a number, the same way
// this file's own author had to. A human with OpenSCAD (and ideally
// the sibling back-shell bead, pilink-8hx.1) still needs to open this
// and check real fit -- that's pilink-8hx.5, not done here.
//
// SIMPLIFICATION, flagged up front: this models a FLAT rectangular
// shell (face plate + straight perimeter skirt), not the real
// ~15-degree-leaning desk-clock body profile from the ADR/proposal --
// that aesthetic body shape (lean, final corner/edge treatment) is
// left for a later styling pass, once this bead and pilink-8hx.1 have
// both landed and can be checked together for fit. What this file
// focuses on getting right, from the real placed-and-routed board, is
// every opening's X/Y position and the window's size -- that is this
// bead's actual scope per its acceptance criteria.
//
// REVISION pilink-3ym (2026-11-16): U201 moved to B.Cu and the A/B/X/Y
// diamond was restored to centre (102,25) by pilink-hdl (PR #60). The four
// button bores below are back on (102,17)/(94,25)/(110,25)/(102,33); the
// knob (SW303, y=25) was never affected. Header notes below that mention
// the pilink-2yw diamond shift are history only.
//
// REVISION (code-review NOT APPROVED on 8da37dc, fixed here): (1) the
// display glass now actually registers at Z=RECESS_DEPTH (1.2mm) below
// the outer face -- see display_cutouts()/panel pocket below -- instead
// of the old geometry's real Z=FACE_T (2.0mm); (2) the board-to-face Y
// mapping is confirmed (not just inherited) to match back_shell.scad's
// own landed derivation -- see board_to_y() below; (3) the knob/encoder
// and A/B/X/Y diamond positions are updated for pilink-2yw's merged
// board re-placement (U201 moved off the knob column; knob -> true
// board-vertical-centre; diamond shifted down 9mm), and the stale
// "lower third" knob description is corrected.
//
// REVISION pilink-8hx.7 (2026-11-18): the shells are joined by four M2
// screws from the back into brass heat-set inserts in standoffs here, one
// per PCB mounting hole, clamping the PCB between the standoffs and the
// back shell's bosses; and the inner part of the rim carries on past the
// seam as a lip that locates the PCB laterally (assembly is face-down).
// See "Shell fasteners" below and common.scad.
// =================================================================

/* [Fasteners] */
// Melt-in hole for the M2x4x3.2 heat-set insert, mm: 0.2 under the 3.2 knurl OD, so the knurl cuts in. Insert hole-size charts give 3.0-3.2 for M2 (tighter in PLA, looser in harder plastics); small FDM holes also print ~0.1-0.2 small. Tune to the printer.
INSERT_HOLE_D = 3.0; // [2.6:0.05:3.4]
// Extra pocket depth below the insert, mm: room for displaced plastic and for the screw tip.
INSERT_POCKET_EXTRA = 1.0; // [0.3:0.1:1.5]
// Standoff wall around the insert's knurl OD, mm (>= 1.2: 3 perimeters at 0.4).
STANDOFF_WALL = 1.4; // [1.2:0.1:2.5]

/* [Hidden] */
$fn = 48;

// pilink-6lz: board size, wall, running clearance, FACE_W/FACE_H, the
// board<->face mapping (board_to_x/board_to_q) and every board-local part
// position (panel, knob, diamond, pinholes, mounting holes) now live in ONE
// place, shared with the back shell and antenna mount.
include <common.scad>

/* ============================== Face / body ============================== */

// Face outline: FACE_W x FACE_H from common.scad (127.5 x 56 since
// pilink-6lz; the ADR's "about 122 W x 56 H" was for the older 118mm board).

// Face-plate thickness (WALL, common.scad, is also the perimeter wall).
// Source: proposal 6c "Body thickness" breakdown: "face 2.0 ... and a
// 2.0 mm back wall".
FACE_T = WALL;

// Depth from the outer face surface to the PCB's front surface / this
// shell's rim (where it meets the back shell, pilink-8hx.1). Since
// pilink-8hx.7 the PCB rests on this shell's insert standoffs at this depth
// and is clamped there by the back shell's bosses; the stack terms are
// shared in common.scad (FRONT_CAVITY = 5.5, Z_PCB_FRONT = 7.5).
// Source: proposal 6c "Body thickness": "face 2.0, 5.5 mm to the PCB
// (5.0 mm switches, 3.3 mm panel stack, J501 about 2 mm)" -> 2.0 + 5.5
// = 7.5 mm. The same 7.5 mm figure is independently cited in proposal
// section 1.2's "Conflict with the aesthetic ADR" note ("the face at
// about 7.5 mm above the PCB") and in this bead's own comment log
// ("the board-to-inner-face gap is only ~5.5mm").
GAP_FACE_TO_PCB = FRONT_CAVITY; // 5.5 mm, inner face surface to PCB front surface
FRONT_SHELL_DEPTH = FACE_T + GAP_FACE_TO_PCB; // 7.5 mm (= Z_PCB_FRONT)
assert(FRONT_SHELL_DEPTH == Z_PCB_FRONT, "front shell depth must match the shared stack");

// Corner radius: own styling choice, NOT sourced from a doc -- the
// aesthetic ADR (.planning/decisions/2026-11-15-enclosure-aesthetic-
// direction.md) only says "deliberate but not aggressive corner
// radii", no number given. Pick something modest; easy to retune in
// a later styling pass.
//
// pilink-lmg: 3.0mm, matching back_shell.scad's CORNER_R, so the outer rim
// no longer steps at the Z=7.5 butt joint (was 6.0 here vs 3.0 there).
// Picked 3.0 over 6.0 because the back shell's cavity corner radius derives
// from CORNER_R and its cavity must clear the PCB's square 122.5x50 corners
// (pilink-cix), and a smaller radius only ADDS material at the four outer
// corners / frees cavity corner volume (inner radius 6-2=4 -> 3-2=1), so
// no face feature (display window, encoder bore, button bores, SW101/102
// pinholes, mounting bosses) loses any clearance. check_fit.py reads this
// value for its rim-mismatch check.
CORNER_RADIUS = 3.0;

/* ===================== Face <-> board coordinate mapping =====================
   board_to_x() / board_to_q() are defined once in common.scad:
     X = board_x + MARGIN_X (2.5),  Q = QTOP (53) - board_y.
   The board is centred in the cavity with BOARD_CLEARANCE_X/Y of running
   clearance per side (common.scad). Q is "up the face", 0 at the bottom outer
   edge -- this file's own Y axis. */
function board_to_y(by) = board_to_q(by);

/* ============================ Display window ============================
   Crystalfontz CFAF240320A0-024SN, landscape (rotated 90deg from its
   native 240x320 per .planning/decisions/2026-11-15-display-panel-
   crystalfontz-cfaf240320a0.md). Raw figures from
   docs/plans/2026-11-15-product-layout-proposal.md section 1.1, which
   cites the Crystalfontz datasheet directly. */

// Panel outline (landscape, 59 x 42) and its board position: common.scad.

// Active area (landscape). Confirmed both by the display ADR and
// proposal 1.1's table ("Active area (AA) 36.72 W x 48.96 H" stated
// in native PORTRAIT -- landscape swaps W/H).
AA_W = 48.96;
AA_H = 36.72;

// Active-area insets from the panel outline. Portrait table values
// re-mapped to landscape per proposal 1.1's own landscape note and
// the ADR's FPC-right decision:
//  - portrait left/right (2.64mm, symmetric) -> landscape top/bottom
//    (still symmetric, unaffected by which way the FPC exits);
//  - portrait top (2.65mm) / bottom-COG-ledge (7.39mm) -> landscape
//    left/right, with the COG/FPC side landing on whichever edge the
//    FPC physically exits. FPC exits toward the buttons (right,
//    larger-X side of this board) per the ADR ("Display FPC exits
//    toward the buttons (right)") -- so the bigger 7.39mm inset is on
//    the RIGHT in this file's X axis.
AA_INSET_TOP    = 2.64;
AA_INSET_BOTTOM = 2.64;
AA_INSET_LEFT   = 2.65; // knob side
AA_INSET_RIGHT  = 7.39; // button / FPC / COG-ledge side

// Active-area centre, board-local. The panel position (PANEL_BOARD_X0.. in
// common.scad, from pilink-4qc) puts it at (61.25, 25): AA_BOARD_CX =
// 34.12 + 2.65 + 48.96/2 = 61.25, which maps to face X 63.75 = FACE_W / 2
// -- the window is centred on the face horizontally -- and AA_BOARD_CY = 25
// maps to Q 28 = FACE_H / 2, centred vertically too.
PANEL_BOARD_CX = (PANEL_BOARD_X0 + PANEL_BOARD_X1) / 2; // 63.62
PANEL_BOARD_CY = (PANEL_BOARD_Y0 + PANEL_BOARD_Y1) / 2; // 25.0
AA_BOARD_CX = PANEL_BOARD_X0 + AA_INSET_LEFT + AA_W / 2; // 61.25
AA_BOARD_CY = PANEL_BOARD_CY; // insets symmetric top/bottom -> 25.0

// This file's own face coordinates for the window and the panel
// pocket behind it.
WINDOW_CX = board_to_x(AA_BOARD_CX);
WINDOW_CY = board_to_y(AA_BOARD_CY);
PANEL_CX  = board_to_x(PANEL_BOARD_CX);
PANEL_CY  = board_to_y(PANEL_BOARD_CY);

// Centring check (pilink-6lz): WINDOW_CX == FACE_W / 2 and WINDOW_CY ==
// FACE_H / 2 by construction (see AA_BOARD_CX above); echoed so a render
// shows it. The PANEL (not the window) is therefore off-centre by
// (AA_INSET_RIGHT - AA_INSET_LEFT) / 2 = 2.37mm toward the right (COG/FPC
// ledge side), as the proposal's "centre the window, not the panel" rule
// intends.
echo(str("[pilink-6lz] window centre (", WINDOW_CX, ", ", WINDOW_CY, ") vs face centre (",
         FACE_W / 2, ", ", FACE_H / 2, "); knob (", ENCODER_CX, ", ", ENCODER_CY,
         "); diamond centre X ", board_to_x(BTN_Y[0])));

// Glass registration depth: how far below the outer face the display
// glass sits, per this bead's own description ("glass ~1.2mm below the
// face with the plate thinned over the panel") and proposal 6c's body-
// thickness stack-up ("face 2.0 ... 3.3mm panel stack" = 1.2mm glass
// depth + 2.1mm panel frame thickness). RECESS_DEPTH is a stated design
// target from those sources, not an independently measured part
// dimension.
//
// FIX (code-review NOT APPROVED on 8da37dc, finding #1): the previous
// geometry cut this same RECESS_DEPTH as a separate, WIDER bezel-margin
// step into the OUTER face (0 to RECESS_DEPTH) while the panel's actual
// registration ledge started at the INNER face (Z=FACE_T=2.0) and ran
// forward -- so the glass really sat at Z=FACE_T (2.0mm), with the
// 1.2mm cut just leaving an 0.8mm lip in front of it, not seating the
// glass at 1.2mm as this comment and the README claimed. Fixed in
// display_cutouts() below: the plate is now actually thinned to
// RECESS_DEPTH over the full panel footprint (PANEL_W x PANEL_H +
// POCKET_CLEARANCE), cut from the INNER face, so the floor of that cut
// -- at Z=RECESS_DEPTH -- is the real surface the panel's frame
// registers against, with the AA aperture (full face-plate depth, see
// below) open in front of it. BEZEL_MARGIN (the old wider outer-step
// size) is removed; there is no separate outer bezel step now, only the
// panel-sized thinned pocket.
RECESS_DEPTH = 1.2; // mm, glass depth below the outer face

// Panel pocket (inner-face side): a retaining ledge sized to the full
// 59 x 42mm frame plus clearance, backed by foam/rib retention
// (assembled, not modeled) per the bead description.
POCKET_CLEARANCE = 1.0; // mm each side, own choice
LEDGE_W     = 2.0;      // mm, retaining-ledge wall width, own choice
LEDGE_DEPTH = 2.2;      // mm, slightly over the panel's own 2.1mm
                         // frame thickness (proposal 1.1 "Frame
                         // outline 42.0 W x 59.0 H x 2.1 D mm") so the
                         // ledge alone doesn't bottom the panel out
                         // before foam behind it can preload it
                         // forward against the window.

/* ========================= Knob / encoder opening =========================
   Alps EC11E18244AU (SW303). */

// Shaft/knob centre, board-local: ENCODER_BOARD_CX/CY in common.scad
// (pilink-4qc: (14.25, 25), the board's vertical centre and the face's
// horizontal centreline, so knob and diamond share one horizontal line).
ENCODER_CX = board_to_x(ENCODER_BOARD_CX);
ENCODER_CY = board_to_y(ENCODER_BOARD_CY);
// (= (16.75, 28) in face coordinates: Q 28 = FACE_H / 2.)

// Body / courtyard, used to size the inner-face pocket.
// Source: docs/plans/2026-11-15-product-layout-proposal.md section
// 1.2 table: "Body outline 12.0 x 11.6mm (shaft centred)".
ENCODER_BODY_W = 12.0;
ENCODER_BODY_H = 11.6;

// Heights above the PCB -- CORRECTED figures, confirmed from Alps'
// own EC11E Series catalogue (Drawing No. 2) and cross-checked
// against the part's own STEP-file bounding box. Source:
// .research/findings/2026-11-15-encoder-ec11e18244au-specs.md,
// "Body height above PCB: CORRECTED" section. These supersede the
// stale "~7-7.5mm body height" figure that this bead's own comment
// log (and the task brief that spawned this work) still carry -- that
// number was a misread of a FOOTPRINT (plan-view) dimension, not a
// height above the board. See the finding for the full correction.
ENCODER_HOUSING_H   = 4.5;  // housing top above PCB
ENCODER_BUSHING_H   = 11.5; // bushing top above PCB
ENCODER_SHAFT_TIP_H = 24.5; // shaft tip above PCB

// Clearance check (arithmetic only, not a modeled dimension): the
// housing top sits at PCB + 4.5mm = FRONT_SHELL_DEPTH - 4.5 = 3.0mm
// from the outer face, i.e. about 1.0mm BEHIND this file's inner face
// plane (FACE_T = 2.0mm) using the corrected housing height. Unlike
// the stale ~7.5mm figure, the housing does NOT need a deep pocket to
// avoid hitting the plate. This file still adds a shallow countersink
// (ENCODER_POCKET_* below) as a tolerance buffer against that ~1mm
// margin, and because the bead explicitly asks for a recessed pocket
// -- not because the corrected numbers show a hard interference.

// Bushing diameter: NOT CONFIRMED by any source read for this bead
// (checked the proposal, the ADR, and the encoder research finding --
// none states a bushing OD; a web search for this specific part
// number also came up empty on this one dimension). ASSUMED 7mm (a
// common Alps EC11-family bushing OD) plus clearance. FLAG FOR
// CONFIRMATION against a real part or Alps' own CAD/drawing before
// finalizing -- if the real bushing is bigger, only
// ENCODER_SHAFT_HOLE_DIA needs to grow, nothing else here depends on
// the exact value.
ENCODER_BUSHING_DIA_ASSUMED = 7.0;  // UNCONFIRMED, see comment above
ENCODER_SHAFT_HOLE_DIA = ENCODER_BUSHING_DIA_ASSUMED + 1.5; // 8.5mm through-plate hole

// Inner-face countersink/pocket, sized to clear the encoder body's
// 12.0 x 11.6mm footprint (bounding circle ~16.7mm) plus margin.
ENCODER_POCKET_DIA   = 18.0;
ENCODER_POCKET_DEPTH = 1.2; // mm, leaves FACE_T - this = 0.8mm of
                             // solid plate at the hole's narrow part

// Knob cap -- informational only, NOT a hole in this shell (the cap
// sits proud, outside the face, on the end of the shaft).
// Source: proposal 6c "Dimensions": knob cap Ø18mm (9mm radius);
// proud figure corrected to ~17mm above the face,
// .research/findings/2026-11-15-encoder-ec11e18244au-specs.md.
KNOB_CAP_DIA  = 18.0; // informational only
KNOB_PROUD_MM = 17.0; // informational only

/* ============================ A/B/X/Y buttons ============================
   C&K PTS645 (SW305-SW308), diamond layout. Names below (Y/X/B/A) are
   BUTTON LABELS, not coordinate axes -- don't confuse e.g. "BTN_Y"
   with a Y coordinate. */

// Diamond positions: BTN_Y/BTN_X/BTN_B/BTN_A in common.scad (pilink-4qc:
// centre (108.25, 25), 8mm pitch; PCB SW308/SW307/SW306/SW305).
// U201 (ESP32-WROOM-32UE) is on the BACK of the board (B.Cu) since
// pilink-hdl -- no longer in a front-side pocket above the diamond, so
// there is nothing to check against on the front any more (the old
// "~0.6mm gap above the shifted diamond" note is obsolete). The diamond's
// F.CrtYd (place.py: x:[88.93,115.07] y:[13.58,36.43]) is unchanged from
// the pre-pilink-2yw layout; U201's B.Cu courtyard (y:[1.75,21.95]) overlaps
// it in XY by design -- opposite board faces, no clash. This file's
// button bores only cut the 2.0mm face plate regardless (Z 0..FACE_T).
// J501 (display FPC connector, F.Cu) courtyard bottom y=31.53 and the
// raised J401 courtyard (B.Cu) y:[34.32,39.68] are not modelled here.

// Cap size / bore clearance.
// Source: bead description + hardware/README.md: "4 A/B/X/Y plunger
// bores (diamond, caps O8mm, +/-8mm centres)".
BUTTON_CAP_DIA = 8.0;
BUTTON_BORE_CLEARANCE = 0.4; // mm diametral, own choice
BUTTON_BORE_DIA = BUTTON_CAP_DIA + BUTTON_BORE_CLEARANCE;
// Entry chamfer on the OUTER face (Z=0) side of each bore (pilink-ci0):
// 45-degree lead-in, BORE_CHAMFER mm wide/deep, so the bore mouth is
// BUTTON_BORE_DIA + 2*BORE_CHAMFER = 9.2mm at Z=0, tapering to the straight
// 8.4mm bore by Z=BORE_CHAMFER. Eases cap insertion; cosmetic edge break.
BORE_CHAMFER = 0.4; // mm

BUTTON_POSITIONS = [
    [board_to_x(BTN_Y[0]), board_to_y(BTN_Y[1])],
    [board_to_x(BTN_X[0]), board_to_y(BTN_X[1])],
    [board_to_x(BTN_B[0]), board_to_y(BTN_B[1])],
    [board_to_x(BTN_A[0]), board_to_y(BTN_A[1])],
];

/* =============== Top-edge service pinholes (SW101/SW102) ===============
   Side-actuated SMD tact switches (BOOTSEL/RESET) at the PCB's top
   edge, reached straight down through the top wall.
   Source: ADR, "front-side SMD ... reached by paperclip pinholes in
   the top edge ... pressed straight down through about a 1.5mm
   pinhole"; positions from hardware/README.md placement table:
   "SW101 (42, 2.7), SW102 (52, 2.7)". */

PINHOLE_DIA = 1.5;

// SW101_BOARD / SW102_BOARD: common.scad.
PINHOLE_X = [board_to_x(SW101_BOARD[0]), board_to_x(SW102_BOARD[0])]; // [44.5, 54.5]

// Depth (Z) position: the switches sit on the PCB's front surface, at
// Z = FRONT_SHELL_DEPTH in this file's convention, right at this
// shell's own rear opening. Not independently re-derived from a
// switch footprint -- this file doesn't model the switch itself, only
// reserves straight pinhole access to roughly where it sits.
PINHOLE_Z = FRONT_SHELL_DEPTH - 1.0;

/* ================ Antenna clearance zone (reserved only) ================
   This bead does NOT design the antenna mount -- that is
   pilink-8hx.4's own bead (`enclosure/antenna_mount.scad`), merged
   separately, which owns the real antenna geometry. This file only
   marks a debug-only, non-cutting X zone in the top wall (OpenSCAD "%"
   modifier -- previews in F5, excluded from the actual solid/STL, cuts
   or adds nothing real) so a human looking at this file's render isn't
   misled about where the antenna actually ended up.
   UPDATED: the original marker (board-local X 5-23, centered 14) cited
   the ADR's pilink-5g8 verification note about U201's U.FL-connector
   edge -- stale (U201 is now on the BACK of the board at x~99,
   pilink-hdl, and its U.FL faces the back shell); pilink-8hx.4's own fix rounds moved the REAL antenna element/mount
   well away from there, to face-local X 58.25-106.05mm (per
   enclosure/README.md's antenna_mount.scad section / the file itself),
   clear of SW101/SW102's pinhole channels. Marker moved to roughly
   match that real position instead of the stale U.FL-pad location, so
   it no longer actively misleads -- the real geometry is
   antenna_mount.scad's, this is only an approximate visual flag. */

// face-local mm, matches antenna_mount.scad's MOUNT_X_MIN/MAX (58.25..106.05):
// SW102 pinhole edge + 3.0mm margin, 47.8mm long.
ANT_ZONE_X0 = board_to_x(SW102_BOARD[0]) + PINHOLE_DIA / 2 + 3.0;
ANT_ZONE_X1 = ANT_ZONE_X0 + 47.8;

/* ===================== Shell fasteners (pilink-8hx.7) =====================
   One insert standoff per PCB mounting hole H1..H4 (PCB_MOUNT_HOLES_BOARD),
   from the inner face (Z = FACE_T) to the PCB front (Z = FRONT_SHELL_DEPTH),
   so the PCB sits on the standoff tops and the M2 screw from the back
   (common.scad: M2x12, head in the back-shell counterbore) runs through the
   PCB into a brass "M2x4x3.2" heat-set insert pressed flush into the top.
   The pocket is INSERT_LEN + INSERT_POCKET_EXTRA deep, blind, and stays in the
   standoff: its floor (Z 2.5) is above the inner face, the face plate is
   untouched. The front of the board has no part within 6mm of any hole
   (courtyards read off hardware/pico-link-hw.kicad_pcb), so a plain cylinder
   clears; check_fit.py checks it against the envelope. */
STANDOFF_OD = INSERT_OD + 2 * STANDOFF_WALL; // 6.0
INSERT_POCKET_DEPTH = INSERT_LEN + INSERT_POCKET_EXTRA; // 5.0
INSERT_POCKET_FLOOR_Z = FRONT_SHELL_DEPTH - INSERT_POCKET_DEPTH; // 2.5
// A standoff that would leave a slot narrower than STANDOFF_MIN_GAP against a
// cavity wall (unprintable, and a line contact if tangent) grows until it
// fuses STANDOFF_FUSE into that wall instead -- H4, 3.5mm below the top wall,
// gets 7.5 (the back shell's H4 boss is 7.5 for the same reason).
STANDOFF_MIN_GAP = 1.0;
STANDOFF_FUSE = 0.25;
function wall_dist(p) = min(p[0] - WALL, FACE_W - WALL - p[0], p[1] - WALL, FACE_H - WALL - p[1]);
function standoff_od(p) = STANDOFF_OD / 2 > wall_dist(p) - STANDOFF_MIN_GAP
    ? max(STANDOFF_OD, 2 * (wall_dist(p) + STANDOFF_FUSE)) : STANDOFF_OD;
STANDOFF_POSITIONS = [ for (h = PCB_MOUNT_HOLES_BOARD) [board_to_x(h[0]), board_to_y(h[1])] ];

// Distance from point p to an axis-aligned w x h rectangle centred on c.
function rect_dist(p, c, w, h) = norm([max(abs(p[0] - c[0]) - w / 2, 0), max(abs(p[1] - c[1]) - h / 2, 0)]);

assert(len([ for (l = SCREW_LENGTHS_ON_HAND) if (l == SCREW_LEN) l ]) == 1, "SCREW_LEN is not a length on hand");
assert(SCREW_ENGAGEMENT >= SCREW_MIN_ENGAGEMENT, "screw too short: thread engagement in the insert below SCREW_MIN_ENGAGEMENT");
assert(SCREW_TIP_Z >= INSERT_POCKET_FLOOR_Z + 0.5, "screw too long: tip within 0.5mm of the insert pocket floor");
assert(INSERT_POCKET_FLOOR_Z >= FACE_T, "insert pocket cuts into the face plate");
assert(INSERT_HOLE_D < INSERT_OD && INSERT_HOLE_D > SCREW_D + 0.5, "insert melt-in hole vs knurl OD / screw");
for (i = [0 : len(STANDOFF_POSITIONS) - 1]) {
    p = STANDOFF_POSITIONS[i];
    r = standoff_od(p) / 2;
    // The panel ledge collar: fused into it, or a printable gap -- never a sliver.
    ledge_gap = rect_dist(p, [PANEL_CX, PANEL_CY], PANEL_W + 2 * LEDGE_W, PANEL_H + 2 * LEDGE_W) - r;
    assert(ledge_gap <= -0.2 || ledge_gap >= 0.8, str("H", i + 1, " standoff leaves a sliver against the panel ledge"));
    // Never into the panel pocket, and >= 1mm from the panel itself.
    assert(rect_dist(p, [PANEL_CX, PANEL_CY], PANEL_W + 2 * POCKET_CLEARANCE, PANEL_H + 2 * POCKET_CLEARANCE) >= r + 0.2,
           str("H", i + 1, " standoff reaches the panel pocket"));
    assert(rect_dist(p, [PANEL_CX, PANEL_CY], PANEL_W, PANEL_H) >= r + 1.0, str("H", i + 1, " standoff within 1mm of the panel"));
    // Knob pocket and button bores: >= 1mm of plate between.
    assert(norm(p - [ENCODER_CX, ENCODER_CY]) >= ENCODER_POCKET_DIA / 2 + r + 1.0, str("H", i + 1, " standoff vs encoder pocket"));
    for (b = BUTTON_POSITIONS)
        assert(norm(p - b) >= BUTTON_BORE_DIA / 2 + BORE_CHAMFER + r + 1.0, str("H", i + 1, " standoff vs a button bore"));
    echo(str("[pilink-8hx.7] H", i + 1, " standoff at (", p[0], ", ", p[1], ") d", 2 * r,
             ", panel-ledge gap ", ledge_gap, " (<0 = fused)"));
}
echo(str("[pilink-8hx.7] M2x", SCREW_LEN, ": head seat Z ", SCREW_SEAT_Z, ", tip Z ", SCREW_TIP_Z,
         ", insert Z ", FRONT_SHELL_DEPTH - INSERT_LEN, "..", FRONT_SHELL_DEPTH, ", engagement ", SCREW_ENGAGEMENT,
         ", tip to pocket floor ", SCREW_TIP_Z - INSERT_POCKET_FLOOR_Z));

/* ================================ Geometry ================================ */

module rounded_rect(w, h, r) {
    rr = min(r, min(w, h) / 2 - 0.01);
    hull() {
        for (sx = [-1, 1]) for (sy = [-1, 1])
            translate([sx * (w / 2 - rr), sy * (h / 2 - rr)])
                circle(r = rr);
    }
}

// Solid outer shell: face plate + perimeter skirt, as one extruded
// rounded-rect prism. Cavities/openings are cut out separately below.
module shell_solid() {
    linear_extrude(height = FRONT_SHELL_DEPTH)
        translate([FACE_W / 2, FACE_H / 2])
            rounded_rect(FACE_W, FACE_H, CORNER_RADIUS);
}

// Interior hollow: inset by WALL on all 4 sides, from just behind the
// front plate (Z = FACE_T) through the rear opening.
module shell_cavity() {
    translate([0, 0, FACE_T])
        linear_extrude(height = FRONT_SHELL_DEPTH - FACE_T + 1)
            translate([FACE_W / 2, FACE_H / 2])
                rounded_rect(FACE_W - 2 * WALL, FACE_H - 2 * WALL,
                             max(CORNER_RADIUS - WALL, 0.1));
}

module z_box(w, h, z0, z1, cx, cy) {
    translate([cx - w / 2, cy - h / 2, z0])
        cube([w, h, z1 - z0]);
}

module display_cutouts() {
    // Full through-aperture, sized to the active area, open across the
    // whole face-plate thickness -- nothing between the glass (which
    // sits right behind this, within the panel pocket cut below) and
    // the viewer.
    z_box(AA_W, AA_H, -0.5, FACE_T + 0.5, WINDOW_CX, WINDOW_CY);
    // Panel pocket: thins the plate to RECESS_DEPTH (1.2mm) over the
    // panel's full outline + assembly clearance, cut from the INNER
    // face (floor at Z=RECESS_DEPTH, roof at Z=FACE_T). The ring of
    // remaining plate between the AA aperture above and this pocket's
    // outer edge is the register surface the panel's frame shoulder
    // seats against, so the glass -- immediately behind that floor,
    // inside the AA aperture -- sits at Z=RECESS_DEPTH (1.2mm) below
    // the outer face, per the bead's target and proposal 6c's stack-up
    // (see RECESS_DEPTH comment above). This is the fix for the
    // "glass sits at 2.0mm, not 1.2mm" review finding.
    z_box(PANEL_W + 2 * POCKET_CLEARANCE, PANEL_H + 2 * POCKET_CLEARANCE,
          RECESS_DEPTH, FACE_T + 0.5, PANEL_CX, PANEL_CY);
}

// Added material (not a cutout): a lateral retaining collar on the
// inner face, OUTSIDE the panel pocket cut in display_cutouts() above
// (it starts at the pocket's own outer boundary, PANEL +
// 2*POCKET_CLEARANCE, and is built forward from Z=FACE_T, i.e. entirely
// behind and outside that pocket -- no overlap). The actual front-face
// registration (where the glass seats at RECESS_DEPTH) is the pocket's
// floor, not this collar; this collar's job is purely lateral retention
// (keeps the panel centred) plus a stop for whatever foam/rib pushes it
// forward from behind (assembled, not modeled).
module panel_ledge() {
    translate([PANEL_CX, PANEL_CY, FACE_T])
        linear_extrude(height = LEDGE_DEPTH)
            difference() {
                square([PANEL_W + 2 * LEDGE_W, PANEL_H + 2 * LEDGE_W], center = true);
                square([PANEL_W + 2 * POCKET_CLEARANCE, PANEL_H + 2 * POCKET_CLEARANCE], center = true);
            }
}

module encoder_cutouts() {
    // through-plate hole for the bushing/shaft
    translate([ENCODER_CX, ENCODER_CY, -0.5])
        cylinder(h = FACE_T + 1, d = ENCODER_SHAFT_HOLE_DIA);
    // shallow inner-face countersink/pocket, tolerance buffer for the
    // encoder housing's wider footprint (see comment above)
    translate([ENCODER_CX, ENCODER_CY, FACE_T - ENCODER_POCKET_DEPTH])
        cylinder(h = ENCODER_POCKET_DEPTH + 0.5, d = ENCODER_POCKET_DIA);
}

module button_cutouts() {
    for (p = BUTTON_POSITIONS)
        translate([p[0], p[1], 0]) {
            translate([0, 0, -0.5])
                cylinder(h = FACE_T + 1, d = BUTTON_BORE_DIA);
            // outer-face entry chamfer (pilink-ci0): 45-degree cone,
            // extended 0.5mm below Z=0 (same slope) for a clean cut
            translate([0, 0, -0.5])
                cylinder(h = BORE_CHAMFER + 0.5,
                         d1 = BUTTON_BORE_DIA + 2 * BORE_CHAMFER + 1,
                         d2 = BUTTON_BORE_DIA);
        }
}

module pinhole_cutouts() {
    for (x = PINHOLE_X)
        translate([x, FACE_H - WALL - 0.5, PINHOLE_Z])
            rotate([-90, 0, 0])
                cylinder(h = WALL + 1, d = PINHOLE_DIA);
}

// pilink-6lz: relief in the top wall so the Ø1.13 pigtail can cross the PCB
// plane above the board's (now 1.0mm) top-edge gap; see common.scad.
// (pilink-8hx.7: runs on through the seam lip, which it removes over the
// notch's width.)
module pigtail_notch_cutout() {
    translate([PIGTAIL_NOTCH_X0, FACE_H - WALL - 0.01, PIGTAIL_NOTCH_Z0])
        cube([PIGTAIL_NOTCH_X1 - PIGTAIL_NOTCH_X0, PIGTAIL_NOTCH_DEPTH + 0.01,
              LIP_TOP_Z + 1 - PIGTAIL_NOTCH_Z0]);
}

module antenna_zone_marker() {
    %translate([ANT_ZONE_X0, FACE_H - WALL, 0])
        cube([ANT_ZONE_X1 - ANT_ZONE_X0, WALL, FRONT_SHELL_DEPTH]);
}

// pilink-8hx.7: insert standoffs, inner face -> PCB front (see "Shell
// fasteners" above). Start 0.01 inside the plate so they fuse with it.
module standoff_solids() {
    for (p = STANDOFF_POSITIONS)
        translate([p[0], p[1], FACE_T - 0.01])
            cylinder(h = FRONT_SHELL_DEPTH - FACE_T + 0.01, d = standoff_od(p));
}

module insert_pockets() {
    for (p = STANDOFF_POSITIONS)
        translate([p[0], p[1], INSERT_POCKET_FLOOR_Z])
            cylinder(h = INSERT_POCKET_DEPTH + 0.5, d = INSERT_HOLE_D, $fn = 32);
}

// pilink-8hx.7: seam lip (common.scad LIP_*). The inner LIP_T of the
// perimeter wall carries on LIP_H past the PCB front surface, its inner face
// flush with the cavity wall (so the board edges keep BOARD_CLEARANCE_X/Y to
// it) and its outer face LIP_CLEARANCE inside the back shell's rabbet.
// Concentric with the outer corners, like the cavity, so it is LIP_T thick
// round them too; the board's square corners clear the cavity's 1mm inner
// corner radius by 0.5mm.
LIP_TOP_Z = FRONT_SHELL_DEPTH + LIP_H; // 10.0
assert(LIP_TOP_Z >= Z_PCB_BACK + 0.5, "seam lip must cover the PCB edge over its whole thickness, plus a lead-in");
module seam_lip() {
    translate([0, 0, FRONT_SHELL_DEPTH - 0.01])
        linear_extrude(height = LIP_H + 0.01)
            translate([FACE_W / 2, FACE_H / 2])
                difference() {
                    rounded_rect(FACE_W - 2 * (WALL - LIP_T), FACE_H - 2 * (WALL - LIP_T),
                                 CORNER_RADIUS - (WALL - LIP_T));
                    rounded_rect(FACE_W - 2 * WALL, FACE_H - 2 * WALL,
                                 max(CORNER_RADIUS - WALL, 0.1));
                }
}

module front_shell() {
    difference() {
        union() {
            difference() {
                shell_solid();
                shell_cavity();
            }
            standoff_solids();
            seam_lip();
        }
        display_cutouts();
        encoder_cutouts();
        button_cutouts();
        pinhole_cutouts();
        pigtail_notch_cutout();
        insert_pockets();
    }
    panel_ledge();
    antenna_zone_marker();
}

front_shell();

/* ================================ Open items ================================
   (summarized here for anyone reading just this file; also in the PR
   body for pilink-8hx.2)
   1. No OpenSCAD render/fit check was possible -- not installed in
      this environment. Needs a human with OpenSCAD, ideally once
      pilink-8hx.1 (back shell) also exists, to confirm real fit
      (pilink-8hx.5).
   2. Encoder bushing diameter is an ASSUMED 7mm, not confirmed from
      any source read for this bead -- confirm against a real part or
      Alps' CAD drawing before finalizing ENCODER_SHAFT_HOLE_DIA.
   3. RESOLVED: the board<->face mapping is defined once in common.scad
      (pilink-6lz) and shared with every other part.
   4. RESOLVED (pilink-4qc + pilink-6lz): the display window is centred on
      the face (WINDOW_CX == FACE_W / 2, WINDOW_CY == FACE_H / 2).
   5. This is a flat rectangular shell, not the ADR's ~15-degree-
      leaning body profile, and has no final corner/edge styling pass.
   6. RESOLVED (pilink-8hx.7): four M2x12 socket head screws from the
      back, through counterbored back-shell bosses and the PCB's H1..H4,
      into M2x4x3.2 heat-set inserts in this shell's standoffs; nothing
      shows on the face (aesthetic ADR). A seam lip locates the PCB and
      registers the back shell's rabbet. Still needs a printed fit check
      (insert hole, lip/rabbet clearance, screw feel): pilink-8hx.5.
   7. pilink-6lz: re-derived for the 122.5 x 50 board of pilink-4qc, face
      127.5 x 56, 0.5mm (X) / 1.0mm (Y) board clearance per side. Every
      board-local position now comes from common.scad.
*/
