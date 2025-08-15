from checks.http.checks import validate_response_code_class
from enums import PacketTypeEnum
from services.aux_services.aux_services import check_value_for_file_var_mode
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.aux_services.json_services import get_payload_data_from_file
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from services.pcap_service import PcapCaptureService, FilterConfig
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) \
        -> tuple[str, str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    variation_name = variation.name
    variation_method = None
    response_code = None
    http_url = None

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                variation_method = message.get('method', None)
                http_url = message.get('http_url', None)
                response_code = message.get('response_code', None)

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
            return (stimulus_src_ip,
                    stimulus_dst_ip,
                    variation_name,
                    variation_method,
                    response_code,
                    http_url)
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_name, variation_method, expected_response_code, \
        http_url = get_filter_parameters(lab_config, filtering_options, variation)
    str_in_message = ""
    for filter_opt in filtering_options:
        if filter_opt.message_type == FilterMessageType.STIMULUS.value:
            str_in_message = get_payload_data_from_file(
                check_value_for_file_var_mode(filter_opt.body_contains), 'plain'
            )

    message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            body_part=str_in_message
        ),
        string_in_message=str_in_message
    )

    try:
        return message.http.response_code, expected_response_code, variation_name
    except AttributeError:
        return "", expected_response_code, variation_name


def get_test_names() -> list:
    return [f"Verify Policy Store sends 4XX response code.",]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        response_code, expected_response_code, variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name=f"Verify Policy Store sends 4XX response code.",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": expected_response_code,
                "response": response_code
            }
        )
    ]
