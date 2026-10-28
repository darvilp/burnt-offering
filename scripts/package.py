#!/usr/bin/env python3
"""Build a reproducible, allowlisted plugin ZIP and SHA-256 checksum."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "LICENSE", "NOTICE", "README.md", "plugin.json",
    "docs/RELEASING.md", "docs/release-readiness.md",
    "skills/pray/SKILL.md", "skills/pray/references/roster.json",
    "skills/pray/scripts/pray.py", "skills/pray/scripts/process_control.py",
)


def build(root, output):
    root = root.resolve()
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    if manifest["name"] != "burnt-offering" or manifest.get("license") != "Apache-2.0":
        raise ValueError("Unexpected plugin identity or license")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?", version):
        raise ValueError("Invalid release version")
    if (catalog["name"] != manifest["name"] or len(catalog["plugins"]) != 1 or
            catalog["plugins"][0]["name"] != manifest["name"] or
            catalog["plugins"][0]["version"] != version):
        raise ValueError("Plugin and catalog identity/version must agree")
    for filename in FILES:
        path = root / filename
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Missing or unsafe package member: {filename}")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"burnt-offering-{version}.zip"
    temporary = archive.with_suffix(".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as handle:
            for filename in sorted(FILES):
                info = zipfile.ZipInfo(filename, date_time=(2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                handle.writestr(info, (root / filename).read_bytes())
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    return archive, checksum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        archive, checksum = build(ROOT, args.output)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Package build failed: {error}\n")
    print(json.dumps({"archive": str(archive), "checksum": str(checksum)}))


if __name__ == "__main__":
    main()
