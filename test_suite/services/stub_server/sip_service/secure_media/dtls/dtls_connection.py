from __future__ import annotations

import ctypes
import logging
import select
import socket
import time

from .constants import (
    BIO_NOCLOSE,
    DTLSRole,
    SSL_ERROR_SSL,
    SSL_ERROR_SYSCALL,
    SSL_ERROR_WANT_READ,
    SSL_ERROR_WANT_WRITE,
    SSL_ERROR_ZERO_RETURN,
)
from .ctypes_loader import (
    OpenSSLLoader,
    TimeVal,
    get_openssl_loader,
)
from .dtls_context import DTLSContext
from .errors import (
    OpenSSLError,
    format_openssl_errors,
    require_pointer,
)
from .exporter import KeyExporter
from .fingerprint import PeerFingerprint

DTLS_CTRL_GET_TIMEOUT = 73
DTLS_CTRL_HANDLE_TIMEOUT = 74


class DTLSConnection:
    """
    Own one native OpenSSL SSL object attached to a connected UDP socket.

    Socket ownership remains with the caller. The datagram BIO is created
    with BIO_NOCLOSE, so freeing the SSL object does not close the socket.
    """

    def __init__(
        self,
        context: DTLSContext,
        udp_socket: socket.socket,
        handshake_timeout: float = 10.0,
        log: logging.Logger | None = None,
    ):
        if udp_socket.type & socket.SOCK_DGRAM == 0:
            raise ValueError("DTLSConnection requires a UDP socket")

        self.context = context
        self.socket = udp_socket
        self.handshake_timeout = float(handshake_timeout)

        if self.handshake_timeout <= 0:
            raise ValueError("DTLS handshake timeout must be greater than zero")

        self.log = log or logging.getLogger("DTLSConnection")

        self._loader: OpenSSLLoader = get_openssl_loader()

        self._ssl: ctypes.c_void_p | None = None
        self._closed = False
        self._handshake_complete = False

        self._fingerprint = PeerFingerprint(self._loader)

        self._exporter = KeyExporter(self._loader)

        self._create_ssl()

    @property
    def ssl(self) -> ctypes.c_void_p:
        if self._ssl is None:
            raise OpenSSLError("DTLS connection is closed")

        return self._ssl

    @property
    def handshake_complete(self) -> bool:
        return self._handshake_complete

    def _create_ssl(self) -> None:
        ssl_pointer = self._loader.ssl.SSL_new(self.context.ctx)

        require_pointer(
            self._loader.libraries,
            ssl_pointer,
            "SSL_new",
        )

        bio = self._loader.crypto.BIO_new_dgram(
            self.socket.fileno(),
            BIO_NOCLOSE,
        )

        if not bio:
            self._loader.ssl.SSL_free(ssl_pointer)

            require_pointer(
                self._loader.libraries,
                bio,
                "BIO_new_dgram",
            )

        # SSL_set_bio transfers ownership of the BIO to the SSL object.
        # The same datagram BIO is used for reading and writing.
        self._loader.ssl.SSL_set_bio(
            ssl_pointer,
            bio,
            bio,
        )

        self._ssl = ssl_pointer

        if self.context.role == DTLSRole.CLIENT:
            self._loader.ssl.SSL_set_connect_state(self.ssl)
        else:
            self._loader.ssl.SSL_set_accept_state(self.ssl)

    def handshake(self) -> None:
        """
        Complete the DTLS handshake.

        OpenSSL's DTLS timeout controls are invoked so handshake flights
        can be retransmitted when UDP packets are lost.
        """
        if self._handshake_complete:
            return

        if self._closed:
            raise OpenSSLError("Cannot handshake a closed DTLS connection")

        original_blocking = self.socket.getblocking()

        self.socket.setblocking(False)

        deadline = time.monotonic() + self.handshake_timeout

        try:
            while True:
                result = self._loader.ssl.SSL_do_handshake(self.ssl)

                if result == 1:
                    self._handshake_complete = True

                    self.log.info(
                        "DTLS handshake completed with %s",
                        self._peer_description(),
                    )
                    return

                error = self._loader.ssl.SSL_get_error(
                    self.ssl,
                    result,
                )

                if error not in {
                    SSL_ERROR_WANT_READ,
                    SSL_ERROR_WANT_WRITE,
                }:
                    self._raise_handshake_error(error)

                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    raise TimeoutError(
                        "DTLS handshake timed out after "
                        f"{self.handshake_timeout} seconds"
                    )

                wait_time = min(
                    remaining,
                    self._get_dtls_timeout(default=0.2),
                )

                if error == SSL_ERROR_WANT_READ:
                    readable, _, _ = select.select(
                        [self.socket],
                        [],
                        [],
                        wait_time,
                    )

                    if not readable:
                        self._handle_dtls_timeout()

                else:
                    _, writable, _ = select.select(
                        [],
                        [self.socket],
                        [],
                        wait_time,
                    )

                    if not writable:
                        self._handle_dtls_timeout()

        finally:
            self.socket.setblocking(original_blocking)

    def _get_dtls_timeout(
        self,
        default: float,
    ) -> float:
        timeout = TimeVal()

        result = self._loader.ssl.SSL_ctrl(
            self.ssl,
            DTLS_CTRL_GET_TIMEOUT,
            0,
            ctypes.byref(timeout),
        )

        if result <= 0:
            return default

        timeout_seconds = float(timeout.tv_sec) + float(timeout.tv_usec) / 1_000_000.0

        if timeout_seconds <= 0:
            return 0.001

        return min(
            timeout_seconds,
            default,
        )

    def _handle_dtls_timeout(self) -> None:
        result = self._loader.ssl.SSL_ctrl(
            self.ssl,
            DTLS_CTRL_HANDLE_TIMEOUT,
            0,
            None,
        )

        if result < 0:
            raise OpenSSLError(
                "DTLS timeout handling failed: "
                f"{format_openssl_errors(self._loader.libraries)}"
            )

    def selected_srtp_profile(self) -> str:
        if not self._handshake_complete:
            raise OpenSSLError("DTLS handshake is not complete")

        profile_pointer = self._loader.ssl.SSL_get_selected_srtp_profile(self.ssl)

        if not profile_pointer or not profile_pointer.contents.name:
            raise OpenSSLError("DTLS handshake did not negotiate an SRTP profile")

        return profile_pointer.contents.name.decode("ascii")

    def peer_fingerprint(
        self,
        digest_name: str = "sha256",
    ) -> str:
        if not self._handshake_complete:
            raise OpenSSLError("DTLS handshake is not complete")

        return self._fingerprint.get(
            self.ssl,
            digest_name,
        )

    def verify_peer_fingerprint(
        self,
        expected: str,
        digest_name: str = "sha256",
    ) -> str:
        if not self._handshake_complete:
            raise OpenSSLError("DTLS handshake is not complete")

        return self._fingerprint.verify(
            self.ssl,
            expected,
            digest_name,
        )

    def export_keying_material(
        self,
        length: int,
    ) -> bytes:
        if not self._handshake_complete:
            raise OpenSSLError("DTLS handshake is not complete")

        return self._exporter.export(
            self.ssl,
            length,
        )

    def _raise_handshake_error(
        self,
        error: int,
    ) -> None:
        if error == SSL_ERROR_ZERO_RETURN:
            raise OpenSSLError("DTLS peer closed the connection during handshake")

        if error == SSL_ERROR_SYSCALL:
            raise OpenSSLError(
                "DTLS handshake failed at the socket layer: "
                f"{format_openssl_errors(self._loader.libraries)}"
            )

        if error == SSL_ERROR_SSL:
            raise OpenSSLError(
                "DTLS protocol handshake failed: "
                f"{format_openssl_errors(self._loader.libraries)}"
            )

        raise OpenSSLError(
            "DTLS handshake failed with SSL error "
            f"{error}: "
            f"{format_openssl_errors(self._loader.libraries)}"
        )

    def _peer_description(self) -> str:
        try:
            return str(self.socket.getpeername())
        except OSError:
            return "unknown peer"

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        ssl_pointer = self._ssl
        self._ssl = None
        self._handshake_complete = False

        if ssl_pointer is not None:
            try:
                self._loader.ssl.SSL_shutdown(ssl_pointer)
            except Exception as exc:
                self.log.debug(exc)

            self._loader.ssl.SSL_free(ssl_pointer)

        self.log.debug("DTLS connection closed")

    def __enter__(
        self,
    ) -> "DTLSConnection":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()
