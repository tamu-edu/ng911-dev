from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_urn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn,
)
from services.aux_services.json_services import (
    is_valid_fqdn,
    iso_to_timestamp,
    float_timestamp_to_iso,
)
from services.aux_services.sip_msg_body_services import is_valid_sip_call_id
from tests.ESRP_010.constants import TIMESTAMP_THRESHOLD, STANDARD_PRIMARY_CALL_TYPE


def validate_common_attributes(
    payload_data: dict, init_timestamp: float, call_id: str
) -> str:
    """
    Validated attributes and values which are common for all log event types.
    @param payload_data: JSW payload data represented as JSON object
    @param init_timestamp: timestamp value from SIP Test System
    @param call_id: 'callId' value from SIP Test System
    @return: 'PASSED' result or "FAILED" with error description
    """
    try:
        # TODO NOT IMPLEMENTED YET
        # assert call_id, \
        #     "STOP ITERATION - INVITE/BYE request 'CallId' is not found."
        # assert init_timestamp, \
        #     "STOP ITERATION - INVITE/BYE request is not found."

        assert payload_data, "FAILED - No JWS found in the response."
        assert isinstance(payload_data, dict), "FAILED - Invalid JWS payload format."

        fe_timestamp = payload_data.get("timestamp", None)

        assert fe_timestamp, "FAILED - FE request is not found."
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
        assert (
            payload_data.get("callIdSIP", None) == call_id
        ), "FAILED - 'callId' in JWS is not the same as in initial request."

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
            payload_data.get("callIdSIP", "")
        ), "FAILED - 'callIdSIP' in JWS should be a valid SIP Call ID."

        assert (
            payload_data.get("direction", "")
            and payload_data.get("direction", "").lower() == "incoming"
        ), "FAILED - 'direction' in JWS should be a have value 'incoming'."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_logging_call_status(jws_data: dict, init_timestamp: float, call_id: str):
    """
    Validates data inside of CallStartLogEvent and CallEndLogEvent.
    @param jws_data: JSW data represented as JSON object
    @param init_timestamp: timestamp value from SIP Test System
    @param call_id: 'callId' value from SIP Test System
    @return: test check result 'PASSED' result or "FAILED" with error description
    """
    try:
        common_validation_result = validate_common_attributes(
            jws_data, init_timestamp, call_id
        )

        assert common_validation_result == "PASSED", common_validation_result

        # OPTIONAL CHECKS
        optional_fields = [
            "standardPrimaryCallType",
            "standardSecondaryCallType",
            "localCallType",
            "localUse",
            "clientAssignedIdentifier",
            "extension",
        ]

        for optional_field_name in optional_fields:
            optional_field_value = jws_data.get(optional_field_name, None)
            if optional_field_value:
                assert (
                    result := is_type(optional_field_value, optional_field_name, str)
                ) == "PASSED", f"FAILED -> {result}"
                if optional_field_name in [
                    "standardPrimaryCallType",
                    "standardSecondaryCallType",
                ]:
                    assert (
                        optional_field_value in STANDARD_PRIMARY_CALL_TYPE
                    ), f"FAILED - Invalid value {optional_field_value} for {optional_field_name}."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_logging_call_signaling_message(jws_data, init_timestamp, text, call_id):
    """

    @param jws_data: JSW data represented as JSON object
    @param init_timestamp: timestamp value from SIP Test System
    @param text: 'text' value from SIP Test System
    @param call_id: 'callId' value from SIP Test System
    @return: test check result 'PASSED' result or "FAILED" with error description
    """
    try:
        common_validation_result = validate_common_attributes(
            jws_data, init_timestamp, call_id
        )

        assert common_validation_result == "PASSED", common_validation_result

        # TODO NOT IMPLEMENTED
        # assert text, \
        #     "STOP ITERATION - No text message sent from SIP Test System being found."
        assert (
            jws_data.get("text", None) and jws_data.get("text").lower() == text.lower()
        ), "FAILED - 'text' value inside of JWS should be the same as in initial SIP request."
        assert (
            jws_data.get("protocol", None) and jws_data.get("protocol").lower() == "sip"
        ), "FAILED - 'protocol' value inside of JWS should be 'sip'."

        return "PASSED"
    except AssertionError as e:
        return str(e)
