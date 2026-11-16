import re

from checks.general.checks import is_test_data_the_same
from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_urn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn,
)
from services.aux_services.aux_services import validate_ip_port_combo
from services.aux_services.json_services import (
    is_valid_fqdn,
    is_timestamp,
    EasyJSON,
)
from services.aux_services.message_services import normalize_string_for_comparison
from services.aux_services.sip_msg_body_services import (
    is_valid_sip_call_id,
)
from services.aux_services.xml_services import is_xml_equal, is_valid_xml
from tests.ESRP_019.constants import (
    DIRECTIONS,
    LOCATION_QUERY_LOG,
    LOCATION_RESPONSE_LOG,
    RESPONSE_CODES,
)


def precondition_validation(test_data):
    """
    Validates Initial Test Data (messages and IDs existence)

    Args:
        test_data: Instance of TestData containing test data for the test case.
    """
    try:
        assert test_data.stimulus_message, "NOT RUN -> No stimulus message found."

        assert (
            test_data.stimulus_call_id_sip
        ), "NOT RUN -> No stimulus call ID sip 'Call-ID' found."

        assert (
            test_data.stimulus_call_id
        ), "NOT RUN -> No stimulus call id 'Call-Info' found."

        assert (
            test_data.stimulus_incident_id
        ), "NOT RUN -> No stimulus incident id 'Call-Info' found."

        if test_data.variation_number in (
            1,
            3,
        ):
            assert (
                test_data.esrp_to_lis_http_post_message
            ), "FAILED -> No ESRP to LIS HTTP POST message found."
        else:
            assert (
                test_data.esrp_to_lis_subscribe_request
            ), "FAILED -> No ESRP to LIS SUBSCRIBE message found."

        assert (
            test_data.esrp_to_logger_post_location_query_message
        ), "FAILED -> No ESRP to LOGGER HTTP POST message with 'LocationQueryLogEvent' found."

        assert (
            test_data.esrp_to_logger_post_location_response_message
        ), "FAILED -> No ESRP to LOGGER HTTP POST message with 'LocationResponseLogEvent' found."

        assert (
            test_data.esrp_to_logger_post_location_query_jws
        ), "FAILED -> Can't extract 'LocationQueryLogEvent' JWS data."

        assert (
            test_data.esrp_to_logger_post_location_response_jws
        ), "FAILED -> Can't extract 'LocationResponseLogEvent' JWS data."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_location_query_response(test_data):
    try:
        initial_data_check = precondition_validation(test_data)
        assert initial_data_check == "PASSED", initial_data_check

        log_query_event_check = location_event_fields_validation(
            test_data,
            test_data.esrp_to_logger_post_location_query_jws,
            LOCATION_QUERY_LOG,
        )
        assert log_query_event_check == "PASSED", log_query_event_check

        log_response_event_check = location_event_fields_validation(
            test_data,
            test_data.esrp_to_logger_post_location_response_jws,
            LOCATION_RESPONSE_LOG,
        )
        assert log_response_event_check == "PASSED", log_response_event_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def location_event_fields_validation(test_data, payload_data, event_type):
    """
    Validates LocationQueryLogEvent and LocationResponseLogEvent data.

    Args:
        test_data: Instance of TestData containing test data for the test case.
        payload_data: JSON object containing payload data for the test case.
        event_type: LocationQueryLogEvent or LocationResponseLogEvent type.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    required_fields = (
        "logEventType",
        "timestamp",
        "elementId",
        "agencyId",
        "direction",
        "callId",
        "incidentId",
        "callIdSip",
        "text",
    )

    if event_type == LOCATION_QUERY_LOG:
        required_fields = required_fields + ("queryId",)
        required_fields = required_fields + ("uri",)
    elif event_type == LOCATION_RESPONSE_LOG:
        required_fields = required_fields + ("responseId",)
        if test_data.variation_number == 3:
            required_fields = required_fields + ("responseStatus",)

    jws_data = None

    try:
        # Required Fields Check
        fields = assert_required_payload_fields(
            event_type, payload_data, required_fields, test_data
        )
        assert fields == "PASSED", fields

        if event_type == LOCATION_QUERY_LOG:
            jws_data = EasyJSON(test_data.esrp_to_logger_post_location_query_jws)
        elif event_type == LOCATION_RESPONSE_LOG:
            jws_data = EasyJSON(test_data.esrp_to_logger_post_location_response_jws)

        if not jws_data:
            return f"FAILED -> Failed to parse JWS payload of '{event_type}'."

        # Check timestamp
        assert is_timestamp(
            jws_data.timestamp
        ), f"FAILED -> Wrong timestamp format for {event_type}. Actual: {jws_data.timestamp}"

        # elementId check
        assert is_valid_fqdn(
            jws_data.elementId
        ), f"FAILED -> 'elementId' in JWS should be a valid FQDN format. Actual: '{jws_data.elementId}'"

        assert jws_data.elementId == test_data.esrp_fqdn, (
            f"FAILED -> 'elementId' value in JWS should be FQDN of ESRP.\n"
            f"Actual: '{jws_data.elementId}', Expected: '{test_data.esrp_fqdn}'"
        )

        # agencyId check
        assert is_valid_fqdn(
            jws_data.agencyId
        ), f"FAILED -> 'agencyId' in JWS should be a valid FQDN format. Actual: '{jws_data.agencyId}'"

        # callId check
        error_msg = (
            f"'{event_type}' 'callId' not the same as in Stimulus 'Call-Info callId'"
        )
        equality_check = is_test_data_the_same(
            _extract_value(test_data.stimulus_call_id), jws_data.callId, error_msg
        )
        assert equality_check == "PASSED", equality_check

        assert (
            result := test_emergency_call_id_urn(jws_data.callId)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_emergency_call_id_string_id(jws_data.callId)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_emergency_call_id_fqdn(jws_data.callId)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        # incidentId check
        error_msg = f"'{event_type}' 'incidentId' not the same as in Stimulus 'Call-Info incidentId'"
        equality_check = is_test_data_the_same(
            _extract_value(test_data.stimulus_incident_id),
            jws_data.incidentId,
            error_msg,
        )
        assert equality_check == "PASSED", equality_check
        assert (
            result := test_incident_tracking_id_urn(jws_data.incidentId)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_incident_tracking_id_string_id(jws_data.incidentId)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_incident_tracking_id_fqdn(jws_data.incidentId)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        # callIdSip check

        assert (
            test_data.stimulus_call_id_sip == jws_data.callIdSip
        ), f"FAILED -> '{event_type}' 'callIdSip' value not the same as in BCF to ESRP Invite 'callIdSip'"

        assert is_valid_sip_call_id(
            jws_data.callIdSip
        ), f"FAILED -> 'callIdSip' in '{event_type}' JWS should be a valid SIP Call ID. Actual: '{jws_data.callIdSip}'"

        # direction check
        assert (
            jws_data.direction.lower() in DIRECTIONS
        ), f"FAILED -> 'direction' value in '{event_type}' JWS should be one of {DIRECTIONS}. Actual: '{jws_data.direction}'"

        # uri field check
        if event_type == LOCATION_QUERY_LOG:
            assert jws_data.uri == _extract_value(test_data.geolocation_raw), (
                f"FAILED -> 'uri' field contains not the same value as INVITE Geolocation URI/URL.\n"
                f"Actual: '{jws_data.uri}'\n"
                f"Expected: '{_extract_value(test_data.geolocation_raw)}'"
            )

        # text field check
        text_field_check = validate_text_field(test_data, jws_data, event_type)
        assert text_field_check == "PASSED", text_field_check

        # Validate queryId and responseId. responseId = queryId
        q_r_check = validate_query_id_response_id_equality(test_data)
        assert q_r_check == "PASSED", q_r_check

        if event_type == LOCATION_QUERY_LOG:
            if not bool(re.match(r"^urn:emergency:uid:queryid:.*$", jws_data.queryId)):
                print(f"⚠️ Wrong 'queryId' format. Actual: {jws_data.queryId}")

        if event_type == LOCATION_RESPONSE_LOG:
            if not bool(
                re.match(r"^urn:emergency:uid:queryid:.*$", jws_data.responseId)
            ):
                print(f"⚠️ Wrong 'responseId' format. Actual: {jws_data.responseId}")

        # responseStatus check
        if event_type == LOCATION_RESPONSE_LOG and test_data.variation_number == 3:
            assert str(jws_data.responseStatus) == str(
                test_data.lis_response_status_code
            ), (
                f"FAILED -> Response code from LIS doesn't match 'responseStatus' code.\n"
                f"Expected: '{test_data.lis_response_status_code}'\n"
                f"Actual: '{jws_data.responseStatus}'"
            )

            assert str(jws_data.responseStatus) in RESPONSE_CODES, (
                f"FAILED -> Wrong 'responseStatus' code.\n"
                f"Actual: '{jws_data.responseStatus}'. Expected one of: {RESPONSE_CODES}"
            )

        # Check optional fields
        optional_fields = optional_attributes_validation(event_type, payload_data)
        assert optional_fields == "PASSED", optional_fields

        return "PASSED"

    except AssertionError as e:
        return str(e)


def validate_text_field(test_data, jws_data, event_type) -> str:
    try:
        if event_type == LOCATION_QUERY_LOG:
            if test_data.variation_number in (
                1,
                3,
            ):
                assert is_xml_equal(
                    jws_data.text, test_data.esrp_to_lis_http_post_message_body
                ), (
                    f"FAILED -> 'text' field of '{LOCATION_QUERY_LOG}' for Variation {test_data.variation_number} contains not the same value as ESRP to LIS HTTP POST Body.\n"
                    f"Actual: '{jws_data.text}'\n"
                    f"Expected: '{test_data.esrp_to_lis_http_post_message_body}'"
                )
            elif test_data.variation_number == 2:
                if test_data.esrp_to_lis_subscribe_message_body == "":
                    assert (
                        jws_data.text == test_data.esrp_to_lis_subscribe_message_body
                    ), (
                        f"FAILED -> 'text' field is not empty as ESRP to LIS SUBSCRIBE body.\n"
                        f"'text' field: {jws_data.text}\n"
                        f"subscribe body: {test_data.esrp_to_lis_subscribe_message_body}"
                    )

                elif test_data.esrp_to_lis_subscribe_message_body:
                    error_msg = f"FAILED -> 'text' field of '{LOCATION_QUERY_LOG}' for Variation {test_data.variation_number} contains not the same value as ESRP to LIS SUBSCRIBE body.\n"
                    f"'text' field: {jws_data.text}\n"
                    f"subscribe body: {test_data.esrp_to_lis_subscribe_message_body}"

                    if is_valid_xml(test_data.esrp_to_lis_subscribe_message_body):
                        assert is_xml_equal(
                            jws_data.text, test_data.esrp_to_lis_subscribe_message_body
                        ), error_msg
                    else:
                        assert (
                            jws_data.text
                            == test_data.esrp_to_lis_subscribe_message_body
                        ), error_msg

        if event_type == LOCATION_RESPONSE_LOG:
            if test_data.variation_number == 1:
                assert is_xml_equal(
                    jws_data.text, test_data.lis_to_esrp_response_message_body
                ), (
                    f"FAILED -> 'text' field of '{LOCATION_RESPONSE_LOG}' for Variation {test_data.variation_number} contains not the same value as LIS to ESRP HTTP response 200 Body.\n"
                    f"Actual: '{jws_data.text}'\n"
                    f"Expected: '{test_data.lis_to_esrp_response_message_body}'"
                )

            elif test_data.variation_number == 2:
                assert is_xml_equal(
                    jws_data.text, test_data.lis_to_esrp_notify_response_message_body
                ), (
                    f"FAILED -> 'text' field of '{LOCATION_RESPONSE_LOG}' for Variation {test_data.variation_number} contains not the same value as LIS to ESRP NOTIFY Body.\n"
                    f"Actual: '{jws_data.text}'\n"
                    f"Expected: '{test_data.lis_to_esrp_notify_response_message_body}'"
                )

            elif test_data.variation_number == 3:

                error_msg = (
                    f"FAILED -> 'text' field of '{LOCATION_RESPONSE_LOG}' for Variation {test_data.variation_number} contains not the same value as LIS to ESRP HTTP ERROR response Body.\n"
                    f"Actual: '{jws_data.text}'\n"
                    f"Expected: '{test_data.lis_to_esrp_response_message_body}'"
                )

                if jws_data.text and is_valid_xml(
                    test_data.lis_to_esrp_response_message_body
                ):
                    assert is_xml_equal(
                        jws_data.text, test_data.lis_to_esrp_response_message_body
                    ), error_msg
                else:
                    assert normalize_string_for_comparison(
                        jws_data.text
                    ) == normalize_string_for_comparison(
                        test_data.lis_to_esrp_response_message_body
                    ), error_msg

        return "PASSED"
    except AssertionError as e:
        return str(e)


def optional_attributes_validation(event_type, payload_data) -> str:
    """
    Validates optional attributes in an event payload.

    Performs checks on optional fields within the provided payload and
    validates their presence or correctness depending on expected rules.

    Args:
        event_type (str): Event type used for contextual assertion messages.
        payload_data: Payload data used for contextual assertion messages.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message string.
    """

    try:
        optional_fields = [
            "clientAssignedIdentifier",
            "agencyAgentId",
            "agencyPositionId",
            "extension",
        ]

        for optional_field_name in optional_fields:
            optional_field_value = payload_data.get(optional_field_name, None)
            if optional_field_value is not None:
                if optional_field_name == "ipAddressPort":
                    ip_address_value = payload_data.get("ipAddressPort", None)

                    if ip_address_value is not None:
                        assert validate_ip_port_combo(
                            ip_address_value
                        ) or is_valid_fqdn(
                            ip_address_value
                        ), f"FAILED -> Invalid IP:PORT or FQDN value for '{event_type}'. Received: '{ip_address_value}'"

                if optional_field_name == "extension":
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, dict
                        )
                    ) == "PASSED", f" {result} Event: '{event_type}', field name: '{optional_field_name}'"
                else:

                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", f"FAILED -> {result} Event: '{event_type}', field name: '{optional_field_name}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def assert_required_payload_fields(
    event_type: str, payload_data: dict, fields: tuple[str, ...], test_data
) -> str:
    try:
        for field in fields:
            if field not in payload_data:
                return f"❌ FAILED -> No '{field}' object found in {event_type} payload data."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_query_id_response_id_equality(test_data):
    """
    Validate equality of 'queryId' and 'responseId' for LocationQueryLogEvent and LocationResponseLogEvent
    """
    location_query_jws = EasyJSON(test_data.esrp_to_logger_post_location_query_jws)
    location_response_jws = EasyJSON(
        test_data.esrp_to_logger_post_location_response_jws
    )
    try:
        assert location_query_jws.queryId == location_response_jws.responseId, (
            f"FAILED -> 'queryId' and 'responseId' are not equal.\n"
            f"LocationQueryLogEvent 'queryId': {location_query_jws.queryId}\n"
            f"LocationResponseLogEvent 'responseId': {location_response_jws.responseId}\n"
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def _extract_value(s):
    return s.partition("<")[2].partition(">")[0] if "<" in s and ">" in s else s
