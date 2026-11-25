# BRIDGE v0.0.3

Firmware **0.0.3+VC51** (`4ddda59`, `version_code` 51). Tag `v0.0.3` on `master-grok`, retagged 26 Nov 2026 (Europe/Vilnius); earlier v0.0.3 tags were 0.0.3+VC48 (`8af90a2`), 0.0.3+VC47 (`12551a4`) and 0.0.3+VC43 (`ad9dc39`).

v0.0.3 moves all device settings to BLE (`cfg_schema` / `cfg_get` / `cfg_set`), leaves the web UI as a dashboard plus a read-only Status page, removes inverter auto-detect, hardens the firmware for 24/7 operation, adds BLE PIN pairing and a crash summary, and lists Sungrow SH6.0RS.

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
- **VC44:** `/diag` reports `cdump_present` and, when a panic image is stored, a compact `cdump` summary (reason, cause, task, pc, backtrace, fw, ELF sha; max 288 B). Size map in `docs/SIZE_VC44.md`, LVGL trimmed, unused features compiled out on ESP32.
- **VC45:** BLE SMP passkey pairing with bonding (MITM, display-only, static passkey); TX/RX need an encrypted, authenticated link. New BLE keys `ble_auth` (default 1) and `ble_pin` (4-6 digits), `ble_pin_reset` over BLE (`confirm=1`) and USB, `auth:` command; `/diag` adds `ble_pin_set`, `ble_auth`, `ble_bonds`, `ble_encrypted`. Factory reset restores the default PIN and clears bonds. See `docs/BLE_PAIRING.md`.
- **VC46:** default BLE PIN is **123456**. A stored 1234 is removed once at boot and bonds are cleared.
- **VC47:** Sungrow SH6.0RS (profile `20`) is listed on the BLE `profile` schema (`0,1,10,11,20`, locked by a host test) and in the manuals; on profile 20 the Dashboard shows import / export / idle (max 5000 W), max export and max charge / discharge current. Review notes in `docs/SUNGROW_SH6RS.md`. No web profile picker (model selection stays in the Flasher and BLE app).
- **VC48:** the Atom S3R LCD page 7/7 (SETUP) shows the running firmware version and build (`FW 0.0.3+VC48`, `BLD 8af90a2`), from the same values as `/diag` and `/health`; the redundant ACTIVE SETUP heading is removed to make room.
- **VC49:** URL OTA pauses the HTTP listener (`opfWebServerQuiesce()` / `opfWebServerResume()`) around the blocking download so `/diag` and `/health` cannot hit async_tcp mid-transfer. ElegantOTA and BLE OTA keep the server. `/diag` and `/api/coredump/summary` include the running ELF SHA and `cdump_matches_build` so a dump from an older image is not read as a panic of this build.
- **VC50:** signed P1 LoRa commands (`uart_reset`, `reboot`, `radio_reinit`) can be queued from the web, BLE, or MQTT and transmitted in the uplink RX window. The key is a build flag (`P1_CMD_KEY_HEX`); without it the radio never leaves receive.
- **VC51:** `/update` is open without a password and restyled. ElegantOTA `/ota/start` and `/ota/upload` have auth cleared. URL OTA skips basic auth and keeps the CSRF, JSON, and confirm gates. `web_auth` still covers inverter and P1 writes.

Remaining write-capable web endpoints: `POST /api/profile-command` (Dashboard controls), `POST /api/ota-preflight`, `POST /api/ota-url` and ElegantOTA `/update`. Deye register 80 remains read-only. AUTOMATIC_MODE is unchanged.

## Hardware validation

- Atom S3R `.110` (Deye HV) already runs VC51 (`4ddda59`) from the post-merge URL OTA, marked_valid. `.236` (DTU base) has been unreachable since 24 Nov and was not retried for this retag. VC44/VC46/VC47 soak on `.110` since 20 Nov: free heap 88-97 KB, no new panic. Waveshare (ATOM_S3) and T-CAN485 (ESP32) images are built for the feed; T-CAN485 site flash is held until on-site rollback is possible.
- Sungrow SH6.0RS is code-reviewed and host-tested only; no Sungrow unit has been tested.
- T-CAN485 has no BLE and no serial commands, so its Wi-Fi/MQTT keys stay at the NVS values or the one-time build-flag seed.
- P1 LoRa downlink commands (VC50) are built in but not active until `P1_CMD_KEY_HEX` is set on both the Bridge and the P1 image.

## Build

Built locally from a clean `4ddda59` worktree with Arduino-ESP32 3.20016 (espressif32@6.7.0), without `platformio.local.ini` secrets, and published to the FEED with `scripts/publish_firmware_feed.py`.
