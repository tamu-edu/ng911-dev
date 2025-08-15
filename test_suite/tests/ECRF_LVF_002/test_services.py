from checks.http.lost_checks.checks import test_http_lost_find_service_response
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from services.aux_services.xml_services import extract_xml_body_string_from_file, extract_all_xml_bodies_from_message


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :param lab_config: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip,
                                            stimulus_dst_ip,
                                            sipp_scenario_file_path), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    sipp_scenario_file_path = None

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                sipp_scenario_file_path = message.get('body', None).removeprefix('file.')

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
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, sipp_scenario_file_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:

    stimulus_src_ip, stimulus_dst_ip, sipp_scenario = get_filter_parameters(lab_config, filtering_options, variation)
    xml_request = extract_xml_body_string_from_file(sipp_scenario)
    message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP
        ),
        xml_request
    )
    try:
        xml_response = extract_all_xml_bodies_from_message(message)[0]
    except IndexError:
        xml_response = ""
    return xml_request, xml_response


def get_test_names() -> list:
    return [f"Validate civic and geodetic locations handling by ECRF.", ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        xml_request,
        xml_response,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Validate civic and geodetic locations handling by ECRF.",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        )
    ]
