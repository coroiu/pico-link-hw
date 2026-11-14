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

## Addendum (2026-11-14) — pin-level integration confirmed (pilink-sd4)

Follow-up to the "couldn't confirm Sterling-LWB+'s pin-level integration
details" gap above. Read Ezurio's own datasheet and host-integration guide
directly (not a distributor summary). Primary sources:

- **Datasheet**: "Sterling-LWB+ Datasheet", Ezurio, Version 2.2, 12 Sep 2025
  — hosted at
  `https://connectivity-staging.s3.us-east-2.amazonaws.com/2025-09/EZ-DS-LWB-Plus_v2_2.pdf`,
  linked from the product page `https://ezurio.com/part/453-00084r`.
  Fetched and parsed directly (as raw PDF content streams, since this
  session had no `pdftotext`/`poppler` available — extracted with a small
  ad hoc script decompressing the PDF's FlateDecode streams and pulling
  `Tj`/`TJ` text-show operators; cross-checked against the rendered
  product-page text for consistency).
- **Host dependency guide**: Ezurio/LairdCP Linux integration docs,
  `https://lairdcp.github.io/guides/linux_docs/1.0/lwb-sona-ifx/sig_lwb_sona_ifx_series_radio_linux_hostdep.html`
  and
  `.../sig_lwb_sona_ifx_series_radio_linux_validation.html`.

### Part numbers (datasheet §3, Module Variants)

- **453-00083** — bare SiP module, 47-pin 0.5mm-pitch LGA, no antenna. Needs
  its own off-module antenna + RF matching design (Ezurio explicitly warns
  this is the harder path, both for host PCB design and for reflow —
  "requires additional care during reflow and PCB assembly"). Not the one
  we want.
- **453-00084 — the MHF4/U.FL-class variant.** Integrates the 453-00083 SiP
  plus an MHF4 RF connector and matching components on a small PCB. This is
  the part referred to as "Sterling-LWB+ MHF4" throughout. Order codes seen
  at distributors: **453-00084R** (reel) and **453-00084C** (cut tape) —
  same part, different packaging/quantity, not different electrical
  variants.
- **453-00085** — chip-antenna variant (integrated ceramic antenna, no
  external-antenna option). This is the one to avoid for this project,
  mirroring why RM2 itself was rejected.
- **453-00141** — M.2 2230 E-key SDIO/UART module. A different form factor
  (M.2 card edge connector), not relevant to a custom PCB design.
- **453-00084-K1** — MHF4 dev/eval kit, ships with an antenna for bench
  evaluation (the datasheet doesn't name the antenna model; a distributor
  listing calls it a "FlexPIFA" antenna, but that term doesn't appear in
  Ezurio's own datasheet, so it isn't repeated here as datasheet
  terminology).
  Useful if the fallback is ever actually prototyped before committing it
  to the board.

So: **453-00084 (order as 453-00084R or 453-00084C) is the confirmed MHF4
part number** for this project's fallback.

### Pinout (datasheet §8.2, Table 13 — MHF4 & chip-antenna module share one
47-pin pinout)

- **Power**: `VDD_3V3` (pin 5) — main WiFi+BT supply. `VDD_VIO` (pin 20) —
  I/O supply, datasheet allows **1.8V or 3.3V**.
- **Enable/reset pins** (direct analogue of RM2/Pico-W's `WL_REG_ON`):
  `WL_REG_ON` (pin 12) and `BT_REG_ON` (pin 21), each with an internal 200kΩ
  pull-down enabled by default (so each section stays off until the host
  drives its pin high; de-asserting holds that section in reset).
  Confirmed independently controllable: the datasheet's power-on timing
  section explicitly documents **"WLAN = OFF, Bluetooth = ON"** (Figure 12)
  as a supported state — Bluetooth can run with WiFi left permanently
  disabled, which is exactly this project's use case (no WiFi needed).
  Ezurio's host-dependency guide adds a required sequencing detail not in
  the datasheet: at least 150ms (250ms recommended) between power being
  stable and asserting either REG_ON pin, and `SDIO_DATA2` (pin
  shared with `JTAG_TDO`) must be high at the moment the *first* REG_ON pin
  transitions low→high (module has an internal pull-up on it already, so
  the host should not drive/load that line).
- **Crystal/clock**: `32KHZ_OSC_IN` (pin 19) — external 32.768kHz clock is
  **mandatory**; the datasheet states in bold: *"A 32.768 KHz crystal is
  required for the module to be functional. The module will not boot
  without this crystal."* (spec: 200ppm accuracy, 30–70% duty cycle,
  200–3300mV p-p, square or sine). No separate host-facing high-speed
  crystal pin — the module's main radio clock is internal to the SiP.
  `CLK_REQ` (pin 13) is only relevant if the *host* shares one TCXO across
  multiple radios instead of giving this module its own crystal; not
  needed in a design that just gives the module its own 32.768kHz crystal.
- **Bluetooth HCI UART** (datasheet §12.2): standard 4-wire interface —
  `BT_UART_TXD` (pin 33), `BT_UART_RXD` (pin 34), `BT_UART_RTS_L` (pin 31),
  `BT_UART_CTS_L` (pin 32). Auto-baud-rate detection on power-up, default
  115.2 kbps, adjustable up to 4.0 Mbps via a vendor-specific HCI command.
  This is precisely the RP2350-UART-to-BTstack transport link the original
  finding anticipated — confirmed to exist as a plain 4-wire UART, not
  bundled with WLAN's SDIO.
- **WLAN SDIO** (datasheet §12.1, only relevant if WiFi is ever used, which
  this project doesn't need): `SDIO_D0..D3`, `SDIO_CMD`, `SDIO_CLK` (pins
  22, 23, 25, 27, 26, 29), SDIO v2.0, 10K–100K pull-ups required on
  DATA/CMD lines. Can be left unconnected for a Bluetooth-only design.
- **Optional wake pins**: `BT_DEV_WAKE` (pin 39), `BT_HOST_WAKE` (pin 40) —
  not required for basic bring-up, recommended for proper low-power
  behavior; can be tied off if the design just keeps the BT section active.
- **Not needed for this project**: `BT_PCM_*` pins (2, 3, 4, 38) — this
  project moves audio over L2CAP/AVDTP (A2DP/LDAC) under BTstack, not
  synchronous PCM voice, so the PCM pins can be left unconnected.

### Firmware blob requirement — confirmed, and the ESP32 tradeoff is real

**Confirmed: yes, Sterling-LWB+ still needs a CYW43439 Bluetooth firmware
patch loaded over the UART at boot**, the same family of requirement as
RM2's `cyw43-driver` blob on RP2350/Pico W — just delivered over a literal
UART instead of RM2's gSPI. Ezurio's own Linux validation guide confirms a
host-side firmware-download step is required before the chip behaves as a
plain HCI device: it explains (discussing "Sterling LWBx series radios"
generically — that page doesn't single out "LWB+" by name) that the UART
must be attached to the Bluetooth stack's HCI interface with the correct
parameters, and that doing so is also what lets the Bluetooth firmware be
downloaded to the radio. (That's a paraphrase of the guide's wording, not
a verbatim quote.) This is the standard Broadcom/Cypress/Infineon
BT-over-UART "download mode" pattern — the same mechanism as
`hciattach`/`brcm_patchram_plus`/`btbcm.c` in Linux. Where the resulting
firmware blob would need to live on a Linux-based host (e.g. a path like
`/lib/firmware/brcm`) is **not** stated in either Ezurio source page used
here, so that specific path is not claimed as confirmed — only that a
firmware-download step exists is confirmed from these sources.

**This means the stated ESP32-vs-fallback tradeoff is real and should be
explicit**: the whole point of the ESP32-WROOM-32U path is that Espressif's
own HCI-over-UART controller firmware already lives in the ESP32's own
flash — RP2350 never has to push a radio firmware blob to it at runtime.
Falling back to Sterling-LWB+ reintroduces exactly the kind of
boot-time-firmware-push dependency the ESP32 path was chosen to avoid,
just moved from RM2's gSPI transport to a plain UART transport. It is a
smaller rewrite than starting from raw CYW43439 (BTstack already ships
generic Broadcom/Cypress/Infineon UART chipset init code, and the download
mechanism itself is industry-standard, not Ezurio-specific), but it is not
transport-work-free the way the "ESP32 hits a wall" framing might suggest.

**Still not confirmed, and not confirmable from Ezurio's public docs
without the physical module in hand**: the exact firmware/`.hcd` identity
string Sterling-LWB+'s Bluetooth controller reports (e.g. whether it
enumerates as `BCM4343A2` or a different variant ID, which determines the
exact firmware filename BTstack's init code would need to request) — this
would need either an Ezurio distributor/integration-guide account with the
module-specific software integration guide, or the actual part on a bench
with a UART analyzer. Flagging this rather than guessing it.

### Sourcing/stock (checked 2026-11-14, re-verified live same day)

- Standard distributors stock it: DigiKey listed **453-00084R** with ~2160
  units (North America) and Mouser ~890 units, both as of this session —
  so the part itself is not scarce through standard distribution.
- **Correction:** an earlier version of this finding said the part was
  "not found on JLCPCB's or LCSC's parts search (checked both directly)."
  That was wrong. Both order codes **are** listed, on both sites, as
  Extended-library parts — they're just at 0 stock. Re-checked live on
  2026-11-14 directly against LCSC's product pages and JLCPCB's parts
  catalog (not just trusting a prior report's numbers):
  - **453-00084R → LCSC `C6091255`** — listed with reference pricing
    (roughly $4.56–$12.03/unit depending on quantity break), shown as
    "Out of Stock" on LCSC's own product page. On JLCPCB's parts catalog:
    Extended library, "In Stock: 0," pre-order available.
  - **453-00084C → LCSC `C6393637`** — listed with reference pricing
    (roughly $11.57–$30.52/unit depending on quantity break), 0 in stock
    on LCSC's search listing. On JLCPCB's parts catalog: Extended library,
    "In Stock: 0."
  - So the accurate claim is weaker than "doesn't exist in their catalog,
    so it needs hand-assembly or a separate assembly house." Both parts
    **are** real, priced catalog entries in JLCPCB's Extended-parts
    library — they are just unavailable to order *today* because both sit
    at 0 stock. That's a stock-availability problem, not a
    catalog-existence problem; stock figures fluctuate, and either part
    coming back into stock would make it orderable through JLCPCB's
    standard Extended-parts assembly flow like any other Extended part
    (Extended parts carry a per-part handling fee and manual pre-order
    confirmation regardless of stock level, so that detail isn't new here).
  - The practical effect on near-term readiness is still similar to
    before: at 0 stock, this part **cannot be ordered through JLCPCB
    today** for an assembly run, so hand-assembly, a separate placement
    step, or a different supplier is still the realistic path if the
    fallback were exercised right now — but that conclusion now rests on
    "temporarily out of stock," not the earlier, incorrect "not in their
    catalog at all."
- Manufacturer is Ezurio (formerly Laird Connectivity), not a JLCPCB
  in-house or affiliated line — this is a genuine extra-supplier
  dependency if the fallback is ever exercised, independent of the
  stock question above.

### Net effect on readiness

The fallback is now genuinely actionable at the hardware level: part
number, full pinout (power, enable pins, crystal, UART HCI pins), and
power-sequencing requirements are all confirmed from Ezurio's own
datasheet and integration guide, not just named. The one thing that
stays open is the exact firmware-blob identity for BTstack's UART init —
a firmware-side detail that can only be nailed down with the physical
module, not from Ezurio's published documentation. The ESP32-WROOM-32U
decision itself is unchanged by this: this addendum firms up the fallback,
it doesn't surface a reason to revisit the primary choice.
