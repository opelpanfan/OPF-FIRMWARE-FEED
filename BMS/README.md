# BMS firmware

Public OTA binaries for BMS. New publishes come from OPF-STORAGE-DASH `master-grok`, env `opf-ws`, as `OPF_WS.bin`.

`latest/` matches immutable folder `1.0.2`. That is the channel flasher should use. `v1.0.x` folders are a separate older line and are not the same bytes as `1.0.x`.

Flasher reads `latest.BMS` in the repository root `index.json`.
