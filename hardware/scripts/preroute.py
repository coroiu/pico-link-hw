#!/usr/bin/env python3
"""Hand pre-route of USB D+/D-, the crystal, backlight and SW101/SW102 (pilink-rqd, pilink-a8i).

Usage (from hardware/):  python3 scripts/preroute.py

Run after scripts/place.py and before scripts/route.py. Adds LOCKED tracks
and vias; route.py keeps locked wiring (exported to Freerouting as fixed
wiring) and routes everything else around it. Adapted from PR #33's
preroute.py for the current placement (J401 on B.Cu, U101 on F.Cu).
Idempotent: it first deletes every track/via on the nets it owns.

  * USB_DP / USB_DM: J401's data pads alternate DP/DM/DP/DM and are plated
    through, so DM is linked A7->B7 on F.Cu and DP A6->B6 on B.Cu (the two
    links cross on different layers). Each net then rises from B7/B6 on
    F.Cu to a via, runs B.Cu as a 45-degree parallel pair under U101's
    body to a via just inside pins 66/67, and returns to the pin on F.Cu.
  * XIN / XOUT: out of U101's bottom edge between decoupling caps C110/C117,
    then to Y101 pad 1 / R101 pad 2 (F.Cu), ending at each pad's centre
    (pilink-xzs: XIN used to stop 0.57mm short of Y101 pad 1 and leave the
    last bit to the router). XTAL2 (R101 pad 1 -> Y101 pad 3) is
    left to the router.

Geometry is derived from the pads' actual positions, so it follows the
parts if place.py moves them, but clearances to neighbours were only
checked for the current placement. DRC is the judge.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
MM = pcbnew.FromMM
W = 0.2
VIA_D, VIA_DRILL = 0.6, 0.3

XIN = "/RP2350B + Memory/XIN"
XOUT = "/RP2350B + Memory/XOUT"
# Nets whose locked tracks/vias route.py must keep (it drops all other vias).
LED_K = "Net-(J501-LED_K)"
LED_A = "Net-(D501-K)"  # backlight anode rail J501 pin 40 -> D501 pad 1
BOOT_NET = "/RP2350B + Memory/BOOTSEL_NODE"
RESET_NET = "/RP2350B + Memory/RESET_NODE"
# GND is listed only for the SW101/SW102 pad-2 escape vias (below); route.py
# keeps locked GND wiring, preroute.py clears all GND tracks/vias before
# re-adding them, so no stale GND copper survives.
PREROUTE_NETS = ["USB_DP", "USB_DM", XIN, XOUT, LED_K, LED_A,
                 BOOT_NET, RESET_NET, "GND"]


def main():
    board = pcbnew.LoadBoard(BOARD)
    for t in list(board.GetTracks()):
        if t.GetNetname() in PREROUTE_NETS:
            board.Remove(t)

    def pad(ref, num):
        fp = board.FindFootprintByReference(ref)
        p = next(p for p in fp.Pads() if p.GetNumber() == num)
        return p.GetPosition().x / 1e6, p.GetPosition().y / 1e6

    def path(net, layer, pts):
        code = board.FindNet(net).GetNetCode()
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if (x0, y0) == (x1, y1):
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
            t.SetWidth(MM(W))
            t.SetLayer(layer)
            t.SetNetCode(code)
            t.SetLocked(True)
            board.Add(t)

    def via(net, x, y):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(VIA_D))
        v.SetDrill(MM(VIA_DRILL))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetNetCode(board.FindNet(net).GetNetCode())
        v.SetLocked(True)
        board.Add(v)

    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    # ---- USB ------------------------------------------------------------
    a6, a7 = pad("J401", "A6"), pad("J401", "A7")   # row nearer the board
    b6, b7 = pad("J401", "B6"), pad("J401", "B7")   # row nearer the shell
    u_dp, u_dm = pad("U101", "67"), pad("U101", "66")
    assert a6[0] < a7[0] and b7[0] < b6[0] and u_dp[0] < u_dm[0], \
        "USB pre-route assumes the current J401/U101 orientation"
    k = 0.25   # short stub that makes the pad-to-pad link 45 degrees
    dp_v = (b6[0], b6[1] - 4.5)     # J401-end vias (B.Cu pair starts here)
    dm_v = (b7[0], b7[1] - 3.3)
    up_v = (u_dp[0], u_dp[1] + 1.1)  # U101-end vias, staggered in the body
    um_v = (u_dm[0] + 0.5, u_dm[1] + 2.9)  # DM jogs right of the DP via

    path("USB_DM", F, [a7, (b7[0], b7[1] + k), b7, dm_v])
    path("USB_DM", F, [um_v, (um_v[0], u_dm[1] + 1.1),
                       (u_dm[0], u_dm[1] + 0.6), u_dm])
    d = dm_v[1] - um_v[1]
    path("USB_DM", B, [um_v, (um_v[0] + d, dm_v[1]), dm_v])
    via("USB_DM", *dm_v)
    via("USB_DM", *um_v)

    path("USB_DP", B, [a6, (b6[0], b6[1] + k), b6])
    path("USB_DP", F, [b6, dp_v])
    path("USB_DP", F, [up_v, u_dp])
    d = dp_v[1] - up_v[1]
    path("USB_DP", B, [up_v, (up_v[0] + d, dp_v[1]), dp_v])
    via("USB_DP", *dp_v)
    via("USB_DP", *up_v)

    # ---- crystal --------------------------------------------------------
    xin, xout = pad("U101", "30"), pad("U101", "31")
    y_xin, r_xout = pad("Y101", "1"), pad("R101", "2")
    # XIN and XOUT both drop through the 0.8mm gap between decoupling caps
    # C110/C117 (GND pads at y~131.7) before turning towards their parts.
    # (the 0.1mm jog right keeps XIN 0.2mm off Y101's GND pad 4, below the
    # point where XOUT has already turned away from XIN)
    xr = xin[0] + 0.1
    path(XIN, F, [xin, (xin[0], 133.4), (xr, 133.5), (xr, y_xin[1] - 1.0),
                  (xr - 0.6, y_xin[1] - 0.4), y_xin])
    path(XOUT, F, [xout, (xout[0], r_xout[1] - 0.96),
                   (xout[0] + 0.93, r_xout[1] - 0.03), r_xout])

    # ---- backlight feedback (pilink-4qc) ---------------------------------
    # J501 pin 39 -> R501 pad 2 (the FB divider), kept right of the boost
    # cluster so it stays >=1.2mm from the switching node (DRU rule
    # backlight_sw_vs_fb). Shape copied from the pre-pilink-4qc master
    # autoroute, expressed relative to J501 pin 39 so it follows the pair
    # (J501 and the boost cluster move together). Freerouting, left alone,
    # looped the net through B.Cu and failed that rule. U501 pin 3 -> R501
    # is left to the router (short).
    j39 = pad("J501", "39")
    ox, oy = j39[0] - 62.08, j39[1] - 9.75
    led = [(62.08, 9.75), (61.28, 9.75), (61.05, 9.52), (61.05, 8.97),
           (61.23, 8.78), (63.03, 8.78), (77.36, 23.11), (77.36, 36.97),
           (77.63, 37.24), (77.63, 41.88), (75.51, 44.0)]
    path(LED_K, F, [(x + ox, y + oy) for x, y in led])
    # Net-(D501-K) runs in parallel just below it (pin 40 -> D501 pad 1);
    # the router could not complete it once LED_K was fixed without it.
    ka = [(62.08, 9.25), (62.89, 9.25), (76.65, 23.01), (76.65, 38.0)]
    path(LED_A, F, [(x + ox, y + oy) for x, y in ka])
    # ... and U501 pin 5 -> D501 pad 1 (short F.Cu link, same shape as before)
    ku = [(76.14, 41.0), (76.45, 41.0), (77.07, 40.38), (77.07, 38.42), (76.65, 38.0)]
    path(LED_A, F, [(x + ox, y + oy) for x, y in ku])

    # ---- SW101 / SW102 BOOTSEL / RESET (pilink-a8i) ------------------------
    # The Alps SKRTLAE010 no-copper area (sw_keepout.py) boxes in pad 2 (GND)
    # and both pad-1 lands on F.Cu, so Freerouting cannot reach them and
    # leaves them unconnected. Same shape the retired sw_reroute.py used:
    #  * GND pad 2: stub up to a via above the switch (B.Cu GND pour).
    #  * pad-1 lands: a via beside each, tied by a B.Cu bar at pad level,
    #    a B.Cu trunk down to a via next to the pull-up's pad 2, then a short
    #    F.Cu stub to that pad.
    for sw_ref, r_ref, net in (("SW101", "R102", BOOT_NET),
                               ("SW102", "R103", RESET_NET)):
        sw = board.FindFootprintByReference(sw_ref)
        assert sw.GetOrientationDegrees() == 0 and sw.GetLayer() == F, \
            "SW pre-route assumes SW101/SW102 unrotated on F.Cu"
        cx, cy = sw.GetPosition().x / 1e6, sw.GetPosition().y / 1e6
        rx, ry = pad(r_ref, "2")
        g_via = (cx, cy - 2.05)
        v_l, v_r = (cx - 2.2, cy - 1.2), (cx + 2.2, cy - 1.2)
        v_low = (cx, ry - 1.1)
        path("GND", F, [(cx, cy - 0.9), g_via])
        via("GND", *g_via)
        for v, px in ((v_l, cx - 1.225), (v_r, cx + 1.225)):
            path(net, F, [(px, v[1]), v])
            via(net, *v)
        path(net, B, [v_l, (cx, v_l[1]), v_r])
        path(net, B, [(cx, v_l[1]), v_low])
        via(net, *v_low)
        path(net, F, [v_low, (rx, ry)])

    pcbnew.SaveBoard(BOARD, board)
    print("pre-routed USB_DP/USB_DM/XIN/XOUT (locked)")
    for n in ("USB_DP", "USB_DM"):
        print(n, round(sum(t.GetLength() / 1e6 for t in board.GetTracks()
                           if t.GetNetname() == n and t.GetClass() == "PCB_TRACK"), 2), "mm")


if __name__ == "__main__":
    main()
