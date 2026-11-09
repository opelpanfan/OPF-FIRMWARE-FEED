# P1 v0.0.2

**Frequency is 869.525 MHz (EU868 g3).** Flash both images from this release together. The radio settings and uplink format are the same as v0.0.1.

- Fast uplink (type `0x06`, 39 bytes) every 1 s. Slow uplink (type `0x07`, 21 bytes) every 30 s. Protocol version byte stays 4. SF7, BW125, CR4/5, preamble 8, sync `0x1424`, 22 dBm. Rolling 1-hour transmit cap stays under 10% duty.
- P1 telegram sanity check: a telegram is published only when it carries U1-3, I1-3 and import power, voltages are 0 V or 150-280 V, currents are at most 100 A, every power is at most `P1_MAX_POWER_W` (50 kW), and frequency, when sent, is 45-55 Hz.
- A new `/` at the start of a line restarts the telegram, so a telegram cut short on the wire is dropped instead of being glued to the next one.
- A missing frequency line goes out as 0 Hz, not 50 Hz.
- Transmitter stall watchdog only fires while a transmit is actually in progress. Duty-cycle refusal and idle time no longer count as a radio fault.
- Radio recovery is split into soft and hard. A hard radio reinit happens only after 3 consecutive faults, and a TX timeout is no longer counted twice.
- The P1 UART is fully drained after a reinit (up to 512 bytes).
- Receiver: Modbus answers exception `0x0B` once no valid frame has arrived for 3 s, so an unplugged meter no longer freezes the last watts. Link stale and Modbus hold are both 3 s.
- Receiver: Modbus reads outside the register map answer exception `0x02`.
- Field diagnostics (read over SWD) add radio IRQ, header error, RSSI/SNR, recovery-pending, last sequence, soft fault and hard recovery counters, and last valid telegram age.
- New PlatformIO env `direct` (P1 to Modbus RS485 with no LoRa) for a meter wired straight to the inverter. It is not part of this feed release.
- `FW_ITERATION_ID` 13.
