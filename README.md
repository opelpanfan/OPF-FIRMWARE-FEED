# OPF Firmware Feed

Public firmware catalog for OPF-FLASHER and device OTA. Binaries live on the `main` branch.

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/index.json`

Read `latest.BMS`, `latest.BRIDGE`, `latest.P1`, `latest.METER`, `latest.CONFIG_APP`, and `latest.FLASHER`.

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

`products[].versions[]` lists every immutable version folder. `latest.*` is the channel.

CONFIG_APP, FLASHER, and METER stay empty until sources publish a version folder. Until then `available` is false and `versions` is `[]`.

This repository is a passive catalog. Sources push `P1/`, `BRIDGE/`, `BMS/`, `METER/`, `CONFIG_APP/`, and `FLASHER/` themselves. There is no ingest workflow and no Action that downloads private releases. This repository does not need `SOURCE_READ_TOKEN`.

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

BMS, BRIDGE, and METER may publish three optional install companions next to each board's app image `<BOARD>.bin`. Publish all three for that board, or none. A partial set is refused. Other boards in the same folder may omit the set. Validation passes when the companions are absent. P1, CONFIG_APP, and FLASHER do not use these files.

| File | Flash offset |
| --- | --- |
| `<BOARD>.bootloader.bin` | `0x0` |
| `<BOARD>.partitions.bin` | `0x8000` |
| `<BOARD>.boot_app0.bin` | `0xe000` |

When the set is present, that board's object in `artifacts[]` includes `install` with `bootloader`, `partitions`, and `boot_app0`. Each of those objects has:

- `path` — filename in that same folder
- `sha256` — digest of that file
- `size` — byte length
- `offset` — `0x0` for bootloader, `0x8000` for partitions, `0xe000` for boot_app0

The same three files are lines in the folder `SHA256SUMS` and the root `SHA256SUMS`. `install` is omitted when the board has no companions. The app image stays `<BOARD>.bin`.

Board filenames are in `.github/feed-catalog.json`.

- `P1/`: `RAK3172_TX.bin` and `RAK3172_RX.bin`, published together.
- `BRIDGE/`: `ATOM_S3_R.bin` and `ATOM_S3.bin`.
- `BMS/`: catalog boards, including `OPF_WS.bin`.
- `METER/`: `transmitter.bin`, `receiver.bin`, `transmitter_lcd.bin`, and `receiver_lcd.bin`, published together under `METER/vX.Y.Z/` and `METER/latest/`. ESP32-S3 images for AtomS3 and AtomS3R from OPF-LORA-METER, built with `partitions/ota_8MB.csv` and qio flash mode. Optional companions use the filenames above.
- `FLASHER/`: `OPF-FLASHER-win-x64.exe` and `OPF-FLASHER-linux-amd64.deb`. Not a board image. Until the first real app release the version folder stays `v0.0.1` and may be replaced in place.
- `CONFIG_APP/`: `opf-config-app.apk`.

<!-- FEED-SUMMARY:START -->
## Versions

Each product below is one this feed knows. Version folders are listed from oldest to newest, then `latest`.
The date is the feed commit that last changed that folder. A source commit is shown when that folder's `index.json` metadata has `source.sha`.
The summary is the first lines of `FEED_RELEASE_NOTES.md` in that folder, or of `RELEASE_NOTES.md` when that is the notes file present.
ESP32 folders also list full-install files: `yes` when that board has bootloader, partitions, and boot_app0, `no` when it has the app image only.

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
- Full-install files: `OPF_WS` no, `OPF_WS_NO_TEMP` no, `OPF_T2CAN` no, `OPF_ATOM_S3` no, `OPF_ATOM_S3R` no, `OPF_WS_DASH` no
- Summary:
  - Web UI: v0.0.1 layout restored (Dashboard, Battery, Settings, Status). New settings sit as plain fields in their v0.0.1 sections.
  - Soft start: after boot, charge and discharge limits ramp from 5 A to max over 60 s.
  - SoC taper: charge and discharge limits ramp from 5 A at the low and high SoC ends and near cell voltage limits.

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
- Full-install files: `OPF_WS` no, `OPF_WS_NO_TEMP` no, `OPF_T2CAN` no, `OPF_ATOM_S3` no, `OPF_ATOM_S3R` no, `OPF_WS_DASH` no
- Summary:
  - Web UI: v0.0.1 layout restored (Dashboard, Battery, Settings, Status). New settings sit as plain fields in their v0.0.1 sections.
  - Soft start: after boot, charge and discharge limits ramp from 5 A to max over 60 s.
  - SoC taper: charge and discharge limits ramp from 5 A at the low and high SoC ends and near cell voltage limits.

### BRIDGE

Source repository: `opelpanfan/OPF-STORAGE-M5-BRIDGE`

#### `v0.0.1`

- Date: 2026-10-20
- Source commit: `5c4711e9b87b8a8626fcb38da824af750219a2d5` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1916320 bytes, 1.83 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (1962048 bytes, 1.87 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (9145 bytes, 8.9 KiB)
  - `SHA256SUMS` (696 bytes)
  - `index.json` (12186 bytes, 11.9 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes
- Summary:
  - Console and AtomS3R LCD layout restored to the v0.0.1 look (v0.0.2 shared-UX layout removed). Non-UI firmware fixes kept.
  - Feed publish target is again `BRIDGE/v0.0.1` (`FEED_FIXED_VERSION`); `BRIDGE/v0.0.2` is removed from the feed. `latest` follows v0.0.1.
  - RS485 read and write waits yield instead of spinning. A dead bus was a priority-2 busy loop and could starve the watchdog tasks (`atom_loop`, LCD).

#### `latest`

- Date: 2026-10-20
- Source commit: `5c4711e9b87b8a8626fcb38da824af750219a2d5` (opelpanfan/OPF-STORAGE-M5-BRIDGE)
- Files:
  - `ATOM_S3.bin` (1916320 bytes, 1.83 MiB)
  - `ATOM_S3.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3.partitions.bin` (3072 bytes, 3.0 KiB)
  - `ATOM_S3_R.bin` (1962048 bytes, 1.87 MiB)
  - `ATOM_S3_R.boot_app0.bin` (8192 bytes, 8.0 KiB)
  - `ATOM_S3_R.bootloader.bin` (15104 bytes, 14.8 KiB)
  - `ATOM_S3_R.partitions.bin` (3072 bytes, 3.0 KiB)
  - `RELEASE_NOTES.md` (9145 bytes, 8.9 KiB)
  - `SHA256SUMS` (696 bytes)
  - `index.json` (12185 bytes, 11.9 KiB)
- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes
- Summary:
  - Console and AtomS3R LCD layout restored to the v0.0.1 look (v0.0.2 shared-UX layout removed). Non-UI firmware fixes kept.
  - Feed publish target is again `BRIDGE/v0.0.1` (`FEED_FIXED_VERSION`); `BRIDGE/v0.0.2` is removed from the feed. `latest` follows v0.0.1.
  - RS485 read and write waits yield instead of spinning. A dead bus was a priority-2 busy loop and could starve the watchdog tasks (`atom_loop`, LCD).

### P1

Source repository: `opelpanfan/OPF-P1`

No version folders.

### CONFIG_APP

Source repository: `opelpanfan/OPF-CONFIG-APP`

No version folders.

### METER

Source repository: `opelpanfan/OPF-LORA-METER`

No version folders.

### FLASHER

Source repository: `opelpanfan/OPF-FLASHER`

No version folders.
<!-- FEED-SUMMARY:END -->
