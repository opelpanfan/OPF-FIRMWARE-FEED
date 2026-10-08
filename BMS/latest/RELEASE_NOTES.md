# BMS v0.0.1

Source: `opelpanfan/OPF-STORAGE-DASH` branch `master-grok` tip **`cac0af0`** (`cac0af0e23fa8b208717e79fc92d497b48494d15`).

## What changed vs the previous feed image (`3340aa9`)

- **Restored the working `master_ws` 0x334 decoder**: 4 cells per mux (`mux * 4`, mux 0–23) so the pack fills **96/96** cells again.
- **Reverted the bad `×4` on v2/v4** from `3340aa9` (those fields were already scaled; applying `×4` again pushed voltages to ~16 kV and the sanity window dropped half the pack → 48/96).
- **Dropped the experimental 3-cell-per-mux unpack** that landed on `master-grok` as `8cc394d` (not flashable / not the live path). Live verification under `master_ws` and this tip shows the 4-cell layout.

## Verified

- Live BMS `.158` flashed with this tip: **96/96** cells, voltages ~4010–4028 mV.

## Boards in this feed folder

`OPF_WS`, `OPF_WS_NO_TEMP`, `OPF_T2CAN`, `OPF_ATOM_S3`, `OPF_ATOM_S3R`, `OPF_WS_DASH` (same catalog as before).

Prior release notes (BLE commissioning, OTA, Device Console, etc.) still apply; this republish is a **PSA2 cell-decode fix only**.
