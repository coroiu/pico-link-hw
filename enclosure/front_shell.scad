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
// =================================================================

$fn = 48;

/* ============================== Face / body ============================== */

// Face outline.
// Source: .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md
// "Decision": "Face about 122 W x 56 H mm"; also
// docs/plans/2026-11-15-product-layout-proposal.md section 6c
// "Dimensions": "about 122 W x 56 H mm along the face".
FACE_W = 122.0;
FACE_H = 56.0;

// Face-plate thickness AND perimeter-wall thickness (the same figure
// is used both ways throughout the source docs).
// Source: proposal 6c "Body thickness" breakdown: "face 2.0 ... and a
// 2.0 mm back wall"; proposal section 2 / Option A width build-up:
// "wall 2 + margin 5 + knob radius 9 ...".
WALL = 2.0;
FACE_T = WALL;

// Depth from the outer face surface to the PCB's front surface / this
// shell's rear opening (where it meets the back shell, pilink-8hx.1,
// with the PCB floating/screwed to the back shell's own bosses
// between the two shells).
// Source: proposal 6c "Body thickness": "face 2.0, 5.5 mm to the PCB
// (5.0 mm switches, 3.3 mm panel stack, J501 about 2 mm)" -> 2.0 + 5.5
// = 7.5 mm. The same 7.5 mm figure is independently cited in proposal
// section 1.2's "Conflict with the aesthetic ADR" note ("the face at
// about 7.5 mm above the PCB") and in this bead's own comment log
// ("the board-to-inner-face gap is only ~5.5mm").
GAP_FACE_TO_PCB = 5.5; // mm, inner face surface to PCB front surface
FRONT_SHELL_DEPTH = FACE_T + GAP_FACE_TO_PCB; // 7.5 mm

// Corner radius: own styling choice, NOT sourced from a doc -- the
// aesthetic ADR (.planning/decisions/2026-11-15-enclosure-aesthetic-
// direction.md) only says "deliberate but not aggressive corner
// radii", no number given. Pick something modest; easy to retune in
// a later styling pass.
CORNER_RADIUS = 6.0;

/* ========================= Real board coordinates =========================
   Source: hardware/README.md, "PCB layout (pilink-7el.12, upright
   desk-clock form factor)" placement table -- the as-placed,
   as-routed board (118 x 50mm), not the earlier Option-A proposal
   sketch. Board-local origin is the board's own top-left corner,
   x right, y DOWN (opposite sense from this file's own Y axis --
   see board_to_y() below). */
BOARD_W = 118.0;
BOARD_H = 50.0;

/* ===================== Face <-> board coordinate mapping ===================== */

// X: exact, no assumption needed. (FACE_W - 2*WALL) == BOARD_W
// (122 - 2*2 == 118) -- the board's width exactly fills the inner
// cavity with zero extra side margin, so board-local X maps onto this
// file's X with a flat WALL offset and no scaling or guessing.
function board_to_x(bx) = WALL + bx;

// Y: NOT exact, but now CONFIRMED to match the convention
// enclosure/back_shell.scad (pilink-8hx.1) independently landed on
// after its own PR #52 review round, not just inherited as an open
// assumption. hardware/README.md's raw rule ("N mm up the face" means
// `y = 50 - N`) implicitly puts the board's bottom edge flush with the
// face's bottom edge, leaving no room for either shell's own WALL_T
// (2mm) wall -- back_shell.scad's review caught that its own PCB cavity
// physically needs that bottom wall, and fixed it by deriving a 2mm
// TOP_SLACK from the real inner-cavity height instead:
// `TOP_SLACK_Y = (FACE_H - 2*WALL_T) - BOARD_H`, giving
// `board_to_face()` Y = `FACE_H - (WALL_T + TOP_SLACK_Y + by)`, i.e.
// Qface = 52 - by. This file's TOP_SLACK/board_to_y() below is the
// exact same formula (WALL == WALL_T, TOP_SLACK == TOP_SLACK_Y, both
// 2.0mm) -- so every Y position in this file already sits 2mm higher
// than README's raw "y = 50 - N" figures (board bottom at face-y=WALL
// =2, not 0), and that is a deliberate, now cross-confirmed choice
// shared with back_shell.scad, not a silent deviation. (A prior review
// round flagged this file's formula as an unreconciled 2mm change from
// README's stated assumption -- it has since been reconciled: both
// shells now derive and state the same 2mm.)
TOP_SLACK = (FACE_H - 2 * WALL) - BOARD_H; // 2.0mm, matches back_shell.scad's TOP_SLACK_Y

// Converts a board-local y (down-positive, 0 at the board's top edge)
// to this file's y (up-positive, 0 at the face's bottom outer edge).
function board_to_y(by) = FACE_H - (WALL + TOP_SLACK + by);

/* ============================ Display window ============================
   Crystalfontz CFAF240320A0-024SN, landscape (rotated 90deg from its
   native 240x320 per .planning/decisions/2026-11-15-display-panel-
   crystalfontz-cfaf240320a0.md). Raw figures from
   docs/plans/2026-11-15-product-layout-proposal.md section 1.1, which
   cites the Crystalfontz datasheet directly. */

// Panel outline (landscape): "Panel footprint 59.0 wide x 42.0 deep".
PANEL_W = 59.0;
PANEL_H = 42.0;

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

// Where the panel sits relative to the real board, used ONLY to
// derive the active area's real center below -- the display is a
// separate physical part held by this shell, connected to J501 by
// FPC, not a PCB footprint with its own fixed coordinate.
// Source: hardware/README.md placement table, "Display panel shadow
// 59 x 42mm ... Treated as x:[28,87] y:[5,47] on the board". That
// rectangle's own size (59 x 42) exactly matches the panel outline
// above, so it is read here as the panel's real intended position,
// not just a generic keepout margin.
PANEL_BOARD_X0 = 28.0;
PANEL_BOARD_X1 = 87.0;
PANEL_BOARD_Y0 = 5.0;
PANEL_BOARD_Y1 = 47.0;

PANEL_BOARD_CX = (PANEL_BOARD_X0 + PANEL_BOARD_X1) / 2; // 57.5
PANEL_BOARD_CY = (PANEL_BOARD_Y0 + PANEL_BOARD_Y1) / 2; // 26.0

// Active-area center, board-local, derived from the panel position
// above plus the datasheet insets. This reproduces the ADR's own
// "2.37mm off panel centre" figure exactly
// ((AA_INSET_RIGHT - AA_INSET_LEFT) / 2 = 2.37) -- a good sign the two
// sources (datasheet insets, real board placement) agree with each
// other.
AA_BOARD_CX = PANEL_BOARD_X0 + AA_INSET_LEFT + AA_W / 2; // 55.13
AA_BOARD_CY = PANEL_BOARD_CY; // insets symmetric top/bottom -> unchanged (26.0)

// This file's own face coordinates for the window and the panel
// pocket behind it.
WINDOW_CX = board_to_x(AA_BOARD_CX);
WINDOW_CY = board_to_y(AA_BOARD_CY);
PANEL_CX  = board_to_x(PANEL_BOARD_CX);
PANEL_CY  = board_to_y(PANEL_BOARD_CY);

// Cross-check worth flagging, NOT resolved here: an earlier design
// rule (proposal section 1.1: "The enclosure should centre the
// *window* on the face, not the panel") implied WINDOW_CX should land
// on FACE_W/2 = 61.0mm exactly. The real board placement above
// instead puts it at board_to_x(55.13) = 57.13mm, about 3.9mm left of
// face-center (toward the knob side -- the right direction per the
// rule, just not the same magnitude). That is expected: this is the
// first place anything fixes the panel's real physical position in
// 3D, so it is derived here from the real placed board rather than
// the pre-placement proposal's idealised centering, the same way the
// board outline, knob position etc. all superseded Option-A's
// placeholder numbers once pilink-7el.12 ran. Flagged for
// pilink-8hx.5 to confirm this is still an acceptable look.

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

// Shaft/knob center, board-local.
// Source: hardware/README.md placement table (updated by pilink-2yw,
// merged 2026-11-16): "Shaft/knob centre at (16, 25) -- exactly
// board-vertical-centre (50/2)". This SUPERSEDES the old (16, 31)
// position: U201 (ESP32) used to share this column and forced the knob
// low; pilink-2yw relocated U201 off the column (see
// hardware/README.md's updated table / hardware/scripts/place.py), so
// the knob could move to the board's true vertical centre instead.
ENCODER_BOARD_CX = 16.0;
ENCODER_BOARD_CY = 25.0;
ENCODER_CX = board_to_x(ENCODER_BOARD_CX);
ENCODER_CY = board_to_y(ENCODER_BOARD_CY);
// (= (18, 27) in this file's coords -- 27mm up from the face's bottom
// edge, i.e. 1mm BELOW the face's own vertical centre (FACE_H/2 =
// 28mm), under this file's board_to_y() mapping (2mm of the face's
// 6mm board/face height slack sits below the board, 4mm above -- see
// board_to_y() above). NOT "lower third" any more -- that description
// was already false for the old (16,31) position (37.5% up a 56mm
// face, past the lower third's 18.7mm cutoff) and is doubly inapplicable
// now that the knob sits at the board's true vertical centre. Describe
// it as "near face vertical centre" instead.)

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

// Diamond positions, board-local [board_x, board_y].
// Source: hardware/README.md placement table, RESTORED by pilink-hdl
// (PR #60, 2026-11-16): centre (102, 25) -- exactly board-vertical-centre,
// same y as the knob -- Y top (102,17), X left (94,25), B right (110,25),
// A bottom (102,33); verified against hardware/pico-link-hw.kicad_pcb
// (SW308 (102,17), SW307 (94,25), SW306 (110,25), SW305 (102,33)).
// pilink-3ym: this SUPERSEDES the pilink-2yw-era centre (102,34) / Y
// (102,26) / X (94,34) / B (110,34) / A (102,42) this file carried from
// PR #50 -- every y below is the old value -9. The 8mm pitch and the
// X-button x=94 are unchanged.
BTN_Y = [102, 17]; // top of diamond
BTN_X = [94, 25];  // left of diamond
BTN_B = [110, 25]; // right of diamond
BTN_A = [102, 33]; // bottom of diamond

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

SW101_BOARD = [42, 2.7];
SW102_BOARD = [52, 2.7];

PINHOLE_X = [board_to_x(SW101_BOARD[0]), board_to_x(SW102_BOARD[0])]; // [44, 54]

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
   well away from there, to face-local X 57.75-105.55mm (per
   enclosure/README.md's antenna_mount.scad section / the file itself),
   clear of SW101/SW102's pinhole channels. Marker moved to roughly
   match that real position instead of the stale U.FL-pad location, so
   it no longer actively misleads -- the real geometry is
   antenna_mount.scad's, this is only an approximate visual flag. */

ANT_ZONE_X0 = 57.75; // face-local mm, matches antenna_mount.scad's real element span
ANT_ZONE_X1 = 105.55;

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
        translate([p[0], p[1], -0.5])
            cylinder(h = FACE_T + 1, d = BUTTON_BORE_DIA);
}

module pinhole_cutouts() {
    for (x = PINHOLE_X)
        translate([x, FACE_H - WALL - 0.5, PINHOLE_Z])
            rotate([-90, 0, 0])
                cylinder(h = WALL + 1, d = PINHOLE_DIA);
}

module antenna_zone_marker() {
    %translate([ANT_ZONE_X0, FACE_H - WALL, 0])
        cube([ANT_ZONE_X1 - ANT_ZONE_X0, WALL, FRONT_SHELL_DEPTH]);
}

module front_shell() {
    difference() {
        shell_solid();
        shell_cavity();
        display_cutouts();
        encoder_cutouts();
        button_cutouts();
        pinhole_cutouts();
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
   3. RESOLVED (was open item 3): the board-to-face Y mapping is now
      cross-confirmed to match enclosure/back_shell.scad's own landed
      derivation (both shells independently arrived at the same 2mm
      TOP_SLACK formula) -- see board_to_y()'s comment above. Not an
      open item any more.
   4. The display window's real center (derived from the as-placed
      board) lands about 3.9mm off the face's exact horizontal center
      -- toward the knob side, the direction the "center the window,
      offset the panel" rule predicts, but not the same magnitude as
      an idealized face-centered window. Flagged, not resolved (display
      position is unaffected by pilink-2yw's coordinate updates).
   5. This is a flat rectangular shell, not the ADR's ~15-degree-
      leaning body profile, and has no final corner/edge styling pass.
   6. Front-to-back shell fastener bosses (hidden heat-set inserts,
      per the aesthetic ADR) are not modeled here -- left for
      reconciliation with pilink-8hx.1's own mating geometry once both
      exist.
   8. pilink-3ym: diamond restored to board centre (102,25) -- bores at
      (102,17)/(94,25)/(110,25)/(102,33); item 7's (102,34) figures are
      superseded. Knob and SW101/SW102 pinholes unchanged. U201 is back-
      side now (B.Cu), so the front-side proximity note is obsolete.
      Not rendered or fit-checked (OpenSCAD not installed).
   7. pilink-2yw (ESP32 relocation + knob/diamond re-placement, merged
      2026-11-16) coordinate updates applied in this revision: knob
      moved to board (16,25) (was (16,31)); A/B/X/Y diamond shifted
      down 9mm to centre (102,34) (was (102,25)); SW101/SW102 pinholes
      confirmed UNCHANGED at board (42,2.7)/(52,2.7) per
      hardware/README.md's updated table. U201's new position (board
      (99,11.6), directly above the new diamond) checked against the
      diamond's and U201's own F.CrtYd boxes -- adjacent with ~0.6mm
      PCB-side clearance, not overlapping, and irrelevant to this
      file's own Z-layer regardless (see the comment by BTN_Y/BTN_X/
      BTN_B/BTN_A above).
*/
