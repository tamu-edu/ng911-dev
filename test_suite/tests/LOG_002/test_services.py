from checks.http.checks import validate_response_code_class
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, variation_url, expected_response_code),
    strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    variation_url = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                variation_url = message.get('http_url', None)
                expected_response_code = message.get('response_code', None)

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
            return stimulus_src_ip, stimulus_dst_ip, variation_url, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_url, expected_response_code = (
        get_filter_parameters(lab_config, filtering_options, variation))

    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.GET, ]
        ),
        uri=variation_url
    )
    try:
        message_response_code = out_message.http.response_code
    except AttributeError:
        return '', expected_response_code
    return message_response_code, expected_response_code


def get_test_names() -> list:
    return [f"Validate Logger 4XX response code for request.", ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter],
                  variation: RunVariation) -> list:
    (
        response_code, expected_response_code
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name=f"Validate Logger 4XX response code for request.",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": expected_response_code,
                "response": response_code
            }
        )
    ]
