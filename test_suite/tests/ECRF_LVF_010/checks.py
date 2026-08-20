from checks.general.checks import is_data_present
from checks.http.checks import is_type

from services.aux_services.json_services import (
    is_timestamp,
    is_valid_fqdn,
    EasyJSON,
    is_valid_json,
    is_empty_json,
)
from tests.ECRF_LVF_010.constants import VALID_POSTURE_VALUES, DIRECTIONS, NORMAL, DOWN


def validate_sip_service_state_event_notification_package(test_data):
    try:
        assert (
            test_data.stimulus_message
        ), "NOT RUN -> No SIP SUBSCRIBE stimulus message found."

        assert (
            test_data.ecrf_to_esrp_initial_notify_state_message
        ), "FAILED -> No ECRF-LVF to ESRP initial state SIP NOTIFY message found."

        assert (
            test_data.ecrf_to_esrp_initial_notify_json
        ), "FAILED -> No ECRF-LVF to ESRP initial SIP NOTIFY JSON body found."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def precondition_check(test_data, only_members_check=False):
    try:

        service_state_pre_check = validate_sip_service_state_event_notification_package(
            test_data
        )
        assert service_state_pre_check == "PASSED", service_state_pre_check

        assert (
            test_data.ecrf_to_logger_http_post_message
        ), "FAILED -> No ECRF-LVF to LOGGER POST ServiceStateChangeLogEvent message found."

        assert (
            test_data.ecrf_to_logger_post_data
        ), "FAILED -> No ECRF-LVF to LOGGER JWS data found."

        if not only_members_check:

            assert (
                test_data.ecrf_to_esrp_notify_second_state_message
            ), "FAILED -> No ECRF-LVF to ESRP changed state Notify message found."

            assert (
                test_data.ecrf_to_esrp_second_notify_json
            ), "FAILED -> No ECRF-LVF to ESRP changed state Notify JSON body found."

            assert not is_empty_json(
                test_data.ecrf_to_esrp_second_notify_json
            ), f"FAILED -> ECRF-LVF to ESRP notify with changed states message body is empty JSON.\nActual: {test_data.ecrf_to_esrp_second_notify_json}"

            assert is_valid_json(
                test_data.ecrf_to_esrp_second_notify_json
            ), f"FAILED -> ECRF-LVF to ESRP notify with changed states message body contains incorrect structure.\nActual: {test_data.ecrf_to_esrp_second_notify_json}"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_service_state(
    test_data,
):
    """
    Validates serviceState values between notifications and ECRF-LVF to LOGGER event .

    Args:
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    try:

        pre_check = precondition_check(test_data)
        assert pre_check == "PASSED", pre_check

        initial_notify_data = EasyJSON(test_data.ecrf_to_esrp_initial_notify_json)
        initial_state = initial_notify_data.serviceState.state

        log_event_data = EasyJSON(test_data.ecrf_to_logger_post_data)
        log_event_state = log_event_data.newState

        final_notify_data = EasyJSON(test_data.ecrf_to_esrp_second_notify_json)
        final_state = final_notify_data.serviceState.state

        assert (
            log_event_state is not None
        ), "FAILED -> ECRF-LVF log event 'newState' member not found."

        assert log_event_state != initial_state, (
            "FAILED -> ECRF-LVF log event contains the same 'state' as initial.\n"
            f"Initial: '{initial_state}', Actual: '{log_event_state}'"
        )

        assert (
            log_event_state == final_state
        ), f"FAILED -> ECRF-LVF to ESRP 'state' value is not the same. Actual: '{final_state}', Expected: '{log_event_state}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_event_members(test_data):
    """
    Validates ECRF-LVF to LOGGER event members.

    Args:
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    required_fields = (
        "logEventType",
        "timestamp",
        "elementId",
        "agencyId",
        "direction",
        "newState",
        "affectedServiceIdentifier",
    )

    try:

        pre_check = precondition_check(test_data, only_members_check=True)
        assert pre_check == "PASSED", pre_check

        # Required Fields Check
        assert_required_payload_fields(
            test_data.ecrf_to_logger_post_data, required_fields
        )

        jws_data = EasyJSON(test_data.ecrf_to_logger_post_data)

        assert (
            jws_data
        ), f"FAILED -> Can't extract JWS payload data. Actual: {test_data.ecrf_to_logger_post_data}"

        # timestamp check
        assert is_timestamp(
            jws_data.timestamp
        ), f"FAILED -> Wrong timestamp format for ServiceStateChangeLogEvent. Actual: {jws_data.timestamp}"

        # elementId check
        assert is_valid_fqdn(
            jws_data.elementId
        ), f"FAILED -> 'elementId' in JWS should be a valid FQDN format. Actual: '{jws_data.elementId}'"

        assert jws_data.elementId == test_data.ecrf_fqdn, (
            f"FAILED -> 'elementId' value in JWS should be FQDN of ECRF_LVF.\n"
            f"Actual: '{jws_data.elementId}', Expected: '{test_data.ecrf_fqdn}'"
        )

        # agencyId check
        assert is_valid_fqdn(
            jws_data.agencyId
        ), f"FAILED -> 'agencyId' in JWS should be a valid FQDN format. Actual: '{jws_data.agencyId}'"

        # direction check
        assert (
            jws_data.direction.lower() in DIRECTIONS
        ), f"FAILED -> 'direction' value in JWS should be one of {DIRECTIONS}. Actual: '{jws_data.direction}'"

        # newState check
        if test_data.is_variant_one:
            assert (
                jws_data.newState == NORMAL
            ), f"FAILED -> 'newState' in JWS should be '{NORMAL}'. Actual: '{jws_data.newState}'"
        else:
            assert (
                jws_data.newState == DOWN
            ), f"FAILED -> 'newState' in JWS should be '{DOWN}'. Actual: '{jws_data.newState}'"

        # affectedServiceIdentifier check
        assert is_valid_fqdn(
            jws_data.affectedServiceIdentifier
        ), f"FAILED -> 'affectedServiceIdentifier' in JWS should be a valid FQDN format. Actual: '{jws_data.affectedServiceIdentifier}'"

        assert jws_data.affectedServiceIdentifier == test_data.ecrf_fqdn, (
            f"FAILED -> 'affectedServiceIdentifier' value in JWS should be FQDN of ECRF_LVF.\n"
            f"Actual: '{jws_data.affectedServiceIdentifier}', Expected: '{test_data.ecrf_fqdn}'"
        )

        # Optional Fields Check
        optional_fields_check = optional_attributes_validation(
            test_data.ecrf_to_logger_post_data, test_data, jws_data
        )
        assert optional_fields_check == "PASSED", optional_fields_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_security_posture(test_data) -> str:
    """
    Validates Security Posture value between ECRF-LVF to LOGGER event and notification to ESRP.

    Args:
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """
    try:
        pre_check = precondition_check(test_data)
        assert pre_check == "PASSED", pre_check

        initial_notify_data = EasyJSON(test_data.ecrf_to_esrp_initial_notify_json)
        initial_posture = initial_notify_data.securityPosture.posture

        log_event_data = EasyJSON(test_data.ecrf_to_logger_post_data)
        log_event_security_posture = log_event_data.newSecurityPosture

        final_notify_data = EasyJSON(test_data.ecrf_to_esrp_second_notify_json)
        final_security_posture = final_notify_data.securityPosture.posture

        assert initial_posture != log_event_security_posture, (
            f"FAILED -> Log Event contains the same security posture value as in initial notify message.\n"
            f"Initial: '{initial_posture}', Actual: '{log_event_security_posture}'"
        )

        assert log_event_security_posture == final_security_posture, (
            f"FAILED -> ECRF-LVF to ESRP security posture value is not the same as in log event.\n"
            f"Actual: '{final_security_posture}', Expected: '{log_event_security_posture}'"
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def optional_attributes_validation(payload_data, test_data, jws_data) -> str:
    """
    Validates optional attributes in an event payload.

    Performs checks on optional fields within the provided payload and
    validates their presence or correctness depending on expected rules.

    Args:
        payload_data: jws payload data.
        test_data: Instance of TestData containing test data for the test case.
        jws_data: Instance of TestData containing JWS data for the test case.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message string.
    """

    try:
        optional_fields = [
            "newSecurityPosture",
            "clientAssignedIdentifier",
            "agencyAgentId",
            "agencyPositionId",
            "extension",
        ]

        for optional_field_name in optional_fields:
            optional_field_value = payload_data.get(optional_field_name, None)
            if optional_field_value is not None:
                if optional_field_name == "newSecurityPosture":
                    assert optional_field_value in VALID_POSTURE_VALUES, (
                        "FAILED -> 'newSecurityPosture' value is not in the valid labels list.\n"
                        f"Actual value: '{optional_field_value}', Expected one of: '{VALID_POSTURE_VALUES}'"
                    )
                elif optional_field_name == "clientAssignedIdentifier":
                    assert jws_data.affectedServiceIdentifier == test_data.ecrf_fqdn, (
                        f"FAILED -> 'affectedServiceIdentifier' value in JWS should be FQDN of ECRF_LVF.\n"
                        f"Actual: '{jws_data.affectedServiceIdentifier}', Expected: '{test_data.ecrf_fqdn}'"
                    )

                else:
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", result

        return "PASSED"
    except AssertionError as e:
        return str(e)


def assert_required_payload_fields(payload_data: dict, fields: tuple[str, ...]) -> None:
    for field in fields:
        value = payload_data.get(field)
        error_msg = f"FAILED -> No '{field}' object found in payload data."
        msg = is_data_present(value, error_msg)
        assert msg == "PASSED", msg
