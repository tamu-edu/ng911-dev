import json
import re
from json import JSONDecodeError

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from services.aux_services.aux_services import validate_ip_port_combo
from services.aux_services.json_services import is_jws, decode_jws, is_valid_rtsp_url, validate_identifier, \
    is_valid_iso_datetime, is_signed_by_tracable_pca, get_jws_from_http_media_layer
from services.aux_services.sip_msg_body_services import is_valid_sip_call_id
from tests.LOG_004.constants import LOG_EVENT_TYPES, REQUIRED_CALL_ID, REQUIRED_INCIDENT_ID

FIELD_TYPES = {"count": int,
               "totalCount": int,
               "logEventContainers": (list, dict, tuple)}


def validate_required_types(record_type, log_event, payload_data):
    list_of_required_types = {"callId": REQUIRED_CALL_ID,
                              "incidentId": REQUIRED_INCIDENT_ID,
                              "callIdSIP": REQUIRED_CALL_ID}

    if record_type in list_of_required_types[log_event]:
        if not payload_data.get(log_event, None):
            return f"FAILED-> Invalid 'callId' is missing for required logEventType: {record_type}"
    return "PASSED"


def validate_response_json_for_http_get_to_logevents_entrypoint(container=None, **result_data: dict[str: str]):
    if not result_data['response'] or result_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"
    if container:
        jws = container
    else:
        jws = get_jws_from_http_media_layer(result_data['response']).replace('\n', '')

    # Validate JWS
    if not jws:
        return "FAILED-> 'logEvent' is missing"

    if not is_jws(jws):
        return "FAILED-> Invalid JWS"

    with open(result_data['pca_key'], "r") as cert:
        trusted_pca_cert = cert.read()

    if not is_signed_by_tracable_pca(jws, trusted_pca_cert):
        return "FAILED-> JWS is not signed by certificate traceable to the PCA"

    payload_header, payload_data = decode_jws(jws, result_data['key_filepath'])

    # Verify that JSW payload JSON contains zero or one 'clientAssignedIdentifier' which is a string
    client_assigned_identifier = payload_data.get('clientAssignedIdentifier', None)
    if client_assigned_identifier:
        if (result := is_type(client_assigned_identifier, 'clientAssignedIdentifier', str)) != 'PASSED':
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
        if (result := is_type(agency_position_id, 'agencyPositionId', str)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

    # Verify that 'callId'/'incidentId'/'callIdSIP' is in required 'logEventType'
    for log_record in ('callId', 'incidentId', 'callIdSIP'):
        if payload_data.get(log_record, None):
            if (result := validate_required_types(payload_data['logEventType'],
                                                  log_record, payload_data)) != 'PASSED':
                return result
            if log_record != "callIdSIP":
                if (result := validate_identifier(payload_data[log_record], log_record)) != 'PASSED':
                    # Test step result FAILED in case of invalid format
                    return result

            else:
                if not is_valid_sip_call_id(payload_data.get(log_record, None)):
                    return "FAILED-> Invalid 'callIdSIP' format"

    # Verify that 'ipAddressPort' is valid FQDN format
    ip_address_port = payload_data.get('ipAddressPort', None)
    if not ip_address_port:
        return "FAILED-> Missing 'ipAddressPort' in JWS"
    if (not re.search(FQDN_PATTERN, ip_address_port) 
            and not validate_ip_port_combo(ip_address_port)):
        return "FAILED-> FQDN or IP address+port not found in 'ipAddressPort' JWS field"

    if payload_data['logEventType'] == 'CallSignalingMessageLogEvent':
        text = payload_data.get('text', None)
        if not text:
            return "FAILED-> 'text' is missing for 'CallSignalingMessageLogEvent' eventType."
        contact = str([line for line in text.split('\n') if 'Contact' in line])
        if ip_address_port not in contact:
            return ("FAILED-> 'ipAddressPort' doesn't match to value in 'text' "
                    "for 'CallSignalingMessageLogEvent' eventType.")

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

    return "PASSED"


def validate_json_body_for_log_events(**result_data):
    rtsp_records = set()

    if not hasattr(result_data['response'], 'http'):
        return "FAILED-> Cannot find repose message"

    if result_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"

    # Validate that: 'count' which is integer,
    #                'totalCount' which is integer,
    #                'logEventContainers' which is array of zero or more objects

    for key, value in FIELD_TYPES.items():
        try:
            elem = json.loads(result_data['response'].json.object)[key]
        except AttributeError or JSONDecodeError:
            return "FAILED -> Cannot find JSON data in output message"
        if (result := is_type(elem, key, value)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

    for element in json.loads(result_data['response'].json.object)['logEventContainers']:
        # Validate that only one 'logEventId' exists which is a string
        log_event_id = element.get('logEventId', None)
        if not log_event_id:
            return "FAILED-> 'logEventId' is missing"

        if (result := validate_identifier(log_event_id, log_event_id)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

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

        if not is_jws(jws):
            return "FAILED-> Invalid JWS"

        if ((result :=
             validate_response_json_for_http_get_to_logevents_entrypoint(container=jws,
                                                                         **result_data))
                != 'PASSED'):
            # Test step result FAILED in case of invalid format
            return result

    return "PASSED"
