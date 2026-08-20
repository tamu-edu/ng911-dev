from __future__ import annotations

import base64
import binascii
import ctypes
import os
import threading

from .constants import (
    DEFAULT_REPLAY_WINDOW,
    SRTCP_MAX_TRAILER_LENGTH,
    SRTP_MAX_TRAILER_LENGTH,
    SSRC_ANY_INBOUND,
    SSRC_ANY_OUTBOUND,
    SRTPProfile,
    SRTPProfileSpec,
    get_srtp_profile,
)
from .ctypes_loader import (
    LibSRTPLoader,
    SRTPPolicy,
    SSRC,
    get_libsrtp_loader,
)
from .errors import (
    SRTPError,
    require_srtp_success,
)


def generate_srtp_key(
    profile: SRTPProfile | str = (SRTPProfile.AES_CM_128_HMAC_SHA1_80),
) -> bytes:
    """
    Generate raw SRTP master-key and master-salt material.
    """
    specification = get_srtp_profile(profile)

    return os.urandom(specification.key_material_length)


def generate_srtp_inline_key(
    profile: SRTPProfile | str = (SRTPProfile.AES_CM_128_HMAC_SHA1_80),
) -> str:
    """
    Generate Base64 material suitable for an SDP a=crypto inline key.
    """
    return base64.b64encode(generate_srtp_key(profile)).decode("ascii")


def decode_srtp_key(
    value: bytes | str,
    profile: SRTPProfile | str,
) -> bytes:
    """
    Convert raw or SDP inline key material to bytes.

    Supported string forms:

        BASE64VALUE
        inline:BASE64VALUE
        inline:BASE64VALUE|2^20|1:4
    """
    specification = get_srtp_profile(profile)

    if isinstance(value, bytes):
        material = value

    else:
        encoded = (value or "").strip()

        if encoded.lower().startswith("inline:"):
            encoded = encoded[len("inline:") :]

        encoded = encoded.split(
            "|",
            1,
        )[0].strip()

        if not encoded:
            raise ValueError("SRTP key material is empty")

        # Accept SDP values whose Base64 padding was omitted.
        encoded += "=" * (-len(encoded) % 4)

        try:
            material = base64.b64decode(
                encoded,
                validate=True,
            )
        except (
            binascii.Error,
            ValueError,
        ) as exc:
            raise ValueError("SRTP key material is not valid Base64") from exc

    if len(material) != specification.key_material_length:
        raise ValueError(
            f"{specification.sdes_name} requires "
            f"{specification.key_material_length} bytes of "
            f"key material, received {len(material)}"
        )

    return material


class _SRTPSession:
    """
    Own one native libSRTP session.

    A distinct session is created for each direction because inbound
    and outbound media may use different keys.
    """

    def __init__(
        self,
        key: bytes,
        profile: SRTPProfileSpec,
        inbound: bool,
        replay_window: int,
        allow_repeat_tx: bool,
        loader: LibSRTPLoader,
    ):
        self._loader = loader
        self._profile = profile
        self._inbound = inbound
        self._session: ctypes.c_void_p | None = None
        self._closed = False

        self._key_buffer = (ctypes.c_ubyte * len(key)).from_buffer_copy(key)

        self._policy = SRTPPolicy()

        ctypes.memset(
            ctypes.byref(self._policy),
            0,
            ctypes.sizeof(self._policy),
        )

        self._configure_policy(
            replay_window=replay_window,
            allow_repeat_tx=allow_repeat_tx,
        )

        self._create_session()

    @property
    def pointer(self) -> ctypes.c_void_p:
        if self._session is None:
            raise SRTPError("SRTP session is closed")

        return self._session

    def _configure_policy(
        self,
        replay_window: int,
        allow_repeat_tx: bool,
    ) -> None:
        lib = self._loader.lib

        if self._profile.profile == SRTPProfile.AES_CM_128_HMAC_SHA1_80:
            lib.srtp_crypto_policy_set_rtp_default(ctypes.byref(self._policy.rtp))
        else:
            lib.srtp_crypto_policy_set_aes_cm_128_hmac_sha1_32(
                ctypes.byref(self._policy.rtp)
            )

        # RFC 4568 recommends the full authentication tag for SRTCP
        # even when RTP uses AES_CM_128_HMAC_SHA1_32.
        lib.srtp_crypto_policy_set_rtcp_default(ctypes.byref(self._policy.rtcp))

        self._policy.ssrc = SSRC(
            type=(SSRC_ANY_INBOUND if self._inbound else SSRC_ANY_OUTBOUND),
            value=0,
        )

        self._policy.key = ctypes.cast(
            self._key_buffer,
            ctypes.POINTER(ctypes.c_ubyte),
        )

        self._policy.keys = None
        self._policy.num_master_keys = 0
        self._policy.deprecated_ekt = None

        self._policy.window_size = int(replay_window)

        self._policy.allow_repeat_tx = int(bool(allow_repeat_tx and not self._inbound))

        self._policy.enc_xtn_hdr = ctypes.POINTER(ctypes.c_int)()

        self._policy.enc_xtn_hdr_count = 0

        self._policy.next = ctypes.POINTER(SRTPPolicy)()

    def _create_session(self) -> None:
        session = ctypes.c_void_p()

        require_srtp_success(
            self._loader.lib.srtp_create(
                ctypes.byref(session),
                ctypes.byref(self._policy),
            ),
            "srtp_create",
        )

        self._session = session

    def transform(
        self,
        packet: bytes,
        operation: str,
        trailer_capacity: int,
    ) -> bytes:
        if not packet:
            raise ValueError("SRTP packet cannot be empty")

        capacity = len(packet) + max(
            trailer_capacity,
            0,
        )

        buffer = ctypes.create_string_buffer(capacity)

        ctypes.memmove(
            buffer,
            packet,
            len(packet),
        )

        packet_length = ctypes.c_int(len(packet))

        function = getattr(
            self._loader.lib,
            operation,
        )

        require_srtp_success(
            function(
                self.pointer,
                buffer,
                ctypes.byref(packet_length),
            ),
            operation,
        )

        return bytes(buffer.raw[: packet_length.value])

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        session = self._session
        self._session = None

        if session is not None:
            require_srtp_success(
                self._loader.lib.srtp_dealloc(session),
                "srtp_dealloc",
            )


class SRTPContext:
    """
    Bidirectional SRTP/SRTCP cryptographic context.

    The context is transport-independent. Keys may come from:

    - SDES-SRTP SDP a=crypto attributes;
    - a DTLS-SRTP RFC 5764 exporter;
    - explicit TestSuite scenario configuration.

    It owns no socket and performs no network I/O.
    """

    def __init__(
        self,
        tx_key: bytes | str | None,
        rx_key: bytes | str | None,
        profile: SRTPProfile | str = (SRTPProfile.AES_CM_128_HMAC_SHA1_80),
        replay_window: int = DEFAULT_REPLAY_WINDOW,
        allow_repeat_tx: bool = False,
    ):
        if tx_key is None and rx_key is None:
            raise ValueError("At least one SRTP direction key is required")

        if replay_window <= 0:
            raise ValueError("SRTP replay window must be greater than zero")

        self.profile = get_srtp_profile(profile)

        self._loader = get_libsrtp_loader()

        self._tx_lock = threading.Lock()
        self._rx_lock = threading.Lock()

        self._tx = (
            _SRTPSession(
                key=decode_srtp_key(
                    tx_key,
                    self.profile.profile,
                ),
                profile=self.profile,
                inbound=False,
                replay_window=replay_window,
                allow_repeat_tx=allow_repeat_tx,
                loader=self._loader,
            )
            if tx_key is not None
            else None
        )

        self._rx = (
            _SRTPSession(
                key=decode_srtp_key(
                    rx_key,
                    self.profile.profile,
                ),
                profile=self.profile,
                inbound=True,
                replay_window=replay_window,
                allow_repeat_tx=False,
                loader=self._loader,
            )
            if rx_key is not None
            else None
        )

        self._closed = False

    def protect_rtp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._tx is None:
            raise SRTPError("Outbound SRTP context is not configured")

        with self._tx_lock:
            return self._tx.transform(
                packet,
                "srtp_protect",
                SRTP_MAX_TRAILER_LENGTH,
            )

    def unprotect_rtp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._rx is None:
            raise SRTPError("Inbound SRTP context is not configured")

        with self._rx_lock:
            return self._rx.transform(
                packet,
                "srtp_unprotect",
                0,
            )

    def protect_rtcp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._tx is None:
            raise SRTPError("Outbound SRTCP context is not configured")

        with self._tx_lock:
            return self._tx.transform(
                packet,
                "srtp_protect_rtcp",
                SRTCP_MAX_TRAILER_LENGTH,
            )

    def unprotect_rtcp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._rx is None:
            raise SRTPError("Inbound SRTCP context is not configured")

        with self._rx_lock:
            return self._rx.transform(
                packet,
                "srtp_unprotect_rtcp",
                0,
            )

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        errors: list[Exception] = []

        for session in (
            self._tx,
            self._rx,
        ):
            if session is None:
                continue

            try:
                session.close()
            except Exception as exc:
                errors.append(exc)

        self._tx = None
        self._rx = None

        if errors:
            raise SRTPError(
                "One or more SRTP sessions failed to close: "
                + "; ".join(str(error) for error in errors)
            )

    def __enter__(
        self,
    ) -> "SRTPContext":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()
