# P1 v0.0.3

**Frequency is 869.525 MHz (EU868 g3).** This is fw17: firmware **0.0.3+VC17** (`9425eea`, `version_code` 17; the device's own version text reads `0.0.2+17`). Tag `v0.0.3` on `master-grok`. Flash both images from this release together. The radio settings and uplink format are the same as v0.0.2.

- The P1 meter stays valid for 15 s (`P1_INVALID_AFTER_MS`), so a meter that sends every 10 s no longer flags every uplink as invalid. In v0.0.2 `dataInvalid` fired after 2 s.
- The transmitter clears USART1 overrun, framing, noise and parity errors (ORE/FE/NE/PE) on the live path. A stuck overrun used to stop reception.
- `recoverP1Uart` reinitializes the port after 30 s without an accepted telegram, then backs off to 60 s and 120 s. It does not reinit on top of a live meter.
- The telegram parser resyncs on `/` after a CR-only cut.
- Field diagnostics over SWD: `gFieldDiag` at `0x20002ffc` is now 75 words (`mdw 0x20002ffc 75`), with new `p1UartOre`, `p1UartFe`, `p1UartNe` and `p1UartPe` counters.
- LoRa downlink command to reset the P1 UART (`P1_UART`). Commands are accepted only when the transmitter is built with a command key. This FEED transmitter image is unkeyed, so commands are disabled.
- The `VERSION` file at this commit reads `0.0.2+17`, so the device version text is `0.0.2+17` while the tag and FEED folder are `v0.0.3`. `FW_ITERATION_ID` is 17.
