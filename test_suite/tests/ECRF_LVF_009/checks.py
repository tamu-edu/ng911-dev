import re

from checks.general.checks import is_data_present
from checks.http.checks import is_type
from services.aux_services.aux_services import validate_ip_port_combo

from services.aux_services.json_services import (
    is_timestamp,
    is_valid_fqdn,
    EasyJSON,
)
from services.aux_services.xml_services import is_xml_equal
from tests.ECRF_LVF_009.constants import RESPONSE_CODES


def precondition_check(test_data):
    try:
        assert test_data.stimulus_message, "NOT RUN -> No stimulus message found."
        assert (
            test_data.ecrf_to_logger_http_post_message
        ), "FAILED -> No ECRF-LVF to LOGGER POST 'LostResponseLogEvent' message found. If the JWS is signed, verify that the keys are correct."
        assert (
            test_data.ecrf_to_logger_post_jws
        ), "FAILED -> No ECRF-LVF to LOGGER 'LostResponseLogEvent' JWS data found."

        if test_data.variant_number in (
            1,
            2,
        ):
            assert (
                test_data.ecrf_to_esrp_response
            ), "FAILED -> No ECRF-LVF to ESRP response message found."
            assert (
                test_data.ecrf_to_esrp_body_xml
            ), "FAILED -> Can't extract ECRF-LVF to ESRP response XML body."

        if test_data.variant_number == 2:
            assert (
                test_data.ecrf_to_logger_second_http_post_message
            ), "FAILED -> No ECRF-LVF to LOGGER POST 'LostResponseLogEvent' message found after 'findServiceResponse' was sent to ESRP."
            assert (
                test_data.ecrf_to_logger_second_post_jws
            ), "FAILED -> No ECRF-LVF to LOGGER JWS data found after 'findServiceResponse' to ESRP."

        if test_data.variant_number in (
            2,
            3,
            4,
        ):
            assert (
                test_data.ecrf_to_ecfr_fwd_post_message
            ), "FAILED -> No ECRF-LVF to TS-ECRF-LVF forwarded message found."

        if test_data.variant_number in (
            2,
            3,
        ):
            assert (
                test_data.ecrf_to_ecfr_fwd_response_message
            ), "FAILED -> No TS-ECRF-LVF to ECRF-LVF 'findServiceResponse' response message found."
            assert (
                test_data.ecrf_to_ecrf_response_body_xml
            ), "FAILED -> Can't extract TS-ECRF-LVF to ECRF-LVF 'findServiceResponse' response XML body."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_ecrf_to_logger_event_members(test_data):
    try:

        pre_check = precondition_check(test_data)
        assert pre_check == "PASSED", pre_check

        members_check = validate_event_members(test_data)
        assert members_check == "PASSED", members_check

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
        "responseAdapter",
        "responseId",
    )

    if test_data.variant_number == 3:
        required_fields = required_fields + ("malformedResponse",)
    if test_data.variant_number in (
        3,
        4,
    ):
        required_fields = required_fields + ("responseStatus",)

    direction = ""
    jws_data_second_post = None

    try:
        jws_data = EasyJSON(test_data.ecrf_to_logger_post_jws)
        if test_data.variant_number == 2:
            jws_data_second_post = EasyJSON(test_data.ecrf_to_logger_second_post_jws)

        # Required Fields Check
        assert_required_payload_fields(
            test_data.ecrf_to_logger_post_jws, required_fields, test_data
        )
        if jws_data_second_post:
            assert_required_payload_fields(
                test_data.ecrf_to_logger_second_post_jws, required_fields, test_data
            )

        assert (
            jws_data
        ), f"FAILED -> Can't extract JWS payload data. Actual: {test_data.ecrf_to_logger_post_jws}"

        # timestamp check
        assert is_timestamp(
            jws_data.timestamp
        ), f"FAILED -> Wrong timestamp format for LostResponseLogEvent. Actual: {jws_data.timestamp}"

        # elementId check
        assert is_valid_fqdn(
            jws_data.elementId
        ), f"FAILED -> 'elementId' in JWS should be a valid FQDN format. Actual: '{jws_data.elementId}'"

        assert jws_data.elementId == test_data.ecrf_fqdn, (
            f"FAILED -> 'elementId' value in JWS should be FQDN of ECRF-LVF.\n"
            f"Actual: '{jws_data.elementId}', Expected: '{test_data.ecrf_fqdn}'"
        )

        # agencyId check
        assert is_valid_fqdn(
            jws_data.agencyId
        ), f"FAILED -> 'agencyId' in JWS should be a valid FQDN format. Actual: '{jws_data.agencyId}'"

        # direction check
        if test_data.variant_number == 1:
            direction = "outgoing"
        elif test_data.variant_number in (
            3,
            4,
        ):
            direction = "incoming"

        if test_data.variant_number in (
            1,
            3,
            4,
        ):
            assert (
                jws_data.direction.lower() == direction
            ), f"FAILED -> 'direction' value in JWS should be '{direction}'. Actual: '{jws_data.direction}'"

        if test_data.variant_number == 2:
            assert (
                jws_data.direction.lower() == "incoming"
            ), f"FAILED -> 'direction' value in JWS should be 'incoming' for TS-ECRF-LVF to ECRF-LVF logging event. Actual: '{jws_data.direction}'"

            assert (
                jws_data_second_post.direction.lower() == "outgoing"
            ), f"FAILED -> 'direction' value in JWS should be 'outgoing'. Actual: '{jws_data_second_post.direction}'"

        # responseAdapter check
        assert isinstance(
            jws_data.responseAdapter, str
        ), f"FAILED -> 'responseAdapter' value should be string. Actual: '{jws_data.responseAdapter}'"

        if test_data.variant_number == 1:
            assert is_xml_equal(
                jws_data.responseAdapter, test_data.ecrf_to_esrp_body_xml
            ), (
                f"FAILED -> 'responseAdapter' value should be the same as ECRF-LVF to ESRP XML body.\n"
                f"Actual:\n{jws_data.responseAdapter}\nExpected:\n{test_data.ecrf_to_esrp_body_xml}"
            )

        if test_data.variant_number == 2 and jws_data_second_post:
            assert is_xml_equal(
                jws_data.responseAdapter, test_data.ecrf_to_ecrf_response_body_xml
            ), (
                f"FAILED -> 'responseAdapter' value should be the same as TS-ECRF-LVF to ECRF-LVF response XML body.\n"
                f"Actual:\n{jws_data.responseAdapter}\nExpected:\n{test_data.ecrf_to_ecrf_response_body_xml}"
            )

            assert is_xml_equal(
                jws_data_second_post.responseAdapter, test_data.ecrf_to_esrp_body_xml
            ), (
                f"FAILED -> 'responseAdapter' value should be the same as ECRF-LVF to ESRP XML body.\n"
                f"Actual:\n{jws_data_second_post.responseAdapter}\nExpected:\n{test_data.ecrf_to_esrp_body_xml}"
            )

        if test_data.variant_number == 3:
            xml = "\n".join(
                line for line in jws_data.responseAdapter.splitlines() if line
            )
            assert xml == test_data.ecrf_to_ecrf_response_body_xml, (
                f"FAILED -> 'responseAdapter' value should be the same as TS-ECRF-LVF to ECRF-LVF response XML body.\n"
                f"Actual:\n{xml}\nExpected:\n{test_data.ecrf_to_ecrf_response_body_xml}"
            )

            # malformedResponse check
            assert isinstance(
                jws_data.malformedResponse, str
            ), f"FAILED -> 'malformedResponse' value should be string. Actual: '{jws_data.malformedResponse}'"

            xml = "\n".join(
                line for line in jws_data.malformedResponse.splitlines() if line
            )
            assert xml == test_data.ecrf_to_ecrf_response_body_xml, (
                f"FAILED -> 'malformedResponse' value should be the same as TS-ECRF-LVF to ECRF-LVF response XML body.\n"
                f"Actual:\n{xml}\nExpected:\n{test_data.ecrf_to_ecrf_response_body_xml}"
            )

        if test_data.variant_number == 4:
            assert jws_data.responseAdapter == "", (
                f"FAILED -> 'responseAdapter' value should be empty.\n"
                f"Actual:\n{jws_data.responseAdapter}\nExpected:\n''"
            )

        # responseId check
        response_id_check = is_type(jws_data.responseId, "responseId", str)
        assert response_id_check == "PASSED", response_id_check
        assert bool(
            re.match(r"^urn:emergency:uid:responseid:[^:].+$", jws_data.responseId)
        ), f"FAILED -> Wrong 'responseId' format. Actual: {jws_data.responseId}"

        # responseStatus check
        if test_data.variant_number in (
            3,
            4,
        ):
            assert (
                str(jws_data.responseStatus) in RESPONSE_CODES
            ), f"FAILED -> Invalid response status code. Actual: '{jws_data.responseStatus}'. Expected one of: {RESPONSE_CODES}"

        # Optional Fields Check
        optional_fields_check = optional_attributes_validation(
            test_data.ecrf_to_logger_post_jws
        )
        assert optional_fields_check == "PASSED", optional_fields_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def optional_attributes_validation(payload_data) -> str:
    """
    Validates optional attributes in an event payload.

    Performs checks on optional fields within the provided payload and
    validates their presence or correctness depending on expected rules.

    Args:
        payload_data: jws payload data.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message string.
    """

    try:
        optional_fields = [
            "clientAssignedIdentifier",
            "agencyAgentId",
            "agencyPositionId",
            "extension",
            "ipAddressPort",
        ]

        for optional_field_name in optional_fields:
            optional_field_value = payload_data.get(optional_field_name, None)
            if optional_field_name == "ipAddressPort":
                ip_address_value = payload_data.get(optional_field_name, None)

                if ip_address_value is not None:
                    assert validate_ip_port_combo(ip_address_value) or is_valid_fqdn(
                        ip_address_value
                    ), f"FAILED -> Invalid IP:PORT or FQDN value. Received: '{ip_address_value}'"
            else:
                if optional_field_value is not None:
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", result

        return "PASSED"
    except AssertionError as e:
        return str(e)


def assert_required_payload_fields(
    payload_data: dict, fields: tuple[str, ...], test_data
) -> None:
    variation = test_data.variant_number

    for field in fields:
        value = payload_data.get(field)
        if variation == 4 and field == "responseAdapter" and value is not None:
            value = True
        error_msg = f"FAILED -> No '{field}' object found in payload data."
        msg = is_data_present(value, error_msg)
        assert msg == "PASSED", msg
