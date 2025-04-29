from services.aux.message_services import extract_sip_uri_from_text
from services.aux.xml_services import (
    is_valid_xml,
    extract_all_values_for_xml_tag_name,
    extract_location_id_from_text, is_http_lost_expired
)


def test_http_lost_list_services_response(stimulus_xml: str, output_xml: str, service_urn: str, by_location=True):
    """
    Test to validate listServicesResponse XML body from output message which is a response for stimulus_xml
    :param stimulus_xml: xml body string from stimulus message
    :param output_xml: xml body string from output message
    """
    try:
        assert is_valid_xml(output_xml), "FAILED -> XML body incorrect"
        for service in extract_all_values_for_xml_tag_name(output_xml, "serviceList"):
            assert service_urn in service, f"FAILED -> service {service} does not match {service_urn}"
        if by_location:
            assert extract_location_id_from_text(stimulus_xml) == extract_location_id_from_text(output_xml), \
                f"FAILED -> locationUsed ID in response does not match location ID from request"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_http_lost_find_service_response(stimulus_xml: str, output_xml: str):
    """
    Test to validate findServiceResponse XML body from output message which is a response for stimulus_xml
    :param stimulus_xml: xml body string from stimulus message
    :param output_xml: xml body string from output message
    """
    try:
        assert is_valid_xml(output_xml), "FAILED -> XML body is incorrect"
        assert "<findServiceResponse" in output_xml, "FAILED -> findServiceResponse not found"
        assert is_http_lost_expired(output_xml) is False, "FAILED -> HTTP LoST message is expired"
        assert (extract_all_values_for_xml_tag_name(stimulus_xml, "service") ==
                extract_all_values_for_xml_tag_name(output_xml, "service")), \
            "FAILED -> 'service' from findServiceResponse does not match findService request"
        assert extract_all_values_for_xml_tag_name(output_xml, "serviceBoundary"), \
            "FAILED -> serviceBoundary not found"
        assert extract_sip_uri_from_text(
            str(extract_all_values_for_xml_tag_name(output_xml, "uri"))
        ), "FAILED -> SIP URI not found in 'uri'"
        # serviceNumber MUST be '911' if present
        service_number = extract_all_values_for_xml_tag_name(output_xml, "serviceNumber")
        if service_number:
            assert "911" in service_number, "FAILED -> serviceNumber is not 911"
        assert extract_location_id_from_text(stimulus_xml) == extract_location_id_from_text(output_xml), \
            f"FAILED -> locationUsed ID in response does not match location ID from request"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_http_lost_find_service_response_with_sip_uri_check(
        stimulus_xml: str,
        output_xml: str,
        expected_sip_uri_list: list
):
    """
    Test to validate findServiceResponse XML body from output message which is a response for stimulus_xml
    The test also checks if SIP URI from response matches expected value
    :param stimulus_xml: xml body string from stimulus message
    :param output_xml: xml body string from output message
    :param expected_sip_uri_list: list of SIP URIs expected in output message
    """
    try:
        test_find_service_response_result = test_http_lost_find_service_response(stimulus_xml, output_xml)
        if test_find_service_response_result == "PASSED":
            assert extract_sip_uri_from_text(
                str(extract_all_values_for_xml_tag_name(output_xml, "uri"))
            ) in expected_sip_uri_list, \
                f"FAILED -> SIP URI in findServiceResponse does not match one of expected values: {expected_sip_uri_list}"
        else:
            return test_find_service_response_result
        return "PASSED"
    except AssertionError as e:
        return str(e)
