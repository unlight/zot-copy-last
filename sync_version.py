#!/usr/bin/env python3
"""Sync the release version into extension.json and copy.py."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
COPY_VERSION = re.compile(r'^VERSION = "[^"]*"$', re.MULTILINE)


def sync_version(version):
    """Write one version to the manifest and the extension constant."""
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"invalid semantic version: {version!r}")

    manifest_path = ROOT / "extension.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = version

    copy_path = ROOT / "copy.py"
    source, count = COPY_VERSION.subn(
        f'VERSION = "{version}"',
        copy_path.read_text(encoding="utf-8"),
    )
    if count != 1:
        raise ValueError(
            f"expected one VERSION assignment in {copy_path}, found {count}"
        )

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    copy_path.write_text(source, encoding="utf-8")


def main(argv):
    if len(argv) != 2:
        raise SystemExit(f"usage: {Path(argv[0]).name} <version>")
    sync_version(argv[1])


if __name__ == "__main__":
    main(sys.argv)
