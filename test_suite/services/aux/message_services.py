import re

from enums import HTTPMethodEnum
from enums.packet_types import PacketTypeEnum
from services.aux.json_services import decrypt_jws
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
        from services.aux.sip_services import extract_raw_sip_message_string
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
    header_name = header_name.replace(":", "")
    for line in raw_message_body_string.splitlines():
        if line.startswith(header_name + ":"):
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
    ip_port = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', text)
    if hasattr(ip_port, 'group'):
        return ip_port.group(0)
    else:
        return ""


def extract_sip_uri_from_text(text: str) -> str:
    """
    Extracts first SIP URI (like sip:test@test.com:5060) found in given text
    :param text: any string to check for pattern
    :return: SIP URI as a string or None if not found
    """
    sip_uri_pattern = r'\b(?:sip[s]?):([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(:\d+)?(\S*)?)\b'
    sip_uri = re.search(sip_uri_pattern, text)
    if hasattr(sip_uri, 'group'):
        return sip_uri.group(0)
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
        if (uri is not None and string_in_message is None and str(message.http.request_uri) != uri)\
         or (uri is not None and string_in_message is not None and str(message.http.request_uri) != uri):
            continue
        elif ((uri is None and string_in_message is not None)
              or (uri is not None and string_in_message is not None and str(message.http.request_uri) == uri)):
            for body in extract_all_contents_from_message_body(message):
                # Remove whitespace characters
                body['body'] = re.sub(r'\s+', '', body['body'])
                if string_in_message not in body['body']:
                    continue
                else:
                    response_timestamp = float(message.sniff_timestamp)
        elif uri is not None and string_in_message is None and str(message.http.request_uri) == uri:
            response_timestamp = float(message.sniff_timestamp)

    print("__________ FILTERS __________")
    print(response_timestamp)
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
            print(message.http.response_code)
            response_message = message
            break
    return response_message
