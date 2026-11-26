# BMS v0.0.3

Firmware **0.0.3+VC90** (`6144b8d`, `version_code` 90). Tag `v0.0.3` on `master-grok`, published 26 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC73 (`bfb4db4`). Verified on the live .158 pack.

## VC74–VC90

- VC74: PSA battery type rework + contactor/wake settings
- VC75: contactor control for PSA V1/V2, wake flag on all types
- VC76: match PSA V2 CAN contactor, wake and DTC clear to the eCMP schedule; keep TesterPresent and DTC read off eCMP UDS
- VC77: store every pack as one series cell count
- VC78: rename Waveshare RS485-CAN board label
- VC79: remove BMS web settings
- VC80: drive the negative contactor GPIO on BMW SE30
- VC81: drive the contactor sequence from b_ctc_ctrl
- VC82: replace split contactor controls with one b_ctc_type
- VC83: add CAN bus (stock BMS) as b_precharge 2
- VC84: reorder slave comm enum to 0 None, 1 RS485, 2 CAN
- VC85: reject CAN bus selectors the board cannot take
- VC86: default T-2CANFD inverter to CAN1, pack stays on CAN2
- VC87: carry b_cell_cap as 32-bit on the RS485 settings push
- VC88: send FAKE pack values on the Pylon live frames
- VC89: PSA V2 Clear DTC runs the reset sequence, add BLE reset_bms
- VC90: board_profile accepted only for the firmware image's own board(s)

## VC65–VC73

- VC65: BLE coredump_info and coredump_get
- VC66: BLE passkey pairing, bonding, and PIN reset
- VC67: show Read OTA data in a modal
- VC68: make grace and timeout timers safe across millis() rollover
- VC69: Resubscribe all MQTT topics after every connect
- VC70: Hold a BLE contactor close through every failsafe
- VC71: Honor the manual contactor hold on PSA 82 type 3
- VC72: Restyle the OTA page to match the dash
- VC73: Add an OTA button on the Status page

## Also in this release (after v0.0.2, through VC63)

- Drop the web Settings and Battery tabs; settings are BLE-only (`cfg_get` / `cfg_set` / `cfg_schema`)
- Publish cell and temperature CSV over MQTT (`cell_data`, `temp_data`); `rt` stays compact and adds module geometry
- Move the standalone CAN dash to OPF-DASH
- Give every web control a BLE command and drop the USB serial console
- Expose the cached pack DTC list on the BLE console (`dtc_list` / `DTC|` notify)
- VC53: remove Status action sections and their HTTP endpoints
- VC54: remove Status Health and flatten Device Overview
- VC55: remove BMS self-test and keep the OTA boot-health gate
- VC56: remove Dashboard Site summary and keep its values on Status
- VC57: add ap_hidden so the SoftAP can hide its SSID; drop the Hide SSID control from the Status page
- VC58: remove the Live data row from the Dashboard
- VC59: match application HTTP routes exactly
- VC60: build /diag snapshot off async_tcp; fix slim /health snapshot
- VC61: remove /health full duplicate and dead code
- VC62: task watchdog config + heartbeat snapshot in reboot log; fix task heartbeat ages
- VC63: coalesce soak NVS writes; label async_tcp heartbeat (not_watched, last feed on async_tcp_last_feed_age_ms)
