#!/usr/bin/env python3
"""Optional ESP32 install companions and the standalone METER product."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

from feedlib import (  # noqa: E402
    FeedError,
    apply_publish,
    load_catalog,
    resolve_ota_url,
    rollback_latest,
    validate_feed,
)

SCRIPT = ROOT / ".github" / "scripts" / "publish_firmware.py"

METER_BOARDS = ("transmitter", "receiver", "transmitter_lcd", "receiver_lcd")
ROLES = ("bootloader", "partitions", "boot_app0")
OFFSETS = {"bootloader": "0x0", "partitions": "0x8000", "boot_app0": "0xe000"}


def _esp(marker: int) -> bytes:
    data = bytearray(64 * 1024)
    data[0] = 0xE9
    data[10] = marker % 256
    data[11] = (marker // 256) % 256
    return bytes(data)


def _stm(marker: int) -> bytes:
    data = bytearray(1024)
    data[0] = 1 if marker == 0xE9 else marker
    data[20] = marker
    return bytes(data)


def _companion(role: str, marker: int) -> bytes:
    data = bytearray(256)
    data[0] = 0xE9 if role == "bootloader" else 0xAA
    data[10] = marker % 256
    data[11] = (marker // 256) % 256
    data[20] = ROLES.index(role)
    return bytes(data)


def _bridge_bins(marker: int) -> dict[str, tuple[bytes, str]]:
    return {
        "ATOM_S3": (_esp(marker), "ATOM_S3.bin"),
        "ATOM_S3_R": (_esp(marker + 1), "ATOM_S3_R.bin"),
    }


def _meter_bins(marker: int) -> dict[str, tuple[bytes, str]]:
    return {
        board: (_esp(marker + index), f"{board}.bin")
        for index, board in enumerate(METER_BOARDS)
    }


def _install_for(boards: tuple[str, ...] | list[str], marker: int, *, shared_boot_app0: bool = False) -> dict:
    shared = _companion("boot_app0", 7) if shared_boot_app0 else None
    install = {}
    for index, board in enumerate(boards):
        roles = {}
        for role_index, role in enumerate(ROLES):
            if role == "boot_app0" and shared is not None:
                roles[role] = shared
            else:
                roles[role] = _companion(role, marker + index * 10 + role_index)
        install[board] = roles
    return install


def _product(doc: dict, product: str) -> dict:
    return next(item for item in doc["products"] if item["id"] == product)


class InstallCompanionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.catalog = load_catalog()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_publish_without_companions_omits_install_and_validates(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.3",
            _bridge_bins(1),
            set_latest=True,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        validate_feed(self.root, self.catalog)
        version_doc = json.loads((self.root / "BRIDGE" / "v1.2.3" / "index.json").read_text())
        for artifact in version_doc["artifacts"]:
            self.assertNotIn("install", artifact)
        sums = (self.root / "BRIDGE" / "v1.2.3" / "SHA256SUMS").read_text()
        self.assertIn("ATOM_S3.bin", sums)
        self.assertNotIn("bootloader", sums)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("- Full-install files: `ATOM_S3` no, `ATOM_S3_R` no", readme)

    def test_publish_with_companions_records_install_and_checksums(self) -> None:
        install = _install_for(("ATOM_S3", "ATOM_S3_R"), 20)
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.3.0",
            _bridge_bins(3),
            set_latest=True,
            install=install,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        validate_feed(self.root, self.catalog)
        version_doc = json.loads((self.root / "BRIDGE" / "v1.3.0" / "index.json").read_text())
        latest_doc = json.loads((self.root / "BRIDGE" / "latest" / "index.json").read_text())
        root_doc = json.loads((self.root / "index.json").read_text())
        self._assert_install(version_doc, install)
        self._assert_install(latest_doc, install)
        self._assert_install(root_doc["latest"]["BRIDGE"], install)
        version_entry = next(item for item in _product(root_doc, "BRIDGE")["versions"] if item["folder"] == "v1.3.0")
        self._assert_install(version_entry, install)
        names = [
            line.split("  ", 1)[1]
            for line in (self.root / "BRIDGE" / "v1.3.0" / "SHA256SUMS").read_text().splitlines()
        ]
        self.assertEqual(
            names,
            [
                "ATOM_S3.bin",
                "ATOM_S3.boot_app0.bin",
                "ATOM_S3.bootloader.bin",
                "ATOM_S3.partitions.bin",
                "ATOM_S3_R.bin",
                "ATOM_S3_R.boot_app0.bin",
                "ATOM_S3_R.bootloader.bin",
                "ATOM_S3_R.partitions.bin",
            ],
        )
        root_sums = (self.root / "SHA256SUMS").read_text()
        for name in names:
            self.assertIn(f"BRIDGE/v1.3.0/{name}", root_sums)
            self.assertIn(f"BRIDGE/latest/{name}", root_sums)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` yes", readme)

    def test_one_board_may_omit_companions(self) -> None:
        install = _install_for(("ATOM_S3",), 30)
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.3.1",
            _bridge_bins(4),
            set_latest=True,
            install=install,
        )
        validate_feed(self.root, self.catalog)
        doc = json.loads((self.root / "BRIDGE" / "v1.3.1" / "index.json").read_text())
        by_board = {item["board"]: item for item in doc["artifacts"]}
        self.assertIn("install", by_board["ATOM_S3"])
        self.assertNotIn("install", by_board["ATOM_S3_R"])
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("- Full-install files: `ATOM_S3` yes, `ATOM_S3_R` no", readme)

    def test_partial_install_set_is_refused(self) -> None:
        install = {
            "ATOM_S3": {
                "bootloader": _companion("bootloader", 1),
                "partitions": _companion("partitions", 2),
            },
            "ATOM_S3_R": _install_for(("ATOM_S3_R",), 4)["ATOM_S3_R"],
        }
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "BRIDGE",
                "1.3.2",
                _bridge_bins(5),
                set_latest=False,
                install=install,
            )
        self.assertIn("boot_app0", str(caught.exception))
        self.assertFalse((self.root / "BRIDGE" / "v1.3.2").exists())

    def test_shared_boot_app0_bytes_are_allowed(self) -> None:
        install = _install_for(("ATOM_S3", "ATOM_S3_R"), 40, shared_boot_app0=True)
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.3.3",
            _bridge_bins(6),
            set_latest=False,
            install=install,
        )
        validate_feed(self.root, self.catalog)
        doc = json.loads((self.root / "BRIDGE" / "v1.3.3" / "index.json").read_text())
        digests = [item["install"]["boot_app0"]["sha256"] for item in doc["artifacts"]]
        self.assertEqual(digests[0], digests[1])

    def test_stm32_refuses_install_companions(self) -> None:
        binaries = {
            "RAK3172_TX": (_stm(2), "tx.bin"),
            "RAK3172_RX": (_stm(3), "rx.bin"),
        }
        with self.assertRaises(FeedError):
            apply_publish(
                self.root,
                self.catalog,
                "P1",
                "2.1.0",
                binaries,
                set_latest=False,
                install=_install_for(("RAK3172_TX", "RAK3172_RX"), 1),
            )
        self.assertFalse((self.root / "P1" / "v2.1.0").exists())

    def test_bootloader_without_esp_header_is_refused(self) -> None:
        bad = bytearray(_companion("bootloader", 1))
        bad[0] = 0x00
        install = _install_for(("ATOM_S3", "ATOM_S3_R"), 50)
        install["ATOM_S3"]["bootloader"] = bytes(bad)
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "BRIDGE",
                "1.3.4",
                _bridge_bins(8),
                set_latest=False,
                install=install,
            )
        self.assertIn("0xE9", str(caught.exception))

    def test_rollback_copies_companions(self) -> None:
        older = _install_for(("ATOM_S3", "ATOM_S3_R"), 60)
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.4.0",
            _bridge_bins(9),
            set_latest=False,
            install=older,
        )
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.4.1",
            _bridge_bins(11),
            set_latest=True,
        )
        version_dir = self.root / "BRIDGE" / "v1.4.0"
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in version_dir.glob("*.bin")}
        rollback_latest(self.root, self.catalog, "BRIDGE", "v1.4.0")
        validate_feed(self.root, self.catalog)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in version_dir.glob("*.bin")}
        self.assertEqual(before, after)
        latest = json.loads((self.root / "BRIDGE" / "latest" / "index.json").read_text())
        self._assert_install(latest, older)
        self.assertTrue((self.root / "BRIDGE" / "latest" / "ATOM_S3.bootloader.bin").is_file())
        self.assertGreater((self.root / "BRIDGE" / "latest" / "ATOM_S3_R.partitions.bin").stat().st_size, 0)

    def test_cli_apply_picks_up_companion_filenames(self) -> None:
        from_dir = self.root / "in"
        from_dir.mkdir()
        for name, marker in (("ATOM_S3.bin", 5), ("ATOM_S3_R.bin", 6)):
            (from_dir / name).write_bytes(_esp(marker))
        install = _install_for(("ATOM_S3", "ATOM_S3_R"), 70)
        for board, roles in install.items():
            for role, data in roles.items():
                (from_dir / f"{board}.{role}.bin").write_bytes(data)
        feed = self.root / "feed"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "apply",
                "--root",
                str(feed),
                "--product",
                "BRIDGE",
                "--version",
                "1.5.0",
                "--from-dir",
                str(from_dir),
                "--set-latest",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        validate_feed(feed, self.catalog)
        doc = json.loads((feed / "BRIDGE" / "v1.5.0" / "index.json").read_text())
        self._assert_install(doc, install)

    def test_cli_partial_companion_set_fails(self) -> None:
        from_dir = self.root / "in"
        from_dir.mkdir()
        for name, marker in (("ATOM_S3.bin", 5), ("ATOM_S3_R.bin", 6)):
            (from_dir / name).write_bytes(_esp(marker))
        (from_dir / "ATOM_S3.bootloader.bin").write_bytes(_companion("bootloader", 1))
        feed = self.root / "feed"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "apply",
                "--root",
                str(feed),
                "--product",
                "BRIDGE",
                "--version",
                "1.5.1",
                "--from-dir",
                str(from_dir),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("incomplete", completed.stderr)
        self.assertFalse((feed / "BRIDGE" / "v1.5.1").exists())

    def test_meter_publishes_four_boards_under_its_own_folder(self) -> None:
        spec = self.catalog["products"]["METER"]
        self.assertEqual(spec["family"], "esp32")
        self.assertEqual(spec["chip"], "esp32-s3")
        self.assertEqual(spec["flash_mode"], "qio")
        self.assertEqual(spec["partition_csv"], "partitions/ota_8MB.csv")
        self.assertEqual(spec["targets"], ["AtomS3", "AtomS3R"])
        self.assertEqual([board for board in spec["boards"]], list(METER_BOARDS))
        self.assertEqual([info["envs"] for info in spec["boards"].values()], [[board] for board in METER_BOARDS])
        self.assertEqual(self.catalog.get("aliases"), {})
        install = _install_for(METER_BOARDS, 80, shared_boot_app0=True)
        apply_publish(
            self.root,
            self.catalog,
            "METER",
            "1.0.0",
            _meter_bins(12),
            set_latest=True,
            install=install,
            source={"kind": "directory", "repository": "opelpanfan/OPF-LORA-METER"},
        )
        validate_feed(self.root, self.catalog)
        self.assertTrue((self.root / "METER" / "v1.0.0" / "transmitter.bin").is_file())
        self.assertTrue((self.root / "METER" / "latest" / "receiver_lcd.partitions.bin").is_file())
        root_doc = json.loads((self.root / "index.json").read_text())
        meter = _product(root_doc, "METER")
        self.assertNotIn("alias_of", meter)
        self.assertTrue(meter["latest"]["available"])
        self.assertEqual(sorted(meter["latest"]["boards"]), sorted(METER_BOARDS))
        self.assertEqual(meter["chip"], "esp32-s3")
        self.assertEqual(meter["flash_mode"], "qio")
        self.assertEqual(meter["partition_csv"], "partitions/ota_8MB.csv")
        self._assert_install(meter["latest"], install)
        url = resolve_ota_url(self.catalog, "METER", "transmitter_lcd", "latest")
        self.assertTrue(url.endswith("/METER/latest/transmitter_lcd.bin"))
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("`transmitter` yes", readme)
        self.assertIn("`receiver_lcd` yes", readme)
        with self.assertRaises(FeedError):
            apply_publish(
                self.root,
                self.catalog,
                "METER",
                "1.0.1",
                {"transmitter": (_esp(1), "transmitter.bin")},
                set_latest=False,
            )

    def test_hand_written_partial_folder_fails_validation(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.6.0",
            _bridge_bins(15),
            set_latest=False,
        )
        folder = self.root / "BRIDGE" / "v1.6.0"
        (folder / "ATOM_S3.bootloader.bin").write_bytes(_companion("bootloader", 1))
        with self.assertRaises(FeedError):
            validate_feed(self.root, self.catalog)

    def test_checked_in_feed_stays_valid_without_companions(self) -> None:
        validate_feed(ROOT, load_catalog())
        root_doc = json.loads((ROOT / "index.json").read_text())
        self.assertEqual(root_doc["aliases"], {})
        meter = _product(root_doc, "METER")
        self.assertEqual(meter["family"], "esp32")
        self.assertFalse(meter["latest"]["available"])
        self.assertEqual(meter["versions"], [])
        self.assertNotIn("alias_of", meter)
        self.assertNotIn('"install"', json.dumps(root_doc))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("- Full-install files:", readme)
        self.assertIn("`ATOM_S3` no", readme)
        self.assertIn("`OPF_WS` no", readme)

    def _assert_install(self, document: dict, install: dict) -> None:
        by_board = {item["board"]: item for item in document["artifacts"]}
        for board, roles in install.items():
            recorded = by_board[board]["install"]
            self.assertEqual(list(recorded), list(ROLES))
            for role, data in roles.items():
                record = recorded[role]
                self.assertEqual(record["path"], f"{board}.{role}.bin")
                self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(record["size"], len(data))
                self.assertEqual(record["offset"], OFFSETS[role])


if __name__ == "__main__":
    unittest.main()
