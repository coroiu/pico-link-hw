# Swap ESP32-WROOM-32U for ESP32-WROOM-32UE before PCB layout

## Context

`.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md` settled on
ESP32-WROOM-32U as the BT Classic coprocessor, and the resulting schematic
(`pilink-7el.4`, merged) wired `U1` as `RF_Module:ESP32-WROOM-32U`
(`ESP32-WROOM-32U-N4`). That bead's implementer flagged Espressif's own
datasheet marking the part NOT RECOMMENDED FOR NEW DESIGNS (NRND), without
confirming whether ESP32-WROOM-32UE (the suggested successor) is a real
drop-in. A dedicated research bead (`pilink-8zj`,
`.research/findings/2026-11-14-esp32-wroom-32ue-swap-eval.md`) answered
that: yes, drop-in, with no new symbol/footprint authoring needed. The user
has now approved acting on that recommendation.

## Decision

Swap `esp32_bt.kicad_sch`'s `U1` from `RF_Module:ESP32-WROOM-32U` /
`ESP32-WROOM-32U-N4` to `RF_Module:ESP32-WROOM-32UE` /
`ESP32-WROOM-32UE-N4`.

## Rationale

- Confirmed pin-for-pin identical (all 39 positions diffed directly against
  both datasheets) — same GPIOs, same alternate functions, same 4x GND,
  same single NC, same EN/3V3. The only difference is a cosmetic pin-name
  change on 6 flash-SPI pins already left unconnected in this design.
- Same physical footprint envelope (18.0 x 19.2 x 3.2mm on both
  datasheets); KiCad 8.0.9's stock `RF_Module` symbol and footprint
  libraries already ship a ready-made `ESP32-WROOM-32UE` symbol/footprint
  pair — no new library authoring required.
- ESP32-WROOM-32UE is not itself NRND/EOL, and carries a guaranteed
  ESP32-D0WD-V3 silicon revision versus the 32U's mixed/unspecified
  revision — a known-good superset for this project's use (HCI-over-UART
  controller firmware only, no PSRAM, no Wi-Fi application code).
- Comparable JLCPCB/LCSC stock in the same N4 (4MB flash) variant already
  chosen (LCSC C701344, ~3,321 units at research time) — doesn't trade one
  sourcing risk for another.
- No PCB layout exists yet — this is the cheapest point to swap. Waiting
  would only add cost (redoing a routed footprint) for no benefit, since
  the equivalence findings remove the uncertainty "wait and see" would
  have been hedging against.

## Alternatives considered

- **Keep ESP32-WROOM-32U despite NRND.** Rejected — the swap is confirmed
  free (same pins, same footprint, library already exists) and 32UE is
  Espressif's actively-maintained part; there's no offsetting cost to
  justify staying on a flagged-NRND part.
- **Wait until closer to fab to decide.** Rejected — cost of swapping only
  increases once PCB routing exists around the current footprint; nothing
  is learned by waiting that isn't already known now.

## Consequences

- `hardware/esp32_bt.kicad_sch` needs a small amendment: `U1`'s `lib_id` →
  `RF_Module:ESP32-WROOM-32UE`, Value → `ESP32-WROOM-32UE-N4`, Footprint →
  `RF_Module:ESP32-WROOM-32UE`, Datasheet →
  `https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf`.
  Net/pinout/GPIO assignment is unchanged — no other part of this sheet or
  any sibling sheet needs touching. Tracked as a new bead.
- BOM/part-number references and the sheet's RISK FLAG text (the NRND
  note) need updating to reflect the swap.
- One residual item flagged by the research, not resolved by this
  decision: the two footprints' pad geometry differs by a small
  (~0.155mm/~0.38mm) offset between library files despite identical pad
  numbering/pitch — needs an ordinary human DRC/courtyard check against
  the 32UE datasheet's mechanical drawing before fab, same as any
  footprint already gated on a human KiCad pass in this project.
- Firmware (`../pico-link`, out of scope for this repo): unaffected — the
  HCI-over-UART architecture and GPIO pin assignments this project depends
  on don't change.
