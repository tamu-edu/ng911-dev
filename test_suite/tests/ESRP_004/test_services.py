from services.aux_services.aux_services import get_messages, get_first_message_matching_filter
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_004.checks import validate_processing_data_by_esrp


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip,
    expected_response_code, request_method), strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_method = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                if message.get('action', None) == 'send':
                    request_method = message.get('method', None)

    if stimulus and expected_response_code and request_method:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, expected_response_code, request_method
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, expected_response_code, method = get_filter_parameters(lab_config,
                                                                                             filtering_options,
                                                                                             variation)
    message_method = [SIPMethodEnum.OPTIONS, ] if method == 'OPTIONS' else [SIPMethodEnum.INVITE, ]
    sip_message_to_esrp = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=message_method
            )
        )
    
    if not sip_message_to_esrp:
        return expected_response_code, '', []
    out_timestamp = float(sip_message_to_esrp.sniff_timestamp)
    call_id = sip_message_to_esrp.sip.get('call_id', None)

    esrp_responses = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            after_timestamp=out_timestamp,
            packet_type=PacketTypeEnum.SIP
        )
    )
    return expected_response_code, call_id, esrp_responses


def get_test_names() -> list:
    return [f"Validate processing of SIP OPTIONS and SIP CANCEL", ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        exp_response_code, call_id, esrp_resp
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Validate processing of SIP OPTIONS and SIP CANCEL",
            test_method=validate_processing_data_by_esrp,
            test_params={
                "exp_response_code": exp_response_code,
                "call_id": call_id,
                "esrp_resp": esrp_resp
            }
        )
    ]
