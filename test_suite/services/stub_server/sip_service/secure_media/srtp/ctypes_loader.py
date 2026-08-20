from __future__ import annotations

import ctypes
import threading

from .errors import (
    SRTPError,
    require_srtp_success,
)


class CryptoPolicy(ctypes.Structure):
    """
    libSRTP 2.5.0 srtp_crypto_policy_t.
    """

    _fields_ = [
        ("cipher_type", ctypes.c_uint32),
        ("cipher_key_len", ctypes.c_int),
        ("auth_type", ctypes.c_uint32),
        ("auth_key_len", ctypes.c_int),
        ("auth_tag_len", ctypes.c_int),
        ("sec_serv", ctypes.c_int),
    ]


class SSRC(ctypes.Structure):
    """
    libSRTP 2.5.0 srtp_ssrc_t.
    """

    _fields_ = [
        ("type", ctypes.c_int),
        ("value", ctypes.c_uint),
    ]


class MasterKey(ctypes.Structure):
    """
    libSRTP 2.5.0 srtp_master_key_t.

    SipService does not currently use MKI, but this structure is part
    of the public srtp_policy_t layout and must be represented exactly.
    """

    _fields_ = [
        (
            "key",
            ctypes.POINTER(ctypes.c_ubyte),
        ),
        (
            "mki_id",
            ctypes.POINTER(ctypes.c_ubyte),
        ),
        ("mki_size", ctypes.c_uint),
    ]


class SRTPPolicy(ctypes.Structure):
    """
    Forward declaration for the linked srtp_policy_t structure.
    """


SRTPPolicy._fields_ = [
    ("ssrc", SSRC),
    ("rtp", CryptoPolicy),
    ("rtcp", CryptoPolicy),
    (
        "key",
        ctypes.POINTER(ctypes.c_ubyte),
    ),
    (
        "keys",
        ctypes.POINTER(ctypes.POINTER(MasterKey)),
    ),
    ("num_master_keys", ctypes.c_ulong),
    ("deprecated_ekt", ctypes.c_void_p),
    ("window_size", ctypes.c_ulong),
    ("allow_repeat_tx", ctypes.c_int),
    (
        "enc_xtn_hdr",
        ctypes.POINTER(ctypes.c_int),
    ),
    ("enc_xtn_hdr_count", ctypes.c_int),
    (
        "next",
        ctypes.POINTER(SRTPPolicy),
    ),
]


class LibSRTPLoader:
    """
    Singleton ctypes binding for libSRTP 2.5.0.

    Supported native library:

        libsrtp2.so.1
    """

    _instance: LibSRTPLoader | None = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> LibSRTPLoader:
        with cls._instance_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialize()
                cls._instance = instance

            return cls._instance

    def _initialize(self) -> None:
        try:
            self.lib = ctypes.CDLL("libsrtp2.so.1")
        except OSError as exc:
            raise SRTPError(
                "Unable to load supported native library " "'libsrtp2.so.1'"
            ) from exc

        self._bind()

        require_srtp_success(
            self.lib.srtp_init(),
            "srtp_init",
        )

    def _bind(self) -> None:
        lib = self.lib

        # -------------------------------------------------------------
        # Global lifecycle
        # -------------------------------------------------------------
        lib.srtp_init.argtypes = []
        lib.srtp_init.restype = ctypes.c_int

        lib.srtp_shutdown.argtypes = []
        lib.srtp_shutdown.restype = ctypes.c_int

        # -------------------------------------------------------------
        # Session lifecycle
        # -------------------------------------------------------------
        lib.srtp_create.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(SRTPPolicy),
        ]
        lib.srtp_create.restype = ctypes.c_int

        lib.srtp_dealloc.argtypes = [
            ctypes.c_void_p,
        ]
        lib.srtp_dealloc.restype = ctypes.c_int

        # -------------------------------------------------------------
        # RTP and RTCP packet processing
        #
        # libSRTP 2.5.0 uses its three-argument in-place API:
        #
        #     srtp_protect(ctx, packet, &length)
        # -------------------------------------------------------------
        for function_name in (
            "srtp_protect",
            "srtp_unprotect",
            "srtp_protect_rtcp",
            "srtp_unprotect_rtcp",
        ):
            function = getattr(
                lib,
                function_name,
            )

            function.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_int),
            ]

            function.restype = ctypes.c_int

        # -------------------------------------------------------------
        # Crypto policy helpers
        # -------------------------------------------------------------
        lib.srtp_crypto_policy_set_rtp_default.argtypes = [
            ctypes.POINTER(CryptoPolicy),
        ]
        lib.srtp_crypto_policy_set_rtp_default.restype = None

        lib.srtp_crypto_policy_set_rtcp_default.argtypes = [
            ctypes.POINTER(CryptoPolicy),
        ]
        lib.srtp_crypto_policy_set_rtcp_default.restype = None

        lib.srtp_crypto_policy_set_aes_cm_128_hmac_sha1_32.argtypes = [
            ctypes.POINTER(CryptoPolicy),
        ]
        lib.srtp_crypto_policy_set_aes_cm_128_hmac_sha1_32.restype = None


def get_libsrtp_loader() -> LibSRTPLoader:
    return LibSRTPLoader()
