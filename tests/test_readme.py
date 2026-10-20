#!/usr/bin/env python3
"""README summary regenerated from the firmware folders on disk."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

from feedlib import (  # noqa: E402
    FEED_SUMMARY_END,
    FEED_SUMMARY_START,
    apply_publish,
    load_catalog,
    validate_feed,
    write_manifests,
    write_readme,
)


def _esp(marker: int) -> bytes:
    data = bytearray(64 * 1024)
    data[0] = 0xE9
    data[10] = marker
    return bytes(data)


def _bridge_bins(marker: int) -> dict[str, tuple[bytes, str]]:
    return {
        "ATOM_S3": (_esp(marker), "ATOM_S3.bin"),
        "ATOM_S3_R": (_esp(marker + 1), "ATOM_S3_R.bin"),
    }


class ReadmeSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.catalog = load_catalog()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_publish_writes_summary_and_keeps_text_outside_markers(self) -> None:
        readme = self.root / "README.md"
        readme.write_text("# Keep\n\nOutside.\n", encoding="utf-8")
        notes = "# Title\n\n- First change.\n- Second change.\n- Third change.\n- Fourth ignored.\n"
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.3",
            _bridge_bins(3),
            set_latest=True,
            release_notes=notes,
            source={
                "kind": "directory",
                "repository": "example/bridge",
                "sha": "abcdef1234567890abcdef1234567890abcdef12",
            },
        )
        validate_feed(self.root, self.catalog)
        text = readme.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Keep\n\nOutside.\n"))
        start = text.index(FEED_SUMMARY_START)
        end = text.index(FEED_SUMMARY_END)
        self.assertLess(start, end)
        section = text[start:end]
        self.assertIn("### BRIDGE", section)
        self.assertIn("### BMS", section)
        self.assertIn("### P1", section)
        self.assertIn("### METER", section)
        self.assertLess(section.index("#### `v1.2.3`"), section.index("#### `latest`"))
        self.assertIn("- Date: unknown", section)
        self.assertIn("`abcdef1234567890abcdef1234567890abcdef12` (example/bridge)", section)
        self.assertIn("`ATOM_S3.bin` (65536 bytes, 64.0 KiB)", section)
        self.assertIn("`ATOM_S3_R.bin` (65536 bytes, 64.0 KiB)", section)
        self.assertIn("First change.", section)
        self.assertIn("Second change.", section)
        self.assertIn("Third change.", section)
        self.assertNotIn("Fourth ignored.", section)
        self.assertIn("No version folders.", section)
        self.assertFalse(write_readme(self.root, self.catalog))

    def test_missing_markers_are_added_and_replaced_in_place(self) -> None:
        readme = self.root / "README.md"
        readme.write_text(
            "before\n\n<!-- FEED-SUMMARY:START -->\nold summary\n<!-- FEED-SUMMARY:END -->\n\nafter\n",
            encoding="utf-8",
        )
        self.assertTrue(write_readme(self.root, self.catalog))
        text = readme.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("before\n\n"))
        self.assertTrue(text.endswith("<!-- FEED-SUMMARY:END -->\n\nafter\n"))
        self.assertEqual(text.count(FEED_SUMMARY_START), 1)
        self.assertEqual(text.count(FEED_SUMMARY_END), 1)
        self.assertNotIn("old summary", text)
        self.assertFalse(write_readme(self.root, self.catalog))

    def test_feed_release_notes_override_the_summary(self) -> None:
        apply_publish(
            self.root,
            self.catalog,
            "BRIDGE",
            "1.2.3",
            _bridge_bins(4),
            set_latest=False,
            release_notes="from release notes\n",
            source={"kind": "directory", "repository": "example/bridge"},
        )
        folder = self.root / "BRIDGE" / "v1.2.3"
        (folder / "FEED_RELEASE_NOTES.md").write_text(
            "# Feed\n\nFrom the feed notes file.\nSecond feed line.\n",
            encoding="utf-8",
        )
        write_manifests(self.root, self.catalog)
        validate_feed(self.root, self.catalog)
        section = (self.root / "README.md").read_text(encoding="utf-8").split(FEED_SUMMARY_START, 1)[1]
        self.assertIn("From the feed notes file.", section)
        self.assertIn("Second feed line.", section)
        self.assertNotIn("from release notes", section)
        self.assertNotIn("- Source commit:", section)

    def test_checked_in_readme_summary_is_current(self) -> None:
        self.assertFalse(write_readme(ROOT, load_catalog()))
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# OPF Firmware Feed\n"))
        self.assertLess(text.index("## Release notes"), text.index(FEED_SUMMARY_START))
        self.assertLess(text.index(FEED_SUMMARY_START), text.index(FEED_SUMMARY_END))
        section = text.split(FEED_SUMMARY_START, 1)[1].split(FEED_SUMMARY_END, 1)[0]
        for product in ("BMS", "BRIDGE", "P1", "METER"):
            self.assertIn(f"### {product}", section)
        self.assertIn("#### `v0.0.1`", section)
        self.assertIn("#### `latest`", section)
        self.assertIn("- Full-install files: `ATOM_S3` no, `ATOM_S3_R` no", section)
        self.assertIn("`OPF_WS` no", section)

    def test_workflow_regenerates_on_main_without_pulling_sources(self) -> None:
        workflow = (ROOT / ".github/workflows/feed-readme.yml").read_text(encoding="utf-8")
        self.assertIn("- main", workflow)
        self.assertIn("- master-grok", workflow)
        self.assertIn("paths-ignore:", workflow)
        self.assertIn("README.md", workflow)
        self.assertIn("index.json", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("GITHUB_TOKEN", workflow)
        self.assertIn("github-actions", workflow)
        self.assertIn("publish_firmware.py rebuild", workflow)
        self.assertIn("publish_firmware.py validate", workflow)
        self.assertEqual(workflow.count("actions/checkout@"), 1)
        self.assertNotIn("repository:", workflow)
        self.assertNotIn("SOURCE_READ_TOKEN", workflow)


if __name__ == "__main__":
    unittest.main()
