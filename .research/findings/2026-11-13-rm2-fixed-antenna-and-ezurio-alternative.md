# RM2's fixed antenna, and the Ezurio Sterling-LWB+ alternative

## Question

The existing Pico Plus 2 W board's Bluetooth range feels weak. Can RM2's
antenna be improved or swapped?

## Findings

- RM2 (Raspberry Pi's radio module, built on Infineon's CYW43439) has a
  fixed onboard PCB trace antenna baked into the module. There is no U.FL or
  other external-antenna connector option on RM2 itself — checked the
  official RM2 datasheet/product-brief listings and RM2 retail pages.
- A lot of "weak Bluetooth" on compact boards is actually antenna
  *placement*, not the chip: RM2's datasheet specifies a ground-plane
  keep-out zone around the antenna edge for it to perform well, and that
  clearance is often compromised on a tightly packed dev board, or by a
  metal enclosure. A board designed for this product specifically (clean
  keep-out, antenna at the PCB edge, away from USB-C and the enclosure's
  metal, if any) can fix a lot of this without touching the RF chain.
- The same CYW43439 silicon is also sold by Ezurio as the **Sterling-LWB+**,
  which has a variant with an **MHF4 (U.FL-class) connector** for a real
  external/swappable antenna, as a pre-certified module — so the
  certification-free benefit of using a module (vs. a raw chip + custom
  antenna matching) is preserved, with antenna freedom added.
  - Catch: Sterling-LWB+ exposes SDIO or HS-UART, not RM2's gSPI interface.
    Using it would mean moving the firmware's Bluetooth transport from the
    gSPI-based `cyw43-driver` glue to BTstack's standard HCI-over-UART
    transport — a real but contained rewrite, since BTstack already ships
    reference chipset init code for this exact chip family over UART (this
    is literally how Raspberry Pi SBCs drive their onboard Bluetooth).
  - Gap: couldn't confirm Sterling-LWB+'s pin-level integration details
    (exact UART pinout, firmware/CLM blob requirements) without what looks
    like an Ezurio distributor account/hardware integration guide. Not
    ruled out, just unverified.

## Informs

`.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md` — Sterling-LWB+
was shelved in favor of an ESP32-WROOM-32U coprocessor, primarily because
ESP32's sourcing/documentation is unambiguous and it's confirmed stocked at
JLCPCB for full SMT assembly, where Sterling-LWB+'s was not confirmable.
Sterling-LWB+ remains the documented fallback if the ESP32 path hits a wall.
