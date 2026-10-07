import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))

from feedlib import (
    MIN_ESP,
    FeedError,
    GitHubHTTPError,
    ReleaseNotReady,
    apply_publish,
    load_catalog,
    match_release_assets,
    match_zip_bins,
    normalize_version,
    resolve_ota_url,
    rollback_latest,
    validate_feed,
    validate_image,
    _fetch_release,
)

ROOT = Path(__file__).resolve().parents[1]


def esp(marker: int) -> bytes:
    data = bytearray(MIN_ESP)
    data[0] = 0xE9
    data[-1] = marker
    return bytes(data)


def stm(marker: int) -> bytes:
    data = bytearray(2048)
    data[0] = 0x20
    data[-1] = marker
    return bytes(data)


def bridge_catalog() -> dict:
    return {
        "schema": 1,
        "repository": "opelpanfan/OPF-FIRMWARE-FEED",
        "branch": "main",
        "raw_base": "https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main",
        "aliases": {},
        "products": {
            "BRIDGE": {
                "family": "esp32",
                "ingest": "any",
                "version_label": "prefixed",
                "source_repository": "opelpanfan/OPF-STORAGE-M5-BRIDGE",
                "source_ref": "master-grok",
                "required_boards": ["ATOM_S3", "ATOM_S3_R"],
                "ignored_envs": ["ATOM_S3_DTU", "ATOM_S3_R_DTU"],
                "boards": {
                    "ATOM_S3": {"filename": "ATOM_S3.bin", "envs": ["ATOM_S3"], "required": True},
                    "ATOM_S3_R": {"filename": "ATOM_S3_R.bin", "envs": ["ATOM_S3_R"], "required": True},
                },
            }
        },
    }


class FeedTests(unittest.TestCase):
    def test_version_rejects_junk(self):
        self.assertEqual(normalize_version("v1.2.3"), "1.2.3")
        for bad in ("1.2", "1.2.3-rc1", "01.2.3", "../1.0.0", "latest", ""):
            with self.assertRaises(FeedError):
                normalize_version(bad)

    def test_images_fail_closed(self):
        validate_image("esp32", esp(1), "ok")
        with self.assertRaises(FeedError):
            validate_image("esp32", b"\x00" * MIN_ESP, "bad")
        with self.assertRaises(FeedError):
            validate_image("stm32", esp(1), "esp-as-stm")
        validate_image("stm32", stm(1), "stm")

    def test_partial_publish_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FeedError):
                apply_publish(
                    root,
                    bridge_catalog(),
                    "BRIDGE",
                    "1.2.3",
                    {"ATOM_S3": (esp(1), "firmware.bin")},
                    set_latest=True,
                )
            self.assertFalse((root / "BRIDGE").exists())

    def test_version_folder_is_immutable_and_latest_tracks_the_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = bridge_catalog()
            binaries = {
                "ATOM_S3": (esp(1), "firmware.bin"),
                "ATOM_S3_R": (esp(2), "firmware.bin"),
            }
            apply_publish(root, catalog, "BRIDGE", "1.0.0", binaries, set_latest=True)
            self.assertEqual((root / "BRIDGE/v1.0.0/ATOM_S3.bin").read_bytes(), esp(1))
            self.assertEqual((root / "BRIDGE/latest/ATOM_S3_R.bin").read_bytes(), esp(2))
            changed = {
                "ATOM_S3": (esp(3), "firmware.bin"),
                "ATOM_S3_R": (esp(4), "firmware.bin"),
            }
            with self.assertRaises(FeedError):
                apply_publish(root, catalog, "BRIDGE", "1.0.0", changed, set_latest=True)
            self.assertEqual((root / "BRIDGE/v1.0.0/ATOM_S3.bin").read_bytes(), esp(1))
            apply_publish(root, catalog, "BRIDGE", "1.0.1", changed, set_latest=True)
            self.assertEqual((root / "BRIDGE/latest/ATOM_S3.bin").read_bytes(), esp(3))
            self.assertEqual((root / "BRIDGE/v1.0.0/ATOM_S3.bin").read_bytes(), esp(1))
            before = (root / "BRIDGE/v1.0.1/ATOM_S3_R.bin").read_bytes()
            rollback_latest(root, catalog, "BRIDGE", "v1.0.0")
            self.assertEqual((root / "BRIDGE/latest/ATOM_S3.bin").read_bytes(), esp(1))
            self.assertEqual((root / "BRIDGE/v1.0.1/ATOM_S3_R.bin").read_bytes(), before)

    def test_bridge_feed_boards_are_atom_s3_r_and_atom_s3(self):
        spec = load_catalog()["products"]["BRIDGE"]
        self.assertEqual(spec["required_boards"], ["ATOM_S3_R", "ATOM_S3"])
        self.assertEqual(set(spec["boards"]), {"ATOM_S3_R", "ATOM_S3"})
        self.assertEqual(spec["source_ref"], "master-grok")
        self.assertEqual(spec["board_contract_sha"], "d9ca7a0")
        self.assertNotIn("ATOM_S3_DTU", spec["boards"])
        self.assertNotIn("ATOM_S3_R_DTU", spec["boards"])

    def test_dtu_artifact_is_ignored_and_names_do_not_overlap(self):
        boards = bridge_catalog()["products"]["BRIDGE"]["boards"]
        ignored = ["ATOM_S3_DTU", "ATOM_S3_R_DTU"]
        mapped = match_zip_bins("ATOM_S3", [(".pio/build/ATOM_S3/firmware.bin", esp(1))], boards, ignored)
        self.assertEqual(mapped[0][0], "ATOM_S3")
        mapped_r = match_zip_bins("ATOM_S3_R", [("firmware.bin", esp(2))], boards, ignored)
        self.assertEqual(mapped_r[0][0], "ATOM_S3_R")
        skipped = match_zip_bins(
            "ATOM_S3_R_DTU",
            [("firmware.bin", esp(9))],
            boards,
            ignored,
        )
        self.assertEqual(skipped, [])
        mixed = match_zip_bins(
            "firmware",
            [
                (".pio/build/ATOM_S3/firmware.bin", esp(1)),
                (".pio/build/ATOM_S3_R/firmware.bin", esp(2)),
                (".pio/build/ATOM_S3_R_DTU/firmware.bin", esp(9)),
            ],
            boards,
            ignored,
        )
        self.assertEqual(sorted(item[0] for item in mixed), ["ATOM_S3", "ATOM_S3_R"])

    def test_p1_release_requires_the_pair(self):
        boards = load_catalog()["products"]["P1"]["boards"]
        assets = [
            {"name": "opf-p1-rak3172_transmiter-fw1.0.0.bin", "url": "https://api.github.com/asset/1"},
            {"name": "rak3172_receiver-fw1.0.0.bin", "url": "https://api.github.com/asset/2"},
            {"name": "notes.txt", "url": "https://api.github.com/asset/3"},
        ]
        selected = match_release_assets(assets, boards, None)
        self.assertEqual(set(selected), {"RAK3172_TX", "RAK3172_RX"})
        with self.assertRaises(ReleaseNotReady):
            match_release_assets(assets[:1], boards, None)

    def test_release_retries_until_the_pair_exists(self):
        os.environ["FEED_NO_SLEEP"] = "1"
        calls = {"n": 0}
        boards = load_catalog()["products"]["P1"]["boards"]
        spec = load_catalog()["products"]["P1"]

        def fake_json(url, token):
            calls["n"] += 1
            if calls["n"] < 3:
                raise GitHubHTTPError(404, "missing")
            return {
                "id": 7,
                "target_commitish": "master-grok",
                "assets": [
                    {
                        "name": "opf-p1-rak3172_transmiter-fw1.0.0.bin",
                        "url": "https://api.github.com/repos/opelpanfan/OPF-P1/releases/assets/1",
                        "digest": "sha256:" + __import__("hashlib").sha256(stm(1)).hexdigest(),
                    },
                    {
                        "name": "rak3172_receiver-fw1.0.0.bin",
                        "url": "https://api.github.com/repos/opelpanfan/OPF-P1/releases/assets/2",
                    },
                ],
            }

        def fake_bytes(url, token):
            if url.endswith("/1"):
                return stm(1)
            return stm(2)

        import feedlib

        original_json = feedlib.github_json
        original_bytes = feedlib.github_bytes
        feedlib.github_json = fake_json
        feedlib.github_bytes = fake_bytes
        try:
            binaries, source = _fetch_release(
                "opelpanfan/OPF-P1",
                "1.0.0",
                "v1.0.0",
                boards,
                None,
                "token",
                spec,
                False,
            )
        finally:
            feedlib.github_json = original_json
            feedlib.github_bytes = original_bytes
            os.environ.pop("FEED_NO_SLEEP", None)
        self.assertEqual(calls["n"], 3)
        self.assertEqual(set(binaries), {"RAK3172_TX", "RAK3172_RX"})
        self.assertEqual(source["tag"], "v1.0.0")

    def test_ota_urls_use_main_and_meter_aliases_p1(self):
        catalog = load_catalog()
        url = resolve_ota_url(catalog, "BRIDGE", "ATOM_S3_R", "latest")
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BRIDGE/latest/ATOM_S3_R.bin",
        )
        paired = resolve_ota_url(catalog, "METER", "RAK3172_TX", "v1.0.0")
        self.assertIn("/main/P1/v1.0.0/RAK3172_TX.bin", paired)
        with self.assertRaises(FeedError):
            resolve_ota_url(catalog, "BRIDGE", "RAK3172_TX", "latest")
        with self.assertRaises(FeedError):
            resolve_ota_url(catalog, "BMS", "OPF_WS", "latest", "https://example.com/fw.bin")

    def test_checked_in_feed_matches_manifests(self):
        if not (ROOT / "BRIDGE/latest/ATOM_S3.bin").exists():
            self.skipTest("feed binaries are not in this tree")
        validate_feed(ROOT)
        root_index = json.loads((ROOT / "index.json").read_text())
        bridge = root_index["latest"]["BRIDGE"]
        bms = root_index["latest"]["BMS"]
        self.assertTrue(bridge["available"])
        self.assertEqual(bridge["matched_folder"], "v1.0.11")
        self.assertEqual(bridge["highest_semver_folder"], "v1.0.14")
        self.assertFalse(bridge["highest_semver_is_latest"])
        self.assertEqual(bridge["boards"], ["ATOM_S3", "ATOM_S3_R"])
        self.assertEqual(bridge["board_contract_sha"], "d9ca7a0")
        self.assertIn("after flash", bridge["runtime_config"])
        self.assertEqual(bms["version"], "1.0.2")
        self.assertEqual(bms["matched_folder"], "1.0.2")
        self.assertFalse(root_index["latest"]["P1"]["available"])
        self.assertEqual(root_index["latest"]["METER"]["alias_of"], "P1")
        self.assertFalse(root_index["latest"]["METER"]["available"])
        bms_latest = json.loads((ROOT / "BMS/latest/index.json").read_text())
        self.assertEqual(bms_latest["version"], "1.0.2")
        self.assertEqual(
            bms_latest["files"]["OPF_WS"],
            "https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BMS/latest/OPF_WS.bin",
        )
        bridge_latest = json.loads((ROOT / "BRIDGE/latest/index.json").read_text())
        self.assertEqual(bridge_latest["version"], "v1.0.11")


if __name__ == "__main__":
    unittest.main()
