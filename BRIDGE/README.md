# BRIDGE firmware

Public OTA binaries for the M5 bridge. A release is `ATOM_S3.bin` and `ATOM_S3_R.bin` together, built from OPF-STORAGE-M5-BRIDGE `master-grok` (`build-firmware.yml`). DTU envs are not published as separate feed binaries.

`latest/` matches immutable folder `v1.0.11`. Higher version folders `v1.0.12`–`v1.0.14` were published earlier. Flasher reads `latest.BRIDGE` in the repository root `index.json` and does not select the highest version number.
