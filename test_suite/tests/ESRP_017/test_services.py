from dataclasses import dataclass
from typing import Optional

from checks.general.checks import is_data_present, is_test_data_the_same
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_incident_tracking_id_urn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn,
)
from services.aux_services.json_services import is_valid_fqdn
from tests.ESRP_014.checks import validate_optional_log_event_fields
from tests.ESRP_017.checks import (
    validate_policy_type,
    validate_policy_id,
    validate_policy_queue_name,
    validate_timestamp,
    validate_call_id_sip,
    validate_policy_owner,
)
from tests.ESRP_017.constants import (
    EMERGENCY_CALL_ID_URN_PREFIX,
    INCIDENT_ID_URN_PREFIX,
    OPTIONAL_FIELDS,
)
from services.aux_services.message_services import (
    get_logevent_list_by_type,
)
from services.aux_services.sip_msg_body_services import (
    clean_up_string,
    is_valid_sip_uri,
)
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    extract_header_by_pattern,
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck


@dataclass
class RouteLogEventData:
    requested_policy_type: Optional[str] = None
    log_event_type: Optional[str] = None
    timestamp: Optional[str] = None
    element_id: Optional[str] = None
    agency_id: Optional[str] = None
    call_id: Optional[str] = None
    incident_id: Optional[str] = None
    call_id_sip: Optional[str] = None
    recipient_uri: Optional[str] = None
    policy_owner: Optional[str] = None
    policy_type: Optional[str] = None
    policy_id: Optional[list] = None
    policy_queue_name: Optional[str] = None
    raw_event: Optional[str] = None


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

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message
            header_contains = message.header_contains
        elif message.message_type == FilterMessageType.OTHER:
            other = message

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
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_src_ip is None
            or out_dst_ip is None
            or other_src_ip is None
            or other_dst_ip is None
            or key_filepath is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
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
        )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required parameters for filtering"
        )


def _extract_route_log_event_data(
    http_post_to_logger, key_filepath, init_call_id, requested_policy_type
) -> RouteLogEventData:
    log_event_list = get_logevent_list_by_type(
        http_post_to_logger,
        "RouteLogEvent",
        key_filepath,
        init_call_id,
    )
    if not log_event_list:
        return RouteLogEventData(requested_policy_type=requested_policy_type)

    event = log_event_list[0]
    return RouteLogEventData(
        # Required
        requested_policy_type=requested_policy_type,
        log_event_type=event.get("logEventType"),
        timestamp=event.get("timestamp"),
        element_id=event.get("elementId"),
        agency_id=event.get("agencyId"),
        recipient_uri=event.get("recipientUri"),
        policy_owner=event.get("policyOwner"),
        policy_type=event.get("policyType"),
        # Optional
        policy_id=event.get("policyId"),
        call_id=event.get("callId"),
        incident_id=event.get("incidentId"),
        call_id_sip=event.get("callIdSip"),
        policy_queue_name=event.get("policyQueueName"),
        raw_event=event,
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
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_sip_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )
    # Resolve Call-ID, Call-Info URNs and receipt timestamp from the stimulus SIP INVITE
    init_call_id = None
    init_timestamp = None
    sip_call_info_call_id = None
    sip_call_info_incident_id = None
    if stimulus_sip_message:
        if hasattr(stimulus_sip_message, "sniff_timestamp"):
            try:
                init_timestamp = float(stimulus_sip_message.sniff_timestamp)
            except (TypeError, ValueError):
                init_timestamp = None
        call_id_fields = extract_all_header_fields_matching_name_from_sip_message(
            stimulus_sip_message, "Call-ID"
        )
        if call_id_fields:
            init_call_id = clean_up_string(call_id_fields[0]).strip("Call-ID: ")
        call_info_fields = extract_all_header_fields_matching_name_from_sip_message(
            stimulus_sip_message, "Call-Info"
        )
        for raw_field in call_info_fields or []:
            cleaned = clean_up_string(raw_field)
            # strip the leading "Call-Info:" label if present
            if ":" in cleaned:
                _, _, cleaned = cleaned.partition(":")
                cleaned = cleaned.strip()
            if sip_call_info_call_id is None:
                sip_call_info_call_id = extract_header_by_pattern(
                    cleaned, EMERGENCY_CALL_ID_URN_PREFIX
                )
            if sip_call_info_incident_id is None:
                sip_call_info_incident_id = extract_header_by_pattern(
                    cleaned, INCIDENT_ID_URN_PREFIX
                )

    # Collect all HTTP POSTs from ESRP to the logger
    if key_filepath == "":
        print(
            "⚠️ WARNING: The ESRP 'certificate_key' value is set to '' (empty line). "
            "There is a risk that message payload may not be decoded."
        )
    http_posts_to_logger = list(
        pcap_service.get_messages_by_config(
            FilterConfig(
                src_ip=out_src_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
            )
        )
    )

    route_log_event_data = _extract_route_log_event_data(
        http_posts_to_logger, key_filepath, init_call_id, variation.name
    )

    return (
        stimulus_sip_message,
        route_log_event_data,
        init_timestamp,
        init_call_id,
        sip_call_info_call_id,
        sip_call_info_incident_id,
    )


def get_test_names() -> list:
    return [
        "Validate ESRP sends HTTP POST RouteLogEvent to /LogEvents",
        "Validate 'logEventType' attribute value in 'RouteLogEvent'",
        "Validate 'timestamp' attribute format and match with SIP INVITE",
        "Validate 'elementId' attribute value in 'RouteLogEvent'",
        "Validate 'agencyId' attribute value in 'RouteLogEvent'",
        "Validate 'callId' attribute value in 'RouteLogEvent'",
        "Validate 'callId' attribute matches SIP INVITE Call-Info CallId",
        "Validate emergency Call Identifier String ID",
        "Validate Emergency Call Identifier FQDN",
        "Validate 'incidentId' attribute value in 'RouteLogEvent'",
        "Validate Incident Tracking Identifier String ID",
        "Validate Incident Tracking Identifier FQDN",
        "Validate 'incidentId' attribute matches SIP INVITE Call-Info IncidentId",
        "Validate 'callIdSip' attribute value in 'RouteLogEvent'",
        "Validate 'recipientUri' attribute value in 'RouteLogEvent'",
        "Validate 'policyOwner' attribute value in 'RouteLogEvent'",
        "Validate 'policyType' attribute value in 'RouteLogEvent'",
        "Validate 'policyId' (optional) attribute value in 'RouteLogEvent'",
        "Validate 'policyQueueName' (optional) attribute value in 'RouteLogEvent'",
        "Validate optional fields and values in 'RouteLogEvent'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_sip_message,
        route_log_event_data,
        init_timestamp,
        init_call_id,
        sip_call_info_call_id,
        sip_call_info_incident_id,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Validate ESRP sends HTTP POST RouteLogEvent to /LogEvents",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find Stimulus message/response from Policy Store",
            test_method=is_data_present,
            test_params={
                "test_data": route_log_event_data.log_event_type,
                "error": "FAILED -> No HTTP POST 'RouteLogEvent' found",
            },
        ),
        TestCheck(
            test_name="Validate 'logEventType' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": route_log_event_data.log_event_type,
                "expected_data": "RouteLogEvent",
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute format and match with SIP INVITE",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=validate_timestamp,
            test_params={
                "fe_timestamp": route_log_event_data.timestamp,
                "init_timestamp": init_timestamp,
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(route_log_event_data.element_id),
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(route_log_event_data.agency_id),
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": route_log_event_data.call_id,
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute matches SIP INVITE Call-Info CallId",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": route_log_event_data.call_id,
                "expected_data": sip_call_info_call_id,
            },
        ),
        TestCheck(
            test_name="Validate emergency Call Identifier String ID",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_emergency_call_id_string_id,
            test_params={
                "emergency_call_id_header": route_log_event_data.call_id,
            },
        ),
        TestCheck(
            test_name="Validate Emergency Call Identifier FQDN",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": route_log_event_data.call_id,
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_incident_tracking_id_urn,
            test_params={
                "incident_tracking_id_header": route_log_event_data.incident_id,
            },
        ),
        TestCheck(
            test_name="Validate Incident Tracking Identifier String ID",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_incident_tracking_id_string_id,
            test_params={
                "incident_tracking_id_header": route_log_event_data.incident_id,
            },
        ),
        TestCheck(
            test_name="Validate Incident Tracking Identifier FQDN",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_incident_tracking_id_fqdn,
            test_params={
                "incident_tracking_id_header": route_log_event_data.incident_id,
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute matches SIP INVITE Call-Info IncidentId",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": route_log_event_data.incident_id,
                "expected_data": sip_call_info_incident_id,
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=validate_call_id_sip,
            test_params={
                "call_id_sip": route_log_event_data.call_id_sip,
                "sip_call_id": init_call_id,
            },
        ),
        TestCheck(
            test_name="Validate 'recipientUri' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_sip_uri(route_log_event_data.recipient_uri),
            },
        ),
        TestCheck(
            test_name="Validate 'policyOwner' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            test_method=validate_policy_owner,
            test_params={
                "policy_owner": route_log_event_data.policy_owner,
            },
        ),
        TestCheck(
            test_name="Validate 'policyType' attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            test_method=validate_policy_type,
            test_params={
                "policy_type": route_log_event_data.policy_type,
            },
        ),
        TestCheck(
            test_name="Validate 'policyId' (optional) attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            test_method=validate_policy_id,
            test_params={
                "policy_type": route_log_event_data.policy_type,
                "policy_id": route_log_event_data.policy_id,
            },
        ),
        TestCheck(
            test_name="Validate 'policyQueueName' (optional) attribute value in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            test_method=validate_policy_queue_name,
            test_params={
                "policy_type": route_log_event_data.policy_type,
                "policy_queue_name": route_log_event_data.policy_queue_name,
            },
        ),
        TestCheck(
            test_name="Validate optional fields and values in 'RouteLogEvent'",
            precondition=stimulus_sip_message,
            test_method=validate_optional_log_event_fields,
            test_params={
                "raw_event": route_log_event_data.raw_event,
                "optional_fields": OPTIONAL_FIELDS,
            },
        ),
    ]
