#!/usr/bin/env python3
"""Antenna-strip track keepout and guard (pilink-a4u, pilink-kiw).

The U.FL antenna element sits ~1mm above the board's top edge, so no routed
copper may run along board x 54..106, y 0..3 (zones.py ANT_KO adds the
pour-only KO_ANT_F/B rule areas for the GND pours).

* route.py calls add_route_keepout() before the DSN export, so Freerouting
  gets the strip as a track/via keepout on both layers (same mechanism as
  sw_keepout.py), and remove_route_keepout() before saving.
* zones.py calls check_strip() on every run: any track or via in the strip
  other than the documented ALLOWED run is a hard failure (non-zero exit),
  not a silent no-op. This replaces the old position-matching reroute of
  GPIO25 / ESP32_HCI_TXD, which did nothing once Freerouting routed them
  differently.
"""
import sys

import pcbnew

MM = pcbnew.FromMM
O = 100.0            # keep in sync with place.py ORIGIN
STRIP = (54.0, 0.0, 106.0, 3.0)      # keep in sync with zones.py ANT_KO
# The guard checks only copper under the antenna element itself (board x
# 56.75..102.55) and ignores sub-0.05mm grazes of the strip's lower edge
# (router grid rounding: committed GND stubs/via touch y=3.0 by ~10um).
# Freerouting is given the full STRIP, margins included.
CHECK = (56.75, 0.0, 102.55, 2.95)
NAME = "KO_ANT_RT_"
# Documented exception: tracks on these nets, on these layers, may stay in
# the strip.
ALLOWED = {("+3V3", pcbnew.B_Cu)}


def _pt(x, y):
    return pcbnew.VECTOR2I(MM(O + x), MM(O + y))


def remove_route_keepout(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith(NAME):
            board.Remove(z)


def add_route_keepout(board):
    """Track + via keepout over the strip, F.Cu and B.Cu (Freerouting only)."""
    remove_route_keepout(board)
    x0, y0, x1, y1 = STRIP
    for layer, tag in ((pcbnew.F_Cu, "F"), (pcbnew.B_Cu, "B")):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetIsRuleArea(True)
        z.SetZoneName(NAME + tag)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(_pt(x, y))
        board.Add(z)


def strip_offenders(board):
    """Tracks/vias whose copper overlaps the strip, minus the ALLOWED run."""
    x0, y0, x1, y1 = CHECK
    box = pcbnew.BOX2I(_pt(x0, y0), pcbnew.VECTOR2I(MM(x1 - x0), MM(y1 - y0)))
    bad = []
    for t in board.GetTracks():
        if not t.GetBoundingBox().Intersects(box):
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            bad.append(t)
        elif (t.GetNetname(), t.GetLayer()) not in ALLOWED:
            bad.append(t)
    return bad


def check_strip(board):
    bad = strip_offenders(board)
    for t in bad:
        kind = "via" if t.Type() == pcbnew.PCB_VIA_T else "track"
        p = t.GetStart()
        print(f"ANTENNA STRIP VIOLATION: {kind} on {t.GetNetname()} "
              f"{t.GetLayerName()} at ({pcbnew.ToMM(p.x) - O:.3f}, "
              f"{pcbnew.ToMM(p.y) - O:.3f})", file=sys.stderr)
    if bad:
        sys.exit(f"{len(bad)} track/via item(s) in the antenna strip; re-run "
                 "route.py (it exports the strip as a keepout) or fix by hand")
    print("antenna strip clean (only the documented +3V3 B.Cu run, if any)")
