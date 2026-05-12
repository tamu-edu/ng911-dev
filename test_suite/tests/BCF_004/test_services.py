from checks.http.checks import validate_response_code
from services.aux_services.message_services import (
    get_http_response_containing_string_in_http_body_for_message_matching_filter,
)
from services.aux_services.sip_services import extract_sip_header_values
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_messages
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_004.checks import validate_bcf_and_source_id


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
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
    header_contains = None

    params = getattr(variation, "params", {})

    if "messages" in params:
        for record in [r for data in params.values() for r in data]:
            # Update values only if they are currently falsy (None or "")
            expected_response_code = (
                expected_response_code or record.get("response_code", "").lower()
            )
            header_contains = (
                header_contains or record.get("header_contains", "").lower()
            )

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                if output:
                    if interface.name == output.src_interface:
                        out_scr_ip = interface.ip
                    elif interface.name == output.dst_interface:
                        out_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required"
                "parameters for osp_ip, bcf_ip, esrp_ip addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                expected_response_code,
                header_contains,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        expected_response_code,
        header_contains,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_messages = bcf_output_messages = response_code = source_id_list = (
        response_code
    ) = None

    # Variation #1
    if out_dst_ip is not None and out_scr_ip is not None:
        stimulus_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )
        bcf_output_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=out_scr_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        source_id_list = None
        if bcf_output_messages:
            source_id_list = extract_sip_header_values(
                bcf_output_messages, "Call-Info", "purpose=emergency-source"
            )
    # Variation #2
    else:
        bad_actors_response = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.POST,
                ],
            ),
            uri=header_contains,
        )

        if bad_actors_response and hasattr(bad_actors_response.http, "response_code"):
            response_code = bad_actors_response.http.response_code

    return [
        stimulus_messages,
        bcf_output_messages,
        expected_response_code,
        response_code,
        source_id_list,
    ]


def get_test_names() -> list:
    return [
        "Validate if outgoing SIP INVITE messages contain correct source-ID",
        "Validate BCF 433 response code for HTTP POST to /BadActors with unknown source-ID",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_messages,
        bcf_output_messages,
        expected_response_code,
        response_code,
        source_id_list,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Validate if outgoing SIP INVITE messages contain correct source-ID",
            test_method=validate_bcf_and_source_id,
            test_params={
                "stimulus_messages": stimulus_messages,
                "bcf_output_messages": bcf_output_messages,
                "source_id_list": source_id_list,
            },
        ),
        TestCheck(
            test_name="Validate BCF 433 response code for HTTP POST to /BadActors with unknown source-ID",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": expected_response_code,
                "response_code": response_code,
            },
        ),
    ]
