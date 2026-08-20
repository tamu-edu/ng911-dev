import socket
import threading
import select
import time

from proxy_server.workers.base_worker import BaseProxyWorker

BUFFER_SIZE = 65535


class TCPProxyWorker(BaseProxyWorker):
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

        self._server_socket: socket.socket | None = None
        self._client_threads: list[threading.Thread] = []
        self._active_sockets: set[socket.socket] = set()
        self._connections_lock = threading.Lock()

    # =========================
    # LIFECYCLE
    # =========================

    def start(self) -> None:
        self._set_running()

        try:

            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._server_socket.bind((self._bind_ip, self._bind_port))
            self._server_socket.listen(100)
        except Exception as e:
            self._set_startup_error(e)
            raise

        self._set_ready()

        print(f"[TCPWorker] Listening on {self._bind_ip}:{self._bind_port}")

        while self._is_running():
            try:
                self._server_socket.settimeout(1.0)
                client_sock, addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[TCPWorker] Accept error: {e}")
                continue

            thread = threading.Thread(
                target=self._handle_client,
                args=(client_sock,),
                daemon=True,
            )

            self._client_threads.append(thread)
            thread.start()

    def _on_stop(self) -> None:
        if self._server_socket:
            self._safe_close(self._server_socket)
            self._server_socket = None

        with self._connections_lock:
            sockets = list(self._active_sockets)

        for sock in sockets:
            self._safe_close(sock)

    def wait_until_stopped(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout

        with self._connections_lock:
            threads = list(self._client_threads)

        for thread in threads:
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                break

            thread.join(timeout=remaining)

        with self._connections_lock:
            return not any(thread.is_alive() for thread in self._client_threads)

    # =========================
    # CLIENT HANDLING
    # =========================

    def _handle_client(self, client_sock: socket.socket) -> None:
        target_sock: socket.socket | None = None

        with self._connections_lock:
            self._active_sockets.add(client_sock)

        try:
            print(
                f"[TCPWorker] Accepted client "
                f"{client_sock.getpeername()} -> "
                f"{self._bind_ip}:{self._bind_port}"
            )

            target_sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )
            target_sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            with self._connections_lock:
                self._active_sockets.add(target_sock)

            egress_port = self._get_egress_port(self._bind_port)

            target_sock.bind((self._bind_ip, egress_port))

            print(f"[TCPWorker] Bound egress socket " f"{self._bind_ip}:{egress_port}")

            target_sock.connect((self._target_ip, self._target_port))

            print(
                f"[TCPWorker] Connected target "
                f"{target_sock.getsockname()} -> "
                f"{self._target_ip}:{self._target_port}"
            )

            self._forward_loop(
                client_sock,
                target_sock,
            )

        except Exception as e:
            if self._is_running():
                print(f"[TCPWorker] Connection error: {e}")

        finally:
            print("[TCPWorker] Closing proxied TCP connection")

            self._safe_close(client_sock)

            if target_sock:
                self._safe_close(target_sock)

            with self._connections_lock:
                self._active_sockets.discard(client_sock)

                if target_sock:
                    self._active_sockets.discard(target_sock)

                current_thread = threading.current_thread()

                if current_thread in self._client_threads:
                    self._client_threads.remove(current_thread)

    # =========================
    # FORWARDING
    # =========================

    def _forward_loop(self, sock_a: socket.socket, sock_b: socket.socket) -> None:
        sockets = [sock_a, sock_b]

        while self._is_running() and sockets:
            try:
                readable, _, _ = select.select(sockets, [], [], 1.0)
            except Exception as e:
                print(f"[TCPWorker] Select error: {e}")
                break

            for src_sock in readable:
                try:
                    if src_sock is sock_a:
                        dst_sock = sock_b
                        direction = "client -> target"
                    else:
                        dst_sock = sock_a
                        direction = "target -> client"

                    data = src_sock.recv(BUFFER_SIZE)

                    if not data:
                        print(f"[TCPWorker] EOF received on {direction}")

                        if src_sock in sockets:
                            sockets.remove(src_sock)

                        try:
                            dst_sock.shutdown(socket.SHUT_WR)
                            print(f"[TCPWorker] Propagated FIN on {direction}")
                        except OSError as e:
                            print(
                                f"[TCPWorker] FIN propagation ignored on {direction}: {e}"
                            )

                        continue

                    dst_sock.sendall(data)

                except Exception as e:
                    print(f"[TCPWorker] Forwarding error on proxied connection: {e}")
                    return

    # =========================
    # UTILS
    # =========================

    @staticmethod
    def _safe_close(sock: socket.socket) -> None:
        try:
            sock.close()
        except OSError:
            pass
