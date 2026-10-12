from __future__ import annotations

import ctypes

from .constants import (
    DTLS_SRTP_EXPORTER_LABEL,
)
from .ctypes_loader import OpenSSLLoader
from .errors import require_success


class KeyExporter:
    """
    OpenSSL RFC 5705 key exporter used by DTLS-SRTP.

    RFC 5764 defines the exporter label:

        EXTRACTOR-dtls_srtp
    """

    def __init__(
        self,
        loader: OpenSSLLoader,
    ):
        self._loader = loader

    def export(
        self,
        ssl_pointer,
        length: int,
    ) -> bytes:
        if length <= 0:
            raise ValueError("Exporter length must be greater than zero")

        output = (ctypes.c_ubyte * length)()

        require_success(
            self._loader.libraries,
            self._loader.ssl.SSL_export_keying_material(
                ssl_pointer,
                output,
                length,
                DTLS_SRTP_EXPORTER_LABEL,
                len(DTLS_SRTP_EXPORTER_LABEL),
                None,
                0,
                0,
            ),
            "SSL_export_keying_material",
        )

        return bytes(output)
