# BMS firmware

Public OTA binaries for BMS. New publishes come from OPF-STORAGE-DASH `master-grok`, env `opf-ws`, as `OPF_WS.bin`.

`latest/` is the channel. Its version label is `1.0.1`. A publish also writes an immutable `vX.Y.Z/` folder. This checkout currently has only `latest/` because older version folders were removed.

Flasher reads `latest.BMS` and that product’s `versions[]` in the repository root `index.json`.
