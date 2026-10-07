# P1 firmware

STM32 RAK3172 transmitter and receiver. They are one release and are flashed as a pair.

Source: OPF-P1 branch `master-grok`, GitHub Release assets:

- `opf-p1-rak3172_transmiter-fw*.bin` → `RAK3172_TX.bin`
- `rak3172_receiver-fw*.bin` → `RAK3172_RX.bin`

The first feed release is tag `v1.0.0`. Publish waits until both assets exist, then writes `P1/v1.0.0/` and `P1/latest/`. Until that ingest succeeds, `latest.P1.available` is false.

Flasher reads `latest.P1` (or `latest.METER`, the same release) from the repository root `index.json`.
