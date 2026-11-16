from __future__ import annotations

import ctypes
import threading
from dataclasses import dataclass

from .errors import OpenSSLError


class SRTPProtectionProfile(ctypes.Structure):
    """
    OpenSSL SRTP_PROTECTION_PROFILE.
    """

    _fields_ = [
        ("name", ctypes.c_char_p),
        ("id", ctypes.c_ulong),
    ]


class TimeVal(ctypes.Structure):
    """
    Native struct timeval used by DTLS timeout handling.
    """

    _fields_ = [
        ("tv_sec", ctypes.c_long),
        ("tv_usec", ctypes.c_long),
    ]


@dataclass(frozen=True)
class OpenSSLLibraries:
    """
    Native OpenSSL libraries supported by TestSuite.
    """

    ssl: ctypes.CDLL
    crypto: ctypes.CDLL


class OpenSSLLoader:
    """
    Direct bindings for:

        OpenSSL 3.0.13
        libssl.so.3
        libcrypto.so.3
    """

    _instance: OpenSSLLoader | None = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> OpenSSLLoader:
        with cls._instance_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialize()
                cls._instance = instance

            return cls._instance

    def _initialize(self) -> None:
        try:
            ssl_library = ctypes.CDLL("libssl.so.3")
        except OSError as exc:
            raise OpenSSLError("Unable to load libssl.so.3") from exc

        try:
            crypto_library = ctypes.CDLL("libcrypto.so.3")
        except OSError as exc:
            raise OpenSSLError("Unable to load libcrypto.so.3") from exc

        self.libraries = OpenSSLLibraries(
            ssl=ssl_library,
            crypto=crypto_library,
        )

        self._bind_crypto()
        self._bind_ssl()

    def _bind_crypto(self) -> None:
        crypto = self.libraries.crypto

        # OpenSSL error queue
        crypto.ERR_get_error.argtypes = []
        crypto.ERR_get_error.restype = ctypes.c_ulong

        crypto.ERR_error_string_n.argtypes = [
            ctypes.c_ulong,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        crypto.ERR_error_string_n.restype = None

        # Datagram BIO
        crypto.BIO_new_dgram.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
        ]
        crypto.BIO_new_dgram.restype = ctypes.c_void_p

        crypto.BIO_free.argtypes = [
            ctypes.c_void_p,
        ]
        crypto.BIO_free.restype = ctypes.c_int

        # X509 certificate handling
        crypto.X509_free.argtypes = [
            ctypes.c_void_p,
        ]
        crypto.X509_free.restype = None

        crypto.EVP_get_digestbyname.argtypes = [
            ctypes.c_char_p,
        ]
        crypto.EVP_get_digestbyname.restype = ctypes.c_void_p

        crypto.X509_digest.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_uint),
        ]
        crypto.X509_digest.restype = ctypes.c_int

    def _bind_ssl(self) -> None:
        ssl = self.libraries.ssl

        # DTLS methods
        ssl.DTLS_client_method.argtypes = []
        ssl.DTLS_client_method.restype = ctypes.c_void_p

        ssl.DTLS_server_method.argtypes = []
        ssl.DTLS_server_method.restype = ctypes.c_void_p

        # SSL_CTX lifecycle
        ssl.SSL_CTX_new.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_CTX_new.restype = ctypes.c_void_p

        ssl.SSL_CTX_free.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_CTX_free.restype = None

        # Certificate and private key
        ssl.SSL_CTX_use_certificate_chain_file.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        ssl.SSL_CTX_use_certificate_chain_file.restype = ctypes.c_int

        ssl.SSL_CTX_use_PrivateKey_file.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        ssl.SSL_CTX_use_PrivateKey_file.restype = ctypes.c_int

        ssl.SSL_CTX_check_private_key.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_CTX_check_private_key.restype = ctypes.c_int

        # Verification and ciphers
        ssl.SSL_CTX_set_verify.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        ssl.SSL_CTX_set_verify.restype = None

        ssl.SSL_CTX_set_cipher_list.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        ssl.SSL_CTX_set_cipher_list.restype = ctypes.c_int

        # DTLS-SRTP extension
        ssl.SSL_CTX_set_tlsext_use_srtp.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        ssl.SSL_CTX_set_tlsext_use_srtp.restype = ctypes.c_int

        ssl.SSL_get_selected_srtp_profile.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_get_selected_srtp_profile.restype = ctypes.POINTER(
            SRTPProtectionProfile
        )

        # SSL lifecycle
        ssl.SSL_new.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_new.restype = ctypes.c_void_p

        ssl.SSL_free.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_free.restype = None

        ssl.SSL_set_connect_state.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_set_connect_state.restype = None

        ssl.SSL_set_accept_state.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_set_accept_state.restype = None

        ssl.SSL_set_bio.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        ssl.SSL_set_bio.restype = None

        # Handshake and error handling
        ssl.SSL_do_handshake.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_do_handshake.restype = ctypes.c_int

        ssl.SSL_get_error.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        ssl.SSL_get_error.restype = ctypes.c_int

        ssl.SSL_ctrl.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_long,
            ctypes.c_void_p,
        ]
        ssl.SSL_ctrl.restype = ctypes.c_long

        ssl.SSL_shutdown.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_shutdown.restype = ctypes.c_int

        # Peer certificate
        ssl.SSL_get1_peer_certificate.argtypes = [
            ctypes.c_void_p,
        ]
        ssl.SSL_get1_peer_certificate.restype = ctypes.c_void_p

        # RFC 5764 key exporter
        ssl.SSL_export_keying_material.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_size_t,
            ctypes.c_char_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_int,
        ]
        ssl.SSL_export_keying_material.restype = ctypes.c_int

    @property
    def ssl(self) -> ctypes.CDLL:
        return self.libraries.ssl

    @property
    def crypto(self) -> ctypes.CDLL:
        return self.libraries.crypto


def get_openssl_loader() -> OpenSSLLoader:
    return OpenSSLLoader()
