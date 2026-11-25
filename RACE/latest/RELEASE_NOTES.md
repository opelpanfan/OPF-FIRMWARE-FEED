# RACE v0.0.2

Version 0.0.2+VC11, commit 116fce71d69b5888af2814da82309f6832e799e4 (master-grok, tag v0.0.2).

OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600).

## This release

- PDM mode & SCS200 integration (`0.0.2` VC1–VC11): Grayhill J1939 keypad support, read-only SCS200 telemetry, key 1–12 output commands, SCS analog inputs, `/pdm.json` rule evaluation with fail-safe CAN loss handling, PDM status and schema 2 setup over BLE, `pdm_scs_apply` ratings, CANBoard column frames, and confirmed PDM bus bitrate change (`pdmbr` / `pdm_bus_baud`)
- Pages: dedicated PDM status page (`07_pdm.json`), Keypad pages (`04_pdm_keypad.json`, `05_pdm_keypad_square.json`, `06_pdm_grayhill_single.json`) with stage keys and centre-out shift bar, full-screen OPF BESS page (`03_bess.json`), and dash type selector (`Race` / `PDM` / `BESS`)
- Stability & settings: pre-rotated static labels into PSRAM images, GT911 I2C finite timeout + bus recovery, non-blocking USB console, slide watchdog, `diag` stall/hang command, Wi-Fi/BLE off at boot, on-screen settings popup (long-press 2 s or 3 s)

## Flash (esptool, USB, ESP32-P4)

Recommended: app only, at `0x10000`. This keeps NVS, otadata and LittleFS (`/pages`, `/canmap`, `/assets`).

    esptool --chip esp32p4 --baud 921600 write-flash 0x10000 esp32-p4.bin

OTA (HTTP `/fw` or BLE `ota_*`) also takes the app image only. Changed page JSONs (`data/pages/04..07`) can be pushed over USB console (`put` + `reload`) without erasing LittleFS.

Full flash (only if the bootloader or partition table must change). The P4 bootloader is at `0x2000`, not `0x0`:

    esptool --chip esp32p4 --baud 921600 write-flash \
      0x2000 bootloader.bin \
      0x8000 partitions.bin \
      0xe000 boot_app0.bin \
      0x10000 firmware.bin

The ESP32-C6 coprocessor is never flashed from this package.

The firmware itself reports `fw_version=0.0.2` (`VC11`, `version_code=11` in feed metadata: `0.0.2+VC11`).
