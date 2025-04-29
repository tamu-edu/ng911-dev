from checks.http.lost_checks.checks import test_http_lost_find_service_response
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_conduction_service import TestCheck
from services.aux.xml_services import extract_xml_body_string_from_file, extract_all_xml_bodies_from_message
from .constants import (
    ESRP_IP,
    ECRF_LVF_IP,
    FindServiceScenarioFiles
)


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None or out_scr_ip is None or out_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> list:

    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip = get_filter_parameters(lab_config,
                                                                                     filtering_options,
                                                                                     variation)

    scenario_files = [scenario.value for name, scenario in FindServiceScenarioFiles.__dict__.items()
                      if isinstance(scenario, FindServiceScenarioFiles)]
    xml_requests = {}

    for scenario in scenario_files:
        xml_requests[scenario] = extract_xml_body_string_from_file(scenario)
    xml_responses = {}
    for scenario in scenario_files:
        message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=ESRP_IP,
                dst_ip=ECRF_LVF_IP,
                packet_type=PacketTypeEnum.HTTP
            ),
            xml_requests[scenario]
        )
        try:
            xml_responses[scenario] = extract_all_xml_bodies_from_message(message)[0]
        except IndexError:
            xml_responses[scenario] = ""
    return [xml_requests, xml_responses]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        xml_request,
        xml_response
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Response for findService by point geolocation",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        ),
        TestCheck(
            test_name="Response for findService by circle geolocation",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        ),
        TestCheck(
            test_name="Response for findService by ellipse geolocation",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        ),
        TestCheck(
            test_name="Response for findService by arc-band geolocation",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        ),
        TestCheck(
            test_name="Response for findService by polygon geolocation",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        ),
        TestCheck(
            test_name="Response for findService by civic address",
            test_method=test_http_lost_find_service_response,
            test_params={
                "stimulus_xml": xml_request,
                "output_xml": xml_response
            }
        )
    ]
