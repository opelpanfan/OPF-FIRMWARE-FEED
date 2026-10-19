# OPF Firmware Feed

Public firmware catalog for OPF-FLASHER and device OTA. Binaries live on the `main` branch.

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/index.json`

Read `latest.BMS`, `latest.BRIDGE`, `latest.P1`, `latest.CONFIG_APP`, and `latest.FLASHER`. `latest.METER` is the same release as `latest.P1` (transmitter and receiver are stored under `P1/`).

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1/METER, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

`products[].versions[]` lists every immutable version folder. `latest.*` is the channel.

P1, BMS, BRIDGE, CONFIG_APP, FLASHER, and the METER alias are empty until sources publish a version folder. Each product folder holds only a README. `available` is false and `versions` is `[]`. There is no root `SHA256SUMS` until a binary is published.

This repository is a passive catalog. Sources push `P1/`, `BRIDGE/`, `BMS/`, `CONFIG_APP/`, and `FLASHER/` themselves. There is no ingest workflow and no Action that downloads private releases. This repository does not need `SOURCE_READ_TOKEN`.

`FLASHER/` holds the OPF-FLASHER desktop packages (a Windows portable exe and a Linux deb), not device firmware. Do not flash those files onto a board. OPF-FLASHER ignores the `FLASHER` product when it lists Bridge, P1, and BMS.

## Release notes

A version folder may include optional UTF-8 markdown at `RELEASE_NOTES.md`. The same file is copied to `latest/` when a publish or rollback updates that channel. Notes are not required, and they are not listed in `SHA256SUMS`.

When the file is present, that folder's `index.json`, `latest.<PRODUCT>`, and `products[].versions[]` include:

- `release_notes` — the markdown text Flasher should show
- `release_notes_url` — raw URL of `RELEASE_NOTES.md` in that folder

Both fields are omitted when the file is absent.

`.bin` bytes in a version folder stay immutable. Notes are stored by the publish that creates the folder. If that publish did not include notes, add them once with `attach-notes`. That command only writes `RELEASE_NOTES.md`. When `latest/` is a byte copy of the folder, it mirrors the file there. Notes cannot be edited after they are published.

```bash
python3 .github/scripts/publish_firmware.py apply \
  --product BMS --version X.Y.Z --from-dir ./out --set-latest \
  --release-notes-file ./RELEASE_NOTES.md

python3 .github/scripts/publish_firmware.py attach-notes \
  --product BMS --folder vX.Y.Z \
  --release-notes-file ./RELEASE_NOTES.md
```

Source repos pass `--release-notes` or `--release-notes-file` on `apply`. This feed does not download notes or firmware.

Board filenames are in `.github/feed-catalog.json`.

- `P1/`: `RAK3172_TX.bin` and `RAK3172_RX.bin`, published together.
- `BRIDGE/`: `ATOM_S3_R.bin` and `ATOM_S3.bin`.
- `BMS/`: catalog boards, including `OPF_WS.bin`.
- `METER/`: alias of P1. No binaries.
- `FLASHER/`: `OPF-FLASHER-win-x64.exe` and `OPF-FLASHER-linux-amd64.deb`. Not a board image. Until the first real app release the version folder stays `v0.0.1` and may be replaced in place.
- `CONFIG_APP/`: `opf-config-app.apk`.

<!-- FEED-SUMMARY:START -->
## Versions

Each product below is one this feed knows. Version folders are listed from oldest to newest, then `latest`.
The date is the feed commit that last changed that folder. A source commit is shown when that folder's `index.json` metadata has `source.sha`.
The summary is the first lines of `FEED_RELEASE_NOTES.md` in that folder, or of `RELEASE_NOTES.md` when that is the notes file present.

### BMS

Source repository: `opelpanfan/OPF-STORAGE-DASH`

#### `v0.0.1`

- Date: 2026-10-19
- Source commit: `a58c429487409ab9e243a869ede6f220264932b3` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1598928 bytes, 1.52 MiB)
  - `OPF_ATOM_S3R.bin` (1799056 bytes, 1.72 MiB)
  - `OPF_T2CAN.bin` (1635776 bytes, 1.56 MiB)
  - `OPF_WS.bin` (1632256 bytes, 1.56 MiB)
  - `OPF_WS_DASH.bin` (2341088 bytes, 2.23 MiB)
  - `OPF_WS_NO_TEMP.bin` (1632096 bytes, 1.56 MiB)
  - `RELEASE_NOTES.md` (981 bytes)
  - `SHA256SUMS` (489 bytes)
  - `index.json` (4864 bytes, 4.8 KiB)
- Summary:
  - Web UI: v0.0.1 layout restored (Dashboard, Battery, Settings, Status). New settings sit as plain fields in their v0.0.1 sections.
  - Soft start: after boot, charge and discharge limits ramp from 5 A to max over 60 s.
  - SoC taper: charge and discharge limits ramp from 5 A at the low and high SoC ends and near cell voltage limits.

#### `v0.0.2`

- Date: 2026-10-19
- Source commit: `e945fd827f88fd324f0f8fcccbf5cdb1b4d84277` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1581904 bytes, 1.51 MiB)
  - `OPF_ATOM_S3R.bin` (1781280 bytes, 1.70 MiB)
  - `OPF_T2CAN.bin` (1618768 bytes, 1.54 MiB)
  - `OPF_WS.bin` (1614496 bytes, 1.54 MiB)
  - `OPF_WS_DASH.bin` (2323168 bytes, 2.22 MiB)
  - `OPF_WS_NO_TEMP.bin` (1614368 bytes, 1.54 MiB)
  - `RELEASE_NOTES.md` (446 bytes)
  - `SHA256SUMS` (489 bytes)
  - `index.json` (4328 bytes, 4.2 KiB)
- Summary:
  - Stability: OTA task-watchdog fix; pack control, UV failsafe, and CAN keep running during OTA; prefs mutex; fixed OTA URL and IP buffers; deferred `WiFi.mode`; PSA2 mux caps.
  - Coredump capture, plus `/coredump` download and erase.
  - Dash Type: dash-only type 100 on display builds.

#### `latest`

- Date: 2026-10-19
- Source commit: `a58c429487409ab9e243a869ede6f220264932b3` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1598928 bytes, 1.52 MiB)
  - `OPF_ATOM_S3R.bin` (1799056 bytes, 1.72 MiB)
  - `OPF_T2CAN.bin` (1635776 bytes, 1.56 MiB)
  - `OPF_WS.bin` (1632256 bytes, 1.56 MiB)
  - `OPF_WS_DASH.bin` (2341088 bytes, 2.23 MiB)
  - `OPF_WS_NO_TEMP.bin` (1632096 bytes, 1.56 MiB)
  - `RELEASE_NOTES.md` (981 bytes)
  - `SHA256SUMS` (489 bytes)
  - `index.json` (4862 bytes, 4.7 KiB)
- Summary:
  - Web UI: v0.0.1 layout restored (Dashboard, Battery, Settings, Status). New settings sit as plain fields in their v0.0.1 sections.
  - Soft start: after boot, charge and discharge limits ramp from 5 A to max over 60 s.
  - SoC taper: charge and discharge limits ramp from 5 A at the low and high SoC ends and near cell voltage limits.

### BRIDGE

Source repository: `opelpanfan/OPF-STORAGE-M5-BRIDGE`

#### `v0.0.1`

- Date: 2026-10-19
- Source commit: `837cad0b06cc06a6a5ba2748553b302dffe4a7f4` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1914080 bytes, 1.83 MiB)
  - `ATOM_S3_R.bin` (1959824 bytes, 1.87 MiB)
  - `RELEASE_NOTES.md` (9145 bytes, 8.9 KiB)
  - `SHA256SUMS` (158 bytes)
  - `index.json` (10830 bytes, 10.6 KiB)
- Summary:
  - Console and AtomS3R LCD layout restored to the v0.0.1 look (v0.0.2 shared-UX layout removed). Non-UI firmware fixes kept.
  - Feed publish target is again `BRIDGE/v0.0.1` (`FEED_FIXED_VERSION`); `BRIDGE/v0.0.2` is removed from the feed. `latest` follows v0.0.1.
  - RS485 read and write waits yield instead of spinning. A dead bus was a priority-2 busy loop and could starve the watchdog tasks (`atom_loop`, LCD).

#### `latest`

- Date: 2026-10-19
- Source commit: `837cad0b06cc06a6a5ba2748553b302dffe4a7f4` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1914080 bytes, 1.83 MiB)
  - `ATOM_S3_R.bin` (1959824 bytes, 1.87 MiB)
  - `RELEASE_NOTES.md` (9145 bytes, 8.9 KiB)
  - `SHA256SUMS` (158 bytes)
  - `index.json` (10829 bytes, 10.6 KiB)
- Summary:
  - Console and AtomS3R LCD layout restored to the v0.0.1 look (v0.0.2 shared-UX layout removed). Non-UI firmware fixes kept.
  - Feed publish target is again `BRIDGE/v0.0.1` (`FEED_FIXED_VERSION`); `BRIDGE/v0.0.2` is removed from the feed. `latest` follows v0.0.1.
  - RS485 read and write waits yield instead of spinning. A dead bus was a priority-2 busy loop and could starve the watchdog tasks (`atom_loop`, LCD).

### P1

Source repository: `opelpanfan/OPF-P1`

#### `v0.0.1`

- Date: 2026-10-19
- Files:
  - `RAK3172_RX.bin` (69836 bytes, 68.2 KiB)
  - `RAK3172_TX.bin` (92508 bytes, 90.3 KiB)
  - `RELEASE_NOTES.md` (1093 bytes, 1.1 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (2641 bytes, 2.6 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** Flash both images from this release together. A Bridge DTU still tuned to 868.000 MHz will not hear these frames.
  - Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm.
  - Rolling 1-hour transmit cap stays under 10% duty, including command ACKs.

#### `v0.0.2`

- Date: 2026-10-19
- Files:
  - `RAK3172_RX.bin` (69836 bytes, 68.2 KiB)
  - `RAK3172_TX.bin` (92508 bytes, 90.3 KiB)
  - `RELEASE_NOTES.md` (1093 bytes, 1.1 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (2641 bytes, 2.6 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** Flash both images from this release together. A Bridge DTU still tuned to 868.000 MHz will not hear these frames.
  - Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm.
  - Rolling 1-hour transmit cap stays under 10% duty, including command ACKs.

#### `latest`

- Date: 2026-10-19
- Files:
  - `RAK3172_RX.bin` (69836 bytes, 68.2 KiB)
  - `RAK3172_TX.bin` (92508 bytes, 90.3 KiB)
  - `RELEASE_NOTES.md` (1093 bytes, 1.1 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (2640 bytes, 2.6 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** Flash both images from this release together. A Bridge DTU still tuned to 868.000 MHz will not hear these frames.
  - Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm.
  - Rolling 1-hour transmit cap stays under 10% duty, including command ACKs.

### CONFIG_APP

Source repository: `opelpanfan/OPF-CONFIG-APP`

No version folders.

### METER

No version folders.

### FLASHER

Source repository: `opelpanfan/OPF-FLASHER`

No version folders.
<!-- FEED-SUMMARY:END -->
