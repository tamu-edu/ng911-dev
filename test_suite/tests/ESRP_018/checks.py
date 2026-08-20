from checks.general.checks import is_data_present
from checks.http.checks import is_type

from services.aux_services.json_services import (
    is_timestamp,
    is_valid_fqdn,
    EasyJSON,
)
from tests.ESRP_018.constants import (
    VALID_POSTURE_VALUES,
    DIRECTIONS,
    NORMAL,
    DOWN,
    GREEN,
    SERVICE_STATE_VALUES,
    ORANGE,
)


def precondition_check(test_data):
    try:
        assert (
            test_data.stimulus_message
        ), "NOT RUN -> No SIP SUBSCRIBE BCF to ESRP stimulus message found."

        assert (
            test_data.esrp_to_bcf_initial_notify_state_message
        ), "FAILED -> No ESRP to BCF initial state SIP NOTIFY message found."

        assert (
            test_data.esrp_to_bcf_initial_notify_json
        ), "FAILED -> No ESRP to BCF initial SIP NOTIFY JSON body found."

        assert (
            test_data.esrp_to_logger_http_post_message
        ), "FAILED -> No ESRP to LOGGER POST ServiceStateChangeLogEvent message found. Please check 'certificate_key' configuration value if signed JWS."

        assert (
            test_data.esrp_to_logger_post_data
        ), "FAILED -> No ESRP to LOGGER JWS data found."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_service_state(
    test_data,
):
    """
    Validates serviceState\newState values between notifications of ESRP -> BCF and ESRP -> LOGGER .

    Args:
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    try:
        initial_state = None
        log_event_state = None

        initial_notify_data = EasyJSON(test_data.esrp_to_bcf_initial_notify_json)
        if initial_notify_data:
            initial_state = initial_notify_data.serviceState.state

        log_event_data = EasyJSON(test_data.esrp_to_logger_post_data)
        if log_event_data:
            log_event_state = log_event_data.newState

        assert (
            log_event_state is not None
        ), "FAILED -> ESRP log event 'newState' member not found."

        assert initial_state == NORMAL, (
            "FAILED -> Wrong initial ESRP notify 'state' value.\n"
            f"Actual: '{initial_state}', Expected: '{NORMAL}'"
        )
        if test_data.is_variant_one:
            assert log_event_state == NORMAL, (
                "FAILED -> Wrong ESRP log event value of 'newState'.\n"
                f"Actual: '{log_event_state}', Expected: '{NORMAL}'"
            )
        else:
            assert log_event_state == DOWN, (
                "FAILED -> Wrong ESRP log event value of 'newState'.\n"
                f"Actual: '{log_event_state}', Expected: '{DOWN}'"
            )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_event_members(test_data):
    """
    Validates ESRP to LOGGER event members.

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

    if test_data.is_variant_one:
        required_fields = required_fields + ("newSecurityPosture",)

    try:

        pre_check = precondition_check(test_data)
        assert pre_check == "PASSED", pre_check

        # Required Fields Check
        assert_required_payload_fields(
            test_data.esrp_to_logger_post_data, required_fields
        )

        jws_data = EasyJSON(test_data.esrp_to_logger_post_data)

        assert (
            jws_data
        ), f"FAILED -> Can't extract JWS payload data. Actual: {test_data.esrp_to_logger_post_data}"

        # timestamp check
        assert is_timestamp(
            jws_data.timestamp
        ), f"FAILED -> Wrong timestamp format for ServiceStateChangeLogEvent. Actual: {jws_data.timestamp}"

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

        # direction check
        assert (
            jws_data.direction.lower() in DIRECTIONS
        ), f"FAILED -> 'direction' value in JWS should be one of {DIRECTIONS}. Actual: '{jws_data.direction}'"

        # newState check
        if test_data.is_variant_one:
            assert (
                jws_data.newState in SERVICE_STATE_VALUES
            ), f"FAILED -> 'newState' in JWS should be one of {SERVICE_STATE_VALUES}'.\nActual: '{jws_data.newState}'"
        else:
            assert jws_data.newState == DOWN, (
                f"FAILED -> Log Event newState value should be '{DOWN}'.\n"
                f"Actual: '{jws_data.newState}'"
            )

        # newSecurityPosture check
        if test_data.is_variant_one:
            assert jws_data.newSecurityPosture == ORANGE, (
                f"FAILED -> Log Event newSecurityPosture value should be '{ORANGE}'.\n"
                f"Actual: '{jws_data.newSecurityPosture}'"
            )

        # affectedServiceIdentifier check
        assert is_valid_fqdn(
            jws_data.affectedServiceIdentifier
        ), f"FAILED -> 'affectedServiceIdentifier' in JWS should be a valid FQDN format. Actual: '{jws_data.affectedServiceIdentifier}'"

        assert jws_data.affectedServiceIdentifier == test_data.esrp_fqdn, (
            f"FAILED -> 'affectedServiceIdentifier' value in JWS should be FQDN of ESRP.\n"
            f"Actual: '{jws_data.affectedServiceIdentifier}', Expected: '{test_data.esrp_fqdn}'"
        )

        # Optional Fields Check
        optional_fields_check = optional_attributes_validation(
            test_data.esrp_to_logger_post_data, test_data, jws_data
        )
        assert optional_fields_check == "PASSED", optional_fields_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_security_posture(test_data) -> str:
    """
    Validates Security Posture value between ESRP -> BCF and ESRP -> LOGGER.

    Args:
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """
    try:
        initial_posture = None
        log_event_security_posture = None

        initial_notify_data = EasyJSON(test_data.esrp_to_bcf_initial_notify_json)
        if initial_notify_data:
            initial_posture = initial_notify_data.securityPosture.posture

        log_event_data = EasyJSON(test_data.esrp_to_logger_post_data)
        if log_event_data:
            log_event_security_posture = log_event_data.newSecurityPosture

        assert initial_posture == GREEN, (
            f"FAILED -> Wrong initial ESRP notify 'posture' value.\n"
            f"Actual: '{initial_posture}', Expected: '{GREEN}'"
        )

        if test_data.is_variant_one:

            assert initial_posture != log_event_security_posture, (
                f"FAILED -> Log Event contains the same security posture value as in initial notify message.\n"
                f"\nInitial: '{initial_posture}'\nActual: '{log_event_security_posture}'\nExpected: '{ORANGE}'"
            )

            assert log_event_security_posture == ORANGE, (
                f"FAILED -> Wrong Log Event security posture value.\n"
                f"Actual: '{log_event_security_posture}', Expected: '{ORANGE}'"
            )

        else:
            assert log_event_security_posture in VALID_POSTURE_VALUES, (
                f"FAILED -> Log Event contains wrong security posture value.\n"
                f"Actual: '{log_event_security_posture}', Expected one of: '{VALID_POSTURE_VALUES}'"
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
