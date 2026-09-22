from __future__ import annotations

from .srtp import SRTPContext


class SRTPProcessor:
    """
    Transport-independent SRTP/SRTCP packet processor.

    The processor owns only the SRTP cryptographic context.

    It does not own:

    - UDP sockets;
    - receiver threads;
    - RTP packet generation;
    - DTLS negotiation.

    The SRTPContext may be initialized from:

    - explicit SDES-SRTP keys;
    - keys derived by DTLS-SRTP;
    - explicit TestSuite scenario values.
    """

    def __init__(
        self,
        context: SRTPContext,
    ):
        self._context = context
        self._closed = False

    @property
    def context(self) -> SRTPContext:
        return self._context

    def protect_rtp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._closed:
            raise RuntimeError("SRTP processor is closed")

        return self._context.protect_rtp(packet)

    def unprotect_rtp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._closed:
            raise RuntimeError("SRTP processor is closed")

        return self._context.unprotect_rtp(packet)

    def protect_rtcp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._closed:
            raise RuntimeError("SRTP processor is closed")

        return self._context.protect_rtcp(packet)

    def unprotect_rtcp(
        self,
        packet: bytes,
    ) -> bytes:
        if self._closed:
            raise RuntimeError("SRTP processor is closed")

        return self._context.unprotect_rtcp(packet)

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._context.close()

    def __enter__(
        self,
    ) -> "SRTPProcessor":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()
