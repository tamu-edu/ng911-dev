import re
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
            message_string += str(line).split("<LayerField raw_sip.line: ")[1].rsplit("  >")[0] + '\r\n'
        return message_string
    elif hasattr(message, "sip"):
        sip_layer = message.sip
        lines = []

        # Add Request-Line or Status-Line
        if hasattr(sip_layer, 'request_line'):
            lines.append(sip_layer.request_line)
        elif hasattr(sip_layer, 'status_line'):
            lines.append(sip_layer.status_line)

        # Iterate over all field names
        for field in sip_layer.field_names:
            if field not in ['request_line', 'status_line', 'msg_body']:
                try:
                    value = getattr(sip_layer, field)
                    lines.append(f"{field.replace('_', '-').title()}: {value}")
                except AttributeError:
                    continue

        # Add message body if exists
        if hasattr(sip_layer, 'msg_body'):
            lines.append('')
            lines.append(sip_layer.msg_body)

        return '\r\n'.join(lines)
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
    header_fields = []
    if hasattr(message, 'sip') and hasattr(message.sip, 'msg_hdr'):
        headers = re.findall(r'(\S+): (\S+)', message.sip.msg_hdr)
        header_names = [h[0] for h in headers if h]
        for header in header_names:
            header_fields.append((header, message.sip.get_field_value(header)))
    return header_fields


def extract_all_header_fields_matching_name_from_sip_message(message, header_field_name: str) -> list:
    """
    Extracts list of header fields matching header_name with their values
    :param message: Full SIP message
    :param header_field_name: Name of header field
    :return: List of header fields with their values or empty list
    """
    message_list = []
    header_field_name = header_field_name.replace(":", "").strip()

    # If there is no 'raw_sip' and 'sip' (in most cases when message is None) return empty list
    if not hasattr(message, 'raw_sip'):
        if hasattr(message, 'sip'):
            message_list = str(message.sip).splitlines()
    else:
        message_list = strip_ansi(str(message.raw_sip)).splitlines()
    headers_matching = [header.strip() for header in message_list
                        if header_field_name.lower() == header.split(':')[0].strip().lower()]
    return headers_matching


def get_list_of_all_non_variable_header_fields_from_sip_message(message) -> list:
    """
    Finds all header fields existing in SIP message that are non-variable
    and returns their names as a list
    :param message: Full SIP message
    :return: List of all non-variable header field names
    """
    non_variable_headers_list = [
        header for header, value in get_list_of_all_header_fields_from_sip_message(message)
        if header not in SIP_VARIABLE_HEADER_FIELDS
    ]
    return non_variable_headers_list


def extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message(stimulus, output) \
        -> [dict, dict]:
    """
    Extracts all non-variable header fields with values for stimulus and output messages
    and returns 2 dicts, 1 for each message
    :param stimulus: Full stimulus SIP message
    :param output: Full output SIP message
    :return: Dict with header names and values for stimulus and another for output message
    """
    stimulus_headers = []
    output_headers = []
    stimulus_header_names = get_list_of_all_non_variable_header_fields_from_sip_message(stimulus)
    output_header_names = get_list_of_all_non_variable_header_fields_from_sip_message(output)
    # Import required function to prevent circular import
    from services.aux_services.message_services import get_header_field_value
    for header in stimulus_header_names:
        stimulus_headers.append({
            header: get_header_field_value(stimulus, header)
        })
    for header in output_header_names:
        output_headers.append({
            header: get_header_field_value(output, header)
        })
    return stimulus_headers, output_headers


def extract_message_data(message) -> str:
    """
    Decodes raw sip data and stores it in string representation
    @param message: packet from
    @return:
    """
    if not message:
        return ''
    if not hasattr(message.sip, 'msg_body'):
        return ''
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
    results = []

    if messages is None:
        return results

    # Ensure messages is an iterable list, even if a single object is passed
    if not isinstance(messages, (list, tuple)):
        messages = [messages]

    for msg in messages:
        if hasattr(msg, 'sip'):
            bcf_headers = split_sip_header_by_pattern(msg.sip.get('msg_hdr'))
            header_value = bcf_headers.get(header_name, '')

            if not header_value:
                continue

            for part in header_value.split(', '):
                if header_keyword in part:
                    value = part.split(';')[0].strip('<>')
                    results.append(value)

    return results
