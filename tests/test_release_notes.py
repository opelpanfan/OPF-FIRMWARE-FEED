#!/usr/bin/env python3
"""Release-notes contract for the passive firmware feed."""

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
    MAX_RELEASE_NOTES,
    FeedError,
    apply_publish,
    attach_release_notes,
    load_catalog,
    rollback_latest,
    validate_feed,
    write_manifests,
)

SCRIPT = ROOT / ".github" / "scripts" / "publish_firmware.py"
NOTES = "# 1.2.3\n\n- Bridge channel fix.\n- Added café mode.\n"


def _esp(marker: int) -> bytes:
    data = bytearray(64 * 1024)
    data[0] = 0xE9
    data[10] = marker
    return bytes(data)


def _stm(marker: int) -> bytes:
    data = bytearray(1024)
    data[0] = 1 if marker == 0xE9 else marker
    data[20] = marker
    return bytes(data)


def _bridge_bins(marker: int) -> dict[str, tuple[bytes, str]]:
    return {
        "ATOM_S3": (_esp(marker), "ATOM_S3.bin"),
        "ATOM_S3_R": (_esp(marker + 1), "ATOM_S3_R.bin"),
    }


def _bin_identity(folder: Path) -> dict[str, tuple[int, int, str]]:
    identity = {}
    for path in folder.glob("*.bin"):
        stat = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        identity[path.name] = (stat.st_mtime_ns, stat.st_ino, digest)
    return identity


def _product(doc: dict, product: str) -> dict:
    return next(item for item in doc["products"] if item["id"] == product)


class ReleaseNotesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.catalog = load_catalog()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_publish_without_notes_omits_fields(self) -> None:
        folder = apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.3",
            _bridge_bins(1),
            set_latest=True,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        validate_feed(self.root, self.catalog)
        self.assertEqual(folder, "v1.2.3")
        self.assertFalse((self.root / "BRIDGE" / "v1.2.3" / "RELEASE_NOTES.md").exists())
        self.assertFalse((self.root / "BRIDGE" / "latest" / "RELEASE_NOTES.md").exists())
        version_doc = json.loads((self.root / "BRIDGE" / "v1.2.3" / "index.json").read_text())
        latest_doc = json.loads((self.root / "BRIDGE" / "latest" / "index.json").read_text())
        root_doc = json.loads((self.root / "index.json").read_text())
        self.assertNotIn("release_notes", version_doc)
        self.assertNotIn("release_notes_url", version_doc)
        self.assertNotIn("release_notes", latest_doc)
        self.assertNotIn("release_notes", root_doc["latest"]["BRIDGE"])
        version = next(item for item in _product(root_doc, "BRIDGE")["versions"] if item["folder"] == "v1.2.3")
        self.assertNotIn("release_notes", version)
        sums = (self.root / "BRIDGE" / "v1.2.3" / "SHA256SUMS").read_text()
        self.assertIn("ATOM_S3.bin", sums)
        self.assertNotIn("RELEASE_NOTES", sums)

    def test_publish_with_notes_text_fills_indexes(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.3",
            _bridge_bins(3),
            set_latest=True,
            release_notes=NOTES.strip(),
            source={"kind": "directory", "repository": "example/bridge"},
        )
        validate_feed(self.root, self.catalog)
        self._assert_notes(self.root, "BRIDGE", "v1.2.3", NOTES if NOTES.endswith("\n") else NOTES + "\n")

    def test_publish_with_notes_file_and_cli(self) -> None:
        from_dir = self.root / "in"
        from_dir.mkdir()
        for name, marker in (("ATOM_S3.bin", 5), ("ATOM_S3_R.bin", 6)):
            (from_dir / name).write_bytes(_esp(marker))
        notes_path = self.root / "notes.md"
        notes_path.write_bytes(NOTES.encode("utf-8"))
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
                "1.2.4",
                "--from-dir",
                str(from_dir),
                "--set-latest",
                "--release-notes-file",
                str(notes_path),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        validate_feed(feed, self.catalog)
        self._assert_notes(feed, "BRIDGE", "v1.2.4", NOTES)

    def test_attach_notes_does_not_rewrite_bins_and_mirrors_latest(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.5",
            _bridge_bins(8),
            set_latest=True,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        version_dir = self.root / "BRIDGE" / "v1.2.5"
        latest_dir = self.root / "BRIDGE" / "latest"
        before_version = _bin_identity(version_dir)
        before_latest = _bin_identity(latest_dir)
        attach_release_notes(
            self.root,
            self.catalog,
            "BRIDGE",
            "v1.2.5",
            release_notes="## testing material\n\nShipped without notes.\n",
        )
        validate_feed(self.root, self.catalog)
        self.assertEqual(_bin_identity(version_dir), before_version)
        self.assertEqual(_bin_identity(latest_dir), before_latest)
        text = (version_dir / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        self.assertEqual((latest_dir / "RELEASE_NOTES.md").read_text(encoding="utf-8"), text)
        self._assert_notes(self.root, "BRIDGE", "v1.2.5", text)

    def test_attach_notes_cli_and_idempotent_refuse_edit(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.6",
            _bridge_bins(11),
            set_latest=False,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "attach-notes",
                "--root",
                str(self.root),
                "--product",
                "BRIDGE",
                "--version",
                "1.2.6",
                "--release-notes",
                "first notes\n",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        notes_path = self.root / "BRIDGE" / "v1.2.6" / "RELEASE_NOTES.md"
        first = notes_path.read_bytes()
        again = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "attach-notes",
                "--root",
                str(self.root),
                "--product",
                "BRIDGE",
                "--folder",
                "v1.2.6",
                "--release-notes",
                "first notes\n",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(notes_path.read_bytes(), first)
        changed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "attach-notes",
                "--root",
                str(self.root),
                "--product",
                "BRIDGE",
                "--folder",
                "v1.2.6",
                "--release-notes",
                "different notes\n",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("cannot be changed", changed.stderr)
        self.assertEqual(notes_path.read_bytes(), first)
        self.assertFalse((self.root / "BRIDGE" / "latest" / "RELEASE_NOTES.md").exists())

    def test_attach_does_not_copy_notes_onto_a_different_latest(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.0.0",
            _bridge_bins(21),
            set_latest=False,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.0.1",
            _bridge_bins(23),
            set_latest=True,
            release_notes="latest notes\n",
            source={"kind": "directory", "repository": "example/bridge"},
        )
        latest_before = (self.root / "BRIDGE" / "latest" / "RELEASE_NOTES.md").read_bytes()
        bins_before = _bin_identity(self.root / "BRIDGE" / "v1.0.0")
        attach_release_notes(
            self.root,
            self.catalog,
            "BRIDGE",
            "v1.0.0",
            release_notes="older version notes\n",
        )
        self.assertEqual(_bin_identity(self.root / "BRIDGE" / "v1.0.0"), bins_before)
        self.assertEqual((self.root / "BRIDGE" / "latest" / "RELEASE_NOTES.md").read_bytes(), latest_before)
        older = json.loads((self.root / "BRIDGE" / "v1.0.0" / "index.json").read_text())
        self.assertIn("older version notes", older["release_notes"])
        latest = json.loads((self.root / "BRIDGE" / "latest" / "index.json").read_text())
        self.assertIn("latest notes", latest["release_notes"])
        self.assertNotIn("older version notes", latest["release_notes"])

    def test_republish_same_bytes_can_fill_missing_notes(self) -> None:
        binaries = _bridge_bins(31)
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.3.0",
            binaries,
            set_latest=True,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        version_dir = self.root / "BRIDGE" / "v1.3.0"
        before = _bin_identity(version_dir)
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.3.0",
            binaries,
            set_latest=True,
            release_notes="filled on republish\n",
            source={"kind": "directory", "repository": "example/bridge"},
        )
        validate_feed(self.root, self.catalog)
        self.assertEqual(_bin_identity(version_dir), before)
        self.assertEqual(
            (version_dir / "RELEASE_NOTES.md").read_text(encoding="utf-8"),
            (self.root / "BRIDGE" / "latest" / "RELEASE_NOTES.md").read_text(encoding="utf-8"),
        )

    def test_rebuild_accepts_notes_file_and_rejects_unknown_names(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.4.0",
            _bridge_bins(41),
            set_latest=True,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        notes_path = self.root / "BRIDGE" / "v1.4.0" / "RELEASE_NOTES.md"
        notes_path.write_text("hand written\n", encoding="utf-8")
        (self.root / "BRIDGE" / "latest" / "RELEASE_NOTES.md").write_text("hand written\n", encoding="utf-8")
        write_manifests(self.root, self.catalog)
        validate_feed(self.root, self.catalog)
        version_doc = json.loads((self.root / "BRIDGE" / "v1.4.0" / "index.json").read_text())
        self.assertEqual(version_doc["release_notes"], "hand written\n")
        stray = self.root / "BRIDGE" / "v1.4.0" / "EXTRA.txt"
        stray.write_text("nope\n", encoding="utf-8")
        with self.assertRaises(FeedError):
            validate_feed(self.root, self.catalog)
        stray.unlink()
        (self.root / "BRIDGE" / "v1.4.0" / "NOPE.bin").write_bytes(_esp(99))
        with self.assertRaises(FeedError):
            validate_feed(self.root, self.catalog)

    def test_rollback_mirrors_notes_without_editing_the_version_folder(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.5.0",
            _bridge_bins(51),
            set_latest=False,
            release_notes="old channel\n",
            source={"kind": "directory", "repository": "example/bridge"},
        )
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.5.1",
            _bridge_bins(53),
            set_latest=True,
            release_notes="new channel\n",
            source={"kind": "directory", "repository": "example/bridge"},
        )
        version_dir = self.root / "BRIDGE" / "v1.5.0"
        before = _bin_identity(version_dir)
        notes_before = (version_dir / "RELEASE_NOTES.md").read_bytes()
        rollback_latest(self.root, self.catalog, "BRIDGE", "v1.5.0")
        validate_feed(self.root, self.catalog)
        self.assertEqual(_bin_identity(version_dir), before)
        self.assertEqual((version_dir / "RELEASE_NOTES.md").read_bytes(), notes_before)
        latest_doc = json.loads((self.root / "BRIDGE" / "latest" / "index.json").read_text())
        self.assertEqual(latest_doc["release_notes"], "old channel\n")
        self.assertTrue(latest_doc["release_notes_url"].endswith("/BRIDGE/latest/RELEASE_NOTES.md"))

    def test_p1_notes_are_visible_on_meter_alias(self) -> None:
        binaries = {
            "RAK3172_TX": (_stm(2), "tx.bin"),
            "RAK3172_RX": (_stm(3), "rx.bin"),
        }
        apply_publish(
            self.root,
            self.catalog,
            "P1",
            "2.0.0",
            binaries,
            set_latest=True,
            release_notes="pair notes\n",
            source={"kind": "directory", "repository": "example/p1"},
        )
        validate_feed(self.root, self.catalog)
        root_doc = json.loads((self.root / "index.json").read_text())
        self.assertEqual(root_doc["latest"]["P1"]["release_notes"], "pair notes\n")
        self.assertEqual(root_doc["latest"]["METER"]["release_notes"], "pair notes\n")
        self.assertTrue(root_doc["latest"]["METER"]["release_notes_url"].endswith("/P1/latest/RELEASE_NOTES.md"))

    def test_invalid_notes_are_refused(self) -> None:
        binaries = _bridge_bins(61)
        bad = self.root / "bad.md"
        bad.write_bytes(b"\xff\xfe not utf-8")
        with self.assertRaises(FeedError):
            apply_publish(
                self.root,
                self.catalog,
                "BRIDGE",
                "1.6.0",
                binaries,
                set_latest=False,
                release_notes_path=bad,
            )
        self.assertFalse((self.root / "BRIDGE" / "v1.6.0").exists())
        with self.assertRaises(FeedError):
            apply_publish(
                self.root,
                self.catalog,
                "BRIDGE",
                "1.6.1",
                binaries,
                set_latest=False,
                release_notes="x" * (MAX_RELEASE_NOTES + 1),
            )
        with self.assertRaises(FeedError):
            apply_publish(
                self.root,
                self.catalog,
                "BRIDGE",
                "1.6.2",
                binaries,
                set_latest=False,
                release_notes="text",
                release_notes_path=bad,
            )
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.6.3",
            binaries,
            set_latest=False,
            source={"kind": "directory", "repository": "example/bridge"},
        )
        with self.assertRaises(FeedError):
            attach_release_notes(self.root, self.catalog, "BRIDGE", "latest", release_notes="nope\n")
        with self.assertRaises(FeedError):
            attach_release_notes(self.root, self.catalog, "BRIDGE", "v1.6.3", release_notes="   \n")

    def test_checked_in_feed_still_validates_without_notes(self) -> None:
        validate_feed(ROOT, load_catalog())

    def _assert_notes(self, root: Path, product: str, folder: str, text: str) -> None:
        version_path = root / product / folder / "RELEASE_NOTES.md"
        latest_path = root / product / "latest" / "RELEASE_NOTES.md"
        self.assertEqual(version_path.read_text(encoding="utf-8"), text)
        self.assertEqual(latest_path.read_text(encoding="utf-8"), text)
        version_doc = json.loads((root / product / folder / "index.json").read_text())
        latest_doc = json.loads((root / product / "latest" / "index.json").read_text())
        root_doc = json.loads((root / "index.json").read_text())
        version_entry = next(item for item in _product(root_doc, product)["versions"] if item["folder"] == folder)
        for document, url_suffix in (
            (version_doc, f"/{product}/{folder}/RELEASE_NOTES.md"),
            (latest_doc, f"/{product}/latest/RELEASE_NOTES.md"),
            (root_doc["latest"][product], f"/{product}/latest/RELEASE_NOTES.md"),
            (version_entry, f"/{product}/{folder}/RELEASE_NOTES.md"),
            (_product(root_doc, product)["latest"], f"/{product}/latest/RELEASE_NOTES.md"),
        ):
            self.assertEqual(document["release_notes"], text)
            self.assertTrue(document["release_notes_url"].endswith(url_suffix), document["release_notes_url"])
        sums = (root / product / folder / "SHA256SUMS").read_text()
        self.assertNotIn("RELEASE_NOTES", sums)


if __name__ == "__main__":
    unittest.main()
