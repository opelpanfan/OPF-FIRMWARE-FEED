# OPF Firmware Feed

Public firmware feed for OPF-FLASHER and device OTA. Binaries live on the `main` branch.

There is no `firmware-packages` branch. OTA and flasher URLs use `main`.

## How flasher lists latest

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/index.json`

Read `latest.BMS`, `latest.BRIDGE`, and `latest.P1`. `latest.METER` is the same release as `latest.P1` (transmitter and receiver are stored under `P1/`).

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1/METER, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

Do not pick the highest `vX.Y.Z` folder. Those numbers were not published in order. `latest.*.highest_semver_is_latest` is false for the current BMS and Bridge channels. `matched_folder` is the immutable folder whose bytes match `latest/` today:

- BMS latest is `1.0.2` (folder `BMS/1.0.2`, also `BMS/latest`). The highest semver folder is `v1.0.4`, published earlier, and it is a different image.
- Bridge latest is `v1.0.11`. `v1.0.12` through `v1.0.14` were published before `v1.0.11`. Flash only `ATOM_S3_R` and `ATOM_S3`. `latest.BRIDGE.runtime_config` records that DTU versus RS485 is chosen after flash. There are no `ATOM_S3_R_DTU` or `ATOM_S3_DTU` files.
- P1 latest stays unavailable until both `v1.0.0` release assets have been ingested.

Direct latest URLs that exist today:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BMS/latest/OPF_WS.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3_R.bin`

After the first successful P1 ingest, the same pattern is:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/P1/latest/RAK3172_TX.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/P1/latest/RAK3172_RX.bin`

Pinned builds stay at `BMS/vX.Y.Z/`, `BMS/X.Y.Z/` (legacy), `BRIDGE/vX.Y.Z/`, and `P1/vX.Y.Z/`. Those folders are not rewritten after publish. Each folder has `index.json` and `SHA256SUMS`.

`BMS/1.0.2/OPF_WS.bin` and `BMS/v1.0.2/OPF_WS.bin` are different files. Devices that already call one of those paths keep getting that file.

## Layout

- `BMS/` from [OPF-STORAGE-DASH](https://github.com/opelpanfan/OPF-STORAGE-DASH) `master-grok`, env `opf-ws`, file `OPF_WS.bin`. Older boards remain in historical folders.
- `BRIDGE/` from [OPF-STORAGE-M5-BRIDGE](https://github.com/opelpanfan/OPF-STORAGE-M5-BRIDGE) `master-grok` at `d9ca7a0`. Flash `ATOM_S3_R.bin` and `ATOM_S3.bin` only. DTU versus RS485 is runtime configuration after flash, so the feed has no `ATOM_S3_R_DTU` or `ATOM_S3_DTU` assets.
- `P1/` from [OPF-P1](https://github.com/opelpanfan/OPF-P1) `master-grok` release tags. `opf-p1-rak3172_transmiter-fw*.bin` becomes `RAK3172_TX.bin`. `rak3172_receiver-fw*.bin` becomes `RAK3172_RX.bin`. TX and RX are published together or not at all.
- `METER/` has no binaries. It is the flasher alias for P1.

## Workflows

- **Publish firmware** downloads a complete source release or `master-grok` workflow run, checks the image, writes `vX.Y.Z/`, then points `latest/` at that release.
- **Rollback latest channel** points `latest/` at an older folder. It does not change the version folder.
- **OTA MQTT smoke test** sends one URL to a QA device. It does not publish firmware.
- **Validate feed** checks manifests, checksums, and image headers on pull requests.

Publish and rollback details, including the secrets below, are in [docs/publishing.md](docs/publishing.md).

## Secrets and permissions

On this repository:

- Actions workflow permissions must allow GitHub Actions to write contents. **Publish firmware** pushes to `main` as `github-actions[bot]`, which is how firmware already landed. If `main` is protected, that identity needs a bypass.
- Secret `SOURCE_READ_TOKEN`: fine-grained PAT with Contents read on `OPF-STORAGE-DASH`, `OPF-STORAGE-M5-BRIDGE`, and `OPF-P1`.

On each source repository:

- Secret `FEED_DISPATCH_TOKEN`: fine-grained PAT for `OPF-FIRMWARE-FEED` only, Actions read and write, used to start **Publish firmware**.

OTA smoke still uses the `QA` environment and `MQTT_HOST`, optional `MQTT_PORT`, `MQTT_USERNAME`, and `MQTT_PASSWORD`. The device id is typed in when the workflow is run.
