#!/usr/bin/env python3
"""Headless placement for pico-link-hw.kicad_pcb (pilink-7el.12, upright
desk-clock form factor).

Usage (from hardware/):  python3 scripts/place.py

Sets the board outline, mounting holes, design-rule minimums and every
footprint position. Idempotent: outline/holes it created earlier are removed
before being re-added, so re-running never duplicates them. It does NOT
touch tracks/vias/zones -- see the README's "PCB layout" section for the
scripts to run after it.

All coordinates below are millimetres in BOARD-LOCAL space: x increases
RIGHT, y increases DOWN THE FACE (y=0 is the board's top edge, y=BOARD_H is
the bottom edge -- so "Nmm up the face" in the ADR/proposal means
y = BOARD_H - N). ORIGIN shifts board-local (0,0) onto the KiCad page.

Supersedes PR #33 (pilink-7el.9)'s 100x55mm flat-slab placement, which is
incompatible with the upright desk-clock form factor decided in
.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md: wrong
outline, encoder on the wrong side, wrong J501 orientation, no panel-shadow
keep-out. This script re-derives every position from that ADR and
docs/plans/2026-11-15-product-layout-proposal.md section 6c, cross-checked
against each footprint's own real pads/courtyard (queried from the board
pcbnew produced via create_board_from_schematic) rather than the ASCII
diagrams' approximate grid.
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
PROJECT = os.path.join(HERE, "..", "pico-link-hw.kicad_pro")

# Net classes. Default clearance must stay below the RP2350B QFN-80's
# 0.18mm pad-to-pad gap, or every adjacent pin pair is a DRC error.
# "Power" is only for nets that never touch the 0.4mm-pitch QFN (the router
# cannot neck a wide track down into a 0.2mm pad).
DEFAULT_CLASS = {"clearance": 0.15, "track_width": 0.2,
                 "via_diameter": 0.6, "via_drill": 0.3}
POWER_CLASS = {"clearance": 0.2, "track_width": 0.5,
               "via_diameter": 0.8, "via_drill": 0.4}
# Net-(D501-K) (backlight anode rail, 40mA) is deliberately not here: a 0.5mm
# track cannot enter J501's 0.3mm pads at 0.5mm pitch. /USB-C/VBUS_RAW is
# also deliberately not here (unlike PR #33's flat-slab layout): J401's
# back-side flip puts its VBUS pads in a pocket already dense with
# CC1/CC2/USB_DP/USB_DM crossings, and Freerouting could not complete a
# 0.5mm VBUS_RAW connection there in any tested placement. Routed at the
# default 0.2mm width instead and widened post-route wherever DRC allows
# (scripts/widen.py), same as the QFN power-rail necking problem below.
POWER_NETS = ["+5V", "Net-(D501-A)"]

ORIGIN = (100.0, 100.0)
# NOTE: comments below that quote x:[28,87] y:[5,47], 59.4, (59,37), 118 etc. describe the
# pre-pilink-4qc geometry; the constants/tables are authoritative.
BOARD_W, BOARD_H = 122.5, 50.0  # pilink-4qc: 118 -> 122.5 (X-flange worst case + >=1mm SW306/knob courtyard to edge)
HOLE_D = 2.2  # M2 clearance, NPTH
# Back-shell boss mounting holes. Not at the board's bare corners: the
# ESP32 (upper-left) and encoder (lower-left) courtyards already claim the
# whole left edge, so holes are placed in the genuinely free pockets --
# top-right and bottom-right of the button zone, the bottom-left strip
# below the encoder, and the gap between the top-edge switches and J501.
# pilink-4qc: right holes follow the wider board (112 -> 116.5, same 6mm edge
# margin). H4: the panel top edge is now y=4 (was 5), so (59,2.5)'s 4.0mm
# screw head (reaches y=4.5) would overlap the 3.3mm-tall panel stack; there
# is no room above it (head needs y<=1.5, hole edge 0.4mm from the board
# edge), so H4 moves LEFT of the panel (panel x starts 34.12): head reaches
# x=31, 3.1mm clear.
HOLES = [(10, 44), (116.5, 6), (116.5, 44), (29, 2.5)]

# Display panel shadow, per the ADR/proposal 6c panel-shadow rule: 59x42mm,
# centred on the face window. Derived from J501's own anchor math below (not
# the other way round): J501's insertion face sits 24mm in from the panel's
# RIGHT edge, and its anchor x=59.4 puts that face at x=63 (anchor + half the
# footprint's 7.25mm-wide courtyard), so the panel's right edge is x=87 and
# (width 59mm) its left edge is x=28 -- i.e. x:[28,87], NOT x:[27,86] (an
# earlier draft of this comment had the off-by-one that README.md's own
# table never had; this constant is now the single source either way).
# y:[5,47] (height 42mm) centred on y=26, matching J501's own target
# centreline.
# pilink-4qc: moved so the ACTIVE AREA (insets L 2.65 / R 7.39 / T,B 2.64 in
# the 59x42 outline -> centre 27.13 in from the panel's left edge, 21 down)
# is centred on the board: x-centre BOARD_W/2 = 61.25 -> left edge 34.12,
# right edge 93.12; knob/diamond are +/-47.0 from the active-area centre (61.25):
# X flange (R4.5) to the front_shell ledge (panel right + 2.0 = 95.12) is
# 0.63mm nominal / 0.43mm worst case (0.2mm bore play), SW306 and the knob
# courtyard sit >=1.0mm from the board edge; y-centre 25 -> y:[4,46]. (Older comment text above that
# says x:[28,87] y:[5,47] is the pre-pilink-4qc geometry.)
PANEL = {"x": (34.12, 93.12), "y": (4.0, 46.0)}

MM = pcbnew.FromMM


def pt(x, y):
    return pcbnew.VECTOR2I(MM(ORIGIN[0] + x), MM(ORIGIN[1] + y))


# --- RP2350B and its ring of decoupling -----------------------------------
# Cluster sits under the display panel shadow (see PANEL above, x:[28,87]
# y:[5,47]): every part in this ring is a QFN/0402/SOIC/USON/crystal, all
# comfortably <=2.5mm tall, so it's allowed under the glass per the
# panel-shadow rule. Shifted left of J501's column (x:[56,63]) to leave it
# clear.
CX, CY = 44.0, 24.0
RING = 7.2  # decoupling cap centre distance from U101 centre

# ref: (x, y, rot) ; rot None/str => auto-orient so pad 1 faces `face`
P = {
    "U101": (CX, CY, 0),
    "C106": (CX - RING, CY - 2.2, "chip"),
    "C116": (CX - RING, CY - 0.2, "chip"),
    "C107": (CX - RING, CY + 1.8, "chip"),
    "C108": (CX - RING, CY + 3.8, "chip"),
    "C119": (CX - 10.6, CY + 0.8, 90),
    "C109": (CX - 2.6, CY + RING, "chip"),
    "C110": (CX - 0.8, CY + RING, "chip"),
    "C117": (CX + 0.8, CY + RING, "chip"),
    "C111": (CX + RING, CY + 3.8, "chip"),
    "C112": (CX + RING, CY + 0.75, "chip"),
    "C118": (CX + RING, CY - 0.75, "chip"),
    "C113": (CX + RING, CY - 3.6, "chip"),
    "C114": (CX - 2.4, CY - RING, "chip"),
    "C115": (CX + 0.7, CY - RING, "chip"),
    "C103": (CX + 2.85, CY - RING, "chip"),
    "C105": (CX + 6.6, CY - 5.4, "chip"),
    "R104": (CX + 6.6, CY - 6.7, 0),
    "L101": (CX + 6.5, CY - 10.6, "chip"),
    "C104": (CX + 10.0, CY - 10.6, "l101"),
    "Y101": (CX, CY + 11.5, 0),
    "C101": (CX - 3.5, CY + 11.5, 90),
    "C102": (CX + 3.5, CY + 11.5, 90),
    "R101": (CX + 2.0, CY + 9.0, 180),
    # QSPI flash + PSRAM, above-left of the QSPI pins
    "U102": (35.0, 11.5, 0),
    "C120": (35.0, 7.4, 0),
    "U103": (42.5, 13.7, 0),
    "C121": (42.2, 11.0, 0),
    "R105": (39.5, 16.6, 0),
    # --- BOOTSEL / RESET: side-actuated SMD tacts at the TOP edge ---------
    # (pilink-7el.10/ADR consequence #4) -- the ~5mm strip between the
    # board's top edge and the panel's top edge (panel starts y=5), laid
    # out laterally over the RP2350B/flash cluster above, clear of the
    # ESP32 (x<24) and the button zone (x>86). Pull-ups follow to keep the
    # QSPI_SS/RUN stubs short.
    "SW101": (42.0, 2.7, 0),
    "SW102": (52.0, 2.7, 0),
    "R102": (42.0, 8.0, 0),
    "R103": (52.0, 8.0, 0),
    # --- USB-C: vertical receptacle on the BACK side, low, centred -------
    # between the rear legs (board-centre x=59, legs at +/-40mm -> x=19/99).
    # Flipped to B.Cu in main() (pcbnew FOOTPRINT.Flip, not expressible as
    # a plain (x,y,rot) tuple).
    # pilink-hdl (user decision, 2026-11-16): raised from y=45.5 to y=37.
    # The proposal (6c) wants the plug exiting ~15mm up the back; with the
    # shell's face mapping Qface = 52 - board_y (back_shell.scad) the old
    # anchor was Qface 6.5, and pilink-8ry (PR #55) found a real 5-6.5mm
    # cable boot would hit the table ~10-13mm behind the case from there.
    # y=37 gives Qface 15 exactly. Real clearance probe (every footprint's
    # bounding box, margin 1mm around J401's 9.05x5.35mm courtyard): nothing
    # within 1mm at y=37 on either layer; the only neighbour that closes in
    # higher up is J501 (courtyard bottom edge y=31.53) -- J401's courtyard
    # top edge is y=34.32 here, 2.8mm clear, left as margin for the FPC
    # fold rather than pushing to y=35 (0.8mm clear, Qface 17).
    # x stays 59 (between the rear legs); that is inside the panel shadow
    # either way, so J401's front-side THT leg protrusion flag is NOT
    # resolved by moving it up (only moving it past x=87 would).
    "J401": (61.25, 37.0, 0),  # pilink-4qc: x re-centred on the wider board (BOARD_W/2)
    # F401/R401-404 (USB-C ESD/CC pocket), right of the backlight cluster.
    # pilink-hdl: restored to their pre-pilink-2yw coordinates (undoing the
    # +9mm-in-Y rigid-group shift pilink-2yw applied to keep clear of
    # U201's old front-side pocket above the diamond) now that U201 has
    # left the front side of the board entirely (see U201 below) -- nothing
    # forces this pocket to stay shifted any more.
    "F401": (90.12, 36.0, 0),
    "R401": (90.12, 32.0, 0),
    "R402": (90.12, 30.0, 0),
    "R403": (94.12, 32.0, 0),
    "R404": (94.12, 30.0, 0),
    # --- 3V3 LDO + bulk caps -----------------------------------------------
    # pilink-2yw relocated this cluster from the free pocket below the
    # button diamond (90-106,42-47.5) into the column U201 used to occupy
    # at the top-left, to make room for U201's (then front-side) move.
    # pilink-hdl: left here rather than moved back -- U201 is now on B.Cu
    # (see below) and no longer needs any front-side column at all, but
    # this spot is still clear of the recentred encoder (SW303, >=1.3mm
    # gap, unchanged) and moving it again would just be more front-side
    # churn for no placement benefit. Anchors keep the same internal
    # geometry as the original cluster (U1 as the reference point, C1/C2/
    # C3 at their original offsets from it).
    "C1": (4.0, 10.0, 0),
    "U1": (14.0, 10.0, 0),
    "C2": (14.0, 15.5, 0),
    "C3": (20.0, 10.0, 0),
    # --- ESP32: relocated to the BACK side (B.Cu) (pilink-hdl) --------------
    # pilink-2yw (2026-11-16) moved U201 from upper-left (14,12.5) to a
    # front-side pocket above the A/B/X/Y diamond at (99,11.6), to free the
    # knob's column so SW303 could re-centre on true board y=25 -- but that
    # forced the diamond itself 9mm off board-centre (y=34, not y=25) as a
    # side effect. Andreas rejected that compromise (pilink-hdl): he wants
    # BOTH the knob AND the diamond centred on y=25 simultaneously.
    #
    # A read-only feasibility scan (pilink-hdl's own investigation) found no
    # front-side-only arrangement works: centring the diamond at (102,25)
    # leaves only ~13.1mm clear above/below it to the board edge, short of
    # U201's real courtyard (measured off this board: 19.55 x 20.25mm, local
    # x:[-9.78,9.78] y:[-9.88,10.38]) by about 6-7mm in every front-side
    # column tried. The only arrangement that lets both the knob and the
    # diamond sit on y=25 at once is moving U201 off the front side
    # entirely, onto B.Cu.
    #
    # Checked before committing to this (not assumed):
    # - Real back-side obstructions: only J401 (B.Cu, x:[54.47,63.53]
    #   y:[42.82,48.18]) and the through-hole LEAD positions of SW303 (the
    #   encoder's 7 THT pins span x:[8.5,23] y:[19.4,30.6] -- much smaller
    #   than its 17.55x14.25mm F.CrtYd) and J101 (THT, at (20,46)) poke
    #   through to the back. Every other populated front-side footprint in
    #   this project (SW101/SW102, SW305-308, J501, the ESP32 decoupling
    #   network, all resistors/caps) is pure SMD (pad attribute SMD, 0mm
    #   drill, confirmed by reading every pad on the board, not assumed from
    #   part type) -- nothing else protrudes to the back. The whole
    #   top-right quadrant (x>87, y<25ish), where U201 used to sit on the
    #   front per pilink-2yw, is therefore completely free on B.Cu: no THT
    #   protrusion, and H2 (112,6) clears U201's B.Cu courtyard at this same
    #   anchor by >=3.2mm (same geometry pilink-2yw already DRC-verified
    #   clean on the front -- flipping the layer doesn't change the XY
    #   footprint or the H2/edge clearances it already passed).
    # - Module height vs. the back-shell's own flat cavity (the real check
    #   this bead asked for, same class as J401's own boss precedent, PR
    #   #52): ESP32-WROOM-32UE's real datasheet-confirmed envelope (external-
    #   antenna variant, both the 32D/U and 32E/UE datasheets agree,
    #   .research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md point 3)
    #   is 18.0 x 19.2 x 3.2mm -- the footprint's own F.Fab outline here
    #   (18 x 19.2mm) matches that exactly, confirming 3.2mm is the real
    #   mounted height above the PCB surface, not a guess. enclosure/
    #   back_shell.scad's REAR_CLEARANCE (the flat cavity depth behind the
    #   PCB before the back wall) is 3.0mm. 3.2mm > 3.0mm by only 0.2mm --
    #   U201 overhangs the bare cavity by 0.2mm, the same class of problem
    #   J401 had (which needed a 2.0mm local boss for its own 1.5mm
    #   overhang), smaller for the module body alone. But 0.2mm understates
    #   it: the mated U.FL plug (Hirose: max 2.5mm above the module PCB,
    #   so roughly 3.3mm above the host PCB, module PCB ~0.8mm inferred) and
    #   the Ø1.13mm pigtail also face the back shell and must exit/bend in
    #   the same 3.0mm cavity -- real local relief, not a 0.2mm boss (see
    #   README Known gap 8). This is a real, non-zero finding -- U201 needs
    #   its own local relief on B.Cu at this spot -- flagged as a follow-up
    #   for back_shell.scad (see the discovered-from bead filed alongside
    #   this placement), not fixed in this PCB-only bead.
    #
    # Anchor kept at pilink-2yw's own (99,11.6) -- same XY, now on B.Cu
    # (FOOTPRINT.Flip in main(), via BACK_SIDE below) instead of F.Cu. Since
    # the courtyard/edge/H2 geometry at this XY was already DRC-verified
    # clean on the front, and a B.Cu footprint occupying the same XY as a
    # front-side SMD part (the recentred diamond, see below) is electrically
    # and physically fine -- opposite sides of a double-sided board, no
    # courtyard-overlap DRC rule spans layers -- reusing it needs no further
    # geometric re-derivation, only the layer change. Antenna orientation
    # (rot=0) unchanged; whether the U.FL->antenna-mount run is still
    # sensible from the BACK of the board (not just a different front-side
    # column) is pilink-8hx.4's own geometry to re-check, not re-derived
    # here -- flagged as a follow-up, same as pilink-2yw flagged its own
    # front-side move.
    "U201": (99.0, 11.6, 0),
    # Decoupling/strap passives moved to B.Cu with U201 (pilink-hdl) --
    # same XY pilink-2yw already placed them at (kept, not re-derived: the
    # panel-shadow clearance concern that drove R202's old "2.2mm is too
    # tight" placement decision was a FRONT-side height rule and no longer
    # applies to any of these now that they're on B.Cu), just following
    # U201 to the back side so EN/strap/decoupling traces to its pads stay
    # direct (no via) rather than crossing to the front.
    "C201": (87.2, 4.1, 0),
    "C202": (87.2, 7.1, 0),
    "R201": (87.3, 10.1, 0),
    "C203": (87.3, 13.1, 0),
    "R202": (111.0, 11.1, 0),
    # --- display FPC + backlight boost, under the panel (all <=2.5mm) ----
    # J501 rotated 270 deg: puts the 40-pin row (local y=-9.75..9.75) along
    # board Y (long axis vertical, per the ADR) and the pad-row/insertion
    # side (local offset +2.68 after this rotation) toward +X, i.e. facing
    # the panel's right edge the FPC folds in from. Anchor x=59.4 puts the
    # insertion-face edge (courtyard max x = anchor+3.625) at x=63, 24mm in
    # from the panel's right edge at x=87 (pilink-0o2's concrete rule).
    # Anchor y=19 puts J501's centre 7.0mm up from the panel's own vertical
    # centreline (y=26, from PANEL above) -- matching the ADR's "~7mm"
    # summary figure exactly; pilink-0o2's own refined measurement was
    # 7.2mm, so this placement is 0.2mm off that figure, right at the edge
    # of (not inside) the finding's own +/-0.2mm tolerance band. Not
    # re-tuned here: the difference is sub-pad-pitch and doesn't change any
    # DRC/netlist result, but say the real built number rather than quoting
    # the finding's number as if it were hit exactly.
    "J501": (65.52, 18.0, 270),  # pilink-4qc: moved with the panel (+6.12, -1) so the FPC-fold offsets are unchanged
    # pilink-4qc: boost cluster moved with J501 (+6.12,-1) and the F401/R401-404 pocket +6.12 in x,
    # keeping J501-LED_K -> U501 FB geometry (backlight_sw_vs_fb DRU rule).
    "C501": (76.12, 36.0, 0),
    # L501 shifted 1.5mm further from U501 than a naive mirror of the old
    # layout would put it: at (70,41) its own pin 1 (SW node) landed only
    # 1.0mm from U501 pin 3 (FB), short of the custom DRU keepout below
    # (1.2mm) -- caught by DRC, not assumed.
    "L501": (74.62, 40.0, 180),
    "D501": (81.12, 37.0, 180),
    "U501": (81.12, 40.0, 0),
    "C502": (86.12, 37.0, 0),
    "R501": (81.12, 43.0, 0),
    # --- user controls -----------------------------------------------------
    # Knob (SW303): the footprint's anchor is pad A (the solder side), NOT
    # the shaft -- the shaft/knob centre sits at local (+7.5,+2.5) from the
    # anchor (confirmed from the footprint's own F.Fab/silkscreen shaft
    # circle, centred at local (7.5,2.5), radius 3mm).
    # pilink-2yw: re-centred now that U201 no longer shares this column
    # (see U201 above). Anchor solved backwards from the TRUE board-
    # vertical-centre shaft target (16, board y=25) -- not the ADR's old
    # "19mm up the face" figure (board y=31, lower third), which was itself
    # only a consequence of U201 stacking above the encoder, not a target
    # worth preserving. Achieved shaft centre: board y=25 EXACTLY (anchor
    # (8.5, 22.5) = (16,25) - (7.5,2.5)) -- no compromise was needed to
    # clear a real courtyard this time (U201 is gone from the column, the
    # LDO cluster placed above it leaves >=1.3mm clearance).
    # Re the README's own board-to-face mapping caveat (corrected here,
    # pilink-2yw code review, 2026-11-16 -- the two conventions below were
    # previously swapped): under the README's stated (unverified)
    # BOTTOM-ALIGNED default (board's bottom edge flush with the face's
    # bottom edge), the face's own vertical centre (28mm up the ~56mm
    # face) falls at board y=22, so this placement (board y=25) sits 3mm
    # BELOW the face's visual centre under that convention -- not exactly
    # centred on it. If instead the face is CENTRED on the board (6mm of
    # slack split evenly top/bottom), the face's visual centre reads as
    # board y=25 -- exactly matching this placement; "exactly centred" is
    # only true under that second convention. Still flagged for
    # pilink-8hx.1/.2 to confirm which convention the real boss/standoff
    # geometry actually uses. Either way this is a real improvement over
    # the old placement (board y=31), which was 9mm below face-centre
    # under the bottom-aligned convention or 6mm under the centred one --
    # there was never a single "~12mm-ish" figure.
    #
    # pilink-hdl: unchanged -- the knob was already exactly on board y=25
    # as of pilink-2yw; this bead's own job was restoring the DIAMOND to
    # y=25 too (see below) without re-opening the knob's own placement.
    "SW303": (6.75, 22.5, 0),  # pilink-4qc: shaft x 14.25 = 61.25 - 47.0, mirror of the diamond centre x=108.25
    "R304": (34.0, 30.0, 0),   # encoder A pull-up (GPIO22)
    "R303": (34.0, 32.0, 0),   # encoder B pull-up (GPIO23)
    "R309": (34.0, 34.0, 0),   # encoder push-switch pull-up (GPIO28)
    # A/B/X/Y diamond, button zone (x>86): caps Ø8mm, +/-8mm centres,
    # standard gamepad layout (Y top/X left/B right/A bottom), matching the
    # proposal's own diagram annotation order. The exact SW305-308 <->
    # physical-position mapping is a layout choice, not schematic-
    # constrained (firmware maps GPIO24-27 to logical buttons separately,
    # see pilink-otf); documented here, not inferred.
    # pilink-2yw shifted the whole group DOWN 9mm as a rigid block, centre
    # (102,25) -> (102,34), to open enough clear height above it for U201's
    # (then front-side) relocation. pilink-hdl restores centre (102,25)
    # EXACTLY -- true board-vertical-centre, same target as the knob above
    # -- now that U201 has moved to B.Cu (see U201's own comment above) and
    # no longer needs any front-side room above or beside this diamond at
    # all. Both the knob and the diamond now sit on board y=25
    # simultaneously, which is what this bead was asked to achieve.
    "SW308": (108.25, 17.0, 0),  # Y (top)
    "SW307": (100.25, 25.0, 0),   # X (left)
    "SW306": (116.25, 25.0, 0),  # B (right)
    "SW305": (108.25, 33.0, 0),  # A (bottom)
    # Pull-ups: pilink-hdl restores these to their pre-pilink-2yw spot
    # (90, 6.0-10.8) -- the sliver right of U201's OLD front-side footprint
    # that pilink-2yw had to vacate them from is irrelevant now that U201
    # isn't on the front there at all; this original spot is clear again
    # (nothing else claims x=90, y=6-10.8 on F.Cu).
    "R308": (90.0, 6.0, 0),
    "R307": (90.0, 7.6, 0),
    "R306": (90.0, 9.2, 0),
    "R305": (90.0, 10.8, 0),
    # --- SWD debug header (pilink-2ar), free pocket below the encoder ----
    # Rotated 180 so the pin-1-anchored courtyard extends UP from the
    # anchor instead of down -- lets it clear both the board's bottom edge
    # and the encoder's courtyard above it in the same ~12mm-tall pocket.
    "J101": (20.0, 46.0, 180),
}

FACE = {"chip": (CX, CY), "l101": (CX + 6.5, CY - 10.6)}

# Footprints that must end up on the back side (B.Cu): vertical-mount J401
# mates perpendicular to the PCB and exits the rear wall, so it is a
# back-side part (pilink-7el.11 / pilink-0do). pilink-hdl adds U201 (moved
# to B.Cu so both the knob and the A/B/X/Y diamond can sit on board y=25 at
# once, see U201's own placement comment above) and its decoupling/strap
# network (C201/C202/R201/C203/R202), moved with it so their traces to
# U201's pads stay direct rather than crossing layers.
BACK_SIDE = {"J401", "U201", "C201", "C202", "R201", "C203", "R202"}


def auto_orient(fp, target):
    """Rotate fp (0/90/180/270) so its pad 1 is the pad nearest target."""
    best = None
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        pad = next(p for p in fp.Pads() if p.GetNumber() == "1")
        d = (pad.GetPosition() - target).EuclideanNorm()
        if best is None or d < best[0]:
            best = (d, rot)
    fp.SetOrientationDegrees(best[1])


def main():
    board = pcbnew.LoadBoard(BOARD)

    # -- design-rule minimums (JLCPCB, checked 2026-11-15; see README) -----
    ds = board.GetDesignSettings()
    ds.m_MinClearance = MM(0.127)
    ds.m_TrackMinWidth = MM(0.127)
    ds.m_ViasMinSize = MM(0.45)
    ds.m_MinThroughDrill = MM(0.2)
    ds.m_ViasMinAnnularWidth = MM(0.1)
    ds.m_HoleToHoleMin = MM(0.25)
    ds.m_HoleClearance = MM(0.2)
    ds.m_CopperEdgeClearance = MM(0.3)

    # -- outline + holes (remove earlier ones first: never duplicate) ------
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(d)
    for fp in list(board.GetFootprints()):
        if fp.GetReference().startswith("H") and fp.GetReference()[1:].isdigit():
            board.Remove(fp)

    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pt(0, 0))
    rect.SetEnd(pt(BOARD_W, BOARD_H))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(MM(0.1))
    board.Add(rect)

    # -- panel-shadow rectangle (documentation graphic, not a keepout rule) -
    # Drawn on User.Comments so it's a single authoritative, queryable
    # record of where the 59x42mm display-panel window sits on THIS board,
    # instead of only living in README/place.py prose that can drift out of
    # sync with each other (as the x:[27,86] vs x:[28,87] mismatch this
    # fixed did). Remove any earlier copy first so re-running this script
    # never duplicates it.
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Cmts_User:
            board.Remove(d)
    panel = pcbnew.PCB_SHAPE(board)
    panel.SetShape(pcbnew.SHAPE_T_RECT)
    panel.SetStart(pt(PANEL["x"][0], PANEL["y"][0]))
    panel.SetEnd(pt(PANEL["x"][1], PANEL["y"][1]))
    panel.SetLayer(pcbnew.Cmts_User)
    panel.SetWidth(MM(0.1))
    board.Add(panel)

    for i, (x, y) in enumerate(HOLES, 1):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(f"H{i}")
        fp.SetValue("MountingHole_M2")
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM
                         | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        pad = pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D)))
        pad.SetDrillSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D)))
        pad.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
        fp.Add(pad)
        cy = pcbnew.PCB_SHAPE(fp)
        cy.SetShape(pcbnew.SHAPE_T_CIRCLE)
        cy.SetCenter(pcbnew.VECTOR2I(0, 0))
        cy.SetEnd(pcbnew.VECTOR2I(MM(HOLE_D / 2 + 0.6), 0))
        cy.SetLayer(pcbnew.F_CrtYd)
        cy.SetWidth(MM(0.05))
        fp.Add(cy)
        board.Add(fp)
        fp.SetPosition(pt(x, y))

    # -- footprints --------------------------------------------------------
    refs = {fp.GetReference() for fp in board.GetFootprints()}
    missing = sorted(r for r in refs if r not in P and not r.startswith("H"))
    extra = sorted(r for r in P if r not in refs)
    if missing or extra:
        sys.exit(f"placement table out of sync: unplaced={missing} unknown={extra}")

    for ref, (x, y, rot) in P.items():
        fp = board.FindFootprintByReference(ref)
        fp.SetPosition(pt(x, y))
        if ref in BACK_SIDE and fp.GetLayer() == pcbnew.B_Cu:
            # Already flipped on an earlier run: only the position is
            # re-applied. Re-running SetOrientationDegrees(rot) on a
            # B.Cu footprint rotates it 180 deg relative to what Flip()
            # produced (found when U201's antenna end silently turned
            # round on a second run, pilink-hdl) -- keep it idempotent.
            # NOTE: this means the `rot` column of BACK_SIDE parts is only
            # honoured on the FIRST (F.Cu -> B.Cu) run; editing it later is
            # a no-op. To change a back-side part's orientation, flip it
            # back to F.Cu in the board first. The board stores U201 at
            # 180 (what Flip(LEFT_RIGHT) gives a rot-0 part), not 0.
            print(f"{ref}: already on B.Cu, position only (rot column skipped)")
            continue
        if isinstance(rot, str):
            fx, fy = FACE[rot]
            auto_orient(fp, pt(fx, fy))
        else:
            fp.SetOrientationDegrees(rot)
        if ref in BACK_SIDE and fp.GetLayer() == pcbnew.F_Cu:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)

    pcbnew.SaveBoard(BOARD, board)

    # -- net classes (project file; SaveBoard has just rewritten it) -------
    with open(PROJECT) as fh:
        pro = json.load(fh)
    ns = pro["net_settings"]
    default = next(c for c in ns["classes"] if c["name"] == "Default")
    default.update(DEFAULT_CLASS)
    power = dict(default, name="Power", **POWER_CLASS)
    ns["classes"] = [default, power]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS]
    with open(PROJECT, "w") as fh:
        json.dump(pro, fh, indent=2)
        fh.write("\n")
    print(f"placed {len(P)} footprints, {len(HOLES)} holes, outline {BOARD_W}x{BOARD_H}mm, "
          f"panel shadow x:{PANEL['x']} y:{PANEL['y']} on User.Comments")


if __name__ == "__main__":
    main()
