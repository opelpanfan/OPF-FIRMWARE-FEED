# P1 firmware

STM32 RAK3172 transmitter and receiver. They are one release and are flashed as a pair.

Source: OPF-P1 pushes the pair. This feed does not download the private release. Tag `v1.0.1` (later tags use the same names with a new `fw*` suffix):

- `opf-p1-rak3172_transmiter-fw6.bin` → `RAK3172_TX.bin`
- `opf-p1-rak3172_receiver-fw6.bin` → `RAK3172_RX.bin`

`P1/v1.0.1/` is the immutable folder. `P1/latest/` matches it. `latest.P1.available` is true. `METER` is an alias of this release.

Flasher reads `latest.P1` (or `latest.METER`) and `products[].versions` for `P1` from the repository root `index.json`.
