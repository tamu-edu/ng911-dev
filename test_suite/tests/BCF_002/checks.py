import json
import re

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from services.aux_services.aux_services import is_valid_timestamp
from services.aux_services.json_services import is_valid_jcard


def validate_support_of_discrepancy_report(**test_data):
    bcf_output_message = test_data['output_message']

    if not bcf_output_message:
        return "FAILED -> No O-BCF response message has been found. BCF should respond with 201 OK."

    json_obcf_response = None

    try:
        if hasattr(bcf_output_message, 'json') and hasattr(bcf_output_message.json, 'object'):
            json_obcf_response = json.loads(bcf_output_message.json.object)

    except AttributeError:
        return "FAILED -> Invalid request message to O-BFC"

    responding_agency_name = json_obcf_response.get('respondingAgencyName', None)
    if not responding_agency_name:
        return "FAILED -> No 'respondingAgencyName' found in the Discrepancy Report."
    if not re.search(FQDN_PATTERN, responding_agency_name):
        return "FAILED -> 'respondingAgencyName' has invalid FQDN value."

    responding_contact_jcard = json_obcf_response.get('respondingContactJcard', None)
    if not responding_contact_jcard:
        return "FAILED -> No 'respondingAgencyName' found in the Discrepancy Report."
    if not is_valid_jcard(responding_contact_jcard):
        return "FAILED -> 'respondingContactJcard' has invalid format."

    responding_agent_id = json_obcf_response.get('respondingAgentId', None)
    if responding_agent_id:
        if (result := is_type(responding_agent_id, 'respondingAgentId', str)) != 'PASSED':
            return result

    response_estimated_return_time = json_obcf_response.get('responseEstimatedReturnTime', None)
    if response_estimated_return_time:
        if not is_valid_timestamp(response_estimated_return_time):
            return "FAILED -> Invalid datetime format for 'responseEstimatedReturnTime'."

    response_comments = json_obcf_response.get('responseComments', None)
    if responding_agent_id:
        if (result := is_type(response_comments, 'responseComments', str)) != 'PASSED':
            return result

    return "PASSED"
