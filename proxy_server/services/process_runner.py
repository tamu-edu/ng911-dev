import subprocess
import threading
from typing import List


def run_process_with_capture(
    cmd: List[str],
    name: str = "process",
    preexec_fn=None,
) -> subprocess.Popen:
    """
    Runs subprocess and streams its output to stdout (TeeStream compatible).
    """

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        preexec_fn=preexec_fn,
    )

    def _reader():
        try:
            for line in process.stdout:
                print(f"[{name}] {line}", end="")
        except Exception as e:
            print(f"[{name}] ⚠️ reader error: {e}")

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()

    return process
