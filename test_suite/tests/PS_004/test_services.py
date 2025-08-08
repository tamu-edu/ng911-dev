from checks.http.checks import validate_response_code_class
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.message_services import get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from tests.PS_004.checks import validate_policy_store_response_body


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str, str, str]:
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
    variation_name = variation.name
    variation_url = None
    message_method = None

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
                variation_url = message.get('http_url', None)
                message_method = message.get('method', None)

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
            return (stimulus_src_ip, stimulus_dst_ip, variation_name, variation_url, message_method,
                    expected_response_code)
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_name, variation_url, message_method, expected_response_code = (
        get_filter_parameters(lab_config, filtering_options, variation))

    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP
        ),
        uri=variation_url
    )
    if variation_name == "Request_with_correct_data_matching_policies_stored":
        return True, out_message, variation_name, expected_response_code

    response_code = out_message.http.response_code if out_message and hasattr(out_message, 'http') else out_message
    return False, response_code, variation_name, expected_response_code


def get_test_names() -> list:
    return [
         f"Validate 4xx error response code is sent.",
         f"Validate response message.",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter],
                  variation: RunVariation) -> list:
    (
        ok_response_variation,
        test_response,
        variation_name,
        expected_response_code
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if not ok_response_variation:
        return [
            TestCheck(
                test_name=f"Validate 4xx error response code is sent.",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": expected_response_code,
                    "response": test_response
                }
            ),
            ]
    else:
        return [
            TestCheck(
                test_name=f"Validate response message.",
                test_method=validate_policy_store_response_body,
                test_params={
                    "response": test_response
                }
            )
        ]

