import os
import signal
import subprocess
from typing import Optional, List

from proxy_server.services.process_runner import run_process_with_capture
from proxy_server.models.session_models import ConduitConfig


class CaptureService:
    """
    Production-grade tshark capture service.
    """

    def __init__(self, session_id: str, base_dir: str = "/tmp/psm"):
        self._session_id = session_id

        self._base_dir = os.path.join(base_dir, session_id)
        self._pcap_file = os.path.join(self._base_dir, "capture.pcap")
        self._keylog_file = os.path.join(self._base_dir, "tls.keys")

        self._process: Optional[subprocess.Popen] = None

        os.makedirs(self._base_dir, exist_ok=True)

    # =========================
    # START
    # =========================

    def start(
        self,
        interface: str = "any",
        conduits: list[ConduitConfig] | None = None,
        capture_filter: str | None = None,
        decode_as: List[str] | None = None,
    ) -> None:
        if conduits:
            capture_filter = capture_filter or self._build_capture_filter(conduits)
            decode_as = decode_as or self._build_decode_as(conduits)

        cmd = [
            "tshark",
            "-i",
            interface,
            "-w",
            self._pcap_file,
            "-q",
        ]

        if capture_filter:
            cmd += ["-f", capture_filter]

        cmd += ["-o", f"tls.keylog_file:{self._keylog_file}"]

        if decode_as:
            for rule in decode_as:
                cmd += ["-d", rule]

        print(f"[Capture] Starting tshark: {' '.join(cmd)}")

        self._process = run_process_with_capture(
            cmd,
            name="tshark",
            preexec_fn=os.setsid,
        )

        print(f"[Capture] Started with PID: {self._process.pid}")

    # =========================
    # STOP
    # =========================

    def stop(self) -> None:
        if not self._process:
            return

        print(f"[Capture] Stopping tshark (PID {self._process.pid})")
        try:
            pgid = os.getpgid(self._process.pid)

            try:
                os.killpg(pgid, signal.SIGTERM)

                self._process.wait(timeout=5)
                print("[Capture] Stopped cleanly")

            except subprocess.TimeoutExpired:
                print("[Capture] Force killing tshark")
                os.killpg(pgid, signal.SIGKILL)

        except Exception as e:
            print(f"[Capture] Stop error: {e}")

    # =========================
    # CLEANUP
    # =========================

    def cleanup(self) -> None:
        self.stop()

    # =========================
    # GETTERS
    # =========================

    def get_pcap_path(self) -> str:
        return self._pcap_file

    def get_keylog_path(self) -> str:
        return self._keylog_file

    def get_artifacts(self) -> dict:
        _a = {
            "pcap_file": f"/artifact/{self._session_id}/capture.pcap",
            "console_log": f"/artifact/{self._session_id}/console.log",
        }

        if os.path.exists(self._keylog_file):
            _a["tls_keys"] = f"/artifact/{self._session_id}/tls.keys"

        return _a

    @staticmethod
    def _build_capture_filter(conduits: list[ConduitConfig]) -> str:
        rules: list[str] = []

        for conduit in conduits:
            protocol = conduit.transport.protocol.lower()

            from_ip = conduit.from_.ip
            to_ip = conduit.to.ip
            proxy_ip = conduit.proxy.ip

            to_port = conduit.to.port
            proxy_port = conduit.proxy.port

            rules.append(f"(host {from_ip} and {protocol} port {to_port})")
            rules.append(f"(host {to_ip} and {protocol} port {to_port})")
            rules.append(f"(host {proxy_ip} and {protocol} port {proxy_port})")

        return " or ".join(rules)

    @staticmethod
    def _build_decode_as(conduits: list[ConduitConfig]) -> list[str]:
        rules: set[str] = set()

        for conduit in conduits:
            transport = conduit.transport

            if transport.protocol.lower() != "tcp":
                continue

            if not transport.tls or not transport.tls.enabled:
                continue

            rules.add(f"tcp.port=={conduit.proxy.port},ssl")

        return list(rules)
