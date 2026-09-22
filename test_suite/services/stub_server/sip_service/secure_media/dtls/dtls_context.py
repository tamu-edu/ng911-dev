from __future__ import annotations

import ctypes
import logging

from .constants import (
    DEFAULT_DTLS_SRTP_PROFILES,
    DTLSRole,
    SSL_FILETYPE_PEM,
    SSL_VERIFY_NONE,
)
from .ctypes_loader import (
    OpenSSLLoader,
    get_openssl_loader,
)
from .errors import (
    OpenSSLError,
    require_pointer,
    require_success,
    raise_openssl_error,
)


class DTLSContext:
    """
    Owns one immutable OpenSSL SSL_CTX.

    Responsibilities:

    - create SSL_CTX
    - load certificate chain
    - load private key
    - validate key pair
    - configure cipher list
    - advertise DTLS-SRTP profiles
    - release SSL_CTX

    This class NEVER owns:

        - SSL objects
        - sockets
        - BIOs
        - handshakes
    """

    def __init__(
        self,
        role: DTLSRole | str,
        certificate_file: str,
        private_key_file: str,
        srtp_profiles: tuple[str, ...] = DEFAULT_DTLS_SRTP_PROFILES,
        cipher_list: str = "DEFAULT",
        log: logging.Logger | None = None,
    ):
        self.log = log or logging.getLogger("DTLSContext")

        self._loader: OpenSSLLoader = get_openssl_loader()

        self._ctx: ctypes.c_void_p | None = None
        self._closed = False

        try:
            self.role = DTLSRole(str(role).lower())
        except ValueError as exc:
            raise ValueError("DTLS role must be client or server") from exc

        self.certificate_file = certificate_file
        self.private_key_file = private_key_file

        self.srtp_profiles = tuple(p.strip() for p in srtp_profiles if p.strip())

        if not self.srtp_profiles:
            raise ValueError("At least one DTLS-SRTP profile is required")

        self.cipher_list = cipher_list or "DEFAULT"

        self._create_context()

    @property
    def ctx(self) -> ctypes.c_void_p:
        if self._ctx is None:
            raise OpenSSLError("DTLS context is closed")

        return self._ctx

    def _create_context(self) -> None:
        ssl = self._loader.ssl

        if self.role == DTLSRole.CLIENT:
            method = ssl.DTLS_client_method()
        else:
            method = ssl.DTLS_server_method()

        require_pointer(
            self._loader.libraries,
            method,
            "DTLS_method",
        )

        self._ctx = ssl.SSL_CTX_new(method)

        require_pointer(
            self._loader.libraries,
            self._ctx,
            "SSL_CTX_new",
        )

        self._load_certificate()
        self._configure_cipher_list()
        self._configure_srtp_profiles()

        ssl.SSL_CTX_set_verify(
            self.ctx,
            SSL_VERIFY_NONE,
            None,
        )

        self.log.debug("DTLS context created.")

    def _load_certificate(
        self,
    ) -> None:
        ssl = self._loader.ssl

        require_success(
            self._loader.libraries,
            ssl.SSL_CTX_use_certificate_chain_file(
                self.ctx,
                self.certificate_file.encode(),
            ),
            "SSL_CTX_use_certificate_chain_file",
        )

        require_success(
            self._loader.libraries,
            ssl.SSL_CTX_use_PrivateKey_file(
                self.ctx,
                self.private_key_file.encode(),
                SSL_FILETYPE_PEM,
            ),
            "SSL_CTX_use_PrivateKey_file",
        )

        require_success(
            self._loader.libraries,
            ssl.SSL_CTX_check_private_key(
                self.ctx,
            ),
            "SSL_CTX_check_private_key",
        )

    def _configure_cipher_list(
        self,
    ) -> None:
        require_success(
            self._loader.libraries,
            self._loader.ssl.SSL_CTX_set_cipher_list(
                self.ctx,
                self.cipher_list.encode(),
            ),
            "SSL_CTX_set_cipher_list",
        )

    def _configure_srtp_profiles(
        self,
    ) -> None:
        profiles = ":".join(self.srtp_profiles).encode()

        result = self._loader.ssl.SSL_CTX_set_tlsext_use_srtp(
            self.ctx,
            profiles,
        )

        if result != 0:
            raise_openssl_error(
                self._loader.libraries,
                "SSL_CTX_set_tlsext_use_srtp",
            )

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        if self._ctx is not None:
            self._loader.ssl.SSL_CTX_free(self._ctx)
            self._ctx = None

        self.log.debug("DTLS context destroyed.")

    def __enter__(
        self,
    ) -> "DTLSContext":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()
