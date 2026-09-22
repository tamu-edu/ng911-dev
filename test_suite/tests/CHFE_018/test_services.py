from checks.general.checks import is_data_present, is_test_data_the_same
from checks.log_events.constants import CALL_STATES_REGISTRY
from checks.log_events.log_event_services import (
    get_jws_payloads_list_by_log_event_type,
    validate_log_event_timestamp,
    validate_optional_log_event_fields,
)
from checks.log_events.log_events import CallStateChangeLogEvent
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_incident_tracking_id_urn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
)
from services.aux_services.json_services import is_valid_fqdn
from services.aux_services.sip_msg_body_services import (
    clean_up_string,
    is_valid_sip_call_id,
)
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.run_config import MessageFilter, RunVariation
from services.message_collector_service import MessageCollectorService
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.aux_services.aux_services import (
    extract_header_by_pattern,
)
from enums import PacketTypeEnum
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.INTEROP_001.test_services import _first_by_method


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (chfe_fqdn, key_filepath)
    """
    key_filepath = None
    output = None

    iut_entity = lab_config.get_conformance_iut_entity()
    chfe_fqdn = iut_entity.get_first_available_fqdn()

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.OUTPUT:
            output = message

    if output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == output.src_interface:
                    key_filepath = entity.certificate_key

    if chfe_fqdn is None:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )
    return (
        chfe_fqdn,
        key_filepath,
    )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):

    variations = {
        "CallStateChangeLogEvent_for_adding_party_to_the_conference": 1,
        "CallStateChangeLogEvent_for_removing_party_from_the_conference": 2,
    }

    if variation.name in variations:
        variation_number = variations.get(variation.name)
    else:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    (
        chfe_fqdn,
        key_filepath,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    # Resolve Call-ID, Call-Info URNs and receipt timestamp from the stimulus SIP INVITE
    init_call_id = None
    init_timestamp = None
    # Var 1: CHFE moves BCF call into conference -> partyAdd/outgoing
    # Var 2: CHFE is dropped from conference by BRIDGE -> partyRemove/incoming
    expected_call_state = "partyAdd" if variation_number == 1 else "partyRemove"
    expected_direction = "outgoing" if variation_number == 1 else "incoming"
    sip_call_info_call_id = None
    sip_call_info_incident_id = None
    sip_call_info_call_id_sip = None
    bridge_call_id = None
    bridge_uri = None

    sip_collector = MessageCollectorService(
        interfaces=[
            "IF_ESRP_CHFE",
            "IF_CHFE_BRIDGE",
            "IF_BRIDGE_BCF",
            "IF_BRIDGE_CHFE",
        ],
        pcap_service=pcap_service,
        lab_config=lab_config,
        packet_type=[PacketTypeEnum.SIP],
    )

    http_collector = MessageCollectorService(
        interfaces=[
            "IF_CHFE_LOG",
        ],
        pcap_service=pcap_service,
        lab_config=lab_config,
        packet_type=[PacketTypeEnum.HTTP],
    )

    esrp_to_chfe = sip_collector.get_requests("IF_ESRP_CHFE")
    bridge_to_chfe = sip_collector.get_requests("IF_BRIDGE_CHFE")
    bridge_to_bcf = sip_collector.get_requests("IF_BRIDGE_BCF")
    chfe_to_bridge = sip_collector.get_requests("IF_CHFE_BRIDGE")

    # Variation 1 - SIP INVITE from Test System ESRP
    # Variation 2 - SIP INVITE from Test System BRIDGE
    if variation_number == 1:
        stimulus_sip_message = _first_by_method(esrp_to_chfe, "INVITE")
    else:
        stimulus_sip_message = _first_by_method(bridge_to_chfe, "INVITE")

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
            # expected callId/incidentId for the LogEvent come from the Call-Info
            # URNs on the same initial INVITE (TD_CHFE_018 Response, callId/incidentId bullets)
            if sip_call_info_call_id is None:
                sip_call_info_call_id = extract_header_by_pattern(
                    cleaned, "urn:emergency:uid:callid:"
                )
            if sip_call_info_incident_id is None:
                sip_call_info_incident_id = extract_header_by_pattern(
                    cleaned, "urn:emergency:uid:incidentid:"
                )

    if key_filepath == "":
        print(
            "⚠️ WARNING: The ESRP 'certificate_key' value is set to '' (empty line). "
            "There is a risk that message payload may not be decoded."
        )

    if variation_number == 1:
        # legCallId/targetId (var 1) come from the BRIDGE->BCF INVITE that
        # pulls the BCF leg into the conference
        request_for_leg_and_target_id = _first_by_method(bridge_to_bcf, "INVITE")
        if request_for_leg_and_target_id:
            bridge_call_id = request_for_leg_and_target_id.sip.get("call_id")
            bridge_uri = request_for_leg_and_target_id.sip.get("r_uri")
    else:
        # legCallId/targetId (var 2) are fixed values from the scenario XML,
        # matching the <call-id>/entity of the TS-CHFE <user> in the SIP NOTIFY body
        bridge_call_id = "tschfeconferencecallid@ts-chfe.ng911.test.example"
        bridge_uri = "sip:TS-CHFE@ts-chfe.ng911.test.example:5060"

    http_posts_to_logger = http_collector.get_requests("IF_CHFE_LOG")

    log_events_payload_list = get_jws_payloads_list_by_log_event_type(
        http_posts_to_logger, "CallStateChangeLogEvent", key_filepath
    )

    call_state_change_log_events_list = [
        CallStateChangeLogEvent(log_event) for log_event in log_events_payload_list
    ]
    call_state_change_log_event = (
        call_state_change_log_events_list[0]
        if call_state_change_log_events_list
        else CallStateChangeLogEvent()
    )

    if variation_number == 1:
        # expected callIdSip (var 1) is the Call-ID of the CHFE->BRIDGE INVITE.
        # Var 2 has no separate CHFE->BRIDGE INVITE, so this check is skipped
        # (precondition below requires sip_call_info_call_id_sip to be set)
        req = _first_by_method(chfe_to_bridge, "INVITE")
    else:
        req = _first_by_method(bridge_to_chfe, "INVITE")
    if req:
        sip_call_info_call_id_sip = req.sip.get("call_id", None)

    return (
        stimulus_sip_message,
        call_state_change_log_event,
        chfe_fqdn,
        init_timestamp,
        init_call_id,
        bridge_call_id,
        bridge_uri,
        expected_call_state,
        expected_direction,
        sip_call_info_call_id,
        sip_call_info_incident_id,
        sip_call_info_call_id_sip,
    )


def get_test_names() -> list:
    return [
        "Validate ESRP sends HTTP POST CallStateChangeLogEvent to /LogEvents",
        "Validate 'logEventType' attribute value in 'CallStateChangeLogEvent'",
        "Validate 'timestamp' attribute format and match with SIP INVITE",
        "Validate 'elementId' attribute value in 'CallStateChangeLogEvent'",
        "Validate 'elementId' attribute has value of CHFE FQDN",
        "Validate 'agencyId' attribute value in 'CallStateChangeLogEvent'",
        "Validate 'callId' attribute value in 'CallStateChangeLogEvent'",
        "Validate 'callId' attribute matches SIP INVITE Call-Info CallId",
        "Validate emergency Call Identifier String ID",
        "Validate Emergency Call Identifier FQDN",
        "Validate 'incidentId' attribute value in 'CallStateChangeLogEvent'",
        "Validate Incident Tracking Identifier String ID",
        "Validate Incident Tracking Identifier FQDN",
        "Validate 'incidentId' attribute matches SIP INVITE Call-Info IncidentId",
        "Validate 'callIdSip' attribute value in 'CallStateChangeLogEvent' is valid",
        "Validate 'callIdSip' attribute value in 'CallStateChangeLogEvent' matches Call-ID in the SIP INVITE with BRIDGE",
        "Validate optional fields type in 'CallStateChangeLogEvent'",
        "Validate 'state' attribute value in 'CallStateChangeLogEvent'",
        "Validate 'state' attribute has expected value",
        "Validate 'direction' attribute value in 'CallStateChangeLogEvent'",
        "Validate 'legCallId'(optional) attribute value in 'CallStateChangeLogEvent'",
        "Validate 'targetId'(optional) attribute value in 'CallStateChangeLogEvent'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_sip_message,
        call_state_change_log_event,
        chfe_fqdn,
        init_timestamp,
        init_call_id,
        bridge_call_id,
        bridge_uri,
        expected_call_state,
        expected_direction,
        sip_call_info_call_id,
        sip_call_info_incident_id,
        sip_call_info_call_id_sip,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Validate ESRP sends HTTP POST CallStateChangeLogEvent to /LogEvents",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find Stimulus message/response from Policy Store",
            test_method=is_data_present,
            test_params={
                "test_data": call_state_change_log_event.logEventType,
                "error": "FAILED -> No HTTP POST 'CallStateChangeLogEvent' found",
            },
        ),
        TestCheck(
            test_name="Validate 'logEventType' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.logEventType,
                "expected_data": "CallStateChangeLogEvent",
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute format and match with SIP INVITE",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=validate_log_event_timestamp,
            test_params={
                "actual_timestamp": call_state_change_log_event.timestamp,
                "expected_timestamp": init_timestamp,
                "timestamp_threshold": 3,
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(call_state_change_log_event.elementId),
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute has value of CHFE FQDN",
            precondition=all([stimulus_sip_message, chfe_fqdn]),
            precondition_error="NOT RUN -> Cannot find response from Stimulus message or CHFE FQDN",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.elementId,
                "expected_data": chfe_fqdn,
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": is_valid_fqdn(call_state_change_log_event.agencyId),
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": call_state_change_log_event.callId,
            },
        ),
        TestCheck(
            test_name="Validate 'callId' attribute matches SIP INVITE Call-Info CallId",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.callId,
                "expected_data": sip_call_info_call_id,
            },
        ),
        TestCheck(
            test_name="Validate emergency Call Identifier String ID",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_emergency_call_id_string_id,
            test_params={
                "emergency_call_id_header": call_state_change_log_event.callId,
            },
        ),
        TestCheck(
            test_name="Validate Emergency Call Identifier FQDN",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": call_state_change_log_event.callId,
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_incident_tracking_id_urn,
            test_params={
                "incident_tracking_id_header": call_state_change_log_event.incidentId,
            },
        ),
        TestCheck(
            test_name="Validate Incident Tracking Identifier String ID",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_incident_tracking_id_string_id,
            test_params={
                "incident_tracking_id_header": call_state_change_log_event.incidentId,
            },
        ),
        TestCheck(
            test_name="Validate Incident Tracking Identifier FQDN",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=test_incident_tracking_id_fqdn,
            test_params={
                "incident_tracking_id_header": call_state_change_log_event.incidentId,
            },
        ),
        TestCheck(
            test_name="Validate 'incidentId' attribute matches SIP INVITE Call-Info IncidentId",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.incidentId,
                "expected_data": sip_call_info_incident_id,
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute value in 'CallStateChangeLogEvent' is valid",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": bool(call_state_change_log_event.callIdSip)
                and is_valid_sip_call_id(call_state_change_log_event.callIdSip),
                "error": f"FAILED -> 'callIdSip' is not a valid SIP Call-ID: '{call_state_change_log_event.callIdSip}'",
            },
        ),
        TestCheck(
            test_name="Validate 'callIdSip' attribute value in 'CallStateChangeLogEvent' matches Call-ID in the SIP INVITE with BRIDGE",
            precondition=all([stimulus_sip_message, sip_call_info_call_id_sip]),
            precondition_error="NOT RUN -> Cannot find response from Stimulus message or BRIDGE SIP INVITE",
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.callIdSip,
                "expected_data": str(sip_call_info_call_id_sip),
            },
        ),
        TestCheck(
            test_name="Validate optional fields type in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            precondition_error="NOT RUN -> Cannot find response from Stimulus message",
            test_method=validate_optional_log_event_fields,
            test_params={
                "log_event_class": call_state_change_log_event,
            },
        ),
        TestCheck(
            test_name="Validate 'state' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            test_method=is_data_present,
            test_params={
                "test_data": call_state_change_log_event.state in CALL_STATES_REGISTRY
            },
        ),
        TestCheck(
            test_name="Validate 'state' attribute has expected value",
            precondition=stimulus_sip_message,
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.state,
                "expected_data": expected_call_state,
            },
        ),
        TestCheck(
            test_name="Validate 'direction' attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.direction,
                "expected_data": expected_direction,
            },
        ),
        TestCheck(
            test_name="Validate 'legCallId'(optional) attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.legCallId,
                "expected_data": str(bridge_call_id),
            },
        ),
        TestCheck(
            test_name="Validate 'targetId'(optional) attribute value in 'CallStateChangeLogEvent'",
            precondition=stimulus_sip_message,
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": call_state_change_log_event.targetId,
                "expected_data": str(bridge_uri),
            },
        ),
    ]
