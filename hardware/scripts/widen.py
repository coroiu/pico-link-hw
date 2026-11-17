#!/usr/bin/env python3
"""Widen power tracks wherever DRC allows it (pilink-7el.12, pilink-yt5).

Usage (from hardware/):  python3 scripts/widen.py

Run after scripts/route.py and before scripts/zones.py (it removes zones so
stale fills cannot confuse DRC; zones.py re-creates them).

Freerouting routes each net at one width, and the rails that touch the
RP2350B's 0.4mm-pitch pads have to be routed at 0.2mm to get into them.
This pass widens every segment of those rails in tiers: it sets them to the
widest tier, runs DRC, puts back any segment DRC objects to, and repeats
until DRC is quiet; segments that could not take that tier then try the next
narrower one. So the rails end up as wide as the space allows and necked
down only where they must be (pilink-yt5: one 0.4mm tier used to leave long
0.2mm runs wherever 0.4 did not fit, though 0.3 would have).
"""
import json
import os
import subprocess
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
# net -> widths to try, widest first (mm)
TIERS = {
    "+3V3": (0.8, 0.6, 0.4, 0.3),
    "/USB-C/VBUS_RAW": (0.8, 0.6, 0.4, 0.3),
    "+1V1": (0.4, 0.3),
    "/RP2350B + Memory/VREG_LX": (0.4, 0.3),
}
MM = pcbnew.FromMM


def drc_uuids():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error",
                        "--format", "json", "-o", out, BOARD],
                       check=True, stdout=subprocess.DEVNULL)
        with open(out) as fh:
            rep = json.load(fh)
    ids = set()
    for v in rep.get("violations", []) + rep.get("unconnected_items", []):
        for item in v.get("items", []):
            ids.add(item["uuid"])
    return ids


def main():
    board = pcbnew.LoadBoard(BOARD)
    for z in list(board.Zones()):
        board.Remove(z)
    segs = {t.m_Uuid.AsString(): t for t in board.GetTracks()
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() in TIERS}
    start = {u: t.GetWidth() for u, t in segs.items()}
    levels = sorted({w for ws in TIERS.values() for w in ws}, reverse=True)
    rounds = 0
    for w in levels:
        before = {}
        for u, t in segs.items():
            if w in TIERS[t.GetNetname()] and t.GetWidth() < MM(w):
                before[u] = t.GetWidth()
                t.SetWidth(MM(w))
        if not before:
            continue
        pcbnew.SaveBoard(BOARD, board)
        trying = set(before)
        for _ in range(20):
            rounds += 1
            offenders = drc_uuids() & trying
            if not offenders:
                break
            for u in offenders:
                segs[u].SetWidth(before[u])
            trying -= offenders
            pcbnew.SaveBoard(BOARD, board)
        else:
            raise SystemExit(f"widen: DRC did not converge at {w}mm")
        print(f"  {w}mm: {len(trying)} of {len(before)} segments")
    widened = sum(1 for u, t in segs.items() if t.GetWidth() > start[u])
    narrow = sum(1 for t in segs.values() if t.GetWidth() <= MM(0.2))
    print(f"widened {widened} of {len(segs)} power segments ({rounds} DRC rounds); "
          f"{narrow} still <= 0.2mm")


if __name__ == "__main__":
    main()
