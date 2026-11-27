# OPF-FLASHER v0.0.3 (package 0.0.2+VC95)

Built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `6a925e2494777bb4e1a40eb6c3d8f2790873a812` on `master-grok` (app version 0.0.2+VC95, git tag `v0.0.3`).

This feed folder is `FLASHER/v0.0.3` because `FLASHER/v0.0.2` is the immutable VC42 package and must not be replaced. The app semver is still 0.0.2.

- **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package with bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.
- **Windows:** `OPF-FLASHER-win-x64.exe` — portable 7-Zip LZMA2 self-extractor (Qt 6.8.3, official MSVC kit, cross-built on the OptiPlex). Run it, extract the `OPF-FLASHER-qt-win64` folder, and start `OPF-FLASHER.exe` from that folder. Leave the Qt DLLs, the MSVC runtime, plugin folders (`tls/` included), and `tools/` next to the exe. esptool 5.5.0 and xPack OpenOCD 0.12.0-7 are bundled as Windows binaries. This Windows build has not been tested on a real Windows machine. It now ships `tls/qschannelbackend.dll` and `tls/qcertonlybackend.dll`, which earlier v0.0.3 (VC44) packages were missing; those are required for HTTPS (the firmware feed) and MQTT TLS.

macOS is not included.

What changed since the previous v0.0.3 (VC44) feed package:

- Race Dash: PDM Channels and Keypad tabs (outputs, groups, presets, icons, formulas, live state, retry, current limits, timing, optional wiper park-stop, live formula and named `fn:`/`in:` values). Settings for display brightness, BLE default, orientation, gear and CanBoard. Clearer Connect timeout wording if the dash is still booting.
- BMS setup matching later firmware (battery type, CTC, slave-com, board profile, pack-Wh, reset and DTC clear).
- CAN IDs and addresses are shown and entered as hex (`0x`); digits-only values stay decimal and are displayed as hex.
- MQTT username and password remain set in Settings or on first Connect, stored per user, and are not baked into the package.
