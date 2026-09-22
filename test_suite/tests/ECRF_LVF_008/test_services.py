from dataclasses import dataclass

from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_008.checks import validate_ecrf_response


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
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    expected_response_code = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if "messages" in getattr(variation, "params", []):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get("response_code", None)
                if config_response_code and not expected_response_code:
                    expected_response_code = (
                        config_response_code[0]
                        if isinstance(config_response_code, list)
                        else config_response_code
                    )

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
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                expected_response_code,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


@dataclass
class TestData:
    expected_response_code = None
    is_variant_2 = False


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    ecrf_to_esrp_response_message = None
    ecrf_to_esrp_response_code = None
    ecrf_response_xml = None
    stimulus_request_xml = None
    response_timestamp = None
    is_variant_2 = False
    ecrf_to_ecrf_forwarded_message = None
    forwarded_request_xml = None

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        expected_response_code,
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

    if stimulus_message and stimulus_timestamp:
        if hasattr(stimulus_message, "http") and hasattr(
            stimulus_message.http, "file_data"
        ):
            message_content = extract_all_contents_from_message_body(stimulus_message)
            if message_content:
                stimulus_request_xml = message_content[0].get("body", "")

        ecrf_to_esrp_response_message = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=stimulus_timestamp,
            ),
        )
        if hasattr(ecrf_to_esrp_response_message, "http") and hasattr(
            ecrf_to_esrp_response_message.http, "response_code"
        ):
            response_timestamp = float(ecrf_to_esrp_response_message.sniff_timestamp)
            ecrf_to_esrp_response_code = (
                ecrf_to_esrp_response_message.http.response_code
            )

        ecrf_to_ecrf_forwarded_message = get_first_message_matching_filter(
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

    if ecrf_to_esrp_response_message:
        if hasattr(ecrf_to_esrp_response_message, "xml"):
            ecrf_response_xml = bytes.fromhex(
                ecrf_to_esrp_response_message.http.file_data.replace(":", "")
            ).decode("utf-8")

    if ecrf_to_ecrf_forwarded_message:
        if hasattr(ecrf_to_ecrf_forwarded_message, "http") and hasattr(
            ecrf_to_ecrf_forwarded_message.http, "file_data"
        ):
            message_content = extract_all_contents_from_message_body(
                ecrf_to_ecrf_forwarded_message
            )
            if message_content:
                forwarded_request_xml = message_content[0].get("body", "")
        is_variant_2 = True

    test_data = TestData()

    test_data.stimulus_message = stimulus_message
    test_data.stimulus_request_xml = stimulus_request_xml
    test_data.expected_response_code = expected_response_code
    test_data.ecrf_to_esrp_response_message = ecrf_to_esrp_response_message
    test_data.ecrf_to_esrp_response_code = ecrf_to_esrp_response_code
    test_data.ecrf_response_xml = ecrf_response_xml
    test_data.response_timestamp = response_timestamp
    test_data.is_variant_2 = is_variant_2
    test_data.ecrf_to_ecrf_forwarded_message = ecrf_to_ecrf_forwarded_message
    test_data.forwarded_request_xml = forwarded_request_xml

    return test_data


def get_test_names() -> list:
    return [
        "Validate ECRF-LVF response on request with callId and incidentTrackingId",
        "Validate ECRF-LVF response and recursive forwarded request with callId and incidentTrackingId",
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

    return (
        [
            TestCheck(
                test_name="Validate ECRF-LVF response on request with callId and incidentTrackingId",
                test_method=validate_ecrf_response,
                test_params={
                    "test_data": test_data,
                },
            )
        ]
        if not test_data.is_variant_2
        else [
            TestCheck(
                test_name="Validate ECRF-LVF response and recursive forwarded request with callId and incidentTrackingId",
                test_method=validate_ecrf_response,
                test_params={
                    "test_data": test_data,
                },
            )
        ]
    )
