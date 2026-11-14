# ESP32-WROOM-32U as the BT Classic coprocessor, not RM2

## Context

The off-the-shelf Pico Plus 2 W board this project is replacing uses
Raspberry Pi's RM2 module (Infineon CYW43439 + antenna + matching, pre-tuned
and pre-certified) for Bluetooth Classic + LE. A custom board needs to decide
how to provide Bluetooth Classic (required for A2DP/LDAC — BLE-only chips
can't do this). The user reported the antenna on their existing Pico Plus 2 W
board is weak and wants that fixed in the custom hardware, with the antenna
staying fully inside the enclosure (no external stub poking out).

## Decision

Use RP2350B for USB audio + display/UI (unchanged from the existing
approach), and a separate ESP32-WROOM-32U module as a dedicated Bluetooth
Classic coprocessor. The ESP32 runs Espressif's official HCI-over-UART
controller firmware and is exposed to BTstack (running on RP2350) as a
standard HCI Bluetooth controller — no profile-level Bluetooth code (A2DP,
AVRCP) runs on the ESP32. RP2350 can double as a USB-to-UART bridge into the
ESP32's boot ROM, so ESP32 firmware updates ride over the same USB cable as
everything else.

## Rationale

- RM2's antenna is a fixed onboard PCB trace with no external-antenna
  option — confirmed via Raspberry Pi's own RM2 datasheet and product
  listings. It cannot be improved without replacing the radio entirely.
- ESP32-WROOM-32U (the U.FL-antenna variant) is confirmed stocked at
  JLCPCB/LCSC for SMT assembly, in multiple flash-size variants — so unlike
  RM2, nothing on the resulting board needs hand-soldering.
- Small adhesive-backed U.FL antennas exist specifically for mounting inside
  a plastic enclosure (e.g. SparkFun WRL-18086-class), satisfying the
  "antenna stays inside the case" requirement.
- Espressif's own "ESP-Hosted, Bluetooth-only, UART HCI" mode is built
  exactly for this shape: pairing ESP32's BT Classic radio with an external
  host stack that isn't Bluedroid. BTstack already ships reference chipset
  init code for Broadcom/Cypress/Infineon BT chips over UART — this is the
  industry-standard way to integrate this chip family, not a novel hack.
- ESP-IDF not having its own A2DP source API is a non-issue: in this
  architecture the ESP32 never runs profile-level Bluetooth code at all.
  HCI is a standardized split — the controller (radio/baseband) sits below
  it, the host (L2CAP, AVDTP, A2DP) sits above it and can be any compliant
  stack. BTstack stays the host; only the controller chip changes.

## Alternatives considered

- **Raw CYW43439 + custom antenna matching.** Full control over the RF
  design, but real RF layout risk and the project would take on its own
  regulatory certification instead of inheriting a pre-certified module's.
  Rejected — not worth the risk when pre-certified alternatives exist.
- **Ezurio Sterling-LWB+ (same CYW43439 silicon, MHF4/U.FL variant).** Same
  chip family as RM2 — in principle the smallest conceptual change, staying
  on one MCU. But it exposes SDIO/HS-UART rather than RM2's gSPI, so the
  firmware's Bluetooth transport would need the same kind of rewrite as the
  ESP32 path anyway, and Sterling-LWB+'s pin-level integration details
  weren't confirmable without an Ezurio distributor account. Shelved, not
  ruled out — worth revisiting if the ESP32 path hits a wall.

## Consequences

- Firmware needs a new BTstack transport (HCI-over-UART, replacing the
  gSPI-based `cyw43-driver` glue) and an ESP32 flashing/bridge path. This is
  firmware work, tracked separately — it does not block the hardware design.
- Two MCUs instead of one. More board area and one more UART link to design
  and flow-control, in exchange for antenna freedom and dramatically simpler
  sourcing/assembly than either of the alternatives.
- Resolved from documentation 2026-11-14 (bead `pilink-kfa`): ESP32's
  classic BT controller does **not** need a Broadcom-style runtime
  firmware/.hcd patch-load step. Espressif's own `controller_hci_uart`
  example and BTstack's chipset-driver registry (no `esp32` entry, unlike
  `bcm`/`csr`/`cc256x`) confirm the controller firmware is flashed once
  (standard `idf.py flash`, the same UART-bootloader path already planned
  for field updates) and answers standard HCI immediately on boot
  thereafter — no per-session vendor command handshake. See the 2026-11-14
  addendum in
  `.research/findings/2026-11-13-esp32-hci-uart-coprocessor-viability.md`
  for sources. This is confirmed from documentation/primary sources, not a
  bench test — a hands-on `HCI_Reset` smoke test once real
  ESP32-WROOM-32U hardware exists is still open, tracked as bead
  `pilink-6c3`. One detail that *does* carry into the schematic
  (`pilink-7el.4`): the HCI UART needs RTS/CTS wired (4-wire, hardware flow
  control, the example's default/recommended configuration — not a
  hard requirement the chip can't run without), separate from the UART0
  pins used for flashing.
