# Publishing into the feed

The feed branch is `main`. Version folders (`vX.Y.Z`, and the older unprefixed BMS folders) are immutable. `latest/` is the only moving channel. A publish is stored only when every required board is present and valid. Nothing is committed if validation fails.

Required set:

| Product | Source | Required files |
| --- | --- | --- |
| BMS | `opelpanfan/OPF-STORAGE-DASH` branch `master-grok`, env `opf-ws` | `OPF_WS.bin` |
| BRIDGE | `opelpanfan/OPF-STORAGE-M5-BRIDGE` `master-grok` @ `d9ca7a0`, workflow `build-firmware.yml` | `ATOM_S3_R.bin` and `ATOM_S3.bin` |
| P1 | `opelpanfan/OPF-P1` branch `master-grok`, GitHub Release tag `v1.0.1` (or a newer `vX.Y.Z`) | both TX and RX assets |

P1 asset names, including the transmitter spelling `transmiter` used by the release. Tag `v1.0.1` publishes these two `.bin` files (the `.elf` files are ignored):

- `opf-p1-rak3172_transmiter-fw6.bin` → `P1/v1.0.1/RAK3172_TX.bin`
- `opf-p1-rak3172_receiver-fw6.bin` → `P1/v1.0.1/RAK3172_RX.bin`

Later tags use the same shape. These globs map onto those board ids:

- `opf-p1-rak3172_transmiter-fw*.bin` (also `transmitter`, with or without the `opf-p1-` prefix) → `RAK3172_TX.bin`
- `opf-p1-rak3172_receiver-fw*.bin` (also `rak3172_receiver-fw*.bin`) → `RAK3172_RX.bin`

Bridge artifact names must be `ATOM_S3_R` or `ATOM_S3`, or the zip must contain `<env>/firmware.bin`. DTU versus RS485 is runtime configuration after flash. A workflow artifact named `ATOM_S3_DTU` or `ATOM_S3_R_DTU` is not a feed board: it is skipped, and the publish still requires the two real images. Any other unmapped `.bin` fails the job.

BMS has no workflow filename in the catalog yet. Pass `workflow_file` (basename only) on the first workflow-run publish, or set it in `.github/feed-catalog.json`.

## What “latest” means

`index.json` at the repository root is the list flasher should use. `latest.BMS`, `latest.BRIDGE`, and `latest.P1` are the channels. `latest.METER` aliases P1.

Every publish writes an immutable `PRODUCT/vX.Y.Z/` folder (`1.0.1` and `v1.0.1` both normalize to `v1.0.1`). `products[].versions[]` lists each of those folders with `artifacts` and `sha256`. That list is what flasher reads for pinned versions. `set_latest` (default true) then copies the same bytes to `PRODUCT/latest/`. `set_latest: false` leaves `latest/` unchanged.

`highest_semver_folder` is informational. It is not the channel. The tree currently has no version folders beside `latest/`, so `products[].versions` is empty and `matched_folder` is null until the next publish. A version folder is still not the channel: `latest/` is.

After a good publish with `set_latest` true, `latest/` is an exact copy of that version folder. A later publish does not edit the old folder. Rollback copies an older folder that is still in the tree back onto `latest/` and leaves every version folder untouched.

## Checks before anything is written

- Semver is `X.Y.Z` or `vX.Y.Z` with no prerelease suffix.
- The source repository must be the catalog repository. Fork runs are refused.
- Workflow runs must be successful and, unless `allow_any_ref` is set, on `master-grok`. Bridge runs must be `build-firmware.yml`.
- Release tags must match the version. A branch-like `target_commitish` must be `master-grok`. A commit SHA is accepted.
- ESP32 images must start with `0xE9` and be at least 64 KiB. P1 images must not be ESP32 images. ELF, zip, and HTML bodies are refused.
- Two boards in one publish cannot be byte-identical.
- If the caller supplies `sha256`, it must match. Release assets that include a GitHub `sha256:` digest are checked too.
- GitHub API 429/5xx and connection errors are retried. A missing or one-sided P1 release is retried five times, then the job fails without writing files.
- If `vX.Y.Z` already exists with different bytes, the publish fails. Republishing the same bytes is allowed.

## Dispatch from a source repo

Sources start a publish with `repository_dispatch`. The Actions secret on the source repo is `FW_FEED_PUSH_TOKEN` (fine-grained PAT, this feed only, Contents: read and write). The feed job then downloads the files itself with `SOURCE_READ_TOKEN` on `OPF-FIRMWARE-FEED`.

```http
POST /repos/opelpanfan/OPF-FIRMWARE-FEED/dispatches
```

Event type: `publish-firmware`.

`client_payload` fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `product` | yes | `BMS`, `BRIDGE`, or `P1`. `METER` is an alias of P1 and is not a publish target. |
| `version` | yes | `X.Y.Z` or `vX.Y.Z`. The folder written is always `vX.Y.Z`. |
| `source` | yes for BMS and BRIDGE | `workflow_run` or `release`. P1 only accepts `release`. Omit it on P1 and it defaults to `release`. |
| `tag` | release | Release tag. Defaults to `v` plus the normalized version. P1 `v1.0.1` is tag `v1.0.1`. |
| `run_id` | workflow_run | Successful Actions run id on the catalog ref. |
| `workflow_file` | workflow_run when the catalog has none | Workflow basename, such as `build-firmware.yml`. Bridge’s catalog value is `build-firmware.yml`. |
| `source_repository` | no | If set, it must be the catalog repository for that product. |
| `boards` | no | Comma-separated board ids, or an array. Must include every required board. |
| `set_latest` | no, default true | After `vX.Y.Z/` is written, copy those bytes to `latest/`. |
| `allow_any_ref` | no, default false | Allow a source ref other than `master-grok`. |
| `sha256` | no | Object of board id to 64 hex characters. A mismatch fails the publish. |
| `overwrite` | rejected | Version folders are immutable. |

The version folder is written even when `set_latest` is false.

P1, on the published `v1.0.1` release (and the same call for a later `v*` tag):

```bash
tag="${GITHUB_REF_NAME}"
version="${tag#v}"
curl -fsS -X POST \
  -H "Authorization: Bearer ${FW_FEED_PUSH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "https://api.github.com/repos/opelpanfan/OPF-FIRMWARE-FEED/dispatches" \
  -d "{\"event_type\":\"publish-firmware\",\"client_payload\":{\"product\":\"P1\",\"version\":\"${version}\",\"source\":\"release\",\"tag\":\"${tag}\",\"set_latest\":true,\"allow_any_ref\":false}}"
```

For tag `v1.0.1` that writes `P1/v1.0.1/RAK3172_TX.bin`, `P1/v1.0.1/RAK3172_RX.bin`, and the same pair under `P1/latest/`. Root `products[].versions[]` for P1 lists that folder with artifacts and sha256. `latest.P1.available` becomes true, and `latest.METER` aliases it.

Bridge, after `build-firmware.yml` succeeds on `master-grok`:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer ${FW_FEED_PUSH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "https://api.github.com/repos/opelpanfan/OPF-FIRMWARE-FEED/dispatches" \
  -d "{\"event_type\":\"publish-firmware\",\"client_payload\":{\"product\":\"BRIDGE\",\"version\":\"${VERSION}\",\"source\":\"workflow_run\",\"run_id\":\"${GITHUB_RUN_ID}\",\"workflow_file\":\"build-firmware.yml\",\"set_latest\":true,\"allow_any_ref\":false}}"
```

`VERSION` is the semver that build already computed (`1.2.3` or `v1.2.3`). The job writes `BRIDGE/vX.Y.Z/` and updates `BRIDGE/latest/`.

BMS is the same pattern as Bridge, with `product` `BMS` and `workflow_file` set to the workflow basename until the catalog records it.

The Actions tab can still run **Publish firmware** by hand (`workflow_dispatch`). Those inputs use the same field names. Source repos call `repository_dispatch`, not that manual form.

## Rollback

Pass the product plus a version folder that is still in the tree, such as `v1.2.3`. Historical folders were removed, so there is no rollback target until a later publish writes `vX.Y.Z/` again. The folder must contain every required board for that product. `latest/` is replaced with that folder’s binaries. The folder itself is not modified.

```bash
python3 .github/scripts/publish_firmware.py rollback --product BRIDGE --folder v1.2.3
```

## Secrets Benas needs to set

1. `OPF-FIRMWARE-FEED` → Settings → Actions → General → Workflow permissions → **Read and write**. The workflow file asks for `contents: write`; the repository setting is the ceiling.
2. If `main` has branch protection, allow `github-actions[bot]` to push, or add a bypass for that app. Publish pushes straight to `main`.
3. Secret `SOURCE_READ_TOKEN` on `OPF-FIRMWARE-FEED`. Fine-grained PAT, Contents: **Read**, on `OPF-STORAGE-DASH`, `OPF-STORAGE-M5-BRIDGE`, and `OPF-P1` only. `OPF-P1` is not readable without that token: unauthenticated GitHub returns 404 for the repository and for tag `v1.0.1`. The publish job cannot download `opf-p1-rak3172_transmiter-fw6.bin` or `opf-p1-rak3172_receiver-fw6.bin` until this secret exists. This change does not create the secret.
4. Secret `FW_FEED_PUSH_TOKEN` on each source repo (`OPF-P1`, `OPF-STORAGE-DASH`, `OPF-STORAGE-M5-BRIDGE`). Fine-grained PAT, this feed only, Contents: **Read and write**, used as the bearer token for `repository_dispatch` event `publish-firmware`. The name is `FW_FEED_PUSH_TOKEN`.
