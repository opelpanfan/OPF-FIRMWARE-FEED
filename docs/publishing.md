# Publishing into the feed

The feed branch is `main`. Version folders (`vX.Y.Z`, and the older unprefixed BMS folders) are immutable. `latest/` is the only moving channel. A publish is stored only when every required board is present and valid. Nothing is committed if validation fails.

Required set:

| Product | Source | Required files |
| --- | --- | --- |
| BMS | `opelpanfan/OPF-STORAGE-DASH` branch `master-grok`, env `opf-ws` | `OPF_WS.bin` |
| BRIDGE | `opelpanfan/OPF-STORAGE-M5-BRIDGE` `master-grok` @ `d9ca7a0`, workflow `build-firmware.yml` | `ATOM_S3_R.bin` and `ATOM_S3.bin` |
| P1 | `opelpanfan/OPF-P1` branch `master-grok`, GitHub Release tag `v1.0.0` (or a newer `vX.Y.Z`) | both TX and RX assets |

P1 asset names, including the transmitter spelling used by the release:

- `opf-p1-rak3172_transmiter-fw*.bin` → `P1/vX.Y.Z/RAK3172_TX.bin`
- `rak3172_receiver-fw*.bin` → `P1/vX.Y.Z/RAK3172_RX.bin`

Bridge artifact names must be `ATOM_S3_R` or `ATOM_S3`, or the zip must contain `<env>/firmware.bin`. DTU versus RS485 is runtime configuration after flash. A workflow artifact named `ATOM_S3_DTU` or `ATOM_S3_R_DTU` is not a feed board: it is skipped, and the publish still requires the two real images. Any other unmapped `.bin` fails the job.

BMS has no workflow filename in the catalog yet. Pass `workflow_file` (basename only) on the first workflow-run publish, or set it in `.github/feed-catalog.json`.

## What “latest” means

`index.json` at the repository root is the list flasher should use. `latest.BMS`, `latest.BRIDGE`, and `latest.P1` are the channels. `latest.METER` aliases P1.

`highest_semver_folder` is informational. It is not the channel. The tree currently has no version folders beside `latest/`, so `highest_semver_folder` and `matched_folder` are null. A new publish adds `vX.Y.Z/` again. That folder still is not the channel.

After a good publish, `latest/` is an exact copy of that version folder. A later publish does not edit the old folder. Rollback copies an older folder that is still in the tree back onto `latest/` and leaves every version folder untouched.

## Checks before anything is written

- Semver is `X.Y.Z` or `vX.Y.Z` with no prerelease suffix.
- The source repository must be the catalog repository. Fork runs are refused.
- Workflow runs must be successful and, unless `allow_any_ref` is set, on `master-grok`. Bridge runs must be `build-firmware.yml`.
- Release tags must match the version. A branch-like `target_commitish` must be `master-grok`. A commit SHA is accepted.
- ESP32 images must start with `0xE9` and be at least 64 KiB. P1 images must not be ESP32 images. ELF, zip, and HTML bodies are refused.
- Two boards in one publish cannot be byte-identical.
- If the caller supplies `sha256`, it must match. Release assets that include a GitHub `sha256:` digest are checked too.
- GitHub API 429/5xx and connection errors are retried. A missing or one-sided P1 release is retried five times, because tag `v1.0.0` may still be rebuilding, and then the job fails without writing files.
- If `vX.Y.Z` already exists with different bytes, the publish fails. Republishing the same bytes is allowed.

## Dispatch from a source repo

Store `FEED_DISPATCH_TOKEN` on the source repo (fine-grained PAT, this feed only, Actions: read and write). The feed job then downloads the files itself with `SOURCE_READ_TOKEN`.

Bridge, after `build-firmware.yml` succeeds on `master-grok`:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer ${FEED_DISPATCH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "https://api.github.com/repos/opelpanfan/OPF-FIRMWARE-FEED/actions/workflows/publish-firmware.yml/dispatches" \
  -d "{\"ref\":\"main\",\"inputs\":{\"product\":\"BRIDGE\",\"version\":\"${VERSION}\",\"source\":\"workflow_run\",\"run_id\":\"${GITHUB_RUN_ID}\",\"set_latest\":\"true\",\"allow_any_ref\":\"false\"}}"
```

`VERSION` is the semver that build already computed (`1.2.3` or `v1.2.3`).

P1, on a published `v*` release:

```bash
tag="${GITHUB_REF_NAME}"
version="${tag#v}"
curl -fsS -X POST \
  -H "Authorization: Bearer ${FEED_DISPATCH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "https://api.github.com/repos/opelpanfan/OPF-FIRMWARE-FEED/actions/workflows/publish-firmware.yml/dispatches" \
  -d "{\"ref\":\"main\",\"inputs\":{\"product\":\"P1\",\"version\":\"${version}\",\"source\":\"release\",\"tag\":\"${tag}\",\"set_latest\":\"true\",\"allow_any_ref\":\"false\"}}"
```

BMS is the same pattern as Bridge, with `product` `BMS` and `workflow_file` set to the workflow basename until the catalog records it.

`repository_dispatch` with event type `publish-firmware` is also accepted. The client payload uses the same field names (`product`, `version`, `source`, `run_id`, `tag`, `workflow_file`, `set_latest`, `allow_any_ref`, `sha256`). `sha256` is an object of board id to hex digest.

## Rollback

Pass the product plus a version folder that is still in the tree, such as `v1.2.3`. Historical folders were removed, so there is no rollback target until a later publish writes `vX.Y.Z/` again. The folder must contain every required board for that product. `latest/` is replaced with that folder’s binaries. The folder itself is not modified.

```bash
python3 .github/scripts/publish_firmware.py rollback --product BRIDGE --folder v1.2.3
```

## Secrets Benas needs to set

1. `OPF-FIRMWARE-FEED` → Settings → Actions → General → Workflow permissions → **Read and write**. The workflow file asks for `contents: write`; the repository setting is the ceiling.
2. If `main` has branch protection, allow `github-actions[bot]` to push, or add a bypass for that app. Publish pushes straight to `main`.
3. Secret `SOURCE_READ_TOKEN` on `OPF-FIRMWARE-FEED`. Fine-grained PAT, Contents: **Read**, on `OPF-STORAGE-DASH`, `OPF-STORAGE-M5-BRIDGE`, and `OPF-P1` only.
4. Secret `FEED_DISPATCH_TOKEN` on each source repo. Fine-grained PAT, this feed only, Actions: **Read and write**.
