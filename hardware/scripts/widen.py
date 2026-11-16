#!/usr/bin/env python3
"""Widen power tracks wherever DRC allows it (pilink-7el.12).

Usage (from hardware/):  python3 scripts/widen.py

Run after scripts/route.py and before scripts/zones.py (it removes zones so
stale fills cannot confuse DRC; zones.py re-creates them).

Freerouting routes each net at one width, and the rails that touch the
RP2350B's 0.4mm-pitch pads have to be routed at 0.2mm to get into them.
This pass sets every segment of those rails to WIDE, runs DRC, puts back
any segment DRC objects to, and repeats until DRC is quiet -- so the rails
end up wide in open board and necked down only at fine-pitch pins.
"""
import json
import os
import subprocess
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
NETS = ["+3V3", "+1V1", "/RP2350B + Memory/VREG_LX", "/USB-C/VBUS_RAW"]
WIDE = 0.4
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
    original = {}
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() in NETS \
                and t.GetWidth() < MM(WIDE):
            original[t.m_Uuid.AsString()] = (t, t.GetWidth())
            t.SetWidth(MM(WIDE))
    pcbnew.SaveBoard(BOARD, board)

    widened = set(original)
    for rounds in range(1, 20):
        offenders = drc_uuids() & widened
        if not offenders:
            break
        for u in offenders:
            t, w = original[u]
            t.SetWidth(w)
        widened -= offenders
        pcbnew.SaveBoard(BOARD, board)
    else:
        raise SystemExit("widen: DRC did not converge")
    print(f"widened {len(widened)} of {len(original)} power segments to {WIDE}mm "
          f"({rounds} DRC rounds)")


if __name__ == "__main__":
    main()
