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
// strain-relief clip coming out U-shaped instead of C-shaped). This
// revision re-derives the position from scratch (see "Mount position"
// below) and fixes all of those.

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

// U201 (ESP32-WROOM-32UE) antenna-connector-end edge, board-local, from
// .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md's
// "Verification: rear USB-C / antenna / FPC clearance check (pilink-5g8)":
// "that module edge sits at board-local Y ~= 2.65-2.9, X ~= 5-23
// (centered X=14)". The connector's exact position along that edge wasn't
// confirmed from a rendered datasheet drawing there either -- same caveat
// carried forward here.
U201_ANTENNA_X_MIN = 5.0;
U201_ANTENNA_X_MAX = 23.0;
U201_ANTENNA_X_CENTER = 14.0;
U201_ANTENNA_Y_MIN = 2.65;
U201_ANTENNA_Y_MAX = 2.9;

// Face-local X center of U201's U.FL connector, used below to check the
// resulting cable run length.
U201_ANTENNA_FACE_X_CENTER = U201_ANTENNA_X_CENTER + BOARD_TO_FACE_X_OFFSET; // 16.0mm

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
LIP_WIDTH = 0.8;              // mm, width of the raised locating lip around the land
LIP_HEIGHT = 0.4;             // mm, height of the raised locating lip
CABLE_CHANNEL_WIDTH = 2.0;    // mm, clear of ANTENNA_CABLE_DIAMETER (1.13mm) with margin for the IPEX plug body
CABLE_CHANNEL_DEPTH = 1.5;    // mm, depth of the groove cut into the channel boss (see channel() below)
CHANNEL_BOSS_MARGIN = 1.0;    // mm, solid shoulder left on each side of the groove so there is material to actually cut the groove into
CABLE_CHANNEL_EXIT_X_INSET = 6.0; // mm, UNSOURCED ASSUMPTION: neither the research finding nor the LCSC listing says where this part's actual pigtail leaves the element (flagged in both places). This file picks an exit point inset from the land's edge nearest U201 (see "Mount position" below for why that edge is nearest), on the assumption that the shortest practical cable run to U201's U.FL connector is the right default absent a real drawing -- not a confirmed exit point on the physical part.
STRAIN_RELIEF_CLIP_ID = 1.6;  // mm, snug over the 1.13mm coax
STRAIN_RELIEF_CLIP_HEIGHT = 2.0; // mm
STRAIN_RELIEF_CLIP_SLOT_WIDTH = ANTENNA_CABLE_DIAMETER + 0.3; // mm, narrow snap-in slot -- wide enough for the 1.13mm coax to press through, not the full half-ring opening the first version cut (which left a U, not a C -- see PR review item 8)

// Land (adhesive mounting area) footprint, element + clearance on all sides.
MOUNT_LAND_LENGTH = ANTENNA_ELEMENT_LENGTH + 2 * ASSEMBLY_CLEARANCE; // 47.8mm
MOUNT_LAND_WIDTH  = ANTENNA_ELEMENT_WIDTH + 2 * ASSEMBLY_CLEARANCE;  // 8.5mm

// ---------------------------------------------------------------------------
// Mount position in the top wall's own local X (= face-local X, left-right,
// unaffected by the lean -- see coordinate note above).
//
// *** FIX for PR #48 review item 1/2 (critical, blocking) ***
// The first version hugged the left inner wall (face-local X 3-50.8mm,
// covering element X 4-49.8mm) to keep the cable run to U201 short. That
// put the element squarely across SW101's pinhole at face-local X=44 --
// SW101_X_FACE_LOCAL above. The review's own measurements (top wall inner
// depth ~10mm: body ~14mm thick minus front/back walls; land+lip depth
// 9.3mm; PTS645-class actuator sits a few mm in front of the PCB plane)
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
// 3-42mm = 39mm, less than the 45.8mm element, so it doesn't fit; checked
// directly here, not assumed). Minimum clearance from SW102's pinhole edge
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
// 63.75mm, roughly 47.75mm in X alone from U201's connector-center at
// face-local X=16.0mm. The part's pigtail is ~240mm (inferred from the
// part number, per the research finding), so a ~50mm run leaves well over
// 150mm of slack to coil inside the enclosure cavity during assembly --
// not a real constraint here, unlike the old (false) assumption that
// hugging the left wall was load-bearing for cable length.
PINHOLE_EDGE_CLEARANCE_X = SW102_X_FACE_LOCAL + PINHOLE_DIAMETER / 2 + PINHOLE_X_CLEARANCE;
MOUNT_X_MIN = PINHOLE_EDGE_CLEARANCE_X;                // 57.75mm
MOUNT_X_MAX = MOUNT_X_MIN + MOUNT_LAND_LENGTH;         // 105.55mm
MOUNT_X_CENTER = (MOUNT_X_MIN + MOUNT_X_MAX) / 2;

echo(str("[pilink-8hx.4] Mount X ", MOUNT_X_MIN, "-", MOUNT_X_MAX,
         "mm. SW101 pinhole X=", SW101_X_FACE_LOCAL, ", SW102 pinhole X=",
         SW102_X_FACE_LOCAL, " (+/-", PINHOLE_DIAMETER / 2,
         "mm radius each) -- both now clear of the mount by construction."));

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
// not a literal collision risk. The real question is the Z (perpendicular
// -to-face) gap between the top wall's inner surface and the panel
// frame/PCB below it at this X position -- and that number is NOT
// derivable from any document in this repo today: pilink-8hx.1/pilink-8hx.2
// haven't landed real 3D wall/standoff geometry yet, so there is no actual
// top-wall-to-PCB distance to check against the ~46mm keepout guidance.
// Stated honestly rather than invented: this file picks the placement that
// resolves the one real, checkable 3D collision (the pinholes) and
// surfaces the panel-shadow X-overlap number above instead of silently
// dropping it; the Z-clearance question is carried forward, unresolved,
// for pilink-8hx.1/pilink-8hx.2/pilink-8hx.5 to actually check once real
// wall geometry exists to measure.
PANEL_OVERLAP_X_MIN = max(MOUNT_X_MIN, PANEL_X_MIN_FACE_LOCAL);
PANEL_OVERLAP_X_MAX = min(MOUNT_X_MAX, PANEL_X_MAX_FACE_LOCAL);
PANEL_OVERLAP_X = PANEL_OVERLAP_X_MAX > PANEL_OVERLAP_X_MIN ? PANEL_OVERLAP_X_MAX - PANEL_OVERLAP_X_MIN : 0;

echo(str("[pilink-8hx.4] Display-panel shadow X ", PANEL_X_MIN_FACE_LOCAL, "-",
         PANEL_X_MAX_FACE_LOCAL, "mm vs mount X ", MOUNT_X_MIN, "-", MOUNT_X_MAX,
         "mm: ", PANEL_OVERLAP_X,
         "mm of X-overlap, unavoidable given the fixed panel/pinhole footprint. ",
         "Z (perpendicular-to-face) clearance to the panel frame/PCB ground plane ",
         "is NOT yet checkable -- no real top-wall 3D geometry exists in this repo ",
         "yet (pilink-8hx.1/.2). Flagged, not resolved here."));

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
  channel_length = 8.0, // mm, short stub -- real length depends on pilink-8hx.1's cavity geometry
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
      // the 1.13mm coax plus its IPEX plug body, cut down channel_depth
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

  channel_boss_height = channel_depth + 1.0; // mirrors channel()'s own boss_height, see note there

  // Strain-relief clip: a C-shaped boss at the channel's far end so the
  // coax doesn't transmit pull-force to the U.FL plug on U201.
  //
  // *** FIX for PR #48 review item 8 (minor, fixed as low-cost) ***
  // The first version's cutout cube spanned a full half-plane across the
  // ring (clip_id + 2*lip_width wide, centered on the ring), which removed
  // more than half the ring -- a U, not a C, with nothing left to grip the
  // cable. This version cuts only a narrow slot (STRAIN_RELIEF_CLIP_SLOT_WIDTH,
  // sized off the coax diameter with a small press-fit margin) so the ring
  // stays mostly closed and can actually snap over and hold the coax.
  module strain_relief_clip() {
    outer_d = clip_id + 2 * lip_width;
    difference() {
      cylinder(h = clip_height, d = outer_d, $fn = 32);
      translate([0, 0, -0.1])
        cylinder(h = clip_height + 0.2, d = clip_id, $fn = 32);
      // Narrow snap-in slot from the outer edge through to the bore, on
      // one side only.
      translate([-outer_d / 2 - 0.1, -STRAIN_RELIEF_CLIP_SLOT_WIDTH / 2, -0.1])
        cube([outer_d / 2 + 0.2, STRAIN_RELIEF_CLIP_SLOT_WIDTH, clip_height + 0.2]);
    }
  }

  translate([channel_exit_x, -channel_length, channel_boss_height])
    rotate([0, 0, 90])
      color("DimGray") strain_relief_clip();
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
