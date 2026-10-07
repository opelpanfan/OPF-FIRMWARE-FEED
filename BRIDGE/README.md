# BRIDGE firmware

Public OTA binaries for the M5 bridge. Flash `ATOM_S3_R.bin` and `ATOM_S3.bin` only. Source is OPF-STORAGE-M5-BRIDGE `master-grok` at `d9ca7a0` (`build-firmware.yml`).

DTU versus RS485 is selected on the device after flash. `ATOM_S3_R_DTU` and `ATOM_S3_DTU` are not feed firmware.

`latest/` is the channel. Its version label is `v1.0.1`, and those bytes also live in immutable `v1.0.1/`. Older version folders, including `v1.0.14/`, stay in this directory. A publish adds `vX.Y.Z/` and refreshes `latest/` only when `set_latest` is true. It does not delete older folders.

Flasher reads `latest.BRIDGE` and that product’s `versions[]` in the repository root `index.json`.
