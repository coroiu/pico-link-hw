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
  * Before pouring (pilink-audit-a, PR #102): split locked pre-route
    segments where the router ends a track on them (split_at_t_joins) and
    drop locked tails the router made redundant (prune_dangling_locked).
  * After pouring: GND stitching vias (stitch_gnd) in every GND polygon
    that is not its layer's main plane, along both sides of the fast nets
    (USB, QSPI, display SPI) and on a STITCH_PITCH grid wherever both
    layers have GND; any GND island still not joined to the main ground
    gets a track to it where one fits (gnd_repair.py); then a per-polygon
    report (gnd_report) and the ground-plane gate (gnd_gate, pilink-r1h),
    which fails the run if the GND copper is not one connected net, any
    GND fragment has no via, a capacitor's GND pad has no GND via within
    1mm, or (gnd_paths.gate, pilink-93a) the regulator's ground or a
    nearby decoupler reaches U101's exposed pad only by a long copper path.

pilink-r1h: GND is poured, not routed. GND is no longer routed by
Freerouting; every F.Cu GND pad has its own locked via (gnd_fanout.py,
laid by preroute.py), and these pours connect them. U1's +3V3 heat
spreader is notched so U1's GND pin and C2/C3's GND pads sit in the GND
pour (they were in no pour at all). plane_keepout.add_pour_keepouts() keeps
the GND pour off the VREG ground island and out from under U101.
"""
import math
import os
import sys

import pcbnew

from preroute import PREROUTE_NETS, DP_MCU, DM_MCU
from antenna_reroute import check_strip as check_antenna_strip
from sw_keepout import add_sw_keepouts
from l101_keepout import add_l101_pour_keepout
from plane_keepout import add_pour_keepouts
from gnd_fanout import GND_STITCH_D, GND_STITCH_DRILL
from gnd_repair import repair as repair_gnd, remove_repairs
import gnd_paths

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")

MM = pcbnew.FromMM
ORIGIN = (100.0, 100.0)      # keep in sync with place.py
BOARD_W, BOARD_H = 122.5, 50.0
# U1 heat spreader, board-relative mm (x0, y0, x1, y1) -- around U1 (14,10)
# and its bulk caps C1/C2/C3 (pilink-2yw relocation; was (92.5,37.0,107.5,
# 47.5) around the old U1 anchor (100,42), same relative box).
SPREADER = (6.5, 5.0, 21.5, 15.5)
# pilink-r1h: the spreader (priority over GND) used to swallow U1's GND pin
# and C3's GND pad, leaving them in no pour. Its outline is the SPREADER box
# less three notches, open to the box edge so the GND pour flows in: U1
# pin 1 (top-left), C3's GND pad (east; place.py turns C3 so that pad faces
# east) and C2's GND pad (bottom edge). Same outline on both layers, so the
# GND fan-out vias land on the B.Cu plane.
SPREADER_NOTCHES = [(6.5, 5.0, 12.25, 8.9),     # U1.1 GND (10.85, 7.7)
                    (19.95, 8.6, 21.5, 11.4),   # C3.1 GND (20.48, 10.0)
                    (11.9, 14.2, 14.2, 15.5)]   # C2.1 GND (13.05, 15.5)
VIA_PITCH = 1.5
VIA_D, VIA_DRILL = 0.6, 0.3
NUDGE_STEPS = 7              # via nudge search radius, in 0.1mm steps
VIA_KEEPOUT = 0.35           # via edge to any foreign copper / pad / hole
# GND stitching (stitch_gnd): grid pitch over the whole board, and the
# spacing of the vias along each side of a fast net
STITCH_PITCH = 4.0
FAST_PITCH = 2.0
FAST_NETS = (["USB_DP", "USB_DM", "/RP2350B + Memory/USB_DP_MCU",
              "/RP2350B + Memory/USB_DM_MCU", "/RP2350B + Memory/PSRAM_CS"]
             + ["/RP2350B + Memory/QSPI_" + n for n in ("SCLK", "SD0", "SD1", "SD2", "SD3", "SS")]
             + ["GPIO29", "GPIO30", "GPIO31", "GPIO32", "GPIO33"])


def spreader_outline():
    """The SPREADER box minus SPREADER_NOTCHES, as a SHAPE_POLY_SET."""
    def rect(x0, y0, x1, y1):
        sp = pcbnew.SHAPE_POLY_SET()
        sp.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            sp.Append(pt(x, y))
        return sp
    out = rect(*SPREADER)
    for n in SPREADER_NOTCHES:
        out.BooleanSubtract(rect(*n))
    return out


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


def add_zone(board, net, layer, box, priority, solid=False, name="", outline=None):
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
    if outline is not None:
        # copy point by point: ZONE.SetOutline() takes ownership of the
        # pointer, and a Python-owned SHAPE_POLY_SET is freed under it
        # (segfault in the zone filler)
        o = z.Outline()
        for i in range(outline.OutlineCount()):
            src = outline.Outline(i)
            o.NewOutline()
            for j in range(src.PointCount()):
                o.Append(src.CPoint(j))
            for h in range(outline.HoleCount(i)):
                ho = outline.Hole(i, h)
                o.NewHole()
                for j in range(ho.PointCount()):
                    o.Append(ho.CPoint(j), -1, -1)
    else:
        o = z.Outline()
        o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pt(x, y))
    board.Add(z)
    return z


def add_pours(board):
    """The pour keepouts, both GND pours and U1's +3V3 heat spreader (not
    filled). Returns the spreader outline. Also used by route.py to check
    the GND connectivity of a fresh routing before accepting it."""
    add_antenna_keepout(board)
    add_l101_pour_keepout(board)   # no F.Cu pour under L101 (pilink-2wq)
    add_pour_keepouts(board)       # VREG ground island, under U101 (pilink-2x7)
    add_sw_keepouts(board)   # Alps SKRTLAE010 no-copper areas (pilink-ge9)
    full = (0, 0, BOARD_W, BOARD_H)
    add_zone(board, "GND", pcbnew.F_Cu, full, 0, name="GND_F")
    add_zone(board, "GND", pcbnew.B_Cu, full, 0, name="GND_B")
    spreader = spreader_outline()
    add_zone(board, "+3V3", pcbnew.F_Cu, SPREADER, 1, solid=True, name="U1_HEAT_F",
             outline=spreader)
    add_zone(board, "+3V3", pcbnew.B_Cu, SPREADER, 1, solid=True, name="U1_HEAT_B",
             outline=spreader)
    return spreader


def gnd_components(board):
    """GND copper split into connected components, from the filled pours,
    GND tracks, vias and pads. Returns (main, strays): main is the component
    holding the largest GND pour polygon, as {layer: [SHAPE_POLY_SET]};
    strays is [(label, {layer: [SHAPE_POLY_SET]})] for every other one.
    Freerouting does not see GND (route.py), so nothing else stops it from
    boxing a fan-out via or a B.Cu GND pad into a pocket of signal tracks."""
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def uni(a, c):
        par[find(a)] = find(c)

    polys = []
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND":
            continue
        for L in (F, B):
            if z.IsOnLayer(L):
                ps = z.GetFilledPolysList(L)
                for i in range(ps.OutlineCount()):
                    k = ("poly", L, z.GetZoneName(), i)
                    polys.append((k, L, pcbnew.SHAPE_POLY_SET(ps.UnitSet(i))))
                    find(k)
    shapes = []      # (key, layers, polyset, label)
    for t in board.GetTracks():
        if t.GetNetname() != "GND":
            continue
        k = ("item", t.m_Uuid.AsString())
        sp = pcbnew.SHAPE_POLY_SET()
        if t.Type() == pcbnew.PCB_VIA_T:
            Ls = [F, B]
            t.TransformShapeToPolygon(sp, F, 0, 5000, pcbnew.ERROR_INSIDE)
            label = "via (%.2f, %.2f)" % (pcbnew.ToMM(t.GetX()) - ORIGIN[0],
                                          pcbnew.ToMM(t.GetY()) - ORIGIN[1])
        else:
            Ls = [t.GetLayer()]
            t.TransformShapeToPolygon(sp, t.GetLayer(), 0, 5000, pcbnew.ERROR_INSIDE)
            label = None
        shapes.append((k, Ls, sp, label))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "GND":
                continue
            Ls = [L for L in (F, B) if p.IsOnLayer(L)]
            if not Ls:
                continue
            sp = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(sp, Ls[0], 0, 5000, pcbnew.ERROR_INSIDE)
            shapes.append((("item", p.m_Uuid.AsString()), Ls, sp,
                           f"{fp.GetReference()}.{p.GetNumber()}"))
    for k, Ls, sp, _ in shapes:
        find(k)

    def touch(a, c):
        if not a.BBox().Intersects(c.BBox()):
            return False
        x = pcbnew.SHAPE_POLY_SET(a)
        x.BooleanIntersection(c)
        return x.OutlineCount() > 0

    for k, Ls, sp, _ in shapes:
        for pk, L, ps in polys:
            if L in Ls and touch(sp, ps):
                uni(k, pk)
    for i, (k, Ls, sp, _) in enumerate(shapes):
        for k2, Ls2, sp2, _ in shapes[i + 1:]:
            if set(Ls) & set(Ls2) and touch(sp, sp2):
                uni(k, k2)
    if not polys:
        raise SystemExit("zones.py: no GND pour to check")
    main = find(max(polys, key=lambda p: p[2].Area())[0])
    groups = {}
    for k, Ls, sp, label in shapes:
        g = groups.setdefault(find(k), {"labels": [], F: [], B: []})
        g["labels"].append(label)
        for L in Ls:
            g[L].append(sp)
    for pk, L, ps in polys:
        g = groups.setdefault(find(pk), {"labels": [], F: [], B: []})
        g[L].append(ps)
    strays = []
    for r, g in groups.items():
        if r == main:
            continue
        named = [s for s in g["labels"] if s]
        area = sum(ps.Area() for pk, L, ps in polys if find(pk) == r) / 1e12
        label = (f"GND island ({area:.1f} mm2 of pour: "
                 + (", ".join(named[:8]) or "no pads") + ")")
        strays.append((label, {F: g[F], B: g[B]}))
    return {F: groups[main][F], B: groups[main][B]}, strays


def pour_and_join(board, rounds=3):
    """Fill, stitch (stitch_gnd), then join any GND island to the main
    ground with a track (gnd_repair), refilling after each round. Returns
    the repair log lines."""
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    stitch_gnd(board)
    log = []
    for _ in range(rounds):
        comps = gnd_components(board)
        if not comps[1]:
            break
        log += repair_gnd(board, comps)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if log:
        # a repair changes the fills; stitch again so every fragment the
        # new fill leaves still gets its via (stitch_gnd keeps its spacing
        # to the vias already there)
        stitch_gnd(board)
    return log


def gnd_islands(board):
    """One line per GND island not joined to the main ground
    (gnd_components)."""
    return [label + " not joined to the main ground" for label, _ in gnd_components(board)[1]]


def split_at_t_joins(board):
    """Freerouting sometimes ends a track on the middle of a locked
    pre-route segment (a T-join). The copper touches, but KiCad only joins
    track ends, so DRC reports `track_dangling` there (pilink-audit-a: an
    ESP32_EN stub onto the C203 -> R201 link). Split the locked segment at
    that point so both tracks share an end. Every T-join on a segment is
    handled (all split points, in order along the segment). The split point
    is the router's own track end, which lies within 5um of the locked
    centreline: moving router ends onto the exact projection instead was
    tried and broke connectivity wherever such an end also met a via or
    another track, so a kink of at most 5um is accepted."""
    tol = MM(0.005)
    tracks = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    ends = {}
    for t in tracks:
        if not t.IsLocked():
            for p in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetNetCode(), t.GetLayer()), set()).add((p.x, p.y))
    n = 0
    for t in tracks:
        if not t.IsLocked():
            continue
        # copies: GetStart()/GetEnd() return references that SetEnd() below
        # would change under us
        a, e = pcbnew.VECTOR2I(t.GetStart()), pcbnew.VECTOR2I(t.GetEnd())
        d = e - a
        L2 = d.x * d.x + d.y * d.y
        if L2 == 0:
            continue
        cuts = []
        for px, py in ends.get((t.GetNetCode(), t.GetLayer()), ()):
            p = pcbnew.VECTOR2I(px, py)
            if p == a or p == e:
                continue
            u = ((p.x - a.x) * d.x + (p.y - a.y) * d.y) / L2
            if not 0 < u < 1:
                continue
            q = pcbnew.VECTOR2I(int(round(a.x + u * d.x)), int(round(a.y + u * d.y)))
            if (q - p).EuclideanNorm() > tol:
                continue
            cuts.append((u, p))
        if not cuts:
            continue
        pts = [a] + [p for _, p in sorted(cuts, key=lambda c: c[0])] + [e]
        t.SetEnd(pts[1])
        for s0, s1 in zip(pts[1:], pts[2:]):
            if s0 == s1:
                continue
            t2 = pcbnew.PCB_TRACK(board)
            t2.SetStart(s0)
            t2.SetEnd(s1)
            t2.SetWidth(t.GetWidth())
            t2.SetLayer(t.GetLayer())
            t2.SetNetCode(t.GetNetCode())
            t2.SetLocked(True)
            board.Add(t2)
        n += len(cuts)
    if n:
        print(f"split locked segments at {n} router T-join(s)")


def prune_dangling_locked(board):
    """Remove pre-routed (locked) tails the router made redundant: when
    Freerouting picks up a locked stub part-way along (a T-join, split by
    split_at_t_joins) the rest of the stub, and a via at its end, are left
    dangling (seen on the CC2 escape from J401). Only nets without a pour
    are touched: on GND/+3V3 a locked via can be joined by the pour alone."""
    skip = {"GND", "+3V3"}
    removed = 0
    nets = set()
    while True:
        tracks = list(board.GetTracks())
        pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
        gone = []
        for t in tracks:
            if not t.IsLocked() or t.GetNetname() in skip:
                continue
            net = t.GetNetCode()
            if t.Type() == pcbnew.PCB_VIA_T:
                pos = t.GetPosition()
                rv = t.GetWidth(pcbnew.F_Cu) // 2
                layers = set()
                for o in tracks:
                    # pilink-r1h: anywhere on the track counts (KiCad joins
                    # a via that a track merely passes over), not only its ends
                    if (o is not t and o.Type() == pcbnew.PCB_TRACE_T and o.GetNetCode() == net
                            and o.HitTest(pos, rv)):
                        layers.add(o.GetLayer())
                if any(p.GetNetCode() == net and p.HitTest(pos) for p in pads):
                    continue
                if len(layers) <= 1:
                    gone.append(t)
                continue
            for end in (t.GetStart(), t.GetEnd()):
                ok = any(p.GetNetCode() == net and p.IsOnLayer(t.GetLayer()) and p.HitTest(end)
                         for p in pads)
                if not ok:
                    for o in tracks:
                        if o is t or o.GetNetCode() != net:
                            continue
                        if o.Type() == pcbnew.PCB_VIA_T:
                            if (o.GetPosition() - end).EuclideanNorm() <= o.GetWidth(pcbnew.F_Cu) // 2:
                                ok = True
                                break
                        # an end anywhere on another same-net track joins it,
                        # as in KiCad's connectivity (router T-joins that
                        # split_at_t_joins did not split exactly, pilink-r1h)
                        elif o.GetLayer() == t.GetLayer() and o.HitTest(end, 0):
                            ok = True
                            break
                if not ok:
                    gone.append(t)
                    break
        if not gone:
            break
        for t in gone:
            nets.add(t.GetNetname())
            board.Remove(t)
        removed += len(gone)
    if removed:
        print(f"pruned {removed} dangling pre-route item(s) on: {', '.join(sorted(nets))}")


def via_ok(board, pos, net, r=None, near_own_pads=False, keepout=None):
    """True if a via at pos clears every pad/track/via not on `net`,
    and every pad on any net (no via-in-pad). With near_own_pads, pads on
    `net` itself only need 0.25mm (room for a solder-mask dam)."""
    r = MM(VIA_D / 2) if r is None else r
    keep = MM(VIA_KEEPOUT if keepout is None else keepout)
    circle_bb = pcbnew.BOX2I(pcbnew.VECTOR2I(pos.x - r - keep, pos.y - r - keep),
                             pcbnew.VECTOR2I(2 * (r + keep), 2 * (r + keep)))
    tight = MM(0.25)
    tight_bb = pcbnew.BOX2I(pcbnew.VECTOR2I(pos.x - r - tight, pos.y - r - tight),
                            pcbnew.VECTOR2I(2 * (r + tight), 2 * (r + tight)))
    for fp in board.GetFootprints():
        if not fp.GetBoundingBox().Intersects(circle_bb):
            continue
        for pad in fp.Pads():
            bb = (tight_bb if near_own_pads and pad.GetNetname() == net
                  and pad.GetDrillSize().x == 0 else circle_bb)
            if pad.GetBoundingBox().Intersects(bb):
                return False
    for t in board.GetTracks():
        if t.GetNetname() == net and t.Type() != pcbnew.PCB_VIA_T:
            continue
        if not t.GetBoundingBox().Intersects(circle_bb):
            continue
        if t.Type() == pcbnew.PCB_TRACE_T:
            # a straight track: its real distance, not its bounding box (a
            # long diagonal's box covers a whole triangle of free pour,
            # which left B.Cu slivers with no legal via spot, pilink-93a)
            a, c = t.GetStart(), t.GetEnd()
            dx, dy = c.x - a.x, c.y - a.y
            L2 = dx * dx + dy * dy
            u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((pos.x - a.x) * dx + (pos.y - a.y) * dy) / L2))
            d = math.hypot(pos.x - (a.x + u * dx), pos.y - (a.y + u * dy))
            if d < r + keep + t.GetWidth() / 2:
                return False
            continue
        return False
    return True


def main():
    board = pcbnew.LoadBoard(BOARD)
    for z in list(board.Zones()):
        board.Remove(z)
    remove_repairs(board)      # this script's own GND island joins (gnd_repair)
    sx0, sy0, sx1, sy1 = SPREADER
    in_spreader = lambda p: (sx0 <= pcbnew.ToMM(p.x) - ORIGIN[0] <= sx1
                             and sy0 <= pcbnew.ToMM(p.y) - ORIGIN[1] <= sy1)
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T or not t.IsLocked():
            continue
        # keep scripts/preroute.py's locked vias (every PREROUTE_NETS net),
        # except this script's own +3V3 stitching vias: +3V3 is a pre-routed
        # net too since pilink-yt5 (the trunk), and preroute.py never puts a
        # via inside the SPREADER box.
        if (t.GetNetname() not in PREROUTE_NETS
                or (t.GetNetname() == "+3V3" and in_spreader(t.GetPosition()))
                or (t.GetNetname() == "GND" and t.GetDrillValue() == MM(GND_STITCH_DRILL))):
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
    # (pilink-8rz: those pins are on the MCU-side nets of R106/R107 now.)
    for t in list(board.GetTracks()):
        if (t.GetClass() == "PCB_TRACK" and not t.IsLocked()
                and t.GetNetname() in ("USB_DP", "USB_DM", DP_MCU, DM_MCU)
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

    # C114 and C111 pad 2 (GND) lost a spoke to re-routes; same solid-connect
    # fix. (C103 used to be here too; since pilink-2x7 its GND pad is on the
    # VREG ground island, which the pour does not reach.)
    for ref in ("C114", "C111"):
        for pad in board.FindFootprintByReference(ref).Pads():
            if pad.GetNetname() == "GND" and pad.GetNumber() == "2":
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    split_at_t_joins(board)
    prune_dangling_locked(board)
    check_antenna_strip(board)
    spreader = add_pours(board)

    # pilink-xzs: the router's own tracks/pads block some nominal grid
    # points, which dropped the count 24 -> 13 after the pilink-rqd re-route.
    # Instead of skipping a blocked point, nudge it to the nearest legal spot
    # within NUDGE_STEPS x 0.1mm (nearest first) so the grid is kept.
    net = board.FindNet("+3V3")
    x0, y0, x1, y1 = SPREADER
    steps = sorted(((dx, dy) for dx in range(-NUDGE_STEPS, NUDGE_STEPS + 1)
                    for dy in range(-NUDGE_STEPS, NUDGE_STEPS + 1)),
                   key=lambda d: d[0] ** 2 + d[1] ** 2)
    # distance to the notched outline's edge (SHAPE_POLY_SET.SquaredDistance
    # with aOutlineOnly is unsupported in KiCad 10 and returns 0)
    chain = spreader.Outline(0)
    edges = [chain.CSegment(i) for i in range(chain.SegmentCount())]
    edge_dist2 = lambda p: min(e.SquaredDistance(p) for e in edges)
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
                if not spreader.Contains(pos) or edge_dist2(pos) < MM(0.8) ** 2:
                    continue      # in a GND notch, or too close to its edge
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

    for line in pour_and_join(board):
        print(line)
    pcbnew.SaveBoard(BOARD, board)
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        area = z.GetFilledArea() / 1e12
        print(f"zone {z.GetZoneName():10} {z.GetNetname():5} "
              f"{board.GetLayerName(z.GetLayer())}: {area:.0f} mm2 filled")
    print(f"{n} heat-spreader stitching vias")
    for line in gnd_report(board):
        print(line)
    problems = gnd_gate(board)
    for p in problems:
        print("GND GATE:", p, file=sys.stderr)
    if problems:
        sys.exit(f"{len(problems)} ground-plane gate failure(s); see above")
    print("ground-plane gate passed")


def gnd_polys(board):
    out = {}
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetZoneName() in ("GND_F", "GND_B"):
            out[z.GetZoneName()] = z.GetFilledPolysList(z.GetLayer())
    return out["GND_F"], out["GND_B"]


def gnd_drills(board):
    """Positions of everything that joins GND_F to GND_B: GND vias and
    plated through-hole GND pads."""
    pts = [t.GetPosition() for t in board.GetTracks()
           if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    pts += [p.GetPosition() for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    return pts


def gnd_report(board):
    """One line per GND pour polygon: area and the vias / PTH pads in it.
    A polygon with 0 of both reaches the other layer only through traces."""
    fpol, bpol = gnd_polys(board)
    drills = gnd_drills(board)
    lines = []
    for name, ps in (("GND_F", fpol), ("GND_B", bpol)):
        rows = []
        for i in range(ps.OutlineCount()):
            sub = pcbnew.SHAPE_POLY_SET(ps.UnitSet(i))
            area = sub.Area() / 1e12
            k = sum(1 for p in drills if ps.Contains(p, i))
            rows.append((area, k))
        rows.sort(reverse=True)
        unstitched = sum(1 for a, k in rows if k == 0)
        lines.append(f"{name}: {len(rows)} polygons, largest {rows[0][0]:.0f} mm2, "
                     f"{unstitched} with no GND via/PTH")
        lines.append("  " + ", ".join(f"{a:.0f}mm2/{k}" for a, k in rows))
    return lines


def stitch_gnd(board):
    """GND stitching vias (all locked, GND_STITCH_D, so a re-run finds and
    removes them):

    1. Fragments (PR #102 review): every GND polygon other than each
       layer's main plane gets at least one via, and one per 40 mm^2, where
       it overlaps GND on the other layer (one as close as possible to each
       GND SMD pad if it had none, then farthest-first, >= 3mm apart).
    2. Fast nets (pilink-r1h): along both sides of every FAST_NETS track,
       one via every FAST_PITCH mm where both layers have GND, so the return
       current under/beside those traces has a nearby path between layers.
    3. Grid (pilink-r1h): one via per STITCH_PITCH grid point (nudged up to
       ~1mm) wherever both layers have GND, so F.Cu pour islands between
       signals are tied to the B.Cu plane all over the board.
    Each pass refills. A spot needs both fills under the whole via (plus
    0.1mm), no via keepout or the antenna strip, VIA_KEEPOUT/0.2mm to
    foreign copper, and 1.5mm to any other GND via (2.5mm for the grid)."""
    r_in = MM(GND_STITCH_D / 2 + 0.1)
    ring = [pcbnew.VECTOR2I(0, 0)] + [
        pcbnew.VECTOR2I(int(r_in * math.cos(a * math.pi / 4)),
                        int(r_in * math.sin(a * math.pi / 4))) for a in range(8)]
    net = board.FindNet("GND")
    counts = {"fragment": 0, "fast-net": 0, "grid": 0}

    def add_via(p):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(p)
        v.SetWidth(pcbnew.F_Cu, MM(GND_STITCH_D))
        v.SetDrill(MM(GND_STITCH_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net)
        v.SetLocked(True)
        board.Add(v)

    # keep stitching vias out of via keepouts (SKRTLAE010 areas) and out of
    # the antenna strip (antenna_reroute.check_strip allows no vias there)
    no_via = [z.Outline() for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    ax0, ay0, ax1, ay1 = ANT_KO
    strip = pcbnew.SHAPE_POLY_SET()
    strip.NewOutline()
    for x, y in ((ax0, ay0), (ax1, ay0), (ax1, ay1 + 0.5), (ax0, ay1 + 0.5)):
        strip.Append(pt(x, y))
    no_via.append(strip)

    def gnd_vias():
        return [t.GetPosition() for t in board.GetTracks()
                if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]

    def spot_ok(p, fpol, bpol, near, spacing):
        if not all(fpol.Contains(p + o) and bpol.Contains(p + o) for o in ring):
            return False
        if any(k.Contains(p + o) for k in no_via for o in ring):
            return False
        if any((p - q).EuclideanNorm() < MM(spacing) for q in near):
            return False
        return via_ok(board, p, "GND", MM(GND_STITCH_D / 2), near_own_pads=True, keepout=0.2)

    # 1. fragments
    for _ in range(3):
        fpol, bpol = gnd_polys(board)
        drills = gnd_drills(board)
        new = []
        for this, other, layer in ((fpol, bpol, pcbnew.F_Cu), (bpol, fpol, pcbnew.B_Cu)):
            mine = max(range(this.OutlineCount()),
                       key=lambda j: pcbnew.SHAPE_POLY_SET(this.UnitSet(j)).Area())
            for i in range(this.OutlineCount()):
                if i == mine:
                    continue      # the main plane: stitched by the routing itself
                sub = pcbnew.SHAPE_POLY_SET(this.UnitSet(i))
                area = sub.Area() / 1e12
                have = [p for p in drills if this.Contains(p, i)]
                want = max(1, int(area / 40))
                if len(have) >= want:
                    continue
                bb = sub.BBox()
                cands = []
                step = MM(0.5)
                for x in range(bb.GetLeft(), bb.GetRight(), step):
                    for y in range(bb.GetTop(), bb.GetBottom(), step):
                        p = pcbnew.VECTOR2I(x, y)
                        if not all(this.Contains(p + o, i) and other.Contains(p + o) for o in ring):
                            continue
                        if any(k.Contains(p + o) for k in no_via for o in ring):
                            continue
                        if via_ok(board, p, "GND", MM(GND_STITCH_D / 2), near_own_pads=True, keepout=0.2):
                            cands.append(p)
                cands = [c for c in cands if all((c - q).EuclideanNorm() >= MM(1.5) for q in new)]
                if not cands:
                    continue
                pick = []
                if not have:
                    pads = [pd.GetPosition() for fp in board.GetFootprints() for pd in fp.Pads()
                            if pd.GetNetname() == "GND" and pd.IsOnLayer(layer)
                            and this.Contains(pd.GetPosition(), i)]
                    for pp in pads:
                        c = min(cands, key=lambda c: (c - pp).EuclideanNorm())
                        if all((c - q).EuclideanNorm() >= MM(1.0) for q in pick):
                            pick.append(c)
                    if not pick:
                        pick.append(cands[len(cands) // 2])
                while len(have) + len(pick) < want:
                    near = have + pick
                    far = [c for c in cands
                           if all((c - q).EuclideanNorm() >= MM(3.0) for q in near)]
                    if not far:
                        break
                    pick.append(max(far, key=lambda c: min((c - q).EuclideanNorm() for q in near)))
                new += pick
        if not new:
            break
        for p in new:
            add_via(p)
        counts["fragment"] += len(new)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # 2. both sides of the fast nets
    fpol, bpol = gnd_polys(board)
    near = gnd_vias()
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() not in FAST_NETS:
            continue
        a, b = t.GetStart(), t.GetEnd()
        L = (b - a).EuclideanNorm()
        if L < MM(0.5):
            continue
        ux, uy = (b.x - a.x) / L, (b.y - a.y) / L
        k = max(1, int(L / MM(FAST_PITCH)))
        for i in range(k):
            f = (i + 0.5) / k
            cx, cy = a.x + (b.x - a.x) * f, a.y + (b.y - a.y) * f
            for side in (1, -1):
                for off in (0.8, 1.0, 1.25, 1.5):
                    d = t.GetWidth() / 2 + MM(off)
                    p = pcbnew.VECTOR2I(int(cx - uy * d * side), int(cy + ux * d * side))
                    if spot_ok(p, fpol, bpol, near, 1.5):
                        add_via(p)
                        near.append(p)
                        counts["fast-net"] += 1
                        break
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # 3. grid
    fpol, bpol = gnd_polys(board)
    near = gnd_vias()
    steps = sorted(((dx, dy) for dx in range(-5, 6) for dy in range(-5, 6)),
                   key=lambda d: d[0] ** 2 + d[1] ** 2)
    y = STITCH_PITCH / 2
    while y < BOARD_H:
        x = STITCH_PITCH / 2
        while x < BOARD_W:
            for dx, dy in steps:
                p = pt(x + dx * 0.2, y + dy * 0.2)
                if spot_ok(p, fpol, bpol, near, 2.5):
                    add_via(p)
                    near.append(p)
                    counts["grid"] += 1
                    break
            x += STITCH_PITCH
        y += STITCH_PITCH
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("GND stitching vias: " + ", ".join(f"{v} {k}" for k, v in counts.items()))


# pilink-r1h gate. The VREG ground island (C103/C104) shares its two vias by
# design (RP2350 DS 6.3.8.1: one connection point); the gate still finds
# them within 1mm of both pads.
GATE_VIA_DIST = 1.0          # via copper edge to capacitor GND pad edge
GATE_MIN_FRAGMENT = 1.0      # mm^2; smaller fill slivers are ignored


def gnd_gate(board):
    """Ground-plane checks; returns a list of problems (empty = pass).
      * Every B.Cu GND polygon but the largest is under GATE_MIN_FRAGMENT
        mm^2 or has a GND via / PTH pad in it. (B.Cu still carries signals
        and is cut into several polygons; this only checks that each one
        reaches F.Cu through a via.)
      * Every F.Cu GND polygon of GATE_MIN_FRAGMENT mm^2 or more has a GND
        via or PTH pad in it (so it reaches the plane through a via, not a
        trace).
      * Every capacitor's F.Cu GND pad has a GND via within GATE_VIA_DIST.
      * U1 pin 1 (LDO GND) touches the F.Cu GND pour.
      * All GND copper is one connected ground (gnd_islands).
      * The VREG ground (PGND pin, C103/C104/C105) and the decouplers
        beside the VREG block reach U101's exposed pad along copper within
        gnd_paths' limits (gnd_paths.gate)."""
    problems = list(gnd_islands(board))
    fpol, bpol = gnd_polys(board)
    drills = gnd_drills(board)
    for name, ps in (("GND_B", bpol), ("GND_F", fpol)):
        areas = [pcbnew.SHAPE_POLY_SET(ps.UnitSet(i)).Area() / 1e12
                 for i in range(ps.OutlineCount())]
        main = max(range(len(areas)), key=lambda i: areas[i])
        for i, a in enumerate(areas):
            if i == main or a < GATE_MIN_FRAGMENT:
                continue
            if not any(ps.Contains(p, i) for p in drills):
                bb = ps.UnitSet(i).BBox()
                problems.append(f"{name} polygon of {a:.1f} mm2 at "
                                f"({pcbnew.ToMM(bb.Centre().x) - ORIGIN[0]:.1f}, "
                                f"{pcbnew.ToMM(bb.Centre().y) - ORIGIN[1]:.1f}) has no GND via")
    vias = [t for t in board.GetTracks()
            if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    for fp in board.GetFootprints():
        if not fp.GetReference().startswith("C"):
            continue
        for p in fp.Pads():
            if p.GetNetname() != "GND" or not p.IsOnLayer(pcbnew.F_Cu) \
                    or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            sp = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(sp, pcbnew.F_Cu, 0, 5000, pcbnew.ERROR_INSIDE)
            best = min((math.sqrt(sp.SquaredDistance(v.GetPosition())) - v.GetWidth(pcbnew.F_Cu) / 2
                        for v in vias), default=1e12)
            if best > MM(GATE_VIA_DIST):
                problems.append(f"{fp.GetReference()}.{p.GetNumber()}: nearest GND via "
                                f"{max(best, 0) / 1e6:.2f}mm from the pad (> {GATE_VIA_DIST}mm)")
    u1 = board.FindFootprintByReference("U1").FindPadByNumber("1")
    sp = pcbnew.SHAPE_POLY_SET()
    u1.TransformShapeToPolygon(sp, pcbnew.F_Cu, MM(0.3), 5000, pcbnew.ERROR_OUTSIDE)
    sp.BooleanIntersection(fpol)
    if sp.OutlineCount() == 0:
        problems.append("U1.1 (LDO GND) is not in the F.Cu GND pour")
    problems += gnd_paths.gate(board)
    return problems


def gnd_metrics(board):
    """Numbers for the README / PR: polygons and largest area per layer,
    GND vias."""
    fpol, bpol = gnd_polys(board)
    out = {}
    for name, ps in (("GND_F", fpol), ("GND_B", bpol)):
        areas = sorted((pcbnew.SHAPE_POLY_SET(ps.UnitSet(i)).Area() / 1e12
                        for i in range(ps.OutlineCount())), reverse=True)
        out[name] = (len(areas), areas[0] if areas else 0.0, sum(areas))
    out["GND vias"] = sum(1 for t in board.GetTracks()
                          if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND")
    return out


if __name__ == "__main__":
    main()
