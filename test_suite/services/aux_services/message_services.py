import json
import re
from json import JSONDecodeError
from dateutil import parser
from typing import Union
from datetime import datetime

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


def is_valid_catype_schema(catype: int, namespace: str) -> bool:
    """
    Validates if the provided schema string is correct for the given
    Civic Address (CA) type number.

    :param: catype: String/Int representation of 'caType'.
    :param: catype: String representation of 'namespace' to check.
    :return: bool
    """

    # --- Define Schema Constants ---
    # Schema for types 0-39 and 128
    NAMESPACE_PIDF_BASE = "urn:ietf:params:xml:ns:pidf:geopriv10:civicAddr"

    # Schemas for type 40
    NAMESPACE_PIDF_EXT = "urn:ietf:params:xml:ns:pidf:geopriv10:civicAddr:ext"
    NAMESPACE_NENA = "	urn:nena:xml:ns:pidf:nenaCivicAddr"

    # We use a set for efficient lookup for type 40, as it allows for
    # multiple valid schemas ("OR" logic).
    VALID_TYPE_40_SCHEMAS = {
        NAMESPACE_PIDF_EXT,
        NAMESPACE_NENA
    }

    if isinstance(catype, str):
        catype = int(catype)
    # Rule 1: For types 0-39 and 128
    if (0 <= catype <= 39) or (catype == 128):
        return namespace == NAMESPACE_PIDF_BASE

    # Rule 2: For type 40
    elif catype == 40:
        return namespace in VALID_TYPE_40_SCHEMAS

    # Default case: Your prompt was cut off, so we don't have rules
    # for other types (e.g., 41-127, 129+). We will assume they
    # are invalid until more rules are added.
    else:
        return False


def is_equal_or_after(timestamp1: Union[str, datetime],
                      timestamp2: Union[str, datetime]) -> bool:
    """
    Compare two timestamps and return True if timestamp1 is equal to or after timestamp2.

    Handles various timestamp formats automatically, including:
    - ISO 8601 with timezone: '2035-08-21T12:58:03.01-05:00'
    - ISO 8601 without timezone: '2035-08-21T12:58:03'
    - Standard format: '2024-01-15 14:30:00'
    - Unix timestamps: '1705328400'
    - And many other formats

    :param: timestamp1: First timestamp (string or datetime object)
    :param: timestamp2: Second timestamp (string or datetime object)
    :return: bool: True if timestamp1 >= timestamp2, False otherwise
    """
    # Convert strings to datetime objects if needed
    dt1 = _parse_timestamp(timestamp1)
    dt2 = _parse_timestamp(timestamp2)

    # If both have timezone info or both are naive, compare directly
    if (dt1.tzinfo is None) == (dt2.tzinfo is None):
        return dt1 >= dt2

    # If one has timezone and other doesn't, convert naive to UTC
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=datetime.now().astimezone().tzinfo)
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=datetime.now().astimezone().tzinfo)

    return dt1 >= dt2


def extract_log_event_types(json_objects):
    """
    Extract all logEventType values from JSON objects
    
    :param json_objects: List of JSON objects to process
    :return: Set of unique log event types found
    """
    types = set()
    for obj in json_objects:
        if isinstance(obj, dict) and obj.get('logEventType'):
            types.add(obj.get('logEventType'))
    return types


def _parse_timestamp(timestamp: Union[str, datetime]) -> datetime or None:
    """
    Parse a timestamp string into a datetime object using multiple strategies.

    :param: timestamp: Timestamp as string or datetime object
    :returns: datetime: Parsed datetime object
    """
    if isinstance(timestamp, datetime):
        return timestamp

    if not isinstance(timestamp, str):
        raise ValueError(f"Expected string or datetime, got {type(timestamp)}")

    # Try dateutil parser (handles most formats automatically)
    try:
        return parser.parse(timestamp)
    except (ValueError, parser.ParserError):
        pass

    # Try as unix timestamp (integer or float)
    try:
        unix_ts = float(timestamp)
        return datetime.fromtimestamp(unix_ts)
    except (ValueError, OSError):
        pass

    except ValueError:
        return ''

