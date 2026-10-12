import socket
import ssl
import threading
import time

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

        self._active_sockets: set[socket.socket | ssl.SSLSocket] = set()

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
            self._safe_close(self._server_socket)
            self._server_socket = None

        with self._connections_lock:
            sockets = list(self._active_sockets)

        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

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

    def _handle_client(
        self,
        raw_client_sock: socket.socket,
    ) -> None:
        client_tls_sock: ssl.SSLSocket | None = None
        target_raw_sock: socket.socket | None = None
        target_tls_sock: ssl.SSLSocket | None = None

        with self._connections_lock:
            self._active_sockets.add(raw_client_sock)

        try:
            print(
                f"[TLSWorker] Accepted raw client "
                f"{raw_client_sock.getpeername()} -> "
                f"{self._bind_ip}:{self._bind_port}"
            )

            server_context = self._build_server_context()

            client_tls_sock = server_context.wrap_socket(
                raw_client_sock,
                server_side=True,
            )

            with self._connections_lock:
                self._active_sockets.discard(raw_client_sock)
                self._active_sockets.add(client_tls_sock)

            print("[TLSWorker] Incoming TLS handshake completed")

            target_raw_sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )

            target_raw_sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            with self._connections_lock:
                self._active_sockets.add(target_raw_sock)

            egress_port = self._get_egress_port(self._bind_port)

            target_raw_sock.bind((self._bind_ip, egress_port))

            print(f"[TLSWorker] Bound egress socket " f"{self._bind_ip}:{egress_port}")

            target_raw_sock.connect((self._target_ip, self._target_port))

            print(
                f"[TLSWorker] Connected raw target "
                f"{target_raw_sock.getsockname()} -> "
                f"{self._target_ip}:{self._target_port}"
            )

            client_context = self._build_client_context()

            target_tls_sock = client_context.wrap_socket(
                target_raw_sock,
                server_hostname=self._target_ip,
            )

            with self._connections_lock:
                self._active_sockets.discard(target_raw_sock)
                self._active_sockets.add(target_tls_sock)

            print("[TLSWorker] Outgoing TLS handshake completed")

            self._forward_loop(
                client_tls_sock,
                target_tls_sock,
            )

        except Exception as e:
            if self._is_running():
                print(f"[TLSWorker] Connection error: {e}")

        finally:
            print("[TLSWorker] Closing proxied TLS connection")

            if client_tls_sock:
                self._safe_close(client_tls_sock)
            else:
                self._safe_close(raw_client_sock)

            if target_tls_sock:
                self._safe_close(target_tls_sock)
            elif target_raw_sock:
                self._safe_close(target_raw_sock)

            with self._connections_lock:
                self._active_sockets.discard(raw_client_sock)

                if client_tls_sock:
                    self._active_sockets.discard(client_tls_sock)

                if target_raw_sock:
                    self._active_sockets.discard(target_raw_sock)

                if target_tls_sock:
                    self._active_sockets.discard(target_tls_sock)

                current_thread = threading.current_thread()

                if current_thread in self._client_threads:
                    self._client_threads.remove(current_thread)

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
        """
        Bidirectional TLS relay.

        Uses one blocking pump thread per direction instead of select() over
        SSLSocket objects. This avoids readiness ambiguity between the TCP fd
        and OpenSSL's internal decrypted-data buffer.
        """
        stop_event = threading.Event()

        try:
            sock_a.settimeout(1.0)
            sock_b.settimeout(1.0)
        except Exception:
            pass

        def pump(
            src_sock: ssl.SSLSocket,
            dst_sock: ssl.SSLSocket,
            direction: str,
        ) -> None:
            while self._is_running() and not stop_event.is_set():
                try:
                    data = src_sock.recv(BUFFER_SIZE)

                    if not data:
                        print(f"[TLSWorker] EOF received on {direction}")
                        stop_event.set()
                        return

                    print(f"[TLSWorker] Forwarding {len(data)} bytes {direction}")

                    dst_sock.sendall(data)

                    print(f"[TLSWorker] Forwarded {len(data)} bytes {direction}")

                except socket.timeout:
                    continue

                except ssl.SSLWantReadError:
                    continue

                except ssl.SSLWantWriteError:
                    continue

                except ssl.SSLError as e:
                    print(f"[TLSWorker] SSL forwarding error on {direction}: {e}")
                    stop_event.set()
                    return

                except OSError as e:
                    print(f"[TLSWorker] Socket forwarding error on {direction}: {e}")
                    stop_event.set()
                    return

                except Exception as e:
                    print(f"[TLSWorker] Forwarding error on {direction}: {e}")
                    stop_event.set()
                    return

        client_to_target = threading.Thread(
            target=pump,
            args=(sock_a, sock_b, "client -> target"),
            daemon=True,
        )

        target_to_client = threading.Thread(
            target=pump,
            args=(sock_b, sock_a, "target -> client"),
            daemon=True,
        )

        client_to_target.start()
        target_to_client.start()

        while self._is_running() and not stop_event.is_set():
            time.sleep(0.1)

        stop_event.set()

        # Wake any pump blocked in recv().
        for sock in (sock_a, sock_b):
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        client_to_target.join(timeout=2)
        target_to_client.join(timeout=2)

        if client_to_target.is_alive():
            print("[TLSWorker] ⚠️ client -> target " "pump did not stop cleanly")

        if target_to_client.is_alive():
            print("[TLSWorker] ⚠️ target -> client " "pump did not stop cleanly")

        print("[TLSWorker] TLS forwarding loop stopped")

    # =========================
    # UTILS
    # =========================

    @staticmethod
    def _safe_close(sock: socket.socket | ssl.SSLSocket) -> None:
        try:
            sock.close()
        except OSError:
            pass
