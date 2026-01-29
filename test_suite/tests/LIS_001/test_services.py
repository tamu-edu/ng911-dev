from checks.sip.message_body_checks.checks import test_if_xml_body_list_contains_pidf_lo_location
from services.aux_services.message_services import extract_all_contents_from_message_body
from services.aux_services.aux_services import check_value_for_file_var_mode
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_first_message_matching_filter, \
    get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from services.aux_services.xml_services import extract_xml_body_string_from_file, is_valid_xml


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
    http_request_body = None
    variation_name = variation.name
    scenario_file_path = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
    for message in variation.params.get('messages'):
        http_request_body = message.get('body', None)
        sipp_scenario = message.get("sipp_scenario", None)
        scenario_file_path = sipp_scenario.get('scenario_file_path') if sipp_scenario else None

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
            return stimulus_src_ip, stimulus_dst_ip, http_request_body, scenario_file_path, variation_name
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> list:
    stimulus_src_ip, stimulus_dst_ip, http_request_body, scenario_filepath, variation\
        = get_filter_parameters(lab_config, filtering_options, variation)

    output_message_xml_body_list = []

    if http_request_body:
        request_body, is_file = check_value_for_file_var_mode(http_request_body)
        if is_file:
            http_xml_request = extract_xml_body_string_from_file(request_body)
        else:
            # TODO might be a situation when req body provided as str in the beginning
            http_xml_request = http_request_body

        http_output_message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=stimulus_src_ip,
                    dst_ip=stimulus_dst_ip,
                    packet_type=PacketTypeEnum.HTTP
                ),
                http_xml_request
            )

        if http_output_message:
            for body in extract_all_contents_from_message_body(http_output_message):
                if is_valid_xml(body['body']):
                    output_message_xml_body_list.append(body)

    if scenario_filepath:
        sip_output_message = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[SIPMethodEnum.NOTIFY,]
            )
        )

        if sip_output_message is not None:
            for body in extract_all_contents_from_message_body(sip_output_message):
                if is_valid_xml(body['body']):
                    output_message_xml_body_list.append(body)

    return [output_message_xml_body_list, variation]


def get_test_names() -> list:
    return [f"locationURI dereference check",]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        output_message_xml_body_list,
        variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="locationURI dereference check",
            test_method=test_if_xml_body_list_contains_pidf_lo_location,
            test_params={
                "message_xml_body_list": output_message_xml_body_list
            }
        )
    ]


