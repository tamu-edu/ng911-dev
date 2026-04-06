import re
from typing import Optional

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from services.aux_services.json_services import get_json
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)
from services.aux_services.sip_msg_body_services import (
    extract_header_field_value_from_raw_body,
)
from tests.ESRP_012.constants import (
    ELEMENT_STATE_VALUES,
    SERVICE_STATE_VALUES,
    VALID_POSTURE_VALUES,
)


def get_event(message) -> str:
    event = ""
    if hasattr(message.sip, "msg_hdr") and hasattr(message.sip.msg_hdr, "event"):
        event_string = extract_header_field_value_from_raw_body(
            "Event", message.sip.msg_hdr
        )
        event = event_string.split(";")[0] if ";" in event_string else event_string
    return event


def extract_json_from_message(message) -> Optional[dict]:
    """Extract the first JSON object from a SIP message body."""
    all_body_content = extract_all_contents_from_message_body(message)
    if not (isinstance(all_body_content, list) and all_body_content):
        return None
    body = all_body_content[0].get("body")
    return get_json(body)


def common_checks(
    sip_subscribe_from_bcf,
    sip_subscribe_message_ok,
    sip_notify_messages,
    state_constant,
    state_type,
) -> str:
    try:
        assert (
            sip_subscribe_from_bcf
        ), "NOT RUN-> Cannot find SIP SUBSCRIBE sent by TS to ESRP."
        assert (
            sip_subscribe_message_ok
        ), "FAILED-> ESRP should respond with 200 OK for SIP SUBSCRIBE."

        bcf_initial_state_event = get_event(sip_subscribe_from_bcf)

        esrp_state_events = set()
        for message in sip_notify_messages:
            element_state = get_event(message)
            assert (
                element_state in state_constant
            ), f"FAILED-> {state_type} value - '{element_state}' is not valid."
            esrp_state_events.add(element_state)

        if state_type == "ElementState":
            assert (
                len(esrp_state_events) > 1
            ), "FAILED-> ESRP should respond for element state change."

        assert (
            bcf_initial_state_event in esrp_state_events
        ), f"FAILED-> {state_type} event not found in ESRP NOTIFY response."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 1
def validate_element_state_and_service_state(
    sip_subscribe_element_state_message,
    sip_subscribe_service_state_message,
    sip_notify_messages,
    sip_notify_ok_messages,
) -> str:
    try:
        assert (
            sip_subscribe_element_state_message
        ), "FAILED-> No SIP SUBSCRIBE with Event: emergency-ElementState from ESRP found."
        assert (
            sip_subscribe_service_state_message
        ), "FAILED-> No SIP SUBSCRIBE with Event: emergency-ServiceState from ESRP found."  # Fix: was missing "No"
        assert len(sip_notify_ok_messages) <= len(
            sip_notify_messages
        ), "FAILED-> ESRP should respond with SIP 200 OK for each received SIP NOTIFY."
        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2
def validate_element_state_and_updating_status(
    sip_subscribe_from_bcf,
    sip_subscribe_message_ok,
    sip_notify_messages,
) -> str:
    try:
        assert (
            result := common_checks(
                sip_subscribe_from_bcf,
                sip_subscribe_message_ok,
                sip_notify_messages,
                ELEMENT_STATE_VALUES,
                "ElementState",
            )
        ) == "PASSED", result

        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert json_object, "FAILED -> No JSON object in NOTIFY message."
            assert (result := validate_element_state(json_object)) == "PASSED", result

        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 3
def validate_server_side_of_service_state(
    sip_subscribe_from_bcf,
    sip_subscribe_message_ok,
    sip_notify_messages,
) -> str:
    try:
        assert (
            result := common_checks(
                sip_subscribe_from_bcf,
                sip_subscribe_message_ok,
                sip_notify_messages,
                SERVICE_STATE_VALUES,
                "ServiceState",
            )
        ) == "PASSED", result

        for message in sip_notify_messages:
            json_object = extract_json_from_message(message)
            assert json_object, "FAILED -> No JSON object in NOTIFY message."
            assert (result := validate_service_state(json_object)) == "PASSED", result

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_element_state(json_object: dict) -> str:
    """
    Validate ElementState SIP NOTIFY response.

    :param json_object: JSON object from response
    :return: "PASSED" or a failure message
    """
    element_id = json_object.get("elementId")
    if not re.search(FQDN_PATTERN, element_id or ""):
        return "FAILED-> Wrong FQDN in 'elementId'"

    state = json_object.get("state")
    if not state:  # Fix: was checking element_id instead of state
        return "FAILED -> 'state' is missing in JSON SIP response."
    if state not in ELEMENT_STATE_VALUES:
        return "FAILED -> Wrong 'state' value."

    if reason := json_object.get("reason"):
        if (result := is_type(reason, "reason", str)) != "PASSED":
            return result

    return "PASSED"


def validate_service_state(json_object: dict) -> str:
    """
    Validate ServiceState SIP NOTIFY response.

    :param json_object: JSON object from response
    :return: "PASSED" or a failure message
    """
    service = json_object.get("service")
    if not service:  # Fix: no None guard before .get() calls
        return "FAILED -> 'service' is missing in JSON SIP response."

    if service.get("name") != "ESRP":
        return "FAILED -> Wrong 'name' value for 'service'."

    if service_id := service.get("serviceId"):
        if not re.search(FQDN_PATTERN, service_id):
            return "FAILED-> Wrong FQDN in 'serviceId'"

    domain = service.get("domain")
    if not re.search(FQDN_PATTERN, domain or ""):
        return "FAILED-> Wrong FQDN in 'domain'"

    service_state = json_object.get("serviceState")
    if not service_state:  # Fix: no None guard before .get() calls
        return "FAILED -> 'serviceState' is missing in JSON SIP response."

    state = service_state.get("state")
    if not state:
        return "FAILED -> 'state' is missing in JSON SIP response 'serviceState'."
    if (
        state not in SERVICE_STATE_VALUES
    ):  # Fix: was comparing service_state (dict) to SERVICE_STATE_VALUES
        return "FAILED -> Wrong 'service' value for 'serviceState'."

    if reason := service_state.get("reason"):
        if (result := is_type(reason, "reason", str)) != "PASSED":
            return result

    if security_posture := json_object.get("securityPosture"):
        posture = security_posture.get("posture")
        if not posture:
            return "FAILED -> 'posture' value is missing in JSON SIP response."
        if posture not in VALID_POSTURE_VALUES:
            return "FAILED -> Wrong 'posture' value."

    return "PASSED"
