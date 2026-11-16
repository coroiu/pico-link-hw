"""Alps SKRTLAE010 "prohibited area of copper tracks" rule areas (pilink-ge9).

Shared by route.py (so Freerouting sees the keepouts) and zones.py (which
removes every zone, then calls this again). Not run on its own.

Source: Alps SKRT catalog, land-pattern drawing for the SKRTLAE010. The
hatched area is 2.0mm wide, centred on pad 2, 1.2mm tall, with its lower
edge flush with the MP pads' outer edge. In footprint-local coordinates
(origin = peg-row centre, +y toward the MP pads):
    x -1.0 .. +1.0,  y +0.3 .. +1.5.
It is on the component (mounting) layer: the switch's underside contacts
sit over it. Applied to F.Cu only, no tracks / vias / pours. B.Cu is the
far side of the 1.6mm board and is not covered by the drawing's note.
The corners go through the footprint's own transform, so a rotated or
flipped switch still gets the right area.
"""
import math

import pcbnew

MM = pcbnew.FromMM
REFS = ("SW101", "SW102")
X0, X1, Y0, Y1 = -1.0, 1.0, 0.3, 1.5
NAME = "KO_SKRT_"


def add_sw_keepouts(board):
    """Remove any earlier KO_SKRT_* rule areas and re-add one per switch."""
    for z in list(board.Zones()):
        if z.GetZoneName().startswith(NAME):
            board.Remove(z)
    for ref in REFS:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            continue
        layer = fp.GetLayer()
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetIsRuleArea(True)
        z.SetZoneName(NAME + ref)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)):
            if layer == pcbnew.B_Cu:
                x = -x
            a = math.radians(fp.GetOrientationDegrees())
            # KiCad angles are CCW on screen with y pointing down
            rx = x * math.cos(a) + y * math.sin(a)
            ry = -x * math.sin(a) + y * math.cos(a)
            c = fp.GetPosition()
            o.Append(c.x + MM(rx), c.y + MM(ry))
        board.Add(z)
