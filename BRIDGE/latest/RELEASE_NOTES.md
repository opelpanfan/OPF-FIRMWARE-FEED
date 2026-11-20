# BRIDGE v0.0.3

Firmware **0.0.3+VC43** (`ad9dc39`, `version_code` 43). Tag `v0.0.3` on `master-grok`, 20 Nov 2026 (Europe/Vilnius).

v0.0.3 moves all device settings to BLE (`cfg_schema` / `cfg_get` / `cfg_set`), leaves the web UI as a dashboard plus a read-only Status page, removes inverter auto-detect, and hardens the firmware for 24/7 operation.

## Changes since v0.0.2 (0.0.2+VC34)

- **VC35:** web settings editors removed. Inverter and LoRa tabs are gone and Status-page actions (RS-485 tests, restarts, factory reset, SoftAP open/close, telemetry resume, smartmeter capture) move to BLE (`reboot`, `mqtt_restart`, `factory_reset`, `ap_open` / `ap_close`, `sta_drop`, `rs485_*`, `sm_cap`, `p1_key_set` / `p1_key_clear`, `p1_reboot`, `p1_uart_restart`). Every former web setting keeps its BLE key.
- **VC36:** Wi-Fi, SoftAP and MQTT (including TLS, the CA and the MQTT OTA host list) are BLE-only. The Settings tab, `POST /device`, `POST /api/security` and `GET /wifi/scan` are removed; `GET /device` stays for the Dashboard. The USB serial command console is removed (logs, `[BOOT]` line and panic text remain; esptool flashing is unchanged).
- **VC37:** Status drops the RS-485, Inverter Detect and Soft AP sections. Those were already BLE-only; the removed HTTP paths return `{"ok":false,"error":"not_found"}`.
- **VC38:** the hidden Profile selector and Status Warnings / Recent events are removed. Profile is BLE `cfg_set` only. `/diag`, `/health` and `/values` keep every key.
- **VC39:** inverter auto-detect removed. Boot loads the saved profile and does not probe the bus; `detect_*` BLE commands are unknown. Manual profile and slave selection, `rs485_info` and `rs485_scan` stay. Inverter writes are never auto-enabled; the write gate is set only by BLE `cfg_set` or MQTT `inv_writes`.
- **VC40:** Status is one plain read-only list.
- **VC41:** `ap_hidden` SoftAP setting (NVS, default 0), reported on `/diag` and `/health`, cleared by factory reset.
- **VC42:** unused dashboard WebSocket and dead web JS removed. MQTT TX buffer raised to 12288 so the ~8.3 KB heartbeat and diag publish. Health and diag buffers are reused, BLE notifies are paced, and `lora_rx` is on the task watchdog.
- **VC43:** the Storage and Battery confirm popup is replaced by an apply review page. Back (button, Esc, browser back) returns to the previous tab and keeps edits; Apply posts the same `/api/profile-command` batch.

Remaining write-capable web endpoints: `POST /api/profile-command` (Dashboard controls), `POST /api/ota-preflight`, `POST /api/ota-url` and ElegantOTA `/update`. Deye register 80 remains read-only. AUTOMATIC_MODE is unchanged.

## Hardware validation

- Atom S3R `.110` runs VC43 (`ad9dc39`, boot 574, MQTT 3/3, P1 OK, `inv_writes`=1, Deye HV confirmed). Waveshare (ATOM_S3) and T-CAN485 (ESP32) images are built for the feed; T-CAN485 site flash is held until on-site rollback is possible.
- T-CAN485 has no BLE and no serial commands, so its Wi-Fi/MQTT keys stay at the NVS values or the one-time build-flag seed.

## Build

Built locally with Arduino-ESP32 3.20016 (espressif32@6.7.0), without `platformio.local.ini` secrets. GitHub Actions artifact storage is full at the account level, so tag CI is expected to fail at artifact upload and the FEED was published locally with `scripts/publish_firmware_feed.py`.
