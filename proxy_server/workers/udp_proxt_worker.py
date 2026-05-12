import socket
from proxy_server.workers.base_worker import BaseProxyWorker

BUFFER_SIZE = 65535


class UDPProxyWorker(BaseProxyWorker):
    def __init__(
        self,
        bind_ip: str,
        bind_port: int,
        target_ip: str,
        target_port: int,
    ):
        super().__init__()

        self._bind_ip = bind_ip
        self._bind_port = bind_port
        self._target_ip = target_ip
        self._target_port = target_port

        self._sock: socket.socket | None = None

        # last known client (simple mapping)
        self._client_addr = None

    # =========================
    # LIFECYCLE
    # =========================

    def start(self) -> None:
        self._set_running()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self._bind_ip, self._bind_port))

        print(f"[UDPWorker] Listening on {self._bind_ip}:{self._bind_port}")

        while self._is_running():
            try:
                self._sock.settimeout(1.0)
                data, addr = self._sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[UDPWorker] Receive error: {e}")
                continue

            self._handle_packet(data, addr)

    def _on_stop(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    # =========================
    # PACKET HANDLING
    # =========================

    def _handle_packet(self, data: bytes, addr):
        """
        Very simple forwarding logic:

        If packet comes from client → send to target
        If packet comes from target → send to last client
        """

        # packet from target
        if addr == (self._target_ip, self._target_port):
            if self._client_addr:
                try:
                    self._sock.sendto(data, self._client_addr)
                except Exception:
                    pass
            return

        # packet from client
        self._client_addr = addr

        try:
            self._sock.sendto(data, (self._target_ip, self._target_port))
        except Exception:
            pass
