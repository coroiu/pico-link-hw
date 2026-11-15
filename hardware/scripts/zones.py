#!/usr/bin/env python3
"""Add copper pours to the routed board (pilink-7el.9).

Usage (from hardware/):  python3 scripts/zones.py

Run after scripts/route.py. Idempotent: every zone, and every via this
script added earlier (they are locked, router vias are not), is removed
before being re-created.

  * GND pour on F.Cu and B.Cu over the whole board.
  * +3V3 heat-spreader pour around U1's tab (AP2114H-3.3, SOT-223; the tab
    is VOUT) on F.Cu, mirrored on B.Cu and stitched with a via grid, solid
    (no thermal-relief spokes) pad connection. See README "PCB layout" for
    the thermal estimate this is sized against.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")

MM = pcbnew.FromMM
ORIGIN = (100.0, 60.0)       # keep in sync with place.py
BOARD_W, BOARD_H = 100.0, 55.0
# U1 heat spreader, board-relative mm (x0, y0, x1, y1)
SPREADER = (58.6, 0.6, 73.4, 19.6)
VIA_PITCH = 1.5
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_KEEPOUT = 0.35           # via edge to any foreign copper / pad / hole


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
        if t.Type() == pcbnew.PCB_VIA_T and t.IsLocked():
            board.Remove(t)

    # J401's end GND pads (A1/B12, A12/B1 share a land) sit against the
    # shell stakes and only have room for one thermal spoke; connect solid.
    for pad in board.FindFootprintByReference("J401").Pads():
        if pad.GetNetname() == "GND" and pad.GetNumber() in ("A1", "A12", "B1", "B12"):
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    full = (0, 0, BOARD_W, BOARD_H)
    add_zone(board, "GND", pcbnew.F_Cu, full, 0, name="GND_F")
    add_zone(board, "GND", pcbnew.B_Cu, full, 0, name="GND_B")
    add_zone(board, "+3V3", pcbnew.F_Cu, SPREADER, 1, solid=True, name="U1_HEAT_F")
    add_zone(board, "+3V3", pcbnew.B_Cu, SPREADER, 1, solid=True, name="U1_HEAT_B")

    net = board.FindNet("+3V3")
    x0, y0, x1, y1 = SPREADER
    n = 0
    y = y0 + 1.0
    while y <= y1 - 1.0:
        x = x0 + 1.0
        while x <= x1 - 1.0:
            pos = pt(x, y)
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
            x += VIA_PITCH
        y += VIA_PITCH

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    for z in board.Zones():
        area = z.GetFilledArea() / 1e12
        print(f"zone {z.GetZoneName():10} {z.GetNetname():5} "
              f"{board.GetLayerName(z.GetLayer())}: {area:.0f} mm2 filled")
    print(f"{n} heat-spreader stitching vias")


if __name__ == "__main__":
    main()
