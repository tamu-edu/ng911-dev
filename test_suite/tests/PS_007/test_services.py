from checks.http.checks import validate_response_code_class
from services.aux_services.json_services import get_payload_data_from_file
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.message_services import get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, variation_file_path,
    message_method, expected_response_code), strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    message_method = None
    variation_file_path = None

    send_fo, recieve_fo = filtering_options
    if send_fo.message_type == FilterMessageType.STIMULUS.value:
        stimulus = send_fo

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                message_method = record.get('method', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    for param in variation.params:
        if param == 'messages':
            for message in variation.params[param]:
                for prep in message['prep_steps']:
                    if prep['method_name'] == 'generate_jws':
                        variation_file_path = prep.get('save_result_as', None).removeprefix("file.")

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
            return stimulus_src_ip, stimulus_dst_ip, variation_file_path, message_method, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_file_path, message_method, expected_response_code = (
        get_filter_parameters(lab_config, filtering_options, variation))

    data_in_request = get_payload_data_from_file(variation_file_path, 'plain')
    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST, ] if message_method == 'POST' else [HTTPMethodEnum.PUT, ]
        ),
        data_in_request
    )
    if not out_message:
        return '', expected_response_code

    response_code = out_message.http.response_code if hasattr(out_message, 'http') else out_message
    return response_code, expected_response_code


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options: list[MessageFilter],
                  variation: RunVariation) -> list:
    (
        response_code,
        expected_response_code
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name=f"Validate 4xx error response.",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": expected_response_code,
                "response": response_code
            }
        ),
    ]
