# ESP32 as a BT Classic HCI-over-UART coprocessor: viability and open question

## Question

Can an ESP32 (original, not S3/C3/C6 — those are BLE-only) act as a pure
Bluetooth Classic radio for an external host's own Bluetooth stack (BTstack,
running on RP2350), rather than running ESP-IDF's own Bluedroid/A2DP stack?

## Findings

- Yes — this is an officially supported Espressif architecture, not a hack.
  Espressif's **ESP-Hosted** project explicitly documents a
  "Bluetooth-only, UART HCI" mode: "classic Bluetooth is supported on ESP32
  only (BR/EDR) ... UART is the direct UART HCI transport (recommended for
  Bluetooth-only applications) ... ESP-Hosted is not involved in
  transporting HCI data" once configured this way. This is built
  specifically for pairing ESP32's BT Classic radio with an external host
  stack that isn't Bluedroid (e.g. a Linux host running BlueZ) — our case
  (BTstack on RP2350) is the same shape.
- This means ESP-IDF not having its own A2DP *source* support is irrelevant
  to this design: in this mode, the ESP32 never runs any profile-level
  Bluetooth code (A2DP, AVRCP, etc.) at all. HCI is a standardized
  controller/host split — the controller (radio/baseband/link-layer) sits
  below HCI and is vendor firmware; the host (L2CAP, SDP, AVDTP, A2DP) sits
  above it and can be any compliant stack. BTstack remains the host and
  keeps its existing A2DP/LDAC source code unchanged; only the controller
  chip changes, from CYW43439 to ESP32's classic radio.
- ESP32-WROOM-32U (U.FL antenna variant) is confirmed stocked at
  JLCPCB/LCSC for SMT assembly, in multiple flash-size variants
  (N4/N8/N16/H4) — checked JLCPCB and LCSC part listings directly. So unlike
  RM2, nothing on the resulting board needs hand-soldering.
- RP2350 can double as a USB-to-UART bridge into the ESP32's boot ROM (the
  same mechanism `esptool.py` uses on any ESP32 dev board — hold GPIO0 low,
  reset, flash over UART), so ESP32 firmware updates can ride over the same
  USB cable used for everything else, with no extra port or header needed.

## Open question (resolved from documentation 2026-11-14 — see addendum below; bench confirmation pending, `pilink-6c3`)

Whether ESP32's classic BT controller firmware needs a vendor-specific
init/firmware-patch step before it behaves as a plain, standard-compliant
HCI device — the way some Broadcom chips require a firmware/.hcd patch
upload at HCI init time before they answer normally. This wasn't confirmed
either way during this research pass. It doesn't change the hardware design
(same UART pins either way), but it affects how much firmware-side glue
BTstack's chipset-init layer needs for ESP32 specifically.

## Informs

`.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`.

## 2026-11-14 addendum: open question resolved — no vendor patch-load step needed

Followed up on the open question above (bead `pilink-kfa`). Checked
Espressif's own ESP-IDF example/docs and BTstack's chipset-driver registry
directly. Short answer: **no**, the ESP32's classic BT controller does not
need a Broadcom-style runtime firmware/.hcd patch upload before it behaves
as a plain, standard-compliant HCI device. It comes up ready to speak H4
over UART immediately after the one-time `idf.py flash` that puts
Espressif's controller firmware on the chip.

- The current, consolidated ESP-IDF example
  `examples/bluetooth/hci/controller_hci_uart` (README fetched from
  `github.com/espressif/esp-idf`, `master` branch, 2026-11-14) states: "HCI
  UART transport is initialized automatically in `esp_bt_controller_init()`"
  and "After startup, HCI messages can be exchanged over the configured HCI
  UART" — no additional patch-load or vendor-init handshake step appears
  anywhere in the setup flow. The only per-deployment requirement is a
  one-time `idf.py -p PORT flash` (standard esptool/UART-bootloader flash,
  the same mechanism already planned for field updates via the
  RP2350-as-USB-UART-bridge path), after which the controller firmware is
  resident in the ESP32's own flash and runs on every boot without the host
  reloading anything.
- The same README flags one caveat worth separating from the "patch load"
  question: "ensure Espressif Vendor-specific HCI commands are **not**
  enabled (disabled by default)... when using a third-party host stack"
  (`components/bt/include/$IDF_TARGET/include/esp_bt_vs.h`). This confirms
  the inverse of a patch requirement — Espressif's own vendor HCI
  extensions are optional and off by default, so standard-only operation
  (which is all BTstack needs) is the out-of-the-box state, not something
  that has to be unlocked.
- Espressif's security advisory
  (`AR2025-004_Security_Advisory_Follow-Up_Updates_and_Fixes_Regarding_ESP32_Undocumented_Bluetooth_Commands_en.pdf`,
  `documentation.espressif.com`) corroborates this from the opposite
  direction: it describes Espressif restricting/disabling undocumented
  vendor HCI commands for serial-HCI use cases, not requiring any vendor
  command before standard operation.
- BTstack's own chipset-driver registry is the strongest corroborating
  signal: `chipset/README.md` and the `chipset/` directory listing in
  `github.com/bluekitchen/btstack` (fetched 2026-11-14) list
  chipset-specific init/patch drivers for Broadcom **and** Infineon/Cypress
  CYW-series parts (both share the same `bcm` folder and
  `btstack_chipset_bcm.c` code — Infineon acquired Cypress's Bluetooth/Wi-Fi
  division, which had itself acquired Broadcom's), CSR (`csr`), TI
  (`cc256x`), Atmel/Microchip ATWILC3000 (`atwilc3000`, an unrelated part,
  not a Cypress/Infineon chip), Realtek, NXP, Intel, etc. — chips that do
  need a runtime init script or firmware patch (typically a `.hcd` file)
  before BTstack can use them. **There is no `esp32` entry/folder in that
  list.** The README's Espressif section instead just describes the ESP32
  as a SoC whose "HCI Controller is implemented in software and accessed
  via a... Virtual HCI (VHCI) interface" and that it "can be configured as
  a regular Bluetooth HCI Controller" — i.e. BTstack's own maintainers
  don't model ESP32 as needing a chipset_t patch driver at all, **unlike**
  Broadcom/Infineon/Cypress/CSR/TI chips: those need the host to push a
  firmware patch over HCI at every power-up, while ESP32 does not (see
  below for why).
- Why the mechanism differs from Broadcom: Broadcom/CSR/TI radio chips ship
  with only a minimal/generic ROM-resident link-layer and need the *host*
  to push a full firmware image over HCI vendor commands on every power-up
  (no onboard flash to persist it, and the patch is module/antenna-variant
  specific). The ESP32 is a SoC with its own QSPI flash: Espressif's full
  controller stack is compiled and flashed into that flash once (at
  manufacture/programming time, not at every HCI session), so there is
  nothing for the external host (RP2350/BTstack) to upload at runtime — the
  "patch" step Broadcom chips need happens once, at flash time, not as part
  of the BTstack chipset-init handshake.

**Hardware-relevant detail surfaced by this pass** (for the schematic bead,
`pilink-7el.4`, which blocks on this one): the `controller_hci_uart`
example's ESP32 defaults use hardware flow control enabled — the HCI UART
is a 4-wire link (TX 5, RX 18, RTS 19, CTS 23 in the example's
`sdkconfig.defaults.esp32`, all remappable via the GPIO matrix/menuconfig)
at 921600 baud, separate from UART0 (used for esptool flashing/logging).
This isn't a new constraint — it's consistent with "same UART pins either
way" in the original finding above — but confirms the BTstack-facing link
needs RTS/CTS wired, not just TX/RX, and that the flashing UART and the HCI
UART are two distinct UART peripherals on the ESP32 side.

**Still unverified / needs hands-on confirmation:** this resolves the
controller-firmware-load question from documentation and primary sources,
not from a bench test. Actually wiring an ESP32-WROOM-32U to a host and
confirming a clean `HCI_Reset` round-trip over UART at the chosen baud rate
once real hardware exists is still worth a quick firmware-side smoke test
before fully relying on it — standard due diligence, not because anything
found here suggests a patch step is hiding. Tracked as bead `pilink-6c3`
(discovered-from `pilink-kfa`).

Sources:
- https://github.com/espressif/esp-idf/blob/master/examples/bluetooth/hci/controller_hci_uart/README.md
- https://github.com/bluekitchen/btstack/blob/master/chipset/README.md
- https://documentation.espressif.com/AR2025-004_Security_Advisory_Follow-Up_Updates_and_Fixes_Regarding_ESP32_Undocumented_Bluetooth_Commands_en.pdf
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/bt-architecture/overview.html
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/classic-bt/overview.html
