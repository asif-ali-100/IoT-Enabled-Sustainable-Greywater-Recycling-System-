# KiCad Schematic & PCB Guide

## ✅ A real, validated, fully-routed schematic

| File | What it is |
|---|---|
| `greywater-system.kicad_sch` | The actual KiCad 7 schematic — opens directly in KiCad |
| `greywater-system.kicad_pro` | Matching KiCad project file |
| `greywater-system.net` | Exported netlist (for reference / cross-checking) |
| `greywater-system-schematic.pdf` | Rendered PDF preview — view without installing KiCad |
| `greywater-system-schematic.svg` | Rendered SVG preview |
| `generate_schematic.py` | The generator script — kept for transparency/reproducibility |

**Every connection is drawn as a real routed wire from component to component** — sensor signals, relay control, relay switching, and the diode/solenoid wiring are all visible copper-equivalent traces on the sheet, not global-label shortcuts. (Power rails — `GND`/`+3V3`/`+12V` — use standard power-flag symbols, which is normal professional schematic practice, not a readability shortcut.)

**How this was built and verified — three independent checks, not just eyeballing it:**
1. **Real symbol geometry.** Every symbol's pins were pulled straight from the actual KiCad 7 standard libraries (`RF_Module`, `Connector_Generic`, `Device`, `Diode`, `Sensor_Temperature`, `power`, `Relay`) — nothing hand-typed or guessed.
2. **Netlist cross-check.** Round-tripped through `kicad-cli` to export a netlist, and every net was verified pin-by-pin against the GPIO map in [`../../docs/WIRING.md`](../../docs/WIRING.md) — e.g. confirming `RELAY_3` really lands on ESP32 `IO23` and really reaches `K3`'s coil, which really reaches `J5` (its solenoid) and `D3` (its flyback diode).
3. **Automated crossing check.** A geometric segment-intersection script checks all 100 wire segments pairwise for unintended crossings (excluding deliberate T-junctions, which are marked with junction dots). Current result: **0 unexplained crossings.**

This took a few real bugs to get right, which is worth knowing about if you extend the generator script:
- A Y-axis sign error that silently mirrored pin positions (caught by the netlist check, not by looking at it).
- A `libId` bug where derived symbols (DS18B20, which extends MAX31820) lost their library namespace when flattened, making the instance invisible to KiCad despite looking structurally fine in the file.
- A genuine routing-topology bug: naively assigning each net its own vertical "lane" (ordered by pin rank) is **not** automatically crossing-free when destination spacing is very different from source spacing — the safe rule this design relies on is that every destination Y must stay on the *same side* of its own source Y as every other net's, not just that the overall order is preserved. Getting this backwards for one group of 4 signals produced 12 real crossings that only the automated checker caught.

### What's modeled
- **U1** — ESP32-WROOM-32, full 38-pin symbol, all sensor/relay/float-switch nets wired per `WIRING.md`.
- **K1–K6** — real SPDT relay symbols (coil `A1`/`A2` + `COM`/`NO`/`NC` contacts), not a bare header. GPIO drives the coil (`A1`); `COM` ties to `+12V`; `NO` switches through to the solenoid — matching how an actual relay (or a relay module's onboard relay) behaves. The `NC` contact is explicitly marked no-connect.
  > Note: this models the **relay contact itself**. On real hardware you're almost certainly using a pre-built opto-isolated relay *module* (per the BOM), which already includes the driver/optocoupler between its logic-input pin and the coil shown here — you are not expected to drive a bare relay coil directly from a GPIO pin.
- **D1–D6** — flyback diodes across each solenoid's switched node and ground return, matching `WIRING.md`.
- **U2** — DS18B20, wired to `ONE_WIRE_TEMP`, `+3V3`, and `GND`, with its 4.7kΩ pull-up (`R1`) tapped directly off the data line via a marked junction.
- **U3** — buck converter shown as a simple 4-pin block (IN+/IN-/OUT+/OUT-) for clarity.
- Layout is optimized for **readable, crossing-free routing**, not compact PCB-ready placement — open it in KiCad and adjust cosmetics/spacing to taste. Footprint assignment (`Ctrl+Y`) and the actual PCB layout are the manual next steps.

### Opening it
```bash
# From the hardware/kicad/ folder:
kicad greywater-system.kicad_pro
```
Run **Inspect → Electrical Rules Checker** once it's open. You'll see a long list of "unconnected pin" warnings for the ESP32's unused GPIOs (flash pins, `EN`, `SENSOR_VP/VN`, etc.) — that's expected, since this design intentionally doesn't use them; everything else should be clean.

## PCB layout rules (once you're ready to route copper)

| Net class | Minimum trace width |
|---|---|
| GPIO signal traces | 0.25–0.4 mm |
| 5V / 3.3V power | 0.8–1.0 mm |
| 12V solenoid current | ≥1.5 mm, or a copper pour for GND return |

- Keep the 12V/relay switching section physically separated from the ESP32's antenna area to avoid RF interference.
- Add a ground pour on both layers, stitched with vias, tied to a single-point star ground near the 12V input.
- Place decoupling capacitors (100nF + 10µF) close to the ESP32's 3V3 pin.
- Keep analog sensor traces short and away from the relay/solenoid switching traces to minimize noise on ADC readings.

## Block diagram
See [`../images/block_diagram.svg`](../images/block_diagram.svg) for the high-level power/signal architecture (this predates the detailed schematic and is still useful as a 30-second overview).
