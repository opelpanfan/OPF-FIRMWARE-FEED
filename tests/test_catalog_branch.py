"""Catalog must serve master-grok, never main/master."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

import feedlib  # noqa: E402


class CatalogBranchTests(unittest.TestCase):
    def test_live_catalog_targets_master_grok(self) -> None:
        catalog = feedlib.load_catalog(ROOT / ".github" / "feed-catalog.json")
        self.assertEqual(catalog["branch"], "master-grok")
        self.assertIn("/master-grok", catalog["raw_base"])
        self.assertFalse(catalog["raw_base"].rstrip("/").endswith("/main"))

    def test_main_branch_rejected(self) -> None:
        catalog = json.loads((ROOT / ".github" / "feed-catalog.json").read_text(encoding="utf-8"))
        catalog["branch"] = "main"
        catalog["raw_base"] = "https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main"
        path = ROOT / "tests" / "_tmp_bad_catalog.json"
        try:
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaises(feedlib.FeedError):
                feedlib.load_catalog(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
