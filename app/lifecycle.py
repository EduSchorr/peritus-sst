from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def wait_process(pid, timeout=45):
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, int(pid or 0))
        if not handle:
            return
        try:
            ctypes.windll.kernel32.WaitForSingleObject(handle, int(timeout * 1000))
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
        return
    end = time.time() + timeout
    while pid and time.time() < end:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(.25)


def restart():
    launcher = ROOT / "app" / "launcher.py"
    pythonw = ROOT / ".runtime" / "Scripts" / "pythonw.exe"
    executable = pythonw if os.name == "nt" and pythonw.exists() else Path(sys.executable)
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess,"CREATE_NO_WINDOW",0)|getattr(subprocess,"DETACHED_PROCESS",0)|getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
    subprocess.Popen([str(executable),str(launcher)],cwd=str(ROOT),stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-pid", type=int, required=True)
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()
    wait_process(args.wait_pid)
    if args.restart:
        restart()
