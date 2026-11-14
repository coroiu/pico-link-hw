# Roadmap

Full design rationale: `docs/plans/2026-11-13-custom-hardware-design.md`.
Settled component/architecture decisions: `.planning/decisions/`.

## This repo's scope

1. **KiCad schematic + BOM** — component selection, netlist, footprints,
   JLCPCB/LCSC part numbers. Not started.
2. **PCB layout** — routing, DRC, gerber export. Needs the KiCad GUI; not
   something this repo's design pass alone can finish without a human at
   the tool.
3. **OpenSCAD enclosure** — two shells, button plungers, rear USB-C cutout,
   internal antenna mount. Not started.
4. **Fit/assembly verification** — once 2 and 3 exist, check the board
   actually fits the case, antenna placement clears the ground plane and the
   USB-C end, and buttons align with the plungers.

## Tracked elsewhere (firmware repo), unblocked by this work

These don't live in this repo, but the hardware decisions above create them
as follow-up work on the firmware side:

- BTstack transport: move from the gSPI-based `cyw43-driver` glue to
  HCI-over-UART, to talk to the ESP32-WROOM-32U coprocessor instead of RM2.
- ESP32 HCI-controller firmware flashing + the RP2350-as-USB-UART-bridge
  path for field updates.
- On-device UI relayout for the new 320x170 display (was built for a 240x240
  square canvas).

## Live risks

- Ezurio Sterling-LWB+ is the documented fallback if the ESP32 coprocessor
  path hits a wall during firmware integration.

## Resolved risks

- ~~ESP32's classic BT controller firmware's exact HCI init behavior
  (vendor-patch step or not) is unconfirmed.~~ Resolved 2026-11-14
  (bead `pilink-kfa`): no vendor patch-load step needed — the controller
  firmware is flashed once and speaks standard HCI on boot. See the
  2026-11-14 addendum in
  `.research/findings/2026-11-13-esp32-hci-uart-coprocessor-viability.md`.
  One follow-on detail for the schematic (`pilink-7el.4`): the HCI UART
  needs RTS/CTS (4-wire), not just TX/RX.
