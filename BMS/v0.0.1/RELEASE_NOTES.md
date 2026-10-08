# BMS v0.0.1

- Always-on BLE (`OPF-BMS-<id>`) for commissioning via the shared `/device` path — works without Wi‑Fi.
- BLE OTA, same protocol as Bridge (`ota_info` / `ota_begin` / `ota_data` / `ota_end`), usable from OPF-FLASHER and OPF-CONFIG-APP.
- BLE telemetry: `tel_get` / `telem_get` live pack snapshot for OPF-CONFIG-APP.
- eFuse-based `device_id` plus firmware version/build reported in `cfg_get` and `ota_info`.
- Read-only `board` identity (equals the FEED artifact name, e.g. `OPF_WS`, `OPF_T2CAN`) in BLE `ota_info` / `cfg_get` / `telem_get` and in `/health` + `/diag`; `cfg_set` on `board` / `device_id` / `fw` answers `ERR|read_only`.
- Web Device Console: Wi‑Fi and BLE link badges in the header (live, polled from `/health` every 4 s), same as the Bridge.
- Device Name over BLE: `cfg_set:device_name=` (max 32), advertised as `OPF-BMS-<name>`; no reboot needed.
- `telem_get` matches the web dashboard: power, contactors, charge/discharge limits, health and warnings, every cell voltage and temperature, Wi‑Fi/AP and BLE link state; `telem_cells:<n>` returns a slave's cells.
- Wi‑Fi modem sleep enabled for stable BLE + Wi‑Fi coexistence.
- Type dropdown: Slave/Display run SoftAP only; Master keeps STA + MQTT + web, with MS readiness and master-only fleet MQTT.
- New board `OPF_WS_DASH`: Waveshare ESP32-S3-Touch-LCD-4.3 / -5 (800×480 variant) / -7, 800×480 RGB panel with the BMS dash UI (based on `opf-dash`, Waveshare 16 MHz panel timing). Builds; untested on hardware.
- Super-stable BLE OTA (Bridge twin): resume after a BLE drop (120 s idle window), SHA-256 flash read-back before the boot switch, `verify_fail` on a bad image, ESP-IDF rollback until the new image passes health checks.
- Full-screen OTA progress view on boards with a screen (`opf-dash`, `OPF_WS_DASH`, `OPF_ATOM_S3R`); `ota_info` reports `lcd=1`.
- `cfg_get` adds read-only `wifi_cred_source` and `ssid_set`; feed `index.json` records the source commit and `fw_build` under `source`.
