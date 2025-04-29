from checks.http.checks import validate_response_code
from services.aux.aux_services import get_messages, get_first_message_matching_filter
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_conduction_service import TestCheck
from tests.CHE_002.constants import VARIATION_DESCRIPTIONS


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        if hasattr(message, 'response_status_code'):
            expected_response_code = message.response_status_code

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, variation.name, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> list:
    stimulus_src_ip, stimulus_dst_ip, variation_name, expected_response_code = get_filter_parameters(lab_config,
                                                                                                     filtering_options,
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

    out_timestamp = float(sip_invite_message.sniff_timestamp)
    call_id = sip_invite_message.sip.get('call_id')

    if out_timestamp:
        messages_after_timestamp = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                message_method=[SIPMethodEnum.INVITE, ],
                after_timestamp=out_timestamp
            )
        )
    else:
        return [None, int(expected_response_code), variation_name]

    for out_message in messages_after_timestamp:
        if (out_message.sip.status_code == expected_response_code and
                out_message.sip.get('call_id') == call_id):
            return [out_message.sip.status_code, int(expected_response_code), variation_name]
    return [None, int(expected_response_code), variation_name]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        response_code, expected_response_code, variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name=VARIATION_DESCRIPTIONS.get(variation_name, variation_name),
            test_method=validate_response_code,
            test_params={
                "response_code": response_code,
                "expected_response_code": expected_response_code
            }
        )
    ]
