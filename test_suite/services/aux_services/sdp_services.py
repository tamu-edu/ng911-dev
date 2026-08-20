import re
from typing import List, Any


def parse_sdp(sdp_str: str) -> dict:
    """
    parsing the SDP part from SIP message.
    :param sdp_str: The full spd part as a string
    :return: The SDP content as a string, or None if not found
    """
    sdp_dict = {}
    lines = sdp_str.strip().splitlines()

    current_media = None
    current_media_block = {}

    for line in lines:
        key, value = line.split("=", 1)

        if key == "v":
            sdp_dict["version"] = value
        elif key == "o":
            sdp_dict["origin"] = value
        elif key == "s":
            sdp_dict["session_name"] = value
        elif key == "b":
            sdp_dict["bandwidth"] = value
        elif key == "t":
            sdp_dict["timing"] = value
        elif key == "m":  # Media section
            media_type, port, protocol, *formats = value.split()
            current_media = media_type
            current_media_block = {
                "port": port,
                "protocol": protocol,
                "formats": formats,
                "attributes": [],
            }
            if current_media == "audio":
                sdp_dict["audio"] = current_media_block
            elif current_media == "video":
                sdp_dict["video"] = current_media_block
        elif key == "c":  # Connection information
            current_media_block["connection_info"] = value
        elif key == "a":  # Attributes
            current_media_block["attributes"].append(value)

    return sdp_dict


def extract_sdp_from_message_body(message) -> str:
    """
    Extracts the SDP part from a multi-part SIP message.
    :param message: The full SIP message
    :return: The SDP content as a string, or None if not found
    """
    message_body = message.sip.msg_body
    hex_data = message_body.replace(":", "")
    byte_data = bytes.fromhex(hex_data)
    str_data = byte_data.decode("ascii", errors="ignore")
    # Regular expression to find the SDP part marked by "Content-Type: application/sdp"
    sdp_pattern = re.compile(
        r"Content-Type: application/sdp.*?\r?\n\r?\n(.*?)(--\w+|$)", re.DOTALL
    )
    # Search for SDP in the message
    match = sdp_pattern.search(str_data)

    # Regular expression to find the SDP part marked by "Content-Type: application/sdp"
    sdp_raw_pattern = re.compile(r"v=0.*", re.DOTALL)
    # Search for raw SDP in the message
    raw_match = sdp_raw_pattern.search(str_data)

    if match:
        # Extract the SDP content
        return match.group(1).strip()
    elif raw_match:
        # Extract the raw SDP content
        return raw_match.group(0).strip()
    else:

        return ""


def extract_sdp_labels_from_string(sdp: str) -> list[str]:
    """
    Extracts all values from SDP attribute lines starting with 'a=label:'.
    Args:
        sdp (str): Raw SDP string.
    Returns:
        list[str]: List of label values found in SDP.
    Example:
        "a=label:audio1\na=label:audio2" -> ["audio1", "audio2"]
    """
    sdp = str(sdp) if sdp is not None else ""
    return [
        line.split(":", 1)[1]
        for line in sdp.splitlines()
        if line.startswith("a=label:")
    ]


def media_quality_stats_to_dict(data: str) -> dict[str, Any]:
    """
    Parses VQSessionReport-style string into a structured dictionary.

    Converts a raw multiline report string into a dict with optional nested
    dictionaries for metrics sections (e.g. LocalMetrics, RemoteMetrics).

    Args:
        data (str): Raw VQSessionReport string.

    Returns:
        dict[str, Any]:
            Parsed representation of the report where:
            - top-level keys are extracted fields
            - LocalMetrics and RemoteMetrics are parsed as nested dicts
            - values are automatically converted to int/float when possible,
              otherwise kept as strings
    """

    allowed_metrics = {"Jitter", "PacketLoss", "Delay", "MOSLQ"}

    def _cast(v: str) -> Any:
        v = v.strip()
        if v.isdigit():
            return int(v)
        try:
            return float(v)
        except ValueError:
            return v

    result: dict[str, Any] = {}
    current_section: str | None = None

    for line in data.splitlines():
        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key in ("LocalMetrics", "RemoteMetrics"):
            current_section = key
            result[current_section] = {}
            continue

        if key == "SessionDesc":
            result.setdefault("SessionDesc", {})
            if "=" in value:
                k, v = value.split("=", 1)
                result["SessionDesc"][k.strip()] = _cast(v)
            continue

        parsed_value = _cast(value)

        if current_section and key in allowed_metrics:
            result[current_section][key] = parsed_value
        else:
            result[key] = parsed_value

    return result


def classify_udp_packets(capture):
    """
    Classifies UDP packets as audio or video based on RTP payload type.
    :param capture: Pyshark capture object containing UDP packets
    :return: Two lists containing audio and video packets
    """
    audio_packets: List[Any] = []
    video_packets: List[Any] = []

    # Iterate through the packets and check for RTP in UDP packets
    for packet in capture:
        if hasattr(packet, "udp") and hasattr(packet, "rtp"):
            rtp_layer = packet.rtp

            # Extract the RTP payload type
            payload_type = int(rtp_layer.p_type)

            # Classify based on RTP payload type
            if payload_type in range(0, 35):  # Common audio payload types
                audio_packets.append(packet)
            elif payload_type >= 96:  # Common dynamic video payload types
                video_packets.append(packet)

    return audio_packets, video_packets
