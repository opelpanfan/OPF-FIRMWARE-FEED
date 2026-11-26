# RACE v0.0.2

Version 0.0.2+VC12, commit f221cfea804e5e722623990af2b2aa1446562fc2 (master-grok, tag v0.0.2).

OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600).

This folder replaces the earlier v0.0.2 package (0.0.2+VC11, 116fce7) at Benas's instruction. The annotated tag `v0.0.2` was moved to this commit.

## This release

- PDM mode & SCS200 integration (`0.0.2` VC1–VC12): Grayhill keypad (J1939 and CANopen 3KG1), read-only SCS200 telemetry, key 1–12 output commands, SCS analog inputs, `/pdm.json` rule evaluation with fail-safe CAN loss handling, PDM status and schema 2 setup over BLE, `pdm_scs_apply` ratings, CANBoard column frames, confirmed PDM bus bitrate change (`pdmbr` / `pdm_bus_baud`), output groups, and `pdmmodel`
- Keypad protocol (`pdmkpproto`, also `pdm_set:keypad.proto` and console `pdmkpproto`): `canopen` (default, current 3KG1 unit) or `j1939` (for the 3K012 units arriving later). CANopen node id is `pdmkpnode` / `keypad.sa`, default 10 (`0x0A`, 3KUM1331-1 Rev D §8 Table 1). Only a J1939 Grayhill locks the bus at 250 kbit/s. `pdm_bus_baud:grayhill_canopen:<250|500>:confirm=1` sends the documented LSS sequence (§9.3) and then tells you to power-cycle; nothing is sent without `confirm=1`
- Pages: dedicated portrait PDM status page (`07_pdm.json`, `orientation: portrait_cw`; firmware builds group and channel tiles from `pdmOutputs`), Keypad pages (`04_pdm_keypad.json`, `05_pdm_keypad_square.json`, `06_pdm_grayhill_single.json`) also portrait, with stage keys and centre-out shift bar, full-screen OPF BESS page (`03_bess.json`), and dash type selector (`Race` / `PDM` / `BESS`)
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

The firmware itself reports `fw_version=0.0.2` (`VC12`, `version_code=12` in feed metadata: `0.0.2+VC12`).
