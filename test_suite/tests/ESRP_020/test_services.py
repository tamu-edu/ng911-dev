from dataclasses import dataclass
from typing import Optional

from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
    check_each_element,
)
from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_incident_tracking_id_urn,
)
from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.json_services import is_valid_fqdn
from services.aux_services.message_services import get_logevent_list_by_type
from services.aux_services.sip_msg_body_services import (
    clean_up_string,
)
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
    extract_sip_header_values,
)
from services.aux_services.xml_services import extract_xml
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.message_collector_service import MessageCollectorService
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_014.checks import validate_optional_log_event_fields
from tests.ESRP_020.constants import OPTIONAL_STRING_FIELDS
from tests.ESRP_020.checks import (
    validate_event_count,
    compare_timestamps,
    check_response_status,
    validate_response_id_match_to_query_id,
)
from tests.ESRP_020.constants import (
    ADR_RESPONSE_LOG_EVENT_TYPE,
    EXPECTED_ADR_COUNT,
)


@dataclass
class AdditionalDataQueryLogEvent:
    text: Optional[str] = None
    uri: Optional[str] = None
    query_id: Optional[str] = None
    direction: Optional[str] = None
    timestamp: Optional[str] = None
    element_id: Optional[str] = None
    agency_id: Optional[str] = None
    call_id: Optional[str] = None
    incident_id: Optional[str] = None
    call_id_sip: Optional[str] = None
    adr_http_post_body: Optional[str] = None
    adr_uri: Optional[str] = None
    extension: Optional[str] = None
    raw_event: Optional[str] = None


@dataclass
class AdditionalDataResponseLogEvent:
    text: Optional[str] = None
    response_status: Optional[str] = None
    response_id: Optional[str] = None
    direction: Optional[str] = None
    timestamp: Optional[str] = None
    element_id: Optional[str] = None
    agency_id: Optional[str] = None
    call_id: Optional[str] = None
    incident_id: Optional[str] = None
    call_id_sip: Optional[str] = None
    adr_http_post_body: Optional[str] = None
    extension: Optional[str] = None
    raw_event: Optional[str] = None


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, key_filepath, is_variation_2)
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    key_filepath = None
    is_variation_2 = False

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    for message in variation.params["messages"]:
        if all(
            (
                message.get("action", None) == "receive",
                "Malformed" in message.get("body", ""),
            )
        ):
            is_variation_2 = True

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                    key_filepath = entity.certificate_key

        missing = [
            name
            for name, value in (
                ("stimulus_src_ip", stimulus_src_ip),
                ("stimulus_dst_ip", stimulus_dst_ip),
            )
            if value is None
        ]

        if missing:
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses.\n"
                f"Missing: {', '.join(missing)}"
            )
        return (
            stimulus_src_ip,
            stimulus_dst_ip,
            key_filepath,
            is_variation_2,
        )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required parameters for filtering"
        )


def _extract_adr_body(adr_requests: list, idx: int) -> str | None:
    """
    Decode the TCP payload of the ADR HTTP request at ``adr_requests[idx][0]``
    and return the XML body extracted from it. Returns an empty string when
    ``idx`` is out of range or the interface has no captured packets.

    :param adr_requests: List of per-interface ADR request captures; each
        element is a list of packet records whose first entry carries the
        ``tcp.payload`` hex string.
    :param idx: Index of the interface (outer list) to read from.
    :return: XML body string produced by :func:`extract_xml`.
    """
    if idx >= len(adr_requests) or not adr_requests[idx]:
        return None
    hex_data = adr_requests[idx][0].tcp.payload.replace(":", "")
    byte_data = bytes.fromhex(hex_data)
    message_body = byte_data.decode("ascii", errors="ignore")
    return extract_xml(message_body).replace("\r", "")


def _extract_adr_uri(adr_requests: list, idx: int) -> Optional[str]:
    """
    Return the ``http.request_full_uri`` of the ADR HTTP request at
    ``adr_requests[idx][0]``, or ``None`` if the index is out of range or the
    packet has no ``request_full_uri`` attribute.

    :param adr_requests: List of per-interface ADR request captures; each
        element is a list of packet records.
    :param idx: Index of the interface (outer list) to read from.
    :return: The full request URI string, or ``None`` when unavailable.
    """
    return (
        adr_requests[idx][0].http.request_full_uri.replace("\r", "")
        if (
            idx < len(adr_requests)
            and adr_requests[idx]
            and hasattr(adr_requests[idx][0].http, "request_full_uri")
        )
        else ""
    )


def _extract_additional_data_logevent_list(
    esrp_log_events, key_filepath, init_call_id, adr_requests, adr_responses
):
    additional_data_query_list = []
    additional_data_response_list = []

    adr_query_logevents = get_logevent_list_by_type(
        esrp_log_events, "AdditionalDataQueryLogEvent", key_filepath, init_call_id
    )

    if adr_query_logevents:
        for idx, logevent in enumerate(adr_query_logevents):
            additional_data_query_list.append(
                AdditionalDataQueryLogEvent(
                    text=logevent.get("text", "").replace("\r", ""),
                    uri=logevent.get("uri"),
                    query_id=logevent.get("queryId"),
                    direction=logevent.get("direction"),
                    timestamp=logevent.get("timestamp"),
                    element_id=logevent.get("elementId"),
                    agency_id=logevent.get("agencyId"),
                    call_id=logevent.get("callId"),
                    incident_id=logevent.get("incidentId"),
                    call_id_sip=logevent.get("callIdSip"),
                    adr_http_post_body=_extract_adr_body(adr_requests, idx),
                    adr_uri=_extract_adr_uri(adr_requests, idx),
                    extension=logevent.get("extension"),
                    raw_event=logevent,
                )
            )

    adr_response_logevents = get_logevent_list_by_type(
        esrp_log_events,
        "AdditionalDataResponseLogEvent",
        key_filepath,
        init_call_id,
    )

    if adr_response_logevents:
        for idx, logevent in enumerate(adr_response_logevents):
            additional_data_response_list.append(
                AdditionalDataResponseLogEvent(
                    text=logevent.get("text", "").replace("\r", ""),
                    response_status=logevent.get("responseStatus", ""),
                    response_id=logevent.get("responseId"),
                    direction=logevent.get("direction"),
                    timestamp=logevent.get("timestamp"),
                    element_id=logevent.get("elementId"),
                    agency_id=logevent.get("agencyId"),
                    call_id=logevent.get("callId"),
                    incident_id=logevent.get("incidentId"),
                    call_id_sip=logevent.get("callIdSip"),
                    adr_http_post_body=_extract_adr_body(adr_responses, idx),
                    extension=logevent.get("extension"),
                    raw_event=logevent,
                )
            )

    return additional_data_query_list, additional_data_response_list


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        key_filepath,
        is_variation_2,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    init_call_id = None
    stimulus_call_id = None
    stimulus_incident_id = None

    stimulus_sip_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )

    if stimulus_sip_message:
        call_id_fields = extract_all_header_fields_matching_name_from_sip_message(
            stimulus_sip_message, "Call-ID"
        )
        if call_id_fields:
            init_call_id = clean_up_string(call_id_fields[0]).strip("Call-ID: ")
        call_id_values = extract_sip_header_values(
            stimulus_sip_message, "Call-Info", "purpose=emergency-CallId"
        )
        if call_id_values:
            stimulus_call_id = call_id_values[0]

        incident_id_values = extract_sip_header_values(
            stimulus_sip_message, "Call-Info", "purpose=emergency-IncidentId"
        )
        if incident_id_values:
            stimulus_incident_id = incident_id_values[0]

    http_collector = MessageCollectorService(
        interfaces=[
            "IF_ESRP_ADR",
            "IF_ESRP_ADR-2",
            "IF_ESRP_ADR-3",
            "IF_ESRP_LOG",
            "IF_ESRP_PS",
        ],
        pcap_service=pcap_service,
        lab_config=lab_config,
        packet_type=[PacketTypeEnum.HTTP],
    )

    adr_requests = [
        http_collector.get_requests("IF_ESRP_ADR"),
        http_collector.get_requests("IF_ESRP_ADR-2"),
        http_collector.get_requests("IF_ESRP_ADR-3"),
    ]

    adr_requests_timestamps = []
    if adr_requests:
        for interface in adr_requests:
            for record in interface:
                if (
                    hasattr(record, "http")
                    and hasattr(record.http, "request_method")
                    and record.http.request_method == "GET"
                ):
                    adr_requests_timestamps.append(float(record.sniff_timestamp))

    adr_responses = [
        http_collector.get_responses("IF_ESRP_ADR"),
        http_collector.get_responses("IF_ESRP_ADR-2"),
        http_collector.get_responses("IF_ESRP_ADR-3"),
    ]

    adr_responses_timestamps = []
    if adr_responses:
        for interface in adr_responses:
            for record in interface:
                if hasattr(record, "http"):
                    adr_responses_timestamps.append(float(record.sniff_timestamp))

    esrp_log_events = http_collector.get_requests("IF_ESRP_LOG")

    ps_response_message = None
    for pkt in http_collector.get_responses("IF_ESRP_PS"):
        if pkt:
            ps_response_message = pkt
            break

    additional_data_query_list, additional_data_response_list = (
        _extract_additional_data_logevent_list(
            esrp_log_events,
            key_filepath,
            init_call_id,
            adr_requests,
            adr_responses,
        )
    )

    return (
        stimulus_sip_message,
        ps_response_message,
        adr_requests_timestamps,
        adr_responses_timestamps,
        additional_data_query_list,
        additional_data_response_list,
        is_variation_2,
        stimulus_call_id,
        stimulus_incident_id,
        esrp_log_events,
    )


def get_test_names() -> list:
    return [
        # AdditionalDataQueryLogEvent
        "Validate ESRP sends HTTP POST 'AdditionalDataQueryLogEvent' records to /LogEvents",
        "Validate 'text' matches body of HTTP POST sent to ADR/ADR2/ADR3",
        "Validate 'uri' matches URI of the HTTP POST request sent to ADR/ADR2/ADR3",
        "Validate 'queryId' attribute is a string",
        "Validate 'queryId' is unique",
        "Validate 'direction' is set to 'outgoing'",
        "Validate 'timestamp' attribute",
        "Validate 'elementId' attribute is a valid FQDN",
        "Validate 'agencyId' attribute is a valid FQDN ",
        "Validate 'callId' attribute format in 'AdditionalDataQueryLogEvent' records",
        "Validate 'callId' in 'AdditionalDataQueryLogEvent' records matches SIP INVITE Call-Info CallId",
        "Validate 'incidentId' attribute format in 'AdditionalDataQueryLogEvent' records",
        "Validate 'incidentId' in 'AdditionalDataQueryLogEvent' matches SIP INVITE Call-Info IncidentId",
        "Validate 'callIdSip' attribute format in 'AdditionalDataQueryLogEvent'",
        "Validate 'extension' attribute in 'AdditionalDataQueryLogEvent'",
        "Validate optional attributes in 'AdditionalDataQueryLogEvent'",
        # AdditionalDataResponseLogEvent
        "Validate ESRP sends HTTP POST 'AdditionalDataResponseLogEvent' records to /LogEvents",
        "Validate 'text' matches body of HTTP POST sent to ADR/ADR2/ADR3",
        "Validate 'responseStatus' attribute",
        "Validate 'responseId' attribute is a string",
        "Validate 'direction' is set to 'incoming'",
        "Validate 'timestamp' attribute",
        "Validate 'elementId' attribute is a valid FQDN",
        "Validate 'agencyId' attribute is a valid FQDN ",
        "Validate 'callId' attribute format in 'AdditionalDataResponseLogEvent' records",
        "Validate 'callId' in 'AdditionalDataResponseLogEvent' records matches SIP INVITE Call-Info CallId",
        "Validate 'incidentId' attribute format in 'AdditionalDataResponseLogEvent' records",
        "Validate 'incidentId' in 'AdditionalDataResponseLogEvent' matches SIP INVITE Call-Info IncidentId",
        "Validate 'callIdSip' attribute format in 'AdditionalDataResponseLogEvent'",
        "Validate 'extension' attribute in 'AdditionalDataResponseLogEvent'",
        "Validate optional attributes in 'AdditionalDataResponseLogEvent'",
        "Validate the number of AdditionalDataQueryLogEvent match to AdditionalDataResponseLogEvent messages",
        "Validate the number of AdditionalDataResponseLogEvent messages messages sent to the Logging Service equals the number of Additional Data conditions",
        "Validate AdditionalDataResponseLogEvent must use a 'responseId' member that matches the 'queryId' from the AdditionalDataQueryLogEvent",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_sip_message,
        ps_response_message,
        adr_requests_timestamps,
        adr_responses_timestamps,
        additional_data_query_list,
        additional_data_response_list,
        is_variation_2,
        stimulus_call_id,
        stimulus_incident_id,
        esrp_log_events,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        # --- AdditionalDataQueryLogEvent checks ---
        TestCheck(
            test_name="Validate ESRP sends HTTP POST 'AdditionalDataQueryLogEvent' records to /LogEvents",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": additional_data_query_list,
                "error": "FAILED -> No HTTP POST 'AdditionalDataQueryLogEvent' record found",
            },
        ),
        TestCheck(
            test_name="Validate 'text' matches body of HTTP POST sent to ADR/ADR2/ADR3",
            precondition=all(
                [adr_requests_timestamps, stimulus_sip_message, ps_response_message]
            ),
            precondition_error=(
                "NOT RUN -> No stimulus/policy response message found"
                if not stimulus_sip_message or not ps_response_message
                else "FAILED -> No ESRP to ADR/ADR2/ADR3 requests found"
            ),
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "expected_data": "adr_http_post_body",
                    "actual_data": "text",
                },
                "error": "'text' in AdditionalDataQueryLogEvent does not match HTTP POST body sent to ADR",
            },
        ),
        TestCheck(
            test_name="Validate 'uri' matches URI of the HTTP POST request sent to ADR/ADR2/ADR3",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "expected_data": "uri",
                    "actual_data": "adr_uri",
                },
                "error": "'uri' in AdditionalDataQueryLogEvent does not match HTTP POST URI sent to ADR",
            },
        ),
        TestCheck(
            test_name="Validate 'queryId' attribute is a string",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_type,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "param": "query_id",
                },
                "param_name": "queryId",
                "expected_type": str,
            },
        ),
        TestCheck(
            test_name="Validate 'queryId' is unique",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": len(
                    set(
                        [log_event.query_id for log_event in additional_data_query_list]
                    )
                ),
                "expected_data": 3,
            },
        ),
        TestCheck(
            test_name="Validate 'direction' is set to 'outgoing'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "actual_data": "direction",
                },
                "expected_data": "outgoing",
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=compare_timestamps,
            test_params={
                "esrp_to_adr_timestamps": adr_requests_timestamps,
                "log_events_timestamps": [
                    logevent.timestamp for logevent in additional_data_query_list
                ],
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute is a valid FQDN",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": all(
                    True if is_valid_fqdn(logevent.element_id) else False
                    for logevent in additional_data_query_list
                ),
                "error": "FAILED -> One of logevent has 'elementId' with  invalid FQDN",
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute is a valid FQDN ",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": all(
                    True if is_valid_fqdn(logevent.agency_id) else False
                    for logevent in additional_data_query_list
                ),
                "error": "FAILED -> One of logevent has 'agency_id' with  invalid FQDN",
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute format in 'AdditionalDataQueryLogEvent' records",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": test_emergency_call_id_urn,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "emergency_call_id_header": "call_id",
                },
            },
        ),
        TestCheck(
            test_name="Validate 'callId' in 'AdditionalDataQueryLogEvent' records matches SIP INVITE Call-Info CallId",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "actual_data": "call_id",
                },
                "expected_data": stimulus_call_id,
                "error": "'callId' in AdditionalDataQueryLogEvent does not match SIP INVITE Call-Info CallId",
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute format in 'AdditionalDataQueryLogEvent' records",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": test_incident_tracking_id_urn,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "incident_tracking_id_header": "incident_id",
                },
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' in 'AdditionalDataQueryLogEvent' matches SIP INVITE Call-Info IncidentId",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "actual_data": "incident_id",
                },
                "expected_data": stimulus_incident_id,
                "error": "'incidentId' in AdditionalDataQueryLogEvent does not match SIP INVITE Call-Info IncidentId",
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute format in 'AdditionalDataQueryLogEvent'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": all(
                    (
                        True
                        if logevent.call_id_sip and bool(logevent.call_id_sip)
                        else False
                    )
                    for logevent in additional_data_query_list
                ),
                "error": "FAILED -> One of logevent has 'callIdSip' which is not a valid SIP Call-ID",
            },
        ),
        TestCheck(
            test_name="Validate 'extension' attribute in 'AdditionalDataQueryLogEvent'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_type,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "param": "extension",
                },
                "param_name": "extension",
                "expected_type": dict,
            },
        ),
        TestCheck(
            test_name="Validate optional attributes in 'AdditionalDataQueryLogEvent'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": validate_optional_log_event_fields,
                "collection": additional_data_query_list,
                "element_attrs": {
                    "raw_event": "raw_event",
                },
                "optional_string_fields": OPTIONAL_STRING_FIELDS,
            },
        ),
        # --- AdditionalDataResponseLogEvent checks ---
        TestCheck(
            test_name="Validate ESRP sends HTTP POST 'AdditionalDataResponseLogEvent' records to /LogEvents",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": additional_data_response_list,
                "error": "FAILED -> No HTTP POST 'AdditionalDataQueryLogEvent' record found",
            },
        ),
        TestCheck(
            test_name="Validate 'text' matches body of HTTP POST sent to ADR/ADR2/ADR3",
            precondition=all(
                [adr_requests_timestamps, stimulus_sip_message, ps_response_message]
            ),
            precondition_error=(
                "NOT RUN -> No stimulus/policy response message found"
                if not stimulus_sip_message or not ps_response_message
                else "FAILED -> No ESRP to ADR/ADR2/ADR3 requests found"
            ),
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "expected_data": "adr_http_post_body",
                    "actual_data": "text",
                },
                "error": "'text' in AdditionalDataQueryLogEvent does not match HTTP POST body sent to ADR",
            },
        ),
        TestCheck(
            test_name="Validate 'responseStatus' attribute",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_response_status,
            test_params={
                "additional_data_response_list": additional_data_response_list,
                "is_variation_2": is_variation_2,
            },
        ),
        TestCheck(
            test_name="Validate 'responseId' attribute is a string",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_type,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "param": "response_id",
                },
                "param_name": "responseId",
                "expected_type": str,
            },
        ),
        TestCheck(
            test_name="Validate 'direction' is set to 'incoming'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "actual_data": "direction",
                },
                "expected_data": "incoming",
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=compare_timestamps,
            test_params={
                "esrp_to_adr_timestamps": adr_responses_timestamps,
                "log_events_timestamps": [
                    logevent.timestamp for logevent in additional_data_response_list
                ],
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute is a valid FQDN",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": all(
                    True if is_valid_fqdn(logevent.element_id) else False
                    for logevent in additional_data_response_list
                ),
                "error": "FAILED -> One of logevent has 'elementId' with  invalid FQDN",
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute is a valid FQDN ",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": all(
                    True if is_valid_fqdn(logevent.agency_id) else False
                    for logevent in additional_data_response_list
                ),
                "error": "FAILED -> One of logevent has 'agency_id' with  invalid FQDN",
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute format in 'AdditionalDataResponseLogEvent' records",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": test_emergency_call_id_urn,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "emergency_call_id_header": "call_id",
                },
            },
        ),
        TestCheck(
            test_name="Validate 'callId' in 'AdditionalDataResponseLogEvent' records matches SIP INVITE Call-Info CallId",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "actual_data": "call_id",
                },
                "expected_data": stimulus_call_id,
                "error": "'callId' in AdditionalDataResponseLogEvent does not match SIP INVITE Call-Info CallId",
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute format in 'AdditionalDataResponseLogEvent' records",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": test_incident_tracking_id_urn,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "incident_tracking_id_header": "incident_id",
                },
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' in 'AdditionalDataResponseLogEvent' matches SIP INVITE Call-Info IncidentId",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "actual_data": "incident_id",
                },
                "expected_data": stimulus_incident_id,
                "error": "'incidentId' in AdditionalDataResponseLogEvent does not match SIP INVITE Call-Info IncidentId",
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute format in 'AdditionalDataResponseLogEvent'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_data_present,
            test_params={
                "test_data": all(
                    (
                        True
                        if logevent.call_id_sip and bool(logevent.call_id_sip)
                        else False
                    )
                    for logevent in additional_data_response_list
                ),
                "error": "FAILED -> One of logevent has 'callIdSip' which is not a valid SIP Call-ID",
            },
        ),
        TestCheck(
            test_name="Validate 'extension' attribute in 'AdditionalDataResponseLogEvent'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": is_type,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "param": "extension",
                },
                "param_name": "extension",
                "expected_type": dict,
            },
        ),
        TestCheck(
            test_name="Validate optional attributes in 'AdditionalDataResponseLogEvent'",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=check_each_element,
            test_params={
                "check_method": validate_optional_log_event_fields,
                "collection": additional_data_response_list,
                "element_attrs": {
                    "raw_event": "raw_event",
                },
                "optional_string_fields": OPTIONAL_STRING_FIELDS,
            },
        ),
        TestCheck(
            test_name="Validate the number of AdditionalDataQueryLogEvent match to AdditionalDataResponseLogEvent messages",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": len(additional_data_response_list),
                "expected_data": len(additional_data_query_list),
            },
        ),
        TestCheck(
            test_name="Validate the number of AdditionalDataResponseLogEvent messages messages sent to the Logging Service equals the number of Additional Data conditions",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=validate_event_count,
            test_params={
                "events": additional_data_response_list,
                "expected": EXPECTED_ADR_COUNT,
                "event_type_name": ADR_RESPONSE_LOG_EVENT_TYPE,
            },
        ),
        TestCheck(
            test_name="Validate AdditionalDataResponseLogEvent must use a 'responseId' member that matches the 'queryId' from the AdditionalDataQueryLogEvent",
            precondition=all([stimulus_sip_message, ps_response_message]),
            precondition_error="NOT RUN -> No stimulus/policy response message found",
            test_method=validate_response_id_match_to_query_id,
            test_params={
                "additional_data_response_list": additional_data_response_list,
                "additional_data_query_list": additional_data_query_list,
            },
        ),
    ]
