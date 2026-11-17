#!/usr/bin/env python3
"""Build the preview's "Files" downloads: JLCPCB fab files + enclosure STLs.

usage: export_fab.py PCB SCH BOM_MD STL_DIR OUT_DIR

Writes, under OUT_DIR (staged by the caller, then swapped in):
  <name>-gerbers.zip      Gerbers (Protel extensions) + Excellon drill (PTH/NPTH)
  <name>-bom-jlcpcb.csv   Comment, Designator, Footprint, LCSC Part #
  <name>-cpl-jlcpcb.csv   Designator, Mid X, Mid Y, Layer, Rotation
  stl/<part>.stl          copied from STL_DIR/stl (one per printed part)
  fab.json                manifest the page builds its Files section from

The schematic carries no LCSC field; the LCSC number per designator lives in
hardware/BOM.md's per-sheet tables, which are parsed here (ranges like
"C106-C117" and comma lists are expanded). DNP parts are excluded from the
BOM and CPL (kicad-cli --exclude-dnp), as hardware/BOM.md assembly flag 0
requires.
"""
import csv
import datetime
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

# Footprint libraries that are project-local (hand-authored or vendor-copied),
# as opposed to KiCad's stock libraries -- see hardware/fp-lib-table.
CUSTOM_LIBS = {"RP2350_80QFN", "Connector_FPC", "Connector_USB_Custom"}
# JLCPCB package rotation offsets (degrees, added after the bottom-side
# conversion), first regex match on the footprint name wins. Transcribed from
# bennymeg/Fabrication-Toolkit plugins/transformations.csv (duplicates
# removed; its Delta X/Y columns are all 0).
ROT_TABLE = [
    ("^Bosch_LGA-", 90), ("^CP_EIA-", 180), ("^CP_Elec_", 180), ("^C_Elec_", 180),
    ("^DFN-", 270), ("^D_SOT-23", 180), ("^HTSSOP-", 270), ("^JST_GH_SM", 180),
    ("^JST_PH_S", 180), ("^LQFP-", 270), ("^MSOP-", 270), ("^PowerPAK_SO-8_Single", 270),
    ("^QFN-", 90), ("^R_Array_Concave_", 90), ("^R_Array_Convex_", 90), ("^SC-74-6", 180),
    ("^SOIC-", 270), ("^SOIC127P798X216-8N", -90), ("^SOP-(?!18_)", 270), ("^SOP-18_", 0),
    ("^SOP-4_", 0), ("^SOT-143", 180), ("^SOT-223", 180), ("^SOT-23", 180),
    ("^SOT-353", 180), ("^SOT-363", 180), ("^SOT-89", 180), ("^SSOP-", 270),
    ("^SW_SPST_B3", 90), ("^TDSON-8-1", 270), ("^TO-277", 90), ("^TQFP-", 270),
    ("^TSOT-23", 180), ("^TSSOP-", 270), ("^UDFN-10", 270), ("^USON-10", 270),
    ("^VSON-8_", 270), ("^VSSOP-10_-", 270), ("^VSSOP-8_", 180), ("^qfn-", 90),
]


def rot_delta(name):
    for pat, deg in ROT_TABLE:
        if re.search(pat, name):
            return float(deg)
    return 0.0
GERBER_LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("%s failed:\n%s%s" % (cmd[:4], p.stdout, p.stderr))


def natkey(d):
    m = re.match(r"([A-Za-z]+)(\d+)", d)
    return (m.group(1), int(m.group(2))) if m else (d, 0)


def expand_refs(cell):
    refs = []
    for tok in re.split(r"[,\s]+", cell.replace("**", "").strip()):
        m = re.fullmatch(r"([A-Za-z]+)(\d+)-(?:\1)?(\d+)", tok)
        if m:
            refs += ["%s%d" % (m.group(1), n) for n in range(int(m.group(2)), int(m.group(3)) + 1)]
        elif re.fullmatch(r"[A-Za-z]+\d+", tok):
            refs.append(tok)
    return refs


def parse_bom_md(path):
    """designator -> LCSC number, from the BOM.md tables that have an LCSC column."""
    lcsc, col = {}, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                col = None
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and cells[0] == "Ref":
                col = cells.index("LCSC") if "LCSC" in cells else None
                continue
            if col is None or col >= len(cells) or set(cells[0]) <= set("-: "):
                continue
            m = re.search(r"\bC\d{3,}\b", cells[col])
            if m:
                for r in expand_refs(cells[0]):
                    lcsc[r] = m.group(0)
    return lcsc


def main():
    pcb, sch, bom_md, stl_dir, out = sys.argv[1:6]
    name = os.path.splitext(os.path.basename(pcb))[0]
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fab")
    files = []

    def add(path, label, desc, **extra):
        files.append(dict(file=os.path.relpath(path, out), label=label, desc=desc,
                          size=os.path.getsize(path), **extra))

    # ---- Gerbers + drill -> zip. Protel extensions (kicad-cli default),
    # soldermask subtracted from silkscreen, zones refilled, no job file;
    # drill is Excellon, mm, decimal zeros, PTH and NPTH in separate files --
    # the settings JLCPCB's KiCad guide asks for.
    gdir = os.path.join(tmp, "gerber")
    os.makedirs(gdir)
    run(["kicad-cli", "pcb", "export", "gerbers", "--layers", GERBER_LAYERS,
         "--subtract-soldermask", "--check-zones", "--no-x2", "-o", gdir, pcb])
    run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon",
         "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
         "--excellon-separate-th", "--drill-origin", "absolute", "-o", gdir, pcb])
    for junk in glob.glob(os.path.join(gdir, "*.gbrjob")):
        os.remove(junk)
    zpath = os.path.join(out, name + "-gerbers.zip")
    layer_files = sorted(os.listdir(gdir))
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in layer_files:
            z.write(os.path.join(gdir, fn), fn)
    add(zpath, "Gerbers + drill (zip)",
        "%d files: 2-layer copper, mask, silkscreen, paste, edge cuts (Protel "
        "extensions) + Excellon PTH/NPTH drill. Upload to JLCPCB as-is." % len(layer_files),
        contents=layer_files)

    # ---- BOM: one kicad-cli row per placed designator, regrouped here so the
    # LCSC number (from BOM.md) is part of the grouping key.
    raw_bom = os.path.join(tmp, "bom.csv")
    run(["kicad-cli", "sch", "export", "bom", "--exclude-dnp",
         "--fields", "Reference,Value,Footprint", "--labels", "Designator,Value,Footprint",
         "--group-by", "", "-o", raw_bom, sch])
    lcsc = parse_bom_md(bom_md)
    with open(raw_bom, newline="", encoding="utf-8") as f:
        placed = [r for r in csv.DictReader(f) if r["Designator"]]
    groups, order = {}, []
    for r in placed:
        key = (r["Value"], r["Footprint"].split(":", 1)[-1], lcsc.get(r["Designator"], ""))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r["Designator"])
    bpath = os.path.join(out, name + "-bom-jlcpcb.csv")
    with open(bpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for key in sorted(order, key=lambda k: min(natkey(d) for d in groups[k])):
            w.writerow([key[0], ",".join(sorted(groups[key], key=natkey)), key[1], key[2]])
    missing = sorted((r["Designator"] for r in placed if r["Designator"] not in lcsc), key=natkey)
    add(bpath, "BOM (JLCPCB CSV)",
        "%d placed parts in %d lines; DNP excluded. Columns: Comment, Designator, "
        "Footprint, LCSC Part #. LCSC numbers come from hardware/BOM.md." % (len(placed), len(order)))

    # ---- CPL, top and bottom in one file. kicad-cli's pos export gives the
    # footprint ANCHOR and KiCad's rotation; JLCPCB wants the part CENTRE and
    # its own rotation convention, so positions/rotations are recomputed with
    # pcbnew the way bennymeg/Fabrication-Toolkit (plugins/process.py,
    # _get_footprint_position + generate_tables) does it:
    #   centre   = centre of the bounding box of all the footprint's pads
    #   Y        = -Y (KiCad's Y points down)
    #   bottom   = rotation 180 - rot ("JLC expect Rotation as viewed from
    #              above"; same in Bouni/kicad-jlcpcb-tools fabrication.py)
    #   package offset = ROT_TABLE (Fabrication-Toolkit transformations.csv)
    #   rotation normalised to [0, 360)
    # kicad-cli's pos export stays as the reference for the set of placed
    # parts and the raw anchor/rotation (cross-checked below).
    import pcbnew
    raw_pos = os.path.join(tmp, "pos.csv")
    run(["kicad-cli", "pcb", "export", "pos", "--exclude-dnp", "--format", "csv",
         "--units", "mm", "--side", "both", "-o", raw_pos, pcb])
    with open(raw_pos, newline="", encoding="utf-8") as f:
        ref_pos = {r["Ref"]: r for r in csv.DictReader(f)}
    board = pcbnew.LoadBoard(pcb)
    cpl = []
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES or fp.IsDNP():
            continue
        ax, ay = fp.GetPosition().x / 1e6, -fp.GetPosition().y / 1e6
        rot = fp.GetOrientation().AsDegrees()
        bottom = fp.GetLayer() != pcbnew.F_Cu
        pads = list(fp.Pads())
        cx, cy = ax, ay
        if pads and rot % 90 == 0:
            bb = pads[0].GetBoundingBox()
            for pd in pads:
                bb.Merge(pd.GetBoundingBox())
            cx, cy = bb.GetCenter().x / 1e6, -bb.GetCenter().y / 1e6
        fname = str(fp.GetFPID().GetLibItemName())
        delta = rot_delta(fname)
        cpl.append(dict(ref=fp.GetReference(), x=cx, y=cy, ax=ax, ay=ay,
                        side="bottom" if bottom else "top",
                        rot=(((180.0 - rot) if bottom else rot) + delta) % 360.0,
                        kicad_rot=rot, delta=delta,
                        fp=str(fp.GetFPID().GetLibNickname()) + ":" + fname))
    cpl.sort(key=lambda r: natkey(r["ref"]))
    if {r["ref"] for r in cpl} != set(ref_pos):
        raise RuntimeError("pcbnew/kicad-cli placed-part mismatch: %s"
                           % sorted({r["ref"] for r in cpl} ^ set(ref_pos)))
    for r in cpl:
        k = ref_pos[r["ref"]]
        drot = (float(k["Rot"]) - r["kicad_rot"] + 180) % 360 - 180
        if abs(float(k["PosX"]) - r["ax"]) > 1e-3 or abs(float(k["PosY"]) - r["ay"]) > 1e-3 \
                or abs(drot) > 1e-3:
            raise RuntimeError("pcbnew anchor/rotation disagrees with kicad-cli for " + r["ref"])
    cpath = os.path.join(out, name + "-cpl-jlcpcb.csv")
    with open(cpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in cpl:
            w.writerow([r["ref"], "%.4f" % r["x"], "%.4f" % r["y"],
                        "Top" if r["side"] == "top" else "Bottom", "%g" % round(r["rot"], 4)])
    nbot = sum(1 for r in cpl if r["side"] == "bottom")
    add(cpath, "CPL / pick-and-place (JLCPCB CSV)",
        "%d parts (%d top, %d bottom); DNP excluded. Mid X/Y = pad-bbox centre; bottom "
        "rotation = 180 - KiCad rotation; package offsets applied; rotation in [0,360)."
        % (len(cpl), len(cpl) - nbot, nbot))

    # ---- Parts to double-check in JLCPCB's placement preview, by name.
    flagged = []
    for r in cpl:
        d, why = r["ref"], []
        shift = math.hypot(r["x"] - r["ax"], r["y"] - r["ay"])
        custom = r["fp"].split(":")[0] in CUSTOM_LIBS
        if r["delta"]:
            why.append("package rotation offset %+g applied (Fabrication-Toolkit table)" % r["delta"])
        if r["side"] == "bottom" and not re.match(r"[RC]\d", d):
            why.append("bottom side: rotation converted with 180 - rot")
        if shift > 0.1:
            why.append("CPL centre is %.2f mm from the footprint anchor" % shift)
            print("[fab] %s: anchor (%.4f, %.4f) -> centre (%.4f, %.4f), %.2f mm; rot KiCad %g -> JLCPCB %g"
                  % (d, r["ax"], r["ay"], r["x"], r["y"], shift, r["kicad_rot"], r["rot"]))
        if custom:
            why.append("custom/project-local footprint: JLCPCB's part model may be oriented differently")
        if d not in lcsc:
            why.append("no LCSC number (BOM.md lists it as not in JLCPCB's catalog)")
        if not r["delta"] and not custom and re.match(r"(U|J|SW|Y|D)\d", d):
            why.append("no known JLCPCB rotation offset for this package; verify orientation in the preview")
        if why:
            flagged.append(dict(ref=d, footprint=r["fp"], reasons=why))

    # ---- Enclosure STLs, one per printed part: whatever export_enclosure.py
    # rendered (the part list is not duplicated here).
    labels = {}
    parts_json = os.path.join(stl_dir, "parts.json")
    if os.path.exists(parts_json):
        with open(parts_json) as f:
            labels = {p["key"]: p["label"] for p in json.load(f).get("parts", [])}
    notes = {}
    notes_json = os.path.join(stl_dir, "stl", "orientation.json")
    if os.path.exists(notes_json):
        with open(notes_json) as f:
            notes = json.load(f)
    os.makedirs(os.path.join(out, "stl"), exist_ok=True)
    for src in sorted(glob.glob(os.path.join(stl_dir, "stl", "*.stl"))):
        key = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(out, "stl", key + ".stl")
        shutil.copyfile(src, dst)
        add(dst, "STL: " + labels.get(key, key),
            "Print orientation: " + notes.get(key, "as rendered by OpenSCAD (no print "
                                                  "orientation defined for this part)."),
            group="stl")

    manifest = dict(
        generated=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        commit=os.environ.get("FAB_SOURCE_COMMIT", "unknown"), files=files,
        missing_lcsc=missing, flagged=flagged, placed=len(placed), cpl_rows=len(cpl))
    with open(os.path.join(out, "fab.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    print("[fab] %d files; BOM %d parts (%d without LCSC), CPL %d rows, %d flagged"
          % (len(files), len(placed), len(missing), len(cpl), len(flagged)))


if __name__ == "__main__":
    main()
