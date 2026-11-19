# SCREEN

OPF CAN dashboard for Waveshare ESP32-S3 LCD boards. Empty until OPF-STORAGE-DASH pushes a plain `vX.Y.Z` folder from `master-grok`.

The firmware build id looks like `v0.0.2+N`. Feed folders and tags stay plain `vX.Y.Z`. Do not publish from `main` or `master`.

`full_flash_required` is set. OTA across a partition-layout change is unsafe. Flash the whole image.

Boards, PlatformIO env, and label:

- `ws-4-480.bin` — `OPF_WS_CAN_DASH_4`, Waveshare Touch-LCD-4 480x480
- `ws-43-800.bin` — `OPF_WS_CAN_DASH_43`, Touch-LCD-4.3B 800x480
- `ws-5-800.bin` — `OPF_WS_CAN_DASH_5` with `-D OPF_CAN_DASH_RES=800`, Touch-LCD-5 800x480
- `ws-5b-1024.bin` — `OPF_WS_CAN_DASH_5` with `-D OPF_CAN_DASH_RES=1024`, Touch-LCD-5B 1024x600, experimental
- `ws-7-800.bin` — `OPF_WS_CAN_DASH_7` with `-D OPF_CAN_DASH_RES=800`, Touch-LCD-7 800x480, UART/download-mode flash only
- `ws-7b-1024.bin` — `OPF_WS_CAN_DASH_7` with `-D OPF_CAN_DASH_RES=1024`, LCD-7B 1024x600, UART-only

Each published board uses `<id>.bin` at `0x10000`, `<id>.bootloader.bin` at `0x0`, `<id>.partitions.bin` at `0x8000`, and `<id>.boot_app0.bin` at `0xe000`. `<id>.factory.bin` at `0x0` is optional.

This feed does not build or download those images.
