from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MediaSecurityMode(str, Enum):
    """
    Security mode derived from the SDP media protocol and attributes.
    """

    RTP = "rtp"
    SDES_SRTP = "sdes_srtp"
    DTLS_SRTP = "dtls_srtp"


@dataclass(frozen=True)
class SDESCryptoAttribute:
    """
    Parsed SDP a=crypto attribute.

    Example:

        a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:BASE64VALUE
    """

    tag: int
    suite: str
    key_params: str
    session_params: tuple[str, ...] = ()


@dataclass(frozen=True)
class SDPFingerprint:
    """
    Parsed SDP a=fingerprint attribute.
    """

    algorithm: str
    value: str


@dataclass(frozen=True)
class RTPMap:
    """
    Parsed SDP a=rtpmap attribute.
    """

    payload_type: int
    encoding: str
    clock_rate: int
    channels: Optional[int] = None


@dataclass(frozen=True)
class MediaDescription:
    """
    Parsed SDP audio-media description.

    Supports:

    - RTP/AVP and RTP/AVPF;
    - RTP/SAVP and RTP/SAVPF using SDES-SRTP;
    - UDP/TLS/RTP/SAVP and UDP/TLS/RTP/SAVPF using DTLS-SRTP.
    """

    ip: Optional[str]
    port: Optional[int]
    protocol: str
    formats: tuple[str, ...]
    security_mode: MediaSecurityMode

    crypto: tuple[SDESCryptoAttribute, ...] = ()
    fingerprint: Optional[SDPFingerprint] = None
    setup: Optional[str] = None

    rtcp_port: Optional[int] = None
    rtcp_ip: Optional[str] = None
    rtcp_mux: bool = False

    rtp_maps: dict[int, RTPMap] = field(default_factory=dict)


_CONNECTION_RE = re.compile(
    r"^\s*c=\s*IN\s+(IP4|IP6)\s+(\S+)\s*$",
    re.IGNORECASE,
)

_MEDIA_RE = re.compile(
    r"^\s*m=\s*audio\s+(\d+)\s+(\S+)(?:\s+(.+))?\s*$",
    re.IGNORECASE,
)

_CRYPTO_RE = re.compile(
    r"^\s*a=crypto:(\d+)\s+(\S+)\s+(\S+)(?:\s+(.+))?\s*$",
    re.IGNORECASE,
)

_FINGERPRINT_RE = re.compile(
    r"^\s*a=fingerprint:(\S+)\s+(.+?)\s*$",
    re.IGNORECASE,
)

_SETUP_RE = re.compile(
    r"^\s*a=setup:(active|passive|actpass|holdconn)\s*$",
    re.IGNORECASE,
)

_RTCP_RE = re.compile(
    r"^\s*a=rtcp:(\d+)" r"(?:\s+IN\s+(?:IP4|IP6)\s+(\S+))?\s*$",
    re.IGNORECASE,
)

_RTCP_MUX_RE = re.compile(
    r"^\s*a=rtcp-mux\s*$",
    re.IGNORECASE,
)

_RTPMAP_RE = re.compile(
    r"^\s*a=rtpmap:(\d+)\s+" r"([^/\s]+)/(\d+)(?:/(\d+))?\s*$",
    re.IGNORECASE,
)


def _resolve_security_mode(
    protocol: str,
    crypto: tuple[SDESCryptoAttribute, ...],
    fingerprint: Optional[SDPFingerprint],
) -> MediaSecurityMode:
    normalized = (protocol or "").strip().upper()

    if normalized in {
        "UDP/TLS/RTP/SAVP",
        "UDP/TLS/RTP/SAVPF",
    }:
        return MediaSecurityMode.DTLS_SRTP

    if normalized in {
        "RTP/SAVP",
        "RTP/SAVPF",
    }:
        # RTP/SAVP normally uses SDES-SRTP in this implementation.
        # A fingerprint is not sufficient to make it DTLS-SRTP unless
        # the media protocol explicitly contains UDP/TLS.
        return MediaSecurityMode.SDES_SRTP

    if crypto:
        return MediaSecurityMode.SDES_SRTP

    if fingerprint and normalized.startswith("UDP/TLS/"):
        return MediaSecurityMode.DTLS_SRTP

    return MediaSecurityMode.RTP


def parse_audio_media_description(
    sdp_text: str,
) -> Optional[MediaDescription]:
    """
    Parse the first SDP audio media section.

    Session-level attributes are inherited by the audio section where
    applicable. Media-level values override session-level values.

    Returns None when no audio media line exists.
    """
    if not sdp_text:
        return None

    lines = [
        line.strip()
        for line in sdp_text.replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .split("\n")
        if line.strip()
    ]

    session_ip: Optional[str] = None
    media_ip: Optional[str] = None

    session_fingerprint: Optional[SDPFingerprint] = None
    media_fingerprint: Optional[SDPFingerprint] = None

    session_setup: Optional[str] = None
    media_setup: Optional[str] = None

    media_port: Optional[int] = None
    media_protocol = ""
    media_formats: tuple[str, ...] = ()

    crypto_attributes: list[SDESCryptoAttribute] = []

    rtcp_port: Optional[int] = None
    rtcp_ip: Optional[str] = None
    rtcp_mux = False

    rtp_maps: dict[int, RTPMap] = {}

    in_audio_section = False
    found_audio = False

    for line in lines:
        media_match = _MEDIA_RE.match(line)

        if media_match:
            if found_audio:
                # Stop when the next media section begins.
                break

            found_audio = True
            in_audio_section = True

            try:
                media_port = int(media_match.group(1))
            except ValueError:
                media_port = None

            media_protocol = (media_match.group(2) or "").strip()

            media_formats = tuple((media_match.group(3) or "").split())

            continue

        if line.lower().startswith("m="):
            if found_audio:
                break

            in_audio_section = False
            continue

        connection_match = _CONNECTION_RE.match(line)

        if connection_match:
            connection_ip = connection_match.group(2).strip()

            if in_audio_section:
                media_ip = connection_ip
            elif not found_audio:
                session_ip = connection_ip

            continue

        fingerprint_match = _FINGERPRINT_RE.match(line)

        if fingerprint_match:
            fingerprint = SDPFingerprint(
                algorithm=(fingerprint_match.group(1).strip().lower()),
                value=(fingerprint_match.group(2).strip()),
            )

            if in_audio_section:
                media_fingerprint = fingerprint
            elif not found_audio:
                session_fingerprint = fingerprint

            continue

        setup_match = _SETUP_RE.match(line)

        if setup_match:
            setup_value = setup_match.group(1).lower()

            if in_audio_section:
                media_setup = setup_value
            elif not found_audio:
                session_setup = setup_value

            continue

        if not in_audio_section:
            continue

        crypto_match = _CRYPTO_RE.match(line)

        if crypto_match:
            session_params = tuple((crypto_match.group(4) or "").split())

            crypto_attributes.append(
                SDESCryptoAttribute(
                    tag=int(crypto_match.group(1)),
                    suite=(crypto_match.group(2).strip()),
                    key_params=(crypto_match.group(3).strip()),
                    session_params=session_params,
                )
            )
            continue

        rtcp_match = _RTCP_RE.match(line)

        if rtcp_match:
            try:
                rtcp_port = int(rtcp_match.group(1))
            except ValueError:
                rtcp_port = None

            rtcp_ip = rtcp_match.group(2).strip() if rtcp_match.group(2) else None
            continue

        if _RTCP_MUX_RE.match(line):
            rtcp_mux = True
            continue

        rtpmap_match = _RTPMAP_RE.match(line)

        if rtpmap_match:
            payload_type = int(rtpmap_match.group(1))

            channels = int(rtpmap_match.group(4)) if rtpmap_match.group(4) else None

            rtp_maps[payload_type] = RTPMap(
                payload_type=payload_type,
                encoding=(rtpmap_match.group(2).strip()),
                clock_rate=int(rtpmap_match.group(3)),
                channels=channels,
            )

    if not found_audio:
        return None

    crypto_tuple = tuple(crypto_attributes)

    fingerprint = media_fingerprint or session_fingerprint

    setup = media_setup or session_setup

    security_mode = _resolve_security_mode(
        protocol=media_protocol,
        crypto=crypto_tuple,
        fingerprint=fingerprint,
    )

    return MediaDescription(
        ip=media_ip or session_ip,
        port=media_port,
        protocol=media_protocol,
        formats=media_formats,
        security_mode=security_mode,
        crypto=crypto_tuple,
        fingerprint=fingerprint,
        setup=setup,
        rtcp_port=rtcp_port,
        rtcp_ip=rtcp_ip,
        rtcp_mux=rtcp_mux,
        rtp_maps=rtp_maps,
    )


def parse_sdp_connection_and_audio_port(
    sdp_text: str,
) -> tuple[Optional[str], Optional[int]]:
    """
    Backward-compatible wrapper used by the existing ScenarioRunner.

    Returns:

        (audio_ip, audio_port)
    """
    try:
        description = parse_audio_media_description(sdp_text)
    except Exception as exc:
        logging.getLogger("LoggerService").debug(exc)

        return None, None

    if description is None:
        return None, None

    return (
        description.ip,
        description.port,
    )
