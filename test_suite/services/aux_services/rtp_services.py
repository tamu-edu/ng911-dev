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


def get_ssrc_value(packet: Any) -> str:
    """
    Safely retrieves the SSRC value from a packet, defaulting to an empty string.
    """
    # Chained getattr is cleaner than nested if statements
    rtp_layer = getattr(packet, "rtp", None)
    if rtp_layer:
        # Get ssrc or return empty string if missing
        return str(getattr(rtp_layer, "ssrc", ""))
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


def hex_str_to_letter(hex_val: str) -> str:
    """Converts '54' or '0x54' to 'T'"""
    try:
        # Base 16 handles '54' and '0x54' automatically
        decimal_val = int(hex_val, 16)
        return chr(decimal_val)
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
