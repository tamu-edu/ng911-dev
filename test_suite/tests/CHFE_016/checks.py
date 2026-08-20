from checks.general.checks import is_data_present, is_test_data_the_same
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
    iso_to_timestamp,
    float_timestamp_to_iso,
    is_timestamp,
    EasyJSON,
)
from services.aux_services.sip_msg_body_services import (
    is_valid_sip_call_id,
)
from tests.CHFE_016.constants import (
    TIMESTAMP_THRESHOLD,
    DIRECTIONS,
    REC_CALL_START,
    REC_CALL_END,
    STANDARD_CALL_TYPE,
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
            test_data.stimulus_timestamp
        ), "NOT RUN -> No stimulus message timestamp found."

        assert (
            test_data.stimulus_call_sip_id
        ), "NOT RUN -> No stimulus call sip id 'Call-ID' found."

        assert (
            test_data.stimulus_call_id
        ), "NOT RUN -> No stimulus call id 'Call-Info' found."

        assert (
            test_data.stimulus_incident_id
        ), "NOT RUN -> No stimulus incident id 'Call-Info' found."

        assert (
            test_data.rec_call_start_msg
        ), f"FAILED -> No POST to logger message for '{REC_CALL_START}' found."

        assert (
            test_data.rec_call_end_msg
        ), f"FAILED -> No POST to logger message for '{REC_CALL_END}' found."

        assert (
            test_data.rec_call_start_jws
        ), f"FAILED -> No JWS data found for '{REC_CALL_START}'. Please check 'certificate_key' configuration value."

        assert (
            test_data.rec_call_end_jws
        ), f"FAILED -> No JWS data found for '{REC_CALL_END}'. Please check 'certificate_key' configuration value."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_rec_call_start_log_events(test_data):
    event_type = "RecCallStartLogEvent"

    try:
        initial_data_check = precondition_validation(test_data)
        assert initial_data_check == "PASSED", initial_data_check

        rec_call_start_check = rec_call_event_validation(
            test_data, test_data.rec_call_start_jws, event_type
        )
        assert rec_call_start_check == "PASSED", rec_call_start_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_rec_call_end_log_events(test_data):
    event_type = "RecCallEndLogEvent"

    try:
        initial_data_check = precondition_validation(test_data)
        assert initial_data_check == "PASSED", initial_data_check

        rec_call_end_check = rec_call_event_validation(
            test_data, test_data.rec_call_end_jws, event_type
        )
        assert rec_call_end_check == "PASSED", rec_call_end_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def rec_call_event_validation(test_data, payload_data, event_type):
    """
    Validates RecCall LogEvent data.

    Args:
        test_data: Instance of TestData containing test data for the test case.
        payload_data: JSON object containing payload data for the test case.
        event_type: RecCallStartLogEvent or RecCallEndLogEvent type.

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
    )

    jws_data = None

    try:
        # Required Fields Check
        assert_required_payload_fields(event_type, payload_data, required_fields)

        if event_type == REC_CALL_START:
            jws_data = EasyJSON(test_data.rec_call_start_jws)
        elif event_type == REC_CALL_END:
            jws_data = EasyJSON(test_data.rec_call_end_jws)

        if not jws_data:
            return f"FAILED -> Failed to parse JWS payload of '{event_type}'."

        # Check RecLogEvent timestamp
        assert is_timestamp(
            jws_data.timestamp
        ), f"FAILED -> Wrong timestamp format for {event_type}. Actual: {jws_data.timestamp}"

        if event_type == REC_CALL_START:
            sip_timestamp = test_data.invite_to_logger_message_timestamp
        else:
            sip_timestamp = test_data.bye_to_logger_message_timestamp

        assert (
            abs(iso_to_timestamp(jws_data.timestamp) - sip_timestamp)
            <= TIMESTAMP_THRESHOLD
        ), (
            f"FAILED -> The time between the sip message and the {event_type} timestamp is greater then {TIMESTAMP_THRESHOLD} sec:\n"
            f"{event_type} {float_timestamp_to_iso(sip_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(jws_data.timestamp))}"
        )

        # elementId check
        assert is_valid_fqdn(
            jws_data.elementId
        ), f"FAILED -> 'elementId' in JWS should be a valid FQDN format. Actual: '{jws_data.elementId}'"

        assert jws_data.elementId == test_data.chfe_fqdn, (
            f"FAILED -> 'elementId' value in JWS should be FQDN of CHFE.\n"
            f"Actual: '{jws_data.elementId}', Expected: '{test_data.chfe_fqdn}'"
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
        error_msg = f"'{event_type}' 'callIdSip' value not the same as in CHFE to LOGGER Invite 'callIdSip'"
        equality_check = is_test_data_the_same(
            _extract_value(test_data.invite_to_logger_call_id_sip),
            jws_data.callIdSip,
            error_msg,
        )

        assert equality_check == "PASSED", equality_check
        assert is_valid_sip_call_id(
            jws_data.callIdSip
        ), f"FAILED - 'callIdSip' in '{event_type}' JWS should be a valid SIP Call ID. Actual: '{jws_data.callIdSip}'"

        # direction check
        assert (
            jws_data.direction.lower() in DIRECTIONS
        ), f"FAILED - 'direction' value in '{event_type}' JWS should be one of {DIRECTIONS}. Actual: '{jws_data.direction}'"

        # Check optional fields
        optional_fields = optional_attributes_validation(event_type, payload_data)
        assert optional_fields == "PASSED", optional_fields

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
            "standardPrimaryCallType",
            "standardSecondaryCallType",
            "localCallType",
            "localUse",
            "ipAddressPort",
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

                if optional_field_name in [
                    "standardPrimaryCallType",
                    "standardSecondaryCallType",
                ]:
                    assert optional_field_value in STANDARD_CALL_TYPE, (
                        f"FAILED -> '{optional_field_name}' value is not in allowed list. Actual: '{optional_field_value}'\n"
                        f"Expected one of : {STANDARD_CALL_TYPE}"
                    )

                if optional_field_name in ["localUse", "extension"]:
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
    event_type: str, payload_data: dict, fields: tuple[str, ...]
) -> None:
    for field in fields:
        value = payload_data.get(field)
        error_msg = f"FAILED -> No '{field}' object found in {event_type} payload data."
        msg = is_data_present(value, error_msg)
        assert msg == "PASSED", msg


def _extract_value(s):
    return s.partition("<")[2].partition(">")[0] if "<" in s and ">" in s else s
