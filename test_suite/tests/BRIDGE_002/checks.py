import re

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from tests.BRIDGE_002.constants import ELEMENT_STATE_VALUES, SERVICE_STATE_VALUES, SERVICE_NAMES


def validate_bridge_state_response_data(**response_data):
    """
    Method that defines which test should be triggered validate_element_state or validate_service_state
    based on data taken from SIP response
    @param response_data: test input data including response from BRIDGE
    @return: result of testing "PASSED" or "FAILED"
    """
    sip_response = response_data.get('sip_response', None)
    if not sip_response:
        return "FAILED -> No SIP NOTIFY response found."
    try:
        json_object = sip_response.json
    except AttributeError:
        return "FAILED -> Invalid JSON body in SIP NOTIFY."

    # Run verification for element state response
    if json_object.get('elementId', None):
        validate_element_state(json_object)

    # Run verification for service state
    if json_object.get('serviceState', None):
        validate_service_state(json_object)
    else:
        return "FAILED -> No valid bridge response found."


def validate_element_state(json_object):
    """
    Function to validate ElementState SIP NOTIFY response
    @param json_object: json object from response
    @return: test result "PASSED" or "FAILED"
    """
    element_id = json_object.get('elementId', None)
    if not re.search(FQDN_PATTERN, element_id):
        return "FAILED-> Wrong FQDN in 'elementId'"
    state = json_object.get('state', None)
    if not element_id:
        return "FAILED -> 'state' is missing in JSON SIP response."
    if state not in ELEMENT_STATE_VALUES:
        return "FAILED -> Wrong 'state' value."

    reason = json_object.get('reason', None)
    if reason:
        if (result := is_type(reason, 'reason', str)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result
    return "PASSED"


def validate_service_state(json_object):
    """
    Function to validate ServiceState SIP NOTIFY response
    @param json_object: json object from response
    @return: test result "PASSED" or "FAILED"
    """
    service = json_object.get('service', None)
    name = service.get('service', None)
    if name not in SERVICE_NAMES:
        return "FAILED -> Wrong 'name' value for 'service'."

    service_id = service.get('serviceId', None)
    if service_id:
        if not re.search(FQDN_PATTERN, service_id):
            return "FAILED-> Wrong FQDN in 'serviceId'"

    domain = service.get('domain', None)
    if not re.search(FQDN_PATTERN, domain):
        return "FAILED-> Wrong FQDN in 'domain'"

    service_state = json_object.get('serviceState', None)

    state = service_state.get('state', None)
    if not state:
        return "FAILED -> 'state' is missing in JSON SIP response 'serviceState'."
    if service_state not in SERVICE_STATE_VALUES:
        return "FAILED -> Wrong 'service' value for 'serviceState'."

    reason = service_state.get('reason', None)
    if (result := is_type(reason, 'reason', str)) != 'PASSED' and reason != '':
        # Test step result FAILED in case of invalid format
        return result

    security_posture = json_object.get('securityPosture', None)
    if security_posture:
        posture = security_posture.get('posture', None)
        if not posture:
            return "FAILED -> 'posture' value is missing in JSON SIP response."
        if posture not in ["Green", "Yellow", "Orange", "Red"]:
            return "FAILED -> Wrong 'posture' value."

    return "PASSED"
