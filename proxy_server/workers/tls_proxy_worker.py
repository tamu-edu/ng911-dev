import select
import socket
import ssl
import threading

from proxy_server.workers.base_worker import BaseProxyWorker

BUFFER_SIZE = 65535


class TLSProxyWorker(BaseProxyWorker):
    def __init__(
        self,
        bind_ip: str,
        bind_port: int,
        target_ip: str,
        target_port: int,
        server_cert: str,
        server_key: str,
        server_ca: str | None,
        client_cert: str | None,
        client_key: str | None,
        client_ca: str | None,
        keylog_file: str,
    ):
        super().__init__()

        self._bind_ip = bind_ip
        self._bind_port = bind_port
        self._target_ip = target_ip
        self._target_port = target_port

        self._server_cert = server_cert
        self._server_key = server_key
        self._server_ca = server_ca

        self._client_cert = client_cert
        self._client_key = client_key
        self._client_ca = client_ca

        self._keylog_file = keylog_file

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

        print(f"[TLSWorker] Listening on {self._bind_ip}:{self._bind_port}")

        while self._is_running():
            try:
                self._server_socket.settimeout(1.0)
                client_sock, _addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[TLSWorker] Accept error: {e}")
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

    def _handle_client(self, raw_client_sock: socket.socket) -> None:
        client_tls_sock: ssl.SSLSocket | None = None
        target_raw_sock: socket.socket | None = None
        target_tls_sock: ssl.SSLSocket | None = None

        try:
            server_context = self._build_server_context()
            client_tls_sock = server_context.wrap_socket(
                raw_client_sock,
                server_side=True,
            )

            target_raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_raw_sock.connect((self._target_ip, self._target_port))

            client_context = self._build_client_context()
            target_tls_sock = client_context.wrap_socket(
                target_raw_sock,
                server_hostname=self._target_ip,
            )

            self._forward_loop(client_tls_sock, target_tls_sock)

        except Exception as e:
            print(f"[TLSWorker] Connection error: {e}")

        finally:
            if client_tls_sock:
                self._safe_close(client_tls_sock)
            else:
                self._safe_close(raw_client_sock)

            if target_tls_sock:
                self._safe_close(target_tls_sock)
            elif target_raw_sock:
                self._safe_close(target_raw_sock)

    # =========================
    # TLS CONTEXTS
    # =========================

    def _build_server_context(self) -> ssl.SSLContext:
        """
        TLS context for incoming connection.

        PSH behaves as TLS server towards Device A.
        """
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        context.load_cert_chain(
            certfile=self._server_cert,
            keyfile=self._server_key,
        )

        if self._server_ca:
            context.load_verify_locations(cafile=self._server_ca)
            # For now we do not require client cert by default.
            # If mTLS is required, change this to CERT_REQUIRED.
            context.verify_mode = ssl.CERT_OPTIONAL
        else:
            context.verify_mode = ssl.CERT_NONE

        context.keylog_filename = self._keylog_file

        return context

    def _build_client_context(self) -> ssl.SSLContext:
        """
        TLS context for outgoing connection.

        PSH behaves as TLS client towards Device B.
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        if self._client_ca:
            context.load_verify_locations(cafile=self._client_ca)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        if self._client_cert and self._client_key:
            context.load_cert_chain(
                certfile=self._client_cert,
                keyfile=self._client_key,
            )

        context.keylog_filename = self._keylog_file

        return context

    # =========================
    # FORWARDING
    # =========================

    def _forward_loop(
        self,
        sock_a: ssl.SSLSocket,
        sock_b: ssl.SSLSocket,
    ) -> None:
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
    def _safe_close(sock: socket.socket | ssl.SSLSocket) -> None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        try:
            sock.close()
        except Exception:
            pass
