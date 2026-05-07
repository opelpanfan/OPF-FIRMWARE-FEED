# OPF Firmware Feed

Public firmware feed and OTA validation repository for OPF bridge devices.

## Purpose

- Hosts public firmware binaries for OTA downloads.
- Provides manual MQTT OTA smoke test workflow against real devices.

## Repository Layout

- `latest/`
  - `ATOM_S3.bin`
  - `ATOM_S3_R.bin`
  - `index.json`
- `vX.Y.Z/`
  - version-pinned firmware files
- `.github/workflows/ota-mqtt-smoke-test.yml`
  - manual OTA smoke test workflow

## OTA URLs

Latest:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/latest/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/latest/ATOM_S3_R.bin`

Versioned example:

- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/v1.0.0/ATOM_S3.bin`
- `https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/firmware-packages/v1.0.0/ATOM_S3_R.bin`

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

Firmware files are expected to be pushed by CI from the private source repository into this repository's `firmware-packages` branch.
