from __future__ import annotations

import logging
import socket
import threading
from typing import Callable

from .dtls import (
    DEFAULT_DTLS_SRTP_PROFILES,
    DTLSRole,
)
from .openssl_dtls import OpenSSLDTLS
from .srtp import SRTPContext

SecureMediaCallback = Callable[
    [bytes, tuple[str, int], bool],
    None,
]


class DTLSSRTPTransport:
    """
    DTLS-SRTP UDP transport.

    The same UDP socket is used for:

    1. DTLS handshake;
    2. SRTP/SRTCP media after the handshake.

    This preserves the negotiated UDP 5-tuple required by DTLS-SRTP.
    """

    def __init__(
        self,
        bind_ip: str,
        bind_port: int,
        remote_ip: str,
        remote_port: int,
        role: DTLSRole | str,
        certificate_file: str,
        private_key_file: str,
        expected_peer_fingerprint: str = "",
        fingerprint_algorithm: str = "sha256",
        srtp_profiles: tuple[str, ...] = (DEFAULT_DTLS_SRTP_PROFILES),
        cipher_list: str = "DEFAULT",
        handshake_timeout: float = 10.0,
        src_ip_filter: str = "",
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

        self.role = role
        self.certificate_file = certificate_file
        self.private_key_file = private_key_file

        self.expected_peer_fingerprint = (expected_peer_fingerprint or "").strip()

        self.fingerprint_algorithm = (fingerprint_algorithm or "sha256").replace(
            "-", ""
        )

        self.srtp_profiles = tuple(srtp_profiles)

        self.cipher_list = cipher_list
        self.handshake_timeout = float(handshake_timeout)

        self.src_ip_filter = (src_ip_filter or "").strip()

        self.log = log or logging.getLogger("DTLSSRTPTransport")

        self.sock: socket.socket | None = None
        self.dtls: OpenSSLDTLS | None = None
        self.srtp: SRTPContext | None = None

        self._stop = threading.Event()
        self._rx_thread: threading.Thread | None = None
        self._closed = False

    @property
    def started(self) -> bool:
        return self.sock is not None and self.dtls is not None and self.srtp is not None

    def start(self) -> None:
        if self.started:
            return

        if self._closed:
            raise RuntimeError("A stopped DTLS-SRTP transport cannot be restarted")

        self._stop.clear()

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        sock.bind(self.bind)

        # DTLS and SRTP are restricted to the peer negotiated through SDP.
        sock.connect(self.remote)

        dtls = OpenSSLDTLS(
            role=self.role,
            udp_socket=sock,
            certificate_file=self.certificate_file,
            private_key_file=self.private_key_file,
            handshake_timeout=self.handshake_timeout,
            srtp_profiles=self.srtp_profiles,
            cipher_list=self.cipher_list,
            log=self.log,
        )

        try:
            dtls.handshake()

            if self.expected_peer_fingerprint:
                actual_fingerprint = dtls.verify_peer_fingerprint(
                    expected=(self.expected_peer_fingerprint),
                    digest_name=(self.fingerprint_algorithm),
                )
            else:
                actual_fingerprint = dtls.peer_fingerprint(
                    digest_name=(self.fingerprint_algorithm)
                )

                self.log.warning(
                    "DTLS peer fingerprint was not configured; "
                    "peer identity was not verified"
                )

            keys = dtls.derive_srtp_keys()

            srtp = SRTPContext(
                tx_key=keys.tx_key,
                rx_key=keys.rx_key,
                profile=keys.profile.profile,
            )

        except Exception:
            dtls.close()
            sock.close()
            raise

        self.sock = sock
        self.dtls = dtls
        self.srtp = srtp

        self.sock.setblocking(True)

        actual_bind = self.sock.getsockname()

        self.log.info(
            "DTLS-SRTP ready at %s:%s → %s:%s " "role=%s profile=%s fingerprint=%s",
            actual_bind[0],
            actual_bind[1],
            self.remote[0],
            self.remote[1],
            self.dtls.role.value,
            keys.profile.dtls_name,
            actual_fingerprint,
        )

    def send_rtp(
        self,
        packet: bytes,
    ) -> None:
        if self.sock is None or self.srtp is None:
            raise RuntimeError("DTLS-SRTP transport is not started")

        protected = self.srtp.protect_rtp(packet)

        self.sock.send(protected)

    def send_rtcp(
        self,
        packet: bytes,
    ) -> None:
        if self.sock is None or self.srtp is None:
            raise RuntimeError("DTLS-SRTP transport is not started")

        protected = self.srtp.protect_rtcp(packet)

        self.sock.send(protected)

    @staticmethod
    def _is_dtls_packet(
        packet: bytes,
    ) -> bool:
        return bool(packet) and 20 <= packet[0] <= 63

    @staticmethod
    def _is_rtp_or_rtcp_packet(
        packet: bytes,
    ) -> bool:
        return bool(packet) and 128 <= packet[0] <= 191

    @staticmethod
    def _is_rtcp_packet(
        packet: bytes,
    ) -> bool:
        return len(packet) >= 2 and 192 <= packet[1] <= 223

    def recv_loop(
        self,
        callback: SecureMediaCallback,
        timeout: float = 0.2,
    ) -> None:
        if self.sock is None or self.srtp is None:
            raise RuntimeError("DTLS-SRTP transport is not started")

        if self._rx_thread and self._rx_thread.is_alive():
            return

        def _loop() -> None:
            while not self._stop.is_set():
                try:
                    if self.sock is None:
                        break

                    self.sock.settimeout(timeout)

                    packet = self.sock.recv(65535)

                except socket.timeout:
                    continue

                except OSError as exc:
                    if not self._stop.is_set():
                        self.log.debug(exc)
                    break

                if self.src_ip_filter and self.remote[0] != self.src_ip_filter:
                    continue

                # Ignore post-handshake DTLS alerts/retransmissions.
                if self._is_dtls_packet(packet):
                    continue

                if not self._is_rtp_or_rtcp_packet(packet):
                    self.log.debug("Ignored unknown packet on " "DTLS-SRTP socket")
                    continue

                is_rtcp = self._is_rtcp_packet(packet)

                try:
                    if is_rtcp:
                        plaintext = self.srtp.unprotect_rtcp(packet)
                    else:
                        plaintext = self.srtp.unprotect_rtp(packet)

                except Exception as exc:
                    self.log.warning(
                        "DTLS-SRTP packet rejected from %s: %s",
                        self.remote,
                        exc,
                    )
                    continue

                try:
                    callback(
                        plaintext,
                        self.remote,
                        is_rtcp,
                    )
                except Exception as exc:
                    self.log.debug(
                        "DTLS-SRTP callback failed: %s",
                        exc,
                    )

        self._rx_thread = threading.Thread(
            target=_loop,
            daemon=True,
        )

        self._rx_thread.start()

    def stop(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._stop.set()

        sock = self.sock
        self.sock = None

        if sock is not None:
            try:
                sock.close()
            except OSError as exc:
                self.log.debug(exc)

        if self._rx_thread and self._rx_thread is not threading.current_thread():
            self._rx_thread.join(timeout=1.0)

        self._rx_thread = None

        try:
            if self.srtp is not None:
                self.srtp.close()
        finally:
            self.srtp = None

        try:
            if self.dtls is not None:
                self.dtls.close()
        finally:
            self.dtls = None

        self.log.info("DTLS-SRTP transport stopped")
