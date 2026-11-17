#!/usr/bin/env python3
"""Hand pre-route of USB D+/D-, the crystal, backlight and SW101/SW102 (pilink-rqd, pilink-a8i).

Usage (from hardware/):  python3 scripts/preroute.py

Run after scripts/place.py and before scripts/route.py. Adds LOCKED tracks
and vias; route.py keeps locked wiring (exported to Freerouting as fixed
wiring) and routes everything else around it. Adapted from PR #33's
preroute.py for the current placement (J401 on B.Cu, U101 on F.Cu).
Idempotent, also on a finished (routed) board: it first deletes only its own
items -- LOCKED tracks/vias on the nets it owns -- so the router's unlocked
copper on those nets (incl. all GND routing) and zones.py's locked +3V3
stitching vias are untouched (pilink-ggt).

  * USB_DP / USB_DM: J401's data pads alternate DP/DM/DP/DM and are plated
    through, so DM is linked A7->B7 on F.Cu and DP A6->B6 on B.Cu (the two
    links cross on different layers). Since pilink-8rz/e63 each net runs on
    B.Cu from B7/B6 through U401's flow-through pad pair (ESD), north and
    then as a 45-degree parallel pair to R106/R107 (27R, B.Cu under U101),
    and from the resistor to a via at pin 66/67 (the MCU-side nets
    USB_DM_MCU / USB_DP_MCU). U401's GND and VBUS pins get their own vias.
  * U201 decoupling / EN (pilink-fvz): pin 2 -> C202 -> C201, pin 3 ->
    C203 -> R201, two GND vias, all B.Cu.
  * +3V3 trunk (pilink-yt5): 0.8mm F.Cu from U1's tab to two vias at C202,
    along the empty strip above the panel.
  * XIN / XOUT: out of U101's bottom edge between decoupling caps C110/C117,
    then to Y101 pad 1 / R101 pad 2 (F.Cu), ending at each pad's centre
    (pilink-xzs: XIN used to stop 0.57mm short of Y101 pad 1 and leave the
    last bit to the router). XTAL2 (R101 pad 1 -> Y101 pad 3) is
    left to the router.

Geometry is derived from the pads' actual positions, so it follows the
parts if place.py moves them, but clearances to neighbours were only
checked for the current placement. DRC is the judge.
"""
import json
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
# keeps locked GND wiring. preroute.py removes only LOCKED items on these
# nets (its own); unlocked router GND copper is never touched.
# pilink-2wq: the QSPI cluster (SCLK, SD0-3, SS) is locked, replayed from the
# master-branch Freerouting result (scripts/qspi_routes.json, board-local mm):
# the same placement of U101/U102/U103/R102/R105, so the same copper, and no
# more run-to-run variance on these nets. PSRAM_CS stays with the router:
# master's copper for it runs under U101's body, where the VREG/DVDD escapes
# now need the room.
LX_NET = "/RP2350B + Memory/VREG_LX"
QSPI_NETS = ["/RP2350B + Memory/" + n for n in
             ("QSPI_SCLK", "QSPI_SD0", "QSPI_SD1", "QSPI_SD2", "QSPI_SD3", "QSPI_SS")]
# pilink-audit-a: USB MCU-side nets (U101 <-> R106/R107), the U401 VBUS via,
# the ESP32 EN/decoupling links and the +3V3 trunk. zones.py owns the locked
# +3V3 stitching vias inside its SPREADER box and re-creates them itself.
DP_MCU = "/RP2350B + Memory/USB_DP_MCU"
DM_MCU = "/RP2350B + Memory/USB_DM_MCU"
VBUS = "/USB-C/VBUS_RAW"
ORIGIN = 100.0   # board-local (0,0) on the KiCad page; keep in sync with place.py
PREROUTE_NETS = ["USB_DP", "USB_DM", DP_MCU, DM_MCU, VBUS, XIN, XOUT, LED_K, LED_A,
                 BOOT_NET, RESET_NET, "GND", "+1V1", "+3V3", "ESP32_EN",
                 LX_NET] + QSPI_NETS


def main():
    board = pcbnew.LoadBoard(BOARD)
    for t in list(board.GetTracks()):
        if t.IsLocked() and t.GetNetname() in PREROUTE_NETS:
            board.Remove(t)

    def pad(ref, num):
        fp = board.FindFootprintByReference(ref)
        p = next(p for p in fp.Pads() if p.GetNumber() == num)
        return p.GetPosition().x / 1e6, p.GetPosition().y / 1e6

    def path(net, layer, pts, width=W):
        code = board.FindNet(net).GetNetCode()
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if (x0, y0) == (x1, y1):
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
            t.SetWidth(MM(width))
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

    # ---- USB (pilink-8rz / pilink-e63) ----------------------------------
    # J401 -> U401 (USBLC6-2SC6, B.Cu, flow-through) -> B.Cu pair -> R106/R107
    # (27R, B.Cu under U101) -> via -> U101 pins 66/67 on F.Cu. Everything
    # between the connector and the resistors is on B.Cu, one via per line.
    a6, a7 = pad("J401", "A6"), pad("J401", "A7")   # row nearer the board edge
    b6, b7 = pad("J401", "B6"), pad("J401", "B7")   # row nearer U401
    u_dp, u_dm = pad("U101", "67"), pad("U101", "66")
    e_dp_s, e_dp_n = pad("U401", "1"), pad("U401", "6")   # I/O1 = D+
    e_dm_s, e_dm_n = pad("U401", "3"), pad("U401", "4")   # I/O2 = D-
    e_gnd, e_vbus = pad("U401", "2"), pad("U401", "5")
    r_dp1, r_dp2 = pad("R107", "1"), pad("R107", "2")
    r_dm1, r_dm2 = pad("R106", "1"), pad("R106", "2")
    assert a6[0] < a7[0] and b7[0] < b6[0] and u_dp[0] < u_dm[0], \
        "USB pre-route assumes the current J401/U101 orientation"
    assert e_dm_s[0] < e_dp_s[0] and e_dp_n[1] < e_dp_s[1] and e_gnd[1] > e_vbus[1], \
        "USB pre-route assumes U401 rot 90 on B.Cu (D- west, GND toward J401)"
    assert r_dp1[0] < r_dp2[0] and r_dm1[0] < r_dm2[0], "R106/R107 pad 1 must face west"
    k = 0.25   # short stub that makes the J401 pad-to-pad link 45 degrees
    # J401's A/B rows: DM linked A7 -> B7 on F.Cu, DP A6 -> B6 on B.Cu.
    path("USB_DM", F, [a7, (b7[0], b7[1] + k), b7])
    path("USB_DP", B, [a6, (b6[0], b6[1] + k), b6])
    # J401 B-row -> U401 south pads, straight up the I/O columns, then
    # through each pad pair (pins 3->4, 1->6 are the same internal line).
    for b_pad, s_pad, n_pad, net in ((b7, e_dm_s, e_dm_n, "USB_DM"),
                                     (b6, e_dp_s, e_dp_n, "USB_DP")):
        jog = (s_pad[0], b_pad[1] - 1.025)
        path(net, B, [b_pad, (b_pad[0], b_pad[1] - 0.625), jog, s_pad, n_pad])
    # U401 GND (pin 2) -> via between the J401 shell slots; VBUS (pin 5) ->
    # via to F.Cu (the router takes it on to VBUS_RAW from there).
    g = (e_gnd[0], e_gnd[1] + 1.21)
    path("GND", B, [e_gnd, g])
    via("GND", *g)
    vb = (e_vbus[0], e_vbus[1] - 1.11)
    path(VBUS, B, [e_vbus, vb])
    via(VBUS, *vb)
    # U401 north pads -> R106/R107: north, west along two lanes 0.8mm apart,
    # then the 45-degree run NW to the resistors. D- (west at U401) is the
    # inner track of every turn, so the pair never crosses.
    dm_lane, dp_lane = e_dm_n[1] - 1.86, e_dm_n[1] - 2.66
    dp_e = (r_dp2[0] + 1.44, r_dp2[1])            # east end of R107's stub
    dm_e = (r_dm2[0] + 0.94, r_dm2[1])
    path("USB_DP", B, [e_dp_n, (e_dp_n[0], dp_lane + 0.5), (e_dp_n[0] - 0.5, dp_lane),
                       (dp_e[0] + (dp_lane - dp_e[1]), dp_lane), dp_e, r_dp2])
    path("USB_DM", B, [e_dm_n, (e_dm_n[0], dm_lane + 0.5), (e_dm_n[0] - 0.5, dm_lane),
                       (dm_e[0] + (dm_lane - dm_e[1]), dm_lane), dm_e, r_dm2])
    # U101 end: DP drops through a via right below pin 67 and runs B.Cu to
    # R107; DM jogs right under the body on F.Cu (crossing over DP's B.Cu
    # stub) to a via beside R106, so DP stays the north-east track.
    v_dp = (u_dp[0], u_dp[1] + 1.1)
    path(DP_MCU, F, [u_dp, v_dp])
    via(DP_MCU, *v_dp)
    path(DP_MCU, B, [v_dp, r_dp1])
    v_dm = (u_dm[0] + 0.5, r_dm1[1])
    path(DM_MCU, F, [u_dm, (u_dm[0], u_dm[1] + 0.6), (u_dm[0] + 0.5, u_dm[1] + 1.1), v_dm])
    via(DM_MCU, *v_dm)
    path(DM_MCU, B, [v_dm, r_dm1])

    # ---- ESP32 decoupling / EN (pilink-fvz) --------------------------------
    # B.Cu, right edge of U201: pin 2 -> C202 -> C201, pin 3 -> C203 -> R201,
    # two GND vias. R201/R202's +3V3 ends (pull-up current only) are left to
    # the router.
    p2, p3 = pad("U201", "2"), pad("U201", "3")
    c202_1, c202_2 = pad("C202", "1"), pad("C202", "2")
    c201_1, c201_2 = pad("C201", "1"), pad("C201", "2")
    c203_1, c203_2 = pad("C203", "1"), pad("C203", "2")
    r201_2 = pad("R201", "2")
    assert c201_1[0] < c201_2[0] and abs(c201_1[1] - c201_2[1]) < 0.01, \
        "C201 expected horizontal, pad 1 west"
    path("+3V3", B, [p2, c202_1, (c202_1[0], c201_1[1]), c201_1], width=0.5)
    path("ESP32_EN", B, [p3, c203_1, r201_2], width=0.3)
    g1 = (c202_2[0] + 0.52, c202_2[1] + 0.79)
    g2 = (c201_2[0], c201_2[1] + 1.35)
    path("GND", B, [c202_2, g1, c203_2], width=0.4)
    path("GND", B, [c201_2, g2], width=0.4)
    via("GND", *g1)
    via("GND", *g2)

    # ---- +3V3 trunk U1 -> U201 (pilink-yt5) -------------------------------
    # 0.8mm F.Cu along the empty strip above the panel/RP2350B cluster (under
    # the SW101/SW102 strip, over the antenna keepout's lower edge), from U1's
    # tab to two vias beside C202/C201. Replaces the router's ~200 mOhm
    # 0.2mm path; the router still feeds every other +3V3 load.
    # U1 has two pads numbered "2" (leg and tab): use the tab (the larger)
    tab = max((p for p in board.FindFootprintByReference("U1").Pads()
               if p.GetNumber() == "2"), key=lambda p: p.GetSize().x * p.GetSize().y)
    tx, ty = tab.GetPosition().x / 1e6, tab.GetPosition().y / 1e6
    v3a = (c202_1[0], c202_1[1] - 1.01)       # both on C202 pad 1's vertical
    v3b = (c202_1[0], c202_1[1] - 1.91)       # +3V3 link to C201
    y1, y2 = ORIGIN + 6.0, ORIGIN + 4.0     # corridor y, board-local 6.0 / 4.0
    path("+3V3", F, [(tx, ty - 1.4), (tx, y1), (ORIGIN + 55.0, y1), (ORIGIN + 57.0, y2),
                     (v3a[0] - 0.55, y2), v3a, v3b], width=0.8)
    via("+3V3", *v3a)
    via("+3V3", *v3b)

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

    # ---- VREG ground return + L101 output (pilink-2wq) ---------------------
    # RP2350 DS 6.3.8.1: short ground return, ground plane under the
    # regulator. GND vias beside U101 pin 62, C103 pad 2 and C104 pad 2 put
    # the loop's return on B.Cu, and two anchor vias just outside L101's
    # courtyard (east side) give the isolated B.Cu pocket under L101 a GND
    # connection so GND_B fills there. L101 pad 2 -> C104 pad 1 is a locked
    # 0.4mm F.Cu link (+1V1; widen.py could not widen the router's 0.2mm one).
    # route.py keeps B.Cu routing out of x 47..53, y 13..20.5 (l101_keepout.py
    # PLANE_B) so these vias land on one connected GND_B region.
    x62, y62 = pad("U101", "62")
    path("GND", F, [(x62, y62), (x62, y62 + 1.2)])
    via("GND", x62, y62 + 1.2)
    xc3, yc3 = pad("C103", "2")
    path("GND", F, [(xc3, yc3), (xc3, yc3 - 0.9)])
    via("GND", xc3, yc3 - 0.9)
    xc4, yc4 = pad("C104", "2")
    # locked B.Cu GND link C103 via <-> C104 via (merges into GND_B): keeps
    # the router from linking them on F.Cu across the FB column below.
    path("GND", B, [(xc4, yc4 + 0.9), (xc3, yc3 - 0.9)])
    path("GND", F, [(xc4, yc4), (xc4, yc4 + 0.9)])
    via("GND", xc4, yc4 + 0.9)
    lx, ly = pad("L101", "2")
    for dy in (-1.0, 0.7):
        via("GND", lx + 3.3, ly + 1.6 + dy + 0.0)
    c1x, c1y = pad("C104", "1")
    path("+1V1", F, [(c1x, c1y), (lx, ly)], width=0.4)
    # VREG_FB (U101 pin 65) -> C104 pad 1: locked straight F.Cu run up its own
    # column, ~6mm, so the router cannot send it the long way round (it did
    # once PLANE_B blocked the B.Cu exit). Stays between the C104 GND via
    # and C103's pads.
    x65, y65 = pad("U101", "65")
    path("+1V1", F, [(x65, y65), (x65, c1y + 0.8), (c1x, c1y)])

    # ---- VREG_LX U101 pin 63 -> L101 pad 1 (pilink-2wq) ---------------------
    # Locked, short, no vias: otherwise the router's +3V3 run can box pin 63
    # in (seen once). widen.py takes it to 0.4mm where DRC allows.
    x63, y63 = pad("U101", "63")
    xl, yl = pad("L101", "1")
    path(LX_NET, F, [(x63, y63), (x63, y63 - 0.5), (xl - 1.35, yl), (xl, yl)])

    # ---- QSPI cluster replay (pilink-2wq) ----------------------------------
    with open(os.path.join(HERE, "qspi_routes.json")) as fh:
        qspi = json.load(fh)
    for short, d in qspi.items():
        net = "/RP2350B + Memory/" + short
        for lay, x0, y0, x1, y1, w in d["tracks"]:
            path(net, F if lay == "F" else B,
                 [(x0 + 100.0, y0 + 100.0), (x1 + 100.0, y1 + 100.0)], width=w)
        for x, y in d["vias"]:
            via(net, x + 100.0, y + 100.0)

    pcbnew.SaveBoard(BOARD, board)
    print("pre-routed USB D+/D- (J401 -> U401 -> R106/R107 -> U101), XIN/XOUT, backlight, "
          "SW101/SW102 BOOTSEL/RESET + GND escapes, ESP32 decoupling/EN, +3V3 trunk (locked)")
    for n in ("USB_DP", "USB_DM", DP_MCU, DM_MCU):
        print(n, round(sum(t.GetLength() / 1e6 for t in board.GetTracks()
                           if t.GetNetname() == n and t.GetClass() == "PCB_TRACK"), 2), "mm")


if __name__ == "__main__":
    main()
