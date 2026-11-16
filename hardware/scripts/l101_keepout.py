"""L101 (VREG inductor) copper keepouts (pilink-2wq).

RP2350 datasheet 6.3.8.1: cut away copper under the inductor on the top
layer and keep the bottom layer as an unbroken ground plane under the
regulator. Shared by route.py and zones.py. Not run on its own.

* add_l101_route_keepout(): B.Cu track/via keepout over the L101 footprint
  plus F.Cu track/via keepouts over the body area between/beside the pads,
  exported to Freerouting by route.py (removed again before the board is
  saved). The pads themselves stay reachable from outside the body.
* add_l101_pour_keepout(): pour-only rule area (F.Cu), added by zones.py so
  GND_F does not fill under or between the L101 pads.
The rectangle is the footprint's body+pad extent plus MARGIN, taken through
the footprint transform so a rotated L101 still gets the right area.
"""
import math

import pcbnew

MM = pcbnew.FromMM
REF = "L101"
X0, X1, Y0, Y1 = -2.4, 2.4, -2.1, 2.1   # pads +/-2.375 x 1.25, body 4.4 x 4.2
MARGIN = 0.1
NAME_RT = "KO_L101_RT_B"
NAME_RT_F = "KO_L101_RT_F"
NAME_F = "KO_L101_F"


# F.Cu track keepout = body footprint minus the two pads (local coords):
# the centre strip between the pads and the four body side strips beside
# them. Tracks may still reach the pads from outside the body.
F_RECTS = [(-0.875, 0.875, -2.2, 2.2),
           (0.875, 2.2, 1.25, 2.2), (0.875, 2.2, -2.2, -1.25),
           (-2.2, -0.875, 1.25, 2.2), (-2.2, -0.875, -2.2, -1.25)]


def _rect(board, box=None):
    fp = board.FindFootprintByReference(REF)
    a = math.radians(fp.GetOrientationDegrees())
    c = fp.GetPosition()
    pts = []
    if box is None:
        bx0, bx1, by0, by1 = X0 - MARGIN, X1 + MARGIN, Y0 - MARGIN, Y1 + MARGIN
    else:
        bx0, bx1, by0, by1 = box
    for x, y in ((bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)):
        rx = x * math.cos(a) + y * math.sin(a)
        ry = -x * math.sin(a) + y * math.cos(a)
        pts.append((c.x + MM(rx), c.y + MM(ry)))
    return pts


def _add(board, name, layer, tracks_vias, pour, box=None):
    for z in list(board.Zones()):
        if z.GetZoneName() == name:
            board.Remove(z)
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks_vias)
    z.SetDoNotAllowVias(tracks_vias)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in _rect(board, box):
        o.Append(int(x), int(y))
    board.Add(z)


def add_l101_route_keepout(board):
    _add(board, NAME_RT, pcbnew.B_Cu, True, False)
    for i, box in enumerate(F_RECTS):
        _add(board, NAME_RT_F + str(i), pcbnew.F_Cu, True, False, box)


def remove_l101_route_keepout(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith("KO_L101_RT_"):
            board.Remove(z)


def add_l101_pour_keepout(board):
    _add(board, NAME_F, pcbnew.F_Cu, False, True)
