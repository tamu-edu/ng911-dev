import json
import re

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from services.aux.json_services import is_jws_string, decrypt_jws, is_valid_rtsp_url, validate_log_event_id, \
    is_valid_iso_datetime
from tests.LOG_004.constants import LOG_EVENT_TYPES, REQUIRED_CALL_ID, REQUIRED_INCIDENT_ID

FIELD_TYPES = {"count": int,
               "totalCount": int,
               "logEventContainers": (list, dict, tuple)}


def validate_required_types(log_event, record_type, payload_data):
    list_of_required_types = {"callId": REQUIRED_CALL_ID,
                              "incidendId": REQUIRED_INCIDENT_ID,
                              "callIdSIP": REQUIRED_CALL_ID}

    if log_event == 'CallSignalingMessageLogEvent' and payload_data['protocol'] == 'sip':
        if not payload_data.get('callId', None):
            return "FAILED-> 'callId' is required for 'CallSignalingMessageLogEvent'"

    if log_event not in list_of_required_types[record_type]:
        return f"FAILED-> Invalid 'callId' is missing for required logEventType: {log_event}"
    else:
        return "PASSED"


def validate_response_json_for_http_get_to_logevents_entrypoint(**result_data: dict[str: str]):

    if result_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"

    # TODO
    """
    JWS is signed by certificate traceable to the PCA
    if 'agencyAgentId' is present then JWS shall be signed by certificate where CN match FQDN from this header field
    if 'agencyAgentId' is not present then JWS shall be signed by certificate where CN match FQDN from 'elementId'
    """

    for element in json.loads(result_data['response'].json.object)['logEventContainers']:
        # Validate that only one 'logEventId' exists which is a string
        log_event_id = element.get('logEventId', None)
        if not log_event_id:
            return "FAILED-> 'logEventId' is missing"
        if (result := is_type(log_event_id, 'logEvent', str)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

        # Validate JWS
        jws = element.get('logEvent', None)
        if not jws:
            return "FAILED-> 'logEvent' is missing"

        if not is_jws_string(jws):
            return "FAILED-> Invalid JWS"

        payload_header, payload_data = decrypt_jws(jws, result_data['scen_filepath'])

        # Verify that JSW payload JSON contains zero or one 'clientAssignedIdentifier' which is a string
        client_assigned_identifier = payload_data.get('clientAssignedIdentifier', None)
        if client_assigned_identifier:
            if (result := is_type(log_event_id, 'clientAssignedIdentifier', str)) != 'PASSED':
                # Test step result FAILED in case of invalid format
                return result

        # Verify that 'logEventType' which has one of expecting values
        payload_elements = {'logEventType', 'timestamp', 'elementId', 'agencyId', 'agencyAgentId'}
        for pe in payload_elements:
            if not payload_data.get(pe):
                return f"FAILED-> No '{pe}' in JWS"
        # Verify that 'logEventType' which has one of required values
        if payload_data['logEventType'] not in LOG_EVENT_TYPES:
            return "FAILED-> Invalid 'logEventType'"

        # Verify that 'timestamp' with string date-time value, example: "2020-03-10T10:00:00-05:00"
        if not is_valid_iso_datetime(payload_data['timestamp']):
            return "FAILED-> Invalid 'timestamp'"

        # Verify that 'elementId' which has string value with FQDN
        if not re.search(FQDN_PATTERN, payload_data['elementId']):
            return "FAILED-> Wrong FQDN in JWS in 'elementId'"

        # Verify that 'agencyId' which has string value with FQDN
        if not re.search(FQDN_PATTERN, payload_data['agencyId']):
            return "FAILED-> Wrong FQDN in JWS in 'agencyId'"

        # Verify that zero or one 'agencyPositionId' which is a string
        agency_position_id = payload_data.get('agencyPositionId', None)
        if agency_position_id:
            if client_assigned_identifier:
                if (result := is_type(agency_position_id, 'agencyPositionId', str)) != 'PASSED':
                    # Test step result FAILED in case of invalid format
                    return result

        # Verify that 'callId'/'incidentId'/'callIdSIP'  is in required 'logEventType'
        for log_record in ('callId', 'incidentId', 'callIdSIP'):
            if payload_data.get(log_record, None):
                if (result := validate_required_types(payload_data['logEventType'],
                                                      log_record, payload_data)) != 'PASSED':
                    return result
                if log_record != "callIdSIP":
                    if (result := validate_log_event_id(payload_data[log_record], log_record)) != 'PASSED':
                        # Test step result FAILED in case of invalid format
                        return result

        # Verify that 'ipAddressPort' is valid FQDN format
        if not re.search(FQDN_PATTERN, payload_data['ipAddressPort']):
            return "FAILED-> Wrong FQDN in JWS in 'ipAddressPort'"

        # Verify that zero or one 'extension' which is a JSON object
        extension = payload_data.get('extension', None)
        if extension:
            if (result := is_type(extension, 'extension', str)) != 'PASSED':
                # Test step result FAILED in case of invalid format
                return result
            # Validate JSON format
            try:
                json.loads(extension)
            except json.JSONDecodeError:
                return "FAILED-> Invalid JSON format for 'extension'"

        # Verify zero or one 'rtsp' which is a string
        rtsp = payload_data.get('rtsp', None)
        if rtsp:
            if (result := is_type(rtsp, 'rtsp', str)) != 'PASSED':
                # Test step result FAILED in case of invalid format
                return result
            elif not is_valid_rtsp_url(rtsp):
                return "FAILED-> Invalid 'rtsp' format"

        # TODO
        """
        'ipAddressPort' should be the same as IP in From header field of SIP message
        included within "text" parameter of Log Event
        """

    return "PASSED"


def validate_json_body_for_log_events(**result_data):
    rtsp_records = set()
    if result_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"

    # Validate that: 'count' which is integer,
    #                'totalCount' which is integer,
    #                'logEventContainers' which is array of zero or more objects
    for key, value in FIELD_TYPES.items():
        elem = json.loads(result_data['response'].json.object)[key]
        if (result := is_type(elem, key, value)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

    for element in json.loads(result_data['response'].json.object)['logEventContainers']:
        # Validate that only one 'logEventId' exists which is a string
        log_event_id = element.get('logEventId', None)
        if not log_event_id:
            return "FAILED-> 'logEventId' is missing"
        if (result := is_type(log_event_id, 'logEvent', str)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

        rtsp = element.get('rtsp', None)

        # Validate RTSP URI if present
        if rtsp:
            if rtsp in rtsp_records:
                return "FAILED-> RTSP URI is not unique"
            else:
                rtsp_records.add(rtsp)
            if not is_valid_rtsp_url(rtsp):
                return "FAILED-> Invalid 'rtsp' format"

        # Validate JWS
        jws = element.get('logEvent', None)
        if not jws:
            return "FAILED-> 'logEvent' is missing"

        if not is_jws_string(jws):
            return "FAILED-> Invalid JWS"

        if (result := validate_response_json_for_http_get_to_logevents_entrypoint(**result_data)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

    return "PASSED"
