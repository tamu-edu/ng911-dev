from __future__ import annotations

import ctypes
import hmac
import re

from .ctypes_loader import OpenSSLLoader
from .errors import (
    OpenSSLError,
    require_pointer,
    require_success,
)


def normalize_fingerprint(
    fingerprint: str,
) -> str:
    """
    Normalize an SDP certificate fingerprint for comparison.

    Examples:

        AA:BB:CC
        aa bb cc
        AABBCC

    all become:

        AABBCC
    """
    return re.sub(
        r"[^0-9A-Fa-f]",
        "",
        fingerprint or "",
    ).upper()


def format_fingerprint(
    fingerprint: str,
) -> str:
    """
    Format a normalized fingerprint using SDP-style colons.
    """
    normalized = normalize_fingerprint(fingerprint)

    return ":".join(
        normalized[index : index + 2]
        for index in range(
            0,
            len(normalized),
            2,
        )
    )


class PeerFingerprint:
    """
    Extract and verify the DTLS peer certificate fingerprint.
    """

    def __init__(
        self,
        loader: OpenSSLLoader,
    ):
        self._loader = loader

    def get(
        self,
        ssl_pointer,
        digest_name: str = "sha256",
    ) -> str:
        certificate = self._loader.ssl.SSL_get1_peer_certificate(ssl_pointer)

        require_pointer(
            self._loader.libraries,
            certificate,
            "SSL_get1_peer_certificate",
        )

        try:
            digest = self._loader.crypto.EVP_get_digestbyname(
                digest_name.encode("ascii")
            )

            if not digest:
                raise OpenSSLError("Unsupported certificate digest " f"{digest_name!r}")

            output = (ctypes.c_ubyte * 64)()

            output_length = ctypes.c_uint(0)

            require_success(
                self._loader.libraries,
                self._loader.crypto.X509_digest(
                    certificate,
                    digest,
                    output,
                    ctypes.byref(output_length),
                ),
                "X509_digest",
            )

            raw_fingerprint = bytes(output[: output_length.value]).hex().upper()

            return format_fingerprint(raw_fingerprint)

        finally:
            self._loader.crypto.X509_free(certificate)

    def verify(
        self,
        ssl_pointer,
        expected: str,
        digest_name: str = "sha256",
    ) -> str:
        """
        Verify the peer certificate against the fingerprint received
        through SDP.

        Returns the actual formatted fingerprint when successful.
        """
        normalized_expected = normalize_fingerprint(expected)

        if not normalized_expected:
            raise ValueError("Expected DTLS peer fingerprint is empty")

        actual = self.get(
            ssl_pointer,
            digest_name,
        )

        normalized_actual = normalize_fingerprint(actual)

        if not hmac.compare_digest(
            normalized_expected,
            normalized_actual,
        ):
            raise OpenSSLError(
                "DTLS peer certificate fingerprint mismatch: "
                f"expected={format_fingerprint(expected)}, "
                f"actual={actual}"
            )

        return actual
