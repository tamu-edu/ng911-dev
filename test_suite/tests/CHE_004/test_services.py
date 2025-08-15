from services.aux_services.aux_services import get_first_message_matching_filter
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.types.test_config import Test as TestConfig
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHE_004.checks import validate_che_callbacks_and_outbound


def get_filter_parameters(lab_config: LabConfig,
                          filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, message_method), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    message_method = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                if not message_method:
                    message_method = message.get('action', None)

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, message_method
    else:
        raise WrongConfigurationError("It seems that the RunConfig does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_method = get_filter_parameters(lab_config, filtering_options,
                                                                               variation)

    sip_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
            )
        )
    # VARIATION 1
    if variation_method == 'send':
        response_from_che = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[SIPMethodEnum.INVITE, ]
            )
        )
    else:
        # VARIATION 2
        response_from_che = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[SIPMethodEnum.INVITE, ]
            )
        )
    return sip_invite_message, response_from_che, variation_method


def get_test_names() -> list:
    return [f"SIP INVITE for callbacks and other outbound calls", ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        sip_invite_to_che, che_response, variation_method
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name='SIP INVITE for callbacks and other outbound calls',
            test_method=validate_che_callbacks_and_outbound,
            test_params={
                "sip_invite_to_che": sip_invite_to_che,
                "che_response": che_response,
                "variation_method": variation_method,
            }
        )
    ]
