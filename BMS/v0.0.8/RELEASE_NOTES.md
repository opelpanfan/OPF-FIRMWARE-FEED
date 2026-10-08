# BMS v0.0.8

- Always-on BLE (`OPF-BMS-<id>`) for commissioning via the shared `/device` path — works without Wi‑Fi.
- BLE OTA, same protocol as Bridge (`ota_info` / `ota_begin` / `ota_data` / `ota_end`), usable from OPF-FLASHER and OPF-CONFIG-APP.
- BLE telemetry: `tel_get` / `telem_get` live pack snapshot for OPF-CONFIG-APP.
- eFuse-based `device_id` plus firmware version/build reported in `cfg_get` and `ota_info`.
- Web Device Console: sticky BLE status bar (advertising / connected) mirrored in `/health` and `/diag`.
- Wi‑Fi modem sleep enabled for stable BLE + Wi‑Fi coexistence.
- Type dropdown: Slave/Display run SoftAP only; Master keeps STA + MQTT + web, with MS readiness and master-only fleet MQTT.
