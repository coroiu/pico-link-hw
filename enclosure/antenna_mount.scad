// Internal mount for the adhesive U.FL 2.4GHz antenna (pilink-8hx.4).
//
// NOT RENDERED/FIT-CHECKED. OpenSCAD is not installed in the environment
// this file was authored (and later fixed) in (see README.md and
// AGENTS.md "This repo has no build/test automation") -- every dimension
// below is transcribed from a cited source or marked as this file's own
// assumption. A human with OpenSCAD (or a later pass with it installed)
// still needs to actually render this and check it against the real
// back-shell geometry from pilink-8hx.1, once that lands.
//
// Scope: this file models only the antenna mount feature itself (a flat
// adhesive-land + retention lip + cable strain relief + a reference cable
// channel), not a full top-wall shell. pilink-8hx.1 (back shell) and
// pilink-8hx.2 (front shell) are being built in parallel on separate
// branches and own the real top-wall geometry; antenna_mount() is meant to
// be instantiated (translated/rotated onto the real wall) from whichever of
// those ends up owning the top wall's inner surface. demo_assembly() below
// is a self-contained preview only -- its "stand-in top wall" slab is NOT
// the real enclosure wall and must not be unioned into either shell.
//
// Revision history: a code-reviewer's NOT APPROVED verdict on PR #48
// (2bdfd6a) found the first version's left-wall-hugging position put the
// antenna element physically inside the SW101 top-edge pinhole's channel
// (a real 3D collision, not just a flagged cross-bead conflict), never
// checked the display-panel/ground-plane clearance it claimed to derive,
// and had three geometry bugs (lip closed on the wrong side, the cable
// channel modeled as a solid bar instead of an actual cutout, and the
// strain-relief clip coming out U-shaped instead of C-shaped). That
// revision (9eac09f) re-derived the position (see "Mount position" below)
// and fixed those three bugs, but a second NOT APPROVED round found: the
// display/ground clearance discussion was framed on the wrong axis (a
// non-existent "Z gap" instead of the real face-Y distance) and wrongly
// called "not derivable" when it is derivable and fails the guidance; the
// land/lip/channel/clip stack was modeled ~19mm deep against a ~10mm
// available wall cavity; the strain-relief clip's bore ran wall-normal
// instead of along the cable's actual path; the cable-channel-width
// comment claimed margin for the IPEX plug body that doesn't mate here at
// all (it mates at U201, far from this stub); and a stated clearance
// figure had an arithmetic slip (39mm instead of 38.25mm). This revision
// fixes all of those -- see the comments at each fix below and
// `.planning` bead `pilink-58z` for the RF-clearance trade-off this file
// now surfaces instead of hiding.
//
// Re-check (pilink-adt, 2026-11-16, discovered-from pilink-2yw): this
// file's U201/cable-run numbers below were derived against U201's OLD
// board-local anchor (14, 12.5), upper-left near the encoder. pilink-2yw
// (merged PR #53) relocated U201 to (99, 11.6), a pocket above the A/B/X/Y
// diamond, and shifted the diamond itself down 9mm (centre (102,25) ->
// (102,34)). Re-checked against hardware/README.md's current placement
// table, not re-derived from scratch -- see U201_ANTENNA_X_* /
// U201_ANTENNA_Y_* below (now sourced from the new anchor) and the two new
// comment blocks this round adds: one confirming the diamond's new
// position does not create a mount collision, one confirming pilink-58z's
// RF-clearance numbers are untouched by this move. This mount's own X
// position (face-local 57.75-105.55) and Y/depth stack-up are NOT
// repositioned or re-derived here -- out of this bead's scope, and no
// geometry finding below calls for it.
//
// A third NOT APPROVED round (47e528d) found the strain-relief clip, as
// built after round 2, couldn't actually hold the cable: its snap-in slot
// (1.43mm) was wider than the 1.13mm coax it was meant to grip; its wall
// thickness was silently tied to LIP_WIDTH and had been thinned to 0.5mm
// along with it; it floated 0.7mm off the wall surface with no real
// support; and its slot opened sideways (-X) while the channel's own
// groove opens upward (+Z), a kink in the cable's path. This revision
// gives the slot its own under-the-coax width, gives the clip its own
// independent wall-thickness constant, adds support legs down to the
// wall surface, and reorients the slot to open the same way as the
// groove -- see strain_relief_clip() and the legs added just after its
// call site below. That round also found this file's own README wording
// overstated the ~46mm clearance figure's source as "the antenna
// datasheet's own guidance" -- fixed in README.md to match what this
// file already said (general adhesive-FPC-antenna practice, not a
// datasheet figure).

// ---------------------------------------------------------------------------
// Antenna part -- Kinghelm KH-FPC2.4G-1.13IPEX-240, LCSC C4943394. Selected
// (over the AIWF026 alternate) in
// .research/findings/2026-11-15-ufl-antenna-selection.md and closed out in
// bd pilink-8wx ("primary Kinghelm KH-FPC2.4G-1.13IPEX-240, alternate
// MyAntenna AIWF026 flagged as fractionally over cert-safe gain ceiling").
// ---------------------------------------------------------------------------

// Element footprint, confirmed directly on LCSC's C4943394 product page
// (packaging field "SMD, 45.8x6.5mm") per the research finding.
ANTENNA_ELEMENT_LENGTH = 45.8;   // mm, long axis
ANTENNA_ELEMENT_WIDTH  = 6.5;    // mm

// Element thickness is NOT given anywhere in the finding or on the LCSC
// listing -- this is this file's own nominal placeholder for a thin
// adhesive-backed FPC, used only so the 3D preview has a visible element;
// it is not a verified dimension and should not drive any clearance math.
ANTENNA_ELEMENT_THICKNESS_NOMINAL = 0.3; // mm, UNVERIFIED placeholder

// Pigtail: Ø1.13mm coax, IPEX/U.FL-class plug. The "-240" part-number
// suffix implies a 240mm cable but the finding is explicit this is
// INFERRED from the part number, not a confirmed datasheet/listing field
// -- confirm before ordering. Not used for any geometry below beyond the
// cable-channel's nominal width.
ANTENNA_CABLE_DIAMETER = 1.13; // mm

// Clearance guidance (.research/findings/2026-11-15-ufl-antenna-selection.md,
// "Clearance / ground-plane guidance"): the 32UE's own datasheet carries no
// keepout for an external antenna (that keepout only applied to the
// on-module antenna variant). The finding instead cites general adhesive-FPC
// practice: "keep the flexible element itself clear of metal/ground
// plane/battery within roughly its own element length on the radiating
// side". Modeled here as a single symmetric reference zone equal to the
// element's own length -- a simplification of what the source guidance
// describes as one-sided/radiating-direction-specific, since neither the
// finding nor any datasheet in this repo states which end of this specific
// part radiates. Shown with `%` (OpenSCAD non-manifold preview modifier) so
// it never affects a boolean/union result -- it is a visual "keep metal
// clear of this" marker for a human reviewing the render, not a solid.
ANTENNA_KEEPOUT_FROM_METAL = ANTENNA_ELEMENT_LENGTH; // mm, see note above

// ---------------------------------------------------------------------------
// Board / face coordinate assumptions.
//
// hardware/README.md "PCB layout (pilink-7el.12, upright desk-clock form
// factor)" gives the real 118 x 50mm board's placement table in board-local
// mm (origin top-left, x right, y down). That same section already flags,
// in its own words, that mapping board-local coordinates onto the ~122 x
// 56mm face is NOT yet settled -- "that assumption was never checked against
// the actual back-shell boss/standoff design (which doesn't exist yet)...
// Flagged for pilink-8hx.1/.2 to confirm". This file inherits that same
// unconfirmed convention rather than inventing a different one, so all
// three enclosure beads stay comparable:
//   - board centered left-right in the face: offset = (FACE_W-BOARD_W)/2
//   - board bottom edge flush with the face's bottom edge: offset =
//     FACE_H-BOARD_H, all of the difference taken up above the board's own
//     top edge (hardware/README.md's own "y = 50 - N" rule)
// X is the one axis that matters for this file: left-right position is
// unaffected by the body's 15-degree lean, so board-local X and face-local
// X are directly comparable to pilink-8hx.2's SW101/SW102 pinhole X values
// via this same offset.
// ---------------------------------------------------------------------------

BOARD_W = 118.0; // mm, hardware/README.md
BOARD_H = 50.0;  // mm, hardware/README.md
FACE_W  = 122.0; // mm, .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md ("Face about 122 W x 56 H mm")
FACE_H  = 56.0;  // mm, same ADR

BOARD_TO_FACE_X_OFFSET = (FACE_W - BOARD_W) / 2; // = 2.0mm, ASSUMPTION, see note above
BOARD_TO_FACE_Y_OFFSET = FACE_H - BOARD_H;       // = 6.0mm, ASSUMPTION, see note above

// U201 (ESP32-WROOM-32UE) antenna-connector-end edge, board-local.
//
// *** RE-CHECK for pilink-adt (2026-11-16) ***
// This used to read U201's OLD anchor (14, 12.5) via
// .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md's
// "that module edge sits at board-local Y ~= 2.65-2.9, X ~= 5-23 (centered
// X=14)" -- note the old anchor X (14) equals that old connector-center X
// (14) exactly, and the old connector Y range (2.65-2.9) sits 9.6-9.85mm
// in -Y from the old anchor Y (12.5): 12.5-9.85=2.65, 12.5-9.6=2.9. That is
// this footprint's own fixed geometry (anchor-to-antenna-edge offset),
// unrelated to board position, so it carries over unchanged to the new
// placement.
//
// pilink-2yw (merged PR #53) relocated U201 to anchor (99, 11.6), rot 0
// (hardware/README.md's placement table, "ESP32 (U201) relocated..." row)
// -- same rotation, so the same fixed X=0 / Y=-9.6..-9.85 offset applies:
//   X center = 99 + 0           = 99.0  (board-local)
//   Y range  = 11.6 - 9.85..9.6 = 1.75-2.0 (board-local)
// This is this file's own re-derivation from the footprint's fixed anchor
// offset, not a newly-confirmed datasheet/drawing figure -- same caveat as
// the old numbers it replaces. (hardware/README.md's own placement-table
// note separately estimates U201's courtyard edge at "~1.1-1.75mm from the
// top edge", a different reference point on the part than the connector
// pad itself, but the same order of magnitude -- consistent, not
// contradictory.) The connector's exact position along that edge still
// isn't confirmed from a rendered datasheet drawing.
U201_ANTENNA_X_MIN = 90.0;
U201_ANTENNA_X_MAX = 108.0;
U201_ANTENNA_X_CENTER = 99.0;
U201_ANTENNA_Y_MIN = 1.75;
U201_ANTENNA_Y_MAX = 2.0;

// Face-local X center of U201's U.FL connector, used below to check the
// resulting cable run length.
U201_ANTENNA_FACE_X_CENTER = U201_ANTENNA_X_CENTER + BOARD_TO_FACE_X_OFFSET; // 101.0mm (was 16.0mm against U201's old anchor -- see RE-CHECK comment above)

// SW101/SW102 (BOOTSEL/RESET) top-edge pinhole X positions, board-local,
// from hardware/README.md's placement table: "SW101 (42, 2.7), SW102
// (52, 2.7) -- in the 5mm strip above the panel". This is pilink-8hx.2's
// own geometry (front shell, top-edge pinhole channels) -- NOT duplicated
// here, only read for the position/collision check below.
SW101_X_BOARD_LOCAL = 42.0;
SW102_X_BOARD_LOCAL = 52.0;
SW101_X_FACE_LOCAL = SW101_X_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 44.0mm
SW102_X_FACE_LOCAL = SW102_X_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 54.0mm

// Pinhole diameter, from the ADR's own wording: "pressed straight down
// through about a 1.5 mm pinhole". Same channel is shared by both
// SW101/SW102 per that same ADR passage.
PINHOLE_DIAMETER = 1.5; // mm, ADR (upright-desk-clock-form-factor.md)

// Display-panel shadow, board-local, from hardware/README.md:971 ("Treated
// as x:[28,87] y:[5,47] on the board"). Converted to face-local X using the
// same offset as everything else in this file. Only the X range is used
// below (see "Display-panel / ground-plane clearance check" note further
// down for why Y/Z aren't checked here).
PANEL_X_MIN_BOARD_LOCAL = 28.0; // mm, hardware/README.md:971
PANEL_X_MAX_BOARD_LOCAL = 87.0; // mm, hardware/README.md:971
PANEL_X_MIN_FACE_LOCAL = PANEL_X_MIN_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 30.0mm
PANEL_X_MAX_FACE_LOCAL = PANEL_X_MAX_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 89.0mm

// ---------------------------------------------------------------------------
// This file's own choices (not sourced from any ADR/finding -- stated so a
// reviewer knows exactly which numbers are mine to argue with).
// ---------------------------------------------------------------------------

ASSEMBLY_CLEARANCE = 1.0;     // mm, margin added around the element footprint so an installer can place the adhesive antenna by eye, not a datasheet figure
WALL_THICKNESS = 2.0;         // mm, nominal FDM shell wall -- pilink-8hx.1 may land on a different value; parameterized so it's a one-line change here
PINHOLE_X_CLEARANCE = 3.0;    // mm, this file's own minimum-margin choice from a pinhole's edge to the mount's land edge (same figure the first version used for the left-wall margin, kept consistent rather than tuned differently just because the position moved)
// *** FIX for PR #48 review item (mount depth vs. available wall depth) ***
// LIP_WIDTH is reduced from 0.8 to 0.5mm here as part of that fix -- see
// the "Mount depth" note below the land-footprint constants for the full
// depth accounting.
LIP_WIDTH = 0.5;              // mm, width of the raised locating lip around the land
LIP_HEIGHT = 0.4;             // mm, height of the raised locating lip
// *** FIX for PR #48 review item (groove width vs. IPEX plug body) ***
// This channel/groove only carries the bare Ø1.13mm coax between the
// antenna land and the cavity -- the IPEX/U.FL-class male plug is on the
// OTHER end of the pigtail, where it mates at U201 (see
// `strain_relief_clip()`'s own comment and the finding), nowhere near this
// stub. So "margin for the plug body" was simply wrong; corrected below.
CABLE_CHANNEL_WIDTH = 2.0;    // mm, clear of ANTENNA_CABLE_DIAMETER (1.13mm) with margin for the bare coax only (no plug passes through this stub)
CABLE_CHANNEL_DEPTH = 1.5;    // mm, depth of the groove cut into the channel boss (see channel() below)
CHANNEL_BOSS_MARGIN = 1.0;    // mm, solid shoulder left on each side of the groove so there is material to actually cut the groove into
CABLE_CHANNEL_EXIT_X_INSET = 6.0; // mm, UNSOURCED ASSUMPTION: neither the research finding nor the LCSC listing says where this part's actual pigtail leaves the element (flagged in both places). This file picks an exit point inset from the land's edge nearest U201 (see "Mount position" below for why that edge is nearest), on the assumption that the shortest practical cable run to U201's U.FL connector is the right default absent a real drawing -- not a confirmed exit point on the physical part.
STRAIN_RELIEF_CLIP_ID = 1.6;  // mm, snug over the 1.13mm coax
// Reduced from 2.0 to 1.0mm as part of the mount-depth fix below -- still
// enough ring thickness along the cable's own axis (after the bore-
// orientation fix, see strain_relief_clip() below) for a printed C-clip to
// grip a cable this thin (Ø1.13mm), just not generously so.
STRAIN_RELIEF_CLIP_HEIGHT = 1.0; // mm
// *** FIX for PR #48 review round 3 (blocking, "clip can't actually hold
// the cable") ***
// This was ANTENNA_CABLE_DIAMETER + 0.3 = 1.43mm -- WIDER than the 1.13mm
// coax, so the cable dropped straight through with no snap at all
// (contradicts the "press through / snap over and hold" comments below).
// A snap-fit slot has to be narrower than the thing it grips so the
// printed plastic has to flex open to let the cable in and spring back
// after; sized here a little under the coax diameter rather than a little
// over it.
STRAIN_RELIEF_CLIP_SLOT_WIDTH = 0.95; // mm, narrow snap-in slot, deliberately UNDER the 1.13mm coax diameter so the ring has to flex open to admit the cable and then grip it, not the full half-ring opening the first version cut (which left a U, not a C -- see PR review item 8)
// *** FIX for PR #48 review round 3 (blocking, "wall thickness silently
// cut via LIP_WIDTH coupling") ***
// The clip ring's own wall used to be computed as `clip_id + 2*lip_width`,
// so cutting LIP_WIDTH (mount lip, a completely different part of the
// model) from 0.8 to 0.5mm in the previous round silently thinned the
// clip's wall too, down to 0.5mm -- about one 0.4mm-nozzle extrusion
// width. Given its own constant here instead, independent of LIP_WIDTH.
STRAIN_RELIEF_CLIP_WALL = 0.8; // mm, clip ring's own radial wall thickness -- independent of LIP_WIDTH (different part of the model), kept at a minimum of 0.8mm so it actually has grip strength when printed

// Land (adhesive mounting area) footprint, element + clearance on all sides.
MOUNT_LAND_LENGTH = ANTENNA_ELEMENT_LENGTH + 2 * ASSEMBLY_CLEARANCE; // 47.8mm
MOUNT_LAND_WIDTH  = ANTENNA_ELEMENT_WIDTH + 2 * ASSEMBLY_CLEARANCE;  // 8.5mm

// *** FIX for PR #48 review item (mount depth vs. available wall depth,
// blocking) ***
// The review measured this mount's own Y-footprint (land + lip on the
// closed +Y edge, plus the channel stub + clip on the open -Y/cable-exit
// edge) at about 19mm, against a top-wall inner cavity depth of only about
// 10mm (ADR: body ~14mm thick, minus ~2mm front/back walls each). That
// axis (this file's local Y) maps to the body's front-to-back depth, not
// to the wall's own thickness, so it is a real fit problem independent of
// the RF-clearance question above, and it doesn't resolve itself just by
// repositioning the mount in X.
//
// With LIP_WIDTH and STRAIN_RELIEF_CLIP_HEIGHT reduced above and a much
// shorter default channel_length (see antenna_mount()'s signature below,
// 1.0mm instead of 8.0mm -- it was always documented as a placeholder
// stub, "real length depends on pilink-8hx.1's cavity geometry", not a
// committed dimension):
//   land + lip (+Y, closed edge):      MOUNT_LAND_WIDTH + LIP_WIDTH = 8.5 + 0.5 = 9.0mm
//   channel stub (-Y, open edge):      1.0mm (new default, was 8.0mm)
//   strain-relief clip (-Y, beyond the channel): STRAIN_RELIEF_CLIP_HEIGHT = 1.0mm (new default, was 2.0mm)
//   total Y-span:                      9.0 + 1.0 + 1.0 = 11.0mm
// That is down from ~19mm to ~11mm, but still about 1mm (~10%) OVER the
// ~10mm estimated wall-cavity budget -- NOT fully resolved. The land+lip
// side alone (9.0mm) already consumes nearly the whole budget.
// *** FIX for PR #48 review round 3 (non-blocking nit): the previous
// wording here claimed the land's width was "not by a tunable default",
// which overstated things -- only the physical element (6.5mm) and
// LIP_WIDTH are fixed; ASSEMBLY_CLEARANCE (1.0mm per side here) IS this
// file's own tunable choice. Tightening it to 0.5mm on this width axis
// alone (keeping it at 1.0mm on the length axis, where it isn't the
// binding constraint) would land the stack at exactly the 10.0mm budget.
// Not taken in this round: that's a third independent margin to cut in
// the same PR (after LIP_WIDTH and the clip height/wall), and stacking
// more cuts on top of each other without pilink-8hx.1/.2's real cavity
// geometry to check the result against risks over-correcting. So there
// IS a small amount of slack left on this axis -- just not spent here.
// Squeezing the channel stub and clip any further would start
// compromising their function (a clip ring thinner than ~1mm along the
// cable axis, or a wall thinner than ~0.8mm, is unlikely to grip a cable
// reliably when printed). Stated plainly rather than silently forced to
// fit: this mount's depth is very tight against the estimated 10mm cavity
// and may need pilink-8hx.1/pilink-8hx.2's actual 3D wall geometry to
// either confirm a bit more than 10mm is really available, or to route
// the strain-relief clip off this straight-line axis entirely (e.g.
// letting the cable turn a corner into the cavity below rather than
// continuing straight back) once that geometry exists to design against.

// ---------------------------------------------------------------------------
// Mount position in the top wall's own local X (= face-local X, left-right,
// unaffected by the lean -- see coordinate note above).
//
// *** FIX for PR #48 review item 1/2 (critical, blocking) ***
// The first version hugged the left inner wall (face-local X 3-50.8mm,
// covering element X 4-49.8mm) to keep the cable run to U201 short. That
// put the element squarely across SW101's pinhole at face-local X=44 --
// SW101_X_FACE_LOCAL above. The review's own measurements at the time (top
// wall inner depth ~10mm: body ~14mm thick minus front/back walls;
// land+lip depth 9.3mm with the lip width this file used then -- since
// reduced to 9.0mm as part of the separate mount-depth fix below;
// PTS645-class actuator sits a few mm in front of the PCB plane)
// show this is a real 3D collision -- the pinhole's paperclip travels
// through the same shallow top-wall cavity the antenna land sits in, not
// just an X-coordinate overlap on paper. That fails this bead's own
// acceptance criterion ("doesn't collide with the top-edge pinholes")
// outright, and the review was correct that resolving it is this bead's
// job, not pilink-8hx.2's: SW101/SW102's X positions are fixed by the
// already-merged, already-placed-and-routed PCB (pilink-7el.12), not a
// free variable for the front shell to retune. The antenna position is
// this bead's own free variable.
//
// Fix: move the mount clear of BOTH pinholes, to the right of SW102 (the
// rightward option -- staying left of SW101 only leaves face-local X
// 2-40.25mm = 38.25mm (inner wall at WALL_THICKNESS=2 to SW101's pinhole
// edge at SW101_X_FACE_LOCAL - PINHOLE_DIAMETER/2 - PINHOLE_X_CLEARANCE =
// 44 - 0.75 - 3 = 40.25), less than the 45.8mm element, so it doesn't fit;
// checked directly here, not assumed -- a review round corrected this
// from a slightly-off "3-42mm = 39mm" to the figure above; the conclusion
// (it doesn't fit) is unchanged either way). Minimum clearance from SW102's pinhole edge
// (SW102_X_FACE_LOCAL +/- half PINHOLE_DIAMETER) to the land is
// PINHOLE_X_CLEARANCE, same margin figure the old left-wall placement used:
//   MOUNT_X_MIN = 54.0 + 1.5/2 + 3.0 = 57.75mm
//   MOUNT_X_MAX = 57.75 + 47.8   = 105.55mm
// Right-side margin to the assumed inner wall (FACE_W - WALL_THICKNESS =
// 120mm) is then 120 - 105.55 = 14.45mm -- comfortably clear, no further
// tuning needed on that side.
//
// Cable-run consequence (not a blocker -- see PR review item 2 and the
// task that produced this fix): the new exit point (see
// CABLE_CHANNEL_EXIT_X_INSET above) sits at face-local X = 57.75 + 6.0 =
// 63.75mm.
//
// *** RE-CHECK for pilink-adt (2026-11-16) ***
// This used to read ~47.75mm in X alone to U201's OLD connector-center
// (face-local X=16.0mm, from U201's old board anchor (14,12.5)).
// pilink-2yw relocated U201 to board anchor (99,11.6) -- see
// U201_ANTENNA_X_CENTER's own re-derivation above -- which moves its
// face-local connector-center X to U201_ANTENNA_FACE_X_CENTER = 99 + 2.0
// = 101.0mm. The new X-only run is therefore:
//   |101.0 - 63.75| = 37.25mm
// i.e. now SHORTER (as expected -- U201 moved into the same right-hand
// half of the board the mount already occupies, rather than the old
// upper-left corner). The part's pigtail is still ~240mm (inferred from
// the part number, per the research finding), so a ~37mm run leaves well
// over 200mm of slack to coil inside the enclosure cavity during assembly
// -- not a real constraint here, same conclusion as before just with a
// smaller (and now correct) number. This is still an X-only approximation
// (no Y/Z component of the real 3D cable path is modeled), same
// simplification the file has used throughout.
PINHOLE_EDGE_CLEARANCE_X = SW102_X_FACE_LOCAL + PINHOLE_DIAMETER / 2 + PINHOLE_X_CLEARANCE;
MOUNT_X_MIN = PINHOLE_EDGE_CLEARANCE_X;                // 57.75mm
MOUNT_X_MAX = MOUNT_X_MIN + MOUNT_LAND_LENGTH;         // 105.55mm
MOUNT_X_CENTER = (MOUNT_X_MIN + MOUNT_X_MAX) / 2;

echo(str("[pilink-8hx.4] Mount X ", MOUNT_X_MIN, "-", MOUNT_X_MAX,
         "mm. SW101 pinhole X=", SW101_X_FACE_LOCAL, ", SW102 pinhole X=",
         SW102_X_FACE_LOCAL, " (+/-", PINHOLE_DIAMETER / 2,
         "mm radius each) -- both now clear of the mount by construction."));

CABLE_CHANNEL_EXIT_FACE_X = MOUNT_X_MIN + CABLE_CHANNEL_EXIT_X_INSET; // 63.75mm
CABLE_RUN_X_ONLY = abs(U201_ANTENNA_FACE_X_CENTER - CABLE_CHANNEL_EXIT_FACE_X);

echo(str("[pilink-adt re-check] Cable-run (X-only approximation): channel exit ",
         "face-X=", CABLE_CHANNEL_EXIT_FACE_X, "mm, U201 connector face-X=",
         U201_ANTENNA_FACE_X_CENTER, "mm -> ", CABLE_RUN_X_ONLY,
         "mm run, vs the part's ~240mm pigtail -- was ~47.75mm against U201's ",
         "old anchor (14,12.5); now shorter after pilink-2yw's U201 move to ",
         "(99,11.6)."));

// *** Diamond-relocation collision check (pilink-adt, 2026-11-16) ***
// pilink-2yw also shifted the A/B/X/Y diamond's whole group down 9mm
// (board-local centre (102,25) -> (102,34); real courtyard union
// x:[88.93,115.07] y:[13.58,36.43], per hardware/README.md's placement
// table). Checked here with real numbers, not assumed equivalent to the
// already-resolved SW101 pinhole case:
//
//   Diamond courtyard, face-local X: 88.93+2.0..115.07+2.0 = 90.93-117.07mm.
//   Mount, face-local X:             MOUNT_X_MIN..MOUNT_X_MAX = 57.75-105.55mm.
//   X-overlap: max(0, min(117.07,105.55) - max(90.93,57.75)) = 14.62mm.
//
// So yes, there IS X-overlap -- bigger than the panel's own 31.25mm would
// suggest is impossible to avoid, but smaller than that figure, and (same
// as the panel case below) this is NOT a repeat of the SW101 pinhole bug.
// The diamond's buttons protrude through the FRONT FACE PLATE at
// board-local Y 13.58-36.43 (face-Y ~19.6-42.4mm, mid-to-lower face), while
// this mount sits in the TOP WALL, whose whole face-Y band (above the
// panel) is only 0-11mm (PANEL_Y_MIN_FACE_LOCAL below) -- NOT to be
// confused with this module's own local Y axis (front-to-back cavity
// depth, see antenna_mount()'s own doc comment), a different axis
// entirely. So this is a different structural layer *and* at least ~8mm
// of face-Y separation even before accounting for the layer difference
// (19.6 - 11 = 8.6mm, using the top wall's full available band as the
// conservative/closest bound -- the element itself sits nearer face-Y~2mm,
// even further away), not the few-mm shared-channel overlap that made the
// SW101 case a real 3D collision. No redesign needed here; stated
// explicitly with numbers rather than left to "should be fine."
DIAMOND_X_MIN_BOARD_LOCAL = 88.93; // mm, hardware/README.md placement table (SW305-308 F.CrtYd union)
DIAMOND_X_MAX_BOARD_LOCAL = 115.07;
DIAMOND_Y_MIN_BOARD_LOCAL = 13.58;
DIAMOND_X_MIN_FACE_LOCAL = DIAMOND_X_MIN_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 90.93mm
DIAMOND_X_MAX_FACE_LOCAL = DIAMOND_X_MAX_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 117.07mm
DIAMOND_Y_MIN_FACE_LOCAL = DIAMOND_Y_MIN_BOARD_LOCAL + BOARD_TO_FACE_Y_OFFSET; // 19.58mm
DIAMOND_OVERLAP_X_MIN = max(MOUNT_X_MIN, DIAMOND_X_MIN_FACE_LOCAL);
DIAMOND_OVERLAP_X_MAX = min(MOUNT_X_MAX, DIAMOND_X_MAX_FACE_LOCAL);
DIAMOND_OVERLAP_X = DIAMOND_OVERLAP_X_MAX > DIAMOND_OVERLAP_X_MIN ? DIAMOND_OVERLAP_X_MAX - DIAMOND_OVERLAP_X_MIN : 0;

echo(str("[pilink-adt re-check] Diamond courtyard face-X ",
         DIAMOND_X_MIN_FACE_LOCAL, "-", DIAMOND_X_MAX_FACE_LOCAL,
         "mm vs mount face-X ", MOUNT_X_MIN, "-", MOUNT_X_MAX, "mm: ",
         DIAMOND_OVERLAP_X, "mm of X-overlap -- NOT a collision: diamond ",
         "buttons are front-face-plate, face-Y>=", DIAMOND_Y_MIN_FACE_LOCAL,
         "mm; this mount is top-wall, face-Y~0-11mm (see face-Y clearance ",
         "check below) -- different layer, >=8mm Y-separation besides."));

// *** Display-panel / ground-plane clearance check (PR #48 review item 3,
// blocking) ***
// The review correctly pointed out the first version drew the clearance
// keepout (ANTENNA_KEEPOUT_FROM_METAL / antenna_keepout_reference() below)
// as a marker and never actually compared it with anything. Doing that
// comparison honestly, with real numbers:
//
//   Display-panel shadow, face-local X: PANEL_X_MIN_FACE_LOCAL..PANEL_X_MAX_FACE_LOCAL = 30-89mm.
//   New mount, face-local X:            MOUNT_X_MIN..MOUNT_X_MAX           = 57.75-105.55mm.
//   X-overlap: max(0, min(89,105.55) - max(30,57.75)) = 31.25mm.
//
// That overlap is NOT avoidable by sliding the mount further: the panel
// shadow alone spans 59mm of the face's 122mm width, and the only clear
// span to its right (past face-local X=89, before the assumed right inner
// wall at X=120) is ~31mm -- less than the 45.8mm element, the same reason
// a left-of-SW101 placement didn't fit either. So within the fixed
// footprint this enclosure already committed to (panel width + a 45.8mm
// element + pinholes that can't move), there is no X position that clears
// the panel's shadow entirely. That is a real, checked conclusion, not an
// assumption -- the file now says so instead of implying it was resolved.
//
// What this does NOT mean is a second instance of the SW101 pinhole bug.
// The display panel and its frame live on the FACE (the tilted front
// panel, mounted a measured 7.5mm forward of the PCB plane per the ADR's
// knob-clearance derivation); the antenna mount lives in the TOP WALL (the
// highest point of the body, per this bead's own description), a
// different structural layer above it, not sharing a channel the way the
// top-wall pinholes do. The guidance this bead is actually weighing is the
// research finding's RF-performance keepout ("keep the flexible element
// clear of metal/ground plane ... within roughly its own element length"),
// not a literal collision risk.
PANEL_OVERLAP_X_MIN = max(MOUNT_X_MIN, PANEL_X_MIN_FACE_LOCAL);
PANEL_OVERLAP_X_MAX = min(MOUNT_X_MAX, PANEL_X_MAX_FACE_LOCAL);
PANEL_OVERLAP_X = PANEL_OVERLAP_X_MAX > PANEL_OVERLAP_X_MIN ? PANEL_OVERLAP_X_MAX - PANEL_OVERLAP_X_MIN : 0;

echo(str("[pilink-8hx.4] Display-panel shadow X ", PANEL_X_MIN_FACE_LOCAL, "-",
         PANEL_X_MAX_FACE_LOCAL, "mm vs mount X ", MOUNT_X_MIN, "-", MOUNT_X_MAX,
         "mm: ", PANEL_OVERLAP_X,
         "mm of X-overlap, unavoidable given the fixed panel/pinhole footprint."));

// *** FIX for PR #48 review round 2 (critical, blocking): the governing
// number here is NOT a Z (perpendicular-to-face) gap -- a prior revision
// of this file wrongly framed it that way and called it "not derivable
// until pilink-8hx.1/.2 land". Both parts were wrong. The antenna sits in
// the top wall, ABOVE the board's top edge and the display panel's top
// edge, in the FACE PLANE (face-Y, the same axis FACE_H/BOARD_H already
// use) -- not in front of or behind them in Z. And that face-Y distance
// *is* derivable to first order from constants already in this file, using
// the same unconfirmed board-to-face mapping the X-axis numbers above
// already rely on (so it carries the same caveat, not a new one).
//
// Display-panel shadow Y start, board-local, from hardware/README.md:971
// ("Treated as x:[28,87] y:[5,47] on the board") -- only the X range was
// captured above; this is its Y start, needed for the face-Y estimate.
PANEL_Y_MIN_BOARD_LOCAL = 5.0; // mm, hardware/README.md:971
PANEL_Y_MIN_FACE_LOCAL = PANEL_Y_MIN_BOARD_LOCAL + BOARD_TO_FACE_Y_OFFSET; // 11.0mm, ESTIMATE (unconfirmed mapping)

// The element itself sits on the top wall's INNER surface, i.e.
// WALL_THICKNESS below the face's own top edge (face-y=0) -- an estimate,
// not a confirmed figure, same caveat as everything else derived from the
// unconfirmed board-to-face mapping.
ANTENNA_ELEMENT_FACE_Y_ESTIMATE = WALL_THICKNESS; // ~2.0mm, ESTIMATE

// Board's own top edge (where SW101/SW102's copper and the board outline
// itself sit) is at face-y = BOARD_TO_FACE_Y_OFFSET = 6.0mm.
CLEARANCE_TO_BOARD_TOP_EDGE_ESTIMATE = BOARD_TO_FACE_Y_OFFSET - ANTENNA_ELEMENT_FACE_Y_ESTIMATE; // ~4.0mm
// Panel frame's top edge is at face-y = PANEL_Y_MIN_FACE_LOCAL = 11.0mm.
CLEARANCE_TO_PANEL_FRAME_ESTIMATE = PANEL_Y_MIN_FACE_LOCAL - ANTENNA_ELEMENT_FACE_Y_ESTIMATE; // ~9.0mm

// The guidance (ANTENNA_KEEPOUT_FROM_METAL, ~46mm -- roughly the element's
// own length) is measured against a face that is only FACE_H=56mm tall in
// total, with only ~11mm of that above the panel's own top edge. So this
// is not a marginal shortfall and not something a different X position in
// this same top wall can fix: EVERY top-wall position puts the element
// within single-digit mm of the board's top-edge copper and the panel
// frame, roughly 5-11x closer (46/9 ~= 5.1x to the panel frame, 46/4 ~=
// 11.5x to the board edge) than the ~46mm guidance asks for. That is a
// real RF-performance trade-off (reduced range/link reliability risk), not
// a modeling gap to leave open in an echo() addressed to a mechanical
// fit-check bead. It is now tracked as its own product decision in
// `pilink-58z` (P1, discovered-from this bead) -- see that bead for the
// options (accept + empirical range test, flip the element's radiating
// end, move to the rear wall, trim PCB copper near the top edge, or grow
// the enclosure). This file does not re-litigate those options or change
// the mount's X position for them; that call belongs to pilink-58z once
// Andreas decides.
echo(str("[pilink-8hx.4] Face-Y clearance ESTIMATE (unconfirmed board-to-face ",
         "mapping, same caveat as the X-axis numbers above): element at ",
         "face-y~", ANTENNA_ELEMENT_FACE_Y_ESTIMATE, "mm, board top edge at ",
         "face-y=", BOARD_TO_FACE_Y_OFFSET, "mm (~",
         CLEARANCE_TO_BOARD_TOP_EDGE_ESTIMATE, "mm clearance), panel frame top ",
         "at face-y=", PANEL_Y_MIN_FACE_LOCAL, "mm (~",
         CLEARANCE_TO_PANEL_FRAME_ESTIMATE, "mm clearance) -- vs the ",
         ANTENNA_KEEPOUT_FROM_METAL, "mm guidance. NOT MET at this or any ",
         "top-wall X position (face is only ", FACE_H, "mm tall, ~11mm of ",
         "it above the panel). Real RF trade-off, tracked in pilink-58z -- ",
         "not resolved here, not left pending."));

// *** pilink-58z confirmation (pilink-adt, 2026-11-16) ***
// pilink-58z's ~46mm-vs-~9mm clearance shortfall is computed entirely from
// PANEL_Y_MIN_BOARD_LOCAL (5.0, hardware/README.md:971's display-panel
// shadow), BOARD_TO_FACE_Y_OFFSET (6.0, the board-to-face mapping ASSUMPTION
// above), WALL_THICKNESS (2.0, this file's own constant) and
// ANTENNA_KEEPOUT_FROM_METAL (46, the research finding) -- none of which
// reference U201 or its board position anywhere in their derivation. Those
// four numbers, and therefore CLEARANCE_TO_PANEL_FRAME_ESTIMATE (~9mm) and
// pilink-58z's own shortfall figures, are unchanged by pilink-2yw's U201
// move: U201 relocating around the board does not move the display panel,
// change the board-to-face Y offset, or change the top wall's own
// thickness. Confirmed explicitly, not left ambiguous -- pilink-58z's RF-
// clearance product decision remains open and is genuinely unaffected by
// this bead's re-check.

module antenna_element_reference() {
  // Non-manifold preview of the antenna element itself, for visual
  // reference only -- never unioned into a shell.
  %color("DarkOliveGreen")
    cube([ANTENNA_ELEMENT_LENGTH, ANTENNA_ELEMENT_WIDTH, ANTENNA_ELEMENT_THICKNESS_NOMINAL]);
}

module antenna_keepout_reference() {
  // Non-manifold preview of the "keep metal clear" zone from the finding's
  // clearance guidance (see ANTENNA_KEEPOUT_FROM_METAL above). Centered on
  // the element, inflated symmetrically in all directions as the
  // simplification noted above.
  k = ANTENNA_KEEPOUT_FROM_METAL;
  %color("Yellow", 0.15)
    translate([-( k - ANTENNA_ELEMENT_LENGTH) / 2, -(k - ANTENNA_ELEMENT_WIDTH) / 2, 0])
      cube([k, k, 0.1]);
}

// The mount itself: a locating lip (raised frame) around the land, plus a
// cable channel and strain-relief clip running toward -Y (i.e. toward
// wherever the integrating shell's cavity continues down to U201 -- this
// file does not know that path in 3D, since pilink-8hx.1's internal
// standoff/cavity geometry above the board's top edge doesn't exist yet;
// the channel below is a short straight stub to hand off to).
//
// Local frame: X = left-right (= face-local X), Y = into the top wall's own
// shallow depth (toward the cavity/cable exit), Z = wall-normal (thickness).
// Origin (0,0,0) is the land's own bottom-left-front corner on the wall's
// inner surface.
module antenna_mount(
  land_length = MOUNT_LAND_LENGTH,
  land_width = MOUNT_LAND_WIDTH,
  lip_width = LIP_WIDTH,
  lip_height = LIP_HEIGHT,
  channel_width = CABLE_CHANNEL_WIDTH,
  channel_depth = CABLE_CHANNEL_DEPTH,
  channel_length = 1.0, // mm, short stub -- reduced from 8.0mm as part of the mount-depth fix (see MOUNT_LAND_WIDTH's "Mount depth" note above); real length still depends on pilink-8hx.1's cavity geometry and is expected to be overridden once that exists
  channel_exit_x = CABLE_CHANNEL_EXIT_X_INSET,
  clip_id = STRAIN_RELIEF_CLIP_ID,
  clip_height = STRAIN_RELIEF_CLIP_HEIGHT
) {
  // Locating lip: a thin rectangular frame standing LIP_HEIGHT proud of the
  // wall's inner surface, outer edge at the land footprint, so an installer
  // seats the adhesive-backed element against its inside face. Left open on
  // the -Y edge (cable exit side).
  //
  // *** FIX for PR #48 review item 4 (blocking) ***
  // The first version's difference() left the lip material on -Y (closed)
  // and nothing on +Y (open) -- backwards from this comment and from the
  // cable channel's own -Y direction below, so the channel ran straight
  // into solid lip material instead of the claimed open side. Rebuilt as
  // an explicit picture-frame (outer ring minus the land's own interior)
  // with the -Y edge's lip strip removed afterward, so -Y is actually open
  // and the end caps + the +Y edge actually stay closed.
  module lip_frame() {
    difference() {
      // Outer ring: land footprint expanded by lip_width on all 4 sides.
      translate([-lip_width, -lip_width, 0])
        cube([land_length + 2 * lip_width, land_width + 2 * lip_width, lip_height]);

      // Remove the land's own interior, leaving only the ring.
      translate([0, 0, -0.1])
        cube([land_length, land_width, lip_height + 0.2]);

      // Open the -Y edge (cable-exit side) by removing that edge's own
      // strip of the ring too, leaving the two end caps and the +Y edge.
      translate([0, -lip_width - 0.1, -0.1])
        cube([land_length, lip_width + 0.2, lip_height + 0.2]);
    }
  }

  color("SlateGray") lip_frame();

  // Cable channel stub: a short solid boss running from the land's open
  // (-Y) edge toward the cavity, with an actual groove cut into its top
  // face for the coax to sit in.
  //
  // *** FIX for PR #48 review item 5 (blocking) ***
  // The first version unioned the rounded-rectangle hull shape in as a
  // solid 2mm rod -- nothing was ever subtracted, so there was no cavity
  // for a cable at all. This version builds a boss with enough material
  // (CHANNEL_BOSS_MARGIN shoulder on each side, channel_depth + 1mm under
  // the groove) to actually cut channel_width x channel_depth of groove
  // out of via difference(), open at the boss's top face.
  module channel() {
    boss_width = channel_width + 2 * CHANNEL_BOSS_MARGIN;
    boss_height = channel_depth + 1.0; // mm, 1mm of wall left under the groove, this file's own choice
    groove_z = boss_height - channel_depth + channel_width / 2;

    difference() {
      translate([channel_exit_x - boss_width / 2, -channel_length, 0])
        cube([boss_width, channel_length, boss_height]);

      // Groove: rounded cross-section (hull of two cylinders) sized for
      // the bare 1.13mm coax only -- the IPEX/U.FL-class plug is on the
      // pigtail's OTHER end, mating at U201, not here (see
      // CABLE_CHANNEL_WIDTH's own comment above) -- cut down channel_depth
      // from the boss's top face.
      hull() {
        translate([channel_exit_x, 0.01, groove_z])
          rotate([90, 0, 0])
            cylinder(h = 0.02, d = channel_width, $fn = 24);
        translate([channel_exit_x, -channel_length - 0.01, groove_z])
          rotate([90, 0, 0])
            cylinder(h = 0.02, d = channel_width, $fn = 24);
      }
    }
  }

  color("SlateGray") channel();

  // Height of the channel's groove axis, mirroring channel()'s own
  // groove_z (boss_height - channel_depth + channel_width/2, and
  // boss_height - channel_depth is always 1.0 by construction above) --
  // used below to line the clip's bore up with the groove's own height so
  // the cable continues at the same level, not stepped.
  channel_groove_z = 1.0 + channel_width / 2;

  // Strain-relief clip: a C-shaped boss just past the channel's far end so
  // the coax doesn't transmit pull-force to the U.FL plug on U201.
  //
  // *** FIX for PR #48 review item 8 (minor, fixed as low-cost) ***
  // The first version's cutout cube spanned a full half-plane across the
  // ring (clip_id + 2*lip_width wide, centered on the ring), which removed
  // more than half the ring -- a U, not a C, with nothing left to grip the
  // cable. This version cuts only a narrow slot (STRAIN_RELIEF_CLIP_SLOT_WIDTH,
  // sized off the coax diameter with a small press-fit margin) so the ring
  // stays mostly closed and can actually snap over and hold the coax.
  //
  // *** FIX for PR #48 review round 2 (clip bore orientation) ***
  // The previous revision's ring had its bore along Z (wall-normal) --
  // rotate([0,0,90]) at the call site only spins the ring about its own
  // (still-Z) axis, it doesn't change which axis the hole runs along. A
  // Z-axis bore only grips the coax if the cable turns 90 degrees toward
  // the wall right at this point, which isn't the cable's real path: the
  // coax runs straight along -Y through the channel groove and keeps
  // going in -Y from here toward the cavity (see antenna_mount()'s own
  // doc comment -- this file hands off a straight stub, it doesn't know
  // the real 3D path beyond it either, but "straight along -Y" is the
  // channel's own direction, not Z). Fixed by building the ring with its
  // bore along Y instead, so the cable passes straight through it in the
  // same direction it travels through the channel.
  //
  // *** FIX for PR #48 review round 3 (blocking, "slot opens the wrong
  // way") ***
  // The slot used to be cut along pre-rotation -X, which rotate([90,0,0])
  // (rotation about the X axis) leaves unchanged -- so after the Y-bore
  // fix above, the slot still opened sideways (-X) while the channel's
  // own groove opens upward (+Z, see channel()'s "open at the boss's top
  // face"). A cable can't travel from the groove into the clip without a
  // 90-degree kink if the two don't open the same way. rotate([90,0,0])
  // maps a pre-rotation point (x,y,z) to (x,-z,y), so a slot that opens
  // along pre-rotation +Y lands on post-rotation +Z. Cut that way below
  // instead, so the slot opens the same direction as the groove.
  module strain_relief_clip() {
    // *** FIX for PR #48 review round 3 (blocking, "wall thickness
    // silently cut via LIP_WIDTH coupling") ***
    // Was `clip_id + 2 * lip_width`, coupling this ring's wall to the
    // mount lip's width. Uses its own STRAIN_RELIEF_CLIP_WALL constant
    // now (see the constant's own comment above for why).
    outer_d = clip_id + 2 * STRAIN_RELIEF_CLIP_WALL;
    // Built with the bore along Z first (easiest to reason about radii
    // and the slot cut), then rotated 90 degrees about X so the bore ends
    // up along Y. rotate([90,0,0]) maps a Z-axis bore to a Y-axis bore;
    // the slot's "full height along Z" (pre-rotation) becomes "full
    // length along Y" (post-rotation), which is what a snap-in slot
    // running the clip's whole length should do.
    rotate([90, 0, 0])
      translate([0, 0, -clip_height / 2])
        difference() {
          cylinder(h = clip_height, d = outer_d, $fn = 32);
          translate([0, 0, -0.1])
            cylinder(h = clip_height + 0.2, d = clip_id, $fn = 32);
          // Narrow snap-in slot from the bore out through the outer edge,
          // on one side only, running the full length of the clip. Cut
          // along pre-rotation +Y (not +/-X) so it opens along +Z after
          // the rotate([90,0,0]) above -- see the fix note at this
          // module's top.
          translate([-STRAIN_RELIEF_CLIP_SLOT_WIDTH / 2, -0.1, -0.1])
            cube([STRAIN_RELIEF_CLIP_SLOT_WIDTH, outer_d / 2 + 0.2, clip_height + 0.2]);
        }
  }

  // Positioned right at the channel's far (-Y) end, extending clip_height
  // further in -Y (so it doesn't overlap the channel boss), with its bore
  // centered at the groove's own height (channel_groove_z) rather than
  // stacked on top of the boss -- see channel_groove_z above.
  translate([channel_exit_x, -channel_length - clip_height / 2, channel_groove_z])
    color("DimGray") strain_relief_clip();

  // *** FIX for PR #48 review round 3 (blocking, "clip floats off the
  // wall") ***
  // After the round-2 re-centring on the groove axis, the ring (outer
  // radius = (clip_id + 2*STRAIN_RELIEF_CLIP_WALL)/2 = 1.6mm, centered at
  // z = channel_groove_z = 2.0mm) spans z = 0.4 to 3.6 -- 0.4mm clear of
  // the wall surface at z=0, with its only attachment a face shared with
  // the channel boss's own end. Not structurally sound on its own.
  //
  // Adds two legs from the wall surface (z=0) up into the ring's own
  // solid wall material, one on each side of the bore -- NOT a single
  // block spanning the full width, which would plug part of the cable's
  // own through-bore (clip_id-diameter hole) where it dips below
  // channel_groove_z. Each leg sits at |x_local| in
  // [clip_id/2, clip_id/2 + STRAIN_RELIEF_CLIP_WALL], i.e. exactly the
  // ring's own annulus width, outside both the bore (radius clip_id/2)
  // and the snap-in slot (|x_local| < STRAIN_RELIEF_CLIP_SLOT_WIDTH/2,
  // well inside the bore radius) -- so it only ever adds material where
  // the ring is already solid, reaching a bit past the ring's own center
  // height (see leg_z below) for real volumetric overlap, not just a
  // touching edge.
  clip_bore_r = clip_id / 2;                             // 0.8mm
  clip_outer_r = clip_id / 2 + STRAIN_RELIEF_CLIP_WALL;  // 1.6mm, = outer_d/2 above
  leg_width = clip_outer_r - clip_bore_r;                // 0.8mm
  leg_y = -channel_length - clip_height;                 // matches the ring's own Y-span
  // Up to slightly past the ring's own center height (channel_groove_z),
  // not stopping exactly at it: at the leg's inner edge (x_local =
  // clip_bore_r, right at the bore boundary) the ring's solid annulus
  // only starts a bit past the center height on that boundary line, so
  // stopping the leg exactly at channel_groove_z would touch the ring
  // there along a knife-edge instead of a real overlapping volume. The
  // margin below gives real overlap depth even at that worst-case edge.
  leg_z = channel_groove_z + 0.5;

  translate([channel_exit_x + clip_bore_r, leg_y, 0])
    color("DimGray") cube([leg_width, clip_height, leg_z]);
  translate([channel_exit_x - clip_outer_r, leg_y, 0])
    color("DimGray") cube([leg_width, clip_height, leg_z]);
}

// Self-contained preview assembly: places antenna_mount() at
// MOUNT_X_MIN/MOUNT_X_CENTER on a STAND-IN slab representing the top wall's
// local area, with the element + keepout reference shown in place, and a
// marker for U201's connector X-center plus the two sibling pinhole X
// positions so the resolved layout is visible in one render. The slab is
// explicitly NOT the real top wall (pilink-8hx.1/.2 own that) -- sized
// dynamically off MOUNT_X_MAX so it stays wide enough for whatever position
// the math above lands on, not a hardcoded guess.
module demo_assembly() {
  slab_length = MOUNT_X_MAX + 10; // mm, local preview only, not FACE_W -- 10mm margin past the mount's own right edge
  slab_depth = 16;  // mm, local preview only, not BODY_THICKNESS
  slab_thickness = WALL_THICKNESS;

  color("LightGray", 0.3)
    cube([slab_length, slab_depth, slab_thickness]);

  translate([MOUNT_X_MIN, slab_depth - MOUNT_LAND_WIDTH - 2, slab_thickness]) {
    antenna_mount();
    translate([ASSEMBLY_CLEARANCE, ASSEMBLY_CLEARANCE, 0])
      antenna_element_reference();
    translate([ASSEMBLY_CLEARANCE, ASSEMBLY_CLEARANCE, 0])
      antenna_keepout_reference();
  }

  // U201 U.FL connector X-center marker (short red peg dropping toward
  // where the PCB sits, well below this local slab).
  //
  // *** FIX for PR #48 review item 7 (minor, fixed as low-cost) ***
  // The first version subtracted MOUNT_X_MIN from every marker's X position,
  // but antenna_mount() is translated by +MOUNT_X_MIN in this same slab
  // frame -- so every marker below was drawn MOUNT_X_MIN mm too far left
  // (e.g. SW101 at 44-3=41 instead of 44), in the one view meant to show
  // the real positions. These markers are already in the slab's own
  // face-local-X frame (the same frame antenna_mount() is translated into),
  // so they need no extra offset.
  translate([U201_ANTENNA_FACE_X_CENTER, 0, 0])
    color("Red") cylinder(h = 0.5, d = 1.0, $fn = 12);

  // SW101/SW102 pinhole X markers (pilink-8hx.2's geometry, not drawn here
  // -- just the X position, to make the now-resolved clearance visible).
  translate([SW101_X_FACE_LOCAL, slab_depth, 0])
    color("Blue") cylinder(h = 0.5, d = 1.0, $fn = 12);
  translate([SW102_X_FACE_LOCAL, slab_depth, 0])
    color("Blue") cylinder(h = 0.5, d = 1.0, $fn = 12);
}

demo_assembly();
