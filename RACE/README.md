# RACE

OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600). Firmware comes from `opelpanfan/OPF-RACE-DASH` `master-grok`. Do not publish from `main` or `master`.

The firmware image reports a plain `fw_version` such as `0.1.16`. Feed folders and tags stay plain `vX.Y.Z`. Feed metadata uses `fw_version` `X.Y.Z+VCnn` and integer `version_code`.

Board, PlatformIO env, and label:

- `esp32-p4.bin` — `opf_dash`, Waveshare ESP32-P4-WIFI6-Touch-LCD-7B 1024x600. The firmware reports `board=esp32-p4`.

Recommended flash is the app image at `0x10000` (USB or OTA). That keeps NVS, otadata and LittleFS (`/pages`, `/canmap`, `/assets`).

This product does not publish the standard FEED bootloader trio (`<id>.bootloader.bin` at `0x0`, `<id>.partitions.bin` at `0x8000`, `<id>.boot_app0.bin` at `0xe000`). The ESP32-P4 bootloader lives at `0x2000`, not `0x0`, so those catalog offsets would be wrong. Full-flash parts and a merged `factory.bin` (write at `0x0`) are on the GitHub release and in the local Desktop folders.

The ESP32-C6 coprocessor is never flashed from this feed.
