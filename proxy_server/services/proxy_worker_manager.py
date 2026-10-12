import subprocess
import threading
import psutil
from typing import List

from proxy_server.models.session_models import ConduitConfig


class ProxyWorkerManager:
    """
    Manages lifecycle of all proxy workers.
    """

    _WORKER_READY_TIMEOUT: int = 10
    _WORKER_STOP_TIMEOUT: int = 5
    _THREAD_STOP_TIMEOUT: int = 5

    def __init__(self, keylog_file: str, host_ip: str):
        self._workers = []
        self._threads: List[threading.Thread] = []
        self._running = False

        self._keylog_file = keylog_file
        self._host_ip = host_ip
        self._ip_aliases: list[tuple[str, int, str]] = []

    # =========================
    # IP ALIASING
    # =========================
    def _find_host_interface(self) -> str:
        for iface_name, iface_addresses in psutil.net_if_addrs().items():
            for addr in iface_addresses or []:
                if addr.family.name == "AF_INET" and addr.address == self._host_ip:
                    return iface_name

        raise RuntimeError(
            f"[ProxyManager] Cannot find network interface "
            f"with host IP {self._host_ip}"
        )

    def _add_ip_aliases(self, conduits: List[ConduitConfig]) -> None:
        interface = self._find_host_interface()

        proxy_ips = {conduit.proxy.ip for conduit in conduits}

        for ip in proxy_ips:
            self._add_ip_alias_safely(
                ip=ip,
                prefix=32,
                interface=interface,
            )

    def _add_ip_alias_safely(
        self,
        ip: str,
        prefix: int,
        interface: str,
    ) -> None:
        existing = subprocess.check_output(
            ["ip", "addr", "show", "dev", interface],
            text=True,
        )

        needle = f"{ip}/{prefix}"

        if needle in existing:
            print(
                f"[ProxyManager] IP alias already exists: " f"{needle} dev {interface}"
            )
            return

        cmd = [
            "sudo",
            "ip",
            "addr",
            "add",
            needle,
            "dev",
            interface,
        ]

        subprocess.run(
            cmd,
            check=True,
            shell=False,
        )

        self._ip_aliases.append((ip, prefix, interface))

        print(f"[ProxyManager] IP alias created: " f"{needle} dev {interface}")

    def _remove_ip_aliases(self) -> None:
        for ip, prefix, interface in self._ip_aliases:
            try:
                cmd = [
                    "sudo",
                    "ip",
                    "addr",
                    "del",
                    f"{ip}/{prefix}",
                    "dev",
                    interface,
                ]

                subprocess.run(
                    cmd,
                    check=False,
                    shell=False,
                )

                print(
                    f"[ProxyManager] IP alias removed: "
                    f"{ip}/{prefix} dev {interface}"
                )

            except Exception as e:
                print(f"[ProxyManager] Failed to remove " f"IP alias {ip}: {e}")

        self._ip_aliases.clear()

    # =========================
    # START
    # =========================

    def start(self, conduits: List[ConduitConfig]) -> None:
        if self._running:
            return

        try:
            self._add_ip_aliases(conduits)

            print("[ProxyManager] Proxy aliases configured.")

            for conduit in conduits:
                worker = self._create_worker(conduit)

                thread = threading.Thread(
                    target=worker.start,
                    daemon=True,
                )

                self._workers.append(worker)
                self._threads.append(thread)

                thread.start()

            print(
                f"[ProxyManager] Waiting for " f"{len(self._workers)} proxy workers..."
            )

            for worker in self._workers:
                if not worker.wait_until_ready(timeout=self._WORKER_READY_TIMEOUT):
                    raise RuntimeError("Proxy worker startup timeout")

                if worker.startup_error is not None:
                    raise RuntimeError(
                        f"Proxy worker failed to start: " f"{worker.startup_error}"
                    )

            self._running = True

            print(
                f"[ProxyManager] All {len(self._workers)} " f"proxy workers are ready."
            )

        except Exception:
            self._cleanup_failed_start()
            raise

    def _cleanup_failed_start(self) -> None:
        print("[ProxyManager] Cleaning up failed " "worker startup...")

        self.stop()

    # =========================
    # STOP
    # =========================

    def stop(self) -> None:
        """
        Stop all proxy workers and wait until all worker-owned
        threads and connections have terminated before removing
        proxy IP aliases.

        This method is intentionally idempotent and may be called
        during partial startup or repeated cleanup.
        """

        # 1. Signal every worker to stop.
        # This closes listener sockets and active connection sockets.
        for worker in self._workers:
            try:
                worker.stop()
            except Exception as e:
                print(f"[ProxyManager] Worker stop error: {e}")

        # 2. Wait for worker listener threads.
        for thread in self._threads:
            try:
                thread.join(timeout=self._THREAD_STOP_TIMEOUT)

                if thread.is_alive():
                    print(
                        f"[ProxyManager] ⚠️ Worker listener "
                        f"thread did not stop: {thread.name}"
                    )

            except Exception as e:
                print(f"[ProxyManager] Joining {thread} " f"caused error: {e}")

        # 3. Wait for worker-owned connection threads.
        all_workers_stopped = True

        for worker in self._workers:
            try:
                stopped = worker.wait_until_stopped(timeout=self._WORKER_STOP_TIMEOUT)

                if not stopped:
                    all_workers_stopped = False

                    print(
                        "[ProxyManager] ⚠️ Worker still has "
                        "active connection threads after timeout"
                    )

            except Exception as e:
                all_workers_stopped = False

                print(f"[ProxyManager] Worker shutdown " f"wait error: {e}")

        # 4. Remove aliases only after worker shutdown was attempted.
        self._remove_ip_aliases()

        # 5. Drop manager references.
        self._workers.clear()
        self._threads.clear()

        self._running = False

        if all_workers_stopped:
            print("[ProxyManager] All proxy workers " "stopped cleanly.")
        else:
            print(
                "[ProxyManager] ⚠️ Proxy worker shutdown "
                "completed with timeout warnings."
            )

    def remove_ip_aliases(self) -> None:
        self._remove_ip_aliases()

    # =========================
    # CLEANUP
    # =========================

    def cleanup(self) -> None:
        """
        Hard cleanup (after reset)
        """
        self.stop()

    # =========================
    # INTERNAL
    # =========================

    def _create_worker(self, conduit: ConduitConfig):
        """
        Factory method for workers
        """

        protocol = conduit.transport.protocol.lower()
        if protocol == "tls" or "tls" in protocol:
            protocol = "tcp"

        tls_config = conduit.transport.tls

        if protocol == "tcp":
            if tls_config and tls_config.enabled:
                return self._create_tls_worker(conduit)
            else:
                return self._create_tcp_worker(conduit)

        if protocol == "udp":
            return self._create_udp_worker(conduit)

        raise ValueError(f"Unsupported protocol: {protocol}")

    def _create_tcp_worker(self, conduit: ConduitConfig):
        from proxy_server.workers.tcp_proxy_worker import TCPProxyWorker

        return TCPProxyWorker(
            bind_ip=conduit.proxy.ip,
            bind_port=conduit.proxy.port,
            target_ip=conduit.to.ip,
            target_port=conduit.to.port,
        )

    def _create_tls_worker(self, conduit: ConduitConfig):
        from proxy_server.workers.tls_proxy_worker import TLSProxyWorker

        tls = conduit.transport.tls

        return TLSProxyWorker(
            bind_ip=conduit.proxy.ip,
            bind_port=conduit.proxy.port,
            target_ip=conduit.to.ip,
            target_port=conduit.to.port,
            server_cert=tls.server_side.cert,
            server_key=tls.server_side.key,
            server_ca=tls.server_side.ca,
            client_cert=tls.client_side.cert,
            client_key=tls.client_side.key,
            client_ca=tls.client_side.ca,
            keylog_file=self._keylog_file,
        )

    def _create_udp_worker(self, conduit: ConduitConfig):
        from proxy_server.workers.udp_proxy_worker import UDPProxyWorker

        return UDPProxyWorker(
            bind_ip=conduit.proxy.ip,
            bind_port=conduit.proxy.port,
            target_ip=conduit.to.ip,
            target_port=conduit.to.port,
        )
