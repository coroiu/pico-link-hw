# Pico Link custom hardware — design

## Why

Pico Link currently runs on two stacked off-the-shelf boards: a Pimoroni Pico
Plus 2 W (RP2350B + Raspberry Pi RM2 radio module) and a Waveshare
Pico-LCD-1.3 (240x240 ST7789, 5-way joystick + 4 buttons). The goal is a single
custom PCB, built for JLCPCB fab + assembly, plus a 3D-printed enclosure —
replacing the stack with purpose-built hardware, fixing the weak antenna, and
upgrading the display.

## Architecture

```
USB-C (rear-exit) ──► RP2350B ──SPI──► ST7789V panel (1.9", 320x170)
                        │   │
                        │   └─GPIO──► 5-way joystick + 4 buttons
                        │
                        ├─QSPI──► 16MB NOR flash (W25Q128JV-class)
                        ├─QSPI──► 8MB PSRAM (APS6404L-3SQR-ZR-class)
                        │
                        └─UART──► ESP32-WROOM-32U (BT Classic HCI coprocessor)
                                        │
                                        └─U.FL──► internal adhesive antenna
```

RP2350B remains the main MCU: USB Audio Class device, display/UI, app logic
(largely the existing C/Rust codebase). Flash and PSRAM parts are unchanged
from the Pimoroni board, so the existing SDK patches and memory layout should
carry over without rework.

### Bluetooth: ESP32 as a coprocessor, not RM2

RM2 (Raspberry Pi's CYW43439-based radio module) was the obvious default —
it's what the Pimoroni board uses, pre-certified, no RF design needed — but
its antenna is fixed (onboard PCB trace, no external-antenna option), and the
whole reason for this redesign is a weak antenna. Alternatives considered:

- **Raw CYW43439 + custom antenna matching.** Full control, but real RF
  layout risk and self-certification burden. Rejected — not worth it when a
  pre-certified alternative exists.
- **Ezurio Sterling-LWB+ (same CYW43439 silicon, MHF4/U.FL variant).**
  Smaller conceptual change (still one MCU, same chip family), but exposes
  SDIO/HS-UART rather than RM2's gSPI, and sourcing/integration docs weren't
  confirmable without an Ezurio distributor account. Shelved, not ruled out —
  revisit if the ESP32 path hits problems.
- **ESP32-WROOM-32U as a dedicated BT Classic coprocessor (chosen).** RP2350B
  keeps USB audio + UI; a second, cheap, U.FL-antenna ESP32 module runs
  Espressif's official HCI-over-UART controller firmware and is exposed to
  BTstack (on RP2350) as a standard HCI Bluetooth controller. No profile-level
  Bluetooth code runs on the ESP32 — A2DP/LDAC source logic stays in BTstack,
  unchanged. This is the architecture Espressif's own "ESP-Hosted,
  Bluetooth-only, UART HCI" mode is built for.

  Confirmed via research: ESP32-WROOM-32U is stocked at JLCPCB/LCSC for SMT
  assembly (multiple flash-size variants) — so unlike RM2, nothing on this
  board needs hand-soldering. RP2350 can double as a USB-to-UART bridge into
  the ESP32's boot ROM, so ESP32 firmware updates ride over the same USB
  cable used for everything else (no extra port).

  Open item to verify during firmware work: whether ESP32's classic BT
  controller needs a vendor-specific init/firmware-patch step before it
  behaves as a plain HCI device (some Broadcom chips do; unconfirmed for
  ESP32's own controller).

### Antenna

Small adhesive-backed 2.4GHz U.FL antenna (SparkFun WRL-18086-class, ~$2),
mounted inside the enclosure on a short pigtail, away from the USB-C
connector and any metal. Fully internal, per requirement — no antenna
poking out of the case.

### Display

1.9" ST7789V IPS, 320x170, SPI, bare panel + 0.5mm-pitch FPC connector —
same pattern as the current 240x240 panel, same driver family (ST7789), but
visibly better quality (viewing angle/contrast), matching the bar set by the
LilyGo T-Embed CC1101.

**This is not a drop-in swap.** 320x170 is a wide rectangle, not the 240x240
square the current on-device UI (home screen, field-list widget, alignment
grid — see `.planning/design/` in the firmware repo) was built around. A UI
relayout is required. Accepted as follow-up firmware work, not a hardware
blocker.

### Input

5-way joystick switch + 4 discrete tact buttons, same logical layout as
today (UP/DOWN/LEFT/RIGHT/PRESS, A/B/X/Y), mounted directly on the PCB.
Physical GPIO numbers may shift from the current `input.h`/`st7789.h`
constants; logical pin names stay the same to minimize firmware churn.

Designed for 3D-printed integration: individual button caps/plungers pass
through holes in the enclosure's top shell and press the PCB-mounted tact
switches beneath — standard approach for printable enclosures, tolerant of
FDM print tolerances.

### Power / connectors

- USB-C, device-only (no host port needed — it's a dongle), standard 5.1kΩ
  CC1/CC2 pulldowns for UFP operation.
- Single 3.3V rail from USB 5V; RP2350B's internal switched regulator
  generates its own core voltage (same pattern as stock Pico boards).
- **USB-C connector exits the rear of the enclosure**, so the cable runs
  straight back and isn't visible from the front (where the screen/buttons
  face the user).

## Manufacturing

JLCPCB fabs and fully assembles the board — RP2350B, flash, PSRAM,
ESP32-WROOM-32U, FPC connector, buttons, USB-C are all stocked parts. No
hand-soldering. Post-assembly manual steps are both solder-free: plug the
antenna pigtail into its U.FL connector, insert the display's flex cable into
its connector.

## Enclosure

3D-printed, two-shell design (top + bottom), screwed together (heat-set
inserts) for serviceability. Holds: the PCB, the display bezel/cutout, button
plungers, USB-C cutout at the rear, and an internal mount point for the
adhesive antenna positioned for clearance from the USB-C end and the PCB's
ground plane.

To be authored as an OpenSCAD (`.scad`) file — parametric, text-based, easy to
version-control and tweak. **Tooling caveat:** OpenSCAD isn't installed in
this environment, so the file can be written but not rendered/visually
verified here. Same caveat applies to the KiCad schematic/PCB files below.
Both need to be opened and checked (DRC, fit) on a machine with the real
tools installed.

## Deliverables (next pass, not yet started)

1. KiCad project: schematic (component selection + netlist), footprints,
   BOM with JLCPCB/LCSC part numbers. PCB routing/layout itself needs doing
   in the KiCad GUI — I can produce a starting schematic and guidance, not a
   routed, DRC-clean board, without the tool installed to verify it.
2. OpenSCAD enclosure file (two shells + button plungers + antenna mount).
3. BOM / sourcing sheet cross-referencing JLCPCB/LCSC part numbers.

## Out of scope / parked

- Firmware: BTstack HCI-UART transport (replacing gSPI `cyw43-driver`),
  ESP32 HCI-controller firmware flashing/bridge, UI relayout for 320x170.
  Owned by the user ("we can fix all of that").
- Selling finished units commercially: both the radio modules' FCC/IC/CE
  modular certification (antenna-gain-limited, firmware-mode caveat) and
  Sony's separate LDAC certification process (required to ship LDAC in a
  commercial product, beyond the Apache-2.0 encoder source) would need real
  follow-up — fine for an open-source build-it-yourself project (what this
  already is), a real gate if that ever changes.
