# OPF-FLASHER v0.0.2 (VC42)

Built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `a61c1576602429fbd1e55fe00e583cef53ea4864` on `master-grok` (version 0.0.2+VC42).

- **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package with bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.
- **Windows:** `OPF-FLASHER-win-x64.exe` — portable self-extracting package (Qt 6.8.3, llvm-mingw). Running it unpacks `OPF-FLASHER-qt-win64` next to the exe and launches `OPF-FLASHER.exe`. esptool and OpenOCD are bundled.

macOS is not included.

This package includes the VC42 MQTT Telemetry work and the earlier VC33–VC41 desktop fixes.
