import json
import os

from checks.http.checks import validate_response_code, validate_response_code_class
from enums import PacketTypeEnum, HTTPMethodEnum
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from services.pcap_service import PcapCaptureService, FilterConfig
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) \
        -> tuple[str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, request_payload_path, message_method,
                                            exp_resp_code), all are strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_payload_path = None
    exp_resp_code = None
    message_method = ''

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                request_payload_path = message.get('body', None).removeprefix('file.')
                exp_resp_code = message.get('response_code', None)
                message_method = message.get('method', None)

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
            return stimulus_src_ip, stimulus_dst_ip, request_payload_path, message_method, exp_resp_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_file_path, str_message_method, expected_response_code = \
        get_filter_parameters(lab_config, filtering_options, variation)

    if str_message_method == 'POST':
        message_method = [HTTPMethodEnum.POST, ]
    else:
        message_method = [HTTPMethodEnum.PUT, ]

    if variation_file_path and os.path.exists(variation_file_path):
        with open(variation_file_path) as var_json:
            data_in_request = json.load(var_json)
    else:
        data_in_request = ''

    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=message_method
        ),
        string_in_message=str(data_in_request).replace("'", '"')
    )

    try:
        return out_message.http.response_code, expected_response_code
    except AttributeError:
        return "", expected_response_code


def get_test_names() -> list:
    return [
        "Validate 201 'Created' response for request",
        "Validate 200 'Policy Successfully Updated' response for request",
        "Validate 4xx error response for request",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (
        http_response_data, expected_response_code
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    if str(expected_response_code) == '201':
        return [
            TestCheck(
                test_name="Validate 201 'Created' response for request",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": expected_response_code,
                    "response": http_response_data
                }
            )
        ]
    elif str(expected_response_code) == '200':
        return [
            TestCheck(
                test_name="Validate 200 'Policy Successfully Updated' response for request",
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
                    "response_code": http_response_data
                }
            )
        ]
