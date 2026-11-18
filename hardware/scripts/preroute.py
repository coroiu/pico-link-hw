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
import sys

import pcbnew

from gnd_fanout import fan_out, check_misses

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
# more run-to-run variance on these nets. PSRAM_CS is not replayed (master's
# copper for it runs under U101's body, where the VREG/DVDD escapes now need
# the room); since pilink-93a it has its own locked route over the VREG
# block (see the VREG section), and only R105's link is left to the router.
LX_NET = "/RP2350B + Memory/VREG_LX"
AVDD_NET = "/RP2350B + Memory/VREG_AVDD"
PSRAM_CS = "/RP2350B + Memory/PSRAM_CS"
GPIO41 = "GPIO41_ADC1"
QSPI_NETS = ["/RP2350B + Memory/" + n for n in
             ("QSPI_SCLK", "QSPI_SD0", "QSPI_SD1", "QSPI_SD2", "QSPI_SD3", "QSPI_SS")]
# pilink-audit-a: USB MCU-side nets (U101 <-> R106/R107), the U401 VBUS via,
# the ESP32 EN/decoupling links and the +3V3 trunk. zones.py owns the locked
# +3V3 stitching vias inside its SPREADER box and re-creates them itself.
DP_MCU = "/RP2350B + Memory/USB_DP_MCU"
DM_MCU = "/RP2350B + Memory/USB_DM_MCU"
VBUS = "/USB-C/VBUS_RAW"
ORIGIN = 100.0   # board-local (0,0) on the KiCad page; keep in sync with place.py
PREROUTE_NETS = ["USB_DP", "USB_DM", DP_MCU, DM_MCU, VBUS, "/USB-C/CC2",
                 XIN, XOUT, LED_K, LED_A,
                 BOOT_NET, RESET_NET, "GND", "+1V1", "+3V3", "ESP32_EN",
                 LX_NET, AVDD_NET, PSRAM_CS, GPIO41] + QSPI_NETS


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
    # J401 VBUS_RAW (pilink-yt5, PR #102 review). J401's VBUS columns (A4/B9
    # at the west, A9/B4 at the east) are boxed in by the GND columns, the
    # shell slots and the 0.15mm in-row pad gaps; the only ways out are the
    # 0.5mm strips between each pad row and its slot pair, which CC2 (B5)
    # also needs. Freerouting cannot use those strips (it adds 10um to every
    # clearance), so these escapes are laid by hand:
    #  * VBUS: F.Cu bar along the north strip joining both columns and on
    #    to F401 pad 2, a second F.Cu bar from the west column along the
    #    south strip to F401, and 0.3mm row-to-row links in each column.
    #  * CC2 (B5): B.Cu stub east along the north strip, past B1, to a via.
    #  * CC1 (A5) needs no help: the B.Cu south strip stays free, and the
    #    router leaves A5 diagonally between the two south slots.
    # 0.18mm in the strips (0.16mm each side), 0.4mm once past the GND column.
    b9, a4 = pad("J401", "B9"), pad("J401", "A4")
    b4, a9 = pad("J401", "B4"), pad("J401", "A9")
    b5, b1 = pad("J401", "B5"), pad("J401", "B1")
    f2 = pad("F401", "2")
    assert b9[0] == a4[0] < b4[0] == a9[0] and f2[0] < b9[0], \
        "VBUS pre-route assumes F401 west of J401 and J401 rot 0 on B.Cu"
    yn, ys = b9[1] - 0.725, a4[1] + 0.725     # strip centres
    xw = b9[0] - 1.8                           # west of the GND column
    path(VBUS, F, [b4, (b4[0], yn), (b9[0], yn), b9], width=0.18)
    path(VBUS, F, [a4, (a4[0], ys)], width=0.18)
    for y, toward in ((yn, -0.36), (ys, 0.36)):
        path(VBUS, F, [(b9[0], y), (xw, y)], width=0.18)
        path(VBUS, F, [(xw, y), (f2[0] + 0.36, y), (f2[0], f2[1] + toward), f2], width=0.4)
    path(VBUS, F, [b9, a4], width=0.3)
    path(VBUS, F, [b4, a9], width=0.3)
    # ends on a via in open board so the router has a fixed point to pick up
    # (it would not reliably reach a bare track end this close to J401)
    cc2_v = (b1[0] + 1.4, yn - 0.6)
    path("/USB-C/CC2", B, [b5, (b5[0] + 0.3, yn), (b1[0] + 0.8, yn), cc2_v], width=0.18)
    via("/USB-C/CC2", *cc2_v)
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

    # ---- VREG (pilink-2x7: RP2350 DS 6.3.8.1 / Fig. 26) --------------------
    # Top-row pins, west to east: 65 FB, 64 VIN, 63 LX, 62 PGND, 61 AVDD.
    # place.py stacks C103 (C_IN) and C104 (C_OUT) right above the pins,
    # each straddling the LX column with its west pad over VIN/FB (+3V3 /
    # +1V1) and its east pad over PGND, and L101 above them with its LX pad
    # (pad 1) at the bottom. Then, all on F.Cu:
    #  * C_IN loop: VIN pin -> C103.1 and PGND pin -> C103.2, each a straight
    #    0.5mm stub, so the hot loop VIN -> C_IN -> PGND is ~1mm long.
    #  * LX: pin 63 straight up between C103's and C104's pads (a 0.15mm
    #    neck, DRU rule vreg_lx_neck) into L101 pad 1, no via.
    #  * High-current ground island: PGND pin + C103.2 + C104.2, joined to
    #    the B.Cu plane at ONE point by two adjacent vias;
    #    plane_keepout.py keeps the GND pour off the island, so nothing else
    #    reaches it. C105 (C_FILT) has its own via (gnd_fanout.py).
    #  * VREG_FB: pin 65 -> C104.1 (C_OUT's output pad), its own 0.15mm
    #    trace, no via, no load on it.
    #  * +1V1 out: L101 pad 2 -> C104.1 down L101's west side (the C_OUT
    #    node). DVDD leaves from that node by a separate trace: east over
    #    L101, down to C118 / pin 51; pin 51's inner end then feeds an F.Cu
    #    ring under the package to pins 10 and 32 (between the pin ring and
    #    the exposed pad), so +1V1 needs no B.Cu at all.
    #  * VIN supply: C103.1 is boxed in by FB, C104 and LX, so VREG_VIN takes
    #    its +3V3 from pin 60 by a short F.Cu link under the package (pin
    #    inner ends).
    #  * AVDD: pin 61 -> C105.1 (C_FILT) directly (~1.6mm), R104 (33R) just
    #    above it.
    def pext(ref, num):
        """(x0, y0, x1, y1) of a pad's bounding box, board page mm."""
        fp = board.FindFootprintByReference(ref)
        p = next(p for p in fp.Pads() if p.GetNumber() == num)
        bb = p.GetBoundingBox()
        return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)

    x61, y61 = pad("U101", "61")
    x62, y62 = pad("U101", "62")
    x63, y63 = pad("U101", "63")
    x64, y64 = pad("U101", "64")
    x65, y65 = pad("U101", "65")
    yo = pext("U101", "63")[1]        # outer end of the top-row pads
    yi = pext("U101", "63")[3]        # inner end
    c3_1, c3_2 = pad("C103", "1"), pad("C103", "2")
    c4_1, c4_2 = pad("C104", "1"), pad("C104", "2")
    l1, l2 = pad("L101", "1"), pad("L101", "2")
    r4_1, r4_2 = pad("R104", "1"), pad("R104", "2")
    c5_1 = pad("C105", "1")
    assert c3_1[0] < x63 < c3_2[0] and c4_1[0] < x63 < c4_2[0], \
        "VREG pre-route assumes C103/C104 straddle the VREG_LX column"
    assert c4_1[1] < c3_1[1] < yo and l1[1] < c4_1[1] and l2[1] < l1[1], \
        "VREG pre-route assumes pins -> C103 -> C104 -> L101 (pad 1 low) going up"
    assert r4_2[0] < r4_1[0] and abs(r4_2[0] - c5_1[0]) < 0.1, \
        "VREG pre-route assumes R104 pad 2 (AVDD) west, above C105 pad 1"
    # C_IN loop and the PGND island
    path("+3V3", F, [(x64, y64), (x64, c3_1[1])], width=0.22)
    path("GND", F, [(x62, y62), (x62, c3_2[1])], width=0.22)
    path("GND", F, [c3_2, c4_2], width=0.4)
    xv = c3_2[0] + 0.82
    for yv in (c4_2[1] + 0.12, c3_2[1] - 0.15):
        path("GND", F, [(c3_2[0], yv), (xv, yv)], width=0.4)
        via("GND", xv, yv)
    # LX: neck between the cap pads, 0.4mm once clear of C104
    c4_top = pext("C104", "1")[1]
    yw = c4_top - 0.37
    path(LX_NET, F, [(x63, y63), (x63, yw)], width=0.15)
    path(LX_NET, F, [(x63, yw), (x63, l1[1])], width=0.4)
    # FB: its own trace into C_OUT's output pad
    path("+1V1", F, [(x65, y65), (x65, yo), (x65 - 0.3, yo - 0.3),
                     (x65 - 0.3, c4_1[1]), c4_1], width=0.15)
    # +1V1: L101 pad 2 -> C104.1 down L101's west side
    l2_top = pext("L101", "2")[1]
    l1_bot = pext("L101", "1")[3]
    ytop = l2_top - 0.37
    xw = pext("L101", "1")[0] - 1.15          # west of L101 (outside its body)
    ylink = l1_bot + 0.365
    path("+1V1", F, [l2, (l2[0], ytop), (xw, ytop), (xw, ylink)], width=0.4)
    path("+1V1", F, [(xw, ylink), (c4_1[0], ylink), c4_1], width=0.3)
    # DVDD: from L101 pad 2's node east over L101, down beside C113, west
    # between C113 and C118 into C118 (4.7uF; DS: a second VOUT cap away
    # from LX/C_OUT), and from C118 onto pin 51. (Entering C118 from above
    # leaves pin 50, +3V3, its way out east under it.)
    c113_2, c118_1 = pad("C113", "2"), pad("C118", "1")
    x51, y51 = pad("U101", "51")
    x_dv = c113_2[0] + 0.82
    y_dv = pext("C118", "1")[1] - 0.64
    x51o = pext("U101", "51")[2]               # outer end of pin 51
    path("+1V1", F, [(l2[0], ytop), (x_dv, ytop), (x_dv, y_dv), (c118_1[0], y_dv), c118_1], width=0.4)
    path("+1V1", F, [c118_1, (x51o + 0.9, y51), (x51o + 0.3, y51)], width=0.25)
    path("+1V1", F, [(x51o + 0.3, y51), (x51, y51)], width=0.2)
    tp = pad("TP101", "1")
    vtp = (tp[0] - 0.95, tp[1])
    path("+1V1", F, [(x_dv, tp[1]), vtp], width=0.4)
    via("+1V1", *vtp)
    path("+1V1", B, [vtp, tp], width=0.4)
    # +1V1 ring under the package: pin 51 inner end -> pins 32 and 10
    x10, y10 = pad("U101", "10")
    x32, y32 = pad("U101", "32")
    x51i = pext("U101", "51")[0]
    x10i = pext("U101", "10")[2]
    y32i = pext("U101", "32")[1]
    epb = board.FindFootprintByReference("U101")
    eps = [p.GetBoundingBox() for p in epb.Pads() if p.GetNumber() == "81"]
    ep_x0 = min(b.GetLeft() for b in eps) / 1e6
    ep_x1 = max(b.GetRight() for b in eps) / 1e6
    ep_y1 = max(b.GetBottom() for b in eps) / 1e6
    xr_e = (ep_x1 + x51i) / 2 - 0.1           # ring, east leg
    xr_w = (ep_x0 + x10i) / 2                 # ring, west leg
    yr_s = (ep_y1 + y32i) / 2 - 0.3           # ring, south leg
    path("+1V1", F, [(x51, y51), (x51i - 0.6, y51)], width=0.2)
    path("+1V1", F, [(x51i - 0.6, y51), (xr_e, y51), (xr_e, yr_s), (xr_w, yr_s),
                     (xr_w, y10), (x10i + 0.2, y10)], width=0.3)
    path("+1V1", F, [(x10i + 0.2, y10), (x10, y10)], width=0.2)
    path("+1V1", F, [(x32, yr_s), (x32, y32i - 0.2)], width=0.3)
    path("+1V1", F, [(x32, y32i - 0.2), (x32, y32)], width=0.2)
    # the other two DVDD caps, straight onto their pins
    c116_1, c117_1 = pad("C116", "1"), pad("C117", "1")
    x10o = pext("U101", "10")[0]
    y32o = pext("U101", "32")[3]
    path("+1V1", F, [c116_1, (x10o - 0.2, y10)], width=0.3)
    path("+1V1", F, [(x10o - 0.2, y10), (x10, y10)], width=0.2)
    path("+1V1", F, [c117_1, (c117_1[0], c117_1[1] - 0.5), (x32, y32o + 0.4)], width=0.3)
    path("+1V1", F, [(x32, y32o + 0.4), (x32, y32)], width=0.2)
    # VREG_VIN supply: pin 64 inner end -> pin 60 (+3V3) under the package
    x60, y60 = pad("U101", "60")
    x60i = pext("U101", "60")[0]
    yl = yi + 0.36
    path("+3V3", F, [(x64, y64), (x64, yl), (x60i - 0.31, yl), (x60i, y60)], width=0.25)
    path("+3V3", F, [(x60i, y60), (x60, y60)], width=0.2)
    # The DVDD run boxes in pins 52..60 on F.Cu (any F.Cu path from the VREG
    # node to a +1V1 pin does). Of those only PSRAM_CS (58) and GPIO41 (52)
    # have to get out: each drops through a via right beside the pins and
    # crosses under the caps column and the DVDD run on B.Cu to a via east
    # of it (~3.5mm of B.Cu each), where the router picks it up. Their
    # lanes stay north of the USB pair's B.Cu diagonal.
    x58o = pext("U101", "58")[2]
    x58, y58 = pad("U101", "58")
    x52, y52 = pad("U101", "52")
    xe = x_dv + 0.85
    v_cs = (x58o + 0.55, y58)
    v_41 = (x58o + 1.01, y58 + 0.75)
    path(PSRAM_CS, F, [(x58, y58), v_cs])
    via(PSRAM_CS, *v_cs)
    path(PSRAM_CS, B, [v_cs, (xe, v_cs[1])])
    via(PSRAM_CS, xe, v_cs[1])
    path(GPIO41, F, [(x52, y52), (x58o + 0.15, y52), (x58o + 0.56, y52 - 0.4),
                     (x58o + 0.56, v_41[1] + 0.4), v_41])
    via(GPIO41, *v_41)
    path(GPIO41, B, [v_41, (xe + 0.45, v_41[1])])
    via(GPIO41, xe + 0.45, v_41[1])
    # PSRAM_CS on to U103 (pilink-93a), locked, ~33mm: from the hop's east
    # via up F.Cu east of the DVDD run (round TP101's +1V1 via), west on
    # F.Cu over the VREG block (north of the +1V1 run, south of R102/R103),
    # then one short B.Cu hop under QSPI_SCLK into U103 pin 1. Left to the
    # router it ran on B.Cu under pins 61-70 (cutting the B.Cu under the
    # regulator off from the EP's) or, with that strip kept out
    # (plane_keepout VREG_PINS_B), under the exposed pad or ~70mm round the
    # west side, and it was the net most often left unrouted. On F.Cu it
    # stays out of the B.Cu lanes the ESP32 UART nets take east (a B.Cu run
    # here boxed U103's GND vias in on every trial). R105 (its pull-up)
    # stays with the router.
    u3_1 = pad("U103", "1")
    x_cs = tp[0] - 0.25                        # east of TP101's +1V1 via
    y_cs = tp[1] - 2.1                         # F.Cu run over the VREG block
    v_a = (u3_1[0] + 1.93, y_cs)               # east of QSPI_SCLK, north of C121
    v_w = (u3_1[0] - 0.8, u3_1[1] - 1.98)      # inside SCLK's hook, north-west of U103 pin 1
    path(PSRAM_CS, F, [(xe, v_cs[1]), (xe, tp[1] + 3.4), (x_cs, tp[1] + 1.0),
                       (x_cs, y_cs + 1.1), (x_cs - 1.1, y_cs), v_a])
    via(PSRAM_CS, *v_a)
    path(PSRAM_CS, B, [v_a, (v_w[0] + (v_w[1] - y_cs), y_cs), v_w])
    via(PSRAM_CS, *v_w)
    path(PSRAM_CS, F, [v_w, (u3_1[0] - 0.39, v_w[1] + 0.41), (u3_1[0] - 0.39, u3_1[1] - 0.4), u3_1])

    # AVDD: pin 61 -> C105.1 (C_FILT), R104.2 -> C105.1
    path(AVDD_NET, F, [(x61, y61), (x61, yo), (x61 + 0.3, yo - 0.3),
                       (c5_1[0], yo - 0.3), c5_1], width=0.2)
    path(AVDD_NET, F, [r4_2, c5_1], width=0.25)
    # R104's +3V3 end: the DVDD run, L101 and the pins box it in on F.Cu,
    # and the B.Cu under the block is plane (plane_keepout.py), so the
    # router can only rarely get it out. Take it straight down past C105's
    # east end into C113.1 (+3V3, the pin 60 decoupler just below).
    c113_1 = pad("C113", "1")
    path("+3V3", F, [r4_1, (c113_1[0], r4_1[1]), c113_1], width=0.25)

    # ---- QSPI cluster replay (pilink-2wq) ----------------------------------
    # --no-qspi leaves the QSPI nets to the router; capture_qspi.py then
    # writes a routed result back into qspi_routes.json (how the replay is
    # refreshed when the copper around it changes, pilink-r1h).
    with open(os.path.join(HERE, "qspi_routes.json")) as fh:
        qspi = {} if "--no-qspi" in sys.argv else json.load(fh)
    for short, d in qspi.items():
        net = "/RP2350B + Memory/" + short
        for lay, x0, y0, x1, y1, w in d["tracks"]:
            path(net, F if lay == "F" else B,
                 [(x0 + 100.0, y0 + 100.0), (x1 + 100.0, y1 + 100.0)], width=w)
        for x, y in d["vias"]:
            via(net, x + 100.0, y + 100.0)

    # ---- GND fan-out (pilink-r1h) -------------------------------------------
    # last, so the vias go round everything locked above
    n, misses = fan_out(board)
    check_misses(misses)
    print(f"GND fan-out: {n} vias")

    pcbnew.SaveBoard(BOARD, board)
    print("pre-routed USB D+/D- (J401 -> U401 -> R106/R107 -> U101), XIN/XOUT, backlight, "
          "SW101/SW102 BOOTSEL/RESET + GND escapes, ESP32 decoupling/EN, +3V3 trunk (locked)")
    for n in ("USB_DP", "USB_DM", DP_MCU, DM_MCU):
        print(n, round(sum(t.GetLength() / 1e6 for t in board.GetTracks()
                           if t.GetNetname() == n and t.GetClass() == "PCB_TRACK"), 2), "mm")


if __name__ == "__main__":
    main()
