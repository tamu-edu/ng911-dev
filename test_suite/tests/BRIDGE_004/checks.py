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
    compare_sip_message_content,
    is_timestamp,
)
from services.aux_services.sip_msg_body_services import is_valid_sip_call_id
from tests.BRIDGE_004.constants import TIMESTAMP_THRESHOLD, STANDARD_PRIMARY_CALL_TYPE


def validate_common_attributes(
    payload_data: dict,
    init_timestamp: float,
    call_id: str,
    is_direction_incoming_wrong_value: bool,
) -> str:
    """
    Validated attributes and values which are common for all log event types.
    @param payload_data: JSW payload data represented as JSON object
    @param init_timestamp: timestamp value from SIP Test System
    @param call_id: 'callId' value from SIP Test System
    @param is_direction_incoming_wrong_value: does signaling message contain 'incoming' direction value
    @return: 'PASSED' result or "FAILED" with error description
    """
    try:
        assert call_id, "NOT RUN - INVITE/BYE request 'CallId' is not found."
        assert init_timestamp, "NOT RUN - INVITE/BYE request is not found."

        if not payload_data and is_direction_incoming_wrong_value:
            return "FAILED -> 'direction' in JWS should be a have value 'incoming'"

        assert payload_data, "FAILED - No JWS found in the response."
        assert isinstance(payload_data, dict), "FAILED - Invalid JWS payload format."

        fe_timestamp = payload_data.get("timestamp", None)

        assert fe_timestamp, "FAILED - FE request is not found."

        assert is_timestamp(
            fe_timestamp
        ), f"FAILED - Timestamp value is not valid. Found: {fe_timestamp}"

        assert (
            abs(iso_to_timestamp(fe_timestamp) - init_timestamp) < TIMESTAMP_THRESHOLD
        ), (
            f"FAILED - Duration between requests cannot be more than 1 sec.\n"
            f"SIP INVITE timestamp: {float_timestamp_to_iso(init_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(fe_timestamp))}"
        )
        assert is_valid_fqdn(
            payload_data.get("elementId", "")
        ), "FAILED - 'elementId' in JWS should be a valid FQDN format."
        assert is_valid_fqdn(
            payload_data.get("agencyId", "")
        ), "FAILED - 'agencyId' in JWS should be a valid FQDN format."

        call_sip_id = payload_data.get("callIdSip", None)

        assert (
            payload_data.get("callIdSip", None) == call_id
        ), f"FAILED - 'callId' in JWS is not the same as in initial request. Actual: {call_sip_id}, Expected: {call_id}"

        # incidentId validation
        incident_id = payload_data.get("incidentId", None)

        assert incident_id, "FAILED - 'incidentId' is not found in JWS."
        assert (
            result := test_incident_tracking_id_urn(incident_id)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_incident_tracking_id_string_id(incident_id)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_incident_tracking_id_fqdn(incident_id)
        ) == "PASSED", f"FAILED -> {result}"

        # callId validation
        call_id_payload = payload_data.get("callId", None)

        assert call_id_payload, "FAILED - 'callId' is not found in JWS."

        assert (
            result := test_emergency_call_id_urn(call_id_payload)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_emergency_call_id_string_id(call_id_payload)
        ) == "PASSED", f"FAILED -> {result}"

        assert (
            result := test_emergency_call_id_fqdn(call_id_payload)
        ) == "PASSED", f"FAILED -> {result}"

        assert is_valid_sip_call_id(
            payload_data.get("callIdSip", "")
        ), "FAILED - 'callIdSip' in JWS should be a valid SIP Call ID."

        direction_value = payload_data.get("direction", "")
        assert (
            direction_value and payload_data.get("direction", "").lower() == "incoming"
        ), f"FAILED - 'direction' in JWS should be a have value 'incoming'. Actual: '{direction_value}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_logging_call_status(
    jws_data: dict,
    init_timestamp: float,
    call_id: str,
    is_direction_incoming_wrong_value: bool,
):
    """
    Validates data inside of CallStartLogEvent and CallEndLogEvent.
    @param jws_data: JSW data represented as JSON object
    @param init_timestamp: timestamp value from SIP Test System
    @param call_id: 'callId' value from SIP Test System
    @param is_direction_incoming_wrong_value: does signaling message contain 'incoming' direction value
    @return: test check result 'PASSED' result or "FAILED" with error description
    """
    try:
        common_validation_result = validate_common_attributes(
            jws_data, init_timestamp, call_id, is_direction_incoming_wrong_value
        )

        assert common_validation_result == "PASSED", common_validation_result

        assert validate_optional_fields(jws_data) == "PASSED", validate_optional_fields(
            jws_data
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_logging_call_signaling_message(
    jws_data, init_timestamp, text, call_id, is_direction_incoming_wrong_value, is_text
):
    """
    @param jws_data: JSW data represented as JSON object
    @param init_timestamp: timestamp value from SIP Test System
    @param text: 'text' value from SIP Test System
    @param call_id: 'callId' value from SIP Test System
    @param is_direction_incoming_wrong_value: does signaling message contain 'incoming' direction value
    @param is_text: True or False for 'text' key or value existence
    @return: test check result 'PASSED' result or "FAILED" with error description
    """
    try:
        common_validation_result = validate_common_attributes(
            jws_data, init_timestamp, call_id, is_direction_incoming_wrong_value
        )
        if not jws_data and not is_text:
            return "FAILED -> 'text' object in JWS was not found or doesn't contain valid string data."

        assert common_validation_result == "PASSED", common_validation_result

        assert text, "NOT RUN -> No text message sent from SIP Test System being found."
        jws_data_text = jws_data.get("text", "")
        assert jws_data_text, "FAILED -> No 'text' in JWS data."
        assert (
            result := compare_sip_message_content(text.lower(), jws_data_text.lower())
        ) == "PASSED", f"FAILED -> {result}"

        # 'protocol' is optional. But if present than is should be 'sip'.
        protocol_value = jws_data.get("protocol", None)
        if protocol_value:
            assert (
                protocol_value.lower() == "sip"
            ), "FAILED - 'protocol' value inside of JWS should be 'sip'."

        assert validate_optional_fields(jws_data) == "PASSED", validate_optional_fields(
            jws_data
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_optional_fields(jws_data: dict):
    """
    Validates optional fields in JWS data
    @param jws_data: JSW data represented as JSON object
    """

    try:
        # OPTIONAL CHECKS
        optional_fields = [
            "standardPrimaryCallType",
            "standardSecondaryCallType",
            "localCallType",
            "localUse",
            "clientAssignedIdentifier",
            "agencyPositionId",
            "agencyAgentId",
            "extension",
            "ipAddressPort",
        ]
        for optional_field_name in optional_fields:
            optional_field_value = jws_data.get(optional_field_name, None)
            if optional_field_name == "ipAddressPort" and optional_field_value:
                assert validate_ip_port_combo(
                    optional_field_value
                ), f"FAILED - Invalid IP:PORT value. Received: '{optional_field_value}'"

            elif optional_field_value:
                assert (
                    result := is_type(optional_field_value, optional_field_name, str)
                ) == "PASSED", f"{result}"
                if optional_field_name in [
                    "standardPrimaryCallType",
                    "standardSecondaryCallType",
                ]:
                    assert (
                        optional_field_value in STANDARD_PRIMARY_CALL_TYPE
                    ), f"FAILED - Invalid value '{optional_field_value}' for '{optional_field_name}'."

        return "PASSED"

    except AssertionError as e:
        return str(e)
