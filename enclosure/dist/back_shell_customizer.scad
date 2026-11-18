// GENERATED FILE -- do not edit. Single-file Customizer copy of
// enclosure/back_shell.scad with its includes inlined, for online OpenSCAD
// configurators (e.g. MakerWorld's Parametric Model Maker). Edit the source
// and regenerate: python3 enclosure/scripts/make_customizer.py

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
// Body lean back from vertical, degrees (25: user decision 2026-11-17; the ADR started from ~15). Fins, pads and the tip-over estimate all follow it. A smaller lean moves the CoG forward: with the front pads flush behind the rear-bottom edge (FRONT_FOOT_OFFSET 0) the forward tip-over margin is ~1.4mm at 25, ~4.0 at 30, and negative below ~23 (the assert stops the render; raise FRONT_FOOT_OFFSET to compensate: ~+4 at 15).
LEAN_DEG = 25; // [8:1:40]
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
// Radius of the fin's rounded rear tip (side view), mm: the hypotenuse rolls over this arc into the short upright heel that rises out of the rear foot pad.
FIN_TIP_R = 6; // [2:0.5:15]

/* [Feet] */
// Rubber foot diameter, mm.
FOOT_DIA = 6.5; // [3:0.5:15]
// Depth of the centring recess in each foot pad, mm.
FOOT_RECESS_DEPTH = 0.6; // [0:0.1:1.5]
// Diametral clearance of the recess around the foot, mm.
FOOT_RECESS_CLEARANCE = 0.4; // [0:0.1:1]
// Pad rim width outside the recess, mm.
FOOT_PAD_RIM = 1.2; // [0.8:0.1:4]
// How each foot pad grows out of its fin. boss: a round bun on the foot axis; flare: the fin's bottom edge widens over FOOT_FLARE_LEN into the pad; runner: the fin's whole bottom edge is a pad-wide rail, both feet recessed in it.
FOOT_STYLE = "runner"; // [boss, flare, runner]
// Height of the pad's short upright outer side, mm; above it the section rolls over a convex round (FOOT_PAD_ROUND) and a concave fillet into the fin.
FOOT_PAD_T = 0.8; // [0.4:0.1:3]
// Convex round on the pad's top outer edge, mm. The concave fillet into the fin takes the rest of the pad's overhang beyond the fin, (pad d - FIN_T)/2.
FOOT_PAD_ROUND = 1.6; // [0.5:0.1:3]
// flare: how far along the fin the flare runs from each foot centre, mm.
FOOT_FLARE_LEN = 14; // [6:0.5:30]
// Front foot pad: position of the pad disc's FRONT edge relative to the body's rear-bottom edge, mm (+ = forward, under the body). 0 = flush behind that edge, the whole pad under the fin (user decision 2026-11-17), at any LEAN_DEG / FOOT_DIA. Each +1 adds ~1mm of forward tip-over margin.
FRONT_FOOT_OFFSET = 0; // [-10:0.5:15]
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
// common.scad. For a single-file upload (MakerWorld's Parametric Model
// Maker and similar online configurators) use the generated
// enclosure/dist/back_shell_customizer.scad, which has it inlined
// (pilink-c6z: enclosure/scripts/make_customizer.py). Keep this include
// after /* [Hidden] */ -- the generator refuses it otherwise.
// ===== BEGIN inlined common.scad (was: include <common.scad>) =====
// =================================================================
// Pico Link enclosure -- shared board/face geometry (pilink-6lz)
//
// ONE definition of the board-to-face mapping, included by
// front_shell.scad, back_shell.scad and antenna_mount.scad
// (button_plunger.scad and knob.scad are board-independent and do not), and read (as plain `NAME = expr;`
// lines) by enclosure/scripts/check_fit.py and
// preview/scripts/export_enclosure.py. It contains no geometry, so it is
// not rendered on its own (check_fit.py skips it).
//
// KEEP EVERY ASSIGNMENT HERE ON ONE LINE (`NAME = expr;`, trailing
// `// comment` allowed): the Python scripts evaluate these with a
// line-based regex, not an OpenSCAD parser. Functions are fine (they are
// ignored by the scripts, which re-implement them from the constants).
//
// Frames (unchanged from the earlier shells):
//   board frame : origin = board top-left corner, x right, y DOWN.
//   face frame  : X = left -> right across the face (0 = left outer edge),
//                 Q = up the face (0 = bottom outer edge, FACE_H = top),
//                 Z = depth, 0 at the outer face surface.
//   X = board_x + MARGIN_X          (MARGIN_X = WALL + BOARD_CLEARANCE_X)
//   Q = QTOP - board_y              (QTOP = FACE_H - WALL - BOARD_CLEARANCE_Y)
// =================================================================

/* ============================ Board (as routed) ============================ */
// hardware/pico-link-hw.kicad_pcb Edge.Cuts, after pilink-4qc (PR #86).
BOARD_W = 122.5;
BOARD_H = 50.0;

/* ===================== Walls and board clearance ===================== */
// Shell wall / face-plate thickness (proposal 6c: "face 2.0 ... 2.0 mm back wall").
WALL = 2.0;

// Running clearance between the board's edge and the cavity wall, per side
// (pilink-6lz, supersedes pilink-mav). Budget the real tolerances: JLCPCB
// outline +/-0.2mm, FDM cavity wall +/-0.1-0.2mm, so +/-0.4mm worst case on
// each side; 0.5mm (X) / 1.0mm (Y) leaves >= 0.1mm worst case, i.e. the board
// never touches a wall even stacked at the extremes, and is not loose.
//  - X: 0.5mm/side widens the face from the earlier 122 to 127.5mm.
//  - Y: FACE_H stays 56mm (ADR/proposal figure, fin/USB-C numbers all
//    key off it), which leaves exactly 1.0mm/side; the old layout had 0.00mm at
//    the bottom and 2.00mm at the top.
BOARD_CLEARANCE_X = 0.5;
BOARD_CLEARANCE_Y = 1.0;

// Face outline: board + clearance + wall, so the board is centred in the
// cavity on both axes by construction.
FACE_W = BOARD_W + 2 * (WALL + BOARD_CLEARANCE_X); // 127.5
FACE_H = BOARD_H + 2 * (WALL + BOARD_CLEARANCE_Y); // 56.0

// Offsets of the board's top-left corner into the face frame.
MARGIN_X = WALL + BOARD_CLEARANCE_X;      // 2.5
QTOP = FACE_H - WALL - BOARD_CLEARANCE_Y; // 53.0 -- Q of board y = 0

function board_to_x(bx) = bx + MARGIN_X;
function board_to_q(by) = QTOP - by;
function board_to_face(bx, by) = [board_to_x(bx), board_to_q(by)];

/* ===================== Display panel (Crystalfontz CFAF240320A0) =====================
   Panel shadow, board-local, as placed by pilink-4qc: x 34.12..93.12, y 4..46
   (59 x 42), active area centred on the board's vertical centre and on the
   FACE's horizontal centre: board x 61.25 -> face X 63.75 = FACE_W / 2. */
PANEL_W = 59.0;
PANEL_H = 42.0;
PANEL_BOARD_X0 = 34.12;
PANEL_BOARD_X1 = PANEL_BOARD_X0 + PANEL_W; // 93.12
PANEL_BOARD_Y0 = 4.0;
PANEL_BOARD_Y1 = PANEL_BOARD_Y0 + PANEL_H; // 46.0

/* ===================== Input parts (board-local) ===================== */
// Alps EC11E18244AU shaft/knob centre (pilink-4qc): (14.25, 25).
ENCODER_BOARD_CX = 14.25;
ENCODER_BOARD_CY = 25.0;

// A/B/X/Y diamond (C&K PTS645), centre (108.25, 25), 8mm pitch.
BTN_Y = [108.25, 17]; // top
BTN_X = [100.25, 25]; // left
BTN_B = [116.25, 25]; // right
BTN_A = [108.25, 33]; // bottom

// SW101 / SW102 (BOOTSEL / RESET) side-actuated tact switches at the top edge.
SW101_BOARD = [42, 2.7];
SW102_BOARD = [52, 2.7];

// M2 mounting holes H1..H4 for the back-shell bosses (pilink-4qc).
PCB_MOUNT_HOLES_BOARD = [[10, 44], [116.5, 6], [116.5, 44], [29, 2.5]];

/* ===================== Pigtail notch (top wall) =====================
   The gap between the board's top edge (Q = QTOP = 53) and the top wall's inner
   surface (Q = FACE_H - WALL = 54) is BOARD_CLEARANCE_Y = 1.0mm, under the
   Ø1.13mm U.FL coax plus the antenna mount's lip/element (0.7mm) -- so the
   pigtail cannot cross the PCB plane at the board edge without a local relief.
   A notch is cut into the top wall of BOTH shells, in FACE-frame coordinates
   (face X, Q, Z from the outer face), just right of the antenna mount's land
   (which ends at face X 106.05) and clear of H3's boss (Q <= 50.5). */
PIGTAIL_NOTCH_X0 = 107.0;    // face X
PIGTAIL_NOTCH_X1 = 114.0;    // face X
PIGTAIL_NOTCH_DEPTH = 1.0;   // mm into the top wall (Q 54 -> 55), 1.0mm of wall left
PIGTAIL_NOTCH_Z0 = 6.0;      // face-frame Z: PCB slab is Z 7.5..9.1, +/- 1.5mm
PIGTAIL_NOTCH_Z1 = 10.6;
// ===== END inlined common.scad =====

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
// TWO pads per fin, front and rear (four feet; user decision 2026-11-17).
// The brief said "a foot pad per fin"; one pad per fin is two contact points
// in total, i.e. a line, and the body tips over it front-to-back
// (statically unstable at any lean). The minimum stable stance on two fins
// is a pad at each end of each fin's bottom edge, giving a FOOT_DIA-wide
// rectangle of contact under the four feet.
//
// Form (user review 2026-11-17: the pads must come out of the fins, not off
// the bottom plate, and read as the fins' own ends, not bolted on):
//   - Each fin is the convex hull of thin horizontal discs (Ø FIN_T) on its
//     side-view outline, so it is FIN_T thick with a FLAT bottom (it prints
//     on it) and half-round ends / rounded hypotenuse edge.
//   - Its bottom edge runs from the rear foot's centre forward to the front
//     foot's centre. Both ends are upright half-rounds of radius FIN_T/2
//     centred on the foot axes.
//   - The foot pads grow out of the fin's bottom edge as one form (user
//     review 2026-11-17: the disc-and-neck pads read as stuck-on knobs). The
//     section is an ogee -- short upright side, convex round, concave fillet
//     tangent into the fin face -- with no flat disc lip; FOOT_STYLE picks the
//     plan shape (round boss / flare along the fin / full-length runner), see
//     foot_form() below.
//   - Rear: the fin rises from the pad as a short upright heel (HEEL_H, the
//     pad height), then rolls over an arc of radius FIN_TIP_R into
//     the hypotenuse (no acute tip, no step at the pad's edge).
//   - Front (user decision 2026-11-17, LEAN 25): the front pads sit wholly
//     behind the body's rear-bottom edge, under the fins, their discs' front
//     edges flush with that edge (FRONT_FOOT_OFFSET 0). At LEAN 25 the CoG is
//     ~2.7mm behind the edge, so the rubber feet's front edges (Z -1.4) are
//     ~1.4mm ahead of it (~3.1mm counting the fins' own mass): a thin forward
//     tip-over margin the user accepted. At LEAN <= ~22 the same pads tip
//     forward and the assert below stops the render; FRONT_FOOT_OFFSET > 0
//     then pushes them forward, the fin's toe running on under the bottom
//     wall (embedded in it) to the front foot's centre.
//   - The fin's front edge runs SOLID from the front pad's neck up into the
//     body (user review 2026-11-17: no notch between the neck, the fin and
//     the back plate). Two extra hull vertices do it: one on the fin bottom
//     whose disc's front edge reaches the rear-bottom edge (Z 0), and one at
//     the embedded corner of the two walls, so the hull fills the wedge
//     between the vertical neck and the back plate leaning away above it.
//   - Fin edges against the walls are embedded FIN_EMBED, deep enough that
//     their rounding stays inside the wall (the part outside is full FIN_T);
//     whatever the hull puts inside the cavity is clipped away.

FIN_EMBED   = (FIN_T/2) / cos(LEAN_DEG) + 0.05;  // ~1.6: the disc rounding's reach along the wall normal, + 0.05
FOOT_RECESS_D = FOOT_DIA + FOOT_RECESS_CLEARANCE;          // centring recess diameter
FOOT_PAD_D  = FOOT_RECESS_D + 2*FOOT_PAD_RIM;              // pad disc diameter
FOOT_PAD_E  = (FOOT_PAD_D - FIN_T) / 2;                    // pad overhang beyond each fin face
FOOT_FILLET_R = FOOT_PAD_E - FOOT_PAD_ROUND;               // concave fillet radius, convex round -> fin face
HEEL_H      = FOOT_PAD_T + FOOT_PAD_E;                     // pad height where its fillet meets the fin
FRONT_FOOT_Z = FRONT_FOOT_OFFSET - FOOT_PAD_D/2;           // front foot centre, world Z (datum = rear-bottom edge; 0 offset = pad flush behind it)
REAR_FOOT_Z  = -FIN_REACH;                                 // rear foot centre, world Z
FIN_BOTTOM_Y = -FLOAT_GAP;                                 // fin bottom / pad underside, world Y
FIN_X = [FACE_W/2 - FIN_OFFSET_X, FACE_W/2 + FIN_OFFSET_X]; // fin mid-planes, world X

// local (Qface, bz) -> world (Y, Z): the rotate([-LEAN_DEG,0,0]) above.
function w_y(q, bz) = q*cos(LEAN_DEG) + bz*sin(LEAN_DEG);
function w_z(q, bz) = -q*sin(LEAN_DEG) + bz*cos(LEAN_DEG);

FIN_TOP_Y = w_y(FIN_TOP_Q, FIN_EMBED);   // top corner (hull vertex, inside the back wall)
FIN_TOP_Z = w_z(FIN_TOP_Q, FIN_EMBED);
BODY_TOP_Y = w_y(FACE_H, 0);             // back-top edge: lowest point of the top of the silhouette

// Toe top: where the vertical front end (at the front foot's axis) meets the
// embed line in the bottom wall -- or in the back wall, for a front foot
// behind the corner (small/negative FRONT_FOOT_OFFSET).
FIN_CORNER_Z = w_z(FIN_EMBED, FIN_EMBED);
FIN_CORNER_Y = w_y(FIN_EMBED, FIN_EMBED);
FIN_TOE_TOP = FRONT_FOOT_Z >= FIN_CORNER_Z
    ? [FRONT_FOOT_Z, w_y(FIN_EMBED, (FRONT_FOOT_Z + FIN_EMBED*sin(LEAN_DEG)) / cos(LEAN_DEG))]
    : [FRONT_FOOT_Z, w_y((FIN_EMBED*cos(LEAN_DEG) - FRONT_FOOT_Z) / sin(LEAN_DEG), FIN_EMBED)];

// Rear tip: arc centre, then the tangent from the top corner onto the arc.
HEEL_C = [REAR_FOOT_Z + FIN_TIP_R, FIN_BOTTOM_Y + HEEL_H];   // [Z, Y]
HEEL_D = [FIN_TOP_Z, FIN_TOP_Y] - HEEL_C;
HEEL_TANGENT_A = atan2(HEEL_D[1], HEEL_D[0]) + acos(FIN_TIP_R / norm(HEEL_D));  // arc runs 180 -> this
HEEL_ARC_N = 12;

// thinnest pad over the recess: at the recess edge, on the convex round (or the upright side if the round is outside the recess)
FOOT_PAD_OVER_RECESS = FOOT_PAD_T + (FOOT_RECESS_D/2 > FOOT_PAD_D/2 - FOOT_PAD_ROUND
    ? sqrt(pow(FOOT_PAD_ROUND, 2) - pow(FOOT_RECESS_D/2 - (FOOT_PAD_D/2 - FOOT_PAD_ROUND), 2))
    : FOOT_PAD_ROUND) - FOOT_RECESS_DEPTH;
assert(FOOT_PAD_OVER_RECESS >= 0.8, "foot pad too thin over its centring recess");
assert(FOOT_FILLET_R > 0, "FOOT_PAD_ROUND leaves no room for the fillet into the fin");
assert(FOOT_STYLE != "flare" || REAR_FOOT_Z + 2*FOOT_FLARE_LEN < FRONT_FOOT_Z, "flares from the two feet overlap");
assert(FOOT_PAD_D > FIN_T, "foot pad narrower than the fin");
assert(FIN_TOP_Q <= FACE_H - WALL_T, "fin top corner above the top wall");
assert(FIN_TOP_Y < BODY_TOP_Y, "fin top would show above the body in the front view");
assert(FIN_OFFSET_X + FOOT_PAD_D/2 <= FACE_W/2 - CORNER_R, "fin/pad would show beside the body in the front view");
assert(norm(HEEL_D) > FIN_TIP_R && HEEL_TANGENT_A < 180 && HEEL_C[0] < FIN_TOP_Z,
       "fin reach too short for its height / FIN_TIP_R too large: no rounded triangle");
assert(REAR_FOOT_Z + FOOT_PAD_D/2 < FRONT_FOOT_Z - FOOT_PAD_D/2, "front and rear pads overlap");

// Side-view hull vertices as [Z, Y].
function fin_vertices() = concat(
    [[FIN_TOP_Z, FIN_TOP_Y],              // top corner, inside the back wall
     FIN_TOE_TOP,                         // toe top, inside the bottom wall above the front foot
     [FIN_CORNER_Z, FIN_CORNER_Y],        // the walls' embedded corner: fills up to the back plate
     [FRONT_FOOT_Z, FIN_BOTTOM_Y],        // toe bottom, on the front foot's axis
     [-FIN_T/2,     FIN_BOTTOM_Y],        // bottom, disc front edge at the rear-bottom edge (Z 0)
     [REAR_FOOT_Z,  FIN_BOTTOM_Y]],       // heel bottom, on the rear foot's axis
    [ for (i = [0 : HEEL_ARC_N]) let(a = 180 - i * (180 - HEEL_TANGENT_A) / HEEL_ARC_N)
        HEEL_C + FIN_TIP_R * [cos(a), sin(a)] ]   // heel top, rolling over into the hypotenuse
);

// A thin horizontal disc (Ø FIN_T) at world (x, y, z). Discs on the fin
// bottom sit on it (y up); the rest are centred.
module fin_disc(x, z, y) {
    translate([x, y, z]) rotate([-90, 0, 0])
        cylinder(h = 0.01, d = FIN_T, center = (y > FIN_BOTTOM_Y + 0.001), $fn = 48);  // $fn = the pad neck's, so the facets line up
}

module fin_plate(x) {
    hull() for (p = fin_vertices()) fin_disc(x, p[0], p[1]);
}

// ---------------------------------------------------------------------
// Foot pads (pilink-s98 foot-form exploration)
// ---------------------------------------------------------------------
// One section language for every style: a short upright outer side
// (FOOT_PAD_T), a convex round (FOOT_PAD_ROUND) and a concave fillet that runs
// tangent into the fin's face -- an ogee, no flat disc lip. Each pad is one
// polyhedron of stacked horizontal rings; ring k is the convex outline (hull)
// of a few circles on the fin's line, grown by the section's overhang at that
// height, so the pad's plan shape sets the style:
//   boss   -- one circle on the foot axis: a round bun.
//   flare  -- the foot circle plus a FIN_T circle FOOT_FLARE_LEN along the fin,
//             that distance shrinking with the overhang: the fin's bottom edge
//             widens into the pad, its ridge on the fin face the same ogee
//             stretched lengthwise.
//   runner -- the two foot circles: a pad-wide rail along the whole bottom.
// Every ring is inside the one below (the overhang only shrinks going up), so
// it prints upright on the fin bottoms without support. The top ring sits
// FOOT_HIDE inside the fin faces and so is buried in the fin plate.
FOOT_HIDE = 0.05;
FOOT_RING_N = 48;   // = the fin discs' $fn
// Section samples [overhang beyond the fin face, height above the fin bottom].
function foot_section() = concat(
    [[FOOT_PAD_E, 0], [FOOT_PAD_E, FOOT_PAD_T]],
    [ for (i = [1 : 8]) let(t = i * 90 / 8)
        [FOOT_PAD_E - FOOT_PAD_ROUND * (1 - cos(t)), FOOT_PAD_T + FOOT_PAD_ROUND * sin(t)] ],
    [ for (i = [1 : 10]) let(t = i * 90 / 10)
        [FOOT_FILLET_R * (1 - sin(t)) - FOOT_HIDE * i / 10, HEEL_H - FOOT_FILLET_R * cos(t)] ]
);
// (the fillet's last few hundredths lean into the fin, so the pad's top ring
// never shares an edge with the fin's own Ø FIN_T end discs)

// Support point of hull(circles [[z, r], ...]) on the line x, direction a (in X-Z).
function hull_pt(x, circles, a) =
    let(s = [ for (c = circles) c[0] * sin(a) + c[1] ], m = max(s),
        c = circles[search(m, s)[0]])
    [x + c[1] * cos(a), c[0] + c[1] * sin(a)];

// Plan circles of one ring, for overhang e (beyond the fin face) at foot z.
// dir = which way along the fin is "inward" (+1 = forward, for the rear foot).
// The front pad's rings slide forward as they shrink, keeping its front edge
// upright at the pad's front (FRONT_FOOT_Z + FOOT_PAD_D/2): above the fin
// bottom that edge is inside the body's rear-bottom corner, so the pad runs
// up into the corner instead of ending in a rim and a neck in front of it.
function foot_c(z, e) = z == FRONT_FOOT_Z ? z + FOOT_PAD_E - max(e, 0) : z;
function foot_circles(z, dir, e) =
    let(r = FIN_T/2 + e)
    FOOT_STYLE == "runner" ? [[REAR_FOOT_Z, r], [foot_c(FRONT_FOOT_Z, e), r]]
  : FOOT_STYLE == "flare"  ? [[foot_c(z, e), r], [z + dir * FOOT_FLARE_LEN * max(e, 0) / FOOT_PAD_E, FIN_T/2 - FOOT_HIDE]]
  :                          [[foot_c(z, e), r]];

module foot_form(x, z, dir) {
    sec = foot_section();
    K = len(sec);
    N = FOOT_RING_N;
    pts = [ for (k = [0 : K - 1]) for (j = [0 : N - 1])
        let(p = hull_pt(x, foot_circles(z, dir, sec[k][0]), (j + 0.5) * 360 / N))  // half a step off the fin discs' vertices
        [p[0], FIN_BOTTOM_Y + sec[k][1], p[1]] ];
    faces = concat(
        [[ for (j = [N - 1 : -1 : 0]) j ]],                              // bottom
        [[ for (j = [0 : N - 1]) (K - 1) * N + j ]],                     // top
        // sides as triangles: the quads between rings are not planar
        [ for (k = [0 : K - 2]) for (j = [0 : N - 1]) for (t = [0, 1])
            t == 0 ? [k*N + j, k*N + (j + 1) % N, (k + 1)*N + (j + 1) % N]
                   : [k*N + j, (k + 1)*N + (j + 1) % N, (k + 1)*N + j] ]
    );
    polyhedron(points = pts, faces = faces, convexity = 4);
}

module foot_pads(x) {
    if (FOOT_STYLE == "runner") foot_form(x, FRONT_FOOT_Z, 1);
    else {
        foot_form(x, FRONT_FOOT_Z, -1);
        foot_form(x, REAR_FOOT_Z, 1);
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
// plane. A front pad pushed far forward (FRONT_FOOT_OFFSET >~ 11 at LEAN 15)
// puts its fillet under the front shell; this keeps a gap between the pad and
// the front shell instead of a near-touch or an edge contact at the joint.
// Only fin/pad material is removed: the shell itself is unioned separately.
FRONT_SHELL_CLEARANCE = 0.4;
module front_shell_zone() {
    translate([-1, -FRONT_SHELL_CLEARANCE, BACK_SHELL_DEPTH - FRONT_SHELL_CLEARANCE])
        cube([FACE_W + 2, FACE_H + FRONT_SHELL_CLEARANCE + 1, BODY_T]);
}

// Fins + pads, clipped so nothing reaches into the cavity, the USB-C
// opening, an insert pocket or the front shell, whatever the parameters
// (the hull fills between the embed lines inside the walls, and the front
// pad's neck rises into the bottom wall).
module fins() {
    difference() {
        union() {
            for (x = FIN_X) {
                fin_plate(x);
                foot_pads(x);
            }
        }
        rotate([-LEAN_DEG, 0, 0]) {
            back_shell_cavity();
            usbc_cutout();
            pcb_mount_insert_pockets();
            front_shell_zone();
        }
    }
}

// The printed part: shell + fins. The foot recesses are cut from the shell
// too: at the defaults the front recess (Z -8.1..-1.2) is wholly behind the
// rear-bottom edge and misses it, but with FRONT_FOOT_OFFSET > ~1.2 at
// FLOAT_GAP 0 it runs under the body's corner and takes up to
// FOOT_RECESS_DEPTH (0.6mm) off the 2mm bottom wall, as the old feet pockets
// did (pilink-9i4).
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
// "tip-over"). Body ~81 g, fins ~9.3 g at the defaults (FIN_REACH 45, LEAN 25). Leaving the
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
