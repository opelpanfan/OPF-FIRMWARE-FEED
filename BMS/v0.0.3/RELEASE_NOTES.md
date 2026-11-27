# BMS v0.0.3

Firmware **0.0.3+VC105** (`ad85bc9`, `version_code` 105). Tag `v0.0.3` on `master-grok`, published 27 Nov 2026 (Europe/Vilnius); the earlier published v0.0.3 was 0.0.3+VC102 (`084cd93`). VC103 (`488b11e`) and VC104 (`e54464c`) were merged to `master-grok` but were not published to this feed. Earlier published tags were 0.0.3+VC101 (`7f17616`), 0.0.3+VC100 (`50c03fa`), 0.0.3+VC97 (`eece3ff`), 0.0.3+VC96 (`e7ce2f5`) and 0.0.3+VC90 (`6144b8d`). This build renumbers config enums so 0 means None, with a safe NVS migration onto new keys.

## VC103–VC105

- VC103: one shared enum id header; magic enum literals in firmware and host tests are replaced with those ids
- VC104: drop test inverter 9; boolean settings are stored and accepted only as 0 or 1; the firmware image id is a read-only cfg key
- VC105: NONE=0 renumber of violator config enums with a safe NVS migration onto new keys (`board_prof2`, `b_bat_can2`, `b_inv_can2`, `b_slv_can2`, `b_dsp_can2`, `b_cmp_src2`, `b_do_neg2` / `pre2` / `pos2` / `gate2`, `b_wake2`, `b_i2c_polarity`). The one-shot commit key `nz_mig=1` is written last; old keys are left untouched so a rollback image still reads the previous encoding. `cfg_get` reports `enum_nz=1`. `cfg_set` writes an old key only when the new value has an old encoding (bus / cmp / wake `None` are not written back; i2c `None` is written to `b_i2c_activelow` as 1). Fail-safe 0: no pack CAN driver and contactors held open, no inverter TX, slave CAN link down, no dash TX, CMP limits 0, no wake TX. A missing `b_wake` uses the new type default (Mute=1 for types 1 and 4, Play=2 otherwise) instead of being treated as a legacy 0/1 value. GPIO 0 is never a contactor/DO pin. Default `b_cmp_current_source` is CAN (2). Factory stored `b_i2c_polarity` is 0 (None / board default, active-low); both 0 and 1 drive active-low. `b_ctc_ctrl` / `b_relay_ctrl` are retired from MQTT health and BLE `cfg_get` but are not renumbered in NVS. Unchanged: `b_priority`, `b_type`, `b_inverter`, `b_protocol`, `b_precharge`, `b_ctc_type`, `b_slave_com`, `b_addon`, chemistry, `DEVICE_STATUS`, and 0/1 flags. MQTT topic/payload/size/buffer are unchanged except the agreed wake-value change and the retired legacy keys.

### Old to new (VC105)

- `board_profile`: old 0–6 → 1–7, old 7 None → 0
- battery / inverter / slave CAN bus: old 0 CAN1 → 1, old 1 CAN2 → 2, new 0 None
- display CAN bus: old 2 Off → 0, old 0 CAN1 → 1, old 1 CAN2 → 2
- `b_cmp_current_source`: old 0 SOC → 1, old 1 CAN → 2, new 0 None
- contactor DO: old -1 None → 0 on the wire (internal -1), GPIO n stays n; GPIO 0 is not a pin
- `b_wake`: old 0 Mute → 1, old 1 Play → 2, new 0 None (no TX)
- `b_i2c_activelow` replaced by `b_i2c_polarity`: old 1 → 1 Active-low, old 0 → 2 Active-high, new 0 None (board default, active-low)

## VC98–VC102

- VC98: watchdog heartbeat snapshot restore after a crash reboot (76 B packed snapshot); MQTT writes bounded to 5000 ms per write; `/diag` gains `mqtt_write_*` keys
- VC99: RS485 master waits 28791 us for the first reply byte (was 5 ms); failure back-off counted per slave instead of one shared counter
- VC100: a SLAVE on a board with RS485 and no slave CAN bus treats a stored `b_slave_com` None as RS485 in RAM only (NVS and `cfg_get` unchanged); every MASTER creates the `rs485_poll` task at boot and idles it when there are no slaves or the link is None; `/diag` gains `slave_link`. Wire format, baud, settings push and MQTT unchanged
- VC101: BLE uses legacy passkey pairing (`OPF_BLE_SC_ENABLED` defaults to 0; LE Secure Connections stay a build option) and no longer calls `startSecurity` on connect, so the central starts pairing (fixes Windows Settings and WinRT "Connection failed"). TX/RX still require encryption and authentication; display-only static passkey (`ble_pin`, default 123456) and the 3-bond store (oldest dropped) are unchanged. The auth log line never includes the passkey or keys
- VC102: `rs485_poll` stores a fresh wake stamp after its 1 s idle delay and during OTA (sleeps 10 ms instead of `vTaskDelayUntil`), and snaps a stamp more than 5 periods stale (tick-wrap safe, `lib/UTILS/task_wake_policy.h`). Since VC100 a stale stamp made the task busy-loop when an OTA started, starving IDLE0 until the 30 s task watchdog reset the unit (seen on a unit with 1744 s uptime). No protocol, settings, MQTT or RS485 frame-timing changes

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
