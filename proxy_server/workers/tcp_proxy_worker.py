import socket
import threading
import select

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

    # =========================
    # LIFECYCLE
    # =========================

    def start(self) -> None:
        self._set_running()

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._server_socket.bind((self._bind_ip, self._bind_port))
        self._server_socket.listen(100)

        print(f"[TCPWorker] Listening on {self._bind_ip}:{self._bind_port}")

        while self._is_running():
            try:
                self._server_socket.settimeout(1.0)
                client_sock, addr = self._server_socket.accept()
            except socket.timeout:
                continue
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
            try:
                self._server_socket.close()
            except Exception:
                pass

    # =========================
    # CLIENT HANDLING
    # =========================

    def _handle_client(self, client_sock: socket.socket) -> None:
        target_sock = None

        try:
            print(
                f"[TCPWorker] Accepted client "
                f"{client_sock.getpeername()} -> {self._bind_ip}:{self._bind_port}"
            )

            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.connect((self._target_ip, self._target_port))

            print(
                f"[TCPWorker] Connected target "
                f"{target_sock.getsockname()} -> {self._target_ip}:{self._target_port}"
            )

            self._forward_loop(client_sock, target_sock)

        except Exception as e:
            print(f"[TCPWorker] Connection error: {e}")

        finally:
            print("[TCPWorker] Closing proxied TCP connection")

            self._safe_close(client_sock)

            if target_sock:
                self._safe_close(target_sock)

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
