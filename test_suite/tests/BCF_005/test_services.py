from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_messages
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_005.checks import validate_log_post_presence, validate_bcf_sip_forwarding, validate_log_event_by_sip_type, validate_direction
from tests.BCF_005.constants import LOG_EVENTS_URI, TEST_NAMES


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) \
        -> tuple[str, str, str, str]:
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip)
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_src_ip = None
    out_dst_ip = None
    # No response-code validation anymore

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
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
        if stimulus_src_ip is None or stimulus_dst_ip is None or out_src_ip is None or out_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required parameters for IP addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple:
    if filtering_options:
        for opt in filtering_options:
            print(f" - message_type={opt.message_type}, src={opt.src_interface}, dst={opt.dst_interface}")
    stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip = (
        get_filter_parameters(lab_config, filtering_options, variation))
    stimulus_sip_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, SIPMethodEnum.MESSAGE]
        )
    )
    bcf_output_sip_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_src_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, SIPMethodEnum.MESSAGE]
        )
    )
    log_src_ip = None
    log_dst_ip = None
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            if interface.name == "IF_BCF_LOG":
                log_src_ip = interface.ip
            elif interface.name == "IF_LOG_BCF":
                log_dst_ip = interface.ip

    http_post_requests = list(pcap_service.get_messages_by_config(
        FilterConfig(
            src_ip=log_src_ip,  # BCF LOG interface IP
            dst_ip=log_dst_ip,  # LOG side IP
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST],
            header_part=LOG_EVENTS_URI
        )
    ))
    return stimulus_sip_messages, bcf_output_sip_messages, http_post_requests


def get_test_names() -> list:
    return TEST_NAMES


def _determine_sip_method(variation: RunVariation, bcf_output_sip_messages: list = None) -> str:
    """
    Determine the SIP method for a test variation.
    
    Args:
        variation: RunVariation instance containing test variation data
        bcf_output_sip_messages: List of SIP messages from BCF output (optional)
        
    Returns:
        str: Determined SIP method (e.g., 'MESSAGE', 'INVITE') or None if cannot be determined
    """
    var_hint = None
    var_name = getattr(variation, 'name', None) or getattr(variation, 'id', None)
    if var_name:
        upper_name = str(var_name).upper()
        if 'MESSAGE' in upper_name:
            var_hint = 'MESSAGE'
        elif 'INVITE' in upper_name:
            var_hint = 'INVITE'

    if bcf_output_sip_messages:
        methods = [
            str(msg.sip.method).upper()
            for msg in bcf_output_sip_messages
            if hasattr(msg, 'sip') and hasattr(msg.sip, 'method') and msg.sip.method is not None
        ]
        if methods:
            return var_hint or ('MESSAGE' if 'MESSAGE' in methods else methods[0])
    
    return var_hint


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (
        stimulus_sip_messages,
        bcf_output_sip_messages,
        http_post_requests,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    checks = [
        TestCheck(
            test_name=TEST_NAMES[0],
            test_method=validate_log_post_presence,
            test_params={
                "http_post_requests": http_post_requests
            }
        ),
        TestCheck(
            test_name=TEST_NAMES[1],
            test_method=validate_bcf_sip_forwarding,
            test_params={
                "bcf_output_messages": bcf_output_sip_messages
            }
        ),
        TestCheck(
            test_name=TEST_NAMES[4],
            test_method=validate_direction,
            test_params={
                "http_post_requests": http_post_requests
            }
        )
    ]
    sip_method = _determine_sip_method(variation, bcf_output_sip_messages)
    test_name = TEST_NAMES[2] if sip_method and str(sip_method).upper() == 'MESSAGE' else TEST_NAMES[3]
    checks.append(
        TestCheck(
            test_name=test_name,
            test_method=validate_log_event_by_sip_type,
            test_params={
                "http_post_requests": http_post_requests,
                "sip_message_type": sip_method
            }
        )
    )

    return checks