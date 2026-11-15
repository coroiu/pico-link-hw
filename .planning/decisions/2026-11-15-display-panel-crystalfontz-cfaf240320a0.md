# Display panel: Crystalfontz CFAF240320A0-024SN, rotated to 320x240

## Context

The original design doc assumed a 1.9" ST7789V IPS panel, 320x170, SPI
(`AGENTS.md`, now stale — updated by this ADR). That assumption was never
stock-checked. Five research rounds
(`.research/findings/2026-11-15-display-wide-bar-height240-contrast.md`,
`-display-alternatives-contrast.md`, `-display-sustainable-stock.md`,
`-display-lcsc-relaxed-size.md`, plus live spot-checks of JLCPCB's own
catalog via the `jlcpcb-search` MCP server) searched broadly for a
240px-tall-or-taller, non-OLED, non-e-ink, wide-aspect SPI TFT with a
ST7789/ST7789V2/ILI9341-family driver (for firmware reuse), prioritizing
contrast ratio and genuine, sustainable stock.

The consistent finding across all five rounds: **no candidate has both
deep, sustainable mainstream stock and strong contrast.** Every part with
a real LCSC catalog listing either has thin/zero live stock on that
listing (Orient Display AFY240320A0-2.4INTH-R: out of stock, $41.92;
Display Visions EA-TFT020-23AINN: in stock on LCSC but currently zero
units) or undocumented/disputed contrast (the JLCPCB-native "HS"-branded
parts — HS28QI084RX, HS28B02A, HS32B01A, HS35B01A — all show "TBD" or
disputed driver/contrast specs on LCSC's own page). Parts with deep,
confirmed stock at a mainstream distributor (Crystalfontz, Newhaven) have
no LCSC listing at all, meaning no single-order convenience with the rest
of the PCB's LCSC/JLCPCB BOM.

The user asked for a final decision given this tradeoff: "Let's lock in
CFAF240320A0-024SN."

## Decision

Use the **Crystalfontz CFAF240320A0-024SN** (plain, non-touch variant),
rotated 90 degrees in firmware (MADCTL/MV row-column exchange, same
mechanism already used for the ST7789V family) to run **320x240
landscape**, SPI interface.

- **Driver:** Sitronix ST7789V — the exact driver already planned,
  confirmed on Crystalfontz's own product page. No firmware
  compatibility risk.
- **Contrast:** 800:1, 850 nits, "sunlight readable" per Crystalfontz's
  product page — directly addresses the original "backlight makes
  everything gray" complaint that motivated looking at alternatives.
- **Resolution/aspect:** 240x320 native, 320x240 (1.33:1) rotated —
  closer to square than the original 1.9"/1.88:1 baseline, but a genuine
  rectangle.
- **Price:** $16.38 @ qty 1, $14.20 @ qty 1000.
- **Stock:** 3,082 units in-stock, confirmed live 2026-11-15 directly on
  Crystalfontz's own site — roughly two orders of magnitude deeper than
  every other candidate checked across all five research rounds.
- **Sourcing:** No LCSC listing exists for this part (checked directly
  and via a broader "any Crystalfontz TFT on LCSC" search). It ships as
  a **separate order direct from Crystalfontz**, not part of the
  LCSC/JLCPCB cart with the rest of the BOM.

## Rationale

Given the confirmed tradeoff (no part wins on both stock depth and
contrast/sourcing convenience), stock depth and driver/contrast
confidence were weighted higher than single-cart sourcing convenience:

- 3,082 confirmed units eliminates the single biggest risk surfaced by
  this whole research chain — several "top" candidates from earlier
  rounds turned out to have 0-56 units in practice once spot-checked,
  which would have blocked or badly delayed a production run.
- The exact planned driver (ST7789V) removes a second recurring risk in
  this chain: several competing parts had disputed or TBD driver/contrast
  specs (ILI9341V drift, "parameters being completed" on LCSC, etc.).
- 800:1 contrast is a real, stated, first-party-sourced number — not a
  marketing-copy guess — and is a clear improvement over the ~500:1
  general baseline that motivated this whole search.
- A single-source, single-SKU, non-LCSC order is an accepted, ordinary
  cost of this choice, not a hidden one — the BOM will have exactly one
  line item that doesn't ship with the rest of the board's parts.

## Alternatives considered

| Candidate | Stock | Driver/contrast | LCSC? | Why not chosen |
|---|---|---|---|---|
| 4D Systems 4DLCD-24320240-IPS | 56 units (DigiKey), live LCSC price ladder | ST7789V (old stock) / ILI9341V (new stock) — unresolved mismatch, 800:1 | Yes (C17506419) | Best LCSC-cart convenience, but driver uncertainty on new stock and far less stock margin |
| Display Visions EA-TFT020-23AINN | 52 units (DigiKey) | ST7789V (exact), 800:1/640:1 min | Yes (C17560114) but out of stock | Real LCSC listing, but that exact channel has zero stock right now |
| Newhaven NHD-2.4-240320AF-CSXP | 7 units (DigiKey) | ST7789VI, 1500:1 best-in-chain | No | Best contrast found, but stock too thin for a production run |
| Orient Display AFY240320A0-2.4INTH-R | Out of stock, $41.92 | ST7789V, ~500-750:1 | Yes (C20578695), out of stock | Matched the user's own screenshot finding — dead end |
| JLCPCB-native "HS"-series (HS28QI084RX, HS28B02A, HS32B01A, HS35B01A) | 6-17 units live via jlcpcb-search MCP | Disputed/TBD driver & contrast on LCSC's own page | Yes, in catalog | Single-digit-to-teens stock and no confirmed contrast spec; not usable |
| Sharp Memory LCD (LS027B7DH01A, LS044Q7DH01) | 0 and 122 units respectively | N/A — monochrome, no backlight, different driver architecture | Mixed | Genuinely different technology (addresses backlight complaint by removing backlight entirely), but monochrome and a different driver/architecture — flagged as an alternative-technology wildcard, not pursued further this round |
| Original 1.9" ST7789V IPS, 320x170 | Never stock-checked | ST7789V, baseline ~500:1 | Unknown | Superseded — the original unverified assumption that triggered this whole research chain |

## Consequences

- **BOM/ordering:** the display is a separate line item ordered directly
  from Crystalfontz, not part of the LCSC/JLCPCB cart. Flag this
  explicitly when the BOM is assembled — it's the one part that won't
  arrive with everything else.
- **Firmware:** display driver init must apply the ST7789V
  MADCTL/MV rotation to present 320x240 landscape from the panel's native
  240x320 orientation — this is the same mechanism already assumed for
  the ST7789V family, not new driver work, but it must not be skipped.
- **Schematic (`display.kicad_sch`, currently empty):** design the
  display connector/interface against CFAF240320A0-024SN's actual pinout
  (SPI 4-wire), not the original 320x170 assumption. Confirm connector
  type (FPC/header) from Crystalfontz's datasheet before finalizing.
- **`AGENTS.md`** updated by this ADR to replace the stale "1.9\" ST7789V
  IPS, 320x170, SPI" line with this part's actual spec.
- **Enclosure:** any existing enclosure sketches assuming a 1.9"/320x170
  cutout need re-checking against this panel's physical dimensions
  (not yet done — flag as follow-up work if/when enclosure work starts).
