from checks.sip.call_info_header_field_checks.constants import EMERGENCY_IDENTIFIER_URN_PATTERN
from services.aux_services.message_services import extract_json_data_from_http
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter, split_sip_header_by_pattern, \
    extract_header_by_pattern
from enums import PacketTypeEnum, HTTPMethodEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_007.checks import validate_support_of_discrepancy_report


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter]) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    # TODO Add fqdn parsing

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
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> tuple:

    # TODO Add fqdn parsing
    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip = get_filter_parameters(lab_config, filtering_options)

    out_message_json = None
    sip_invite_str = None
    emergency_call_info_header = ''

    sip_invite_msg = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )

    if sip_invite_msg:
        sip_invite_str = str(sip_invite_msg.sip)

        bcf_headers = split_sip_header_by_pattern(sip_invite_msg.sip.get('msg_hdr'))
        for call_info_header in bcf_headers.get('Call-Info', []):
            for header_value in call_info_header.split(', '):
                if 'purpose=emergency-source' in header_value:
                    emergency_call_info_header = header_value

    esrp_output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST, ]
        )
    )

    if esrp_output_message:
        out_message_json = extract_json_data_from_http(esrp_output_message)

    return sip_invite_str, out_message_json, emergency_call_info_header


def get_test_names() -> list:
    return [f"Validate Discrepancy Report function support", ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    sip_invite_str, out_message_json, emergency_call_info_header = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Validate Discrepancy Report function support",
            test_method=validate_support_of_discrepancy_report,
            test_params={
                "sip_invite_str": sip_invite_str,
                "out_message_json": out_message_json,
                "emergency_call_info_header": emergency_call_info_header
            }
        )
    ]
