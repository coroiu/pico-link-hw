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
  * After pouring: a GND via beside each RETURN_VIA_PADS pad and GND
    stitching vias in every GND polygon that is not its layer's main plane
    (stitch_gnd), then a per-polygon report (gnd_report): area and the GND
    vias / PTH pads in each, so an unstitched fragment is visible.
"""
import math
import os
import sys

import pcbnew

from preroute import PREROUTE_NETS, DP_MCU, DM_MCU
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
# GND fragment stitching vias (stitch_gnd). A size no other script uses, so
# zones.py can find and remove its own on a re-run (GND is a pre-routed net,
# so locked GND vias are otherwise kept).
GND_STITCH_D, GND_STITCH_DRILL = 0.7, 0.35
RETURN_VIA_PADS = [("C502", "1")]   # always get an adjacent GND via (stitch_gnd)


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
                    if (o is not t and o.Type() == pcbnew.PCB_TRACE_T and o.GetNetCode() == net
                            and min((pos - o.GetStart()).EuclideanNorm(), (pos - o.GetEnd()).EuclideanNorm()) <= rv):
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
                        elif o.GetLayer() == t.GetLayer() and end in (o.GetStart(), o.GetEnd()):
                            ok = True
                            break
                if not ok:
                    gone.append(t)
                    break
        if not gone:
            break
        for t in gone:
            board.Remove(t)
        removed += len(gone)
    if removed:
        print(f"pruned {removed} dangling pre-route item(s)")


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
        if t.GetBoundingBox().Intersects(circle_bb):
            return False
    return True


def main():
    board = pcbnew.LoadBoard(BOARD)
    for z in list(board.Zones()):
        board.Remove(z)
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

    # C103 pad 2 (GND, VREG_VIN cap, pilink-2wq): the KO_L101_F pour cut-out
    # beside it leaves a single thermal spoke after the L101 re-placement;
    # same solid-connect fix as above.
    # C114 and C111 pad 2 (GND) likewise lost a spoke to re-routes.
    for ref in ("C103", "C114", "C111"):
        for pad in board.FindFootprintByReference(ref).Pads():
            if pad.GetNetname() == "GND" and pad.GetNumber() == "2":
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    split_at_t_joins(board)
    prune_dangling_locked(board)
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
    stitch_gnd(board)
    pcbnew.SaveBoard(BOARD, board)
    for z in board.Zones():
        area = z.GetFilledArea() / 1e12
        print(f"zone {z.GetZoneName():10} {z.GetNetname():5} "
              f"{board.GetLayerName(z.GetLayer())}: {area:.0f} mm2 filled")
    print(f"{n} heat-spreader stitching vias")
    for line in gnd_report(board):
        print(line)


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
    """PR #102 review: the locked +3V3 trunk (preroute.py) closes off a strip
    of GND_F that had no via to GND_B (C502's return went through two 0.2mm
    traces). First, every pad in RETURN_VIA_PADS gets a GND via right beside
    it. Then every GND pour polygon other than each layer's main plane gets
    stitched to the other layer: at least one GND via or PTH pad, and one
    per 40 mm^2, placed where the polygon overlaps any GND polygon of the
    other layer (one as close as possible to each GND SMD pad if it had
    none, then farthest-first, >= 3mm apart). Repeats after a refill.
    Polygons with no legal via spot (slivers round a pad) stay unstitched;
    gnd_report() lists them."""
    r_in = MM(GND_STITCH_D / 2 + 0.1)
    ring = [pcbnew.VECTOR2I(int(r_in * math.cos(a * math.pi / 4)),
                            int(r_in * math.sin(a * math.pi / 4))) for a in range(8)]
    net = board.FindNet("GND")
    added = 0

    def add_via(p):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(p)
        v.SetWidth(pcbnew.F_Cu, MM(GND_STITCH_D))
        v.SetDrill(MM(GND_STITCH_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net)
        v.SetLocked(True)
        board.Add(v)

    # Return-path pads that always get their own GND via right beside them,
    # whatever the fill does (PR #102 review: C502 is the AP3031 boost's
    # output cap, its GND pad carries the switching return).
    for ref, num in RETURN_VIA_PADS:
        pad = board.FindFootprintByReference(ref).FindPadByNumber(num)
        c = pad.GetPosition()
        best = None
        for dx in range(-30, 31):
            for dy in range(-30, 31):
                p = pcbnew.VECTOR2I(c.x + dx * MM(0.1), c.y + dy * MM(0.1))
                d = (p - c).EuclideanNorm()
                if best is not None and d >= best[0]:
                    continue
                if via_ok(board, p, "GND", MM(GND_STITCH_D / 2), near_own_pads=True):
                    best = (d, p)
        if best is None:
            sys.exit(f"stitch_gnd: no legal GND via spot within 3mm of {ref}.{num}")
        add_via(best[1])
        added += 1
        print(f"GND via {best[0] / 1e6:.2f}mm from {ref}.{num}")
    if added:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # keep stitching vias out of via keepouts (SKRTLAE010 areas) and out of
    # the antenna strip (antenna_reroute.check_strip allows no vias there)
    no_via = [z.Outline() for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    ax0, ay0, ax1, ay1 = ANT_KO
    strip = pcbnew.SHAPE_POLY_SET()
    strip.NewOutline()
    for x, y in ((ax0, ay0), (ax1, ay0), (ax1, ay1 + 0.5), (ax0, ay1 + 0.5)):
        strip.Append(pt(x, y))
    no_via.append(strip)
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
                        if not all(this.Contains(p + o, i) and other.Contains(p + o)
                                   for o in [pcbnew.VECTOR2I(0, 0)] + ring):
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
        added += len(new)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("GND fragment stitching vias:", added)


if __name__ == "__main__":
    main()
