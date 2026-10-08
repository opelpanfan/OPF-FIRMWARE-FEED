# BRIDGE v0.0.1

- BLE OTA hardened (BMS twin): resume via `next_seq`, read-back SHA256 check, and rollback if the new image fails.
- BLE telemetry: `telem_get` (BMS twin), plus P1-over-LoRa `dtu_*` / `p1_*` values in TELEM and `/values`.
- Deye HV: grid/load voltage and current, battery 2 absent gate, derived totals, and `device_id`.
- Read-only `board` identity (`ATOM_S3_R` / `ATOM_S3`, equals the FEED artifact name) in BLE `ota_info` / `cfg_get` / `telem_get` and `GET /health` + `/diag`.
- Credentials: NVS is the source of truth for Wi‑Fi, MQTT and OTA login; build-time values only seed empty keys once, so FEED images keep stored settings. `cfg_get`, `telem_get` and `/diag` report credential source/presence (never the values).
- FEED metadata: `source_sha` and `fw_build` recorded for each BRIDGE publish.
- UI: always-on BLE indicator (advertising vs connected).
- Build reports `fw_version` from the release tag.
