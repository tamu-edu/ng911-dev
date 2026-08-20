from dataclasses import dataclass
from typing import Optional

from checks.general.checks import is_data_present, is_test_data_the_same
from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_fqdn,
    test_emergency_call_id_urn,
    test_incident_tracking_id_urn,
)
from services.aux_services.json_services import is_valid_fqdn
from services.aux_services.message_services import (
    get_logevent_list_by_type,
    extract_all_contents_from_message_body,
)
from services.aux_services.sip_msg_body_services import (
    clean_up_string,
    is_valid_sip_call_id,
)
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
    extract_sip_header_values,
)
from services.aux_services.xml_services import is_valid_xml
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_014.checks import (
    validate_timestamp,
    validate_optional_log_event_fields,
    validate_response_direction,
    validate_malformed_response,
)
from tests.ESRP_014.constants import (
    MALFORMED_RESPONSE_BODY_FILE,
    OPTIONAL_STRING_FIELDS,
)


@dataclass
class LostQueryEventData:
    log_event_list: Optional[list] = None
    xml_from_esrp_to_ecrf: Optional[str] = None
    xml_from_esrp_to_logger: Optional[str] = None
    direction: Optional[str] = None
    query_id: Optional[str] = None
    timestamp: Optional[str] = None
    element_id: Optional[str] = None
    agency_id: Optional[str] = None
    call_id: Optional[str] = None
    incident_id: Optional[str] = None
    call_id_sip: Optional[str] = None
    extension: Optional[str] = None
    raw_event: Optional[dict] = None
    ecrf_response: Optional[float] = None


@dataclass
class LostResponseEventData:
    log_event_list: Optional[list] = None
    response_adapter: Optional[str] = None
    direction: Optional[str] = None
    response_id: Optional[str] = None
    malformed_response: Optional[str] = None
    timestamp: Optional[str] = None
    element_id: Optional[str] = None
    agency_id: Optional[str] = None
    call_id: Optional[str] = None
    incident_id: Optional[str] = None
    call_id_sip: Optional[str] = None
    extension: Optional[str] = None
    raw_event: Optional[dict] = None
    ecrf_response: Optional[float] = None


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip, other_src_ip, other_dst_ip,
                    header_contains, key_filepath, lost_url)
    """
    stimulus = None
    output = None
    other = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_src_ip = None
    out_dst_ip = None
    other_src_ip = None
    other_dst_ip = None
    header_contains = None
    key_filepath = None
    lost_url = None
    is_variation_2 = False

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message
            header_contains = message.header_contains
        elif message.message_type == FilterMessageType.OTHER:
            other = message

    for message in variation.params["messages"]:
        if all(
            (
                message.get("action", None) == "receive",
                MALFORMED_RESPONSE_BODY_FILE in message.get("body", ""),
            )
        ):
            is_variation_2 = True

    if stimulus and output and other:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                    key_filepath = entity.certificate_key
                elif interface.name == output.src_interface:
                    out_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
                elif interface.name == other.src_interface:
                    other_src_ip = interface.ip
                elif interface.name == other.dst_interface:
                    other_dst_ip = interface.ip
                    if (
                        hasattr(entity, "api_http_url_prefix")
                        and entity.api_http_url_prefix
                    ):
                        lost_url = entity.api_http_url_prefix
        missing = [
            name
            for name, value in (
                ("stimulus_src_ip", stimulus_src_ip),
                ("stimulus_dst_ip", stimulus_dst_ip),
                ("out_src_ip", out_src_ip),
                ("out_dst_ip", out_dst_ip),
                ("other_src_ip", other_src_ip),
                ("other_dst_ip", other_dst_ip),
                ("lost_url", lost_url),
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
            out_src_ip,
            out_dst_ip,
            other_src_ip,
            other_dst_ip,
            header_contains,
            key_filepath,
            lost_url,
            is_variation_2,
        )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required parameters for filtering"
        )


def _extract_lost_query_event_data(
    http_post_to_logger,
    key_filepath,
    init_call_id,
    xml_from_esrp_to_ecrf,
    ecrf_response,
) -> LostQueryEventData:
    log_event_list = get_logevent_list_by_type(
        http_post_to_logger, "LostQueryLogEvent", key_filepath, init_call_id
    )
    if not log_event_list:
        return LostQueryEventData(xml_from_esrp_to_ecrf=xml_from_esrp_to_ecrf)

    event = log_event_list[0]
    return LostQueryEventData(
        log_event_list=log_event_list,
        xml_from_esrp_to_ecrf=xml_from_esrp_to_ecrf,
        xml_from_esrp_to_logger=clean_up_string(event.get("queryAdapter"), is_xml=True),
        direction=event.get("direction"),
        query_id=event.get("queryId"),
        timestamp=event.get("timestamp"),
        element_id=event.get("elementId"),
        agency_id=event.get("agencyId"),
        call_id=event.get("callId"),
        incident_id=event.get("incidentId"),
        call_id_sip=event.get("callIdSip"),
        extension=event.get("extension"),
        raw_event=event,
        ecrf_response=ecrf_response,
    )


def _extract_lost_response_event_data(
    http_post_to_logger, key_filepath, init_call_id, ecrf_response
) -> LostResponseEventData:
    log_event_list = get_logevent_list_by_type(
        http_post_to_logger, "LostResponseLogEvent", key_filepath, init_call_id
    )
    if not log_event_list:
        return LostResponseEventData()

    event = log_event_list[0]
    return LostResponseEventData(
        log_event_list=log_event_list,
        response_adapter=clean_up_string(event.get("responseAdapter"), is_xml=True),
        direction=event.get("direction"),
        response_id=event.get("responseId"),
        malformed_response=event.get("malformedResponse"),
        timestamp=event.get("timestamp"),
        element_id=event.get("elementId"),
        agency_id=event.get("agencyId"),
        call_id=event.get("callId"),
        incident_id=event.get("incidentId"),
        call_id_sip=event.get("callIdSip"),
        extension=event.get("extension"),
        raw_event=event,
        ecrf_response=ecrf_response,
    )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        header_contains,
        key_filepath,
        lost_url,
        is_variation_2,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    # Resolve Call-ID, callId, incidentId and timestamp from the stimulus SIP INVITE
    init_call_id = None
    ecrf_response = None
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

    # Extract LoST query XML sent from ESRP to ECRF (used for content comparison)
    xml_from_esrp_to_ecrf = None
    esrp_to_ecrf_msg = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_src_ip,
            dst_ip=other_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST],
            header_part=lost_url,
        ),
    )
    if esrp_to_ecrf_msg:
        for body in extract_all_contents_from_message_body(esrp_to_ecrf_msg):
            if is_valid_xml(body["body"]):
                xml_from_esrp_to_ecrf = clean_up_string(body["body"], is_xml=True)

    # Collect all HTTP POSTs from ESRP to the logger
    if key_filepath == "":
        print(
            "⚠️ WARNING: The ESRP 'certificate_key' value is set to '' (empty line). "
            "There is a risk that message payload may not be decoded."
        )

    ecrf_to_esrp_msg_response = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_dst_ip,
            dst_ip=other_src_ip,
            packet_type=PacketTypeEnum.HTTP,
            http_status_code=201,
        ),
    )
    if ecrf_to_esrp_msg_response:
        if hasattr(stimulus_sip_message, "sniff_timestamp"):
            ecrf_response = float(stimulus_sip_message.sniff_timestamp)

    http_post_to_logger = list(
        pcap_service.get_messages_by_config(
            FilterConfig(
                src_ip=out_src_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
                header_part=header_contains,
            )
        )
    )

    lost_query_data = _extract_lost_query_event_data(
        http_post_to_logger,
        key_filepath,
        init_call_id,
        xml_from_esrp_to_ecrf,
        ecrf_response,
    )

    lost_response_data = _extract_lost_response_event_data(
        http_post_to_logger, key_filepath, init_call_id, ecrf_response
    )

    return (
        lost_query_data,
        lost_response_data,
        is_variation_2,
        stimulus_call_id,
        stimulus_incident_id,
    )


def get_test_names() -> list:
    return [
        # LostQueryLogEvent
        "Validate ESRP sends HTTP POST 'LostQueryLogEvent' to /LogEvents",
        "Validate 'queryAdapter' string is present in 'LostQueryLogEvent'",
        "Validate 'queryAdapter' matches LoST query XML sent to ECRF",
        "Validate 'direction' attribute value in 'LostQueryLogEvent'",
        "Validate 'queryId' attribute is a string",
        "Validate 'timestamp' attribute format and value in 'LostQueryLogEvent'",
        "Validate 'elementId' attribute is a valid FQDN in 'LostQueryLogEvent'",
        "Validate 'agencyId' attribute is a valid FQDN in 'LostQueryLogEvent'",
        "Validate 'callId' attribute format in 'LostQueryLogEvent'",
        "Validate 'callId' in 'LostQueryLogEvent' matches SIP INVITE Call-Info CallId",
        "Validate 'incidentId' attribute format in 'LostQueryLogEvent'",
        "Validate 'incidentId' in 'LostQueryLogEvent' matches SIP INVITE Call-Info IncidentId",
        "Validate 'callIdSip' attribute format in 'LostQueryLogEvent'",
        "Validate 'extension' attribute in 'LostQueryLogEvent'",
        "Validate optional attributes in 'LostQueryLogEvent'",
        # LostResponseLogEvent
        "Validate ESRP sends HTTP POST 'LostResponseLogEvent' to /LogEvents",
        "Validate 'responseAdapter' string is present in 'LostResponseLogEvent'",
        "Validate 'direction' attribute value in 'LostResponseLogEvent'",
        "Validate 'responseId' attribute is a string",
        "Validate 'malformedResponse' attribute in 'LostResponseLogEvent'",
        "Validate 'responseId' matches 'queryId' from 'LostQueryLogEvent'",
        "Validate 'timestamp' attribute format and value in 'LostResponseLogEvent'",
        "Validate 'elementId' attribute is a valid FQDN in 'LostResponseLogEvent'",
        "Validate 'agencyId' attribute is a valid FQDN in 'LostResponseLogEvent'",
        "Validate 'callId' attribute format in 'LostResponseLogEvent'",
        "Validate 'callId' in 'LostResponseLogEvent' matches SIP INVITE Call-Info CallId",
        "Validate 'incidentId' attribute format in 'LostResponseLogEvent'",
        "Validate 'incidentId' in 'LostResponseLogEvent' matches SIP INVITE Call-Info IncidentId",
        "Validate 'callIdSip' attribute format in 'LostResponseLogEvent'",
        "Validate 'extension' attribute in 'LostResponseLogEvent'",
        "Validate optional attributes in 'LostResponseLogEvent'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        lost_query_data,
        lost_response_data,
        is_variation_2,
        stimulus_call_id,
        stimulus_incident_id,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        # --- LostQueryLogEvent checks ---
        TestCheck(
            test_name="Validate ESRP sends HTTP POST 'LostQueryLogEvent' to /LogEvents",
            test_method=is_data_present,
            test_params={
                "test_data": lost_query_data.log_event_list,
                "error": "FAILED -> No HTTP POST 'LostQueryLogEvent' found",
            },
        ),
        TestCheck(
            test_name="Validate 'queryAdapter' string is present in 'LostQueryLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": lost_query_data.xml_from_esrp_to_logger,
                "error": "FAILED -> No 'queryAdapter' found in JWS",
            },
        ),
        TestCheck(
            test_name="Validate 'queryAdapter' matches LoST query XML sent to ECRF",
            precondition=lost_query_data.xml_from_esrp_to_ecrf,
            precondition_error="FAILED -> No ESRP to ECRF LoST message found",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": lost_query_data.xml_from_esrp_to_ecrf,
                "actual_data": lost_query_data.xml_from_esrp_to_logger,
            },
        ),
        TestCheck(
            test_name="Validate 'direction' attribute value in 'LostQueryLogEvent'",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": "outgoing",
                "actual_data": lost_query_data.direction,
            },
        ),
        TestCheck(
            test_name="Validate 'queryId' attribute is a string",
            test_method=is_type,
            test_params={
                "param": lost_query_data.query_id,
                "param_name": "queryId",
                "expected_type": str,
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute format and value in 'LostQueryLogEvent'",
            test_method=validate_timestamp,
            test_params={
                "actual_timestamp": lost_query_data.timestamp,
                "expected_timestamp": lost_query_data.ecrf_response,
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute is a valid FQDN in 'LostQueryLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(lost_query_data.element_id),
                "error": f"FAILED -> 'elementId' is not a valid FQDN: '{lost_query_data.element_id}'",
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute is a valid FQDN in 'LostQueryLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(lost_query_data.agency_id),
                "error": f"FAILED -> 'agencyId' is not a valid FQDN: '{lost_query_data.agency_id}'",
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute format in 'LostQueryLogEvent'",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": lost_query_data.call_id,
            },
        ),
        TestCheck(
            test_name="Validate 'callId' in 'LostQueryLogEvent' matches SIP INVITE Call-Info CallId",
            precondition=stimulus_call_id,
            precondition_error="NOT RUN -> No stimulus Call-Id found",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": stimulus_call_id,
                "actual_data": lost_query_data.call_id,
                "error": "'callId' in LostQueryLogEvent does not match SIP INVITE Call-Info CallId",
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute format in 'LostQueryLogEvent'",
            test_method=test_incident_tracking_id_urn,
            test_params={
                "incident_tracking_id_header": lost_query_data.incident_id,
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' in 'LostQueryLogEvent' matches SIP INVITE Call-Info IncidentId",
            precondition=stimulus_incident_id,
            precondition_error="NOT RUN -> No stimulus Incident-Id found",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": stimulus_incident_id,
                "actual_data": lost_query_data.incident_id,
                "error": "'incidentId' in LostQueryLogEvent does not match SIP INVITE Call-Info IncidentId",
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute format in 'LostQueryLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": bool(lost_query_data.call_id_sip)
                and is_valid_sip_call_id(lost_query_data.call_id_sip),
                "error": f"FAILED -> 'callIdSip' is not a valid SIP Call-ID: '{lost_query_data.call_id_sip}'",
            },
        ),
        TestCheck(
            test_name="Validate 'extension' attribute in 'LostQueryLogEvent'",
            test_method=is_type,
            test_params={
                "param": lost_query_data.extension,
                "param_name": "extension",
                "expected_type": dict,
            },
        ),
        TestCheck(
            test_name="Validate optional attributes in 'LostQueryLogEvent'",
            test_method=validate_optional_log_event_fields,
            test_params={
                "raw_event": lost_query_data.raw_event,
                "optional_string_fields": OPTIONAL_STRING_FIELDS,
            },
        ),
        # --- LostResponseLogEvent checks ---
        TestCheck(
            test_name="Validate ESRP sends HTTP POST 'LostResponseLogEvent' to /LogEvents",
            test_method=is_data_present,
            test_params={
                "test_data": lost_response_data.log_event_list,
                "error": "FAILED -> No HTTP POST 'LostResponseLogEvent' found",
            },
        ),
        TestCheck(
            test_name="Validate 'responseAdapter' string is present in 'LostResponseLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": lost_response_data.response_adapter,
                "error": "FAILED -> No 'responseAdapter' found in JWS",
            },
        ),
        TestCheck(
            test_name="Validate 'direction' attribute value in 'LostResponseLogEvent'",
            test_method=validate_response_direction,
            test_params={
                "direction": lost_response_data.direction,
            },
        ),
        TestCheck(
            test_name="Validate 'responseId' attribute is a string",
            test_method=is_type,
            test_params={
                "param": lost_response_data.response_id,
                "param_name": "responseId",
                "expected_type": str,
            },
        ),
        TestCheck(
            test_name="Validate 'malformedResponse' attribute in 'LostResponseLogEvent'",
            test_method=validate_malformed_response,
            test_params={
                "field_value": lost_response_data.malformed_response,
                "field_name": "malformedResponse",
                "is_required": is_variation_2,
            },
        ),
        TestCheck(
            test_name="Validate 'responseId' matches 'queryId' from 'LostQueryLogEvent'",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": lost_query_data.query_id,
                "actual_data": lost_response_data.response_id,
                "error": "'responseId' in LostResponseLogEvent does not match 'queryId' in LostQueryLogEvent",
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute format and value in 'LostResponseLogEvent'",
            test_method=validate_timestamp,
            test_params={
                "actual_timestamp": lost_response_data.timestamp,
                "expected_timestamp": lost_response_data.ecrf_response,
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute is a valid FQDN in 'LostResponseLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(lost_response_data.element_id),
                "error": f"FAILED -> 'elementId' is not a valid FQDN: '{lost_response_data.element_id}'",
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute is a valid FQDN in 'LostResponseLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(lost_response_data.agency_id),
                "error": f"FAILED -> 'agencyId' is not a valid FQDN: '{lost_response_data.agency_id}'",
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute format in 'LostResponseLogEvent'",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": lost_response_data.call_id,
            },
        ),
        TestCheck(
            test_name="Validate 'callId' in 'LostResponseLogEvent' matches SIP INVITE Call-Info CallId",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": stimulus_call_id,
                "actual_data": lost_response_data.call_id,
                "error": "'callId' in LostResponseLogEvent does not match SIP INVITE Call-Info CallId",
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute format in 'LostResponseLogEvent'",
            test_method=test_incident_tracking_id_fqdn,
            test_params={
                "incident_tracking_id_header": lost_response_data.incident_id,
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' in 'LostResponseLogEvent' matches SIP INVITE Call-Info IncidentId",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": stimulus_incident_id,
                "actual_data": lost_response_data.incident_id,
                "error": "'incidentId' in LostResponseLogEvent does not match SIP INVITE Call-Info IncidentId",
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute format in 'LostResponseLogEvent'",
            test_method=is_data_present,
            test_params={
                "test_data": bool(lost_response_data.call_id_sip)
                and is_valid_sip_call_id(lost_response_data.call_id_sip),
                "error": f"FAILED -> 'callIdSip' is not a valid SIP Call-ID: '{lost_response_data.call_id_sip}'",
            },
        ),
        TestCheck(
            test_name="Validate 'extension' attribute in 'LostResponseLogEvent'",
            test_method=is_type,
            test_params={
                "param": lost_response_data.extension,
                "param_name": "extension",
                "expected_type": dict,
            },
        ),
        TestCheck(
            test_name="Validate optional attributes in 'LostResponseLogEvent'",
            test_method=validate_optional_log_event_fields,
            test_params={
                "raw_event": lost_response_data.raw_event,
                "optional_string_fields": OPTIONAL_STRING_FIELDS,
            },
        ),
    ]
