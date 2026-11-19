Tag `v0.0.2` → `a1cc2bb` (firmware `0.0.2+VC34`, proven on Atom S3R .110). Feed: OPF-FIRMWARE-FEED `master-grok` (BRIDGE/v0.0.2 + latest; commit sha filled after publish).

GitHub Actions artifact storage is still full at the account level, so FEED was published locally with `scripts/publish_firmware_feed.py` using Arduino-ESP32 3.20016, without `platformio.local.ini` secrets.

# Release Notes - v0.0.2

Release type: Stability, diagnostics, and versioning
Status: Retagged on `master-grok` as `v0.0.2` at `a1cc2bb` (`0.0.2+VC34`) on 20 Nov 2026 (Europe/Vilnius)

## Retag 20 Nov 2026 — 0.0.2+VC34 (`a1cc2bb`)

This tag now points at `master-grok` `a1cc2bb`. Firmware reports `0.0.2+VC34` (`version_code` 34). Previous tag target was `3cf5c04` (firmware `0.0.2+VC33`).

### Since the previous v0.0.2 tag

- **VC34 LoRa RX drain:** LoRa RX is drained off the UART lock so P1 packets are not dropped while RS485 or MQTT holds the bus. `/diag` adds `lora_uart_rx_overflow`, `lora_reader_gap_ms_max`, `lora_lock_wait_max_ms`, and `lora_rx_stack_free` (`a1cc2bb`).
- Deye register 80 remains read-only. AUTOMATIC_MODE is unchanged.

### Hardware validation for this retag

- Atom S3R `.110` is on VC34 (`a1cc2bb`, boot 565, MQTT 3/3, `short_id_effective` I9DYA8, reg 128=50 / 130=1, `telemetry_read_ms` 5000). At ~3 min uptime P1/LoRa was `dtu_rx_rate_hz` 0.97, `dtu_rx_fail` 0, `dtu_rx_gap_ms_max` 1054, overflow 0. Waveshare and T-CAN485 images are built for the feed; T-CAN485 site flash is held until on-site rollback is possible.

## Summary

v0.0.2 hardens MQTT and concurrent access after a field PANIC on Atom Bridge (lwIP `pbuf_free` double-free from multi-task `PubSubClient` / `WiFiClient` use), adds read-only coredump HTTP access, finishes the PSRAM heap phases, and raises LCD task stack headroom. Web UI layout is unchanged (P1 Meter card moved only).

Retagged on `a1cc2bb`: `0.0.2+VC34` (LoRa RX drain / P1 reliability, plus VC31–VC33: BLE chunk retry, ESP32 without NimBLE, RS485 cadence, SoftAP and short id, MQTT-outage local-control hold).

## Retag 19 Nov 2026 — 0.0.2+VC33 (`3cf5c04`)

This tag now points at `master-grok` `3cf5c04`. Firmware reports `0.0.2+VC33` (`version_code` 33). Previous tag target was `646543a` (firmware `0.0.2+VC30`).

### Since the previous v0.0.2 tag (VC31–VC33)

- **VC31 BLE and ESP32 size:** BLE TX backpressure (at most 4 notifies in flight, 400 ms per-part budget) and a `C|ERR|ble_tx|incomplete` line when a part cannot be sent. The ESP32 (T-CAN485) env no longer includes NimBLE, which frees flash. `/diag` adds `heap_largest` and `heap_largest_min`. `telemetry_read_ms` default is 5000 (`8209006`).
- **VC32 RS485, LoRa UART, SoftAP, short id:** RS485 lock is taken per key, with fast values every cycle and slow values every 30 s; `/diag` adds `rs485_cycle_ms` and `rs485_cycle_max_ms`. The LoRa UART has a single recursive-lock owner. SoftAP is configurable (`ap_enable`, `ap_ssid`, write-only `ap_password`); `short_id` can be derived or set (6 chars 0-9A-Z). `ui_theme` and `ui_language` are BLE-only and are no longer on the web settings schema (`a71dcd9`).
- **VC33 MQTT-outage resilience:** a loop watchdog keeps local inverter, RS485 and LoRa control running through MQTT or internet outages instead of rebooting; flash writes are reduced; T-CAN485 gets a log buffer. The 5 s / 10 s `grid_p` cadence on the dashboard was display-only: the timestamp now advances on every successful read, not only when the value changes (`3cf5c04`).
- Deye register 80 remains read-only. AUTOMATIC_MODE is unchanged.

### Hardware validation for this retag

- Atom S3R `.110` is on VC33 (`3cf5c04`, boot 564, MQTT 3/3, `short_id_effective` I9DYA8, reg 128=50 / 130=1, `telemetry_read_ms` 5000). Waveshare and T-CAN485 images are built for the feed; T-CAN485 site flash is held until on-site rollback is possible.

## Summary

v0.0.2 hardens MQTT and concurrent access after a field PANIC on Atom Bridge (lwIP `pbuf_free` double-free from multi-task `PubSubClient` / `WiFiClient` use), adds read-only coredump HTTP access, finishes the PSRAM heap phases, and raises LCD task stack headroom. Web UI layout is unchanged (P1 Meter card moved only).

Retagged on `3cf5c04`: `0.0.2+VC33` (BLE chunk retry, ESP32 without NimBLE, RS485 cadence, SoftAP and short id, MQTT-outage local-control hold).

## Retag 19 Nov 2026 — 0.0.2+VC30 (`646543a`)

This tag now points at `master-grok` `646543a`. Firmware reports `0.0.2+VC30` (`version_code` 30). Previous tag target was `82a71fc` (firmware `dd43363`).

### Since the previous v0.0.2 tag

- **VC28 versioning:** firmware reports `0.0.2+VC<N>`; numeric `version_code` is on `/health`, `/diag`, `/device`, `/values`, BLE, MQTT, and FEED `source.version_code`. Semver stays on the `v0.0.2` tag; `N` lives in `version_code.txt` and is bumped on each firmware commit (`748fe74`).
- **VC29 Deye HV per-phase grid power:** signed INT32 `grid_p_l1..3` from register pairs {616,705}, {617,706}, {618,707} (same decode as `grid_ctp`). The existing 616..708 span is used, so there are no extra Modbus requests. Also on BLE `telem_get` (`8c419d8`, `fea48c3`).
- **VC30 lazy PSRAM rings:** large static rings moved to first-use heap allocation; blocks of 1 KB or more go to PSRAM on the S3R (`646543a`).
- **Stack fix:** S3 task stacks sized from field high-water marks (net about −3 KB internal heap) (`ed6ac77`).
- **Unified settings registry:** one settings list for BLE, web (`GET /api/settings-schema`), and the Flasher; BLE `cfg_schema` / `cfg_set` also expose former web-only keys (`lcd_rotation`, `chip_id_string`, `mqtt_ca`, `lora_*`). Unknown `hw_board` tokens are rejected on web and BLE save (`4388cf4`, `51e84ed`, `2a54bf9`).
- **BLE:** only one central at a time; `telem_get` includes held P1-over-LoRa readings when `atom_base=dtu`; P1 command state keys and reboot / P1 UART-restart commands.
- **Site mode (T-CAN485):** BLE off by default on the PSRAM-less ESP32 site build (NVS `site_ble=1` re-enables); Bluetooth controller RAM released when BLE is off; 1.0.4 MQTT identity/commands, NVS first-boot migration, Deye HV default profile; `rs485_pulse` option. Hardware flash of site Bridges waits until someone is on site to roll back.
- **CI:** the build/feed workflow runs only on `v*` tags and manual dispatch (`af6a859`).
- Other post-tag work still in this build: LoRa RX watchdog and faster RX re-arm after P1 command TX; MQTT SUBACK confirmation; Sungrow SH6.0RS profile (not hardware-proven); Deye register 80 remains read-only.

### Hardware validation for this retag

- Atom S3R `.110` is on VC30 (`646543a`). Waveshare and T-CAN485 images are built for the feed; T-CAN485 site flash is held until on-site rollback is possible.

## Summary

v0.0.2 hardens MQTT and concurrent access after a field PANIC on Atom Bridge (lwIP `pbuf_free` double-free from multi-task `PubSubClient` / `WiFiClient` use), adds read-only coredump HTTP access, finishes the PSRAM heap phases, and raises LCD task stack headroom. Web UI layout is unchanged (P1 Meter card moved only).

Retagged on `646543a`: `0.0.2+VC30` (versioning, Deye per-phase grid power, lazy PSRAM rings, unified settings, site mode, stack trim).

Earlier retag on `dd43363`: nimble_host task stack 4→5 KB, staggered first-page fetches, gzipped web UI 62,805→59,513 B.

Earlier retag on `829d01c`: heap pass 2 (measured stack trims, NimBLE msys 12, ESP32_S3 release `-Os`), SoftAP closes 60 s after STA is stable, plus the earlier Deye 128/130 restore fix, Settings Save fix, BMS-style layout, and Device Settings move.

Earlier retag on `cf5aaee`: added the Deye reg 128/130 TOU restore fix, the Atom S3R internal-heap fix, the Settings Save (NVS key) fix, the BMS-style Settings layout, and the Device Settings move with collapsed dashboard sections, on top of P1 in MQTT and the V2C EV charger.

Earlier retag on `378fad4`: added the OTA crash fix for Atom S3R / Waveshare OPF_WS, S3R LCD rotation, Solis S6 BMS cell min/max V/T, and the P1 Meter card move.

## Highlights

- MQTT single-owner: only `comms_loop` touches the MQTT client; other tasks publish through a FreeRTOS queue and read a cached connected flag.
- OTA quiesce handshake parks `comms_loop` cooperatively (semaphore, timeout) instead of `vTaskSuspend`.
- Read-only coredump HTTP: `GET /api/coredump/summary` and `GET /api/coredump` (no erase).
- Telemetry slot lock with snapshot reads; staged `/device` `chip_id` override applied by `comms_loop`.
- LVGL / `lvgl_loop` stack raised 4 KB → 8 KB.
- Host lint: MQTT client owner allowlist + telemetry writer allowlist (`test/host/run_all.sh`).
- PSRAM phases 1–3: diag watermarks, large cold buffers, mid-size JSON bodies in PSRAM when present.

## Added

- Read-only `GET /api/heap`: internal / DMA / PSRAM free, window and boot low-water marks with activity context (BLE, SoftAP, web, MQTT, EV, ...), per-task stack free and placement (4a09fc1).
- Atom S3R LCD rotation setting (`lcd_rotation` 0/90/180/270, default 180, NVS `lcd_rot`) next to the Base selector in Device settings; applied live (6f05233).
- MQTT telemetry (`rut/<id>/telemetry` + legacy `storage/<chip>/bridge`) includes P1-over-LoRa data when the Atom base is DTU: `dtu_link`, `dtu_state`, `dtu_rf_*`, `dtu_p1_data`, `dtu_p1_fresh`, `p1_valid`, `p1_data_invalid`, and the `p1_*` measurements (same keys/units as BLE `telem_get` and `/values`; `p1_e_imp_wh`/`p1_e_exp_wh` as exact integers). No `dtu_rx_*` debug counters. Non-DTU payloads unchanged.
- V2C Trydan EV charger (read-only): Device settings "EV charger" (None / V2C Trydan) + IP (NVS `ev_type`/`ev_ip`, live, also BLE `cfg_set`); `ev_loop` polls `GET http://<ip>/RealTimeData` every 5 s (backoff to 60 s). MQTT adds only `ev_type`, `ev_link`, `ev_state`, `ev_paused`, `ev_power_w`, `ev_energy_kwh`; full `ev_*` set on BLE `telem_get`, `/values` (`ev`) and `GET /api/ev`; Dashboard EV Charger card below P1 Meter. P1 Meter / EV Charger headers show last-update time. No charger control.
- Solis S6: BMS cell voltage min/max (34348/34349, ×0.001 V) and cell temperature min/max (34350/34351, ×0.1 °C), plus BMS2 equivalents (34373–34376), from the Ver3.5 register map (2895186).
- `src/opf_coredump_http.{h,cpp}` — read-only flash coredump summary and raw dump over HTTP.
- Host tests: `test_mqtt_owner_lint.cpp`, `test_telemetry_writer_lint.cpp`, `test/host/run_all.sh`.
- Diag / heap: PSRAM presence and free watermark reporting; cold buffers and mid-size JSON moved to PSRAM when available.

## Changed

- NimBLE host task stack 4→5 KB (`CONFIG_BT_NIMBLE_HOST_TASK_STACK_SIZE=5120`). Under a BLE connection plus GATT discovery the free watermark is about 2040 B (was ~824–888 B) (7f2089f).
- Web UI: `GET /device` completes before the live poll chain starts so the full `/dashboard-telemetry` no longer overlaps it. Unused CSS/JS removed; CSS token-squeezed in the deterministic gzip -9 / mtime 0 minifier (62,805 → 59,513 B) (dd43363).
- Heap pass 2: comms 16→8 KB, ota 10→9 KB (URL-OTA used ~6.7 KB, so 5–6 KB was unsafe), telem 8→6 KB, `CONFIG_ASYNC_TCP_STACK_SIZE` 16→8 KB. NimBLE `CONFIG_BT_NIMBLE_MSYS1_BLOCK_COUNT` 24→12. ESP32_S3 `build_type=release` with `-Os` and `-g2` (829d01c / 8e1adfb / c78054a).
- SoftAP: no 5-minute boot window. The portal stays until 60 s after STA has an IP (`sta_hold`), reopens after STA has been down 15 s (or immediately if there are no credentials). Explicit windows (serial `AP OPEN`, `POST /api/ap/window`, OTA 30 min) unchanged. `/diag` reports `ap_want` / `ap_reason` (c78054a, 1f5254a).
- Settings: BMS-style form grid (3 columns, 1 column below 640 px). Device Settings rows Name / Type, Board, Atom base / Screen rotation, EV charger, EV IP; MQTT Server + Port (one column each) / Username + Password. LoRa page uses the same section-header markup as the other pages. Ids and NVS keys unchanged (980d257).
- Device mode fields moved from the Inverter tab to Settings → Device Settings; dashboard Instant control, Storage mode and Battery sections load collapsed (9ae5234).
- Atom S3R heap: after setup, runtime allocations >= 1 KB use PSRAM (`OPF_EXTMEM_THRESHOLD`), ESPAsyncWebServer in-flight data per response capped at 2872 B (`OPF_ASYNC_MAX_INFLIGHT`, build-time patch `tools/patch_asyncweb_inflight.py`), `ev_loop` stack 6 KB (358a564).
- Dashboard: P1 Meter card moved between Live and Instant Control (2944d47).
- MQTT ownership and publish path (queue + cached connected state).
- OTA start: quiesce handshake with `comms_loop` (no suspend of the MQTT owner task).
- `/device` `chip_id` override is staged and applied on the comms task.
- `TELEMETRY[]` writes take a per-slot lock; readers use snapshots.
- `lvgl_loop` stack (`LVGL_TASK_STACK_BYTES`) 8192.

## Fixed

- Deye TOU restore (idle / end / lease fail-safe) wrote reg 128 (grid charge current) and 130 (grid charge enable) back from the session-start snapshot even when the session never wrote them, reverting a manual change (50 A → 1 A). Now restored only when the session's remote control wrote them; the flags are kept in the NVS snapshot across a reboot (snapshots from older firmware restore neither). Other registers unchanged; reg 80 never touched (cf5aaee).
- Settings Save: NVS key `telemetry_read_ms` (17 chars) exceeded the 15-char limit; the failed write aborted the save and skipped the following fields. Renamed to `telem_read_ms` (API name unchanged); failures are listed by key and the remaining fields are still saved (d2d6520).
- Atom S3R internal heap fell to about 20 KB with a BLE app connected, SoftAP open and dashboard loads (heap_warn); see Changed (358a564).
- OTA crash on Atom S3R / Waveshare OPF_WS: OTA start/end (web, URL, MQTT) and BLE OTA drove the status NeoPixel on GPIO35, an octal-PSRAM line on those boards, corrupting PSRAM/heap (panics seconds after OTA, 0x40404040 patterns). Status-LED writes now go through `statusLedShow()`, gated on the runtime board (378fad4). Atom S3 and T-CAN485 unchanged.
- Multi-task MQTT / `WiFiClient` use that could double-free lwIP `pbuf`s (field PANIC).
- OTA path that suspended `comms_loop` while the network stack was still in use.

## Boards / environments

- PlatformIO envs (two MCU builds): `ESP32_S3` (8 MB partitions; runtime `hw_board` = Atom S3 / Atom S3R / Waveshare OPF_WS) and `ESP32` (4 MB; LilyGO T-CAN485 only).
- Feed still ships legacy names `ATOM_S3_R.bin` / `ATOM_S3.bin` (identical `ESP32_S3` image) plus `ESP32.bin`.
- Hardware-proven on Atom S3R `.110` for this tag (VC30); `.236` and earlier tags were proven for previous retags. WS and T-CAN485 not hardware-proven on this tag.

## Upgrade Notes

- `fw_version` is taken from the git tag at build time (`version_extractor.py`) and is reported as `0.0.2+VC<N>`; `fw_build` remains the short commit SHA; `version_code` is the integer N.
- Existing NVS settings (Wi-Fi, MQTT, OTA login) are preserved across OTA.
- No web UI redesign; FEED publish is separate and only when explicitly requested.

## Validation Notes

- `646543a` (VC30): Atom S3R `.110` flashed and health-checked after merge. Lazy rings use first-use heap / PSRAM. T-CAN485 site rollout is held until on-site rollback is possible.
- `dd43363`: Atom S3R `.236` URL OTA; BLE connect + GATT discovery, nimble_host free 2040 B; first dashboard-load heap min 86.7 KB, after walking every page 76.6 KB through a 10-min soak (MQTT/P1/EV ok, 0 disconnects). Settings Save 200; collapse-on-load and 3-column Settings intact. URL OTA on Atom S3R `.110`: settings identical, no inverter writes; session 71 still active (lease survived reboot); reg 128 stayed 50 A; 10-min soak heap min 78.8 KB, MQTT 0 disconnects, RS485/P1/EV ok. Host tests (21 suites) pass.
- `829d01c`: Atom S3R `.236` boot-worst (BLE across reboot + SoftAP + page loads) 78.8 KB internal free; 6× `GET /` 59.1 KB; 10-min soak 80.2 KB, 0 MQTT disconnects, 0 BLE notify drops at MTU 517; 3 consecutive URL OTAs. URL OTA on Atom S3R `.110`: settings identical, no inverter writes, AP closed ~62 s after STA up, MQTT `opf.systems:1883` (TLS off) stayed connected (0 disconnects) for a 10-min status soak; heap min 71.2 KB (was 40.7 KB), `heap_warn` false; EV / P1 / RS485 ok.
- `cf5aaee`: Atom S3R `.236` worst case (BLE polling across a reboot + SoftAP + dashboard loads) boot low 58–62 KB internal free, 10-min soak low 54.6 KB, 0 MQTT disconnects; Settings Save 200 and values persist across reboot. URL OTA on Atom S3R `.110`: settings identical, no inverter writes, 5-min soak with MQTT / RS485 / EV / P1 ok; internal-heap low 40.7 KB with the BLE app active (was 20 KB). Host tests (21 suites) pass, incl. Deye 128/130 restore cases.
- OTA fix `378fad4`: three clean OTAs on Atom S3R `.236` (DTU base) and one clean URL OTA plus soak on Atom S3R `.110`; no new coredump.
- Proven on lab Atom `.110` (`hw_board=ATOM_S3_R`, non-DTU): OTA/soak on `7d6d1a7` (`fw_build=7d6d1a7`) after MQTT single-owner + two-env work.
- Host lint / host test suite included for MQTT owner and telemetry writers.
- Waveshare OPF_WS and LilyGO T-CAN485: feed images built; **not** hardware-tested on this tag.
