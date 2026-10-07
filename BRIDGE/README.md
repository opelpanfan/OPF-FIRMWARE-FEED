# BRIDGE firmware

Public OTA binaries for the M5 bridge. Flash `ATOM_S3_R.bin` and `ATOM_S3.bin` only. Source is OPF-STORAGE-M5-BRIDGE `master-grok` at `d9ca7a0` (`build-firmware.yml`).

DTU versus RS485 is selected on the device after flash. `ATOM_S3_R_DTU` and `ATOM_S3_DTU` are not feed firmware.

`latest/` is the channel. Its version label is `v1.0.1`. A publish also writes an immutable `vX.Y.Z/` folder. This checkout currently has only `latest/` because older version folders were removed.

Flasher reads `latest.BRIDGE` and that product’s `versions[]` in the repository root `index.json`.
