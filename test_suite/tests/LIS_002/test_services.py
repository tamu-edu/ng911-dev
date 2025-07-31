from checks.http.held_checks.checks import test_if_location_response_contains_correct_location_uri, \
    test_location_response_expiration_time
from services.aux_services.message_services import extract_all_contents_from_message_body
from services.aux_services.xml_services import extract_xml_body_string_from_file
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, req_scen_file, loc_req_device_uri), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    loc_req_device_uri = None
    req_scen_file = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                req_scen_file = message.get('body', None).removeprefix('file.')
                loc_req_device_uri = message.get('param_name', None)

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
            return stimulus_src_ip, stimulus_dst_ip, req_scen_file, loc_req_device_uri

    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, request_scenario_file, location_request_device_uri = (
        get_filter_parameters(lab_config, filtering_options, variation))

    http_xml_request = extract_xml_body_string_from_file(request_scenario_file)

    http_output_message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP
            ),
            http_xml_request
    )
    response_bodies = extract_all_contents_from_message_body(http_output_message)
    http_xml_response = ""
    for body in response_bodies:
        if 'xml' in body['Content-Type']:
            http_xml_response = body['body']
            break
    if not http_output_message:
        return http_xml_response, ''

    http_held_message_timestamp = float(http_output_message.sniff_timestamp)
    return http_xml_response, http_held_message_timestamp


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter],
                  variation: RunVariation) -> list:
    (
        http_xml_response,
        http_held_message_timestamp
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="locationResponse contains correct locationURI URL",
            test_method=test_if_location_response_contains_correct_location_uri,
            test_params={
                "output_xml": http_xml_response
            }
        ),
        TestCheck(
            test_name="locationResponse expiration time is between 30min and 24h",
            test_method=test_location_response_expiration_time,
            test_params={
                "output_xml": http_xml_response,
                "output_message_timestamp": http_held_message_timestamp
            }
        )
    ]
