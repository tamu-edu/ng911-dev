from services.aux_services.aux_services import get_first_message_matching_filter
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.aux_services.sip_msg_body_services import extract_all_contents_from_message_body, is_valid_pidf_lo
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
    get_list_of_all_header_fields_from_sip_message
)
from services.aux_services.message_services import extract_header_field_value_from_raw_string_body
from services.test_services.test_assessment_service import TestCheck
from checks.sip.message_body_checks.checks import (
    test_keeping_original_message_bodies,
    test_adding_default_pidf_lo
)
from checks.sip.geolocation_header_field_checks.checks import (
    test_adding_geolocation_header_pointing_to_pidf_lo
)
from checks.sip.header_field_checks.checks import (
    test_keeping_original_header_field,
    test_adding_header_field_on_top_of_its_section
)
from tests.ESRP_003.constants import VARIATION_TO_NAME_MAPPING


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
    expected_response_code, variation_name), all are strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    output = None
    out_scr_ip = None
    out_dst_ip = None
    variation_name = variation.name

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
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
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return (stimulus_src_ip, stimulus_dst_ip,
                    out_scr_ip, out_dst_ip,
                    expected_response_code, variation_name)
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> list:

    (stimulus_src_ip, stimulus_dst_ip,
     out_scr_ip, out_dst_ip,
     expected_response_code, variation_name) = (
        get_filter_parameters(lab_config, filtering_options, variation))

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )
    output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )
    stimulus_message_body_list = extract_all_contents_from_message_body(stimulus_message)
    output_message_body_list = extract_all_contents_from_message_body(output_message)
    stimulus_geolocation_header_fields = extract_all_header_fields_matching_name_from_sip_message(
        'Geolocation', stimulus_message)
    stimulus_geolocation_header_cid_list = []
    for cid in stimulus_geolocation_header_fields:
        stimulus_geolocation_header_cid_list.append(
            extract_header_field_value_from_raw_string_body('Geolocation', cid)
        )
    output_geolocation_header_fields = extract_all_header_fields_matching_name_from_sip_message(
        'Geolocation', output_message)
    output_geolocation_header_cid_list = []
    for cid in output_geolocation_header_fields:
        output_geolocation_header_cid_list.append(
            extract_header_field_value_from_raw_string_body('Geolocation', cid)
        )
    output_pidf_lo_body_list = [body for body in output_message_body_list if is_valid_pidf_lo(body['body'])]
    stimulus_header_fields = get_list_of_all_header_fields_from_sip_message(stimulus_message)
    output_header_fields = get_list_of_all_header_fields_from_sip_message(output_message)
    stimulus_message_xml_json_body_list = [body for body in stimulus_message_body_list
                                           if 'xml' or 'json' in body['Content-Type']]
    output_message_xml_json_body_list = [body for body in output_message_body_list
                                         if 'xml' or 'json' in body['Content-Type']]
    return [stimulus_message, output_message, stimulus_message_body_list, output_message_body_list,
            stimulus_geolocation_header_cid_list, output_geolocation_header_cid_list, output_pidf_lo_body_list,
            stimulus_header_fields, output_header_fields, stimulus_message_xml_json_body_list,
            output_message_xml_json_body_list, VARIATION_TO_NAME_MAPPING.get(variation_name, variation_name)]


def get_test_names() -> list:
    return [
         f"Adding default PIDF-LO."
         f"Adding 'Geolocation' pointing to default PIDF-LO.",
         f"Adding 'Geolocation' as top-most entry in 'Geolocation' section.",
         f"Keeping original 'Geolocation' header field.",
         f"Keeping original message bodies.",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter],
                  variation: RunVariation) -> list:
    (
        stimulus_message,
        output_message,
        stimulus_message_body_list,
        output_message_body_list,
        stimulus_geolocation_header_cid_list,
        output_geolocation_header_cid_list,
        output_pidf_lo_body_list,
        stimulus_header_fields,
        output_header_fields,
        stimulus_message_xml_json_body_list,
        output_message_xml_json_body_list,
        variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    test_list = []

    if variation_name in ("no_geolocation_data",
                          "garbled_pidf_lo",
                          "geolocation_header_unable_to_dereference"
                          ):
        test_list.append(
            TestCheck(
                test_name=f"Adding default PIDF-LO.",
                test_method=test_adding_default_pidf_lo,
                test_params={
                    "stimulus_message_body_list": stimulus_message_body_list,
                    "output_message_body_list": output_message_body_list
                }
            )
        )
    if variation_name in ("no_geolocation_data",
                          "garbled_pidf_lo",
                          "geolocation_header_unable_to_dereference"
                          ):
        test_list.append(
            TestCheck(
                test_name=f"Adding 'Geolocation' pointing to default PIDF-LO.",
                test_method=test_adding_geolocation_header_pointing_to_pidf_lo,
                test_params={
                    "stimulus_geolocation_header_cid_list": stimulus_geolocation_header_cid_list,
                    "output_geolocation_header_cid_list": output_geolocation_header_cid_list,
                    "output_pidf_lo_body_list": output_pidf_lo_body_list
                }
            )
        )
    if variation_name in ("garbled_pidf_lo",
                          "geolocation_header_unable_to_dereference"
                          ):
        test_list.append(
            TestCheck(
                test_name=f"Adding 'Geolocation' as top-most entry in 'Geolocation' section.",
                test_method=test_adding_header_field_on_top_of_its_section,
                test_params={
                    "stimulus": stimulus_message,
                    "output": output_message,
                    "header_name": 'Geolocation'
                }
            )
        )
    if variation_name in ("garbled_pidf_lo",
                          "geolocation_header_unable_to_dereference"
                          ):
        test_list.append(
            TestCheck(
                test_name=f"Keeping original 'Geolocation' header field.",
                test_method=test_keeping_original_header_field,
                test_params={
                    "stimulus_header_fields": stimulus_header_fields,
                    "output_header_fields": output_header_fields,
                }
            )
        )
    if variation_name == "garbled_pidf_lo":
        test_list.append(
            TestCheck(
                test_name=f"Keeping original message bodies.",
                test_method=test_keeping_original_message_bodies,
                test_params={
                    "stimulus_message_body_list": stimulus_message_xml_json_body_list,
                    "output_message_body_list": output_message_xml_json_body_list
                }
            )
        )
    return test_list
