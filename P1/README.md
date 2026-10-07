# P1 firmware

STM32 RAK3172 transmitter and receiver. They are one release and are flashed as a pair.

Source: OPF-P1 branch `master-grok`, GitHub Release tag `v1.0.1` (later tags use the same names with a new `fw*` suffix):

- `opf-p1-rak3172_transmiter-fw6.bin` → `RAK3172_TX.bin`
- `opf-p1-rak3172_receiver-fw6.bin` → `RAK3172_RX.bin`

Publish writes immutable `P1/v1.0.1/` and, when `set_latest` is true, `P1/latest/`. Until that ingest succeeds, `latest.P1.available` is false and this folder has no binaries. `METER` is an alias of this release.

Flasher reads `latest.P1` (or `latest.METER`) and `products[].versions` for `P1` from the repository root `index.json`.
