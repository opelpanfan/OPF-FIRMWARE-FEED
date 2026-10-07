#!/usr/bin/env python3
"""Resolve a smoke-test firmware URL from the feed catalog. Fail closed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from feedlib import FeedError, load_catalog, resolve_ota_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve an OPF feed firmware URL")
    parser.add_argument("--product", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--package-version", required=True)
    parser.add_argument("--firmware-url", default="")
    args = parser.parse_args(argv)
    try:
        print(
            resolve_ota_url(
                load_catalog(),
                args.product,
                args.board,
                args.package_version,
                args.firmware_url,
            )
        )
    except FeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
