import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))

from feedlib import (
    MIN_ESP,
    FeedError,
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
            index = json.loads((root / "index.json").read_text())
            versions = index["products"][0]["versions"]
            self.assertEqual([item["folder"] for item in versions], ["v1.0.1", "v1.0.0"])
            self.assertEqual(versions[1]["sha256"]["ATOM_S3"], hashlib.sha256(esp(1)).hexdigest())
            self.assertEqual(versions[1]["artifacts"][0]["sha256"], versions[1]["sha256"]["ATOM_S3"])
            self.assertEqual(index["latest"]["BRIDGE"]["matched_folder"], "v1.0.0")
            self.assertEqual(index["latest"]["BRIDGE"]["highest_semver_folder"], "v1.0.1")
            self.assertFalse(index["latest"]["BRIDGE"]["highest_semver_is_latest"])

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

    def test_p1_v101_release_asset_names_map_tx_and_rx(self):
        boards = load_catalog()["products"]["P1"]["boards"]
        assets = [
            {"name": "opf-p1-rak3172_transmiter-fw6.bin", "url": "https://api.github.com/asset/1"},
            {"name": "opf-p1-rak3172_receiver-fw6.bin", "url": "https://api.github.com/asset/2"},
            {"name": "opf-p1-rak3172_transmiter-fw6.elf", "url": "https://api.github.com/asset/3"},
            {"name": "opf-p1-rak3172_receiver-fw6.elf", "url": "https://api.github.com/asset/4"},
        ]
        selected = match_release_assets(assets, boards, None)
        self.assertEqual(selected["RAK3172_TX"]["name"], "opf-p1-rak3172_transmiter-fw6.bin")
        self.assertEqual(selected["RAK3172_RX"]["name"], "opf-p1-rak3172_receiver-fw6.bin")
        folded = [
            {"name": "OPF-P1-RAK3172_TRANSMITER-FW6.BIN", "url": "https://api.github.com/asset/1"},
            {"name": "OPF-P1-RAK3172_RECEIVER-FW6.BIN", "url": "https://api.github.com/asset/2"},
        ]
        selected = match_release_assets(folded, boards, None)
        self.assertEqual(set(selected), {"RAK3172_TX", "RAK3172_RX"})
        with self.assertRaises(FeedError):
            match_release_assets(assets + [{"name": "bootloader.bin", "url": "https://api.github.com/asset/9"}], boards, None)

    def test_set_latest_false_writes_only_the_version_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = load_catalog()
            binaries = {
                "RAK3172_TX": (stm(1), "opf-p1-rak3172_transmiter-fw6.bin"),
                "RAK3172_RX": (stm(2), "opf-p1-rak3172_receiver-fw6.bin"),
            }
            folder = apply_publish(
                root,
                catalog,
                "P1",
                "v1.0.1",
                binaries,
                set_latest=False,
                source={"kind": "release", "repository": "opelpanfan/OPF-P1", "tag": "v1.0.1"},
            )
            self.assertEqual(folder, "v1.0.1")
            self.assertTrue((root / "P1/v1.0.1/RAK3172_TX.bin").is_file())
            self.assertFalse((root / "P1/latest").exists())
            index = json.loads((root / "index.json").read_text())
            products = {item["id"]: item for item in index["products"]}
            self.assertEqual(products["P1"]["versions"][0]["folder"], "v1.0.1")
            self.assertIn("RAK3172_RX", products["P1"]["versions"][0]["sha256"])
            self.assertFalse(index["latest"]["P1"]["available"])
            apply_publish(
                root,
                catalog,
                "P1",
                "1.0.1",
                binaries,
                set_latest=True,
                source={"kind": "release", "repository": "opelpanfan/OPF-P1", "tag": "v1.0.1"},
            )
            self.assertEqual((root / "P1/latest/RAK3172_RX.bin").read_bytes(), stm(2))
            self.assertEqual((root / "P1/v1.0.1/RAK3172_TX.bin").read_bytes(), stm(1))
            index = json.loads((root / "index.json").read_text())
            self.assertTrue(index["latest"]["P1"]["available"])
            self.assertEqual(index["latest"]["P1"]["highest_semver_folder"], "v1.0.1")
            self.assertTrue(index["latest"]["P1"]["highest_semver_is_latest"])

    def test_feed_has_no_action_that_pulls_private_releases(self):
        import feedlib

        self.assertFalse(hasattr(feedlib, "ingest_from_env"))
        self.assertFalse(hasattr(feedlib, "github_json"))
        self.assertFalse(hasattr(feedlib, "github_bytes"))
        script = (ROOT / ".github/scripts/publish_firmware.py").read_text()
        self.assertNotIn("ingest", script)
        self.assertNotIn("SOURCE_READ_TOKEN", script)
        workflows = ROOT / ".github/workflows"
        workflow_files = list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml")) if workflows.exists() else []
        self.assertEqual(workflow_files, [])
        for path in (ROOT / ".github").rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".yml", ".yaml"}:
                continue
            body = path.read_text()
            self.assertNotIn("secrets.", body)
            self.assertNotIn("repository_dispatch", body)
            self.assertNotIn("api.github.com", body)
            self.assertNotIn("SOURCE_READ_TOKEN", body)

    def test_publish_docs_tell_sources_to_push(self):
        text = (ROOT / "docs/publishing.md").read_text()
        readme = (ROOT / "README.md").read_text()
        for body in (text, readme):
            self.assertIn("FW_FEED_PUSH_TOKEN", body)
            self.assertIn("SOURCE_READ_TOKEN", body)
            self.assertNotIn("repository_dispatch", body)
            self.assertNotIn("FEED_DISPATCH_TOKEN", body)
        self.assertIn("does not download", text)
        self.assertIn("No `SOURCE_READ_TOKEN`", text)
        self.assertIn("passive", text.lower())
        self.assertIn("python3 .github/scripts/publish_firmware.py validate", text)

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
        self.assertEqual(bridge["version"], "v1.0.1")
        self.assertEqual(bridge["matched_folder"], "v1.0.1")
        self.assertEqual(bridge["matches_folders"], ["v1.0.1"])
        self.assertEqual(bridge["highest_semver_folder"], "v1.0.14")
        self.assertFalse(bridge["highest_semver_is_latest"])
        self.assertEqual(bridge["boards"], ["ATOM_S3", "ATOM_S3_R"])
        self.assertEqual(bridge["board_contract_sha"], "d9ca7a0")
        self.assertIn("after flash", bridge["runtime_config"])
        self.assertTrue(all("/BRIDGE/latest/" in item["url"] for item in bridge["artifacts"]))
        self.assertEqual(bms["version"], "1.0.1")
        self.assertEqual(bms["matched_folder"], "v1.0.1")
        self.assertEqual(bms["matches_folders"], ["v1.0.1"])
        self.assertEqual(bms["highest_semver_folder"], "v1.0.5")
        self.assertFalse(bms["highest_semver_is_latest"])
        self.assertTrue(all("/BMS/latest/" in item["url"] for item in bms["artifacts"]))
        p1 = root_index["latest"]["P1"]
        self.assertTrue(p1["available"])
        self.assertEqual(p1["version"], "v1.0.1")
        self.assertEqual(p1["matched_folder"], "v1.0.1")
        self.assertEqual(p1["flash_as_pair"], ["RAK3172_TX", "RAK3172_RX"])
        self.assertTrue(all("/P1/latest/" in item["url"] for item in p1["artifacts"]))
        self.assertEqual(root_index["latest"]["METER"]["alias_of"], "P1")
        self.assertTrue(root_index["latest"]["METER"]["available"])
        products = {item["id"]: item for item in root_index["products"]}
        self.assertEqual([item["folder"] for item in products["P1"]["versions"]], ["v1.0.1"])
        self.assertEqual(products["METER"]["versions"], [])
        self.assertNotIn("note", products["P1"])
        for product_id in ("BMS", "BRIDGE", "P1"):
            product_dir = ROOT / product_id
            folders = sorted(path.name for path in product_dir.iterdir() if path.is_dir() and path.name != "latest")
            listed = products[product_id]["versions"]
            self.assertEqual(sorted(item["folder"] for item in listed), folders)
            self.assertIn("v1.0.1", folders)
            for item in listed:
                self.assertTrue(item["artifacts"])
                self.assertEqual(
                    item["sha256"],
                    {artifact["board"]: artifact["sha256"] for artifact in item["artifacts"]},
                )
        self.assertTrue((ROOT / "BRIDGE/v1.0.1/ATOM_S3.bin").is_file())
        self.assertTrue((ROOT / "BRIDGE/v1.0.1/ATOM_S3_R.bin").is_file())
        self.assertEqual(
            (ROOT / "BRIDGE/v1.0.1/ATOM_S3_R.bin").read_bytes(),
            (ROOT / "BRIDGE/latest/ATOM_S3_R.bin").read_bytes(),
        )
        bridge_v101 = next(item for item in products["BRIDGE"]["versions"] if item["folder"] == "v1.0.1")
        self.assertEqual(bridge_v101["sha256"], bridge["sha256"])
        sums = (ROOT / "SHA256SUMS").read_text()
        self.assertIn("BMS/v1.0.1/OPF_WS.bin", sums)
        self.assertIn("BMS/master_ws_redesign/OPF_WS.bin", sums)
        self.assertIn("BRIDGE/v1.0.1/ATOM_S3_R.bin", sums)
        self.assertIn("BRIDGE/v1.0.14/ATOM_S3.bin", sums)
        self.assertIn("BMS/latest/OPF_WS.bin", sums)
        self.assertIn("BRIDGE/latest/ATOM_S3_R.bin", sums)
        self.assertIn("P1/v1.0.1/RAK3172_TX.bin", sums)
        self.assertIn("P1/latest/RAK3172_RX.bin", sums)
        bms_latest = json.loads((ROOT / "BMS/latest/index.json").read_text())
        self.assertEqual(bms_latest["version"], "1.0.1")
        self.assertEqual(
            bms_latest["files"]["OPF_WS"],
            "https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/main/BMS/latest/OPF_WS.bin",
        )
        bridge_latest = json.loads((ROOT / "BRIDGE/latest/index.json").read_text())
        self.assertEqual(bridge_latest["version"], "v1.0.1")
        p1_latest = json.loads((ROOT / "P1/latest/index.json").read_text())
        self.assertEqual(p1_latest["version"], "v1.0.1")
        self.assertEqual(
            (ROOT / "P1/v1.0.1/RAK3172_TX.bin").read_bytes(),
            (ROOT / "P1/latest/RAK3172_TX.bin").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "P1/v1.0.1/RAK3172_RX.bin").read_bytes(),
            (ROOT / "P1/latest/RAK3172_RX.bin").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
