import re
import xml.etree.ElementTree as XML_ElementTree
import json
from collections import Counter


def extract_header_field_value_from_raw_body(header: str, message) -> str:
    """
    Extracts value of header field from raw SIP message
    :param header: Name of header field
    :param message: The full SIP message
    :return: Value of header field or None
    """
    pattern = rf'{header}:\s*(\S+/\S+|\S+)'
    match = re.search(pattern, message)
    if match:
        return match.group(1)
    else:
        return ""


def extract_all_contents_from_message_body(message) -> list:
    """
    Extracts contents from message body as a list of dict
    :param message: The full SIP message
    :return: List of dict, or None if not found
    """
    content_list = []
    try:
        message_body = message.sip.msg_body
    except Exception as e:
        print(f"ERROR - content not found for following SIP message: {e}")
        print(f"{getattr(message, 'raw_sip', 'Cannot get raw_sip attr from message')}")
        return []
    hex_data = message_body.replace(":", "")
    byte_data = bytes.fromhex(hex_data)
    message_body = byte_data.decode("ascii", errors="ignore")
    content_dict = {}
    if 'boundary=' in message.sip.get("Content-Type"):
        message_boundary = message.sip.get("Content-Type").split('boundary=')[1].split(";")[0]
        message_boundary = "--" + message_boundary
        contents = message_body.split(message_boundary)
    else:
        content_dict = {
            'Content-Type': message.sip.get("Content-Type").split(";")[0],
            'Content-ID': message.sip.get("Content-ID"),
            'body': "\n".join([line for line in message_body.splitlines() if line])
        }
        content_list.append(content_dict)
        return content_list

    for content in contents:
        if not content:
            continue
        # Split to parts separated by empty line
        content_parts = re.split(r'(\r?\n){2,}', content.strip())
        content_dict = {
            # In part containing header fields read Content-Type and Content-ID
            'Content-Type': extract_header_field_value_from_raw_body("Content-Type", content_parts[0]),
            'Content-ID': extract_header_field_value_from_raw_body("Content-ID", content_parts[0]),
            # Assuming that body is separated by empty line from headers part
            'body': content_parts[2]
        }
        content_list.append(content_dict.copy())
    return content_list


def is_valid_pidf_lo(xml_body: str) -> bool:
    # TODO test with different PIDF-LO examples, check if basic verification is sufficient
    """
    Checks if xml body given as a param is a valid PIDF-LO
    :param xml_body: Full xml body
    :return: True or False
    """
    # Try to parse XML
    try:
        XML_ElementTree.fromstring(xml_body)
    except XML_ElementTree.ParseError:
        return False
    if ('presence' and 'xmlns="urn:ietf:params:xml:ns:pidf"') not in xml_body:
        return False
    if 'location-info' not in xml_body:
        return False
    pidf_lo_location_tags = (
        'civicAddress',
        'Dynamic',
        'Point',
        'Polygon',
        'Circle',
        'Ellipse',
        'ArcBand',
        'Sphere',
        'Ellipsoid',
        'Prism'
    )
    location_tag = [t for t in pidf_lo_location_tags if t in xml_body]
    if not location_tag:
        return False
    return True


def get_json_value_from_sip_body(message, content_type: str, json_key: str) -> str:
    """
    For given SIP message looks for 1st body with content_type
    and returns value for json_key
    :param message: The full SIP message
    :param content_type: Content-Type value of message body
    :param json_key: JSON key for which value is returned
    :return: json_key value or None
    """
    json_value = ""
    msg_body_list = extract_all_contents_from_message_body(message)
    for msg_body in msg_body_list:
        if msg_body['Content-Type'].lower() == content_type.lower():
            json_search = re.search(r'\{.*?\}', msg_body['body'], re.DOTALL)
            try:
                json_body = json.loads(json_search.group(0))
                json_value = json_body.get(json_key)
            except json.JSONDecodeError:
                return ""
    if json_value:
        return json_value
    else:
        return ""


def get_message_bodies_matching_cid(message_body_list: list, cid: str) -> list:
    """
    For message_body_list as a list of dicts (format from extract_all_contents_from_message_body)
    function looks for all matching given CID and returns them in the same format
    :param message_body_list: message bodies in format from function extract_all_contents_from_message_body
    :param cid: Content-ID to look for
    :return: list of dicts with message bodies matching given CID
    """
    message_bodies_matching_cid = []
    # Remove < and > from Content-ID
    cid = cid.replace("\\r", "").replace("\\n", "")
    cid = cid.replace("cid:", "")
    for msg_body in message_body_list:
        if cid in msg_body['Content-ID']:
            message_bodies_matching_cid.append(msg_body)
    return message_bodies_matching_cid


def get_sip_media_attributes(sip_message):
    media_attrs = [record.replace('\t', '')
                   for record in str(sip_message.sip).split('\n') if 'Media Attribute' in record
                   and "sendrecv" not in record]
    return media_attrs


def is_valid_sip_call_id(call_id: str) -> bool:
    """
    Validates a SIP Call-ID header value.
    call_id: The Call-ID string to validate.
    returns: True if the Call-ID appears valid, False otherwise.
    """
    # Strip surrounding whitespace and normalize
    call_id = call_id.strip()

    # SIP Call-ID generally follows the format: uniqueid@host
    pattern = r"^[a-zA-Z0-9\.\-_]+@[a-zA-Z0-9\.\-]+$"
    return bool(re.match(pattern, call_id))


def get_multiple_attrs(attrs: str) -> list:
    """
    Method that extracts common part for string using right split and " " as split character
    Example: 'Media Attribute (a): fmtp:98 profile-level-id=42B00B;packetization-mode=1' to ->
          -> 'profile-level-id=42B00B;packetization-mode=1'
    @param attrs: String with media attribute data
    @return: Split string
    """
    if not attrs:
        return []
    stripped_attrs = attrs.split(' ', 1)[-1].lower().replace(' ', '')
    return stripped_attrs.split(";")


def is_having_similar_attrs(media_attr: str, actual_media_attrs: list) -> bool:
    """
    Method that searches for same attributes but in a different order in CHE responses
    @param media_attr: String with expected attributes data
    @param actual_media_attrs: list with all attributes reported by CHE
    @return: True or False
    """
    def cleanup_media_str(input_string):
        """
        Helper method to clean up the stings and prepare then for following checks
        @param input_string: string with media attribute data
        @return: unified string prepared to comparison
        """

        result = input_string.lower()
        result = result.replace('media attribute (a): ', '')

        return result

    media_attr = cleanup_media_str(media_attr)
    exp_attrs_list = get_multiple_attrs(media_attr)

    for act_media_attr in actual_media_attrs:
        # Check matches in expected and actual media attribute data
        act_media_attr = cleanup_media_str(act_media_attr)
        act_attrs_list = get_multiple_attrs(act_media_attr)

        # Count number of occurrences of each symbol in string and compare with expected
        if Counter("".join(act_attrs_list)) == Counter("".join(exp_attrs_list)):
            return True
    # If no match found
    return False
