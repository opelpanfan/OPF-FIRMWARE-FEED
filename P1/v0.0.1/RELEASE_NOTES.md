# P1 v0.0.1

**Frequency is 869.525 MHz (EU868 g3).** Flash both images from this release together. A Bridge DTU still tuned to 868.000 MHz will not hear these frames.

- Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm.
- Rolling 1-hour transmit cap stays under 10% duty, including command ACKs.
- Optional authenticated command downlink (reboot, P1 UART reinit, radio reinit) after each uplink. It is off in this image unless the build had `P1_CMD_KEY_HEX` set. Uplink format is unchanged either way.
- `FW_ITERATION_ID` 8.
