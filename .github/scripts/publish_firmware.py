#!/usr/bin/env python3
"""Local tools for the passive OPF firmware feed.

Source repositories push product folders themselves. These commands read and
write the checkout only. They do not download private releases or workflow
artifacts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from feedlib import (
    FeedError,
    apply_publish,
    attach_release_notes,
    load_catalog,
    normalize_version,
    rollback_latest,
    validate_feed,
    version_folder,
    write_manifests,
)

ROOT = Path(__file__).resolve().parents[2]


def _notes_folder(folder: str | None, version: str | None) -> str:
    if folder and version:
        expected = version_folder(version)
        plain = normalize_version(version)
        if folder not in (expected, plain):
            raise FeedError(f"--folder {folder} does not match --version {version}")
        return folder
    if folder:
        return folder
    if version:
        return version_folder(version)
    raise FeedError("attach-notes requires --folder or --version")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OPF firmware feed local tools")
    sub = parser.add_subparsers(dest="command", required=True)

    rebuild = sub.add_parser("rebuild", help="rewrite index.json and SHA256SUMS from binaries on disk")
    rebuild.add_argument("--root", type=Path, default=ROOT)

    validate = sub.add_parser("validate", help="fail if manifests or firmware images are inconsistent")
    validate.add_argument("--root", type=Path, default=ROOT)

    apply = sub.add_parser("apply", help="publish binaries that are already named as feed boards")
    apply.add_argument("--root", type=Path, default=ROOT)
    apply.add_argument("--product", required=True)
    apply.add_argument("--version", required=True)
    apply.add_argument("--from-dir", type=Path, required=True)
    apply.add_argument("--set-latest", action="store_true")
    apply_notes = apply.add_mutually_exclusive_group()
    apply_notes.add_argument("--release-notes", help="optional UTF-8 markdown stored as RELEASE_NOTES.md")
    apply_notes.add_argument("--release-notes-file", type=Path, help="optional UTF-8 markdown file")

    attach = sub.add_parser(
        "attach-notes",
        help="add RELEASE_NOTES.md to a version folder that does not have one yet",
    )
    attach.add_argument("--root", type=Path, default=ROOT)
    attach.add_argument("--product", required=True)
    attach.add_argument("--folder", help="existing version folder, such as vX.Y.Z")
    attach.add_argument("--version", help="semver X.Y.Z or vX.Y.Z when --folder is omitted")
    attach_notes = attach.add_mutually_exclusive_group(required=True)
    attach_notes.add_argument("--release-notes", help="UTF-8 markdown text")
    attach_notes.add_argument("--release-notes-file", type=Path, help="UTF-8 markdown file")

    rollback = sub.add_parser("rollback", help="point latest at an existing immutable version folder")
    rollback.add_argument("--root", type=Path, default=ROOT)
    rollback.add_argument("--product", required=True)
    rollback.add_argument("--folder", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "rebuild":
            written = write_manifests(args.root, load_catalog())
            print(f"updated {len(written)} manifest files" if written else "manifests already current")
        elif args.command == "validate":
            validate_feed(args.root, load_catalog())
            print("feed ok")
        elif args.command == "apply":
            catalog = load_catalog()
            binaries = {}
            for path in sorted(args.from_dir.glob("*.bin")):
                binaries[path.stem] = (path.read_bytes(), path.name)
            folder = apply_publish(
                args.root,
                catalog,
                args.product,
                args.version,
                binaries,
                set_latest=args.set_latest,
                source={"kind": "directory", "repository": catalog["products"][args.product]["source_repository"]},
                release_notes=args.release_notes,
                release_notes_path=args.release_notes_file,
            )
            validate_feed(args.root, catalog)
            print(f"published {folder}")
        elif args.command == "attach-notes":
            catalog = load_catalog()
            folder_name = _notes_folder(args.folder, args.version)
            folder = attach_release_notes(
                args.root,
                catalog,
                args.product,
                folder_name,
                release_notes=args.release_notes,
                release_notes_path=args.release_notes_file,
            )
            validate_feed(args.root, catalog)
            print(f"release notes attached to {folder}")
        elif args.command == "rollback":
            catalog = load_catalog()
            folder = rollback_latest(args.root, catalog, args.product, args.folder)
            validate_feed(args.root, catalog)
            print(f"latest now matches {folder}")
        else:
            parser.error(f"unknown command {args.command}")
    except FeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
