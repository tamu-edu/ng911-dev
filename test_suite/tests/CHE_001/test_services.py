from services.aux_services.aux_services import get_messages
from services.aux_services.message_services import get_sip_response_by_attribute_and_attr_value
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHE_001.checks import verify_http_held, verify_sip_subscribe


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, request_method, expected_response_code),
    strings
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
                if message.get('action', None) == 'receive':
                    request_method = message.get('method', None)

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
            return stimulus_src_ip, stimulus_dst_ip, request_method, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple or None:
    stimulus_src_ip, stimulus_dst_ip, request_method, expected_response_code = \
        get_filter_parameters(lab_config, filtering_options, variation)

    out_response = get_sip_response_by_attribute_and_attr_value(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        ),
        'geolocation'
    )
    geolocation = None
    che_responses = []
    if not out_response:
        return che_responses, geolocation, request_method

    if getattr(out_response, 'sip', None):
        geolocation = out_response.sip.get('geolocation', None)

    if request_method == 'POST':
        packet_type = PacketTypeEnum.HTTP
    else:
        packet_type = PacketTypeEnum.SIP

    messages_after_timestamp = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            packet_type=packet_type,
            after_timestamp=float(out_response.sniff_timestamp)
        )
    )
    return messages_after_timestamp, geolocation, request_method


def get_test_names() -> list:
    return [
         f"Validate HTTP POST sent to LIS after receiving SIP INVITE (HELD)",
         f"Validate SIP SUBSCRIBE sent to LIS after receiving SIP INVITE (SIP Presence Event Package)",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        http_response_codes_or_response_data, invite_geolocation, variation_method
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if "POST" in variation_method:
        return [
            TestCheck(
                test_name="Validate HTTP POST sent to LIS after receiving SIP INVITE (HELD)",
                test_method=verify_http_held,
                test_params={
                    "response": http_response_codes_or_response_data,
                    "geolocation": invite_geolocation
                }
            )
            ]
    else:
        return [
            TestCheck(
                test_name="Validate SIP SUBSCRIBE sent to LIS after receiving SIP INVITE (SIP Presence Event Package)",
                test_method=verify_sip_subscribe,
                test_params={
                    "response": http_response_codes_or_response_data,
                    "geolocation": invite_geolocation
                }
            )
        ]
