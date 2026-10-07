# Publishing into the feed

OPF-FIRMWARE-FEED is a passive catalog on `main`. Source repositories push product folders themselves. This repository does not download private releases, workflow artifacts, or any other source asset. There is no GitHub Action here that receives firmware, and a normal publish does not use `SOURCE_READ_TOKEN`.

Sources:

| Product | Source repository | Required files in the feed |
| --- | --- | --- |
| BMS | `opelpanfan/OPF-STORAGE-DASH` | `OPF_WS.bin` |
| BRIDGE | `opelpanfan/OPF-STORAGE-M5-BRIDGE` | `ATOM_S3_R.bin` and `ATOM_S3.bin` |
| P1 | `opelpanfan/OPF-P1` | `RAK3172_TX.bin` and `RAK3172_RX.bin` |

`METER` is an alias of P1. Do not push binaries under `METER/`.

Each source stores `FW_FEED_PUSH_TOKEN` as an Actions secret (fine-grained PAT, this feed only, Contents: **Read and write**). The source checks out this repository with that token, writes the folder, and pushes to `main`. The feed stores that commit. It does not call back into the private source.

## Folder layout

Version folders (`vX.Y.Z`, and the older unprefixed BMS folders) are immutable. `latest/` is the only moving channel. A publish is stored only when every required board is present and valid. Nothing is committed if validation fails.

`1.0.1` and `v1.0.1` both normalize to the folder `v1.0.1`. Older version folders stay in the tree. A later publish does not edit them and does not delete them.

`index.json` at the repository root is the list flasher and MQTT OTA read. `latest.BMS`, `latest.BRIDGE`, and `latest.P1` are the channels. `latest.METER` aliases P1. `products[].versions[]` lists every immutable version folder with `artifacts` and `sha256`.

Pass `--set-latest` to copy the same bytes to `PRODUCT/latest/`. Without that flag, `latest/` stays unchanged. `highest_semver_folder` is informational. It is not the channel.

After a good publish that updates the channel, `latest/` is an exact copy of that version folder. Rollback copies an older folder that is still in the tree back onto `latest/` and leaves every version folder untouched.

P1 asset names on the private OPF-P1 release, including the transmitter spelling `transmiter`. The source renames them before the push. Tag `v1.0.1` is already stored as:

- `opf-p1-rak3172_transmiter-fw6.bin` → `P1/v1.0.1/RAK3172_TX.bin`
- `opf-p1-rak3172_receiver-fw6.bin` → `P1/v1.0.1/RAK3172_RX.bin`

Later tags use the same shape. These globs map onto those board ids:

- `opf-p1-rak3172_transmiter-fw*.bin` (also `transmitter`, with or without the `opf-p1-` prefix) → `RAK3172_TX.bin`
- `opf-p1-rak3172_receiver-fw*.bin` (also `rak3172_receiver-fw*.bin`) → `RAK3172_RX.bin`

Bridge files in the feed are `ATOM_S3_R.bin` and `ATOM_S3.bin`. DTU versus RS485 is runtime configuration after flash. Do not push `ATOM_S3_DTU` or `ATOM_S3_R_DTU`.

## Checks before anything is written

Run these locally against the feed checkout. They read files already on disk.

- Semver is `X.Y.Z` or `vX.Y.Z` with no prerelease suffix.
- ESP32 images must start with `0xE9` and be at least 64 KiB. P1 images must not be ESP32 images. ELF, zip, and HTML bodies are refused.
- Two boards in one publish cannot be byte-identical.
- The required board set must be complete. P1 TX and RX are one pair.
- If `vX.Y.Z` already exists with different bytes, the publish fails. Republishing the same bytes is allowed.
- `python3 .github/scripts/publish_firmware.py validate` fails when `index.json` or `SHA256SUMS` disagree with the binaries.

## Push from a source repo

`FW_FEED_PUSH_TOKEN` is the only secret a normal publish needs, and it lives on the source repository, not on this feed.

```bash
git clone "https://x-access-token:${FW_FEED_PUSH_TOKEN}@github.com/opelpanfan/OPF-FIRMWARE-FEED.git"
cd OPF-FIRMWARE-FEED
git checkout main
```

Stage the feed filenames, then let the local tool write the immutable folder, `latest/` when requested, `index.json`, and `SHA256SUMS`. `--from-dir` must already use board filenames (`RAK3172_TX.bin`, not the private release asset name).

P1:

```bash
mkdir -p staging
cp "$TX_BIN" staging/RAK3172_TX.bin
cp "$RX_BIN" staging/RAK3172_RX.bin
python3 .github/scripts/publish_firmware.py apply \
  --product P1 \
  --version "${VERSION}" \
  --from-dir staging \
  --set-latest
python3 .github/scripts/publish_firmware.py validate
git add -- P1 index.json SHA256SUMS
git commit -m "Publish P1 firmware ${VERSION}"
git push origin HEAD:main
```

`VERSION` is `1.0.1` or `v1.0.1`. The folder written is `P1/v1.0.1/`. Omit `--set-latest` to leave `P1/latest/` unchanged.

Bridge, from the two board images:

```bash
mkdir -p staging
cp "$ATOM_S3_BIN" staging/ATOM_S3.bin
cp "$ATOM_S3_R_BIN" staging/ATOM_S3_R.bin
python3 .github/scripts/publish_firmware.py apply \
  --product BRIDGE \
  --version "${VERSION}" \
  --from-dir staging \
  --set-latest
python3 .github/scripts/publish_firmware.py validate
git add -- BRIDGE index.json SHA256SUMS
git commit -m "Publish BRIDGE firmware ${VERSION}"
git push origin HEAD:main
```

BMS is the same pattern with `--product BMS` and `staging/OPF_WS.bin` (plus any extra catalog boards that are part of that release). The commit adds `BMS/vX.Y.Z/` and, with `--set-latest`, replaces `BMS/latest/`.

`apply` and `validate` do not contact GitHub. A human can run `validate` on a checkout with no token at all.

## Rollback

Pass the product plus a version folder that is in the tree, such as `BRIDGE/v1.0.1` or `v1.2.3`. The folder must contain every required board for that product. `latest/` is replaced with that folder’s binaries. The folder itself is not modified, and no other version folder is deleted. Commit and push the result with `FW_FEED_PUSH_TOKEN` the same way as a publish.

```bash
python3 .github/scripts/publish_firmware.py rollback --product BRIDGE --folder v1.2.3
python3 .github/scripts/publish_firmware.py validate
```

## Secrets

On each source repo (`OPF-P1`, `OPF-STORAGE-M5-BRIDGE`, `OPF-STORAGE-DASH`):

- Secret `FW_FEED_PUSH_TOKEN`: fine-grained PAT for `OPF-FIRMWARE-FEED` only, Contents **Read and write**, used to clone and push product folders.

On `OPF-FIRMWARE-FEED`:

- No `SOURCE_READ_TOKEN`. Normal publishes do not read the private source repositories from this repo.
- No Actions secret is required to receive firmware. This repository has no publish or ingest workflow.
