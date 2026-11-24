# RACE v0.1.16

Version 0.1.16+VC17, commit 945821e7a897883c6dadda80adae347ebf344605 (master-grok, tag v0.1.16).

OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600). This is the first RACE package on the firmware feed.

## This release

- Tick-driven screen refresh after each CAN update, aiming for a steady 50 FPS
- Faster LVGL refresh (10 ms) and shorter pause before a page slide
- Partial digit invalidation so only changed digits are redrawn
- USB `perf` command for FPS and CPU measurements
- Page-name badge for 10 seconds after a page change (from 0.1.15)
- Pages on the image: JDM Fuji, UC-10 Retro, Rothmans

## Flash (esptool, USB, ESP32-P4)

Recommended: app only, at `0x10000`. This keeps NVS, otadata and LittleFS (`/pages`, `/canmap`, `/assets`).

    esptool --chip esp32p4 --baud 921600 write-flash 0x10000 esp32-p4.bin

OTA (HTTP `/fw` or BLE `ota_*`) also takes the app image only.

Full flash (only if the bootloader or partition table must change). The P4 bootloader is at `0x2000`, not `0x0`:

    esptool --chip esp32p4 --baud 921600 write-flash \
      0x2000 bootloader.bin \
      0x8000 partitions.bin \
      0xe000 boot_app0.bin \
      0x10000 firmware.bin

A LittleFS image may be written at `0x1010000`. That erases every page, canmap and asset on the device. Prefer USB `put` / `get` / `ls` for individual files.

The ESP32-C6 coprocessor is never flashed from this package.

The firmware itself reports `fw_version=0.1.16` (no `+VCnn` and no `version_code` in the image). Feed metadata is `0.1.16+VC17` / `version_code` 17.
