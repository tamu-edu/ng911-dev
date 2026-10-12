from __future__ import annotations

import logging
import socket
import ssl
import threading
import time

from msrp_message import (
    MSRPMessage,
    extract_msrp_message,
)


class MSRPTransport:
    """
    Connection-oriented transport for MSRP and MSRPS.

    Responsibilities:

    - TCP listener lifecycle;
    - TCP client connection establishment;
    - optional TLS wrapping for MSRPS;
    - stream buffering;
    - extraction of complete MSRP messages;
    - deterministic connection shutdown.

    MSRP framing itself belongs to msrp_message.py.
    """

    def __init__(
        self,
        bind_ip: str,
        bind_port: int = 0,
        remote_ip: str = "",
        remote_port: int = 0,
        secure: bool = False,
        server_ssl_context: ssl.SSLContext | None = None,
        client_ssl_context: ssl.SSLContext | None = None,
        server_hostname: str | None = None,
        connect_timeout: float = 5.0,
        log: logging.Logger | None = None,
    ):
        self.bind = (
            bind_ip,
            int(bind_port),
        )

        self.remote = (
            remote_ip,
            int(remote_port),
        )

        self.secure = bool(secure)

        self.server_ssl_context = server_ssl_context
        self.client_ssl_context = client_ssl_context

        self.server_hostname = server_hostname

        self.connect_timeout = float(connect_timeout)

        self.log = log or logging.getLogger("MSRPTransport")

        self.listener: socket.socket | None = None
        self.conn: socket.socket | ssl.SSLSocket | None = None

        self.peer: tuple[str, int] | None = None

        self._buffer = b""
        self._closed = False

        self._accept_thread: threading.Thread | None = None
        self._accept_ready = threading.Event()
        self._accept_error: Exception | None = None

    @property
    def connected(self) -> bool:
        return self.conn is not None

    @property
    def listening(self) -> bool:
        return self.listener is not None

    @property
    def local_address(self) -> tuple[str, int]:
        if self.conn is not None:
            try:
                local = self.conn.getsockname()

                return (
                    str(local[0]),
                    int(local[1]),
                )
            except OSError:
                pass

        if self.listener is not None:
            local = self.listener.getsockname()

            return (
                str(local[0]),
                int(local[1]),
            )

        return self.bind

    def start_listener(self) -> None:
        """
        Bind and start listening.

        This method intentionally does not block waiting for a connection.
        A passive MSRP/MSRPS endpoint can therefore start its listener
        before the SIP/SDP response is transmitted.
        """

        if self._closed:
            raise RuntimeError("A stopped MSRP transport cannot be restarted")

        if self.listener is not None:
            return

        if self.secure and self.server_ssl_context is None:
            raise RuntimeError("MSRPS listener requires a server SSL context")

        listener = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        listener.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        try:
            listener.bind(self.bind)
            listener.listen(5)
        except Exception:
            listener.close()
            raise

        self.listener = listener

        actual = self.listener.getsockname()

        self.log.info(
            "%s listener started at %s:%s",
            "MSRPS" if self.secure else "MSRP",
            actual[0],
            actual[1],
        )

    def connect(self) -> None:
        """
        Establish an outbound MSRP/MSRPS connection.

        The connection remains open until stop() is called.
        """

        if self._closed:
            raise RuntimeError("A stopped MSRP transport cannot be restarted")

        if self.conn is not None:
            return

        remote_ip, remote_port = self.remote

        if not remote_ip or not remote_port:
            raise RuntimeError(
                "MSRP outbound connection requires remote_ip and remote_port"
            )

        if self.secure and self.client_ssl_context is None:
            raise RuntimeError(
                "MSRPS outbound connection requires a client SSL context"
            )

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        try:
            sock.bind(self.bind)

            sock.settimeout(self.connect_timeout)

            sock.connect(
                (
                    remote_ip,
                    remote_port,
                )
            )

            if self.secure:
                if self.client_ssl_context is None:
                    raise RuntimeError("MSRPS client SSL context is not configured")

                hostname = self.server_hostname

                if hostname is None and self.client_ssl_context.check_hostname:
                    hostname = remote_ip

                sock = self.client_ssl_context.wrap_socket(
                    sock,
                    server_hostname=hostname,
                )

            sock.settimeout(None)

        except Exception:
            sock.close()
            raise

        self.conn = sock

        peer = self.conn.getpeername()

        self.peer = (
            str(peer[0]),
            int(peer[1]),
        )

        local = self.conn.getsockname()

        self.log.info(
            "%s connected %s:%s → %s:%s",
            "MSRPS" if self.secure else "MSRP",
            local[0],
            local[1],
            self.peer[0],
            self.peer[1],
        )

    def accept(
        self,
        timeout: float | None = None,
    ) -> tuple[str, int]:
        """
        Accept one inbound MSRP/MSRPS connection.

        The listener must already have been started using
        start_listener().
        """

        if self._closed:
            raise RuntimeError("MSRP transport is closed")

        if self.conn is not None and self.peer is not None:
            return self.peer

        if self.listener is None:
            raise RuntimeError("MSRP listener is not started")

        self.listener.settimeout(timeout)

        try:
            conn, peer = self.listener.accept()

        except socket.timeout as exc:
            raise TimeoutError("Timed out waiting for MSRP connection") from exc

        finally:
            if self.listener is not None:
                self.listener.settimeout(None)

        try:
            if self.secure:
                if self.server_ssl_context is None:
                    raise RuntimeError("MSRPS server SSL context is not configured")

                conn.settimeout(timeout)

                conn = self.server_ssl_context.wrap_socket(
                    conn,
                    server_side=True,
                )

            conn.settimeout(None)

        except Exception:
            conn.close()
            raise

        self.conn = conn

        self.peer = (
            str(peer[0]),
            int(peer[1]),
        )

        self.log.info(
            "Accepted %s connection from %s:%s",
            "MSRPS" if self.secure else "MSRP",
            self.peer[0],
            self.peer[1],
        )

        return self.peer

    def send(
        self,
        data: bytes,
    ) -> None:
        """
        Send raw MSRP bytes over the established connection.

        For an active endpoint, connect() is performed lazily.
        """

        if self._closed:
            raise RuntimeError("MSRP transport is closed")

        if self.conn is None:
            self.connect()

        if self.conn is None:
            raise RuntimeError("MSRP connection is not established")

        self.conn.sendall(data)

        self.log.debug(
            "%s TX %d bytes",
            "MSRPS" if self.secure else "MSRP",
            len(data),
        )

    def receive(
        self,
        timeout: float = 5.0,
    ) -> MSRPMessage:
        """
        Receive and parse one complete MSRP message.

        TCP may deliver one MSRP message across multiple recv() calls or
        multiple MSRP messages in a single recv() call. The internal
        buffer preserves stream framing correctly.
        """

        if self._closed:
            raise RuntimeError("MSRP transport is closed")

        timeout = float(timeout)

        if timeout <= 0:
            raise ValueError("MSRP receive timeout must be greater than zero")

        deadline = time.monotonic() + timeout

        while True:
            message, remaining = extract_msrp_message(self._buffer)

            if message is not None:
                self._buffer = remaining

                self.log.debug(
                    "%s RX transaction=%s method=%s status=%s body=%dB",
                    "MSRPS" if self.secure else "MSRP",
                    message.transaction_id,
                    message.method,
                    message.status_code,
                    len(message.body),
                )

                return message

            remaining_timeout = deadline - time.monotonic()

            if remaining_timeout <= 0:
                raise TimeoutError("Timed out waiting for complete MSRP message")

            if self.conn is None:
                self.wait_connected(
                    timeout=remaining_timeout,
                )

            if self.conn is None:
                raise RuntimeError("MSRP connection is not established")

            self.conn.settimeout(remaining_timeout)

            try:
                chunk = self.conn.recv(65535)

            except socket.timeout as exc:
                raise TimeoutError("Timed out waiting for MSRP data") from exc

            finally:
                if self.conn is not None:
                    self.conn.settimeout(None)

            if not chunk:
                raise ConnectionError("MSRP peer closed the connection")

            self._buffer += chunk

    def stop(self) -> None:
        """
        Idempotently close the active connection and listener.
        """

        if self._closed:
            return

        self._closed = True

        conn = self.conn
        self.conn = None

        if conn is not None:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                conn.close()
            except OSError as exc:
                self.log.debug(exc)

        listener = self.listener
        self.listener = None

        if listener is not None:
            try:
                listener.close()
            except OSError as exc:
                self.log.debug(exc)

        if (
            self._accept_thread is not None
            and self._accept_thread is not threading.current_thread()
        ):
            self._accept_thread.join(timeout=1.0)

        self._accept_thread = None
        self._accept_ready.set()
        self._accept_error = None

        self.peer = None
        self._buffer = b""

        self.log.info(
            "%s transport stopped",
            "MSRPS" if self.secure else "MSRP",
        )

    def start_accepting(
        self,
        timeout: float | None = None,
    ) -> None:
        """
        Start accepting an inbound MSRP/MSRPS connection in the background.

        This is required for passive MSRPS endpoints because the TLS
        handshake must be serviced independently from SIP scenario
        execution.
        """

        if self._closed:
            raise RuntimeError("MSRP transport is closed")

        if self.conn is not None:
            self._accept_ready.set()
            return

        if self.listener is None:
            raise RuntimeError("MSRP listener is not started")

        if self._accept_thread is not None and self._accept_thread.is_alive():
            return

        self._accept_ready.clear()
        self._accept_error = None

        def _run() -> None:
            try:
                self.accept(
                    timeout=timeout,
                )

            except Exception as exc:
                if not self._closed:
                    self._accept_error = exc

            finally:
                self._accept_ready.set()

        self._accept_thread = threading.Thread(
            target=_run,
            daemon=True,
        )

        self._accept_thread.start()

    def wait_connected(
        self,
        timeout: float,
    ) -> None:
        """
        Wait until an inbound background accept has completed.

        If no background accept was started, accept synchronously.
        """

        if self.conn is not None:
            return

        if self._accept_thread is None and not self._accept_ready.is_set():
            self.accept(
                timeout=timeout,
            )
            return

        if not self._accept_ready.wait(timeout=timeout):
            raise TimeoutError("Timed out waiting for MSRP connection")

        if self._accept_error is not None:
            error = self._accept_error
            self._accept_error = None
            raise error

        if self.conn is None:
            raise RuntimeError("MSRP connection was not established")
