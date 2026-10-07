"""Fail-closed firmware feed catalog, ingest, and manifest rendering.

Binaries already on ``main`` stay where they are. This module only adds
manifests, checks images, and places new publishes into ``vX.Y.Z`` folders.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from fnmatch import fnmatchcase
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "feed-catalog.json"
API = "https://api.github.com"
SEMVER_RE = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
FOLDER_RE = re.compile(
    r"^(latest|master_ws_redesign|v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*))$"
)
REPO_RE = re.compile(r"^opelpanfan/[A-Za-z0-9._-]+$")
WORKFLOW_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+\.ya?ml$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BOARD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

ESP_MAGIC = 0xE9
MIN_ESP = 64 * 1024
MIN_STM = 1024
MAX_BIN = 8 * 1024 * 1024
ALLOWED_OTA_PREFIXES = (
    "https://raw.githubusercontent.com/opelpanfan/OPF-FIRMWARE-FEED/",
    "https://github.com/opelpanfan/OPF-FIRMWARE-FEED/",
)
SOURCE_KEYS = (
    "kind",
    "repository",
    "ref",
    "sha",
    "tag",
    "run_id",
    "workflow",
    "release_id",
)


class FeedError(Exception):
    """A publish or manifest check failed closed."""


class ReleaseNotReady(FeedError):
    """A release tag exists but both firmware assets are not ready yet."""


class GitHubHTTPError(FeedError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def load_catalog(path: Path | None = None) -> dict:
    catalog_path = path or CATALOG_PATH
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FeedError(f"cannot read feed catalog: {exc}") from exc
    if catalog.get("schema") != 1:
        raise FeedError("feed catalog schema must be 1")
    products = catalog.get("products")
    if not isinstance(products, dict) or not products:
        raise FeedError("feed catalog has no products")
    aliases = catalog.get("aliases") or {}
    if not isinstance(aliases, dict):
        raise FeedError("feed catalog aliases must be an object")
    for alias, target in aliases.items():
        if target not in products:
            raise FeedError(f"alias {alias} points at unknown product {target}")
    for product, spec in products.items():
        if not BOARD_RE.fullmatch(product):
            raise FeedError(f"invalid product id {product!r}")
        boards = spec.get("boards")
        if not isinstance(boards, dict):
            raise FeedError(f"{product} boards must be an object")
        for board, board_spec in boards.items():
            if not BOARD_RE.fullmatch(board):
                raise FeedError(f"invalid board id {product}/{board}")
            filename = board_spec.get("filename")
            if filename != f"{board}.bin":
                raise FeedError(f"{product}/{board} filename must be {board}.bin")
    return catalog


def normalize_version(value: str) -> str:
    text = str(value or "").strip()
    match = SEMVER_RE.fullmatch(text)
    if not match:
        raise FeedError(
            f"version {value!r} is not plain semver X.Y.Z or vX.Y.Z "
            "(no prerelease, build metadata, or leading zeros)"
        )
    return ".".join(match.groups())


def version_folder(semver: str) -> str:
    return f"v{normalize_version(semver)}"


def parse_semver(folder: str) -> str | None:
    match = SEMVER_RE.fullmatch(folder)
    if not match:
        return None
    return ".".join(match.groups())


def version_key(semver: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in semver.split("."))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image(family: str, data: bytes, label: str) -> None:
    if not data:
        raise FeedError(f"{label} is empty")
    if len(data) > MAX_BIN:
        raise FeedError(f"{label} is {len(data)} bytes; limit is {MAX_BIN}")
    if data.startswith(b"\x7fELF"):
        raise FeedError(f"{label} is an ELF file; the feed stores raw .bin images")
    if data.startswith(b"PK\x03\x04"):
        raise FeedError(f"{label} is a zip archive, not a firmware image")
    stripped = data.lstrip()
    if stripped.startswith((b"<", b"{", b"Not Found", b"404")):
        raise FeedError(f"{label} looks like an error page, not firmware")
    if family == "esp32":
        if len(data) < MIN_ESP:
            raise FeedError(f"{label} is {len(data)} bytes; ESP32 images must be at least {MIN_ESP}")
        if data[0] != ESP_MAGIC:
            raise FeedError(f"{label} is missing the ESP32 image header 0xE9")
    elif family == "stm32":
        if len(data) < MIN_STM:
            raise FeedError(f"{label} is {len(data)} bytes; STM32 images must be at least {MIN_STM}")
        if data[0] == ESP_MAGIC:
            raise FeedError(f"{label} has an ESP32 header; refusing it as STM32/P1 firmware")
    elif family == "reserved":
        raise FeedError(f"{label} cannot be published; product family is reserved")
    else:
        raise FeedError(f"{label} has unknown image family {family!r}")


def product_spec(catalog: dict, product: str) -> dict:
    try:
        return catalog["products"][product]
    except KeyError as exc:
        known = ", ".join(catalog["products"])
        raise FeedError(f"unknown product {product!r}; known products: {known}") from exc


def require_publishable(spec: dict, product: str) -> dict:
    boards = spec.get("boards") or {}
    if spec.get("ingest") == "none" or spec.get("family") == "reserved" or not boards:
        raise FeedError(
            f"{product} does not accept firmware publishes"
            + ("; P1 transmitter/receiver binaries belong under P1/" if product == "METER" else "")
        )
    return boards


def raw_url(catalog: dict, product: str, folder: str, filename: str) -> str:
    base = str(catalog["raw_base"]).rstrip("/")
    return f"{base}/{product}/{folder}/{filename}"


def canonical_source(source: dict | None) -> dict | None:
    if not source:
        return None
    cleaned = canonical_source_dict(source)
    return cleaned or None


def canonical_source_dict(source: dict) -> dict:
    out: dict = {}
    for key in SOURCE_KEYS:
        if key not in source:
            continue
        value = source[key]
        if value in (None, ""):
            continue
        if key in ("run_id", "release_id"):
            value = int(value)
        out[key] = value
    for key in sorted(set(source) - set(out)):
        if key in SOURCE_KEYS:
            continue
        value = source[key]
        if value in (None, ""):
            continue
        out[key] = value
    return out


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FeedError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FeedError(f"{path} must be a JSON object")
    return data


def _dump(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def _artifact(board: str, filename: str, digest: str, size: int, url: str, source_filename: str | None) -> dict:
    item = {
        "board": board,
        "filename": filename,
        "sha256": digest,
        "size": size,
        "url": url,
    }
    if source_filename:
        item["source_filename"] = source_filename
    return item


def _folder_documents(
    catalog: dict,
    product: str,
    folder: Path,
    provenance: dict | None,
    source_filenames: dict[str, str],
) -> tuple[dict, str]:
    spec = product_spec(catalog, product)
    boards = spec.get("boards") or {}
    existing = _read_json(folder / "index.json")
    allowed_names = {"index.json", "SHA256SUMS", "README.md"}
    bins = []
    for path in folder.iterdir():
        if path.is_dir() or path.name.startswith("."):
            raise FeedError(f"unexpected path {path.relative_to(folder.parent.parent)}")
        if path.suffix == ".bin":
            bins.append(path)
            continue
        if path.name not in allowed_names:
            raise FeedError(f"unexpected file {path.relative_to(folder.parent.parent)}")
    bins.sort()
    if not bins:
        raise FeedError(f"{folder} has no firmware binaries")

    files: dict[str, str] = {}
    digests: dict[str, str] = {}
    artifacts = []
    sums = []
    preserved_names = {
        item.get("board"): item.get("source_filename")
        for item in existing.get("artifacts") or []
        if isinstance(item, dict) and item.get("source_filename")
    }
    preserved_names.update(source_filenames)

    for path in bins:
        board = path.stem
        if board not in boards:
            known = ", ".join(sorted(boards)) or "(none)"
            raise FeedError(f"unexpected binary {path.name} in {product}/{folder.name}; known boards: {known}")
        if boards[board]["filename"] != path.name:
            raise FeedError(f"{path.name} does not match catalog filename {boards[board]['filename']}")
        data_sha = sha256_file(path)
        size = path.stat().st_size
        validate_image(spec["family"], path.read_bytes(), f"{product}/{folder.name}/{path.name}")
        url = raw_url(catalog, product, folder.name, path.name)
        files[board] = url
        digests[board] = data_sha
        artifacts.append(
            _artifact(board, path.name, data_sha, size, url, preserved_names.get(board))
        )
        sums.append(f"{data_sha}  {path.name}")

    semver = parse_semver(folder.name)
    if folder.name == "latest":
        channel = "latest"
    elif semver:
        channel = "version"
    else:
        channel = "snapshot"
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", folder.name):
            raise FeedError(f"unsafe snapshot folder {folder.name}")

    version_label = existing.get("version")
    if provenance and provenance.get("version_label"):
        version_label = provenance["version_label"]
    elif channel == "version":
        version_label = folder.name
    elif channel == "snapshot":
        version_label = folder.name
    if channel == "latest" and version_label:
        semver = parse_semver(str(version_label))

    source = canonical_source(provenance.get("source") if provenance else None)
    if source is None:
        source = canonical_source(existing.get("source") if isinstance(existing.get("source"), dict) else None)

    document = {
        "schema": 1,
        "product": product,
        "version": version_label,
        "semver": semver,
        "channel": channel,
        "folder": folder.name,
        "files": files,
        "sha256": digests,
        "artifacts": artifacts,
    }
    if spec.get("flash_as_pair"):
        document["flash_as_pair"] = list(spec["flash_as_pair"])
    if source:
        document["source"] = source
    sums_text = "\n".join(sums) + "\n"
    return document, sums_text


def _exact_folder_matches(root: Path, product: str, latest: Path) -> list[str]:
    latest_bins = {
        path.name: sha256_file(path)
        for path in latest.glob("*.bin")
    }
    matches = []
    base = root / product
    for folder in sorted(path for path in base.iterdir() if path.is_dir() and path.name != "latest"):
        bins = list(folder.glob("*.bin"))
        if not bins:
            continue
        folder_bins = {path.name: sha256_file(path) for path in bins}
        if folder_bins == latest_bins:
            matches.append(folder.name)
    return matches


def _available_latest(catalog, product, spec, latest_doc, matches, highest_semver_folder) -> dict:
    if len(matches) == 1:
        matched = matches[0]
    elif matches:
        matched = _prefer_match(matches, latest_doc.get("version"))
    else:
        matched = None
    entry = {
        "product": product,
        "available": True,
        "semver": latest_doc.get("semver"),
        "version": latest_doc.get("version"),
        "matched_folder": matched,
        "matches_folders": matches,
        "highest_semver_folder": highest_semver_folder,
        "highest_semver_is_latest": bool(matched and matched == highest_semver_folder),
        "index_url": raw_url(catalog, product, "latest", "index.json"),
        "boards": [item["board"] for item in latest_doc["artifacts"]],
        "sha256": latest_doc["sha256"],
        "artifacts": latest_doc["artifacts"],
    }
    if spec.get("runtime_config"):
        entry["runtime_config"] = spec["runtime_config"]
    if spec.get("board_contract_sha"):
        entry["board_contract_sha"] = spec["board_contract_sha"]
    if spec.get("flash_as_pair"):
        entry["flash_as_pair"] = list(spec["flash_as_pair"])
        missing = [board for board in spec["flash_as_pair"] if board not in entry["boards"]]
        if missing:
            entry["available"] = False
            entry["note"] = f"incomplete pair, missing {', '.join(missing)}"
    return entry


def _unavailable_latest(product: str, spec: dict, highest_semver_folder: str | None) -> dict:
    entry = {
        "product": product,
        "available": False,
        "semver": None,
        "version": None,
        "matched_folder": None,
        "matches_folders": [],
        "highest_semver_folder": highest_semver_folder,
        "highest_semver_is_latest": False,
        "index_url": None,
        "boards": [],
        "artifacts": [],
        "sha256": {},
    }
    if spec.get("flash_as_pair"):
        entry["flash_as_pair"] = list(spec["flash_as_pair"])
    if product == "P1":
        entry["note"] = "No matched TX/RX release is in the feed yet."
    return entry


def _empty_product(catalog: dict, product: str, spec: dict) -> dict:
    entry = {
        "id": product,
        "family": spec.get("family"),
        "source_repository": spec.get("source_repository"),
        "latest": _unavailable_latest(product, spec, None),
        "versions": [],
    }
    if spec.get("flash_as_pair"):
        entry["flash_as_pair"] = list(spec["flash_as_pair"])
        entry["note"] = (
            "Publish waits for a matched pair of OPF-P1 release assets "
            "opf-p1-rak3172_transmiter-fw*.bin and opf-p1-rak3172_receiver-fw*.bin."
        )
    if spec.get("alias_of"):
        entry["alias_of"] = spec["alias_of"]
    return entry


def render_manifests(
    root: Path,
    catalog: dict | None = None,
    provenance: dict[tuple[str, str], dict] | None = None,
    source_filenames: dict[tuple[str, str, str], str] | None = None,
) -> dict[str, str]:
    """Return the manifest text that must be committed for this tree."""

    catalog = catalog or load_catalog()
    provenance = provenance or {}
    source_filenames = source_filenames or {}
    documents: dict[str, str] = {}
    root_products = []
    root_sums = []

    for product, spec in catalog["products"].items():
        base = root / product
        if not base.exists():
            root_products.append(_empty_product(catalog, product, spec))
            continue

        _reject_unexpected_product_entries(base)
        folder_indexes: dict[str, dict] = {}
        for folder in sorted(path for path in base.iterdir() if path.is_dir()):
            names = {
                board: name
                for (prod, folder_name, board), name in source_filenames.items()
                if prod == product and folder_name == folder.name
            }
            document, sums = _folder_documents(
                catalog,
                product,
                folder,
                provenance.get((product, folder.name)),
                names,
            )
            folder_indexes[folder.name] = document
            documents[f"{product}/{folder.name}/index.json"] = _dump(document)
            documents[f"{product}/{folder.name}/SHA256SUMS"] = sums
            for artifact in document["artifacts"]:
                root_sums.append(
                    f"{artifact['sha256']}  {product}/{folder.name}/{artifact['filename']}"
                )

        latest_doc = folder_indexes.get("latest")
        matches = _exact_folder_matches(root, product, base / "latest") if latest_doc else []
        if latest_doc and matches and not (provenance.get((product, "latest")) or {}).get("version_label"):
            preferred = matches[0] if len(matches) == 1 else _prefer_match(matches, latest_doc.get("version"))
            current = "" if latest_doc.get("version") is None else str(latest_doc.get("version"))
            # Keep a compatible version string when it is the same semver as the
            # byte-identical folder (BMS latest says "1.0.2", not "v1.0.2").
            if parse_semver(current) != parse_semver(preferred):
                latest_doc["version"] = preferred
            latest_doc["semver"] = parse_semver(preferred) or parse_semver(current)
            documents[f"{product}/latest/index.json"] = _dump(latest_doc)

        versions = []
        canonical_folders = []
        legacy_folders = []
        for folder_name, document in folder_indexes.items():
            if folder_name == "latest":
                continue
            semver = document.get("semver")
            if semver and folder_name == version_folder(semver):
                layout = "canonical"
                canonical_folders.append((version_key(semver), folder_name))
            elif semver and folder_name == semver:
                layout = "legacy_unprefixed"
                legacy_folders.append((version_key(semver), folder_name))
            else:
                layout = "snapshot"
            versions.append(
                {
                    "folder": folder_name,
                    "semver": semver,
                    "layout": layout,
                    "channel": document["channel"],
                    "boards": [item["board"] for item in document["artifacts"]],
                    "sha256": dict(document["sha256"]),
                    "index_url": raw_url(catalog, product, folder_name, "index.json"),
                    "artifacts": document["artifacts"],
                }
            )

        versions.sort(key=_version_sort_key)
        canonical_folders.sort()
        legacy_folders.sort()
        semver_folders = canonical_folders + legacy_folders
        semver_folders.sort()
        highest_semver_folder = semver_folders[-1][1] if semver_folders else None
        if latest_doc:
            latest_entry = _available_latest(catalog, product, spec, latest_doc, matches, highest_semver_folder)
        else:
            latest_entry = _unavailable_latest(product, spec, highest_semver_folder)

        entry = {
            "id": product,
            "family": spec.get("family"),
            "source_repository": spec.get("source_repository"),
            "latest": latest_entry,
            "versions": versions,
        }
        if spec.get("source_ref"):
            entry["source_ref"] = spec["source_ref"]
        if spec.get("board_contract_sha"):
            entry["board_contract_sha"] = spec["board_contract_sha"]
        if spec.get("runtime_config"):
            entry["runtime_config"] = spec["runtime_config"]
        if spec.get("flash_as_pair"):
            entry["flash_as_pair"] = list(spec["flash_as_pair"])
        if spec.get("alias_of"):
            entry["alias_of"] = spec["alias_of"]
        if product == "METER":
            entry["note"] = "Alias of P1. Transmitter and receiver bytes are stored under P1/."
        elif product == "P1" and not latest_entry.get("available"):
            entry["note"] = (
                "Publish waits for a matched pair of OPF-P1 release assets "
                "opf-p1-rak3172_transmiter-fw*.bin and opf-p1-rak3172_receiver-fw*.bin "
                "from tag vX.Y.Z (currently v1.0.1) on branch master-grok."
            )
        root_products.append(entry)

    by_id = {entry["id"]: entry for entry in root_products}
    if "P1" in by_id and "METER" in by_id:
        meter_latest = dict(by_id["P1"]["latest"])
        meter_latest["alias_of"] = "P1"
        by_id["METER"]["latest"] = meter_latest
        by_id["METER"]["flash_as_pair"] = list(by_id["P1"].get("flash_as_pair") or [])
        by_id["METER"]["versions"] = []

    latest_map = {entry["id"]: entry["latest"] for entry in root_products}
    root_doc = {
        "schema": 1,
        "repository": catalog["repository"],
        "branch": catalog["branch"],
        "latest_selection": (
            "Read latest.BMS, latest.BRIDGE, and latest.P1. latest.METER aliases latest.P1. "
            "Do not choose the highest semver folder: historical version numbers were not published in order."
        ),
        "aliases": catalog.get("aliases") or {},
        "latest": latest_map,
        "products": root_products,
    }
    documents["index.json"] = _dump(root_doc)
    documents["SHA256SUMS"] = ("\n".join(sorted(root_sums)) + "\n") if root_sums else ""
    return documents


def _prefer_match(matches: list[str], current: str | None) -> str:
    if current in matches:
        return str(current)
    prefixed = [folder for folder in matches if folder.startswith("v")]
    if len(prefixed) == 1:
        return prefixed[0]
    return sorted(matches)[0]


def _version_sort_key(entry: dict) -> tuple:
    semver = entry.get("semver")
    layout = entry.get("layout")
    layout_rank = {"canonical": 0, "legacy_unprefixed": 1, "snapshot": 2}.get(layout, 9)
    if semver:
        return (0, tuple(-part for part in version_key(semver)), layout_rank, entry["folder"])
    return (1, entry["folder"], layout_rank, "")


def _reject_unexpected_product_entries(base: Path) -> None:
    for child in base.iterdir():
        if child.name.startswith("."):
            raise FeedError(f"unexpected hidden path {child}")
        if child.is_file():
            if child.name != "README.md":
                raise FeedError(f"unexpected file {child.relative_to(base.parent)}")
            continue
        if not child.is_dir():
            raise FeedError(f"unexpected path {child}")
        for nested in child.rglob("*"):
            if nested.name.startswith("."):
                raise FeedError(f"unexpected hidden path {nested}")


def write_manifests(
    root: Path,
    catalog: dict | None = None,
    provenance: dict[tuple[str, str], dict] | None = None,
    source_filenames: dict[tuple[str, str, str], str] | None = None,
) -> list[str]:
    documents = render_manifests(root, catalog, provenance, source_filenames)
    written = []
    for relative, text in documents.items():
        if relative == "SHA256SUMS" and text == "":
            path = root / relative
            if path.exists():
                path.unlink()
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            path.write_text(text, encoding="utf-8")
            written.append(relative)
    return written


def validate_feed(root: Path, catalog: dict | None = None) -> None:
    catalog = catalog or load_catalog()
    expected = render_manifests(root, catalog)
    for relative, text in expected.items():
        path = root / relative
        if text == "":
            if path.exists():
                raise FeedError(f"{relative} should not exist")
            continue
        if not path.exists():
            raise FeedError(f"missing manifest {relative}")
        actual = path.read_text(encoding="utf-8")
        if actual != text:
            raise FeedError(f"manifest drift in {relative}; run python3 .github/scripts/publish_firmware.py rebuild")
    for product, spec in catalog["products"].items():
        base = root / product
        if not base.exists():
            continue
        for folder in base.iterdir():
            if not folder.is_dir():
                continue
            for path in folder.glob("*.bin"):
                validate_image(spec["family"], path.read_bytes(), f"{product}/{folder.name}/{path.name}")


def _check_same_bytes(incoming: list[tuple[str, bytes]]) -> None:
    seen: dict[str, str] = {}
    for board, data in incoming:
        digest = sha256_bytes(data)
        if digest in seen:
            raise FeedError(f"{board} and {seen[digest]} are byte-identical; refusing the publish")
        seen[digest] = board


def _stage_file(plan: list[tuple[Path, bytes]], path: Path, data: bytes, overwrite: bool) -> None:
    if path.exists():
        current = path.read_bytes()
        if current == data:
            return
        if not overwrite:
            raise FeedError(
                f"{path} already exists with different bytes; "
                "pass overwrite=true to replace a published version folder"
            )
    plan.append((path, data))


def required_board_ids(spec: dict) -> list[str]:
    explicit = spec.get("required_boards")
    if isinstance(explicit, list) and explicit:
        return list(explicit)
    return [board for board, info in (spec.get("boards") or {}).items() if info.get("required")]


def assert_complete_publish(spec: dict, binaries: dict) -> None:
    missing = [board for board in required_board_ids(spec) if board not in binaries]
    if missing:
        pair = spec.get("flash_as_pair") or []
        if pair:
            raise FeedError(
                "refusing partial P1 publish; TX and RX must be ingested together. "
                f"Missing {', '.join(missing)}"
            )
        raise FeedError(f"refusing partial publish; missing {', '.join(missing)}")
    pair = spec.get("flash_as_pair") or []
    if pair and sorted(pair) != sorted(board for board in pair if board in binaries):
        raise FeedError("TX and RX must be published as one matched pair")


def _replace_tree(directory: Path, files: dict[str, bytes]) -> None:
    """Write a complete binary set, then delete anything else in the directory."""

    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, data in files.items():
        destination = directory / filename
        if destination.exists() and destination.read_bytes() == data:
            written.append(filename)
            continue
        temporary = directory / f".{filename}.tmp"
        temporary.write_bytes(data)
        os.replace(temporary, destination)
        written.append(filename)
    for path in directory.glob("*.bin"):
        if path.name not in files:
            path.unlink()
    if set(written) != set(files):
        raise FeedError(f"incomplete write in {directory}")


def apply_publish(
    root: Path,
    catalog: dict,
    product: str,
    version: str,
    binaries: dict[str, tuple[bytes, str]],
    *,
    set_latest: bool,
    overwrite: bool = False,
    source: dict | None = None,
) -> str:
    """Place a complete release. Version folders are immutable. Returns the folder name.

    ``binaries`` maps board id to ``(data, source_filename)``.
    """

    if overwrite:
        raise FeedError(
            "version folders are immutable. Publish a new version, or point latest at an older folder with rollback."
        )
    spec = product_spec(catalog, product)
    boards = require_publishable(spec, product)
    semver = normalize_version(version)
    if not binaries:
        raise FeedError("publish contains no binaries")
    assert_complete_publish(spec, binaries)

    unknown = sorted(set(binaries) - set(boards))
    if unknown:
        raise FeedError(f"unknown boards for {product}: {', '.join(unknown)}")

    planned: dict[str, bytes] = {}
    incoming = []
    for board, (data, source_filename) in binaries.items():
        validate_image(spec["family"], data, f"{product}/{board}")
        if source_filename and (Path(source_filename).name != source_filename or "/" in source_filename):
            raise FeedError(f"unsafe source filename for {board}")
        planned[boards[board]["filename"]] = data
        incoming.append((board, data))
    _check_same_bytes(incoming)

    folder_name = version_folder(semver)
    label = folder_name if spec.get("version_label") == "prefixed" else semver
    destination = root / product / folder_name
    if destination.exists():
        existing = {path.name: path.read_bytes() for path in destination.glob("*.bin")}
        if existing != planned:
            raise FeedError(
                f"{product}/{folder_name} is immutable and already has different bytes. "
                "Publish a new version. To move the channel without changing history, roll latest back."
            )
    else:
        destination.mkdir(parents=True, exist_ok=False)
        try:
            _replace_tree(destination, planned)
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise

    if set_latest:
        _replace_tree(root / product / "latest", planned)

    provenance: dict[tuple[str, str], dict] = {}
    names: dict[tuple[str, str, str], str] = {}
    source_doc = canonical_source(source)
    touched = [folder_name]
    if set_latest:
        touched.append("latest")
    for folder in touched:
        meta = {"source": source_doc} if source_doc else {}
        if folder == "latest":
            meta["version_label"] = label
        provenance[(product, folder)] = meta
        for board, (_data, source_filename) in binaries.items():
            if source_filename:
                names[(product, folder, board)] = source_filename

    write_manifests(root, catalog, provenance, names)
    return folder_name


def rollback_latest(root: Path, catalog: dict, product: str, folder: str) -> str:
    """Point latest at an existing immutable version folder. Does not change that folder."""

    spec = product_spec(catalog, product)
    require_publishable(spec, product)
    folder_name = (folder or "").strip()
    if folder_name in ("", "latest") or not FOLDER_RE.fullmatch(folder_name):
        raise FeedError("rollback folder must be an existing version folder, not latest")
    if "/" in folder_name or ".." in folder_name:
        raise FeedError("unsafe rollback folder")
    source_dir = root / product / folder_name
    if not source_dir.is_dir():
        raise FeedError(f"{product}/{folder_name} does not exist")
    bins = sorted(source_dir.glob("*.bin"))
    if not bins:
        raise FeedError(f"{product}/{folder_name} has no binaries")
    boards = spec.get("boards") or {}
    present = []
    files: dict[str, bytes] = {}
    for path in bins:
        if path.stem not in boards:
            raise FeedError(f"{path.name} is not a known {product} board")
        data = path.read_bytes()
        validate_image(spec["family"], data, f"{product}/{folder_name}/{path.name}")
        files[path.name] = data
        present.append(path.stem)
    missing = [board for board in required_board_ids(spec) if board not in present]
    if missing:
        raise FeedError(f"cannot point latest at {folder_name}; missing {', '.join(missing)}")
    originals = {path.name: hashlib.sha256(files[path.name]).hexdigest() for path in bins}
    _replace_tree(root / product / "latest", files)
    for path in bins:
        if hashlib.sha256(path.read_bytes()).hexdigest() != originals[path.name]:
            raise FeedError(f"rollback changed {path}, which must stay immutable")
    label = folder_name if spec.get("version_label") == "prefixed" or folder_name.startswith("v") else folder_name
    if spec.get("version_label") == "plain" and parse_semver(folder_name):
        label = parse_semver(folder_name) if not folder_name.startswith("v") else folder_name
    source = {
        "kind": "rollback",
        "repository": catalog.get("repository"),
        "rolled_back_to": folder_name,
    }
    write_manifests(
        root,
        catalog,
        {(product, "latest"): {"source": source, "version_label": label}},
    )
    return folder_name


def canonical_product_id(catalog: dict, product: str) -> str:
    aliases = catalog.get("aliases") or {}
    mapped = aliases.get(product, product)
    if mapped not in catalog.get("products", {}):
        known = ", ".join([*catalog.get("products", {}), *aliases])
        raise FeedError(f"unknown product {product!r}; known products: {known}")
    return mapped


def resolve_ota_url(
    catalog: dict,
    product: str,
    board: str,
    package_version: str,
    firmware_url: str = "",
) -> str:
    override = (firmware_url or "").strip()
    if override:
        return _validate_override_url(override)

    canonical = canonical_product_id(catalog, product)
    spec = product_spec(catalog, canonical)
    boards = spec.get("boards") or {}
    shown = product if product == canonical else f"{product} (alias of {canonical})"
    if not boards:
        raise FeedError(f"{shown} has no firmware")
    if board not in boards:
        known = ", ".join(sorted(boards))
        raise FeedError(f"board {board!r} is not valid for {shown}; known boards: {known}")
    folder = (package_version or "").strip()
    if not FOLDER_RE.fullmatch(folder):
        raise FeedError(
            "package_version must be a folder name: latest, vX.Y.Z, legacy X.Y.Z, or master_ws_redesign"
        )
    if folder == "master_ws_redesign" and canonical != "BMS":
        raise FeedError("master_ws_redesign is a BMS snapshot folder")
    return raw_url(catalog, canonical, folder, boards[board]["filename"])


def _validate_override_url(url: str) -> str:
    if any(char in url for char in ("\n", "\r", "\t", " ")):
        raise FeedError("firmware URL contains whitespace")
    if ".." in url:
        raise FeedError("firmware URL must not contain '..'")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise FeedError("firmware URL must be https with no userinfo, query, or fragment")
    if not any(url.startswith(prefix) for prefix in ALLOWED_OTA_PREFIXES):
        raise FeedError(
            "firmware URL override must point at opelpanfan/OPF-FIRMWARE-FEED "
            "on raw.githubusercontent.com or github.com"
        )
    return url


def host_allowed(hostname: str) -> bool:
    host = (hostname or "").lower().rstrip(".")
    return host == "github.com" or host.endswith(".github.com") or host.endswith(".githubusercontent.com")


def _backoff(attempt: int, kind: str = "http") -> None:
    if os.environ.get("FEED_NO_SLEEP") == "1":
        return
    delays = (2, 4, 8, 16, 16) if kind == "http" else (10, 20, 30, 30, 30)
    time.sleep(delays[min(attempt, len(delays) - 1)])


def _request_bytes(url: str, token: str, accept: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not host_allowed(parsed.hostname or ""):
        raise FeedError(f"refusing URL host {parsed.hostname!r}")
    if parsed.hostname != "api.github.com":
        raise FeedError("downloads must start at api.github.com")

    class Guard(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urllib.parse.urlparse(newurl)
            if target.scheme != "https" or not host_allowed(target.hostname or ""):
                raise FeedError(f"refusing redirect host {target.hostname!r}")
            new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
            if new_req is not None:
                # Authorization is an unredirected header and must not follow to object storage.
                new_req.remove_header("Authorization")
            return new_req

    opener = urllib.request.build_opener(Guard)
    last_error: Exception | None = None
    for attempt in range(5):
        request = urllib.request.Request(url)
        request.add_header("Accept", accept)
        request.add_header("User-Agent", "opf-firmware-feed")
        request.add_header("X-GitHub-Api-Version", "2026-03-10")
        if token:
            request.add_unredirected_header("Authorization", f"Bearer {token}")
        try:
            with opener.open(request, timeout=60) as response:
                return response.read()
        except FeedError:
            raise
        except urllib.error.HTTPError as exc:
            detail = exc.read(300).decode("utf-8", errors="replace").replace("\n", " ")
            hint = ""
            if exc.code in (401, 403):
                hint = " Check SOURCE_READ_TOKEN (contents: read on the private source repo)."
            message = f"GitHub API {exc.code} for {parsed.path}.{hint} {detail}"
            if exc.code in (429, 500, 502, 503, 504) and attempt < 4:
                print(f"retrying GitHub API {exc.code} ({attempt + 1}/5)", file=sys.stderr)
                last_error = GitHubHTTPError(exc.code, message)
                _backoff(attempt, "http")
                continue
            raise GitHubHTTPError(exc.code, message) from exc
        except urllib.error.URLError as exc:
            last_error = FeedError(f"GitHub API request failed: {exc.reason}")
            if attempt < 4:
                print(f"retrying GitHub API connection ({attempt + 1}/5)", file=sys.stderr)
                _backoff(attempt, "http")
                continue
            raise last_error from exc
    raise last_error or FeedError("GitHub API request failed")


def github_json(url: str, token: str) -> dict:
    data = _request_bytes(url, token, "application/vnd.github+json")
    try:
        parsed = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise FeedError("GitHub API returned non-JSON") from exc
    if not isinstance(parsed, dict):
        raise FeedError("GitHub API returned an unexpected payload")
    return parsed


def github_bytes(url: str, token: str) -> bytes:
    return _request_bytes(url, token, "application/octet-stream")


def parse_repo(repository: str) -> str:
    repo = (repository or "").strip()
    if not REPO_RE.fullmatch(repo):
        raise FeedError(f"source repository {repository!r} must look like opelpanfan/NAME")
    return repo


def bins_in_zip(data: bytes) -> list[tuple[str, bytes]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise FeedError("workflow artifact is not a zip") from exc
    found = []
    for info in archive.infolist():
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/")
        parts = Path(name).parts
        if not name or name.startswith("/") or ".." in parts:
            raise FeedError("artifact zip contains an unsafe path")
        if "__MACOSX" in parts:
            continue
        if not name.lower().endswith(".bin"):
            continue
        if info.file_size > MAX_BIN:
            raise FeedError(f"{name} inside the artifact exceeds the size limit")
        found.append((name, archive.read(info)))
    return found


def _board_keys(board: str, spec: dict) -> list[str]:
    keys = [board]
    for env in spec.get("envs") or []:
        if env not in keys:
            keys.append(env)
    return keys


def match_artifact_name(artifact_name: str, boards: dict) -> list[str]:
    """Match an artifact name to one board without treating ATOM_S3 as ATOM_S3_R."""

    hits = match_board_token(artifact_name, boards)
    if hits:
        return hits
    folded = artifact_name.casefold()
    for prefix in ("firmware-", "fw-"):
        if folded.startswith(prefix):
            return match_board_token(artifact_name[len(prefix) :], boards)
    for suffix in ("-firmware", "-fw"):
        if folded.endswith(suffix):
            return match_board_token(artifact_name[: -len(suffix)], boards)
    return []


def match_board_token(token: str, boards: dict) -> list[str]:
    hits = []
    folded = token.casefold()
    for board, spec in boards.items():
        if any(folded == key.casefold() for key in _board_keys(board, spec)):
            hits.append(board)
    return hits


def _token_ignored(token: str, ignored: list[str]) -> bool:
    folded = token.casefold()
    return any(folded == item.casefold() for item in ignored)


def match_zip_bins(
    artifact_name: str,
    files: list[tuple[str, bytes]],
    boards: dict,
    ignored: list[str] | None = None,
) -> list[tuple[str, str, bytes]]:
    """Map firmware files in one artifact zip to catalog boards."""

    ignored = list(ignored or [])
    files = [
        (path, data)
        for path, data in files
        if not any(_token_ignored(part, ignored) for part in (*Path(path).parts, Path(path).stem))
        and not _token_ignored(artifact_name, ignored)
    ]
    if not files:
        return []
    resolved: list[tuple[str, str, bytes]] = []
    unresolved: list[str] = []
    for path, data in files:
        parts = Path(path).parts
        basename = parts[-1]
        name_hits = [
            board
            for board, spec in boards.items()
            if basename == spec["filename"] or basename.casefold() == f"{board}.bin".casefold()
        ]
        if len(name_hits) == 1:
            resolved.append((name_hits[0], Path(path).name, data))
            continue
        if len(name_hits) > 1:
            raise FeedError(f"ambiguous firmware filename {basename} in artifact {artifact_name}")

        component_hits: list[str] = []
        for part in parts[:-1]:
            component_hits.extend(match_board_token(part, boards))
        component_hits = list(dict.fromkeys(component_hits))
        if len(component_hits) == 1 and basename.lower() == "firmware.bin":
            resolved.append((component_hits[0], Path(path).name, data))
            continue
        if len(component_hits) > 1:
            raise FeedError(f"ambiguous env path {path} in artifact {artifact_name}")
        unresolved.append(path)

    if unresolved:
        if len(files) == 1 and Path(files[0][0]).name.lower() == "firmware.bin":
            hits = match_artifact_name(artifact_name, boards)
            if len(hits) == 1:
                return [(hits[0], Path(files[0][0]).name, files[0][1])]
        known = ", ".join(sorted(boards))
        raise FeedError(
            f"artifact {artifact_name!r} contains unmapped firmware {unresolved}. "
            f"Name the artifact exactly as the env/board or store <env>/firmware.bin. "
            f"Known boards: {known}"
        )

    seen: dict[str, str] = {}
    for board, source_name, _data in resolved:
        if board in seen:
            raise FeedError(f"artifact {artifact_name!r} maps to {board} more than once")
        seen[board] = source_name
    return resolved


def match_release_assets(assets: list[dict], boards: dict, requested: set[str] | None) -> dict[str, dict]:
    selected: dict[str, dict] = {}
    used: set[str] = set()
    for board, spec in boards.items():
        if requested is not None and board not in requested:
            continue
        globs = list(spec.get("asset_globs") or [spec["filename"]])
        hits = [
            asset
            for asset in assets
            if any(_release_name_matches(asset.get("name", ""), pattern) for pattern in globs)
        ]
        if len(hits) > 1:
            names = ", ".join(asset.get("name", "") for asset in hits)
            raise FeedError(f"{board} matched multiple release assets: {names}")
        if len(hits) == 1:
            selected[board] = hits[0]
            used.add(hits[0].get("name", ""))
        elif spec.get("required"):
            raise ReleaseNotReady(
                f"release is missing required asset for {board} (expected one of: {', '.join(globs)})"
            )

    for asset in assets:
        name = asset.get("name") or ""
        if name.lower().endswith(".bin") and name not in used:
            raise FeedError(f"release asset {name} is a .bin and did not match any board")
    if requested is not None:
        missing = sorted(requested - set(selected))
        if missing:
            raise ReleaseNotReady(f"release is missing requested boards: {', '.join(missing)}")
    if not selected:
        raise ReleaseNotReady("release has no firmware assets that match the catalog")
    return selected


def _release_name_matches(name: str, pattern: str) -> bool:
    """Match a release asset name. Globs are case-insensitive; spelling stays exact."""

    if fnmatchcase(name, pattern):
        return True
    return fnmatchcase(name.casefold(), pattern.casefold())


def parse_board_list(value, boards: dict) -> set[str] | None:
    if value is None or value == "":
        return None
    if isinstance(value, list):
        parts = value
    else:
        text = str(value).strip()
        if not text:
            return None
        parts = text.split(",")
    found = []
    for part in parts:
        board = str(part).strip()
        if not board:
            continue
        if board not in boards:
            known = ", ".join(sorted(boards))
            raise FeedError(f"unknown board {board!r}; known boards: {known}")
        found.append(board)
    if not found:
        raise FeedError("boards filter is empty")
    return set(found)


def parse_expected_sha256(value) -> dict[str, str]:
    if value in (None, "", {}):
        return {}
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise FeedError("sha256 must be an object of board to hex digest")
    expected = {}
    for board, digest in value.items():
        if not BOARD_RE.fullmatch(str(board)):
            raise FeedError(f"invalid sha256 board {board!r}")
        text = str(digest).strip().lower()
        if not SHA256_RE.fullmatch(text):
            raise FeedError(f"sha256 for {board} must be 64 hex characters")
        expected[str(board)] = text
    return expected


def check_expected_sha256(binaries: dict[str, tuple[bytes, str]], expected: dict[str, str]) -> None:
    for board, digest in expected.items():
        if board not in binaries:
            raise FeedError(f"sha256 was provided for {board}, which was not ingested")
        actual = sha256_bytes(binaries[board][0])
        if actual != digest:
            raise FeedError(f"sha256 mismatch for {board}")
    for board in binaries:
        if expected and board not in expected:
            # Partial expected hashes are allowed, but a provided digest must match.
            continue


def _truthy(value, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes"):
        return True
    if text in ("0", "false", "no"):
        return False
    raise FeedError(f"expected true/false, got {value!r}")


def ingest_from_env(root: Path, env: dict[str, str] | None = None) -> str:
    env = env if env is not None else dict(os.environ)
    catalog = load_catalog()
    event = env.get("EVENT_NAME") or "workflow_dispatch"
    if event == "repository_dispatch":
        try:
            payload = json.loads(env.get("CLIENT_PAYLOAD") or "{}")
        except json.JSONDecodeError as exc:
            raise FeedError("repository_dispatch client_payload is not JSON") from exc
        if not isinstance(payload, dict):
            raise FeedError("repository_dispatch client_payload must be an object")
        request = payload
    else:
        request = {
            "product": env.get("INPUT_PRODUCT"),
            "version": env.get("INPUT_VERSION"),
            "source": env.get("INPUT_SOURCE"),
            "source_repository": env.get("INPUT_SOURCE_REPOSITORY"),
            "run_id": env.get("INPUT_RUN_ID"),
            "tag": env.get("INPUT_TAG"),
            "workflow_file": env.get("INPUT_WORKFLOW_FILE"),
            "boards": env.get("INPUT_BOARDS"),
            "set_latest": env.get("INPUT_SET_LATEST"),
            "overwrite": env.get("INPUT_OVERWRITE"),
            "allow_any_ref": env.get("INPUT_ALLOW_ANY_REF"),
            "sha256": env.get("INPUT_SHA256"),
        }

    product = str(request.get("product") or "").strip()
    spec = product_spec(catalog, product)
    boards = require_publishable(spec, product)
    semver = normalize_version(str(request.get("version") or ""))
    source_kind = str(request.get("source") or "").strip()
    allowed = spec.get("ingest") or "any"
    if not source_kind:
        source_kind = "release" if allowed == "release" else ""
    if source_kind not in ("workflow_run", "release"):
        raise FeedError("source must be workflow_run or release")
    if allowed == "release" and source_kind != "release":
        raise FeedError(f"{product} only accepts GitHub Release asset ingest")
    if allowed == "workflow_run" and source_kind != "workflow_run":
        raise FeedError(f"{product} only accepts workflow artifact ingest")

    catalog_repo = spec.get("source_repository")
    requested_repo = str(request.get("source_repository") or "").strip()
    if requested_repo and requested_repo != catalog_repo:
        raise FeedError(f"source_repository must be {catalog_repo}")
    repository = parse_repo(catalog_repo)
    token = env.get("SOURCE_READ_TOKEN") or ""
    if not token:
        raise FeedError(
            "Missing secret SOURCE_READ_TOKEN. Create a fine-grained PAT with "
            "Contents: Read on the source repository and store it on OPF-FIRMWARE-FEED."
        )

    set_latest = _truthy(request.get("set_latest"), True)
    if _truthy(request.get("overwrite"), False):
        raise FeedError(
            "version folders are immutable. Publish a new version, or roll latest back to an older folder."
        )
    allow_any_ref = _truthy(request.get("allow_any_ref"), False)
    requested_boards = parse_board_list(request.get("boards"), boards)
    if requested_boards is not None:
        missing_required = [board for board in required_board_ids(spec) if board not in requested_boards]
        if missing_required:
            raise FeedError(
                f"boards filter omits {', '.join(missing_required)}; refusing a partial publish"
            )
    expected = parse_expected_sha256(request.get("sha256"))

    if source_kind == "release":
        binaries, source = _fetch_release(
            repository, semver, str(request.get("tag") or ""), boards, requested_boards, token, spec, allow_any_ref
        )
    else:
        binaries, source = _fetch_workflow_run(
            repository,
            spec,
            str(request.get("run_id") or ""),
            str(request.get("workflow_file") or ""),
            boards,
            requested_boards,
            allow_any_ref,
            token,
        )
    assert_complete_publish(spec, binaries)
    check_expected_sha256(binaries, expected)
    folder = apply_publish(
        root,
        catalog,
        product,
        semver,
        binaries,
        set_latest=set_latest,
        source=source,
    )
    validate_feed(root, catalog)
    _export_github_env(product, semver, folder)
    return folder


def _export_github_env(product: str, semver: str, folder: str) -> None:
    path = os.environ.get("GITHUB_ENV")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"PUBLISH_PRODUCT={product}\n")
        handle.write(f"PUBLISH_VERSION={semver}\n")
        handle.write(f"PUBLISH_FOLDER={folder}\n")


def _fetch_release(repository, semver, tag, boards, requested, token, spec, allow_any_ref=False):
    tag = tag.strip() or f"v{semver}"
    if parse_semver(tag) != semver:
        raise FeedError(f"release tag {tag} does not match version {semver}")
    last: Exception | None = None
    for attempt in range(5):
        try:
            return _fetch_release_once(repository, semver, tag, boards, requested, token, spec, allow_any_ref)
        except ReleaseNotReady as exc:
            last = exc
            print(f"release {tag} not ready ({attempt + 1}/5): {exc}", file=sys.stderr)
            if attempt == 4:
                break
            _backoff(attempt, "release")
        except GitHubHTTPError as exc:
            if exc.code != 404:
                raise
            last = ReleaseNotReady(f"release tag {tag} is not available yet ({exc})")
            print(f"release {tag} not ready ({attempt + 1}/5): {last}", file=sys.stderr)
            if attempt == 4:
                break
            _backoff(attempt, "release")
    raise FeedError(f"{last} Nothing was published.")


def _fetch_release_once(repository, semver, tag, boards, requested, token, spec, allow_any_ref):
    quoted = urllib.parse.quote(tag, safe="")
    try:
        release = github_json(f"{API}/repos/{repository}/releases/tags/{quoted}", token)
    except GitHubHTTPError as exc:
        if exc.code == 404:
            raise ReleaseNotReady(f"release tag {tag} is not available yet") from exc
        raise
    target = str(release.get("target_commitish") or "")
    expected_ref = spec.get("source_ref")
    if expected_ref and not allow_any_ref and target and not re.fullmatch(r"[0-9a-fA-F]{40}", target):
        if target != expected_ref:
            raise FeedError(
                f"release target_commitish is {target!r}; catalog requires {expected_ref}. "
                "Pass allow_any_ref=true only for an intentional exception."
            )
    assets = release.get("assets") or []
    if not isinstance(assets, list):
        raise FeedError("release assets payload is invalid")
    selected = match_release_assets(assets, boards, requested)
    binaries = {}
    for board, asset in selected.items():
        api_url = asset.get("url") or ""
        if not str(api_url).startswith(f"{API}/"):
            raise FeedError(f"release asset {asset.get('name')} has no API download URL")
        data = github_bytes(api_url, token)
        digest = str(asset.get("digest") or "")
        if digest.startswith("sha256:"):
            expected = digest.split(":", 1)[1].lower()
            actual = sha256_bytes(data)
            if actual != expected:
                raise FeedError(f"sha256 mismatch for release asset {asset.get('name')}")
        binaries[board] = (data, str(asset.get("name")))
    source = {
        "kind": "release",
        "repository": repository,
        "ref": spec.get("source_ref"),
        "tag": tag,
        "release_id": release.get("id"),
        "sha": target if re.fullmatch(r"[0-9a-fA-F]{40}", target) else None,
    }
    return binaries, canonical_source(source) or source


def _fetch_workflow_run(repository, spec, run_id, workflow_file, boards, requested, allow_any_ref, token):
    if not re.fullmatch(r"[1-9]\d{0,18}", run_id or ""):
        raise FeedError("run_id must be a positive integer")
    run = github_json(f"{API}/repos/{repository}/actions/runs/{run_id}", token)
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise FeedError(
            f"workflow run {run_id} is {run.get('status')}/{run.get('conclusion')}; only successful runs can be published"
        )
    head_repo = ((run.get("head_repository") or {}).get("full_name"))
    if head_repo != repository:
        raise FeedError(f"refusing workflow run from {head_repo or 'a fork'}; expected {repository}")
    expected_ref = spec.get("source_ref")
    if expected_ref and not allow_any_ref and run.get("head_branch") != expected_ref:
        raise FeedError(
            f"workflow run branch is {run.get('head_branch')!r}; catalog requires {expected_ref}. "
            "Pass allow_any_ref=true only for an intentional exception."
        )
    expected_workflow = _expected_workflow_file(spec, workflow_file)
    actual_workflow = Path(str(run.get("path") or "")).name
    if actual_workflow != expected_workflow:
        raise FeedError(f"workflow run file is {run.get('path')}; expected {expected_workflow}")

    artifacts = _list_artifacts(repository, run_id, token)
    binaries: dict[str, tuple[bytes, str]] = {}
    for artifact in artifacts:
        if artifact.get("expired"):
            raise FeedError(f"artifact {artifact.get('name')} is expired; re-run the source workflow")
        archive_url = artifact.get("archive_download_url") or ""
        if not str(archive_url).startswith(f"{API}/"):
            raise FeedError(f"artifact {artifact.get('name')} has no API download URL")
        files = bins_in_zip(github_bytes(archive_url, token))
        mapped = match_zip_bins(
            str(artifact.get("name") or ""),
            files,
            boards,
            list(spec.get("ignored_envs") or []),
        )
        for board, source_name, data in mapped:
            if requested is not None and board not in requested:
                raise FeedError(
                    f"artifact produced {board}, which is outside the boards filter; refusing to drop it silently"
                )
            if board in binaries:
                raise FeedError(f"{board} was produced by more than one artifact")
            binaries[board] = (data, source_name)
    if requested is not None:
        missing = sorted(requested - set(binaries))
        if missing:
            raise FeedError(f"workflow run is missing requested boards: {', '.join(missing)}")
    if not binaries:
        raise FeedError("workflow run artifacts contained no mapped firmware binaries")
    source = {
        "kind": "workflow_run",
        "repository": repository,
        "ref": run.get("head_branch"),
        "sha": run.get("head_sha"),
        "run_id": int(run_id),
        "workflow": run.get("path"),
    }
    return binaries, source


def _expected_workflow_file(spec: dict, requested: str) -> str:
    catalog_file = spec.get("workflow_file")
    requested = (requested or "").strip()
    if catalog_file:
        if requested and requested != catalog_file:
            raise FeedError(f"workflow_file must be {catalog_file}")
        return str(catalog_file)
    if not WORKFLOW_FILE_RE.fullmatch(requested):
        raise FeedError(
            "workflow_file is required for this product until .github/feed-catalog.json records one "
            "(basename only, for example build-firmware.yml)"
        )
    return requested


def _list_artifacts(repository: str, run_id: str, token: str) -> list[dict]:
    artifacts = []
    for page in range(1, 21):
        payload = github_json(
            f"{API}/repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100&page={page}",
            token,
        )
        batch = payload.get("artifacts") or []
        if not isinstance(batch, list):
            raise FeedError("artifact list payload is invalid")
        artifacts.extend(batch)
        if len(batch) < 100:
            return artifacts
    raise FeedError("workflow run has too many artifact pages")
