import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package", ROOT / "scripts/package.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class DistributionTests(unittest.TestCase):
    def test_archive_is_allowlisted_reproducible_and_checksummed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            for name in (*package.FILES, ".agents/plugins/marketplace.json"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            (root / "skills/pray/.env").write_text("must not ship")
            first, checksum = package.build(root, Path(directory) / "one")
            second, _ = package.build(root, Path(directory) / "two")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            digest = hashlib.sha256(first.read_bytes()).hexdigest()
            self.assertEqual(checksum.read_text().strip(), f"{digest}  {first.name}")
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(set(archive.namelist()), set(package.FILES))
                self.assertIn("Apache License", archive.read("LICENSE").decode())
            catalog = root / ".agents/plugins/marketplace.json"
            value = json.loads(catalog.read_text())
            value["plugins"][0]["version"] = "0.0.0"
            catalog.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                package.build(root, Path(directory) / "invalid")

    def test_relocated_package_runs_and_reports_without_checkout_or_symlink(self):
        with tempfile.TemporaryDirectory(prefix="distribution 雨 ") as directory:
            base = Path(directory)
            archive, _ = package.build(ROOT, base / "dist")
            installed = base / "installed plugin"
            with zipfile.ZipFile(archive) as handle:
                handle.extractall(installed)
            elsewhere = base / "unrelated project"
            elsewhere.mkdir()
            helper = installed / "skills/pray/scripts/pray.py"
            command = [sys.executable, str(helper)]
            result = subprocess.run(command + ["--help"], cwd=elsewhere, capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            blocked = subprocess.run(command + ["--data-dir", str(installed / "records"), "status", "a" * 32],
                                     cwd=elsewhere, capture_output=True, encoding="utf-8")
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("outside", json.loads(blocked.stdout)["error"])
            self.assertFalse((installed / "records").exists())
            probe = r'''
import asyncio, contextlib, io, json, runpy, sys
from pathlib import Path
helper, fake, records = map(Path, sys.argv[1:])
sys.path.insert(0, str(helper.parent))
module = runpy.run_path(str(helper), run_name="packaged_pray")
assert len(module["load_subjects"](use_all=True)) == 25
async def main():
    for devotion in ("standard", "templeos"):
        run_id = ("a" if devotion == "standard" else "b") * 32
        args = ["run", "--run-id", run_id, "--intention", "Peace. سلام.", "--duration", "2", "--max-batches", "2", "--controller-thread", "controller"]
        args += ["--target", "islam"] if devotion == "standard" else ["--devotion", "templeos"]
        spec = module["build_spec"](module["parser"]().parse_args(args))
        path = records / run_id
        path.mkdir(parents=True)
        info = {"goal": {"objective": f"prayer-run {run_id}: test", "tokensUsed": 100, "status": "active"}, "resolved": {"model": "worker", "effort": "low"}, "worker_config": module["WORKER_CONFIG"]}
        server = await module["AppServer"](path, [sys.executable, str(fake), "normal", run_id]).start()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                status = await module["Runner"](server, info, spec, path).run()
            assert status["completed_prayers"] == 2
        finally:
            await server.close()
asyncio.run(main())
'''
            records = base / "private records"
            completed = subprocess.run([sys.executable, "-c", probe, str(helper),
                                        str(ROOT / "tests/fake_app_server.py"), str(records)],
                                       cwd=elsewhere, capture_output=True, encoding="utf-8", timeout=15)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for run_id in ("a" * 32, "b" * 32):
                report = subprocess.run(command + ["--data-dir", str(records), "report", run_id, "--format", "html"],
                                        cwd=elsewhere, capture_output=True, encoding="utf-8")
                self.assertEqual(report.returncode, 0, report.stderr)
                self.assertIn("سلام", report.stdout)
                if run_id.startswith("b"):
                    self.assertIn('id="temple-screen"', report.stdout)
            shutil.rmtree(installed)
            self.assertTrue((records / ("a" * 32) / "report.html").exists())
