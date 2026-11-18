"""GND fan-out: a locked via next to every SMD GND pad (pilink-r1h).

Library, called by preroute.py (after its own pre-routes, before route.py).
Not run on its own.

B.Cu is the board's ground plane. Freerouting no longer routes GND at all
(route.py takes GND out of the DSN netlist), so every F.Cu GND pad gets its
own short F.Cu stub to a via here, before routing, and the router routes
the signals around those vias. Every decoupling capacitor's GND pad thus has
its own via to the plane beside the pad, not a 0.2mm trace through the
neighbourhood (the 2026-11-17 audit's finding).

Placement, per pad: candidate via spots on rays out of the pad (every 15
degrees, via edge 0.15..1.0mm from the pad edge), legal when the via clears
every foreign pad/track/via by CLEAR, every other GND pad by CLEAR, NPTH
holes, the board edge, other footprints' courtyards and the via keepouts
(antenna strip, SKRTLAE010 areas, under L101). The best spot is the closest
one, with a penalty for pointing back across the part (toward its other
pads), so a 0402's via sits beyond its GND end. EXTRA lists high-current
returns that get more than one via.

Not fanned out here:
  * U101: the exposed pad has its own 9 thermal vias; PGND (pin 62), C103
    and C104 form the VREG high-current ground island, which reaches the
    plane only through its own two vias (preroute.py, RP2350 DS 6.3.8.1).
  * SW101/SW102 pad 2: preroute.py's escape vias (the Alps keepout boxes
    the pad in).
  * J501: its GND pins come in runs at 0.5mm pitch; each run is tied by a
    bar along the pads' outer ends with vias beyond it (fan_j501).
  * Through-hole GND pads (already on both layers).
  * U201's exposed pad (pad 39, its own thermal vias).
B.Cu SMD GND pads (U201's, C201-C203, the test pads) get a B.Cu stub and a
via the same way: B.Cu also carries signals, so a B.Cu pad is not on the
plane by itself (a trial routing boxed U201.15 into a 2.7 mm^2 pocket).
"""
import math

import pcbnew

MM = pcbnew.FromMM
O = 100.0                      # board-local origin on the page (place.py)
BOARD_W, BOARD_H = 122.5, 50.0
VIA_D, VIA_DRILL = 0.6, 0.3
# zones.py's stitching vias. A size nobody else uses, so zones.py (and
# route.py, which strips them before routing) can tell them apart from the
# locked fan-out vias below, which are kept.
GND_STITCH_D, GND_STITCH_DRILL = 0.7, 0.35
CLEAR = 0.2                    # via copper to any other copper
GAP_MIN, GAP_MAX = 0.15, 1.0   # via edge to its own pad's edge
HOLE_CLEAR = 0.25              # via copper to an NPTH hole edge
EDGE = 0.5                     # via copper to the board edge
SKIP = {("U101", "62"), ("U101", "81"), ("C103", "2"), ("C104", "2"),
        ("SW101", "2"), ("SW102", "2"),
        ("U201", "39")}     # U201's exposed pad: its own 9 thermal vias
SKIP_REFS = {"J501"}
# high-current / switching returns: (ref, pad) -> number of vias
EXTRA = {("U1", "1"): 3, ("C2", "1"): 2, ("C1", "1"): 2,
         ("C501", "1"): 2, ("C502", "1"): 2, ("U501", "2"): 2, ("D401", "2"): 2,
         # pilink-93a: C111's one via landed in a pocket of the east pin
         # row's B.Cu escapes on 3 of 12 trials; a second via gives the
         # pour a second way in
         ("C111", "2"): 2}
# pilink-xy5: via spots tried before the ray search, (dx, dy) mm from the
# pad centre. C112's best ray spot is east of its GND pad, between the USB
# pair's two B.Cu diagonals and beyond them, where the B.Cu reaches U101's
# EP only the long way round; this spot is south-west of the pad, west of
# the D- diagonal (0.24mm clear) and of C112.1 (0.4mm), inside
# plane_keepout's EP_E channel to the EP.
PREFER = {("C112", "2"): (-0.23, 0.85)}
# locked F.Cu GND links between pads, laid before the vias: C118's GND pad
# sits east of the USB pair's D+ diagonal (no B.Cu way to the EP channel and
# no room for a via west of the pair), so it joins C112's GND pad, 1.5mm
# straight down, and shares its via.
LINKS = [(("C118", "2"), ("C112", "2"), 0.4)]
# pads whose via may not be found (nothing depends on it): a miss is a
# warning, not an error. Everything else (every capacitor, every IC) must
# get its via or the script fails.
OPTIONAL_REFS = ("SW30",)
# B.Cu pads with no legal spot that are tied in another way: U201.38 sits
# against the antenna strip (no vias there) in the B.Cu pour; U401.2 (ESD
# GND) already has its own via from preroute.py.
OPTIONAL_PADS = ("U201.38", "U401.2")


def _pt(x, y):
    return pcbnew.VECTOR2I(MM(O + x), MM(O + y))


class Obstacles:
    """Copper / holes / keepouts a new GND via must clear."""

    def __init__(self, board, keepouts):
        self.board = board
        self.pads = []      # (polyset F or None, polyset B or None, net, pad)
        self.holes = []     # (centre, radius) NPTH
        self.court = []     # (ref, polyset) F and B courtyards
        for fp in board.GetFootprints():
            for L in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                c = fp.GetCourtyard(L)
                if c.OutlineCount():
                    self.court.append((fp.GetReference(), c))
            for p in fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.holes.append((p.GetPosition(), p.GetDrillSizeX() // 2))
                    continue
                polys = []
                for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if p.IsOnLayer(L):
                        sp = pcbnew.SHAPE_POLY_SET()
                        p.TransformShapeToPolygon(sp, L, 0, 5000, pcbnew.ERROR_INSIDE)
                        polys.append(sp)
                    else:
                        polys.append(None)
                bb = p.GetBoundingBox()
                self.pads.append((polys[0], polys[1], p.GetNetname(), p.m_Uuid.AsString(),
                                  (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())))
        self.tracks = []    # (layer, a, b, halfwidth, net)
        self.vias = []      # (pos, radius, net)
        for t in board.GetTracks():
            # only locked (pre-routed) copper: route.py strips the rest
            if not t.IsLocked():
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                self.vias.append((t.GetPosition(), t.GetWidth(pcbnew.F_Cu) // 2,
                                  t.GetNetname()))
            elif t.Type() == pcbnew.PCB_TRACE_T:
                self.tracks.append((t.GetLayer(), t.GetStart(), t.GetEnd(),
                                    t.GetWidth() // 2, t.GetNetname()))
        self.keepouts = keepouts   # polysets (vias not allowed inside)

    def add_via(self, pos, r):
        self.vias.append((pos, r, "GND"))

    def add_track(self, layer, a, b, hw):
        self.tracks.append((layer, a, b, hw, "GND"))

    @staticmethod
    def _seg_dist(p, a, b):
        ax, ay, bx, by, px, py = a.x, a.y, b.x, b.y, p.x, p.y
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        qx, qy = ax + t * dx, ay + t * dy
        return math.hypot(px - qx, py - qy)

    def via_ok(self, pos, r, own_pad, own_ref):
        clear = MM(CLEAR)
        x, y = pcbnew.ToMM(pos.x) - O, pcbnew.ToMM(pos.y) - O
        rm = pcbnew.ToMM(r)
        if (x - rm < EDGE or y - rm < EDGE or x + rm > BOARD_W - EDGE
                or y + rm > BOARD_H - EDGE):
            return False
        for c, hr in self.holes:
            if (pos - c).EuclideanNorm() < r + hr + MM(HOLE_CLEAR):
                return False
        for k in self.keepouts:
            if k.Contains(pos) or k.SquaredDistance(pos) < r * r:
                return False
        for ref, c in self.court:
            if ref != own_ref and c.Contains(pos):
                return False
        reach = r + clear
        own = own_pad.m_Uuid.AsString() if own_pad is not None else None
        for pf, pb, net, uid, (bl, bt, br, bb) in self.pads:
            if uid == own:
                continue
            if (pos.x < bl - reach or pos.x > br + reach
                    or pos.y < bt - reach or pos.y > bb + reach):
                continue
            for sp in (pf, pb):
                if sp is not None and sp.SquaredDistance(pos) < (r + clear) ** 2:
                    return False
        for layer, a, b, hw, net in self.tracks:
            if net == "GND":
                # own fan-out stubs and other GND copper: just keep the via
                # off the middle of them (a via may touch a GND track end)
                continue
            if self._seg_dist(pos, a, b) < r + hw + clear:
                return False
        for c, vr, net in self.vias:
            gap = MM(0.15) if net == "GND" else clear
            if (pos - c).EuclideanNorm() < r + vr + gap:
                return False
        return True

    def stub_ok(self, a, b, hw, own_pad, on=pcbnew.F_Cu):
        """GND stub a->b on layer `on` clears foreign pads and tracks."""
        clear = MM(CLEAR)
        n = max(2, int((b - a).EuclideanNorm() / MM(0.05)))
        for i in range(n + 1):
            p = pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * i / n), int(a.y + (b.y - a.y) * i / n))
            reach = hw + clear
            for pf, pb, net, uid, (bl, bt, br, bb) in self.pads:
                ps = pf if on == pcbnew.F_Cu else pb
                if net == "GND" or ps is None:
                    continue
                if (p.x < bl - reach or p.x > br + reach
                        or p.y < bt - reach or p.y > bb + reach):
                    continue
                if ps.SquaredDistance(p) < (hw + clear) ** 2:
                    return False
            for layer, s, e, thw, net in self.tracks:
                if net == "GND" or layer != on:
                    continue
                if self._seg_dist(p, s, e) < hw + thw + clear:
                    return False
            for c, vr, net in self.vias:
                if net != "GND" and (p - c).EuclideanNorm() < hw + vr + clear:
                    return False
        return True


def _keepouts(board):
    """Polysets where no via may go: antenna strip, SKRTLAE010 no-copper
    areas, the L101 footprint (B.Cu keepout)."""
    from antenna_reroute import STRIP
    from sw_keepout import add_sw_keepouts
    from l101_keepout import _rect as l101_rect
    out = []
    x0, y0, x1, y1 = STRIP
    sp = pcbnew.SHAPE_POLY_SET()
    sp.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1 + 0.5), (x0, y1 + 0.5)):
        sp.Append(_pt(x, y))
    out.append(sp)
    add_sw_keepouts(board)
    for z in list(board.Zones()):
        if z.GetZoneName().startswith("KO_SKRT_"):
            out.append(pcbnew.SHAPE_POLY_SET(z.Outline()))
            board.Remove(z)
    sp = pcbnew.SHAPE_POLY_SET()
    sp.NewOutline()
    for x, y in l101_rect(board):
        sp.Append(int(x), int(y))
    out.append(sp)
    return out


def _add_via(board, pos, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pos)
    v.SetWidth(pcbnew.F_Cu, MM(d))
    v.SetDrill(MM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(board.FindNet("GND"))
    v.SetLocked(True)
    board.Add(v)


def _add_track(board, a, b, w, layer=pcbnew.F_Cu):
    if a == b:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(a)
    t.SetEnd(b)
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet("GND"))
    t.SetLocked(True)
    board.Add(t)


def _candidates(pad, fp):
    """(score, via position) on rays out of the pad, best first."""
    c = pad.GetPosition()
    sz = pad.GetSize()
    hx, hy = sz.x / 2, sz.y / 2
    ang = math.radians(pad.GetOrientationDegrees())
    fc = fp.GetPosition()
    # direction "back across the part": from this pad toward the centre of
    # the part's other pads
    me = pad.m_Uuid.AsString()
    others = [p.GetPosition() for p in fp.Pads()
              if p.m_Uuid.AsString() != me and p.GetDrillSizeX() == 0]
    if others:
        ox = sum(p.x for p in others) / len(others) - c.x
        oy = sum(p.y for p in others) / len(others) - c.y
    else:
        ox, oy = fc.x - c.x, fc.y - c.y
    on = math.hypot(ox, oy) or 1.0
    ox, oy = ox / on, oy / on
    r = MM(VIA_D / 2)
    out = []
    for k in range(24):
        a = math.radians(k * 15)
        dx, dy = math.cos(a), math.sin(a)
        # pad half-extent along this direction (rectangle support function,
        # in the pad's own frame; KiCad angles are CCW with y down)
        lx = dx * math.cos(ang) - dy * math.sin(ang)
        ly = dx * math.sin(ang) + dy * math.cos(ang)
        ext = abs(lx) * hx + abs(ly) * hy
        back = dx * ox + dy * oy
        if back > 0.5:
            continue          # never across the part body
        for gi in range(int((GAP_MAX - GAP_MIN) / 0.05) + 1):
            gap = GAP_MIN + gi * 0.05
            d = ext + MM(gap) + r
            pos = pcbnew.VECTOR2I(int(c.x + dx * d), int(c.y + dy * d))
            score = gap + 0.8 * max(0.0, back + 0.2)
            out.append((score, pos))
    out.sort(key=lambda s: s[0])
    return out


def fan_pad(board, obs, fp, pad, n_vias):
    """Place n_vias GND vias beside pad; returns how many were placed."""
    r = MM(VIA_D / 2)
    hw = MM(min(0.4, 0.8 * pcbnew.ToMM(min(pad.GetSize().x, pad.GetSize().y))) / 2)
    on = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    placed = []
    cands = _candidates(pad, fp)
    pref = PREFER.get((fp.GetReference(), pad.GetNumber()))
    if pref:
        c = pad.GetPosition()
        cands.insert(0, (0.0, pcbnew.VECTOR2I(c.x + MM(pref[0]), c.y + MM(pref[1]))))
    for score, pos in cands:
        if len(placed) >= n_vias:
            break
        if any((pos - q).EuclideanNorm() < MM(0.9) for q in placed):
            continue
        if not obs.via_ok(pos, r, pad, fp.GetReference()):
            continue
        if not obs.stub_ok(pad.GetPosition(), pos, hw, pad, on):
            continue
        _add_via(board, pos)
        _add_track(board, pad.GetPosition(), pos, pcbnew.ToMM(hw * 2), on)
        obs.add_via(pos, r)
        obs.add_track(on, pad.GetPosition(), pos, hw)
        placed.append(pos)
    return len(placed)


def fan_j501(board, obs):
    """J501's GND pins: a 0.3mm bar along the outer ends of each run of
    adjacent GND pads, a via beyond it every ~2mm (and at least one per
    run), plus the two mounting tabs (MP1/MP2) like any other pad."""
    fp = board.FindFootprintByReference("J501")
    sig = sorted((p for p in fp.Pads() if p.GetNumber().isdigit()),
                 key=lambda p: p.GetPosition().y)
    runs, cur = [], []
    for p in sig:
        if p.GetNetname() == "GND":
            cur.append(p)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    # the pads are long in x; their outer (east) end faces away from the
    # connector body
    bb0 = sig[0].GetBoundingBox()
    assert bb0.GetWidth() > bb0.GetHeight() and fp.GetOrientationDegrees() in (-90, 270), \
        "fan_j501 assumes J501 rot 270 with its pad row along y, outer ends at +x"
    xe = max(pp.GetBoundingBox().GetRight() for pp in sig)
    bar_x = xe - MM(0.05)
    via_x = xe + MM(0.95)
    r = MM(VIA_D / 2)
    n = 0
    for run in runs:
        ya, yb = run[0].GetPosition().y, run[-1].GetPosition().y
        for p in run:
            _add_track(board, pcbnew.VECTOR2I(p.GetPosition().x, p.GetPosition().y),
                       pcbnew.VECTOR2I(bar_x, p.GetPosition().y), 0.3)
        if len(run) > 1:
            _add_track(board, pcbnew.VECTOR2I(bar_x, ya), pcbnew.VECTOR2I(bar_x, yb), 0.3)
        length = pcbnew.ToMM(yb - ya)
        k = max(1, int(round(length / 2.0)) + (1 if length > 1.0 else 0))
        ys = [ya + (yb - ya) * (i + 0.5) / k for i in range(k)] if k > 1 else [(ya + yb) // 2]
        if len(run) == 1:
            ys = [ya]
        for y in ys:
            # snap to the nearest GND pad's centreline so the stub runs
            # between the neighbouring signal pads' ends, never past them
            yy = min((p.GetPosition().y for p in run), key=lambda q: abs(q - y))
            pos = pcbnew.VECTOR2I(via_x, int(yy))
            if not obs.via_ok(pos, r, None, "J501"):
                continue
            _add_via(board, pos)
            _add_track(board, pcbnew.VECTOR2I(bar_x, int(yy)), pos, 0.3)
            obs.add_via(pos, r)
            n += 1
    for num in ("MP1", "MP2"):
        pad = fp.FindPadByNumber(num)
        n += fan_pad(board, obs, fp, pad, 2)
    return n


def fan_out(board):
    """Add the fan-out vias to `board` (in place). Returns (vias, misses)."""
    keep = _keepouts(board)
    obs = Obstacles(board, keep)
    total, misses = 0, []
    for (ra, na), (rb, nb), w in LINKS:
        pa = board.FindFootprintByReference(ra).FindPadByNumber(na)
        pb = board.FindFootprintByReference(rb).FindPadByNumber(nb)
        layer = pcbnew.F_Cu if pa.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        assert pa.GetNetname() == pb.GetNetname() == "GND" and pb.IsOnLayer(layer)
        if not obs.stub_ok(pa.GetPosition(), pb.GetPosition(), MM(w / 2), pa, layer):
            raise SystemExit(f"GND link {ra}.{na} -> {rb}.{nb} is blocked")
        _add_track(board, pa.GetPosition(), pb.GetPosition(), w, layer)
        obs.add_track(layer, pa.GetPosition(), pb.GetPosition(), MM(w / 2))
    # big / multi-via pads first (they need the most room), then the rest
    # in a fixed order (by reference) so the result is reproducible
    pads = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in SKIP_REFS:
            continue
        for p in fp.Pads():
            # pilink-r1h: B.Cu GND pads too (U201's, the test pads, ...):
            # B.Cu also carries signals, so a B.Cu pad is not on the plane by
            # itself (U201.15 ended up in a 2.7 mm^2 sliver boxed in by tracks)
            if (p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD
                    or (ref, p.GetNumber()) in SKIP):
                continue
            n = EXTRA.get((ref, p.GetNumber()), 1)
            pads.append((-n, ref, p.GetNumber(), fp, p))
    pads.sort(key=lambda t: (t[0], t[1], t[2]))
    for neg, ref, num, fp, p in pads:
        got = fan_pad(board, obs, fp, p, -neg)
        total += got
        if got == 0:
            misses.append(f"{ref}.{num}")
    total += fan_j501(board, obs)
    return total, misses


def check_misses(misses):
    fatal = [m for m in misses if not m.startswith(OPTIONAL_REFS) and m not in OPTIONAL_PADS]
    if misses:
        print("GND fan-out: no via spot for " + ", ".join(misses))
    if fatal:
        raise SystemExit("GND fan-out failed for required pads: " + ", ".join(fatal))
