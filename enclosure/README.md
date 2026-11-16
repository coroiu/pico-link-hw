# Enclosure

OpenSCAD source for the 3D-printed case goes here: two shells (top/bottom),
button plungers, internal antenna mount, rear USB-C cutout.

Not started yet — see "Enclosure" and "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md).

OpenSCAD isn't available in the agent environment this repo was scaffolded
in. A parametric `.scad` file can be authored as code, but rendering and
fit-checking need OpenSCAD installed on a machine that has it.

`cube.scad` is a trivial seed file for the `preview/` docker-compose
service — it proves the OpenSCAD -> STL -> GLB export pipeline end-to-end
before the real enclosure exists. Delete it once the real enclosure from
pilink-8hx lands; the preview pipeline picks up whatever `*.scad` file it
finds here.

## `antenna_mount.scad` (pilink-8hx.4)

Internal mount for the adhesive U.FL 2.4GHz antenna, for the top wall of
the upright desk-clock body
([`.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`](../.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md)).
Not rendered or fit-checked — OpenSCAD still isn't installed in this
environment (see the note above); every dimension in the file cites its
source (hardware/README.md's PCB placement table, the ADR, or
[`.research/findings/2026-11-15-ufl-antenna-selection.md`](../.research/findings/2026-11-15-ufl-antenna-selection.md))
or is marked as this file's own assumption.

- **Part:** Kinghelm KH-FPC2.4G-1.13IPEX-240 (LCSC `C4943394`), the primary
  selected in `pilink-8wx` — 45.8 x 6.5mm adhesive-backed FPC monopole,
  Ø1.13mm IPEX/U.FL-class pigtail. (The AIWF026 alternate from the same
  finding was not chosen: its in-band gain sits fractionally over
  Espressif's cert-safe ceiling.)
- **What's modeled:** a flat adhesive land sized to the element plus a 1mm
  assembly margin (47.8 x 8.5mm), a raised locating lip around three sides,
  a short cable channel + strain-relief clip stub toward the cavity below,
  and non-manifold (`%`) preview markers for the element itself and the
  clearance-guidance keepout zone from the research finding. It is a mount
  feature only, not a full top-wall shell — `pilink-8hx.1`/`pilink-8hx.2`
  own the real top-wall geometry this feature gets instantiated onto; the
  file's own `demo_assembly()` stand-in slab is for local preview only and
  must not be unioned into either shell.
- **Position:** face-local X 57.75-105.55mm, clear of both SW101 (X=44mm)
  and SW102 (X=54mm) top-edge pinholes by construction (3mm margin past
  each pinhole's own ~1.5mm channel radius). A left-of-SW101 placement
  doesn't fit (only 39mm of clear width there, less than the 45.8mm
  element) — fixed per a code-reviewer's NOT APPROVED verdict on the first
  version (PR #48), which had the element physically colliding with
  SW101's pinhole channel. The resulting cable run to U201's U.FL connector
  (face-local X-center ~16mm) is ~48mm, well within the part's ~240mm
  (inferred) pigtail. Board-to-face coordinate mapping (board centered
  left-right, bottom-flush in the face) is the same unconfirmed convention
  hardware/README.md's own placement table already flags as pending
  `pilink-8hx.1`/`.2` confirmation — carried here unchanged rather than
  inventing a different one.
- **Display-panel clearance, checked but not fully resolved:** the new
  position still overlaps the display-panel shadow's face-local X range
  (30-89mm) by 31.25mm — unavoidable, since the panel shadow alone spans
  59mm of the 122mm-wide face and the only clear span past it (X>89mm) is
  ~31mm, less than the element. The panel and the antenna mount sit in
  different structural layers (face vs. top wall), so this is an RF-keepout
  concern, not a second pinhole-style collision — but the actual Z
  (perpendicular-to-face) clearance between the top wall and the panel
  frame/PCB below it can't be checked yet, since no real 3D wall geometry
  exists in this repo (`pilink-8hx.1`/`.2` haven't landed). Flagged
  explicitly in the `.scad` file's comments and its `echo()` output for
  `pilink-8hx.1`/`.2`/`pilink-8hx.5` to actually check once that geometry
  exists.
