from checks.http.checks import validate_response_code
from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_012.checks import (
    check_subscribe_with_element_state_event_sent,
    check_subscribe_with_service_state_event_sent,
    check_notify_200_ok_for_each_received_notify,
    check_all_notify_element_state_values_valid,
    check_element_state_change_observed,
    check_all_notify_messages_have_json_body,
    check_all_notify_element_id_is_valid_fqdn,
    check_all_notify_element_state_field_present,
    check_all_notify_element_reason_is_string,
    check_all_notify_service_state_values_valid,
    check_all_notify_service_object_present,
    check_all_notify_service_name_is_esrp,
    check_all_notify_service_id_is_valid_fqdn,
    check_all_notify_service_domain_is_valid_fqdn,
    check_all_notify_service_state_object_present,
    check_all_notify_service_state_value_present,
    check_all_notify_service_state_value_is_valid,
    check_all_notify_service_state_reason_is_string,
    check_all_notify_security_posture_field_present,
    check_all_notify_security_posture_value_is_valid,
    get_event,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (esrp_fe_src_ip, esrp_fe_dst_ip), strings
    """
    stimulus = None
    esrp_fe_src_ip = None
    esrp_fe_dst_ip = None
    state_type = None

    for message in filtering_options:
        # Variation 2/3
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            state_type = message.header_contains
        # Variation #1
        elif (
            message.message_type == FilterMessageType.OTHER
            and message.sip_method == "NOTIFY"
            and message.header_contains == "emergency-ServiceState"
        ):
            stimulus = message
            state_type = "BOTH"

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    esrp_fe_dst_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    esrp_fe_src_ip = interface.ip
        missing = [
            name
            for name, val in [
                ("esrp_fe_src_ip", esrp_fe_src_ip),
                ("esrp_fe_dst_ip", esrp_fe_dst_ip),
                ("state_type", state_type),
            ]
            if val is None
        ]
        if missing:
            raise WrongConfigurationError(
                f"Lab Config file error - the following are None: {', '.join(missing)}"
            )
        else:
            return esrp_fe_src_ip, esrp_fe_dst_ip, state_type
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
):

    esrp_fe_src_ip, esrp_fe_dst_ip, state_type = get_filter_parameters(
        lab_config, filtering_options
    )

    sip_subscribe_element_state_message = None
    sip_subscribe_service_state_message = None
    sip_notify_messages = []
    sip_notify_ok_messages = []
    sip_subscribe_message_ok = None

    ###### Variation #1 ######
    if state_type == "BOTH":
        sip_subscribe_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=esrp_fe_src_ip,
                dst_ip=esrp_fe_dst_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.SUBSCRIBE,
                ],
            ),
        )

        for message in sip_subscribe_messages:
            if hasattr(message.sip, "msg_hdr") and hasattr(message.sip, "event"):
                subscribe_event = message.sip.get("event")
                if "emergency-ElementState" in subscribe_event:
                    sip_subscribe_element_state_message = message
                elif "emergency-ServiceState" in subscribe_event:
                    sip_subscribe_service_state_message = message

        if sip_subscribe_element_state_message:
            sip_notify_messages = get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=esrp_fe_dst_ip,
                    dst_ip=esrp_fe_src_ip,
                    packet_type=PacketTypeEnum.SIP,
                    message_method=[
                        SIPMethodEnum.NOTIFY,
                    ],
                    after_timestamp=float(
                        sip_subscribe_element_state_message.sniff_timestamp
                    ),
                ),
            )

    ###### Variation #2/3 ######
    else:
        sip_subscribe_from_bcf = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=esrp_fe_dst_ip,
                dst_ip=esrp_fe_src_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.SUBSCRIBE,
                ],
            ),
        )

        if sip_subscribe_from_bcf:
            subscribe_response = get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=esrp_fe_src_ip,
                    dst_ip=esrp_fe_dst_ip,
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=float(sip_subscribe_from_bcf.sniff_timestamp),
                ),
            )

            for message in subscribe_response:
                if hasattr(message.sip, "status_code") and hasattr(
                    message.sip, "cseq_method"
                ):
                    if (
                        message.sip.status_code == "200"
                        and message.sip.cseq_method == "SUBSCRIBE"
                    ):
                        sip_subscribe_message_ok = message.sip.status_code
                        break

            sip_notify_messages = get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=esrp_fe_src_ip,
                    dst_ip=esrp_fe_dst_ip,
                    packet_type=PacketTypeEnum.SIP,
                    message_method=[
                        SIPMethodEnum.NOTIFY,
                    ],
                    after_timestamp=float(sip_subscribe_from_bcf.sniff_timestamp),
                ),
            )

            sip_notify_messages = [
                message
                for message in sip_notify_messages
                if hasattr(message, "sip")
                and hasattr(message.sip, "event")
                and get_event(message)
                in ["emergency-ElementState", "emergency-ServiceState"]
            ]

    if sip_notify_messages:
        if state_type == "BOTH":
            src = esrp_fe_src_ip
            dst = esrp_fe_dst_ip
        else:
            src = esrp_fe_dst_ip
            dst = esrp_fe_src_ip

        sip_notify_ok_response_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=src,
                dst_ip=dst,
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=float(sip_notify_messages[0].sniff_timestamp),
            ),
        )

        for message in sip_notify_ok_response_messages:
            if hasattr(message.sip, "status_code") and hasattr(
                message.sip, "cseq_method"
            ):
                if (
                    message.sip.status_code == "200"
                    and message.sip.cseq_method == "NOTIFY"
                ):
                    sip_notify_ok_messages.append(message)

    return (
        # For variation #1
        sip_subscribe_element_state_message,
        sip_subscribe_service_state_message,
        # For variations #2/3
        sip_notify_messages,
        sip_notify_ok_messages,
        sip_subscribe_message_ok,
        state_type,
    )


def get_test_names() -> list:
    return [
        # Variation 1
        "Validate ESRP sends SIP SUBSCRIBE with event emergency-ElementState",
        "Validate ESRP sends SIP SUBSCRIBE with event emergency-ServiceState",
        "Validate ESRP responds with SIP 200 OK for each received SIP NOTIFY",
        # Variation 2 & 3 (shared)
        "Validate ESRP responds with SIP 200 OK to SIP SUBSCRIBE",
        "Validate all SIP NOTIFY messages contain JSON body",
        # Variation 2
        "Validate all SIP NOTIFY messages carry valid 'elementState' value",
        "Validate ESRP reports element state change across SIP NOTIFY messages",
        "Validate all SIP NOTIFY messages contain valid FQDN in elementId",
        "Validate all SIP NOTIFY messages contain 'state' field in JSON body",
        "Validate SIP NOTIFY messages contain valid 'reason'(optional) field Type",
        # Variation 3
        "Validate all SIP NOTIFY messages carry valid 'serviceState' value",
        "Validate all SIP NOTIFY messages contain 'service' object in JSON Body",
        "Validate all SIP NOTIFY messages contain 'name' ESRP",
        "Validate all SIP NOTIFY messages contain valid FQDN in 'serviceId'(optional)",
        "Validate all SIP NOTIFY messages contain valid FQDN in 'domain'",
        "Validate all SIP NOTIFY messages contain 'serviceState' object in JSON body",
        "Validate all SIP NOTIFY messages contain 'state' field in 'serviceState'",
        "Validate all SIP NOTIFY messages contain valid 'state' value in 'serviceState'",
        "Validate all SIP NOTIFY messages contain valid 'reason'(optional) field type in 'serviceState'",
        "Validate all SIP NOTIFY messages contain 'posture' field in 'securityPosture'",
        "Validate all SIP NOTIFY messages contain valid 'posture' value in 'securityPosture'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:

    (
        sip_subscribe_element_state_message,
        sip_subscribe_service_state_message,
        sip_notify_messages,
        sip_notify_ok_messages,
        sip_subscribe_message_ok,
        state_type,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)

    # Variation #1
    if state_type == "BOTH":
        return [
            TestCheck(
                test_name="Validate ESRP sends SIP SUBSCRIBE with event emergency-ElementState",
                test_method=check_subscribe_with_element_state_event_sent,
                test_params={
                    "sip_subscribe_element_state_message": sip_subscribe_element_state_message,
                },
            ),
            TestCheck(
                test_name="Validate ESRP sends SIP SUBSCRIBE with event emergency-ServiceState",
                test_method=check_subscribe_with_service_state_event_sent,
                test_params={
                    "sip_subscribe_service_state_message": sip_subscribe_service_state_message,
                },
            ),
            TestCheck(
                test_name="Validate ESRP responds with SIP 200 OK for each received SIP NOTIFY",
                test_method=check_notify_200_ok_for_each_received_notify,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                    "sip_notify_ok_messages": sip_notify_ok_messages,
                },
            ),
        ]
    # Variation #2
    elif state_type == "emergency-ElementState":
        return [
            TestCheck(
                test_name="Validate ESRP responds with SIP 200 OK to SIP SUBSCRIBE",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": "200",
                    "response": sip_subscribe_message_ok,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages carry valid 'elementState' value",
                test_method=check_all_notify_element_state_values_valid,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate ESRP reports element state change across SIP NOTIFY messages",
                test_method=check_element_state_change_observed,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain JSON body",
                test_method=check_all_notify_messages_have_json_body,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain valid FQDN in elementId",
                test_method=check_all_notify_element_id_is_valid_fqdn,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain 'state' field in JSON body",
                test_method=check_all_notify_element_state_field_present,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate SIP NOTIFY messages contain valid 'reason'(optional) field Type",
                test_method=check_all_notify_element_reason_is_string,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
        ]
    # Variation #3
    else:
        return [
            TestCheck(
                test_name="Validate ESRP responds with SIP 200 OK to SIP SUBSCRIBE",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": "200",
                    "response": sip_subscribe_message_ok,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages carry valid 'serviceState' value",
                test_method=check_all_notify_service_state_values_valid,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain JSON body",
                test_method=check_all_notify_messages_have_json_body,
                test_params={
                    "sip_notify_messages": sip_notify_messages,
                },
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain 'service' object in JSON Body",
                test_method=check_all_notify_service_object_present,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain 'name' ESRP",
                test_method=check_all_notify_service_name_is_esrp,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain valid FQDN in 'serviceId'(optional)",
                test_method=check_all_notify_service_id_is_valid_fqdn,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain valid FQDN in 'domain'",
                test_method=check_all_notify_service_domain_is_valid_fqdn,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain 'serviceState' object in JSON body",
                test_method=check_all_notify_service_state_object_present,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain 'state' field in 'serviceState'",
                test_method=check_all_notify_service_state_value_present,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain valid 'state' value in 'serviceState'",
                test_method=check_all_notify_service_state_value_is_valid,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain valid "
                "'reason'(optional) field type in 'serviceState'",
                test_method=check_all_notify_service_state_reason_is_string,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain 'posture' field in 'securityPosture'",
                test_method=check_all_notify_security_posture_field_present,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
            TestCheck(
                test_name="Validate all SIP NOTIFY messages contain valid 'posture' value in 'securityPosture'",
                test_method=check_all_notify_security_posture_value_is_valid,
                test_params={"sip_notify_messages": sip_notify_messages},
            ),
        ]
