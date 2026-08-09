# Compiled Firmware Build Output

These are **real compiled artifacts**, produced by actually building `firmware/greywater_system/greywater_system.ino` with `arduino-cli` + the official `esp32:esp32@2.0.9` core (Espressif's arduino-esp32), targeting the `esp32:esp32:esp32` (ESP32 Dev Module) board — using placeholder WiFi/Firebase credentials from the committed `config.h`.

| File | What it is |
|---|---|
| `greywater_system.bin` | The application firmware image — flash this with `esptool.py` or Arduino IDE at offset `0x10000` |
| `bootloader.bin` | Second-stage bootloader — flash at offset `0x1000` |
| `partitions.bin` | Partition table — flash at offset `0x8000` |
| `greywater_system.elf` | Full ELF with debug symbols (for `addr2line`, GDB, or Wokwi's debugger) |
| `greywater_system.hex` | Intel HEX conversion of the ELF (via `xtensa-esp32-elf-objcopy -O ihex`), provided for tools that expect `.hex` — see the caveat below |

Build stats from this compile:
```
Sketch uses 1045317 bytes (79%) of program storage space. Maximum is 1310720 bytes.
Global variables use 46780 bytes (14%) of dynamic memory, leaving 280900 bytes for local variables. Maximum is 327680 bytes.
```

## ⚠️ Rebuild before real deployment
This build uses the **placeholder** WiFi SSID/password and Firebase host/token from `config.h` in the committed source. It will compile and run, but it obviously can't reach your actual WiFi/Firebase. **Edit `config.h` with your real credentials and thresholds, then rebuild**, before flashing a physical board.

## Flashing to real hardware
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 921600 write_flash \
  0x1000  bootloader.bin \
  0x8000  partitions.bin \
  0x10000 greywater_system.bin
```
(Arduino IDE's Upload button does this automatically — see [`../../docs/SETUP.md`](../../docs/SETUP.md).)

## Reproducing this build yourself
```bash
# 1. Install arduino-cli, then:
arduino-cli config init
arduino-cli config set board_manager.additional_urls \
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
arduino-cli core install esp32:esp32

# 2. Install libraries (Library Manager or manually clone):
#    - Firebase ESP32 Client (Mobizt)
#    - OneWire (PaulStoffregen)
#    - DallasTemperature (milesburton)

# 3. Compile:
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/greywater_system --output-dir firmware/build
```
