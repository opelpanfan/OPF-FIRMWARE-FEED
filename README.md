# OPF Firmware Feed

Public firmware catalog for OPF-FLASHER and device OTA. Binaries live on the `master-grok` branch.

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/master-grok/index.json`

Read `latest.BMS`, `latest.BRIDGE`, `latest.P1`, `latest.METER`, `latest.CONFIG_APP`, `latest.FLASHER`, and `latest.SCREEN`.

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

`products[].versions[]` lists every immutable version folder. `latest.*` is the channel.

CONFIG_APP, METER, and SCREEN stay empty until sources publish a version folder. Until then `available` is false and `versions` is `[]`.

This repository is a passive catalog. Sources push `P1/`, `BRIDGE/`, `BMS/`, `SCREEN/`, `METER/`, `CONFIG_APP/`, and `FLASHER/` themselves. There is no ingest workflow and no Action that downloads private releases. This repository does not need `SOURCE_READ_TOKEN`.

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

## ESP32 full install

BMS, BRIDGE, METER, and SCREEN may publish three optional install companions next to each board's app image `<BOARD>.bin`. Publish all three for that board, or none. A partial set is refused. Other boards in the same folder may omit the set. Validation passes when the companions are absent. P1, CONFIG_APP, and FLASHER do not use these files.

| File | Flash offset |
| --- | --- |
| `<BOARD>.bin` | `0x10000` |
| `<BOARD>.bootloader.bin` | `0x0` |
| `<BOARD>.partitions.bin` | `0x8000` |
| `<BOARD>.boot_app0.bin` | `0xe000` |
| `<BOARD>.factory.bin` (SCREEN, optional) | `0x0` |

When the set is present, that board's object in `artifacts[]` includes `install` with `bootloader`, `partitions`, and `boot_app0`. Each of those objects has:

- `path` — filename in that same folder
- `sha256` — digest of that file
- `size` — byte length
- `offset` — `0x0` for bootloader, `0x8000` for partitions, `0xe000` for boot_app0

The same three files are lines in the folder `SHA256SUMS` and the root `SHA256SUMS`. `install` is omitted when the board has no companions. The app image stays `<BOARD>.bin` and is flashed at `0x10000`. SCREEN also sets `full_flash_required` and `app_offset` on the product metadata, and may add optional `install.factory` for `<BOARD>.factory.bin` at `0x0`. A factory file does not replace the three companions.

Board filenames are in `.github/feed-catalog.json`.

- `P1/`: `RAK3172_TX.bin` and `RAK3172_RX.bin`, published together.
- `BRIDGE/`: `ATOM_S3_R.bin` and `ATOM_S3.bin` (shared ESP32_S3 MCU image; runtime `hw_board`) plus `ESP32.bin` (LilyGO T-CAN485).
- `BMS/`: catalog boards, including `OPF_WS.bin`.
- `SCREEN/`: OPF CAN dashboard, ESP32-S3. Boards are `ws-4-480` (`OPF_WS_CAN_DASH_4`, Waveshare Touch-LCD-4 480x480), `ws-43-800` (`OPF_WS_CAN_DASH_43`, Touch-LCD-4.3B 800x480), `ws-5-800` (`OPF_WS_CAN_DASH_5`, Touch-LCD-5 800x480), `ws-5b-1024` (`OPF_WS_CAN_DASH_5` with `-D OPF_CAN_DASH_RES=1024`, Touch-LCD-5B 1024x600, experimental), `ws-7-800` (`OPF_WS_CAN_DASH_7`, Touch-LCD-7 800x480, UART/download-mode flash only), and `ws-7b-1024` (`OPF_WS_CAN_DASH_7` with `-D OPF_CAN_DASH_RES=1024`, LCD-7B 1024x600, UART-only). Each board publishes `<id>.bin`, `<id>.bootloader.bin`, `<id>.partitions.bin`, and `<id>.boot_app0.bin`. `<id>.factory.bin` at `0x0` is optional. `full_flash_required` is true: do not OTA an app image across a partition-layout change. Firmware comes from OPF-STORAGE-DASH `master-grok` only, never `main` or `master`. The build id looks like `v0.0.2+N`. The feed folder and the tag stay plain `vX.Y.Z`. No SCREEN binaries are published until that source pushes a folder.
- `METER/`: `transmitter.bin`, `receiver.bin`, `transmitter_lcd.bin`, and `receiver_lcd.bin`, published together under `METER/vX.Y.Z/` and `METER/latest/`. ESP32-S3 images for AtomS3 and AtomS3R from OPF-LORA-METER, built with `partitions/ota_8MB.csv` and qio flash mode. Optional companions use the filenames above.
- `FLASHER/`: `OPF-FLASHER-win-x64.exe` and `OPF-FLASHER-linux-amd64.deb`. Not a board image. Publish an immutable `FLASHER/vX.Y.Z/` and mirror `FLASHER/latest/`. Do not replace an existing version folder, including historical `v0.0.1`.
- `CONFIG_APP/`: `opf-config-app.apk`.

<!-- FEED-SUMMARY:START -->
## Versions

Each product below is one this feed knows. Version folders are listed from oldest to newest, then `latest`.
The date is the feed commit that last changed that folder. A source commit is shown when that folder's `index.json` metadata has `source.sha`.
The summary is the first lines of `FEED_RELEASE_NOTES.md` in that folder, or of `RELEASE_NOTES.md` when that is the notes file present.
ESP32 folders also list full-install files: `yes` when that board has bootloader, partitions, and boot_app0, `no` when it has the app image only.

### BMS

Source repository: `opelpanfan/OPF-STORAGE-DASH`

#### `v0.0.2`

- Date: 2026-11-24
- Source commit: `e4fd3b3104efc6d39a3f68da094aa294cdb77ba7` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1865776 bytes, 1.78 MiB)
  - `OPF_ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_ATOM_S3R.bin` (2065216 bytes, 1.97 MiB)
  - `OPF_ATOM_S3R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_T2CAN.bin` (1927920 bytes, 1.84 MiB)
  - `OPF_T2CAN.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_T2CAN.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_T2CAN.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS.bin` (1910432 bytes, 1.82 MiB)
  - `OPF_WS.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS_DASH.bin` (2599920 bytes, 2.48 MiB)
  - `OPF_WS_DASH.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS_DASH.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS_DASH.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (1256 bytes, 1.2 KiB)
  - `SHA256SUMS` (1776 bytes, 1.7 KiB)
  - `index.json` (8165 bytes, 8.0 KiB)
- Full-install files: `OPF_WS` yes, `OPF_T2CAN` yes, `OPF_ATOM_S3` yes, `OPF_ATOM_S3R` yes, `OPF_WS_DASH` yes
- Summary:
  - Firmware **0.0.2+VC48** (`version_code` 48). Tag `v0.0.2` points at `970de34`, where VERSION is `0.0.2+48`. The FEED binaries were built from `e4fd3b3` (the v0.0.2 feed publish). `+48` maps to `VC48` because VCnn continues the same counter (VC53 came right after 0.0.3+52).
  - Web UI: v0.0.1 layout restored (Dashboard, Battery, Settings, Status). New settings sit as plain fields in their v0.0.1 sections.
  - Soft start: after boot, charge and discharge limits ramp from 5 A to max over 60 s.

#### `v0.0.3`

- Date: 2026-11-24
- Source commit: `bfb4db446eaa1ab00fa78501e058548eb612e942` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1855088 bytes, 1.77 MiB)
  - `OPF_ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_ATOM_S3R.bin` (2055008 bytes, 1.96 MiB)
  - `OPF_ATOM_S3R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_T2CAN.bin` (1913504 bytes, 1.82 MiB)
  - `OPF_T2CAN.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_T2CAN.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_T2CAN.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS.bin` (1900112 bytes, 1.81 MiB)
  - `OPF_WS.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS_DASH.bin` (2589760 bytes, 2.47 MiB)
  - `OPF_WS_DASH.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS_DASH.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS_DASH.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (1950 bytes, 1.9 KiB)
  - `SHA256SUMS` (1776 bytes, 1.7 KiB)
  - `index.json` (8856 bytes, 8.6 KiB)
- Full-install files: `OPF_WS` yes, `OPF_T2CAN` yes, `OPF_ATOM_S3` yes, `OPF_ATOM_S3R` yes, `OPF_WS_DASH` yes
- Summary:
  - Firmware **0.0.3+VC73** (`bfb4db4`, `version_code` 73). Tag `v0.0.3` on `master-grok`, published 24 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC63 (`d046dd1`). Verified on the live .158 pack.
  - VC65: BLE coredump_info and coredump_get
  - VC66: BLE passkey pairing, bonding, and PIN reset

#### `latest`

- Date: 2026-11-24
- Source commit: `bfb4db446eaa1ab00fa78501e058548eb612e942` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1855088 bytes, 1.77 MiB)
  - `OPF_ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_ATOM_S3R.bin` (2055008 bytes, 1.96 MiB)
  - `OPF_ATOM_S3R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_T2CAN.bin` (1913504 bytes, 1.82 MiB)
  - `OPF_T2CAN.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_T2CAN.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_T2CAN.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS.bin` (1900112 bytes, 1.81 MiB)
  - `OPF_WS.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS_DASH.bin` (2589760 bytes, 2.47 MiB)
  - `OPF_WS_DASH.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS_DASH.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS_DASH.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (1950 bytes, 1.9 KiB)
  - `SHA256SUMS` (1776 bytes, 1.7 KiB)
  - `index.json` (8854 bytes, 8.6 KiB)
- Full-install files: `OPF_WS` yes, `OPF_T2CAN` yes, `OPF_ATOM_S3` yes, `OPF_ATOM_S3R` yes, `OPF_WS_DASH` yes
- Summary:
  - Firmware **0.0.3+VC73** (`bfb4db4`, `version_code` 73). Tag `v0.0.3` on `master-grok`, published 24 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC63 (`d046dd1`). Verified on the live .158 pack.
  - VC65: BLE coredump_info and coredump_get
  - VC66: BLE passkey pairing, bonding, and PIN reset

### BRIDGE

Source repository: `opelpanfan/OPF-STORAGE-M5-BRIDGE`

#### `v0.0.2`

- Date: 2026-11-20
- Source commit: `a1cc2bb58d02bcd9a44bedc896484b6c4d62971f` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (2028112 bytes, 1.93 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (2028112 bytes, 1.93 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ESP32.bin` (1598624 bytes, 1.52 MiB)
  - `ESP32.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ESP32.bootloader.bin` (18992 bytes, 18.5 KiB)
  - `ESP32.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (17139 bytes, 16.7 KiB)
  - `SHA256SUMS` (1032 bytes, 1.0 KiB)
  - `index.json` (21588 bytes, 21.1 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes, `ESP32` yes
- Summary:
  - Tag `v0.0.2` → `a1cc2bb` (firmware `0.0.2+VC34`, proven on Atom S3R .110). Feed: OPF-FIRMWARE-FEED `master-grok` (BRIDGE/v0.0.2 + latest; commit sha filled after publish).
  - GitHub Actions artifact storage is still full at the account level, so FEED was published locally with `scripts/publish_firmware_feed.py` using Arduino-ESP32 3.20016, without `platformio.local.ini` secrets.
  - Release type: Stability, diagnostics, and versioning

#### `v0.0.3`

- Date: 2026-11-24
- Source commit: `12551a4c91910bb5a221f6bf2473e64677831e3b` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1925568 bytes, 1.84 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (1925568 bytes, 1.84 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ESP32.bin` (1390144 bytes, 1.33 MiB)
  - `ESP32.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ESP32.bootloader.bin` (18992 bytes, 18.5 KiB)
  - `ESP32.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (4727 bytes, 4.6 KiB)
  - `SHA256SUMS` (1032 bytes, 1.0 KiB)
  - `index.json` (8971 bytes, 8.8 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes, `ESP32` yes
- Summary:
  - Firmware **0.0.3+VC47** (`12551a4`, `version_code` 47). Tag `v0.0.3` on `master-grok`, retagged 24 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC43 (`ad9dc39`).
  - v0.0.3 moves all device settings to BLE (`cfg_schema` / `cfg_get` / `cfg_set`), leaves the web UI as a dashboard plus a read-only Status page, removes inverter auto-detect, hardens the firmware for 24/7 operation, adds BLE PIN pairing and a crash summary, and lists Sungrow…
  - **VC35:** web settings editors removed. Inverter and LoRa tabs are gone and Status-page actions (RS-485 tests, restarts, factory reset, SoftAP open/close, telemetry resume, smartmeter capture) move to BLE (`reboot`, `mqtt_restart`, `factory_reset`, `ap_open` / `ap_close`,…

#### `latest`

- Date: 2026-11-24
- Source commit: `12551a4c91910bb5a221f6bf2473e64677831e3b` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1925568 bytes, 1.84 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (1925568 bytes, 1.84 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ESP32.bin` (1390144 bytes, 1.33 MiB)
  - `ESP32.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ESP32.bootloader.bin` (18992 bytes, 18.5 KiB)
  - `ESP32.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (4727 bytes, 4.6 KiB)
  - `SHA256SUMS` (1032 bytes, 1.0 KiB)
  - `index.json` (8970 bytes, 8.8 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes, `ESP32` yes
- Summary:
  - Firmware **0.0.3+VC47** (`12551a4`, `version_code` 47). Tag `v0.0.3` on `master-grok`, retagged 24 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC43 (`ad9dc39`).
  - v0.0.3 moves all device settings to BLE (`cfg_schema` / `cfg_get` / `cfg_set`), leaves the web UI as a dashboard plus a read-only Status page, removes inverter auto-detect, hardens the firmware for 24/7 operation, adds BLE PIN pairing and a crash summary, and lists Sungrow…
  - **VC35:** web settings editors removed. Inverter and LoRa tabs are gone and Status-page actions (RS-485 tests, restarts, factory reset, SoftAP open/close, telemetry resume, smartmeter capture) move to BLE (`reboot`, `mqtt_restart`, `factory_reset`, `ap_open` / `ap_close`,…

### P1

Source repository: `opelpanfan/OPF-P1`

#### `v0.0.1`

- Date: 2026-11-24
- Source commit: `f8e1f424e00651a51f0815848465564cd467502d` (opelpanfan/OPF-P1)
- Files:
  - `RAK3172_RX.bin` (69836 bytes, 68.2 KiB)
  - `RAK3172_TX.bin` (92508 bytes, 90.3 KiB)
  - `RELEASE_NOTES.md` (1194 bytes, 1.2 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (2960 bytes, 2.9 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** This is fw10: firmware **0.0.1+VC10** (`f8e1f42`, `version_code` 10). Tag `v0.0.1` on `master-grok`. Flash both images from this release together. A Bridge DTU still tuned to 868.000 MHz will not hear these frames.
  - Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm.
  - Rolling 1-hour transmit cap stays under 10% duty, including command ACKs.

#### `v0.0.2`

- Date: 2026-11-24
- Source commit: `1196aeefe2a98952b070a90ab3c41ca8371eb9ea` (opelpanfan/OPF-P1)
- Files:
  - `RAK3172_RX.bin` (70356 bytes, 68.7 KiB)
  - `RAK3172_TX.bin` (94620 bytes, 92.4 KiB)
  - `RELEASE_NOTES.md` (3143 bytes, 3.1 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (4918 bytes, 4.8 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** This is fw16: firmware **0.0.2+VC16** (`1196aee`, `version_code` 16; the device's own version text reads `0.0.2+16`). Tag `v0.0.2` on `master-grok`. Flash both images from this release together. The radio settings and uplink format are…
  - Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm. Rolling 1-hour transmit cap stays under 10% duty.
  - `P1_REQUIRE_CRC=0`. A telegram with a missing or wrong CRC is accepted only if it carries U1-3, I1-3 and import power and passes the plausibility guard. A CRC-matching telegram is accepted without that guard.

#### `latest`

- Date: 2026-11-24
- Source commit: `1196aeefe2a98952b070a90ab3c41ca8371eb9ea` (opelpanfan/OPF-P1)
- Files:
  - `RAK3172_RX.bin` (70356 bytes, 68.7 KiB)
  - `RAK3172_TX.bin` (94620 bytes, 92.4 KiB)
  - `RELEASE_NOTES.md` (3143 bytes, 3.1 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (4917 bytes, 4.8 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** This is fw16: firmware **0.0.2+VC16** (`1196aee`, `version_code` 16; the device's own version text reads `0.0.2+16`). Tag `v0.0.2` on `master-grok`. Flash both images from this release together. The radio settings and uplink format are…
  - Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm. Rolling 1-hour transmit cap stays under 10% duty.
  - `P1_REQUIRE_CRC=0`. A telegram with a missing or wrong CRC is accepted only if it carries U1-3, I1-3 and import power and passes the plausibility guard. A CRC-matching telegram is accepted without that guard.

### CONFIG_APP

Source repository: `opelpanfan/OPF-CONFIG-APP`

No version folders.

### METER

Source repository: `opelpanfan/OPF-LORA-METER`

No version folders.

### FLASHER

Source repository: `opelpanfan/OPF-FLASHER`

No version folders.

### SCREEN

Source repository: `opelpanfan/OPF-STORAGE-DASH`

Full flash is required. OTA of the app image alone is unsafe across partition layouts.

No version folders.
<!-- FEED-SUMMARY:END -->
