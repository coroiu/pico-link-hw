#!/usr/bin/env python3
"""Hand-route the nets an autorouter should not be trusted with (pilink-7el.9).

Usage (from hardware/):  python3 scripts/preroute.py

Run after scripts/place.py and before scripts/route.py. Adds LOCKED F.Cu
tracks; route.py exports them to Freerouting as fixed wiring and routes
everything else around them. Idempotent: all tracks are removed first (a
pre-route is only valid on an otherwise unrouted board anyway).

  * USB_DP / USB_DM: J401 -> U101 as a side-by-side pair, no vias. The
    receptacle's four data pads alternate DP/DM/DP/DM, so the DM pair is
    linked on the connector side of the pad row (under the shell) and the DP
    pair on the board side, which keeps both nets on one layer.
  * XIN / XOUT: straight out of U101 between the two decoupling caps to the
    crystal / its series resistor.

Paths are built from the pads' actual positions, so they follow U101, J401,
Y101 and R101 if place.py moves them -- but the clearances to neighbouring
parts were only checked for the placement in place.py. DRC is the judge.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
MM = pcbnew.FromMM
W = 0.2


def main():
    board = pcbnew.LoadBoard(BOARD)
    for t in list(board.GetTracks()):
        board.Remove(t)
    for z in list(board.Zones()):
        board.Remove(z)

    def pad(ref, num):
        fp = board.FindFootprintByReference(ref)
        p = next(p for p in fp.Pads() if p.GetNumber() == num)
        return p.GetPosition().x / 1e6, p.GetPosition().y / 1e6

    def path(net, pts):
        code = board.FindNet(net).GetNetCode()
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
            t.SetWidth(MM(W))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNetCode(code)
            t.SetLocked(True)
            board.Add(t)

    # ---- USB ------------------------------------------------------------
    dp_l, dm_l = pad("J401", "B6"), pad("J401", "A7")   # left two data pads
    dp_r, dm_r = pad("J401", "A6"), pad("J401", "B7")   # right two
    u_dp, u_dm = pad("U101", "67"), pad("U101", "66")
    assert dp_l[0] < dm_l[0] < dp_r[0] < dm_r[0] and u_dp[0] < u_dm[0], \
        "USB pre-route assumes J401 rotated 180 and U101 at 0"
    y_pad = dp_l[1]
    y_over = y_pad - 1.25      # DM link, connector side of the pad row
    y_under = y_pad + 1.35     # DP link, board side of the pad row
    y_jog = y_under + 0.9
    path("USB_DM", [dm_l, (dm_l[0], y_over), (dm_r[0], y_over), dm_r,
                    (dm_r[0], y_jog + 0.3),
                    (u_dm[0], y_jog + 0.3 + (dm_r[0] - u_dm[0])), u_dm])
    path("USB_DP", [dp_l, (dp_l[0], y_under), (dp_r[0], y_under), dp_r])
    path("USB_DP", [(dp_r[0], y_under), (dp_r[0], y_jog),
                    (u_dp[0], y_jog + (dp_r[0] - u_dp[0])), u_dp])

    # ---- crystal --------------------------------------------------------
    xin, xout = pad("U101", "30"), pad("U101", "31")
    y_xin, y_x3 = pad("Y101", "1"), pad("Y101", "3")
    r_xout = pad("R101", "2")
    xc = (y_xin[0] + y_x3[0]) / 2          # gap between Y101's pad columns
    y_split = r_xout[1] - (r_xout[0] - 0.6 - xout[0])
    path("/RP2350B + Memory/XOUT",
         [xout, (xout[0], y_split), (r_xout[0] - 0.6, r_xout[1]), r_xout])
    y_turn = y_split + 0.9
    path("/RP2350B + Memory/XIN",
         [xin, (xin[0], y_turn), (xc, y_turn + (xc - xin[0])),
          (xc, y_xin[1]), y_xin])

    pcbnew.SaveBoard(BOARD, board)
    n = sum(1 for t in board.GetTracks())
    print(f"pre-routed {n} locked segments (USB_DP, USB_DM, XIN, XOUT)")


if __name__ == "__main__":
    main()
