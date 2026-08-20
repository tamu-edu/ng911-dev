import xml.etree.ElementTree as XML_ElementTree
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Any, Union
from pyshark.packet.packet import Packet


from bs4 import BeautifulSoup
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)


class EasyXML:
    """
    Parses an XML string and provides dot-access to its data.

    Usage:
        s = EasyXML(xml_string)
        Allowed camelCase or lowercase (ex. s.findservice_xmlns or s.findService_xmlns)

        s.mapping                    # True  (tag exists)
        s.mapping_service_text       # 'urn:service:sos'
        s.path_via_list              # List of path via objects [{'source': 'ecrf-1.example'}, ...]
        s.mapping_uri_text           # ['sip:...', 'xmpp:...']
        s.mapping_serviceboundary_polygon_exterior_linearring_pos_text  # [[lat, lon], ...]
        s.findServiceResponse_xmlns  # ['urn:...', ...]
        s.mapping_node               # raw xml string of the node
        s.unknown                    # False  (missing key)
    """

    def __init__(self, xml_string: str):
        self.__dict__["_tags"] = set()
        self.__dict__["_attrs"] = {}
        self.__dict__["_nodes"] = {}
        try:
            xml_string = xml_string.strip()
            root = XML_ElementTree.fromstring(xml_string)

            local = self._local(root.tag).lower()
            xmlns_values = re.findall(r'xmlns(?::\w+)?="([^"]+)"', xml_string)
            if xmlns_values:
                self._attrs[f"{local}_xmlns"] = xmlns_values

            for attr, value in root.attrib.items():
                attr_local = self._local(attr).lower()
                self._attrs[attr_local] = value

            for child in root:
                self._parse_element(child)

            self._tags.add(local)
            self._nodes[local] = root
        except Exception as e:
            print(f"[XMLNode] parse error: {e}")

    @staticmethod
    def _local(tag: str) -> str:
        return tag.split("}")[-1] if "}" in tag else tag

    def _parse_element(self, element, prefix=""):
        try:
            local = self._local(element.tag).lower()
            key = f"{prefix}{local}" if prefix else local
            self._tags.add(key)
            self._nodes[key] = element

            buckets = defaultdict(list)
            for attr, value in element.attrib.items():
                attr_local = self._local(attr).lower()
                buckets[f"{key}_{attr_local}"].append(value)

            for attr_key, values in buckets.items():
                self._attrs[attr_key] = values[0] if len(values) == 1 else values

            text = (element.text or "").strip()
            if text:
                parts = text.replace(",", "").split()
                try:
                    coords = [float(p) for p in parts] if len(parts) > 1 else text
                except ValueError:
                    coords = text

                text_key = f"{key}_text"
                if text_key in self._attrs:
                    existing = self._attrs[text_key]
                    if not isinstance(existing, list) or not isinstance(
                        existing[0], list
                    ):
                        self._attrs[text_key] = [existing, coords]
                    else:
                        self._attrs[text_key].append(coords)
                else:
                    self._attrs[text_key] = coords

            child_counts = defaultdict(int)
            for child in element:
                child_local = self._local(child.tag).lower()
                child_counts[child_local] += 1

            for child in element:
                child_local = self._local(child.tag).lower()
                child_key = f"{key}_{child_local}"
                if child_counts[child_local] > 1:
                    self._parse_element(child, prefix=f"{key}_")
                    child_attrs = {}
                    for attr, value in child.attrib.items():
                        attr_local = self._local(attr).lower()
                        child_attrs[attr_local] = value

                    existing = self._attrs.get(child_key, [])
                    if not isinstance(existing, list):
                        existing = [existing]
                    existing.append(child_attrs if child_attrs else True)
                    self._attrs[child_key] = existing
                else:
                    self._parse_element(child, prefix=f"{key}_")
                    child_attrs = {}
                    for attr, value in child.attrib.items():
                        attr_local = self._local(attr).lower()
                        child_attrs[attr_local] = value
                    if child_attrs:
                        self._attrs[child_key] = child_attrs
        except Exception as e:
            print(f"[XMLNode] element parse error: {e}")
            return False

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            if name.endswith("_list"):
                key = name[:-5]
                attrs = self.__dict__.get("_attrs", {})
                tags = self.__dict__.get("_tags", set())
                lower = key.lower()

                result = attrs.get(key) or attrs.get(lower)
                if result is not None:
                    if not isinstance(result, list):
                        return [result]
                    return result
                if key in tags or lower in tags:
                    return [True]
                return []

            if name.endswith("_node"):
                key = name[:-5]
                nodes = self.__dict__.get("_nodes", {})
                if key in nodes:
                    return XML_ElementTree.tostring(nodes[key], encoding="unicode")
                lower = key.lower()
                if lower in nodes:
                    return XML_ElementTree.tostring(nodes[lower], encoding="unicode")
                return False

            if name in self._attrs:
                return self._attrs[name]
            if name in self._tags:
                return True
            lower = name.lower()
            if lower in self._attrs:
                return self._attrs[lower]
            if lower in self._tags:
                return True
            return False
        except Exception as e:
            print(f"[XMLNode] attribute error '{name}': {e}")
            return False


def is_xml_equal(a: str, b: str) -> bool:
    """Compare two XML strings semantically, ignoring whitespace differences.

    Args:
        a: First XML string.
        b: Second XML string.

    Returns:
        True if XML structures are semantically equal.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        return False

    def normalize(tree):
        for el in tree.iter():
            el.text = (el.text or "").strip()
            el.tail = (el.tail or "").strip()
        return XML_ElementTree.tostring(tree, encoding="unicode")

    try:
        return normalize(XML_ElementTree.fromstring(a.strip())) == normalize(
            XML_ElementTree.fromstring(b.strip())
        )
    except XML_ElementTree.ParseError as e:
        print(f"XML parse error: {e}")
        return False


def is_malformed_xml(source: Union[str, Packet]) -> bool:
    """Check if XML is malformed, accepting either an XML string or a PyShark HTTP packet.

    Args:
        source: Either an XML string or a PyShark HTTP packet with HTTP layer.

    Returns:
        True if XML is malformed or missing, False if valid.
    """
    try:
        if isinstance(source, str):
            xml_string = source
        elif isinstance(source, Packet):
            if not hasattr(source, "http"):
                print(f"Packet {source.number}: no HTTP layer")
                return False

            content_type = source.http.get_field("content_type") or ""
            if "xml" not in content_type.lower():
                print(
                    f"Packet {source.number}: Content-Type is not XML: {content_type}"
                )
                return False

            raw = source.http.file_data
            if isinstance(raw, str) and not raw.strip().startswith("<"):
                xml_string = bytes.fromhex(raw.replace(":", "")).decode("utf-8")
            else:
                xml_string = raw
        else:
            print(
                f"Invalid type: expected str or PyShark Packet, got {type(source).__name__}"
            )
            return True

        XML_ElementTree.fromstring(xml_string)
        return False

    except XML_ElementTree.ParseError as e:
        print(f"Malformed XML: {e}")
        return True
    except (AttributeError, ValueError) as e:
        print(f"Could not extract XML from packet: {e}")
        return True


def is_valid_xml(xml_body: str) -> bool:
    """
    Checks if given xml body string as a param is a valid XML
    :param xml_body: Full xml body
    :return: True or False
    """
    # Try to parse XML
    try:
        if "<!DOCTYPE" in xml_body or "<!ENTITY" in xml_body:
            raise ValueError("Unsafe XML content")

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
    xml_list: List[Any] = []
    for body in extract_all_contents_from_message_body(message):
        if "body" in body:
            if is_valid_xml(body["body"]):
                xml_list.append(body["body"])
    return xml_list


def extract_xml_body_string_from_file(file_path: str) -> str | None:
    """
    Extracts xml body string from the file
    :param file_path: path to the file
    :return: XML body as a string or None if not found
    """
    xml_body = None
    is_path = False
    try:
        is_path = Path(file_path).exists()
    except OSError:
        pass
    if is_path:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
        # XML pattern from first found '<?xml' until last '>'
        # xml_pattern = r'(<\?xml.*?\?>.*?<\s*/\s*[^>]*\s*>)'
        match = re.search(r"<\?xml.*?\?>.*", file_content, re.DOTALL)
        if match:
            return match.group(0)
    return xml_body


def extract_all_values_for_xml_tag_name(xml: str, tag_name: str) -> list:
    """
    Parses given xml and returns values of specified tag name
    :param xml: xml body string
    :param tag_name: tag to search for in xml body
    :return: xml tag values as a list of string or empty list if not found
    """
    xml_parsed = BeautifulSoup(xml, "xml")
    values_list: List[Any] = []
    # Iterate through all tag blocks found
    for found_tag in xml_parsed.find_all(tag_name):
        # Remove opening and closing tags
        tag_content = re.sub(r"<[^>]+>", "", str(found_tag))
        values_list.extend(
            [
                # For each value remove whitespaces
                re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", value)
                for value in tag_content.split("\n")
                if re.search(r"\S", value)  # Process only alphanumeric lines
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


def extract_location_from_text(message_body: str) -> str:
    """
    Extracts the position value from an XML string by trying common GML position tag variants.
    Checks for "gs:pos", "gml:pos", and "pos" tags in that order, returning the first match.
    :param message_body: XML data represented as text string
    :return: position value as a string, or empty string if not found
    """
    patterns = [
        r"<gs:pos>(.*?)</gs:pos>",
        r"<gml:pos>(.*?)</gml:pos>",
        r"pos>(.*?)</",
    ]
    for pattern in patterns:
        if match := re.search(pattern, message_body):
            return match.group(1)
    return ""


def extract_emergency_call_incident_id_from_ext(
    message_body: str,
) -> tuple[None, None] | tuple[str | None | Any, str | None | Any]:
    """
    Extracts callId and incidentTrackingId from an emergencyCallIncidentId element.
    Matches the element regardless of namespace prefix (e.g. <nena:emergencyCallIncidentId .../>).
    :param message_body: XML data represented as text string
    :return: tuple with  "callId" and "incidentTrackingId"; missing attributes default to ""
    """
    call_id = None
    incident_tracking_id = None
    element_match = re.search(
        r"<[^>]*emergencyCallIncidentId\b[^>]*>",
        message_body,
        re.DOTALL,
    )
    if not element_match:
        return call_id, incident_tracking_id
    element = element_match.group(0)
    for attr in ("callId", "incidentTrackingId"):
        if attr_match := re.search(rf'{attr}\s*=\s*"([^"]*)"', element):
            if attr == "callId":
                call_id = attr_match.group(1)
            elif attr == "incidentTrackingId":
                incident_tracking_id = attr_match.group(1)
    return call_id, incident_tracking_id


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
    expires = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S.%f%z")
    return expires.timestamp()


def extract_tag_content(xml_data: str, tag_name: str) -> str:
    """
    Extracts the content of the first occurrence of a given XML tag.
    @param xml_data: The XML data as a string.
    @param tag_name: The name of the tag to search for (can include namespace, e.g., 'dyn:speed').
    @return:
    """
    pattern = rf"<[^>]*{tag_name}[^>]*>(.*?)</[^>]*{tag_name}>"
    match = re.search(pattern, xml_data, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return ""


def get_xml(xml_source) -> str:
    """
    Tries to get XML object from xml_source which can be path to file or XML str

    :param xml_source: source of XML payload. Can be a str containing XML,
                        or str with full path to file containing XML body
    :return: XML object as a str or None
    """
    if not isinstance(xml_source, str):
        return ""
    if is_valid_xml(xml_source):
        return xml_source
    return extract_xml_body_string_from_file(xml_source)


def extract_xml(source: str) -> str:
    """
    Extracts an XML document from a string that may contain leading non-XML content
    (e.g. HTTP response headers prepended to the body). Tries in order: return the
    source as-is if already valid XML, scan for any processing instruction (<? …>),
    then scan for the first element opening tag.

    :param source: Raw string possibly containing an embedded XML document.
    :return: Extracted XML string, or empty string if none found.
    """
    if not isinstance(source, str) or not source.strip():
        return ""

    source = source.strip()

    if is_valid_xml(source):
        return source

    match = re.search(r"<\?[\s\S]*", source)
    if match:
        return match.group(0).strip()

    match = re.search(r"<[a-zA-Z_:][^\s/>]*[\s\S]*", source)
    if match:
        return match.group(0).strip()

    return ""
