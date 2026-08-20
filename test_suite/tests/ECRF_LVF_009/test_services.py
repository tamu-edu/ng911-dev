from dataclasses import dataclass

from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
    get_messages,
    get_message_and_jws_by_event_type,
)
from services.aux_services.xml_services import (
    extract_all_xml_bodies_from_message,
    is_malformed_xml,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_009.checks import (
    validate_ecrf_to_logger_event_members,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    other = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    other_scr_ip = None
    key_filepath = None
    cert_filepath = None
    ecrf_fqdn = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message
        elif message.message_type == FilterMessageType.OTHER:
            other = message

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
                        ecrf_fqdn = interface.fqdn
                        key_filepath = entity.certificate_key
                        cert_filepath = entity.certificate_file
                    elif interface.name == output.dst_interface:
                        out_dst_ip = interface.ip

                if other:
                    if interface.name == other.src_interface:
                        other_scr_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
            or other_scr_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        elif not ecrf_fqdn:
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required FQDN records for ECRF-LVF interfaces"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                other_scr_ip,
                key_filepath,
                cert_filepath,
                ecrf_fqdn,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


@dataclass
class TestData:
    variant_number: int = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    ecrf_to_esrp_body_xml = None
    ecrf_to_logger_http_post_message = None
    ecrf_to_logger_post_jws = None
    variant_number = 1
    ecrf_to_ecfr_fwd_response_message = None
    ecrf_to_ecrf_response_body_xml = None
    ecrf_to_logger_second_post_jws = None
    ecrf_to_logger_second_http_post_message = None
    ecrf_to_logger_http_post_message_timestamp = 0

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        other_scr_ip,
        key_filepath,
        cert_filepath,
        ecrf_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    stimulus_timestamp = getattr(stimulus_message, "sniff_timestamp", 0)

    ecrf_to_ecfr_fwd_post_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=other_scr_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=stimulus_timestamp,
        ),
    )

    if ecrf_to_ecfr_fwd_post_message:
        ecrf_to_ecfr_fwd_post_message_timestamp = getattr(
            ecrf_to_ecfr_fwd_post_message, "sniff_timestamp", 0
        )
        variant_number = 2

        ecrf_to_ecfr_fwd_response_message = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=other_scr_ip,
                dst_ip=out_scr_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=ecrf_to_ecfr_fwd_post_message_timestamp,
            ),
        )

        if ecrf_to_ecfr_fwd_response_message:

            if hasattr(ecrf_to_ecfr_fwd_response_message, "http") and hasattr(
                ecrf_to_ecfr_fwd_response_message.http, "file_data"
            ):
                message_content = extract_all_contents_from_message_body(
                    ecrf_to_ecfr_fwd_response_message, ignore_content_type=True
                )
                if is_malformed_xml(ecrf_to_ecfr_fwd_response_message):
                    variant_number = 3

                if message_content:
                    ecrf_to_ecrf_response_body_xml = message_content[0].get("body", "")

    ecrf_to_esrp_response = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.HTTP,
            after_timestamp=stimulus_timestamp,
        ),
    )

    if ecrf_to_esrp_response:
        message_content = extract_all_xml_bodies_from_message(ecrf_to_esrp_response)
        if message_content:
            ecrf_to_esrp_body_xml = message_content[0]

    ecrf_to_logger_http_post_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=stimulus_timestamp,
        ),
    )

    if ecrf_to_logger_http_post_messages:
        jws, message = get_message_and_jws_by_event_type(
            ecrf_to_logger_http_post_messages, "LostResponseLogEvent", key_filepath
        )
        ecrf_to_logger_post_jws = jws
        ecrf_to_logger_http_post_message = message
        ecrf_to_logger_http_post_message_timestamp = getattr(
            ecrf_to_logger_http_post_message, "sniff_timestamp", 0
        )

    if variant_number == 2:
        ecrf_to_logger_http_second_post_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=out_scr_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.POST,
                ],
                after_timestamp=ecrf_to_logger_http_post_message_timestamp,
            ),
        )
        if ecrf_to_logger_http_second_post_messages:
            jws, message = get_message_and_jws_by_event_type(
                ecrf_to_logger_http_second_post_messages,
                "LostResponseLogEvent",
                key_filepath,
            )
            ecrf_to_logger_second_post_jws = jws
            ecrf_to_logger_second_http_post_message = message

    test_data = TestData()

    test_data.stimulus_message = stimulus_message
    test_data.ecrf_to_esrp_response = ecrf_to_esrp_response
    test_data.ecrf_to_esrp_body_xml = ecrf_to_esrp_body_xml
    test_data.ecrf_to_logger_http_post_message = ecrf_to_logger_http_post_message
    test_data.ecrf_to_logger_post_jws = ecrf_to_logger_post_jws
    test_data.ecrf_to_logger_second_post_jws = ecrf_to_logger_second_post_jws
    test_data.ecrf_to_logger_second_http_post_message = (
        ecrf_to_logger_second_http_post_message
    )
    test_data.ecrf_to_ecfr_fwd_post_message = ecrf_to_ecfr_fwd_post_message
    test_data.ecrf_to_ecrf_response_body_xml = ecrf_to_ecrf_response_body_xml
    test_data.ecrf_to_ecfr_fwd_response_message = ecrf_to_ecfr_fwd_response_message
    test_data.ecrf_fqdn = ecrf_fqdn
    test_data.variant_number = variant_number

    return test_data


def get_test_names() -> list:
    return [
        "Validate ECRF-LVF to LOGGER LostResponseLogEvent members",
        "Validate ECRF-LVF to LOGGER LostResponseLogEvent members after ECRF-LVF recursive forwarded request",
        "Validate ECRF-LVF to LOGGER LostResponseLogEvent members after ECRF-LVF recursive forwarded request and malformed XML response",
        "Validate ECRF-LVF to LOGGER LostResponseLogEvent 'responseStatus' field when no response from TS-ECRF-LVF",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation
    )

    var_idx = test_data.variant_number - 1

    variant_four_name = (
        "LostResponseLogEvent members after ECRF-LVF does not receive a response"
    )

    if variation.name == variant_four_name:
        test_data.variant_number = 4
        var_idx = 3

    return [
        TestCheck(
            test_name=get_test_names()[var_idx],
            test_method=validate_ecrf_to_logger_event_members,
            test_params={
                "test_data": test_data,
            },
        )
    ]
