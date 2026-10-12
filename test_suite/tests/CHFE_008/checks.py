import re
from typing import Any, Dict

from pyshark.packet.packet import Packet

from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from enums import SIPStatusCodeEnum, SIPMethodEnum
from services.aux_services.json_services import get_json
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)
from services.aux_services.sip_msg_body_services import (
    extract_header_field_value_from_raw_body,
)
from tests.CHFE_008.constants import (
    SERVICE_STATE_VALUES,
    SERVICE_NAMES,
    EVENT,
    POSTURE_VALUES,
    PASSED,
)


def validate_chfe_state_response_data(
    sip_response_data: tuple[Packet, Packet, Packet] | None,
) -> str:
    """
    A function that runs validation functions according to the TD CHFE_008 against SIP NOTIFY response.
    @param sip_response_data: test input packets from CHFE (Notify response, Subscribe request, Subscribe response)
    @return: result of testing "PASSED" or "FAILED"
    """

    if not sip_response_data:
        return "FAILED -> No SIP NOTIFY response found."

    notify_message, subscribe_request, subscribe_response = sip_response_data

    try:
        json_object = getattr(notify_message, "json", None)
        if json_object is None:
            all_body_content = extract_all_contents_from_message_body(notify_message)
            if isinstance(all_body_content, list) and all_body_content:
                body = all_body_content[0].get("body")
                json_object = get_json(body)
    except AttributeError:
        return "FAILED -> Invalid JSON body in SIP NOTIFY."

    try:
        result_subscribe_status_validation = validate_subscribe_response_status(
            subscribe_response
        )
        assert (
            result_subscribe_status_validation == PASSED
        ), result_subscribe_status_validation

        result_response_event_validation = validate_response_event(
            notify_message, subscribe_request
        )
        assert (
            result_response_event_validation == PASSED
        ), result_response_event_validation

        result_service_data_field_validation = validate_service_fields(json_object)
        assert (
            result_service_data_field_validation == PASSED
        ), result_service_data_field_validation

        result_service_state_data_field_validation = validate_service_state_fields(
            json_object
        )
        assert (
            result_service_state_data_field_validation == PASSED
        ), result_service_state_data_field_validation

        result_security_posture_field_validation = validate_security_posture_fields(
            json_object
        )
        assert (
            result_security_posture_field_validation == PASSED
        ), result_security_posture_field_validation

    except AssertionError as e:
        return str(e)

    return PASSED


def validate_subscribe_response_status(subscribe: Packet | None) -> str:
    """
    Function to validate response status of SIP NOTIFY
    @param subscribe: Subscribe response
    @return: test result "PASSED" or "FAILED"
    """

    if not subscribe:
        return "FAILED -> Subscribe response not found."

    sip_attribute_str = "sip"
    sip_status_line_attribute_str = "status_line"

    sip = getattr(subscribe, sip_attribute_str, None)
    if not sip:
        return f"FAILED -> Subscribe doesn't contain the {sip_attribute_str} attribute."

    if not hasattr(sip, sip_status_line_attribute_str):
        return f"FAILED -> Subscribe sip doesn't contain the '{sip_status_line_attribute_str}' attribute."

    subscribe_response_status_line = subscribe.sip.status_line

    if (
        isinstance(subscribe_response_status_line, str)
        and len(subscribe_response_status_line.split()) == 3
    ):
        _, code, status = subscribe_response_status_line.split()
        if str(code) != str(SIPStatusCodeEnum.OK.value):
            return f"FAILED -> Actual SUBSCRIBE response code is '{code}'. Expected '{SIPStatusCodeEnum.OK.value}'."

        if status != SIPMethodEnum.OK:
            return f"FAILED -> Actual response status phrase is '{status}'. Expected '{SIPMethodEnum.OK.value}'."

    else:
        return "FAILED -> SUBSCRIBE response Status-Line field doesn't contain response status"

    return PASSED


def validate_response_event(notify: Packet | None, subscribe: Packet | None) -> str:
    """
    Function to validate Event of SIP NOTIFY
    @param notify: SIP Notify response packet
    @param subscribe: SIP Subscribe request packet
    @return: test result "PASSED" or "FAILED"
    """

    if not notify:
        return "FAILED -> Notify packet not found."
    if not subscribe:
        return "FAILED -> Subscribe packet not found."

    sip_attribute_str = "sip"
    sip_msg_hdr_attribute_str = "msg_hdr"

    sip = getattr(subscribe, sip_attribute_str, None)
    if not sip:
        return f"FAILED -> Subscribe doesn't contain the {sip_attribute_str} attribute."

    if not hasattr(sip, sip_msg_hdr_attribute_str):
        return f"FAILED -> Subscribe sip doesn't contain the '{sip_msg_hdr_attribute_str}' attribute."

    subscribe_event = extract_header_field_value_from_raw_body(
        "Event", subscribe.sip.msg_hdr
    ).split(";")[0]

    sip = getattr(notify, sip_attribute_str, None)
    if not sip:
        return f"FAILED -> Notify doesn't contain the '{sip_attribute_str}' attribute."

    if not hasattr(sip, sip_msg_hdr_attribute_str):
        return f"FAILED -> Notify sip doesn't contain the '{sip_msg_hdr_attribute_str}' attribute."

    notify_event = extract_header_field_value_from_raw_body(
        "Event", notify.sip.msg_hdr
    ).split(";")[0]

    if subscribe_event == EVENT and notify_event == EVENT:
        return PASSED
    else:
        return f"FAILED -> Expected event '{EVENT}'. Found Subscribe Event - '{subscribe_event}', Notify Event - '{notify_event}'."


def validate_service_fields(json_object: Dict[str, Any]) -> str:
    """
    Function to validate 'service' SIP NOTIFY response
    @param json_object: json object from response
    @return: test result "PASSED" or "FAILED"
    """

    if not json_object:
        return "FAILED -> JSON body not found in SIP NOTIFY"

    service_field_name = "service"
    service = json_object.get(service_field_name, None)
    initial_validation_result = validate_field(service, service_field_name, nested=True)
    assert initial_validation_result == PASSED, initial_validation_result

    # Validate service name

    name_string = "name"
    service_name = service.get(name_string, None)

    service_name_initial_validation = validate_field(service_name, name_string)
    assert service_name_initial_validation == PASSED, service_name_initial_validation

    if service_name not in SERVICE_NAMES:
        return f"FAILED -> Actual {name_string} value for 'service' is '{service_name}'. Expected one of '{SERVICE_NAMES}'"

    # Validate domain

    domain_fqdn = None
    domain_string = "domain"
    domain = service.get(domain_string, None)

    domain_initial_validation = validate_field(domain, domain_string)
    assert domain_initial_validation == PASSED, domain_initial_validation

    if not re.search(FQDN_PATTERN, domain):
        return f"FAILED-> Wrong FQDN in {domain_string}"
    else:
        domain_fqdn = domain

    # Validate service ID

    service_id_name = "serviceId"
    service_id = service.get(service_id_name, None)

    if service_id is None:
        pass
    elif not service_id:
        return f"FAILED -> Field {service_id_name} is empty."
    else:
        if service_id not in domain_fqdn:
            return f"FAILED -> {service_id_name} FQDN - '{service_id}' is not the same as 'domain' FQDN - '{domain_fqdn}'."

    return PASSED


def validate_service_state_fields(json_object: Dict[str, Any]) -> str:
    """
    Function to validate 'serviceState' SIP NOTIFY response
    @param json_object: json object from response
    @return: test result "PASSED" or "FAILED"
    """

    service_state_field_name = "serviceState"
    service_state = json_object.get(service_state_field_name, None)
    initial_validation_result = validate_field(
        service_state, service_state_field_name, nested=True
    )
    assert initial_validation_result == PASSED, initial_validation_result

    state_string = "state"
    state = service_state.get(state_string, None)

    state_initial_validation = validate_field(state, state_string)
    assert state_initial_validation == PASSED, state_initial_validation

    if state not in SERVICE_STATE_VALUES:
        return f"FAILED -> Actual {state_string} value for {service_state_field_name} is '{state}'. Expected one of '{SERVICE_STATE_VALUES}'"

    reason_string = "reason"
    reason = service_state.get(reason_string, None)

    if reason is None:
        return f"FAILED -> '{reason_string}' field doesn't exist."
    elif not isinstance(reason, str):
        return f"FAILED -> '{reason_string}' field is not a string."

    return PASSED


def validate_security_posture_fields(json_object: Dict[str, Any]) -> str:
    """
    Function to validate optional 'securityPosture' SIP NOTIFY response
    @param json_object: json object from response
    @return: test result "PASSED" or "FAILED"
    """

    security_posture_field_name = "securityPosture"
    posture_name = "posture"
    security_posture = json_object.get(security_posture_field_name, None)

    if security_posture is None:
        pass
    else:
        posture_initial_validation = validate_field(
            security_posture, posture_name, nested=True
        )
        assert posture_initial_validation == PASSED, posture_initial_validation

        posture = security_posture.get(posture_name, None)
        posture_field_validation = validate_field(posture, posture_name)
        assert posture_field_validation == PASSED, posture_field_validation

        if posture not in POSTURE_VALUES:
            return f"FAILED -> Actual '{posture_name}' value for {security_posture_field_name} is '{posture}'. Expected one of '{POSTURE_VALUES}'"

    return PASSED


def validate_field(json_data: Dict[str, Any], field: str, nested: bool = False) -> str:
    """
    Function to validate field nested data
    @param json_data: json object to check
    @param field: field name to check
    @param nested: True - check if nested obj is dictionary.
    @return: test result "PASSED" or "FAILED"
    """

    if nested and not isinstance(json_data, dict) and json_data is not None:
        return f"FAILED -> Field '{field}' doesn't contain nested JSON object. Actual data is '{json_data}'."
    elif json_data is None:
        return f"FAILED -> '{field}' doesn't exist in JSON SIP response."
    elif not json_data:
        return f"FAILED -> '{field}' field is empty JSON SIP response."

    return PASSED
