# BMS v0.0.3

Firmware **0.0.3+VC73** (`bfb4db4`, `version_code` 73). Tag `v0.0.3` on `master-grok`, published 24 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC63 (`d046dd1`). Verified on the live .158 pack.

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
