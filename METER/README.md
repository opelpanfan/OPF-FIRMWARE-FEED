# METER

Empty until sources push `v0.0.1`.

OPF-LORA-METER is an ESP32-S3 product for AtomS3 and AtomS3R. Images are stored in this folder. Builds use `partitions/ota_8MB.csv` and qio flash mode.

Publish all four app images together under `METER/vX.Y.Z/` and copy them to `METER/latest/`:

- `transmitter.bin` (env `transmitter`)
- `receiver.bin` (env `receiver`)
- `transmitter_lcd.bin` (env `transmitter_lcd`)
- `receiver_lcd.bin` (env `receiver_lcd`)

Optional full-install files for each board, next to that board's app image. Publish all three or none:

- `<BOARD>.bootloader.bin` at `0x0`
- `<BOARD>.partitions.bin` at `0x8000`
- `<BOARD>.boot_app0.bin` at `0xe000`

This feed does not build or download OPF-LORA-METER.
