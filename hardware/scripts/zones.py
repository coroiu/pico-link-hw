#!/usr/bin/env python3
"""Add copper pours to the routed board (pilink-7el.12).

Usage (from hardware/):  python3 scripts/zones.py

Run after scripts/route.py. Idempotent: every zone, and every via this
script added earlier (they are locked, router vias are not), is removed
before being re-created.

  * GND pour on F.Cu and B.Cu over the whole board.
  * +3V3 heat-spreader pour around U1's tab (AP2114H-3.3, SOT-223; the tab
    is VOUT) on F.Cu, mirrored on B.Cu and stitched with a via grid, solid
    (no thermal-relief spokes) pad connection. See README "Power subsystem"
    (U1 thermal check) and "Known gaps" item 10 for the estimates this is
    sized against. Box re-centred on U1's new
    free-pocket location (board-local x~100,y~42) for the upright-form-
    factor placement (pilink-7el.12); the thermal math from pilink-mxx is
    unaffected by XY position.

    pilink-2yw: U1/C1/C2/C3 moved again (to board-local x~14,y~10, the
    column U201 vacated -- see place.py) to make room for U201's own
    relocation. SPREADER re-centred to follow, same relative box around U1
    as before (-7.5/-5 to +7.5/+5.5 from U1's anchor) -- otherwise this
    zone keeps pouring over its OLD empty spot and shows up as DRC
    "isolated_copper" (caught by drc_summary.py -v, not assumed).
"""
import os

import pcbnew

from preroute import PREROUTE_NETS
from antenna_reroute import check_strip as check_antenna_strip
from sw_keepout import add_sw_keepouts
from l101_keepout import add_l101_pour_keepout

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")

MM = pcbnew.FromMM
ORIGIN = (100.0, 100.0)      # keep in sync with place.py
BOARD_W, BOARD_H = 122.5, 50.0
# U1 heat spreader, board-relative mm (x0, y0, x1, y1) -- around U1 (14,10)
# and its bulk caps C1/C2/C3 (pilink-2yw relocation; was (92.5,37.0,107.5,
# 47.5) around the old U1 anchor (100,42), same relative box).
SPREADER = (6.5, 5.0, 21.5, 15.5)
VIA_PITCH = 1.5
VIA_D, VIA_DRILL = 0.6, 0.3
NUDGE_STEPS = 7              # via nudge search radius, in 0.1mm steps
VIA_KEEPOUT = 0.35           # via edge to any foreign copper / pad / hole


# pilink-a4u: no GND pour along the board's top edge under the U.FL antenna
# element. Element = face X 59.25..105.05 = board X 56.75..102.55 (face X =
# board X + 2.5; land 58.25..106.05 less 1.0mm assembly clearance each end),
# sitting ~1.0mm above the board's top edge (Q 54 vs board edge Q 53).
# Pour-only rule area on both layers, ~2.75mm X margin each side (the end
# margin keeps the pour corners ~2.5mm+ from the element). Depth 3.0mm:
# U201 GND pad 38 (top at y 2.74) and C201 pad 2 stay on pour that remains.
# route.py exports the strip to Freerouting as a track/via keepout and
# main() runs antenna_reroute.check_strip(), which fails if any track/via is
# left under the element; only the +3V3 B.Cu run at y~2.4 (x 86..109, under
# U201's own antenna end) is allowed. See README.
ANT_KO = (54.0, 0.0, 106.0, 3.0)


def add_antenna_keepout(board):
    x0, y0, x1, y1 = ANT_KO
    for layer, tag in ((pcbnew.F_Cu, "F"), (pcbnew.B_Cu, "B")):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetIsRuleArea(True)
        z.SetZoneName("KO_ANT_" + tag)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pt(x, y))
        board.Add(z)


def pt(x, y):
    return pcbnew.VECTOR2I(MM(ORIGIN[0] + x), MM(ORIGIN[1] + y))


def add_zone(board, net, layer, box, priority, solid=False, name=""):
    x0, y0, x1, y1 = box
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(board.FindNet(net).GetNetCode())
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.2))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid
                       else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25))
    z.SetThermalReliefSpokeWidth(MM(0.3))
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(pt(x, y))
    board.Add(z)
    return z


def via_ok(board, pos, net):
    """True if a via at pos clears every pad/track/via not on `net`,
    and every pad on any net (no via-in-pad)."""
    r = MM(VIA_D / 2)
    keep = MM(VIA_KEEPOUT)
    circle_bb = pcbnew.BOX2I(pcbnew.VECTOR2I(pos.x - r - keep, pos.y - r - keep),
                             pcbnew.VECTOR2I(2 * (r + keep), 2 * (r + keep)))
    for fp in board.GetFootprints():
        if not fp.GetBoundingBox().Intersects(circle_bb):
            continue
        for pad in fp.Pads():
            if pad.GetBoundingBox().Intersects(circle_bb):
                return False
    for t in board.GetTracks():
        if t.GetNetname() == net and t.Type() != pcbnew.PCB_VIA_T:
            continue
        if t.GetBoundingBox().Intersects(circle_bb):
            return False
    return True


def main():
    board = pcbnew.LoadBoard(BOARD)
    for z in list(board.Zones()):
        board.Remove(z)
    for t in list(board.GetTracks()):
        # keep scripts/preroute.py's locked vias (every PREROUTE_NETS net)
        if (t.Type() == pcbnew.PCB_VIA_T and t.IsLocked()
                and t.GetNetname() not in PREROUTE_NETS):
            board.Remove(t)

    # J401's end GND pads (A1/B12, A12/B1 share a land) sit against the
    # shell stakes and only have room for one thermal spoke; connect solid.
    # (The four shell-stake pads are all numbered "S1" in the footprint, so
    # matching on "S1" covers them all; the router's GND tracks to them
    # leave one spoke on some runs.)
    for pad in board.FindFootprintByReference("J401").Pads():
        if pad.GetNetname() == "GND" and pad.GetNumber() in (
                "A1", "A12", "B1", "B12", "S1"):
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J501 pad 5 (GND, pilink-dya footprint sync): the FC-05B40P21H20's
    # larger signal pads leave room for only one thermal spoke here too;
    # same fix as J401 above.
    for pad in board.FindFootprintByReference("J501").Pads():
        if pad.GetNetname() == "GND" and pad.GetNumber() in ("1", "5"):
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # pilink-xzs: the router leaves sub-5um stubs at U101 pins 66/67 (USB
    # D-/D+) where its grid snap misses the pad centre by 0.5um; drop them.
    for t in list(board.GetTracks()):
        if (t.GetClass() == "PCB_TRACK" and not t.IsLocked()
                and t.GetNetname() in ("USB_DP", "USB_DM")
                and t.GetLength() < 5000):   # 5um, in nm
            board.Remove(t)

    # U103 pad 4 (GND): after the pilink-xzs XIN pre-route change the router's
    # GND track to it leaves a single thermal spoke (DRC starved_thermal);
    # same solid-connect fix as the J401/J501 pads above.
    for pad in board.FindFootprintByReference("U103").Pads():
        if pad.GetNetname() == "GND" and pad.GetNumber() == "4":
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # C202 pad 2 (GND, B.Cu, pilink-4qc): the router's GND stub to it leaves a
    # single thermal spoke after the re-placement; same solid-connect fix.
    for pad in board.FindFootprintByReference("C202").Pads():
        if pad.GetNetname() == "GND" and pad.GetNumber() == "2":
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # C103 pad 2 (GND, VREG_VIN cap, pilink-2wq): the KO_L101_F pour cut-out
    # beside it leaves a single thermal spoke after the L101 re-placement;
    # same solid-connect fix as above.
    # C114 pad 2 (GND) likewise lost a spoke to the re-route.
    for ref in ("C103", "C114"):
        for pad in board.FindFootprintByReference(ref).Pads():
            if pad.GetNetname() == "GND" and pad.GetNumber() == "2":
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    check_antenna_strip(board)
    add_antenna_keepout(board)
    add_l101_pour_keepout(board)   # no F.Cu pour under L101 (pilink-2wq)
    add_sw_keepouts(board)   # Alps SKRTLAE010 no-copper areas (pilink-ge9)
    full = (0, 0, BOARD_W, BOARD_H)
    add_zone(board, "GND", pcbnew.F_Cu, full, 0, name="GND_F")
    add_zone(board, "GND", pcbnew.B_Cu, full, 0, name="GND_B")
    add_zone(board, "+3V3", pcbnew.F_Cu, SPREADER, 1, solid=True, name="U1_HEAT_F")
    add_zone(board, "+3V3", pcbnew.B_Cu, SPREADER, 1, solid=True, name="U1_HEAT_B")

    # pilink-xzs: the router's own tracks/pads block some nominal grid
    # points, which dropped the count 24 -> 13 after the pilink-rqd re-route.
    # Instead of skipping a blocked point, nudge it to the nearest legal spot
    # within NUDGE_STEPS x 0.1mm (nearest first) so the grid is kept.
    net = board.FindNet("+3V3")
    x0, y0, x1, y1 = SPREADER
    steps = sorted(((dx, dy) for dx in range(-NUDGE_STEPS, NUDGE_STEPS + 1)
                    for dy in range(-NUDGE_STEPS, NUDGE_STEPS + 1)),
                   key=lambda d: d[0] ** 2 + d[1] ** 2)
    n = 0
    y = y0 + 1.0
    while y <= y1 - 1.0:
        x = x0 + 1.0
        while x <= x1 - 1.0:
            for dx, dy in steps:
                nx, ny = x + dx * 0.1, y + dy * 0.1
                if not (x0 + 0.8 <= nx <= x1 - 0.8 and y0 + 0.8 <= ny <= y1 - 0.8):
                    continue
                pos = pt(nx, ny)
                if via_ok(board, pos, "+3V3"):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pos)
                    v.SetWidth(pcbnew.F_Cu, MM(VIA_D))
                    v.SetDrill(MM(VIA_DRILL))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    v.SetNet(net)
                    v.SetLocked(True)
                    board.Add(v)
                    n += 1
                    break
            x += VIA_PITCH
        y += VIA_PITCH
    print("+3V3 stitching vias:", n)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    for z in board.Zones():
        area = z.GetFilledArea() / 1e12
        print(f"zone {z.GetZoneName():10} {z.GetNetname():5} "
              f"{board.GetLayerName(z.GetLayer())}: {area:.0f} mm2 filled")
    print(f"{n} heat-spreader stitching vias")


if __name__ == "__main__":
    main()
