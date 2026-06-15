from checks.general.checks import is_data_present
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
    is_jws,
    is_timestamp,
)
from services.aux_services.sip_msg_body_services import (
    is_valid_sip_call_id,
)
from tests.CHFE_010.constants import TIMESTAMP_THRESHOLD


def validate_logging_call_signaling_message(
    stimulus_message,
    raw_conference_invite_message,
    post_to_logger_messages,
    json_data_from_message,
    key_found,
    payload_data,
    stimulus_timestamp,
):
    """
    @param stimulus_message: filtered stimulus message
    @param raw_conference_invite_message: raw conference invite message
    @param post_to_logger_messages: POST to logger messages
    @param json_data_from_message: extracted JSON data from POST to logger message
    @param key_found: is certificate key found
    @param payload_data: JWS payload data
    @param stimulus_timestamp: timestamp of the stimulus message

    @return: test check result 'PASSED' result or "FAILED" with error description
    """

    try:
        assert stimulus_message, "NOT RUN -> No stimulus message found."

        assert (
            raw_conference_invite_message
        ), "FAILED -> Can't extract raw conference invite message."

        assert (
            post_to_logger_messages
        ), "FAILED -> CHFE to LOGGER POST message not found."

        assert (
            json_data_from_message
        ), f"FAILED -> Can't extract JSON data from POST to LOGGER request. Actual data: {json_data_from_message}"

        assert is_jws(
            json_data_from_message
        ), "FAILED -> Received wrong JWS payload format."

        assert key_found, "FAILED -> JWS is signed and Certificate Key was not found."

        assert stimulus_timestamp, "FAILED -> No stimulus timestamp received."

        assert payload_data, "FAILED -> No JWS payload data found."

        assert isinstance(
            payload_data, dict
        ), f"FAILED - Invalid JWS payload object format. Actual: {payload_data} Expected: 'dict'"

        base_payload_data_validation = validate_payload_data(
            payload_data, stimulus_timestamp, raw_conference_invite_message
        )
        assert base_payload_data_validation == "PASSED", base_payload_data_validation

        optional_payload_data_validation = optional_attributes_validation(payload_data)
        assert (
            optional_payload_data_validation == "PASSED"
        ), optional_payload_data_validation

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_payload_data(
    payload_data: dict, stimulus_timestamp: float, raw_conference_invite_message: str
) -> str:
    """
    Base JWS payload data validation

    @param payload_data: JWS payload data
    @param stimulus_timestamp: timestamp of the stimulus message
    @param raw_conference_invite_message: raw conference invite message
    """

    log_event_type = payload_data.get("logEventType", None)
    timestamp = payload_data.get("timestamp", None)
    element_id = payload_data.get("elementId", None)
    agency_id = payload_data.get("agencyId", None)
    call_id = payload_data.get("callId", None)
    incident_id = payload_data.get("incidentId", None)
    call_id_sip = payload_data.get("callIdSip", None)
    direction = payload_data.get("direction", None)
    text_data = payload_data.get("text", None)

    try:
        # logEventType check
        log_event_type_object_check = is_data_present(
            log_event_type, "FAILED -> No 'logEventType' object found in payload data."
        )
        assert log_event_type_object_check == "PASSED", log_event_type_object_check
        assert (
            log_event_type == "CallSignalingMessageLogEvent"
        ), f"FAILED -> 'logEventType' value error. Actual: {log_event_type}, Expected: 'CallSignalingMessageLogEvent'"

        # timestamp check
        timestamp_object_check = is_data_present(
            timestamp, "FAILED -> No 'timestamp' object found in payload data."
        )
        assert timestamp_object_check == "PASSED", timestamp_object_check
        assert is_timestamp(
            timestamp
        ), f"FAILED -> Wrong timestamp format. Actual: {timestamp}"
        assert (
            abs(iso_to_timestamp(timestamp) - stimulus_timestamp) <= TIMESTAMP_THRESHOLD
        ), (
            f"FAILED - The time between the stimulus invite message and the payload timestamp is greater then 1 sec:\n"
            f"{float_timestamp_to_iso(stimulus_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(timestamp))}"
        )

        # elementId check
        element_id_object_check = is_data_present(
            element_id, "FAILED -> No 'elementId' object found in payload data."
        )
        assert element_id_object_check == "PASSED", element_id_object_check
        assert is_valid_fqdn(
            element_id
        ), f"FAILED - 'elementId' in JWS should be a valid FQDN format. Actual: '{element_id}'"

        # agencyId check
        agency_id_object_check = is_data_present(
            agency_id, "FAILED -> No 'agencyId' object found in payload data."
        )
        assert agency_id_object_check == "PASSED", agency_id_object_check
        assert is_valid_fqdn(
            agency_id
        ), f"FAILED - 'agencyId' in JWS should be a valid FQDN format. Actual: '{agency_id}'"

        # callId check
        call_id_object_check = is_data_present(
            call_id, "FAILED -> No 'callId' object found in payload data."
        )
        assert call_id_object_check == "PASSED", call_id_object_check

        assert (
            result := test_emergency_call_id_urn(call_id)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_emergency_call_id_string_id(call_id)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_emergency_call_id_fqdn(call_id)
        ) == "PASSED", f"FAILED -> {result}"

        # incidentId check
        incident_id_object_check = is_data_present(
            incident_id, "FAILED -> No 'incidentId' object found in payload data."
        )
        assert incident_id_object_check == "PASSED", incident_id_object_check

        assert (
            result := test_incident_tracking_id_urn(incident_id)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_incident_tracking_id_string_id(incident_id)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_incident_tracking_id_fqdn(incident_id)
        ) == "PASSED", f"FAILED -> {result}"

        # callIdSip check
        call_id_object_check = is_data_present(
            call_id_sip, "FAILED -> No 'callIdSip' object found in payload data."
        )
        assert call_id_object_check == "PASSED", call_id_object_check
        assert is_valid_sip_call_id(
            call_id_sip
        ), f"FAILED - 'callIdSip' in JWS should be a valid SIP Call ID. Actual: '{call_id_sip}'"

        # direction check
        direction_object_check = is_data_present(
            direction, "FAILED -> No 'direction' object found in payload data."
        )
        assert direction_object_check == "PASSED", direction_object_check

        assert (
            direction.lower() == "outgoing"
        ), f"FAILED - 'direction' value in JWS should be 'outgoing'. Actual: '{direction}'"

        # text field check
        text_object_check = is_data_present(
            text_data, "FAILED -> No 'text' object found in payload data."
        )
        assert text_object_check == "PASSED", text_object_check

        assert raw_conference_invite_message == text_data, (
            f"FAILED -> Invite message from the CHFE to the CONFERENCE and JWS text value are not the same:\n"
            "##### INVITE MESSAGE #####\n"
            f"{raw_conference_invite_message}\n"
            "##### TEXT FIELD VALUE INVITE MESSAGE #####\n"
            f"{text_data}"
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def optional_attributes_validation(payload_data: dict) -> str:
    """
    Optional payload attributes validation
    :param payload_data: payload data
    """
    try:
        optional_fields = [
            "protocol",
            "ipAddressPort",
            "clientAssignedIdentifier",
            "agencyAgentId",
            "agencyPositionId",
            "extension",
        ]

        for optional_field_name in optional_fields:
            optional_field_value = payload_data.get(optional_field_name, None)
            if optional_field_value or optional_field_value == "":
                if optional_field_name == "protocol":
                    protocol_value = payload_data.get("protocol", None).lower()
                    assert (
                        protocol_value == "sip"
                    ), f"FAILED -> 'protocol' value inside of JWS should be 'sip'. Actual: '{protocol_value}'"

                elif optional_field_name == "ipAddressPort":
                    ip_address_value = payload_data.get("ipAddressPort", None)

                    if ip_address_value is not None:
                        assert validate_ip_port_combo(
                            ip_address_value
                        ) or is_valid_fqdn(
                            ip_address_value
                        ), f"FAILED - Invalid IP:PORT or FQDN value. Received: '{ip_address_value}'"
                else:
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", f"FAILED -> {result}"

        return "PASSED"
    except AssertionError as e:
        return str(e)
