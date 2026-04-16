from typing import List, Any

from checks.sip.header_field_checks.constants import SIP_VARIABLE_HEADER_FIELDS
from services.aux_services.aux_services import split_sip_header_by_pattern
from test_suite.services.aux_services.message_services import strip_ansi


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
                str(line).split("<LayerField raw_sip.line: ")[1].rsplit("  >")[0]
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


def extract_all_header_fields_matching_name_from_sip_message(
    message, header_field_name: str
) -> list:
    """
    Extracts list of header fields matching header_name with their values
    :param message: Full SIP message
    :param header_field_name: Name of header field
    :return: List of header fields with their values or empty list
    """
    message_list: List[Any] = []
    header_field_name = header_field_name.replace(":", "").strip()

    # If there is no 'raw_sip' and 'sip' (in most cases when message is None) return empty list
    if not hasattr(message, "raw_sip"):
        if hasattr(message, "sip"):
            message_list = str(message.sip).splitlines()
    else:
        message_list = strip_ansi(str(message.raw_sip)).splitlines()
    headers_matching = [
        header.strip()
        for header in message_list
        if header_field_name.lower() == header.split(":")[0].strip().lower()
    ]
    return headers_matching


def get_list_of_all_non_variable_header_fields_from_sip_message(message) -> list:
    """
    Finds all header fields existing in SIP message that are non-variable
    and returns their names as a list
    :param message: Full SIP message
    :return: List of all non-variable header field names
    """
    non_variable_headers_list = [
        header
        for header, value in get_list_of_all_header_fields_from_sip_message(message)
        if header not in SIP_VARIABLE_HEADER_FIELDS
    ]
    return non_variable_headers_list


def extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message(
    stimulus, output
) -> tuple[List[Any], list[Any]]:
    """
    Extracts all non-variable header fields with values for stimulus and output messages
    and returns 2 dicts, 1 for each message
    :param stimulus: Full stimulus SIP message
    :param output: Full output SIP message
    :return: Dict with header names and values for stimulus and another for output message
    """
    stimulus_headers: List[Any] = []
    output_headers: List[Any] = []
    stimulus_header_names = get_list_of_all_non_variable_header_fields_from_sip_message(
        stimulus
    )
    output_header_names = get_list_of_all_non_variable_header_fields_from_sip_message(
        output
    )
    # Import required function to prevent circular import
    from services.aux_services.message_services import get_header_field_value

    for header in stimulus_header_names:
        stimulus_headers.append({header: get_header_field_value(stimulus, header)})
    for header in output_header_names:
        output_headers.append({header: get_header_field_value(output, header)})
    return stimulus_headers, output_headers


def extract_message_data(message) -> str:
    """
    Decodes raw sip data and stores it in string representation
    @param message: packet from
    @return:
    """
    if not message:
        return ""
    if not hasattr(message.sip, "msg_body"):
        return ""
    hex_data = message.sip.msg_body.replace(":", "")
    byte_data = bytes.fromhex(hex_data)
    return byte_data.decode("ascii", errors="ignore")


def extract_sip_header_values(messages, header_name: str, header_keyword: str):
    """
    Extracts SIP header values from messages based on a header name and keyword.
    :param messages: Iterable of message objects that may contain a 'sip' attribute.
    :param header_name: The SIP header to look for (e.g., 'Call-Info').
    :param header_keyword: Keyword to match inside the header (e.g., 'purpose=emergency-source').
    :return: list[str]: List of extracted values (e.g., ['+120255512121@test.system.bcf'])
    """
    results: List[Any] = []

    if messages is None:
        return results

    # Ensure messages is an iterable list, even if a single object is passed
    if not isinstance(messages, (list, tuple)):
        messages = [messages]

    for msg in messages:
        if hasattr(msg, "sip"):
            bcf_headers = split_sip_header_by_pattern(msg.sip.get("msg_hdr"))
            header_value = bcf_headers.get(header_name, "")

            if not header_value:
                continue

            for part in header_value.split(", "):
                if header_keyword in part:
                    value = part.split(";")[0].strip("<>")
                    results.append(value)

    return results
