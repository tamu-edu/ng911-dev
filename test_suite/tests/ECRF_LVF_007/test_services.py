from dataclasses import dataclass

from services.aux_services.json_services import get_json
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
    get_messages,
    extract_json_data_from_http,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_015.checks import validate_json_serialization_jws_format


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
    key_filepath = None
    cert_filepath = None

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
                    key_filepath = entity.certificate_key
                    cert_filepath = entity.certificate_file
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                    key_filepath = entity.certificate_key
                    cert_filepath = entity.certificate_file
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
                key_filepath,
                cert_filepath,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


@dataclass
class TestData:
    stimulus_message = None
    post_to_logger_message = None
    json_dict_body_from_message: dict = None
    content_body: str = None
    key_filepath: str = None
    cert_filepath: str = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    post_to_logger_message = None
    post_to_logger_messages = None
    json_dict_body_from_message = None
    content_body = None

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        key_filepath,
        cert_filepath,
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
        post_to_logger_messages = get_messages(
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

    if post_to_logger_messages:
        for message in post_to_logger_messages:

            if hasattr(message, "http") and hasattr(message.http, "file_data"):
                message_content = extract_all_contents_from_message_body(
                    message, ignore_content_type=True
                )
                if message_content:
                    content_body = message_content[0].get("body", "")
                    if content_body and get_json(content_body):
                        post_to_logger_message = message
                        json_dict_body_from_message = extract_json_data_from_http(
                            message
                        )
                        break

    return (
        stimulus_message,
        post_to_logger_message,
        json_dict_body_from_message,
        content_body,
        key_filepath,
        cert_filepath,
    )


def get_test_names() -> list:
    return ["Verify JWS use the Flat JSON serialization format"]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    test_data = TestData()

    (
        test_data.stimulus_message,
        test_data.post_to_logger_message,
        test_data.json_dict_body_from_message,
        test_data.content_body,
        test_data.key_filepath,
        test_data.cert_filepath,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify JWS use the Flat JSON serialization format",
            test_method=validate_json_serialization_jws_format,
            test_params={
                "test_data": test_data,
            },
        )
    ]
