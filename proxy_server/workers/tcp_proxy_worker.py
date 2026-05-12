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
            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.connect((self._target_ip, self._target_port))

            self._forward_loop(client_sock, target_sock)

        except Exception as e:
            print(f"[TCPWorker] Connection error: {e}")

        finally:
            self._safe_close(client_sock)
            if target_sock:
                self._safe_close(target_sock)

    # =========================
    # FORWARDING
    # =========================

    def _forward_loop(self, sock_a: socket.socket, sock_b: socket.socket) -> None:
        sockets = [sock_a, sock_b]

        while self._is_running():
            try:
                readable, _, _ = select.select(sockets, [], [], 1.0)
            except Exception:
                break

            for s in readable:
                try:
                    data = s.recv(BUFFER_SIZE)
                    if not data:
                        return

                    if s is sock_a:
                        sock_b.sendall(data)
                    else:
                        sock_a.sendall(data)

                except Exception:
                    return

    # =========================
    # UTILS
    # =========================

    @staticmethod
    def _safe_close(sock: socket.socket) -> None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
