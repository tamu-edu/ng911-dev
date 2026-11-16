from typing import List, Any


def get_list_of_all_header_fields_from_sip_message(message) -> list:
    """
    Finds all header fields existing in SIP message and returns their names and values as a list of tuples
    :param message: Full SIP message
    :return: List of tuples with all header field names and values
    """
    if not message:
        return []
    header_fields: List[Any] = []
    if hasattr(message, "sip") and hasattr(message.sip, "msg_hdr"):
        headers: List[Any] = []
        i = 0
        n = len(message.sip.msg_hdr)

        while i < n:
            # Step 1: Find the start of the next header (must be a capital letter followed by valid key and colon)
            start = i
            while start < n and not (
                message.sip.msg_hdr[start].isupper()
                and (start == 0 or message.sip.msg_hdr[start - 1].isspace())
            ):
                start += 1
            if start >= n:
                break

            # Step 2: Find the end of the key (letters, digits, hyphen)
            key_end = start
            while key_end < n and (
                message.sip.msg_hdr[key_end].isalnum()
                or message.sip.msg_hdr[key_end] == "-"
            ):
                key_end += 1
            if key_end >= n or message.sip.msg_hdr[key_end] != ":":
                i = key_end
                continue

            # Include colon in the key
            key_end += 1

            # Step 3: Find where the value ends (right before the next header or end of string)
            value_end = key_end
            while value_end < n:
                # Lookahead for next header
                if (
                    message.sip.msg_hdr[value_end].isupper()
                    and value_end > key_end
                    and message.sip.msg_hdr[value_end - 1].isspace()
                ):
                    # Check that this is a valid header key (letters/digits/hyphen + colon)
                    j = value_end
                    while j < n and (
                        message.sip.msg_hdr[j].isalnum()
                        or message.sip.msg_hdr[j] == "-"
                    ):
                        j += 1
                    if j < n and message.sip.msg_hdr[j] == ":":
                        break  # found next header
                value_end += 1

            # Step 4: Extract current header
            header = message.sip.msg_hdr[start:value_end].strip()
            headers.append(header)

            # Move to the next character after this header
            i = value_end
        for h in headers:
            header_and_value = h.split(": ")
            if len(header_and_value) > 1:
                header_fields.append((header_and_value[0], header_and_value[1]))

    return header_fields


def extract_raw_sip_message_string(message) -> str:
    """
    Extracts raw SIP message as a string
    :param message: Full SIP message
    :return: Full SIP message as a string or None in case read failure
    """
    message_string = ""
    # Example raw line: <LayerField raw_sip.line: INVITE urn:service:sos SIP/2.0  >
    if hasattr(message, "raw_sip"):
        for line in message.raw_sip.line.all_fields:
            # Extracting SIP header field + value
            message_string += (
                str(line)
                .split("<LayerField raw_sip.line: ")[1]
                .rsplit(">", maxsplit=1)[0]
                .replace("\\n", "")
                .replace("\\r", "")
                + "\r\n"
            )
        return message_string
    elif hasattr(message, "sip"):
        lines: List[Any] = []

        # Add Request-Line or Status-Line
        if hasattr(message.sip, "request_line"):
            lines.append(message.sip.request_line)
        elif hasattr(message.sip, "status_line"):
            lines.append(message.sip.status_line)

        headers = get_list_of_all_header_fields_from_sip_message(message)
        if headers:
            for h in headers:
                lines.append(f"{h[0]}: {h[1]}")

        # Add message body if exists
        if hasattr(message.sip, "msg_body"):
            lines.append("")
            hex_data = message.sip.msg_body.replace(":", "")
            byte_data = bytes.fromhex(hex_data)
            message_body = byte_data.decode("ascii", errors="ignore")
            lines.append(message_body)

        return "\r\n".join(lines)
    else:
        raise ValueError("No SIP layer found in packet")
