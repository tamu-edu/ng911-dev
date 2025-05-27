import xml.etree.ElementTree as XML_ElementTree
import re
from datetime import datetime
from bs4 import BeautifulSoup
from services.aux.message_services import extract_all_contents_from_message_body


def is_valid_xml(xml_body: str) -> bool:
    """
    Checks if given xml body string as a param is a valid XML
    :param xml_body: Full xml body
    :return: True or False
    """
    # Try to parse XML
    try:
        XML_ElementTree.fromstring(xml_body)
    except XML_ElementTree.ParseError:
        return False
    return True


def extract_all_xml_bodies_from_message(message) -> list:
    """
    Extracts all message bodies which are correct XML
    :param message: Full HTTP/SIP message
    :return: List of XML message bodies or empty list if not found
    """
    xml_list = []
    for body in extract_all_contents_from_message_body(message):
        if 'body' in body:
            if is_valid_xml(body['body']):
                xml_list.append(body['body'])
    return xml_list


def extract_xml_body_string_from_file(file_path: str) -> str:
    """
    Extracts xml body string from the file
    :param file_path: path to the file
    :return: XML body as a string or None if not found
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    # XML pattern from first found '<?xml' until last '>'
    xml_pattern = r'(<\?xml.*?\?>.*?<\s*/\s*[^>]*\s*>)'
    match = re.search(r'<\?xml.*?\?>.*', file_content, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return ""


def extract_all_values_for_xml_tag_name(xml: str, tag_name: str) -> list:
    """
    Parses given xml and returns values of specified tag name
    :param xml: xml body string
    :param tag_name: tag to search for in xml body
    :return: xml tag values as a list of string or empty list if not found
    """
    xml_parsed = BeautifulSoup(xml, 'xml')
    values_list = []
    # Iterate through all tag blocks found
    for found_tag in xml_parsed.find_all(tag_name):
        # Remove opening and closing tags
        tag_content = re.sub(r'<[^>]+>', '', str(found_tag))
        values_list.extend(
            [
                # For each value remove whitespaces
                re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', value)
                for value in tag_content.split('\n')
                if re.search(r'\S', value)  # Process only alphanumeric lines
            ]
        )
    return values_list


def extract_location_id_from_text(text: str) -> str:
    """
    Extracts value of location id or locationUsed id and returns as a string or None if not found.
    Example location tag:
    <locationUsed id="12345678999999"/>
    :param text: text string
    :return: value of location id or locationUsed id or None if not found
    """
    pattern = r'<(?:locationUsed|location)\s+id="(\d+)"'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return ""


def is_http_lost_expired(output_xml: str) -> bool:
    """
    Checks expires parameter in HTTP LoST XML message body and returns True if message is expired
    :param output_xml: XML string from output message
    :return: True if message is expired or False
    """
    match = re.search(r'expires="([^"]+)"', output_xml)
    if not match:
        return False
    expires = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%SZ")
    current_time = datetime.utcnow()
    if expires < current_time:
        return True
    else:
        return False


def extract_xml_expiration_time_as_timestamp(output_xml: str) -> float | None:
    """
    Extracts from given XML date from expires parameter and returns as a timestamp
    :param output_xml: XML body string
    """
    match = re.search(r'expires="([^"]+)"', output_xml)
    if not match:
        return None
    expires = datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%S.%f%z')
    return expires.timestamp()
