#!/usr/bin/env python3
"""SCREEN, the OPF CAN dashboard, is accepted without publishing binaries."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

from feedlib import (  # noqa: E402
    APP_OFFSET,
    FeedError,
    apply_publish,
    load_catalog,
    validate_feed,
)

SCRIPT = ROOT / ".github" / "scripts" / "publish_firmware.py"
BOARDS = (
    "ws-4-480",
    "ws-43-800",
    "ws-5-800",
    "ws-5b-1024",
    "ws-7-800",
    "ws-7b-1024",
)
ROLES = ("bootloader", "partitions", "boot_app0")
OFFSETS = {"bootloader": "0x0", "partitions": "0x8000", "boot_app0": "0xe000"}
SOURCE = {
    "kind": "directory",
    "repository": "opelpanfan/OPF-STORAGE-DASH",
    "ref": "refs/heads/master-grok",
}


def _esp(marker: int) -> bytes:
    data = bytearray(64 * 1024)
    data[0] = 0xE9
    data[10] = marker % 256
    data[11] = (marker // 256) % 256
    return bytes(data)


def _companion(role: str, marker: int) -> bytes:
    data = bytearray(256 if role != "factory" else 64 * 1024)
    data[0] = 0xE9 if role in ("bootloader", "factory") else 0xAA
    data[10] = marker % 256
    data[11] = (marker // 256) % 256
    return bytes(data)


def _bins(marker: int) -> dict[str, tuple[bytes, str]]:
    return {board: (_esp(marker + index + 1), f"{board}.bin") for index, board in enumerate(BOARDS)}


def _install(marker: int, *, factory_for: str | None = None) -> dict:
    install = {}
    for index, board in enumerate(BOARDS):
        roles = {role: _companion(role, marker + index * 10 + role_index) for role_index, role in enumerate(ROLES)}
        if board == factory_for:
            roles["factory"] = _companion("factory", marker + 90 + index)
        install[board] = roles
    return install


def _product(doc: dict, product: str) -> dict:
    return next(item for item in doc["products"] if item["id"] == product)


class ScreenCatalogTests(unittest.TestCase):
    def test_catalog_lists_the_waveshare_boards(self) -> None:
        spec = load_catalog()["products"]["SCREEN"]
        self.assertEqual(spec["family"], "esp32")
        self.assertEqual(spec["chip"], "ESP32-S3")
        self.assertEqual(spec["source_repository"], "opelpanfan/OPF-STORAGE-DASH")
        self.assertEqual(spec["source_ref"], "master-grok")
        self.assertTrue(spec["full_flash_required"])
        self.assertEqual(spec["app_offset"], APP_OFFSET)
        self.assertEqual(list(spec["boards"]), list(BOARDS))
        self.assertEqual(spec["boards"]["ws-4-480"]["envs"], ["OPF_WS_CAN_DASH_4"])
        self.assertEqual(spec["boards"]["ws-43-800"]["envs"], ["OPF_WS_CAN_DASH_43"])
        self.assertEqual(spec["boards"]["ws-5-800"]["envs"], ["OPF_WS_CAN_DASH_5"])
        self.assertEqual(spec["boards"]["ws-5-800"]["build_flags"], ["-D OPF_CAN_DASH_RES=800"])
        self.assertEqual(spec["boards"]["ws-5b-1024"]["envs"], ["OPF_WS_CAN_DASH_5"])
        self.assertEqual(spec["boards"]["ws-5b-1024"]["build_flags"], ["-D OPF_CAN_DASH_RES=1024"])
        self.assertTrue(spec["boards"]["ws-5b-1024"]["experimental"])
        self.assertEqual(spec["boards"]["ws-5b-1024"]["label"], "Touch-LCD-5B 1024x600")
        self.assertTrue(spec["boards"]["ws-7-800"]["uart_only"])
        self.assertIn("download-mode", spec["boards"]["ws-7-800"]["note"])
        self.assertTrue(spec["boards"]["ws-7b-1024"]["uart_only"])
        self.assertEqual(spec["boards"]["ws-7b-1024"]["note"], "UART-only")
        self.assertEqual(spec["boards"]["ws-7b-1024"]["build_flags"], ["-D OPF_CAN_DASH_RES=1024"])

    def test_checked_in_tree_has_no_screen_binaries(self) -> None:
        self.assertEqual(list((ROOT / "SCREEN").rglob("*.bin")), [])
        validate_feed(ROOT, load_catalog())


class ScreenPublishTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.catalog = load_catalog()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_publish_records_offsets_flags_and_optional_factory(self) -> None:
        install = _install(20, factory_for="ws-4-480")
        folder = apply_publish(
            self.root,
            self.catalog,
            "SCREEN",
            "v0.0.2",
            _bins(3),
            set_latest=True,
            install=install,
            source={**SOURCE, "tag": "v0.0.2"},
        )
        self.assertEqual(folder, "v0.0.2")
        validate_feed(self.root, self.catalog)
        version_doc = json.loads((self.root / "SCREEN" / "v0.0.2" / "index.json").read_text())
        self.assertTrue(version_doc["full_flash_required"])
        self.assertEqual(version_doc["app_offset"], "0x10000")
        self.assertEqual(version_doc["version"], "v0.0.2")
        by_board = {item["board"]: item for item in version_doc["artifacts"]}
        self.assertEqual(list(by_board), list(BOARDS))
        plain = by_board["ws-43-800"]
        self.assertEqual(plain["offset"], "0x10000")
        self.assertEqual(plain["env"], "OPF_WS_CAN_DASH_43")
        self.assertEqual(plain["label"], "Touch-LCD-4.3B 800x480")
        self.assertNotIn("factory", plain["install"])
        experimental = by_board["ws-5b-1024"]
        self.assertTrue(experimental["experimental"])
        self.assertEqual(experimental["build_flags"], ["-D OPF_CAN_DASH_RES=1024"])
        self.assertEqual(experimental["env"], "OPF_WS_CAN_DASH_5")
        uart = by_board["ws-7-800"]
        self.assertTrue(uart["uart_only"])
        self.assertIn("download-mode", uart["note"])
        uart_b = by_board["ws-7b-1024"]
        self.assertTrue(uart_b["uart_only"])
        self.assertEqual(uart_b["note"], "UART-only")
        factory_board = by_board["ws-4-480"]
        for role, data in install["ws-4-480"].items():
            record = factory_board["install"][role]
            self.assertEqual(record["path"], f"ws-4-480.{role}.bin")
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["offset"], "0x0" if role == "factory" else OFFSETS[role])
        names = (self.root / "SCREEN" / "v0.0.2" / "SHA256SUMS").read_text()
        self.assertIn("ws-4-480.factory.bin", names)
        self.assertIn("ws-4-480.bootloader.bin", names)
        self.assertNotIn("ws-43-800.factory.bin", names)
        root_doc = json.loads((self.root / "index.json").read_text())
        screen = _product(root_doc, "SCREEN")
        self.assertTrue(screen["full_flash_required"])
        self.assertEqual(screen["chip"], "ESP32-S3")
        self.assertEqual(screen["source_ref"], "master-grok")
        self.assertEqual(screen["source_repository"], "opelpanfan/OPF-STORAGE-DASH")
        self.assertEqual([row["id"] for row in screen["catalog_boards"]], list(BOARDS))
        self.assertTrue(root_doc["latest"]["SCREEN"]["full_flash_required"])
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("### SCREEN", readme)
        self.assertIn("Full flash is required.", readme)
        self.assertIn("`ws-5b-1024` yes", readme)

    def test_build_metadata_and_other_branches_are_refused(self) -> None:
        binaries = _bins(8)
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "SCREEN",
                "v0.0.2+9",
                binaries,
                set_latest=False,
                source=SOURCE,
            )
        self.assertIn("plain vX.Y.Z", str(caught.exception))
        self.assertFalse((self.root / "SCREEN").exists())
        for ref in ("refs/heads/main", "refs/heads/master", "main", "master"):
            with self.assertRaises(FeedError) as caught:
                apply_publish(
                    self.root,
                    self.catalog,
                    "SCREEN",
                    "0.0.3",
                    binaries,
                    set_latest=False,
                    source={**SOURCE, "ref": ref},
                )
            self.assertIn("never", str(caught.exception))
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "SCREEN",
                "0.0.3",
                binaries,
                set_latest=False,
                source={**SOURCE, "repository": "opelpanfan/OPF-STORAGE-DASH", "ref": "refs/heads/feature"},
            )
        self.assertIn("master-grok", str(caught.exception))
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "SCREEN",
                "0.0.3",
                binaries,
                set_latest=False,
                source={"kind": "directory", "repository": "example/other", "ref": "refs/heads/master-grok"},
            )
        self.assertIn("OPF-STORAGE-DASH", str(caught.exception))
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "SCREEN",
                "0.0.3",
                binaries,
                set_latest=False,
                source={**SOURCE, "tag": "v0.0.2+3"},
            )
        self.assertIn("+", str(caught.exception))
        self.assertFalse((self.root / "SCREEN" / "v0.0.3").exists())

    def test_shared_env_with_different_resolution_cannot_reuse_bytes(self) -> None:
        binaries = _bins(11)
        binaries["ws-5b-1024"] = binaries["ws-5-800"]
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "SCREEN",
                "0.0.4",
                binaries,
                set_latest=False,
                source=SOURCE,
            )
        self.assertIn("byte-identical", str(caught.exception))

    def test_factory_without_the_trio_is_optional(self) -> None:
        binaries = _bins(15)
        install = {"ws-7b-1024": {"factory": _companion("factory", 4)}}
        apply_publish(
            self.root,
            self.catalog,
            "SCREEN",
            "0.0.5",
            binaries,
            set_latest=False,
            install=install,
            source={**SOURCE, "tag": "v0.0.5"},
        )
        validate_feed(self.root, self.catalog)
        doc = json.loads((self.root / "SCREEN" / "v0.0.5" / "index.json").read_text())
        by_board = {item["board"]: item for item in doc["artifacts"]}
        self.assertEqual(list(by_board["ws-7b-1024"]["install"]), ["factory"])
        self.assertEqual(by_board["ws-7b-1024"]["install"]["factory"]["offset"], "0x0")
        self.assertNotIn("install", by_board["ws-4-480"])
        with self.assertRaises(FeedError) as caught:
            apply_publish(
                self.root,
                self.catalog,
                "SCREEN",
                "0.0.6",
                binaries,
                set_latest=False,
                install={"ws-4-480": {"bootloader": _companion("bootloader", 1), "factory": _companion("factory", 2)}},
                source=SOURCE,
            )
        self.assertIn("boot_app0", str(caught.exception))

    def test_cli_apply_accepts_a_plain_tag_from_master_grok(self) -> None:
        from_dir = self.root / "in"
        from_dir.mkdir()
        for index, board in enumerate(BOARDS):
            (from_dir / f"{board}.bin").write_bytes(_esp(30 + index))
            for role_index, role in enumerate(ROLES):
                (from_dir / f"{board}.{role}.bin").write_bytes(_companion(role, 40 + index * 5 + role_index))
        (from_dir / "ws-5-800.factory.bin").write_bytes(_companion("factory", 77))
        feed = self.root / "feed"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "apply",
                "--root",
                str(feed),
                "--product",
                "SCREEN",
                "--version",
                "v0.0.2",
                "--from-dir",
                str(from_dir),
                "--set-latest",
            ],
            check=False,
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "FEED_SOURCE_KIND": "workflow",
                "GITHUB_REF": "refs/tags/v0.0.2",
                "GITHUB_REF_NAME": "v0.0.2",
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("published v0.0.2", completed.stdout)
        doc = json.loads((feed / "SCREEN" / "v0.0.2" / "index.json").read_text())
        five = next(item for item in doc["artifacts"] if item["board"] == "ws-5-800")
        self.assertEqual(five["offset"], "0x10000")
        self.assertEqual(five["install"]["factory"]["offset"], "0x0")
        self.assertEqual(five["install"]["partitions"]["offset"], "0x8000")
        self.assertEqual(doc["source"]["repository"], "opelpanfan/OPF-STORAGE-DASH")
        self.assertEqual(doc["source"]["tag"], "v0.0.2")
        refused = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "apply",
                "--root",
                str(self.root / "refused"),
                "--product",
                "SCREEN",
                "--version",
                "v0.0.2+4",
                "--from-dir",
                str(from_dir),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("plain vX.Y.Z", refused.stderr)
        self.assertFalse((self.root / "refused" / "SCREEN").exists())


if __name__ == "__main__":
    unittest.main()
