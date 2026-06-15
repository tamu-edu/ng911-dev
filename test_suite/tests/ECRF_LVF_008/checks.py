from checks.general.checks import is_test_data_the_same

from services.aux_services.json_services import iso_to_timestamp
from services.aux_services.sip_msg_body_services import is_valid_sip_uri
from services.aux_services.xml_services import EasyXML


def validate_ecrf_response(
    test_data,
):
    try:
        assert test_data.stimulus_message, "NOT RUN -> No stimulus message found."

        # Check Variant2 forwarded request
        if test_data.is_variant_2:
            forwarded_check_result = validate_ecrf_request_forwarded(test_data)
            assert forwarded_check_result == "PASSED", forwarded_check_result

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

        # Check errors or redirect in response
        assert (
            not xml_resp.errors
        ), f"FAILED -> ECRF-LVF to ESRP response contains errors element.\n{xml_resp.errors_node}"
        assert (
            not xml_resp.redirect
        ), f"FAILED -> ECRF-LVF to ESRP response contains redirect element.\n{xml_resp.redirect_node}"

        # Check mapping node exists
        assert (
            xml_resp.mapping
        ), "FAILED -> No 'mapping' node found in ECRF-LVF to ESRP response."

        # Check SIP URI
        assert is_valid_sip_uri(
            xml_resp.mapping_uri_text
        ), f"FAILED -> Wrong response 'uri' format. Actual: {xml_resp.mapping_uri_text}"

        # Check 'service' the same
        wrong_code_msg = "FAILED -> ECRF-LVF 'service' response doesn't match to 'service' in request."
        result = is_test_data_the_same(
            xml_req.service_text, xml_resp.mapping_service_text, wrong_code_msg
        )
        assert result == "PASSED", result

        # Check expires date
        assert (
            xml_resp.mapping_expires
            and test_data.response_timestamp
            < iso_to_timestamp(xml_resp.mapping_expires)
        ), f"FAILED -> ECRF-LVF response 'expires' time is lower then response time. Actual: {xml_resp.mapping_expires}"

        # Check path element
        assert (
            xml_resp.path_via
        ), "FAILED -> 'ECRF-LVF response 'path' node doesn't exist or doesn't contain 'via' objects."

        # Check 'locationUsed' id the same
        fail_msg = "FAILED -> ECRF-LVF 'locationUsed' id in response doesn't match to 'locationUsed' id in request."
        result = is_test_data_the_same(
            xml_req.location_id, xml_resp.locationUsed_id, fail_msg
        )
        assert result == "PASSED", result

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_ecrf_request_forwarded(
    test_data,
):
    name_space = "urn:emergency:xml:ns:lostExt:Ids"

    try:
        assert (
            test_data.ecrf_to_ecrf_forwarded_message
        ), "FAILED -> 'No forwarded request from ECRF-LVF to ECRF-LVF-2 found."
        assert isinstance(
            test_data.forwarded_request_xml, str
        ), f"FAILED -> Failed to extract ECRF-LVF to to ECRF-LVF-2 request XML. Actual: {test_data.forwarded_request_xml}"

        xml_req = EasyXML(test_data.stimulus_request_xml)
        xml_fwd = EasyXML(test_data.forwarded_request_xml)
        xml_resp = EasyXML(test_data.ecrf_response_xml)

        # Check namespace
        assert (
            name_space in xml_fwd.findService_xmlns
        ), f"FAILED -> Namespace {name_space} not found. Actual: {xml_fwd.findService_xmlns}"
        # Check emergencyCallIncidentId
        assert (
            xml_fwd.emergencyCallIncidentId
        ), "FAILED -> 'No emergencyCallIncidentId element in request from ECRF-LVF to ECRF-LVF-2 found."

        # Check callId
        fail_msg = "FAILED -> Forwarded 'callId' is not the same as in initial request to ECRF-LVF"
        validation = is_test_data_the_same(
            xml_req.emergencyCallIncidentId_callId,
            xml_fwd.emergencyCallIncidentId_callId,
            fail_msg,
        )
        assert validation == "PASSED", validation

        # Check incidentTrackingId
        fail_msg = "FAILED -> Forwarded 'incidentTrackingId' is not the same as in initial request to ECRF-LVF"
        validation = is_test_data_the_same(
            xml_req.emergencyCallIncidentId_incidentTrackingId,
            xml_fwd.emergencyCallIncidentId_incidentTrackingId,
            fail_msg,
        )
        assert validation == "PASSED", validation

        # Check path element
        assert (
            len(xml_resp.path_via_list) > 1
        ), f"FAILED -> 'ECRF-LVF response 'path' node doesn't exist or contains only one 'via' objects. Actual: {xml_resp.path_via_list}"

        return "PASSED"
    except AssertionError as e:
        return str(e)
