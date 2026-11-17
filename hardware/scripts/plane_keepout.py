"""Ground-plane keepouts (pilink-r1h, pilink-2x7). Library, not run directly.

B.Cu is the board's ground plane; F.Cu carries the signals. Two kinds of
rule area keep it that way where it matters most:

* add_plane_keepouts() / remove_plane_keepouts(): B.Cu track keepouts that
  route.py exports to Freerouting (and removes again before saving), so
  no signal runs on B.Cu
    - under the VREG block (RP2350 DS 6.3.8.1: "the bottom layer under the
      regulator is a ground plane that connects to the QFN GND central
      pad"),
    - under U101, so its exposed pad's thermal vias land on the main plane
      (minus the corner where the USB pre-route's R106/R107 sit on B.Cu),
    - under the crystal (Y101, its load caps and R101).
  Vias stay allowed (GND fan-out / stitching vias are plane, not signal).
* add_pour_keepouts(): F.Cu no-fill areas zones.py adds, so the GND pour
  does not reach the VREG high-current ground island (PGND + C103.2 +
  C104.2, which must meet the main ground at its own two vias only) or the
  area between U101's pin ring and its exposed pad (where it would tie
  PGND's inner end straight to the EP).
Boxes are board-local mm (x0, y0, x1, y1); polygons are point lists.
"""
import pcbnew

O = 100.0          # keep in sync with place.py ORIGIN
NAME_B = "KO_PLANE_B_"
NAME_F = "KO_POUR_F_"
# VREG block: L101, C103/C104/C105, R104, the island vias, FB and the +1V1
# link (place.py / preroute.py geometry)
VREG_B = [(44.9, 10.3), (52.1, 10.3), (52.1, 19.2), (44.9, 19.2)]
# U101's body (38.4..49.6 x 18.4..29.6) less the USB corner (R106/R107,
# the pin 66/67 vias and the pair's exit to the south-east)
U101_B =[(38.4, 18.4), (44.9, 18.4), (44.9, 23.6), (49.6, 23.6), (49.6, 29.6),
          (38.4, 29.6)]
CRYSTAL_B = [(39.5, 32.0), (48.6, 32.0), (48.6, 38.0), (39.5, 38.0)]
PLANE_B = {"VREG": VREG_B, "U101": U101_B, "XTAL": CRYSTAL_B}
# F.Cu no-fill: the VREG ground island (FB's west edge to the island vias'
# east edge, L101's pad 1 down to just above the pins) and U101's inside
VREG_F = [(45.75, 16.0), (48.75, 16.0), (48.75, 18.66), (45.75, 18.66)]
U101_F = [(39.4, 19.4), (48.6, 19.4), (48.6, 28.6), (39.4, 28.6)]
POUR_F = {"VREG": VREG_F, "U101": U101_F}


def _area(board, name, layer, pts, tracks, fill):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowZoneFills(fill)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(O + x), pcbnew.FromMM(O + y))
    board.Add(z)


def remove_plane_keepouts(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith(NAME_B):
            board.Remove(z)


def add_plane_keepouts(board):
    remove_plane_keepouts(board)
    for tag, pts in PLANE_B.items():
        _area(board, NAME_B + tag, pcbnew.B_Cu, pts, True, False)


def add_pour_keepouts(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith(NAME_F):
            board.Remove(z)
    for tag, pts in POUR_F.items():
        _area(board, NAME_F + tag, pcbnew.F_Cu, pts, False, True)
