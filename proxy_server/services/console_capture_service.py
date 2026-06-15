import sys
import os
from typing import Optional


class TeeStream:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


class ConsoleCaptureService:
    """
    Redirects stdout/stderr to both:
    - original console
    - session log file
    """

    def __init__(self, session_id: str, base_dir: str = "/tmp/psm"):
        self._session_id = session_id
        self._base_dir = os.path.join(base_dir, session_id)

        self._log_file_path = os.path.join(self._base_dir, "console.log")

        self._original_stdout: Optional[object] = None
        self._original_stderr: Optional[object] = None
        self._file = None

    def start(self):
        os.makedirs(self._base_dir, exist_ok=True)

        self._file = open(self._log_file_path, "a", buffering=1)

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        tee = TeeStream(self._original_stdout, self._file)

        sys.stdout = tee
        sys.stderr = tee

        print(f"[ConsoleCapture] Started for session {self._session_id}")

    def stop(self):
        if self._original_stdout:
            sys.stdout = self._original_stdout

        if self._original_stderr:
            sys.stderr = self._original_stderr

        if self._file:
            try:
                self._file.close()
            except Exception:
                pass

        print(f"[ConsoleCapture] Stopped for session {self._session_id}")

    def get_log_path(self) -> str:
        return self._log_file_path

    def get_artifact_path(self) -> str:
        return f"/artifact/{self._session_id}/console.log"
