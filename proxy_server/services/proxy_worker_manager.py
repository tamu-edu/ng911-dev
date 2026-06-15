import threading
from typing import List

from proxy_server.models.session_models import ConduitConfig


class ProxyWorkerManager:
    """
    Manages lifecycle of all proxy workers.
    """

    def __init__(self, keylog_file: str):
        self._workers = []
        self._threads: List[threading.Thread] = []
        self._running = False

        self._keylog_file = keylog_file

    # =========================
    # START
    # =========================

    def start(self, conduits: List[ConduitConfig]) -> None:
        if self._running:
            return

        self._running = True

        for conduit in conduits:
            worker = self._create_worker(conduit)

            thread = threading.Thread(
                target=worker.start,
                daemon=True,
            )

            self._workers.append(worker)
            self._threads.append(thread)

            thread.start()

    # =========================
    # STOP
    # =========================

    def stop(self) -> None:
        if not self._running:
            return

        for worker in self._workers:
            try:
                worker.stop()
            except Exception as e:
                print(f"[ProxyManager] Worker stop error: {e}")

        self._running = False

    # =========================
    # CLEANUP
    # =========================

    def cleanup(self) -> None:
        """
        Hard cleanup (after reset)
        """
        self.stop()
        self._workers.clear()
        self._threads.clear()

    # =========================
    # INTERNAL
    # =========================

    def _create_worker(self, conduit: ConduitConfig):
        """
        Factory method for workers
        """

        protocol = conduit.transport.protocol.lower()

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
