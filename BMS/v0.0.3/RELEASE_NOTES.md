# BMS v0.0.3

Firmware **0.0.3+VC101** (`7f17616`, `version_code` 101). Tag `v0.0.3` on `master-grok`, published 27 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC100 (`50c03fa`), 0.0.3+VC97 (`eece3ff`), 0.0.3+VC96 (`e7ce2f5`) and 0.0.3+VC90 (`6144b8d`). This build fixes BLE pairing from Windows.

## VC98–VC101

- VC98: watchdog heartbeat snapshot restore after a crash reboot (76 B packed snapshot); MQTT writes bounded to 5000 ms per write; `/diag` gains `mqtt_write_*` keys
- VC99: RS485 master waits 28791 us for the first reply byte (was 5 ms); failure back-off counted per slave instead of one shared counter
- VC100: a SLAVE on a board with RS485 and no slave CAN bus treats a stored `b_slave_com` None as RS485 in RAM only (NVS and `cfg_get` unchanged); every MASTER creates the `rs485_poll` task at boot and idles it when there are no slaves or the link is None; `/diag` gains `slave_link`. Wire format, baud, settings push and MQTT unchanged
- VC101: BLE uses legacy passkey pairing (`OPF_BLE_SC_ENABLED` defaults to 0; LE Secure Connections stay a build option) and no longer calls `startSecurity` on connect, so the central starts pairing (fixes Windows Settings and WinRT "Connection failed"). TX/RX still require encryption and authentication; display-only static passkey (`ble_pin`, default 123456) and the 3-bond store (oldest dropped) are unchanged. The auth log line never includes the passkey or keys

## VC91–VC97

- VC91: dropped (the relay-control-via-web-UI row was Flasher-only; Flasher removed it in its VC57)
- VC92: default b_mqtt_contactor on when the NVS key is missing
- VC93: gate non-SE30 BMW iX PACK_SOC on E5CE ready, otherwise hold the last value
- VC94: one-decimal SoC for BMW iX (E5CE pptt) on web UI and BLE via soc_cpct (0.01 %); MQTT unchanged
- VC95: PSA V2 reads SOH once after boot (0x22 DC64) with retries at 5, 15 and 45 s, stored in PACK_SOH; /diag gains soh_boot_* keys
- VC96: CAN IDs shown as uppercase 0x-hex on serial, logs and /diag (lib/UTILS/can_id_fmt.h); cfg_set for b_ivt_id_base and b_i2c_addr accepts 0x, decimal or bare hex. Wire, NVS and MQTT unchanged
- VC97: copy CAN ID keys in /diag `psa2_tx_suppressed` and `can_dup_rx_ids` so /diag is valid JSON

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
