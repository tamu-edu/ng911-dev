from services.aux_services.json_services import get_payload_data_from_file
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import (get_http_response_containing_string_in_xml_body_for_message_matching_filter,
                                                get_first_message_matching_filter)
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from services.aux_services.xml_services import extract_all_xml_bodies_from_message
from checks.general.checks import test_if_parameter_has_expected_value, test_if_url_is_valid
from checks.http.checks import validate_response_code_class


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, request_payload_path), all are strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    output = None
    output_src_ip = None
    output_dst_ip = None
    response_status_code = None
    request_payload_path = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        if message.message_type == FilterMessageType.OUTPUT.value:
            output = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                if message.get('action', None) == "send":
                    response_status_code = message.get('response_code', None)
                    request_payload_path = message.get('body', None).removeprefix('file.')

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    output_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    output_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return (stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip,
                    response_status_code, request_payload_path)
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip, expected_response_code, request_payload_path = (
        get_filter_parameters(lab_config, filtering_options, variation))

    stimulus_message_xml = "".join(get_payload_data_from_file(request_payload_path, 'plain').split())

    stimulus_response_message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
            ),
            stimulus_message_xml
        )

    if output_src_ip and output_dst_ip and not expected_response_code:
        output_message = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=output_src_ip,
                dst_ip=output_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.GET, ]
            )
        )
        output_message_response = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=output_src_ip,
                dst_ip=output_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
            ),
            stimulus_message_xml
        )

        def get_first_xml(message):
            try:
                return extract_all_xml_bodies_from_message(message)[0]
            except IndexError:
                return None
        output_message_xml = "".join(get_first_xml(output_message).split())
        output_message_response_xml = "".join(get_first_xml(output_message_response).split())
        stimulus_message_response_xml = "".join(get_first_xml(stimulus_response_message).split())

        return (expected_response_code, stimulus_message_xml, stimulus_message_response_xml, None,
                None, output_message_xml, output_message_response_xml)
    else:
        stimulus_message_response_status_code = None
        stimulus_message_response_location_url = None
        if stimulus_response_message:
            stimulus_message_response_status_code = stimulus_response_message.http.response_code
            stimulus_message_response_location_url = stimulus_response_message.http.get('location')
        return (expected_response_code, None, None,
                stimulus_message_response_status_code, stimulus_message_response_location_url, None, None)


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        expected_response_code, stimulus_message_xml, stimulus_message_response_xml,
        stimulus_message_response_status_code, stimulus_message_response_location_url,
        output_message_xml, output_message_response_xml
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if not expected_response_code:
        return [
            TestCheck(
                test_name="Validate sending HTTP LoST request to another ECRF",
                test_method=test_if_parameter_has_expected_value,
                test_params={
                    "parameter_name": "HTTP LoST request XML body",
                    "parameter_value": output_message_xml,
                    "expected_value": stimulus_message_xml,
                }
            ),
            TestCheck(
                test_name="Validate sending back HTTP LoST response from another ECRF",
                test_method=test_if_parameter_has_expected_value,
                test_params={
                    "parameter_name": "HTTP LoST response XML body",
                    "parameter_value": stimulus_message_response_xml,
                    "expected_value": output_message_response_xml,
                }
            ),
        ]
    else:
        return [
            TestCheck(
                test_name=f"Validate 3xx response",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": "3xx",
                    "response": stimulus_message_response_status_code,
                }
            ),
            TestCheck(
                test_name="Validate if LoST response contain URL",
                test_method=test_if_url_is_valid,
                test_params={
                    "url": stimulus_message_response_location_url
                }
            )
        ]
