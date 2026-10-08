# P1 v0.0.1

First FEED release of the P1 meter link (RAK3172 / STM32WLE5): `RAK3172_TX` reads the smart-meter P1 port and sends it over LoRa; `RAK3172_RX` serves it as an Eastron-style meter on RS485/Modbus. Flash both as a pair (TX, then RX).

- P1 (DSMR/Sagemcom) telegram parsing with CRC check; corrupt telegrams are never parsed.
- LoRa split into a fast electrical frame (voltage, current, per-phase power, frequency, ~200 ms) and a slow energy frame (import/export Wh, ~30 s).
- When P1 drops, TX keeps sending the last known-good snapshot flagged `dataInvalid`; stale data expires by age and is not published as live.
- Long-run hardening: no allocation on the 1 Hz telegram path, wedged UART restarts with backoff, task stalls trip the watchdog instead of hanging, and RX stops serving Modbus after a silent LoRa link.
- RX holds RS485 DE through the last stop bit.
