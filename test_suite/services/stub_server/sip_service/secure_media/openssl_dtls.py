from __future__ import annotations

import logging
import socket

from .dtls import (
    DEFAULT_DTLS_SRTP_PROFILES,
    DTLSConnection,
    DTLSContext,
    DTLSRole,
    SRTPKeys,
    derive_srtp_keys,
    get_exporter_length,
)


class OpenSSLDTLS:
    """
    Public DTLS-SRTP facade.

    The rest of SipService uses this class instead of importing internal
    OpenSSL context, connection, exporter, or fingerprint components.
    """

    def __init__(
        self,
        role: DTLSRole | str,
        udp_socket: socket.socket,
        certificate_file: str,
        private_key_file: str,
        handshake_timeout: float = 10.0,
        srtp_profiles: tuple[str, ...] = (DEFAULT_DTLS_SRTP_PROFILES),
        cipher_list: str = "DEFAULT",
        log: logging.Logger | None = None,
    ):
        self.log = log or logging.getLogger("OpenSSLDTLS")

        self.context = DTLSContext(
            role=role,
            certificate_file=certificate_file,
            private_key_file=private_key_file,
            srtp_profiles=srtp_profiles,
            cipher_list=cipher_list,
            log=self.log,
        )

        try:
            self.connection = DTLSConnection(
                context=self.context,
                udp_socket=udp_socket,
                handshake_timeout=handshake_timeout,
                log=self.log,
            )
        except Exception:
            self.context.close()
            raise

        self._closed = False

    @property
    def role(self) -> DTLSRole:
        return self.context.role

    @property
    def handshake_complete(self) -> bool:
        return self.connection.handshake_complete

    def handshake(self) -> None:
        self.connection.handshake()

    def selected_srtp_profile(self) -> str:
        return self.connection.selected_srtp_profile()

    def peer_fingerprint(
        self,
        digest_name: str = "sha256",
    ) -> str:
        return self.connection.peer_fingerprint(digest_name)

    def verify_peer_fingerprint(
        self,
        expected: str,
        digest_name: str = "sha256",
    ) -> str:
        return self.connection.verify_peer_fingerprint(
            expected=expected,
            digest_name=digest_name,
        )

    def export_keying_material(
        self,
        length: int,
    ) -> bytes:
        return self.connection.export_keying_material(length)

    def derive_srtp_keys(self) -> SRTPKeys:
        """
        Return directional SRTP keys for the negotiated profile.

        The caller does not need to know the RFC 5764 exporter layout.
        """
        if not self.handshake_complete:
            raise RuntimeError("DTLS handshake is not complete")

        negotiated_profile = self.selected_srtp_profile()

        exporter_length = get_exporter_length(negotiated_profile)

        exporter_material = self.export_keying_material(exporter_length)

        return derive_srtp_keys(
            exporter_keying_material=exporter_material,
            role=self.role,
            profile=negotiated_profile,
        )

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        try:
            self.connection.close()
        finally:
            self.context.close()

    def __enter__(
        self,
    ) -> "OpenSSLDTLS":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()
