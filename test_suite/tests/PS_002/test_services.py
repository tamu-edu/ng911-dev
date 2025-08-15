from checks.http.checks import validate_response_code, validate_response_code_class
from enums import PacketTypeEnum
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.aux_services.json_services import get_payload_data_from_file
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from services.pcap_service import PcapCaptureService, FilterConfig
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, request_uri, request_payload_path,
    variation_name, exp_resp_code), all are strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_url = None
    request_payload_path = None
    exp_resp_code = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                request_payload_path = message.get('body', None).removeprefix('file.')
                request_url = message.get('http_url', None)
                exp_resp_code = message.get('response_code', None)

    if stimulus and request_url and request_payload_path:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip,  request_url, request_payload_path, variation.name, exp_resp_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, uri, payload_path, variation_name, expected_response_code = \
        get_filter_parameters(lab_config, filtering_options, variation)
    payload = get_payload_data_from_file(payload_path, 'plain')

    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP
        ),
        string_in_message=payload
    )
    response_code = out_message.http.response_code if out_message and hasattr(out_message, 'http') else out_message
    return response_code, variation_name, expected_response_code


def get_test_names() -> list:
    return [
         f"Validate 201 Created response for request",
         f"Validate 4xx error response for request",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        http_response_data, variation_name, expected_response_code
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    if str(expected_response_code) in '201':
        return [
            TestCheck(
                test_name="Validate 201 Created response for request",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": expected_response_code,
                    "response": http_response_data
                }
            )
        ]
    else:
        return [
            TestCheck(
                test_name="Validate 4xx error response for request",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": expected_response_code,
                    "response": http_response_data
                }
            )
        ]
