# Contributing

Contributions are welcome — bug fixes, calibration improvements, PCB layout files, alternate sensor support, translations of docs, etc.

## How to contribute
1. Fork the repo and create a feature branch: `git checkout -b feature/my-improvement`
2. Make your changes.
3. If you change pin mappings or thresholds, update both `firmware/greywater_system/config.h` **and** [`docs/WIRING.md`](docs/WIRING.md) so they stay in sync.
4. Test on real hardware where possible, or note in your PR description that it was only verified in simulation.
5. Open a Pull Request describing what changed and why.

## Reporting issues
Please include:
- ESP32 board variant
- Arduino IDE / arduino-esp32 core version
- Relevant Serial Monitor output
- What you expected vs. what happened

## Code style
- Keep hardware configuration (pins, credentials, thresholds) in `config.h`, not hardcoded in the `.ino`.
- Prefer small, named functions over one giant `loop()`.
- Comment any calibration constant with how you derived it.
