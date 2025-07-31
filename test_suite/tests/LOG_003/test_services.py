from checks.http.checks import validate_response_code_class, validate_response_code
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.aux_services.json_services import get_payload_data_from_file
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LOG_003.constants import VARIATIONS_WITH_HTTP_201


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, variation_name, request_payload_path),
    all are strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_payload_path = None
    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                request_payload_path = message.get('body', None).removeprefix('file.')

    if stimulus and request_payload_path:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip,  variation.name, request_payload_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_name, payload_path = get_filter_parameters(lab_config,
                                                                                           filtering_options,
                                                                                           variation)

    payload = get_payload_data_from_file(payload_path, 'plain')
    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST, ]
        ),
        str(payload),
    )
    if variation_name in VARIATIONS_WITH_HTTP_201:
        return out_message, variation_name
    else:
        try:
            response_code = out_message.http.response_code
            return response_code, variation_name
        except AttributeError:
            return '', variation_name


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        http_response_codes_or_response_data, variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if variation_name in VARIATIONS_WITH_HTTP_201:
        return [
            TestCheck(
                test_name="Validate 201 success response code for request",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": 201,
                    "response": http_response_codes_or_response_data
                }
            )
        ]
    else:
        return [
            TestCheck(
                test_name="Validate 4xx error response code class for request",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": 400,
                    "response": http_response_codes_or_response_data
                }
            )
        ]
