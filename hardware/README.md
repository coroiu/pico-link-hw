# Hardware

KiCad project goes here: schematic, PCB layout, footprints, and a BOM with
JLCPCB/LCSC part numbers.

Not started yet — see "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md)
for scope, and `.planning/decisions/` for the component choices already
settled (MCU, radio coprocessor, display, memory).

Neither KiCad nor its CLI is available in the agent environment this repo was
scaffolded in. A schematic/BOM can be authored as real KiCad project files,
but PCB routing, DRC/ERC, and gerber export need to happen in the KiCad GUI
on a machine that has it installed.
