# Pico Link — custom hardware

Custom PCB and 3D-printed enclosure design for
[Pico Link](https://github.com/coroiu/pico-link), a USB-to-Bluetooth LDAC
audio dongle with a screen. This repo replaces the two stacked off-the-shelf
dev boards the project currently runs on with a single purpose-built board,
designed for JLCPCB fab + assembly.

See the design doc for the full rationale:
[`docs/plans/2026-11-13-custom-hardware-design.md`](docs/plans/2026-11-13-custom-hardware-design.md).

## Layout

- `hardware/` — KiCad project: schematic, PCB, footprints, BOM/JLCPCB part numbers.
- `enclosure/` — OpenSCAD source for the 3D-printed case.
- `docs/plans/` — design docs.
- `.planning/`, `.research/` — decision records and research findings, kept
  separate from the ephemeral issue tracker (see `AGENTS.md`).

Both `hardware/` and `enclosure/` are placeholders pending the next
implementation pass — see the design doc's "Deliverables" section.

## Status

No firmware lives in this repo — that's [coroiu/pico-link](https://github.com/coroiu/pico-link).
This repo only tracks the physical design: PCB, BOM, enclosure.
