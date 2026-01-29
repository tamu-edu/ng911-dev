from checks.http.checks import validate_response_code_class
from services.aux_services.sip_services import extract_sip_header_values
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (get_first_message_matching_filter, get_messages)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_004.checks import validate_bcf_and_source_id


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) \
        -> tuple[str, str, str, str, None | str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings

    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    expected_response_code = None

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
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> list:
    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, expected_response_code = (
        get_filter_parameters(lab_config, filtering_options, variation))

    stimulus_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )
    bcf_output_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )

    source_id_list = None
    if bcf_output_messages:
        source_id_list = extract_sip_header_values(bcf_output_messages,
                                                   'Call-Info',
                                                   'purpose=emergency-source')

    bad_actors_post = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST, ]
        )
    )

    response_code = None
    bad_actors_text_data = None

    if bad_actors_post:
        if hasattr(bad_actors_post, PacketTypeEnum.HTTP) and hasattr(bad_actors_post.http, "file_data"):
            message_body = bad_actors_post.http.file_data
            bad_actors_text_data = bytes.fromhex(message_body.replace(":", "")).decode("utf-8")

        bad_actors_response = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=float(bad_actors_post.sniff_timestamp)
            )
        )
        if bad_actors_response:
            if hasattr(bad_actors_response, 'http') and hasattr(bad_actors_response.http, 'response_code'):
                response_code = bad_actors_response.http.response_code

    return [stimulus_messages, bcf_output_messages, expected_response_code,
            response_code, source_id_list, bad_actors_text_data]


def get_test_names() -> list:
    return [
        f"Validate if stimulus HTTP POST contain unknown source-ID",
        f"Validate BCF 4XX response code for HTTP POST to /BadActors with unknown source-ID"
    ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (
        stimulus_messages,
        bcf_output_messages,
        expected_response_code,
        response_code,
        source_id_list,
        bad_actors_text_data

    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name=f"Validate if stimulus HTTP POST contain unknown source-ID",
            test_method=validate_bcf_and_source_id,
            test_params={
                "stimulus_messages": stimulus_messages,
                "bcf_output_messages": bcf_output_messages,
                "source_id_list": source_id_list,
                "bad_actors_text_data": bad_actors_text_data
            }
        ),
        TestCheck(
            test_name=f"Validate BCF 4XX response code for HTTP POST to /BadActors with unknown source-ID",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": expected_response_code,
                "response_code": response_code
            }
        )
    ]
