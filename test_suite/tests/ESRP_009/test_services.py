from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_messages
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_005.checks import (
    validate_log_post_presence,
    validate_iut_sip_forwarding,
    validate_log_event_by_sip_type,
    validate_direction,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip, other_src_ip, other_dst_ip,
                    header_contains, sip_method)
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
    sip_method = None
    header_contains = None
    # No response-code validation anymore

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            sip_method = message.sip_method
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
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_src_ip,
                out_dst_ip,
                other_src_ip,
                other_dst_ip,
                header_contains,
                sip_method,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    if filtering_options:
        for opt in filtering_options:
            print(
                f" - message_type={opt.message_type}, src={opt.src_interface}, dst={opt.dst_interface}"
            )
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        sip_method,
        header_contains,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_sip_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, SIPMethodEnum.MESSAGE],
        ),
    )
    esrp_sip_inviete_to_chfe = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=other_src_ip,
            dst_ip=other_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, SIPMethodEnum.MESSAGE],
        ),
    )

    http_post_requests = list(
        pcap_service.get_messages_by_config(
            FilterConfig(
                src_ip=out_src_ip,  # BCF LOG interface IP
                dst_ip=out_dst_ip,  # LOG side IP
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
                header_part=header_contains,
            )
        )
    )
    return (
        stimulus_sip_messages,
        esrp_sip_inviete_to_chfe,
        http_post_requests,
        sip_method,
    )


def get_test_names() -> list:
    return [
        "Validate ESRP sends HTTP POST to /LogEvents",
        "Validate ESRP send SIP CHFE",
        "Validate Log Event depends on SIP MESSAGE",
        "Validate Log Event depends on SIP Other message type",
        "Validate Log Event direction values",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_sip_messages,
        esrp_sip_inviete_to_chfe,
        http_post_requests,
        sip_method,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    checks = [
        TestCheck(
            test_name="Validate ESRP sends HTTP POST to /LogEvents",
            test_method=validate_log_post_presence,
            test_params={"http_post_requests": http_post_requests},
        ),
        TestCheck(
            test_name="Validate ESRP send SIP CHFE",
            test_method=validate_iut_sip_forwarding,
            test_params={"iut_output_messages": esrp_sip_inviete_to_chfe},
        ),
        TestCheck(
            test_name="Validate Log Event direction values",
            test_method=validate_direction,
            test_params={"http_post_requests": http_post_requests},
        ),
    ]
    test_name = (
        "Validate Log Event depends on SIP MESSAGE"
        if sip_method and str(sip_method).upper() == "MESSAGE"
        else "Validate Log Event depends on SIP Other message type"
    )
    checks.append(
        TestCheck(
            test_name=test_name,
            test_method=validate_log_event_by_sip_type,
            test_params={
                "http_post_requests": http_post_requests,
                "sip_message_type": sip_method,
            },
        )
    )

    return checks
