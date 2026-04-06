import logging
import os
import signal
import subprocess
import threading
import traceback
from typing import List, Any

_cleanup_hooks: List[Any] = []
_lock = threading.Lock()

_CLEANUP_ALREADY_RUN = False  # ✅ add this


def _get_sudo():
    user = subprocess.run(["whoami"], capture_output=True, text=True, shell=False)
    if user.stdout.strip() == "root":
        return ""
    return "sudo"


def register_cleanup(name: str, fn):
    with _lock:
        _cleanup_hooks.append((name, fn))


def run_cleanup():
    global _CLEANUP_ALREADY_RUN
    with _lock:
        if _CLEANUP_ALREADY_RUN:
            return
        _CLEANUP_ALREADY_RUN = True

        print("\n[cleanup] Running cleanup hooks...")
        for name, fn in reversed(_cleanup_hooks):
            try:
                print(f"[cleanup] → {name}")
                fn()
            except Exception as e:
                _logger = logging.getLogger("LoggerService")
                _logger.debug(e)
                # keep this, but note: printing tracebacks inside signal cascades can also re-enter
                print(f"[cleanup] ✖ Failed in {name}")
                traceback.print_exc()
        _cleanup_hooks.clear()


def kill_process_tree(pid: int):
    """
    Signal-safe version.
    Must NEVER raise or trigger new signals during shutdown.
    """
    try:
        os.killpg(pid, signal.SIGTERM)
    except Exception as e:
        _logger = logging.getLogger("LoggerService")
        _logger.debug(e)
        return False
