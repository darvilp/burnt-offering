#!/usr/bin/env python3
"""No-model integration check using a temporary, uniquely named Codex catalog.

Temporarily adds and removes only its own marketplace/plugin entries. Run on a
disposable CI account or with permission to modify local Codex plugin state.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/pray/scripts"))
from pray import AppServer
from process_control import codex_command


def cli(arguments, cwd, check=True):
    result = subprocess.run(codex_command(["-c", 'cli_auth_credentials_store="ephemeral"', *arguments]), cwd=cwd, capture_output=True,
                            encoding="utf-8", timeout=90)
    if check and result.returncode:
        raise RuntimeError(f"Codex {arguments[0]} failed: {result.stderr[-2000:]}")
    return result


async def installed_skill(cwd, installed):
    server = AppServer(cwd, codex_command([
        "-c", 'cli_auth_credentials_store="ephemeral"',
        "app-server", "--stdio", "--enable", "plugins", "--disable", "apps", "--disable", "hooks"]))
    try:
        await server.start()
        account = await server.rpc("account/read", {"refreshToken": False})
        if account.get("account") is not None:
            raise RuntimeError("The installation check must run without model credentials")
        result = await server.rpc("skills/list", {"cwds": [str(cwd)], "forceReload": True})
        expected = (installed / "skills/pray/SKILL.md").resolve()
        for group in result.get("data", []):
            for skill in group.get("skills", []):
                if Path(skill["path"]).resolve() == expected and skill.get("enabled"):
                    return skill["name"]
        raise RuntimeError("The installed plugin's Pray skill was not enabled/discovered")
    finally:
        await server.close()


def check(archive):
    namespace = "burnt-offering-check-" + uuid.uuid4().hex[:10]
    plugin_id = "burnt-offering@" + namespace
    with tempfile.TemporaryDirectory(prefix="plugin install 雨 ") as directory:
        base = Path(directory)
        source, unrelated = base / "package", base / "unrelated"
        unrelated.mkdir()
        with zipfile.ZipFile(archive) as handle:
            for name in handle.namelist():
                if not (source / name).resolve().is_relative_to(source.resolve()):
                    raise ValueError("Unsafe archive member")
            handle.extractall(source)
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        catalog["name"] = namespace
        catalog["plugins"][0]["source"]["path"] = "./package"
        catalog_path = base / ".agents/plugins/marketplace.json"
        catalog_path.parent.mkdir(parents=True)
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        record = base / "private records/retained.json"
        record.parent.mkdir()
        record.write_text('{"fixture": "retain after uninstall"}', encoding="utf-8")
        registered = False
        try:
            cli(["plugin", "marketplace", "add", str(base), "--json"], unrelated)
            registered = True
            for _ in range(2):
                installed = json.loads(cli(["plugin", "add", plugin_id, "--json"], unrelated).stdout)
                path = Path(installed["installedPath"])
                skill_name = asyncio.run(installed_skill(unrelated, path))
                helper = path / "skills/pray/scripts/pray.py"
                subprocess.run([sys.executable, str(helper), "--help"], cwd=unrelated,
                               check=True, capture_output=True, timeout=10)
                cli(["plugin", "remove", plugin_id, "--json"], unrelated)
                if not record.is_file():
                    raise RuntimeError("Uninstall removed private records")
            return {"platform": sys.platform, "python": sys.version.split()[0],
                    "codex": cli(["--version"], unrelated).stdout.strip(),
                    "skill": skill_name, "install_and_reinstall": True, "records_retained": True}
        finally:
            if registered:
                cli(["plugin", "remove", plugin_id, "--json"], unrelated, check=False)
                cli(["plugin", "marketplace", "remove", namespace, "--json"], unrelated)


def main():
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY"):
        os.environ.pop(name, None)
    parser = argparse.ArgumentParser(description=__doc__)
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    parser.add_argument("--archive", type=Path,
                        default=ROOT / "dist" / f"burnt-offering-{manifest['version']}.zip")
    args = parser.parse_args()
    print(json.dumps(check(args.archive)))


if __name__ == "__main__":
    main()
