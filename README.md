# OPF Firmware Feed

Public firmware feed and OTA validation repository for OPF devices.

## Purpose

- Hosts public firmware binaries for OTA downloads.
- Provides manual MQTT OTA smoke test workflow against real devices.

## Repository Layout

Firmware is separated by product family:

- `BMS/`
  - `latest/`
  - `vX.Y.Z/`
- `BRIDGE/`
  - `latest/`
  - `vX.Y.Z/`
- `METER/`
  - `latest/`
  - `vX.Y.Z/`
- `.github/workflows/ota-mqtt-smoke-test.yml`
  - manual OTA smoke test workflow

Each product keeps its own binaries and `latest/index.json`.

## OTA URLs

Latest:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/BRIDGE/latest/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/BRIDGE/latest/ATOM_S3_R.bin`

Versioned example:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/BRIDGE/v1.0.0/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/BRIDGE/v1.0.0/ATOM_S3_R.bin`

## OTA Smoke Test Workflow

The `OTA MQTT Smoke Test` workflow is run manually from Actions.

Required Environment and Secrets:

- Environment: `QA`
- Secrets:
  - `MQTT_HOST`
  - `MQTT_PORT` (optional; defaults to 1883)
  - `MQTT_USERNAME` (optional)
  - `MQTT_PASSWORD` (optional)

Default target device is `8ABO2G`.

## Publishing Firmware Files

Firmware files are expected to be pushed by CI from private source repositories into this repository's `firmware-packages` branch, under the matching product folder (`BMS`, `BRIDGE`, `METER`).
