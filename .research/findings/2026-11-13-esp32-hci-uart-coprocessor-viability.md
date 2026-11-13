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

## Open question (unresolved — flag for firmware work)

Whether ESP32's classic BT controller firmware needs a vendor-specific
init/firmware-patch step before it behaves as a plain, standard-compliant
HCI device — the way some Broadcom chips require a firmware/.hcd patch
upload at HCI init time before they answer normally. This wasn't confirmed
either way during this research pass. It doesn't change the hardware design
(same UART pins either way), but it affects how much firmware-side glue
BTstack's chipset-init layer needs for ESP32 specifically.

## Informs

`.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`.
