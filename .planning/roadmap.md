# Roadmap

Full design rationale: `docs/plans/2026-11-13-custom-hardware-design.md`.
Settled component/architecture decisions: `.planning/decisions/`.

## This repo's scope

1. **KiCad schematic + BOM** — component selection, netlist, footprints,
   JLCPCB/LCSC part numbers. Not started.
2. **PCB layout** — first placed and routed board exists
   (`hardware/pico-link-hw.kicad_pcb`, `pilink-7el.9`): 2-layer, 100x55mm,
   DRC 0 errors. Not orderable yet: see "Known gaps" in
   `hardware/README.md`, chiefly `pilink-kt4`. Still needs a human look in
   the KiCad GUI and gerber export.
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

- **Blocks fab:** the schematic never connects the ESP32 to the RP2350
  (`pilink-kt4`) — no HCI UART, EN/BOOT0 control or flashing path in the
  netlist. Found during PCB layout; the routed board inherits it.
- Ezurio Sterling-LWB+ is the documented fallback if the ESP32 coprocessor
  path hits a wall during firmware integration.

## Resolved risks (from documentation; bench test pending)

- ~~ESP32's classic BT controller firmware's exact HCI init behavior
  (vendor-patch step or not) is unconfirmed.~~ Resolved from documentation
  2026-11-14 (bead `pilink-kfa`): no vendor patch-load step needed — the
  controller firmware is flashed once and speaks standard HCI on boot. See
  the 2026-11-14 addendum in
  `.research/findings/2026-11-13-esp32-hci-uart-coprocessor-viability.md`.
  This is confirmed from documentation/primary sources only, not a bench
  test — a hands-on `HCI_Reset` smoke test once real ESP32-WROOM-32U
  hardware exists is still open, tracked as bead `pilink-6c3`. One
  follow-on detail for the schematic (`pilink-7el.4`): the HCI UART needs
  RTS/CTS (4-wire), not just TX/RX — the example's default/recommended
  configuration, not a hard requirement the chip can't run without.
