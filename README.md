# 🌊 Automated IoT Greywater Recycling System (ESP32)

An ESP32-WROOM-32 based, fully automated 5-tank greywater recycling system with real-time monitoring via **Firebase Realtime Database** and a companion **MIT App Inventor** mobile app.

The system collects household greywater, screens it for hazardous gas, filters it, evaluates water quality (turbidity, pH, temperature, gas), and automatically routes clean water to a **garden irrigation tank** or lower-quality water to a **toilet-flush tank** — with automatic overflow release and manual remote override from a phone.

> ⚠️ **Status:** This is a personal / educational hobby project. It is **not** a certified plumbing, potable-water, or safety-critical system. Do not use for drinking water. Always follow local plumbing and electrical codes.

---

## 📐 System Overview

```
                         ┌────────────────────┐
  Greywater In  ───────▶ │  TANK 1 (Collect)  │
                         │  Gas Sensor         │
                         └─────────┬───────────┘
                     Gas detected? │
                    ┌──────Yes─────┴──────No───────┐
                    ▼                               ▼
              [ Drainage ]                 ┌────────────────────┐
                                            │ TANK 2 (Filtration) │  ← passive, no electronics
                                            └─────────┬──────────┘
                                                       ▼
                                            ┌────────────────────┐
                                            │  TANK 3 (Analysis)  │
                                            │ Gas / Turbidity /   │
                                            │ pH / Temperature    │
                                            └─────────┬──────────┘
                                     All readings OK?  │
                              ┌───────────Yes──────────┴─────No───────────┐
                              ▼                                            ▼
                    ┌───────────────────┐                       ┌───────────────────┐
                    │ TANK 4 (Irrigation)│                       │ TANK 5 (Toilet)    │
                    │ Float switch       │                       │ Float switch       │
                    └─────────┬──────────┘                       └─────────┬─────────┘
                        Full? │                                       Full? │
                              ▼                                            ▼
                     Auto-release to garden                     Auto-release to drainage
```

Full sensor/actuator-to-GPIO mapping is in [`docs/WIRING.md`](docs/WIRING.md).

---

## 📁 Repository Structure

```
greywater-recycling-esp32/
├── firmware/
│   ├── greywater_system/
│   │   ├── greywater_system.ino   # Main Arduino sketch
│   │   └── config.h               # WiFi/Firebase credentials + thresholds (EDIT THIS)
│   └── build/                     # Real compiled output (.bin/.elf/.hex) — see build/README.md
├── docs/
│   ├── WIRING.md                  # Full pin map + wiring instructions
│   ├── BOM.md                     # Bill of materials
│   ├── SETUP.md                   # Arduino IDE setup, flashing, generating .bin/.hex
│   ├── FIREBASE_SETUP.md          # Firebase Realtime Database setup
│   └── APP_INVENTOR.md            # MIT App Inventor mobile app blocks
├── hardware/
│   ├── kicad/
│   │   ├── greywater-system.kicad_sch     # Real, netlist-validated KiCad 7 schematic
│   │   ├── greywater-system.kicad_pro
│   │   ├── greywater-system-schematic.pdf # Preview without needing KiCad installed
│   │   ├── generate_schematic.py          # The generator script (reproducible/auditable)
│   │   └── README.md
│   └── images/
│       └── block_diagram.svg      # System architecture diagram
├── simulation/
│   ├── PROTEUS.md                 # Proteus limitations + recommended alternative
│   └── wokwi/                     # Real, loadable Wokwi simulation project
│       ├── diagram.json
│       ├── wokwi.toml             # Points at the real compiled firmware
│       └── README.md
├── LICENSE
├── CONTRIBUTING.md
└── .gitignore
```

---

## 🚀 Quick Start

1. Read [`docs/BOM.md`](docs/BOM.md) and gather the hardware.
2. Wire everything per [`docs/WIRING.md`](docs/WIRING.md).
3. Copy `firmware/greywater_system/config.h` and fill in your WiFi + Firebase credentials.
4. Follow [`docs/SETUP.md`](docs/SETUP.md) to install libraries and flash the ESP32 — or just re-flash the pre-compiled binaries in [`firmware/build/`](firmware/build/README.md) once you've rebuilt with your own credentials.
5. Set up the cloud dashboard: [`docs/FIREBASE_SETUP.md`](docs/FIREBASE_SETUP.md).
6. Build the mobile app: [`docs/APP_INVENTOR.md`](docs/APP_INVENTOR.md).
7. Want to simulate before building hardware? Open [`simulation/wokwi/`](simulation/wokwi/README.md) — it's a real, ready-to-run Wokwi project wired to the actual compiled firmware. See [`simulation/PROTEUS.md`](simulation/PROTEUS.md) for the Proteus option/limitations.
8. Designing the PCB? Open [`hardware/kicad/greywater-system.kicad_pro`](hardware/kicad/) directly in KiCad — it's a real, netlist-validated schematic, ready for you to lay out and route.

---

## 🔧 Core Features

- **Tank 1 — Gas Safety Screening**: MQ-series gas sensor diverts contaminated water straight to drainage.
- **Tank 3 — Multi-parameter Water Quality Check**: gas, turbidity, pH, and temperature all must pass thresholds.
- **Automatic Routing**: clean water → irrigation tank, failed water → toilet-flush tank.
- **Overflow Protection**: float switches auto-release full tanks.
- **Cloud Telemetry**: sensor data pushed to Firebase every 3 seconds.
- **Remote Manual Override**: force-drain from the mobile app in an emergency.
- **Fail-safe Defaults**: all solenoids default OFF on boot / WiFi loss.

## ⚙️ Hardware Summary

| Subsystem | Component |
|---|---|
| MCU | ESP32-WROOM-32 DevKit |
| Gas sensing | 2× MQ-135 (or MQ-2) |
| Water clarity | Analog turbidity sensor |
| Water quality | Analog pH sensor probe |
| Temperature | DS18B20 (OneWire) |
| Tank level | 2× float switches |
| Actuation | 8-channel relay module + 6× 12V solenoid valves |
| Power | 12V DC supply + 5V buck converter |

Full BOM with suggested part numbers: [`docs/BOM.md`](docs/BOM.md).

## 🛡️ Safety Notes

- Solenoids run on 12V — power them from a separate supply, **never** from the ESP32.
- Share a common GND between the 12V supply, relay board, and ESP32.
- Remove the relay module's JD-VCC jumper and feed 5V/12V coil power separately from the ESP32's 3.3V logic rail (opto-isolation).
- Add flyback (1N4007) diodes across every solenoid coil.
- This project does not treat water to a potable standard — recycled output is for **non-potable reuse only** (irrigation, flushing).

## 📄 License

MIT — see [`LICENSE`](LICENSE). Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
