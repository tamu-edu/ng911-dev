from services.aux.aux_services import is_valid_http_https_url
from services.aux.xml_services import is_valid_xml, extract_xml_expiration_time_as_timestamp, \
    extract_all_values_for_xml_tag_name


def test_if_location_response_contains_correct_location_uri(output_xml: str):
    """
    Test to validate if XML with locationResponse contains correct locationURI URL
    :param output_xml: XML body from HTTP response
    """
    try:
        assert output_xml, "FAILED -> XML body not found"
        assert is_valid_xml(output_xml), "FAILED -> XML body is incorrect"
        assert is_valid_http_https_url(
            extract_all_values_for_xml_tag_name(output_xml, 'locationURI')[0]
        ), "FAILED -> locationURI has incorrect URL"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_location_response_expiration_time(output_xml: str, output_message_timestamp: float):
    """
    Test to validate if XML with locationResponse contains
    expiration time between 30min and 24h
    :param output_xml: XML body from HTTP response
    """
    try:
        assert output_xml, "FAILED -> XML body not found"
        xml_timestamp = float(extract_xml_expiration_time_as_timestamp(output_xml))
        assert xml_timestamp > (output_message_timestamp + (30 * 60)), \
            "FAILED -> expiration time of XML message is lower than 30min"
        assert xml_timestamp < (output_message_timestamp + (24 * 60 * 60)), \
            "FAILED -> expiration time of XML message is higher than 24h"
        return "PASSED"
    except AssertionError as e:
        return str(e)
