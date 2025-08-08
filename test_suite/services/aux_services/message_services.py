import json
import re
from json import JSONDecodeError

from enums.packet_types import PacketTypeEnum
from services.pcap_service import FilterConfig, PcapCaptureService


def get_header_field_value(message, header_name: str) -> str:
    """
    Returns value of header field for HTTP or SIP message type.
    SIP header fields are extracted from raw string as pyShark does not
    support custom ones
    :param message: Full HTTP/SIP message
    :param header_name: Name of header field for extracting value
    :return: header field value
    """
    if hasattr(message, PacketTypeEnum.HTTP):
        return message.http.get(header_name)
    elif hasattr(message, PacketTypeEnum.SIP):
        # Import required function to prevent circular import
        from services.aux_services.sip_services import extract_raw_sip_message_string
        return extract_header_field_value_from_raw_string_body(
            header_name,
            extract_raw_sip_message_string(message)
        )


def extract_header_field_value_from_raw_string_body(header_name: str, raw_message_body_string: str) -> str:
    """
    Extracts value of header field from raw message
    :param header_name: Name of header field
    :param raw_message_body_string: raw string body
    :return: Value of header field or None
    """
    if not header_name:
        return ""
    header_name = header_name.replace(":", "")
    for line in raw_message_body_string.splitlines():
        if line.lower().startswith(header_name.lower() + ":"):
            return line.split(":", 1)[1].strip()
    return ""


def extract_all_contents_from_message_body(message) -> list:
    """
    Extracts contents from message body as a list of dict
    :param message: The full SIP/HTTP message
    :return: List of dict, or None if not found
    """
    content_list = []
    if hasattr(message, PacketTypeEnum.HTTP) and hasattr(message.http, "file_data"):
        message_body = message.http.file_data
    elif hasattr(message, PacketTypeEnum.SIP) and hasattr(message.sip, "msg_body"):
        message_body = message.sip.msg_body
    else:
        return []
    content_type = get_header_field_value(message, "Content-Type")
    content_id = get_header_field_value(message, "Content-ID")
    hex_data = message_body.replace(":", "")
    byte_data = bytes.fromhex(hex_data)
    message_body = byte_data.decode("ascii", errors="ignore")
    content_dict = {}
    if content_type:
        if 'boundary=' in content_type:
            message_boundary = content_type.split('boundary=')[1].split(";")[0]
            message_boundary = "--" + message_boundary
            contents = message_body.split(message_boundary)
        else:
            content_dict['Content-Type'] = content_type.split(";")[0]
            content_dict['Content-ID'] = content_id
            message_body = "\n".join([line for line in message_body.splitlines() if line])
            content_dict['body'] = message_body
            content_list.append(content_dict)
            return content_list

        for content in contents:
            if not content:
                continue
            # Split to parts separated by empty line
            content_parts = re.split(r'(\r?\n){2,}', content.strip())
            # In part containing header fields read Content-Type and Content-ID
            content_dict['Content-Type'] = extract_header_field_value_from_raw_string_body("Content-Type", content_parts[0])
            content_dict['Content-ID'] = extract_header_field_value_from_raw_string_body("Content-ID", content_parts[0])
            # Assuming that body is separated by empty line from headers part
            content_dict['body'] = content_parts[2]
            content_list.append(content_dict.copy())
    return content_list


def extract_ip_and_port_from_text(text: str) -> str:
    """
    Extracts first IP_ADDRESS:PORT found in given text
    :param text: any string to check for pattern
    :return: IP_ADDRESS:PORT as a string or None if not found
    """
    if not text:
        return ""

    match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})(?::(\d+))?', text)
    if match:
        ip = match.group(1)
        port = int(match.group(2)) if match.group(2) else None
        return f'{ip}:{port}'
    return ''


def extract_sip_uri_from_text(text: str) -> str:
    """
    Extracts first SIP URI (like sip:test@test.com:5060) found in given text
    :param text: any string to check for pattern
    :return: SIP URI as a string or None if not found
    """
    if not text:
        return ""
    sip_uri_pattern = r'\b(?:sip[s]?):([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(:\d+)?(\S*)?)\b'
    sip_uri = re.search(sip_uri_pattern, text)
    if hasattr(sip_uri, 'group'):
        return sip_uri.group(0).split(';')[0]
    else:
        return ""


def get_messages(pcap: PcapCaptureService, message_filter: FilterConfig):
    try:
        return pcap.get_messages_by_config(message_filter)
    except IndexError:
        return None


def get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap: PcapCaptureService,
        message_filter: FilterConfig,
        string_in_message=None,
        uri=None
):
    """
    Function tries to find HTTP request matching filter and containing
    given string_in_message and returns response message
    :param pcap: Pcap Service object
    :param message_filter: filter configuration for request message
    :param string_in_message: string to be found in request
    :param uri: string to be found in request_uri
    :return: first found response to request matching filter
    and containing string_in_message or None
    """
    try:
        messages = pcap.get_messages_by_config(message_filter)
    except IndexError:
        return None
    response_message = None
    response_timestamp = None

    # Remove whitespace characters
    if string_in_message:
        string_in_message = re.sub(r'\s+', '', string_in_message)

    # Find message with expected string and uri and save its timestamp
    for message in messages:
        if (uri is not None and string_in_message is None and uri.lower() not in str(message.http.request_uri).lower())\
         or (uri is not None and string_in_message is not None and uri.lower() not in str(message.http.request_uri).lower()):
            continue
        elif ((uri is None and string_in_message is not None)
              or (uri is not None and string_in_message is not None
                  and uri.lower() in str(message.http.request_uri).lower())):
            for body in extract_all_contents_from_message_body(message):
                # Remove whitespace characters
                body['body'] = re.sub(r'\s+', '', body['body'])
                if string_in_message not in body['body']:
                    continue
                else:
                    response_timestamp = float(message.sniff_timestamp)
        elif uri is not None and string_in_message is None and uri.lower() in str(message.http.request_uri).lower():
            response_timestamp = float(message.sniff_timestamp)

    if not response_timestamp:
        return None
    messages_after_timestamp = get_messages(
        pcap,
        FilterConfig(
            src_ip=message_filter.dst_ip,
            dst_ip=message_filter.src_ip,
            packet_type=PacketTypeEnum.HTTP,
            after_timestamp=response_timestamp
        )
    )
    # Find first message with any response code
    for message in messages_after_timestamp:
        if hasattr(message.http, "response_code"):
            response_message = message
            break
    return response_message


def get_sip_response_by_attribute_and_attr_value(
        pcap: PcapCaptureService,
        message_filter: FilterConfig,
        attribute='',
        attr_value='',
):
    """
    Function tries to find SIP request timestamp matching filter and containing
    given header_field and returns response message
    :param pcap: Pcap Service object
    :param message_filter: filter configuration for request message
    :param attribute: string to be found in request
    :param attr_value: attribute value to be found in request
    :return: first found response timestamp to request matching filter or None
    """
    try:
        messages = pcap.get_messages_by_config(message_filter)
    except IndexError:
        return None
    response = None

    # Find message with expected string and uri and save its timestamp
    for message in messages:

        if message.sip.get(attribute):
            if not attr_value:
                response = message
                break
            else:
                if attr_value in message.sip.get(attribute):
                    response = message
                    break

    return response


def strip_ansi(text):
    """
    Strips ANSI console colour formatting etc. from raw messages strings
    """
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text) if text else ""


def extract_json_data_from_http(message):
    try:
     http_message_converted = str(message.http.file_data).replace(":", "")
    except AttributeError:
        return None
    extracted = bytes.fromhex(http_message_converted).decode("ascii", errors="ignore")
    try:
        json_formed = json.loads(extracted)
        return json_formed
    except JSONDecodeError:
        return None


def get_header_field_multiple_values(message, header_name: str, coma_separated=True) -> set:
    """
    Returns list with values of header field for HTTP or SIP message type.
    SIP header fields are extracted from raw string as pyShark does not
    support custom ones
    :param message: Full HTTP/SIP message
    :param header_name: Name of header field for extracting value
    :return: list with header field values
    """
    result = []
    if hasattr(message, PacketTypeEnum.HTTP):
        return message.http.get(header_name)
    elif hasattr(message, PacketTypeEnum.SIP):
        # Import required function to prevent circular import
        from services.aux_services.sip_services import extract_raw_sip_message_string
        message_str = extract_raw_sip_message_string(message)
        msgs_headers_lst = [msg_str for msg_str in message_str.splitlines() if header_name in msg_str]
        if msgs_headers_lst:
            for mgs_header in msgs_headers_lst:
                if coma_separated:
                    result = [extract_header_field_value_from_raw_string_body(header_name, item.strip())
                              for item in mgs_header.split(',')]
                else:
                    field_value = extract_header_field_value_from_raw_string_body(header_name, mgs_header)
                    if field_value:
                        result.append(field_value)

    return set(result)

