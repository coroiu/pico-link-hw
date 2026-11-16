// Pico Link enclosure -- back shell + rear legs (pilink-8hx.1)
//
// Scope of THIS file: the back shell (PCB-mounting bosses, the 3mm
// clearance cavity behind the PCB, the rear USB-C cutout + local boss, the
// horizontal base strip with feet, and the two leg-mounting bosses) plus
// the fixed two-leg A-frame itself. The front shell (face, display window,
// button/knob openings -- pilink-8hx.2) and the antenna mount
// (pilink-8hx.4) are separate beads/files worked in parallel; this file
// does not model them and only touches enclosure/README.md besides itself.
//
// *** OpenSCAD is NOT installed in this environment (confirmed in
// AGENTS.md) -- this file has never been opened, rendered, or
// dimension-checked. Every numeric constant below cites where it comes
// from; render + fit-check is pilink-8hx.5's job, on a machine that has
// OpenSCAD. The echo() statements at the bottom print the handful of
// numbers this bead's own NOTE asked to verify (USB-C vs. leg clearance)
// so a human can see them even via a headless `openscad -o /dev/null
// back_shell.scad` run, without a GUI. ***
//
// ---------------------------------------------------------------------
// Coordinate frames used in this file
// ---------------------------------------------------------------------
// 1. "Local" frame (back_shell_local() and everything it contains):
//      X = Pface  -- lateral position across the face, 0 at the face's
//                     left edge, FACE_W (127.5mm) at its right edge.
//      Y = Qface  -- position up the face, 0 at the face's bottom edge,
//                     FACE_H (56mm) at its top edge. This is exactly the
//                     "N mm up the face" quantity the ADR and
//                     hardware/README.md use.
//      Z = bz     -- depth, 0 at the back wall's OUTER (world-facing)
//                     surface, increasing toward the open front rim
//                     where this shell meets the front shell / the PCB's
//                     own front surface (bz = BACK_SHELL_DEPTH there).
//    This frame is NOT tilted -- it's the shell "unfolded" flat, which is
//    the natural frame for anything that has to line up with the PCB
//    (bosses, the USB-C cutout) since the PCB itself is flat.
// 2. "World" frame (base_strip(), leg(), and the top-level assembly):
//      X unchanged (lateral position is unaffected by the body's lean).
//      Y = height above an assumed table-level datum.
//      Z = how far forward (+) / back (-) of that same datum.
//    The two frames are related by the ADR's 15 degree lean, applied as
//    rotate([-LEAN_DEG, 0, 0]) to the local frame. The datum (world
//    Y=0, Z=0) is THIS file's own choice: the back wall's own
//    bottom-outer corner (local Qface=0, bz=0). That point is NOT
//    necessarily table height in the real assembled product -- the real
//    table contact comes from the base strip and the leg feet, whose own
//    exact height depends on the front shell's base profile, which
//    doesn't exist yet (pilink-8hx.2). Flagged wherever it matters below.
//
// ---------------------------------------------------------------------
// Source documents (every dimension below cites one of these)
// ---------------------------------------------------------------------
//   ADR   = .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md
//   PROP  = docs/plans/2026-11-15-product-layout-proposal.md, section 6c
//   PCB   = hardware/README.md, "PCB layout (pilink-7el.12 ...)" section
//           (board-local coordinates, origin top-left, X right, Y down)
//   USBC  = .research/findings/2026-11-15-vertical-usb-c-receptacle-selection.md
//   ENC   = .research/findings/2026-11-15-encoder-ec11e18244au-specs.md
//   AES   = .planning/decisions/2026-11-15-enclosure-aesthetic-direction.md

// =====================================================================
// Constants
// =====================================================================

// --- Overall envelope ---
// pilink-6lz: board size, wall, board clearance, FACE_W/FACE_H, the
// board<->face mapping (board_to_face(), MARGIN_X, QTOP) and the board-local
// mounting-hole positions are defined once in common.scad, shared with the
// front shell and every other part. The board is centred in this shell's
// cavity with BOARD_CLEARANCE_X (0.5mm) / BOARD_CLEARANCE_Y (1.0mm) per side
// (supersedes pilink-mav's 0.00mm bottom gap and the old 0.00/0.4mm side
// gaps).
include <common.scad>

LEAN_DEG    = 15;      // ADR: body leans back ~15 deg (face ~75 deg to table)

WALL_T      = WALL;    // = 2.0mm side/top/bottom wall, same as the back wall

// --- Body thickness stack-up (PROP 6c: "about 14mm. That's face 2.0,
// 5.5mm to the PCB (5.0 switches, 3.3 panel stack, J501 ~2mm), PCB 1.6,
// 3mm behind the PCB for the encoder's leads, and a 2.0mm back wall.")
// Only the last three terms belong to the BACK shell; the first two
// (face wall + front cavity) are pilink-8hx.2's (front shell) to build.
FACE_T          = 2.0;   // front shell's own face wall -- not built here,
FRONT_CAVITY    = 5.5;   // ...nor the front cavity -- both only used here
                           // for the BODY_T sanity check below and for
                           // the base-strip/leg "front edge" reference
                           // further down, so the two shells can be
                           // designed to meet correctly later.
PCB_T           = 1.6;   // PCB thickness, matches hardware/README.md
// pilink-9i4: was 3.0 (ADR "3mm for the encoder's leads"). Deepened to 7.0 so
// the WHOLE rear cavity clears every B.Cu envelope with no local relief or
// raised pad on the outside of the back plate (the ESP32 relief used to show as
// a bump). Envelopes above the PCB back surface (mm):
//   J401 USB-C receptacle        6.5   (USBC_HEIGHT_ABOVE_PCB) -> 0.5 margin
//   U201 module body             3.2
//   U201 mated U.FL plug top     3.3   (U201_MODULE_PCB_TOP_H + 2.5)
//   coax centre leaving plug     ~3.0..3.3, Ø1.13; to reach the top-wall notch
//                                it must drop ~2mm to the PCB plane over the
//                                ~5mm run to the board edge: an R >= 4.5mm
//                                arc (min bend, TE/Data Alliance) fits in 7.0
//   pigtail spool stack          2.26  (2 cables on the wall) on a 2.6 post
//   encoder/through-hole leads   <= 3.0 (original ADR need)
// J401 sets the figure: 6.5 + 0.5 = 7.0. U201 + plug + bend then have 3.7mm
// of headroom. +4.0mm on BODY_T (14.1 -> 18.1).
REAR_CLEARANCE  = 7.0;
BACK_WALL_T     = 2.0;   // ADR: "a 2.0mm back wall"

BACK_SHELL_DEPTH = PCB_T + REAR_CLEARANCE + BACK_WALL_T;  // = 6.6mm --
                    // this file's own depth, back-wall-outer (bz=0) to
                    // open front rim (bz=BACK_SHELL_DEPTH), where the PCB
                    // front surface / front shell's rim meets it.
BODY_T = FACE_T + FRONT_CAVITY + PCB_T + REAR_CLEARANCE + BACK_WALL_T;
// BODY_T = 18.1mm (was 14.1 before pilink-9i4; the ADR's "about 14mm" assumed
// a 3mm rear cavity -- the user chose a deeper cavity over any outside bump).

CORNER_R = 3.0;  // style choice (AES: "deliberate but not aggressive
                  // corner radii"), not a dimensioned source figure.

// =====================================================================
// PCB mounting bosses (heat-set inserts carrying the PCB parallel to the
// face, per the bead description)
// =====================================================================
// Positions: hardware/README.md, "Mounting holes for back-shell bosses"
// row -- 4 M2 holes at board-local (10,44), (116.5,6), (116.5,44), (29,2.5)
// after pilink-4qc.
// (positions: PCB_MOUNT_HOLES_BOARD in common.scad)
PCB_MOUNT_HOLES_FACE  = [ for (p = PCB_MOUNT_HOLES_BOARD) board_to_face(p[0], p[1]) ];
// -> [[12.5,43], [119,47], [119,9], [31.5,50.5]] in (Pface, Qface).
//
// H4 (current position comes from PCB_MOUNT_HOLES_BOARD in common.scad,
// board (29,2.5)): at pilink-8ag the hole sat at (59,2.5) so its screw HEAD (driven in from the FRONT, through the PCB)
// stayed clear of the display panel envelope; pilink-4qc moved the panel to
// y 4..46 and H4 to x 29 (left of the panel, which starts at x 34.12), head
// radius 2.0 -> reaches x 31, 3.1mm clear. Do not hard-code face
// coordinates here; derive them via board_to_face().

// Heat-set insert sizing: no bead/finding pins an exact insert down for
// this project, so this is this file's own reasonable-default choice,
// NOT a cited source figure -- flagged for the human assembling the real
// part to confirm against whatever insert is actually bought. Common M2
// brass heat-set inserts for 3D printing run ~2.8-3.5mm OD x 3-6mm long
// (e.g. Bambu Lab's M2x3.5x4 insert); this file uses the middle of that
// range.
INSERT_OD   = 3.5;
INSERT_LEN  = 4.0;
BOSS_OD     = 7.0;   // insert OD + ~1.75mm wall each side
// pilink-i72: H2 (index 1, board (116.5,6)) uses the same 7.0mm boss as the
// others. Since pilink-4qc moved H2 to x 116.5 its boss left edge is at face
// X 115.5, 4.7mm clear of the U201 relief pocket's right edge (110.8).

// =====================================================================
// Rear USB-C opening (J401, vertical-mount receptacle on the PCB back)
// =====================================================================
// Position: board-local (61.25, 37) after pilink-4qc (was (59, 37)), B.Cu,
// rot 0 -- on the face's vertical centreline X = FACE_W / 2 = 63.75. pilink-3ym (2026-11-16): UPDATED for pilink-hdl's J401 raise
// (user decision) from (59, 45.5) to (59, 37); pilink-4qc moved it to
// x 61.25. Plug centreline Qface is now QTOP - 37 = 53 - 37 = 16.0 (was 15.0
// under the old Q = 52 - by mapping and 6.5 before that) -- the product-layout
// proposal's own "~15mm up the back" intent (section 6c). The old (59, 45.5) -> face (61, 6.5)
// position is history; every pilink-8ry table/strip number computed for
// it is recomputed in enclosure/README.md.
J401_FACE = board_to_face(61.25, 37); // -> (63.75, 16) in (Pface, Qface)
USBC_PFACE = J401_FACE[0];
USBC_QFACE = J401_FACE[1];

// Connector geometry, all from USBC finding (TYPE-C-31-D-09, LCSC
// C7463258), datasheet-confirmed there:
USBC_SHELL_W          = 9.0;  // shell outer body, long axis
USBC_SHELL_H          = 3.2;  // shell outer body, short axis
USBC_PAD_EXTENT_W     = 8.6;  // copper/pad+peg extent (PCB-side only;
USBC_PAD_EXTENT_H     = 5.3;  // not needed for the enclosure cutout, kept
                               // here only so the two "~9x~5" figures in
                               // the finding aren't conflated)
USBC_HEIGHT_ABOVE_PCB = 6.5;  // component height above the PCB back
                               // surface -- this is the number that
                               // drives the local boss below.

// Footprint orientation, VERIFIED against hardware/pico-link-hw.kicad_pcb
// (PR #52 review minor item): J401's footprint instance is
// `(at 159 145.5)` at the time (now `(at 159 137)`, pilink-hdl/3ym) with no rotation field -- KiCad omits the angle when
// it's 0, so this is rot 0, matching this file's own J401_FACE comment
// above ("rot 0") and hardware/README.md's placement table, not a
// 270 deg rotation. The footprint's own pad geometry (A1..A12 signal pads span
// local X -3.85..+3.85 = 7.70mm, local Y only +/-0.675mm) confirms the
// long axis (matching the ~9.0mm shell width) is local X, which maps
// directly onto board/face X at rot 0. Being mounted on the back
// (B.Cu) mirrors X (KiCad auto-mirrors back-layer footprints) but a
// mirror doesn't swap which axis is long -- so "long axis horizontal"
// is a confirmed fact here, not an open assumption.

// The bare back cavity here is only BACK_WALL_T + REAR_CLEARANCE = 5.0mm
// deep (PCB back surface to back wall outer face), but the connector is
// 6.5mm tall -- it overhangs by 1.5mm. USBC finding's own recommendation:
// "add a ~1.5-2mm boss around the connector cutout". This file uses the
// upper end of that range for a bit of margin.
// pilink-9i4: NO boss any more -- REAR_CLEARANCE = 7.0 holds the 6.5mm
// connector entirely inside the cavity: its mating face ends 0.5mm clear of
// the wall's inner face (bz 2.5, i.e. 2.5mm behind the outer face).
USBC_BOSS_RISE = 0.0;

// Clear opening through the back wall / boss: sized to pass the
// connector's own shell (9.0 x 3.2mm) with margin. NOTE: this does NOT
// account for the mated USB-C PLUG's own molded cable boot, whose width
// varies a lot by cable and isn't confirmed against any datasheet in
// this project -- flagged as an open item, not resolved here. The figure
// below is this file's own reasonable allowance, not a cited spec.
// pilink-9i4: the receptacle's mating face is now recessed (see
// USBC_MATING_BZ) so the opening is widened 12 x 6 for the plug's overmould.
USBC_CUTOUT_W   = 12.0;
USBC_CUTOUT_H   = 6.0;
USBC_MATING_BZ  = BACK_WALL_T + REAR_CLEARANCE - USBC_HEIGHT_ABOVE_PCB; // 2.5: mating face depth below the outer face
USBC_BOSS_PAD_W = 18.0;  // raised-boss footprint around the cutout
USBC_BOSS_PAD_H = 12.0;  // (generous, own choice -- not a cited figure)

// =====================================================================
// U201 (ESP32-WROOM-32UE) back-side envelope (pilink-3ym, reworked pilink-9i4)
// =====================================================================
// pilink-hdl (PR #60) moved U201 to B.Cu at board-local (99, 11.6), so the
// module body, its mated U.FL plug and the Ø1.13mm pigtail sit in the rear
// cavity. Until pilink-9i4 this had a local relief pocket plus a raised pad
// on the OUTSIDE of the back plate (a visible bump). The whole cavity is now
// deep enough (REAR_CLEARANCE = 7.0, see the stack-up above), so there is no
// relief at all: the module (3.2) and plug top (3.3) clear the wall by
// REAR_CLEARANCE - 3.3 = 3.7mm, room for the R >= 4.5mm coax bend.
//
// Sources: module 18.0 x 19.2 x 3.2mm (hardware/README.md U201 row,
// datasheet-confirmed for the external-antenna variants; F.Fab outline
// measured off the board: x:[90,108] y:[2.0,21.2]); mated U.FL-LP-066 plug
// max 2.5mm above the receptacle mounting surface (Hirose, quoted in
// hardware/README.md Known gap 8); module PCB top ~0.8mm above the host
// PCB (INFERRED as 3.2mm minus an assumed ~2.4mm shield can -- NOT
// verified, MEASURE a real module before trusting the 3.3mm figure).
U201_BOARD            = [99.0, 11.6];  // anchor, B.Cu (stored rot 180 = L/R mirror)
U201_MODULE_H         = 3.2;           // above the host PCB back surface
U201_MODULE_PCB_TOP_H = 0.8;           // INFERRED, see above
UFL_PLUG_ABOVE_RECEPTACLE = 2.5;       // Hirose max mated height
UFL_PLUG_TOP_H        = U201_MODULE_PCB_TOP_H + UFL_PLUG_ABOVE_RECEPTACLE; // 3.3mm
U201_BODY_X = [90.0, 108.0];   // board-local, measured off hardware/pico-link-hw.kicad_pcb
U201_BODY_Y = [2.0, 21.2];
// U.FL receptacle position (NOT in the footprint). VERIFIED in pilink-bl2
// from Espressif's ESP32-WROOM-32E/32UE datasheet v2.1 Figure 11: centre
// 3.07mm in from the antenna-end edge (board y 2.0) and 3.27mm in from the
// long edge on the pin 25-38 side (board x 90.0 on this B.Cu module), i.e.
// the corner beside the antenna notch, not module-centre X.
U201_UFL_BOARD_ASSUMED = [U201_BODY_X[0] + 3.27, U201_BODY_Y[0] + 3.07];  // [93.27, 5.07]
U201_UFL_FACE = board_to_face(U201_UFL_BOARD_ASSUMED[0], U201_UFL_BOARD_ASSUMED[1]);
U201_HEADROOM = REAR_CLEARANCE - max(U201_MODULE_H, UFL_PLUG_TOP_H);  // 3.7mm
assert(U201_HEADROOM >= 3.5, "rear cavity too shallow for U201 + plug + coax bend");

// ---------------------------------------------------------------------
// U.FL pigtail slack spool (pilink-phg)
// ---------------------------------------------------------------------
// The antenna part (Kinghelm KH-FPC2.4G-1.13IPEX-240, LCSC C4943394) has an
// ~240mm pigtail (part number + datasheet table; the datasheet drawing says
// 100+-2mm, pilink-bl2 -- unresolved, spool sized for the 240 worst case) against a
// ~18-30mm run from U201's back-side U.FL to the top-wall mount, so ~210mm
// of coax must be stowed. A shorter part was NOT swapped in: the Kinghelm
// -100 variants on LCSC have unverified cable length / gain / size, and the
// research finding's AIWF026 (100mm) sits 0.02dB over the cert-safe gain
// ceiling -- see enclosure/README.md for the per-part facts. The
// pigtail can't be trimmed (needs crimp tooling), so it is wound here.
//
// The board's B.Cu is nearly empty left of U201 (only J401 at board
// (61.25,37), the 0402/0603 parts at x~87-89 beside the module; H4 is now
// at (29,2.5)); the 3.0mm cavity behind the PCB there is free. A flat spiral is
// wound on a printed post: coax Ø1.13, min bend radius 5mm (TE UMCC 5mm /
// Data Alliance 4.5mm), so post Ø10 -> first turn centreline R 5.57mm.
// Both cable ends are fixed (U.FL plug, antenna), so the inner end has to
// cross back over the turns: the stack is 2 cables = 2.26mm (cable on the
// wall bz 2.0..4.26), under the 2.6mm post/lug height and the 5.0mm PCB
// surface. Capacity: 4 turns = 182mm gross, ~160mm after the
// crossover/entry/exit; a 5th turn (245.8mm gross, outer centreline R
// 10.1) is tight and not counted on, so ~50mm of the 210mm excess stays a
// loose >=5mm-radius loop on the route. Three lugs at R 12 hold it in. Centre: board (73,18) =
// face (75.5,35): board x 61..85 (4.7mm short of the relief's left edge,
// 92.2 face X; the lugs reach board y 30, J401's shell starts at y 35.4).
// UNVERIFIED: J401's real body extent (not read off the board outline);
// whether the plug-to-relief-top-wall bend (cable centre bz <= ~2.9, see
// pilink-phg comment) works with the real mated plug. Needs a real module.
SPOOL_BOARD         = [73.0, 18.0];
SPOOL_POST_D        = 10.0;
SPOOL_POST_H        = 2.6;   // pilink-9i4: fixed (was REAR_CLEARANCE - 0.4); above the 2.26mm cable stack, well short of the PCB
SPOOL_LUG_R         = 12.0;
SPOOL_LUG_D         = 2.0;
SPOOL_FACE          = board_to_face(SPOOL_BOARD[0], SPOOL_BOARD[1]);  // [75, 34]
module pigtail_spool() {
    translate([SPOOL_FACE[0], SPOOL_FACE[1], BACK_WALL_T]) {
        cylinder(h = SPOOL_POST_H, d = SPOOL_POST_D, $fn = 48);
        for (a = [90, 210, 330])
            translate([SPOOL_LUG_R*cos(a), SPOOL_LUG_R*sin(a), 0])
                cylinder(h = SPOOL_POST_H, d = SPOOL_LUG_D, $fn = 16);
    }
}

echo(str("U201 headroom behind PCB: ", U201_HEADROOM, "mm; REAR_CLEARANCE ", REAR_CLEARANCE, ", BODY_T ", BODY_T));

// =====================================================================
// Rear legs / A-frame mounting bosses
// =====================================================================
// ADR: "fixed (non-hinged) printed two-leg A-frame (legs ~+/-40mm from
// centre, feet ~45-50mm behind the front edge) screwed to back-shell
// bosses ~40mm up the face ... hidden fasteners (feet cover screw
// heads)."
LEG_OFFSET      = 40;   // +/- from face centre (FACE_W/2), lateral
LEG_MOUNT_Q     = 40;   // "~40mm up the face" -- directly a Qface value
LEG_FOOT_SETBACK = 47;  // midpoint of the ADR's "45-50mm behind the
                         // front edge" range

// Cross-check against the PCB: leg lateral positions (Pface 23.75, 103.75)
// map back to board-local X = 21.25 and 101.25 (x = Pface - MARGIN_X), i.e.
// board centre / J401 at x 61.25 +/- 40 -- the legs stay symmetric about the
// J401 / face centreline (FACE_W/2 = 63.75).
LEG_PFACE_LEFT  = FACE_W/2 - LEG_OFFSET;   // = 23.75
LEG_PFACE_RIGHT = FACE_W/2 + LEG_OFFSET;   // = 103.75

// "Hidden fasteners (feet cover screw heads)" -- this file's reading:
// each leg is attached to its back-shell mounting boss by a single long
// screw driven in from the FOOT end (through a channel bored the length
// of the leg strut) into a heat-set insert at the boss, ~40mm up the
// face. The rubber foot pad then glues over the screw's access hole at
// the foot, hiding it -- the only construction that actually makes a
// foot "cover" a screw head for THIS leg's own fastener (the mount point
// and the foot are ~45mm apart, so a foot pad at the mount point itself
// isn't geometrically sensible). Flagged as this bead's own design
// choice, not spelled out verbatim in the ADR.
LEG_MOUNT_BOSS_LEN = 6.0;  // boss protrudes this far behind the back
                            // wall's outer surface -- own choice.

// ---------------------------------------------------------------------
// Leg axis geometry (world frame) -- PR #52 review findings #2, #3, #6.
// Computed here, early, so both the back-shell boss/insert modules
// below (which need the tilt, in LOCAL frame) and the leg() module
// further down (which needs the mount/foot points, in WORLD frame)
// read from one single derivation instead of two that can disagree.
// ---------------------------------------------------------------------
// This file's own front-edge stand-in (see the Base strip section
// below for why it's a stand-in, not the real front-shell edge) and
// the leg mount/foot points, in WORLD (y = height above table datum,
// z = forward(+)/back(-)) coordinates -- the header's own
// rotate([-LEAN_DEG,0,0]) transform: world y = Q*cos(LEAN)+bz*sin(LEAN),
// world z = -Q*sin(LEAN)+bz*cos(LEAN).
front_edge_y = 0*cos(LEAN_DEG) + BACK_SHELL_DEPTH*sin(LEAN_DEG);
front_edge_z = -0*sin(LEAN_DEG) + BACK_SHELL_DEPTH*cos(LEAN_DEG);

// Original mount point: the back wall's own OUTER surface (bz=0),
// Qface=LEG_MOUNT_Q -- i.e. where the leg-mount boss's BASE sits (the
// boss itself then protrudes LEG_MOUNT_BOSS_LEN further outward, along
// the tilted axis derived below, not straight out along local Z).
leg_mount_y = LEG_MOUNT_Q*cos(LEAN_DEG);
leg_mount_z = -LEG_MOUNT_Q*sin(LEAN_DEG);

// Foot point: table level (world Y=0, flagged assumption -- see header),
// LEG_FOOT_SETBACK behind this file's own front-edge stand-in.
leg_foot_y = 0;
leg_foot_z = front_edge_z - LEG_FOOT_SETBACK;

LEG_DY = leg_foot_y - leg_mount_y;  // world Y, wall-mount point -> foot
LEG_DZ = leg_foot_z - leg_mount_z;  // world Z, wall-mount point -> foot
leg_length = sqrt(LEG_DY*LEG_DY + LEG_DZ*LEG_DZ);

// Review finding #2: a single straight screw has to run the leg's full
// length, from the foot into the mount boss's own insert -- so the
// boss itself must be tilted to point along this same mount->foot
// line, not straight out from the (near-vertical) back wall (the
// original bug: those two axes were ~37 deg apart, and the channel
// stopped at the boss's base instead of reaching the insert at its
// tip). Deriving the LOCAL (pre-lean-rotation) tilt that achieves this:
// rotating a cylinder (default +Z) by angle theta about local X, then
// applying this shell's own global rotate([-LEAN_DEG,0,0]), composes
// to one net rotation of (theta - LEAN_DEG) about world X (both share
// the X axis). Solving for the local theta whose net rotation points
// along the world mount->foot direction (LEG_DY, LEG_DZ) -- i.e.
// (-sin(theta-LEAN_DEG), cos(theta-LEAN_DEG)) proportional to
// (LEG_DY, LEG_DZ) -- gives:
LEG_BOSS_TILT = atan2(-LEG_DY, LEG_DZ) + LEAN_DEG;

// The boss's tip (where the leg attaches) then lies exactly on the
// mount->foot line, LEG_MOUNT_BOSS_LEN out from the wall -- used as the
// leg's own mount point below. Review finding #6 (round 2): sitting AT
// this point isn't by itself enough for the strut to mate flush --
// see the mount-point comment above leg()'s p_mount for why the strut
// also needs a flat (disc) end here, not a sphere.
leg_mount_tip_y = leg_mount_y + LEG_MOUNT_BOSS_LEN * LEG_DY/leg_length;
leg_mount_tip_z = leg_mount_z + LEG_MOUNT_BOSS_LEN * LEG_DZ/leg_length;

// Axis for the foot-end screw-head counterbore (review finding #2's
// last point -- the counterbore was modelled vertical, ~38 deg off the
// screw axis). Rotating a cylinder by this angle about world X points
// it from the foot back toward the mount, along the leg's own straight
// axis -- what the counterbore needs, since the screw HEAD sits where
// the screw travels, not where the rubber foot (a separate, genuinely
// vertical feature) sits.
LEG_AXIS_TILT = atan2(LEG_DY, -LEG_DZ);

echo(str("Leg mount boss tilt (local frame, deg): ", LEG_BOSS_TILT));
echo(str("Leg axis tilt (world frame, deg, foot->mount): ", LEG_AXIS_TILT));

// Leg structural cross-section: no bead/finding sizes this -- own
// choice, sized generously for a small printed PETG/PLA strut under the
// ADR's own ~110g body weight and knob-torque reaction loads (ADR,
// PROP 6c stability section), but NOT load-calculated. Flagged for a
// human to verify once a real print exists.
LEG_STRUT_D      = 8.0;
SCREW_CHANNEL_D  = 2.6;  // common M2 clearance-hole size
SCREW_HEAD_D     = 4.2;  // common M2 pan/socket-head clearance, generic
FOOT_PAD_D       = 12.0; // flat pad the rubber foot sticks to
FOOT_PAD_T       = 2.5;
FOOT_RECESS_D    = 10.4; // registration pocket for the rubber foot,
FOOT_RECESS_T    = 1.0;  // sized for the chosen foot product (below)

// PR #52 review (46647da, finding #6 carried over): the strut's mount
// end must be a flat disc, not a sphere -- see the leg() comment below.
// A true zero-height disc is a degenerate (non-solid) cylinder in
// OpenSCAD, so this uses a near-zero but nonzero height instead; half
// of it (0.005mm) sits on the boss side of the tip, which is two
// orders of magnitude under typical FDM dimensional tolerance
// (+/-0.1-0.2mm) -- negligible next to the ~4mm intrusion it replaces.
MOUNT_CAP_T      = 0.01;

// =====================================================================
// Base strip + feet (front contact patch, separate from the leg feet)
// =====================================================================
// ADR / PROP 6c: "The body's own bottom is a horizontal strip about
// 14.5mm deep with feet, so it doesn't stand on its front edge." This is
// a SEPARATE ground-contact patch from the rear leg feet (confirmed by
// the proposal's own side-profile ASCII diagram, which draws two
// distinct "o" foot regions with a gap between them -- one long strip
// under the main body, one short cluster under each leg).
BASE_STRIP_DEPTH = 14.5;  // ADR figure
BASE_STRIP_T     = WALL_T;  // = 2.0mm, matches the shell's own wall
BASE_STRIP_FOOT_OFFSET_X = 30;  // lateral spacing of the strip's own 2
                                  // feet -- own choice, not a cited
                                  // figure (chosen to sit well inside
                                  // FACE_W/2=63.75 on each side).

// Ballast reserve (PR #52 review finding #5): the bead description
// says to "leave room for a later ballast insert (weighted-base
// fallback, not committed)" -- this was missing entirely from the
// first version of this file. This is a shallow pocket cut into the
// base strip's TOP face (the side facing into the assembled interior,
// not the table-facing underside), reserving genuine volume without
// committing to any specific ballast part/shape -- NOT a finished
// ballast design, just reserved space, consistent with the bead's own
// "not committed" wording.
BALLAST_RESERVE_W = 40.0;  // own choice -- centred, comfortably inside
                            // the two foot recesses (at FACE_W/2 +/-30
                            // = 31/91, each FOOT_RECESS_D=10.4mm wide,
                            // so their outer edges sit at ~25.8/96.2 --
                            // this leaves >4mm clearance on each side).
BALLAST_RESERVE_D = 10.0;  // own choice -- leaves >2mm margin on the
                            // strip's own 14.5mm depth, front and back.
BALLAST_RESERVE_T = 1.0;   // shallow -- half of the strip's own 2.0mm
                            // thickness (BASE_STRIP_T), leaving a 1.0mm
                            // floor so the table-facing underside is
                            // never breached.

// Foot product (bead: "feet pockets sized for a NAMED rubber/gel pad
// product"): picked a 10mm (diameter) x 3mm (thick) self-adhesive
// round rubber/polyurethane foot. This is not one single SKU but a size
// that recurs, essentially unchanged, across multiple distributors'
// catalogues -- Delock 18309 (10 x 3mm self-adhesive round feet),
// Essentra RBS-10 (9.9mm dia x 3mm), Multicomp Pro MP2010-CL1-48 (10mm
// dia x 3.1mm -- the same-size listed replacement for Multicomp's own
// PD.2010C, which element14 lists as no longer manufactured; PR #52
// review minor item), Ettinger 17-52-108 (10mm dia x 3.2mm) -- which is itself good
// evidence this is a genuinely standard, widely-stocked size rather than
// one vendor's quirk, satisfying "high-friction rubber/gel feet" (ADR)
// without betting on a single hard-to-source part. FOOT_RECESS_D above
// (10.4mm) gives the 10mm pad a shallow registration pocket with 0.4mm
// clearance; FOOT_RECESS_T (1.0mm) is intentionally shallow relative to
// the pad's own ~3mm thickness so most of the compliant material stays
// proud of the shell and actually grips the table, per the ADR's
// friction/shear argument.

// =====================================================================
// Helper modules
// =====================================================================

module rounded_rect(w, h, r) {
    hull() {
        translate([r, r])     circle(r = r, $fn = 48);
        translate([w - r, r]) circle(r = r, $fn = 48);
        translate([r, h - r]) circle(r = r, $fn = 48);
        translate([w - r, h - r]) circle(r = r, $fn = 48);
    }
}

module rounded_box(w, h, depth, r) {
    linear_extrude(height = depth) rounded_rect(w, h, r);
}

// A plain boss cylinder (no pocket of its own). Insert pockets are cut
// separately, in one difference() at the back_shell_local() level, not
// inside this module -- see the comment on pcb_mount_insert_pockets()
// below for why: INSERT_LEN (4.0mm) is deeper than the PCB bosses are
// tall (REAR_CLEARANCE, 3.0mm) by design (the pocket is meant to dip
// slightly into the back wall below), and subtracting a pocket that
// deep from just the boss cylinder in isolation would delete the whole
// boss rather than leave a blind pocket.
module boss_solid(height, boss_d = BOSS_OD) {
    cylinder(h = height, d = boss_d, $fn = 32);
}

// =====================================================================
// Back shell (local frame)
// =====================================================================

module back_shell_shell() {
    difference() {
        rounded_box(FACE_W, FACE_H, BACK_SHELL_DEPTH, CORNER_R);
        // Hollow it out: a through-cut from just above the back wall
        // (bz = WALL_T) out past the open front rim, inset by WALL_T on all
        // four sides. pilink-6lz: FACE_W/FACE_H are now BOARD_W/H plus
        // 2*(WALL + clearance) (common.scad), so this one cavity already
        // leaves the board BOARD_CLEARANCE_X = 0.5mm on each side and
        // BOARD_CLEARANCE_Y = 1.0mm top and bottom, centred. (Before, the X
        // side wall was thinned to 1.6mm to buy 0.4mm and Y had 0.00mm at the
        // bottom; the side wall is back to a full 2.0mm.)
        //
        // pilink-cix: the cavity's four corners are SQUARE (corner relief),
        // not rounded, so the board's square corners are never clipped
        // (Edge.Cuts has no corner arcs). With the outer corner at CORNER_R =
        // 3.0 (centre (3,3) from the face corner) the square inner corner at
        // (2.0, 2.0) is sqrt(1^2 + 1^2) = 1.41mm from that centre, so the wall
        // at the diagonal is 3.0 - 1.41 = 1.59mm: thinner than the 2.0mm walls
        // elsewhere, but still >= 3 perimeters of a 0.4mm nozzle.
        translate([WALL_T, WALL_T, WALL_T])
            cube([FACE_W - 2*WALL_T, FACE_H - 2*WALL_T, BACK_SHELL_DEPTH]);
    }
}

// pilink-6lz: H4 (board (29, 2.5) -> face (31.5, 50.5)) sits 3.5mm below the
// top wall's inner surface (Q 54), so a 7.0mm boss is exactly TANGENT to the
// wall -- a line contact that makes the STL non-manifold. A 7.5mm boss on H4
// overlaps the wall by 0.25mm instead and fuses with it cleanly (the boss
// stays behind the board, which ends at Q 53, so nothing else is affected).
BOSS_OD_H4 = BOSS_OD + 0.5;

module pcb_mount_boss_solids() {
    for (i = [0 : len(PCB_MOUNT_HOLES_FACE) - 1])
        translate([PCB_MOUNT_HOLES_FACE[i][0], PCB_MOUNT_HOLES_FACE[i][1], BACK_WALL_T])
            boss_solid(height = REAR_CLEARANCE,
                       boss_d = (i == 3) ? BOSS_OD_H4 : BOSS_OD);
            // Boss spans bz = BACK_WALL_T .. BACK_WALL_T+REAR_CLEARANCE
            // (= 5.0mm = exactly the PCB's back surface, see the
            // BACK_SHELL_DEPTH stack-up above).
}

module pcb_mount_insert_pockets() {
    // Bored from the PCB-facing top (bz = BACK_WALL_T+REAR_CLEARANCE,
    // the PCB's own back surface -- screw comes from the front, through
    // the PCB's mounting hole, down into this insert) downward by
    // INSERT_LEN. INSERT_LEN (4.0mm) is deeper than the boss alone
    // (REAR_CLEARANCE, 3.0mm), so this deliberately dips ~1mm into the
    // solid back wall below -- it stays blind (BACK_WALL_T=2.0mm, so
    // the pocket bottom at bz=1.0 is still 1.0mm short of the back
    // wall's own outer face at bz=0).
    for (p = PCB_MOUNT_HOLES_FACE)
        translate([p[0], p[1], BACK_WALL_T + REAR_CLEARANCE - INSERT_LEN])
            cylinder(h = INSERT_LEN + 0.1, d = INSERT_OD, $fn = 32);
}

// pilink-9i4: the J401 boss pad (and its cable-vs-table clamp) is gone; the
// 7.0mm cavity holds the connector entirely inside the shell.
module usbc_cutout() {
    translate([USBC_PFACE - USBC_CUTOUT_W/2,
               USBC_QFACE - USBC_CUTOUT_H/2,
               -USBC_BOSS_RISE - 0.5])
        cube([USBC_CUTOUT_W, USBC_CUTOUT_H,
              USBC_BOSS_RISE + BACK_SHELL_DEPTH + 1.0]);
}

// pilink-9i4 (rev 2): the leg-mount boss keeps the original scheme (heat-set
// insert in the boss tip, screw from the foot through the leg). Its flat base
// face used to sit proud of the plate (the tilted cylinder's base disc is only
// cut by the rear plane, leaving half of it exposed), so the boss is extended
// back along its own axis and clipped at the plate's inner side (bz = 1.0):
// the cylinder runs into the rear surface with no exposed flat face.
LEG_BOSS_EXTEND = 8.0;   // extension behind the base along the boss axis

module leg_mount_boss_solids() {
    for (x = [LEG_PFACE_LEFT, LEG_PFACE_RIGHT])
        translate([x, LEG_MOUNT_Q, 0])
            intersection() {
                rotate([LEG_BOSS_TILT, 0, 0])
                    translate([0, 0, -LEG_BOSS_EXTEND])
                        boss_solid(height = LEG_MOUNT_BOSS_LEN + LEG_BOSS_EXTEND);
                translate([-50, -50, -50]) cube([100, 100, 51.0]);
            }
}

module leg_mount_insert_pockets() {
    for (x = [LEG_PFACE_LEFT, LEG_PFACE_RIGHT])
        translate([x, LEG_MOUNT_Q, 0])
            rotate([LEG_BOSS_TILT, 0, 0])
                translate([0, 0, LEG_MOUNT_BOSS_LEN - INSERT_LEN])
                    cylinder(h = INSERT_LEN + 0.1, d = INSERT_OD, $fn = 32);
}

// pilink-6lz: relief in the top wall so the Ø1.13 pigtail can cross the PCB
// plane above the board's (now 1.0mm) top-edge gap; see common.scad. Face-frame
// Z maps to local bz = BODY_T - Z.
module pigtail_notch_cutout() {
    translate([PIGTAIL_NOTCH_X0, FACE_H - WALL_T - 0.01, BODY_T - PIGTAIL_NOTCH_Z1])
        cube([PIGTAIL_NOTCH_X1 - PIGTAIL_NOTCH_X0, PIGTAIL_NOTCH_DEPTH + 0.01,
              BACK_SHELL_DEPTH + 1 - (BODY_T - PIGTAIL_NOTCH_Z1)]);
}

module back_shell_local() {
    difference() {
        union() {
            back_shell_shell();
            pigtail_spool();
            pcb_mount_boss_solids();
            leg_mount_boss_solids();
        }
        usbc_cutout();
        pigtail_notch_cutout();
        pcb_mount_insert_pockets();
        leg_mount_insert_pockets();
    }
}

// =====================================================================
// Base strip (world frame -- built flat/level directly, see header note)
// =====================================================================
// Reference point: this file's own open-rim bottom edge (local Qface=0,
// bz=BACK_SHELL_DEPTH) is treated as a stand-in for the ADR's "front
// edge" (the real front edge is the front shell's own face surface,
// further forward still by FACE_T+FRONT_CAVITY=7.5mm -- that's
// pilink-8hx.2's geometry, not built here). Using this file's own edge
// is a conservative, explicitly-flagged simplification; a human should
// re-check leg/strip placement once the front shell exists. (PR #52
// review: left as-is, not re-derived against BODY_T, since doing so
// here risks drifting out of sync with the leg-axis geometry above,
// which was computed and hand-verified against THIS same stand-in --
// a human re-deriving one should re-check the other.)
// front_edge_y/z, leg_mount_y/z and leg_foot_y/z are now computed once,
// earlier in the file (the "Leg axis geometry" block, Rear legs
// section) so this module and leg() below read the same values.

// pilink-9i4: feet pockets as a cutter, applied to the strip AND the shell.
// The shell's rear-bottom corner dips into the strip's y 0..1 band over
// z ~0..3.7, so cutting the pockets only from the strip left the back plate
// filling half of each one.
module feet_recess_cutters() {
    z0 = front_edge_z;
    z1 = front_edge_z - BASE_STRIP_DEPTH;
    for (side = [-1, 1])
        translate([FACE_W/2 + side*BASE_STRIP_FOOT_OFFSET_X, -0.1, (z0 + z1)/2])
            rotate([-90, 0, 0])
                cylinder(h = FOOT_RECESS_T + 0.1, d = FOOT_RECESS_D, $fn = 32);
}

module shell_world() {
    difference() {
        rotate([-LEAN_DEG, 0, 0]) back_shell_local();
        feet_recess_cutters();
    }
}

module base_strip() {
    z0 = front_edge_z;
    z1 = front_edge_z - BASE_STRIP_DEPTH;
    difference() {
        // cube([x,y,z]) = [FACE_W, BASE_STRIP_T, z0-z1]: lateral width,
        // then the strip's own small vertical thickness (Y, sitting on
        // the table at Y=0..BASE_STRIP_T), then its 14.5mm depth (Z,
        // from z1 up to z0).
        translate([0, 0, z1])
            cube([FACE_W, BASE_STRIP_T, z0 - z1]);
        // feet recesses, cut from the strip's bottom (table-facing) face
        feet_recess_cutters();
        // Ballast reserve (review finding #5): shallow pocket cut from
        // the strip's TOP (interior-facing) face, centred, well clear
        // of both foot recesses -- see BALLAST_RESERVE_* above. Not a
        // committed ballast design, just reserved room.
        translate([FACE_W/2 - BALLAST_RESERVE_W/2,
                   BASE_STRIP_T - BALLAST_RESERVE_T,
                   (z0 + z1)/2 - BALLAST_RESERVE_D/2])
            cube([BALLAST_RESERVE_W, BALLAST_RESERVE_T + 0.1, BALLAST_RESERVE_D]);
    }
}

// =====================================================================
// Leg (world frame)
// =====================================================================
// Mount point: PR #52 review finding #6 -- previously this was the back
// wall's own outer surface (bz=0), which made the leg's mount-end
// sphere (r=4) overlap the boss/shell by ~4mm since the capsule started
// AT the wall rather than at the boss's own tip. Now uses
// leg_mount_tip_y/z (derived above, in the "Leg axis geometry" block),
// the point LEG_MOUNT_BOSS_LEN out from the wall ALONG THE SAME tilted
// axis the boss itself now uses (LEG_BOSS_TILT).
//
// Still-blocking re-review on 46647da (finding #6, round 2): moving the
// capsule's mount-end SPHERE to that tip point did not actually make it
// flush -- a sphere of radius LEG_STRUT_D/2 (4mm) centred ON the boss's
// tip still reaches 4mm back INTO the boss along the axis (the boss is
// only LEG_MOUNT_BOSS_LEN=6mm long), filling the boss's last 4mm --
// which is exactly where leg_mount_insert_pockets() puts the heat-set
// insert pocket (axis distance 2..6.1 from the wall). "Mates flush"
// was true of the POINT the capsule started at, not of the capsule's
// actual solid, so the leg and back-shell STLs still intersected.
// Fixed below: the mount end is now a flat disc (MOUNT_CAP_T thick,
// same LEG_STRUT_D diameter), rotated to the boss's own net world axis
// angle (LEG_BOSS_TILT - LEAN_DEG) and centred at p_mount, so the
// strut's solid stops at the boss's own tip FACE instead of wrapping
// around and past it. This still leaves the exact mounting lug/socket
// interface geometry (where the leg physically registers onto the
// boss, beyond just the screw) unmodelled -- a human should add that
// once this is actually rendered and fitted.

module leg(side) {
    x = FACE_W/2 + side*LEG_OFFSET;
    p_mount = [x, leg_mount_tip_y, leg_mount_tip_z];
    p_foot  = [x, leg_foot_y,      leg_foot_z];
    // PR #52 review finding #3(b): the strut capsule's own foot-end
    // sphere (r = LEG_STRUT_D/2) was centred AT p_foot (world Y=0, the
    // table datum), so it reached 4mm BELOW the table -- the leg would
    // have stood on this sphere, not on the modelled rubber foot. A
    // sphere's lowest point is simply (centre Y - radius) regardless of
    // its other coordinates, so raising the centre to Y=LEG_STRUT_D/2
    // puts its lowest point exactly at Y=0; the flat foot pad below
    // (still built at the true p_foot) fills the small remaining gap
    // down to the table, and is what actually contacts it.
    p_foot_strut = [p_foot[0], LEG_STRUT_D/2, p_foot[2]];
    difference() {
        union() {
            // Strut: hull of a flat disc at the mount end and a sphere
            // at the (raised) foot end. The foot end stays a sphere --
            // direction-agnostic is fine there, since only its lowest
            // point matters (review finding #3(b), above). The mount
            // end is a disc, not a sphere (review finding #6, round 2,
            // see the comment above p_mount): a sphere centred on the
            // boss tip reaches back along the axis and fills part of
            // the boss, including its own insert pocket, with solid
            // strut material -- not actually flush. A disc perpendicular
            // to the mount->foot axis, rotated by that same net world
            // angle (LEG_BOSS_TILT - LEAN_DEG -- the boss's own axis,
            // see the "Leg axis geometry" block) and centred AT p_mount,
            // caps the strut at the boss's own tip face instead of past
            // it. This does use an arbitrary-axis rotation; the old
            // reason for avoiding one here ("can't test-render to
            // verify") no longer applies now that the screw-head
            // counterbore below (LEG_AXIS_TILT) already relies on
            // exactly this kind of rotation and was independently
            // re-verified by the PR #52 review.
            hull() {
                translate(p_mount)
                    rotate([LEG_BOSS_TILT - LEAN_DEG, 0, 0])
                        cylinder(h = MOUNT_CAP_T, d = LEG_STRUT_D, $fn = 24, center = true);
                translate(p_foot_strut) sphere(d = LEG_STRUT_D, $fn = 24);
            }
            // Flat pad at the foot end for the rubber foot to stick to.
            // Genuinely vertical (unlike the counterbore below): this
            // is the part that must sit flat against the horizontal
            // table regardless of the leg's own angle.
            // (cylinder() is already centred in X/Z by the rotate below,
            // so the translate only needs the foot's own X/Z position,
            // same pattern as the counterbore block below.)
            translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
                rotate([-90, 0, 0])
                    cylinder(h = FOOT_PAD_T, d = FOOT_PAD_D, $fn = 32);
        }
        // Screw channel: another capsule, hidden-fastener design (see
        // LEG_MOUNT_BOSS_LEN comment above) -- a single long screw runs
        // from the foot end up into the back-shell's insert, now along
        // the SAME axis as that insert (review finding #2), since
        // p_mount is the boss's own tip.
        hull() {
            translate(p_mount) sphere(d = SCREW_CHANNEL_D, $fn = 16);
            translate(p_foot)  sphere(d = SCREW_CHANNEL_D, $fn = 16);
        }
        // Foot-pad registration recess: genuinely vertical (same axis
        // as the pad above, not the screw) -- PR #52 review finding
        // #3(a): previously stacked ABOVE the counterbore in the same
        // (wrong) vertical frame, landing inside the strut above the
        // pad instead of at the bottom. Now cut first, directly from
        // the bottom (y ~ -0.1..0.9), where the rubber foot actually
        // sits, within the FOOT_PAD_D=12mm pad (FOOT_RECESS_D=10.4mm
        // fits inside it with margin).
        translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
            rotate([-90, 0, 0])
                cylinder(h = FOOT_RECESS_T + 0.1, d = FOOT_RECESS_D, $fn = 32);
        // Screw-head counterbore: review finding #2's last point -- was
        // vertical (~38 deg off the screw axis), now aligned to
        // LEG_AXIS_TILT (derived above), the same straight line as the
        // screw channel and the boss's own insert. Starts just past the
        // foot recess (so the two don't have to share one frame) and
        // extends up into the strut along the real screw path.
        translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
            rotate([LEG_AXIS_TILT, 0, 0])
                translate([0, 0, FOOT_RECESS_T])
                    cylinder(h = 3.0, d = SCREW_HEAD_D, $fn = 16);
    }
}

// =====================================================================
// USB-C vs. rear-leg clearance check (this bead's own NOTE)
// =====================================================================
// J401's shell long axis is horizontal (board/face X) -- confirmed
// against the real footprint instance in hardware/pico-link-hw.kicad_pcb
// (rot 0, pad geometry), see the USBC_HEIGHT_ABOVE_PCB comment above.
usbc_edge_left  = USBC_PFACE - USBC_SHELL_W/2;
usbc_edge_right = USBC_PFACE + USBC_SHELL_W/2;
leg_surface_left  = LEG_PFACE_LEFT  + LEG_STRUT_D/2;
leg_surface_right = LEG_PFACE_RIGHT - LEG_STRUT_D/2;
clearance_left  = usbc_edge_left  - leg_surface_left;
clearance_right = leg_surface_right - usbc_edge_right;

echo(str("BODY_T (sanity check vs. ADR ~14mm): ", BODY_T));
echo(str("Leg length (mount to foot, derived): ", leg_length, " mm"));
echo(str("Leg mount point (world y,z): (", leg_mount_y, ", ", leg_mount_z, ")"));
echo(str("Leg foot point (world y,z): (", leg_foot_y, ", ", leg_foot_z, ")"));
echo(str("USB-C port lateral centre (Pface): ", USBC_PFACE,
         " -- legs at Pface ", LEG_PFACE_LEFT, " / ", LEG_PFACE_RIGHT));
echo(str("USB-C-to-leg clearance, left: ", clearance_left, " mm"));
echo(str("USB-C-to-leg clearance, right: ", clearance_right, " mm"));
// pilink-3ym: USB-C cable-vs-table numbers at the raised J401 (Qface 15),
// same method as enclosure/README.md's pilink-8ry section (boot = 2D offset
// of the mating axis by D/2, axis 15 deg below horizontal heading -bz,
// mating face at bz = +2.5 after pilink-9i4: recessed 2.5mm behind the outer face). Mating-face world position:
usbc_face_y = USBC_QFACE*cos(LEAN_DEG) + USBC_MATING_BZ*sin(LEAN_DEG);   // pilink-9i4: bz +2.5 (recessed)
usbc_face_z = -USBC_QFACE*sin(LEAN_DEG) + USBC_MATING_BZ*cos(LEAN_DEG);
// along-axis distance to table contact for a boot of diameter D:
function usbc_table_s(D) = (usbc_face_y - (D/2)*cos(LEAN_DEG)) / sin(LEAN_DEG);
echo(str("USB-C mating face world (Y,Z): (", usbc_face_y, ", ", usbc_face_z,
         "); 6.3mm boot reaches the table ", usbc_table_s(6.3), "mm along the axis (was 11.0mm at Qface 6.5)"));
// Both come out to ~31.5mm in this model (40mm leg offset minus the
// connector's own 4.5mm shell half-width minus the leg's own 4mm strut
// half-width) -- the legs run at a constant lateral (Pface) position
// top to bottom in this model, so this clearance holds at every height
// along the leg, not just at one cross-section. No clearance conflict
// found between J401 and the rear legs.

// =====================================================================
// Top-level assembly / render selection
// =====================================================================
// PART: "assembly" (default, for visual review once OpenSCAD is
// available), "back_shell" or "leg_left" / "leg_right" (for individual
// STL export -- these are 3 separately-printed parts).
PART = "assembly";

if (PART == "assembly") {
    color("dimgray") shell_world();
    color("gray") base_strip();
    color("slategray") leg(-1);
    color("slategray") leg(1);
} else if (PART == "back_shell") {
    shell_world();
    base_strip();
} else if (PART == "leg_left") {
    leg(-1);
} else if (PART == "leg_right") {
    leg(1);
}
