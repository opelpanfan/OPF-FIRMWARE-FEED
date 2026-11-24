# OPF-FLASHER v0.0.3 (package 0.0.2+VC44)

Built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `f361e2220a27795cc91073dd92f63e2e5b3c5290` on `master-grok` (app version 0.0.2+VC44).

This feed folder is `FLASHER/v0.0.3` because `FLASHER/v0.0.2` is the immutable VC42 package and must not be replaced. The app semver is still 0.0.2.

- **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package with bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.
- **Windows:** `OPF-FLASHER-win-x64.exe` — portable 7-Zip LZMA2 self-extractor (Qt 6.8.3, official MSVC kit). Run it, extract the `OPF-FLASHER-qt-win64` folder, and start `OPF-FLASHER.exe` from that folder. Leave the Qt DLLs, the MSVC runtime, plugin folders, and `tools/` next to the exe. esptool 5.5.0 and xPack OpenOCD 0.12.0-7 are bundled as Windows binaries.

What changed since the v0.0.2 (VC42) feed package:

- The main window is freely resizable (minimum 320×200) and the layout reflows at narrow widths (header, tabs, and page content).
- Windows Bluetooth uses the WinRT backend. The earlier MinGW package shipped a dummy backend, so no adapter was found.
- MQTT username (default `opf_api`) and password are set in Settings or on first Connect, stored per user. They are not baked into the installer.
- The Windows package is a 7-Zip LZMA2 SFX so every feed file stays under GitHub's 100 MB limit.

macOS is not included.
