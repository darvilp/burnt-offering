"""Owned process trees and runner identities on Linux, macOS and Windows."""

import contextlib
import ctypes
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys


def codex_command(arguments):
    executable = (shutil.which("codex.exe") if os.name == "nt" else None) or shutil.which("codex")
    if not executable:
        raise RuntimeError("Install the Codex CLI and make it available on PATH")
    if os.name == "nt" and Path(executable).suffix.lower() in (".cmd", ".bat"):
        # Invoke the official npm launcher directly, avoiding cmd.exe quoting of arguments.
        launcher = Path(executable).parent / "node_modules/@openai/codex/bin/codex.js"
        node = shutil.which("node.exe")
        if not node or not launcher.is_file():
            raise RuntimeError("Use codex.exe or the official global npm Codex installation on Windows")
        return [node, str(launcher), *arguments]
    return [executable, *arguments]


def process_start(pid):
    if type(pid) is not int or pid <= 0:
        return None
    try:
        if sys.platform.startswith("linux"):
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            return None if fields[0] in ("Z", "X") else fields[19]
        if sys.platform == "darwin":
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "lstart=", "-o", "stat="],
                capture_output=True, text=True, timeout=2, env={**os.environ, "LC_ALL": "C"})
            if result.returncode or not result.stdout.strip():
                return None
            started, state = result.stdout.strip().rsplit(None, 1)
            return None if state.startswith(("Z", "X")) else "darwin:" + started
        if os.name == "nt":
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
            handle = kernel.OpenProcess(0x1000 | 0x100000, False, pid)
            if not handle:
                return None
            try:
                if kernel.WaitForSingleObject(handle, 0) != 258:
                    return None
                times = [wintypes.FILETIME() for _ in range(4)]
                if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
                    return None
                return "win32:" + str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
            finally:
                kernel.CloseHandle(handle)
    except (OSError, IndexError, ValueError, subprocess.TimeoutExpired):
        return None
    return None


class WindowsJob:
    def __init__(self):
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                        ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("basic", BasicLimits), ("io_counters", ctypes.c_ulonglong * 6),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def attach(self, pid):
        process = self.kernel.OpenProcess(0x0101, False, pid)
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.kernel.AssignProcessToJobObject(self.handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.kernel.CloseHandle(process)

    def terminate(self):
        if self.handle and not self.kernel.TerminateJobObject(self.handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


class ProcessTree:
    def __init__(self):
        self.pid = None
        self.job = WindowsJob() if os.name == "nt" else None

    def spawn_options(self):
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}

    def attach(self, pid):
        self.pid = pid
        if self.job:
            self.job.attach(pid)

    def terminate(self, force=False):
        if self.job:
            self.job.terminate()
        elif self.pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(self.pid, signal.SIGKILL if force else signal.SIGTERM)

    def close(self):
        if self.job:
            self.job.close()
        else:
            self.terminate(force=True)


@contextlib.contextmanager
def stop_handlers(loop, event):
    previous = {}
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.getsignal(sig)
            if os.name == "nt":
                signal.signal(sig, lambda *_: loop.call_soon_threadsafe(event.set))
            else:
                loop.add_signal_handler(sig, event.set)
        yield
    finally:
        for sig, handler in previous.items():
            if os.name != "nt":
                loop.remove_signal_handler(sig)
            signal.signal(sig, handler)
