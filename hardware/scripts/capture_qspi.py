#!/usr/bin/env python3
"""Capture the routed QSPI copper into qspi_routes.json (pilink-r1h).

Usage (from hardware/):
    python3 scripts/capture_qspi.py            # compare only
    python3 scripts/capture_qspi.py --write    # and overwrite the json

preroute.py replays scripts/qspi_routes.json as locked copper so the QSPI
bus (SCLK, SD0-3, SS) does not change from run to run. When the copper
around it changes, refresh it: preroute.py --no-qspi -> route.py, then this
script. It prints, per net, the length / vias / B.Cu length of the routed
board next to the json's, and with --write replaces the json only if no net
got longer than it was (the "master lengths or better" rule).
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
JSON = os.path.join(HERE, "qspi_routes.json")
NETS = ("QSPI_SCLK", "QSPI_SD0", "QSPI_SD1", "QSPI_SD2", "QSPI_SD3", "QSPI_SS")
PREFIX = "/RP2350B + Memory/"
O = 100.0


def stats(d):
    length = sum(((t[3] - t[1]) ** 2 + (t[4] - t[2]) ** 2) ** 0.5 for t in d["tracks"])
    blen = sum(((t[3] - t[1]) ** 2 + (t[4] - t[2]) ** 2) ** 0.5
               for t in d["tracks"] if t[0] == "B")
    return length, len(d["vias"]), blen


def main():
    board = pcbnew.LoadBoard(BOARD)
    new = {}
    for short in NETS:
        d = {"tracks": [], "vias": []}
        for t in board.GetTracks():
            if t.GetNetname() != PREFIX + short:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                p = t.GetPosition()
                d["vias"].append([round(pcbnew.ToMM(p.x) - O, 3), round(pcbnew.ToMM(p.y) - O, 3)])
            elif t.Type() == pcbnew.PCB_TRACE_T:
                s, e = t.GetStart(), t.GetEnd()
                d["tracks"].append(["F" if t.GetLayer() == pcbnew.F_Cu else "B",
                                    round(pcbnew.ToMM(s.x) - O, 3), round(pcbnew.ToMM(s.y) - O, 3),
                                    round(pcbnew.ToMM(e.x) - O, 3), round(pcbnew.ToMM(e.y) - O, 3),
                                    round(pcbnew.ToMM(t.GetWidth()), 3)])
        new[short] = d
    with open(JSON) as fh:
        old = json.load(fh)
    worse = []
    print(f"{'net':10} {'json mm/vias/B.Cu mm':>24} {'board mm/vias/B.Cu mm':>24}")
    for short in NETS:
        lo, vo, bo = stats(old[short])
        ln, vn, bn = stats(new[short])
        print(f"{short:10} {lo:12.2f} {vo:3d} {bo:6.2f}   {ln:12.2f} {vn:3d} {bn:6.2f}")
        if ln > lo + 0.01:
            worse.append(short)
    if "--write" in sys.argv:
        if worse:
            sys.exit("not written: longer than the json for " + ", ".join(worse))
        with open(JSON, "w") as fh:
            json.dump(new, fh, indent=0)
            fh.write("\n")
        print("qspi_routes.json updated")


if __name__ == "__main__":
    main()
