from typing import Optional, Any

from checks.http.checks import is_type
from services.aux_services.json_services import get_json, is_valid_fqdn
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)

from tests.ESRP_012.constants import (
    ELEMENT_STATE_VALUES,
    SERVICE_STATE_VALUES,
    VALID_POSTURE_VALUES,
)


def get_event(message) -> str:
    """Extract the Event header value from a SIP message, stripping any parameters after ';'.

    :param message: Parsed SIP message object.
    :return: Event type string, or empty string if the header is absent.
    """
    event = ""
    if hasattr(message.sip, "event"):
        event_string = message.sip.event
        event = event_string.split(";")[0] if ";" in event_string else message.sip.event
    return event


def get_state(message) -> Any | None:
    """Extract the top-level 'state' field from the JSON body of a SIP message.

    :param message: Parsed SIP message object.
    :return: State string value, or None if the body is absent or contains no 'state' key.
    """
    json_object = extract_json_from_message(message)
    if json_object:
        return json_object.get("state", None)
    return None


def extract_json_from_message(message) -> Optional[dict]:
    """Extract the first JSON object from a SIP message body.

    :param message: Parsed SIP message object.
    :return: Parsed JSON dict from the first body part, or None if absent or not valid JSON.
    """
    all_body_content = extract_all_contents_from_message_body(message)
    if not (isinstance(all_body_content, list) and all_body_content):
        return None
    body = all_body_content[0].get("body")
    return get_json(body)


# Variation 2 - Check 2
def check_all_notify_element_state_values_valid(sip_notify_messages) -> str:
    """Verify that every SIP NOTIFY carries a 'state' value from the allowed ElementState set.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first invalid state value.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            element_state = get_state(message)
            assert (
                element_state in ELEMENT_STATE_VALUES
            ), f"FAILED -> Expected: one of {ELEMENT_STATE_VALUES}. Actual: '{element_state}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2 - Check 3
def check_element_state_change_observed(sip_notify_messages) -> str:
    """Verify that at least two distinct ElementState values appear across the SIP NOTIFY messages,
    confirming that the IUT reported a state transition.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if all NOTIFYs carry the same state.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        esrp_state_events = {get_state(message) for message in sip_notify_messages}
        assert (
            len(esrp_state_events) > 1
        ), f"FAILED -> Expected: at least 2 distinct ElementState values. Actual: {len(esrp_state_events)} unique state(s) observed: {esrp_state_events}."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2 & 3 - Check (shared)
def check_all_notify_messages_have_json_body(sip_notify_messages) -> str:
    """Verify that every SIP NOTIFY message contains a parseable JSON body.

    Shared by Variation 2 (ElementState) and Variation 3 (ServiceState).

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first NOTIFY with a missing JSON body.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2 - Check 4
def check_all_notify_element_id_is_valid_fqdn(sip_notify_messages) -> str:
    """Verify that the 'elementId' field in every SIP NOTIFY JSON body is a valid FQDN.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first invalid elementId.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            element_id = json_object.get("elementId")
            assert is_valid_fqdn(
                element_id
            ), f"FAILED -> Expected: valid FQDN in 'elementId'. Actual: '{element_id}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2 - Check 5
def check_all_notify_element_state_field_present(sip_notify_messages) -> str:
    """Verify that the 'state' field is present in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if the field is absent or empty.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            assert json_object.get(
                "state"
            ), "FAILED -> Expected: 'state' field present in JSON body. Actual: field is absent."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2 - Check 6
def check_all_notify_element_reason_is_string(sip_notify_messages) -> str:
    """Verify that the optional 'reason' field, when present, is a string type
    in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if 'reason' is present but not a string.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            if reason := json_object.get("reason"):
                result = is_type(reason, "reason", str)
                assert result == "PASSED", result
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 2
def check_all_notify_service_state_values_valid(sip_notify_messages) -> str:
    """Verify that every SIP NOTIFY carries a 'state' value from the allowed ServiceState set.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first invalid state value.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service_state = json_object.get("serviceState", None)
            assert service_state, "FAILED - ServiceState field is absent."
            state = service_state.get("state", None)
            assert (
                state in SERVICE_STATE_VALUES
            ), f"FAILED -> Expected: one of {SERVICE_STATE_VALUES}. Actual: '{state}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 3
def check_all_notify_service_object_present(sip_notify_messages) -> str:
    """Verify that the 'service' object is present in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if the field is absent.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            assert json_object.get(
                "service"
            ), "FAILED -> Expected: 'service' object present in JSON body. Actual: field is absent."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 4
def check_all_notify_service_name_is_esrp(sip_notify_messages) -> str:
    """Verify that the 'service.name' field equals 'ESRP' in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if the value is wrong or absent.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service = json_object.get("service")
            if service:
                actual_name = service.get("name")
                assert (
                    actual_name == "ESRP"
                ), f"FAILED -> Expected: service.name = 'ESRP'. Actual: '{actual_name}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 5
def check_all_notify_service_id_is_valid_fqdn(sip_notify_messages) -> str:
    """Verify that the optional 'service.serviceId' field, when present,
    is a valid FQDN in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first invalid serviceId.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service = json_object.get("service")
            if service:
                if service_id := service.get("serviceId"):
                    assert is_valid_fqdn(
                        service_id
                    ), f"FAILED -> Expected: valid FQDN in 'service.serviceId'. Actual: '{service_id}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 6
def check_all_notify_service_domain_is_valid_fqdn(sip_notify_messages) -> str:
    """Verify that the 'service.domain' field is a valid FQDN in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first invalid domain.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service = json_object.get("service")
            if service:
                domain = service.get("domain")
                assert is_valid_fqdn(
                    domain
                ), f"FAILED -> Expected: valid FQDN in 'service.domain'. Actual: '{domain}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 7
def check_all_notify_service_state_object_present(sip_notify_messages) -> str:
    """Verify that the 'serviceState' object is present in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if the object is absent.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            assert json_object.get(
                "serviceState"
            ), "FAILED -> Expected: 'serviceState' object present in JSON body. Actual: field is absent."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 8
def check_all_notify_service_state_value_present(sip_notify_messages) -> str:
    """Verify that the 'state' field is present inside the 'serviceState' object
    in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if the field is absent or empty.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service_state = json_object.get("serviceState")
            if service_state:
                assert service_state.get(
                    "state"
                ), "FAILED -> Expected: 'state' field present in 'serviceState'. Actual: field is absent."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 9
def check_all_notify_service_state_value_is_valid(sip_notify_messages) -> str:
    """Verify that the 'serviceState.state' value is from the allowed ServiceState set
    in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message identifying the first invalid state value.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service_state = json_object.get("serviceState")
            if service_state:
                state = service_state.get("state")
                assert (
                    state in SERVICE_STATE_VALUES
                ), f"FAILED -> Expected: serviceState.state to be one of {SERVICE_STATE_VALUES}. Actual: '{state}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 10
def check_all_notify_service_state_reason_is_string(sip_notify_messages) -> str:
    """Verify that the optional 'reason' field inside 'serviceState', when present,
    is a string type in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if 'reason' is present but not a string.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            service_state = json_object.get("serviceState")
            assert service_state, "FAILED -> 'serviceState' is missing"
            if reason := service_state.get("reason"):
                result = is_type(reason, "reason", str)
                assert result == "PASSED", result
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 11
def check_all_notify_security_posture_field_present(sip_notify_messages) -> str:
    """Verify that the 'posture' field is present inside 'securityPosture', when that
    object exists, in every SIP NOTIFY JSON body.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if 'posture' is absent inside 'securityPosture'.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            security_posture = json_object.get("securityPosture")
            assert security_posture, "FAILED -> 'securityPosture' is missing"
            posture = security_posture.get("posture")
            assert posture in [
                "Green",
                "Yellow",
                "Orange",
                "Red",
            ], "FAILED -> 'posture' should be one of Green/Yellow/Orange/Red. Actual: '{posture}'."

        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3 - Check 12
def check_all_notify_security_posture_value_is_valid(sip_notify_messages) -> str:
    """Verify that the 'securityPosture.posture' value is from the allowed posture set
    in every SIP NOTIFY JSON body where 'securityPosture' is present.

    :param sip_notify_messages: List of captured SIP NOTIFY messages.
    :return: "PASSED" or a failure message if the posture value is not recognised.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages found."
        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert (
                json_object
            ), "FAILED -> Expected: parseable JSON body in SIP NOTIFY. Actual: no JSON body found."
            if security_posture := json_object.get("securityPosture"):
                posture = security_posture.get("posture")
                if posture:
                    assert (
                        posture in VALID_POSTURE_VALUES
                    ), f"FAILED -> Expected: securityPosture.posture to be one of {VALID_POSTURE_VALUES}. Actual: '{posture}'."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 1 - Check 1
def check_subscribe_with_element_state_event_sent(
    sip_subscribe_element_state_message,
) -> str:
    """Verify that the ESRP sent a SIP SUBSCRIBE with Event: emergency-ElementState
    to the downstream ESRP.

    :param sip_subscribe_element_state_message: Captured SUBSCRIBE message, or None if not found.
    :return: "PASSED" or a failure message string.
    """
    try:
        assert (
            sip_subscribe_element_state_message
        ), "FAILED -> Expected: SIP SUBSCRIBE with Event: emergency-ElementState from ESRP. Actual: no such message found."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 1 - Check 2
def check_subscribe_with_service_state_event_sent(
    sip_subscribe_service_state_message,
) -> str:
    """Verify that the ESRP sent a SIP SUBSCRIBE with Event: emergency-ServiceState
    to the downstream ESRP.

    :param sip_subscribe_service_state_message: Captured SUBSCRIBE message, or None if not found.
    :return: "PASSED" or a failure message string.
    """
    try:
        assert (
            sip_subscribe_service_state_message
        ), "FAILED -> Expected: SIP SUBSCRIBE with Event: emergency-ServiceState from ESRP. Actual: no such message found."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 1 - Check 3
def check_notify_200_ok_for_each_received_notify(
    sip_notify_messages,
    sip_notify_ok_messages,
) -> str:
    """Verify that the ESRP responded with SIP 200 OK for each received SIP NOTIFY,
    i.e. the count of 200 OK responses does not exceed the count of NOTIFY messages.

    :param sip_notify_messages: List of SIP NOTIFY messages received by the ESRP.
    :param sip_notify_ok_messages: List of SIP 200 OK responses sent by the ESRP.
    :return: "PASSED" or a failure message string.
    """
    try:
        assert sip_notify_messages, "FAILED -> No SIP NOTIFY messages have been found."
        assert (
            sip_notify_ok_messages
        ), "FAILED -> No SIP NOTIFY OK messages have been found."
        assert len(sip_notify_ok_messages) == len(
            sip_notify_messages
        ), f"FAILED -> Expected: {len(sip_notify_messages)} SIP 200 OK responses (one per NOTIFY). Actual: {len(sip_notify_ok_messages)} found."
        return "PASSED"
    except AssertionError as e:
        return str(e)
