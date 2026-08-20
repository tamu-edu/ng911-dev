from checks.general.checks import is_test_data_the_same

from services.aux_services.json_services import iso_to_timestamp
from services.aux_services.sip_msg_body_services import is_valid_sip_uri
from services.aux_services.xml_services import EasyXML


def validate_ecrf_service_urn_response(test_data):
    try:
        assert test_data.stimulus_message, "NOT RUN -> No stimulus message found."

        assert (
            test_data.ecrf_to_esrp_response_message
        ), "FAILED -> No ECRF-LVF to ESRP response found."

        wrong_code_msg = "FAILED -> Wrong ECRF-LVF to ESRP response CODE."
        response_code_validation = is_test_data_the_same(
            test_data.expected_response_code,
            test_data.ecrf_to_esrp_response_code,
            wrong_code_msg,
        )
        assert response_code_validation == "PASSED", response_code_validation

        assert isinstance(
            test_data.ecrf_response_xml, str
        ), f"FAILED -> Failed to extract ECRF-LVF to ESRP response XML. Actual: {test_data.ecrf_response_xml}"

        xml_req = EasyXML(test_data.stimulus_request_xml)
        xml_resp = EasyXML(test_data.ecrf_response_xml)

        # Requested Service URN MUST come from the urn:emergency:service namespace
        assert xml_req.service_text and str(xml_req.service_text).startswith(
            "urn:emergency:service"
        ), (
            "NOT RUN -> Stimulus findService does not target the "
            f"'{"urn:emergency:service"}' namespace. Actual: {xml_req.service_text}"
        )

        # No errors / no redirect
        assert (
            not xml_resp.errors
        ), f"FAILED -> ECRF-LVF response contains errors element.\n{xml_resp.errors_node}"
        assert (
            not xml_resp.redirect
        ), f"FAILED -> ECRF-LVF response contains redirect element.\n{xml_resp.redirect_node}"

        # No serviceSubstitution warning
        assert not xml_resp.warnings_serviceSubstitution, (
            "FAILED -> ECRF-LVF response contains a 'serviceSubstitution' warning.\n"
            f"{xml_resp.warnings_node}"
        )

        # Mapping node exists
        assert (
            xml_resp.mapping
        ), "FAILED -> No 'mapping' node found in ECRF-LVF to ESRP response."

        # <service> in response MUST match the requested URN
        fail_msg = "FAILED -> ECRF-LVF 'service' response doesn't match to 'service' in request."
        result = is_test_data_the_same(
            xml_req.service_text, xml_resp.mapping_service_text, fail_msg
        )
        assert result == "PASSED", result

        # One or more <uri> elements, each a valid SIP URI
        uri_values = xml_resp.mapping_uri_text_list
        assert uri_values, "FAILED -> ECRF-LVF response 'mapping' has no 'uri' element."
        for uri in uri_values:
            assert is_valid_sip_uri(
                uri
            ), f"FAILED -> Wrong response 'uri' format. Actual: {uri}"

        # Expires attribute is a future timestamp relative to the response time
        assert (
            xml_resp.mapping_expires
            and test_data.response_timestamp
            < iso_to_timestamp(xml_resp.mapping_expires)
        ), (
            "FAILED -> ECRF-LVF response 'expires' time is lower than response time. "
            f"Actual: {xml_resp.mapping_expires}"
        )

        # <path> with at least one <via>
        assert (
            xml_resp.path_via
        ), "FAILED -> ECRF-LVF response 'path' node doesn't exist or doesn't contain 'via' objects."

        # <locationUsed> id MUST match the id from the request
        fail_msg = "FAILED -> ECRF-LVF 'locationUsed' id in response doesn't match to 'locationUsed' id in request."
        result = is_test_data_the_same(
            xml_req.location_id, xml_resp.locationUsed_id, fail_msg
        )
        assert result == "PASSED", result

        return "PASSED"
    except AssertionError as e:
        return str(e)
