# BMS firmware

Public OTA binaries for BMS. New publishes come from OPF-STORAGE-DASH `master-grok`, env `opf-ws`, as `OPF_WS.bin`.

`latest/` is the channel. Its version label is `1.0.1`, and those bytes also live in immutable `v1.0.1/`. Older version folders stay in this directory. A publish adds `vX.Y.Z/` and refreshes `latest/` only when `set_latest` is true. It does not delete older folders.

Flasher reads `latest.BMS` and that product’s `versions[]` in the repository root `index.json`.
