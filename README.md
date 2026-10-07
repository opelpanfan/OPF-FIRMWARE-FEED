# OPF Firmware Feed

Public firmware feed for OPF-FLASHER and device OTA. Binaries live on the `main` branch.

There is no `firmware-packages` branch. OTA and flasher URLs use `main`.

## How flasher lists latest

Fetch one file:

`https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/index.json`

Read `latest.BMS`, `latest.BRIDGE`, and `latest.P1`. `latest.METER` is the same release as `latest.P1` (transmitter and receiver are stored under `P1/`).

Use a product only when `available` is true. Download each object in `artifacts[]`, check `sha256`, then flash. For P1/METER, flash `RAK3172_TX` and `RAK3172_RX` from that same latest object as a pair. If either board is missing, do not flash.

`products[].versions[]` lists every immutable `vX.Y.Z/` folder, with `artifacts` and `sha256`. `latest.*` is the channel. Historical version folders were removed, so today `products[].versions` is empty, `matched_folder` is null, and `highest_semver_is_latest` is false. The next publish writes `vX.Y.Z/` again and lists it there. The version label stored inside each `latest/` folder is:

- BMS latest is version `1.0.1`. The bytes are only at `BMS/latest/` until the next publish also stores `BMS/vX.Y.Z/`.
- Bridge latest is version `v1.0.1`. Flash only `ATOM_S3_R` and `ATOM_S3`. `latest.BRIDGE.runtime_config` records that DTU versus RS485 is chosen after flash. There are no `ATOM_S3_R_DTU` or `ATOM_S3_DTU` files.
- P1 latest stays unavailable until tag `v1.0.1` is ingested (`opf-p1-rak3172_transmiter-fw6.bin` and `opf-p1-rak3172_receiver-fw6.bin`).

Direct latest URLs that exist today:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BMS/latest/OPF_WS.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3_R.bin`

After the first successful P1 ingest, the same pattern is:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/P1/latest/RAK3172_TX.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/P1/latest/RAK3172_RX.bin`

A later publish still writes an immutable `vX.Y.Z/` folder and copies those bytes onto `latest/`. Until that happens, older pinned URLs such as `BMS/1.0.2/`, `BMS/v1.0.5/`, `BMS/master_ws_redesign/`, and `BRIDGE/v1.0.14/` are not in the feed.

## Layout

- `BMS/` from [OPF-STORAGE-DASH](https://github.com/opelpanfan/OPF-STORAGE-DASH) `master-grok`, env `opf-ws`. The channel is `BMS/latest/`.
- `BRIDGE/` from [OPF-STORAGE-M5-BRIDGE](https://github.com/opelpanfan/OPF-STORAGE-M5-BRIDGE) `master-grok` at `d9ca7a0`. Flash `ATOM_S3_R.bin` and `ATOM_S3.bin` only. DTU versus RS485 is runtime configuration after flash, so the feed has no `ATOM_S3_R_DTU` or `ATOM_S3_DTU` assets.
- `P1/` from [OPF-P1](https://github.com/opelpanfan/OPF-P1) `master-grok` release tags. `opf-p1-rak3172_transmiter-fw*.bin` becomes `RAK3172_TX.bin`. `opf-p1-rak3172_receiver-fw*.bin` becomes `RAK3172_RX.bin`. Tag `v1.0.1` uses the `fw6` asset names. TX and RX are published together or not at all.
- `METER/` has no binaries. It is the flasher alias for P1.

## Workflows

- **Publish firmware** downloads a complete source release or `master-grok` workflow run, checks the image, writes `vX.Y.Z/`, then points `latest/` at that release.

Publish details, including the secrets below, are in [docs/publishing.md](docs/publishing.md).

## Secrets and permissions

On this repository:

- Actions workflow permissions must allow GitHub Actions to write contents. **Publish firmware** pushes to `main` as `github-actions[bot]`, which is how firmware already landed. If `main` is protected, that identity needs a bypass.
- Secret `SOURCE_READ_TOKEN`: fine-grained PAT with Contents read on `OPF-STORAGE-DASH`, `OPF-STORAGE-M5-BRIDGE`, and `OPF-P1`.

On each source repository:

- Secret `FW_FEED_PUSH_TOKEN`: fine-grained PAT for `OPF-FIRMWARE-FEED` only, Contents read and write, used to send `repository_dispatch` event `publish-firmware`. The feed then downloads the binaries with `SOURCE_READ_TOKEN`.

