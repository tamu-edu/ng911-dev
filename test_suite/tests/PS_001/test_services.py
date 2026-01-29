import json
import os

from checks.http.checks import validate_response_code_class, validate_response_code
from enums import PacketTypeEnum
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
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, response_code, http_url,
                                            variation_file_path), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    response_code = None
    http_url = None
    variation_file_path = None

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                http_url = message.get('http_url', None)
                response_code = message.get('response_code', None)
                variation_file_path = message.get('body', None).removeprefix('file.')

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip

        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required parameters")
        else:
            return stimulus_src_ip, stimulus_dst_ip, response_code, http_url, variation_file_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, expected_response_code, http_url, variation_file_path = (
        get_filter_parameters(lab_config, filtering_options, variation))

    if variation_file_path and os.path.exists(variation_file_path):
        with open(variation_file_path) as var_json:
            data_in_request = json.load(var_json)
    else:
        data_in_request = ''

    message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP
        ),
        string_in_message=str(data_in_request).replace("'", '"')
    )

    try:
        return message.http.response_code, expected_response_code
    except AttributeError:
        return "", expected_response_code


def get_test_names() -> list:
    return ["Verify Policy Store sends 4XX response code.",
            "Verify Policy Store sends '201 - Policy Successfully Created'."]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:

    response_code, expected_response_code = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if expected_response_code == "4xx":
        return [
            TestCheck(
                test_name="Verify Policy Store sends 4XX response code.",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": expected_response_code,
                    "response_code": response_code
                }
            )
        ]
    else:
        return [
            TestCheck(
                test_name="Verify Policy Store sends '201 - Policy Successfully Created'.",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": expected_response_code,
                    "response": response_code
                }
            )
        ]
