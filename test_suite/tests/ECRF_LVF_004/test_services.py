from checks.http.lost_checks.checks import test_http_lost_list_services_response
from services.aux_services.json_services import get_payload_data_from_file
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from services.aux_services.xml_services import extract_all_xml_bodies_from_message, extract_all_values_for_xml_tag_name


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str]:
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
            return stimulus_src_ip, stimulus_dst_ip,  request_payload_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, payload_path = \
        get_filter_parameters(lab_config, filtering_options, variation)
    payload = get_payload_data_from_file(payload_path, 'plain')
    message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP
        ),
        payload
    )

    service_urn = None

    by_location = True if extract_all_values_for_xml_tag_name(payload, "listServicesByLocation") else False
    if by_location:
        service_urn = [record for record in
                       extract_all_values_for_xml_tag_name(payload, "listServicesByLocation")
                       if 'service' in record][0]
    else:
        list_services = extract_all_values_for_xml_tag_name(payload, "listServices")
        if list_services:
            service_urn = list_services[0]
    try:
        return payload, extract_all_xml_bodies_from_message(message)[0], service_urn, by_location
    except IndexError:
        return payload, "", service_urn, by_location


def get_test_names() -> list:
    return [f"Validate http response for listServices", ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        xml_request, xml_response, service_urn, by_location
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Validate http response for listServices",
            test_method=test_http_lost_list_services_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response,
                "service_urn": service_urn,
                "by_location": by_location
            }
        )
    ]
