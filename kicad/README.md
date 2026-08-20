# KiCad Schematic

## Files
| File | What it is |
|---|---|
| `greywater-monitor.kicad_sch` | The real KiCad 7 schematic — opens directly in KiCad |
| `greywater-monitor.kicad_pro` | Matching project file |
| `greywater-monitor-schematic.pdf` | Rendered preview — view without installing KiCad |
| `greywater-monitor-schematic.svg` | Rendered preview |
| `generate_schematic.py` | The generator script (kept for transparency/reproducibility) |

## How this was built and verified
Same methodology as the rest of this project's hardware work, not hand-drawn guesswork:
1. **Real symbol geometry** pulled from the actual installed KiCad 7 libraries (`RF_Module`, `Connector_Generic`, `Device`, `Relay`, `Motor`, `power`) — including the BC547 transistor (`Q_NPN_BCE`) and DC motor (`Motor_DC`) symbols.
2. **Every signal net is a real routed wire** — sensor readings, relay control, and the resistor→transistor→relay→motor chain are all visible traces, not global-label shortcuts. Power (`GND`/`+5V`/`+12V`) uses standard power-flag symbols.
3. **Netlist-verified.** Every one of the 14 signal nets was checked against the intended ESP32 pin (see [`../../docs/WIRING.md`](../../docs/WIRING.md)) using `kicad-cli`'s own netlist export — this caught a real bug where one resistor's own routing accidentally shorted its two pins together (fixed; verified R and the transistor base are now on separate nets, as a resistor should be).
4. **Zero wire crossings**, confirmed by an automated geometric segment-intersection check across all 127 wires.

## Circuit summary
- **U1** ESP32-WROOM-32 — central controller.
- **pH, temperature, turbidity, gas ×2, level sensors** — wired per `WIRING.md`.
- **16x2 I2C LCD** — status display.
- **5× driver stage** (R + Q_BC547 + Relay_SPDT + 1N4007 flyback diode + DC motor) — GPIO drives a transistor, which switches a relay, which switches +12V through to the motor.
- **Voltage regulator + power jack** — 12V input down to a 5V rail for the ESP32/sensors/LCD; +12V feeds the relay COM pins and motors directly.

## Opening it
```bash
kicad greywater-monitor.kicad_pro
```
Layout is optimized for correctness and readability, not final PCB placement — rearrange/route as needed once it's open. Expect ERC warnings for the ESP32's unused pins (flash, `EN`, `SENSOR_VP/VN`) — that's expected since this design doesn't use them.
