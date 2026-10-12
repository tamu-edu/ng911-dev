from enums import PacketTypeEnum
from services.aux_services.sip_msg_body_services import extract_media_attributes
from services.messages.packet_fetcher import PacketFetcher


def _get_negotiated_media_ports(
    stimulus_invite_message,
    bcf_esrp_invite_message,
    esrp_bcf_ok_message,
    bcf_osp_ok_message,
):
    """
    Extracts negotiated media ports for all four traffic directions:
        - osp_bcf: port BCF announced in its 200 OK to OSP (OSP sends here)
        - bcf_osp: port OSP announced in its original INVITE (BCF sends here)
        - bcf_esrp: port ESRP announced in its 200 OK to BCF (BCF sends here)
        - esrp_bcf: port BCF announced in its INVITE to ESRP (ESRP sends here)

    Returns a dict {route: port} as ints, or None if any of the four
    SDPs is missing / has no media port / has a non-numeric port.
    """
    if not all(
        (
            stimulus_invite_message,
            bcf_esrp_invite_message,
            esrp_bcf_ok_message,
            bcf_osp_ok_message,
        )
    ):
        return None

    stimulus_sdp = extract_media_attributes(
        stimulus_invite_message, return_full_attr=True
    )
    bcf_esrp_invite_sdp = extract_media_attributes(
        bcf_esrp_invite_message, return_full_attr=True
    )
    esrp_bcf_sdp = extract_media_attributes(esrp_bcf_ok_message, return_full_attr=True)
    bcf_osp_sdp = extract_media_attributes(bcf_osp_ok_message, return_full_attr=True)

    osp_invite_port_raw = stimulus_sdp.get("media_port") if stimulus_sdp else None
    bcf_invite_port_raw = (
        bcf_esrp_invite_sdp.get("media_port") if bcf_esrp_invite_sdp else None
    )
    bcf_esrp_port_raw = esrp_bcf_sdp.get("media_port") if esrp_bcf_sdp else None
    osp_bcf_port_raw = bcf_osp_sdp.get("media_port") if bcf_osp_sdp else None

    if not all(
        (osp_invite_port_raw, bcf_invite_port_raw, bcf_esrp_port_raw, osp_bcf_port_raw)
    ):
        return None

    try:
        return {
            "osp_bcf": int(osp_bcf_port_raw),
            "bcf_osp": int(osp_invite_port_raw),
            "bcf_esrp": int(bcf_esrp_port_raw),
            "esrp_bcf": int(bcf_invite_port_raw),
        }
    except ValueError:
        return None


def _is_msrps(sdp: dict) -> bool:
    """True if the SDP media line declares MSRP over TLS (TCP/TLS/MSRP)."""
    transport = sdp.get("media_transport") if sdp else None
    return transport == "TCP/TLS/MSRP"


def _rtp_packets_present(fetcher: PacketFetcher, ports: dict) -> bool:
    """
    Confirms at least one RTP packet is present on all four traffic
    directions, filtered by each direction's negotiated port. Covers
    audio, video, and real-time text (RTT) - all carried over RTP.
    """
    routes = ["osp_bcf", "bcf_osp", "bcf_esrp", "esrp_bcf"]

    for route in routes:
        packets = fetcher.get_rtp_messages(route, dst_port=ports[route])
        if not packets:
            return False

    return True


def _msrp_packets_present(
    fetcher: PacketFetcher, route: str, port: int, is_secure: bool
) -> bool:
    """
    Confirms at least one MSRP packet is present on the given route/port.

    For declared-secure (MSRPS) legs, tries the raw decrypted-bytes path
    first (no msrp dissector exists for decrypted TLS data). If that
    finds nothing, falls back to checking for plain MSRP packets, in
    case the leg turned out to be unencrypted despite being declared
    as MSRPS in SDP (e.g. TLS handshake failed, or the SDP declaration
    doesn't match the actual traffic).
    """
    if not is_secure:
        packets = fetcher.get_msrp_messages(route, dst_port=port)
        return bool(packets)

    if _decrypted_msrp_present(fetcher, route, port):
        return True

    packets = fetcher.get_msrp_messages(route, dst_port=port)
    return bool(packets)


def _decrypted_msrp_present(fetcher: PacketFetcher, route: str, port: int) -> bool:
    """
    Checks decrypted TCP application data for MSRP-like content
    """
    packets = fetcher.get_messages(
        route, dst_port=port, packet_type=[PacketTypeEnum.TCP]
    )
    if not packets:
        return False

    for packet in packets:
        if not hasattr(packet, "data"):
            continue
        try:
            raw_bytes = bytes.fromhex(packet.data.data.replace(":", ""))
            text = raw_bytes.decode("utf-8", errors="replace")
        except (AttributeError, ValueError):
            continue

        if text.strip().startswith("MSRP ") or "MSRP/1.0" in text:
            return True

    return False


def _get_media_transports(stimulus_sdp, bcf_esrp_invite_message):
    """
    Determines whether each leg (osp_bcf and bcf_esrp) uses plain MSRP
    or MSRPS

    :param stimulus_sdp: Already-extracted SDP attributes dict for the
        OSP INVITE
    :param bcf_esrp_invite_message: Raw INVITE message BCF sends to ESRP.
    :return: {"osp_bcf": bool, "bcf_esrp": bool} True means secure
        (MSRPS), or None if either SDP is missing/unreadable.
    """
    if not stimulus_sdp or not bcf_esrp_invite_message:
        return None

    bcf_esrp_invite_sdp = extract_media_attributes(
        bcf_esrp_invite_message, return_full_attr=True
    )
    if not bcf_esrp_invite_sdp:
        return None

    return {
        "osp_bcf": _is_msrps(stimulus_sdp),
        "bcf_esrp": _is_msrps(bcf_esrp_invite_sdp),
    }


def verify_media_established(
    fetcher: PacketFetcher,
    stimulus_invite_message,
    bcf_esrp_invite_message,
    esrp_bcf_ok_message,
    bcf_osp_ok_message,
) -> bool:
    """
    Verifies media is established end-to-end (OSP <-> BCF <-> ESRP,
    BCF-anchored): confirms all four SDPs negotiate a media port, then
    confirms real media packets are observed on all four traffic
    directions. Handles RTP-based media (audio/video/RTT) and
    MSRP/MSRPS (message) transparently - each leg's security (plain
    MSRP vs MSRPS) is determined independently, since the two legs can
    differ.
    """
    stimulus_sdp = extract_media_attributes(
        stimulus_invite_message, return_full_attr=True
    )

    ports = _get_negotiated_media_ports(
        stimulus_invite_message,
        bcf_esrp_invite_message,
        esrp_bcf_ok_message,
        bcf_osp_ok_message,
    )
    if ports is None:
        return False

    media_type = stimulus_sdp.get("media_type") if stimulus_sdp else None

    if media_type != "message":
        return _rtp_packets_present(fetcher, ports)

    transports = _get_media_transports(stimulus_sdp, bcf_esrp_invite_message)
    if transports is None:
        return False

    route_is_secure = {
        "osp_bcf": transports["osp_bcf"],
        "bcf_osp": transports["osp_bcf"],
        "bcf_esrp": transports["bcf_esrp"],
        "esrp_bcf": transports["bcf_esrp"],
    }

    for route, is_secure in route_is_secure.items():
        if not _msrp_packets_present(fetcher, route, ports[route], is_secure):
            return False

    return True


def get_sip_status_codes(packet) -> list[int]:
    """
    Returns the status codes of all SIP response layers in a frame
    """
    codes = []
    for layer in getattr(packet, "layers", []):
        if getattr(layer, "layer_name", None) != "sip":
            continue
        raw_code = getattr(layer, "status_code", None)
        try:
            codes.append(int(raw_code))
        except (TypeError, ValueError):
            continue
    return codes


def get_final_sip_status_code(packet) -> int | None:
    """
    Returns the first final status code (>= 200) found in the frame, or
    None if the frame only contains provisional (1xx) responses or no
    responses at all.
    """
    return next((code for code in get_sip_status_codes(packet) if code >= 200), None)
