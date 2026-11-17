// Pico Link enclosure -- back shell + rear fin stand (pilink-8hx.1, pilink-s98)
//
// Scope of THIS file: the back shell (PCB-mounting bosses, the clearance
// cavity behind the PCB, the rear USB-C cutout, the pigtail spool and the
// top-wall pigtail notch) plus the stand: two flat triangular fins off the
// back wall, each carrying two rubber-foot pads, printed in one piece with
// the shell (pilink-s98, replaces the glued two-leg A-frame and the base
// strip with feet). The front shell, knob, plungers and antenna mount are
// their own files.
//
// The user-tunable parameters come first, with OpenSCAD Customizer
// annotations (/* [Section] */ headers, `// [min:step:max]` ranges, a
// description comment on the line above each). They are literals placed
// BEFORE `include <common.scad>` so the Customizer lists them; everything
// after /* [Hidden] */ is derived. Every fin, pad and recess dimension below
// follows from these, from LEAN_DEG and from the shell constants -- no fin
// geometry is hard-coded. Rendered and checked with OpenSCAD 2021.01 and
// enclosure/scripts/check_fit.sh; see enclosure/README.md (pilink-s98).
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
// 2. "World" frame (the fins, the feet and the top-level assembly):
//      X unchanged (lateral position is unaffected by the body's lean).
//      Y = height, Z = forward (+) / back (-).
//    World = rotate([-LEAN_DEG, 0, 0]) applied to the local frame, so the
//    datum (world Y = 0, Z = 0) is the back wall's bottom-outer edge (local
//    Qface = 0, bz = 0). With the body leaning back, that edge is the
//    body's LOWEST point (the bottom face rises toward the front at
//    LEAN_DEG), so "the body's bottom edge" below always means this edge.
//    The fin bottoms sit at world Y = -FLOAT_GAP; the table is a further
//    FOOT_H - FOOT_RECESS_DEPTH lower (rubber feet, not modelled in the
//    printed part).
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

/* [Stand] */
// Body lean back from vertical, degrees (ADR: ~15, face ~75 deg to the table). Fins, pads and the tip-over estimate all follow it. Below ~8 the CoG moves too far forward for a useful front tip-over margin.
LEAN_DEG = 15; // [8:1:25]
// How far the fin bottoms reach below the body's lowest (rear-bottom) edge, mm. 0 = flush: the float then comes from the rubber feet only.
FLOAT_GAP = 0; // [0:0.5:15]

/* [Fins] */
// Fin thickness, mm (lateral). The fins stay this thin except at the foot pads.
FIN_T = 3.0; // [2:0.5:6]
// Lateral offset of each fin from the face centreline, mm (+/-30 = the removed base strip's foot positions).
FIN_OFFSET_X = 30; // [12:1:58]
// Height of each fin's top corner up the back, measured along the face from its bottom edge, mm.
FIN_TOP_Q = 40; // [10:1:52]
// Rear foot centre, horizontal distance behind the body's rear-bottom edge, mm (45: user decision 2026-11-17; a button press tips it back at ~2.5 N, about where the feet would slide anyway).
FIN_REACH = 45; // [15:1:70]

/* [Feet] */
// Rubber foot diameter, mm.
FOOT_DIA = 6.5; // [3:0.5:15]
// Depth of the centring recess in each foot pad, mm.
FOOT_RECESS_DEPTH = 0.6; // [0:0.1:1.5]
// Diametral clearance of the recess around the foot, mm.
FOOT_RECESS_CLEARANCE = 0.4; // [0:0.1:1]
// Pad rim width outside the recess, mm.
FOOT_PAD_RIM = 1.2; // [0.8:0.1:4]
// Pad disc thickness, mm (a 45 deg taper above it blends the pad into the fin).
FOOT_PAD_T = 1.6; // [1:0.1:4]
// Front foot: position of its REAR edge relative to the body's rear-bottom edge, mm (+ = forward, under the body). 3.5 gives ~7.5mm of forward tip-over margin; more = the front pads sit further under the body (taller where they show against its sloped underside).
FRONT_FOOT_OFFSET = 3.5; // [-5:0.5:10]
// Rubber foot height, mm -- DISPLAY ONLY (assembly view); no printed geometry uses it.
FOOT_H = 2.0; // [0.5:0.1:8]
// Show the rubber feet in the assembly view.
SHOW_FEET = true;

/* [Render] */
// What to render: the assembly view, or the printable back shell (with its fins) alone.
PART = "assembly"; // [assembly, back_shell]

/* [Hidden] */
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
// gaps). Customizer note: this include makes the file depend on
// common.scad; a single-file upload (e.g. an online configurator) needs it
// inlined first.
include <common.scad>

WALL_T      = WALL;    // = 2.0mm side/top/bottom wall, same as the back wall

// --- Body thickness stack-up (PROP 6c: "about 14mm. That's face 2.0,
// 5.5mm to the PCB (5.0 switches, 3.3 panel stack, J501 ~2mm), PCB 1.6,
// 3mm behind the PCB for the encoder's leads, and a 2.0mm back wall.")
// Only the last three terms belong to the BACK shell; the first two
// (face wall + front cavity) are pilink-8hx.2's (front shell) to build.
FACE_T          = 2.0;   // front shell's own face wall -- not built here,
FRONT_CAVITY    = 5.5;   // ...nor the front cavity -- both only used here
                           // for the BODY_T sanity check below, so the
                           // two shells meet correctly.
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

BACK_SHELL_DEPTH = PCB_T + REAR_CLEARANCE + BACK_WALL_T;  // = 10.6mm --
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
// USBC_MATING_BZ), so a full-size plug has to pass the opening to seat. USB-IF
// Type-C spec (rev 1.2) max overmould is 12.35 x 6.5mm with 6.65mm of plug past
// it; opening = overmould + ~0.85mm FDM clearance, corners radiused.
USBC_CUTOUT_W   = 13.2;
USBC_CUTOUT_H   = 7.4;
USBC_CUTOUT_R   = 1.0;
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
        back_shell_cavity();
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
        linear_extrude(height = USBC_BOSS_RISE + BACK_SHELL_DEPTH + 1.0)
            rounded_rect(USBC_CUTOUT_W, USBC_CUTOUT_H, USBC_CUTOUT_R);
}

// pilink-6lz: relief in the top wall so the Ø1.13 pigtail can cross the PCB
// plane above the board's (now 1.0mm) top-edge gap; see common.scad. Face-frame
// Z maps to local bz = BODY_T - Z.
module pigtail_notch_cutout() {
    translate([PIGTAIL_NOTCH_X0, FACE_H - WALL_T - 0.01, BODY_T - PIGTAIL_NOTCH_Z1])
        cube([PIGTAIL_NOTCH_X1 - PIGTAIL_NOTCH_X0, PIGTAIL_NOTCH_DEPTH + 0.01,
              BACK_SHELL_DEPTH + 1 - (BODY_T - PIGTAIL_NOTCH_Z1)]);
}

// The open cavity, as its own module so the fins can be clipped against it
// (same box back_shell_shell() subtracts).
module back_shell_cavity() {
    translate([WALL_T, WALL_T, WALL_T])
        cube([FACE_W - 2*WALL_T, FACE_H - 2*WALL_T, BACK_SHELL_DEPTH]);
}

module back_shell_local() {
    difference() {
        union() {
            back_shell_shell();
            pigtail_spool();
            pcb_mount_boss_solids();
        }
        usbc_cutout();
        pigtail_notch_cutout();
        pcb_mount_insert_pockets();
    }
}

// =====================================================================
// Rear fin stand (pilink-s98, world frame)
// =====================================================================
// Replaces the glued two-leg A-frame (pilink-8jy) and the base strip with
// its feet and ballast pocket. User design, 2026-11-17: two flat triangular
// fins behind the body at the old base-strip feet positions (FACE_W/2 +/-
// FIN_OFFSET_X), hidden behind the body in the straight-on front view, each
// with rubber-foot pads; fin bottoms FLOAT_GAP below the body's lowest edge.
//
// Fin outline, in the world Y-Z plane (side view), FIN_T thick in X:
//   - front edge: along the back wall's outer face, from the bottom edge up
//     to FIN_TOP_Q (embedded FIN_EMBED into the 2mm wall so it fuses),
//     then straight down FLOAT_GAP to the fin bottom;
//   - bottom edge: flat at world Y = -FLOAT_GAP, back to the rear pad's far
//     edge;
//   - back edge: a short vertical step (pad height) at the rear, then the
//     hypotenuse up to the top corner on the back face.
//
// TWO pads per fin, front and rear (four feet; user decision 2026-11-17).
// The brief said "a foot pad per fin"; one pad per fin is two contact points
// in total, i.e. a line, and the body tips over it front-to-back
// (statically unstable at any lean). The minimum stable stance on two fins
// is a pad at each end of each fin's bottom edge, giving a FOOT_DIA-wide
// rectangle of contact under the four feet.
//
// Front pad position: the body's centre of gravity sits just AHEAD of the
// rear-bottom edge at LEAN 15 (see the tip-over estimate below), so the
// front feet must reach forward of that edge, i.e. under the body.
// FRONT_FOOT_OFFSET puts each front foot's rear edge that far ahead of it
// (3.5 by default, ~7.5mm forward margin, more than the mass model's likely
// error). The cost is visibility: in a dead-level front view the front pads
// show against the body's sloped underside (2.6mm tall at LEAN 15) and the
// rubber feet below its outline; the fins themselves stay hidden.

FIN_EMBED   = BACK_WALL_T - 1.2;   // 0.8mm into the 2.0mm back wall (fuses; stays clear of the 1.0mm insert-pocket floor)
FOOT_RECESS_D = FOOT_DIA + FOOT_RECESS_CLEARANCE;          // centring recess diameter
FOOT_PAD_D  = FOOT_RECESS_D + 2*FOOT_PAD_RIM;              // pad disc diameter
FOOT_PAD_TAPER_H = (FOOT_PAD_D - FIN_T) / 2;               // 45 deg taper, pad -> fin thickness
FRONT_FOOT_Z = FRONT_FOOT_OFFSET + FOOT_DIA/2;             // front foot centre, world Z (datum = rear-bottom edge)
REAR_FOOT_Z  = -FIN_REACH;                                 // rear foot centre, world Z
FIN_BOTTOM_Y = -FLOAT_GAP;                                 // fin bottom / pad underside, world Y
FIN_X = [FACE_W/2 - FIN_OFFSET_X, FACE_W/2 + FIN_OFFSET_X]; // fin mid-planes, world X

// local (Qface, bz) -> world (Y, Z): the rotate([-LEAN_DEG,0,0]) above.
function w_y(q, bz) = q*cos(LEAN_DEG) + bz*sin(LEAN_DEG);
function w_z(q, bz) = -q*sin(LEAN_DEG) + bz*cos(LEAN_DEG);

FIN_TOP_Y = w_y(FIN_TOP_Q, 0);   // top corner on the back face
FIN_TOP_Z = w_z(FIN_TOP_Q, 0);
FIN_REAR_Z = REAR_FOOT_Z - FOOT_PAD_D/2;   // fin's rear end = rear pad's far edge
BODY_TOP_Y = w_y(FACE_H, 0);               // back-top edge: lowest point of the top of the silhouette

assert(FOOT_PAD_T >= FOOT_RECESS_DEPTH + 0.8, "foot pad too thin over its centring recess");
assert(FIN_TOP_Q <= FACE_H - WALL_T, "fin top corner above the top wall");
assert(FIN_TOP_Y < BODY_TOP_Y, "fin top would show above the body in the front view");
assert(FIN_OFFSET_X + FOOT_PAD_D/2 <= FACE_W/2 - CORNER_R, "fin/pad would show beside the body in the front view");
assert(FIN_REAR_Z < FIN_TOP_Z, "fin reach too short for its height: not a triangle");
assert(REAR_FOOT_Z + FOOT_PAD_D/2 < FRONT_FOOT_Z - FOOT_PAD_D/2, "front and rear pads overlap");

// Side-view outline as [Z, Y] pairs.
function fin_outline() = [
    [w_z(FIN_TOP_Q, FIN_EMBED), w_y(FIN_TOP_Q, FIN_EMBED)],   // top corner, inside the wall
    [w_z(0, FIN_EMBED),         w_y(0, FIN_EMBED)],           // bottom edge, inside the bottom wall
    [w_z(0, FIN_EMBED),         FIN_BOTTOM_Y],                // straight down to the fin bottom
    [FIN_REAR_Z,                FIN_BOTTOM_Y],                // flat bottom to the rear pad's far edge
    [FIN_REAR_Z,                FIN_BOTTOM_Y + FOOT_PAD_T],   // short vertical rear step
    [FIN_TOP_Z,                 FIN_TOP_Y]                    // hypotenuse back up to the top corner
];

// rotate([0,90,0]) maps 2D (u, v, extrude w) -> world (X = w, Y = v, Z = -u).
module fin_plate(x) {
    translate([x, 0, 0])
        rotate([0, 90, 0])
            linear_extrude(height = FIN_T, center = true)
                polygon([ for (p = fin_outline()) [-p[0], p[1]] ]);
}

// Pad disc + 45 deg taper up into the fin (prints support-free upright).
module foot_pad(x, z) {
    translate([x, FIN_BOTTOM_Y, z])
        rotate([-90, 0, 0]) {
            cylinder(h = FOOT_PAD_T, d = FOOT_PAD_D, $fn = 48);
            translate([0, 0, FOOT_PAD_T - 0.01])
                cylinder(h = FOOT_PAD_TAPER_H + 0.01, d1 = FOOT_PAD_D, d2 = FIN_T, $fn = 48);
        }
}

module foot_recess(x, z) {
    translate([x, FIN_BOTTOM_Y - 0.1, z])
        rotate([-90, 0, 0])
            cylinder(h = FOOT_RECESS_DEPTH + 0.1, d = FOOT_RECESS_D, $fn = 48);
}

module foot_recesses() {
    for (x = FIN_X, z = [FRONT_FOOT_Z, REAR_FOOT_Z]) foot_recess(x, z);
}

// The front shell's zone (local bz >= BACK_SHELL_DEPTH), grown by
// FRONT_SHELL_CLEARANCE down below its bottom face and back past the joint
// plane. A front pad pushed far forward (FRONT_FOOT_OFFSET >~ 3 at LEAN 15)
// puts its taper under the front shell; this keeps a gap between the pad and
// the front shell instead of a near-touch or an edge contact at the joint.
// Only fin/pad material is removed: the shell itself is unioned separately.
FRONT_SHELL_CLEARANCE = 0.4;
module front_shell_zone() {
    translate([-1, -FRONT_SHELL_CLEARANCE, BACK_SHELL_DEPTH - FRONT_SHELL_CLEARANCE])
        cube([FACE_W + 2, FACE_H + FRONT_SHELL_CLEARANCE + 1, BODY_T]);
}

// Fins + pads, clipped so nothing reaches into the cavity, the USB-C
// opening or the front shell, whatever the parameters (e.g. a thick pad at
// FLOAT_GAP 0 under the bottom wall, or a fin moved onto the cutout).
module fins() {
    difference() {
        union() {
            for (x = FIN_X) {
                fin_plate(x);
                foot_pad(x, FRONT_FOOT_Z);
                foot_pad(x, REAR_FOOT_Z);
            }
        }
        rotate([-LEAN_DEG, 0, 0]) {
            back_shell_cavity();
            usbc_cutout();
            front_shell_zone();
        }
    }
}

// The printed part: shell + fins. The foot recesses are cut from the shell
// too: at FLOAT_GAP 0 with a small FRONT_FOOT_OFFSET the front recess clips
// the body's rear-bottom edge by up to FOOT_RECESS_DEPTH (the old feet
// pockets did the same, pilink-9i4); at the default 3.5 it stays clear.
module shell_world() {
    difference() {
        union() {
            rotate([-LEAN_DEG, 0, 0]) back_shell_local();
            fins();
        }
        foot_recesses();
    }
}

// Rubber feet, display only (FOOT_H is not used by any printed geometry).
module feet_display() {
    for (x = FIN_X, z = [FRONT_FOOT_Z, REAR_FOOT_Z])
        translate([x, FIN_BOTTOM_Y + FOOT_RECESS_DEPTH - FOOT_H, z])
            rotate([-90, 0, 0])
                cylinder(h = FOOT_H, d = FOOT_DIA, $fn = 32);
}

// =====================================================================
// Tip-over estimate (pilink-s98)
// =====================================================================
// Centre of gravity of the assembled body WITHOUT the fins, in the local
// frame, from check_fit.py's mass model (rendered shells, knob, plungers and
// antenna mount at 1.24 g/cm3 solid; PCB slab FR4 1.85; component envelope
// boxes 1.0; display stack box 0.9, ~7.4 g; M2 screws steel -- see check_fit.py
// "tip-over"). Body ~81 g, fins ~8.4 g at the defaults (FIN_REACH 45). Leaving the
// fins out moves the CoG forward, i.e. it is conservative for forward
// tipping (the critical side). Re-measure (check_fit.sh prints it) if the
// shells or the PCB stack change.
COG_Q  = 28.4;    // mm up the face (check_fit.sh, pilink-s98: 28.35)
COG_BZ = 10.2;    // mm forward of the back wall's outer face (check_fit.sh: 10.23)
COG_Y = w_y(COG_Q, COG_BZ);
COG_Z = w_z(COG_Q, COG_BZ);
TIP_MARGIN_FRONT = (FRONT_FOOT_Z + FOOT_DIA/2) - COG_Z;   // CoG to the front feet's front edge
TIP_MARGIN_BACK  = COG_Z - (REAR_FOOT_Z - FOOT_DIA/2);    // CoG to the rear feet's back edge
echo(str("Tip-over (feet contact, world Z): CoG Z ", COG_Z, ", front feet edge ", FRONT_FOOT_Z + FOOT_DIA/2,
         ", rear feet edge ", REAR_FOOT_Z - FOOT_DIA/2, " -> margin front ", TIP_MARGIN_FRONT,
         " mm, back ", TIP_MARGIN_BACK, " mm"));
assert(TIP_MARGIN_FRONT > 0, "CoG ahead of the front feet: tips forward (raise FRONT_FOOT_OFFSET or LEAN_DEG)");

// =====================================================================
// Clearances: USB-C cable and antenna pigtail notch vs. the fins
// =====================================================================
// J401's shell long axis is horizontal (board/face X) -- confirmed
// against the real footprint instance in hardware/pico-link-hw.kicad_pcb
// (rot 0, pad geometry), see the USBC_HEIGHT_ABOVE_PCB comment above.
// The fins run at a constant X, so the lateral gap between the cutout
// (which passes a max-spec 12.35mm-wide plug overmould) and each fin's /
// pad's inner face holds along the cable's whole run back and down.
fin_inner_left  = FIN_X[0] + max(FIN_T, FOOT_PAD_D)/2;
fin_inner_right = FIN_X[1] - max(FIN_T, FOOT_PAD_D)/2;
usbc_open_left  = USBC_PFACE - USBC_CUTOUT_W/2;
usbc_open_right = USBC_PFACE + USBC_CUTOUT_W/2;
echo(str("USB-C opening to fin/pad inner faces: left ", usbc_open_left - fin_inner_left,
         " mm, right ", fin_inner_right - usbc_open_right, " mm (fin plates alone: ",
         usbc_open_left - (FIN_X[0] + FIN_T/2), " mm)"));
assert(usbc_open_left - fin_inner_left >= 5 && fin_inner_right - usbc_open_right >= 5,
       "fins/pads crowd the USB-C opening / cable");
// Pigtail notch: an internal relief in the TOP wall (face X 107..114, Q 54..55).
echo(str("Pigtail notch to nearest fin: ", PIGTAIL_NOTCH_X0 - (FIN_X[1] + FOOT_PAD_D/2), " mm in X, ",
         FACE_H - WALL_T - FIN_TOP_Q, " mm in Q below the top wall's inner face"));
echo(str("BODY_T (sanity check vs. ADR ~14mm): ", BODY_T));
echo(str("Fins: X ", FIN_X, ", top corner Q ", FIN_TOP_Q, " (world Y ", FIN_TOP_Y, ", Z ", FIN_TOP_Z,
         "), bottom Y ", FIN_BOTTOM_Y, ", feet Z ", FRONT_FOOT_Z, " / ", REAR_FOOT_Z, ", pad d ", FOOT_PAD_D));
// pilink-3ym: USB-C cable-vs-table numbers at the raised J401 (Qface 16),
// same method as enclosure/README.md's pilink-8ry section (boot = 2D offset
// of the mating axis by D/2, axis LEAN_DEG below horizontal heading -bz,
// mating face at bz = +2.5 after pilink-9i4: recessed 2.5mm behind the outer
// face). pilink-s98: the table is now FLOAT_GAP + FOOT_H - FOOT_RECESS_DEPTH
// below the datum; the echo uses FLOAT_GAP only (feet ignored), i.e. the
// worst case.
usbc_face_y = USBC_QFACE*cos(LEAN_DEG) + USBC_MATING_BZ*sin(LEAN_DEG);
usbc_face_z = -USBC_QFACE*sin(LEAN_DEG) + USBC_MATING_BZ*cos(LEAN_DEG);
// along-axis distance to table contact for a boot of diameter D:
function usbc_table_s(D) = (usbc_face_y + FLOAT_GAP - (D/2)*cos(LEAN_DEG)) / sin(LEAN_DEG);
echo(str("USB-C mating face world (Y,Z): (", usbc_face_y, ", ", usbc_face_z,
         "); 6.3mm boot reaches the table ", usbc_table_s(6.3), "mm along the axis (feet ignored)"));

// =====================================================================
// Top-level assembly / render selection
// =====================================================================
// PART (Customizer [Render] section): "assembly" (shell + fins, plus the
// rubber feet for display) or "back_shell" (the single printed part: shell
// with its fins, world frame; export_enclosure.py turns it upright onto the
// fin bottoms for printing). Any other value (check_fit.py uses "none")
// renders nothing, so the file can be included as a library.
if (PART == "assembly") {
    color("dimgray") shell_world();
    if (SHOW_FEET) color("black") feet_display();
} else if (PART == "back_shell") {
    shell_world();
}
