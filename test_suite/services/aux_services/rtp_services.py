import base64
from typing import List, Set, Tuple, Any, Iterable, Union


def get_rtp_attribute_list_attr(message: Any, attr: str) -> List[str]:
    """
    Parses the string representation of the RTP layer to find a specific attribute.
    """
    rtp_layer = getattr(message, "rtp", None)
    if not rtp_layer:
        return []

    attr_lower = attr.lower()
    found_values: List[Any] = []
    for line in str(rtp_layer).splitlines():
        if attr_lower in line.lower() and ": " in line:
            _, attr_value = line.split(": ", 1)
            found_values.append(attr_value)

    return found_values


def get_unique_rtp_attributes_set(
    packets: Iterable[Any], attr_name: str
) -> Set[Tuple[str, ...]]:
    """
    Returns a set of tuples containing unique attributes found across all packets.
    """
    return {
        tuple(values)
        for packet in packets
        # The walrus operator (:=) assigns and checks truthiness in one step
        if (values := get_rtp_attribute_list_attr(packet, attr_name))
    }


def is_attr_list_contains_empty_values(attr_list: List[Any]) -> bool:
    """
    Returns True only if the list is not empty AND all its sub-elements are empty.
    """
    return bool(attr_list) and all(not sublist for sublist in attr_list)


def get_ssrc_value(packet: Any, full_bit: bool = False) -> str:
    """
    Extracts and normalizes the RTP SSRC value from a packet.

    The function retrieves the SSRC from the RTP layer (if present) and returns
    it as a hexadecimal string. The value is normalized to ensure consistent
    formatting regardless of how it appears in the packet (e.g. with or without
    leading zeros).

    Args:
        packet (Any): Packet object.
        full_bit (bool, optional): If True, returns SSRC as a zero-padded 32-bit
            hexadecimal string (e.g. "0x00000444"). If False, returns a compact
            hexadecimal string without leading zeros (e.g. "0x444"). Defaults to False.

    Returns:
        str: Normalized SSRC value as a hexadecimal string, or an empty string
        if the RTP layer or SSRC field is not present or cannot be parsed.

    Examples:
        get_ssrc_value(packet)
        '0x444'

        get_ssrc_value(packet, full_bit=True)
        '0x00000444'
    """

    rtp_layer = getattr(packet, "rtp", None)
    if not rtp_layer:
        return ""
    if not rtp_layer:
        return ""

    ssrc = getattr(rtp_layer, "ssrc", "")
    if not ssrc:
        return ""

    try:
        value = int(ssrc, 16)

        if full_bit:
            return f"0x{value:08x}"
        else:
            return hex(value)

    except ValueError:
        return ""


def is_ssrc_in_any_csrc_message(ssrc: str, csrc_list: Iterable[Iterable[str]]) -> bool:
    """
    Checks if the SSRC exists in ANY of the CSRC sub-lists.
    """
    return any(ssrc in sublist for sublist in csrc_list)


def is_ssrc_in_all_csrc_messages(ssrc: str, csrc_list: Iterable[Iterable[str]]) -> bool:
    """
    Checks if the SSRC exists in ALL of the CSRC sub-lists.
    """
    return all(ssrc in sublist for sublist in csrc_list)


def hex_stream_to_string(hex_stream):
    """Converts a continuous hex string into a full word."""
    try:
        return bytes.fromhex(hex_stream).decode("ascii")
    except ValueError:
        return ""


def hex_str_to_letter(payload: str) -> str:
    """Converts byte '54' or '0x54' to 'T' or bytes sequence to chars"""
    try:
        cleaned = payload.lower().replace("0x", "")
        parts = cleaned.replace(":", " ").split()

        if len(parts) == 1 and len(parts[0]) > 2:
            return bytes.fromhex(parts[0]).decode("utf-8", errors="ignore")

        return "".join(chr(int(p, 16)) for p in parts)

    except (ValueError, TypeError):
        return ""


def get_text_from_rtp_messages(rtp_messages: Union[Iterable[Any], Any]) -> str:
    """
    Extracts and concatenates payload text from a sequence of RTP messages.
    """
    if not isinstance(rtp_messages, (list, tuple)):
        rtp_messages = [rtp_messages]

    decoded_chars: List[str] = []

    for message in rtp_messages:
        rtp = getattr(message, "rtp", None)
        payload = getattr(rtp, "payload", None)

        if payload:
            try:
                char = hex_str_to_letter(payload)
                if char:
                    decoded_chars.append(char)
            except (ValueError, TypeError):
                continue

    return "".join(decoded_chars)


def is_rtp_packet(rtp_input: Union["object", Iterable]) -> bool:
    """
    Determine whether a packet has an RTP layer (encrypted or not).

    Accepts a single packet or a list/iterable of packets (in which
    case only the first packet is analyzed).

    :param rtp_input: a single pyshark packet, or a list/iterable of packets.
    :return: True if the packet has an RTP layer, False otherwise.
    """
    packet = _first_packet(rtp_input)
    if packet is None:
        return False

    return "RTP" in packet


def is_srtp_packet(rtp_input: Union["object", Iterable]) -> bool:
    """
    Determine whether an RTP packet is encrypted (SRTP).

    Accepts a single packet or a list/iterable of packets (in which
    case only the first packet is analyzed). First tries to detect SRTP via
    known RTP layer fields, then falls back to a text search within the
    RTP layer representation.

    :param rtp_input: a single pyshark packet, or a list/iterable of packets.
    :return: True if the packet is recognized as SRTP, False otherwise.
    """

    srtp_field_markers = (
        "srtp_enc_payload",
        "srtp_auth_tag",
        "srtp_mki",
        "senc_payload",
        "sauth_tag",
    )

    srtp_text_markers = (
        "srtp encrypted payload",
        "srtp auth tag",
        "encrypted payload",
    )

    packet = _first_packet(rtp_input)
    if packet is None or not is_rtp_packet(packet):
        return False

    rtp_layer = packet.rtp

    # detect SRTP via known field names
    field_names = {
        name.lower() for name in (getattr(rtp_layer, "field_names", None) or [])
    }
    if any(marker in field_names for marker in srtp_field_markers):
        return True

    # Fallback: search for SRTP text markers
    layer_text = str(rtp_layer).lower()
    if any(marker in layer_text for marker in srtp_text_markers):
        return True

    return False


def _first_packet(rtp_input: Union["object", Iterable]):
    """
    Normalizes rtp_input to a single packet: if it's a single packet, returns
    it as-is; if it's an iterable of packets, returns the first one (or None
    if empty).
    """
    if isinstance(rtp_input, Iterable) and not hasattr(rtp_input, "rtp"):
        return next(iter(rtp_input), None)
    return rtp_input


def find_server_hello_with_srtp(packets):
    """
    Find the DTLS ServerHello packet that contains the negotiated use_srtp profile.

    :param packets: iterable of packets (or None).
    :return: the matching packet, or None if not found / input invalid.
    """
    if not packets:
        return None

    try:
        for packet in packets:
            if packet is None:
                continue
            try:
                if "DTLS" not in packet:
                    continue
            except TypeError:
                continue

            dtls_layer = getattr(packet, "dtls", None)
            if dtls_layer is None:
                continue

            handshake_type = getattr(dtls_layer, "handshake_type", None)
            if handshake_type != "2":  # 2 = ServerHello
                continue

            if getattr(dtls_layer, "use_srtp_protection_profile", None):
                return packet
    except TypeError:
        return None

    return None


def is_srtp_by_dtls_profile(dtls_packet, profile_name: str) -> bool:
    """
    Return True if the DTLS packet negotiates the given SRTP protection profile.

    :param dtls_packet: pyshark packet expected to contain a DTLS layer
    :param profile_name: SRTP protection profile name, e.g. "AEAD_AES_256_GCM"
        or "AEAD_AES_128_GCM"
    :return: True if the negotiated profile matches profile_name
    :raises ValueError: if profile_name is not a known profile
    """
    srtp_protection_profiles = {
        "AEAD_AES_256_GCM": "0x0008",
        "AEAD_AES_128_GCM": "0x0007",
        "AES128_CM_HMAC_SHA1_80": "0x0001",
        "AES128_CM_HMAC_SHA1_32": "0x0002",
    }

    if profile_name not in srtp_protection_profiles:
        raise ValueError(
            f"Unknown SRTP profile '{profile_name}'. "
            f"Known profiles: {list(srtp_protection_profiles)}"
        )
    expected_code = srtp_protection_profiles[profile_name]

    if dtls_packet is None:
        return False

    try:
        if "DTLS" not in dtls_packet:
            return False
    except TypeError:
        return False

    dtls_layer = getattr(dtls_packet, "dtls", None)
    if dtls_layer is None:
        return False

    profile = getattr(dtls_layer, "use_srtp_protection_profile", None)
    if not profile:
        return False

    return str(profile) == expected_code


def is_srtp_crypto_suite(sdp_media: dict, expected_suite: str) -> bool:
    """
    Return True if the SDP media block negotiates the given SRTP crypto
    suite via SDES (a=crypto), verified two ways:
        1. the crypto suite name in a=crypto matches expected_suite
        2. the actual decoded inline key material matches the expected
           key+salt size for that suite (RFC 3711/6188), independent of
           what the suite name claims

    If either check fails, prints which one disagreed and returns False.

    Known crypto suites and their SRTP master key+salt size in bytes:
        AES_CM_128_HMAC_SHA1_80  -> 30  (16-byte key + 14-byte salt)
        AES_CM_128_HMAC_SHA1_32  -> 30  (16-byte key + 14-byte salt)
        AES_256_CM_HMAC_SHA1_80  -> 46  (32-byte key + 14-byte salt)
        AES_256_CM_HMAC_SHA1_32  -> 46  (32-byte key + 14-byte salt)
        AEAD_AES_128_GCM         -> 28  (16-byte key + 12-byte salt)
        AEAD_AES_256_GCM         -> 44  (32-byte key + 12-byte salt)

    :param sdp_media: dict of SDP media attributes
    :param expected_suite: expected crypto suite name — must be a key in
        the known suites listed above
    :return: True only if both the suite name and the actual key length
        confirm expected_suite
    :raises ValueError: if expected_suite is not a known crypto suite
    """
    known_suites = {
        "AES_CM_128_HMAC_SHA1_80": 30,
        "AES_CM_128_HMAC_SHA1_32": 30,
        "AES_256_CM_HMAC_SHA1_80": 46,
        "AES_256_CM_HMAC_SHA1_32": 46,
        "AEAD_AES_128_GCM": 28,
        "AEAD_AES_256_GCM": 44,
    }

    if expected_suite not in known_suites:
        raise ValueError(
            f"Unknown SRTP crypto suite '{expected_suite}'. "
            f"Known suites: {list(known_suites)}"
        )
    expected_key_bytes = known_suites[expected_suite]

    if not sdp_media:
        print("No SDP media data provided")
        return False

    crypto = sdp_media.get("crypto")
    if not crypto:
        print("No a=crypto attribute found in SDP")
        return False

    parts = crypto.split()
    if len(parts) < 2:
        print(f"Malformed a=crypto attribute: '{crypto}'")
        return False

    suite_name = parts[1]
    inline_marker = "inline:"
    inline_index = crypto.find(inline_marker)
    if inline_index == -1:
        print(f"No inline key found in a=crypto: '{crypto}'")
        return False

    key_part = crypto[inline_index + len(inline_marker) :].split()[0]
    try:
        decoded_key = base64.b64decode(key_part)
    except (ValueError, TypeError):
        print(f"Could not decode inline key as base64: '{key_part}'")
        return False

    name_ok = suite_name == expected_suite
    key_length_ok = len(decoded_key) == expected_key_bytes

    return name_ok and key_length_ok
