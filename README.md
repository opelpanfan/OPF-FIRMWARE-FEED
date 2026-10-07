# OPF Firmware Feed

Public firmware feed for OPF-FLASHER and device OTA. Binaries live on the `main` branch.

There is no `firmware-packages` branch. OTA and flasher URLs use `main`.

## How flasher lists latest

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/index.json`

Read `latest.BMS`, `latest.BRIDGE`, and `latest.P1`. `latest.METER` is the same release as `latest.P1` (transmitter and receiver are stored under `P1/`).

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1/METER, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

`products[].versions[]` lists every immutable version folder, with `artifacts` and `sha256`. Those folders stay in the tree. `latest.*` is the channel and is refreshed from a publish only when `set_latest` is true. `highest_semver_is_latest` is false: the highest folder is not the channel.

- BMS `latest/` is version `1.0.1` and matches `BMS/v1.0.1/`. Older folders such as `BMS/v1.0.5/` and `BMS/1.0.2/` stay published.
- Bridge `latest/` is version `v1.0.1` and matches `BRIDGE/v1.0.1/`. Flash only `ATOM_S3_R` and `ATOM_S3`. `latest.BRIDGE.runtime_config` records that DTU versus RS485 is chosen after flash. There are no `ATOM_S3_R_DTU` or `ATOM_S3_DTU` files. Older folders through `BRIDGE/v1.0.14/` stay published.
- P1 `latest/` is version `v1.0.1` and matches `P1/v1.0.1/`. Flash `RAK3172_TX` and `RAK3172_RX` as a pair. `latest.METER` is that same pair.

Direct latest URLs:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BMS/latest/OPF_WS.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3_R.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/P1/latest/RAK3172_TX.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/P1/latest/RAK3172_RX.bin`

A source push writes an immutable `vX.Y.Z/` folder and, when that release is the channel, copies those bytes onto `latest/`. It does not delete older version folders. Pinned URLs such as `BMS/v1.0.1/`, `BMS/1.0.2/`, `BRIDGE/v1.0.1/`, `BRIDGE/v1.0.14/`, and `P1/v1.0.1/` stay in the feed.

## Layout

- `BMS/` from [OPF-STORAGE-DASH](https://github.com/opelpanfan/OPF-STORAGE-DASH) `master-grok`, env `opf-ws`. The channel is `BMS/latest/`.
- `BRIDGE/` from [OPF-STORAGE-M5-BRIDGE](https://github.com/opelpanfan/OPF-STORAGE-M5-BRIDGE) `master-grok` at `d9ca7a0`. Flash `ATOM_S3_R.bin` and `ATOM_S3.bin` only. DTU versus RS485 is runtime configuration after flash, so the feed has no `ATOM_S3_R_DTU` or `ATOM_S3_DTU` assets.
- `P1/` from [OPF-P1](https://github.com/opelpanfan/OPF-P1). The source renames `opf-p1-rak3172_transmiter-fw*.bin` to `RAK3172_TX.bin` and `opf-p1-rak3172_receiver-fw*.bin` to `RAK3172_RX.bin`, then pushes the folder. Tag `v1.0.1` is already published. TX and RX are published together or not at all.
- `METER/` has no binaries. It is the flasher alias for P1.

## How firmware arrives

This repository is a passive catalog. OPF-P1, OPF-STORAGE-M5-BRIDGE, and OPF-STORAGE-DASH push `P1/`, `BRIDGE/`, and `BMS/` themselves. There is no ingest workflow and no Action that downloads private releases.

Publish details are in [docs/publishing.md](docs/publishing.md).

## Secrets

This repository does not need `SOURCE_READ_TOKEN`, and it does not need an Actions secret to receive firmware.

On each source repository:

- Secret `FW_FEED_PUSH_TOKEN`: fine-grained PAT for `OPF-FIRMWARE-FEED` only, Contents read and write, used to clone this feed and push the product folder.

