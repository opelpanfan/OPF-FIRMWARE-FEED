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

from feedlib import FeedError, apply_publish, load_catalog, rollback_latest, validate_feed, write_manifests

ROOT = Path(__file__).resolve().parents[2]


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
            )
            validate_feed(args.root, catalog)
            print(f"published {folder}")
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
