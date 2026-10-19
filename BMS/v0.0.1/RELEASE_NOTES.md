# BMS v0.0.1

- Web UI: v0.0.1 layout restored (Dashboard, Battery, Settings, Status). New settings sit as plain fields in their v0.0.1 sections.
- Soft start: after boot, charge and discharge limits ramp from 5 A to max over 60 s.
- SoC taper: charge and discharge limits ramp from 5 A at the low and high SoC ends and near cell voltage limits.
- Low-SoC fix: SoC follows IVT Ah counting (charge raises it), seeded from the real reading once cells are valid, with spike rejection and hysteresis. Stops the 5%/7% charge/discharge loop.
- Soft stop: OTA and other requested reboots ramp current down first, then reboot.
- Crash fix: `logs_loop` panic (JSON allocator double-free, unlocked console print, MQTT publish race).
- Settings: keys over 15 characters renamed so they save.
- `/health`: ramp, taper, SoC and last restart reason fields.
- Stability from earlier on this line: OTA watchdog fix, coredump capture and `/coredump`, PSA2 96-cell decode, IVT support, UV failsafe.
