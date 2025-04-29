from checks.sip.message_body_checks.checks import test_if_xml_body_list_contains_pidf_lo_location
from services.aux.message_services import extract_all_contents_from_message_body
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.aux_services import get_first_message_matching_filter, \
    get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_conduction_service import TestCheck
from services.aux.xml_services import extract_xml_body_string_from_file, is_valid_xml


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str, str, str]:
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
    request_scenario = None
    variation_name = variation.name
    scenario_file_path = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
    for message in variation.params.get('messages'):
        request_scenario = message.get('body', None)
        if message.get("sipp_scenario", None):
            scenario_file_path = message["sipp_scenario"]['scenario_file_path']

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
            return stimulus_src_ip, stimulus_dst_ip, request_scenario, scenario_file_path, variation_name
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> list:
    stimulus_src_ip, stimulus_dst_ip, request_scenario, scenario_filepath, variation\
        = get_filter_parameters(lab_config, filtering_options, variation)
    if variation == 'Location_URI_dereference_using_SIP_Presence_Event_Package':
        http_xml_request = extract_xml_body_string_from_file(scenario_filepath.split('file.')[-1])
    else:
        http_xml_request = extract_xml_body_string_from_file(request_scenario.strip('file.'))
    http_output_message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP
            ),
            http_xml_request
        )
    sip_output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.NOTIFY,]
        )
    )
    http_output_message_xml_body_list = [body for body in extract_all_contents_from_message_body(http_output_message)
                                         if is_valid_xml(body['body'])]
    sip_output_message_xml_body_list = [body for body in extract_all_contents_from_message_body(sip_output_message)
                                        if is_valid_xml(body['body'])]
    return [http_output_message_xml_body_list, sip_output_message_xml_body_list, variation]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        output_message_xml_body_list,
        sip_output_message_xml_body_list,
        variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if variation_name == 'Location_URI_dereference_using_SIP_Presence_Event_Package':
        return [
            TestCheck(
                test_name="locationURI dereference using HTTP HELD",
                test_method=test_if_xml_body_list_contains_pidf_lo_location,
                test_params={
                    "message_xml_body_list": output_message_xml_body_list
                }
            )
            ]
    else:
        return [
            TestCheck(
                test_name="locationURI dereference using SIP",
                test_method=test_if_xml_body_list_contains_pidf_lo_location,
                test_params={
                    "message_xml_body_list": sip_output_message_xml_body_list
                }
            )
    ]
