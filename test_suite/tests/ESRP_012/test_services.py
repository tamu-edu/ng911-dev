from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.aux_services.sip_msg_body_services import (
    extract_header_field_value_from_raw_body,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_012.checks import (
    validate_element_state_and_service_state,
    validate_element_state_and_updating_status,
    validate_server_side_of_service_state,
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
        if esrp_fe_src_ip is None or esrp_fe_dst_ip is None or state_type is None:
            raise WrongConfigurationError(
                "Lab Config file error - src and dst ip addresses not found"
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
    sip_subscribe_from_bcf = None
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
            if hasattr(message.sip, "msg_hdr") and hasattr(
                message.sip.msg_hdr, "event"
            ):
                subscribe_event = extract_header_field_value_from_raw_body(
                    "Event", message.sip.msg_hdr
                )
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
            if sip_notify_messages:
                sip_notify_ok_response_messages = get_messages(
                    pcap_service,
                    FilterConfig(
                        src_ip=esrp_fe_src_ip,
                        dst_ip=esrp_fe_dst_ip,
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
                        sip_subscribe_message_ok = message
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
    return (
        sip_subscribe_element_state_message,
        sip_subscribe_service_state_message,
        sip_notify_messages,
        sip_notify_ok_messages,
        sip_subscribe_from_bcf,
        sip_subscribe_message_ok,
        state_type,
    )


def get_test_names() -> list:
    return [
        "Validate Client-side of ElementState + ServiceState for downstream ESRP",
        "Validate Server-side of ElementState + updating status",
        "Validate Server-side of ServiceState",
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
        sip_subscribe_from_bcf,
        sip_subscribe_message_ok,
        state_type,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)

    # Variation #1
    if state_type == "BOTH":
        return [
            TestCheck(
                test_name="Validate Client-side of ElementState + ServiceState for downstream ESRP",
                test_method=validate_element_state_and_service_state,
                test_params={
                    "sip_subscribe_element_state_message": sip_subscribe_element_state_message,
                    "sip_subscribe_service_state_message": sip_subscribe_service_state_message,
                    "sip_notify_messages": sip_notify_messages,
                    "sip_notify_ok_messages": sip_notify_ok_messages,
                },
            )
        ]
    # Variation #2
    elif state_type == "emergency-ServiceState":
        return [
            TestCheck(
                test_name="Validate Server-side of ElementState + updating status",
                test_method=validate_element_state_and_updating_status,
                test_params={
                    "sip_subscribe_from_bcf": sip_subscribe_from_bcf,
                    "sip_subscribe_message_ok": sip_subscribe_message_ok,
                    "sip_notify_messages": sip_notify_messages,
                },
            )
        ]
    # Variation #3
    else:
        return [
            TestCheck(
                test_name="Validate Server-side of ServiceState",
                test_method=validate_server_side_of_service_state,
                test_params={
                    "sip_subscribe_from_bcf": sip_subscribe_from_bcf,
                    "sip_subscribe_message_ok": sip_subscribe_message_ok,
                    "sip_notify_messages": sip_notify_messages,
                },
            )
        ]
