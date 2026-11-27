# OPF-FLASHER latest (Linux 0.0.2+VC95, Windows 0.0.2+VC99)

`FLASHER/latest` is a mixed package. The Linux deb is still the tagged v0.0.3 build. The Windows portable exe is a newer desktop build. The immutable folder `FLASHER/v0.0.3` and the git tag `v0.0.3` on `opelpanfan/OPF-FLASHER` are unchanged (both platforms there remain 0.0.2+VC95 from `6a925e2494777bb4e1a40eb6c3d8f2790873a812`).

- **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package 0.0.2+VC95, built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `6a925e2494777bb4e1a40eb6c3d8f2790873a812` on `master-grok` (git tag `v0.0.3`). Bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.
- **Windows:** `OPF-FLASHER-win-x64.exe` — portable 7-Zip LZMA2 self-extractor, app version 0.0.2+VC99 from `opelpanfan/OPF-FLASHER` commit `bec870d0b50825e84fedccee87bab19821dadc98` on `master-grok`. Cross-built on the OptiPlex (Qt 6.8.3, official MSVC kit, clang-cl). This Windows build has not been tested on a real Windows machine. Run the exe, extract the `OPF-FLASHER-qt-win64` folder, and start `OPF-FLASHER.exe` from that folder. Leave the Qt DLLs, the MSVC runtime, plugin folders (`tls/` included), and `tools/` next to the exe. esptool 5.5.0 and xPack OpenOCD 0.12.0-7 are bundled as Windows binaries. The package includes `tls/qschannelbackend.dll` and `tls/qcertonlybackend.dll`, which are required for HTTPS (the firmware feed index and downloads). MQTT in this app does not use TLS.

macOS is not included.

What changed in the Windows package since the v0.0.3 (VC95) feed build:

- TLS plugin folder is packaged and checked, and the app logs whether HTTPS will work at startup. A crash on Windows writes a minidump next to the session log.
- esptool 5 no longer starts a second verify run on the same COM port after a hard reset (ESP32-S3 native USB can get a new COM number). Serial errors use Windows wording (no "dialout") and mention CH340, CP210x, and ESP32-S3 drivers.
- CAN help names the vendor driver each backend needs on Windows, uses the Qt PEAK names (`usb1`, not `PCAN_USBBUS1`), and says listen-only still ACKs on vendor adapters. gs_usb / candleLight users are pointed at slcan firmware or a PCAN adapter.
- Race Dash pairing waits for the Windows PIN dialog (default 123456). The "already connected on this computer" check is skipped on Windows. BLE OTA logs the MTU and uses acknowledged writes when Windows reports 23 or does not report one.

Linux is unchanged from the v0.0.3 (VC95) package.
