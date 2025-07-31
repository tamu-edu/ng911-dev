import xml.etree.ElementTree as ET

from services.aux_services.locations_services import is_valid_distance_between_points, is_valid_speed_between_messages, \
    extract_shape_data, is_point_in_shape
from services.aux_services.sip_services import extract_message_data
from services.aux_services.xml_services import extract_tag_content


def extract_changed_tags(suffix: str, xml_string: str) -> str or None:
    # Register the namespace used in the XML
    ns = {'sf': 'urn:ietf:params:xml:ns:simple-filter'}

    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Find the 'changed' element using the namespace
    changed_elem = root.find('.//sf:changed', namespaces=ns)

    # Return the 'from' attribute value if it exists
    if changed_elem is not None and suffix in changed_elem.attrib:
        return changed_elem.attrib[suffix]

    return None  # or raise an exception if preferred


# Variation methods
# Variation #1
def validate_lis_responses_distance_filter(**response_data):
    """
    Verifies geolocations of first and second SIP NOTIFY PIDF-LO body received,
    distance should be more than 300 meters.
    """
    messages = response_data['responses']
    subscribe_msg = response_data['subscribe_msg']
    coords = []

    if not messages or not subscribe_msg:
        return "FAILED -> No SIP SUBSCRIBE/NOTIFY messages found."

    for message in messages:
        coords.append(extract_tag_content(extract_message_data(message), 'pos'))
    if not all(coords) and coords[0] == 'None':
        return "FAILED -> Location coordinates are not found in output message."
    threshold = int(extract_tag_content(extract_message_data(subscribe_msg), 'moved'))
    if not threshold:
        return "FAILED -> Cannot found threshold data in SIP SUBSCRIBE message."
    if not is_valid_distance_between_points(coords, threshold):
        return f"FAILED -> Distance between coordinates is less than {str(threshold)} meters."

    return "PASSED"


# Variation #2
def validate_lis_responses_speed_filter(**response_data):
    """
    Verifies values of "speed" parameter of first and second SIP NOTIFY PIDF-LO bodies,
    change of speed shall be higher than 3 meters/second.
    """
    messages = response_data['responses']
    subscribe_msg = response_data['subscribe_msg']
    speed_list = []

    if not messages or not subscribe_msg:
        return "FAILED -> No SIP SUBSCRIBE/NOTIFY messages found."

    for message in messages:
        speed_list.append(extract_tag_content(extract_message_data(message), 'speed'))
    if not all(speed_list) and speed_list[0] == 'None':
        return "FAILED -> Speed values are not found in output message."

    threshold = int(extract_changed_tags('by', extract_message_data(subscribe_msg)))
    if not is_valid_speed_between_messages(speed_list, threshold):
        return "FAILED -> Detected speed values between messages do not meet the minimum allowed threshold."

    return "PASSED"


# Variation #3
def validate_lis_responses_element_val_change_filter(**response_data):
    """
    Verifies if first SIP NOTIFY received contain different country civic address value in PIDF-LO body.
    """
    messages = response_data['responses']
    subscribe_msg = response_data['subscribe_msg']
    changed_from = extract_changed_tags('from', extract_message_data(subscribe_msg))

    if not messages or not changed_from:
        return "FAILED -> No SIP SUBSCRIBE/NOTIFY messages found."

    elem_values_list = []
    for message in messages:
        elem_values_list.append(extract_tag_content(extract_message_data(message), 'country'))
    if not all(elem_values_list) and elem_values_list[0] == 'None':
        return "FAILED -> Country record data is not found in output message."

    if elem_values_list[0] != changed_from:
        return "FAILED -> 'Country' value should not differ between SIP SUBSCRIBE and first NOTIFY message."

    if elem_values_list[1] == changed_from:
        return "FAILED -> 'Country' value should differ between first SIP NOTIFY and the next one."
    return "PASSED"


# Variation #4
def validate_lis_responses_entering_area_change_filter(**response_data):
    """
    Verifies if first SIP NOTIFY received contain PIDF-LO body with Point geolocation with coordinates.
    """
    messages = response_data['responses']
    sip_subscribe = response_data['subscribe_msg']
    coords = []

    if not messages or not sip_subscribe:
        return "FAILED -> No SIP SUBSCRIBE/NOTIFY messages found."

    shape_data = extract_shape_data(extract_message_data(sip_subscribe))

    for message in messages:
        coords.append(extract_tag_content(extract_message_data(message), 'pos'))
    if not all(coords) and coords[0] == 'None':
        return "FAILED -> Location coordinates are not found in output message."
    if not coords:
        return "FAILED -> No coordinates data found in output message."

    if len(coords) < 2:
        return "FAILED -> Number of NOTIFY messages cannot be less than 2."

    if is_point_in_shape(shape_data, coords[0]):
        return "FAILED -> First NOTIFY message should be outside the area."

    if not is_point_in_shape(shape_data, coords[1]):
        return "FAILED -> Second NOTIFY message should be inside the area."

    return "PASSED"


# Variation #5
def validate_lis_responses_location_type_change_filter(**response_data):
    """
    Checks if the first NOTIFY has in xml: <cl:civicAddress> and </cl:civicAddress>.
    """
    messages = response_data['responses']

    if not messages:
        return "FAILED -> No coordinates data found in output message."

    if len(messages) < 2:
        return "FAILED -> Number of NOTIFY messages cannot be less than 2."

    # Check first NOTIFY message
    try:
        if extract_tag_content(extract_message_data(messages[0]), 'civicAddress'):
            return "FAILED -> No 'civicAddress' data should be included in first NOTIFY message."
    except ValueError:
        pass

    # Check second NOTIFY message
    try:
        if not extract_tag_content(extract_message_data(messages[1]), 'civicAddress'):
            return "FAILED -> No 'civicAddress' data found"
    except ValueError:
        return "FAILED -> No 'civicAddress' data found"

    return "PASSED"
