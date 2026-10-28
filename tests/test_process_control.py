import asyncio
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pray/scripts"))
from process_control import ProcessTree, process_start, stop_handlers


class ProcessTests(unittest.IsolatedAsyncioTestCase):
    async def test_current_identity_is_stable_and_missing_process_is_absent(self):
        identity = process_start(os.getpid())
        self.assertIsNotNone(identity)
        self.assertEqual(process_start(os.getpid()), identity)
        for pid in (-1, 0, 2**30, "invalid"):
            self.assertIsNone(process_start(pid))

    async def test_close_removes_owned_parent_and_descendant(self):
        with tempfile.TemporaryDirectory(prefix="process tree 雨 ") as directory:
            record = Path(directory) / "child.json"
            tree = ProcessTree()
            code = ("import json,subprocess,sys,time; from pathlib import Path; "
                    "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                    "Path(sys.argv[1]).write_text(json.dumps(child.pid)); time.sleep(60)")
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-c", code, str(record), **tree.spawn_options())
            child = None
            try:
                tree.attach(process.pid)
                end = time.monotonic() + 5
                while not record.exists() and time.monotonic() < end:
                    await asyncio.sleep(.02)
                self.assertTrue(record.exists())
                child = json.loads(record.read_text())
                self.assertIsNotNone(process_start(child))
                tree.close()
                await asyncio.wait_for(process.wait(), 3)
                end = time.monotonic() + 3
                while process_start(child) is not None and time.monotonic() < end:
                    await asyncio.sleep(.02)
                self.assertIsNone(process_start(child))
                self.assertIsNone(process_start(process.pid))
                tree.close()
            finally:
                tree.close()
                if process.returncode is None:
                    process.kill()
                await process.wait()

    async def test_interrupt_sets_stop_event_and_restores_handler(self):
        event = asyncio.Event()
        previous = signal.getsignal(signal.SIGINT)
        with stop_handlers(asyncio.get_running_loop(), event):
            os.kill(os.getpid(), signal.SIGINT) if os.name != "nt" else signal.raise_signal(signal.SIGINT)
            await asyncio.wait_for(event.wait(), 1)
        self.assertEqual(signal.getsignal(signal.SIGINT), previous)
