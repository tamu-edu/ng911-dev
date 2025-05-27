import re
from collections import defaultdict
from urllib.parse import urlparse

from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from enums import PacketTypeEnum
from services.config.config_enum import EntityFunction
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.xml_services import extract_all_xml_bodies_from_message
from services.stub_server.enums import StubServerProtocol


def extract_header_value_by_separator(header: str, separator: str, field_index: int) -> str | None:
    """
    Extract a specific value from a header line based on the separator and field index.
    """
    try:
        parts = header.split(separator)
        return parts[field_index].strip() if len(parts) > field_index else ""
    except IndexError as e:
        return None


def extract_header_by_pattern(call_info_header: str, pattern: str) -> str | None:
    """
    Extract a specific emergency call id header based on the Call Info header
    :param call_info_header: Call Info header string
    :param pattern: pattern to match in the Call Info header
    :return: str or None
    """
    try:
        for part in call_info_header.split(","):
            for sub_part in part.split(';'):
                value = sub_part.strip("<>")
                if pattern in value:
                    return value
    except AttributeError as e:
        return None


def split_sip_header_by_pattern(header: str):
    # Regex pattern to split on headers like "Header-Name:"
    pattern = r'\b([A-Z][A-Za-z\-]*):'
    matches = list(re.finditer(pattern, header))

    # Extract headers using match positions
    headers = defaultdict(list)
    for i in range(len(matches)):
        key = matches[i].group(1)
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(header)
        value = header[start:end].strip()
        headers[key].append(value)

    # Merge multiple values into comma-separated string
    final_headers = {key: ", ".join(values) for key, values in headers.items()}
    return final_headers


def conduct_test_on_parameter(test_name: str, test_function, test_parameter) -> list:
    return [test_function(test_parameter), test_name]


def conduct_test_on_parameters(test_name: str, test_function, test_parameters: list) -> list:
    return [test_function(*test_parameters), test_name]


def get_general_verdict(intermediate_verdicts) -> str:
    for _verdict in intermediate_verdicts:
        if "FAILED" in str(_verdict[0]):
            return "FAILED"
    return "PASSED"


def get_messages(pcap: PcapCaptureService, message_filter: FilterConfig):
    try:
        return pcap.get_messages_by_config(message_filter)
    except IndexError:
        return None


def get_first_message_matching_filter(pcap: PcapCaptureService, message_filter: FilterConfig):
    try:
        return pcap.get_messages_by_config(message_filter)[0]
    except IndexError:
        return None


def get_http_response_containing_string_in_xml_body_for_message_matching_filter(
        pcap: PcapCaptureService,
        message_filter: FilterConfig,
        string_in_message: str
):
    """
    Function tries to find HTTP request matching filter and containing
    given string_in_message and returns response message
    :param pcap: Pcap Service object
    :param message_filter: filter configuration for request message
    :param string_in_message: string to be found in request
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
    string_in_message = re.sub(r'\s+', '', string_in_message)

    # Find message with expected string and save its timestamp
    for message in messages:
        for body in extract_all_xml_bodies_from_message(message):
            # Remove whitespace characters
            body = re.sub(r'\s+', '', body)
            if string_in_message in body:
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


def is_valid_http_https_url(url: str) -> bool:
    """
    Function validated if given string is a valid URL with http/https
    :param url: URL as a string
    :return: True/False
    """
    parsed_url = urlparse(url)
    return bool(
        (parsed_url.scheme == "http" or parsed_url.scheme == "https")
        and re.search(FQDN_PATTERN, parsed_url.netloc)
    )


def get_entity_protocol(entity_function: EntityFunction) -> StubServerProtocol:
    if entity_function in ["BCF, OSP, ESRP"]:
        return StubServerProtocol.SIP.value
    return StubServerProtocol.HTTP.value


def check_value_for_file_var_mode(value: str):
    if value is None:
        return None
    value_split = value.split(".")
    if value_split[0] == "file":
        # if not os.path.exists(value_split[1]):
        #     raise FileNotFoundError(f"File not found: {value_split[1]}")
        result = value_split[1]
        for item in value_split[2:]:
            result += f".{item}"
        return result
    if value_split[0] == "var":
        return value_split[1]
