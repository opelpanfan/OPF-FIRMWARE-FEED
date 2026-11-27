# OPF Firmware Feed

Public firmware catalog for OPF-FLASHER and device OTA. Binaries live on the `master-grok` branch.

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/master-grok/index.json`

Read `latest.BMS`, `latest.BRIDGE`, `latest.P1`, `latest.METER`, `latest.CONFIG_APP`, `latest.FLASHER`, `latest.SCREEN`, and `latest.RACE`.

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

`products[].versions[]` lists every immutable version folder. `latest.*` is the channel.

CONFIG_APP, METER, and SCREEN stay empty until sources publish a version folder. Until then `available` is false and `versions` is `[]`.

This repository is a passive catalog. Sources push `P1/`, `BRIDGE/`, `BMS/`, `SCREEN/`, `METER/`, `CONFIG_APP/`, `FLASHER/`, and `RACE/` themselves. There is no ingest workflow and no Action that downloads private releases. This repository does not need `SOURCE_READ_TOKEN`.

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

BMS, BRIDGE, METER, and SCREEN may publish three optional install companions next to each board's app image `<BOARD>.bin`. Publish all three for that board, or none. A partial set is refused. Other boards in the same folder may omit the set. Validation passes when the companions are absent. P1, CONFIG_APP, and FLASHER do not use these files. RACE also omits the trio: the ESP32-P4 bootloader is at `0x2000`, not the catalog default `0x0`.

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
- `RACE/`: `esp32-p4.bin` (Waveshare ESP32-P4-WIFI6-Touch-LCD-7B, PlatformIO env `opf_dash`). App-only flash at `0x10000` is recommended. The standard bootloader trio is not published here because the P4 bootloader is at `0x2000`, not `0x0`. Firmware comes from OPF-RACE-DASH `master-grok`. The image reports `fw_version` such as `0.1.16`; feed metadata is `0.1.16+VC17`.
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

- Date: 2026-11-26
- Source commit: `6144b8d6542f022f221c0559a6e80403d2f15b9c` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1860560 bytes, 1.77 MiB)
  - `OPF_ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_ATOM_S3R.bin` (2060752 bytes, 1.97 MiB)
  - `OPF_ATOM_S3R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_T2CAN.bin` (1918672 bytes, 1.83 MiB)
  - `OPF_T2CAN.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_T2CAN.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_T2CAN.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS.bin` (1905936 bytes, 1.82 MiB)
  - `OPF_WS.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS_DASH.bin` (2597408 bytes, 2.48 MiB)
  - `OPF_WS_DASH.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS_DASH.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS_DASH.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (2991 bytes, 2.9 KiB)
  - `SHA256SUMS` (1776 bytes, 1.7 KiB)
  - `index.json` (9947 bytes, 9.7 KiB)
- Full-install files: `OPF_WS` yes, `OPF_T2CAN` yes, `OPF_ATOM_S3` yes, `OPF_ATOM_S3R` yes, `OPF_WS_DASH` yes
- Summary:
  - Firmware **0.0.3+VC90** (`6144b8d`, `version_code` 90). Tag `v0.0.3` on `master-grok`, published 26 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC73 (`bfb4db4`). Verified on the live .158 pack.
  - VC74: PSA battery type rework + contactor/wake settings
  - VC75: contactor control for PSA V1/V2, wake flag on all types

#### `latest`

- Date: 2026-11-26
- Source commit: `6144b8d6542f022f221c0559a6e80403d2f15b9c` (opelpanfan/OPF-STORAGE-DASH)
- Files:
  - `OPF_ATOM_S3.bin` (1860560 bytes, 1.77 MiB)
  - `OPF_ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_ATOM_S3R.bin` (2060752 bytes, 1.97 MiB)
  - `OPF_ATOM_S3R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_ATOM_S3R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_ATOM_S3R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_T2CAN.bin` (1918672 bytes, 1.83 MiB)
  - `OPF_T2CAN.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_T2CAN.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_T2CAN.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS.bin` (1905936 bytes, 1.82 MiB)
  - `OPF_WS.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS.partitions.bin` (3072 bytes, 3.0 KiB)
  - `OPF_WS_DASH.bin` (2597408 bytes, 2.48 MiB)
  - `OPF_WS_DASH.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `OPF_WS_DASH.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `OPF_WS_DASH.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (2991 bytes, 2.9 KiB)
  - `SHA256SUMS` (1776 bytes, 1.7 KiB)
  - `index.json` (9945 bytes, 9.7 KiB)
- Full-install files: `OPF_WS` yes, `OPF_T2CAN` yes, `OPF_ATOM_S3` yes, `OPF_ATOM_S3R` yes, `OPF_WS_DASH` yes
- Summary:
  - Firmware **0.0.3+VC90** (`6144b8d`, `version_code` 90). Tag `v0.0.3` on `master-grok`, published 26 Nov 2026 (Europe/Vilnius); the earlier v0.0.3 was 0.0.3+VC73 (`bfb4db4`). Verified on the live .158 pack.
  - VC74: PSA battery type rework + contactor/wake settings
  - VC75: contactor control for PSA V1/V2, wake flag on all types

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

- Date: 2026-11-27
- Source commit: `2cbc83552b50fbfb2e024ce80c820ace77ee4acc` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1930192 bytes, 1.84 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (1930192 bytes, 1.84 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ESP32.bin` (1394672 bytes, 1.33 MiB)
  - `ESP32.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ESP32.bootloader.bin` (18992 bytes, 18.5 KiB)
  - `ESP32.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (6491 bytes, 6.3 KiB)
  - `SHA256SUMS` (1032 bytes, 1.0 KiB)
  - `index.json` (10741 bytes, 10.5 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes, `ESP32` yes
- Summary:
  - Firmware **0.0.3+VC52** (`2cbc835`, `version_code` 52). Tag `v0.0.3` on `master-grok`, retagged 27 Nov 2026 (Europe/Vilnius); earlier v0.0.3 tags were 0.0.3+VC51 (`4ddda59`), 0.0.3+VC48 (`8af90a2`), 0.0.3+VC47 (`12551a4`) and 0.0.3+VC43 (`ad9dc39`).
  - v0.0.3 moves all device settings to BLE (`cfg_schema` / `cfg_get` / `cfg_set`), leaves the web UI as a dashboard plus a read-only Status page, removes inverter auto-detect, hardens the firmware for 24/7 operation, adds BLE PIN pairing and a crash summary, and lists Sungrow…
  - **VC35:** web settings editors removed. Inverter and LoRa tabs are gone and Status-page actions (RS-485 tests, restarts, factory reset, SoftAP open/close, telemetry resume, smartmeter capture) move to BLE (`reboot`, `mqtt_restart`, `factory_reset`, `ap_open` / `ap_close`,…

#### `latest`

- Date: 2026-11-27
- Source commit: `2cbc83552b50fbfb2e024ce80c820ace77ee4acc` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1930192 bytes, 1.84 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (1930192 bytes, 1.84 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ESP32.bin` (1394672 bytes, 1.33 MiB)
  - `ESP32.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ESP32.bootloader.bin` (18992 bytes, 18.5 KiB)
  - `ESP32.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (6491 bytes, 6.3 KiB)
  - `SHA256SUMS` (1032 bytes, 1.0 KiB)
  - `index.json` (10740 bytes, 10.5 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes, `ESP32` yes
- Summary:
  - Firmware **0.0.3+VC52** (`2cbc835`, `version_code` 52). Tag `v0.0.3` on `master-grok`, retagged 27 Nov 2026 (Europe/Vilnius); earlier v0.0.3 tags were 0.0.3+VC51 (`4ddda59`), 0.0.3+VC48 (`8af90a2`), 0.0.3+VC47 (`12551a4`) and 0.0.3+VC43 (`ad9dc39`).
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

#### `v0.0.3`

- Date: 2026-11-27
- Source commit: `c94a98f79e2473185ffc1ca3ef9becf2540e34dc` (opelpanfan/OPF-P1)
- Files:
  - `RAK3172_RX.bin` (70372 bytes, 68.7 KiB)
  - `RAK3172_TX.bin` (95148 bytes, 92.9 KiB)
  - `RELEASE_NOTES.md` (1302 bytes, 1.3 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (3069 bytes, 3.0 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** This is fw17: firmware **0.0.3+VC17** (`c94a98f`, `version_code` 17; the device's own version text reads `0.0.3+17`). Tag `v0.0.3` on `master-grok`, built from `c94a98f79e2473185ffc1ca3ef9becf2540e34dc`. Flash both images from this…
  - The P1 meter stays valid for 15 s (`P1_INVALID_AFTER_MS`), so a meter that sends every 10 s no longer flags every uplink as invalid. In v0.0.2 `dataInvalid` fired after 2 s.
  - The transmitter clears USART1 overrun, framing, noise and parity errors (ORE/FE/NE/PE) on the live path. A stuck overrun used to stop reception.

#### `latest`

- Date: 2026-11-27
- Source commit: `c94a98f79e2473185ffc1ca3ef9becf2540e34dc` (opelpanfan/OPF-P1)
- Files:
  - `RAK3172_RX.bin` (70372 bytes, 68.7 KiB)
  - `RAK3172_TX.bin` (95148 bytes, 92.9 KiB)
  - `RELEASE_NOTES.md` (1302 bytes, 1.3 KiB)
  - `SHA256SUMS` (162 bytes)
  - `index.json` (3068 bytes, 3.0 KiB)
- Summary:
  - **Frequency is 869.525 MHz (EU868 g3).** This is fw17: firmware **0.0.3+VC17** (`c94a98f`, `version_code` 17; the device's own version text reads `0.0.3+17`). Tag `v0.0.3` on `master-grok`, built from `c94a98f79e2473185ffc1ca3ef9becf2540e34dc`. Flash both images from this…
  - The P1 meter stays valid for 15 s (`P1_INVALID_AFTER_MS`), so a meter that sends every 10 s no longer flags every uplink as invalid. In v0.0.2 `dataInvalid` fired after 2 s.
  - The transmitter clears USART1 overrun, framing, noise and parity errors (ORE/FE/NE/PE) on the live path. A stuck overrun used to stop reception.

### CONFIG_APP

Source repository: `opelpanfan/OPF-CONFIG-APP`

#### `v0.0.3`

- Date: 2026-11-27
- Source commit: `16bef971e14167808eed32daebdb4a349e005e29` (opelpanfan/OPF-CONFIG-APP)
- Files:
  - `RELEASE_NOTES.md` (14671 bytes, 14.3 KiB)
  - `SHA256SUMS` (85 bytes)
  - `index.json` (16006 bytes, 15.6 KiB)
  - `opf-config-app.apk` (22750404 bytes, 21.70 MiB)
- Summary:
  - 0.0.3+109: Race Dash / PDM work since 0.0.1+104, including live input and formula values, pdm_caps field hiding, park-stop (wiperpark), bitrate labels that never show a raw number, and mid-transfer cancel for fs_put uploads (disconnect, no auto-reconnect). Android versionName…
  - 0.0.1+104: Cell count is the pack series total from `cell_count` / `b_cell_count`, shown as sent. `b_cells_editable` = 1 (or PSA Custom when that flag is absent on enum v4) is the only editable case, and Save writes `b_cell_count` as the total (1–108). Module counts are…
  - 0.0.1+103: BMS VC77 cells. Module count is gone from settings, and the live cell view is one flat bar chart (min blue, max amber, the rest green) with a table toggle. On `b_type_enum_v` >= 4, cell count is editable only for PSA Custom (or when cfg_get says so); PSA V1 shows…

#### `latest`

- Date: 2026-11-27
- Source commit: `16bef971e14167808eed32daebdb4a349e005e29` (opelpanfan/OPF-CONFIG-APP)
- Files:
  - `RELEASE_NOTES.md` (14671 bytes, 14.3 KiB)
  - `SHA256SUMS` (85 bytes)
  - `index.json` (16005 bytes, 15.6 KiB)
  - `opf-config-app.apk` (22750404 bytes, 21.70 MiB)
- Summary:
  - 0.0.3+109: Race Dash / PDM work since 0.0.1+104, including live input and formula values, pdm_caps field hiding, park-stop (wiperpark), bitrate labels that never show a raw number, and mid-transfer cancel for fs_put uploads (disconnect, no auto-reconnect). Android versionName…
  - 0.0.1+104: Cell count is the pack series total from `cell_count` / `b_cell_count`, shown as sent. `b_cells_editable` = 1 (or PSA Custom when that flag is absent on enum v4) is the only editable case, and Save writes `b_cell_count` as the total (1–108). Module counts are…
  - 0.0.1+103: BMS VC77 cells. Module count is gone from settings, and the live cell view is one flat bar chart (min blue, max amber, the rest green) with a table toggle. On `b_type_enum_v` >= 4, cell count is editable only for PSA Custom (or when cfg_get says so); PSA V1 shows…

### METER

Source repository: `opelpanfan/OPF-LORA-METER`

No version folders.

### FLASHER

Source repository: `opelpanfan/OPF-FLASHER`

#### `v0.0.2`

- Date: 2026-11-24
- Source commit: `a61c1576602429fbd1e55fe00e583cef53ea4864` (opelpanfan/OPF-FLASHER)
- Files:
  - `OPF-FLASHER-linux-amd64.deb` (53819944 bytes, 51.33 MiB)
  - `OPF-FLASHER-win-x64.exe` (87030472 bytes, 83.00 MiB)
  - `RELEASE_NOTES.md` (761 bytes)
  - `SHA256SUMS` (184 bytes)
  - `index.json` (2575 bytes, 2.5 KiB)
- Summary:
  - Built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `a61c1576602429fbd1e55fe00e583cef53ea4864` on `master-grok` (version 0.0.2+VC42).
  - **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package with bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.
  - **Windows:** `OPF-FLASHER-win-x64.exe` — portable self-extracting package (Qt 6.8.3, llvm-mingw). Running it unpacks `OPF-FLASHER-qt-win64` next to the exe and launches `OPF-FLASHER.exe`. esptool and OpenOCD are bundled.

#### `v0.0.3`

- Date: 2026-11-27
- Source commit: `6a925e2494777bb4e1a40eb6c3d8f2790873a812` (opelpanfan/OPF-FLASHER)
- Files:
  - `OPF-FLASHER-linux-amd64.deb` (54369188 bytes, 51.85 MiB)
  - `OPF-FLASHER-win-x64.exe` (33175462 bytes, 31.64 MiB)
  - `RELEASE_NOTES.md` (2051 bytes, 2.0 KiB)
  - `SHA256SUMS` (184 bytes)
  - `index.json` (3869 bytes, 3.8 KiB)
- Summary:
  - Built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `6a925e2494777bb4e1a40eb6c3d8f2790873a812` on `master-grok` (app version 0.0.2+VC95, git tag `v0.0.3`).
  - This feed folder is `FLASHER/v0.0.3` because `FLASHER/v0.0.2` is the immutable VC42 package and must not be replaced. The app semver is still 0.0.2.
  - **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package with bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.

#### `latest`

- Date: 2026-11-27
- Source commit: `6a925e2494777bb4e1a40eb6c3d8f2790873a812` (opelpanfan/OPF-FLASHER)
- Files:
  - `OPF-FLASHER-linux-amd64.deb` (54369188 bytes, 51.85 MiB)
  - `OPF-FLASHER-win-x64.exe` (33175462 bytes, 31.64 MiB)
  - `RELEASE_NOTES.md` (2051 bytes, 2.0 KiB)
  - `SHA256SUMS` (184 bytes)
  - `index.json` (3868 bytes, 3.8 KiB)
- Summary:
  - Built on the OptiPlex from `opelpanfan/OPF-FLASHER` commit `6a925e2494777bb4e1a40eb6c3d8f2790873a812` on `master-grok` (app version 0.0.2+VC95, git tag `v0.0.3`).
  - This feed folder is `FLASHER/v0.0.3` because `FLASHER/v0.0.2` is the immutable VC42 package and must not be replaced. The app semver is still 0.0.2.
  - **Linux:** `OPF-FLASHER-linux-amd64.deb` — amd64 package with bundled Qt 6.8.3, esptool, and OpenOCD. Install with your package manager (`dpkg -i` or equivalent). Needs common system graphics and font libraries listed in the package Depends.

### SCREEN

Source repository: `opelpanfan/OPF-STORAGE-DASH`

Full flash is required. OTA of the app image alone is unsafe across partition layouts.

No version folders.

### RACE

Source repository: `opelpanfan/OPF-RACE-DASH`

#### `v0.0.2`

- Date: 2026-11-26
- Source commit: `f221cfea804e5e722623990af2b2aa1446562fc2` (opelpanfan/OPF-RACE-DASH)
- Files:
  - `RELEASE_NOTES.md` (2752 bytes, 2.7 KiB)
  - `SHA256SUMS` (79 bytes)
  - `esp32-p4.bin` (2557360 bytes, 2.44 MiB)
  - `index.json` (4098 bytes, 4.0 KiB)
- Full-install files: `esp32-p4` no
- Summary:
  - Version 0.0.2+VC12, commit f221cfea804e5e722623990af2b2aa1446562fc2 (master-grok, tag v0.0.2).
  - OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600).
  - This folder replaces the earlier v0.0.2 package (0.0.2+VC11, 116fce7) at Benas's instruction. The annotated tag `v0.0.2` was moved to this commit.

#### `v0.1.16`

- Date: 2026-11-24
- Source commit: `945821e7a897883c6dadda80adae347ebf344605` (opelpanfan/OPF-RACE-DASH)
- Files:
  - `RELEASE_NOTES.md` (1579 bytes, 1.5 KiB)
  - `SHA256SUMS` (79 bytes)
  - `esp32-p4.bin` (1960288 bytes, 1.87 MiB)
  - `index.json` (2921 bytes, 2.9 KiB)
- Full-install files: `esp32-p4` no
- Summary:
  - Version 0.1.16+VC17, commit 945821e7a897883c6dadda80adae347ebf344605 (master-grok, tag v0.1.16).
  - OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600). This is the first RACE package on the firmware feed.
  - Tick-driven screen refresh after each CAN update, aiming for a steady 50 FPS

#### `latest`

- Date: 2026-11-26
- Source commit: `f221cfea804e5e722623990af2b2aa1446562fc2` (opelpanfan/OPF-RACE-DASH)
- Files:
  - `RELEASE_NOTES.md` (2752 bytes, 2.7 KiB)
  - `SHA256SUMS` (79 bytes)
  - `esp32-p4.bin` (2557360 bytes, 2.44 MiB)
  - `index.json` (4097 bytes, 4.0 KiB)
- Full-install files: `esp32-p4` no
- Summary:
  - Version 0.0.2+VC12, commit f221cfea804e5e722623990af2b2aa1446562fc2 (master-grok, tag v0.0.2).
  - OPF Race Dash for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (1024x600).
  - This folder replaces the earlier v0.0.2 package (0.0.2+VC11, 116fce7) at Benas's instruction. The annotated tag `v0.0.2` was moved to this commit.
<!-- FEED-SUMMARY:END -->
