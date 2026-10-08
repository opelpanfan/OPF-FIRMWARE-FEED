# BRIDGE v0.0.8

- BLE OTA hardened (BMS twin): resume via `next_seq`, read-back SHA256 check, and rollback if the new image fails.
- BLE telemetry: `telem_get` (BMS twin), plus P1-over-LoRa `dtu_*` / `p1_*` values in TELEM and `/values`.
- Deye HV: grid/load voltage and current, battery 2 absent gate, derived totals, and `device_id`.
- UI: always-on BLE indicator (advertising vs connected).
- Build reports `fw_version` from the release tag.
