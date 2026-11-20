# BMS v0.0.3

Firmware tag at d046dd1 (VC63), verified on the live .158 pack.

## VC53–VC63

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

## Also in this release (after v0.0.2, before VC53)

- Drop the web Settings and Battery tabs; settings are BLE-only (`cfg_get` / `cfg_set` / `cfg_schema`)
- Publish cell and temperature CSV over MQTT (`cell_data`, `temp_data`); `rt` stays compact and adds module geometry
- Move the standalone CAN dash to OPF-DASH
- Give every web control a BLE command and drop the USB serial console
- Expose the cached pack DTC list on the BLE console (`dtc_list` / `DTC|` notify)
