# BRIDGE firmware

Public OTA binaries for the M5 bridge. Flash `ATOM_S3_R.bin` and `ATOM_S3.bin` only. Source is OPF-STORAGE-M5-BRIDGE `master-grok` at `d9ca7a0` (`build-firmware.yml`).

DTU versus RS485 is selected on the device after flash. `ATOM_S3_R_DTU` and `ATOM_S3_DTU` are not feed firmware.

`latest/` matches immutable folder `v1.0.11`. Higher version folders `v1.0.12`–`v1.0.14` were published earlier. Flasher reads `latest.BRIDGE` in the repository root `index.json` and does not select the highest version number.
