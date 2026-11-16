from dataclasses import dataclass, field
from urllib.parse import urlparse

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present
from checks.jws.checks import validate_jws_payload_serialization_format
from services.aux_services.message_services import (
    extract_json_data_from_http,
    get_http_messages_by_log_event_type,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from enums import HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_013.constants import CALL_START_LOG_EVENT, NOT_RUN, NO_CHFE_LOGGER_MSG


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip,
        out_src_ip, out_dst_ip, key_filepath, cert_filepath, log_event_endpoint)
    """
    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)

    if not (stimulus and output):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    log_event_endpoint = output.header_contains
    if not log_event_endpoint:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain the LogEvents endpoint"
        )

    ip_by_interface_name = {}
    key_filepath = None
    cert_filepath = None
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip
            if interface.name == output.src_interface:
                key_filepath = entity.certificate_key
                cert_filepath = entity.certificate_file

    stimulus_src_ip = ip_by_interface_name.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface_name.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface_name.get(output.src_interface)
    out_dst_ip = ip_by_interface_name.get(output.dst_interface)

    required_ips = (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
    )
    if None in required_ips:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        key_filepath,
        cert_filepath,
        log_event_endpoint,
    )


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Packet | None = None
    http_requests_chfe_to_logger: list[Packet] = field(default_factory=list)
    chfe_logger_post_message: Packet | None = None
    json_dict_body_from_message: dict | None = None
    post_to_logger_body: str | None = None
    key_filepath: str | None = None
    cert_filepath: str | None = None
    is_http_post_method: bool | None = None
    is_correct_endpoint: bool | None = None
    request_target: str | None = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        key_filepath,
        cert_filepath,
        log_event_endpoint,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_logger", out_src_ip, out_dst_ip)

    data: dict = {"cert_filepath": cert_filepath, "key_filepath": key_filepath}

    # Get stimulus message and time stamp
    stimulus_message, stimulus_ts = fetcher.get_first_sip(
        "esrp_chfe", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    # Get all HTTP to LOGGER messages
    http_requests_chfe_to_logger = fetcher.get_http_messages(
        "chfe_logger", after_timestamp=stimulus_ts
    )
    data["http_requests_chfe_to_logger"] = http_requests_chfe_to_logger

    # Get first POST message with LostQueryLogEvent
    matched_event_messages = (
        get_http_messages_by_log_event_type(
            http_requests_chfe_to_logger, CALL_START_LOG_EVENT
        )
        if http_requests_chfe_to_logger
        else []
    )
    chfe_logger_post_message = next(iter(matched_event_messages or []), None)

    # Get POST to LOGGER message and extract content
    http_msg = (
        HttpMessage.from_packet(chfe_logger_post_message)
        if chfe_logger_post_message
        else None
    )
    if not http_msg:
        return TestData(**data)

    data["chfe_logger_post_message"] = chfe_logger_post_message
    data["post_to_logger_body"] = http_msg.body

    if data["post_to_logger_body"]:
        data["json_dict_body_from_message"] = extract_json_data_from_http(
            chfe_logger_post_message
        )

    # Is HTTP requests use the POST method
    data["is_http_post_method"] = http_msg.method == HTTPMethodEnum.POST.value

    # Is correct endpoint
    data["request_target"] = http_msg.request_target
    parsed_target = urlparse(data["request_target"] or "")
    data["is_correct_endpoint"] = (
        parsed_target.path.rstrip("/") == log_event_endpoint and not parsed_target.query
    )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Verify CHFE to LOGGER requests are present",
        "Verify CHFE to LOGGER request use the POST method",
        "Verify CHFE to LOGGER POST request target endpoint with no query parameters",
        "Verify JWS use the Flat JSON serialization format and protection",
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

    return [
        TestCheck(
            test_name="Verify CHFE to LOGGER requests are present",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.http_requests_chfe_to_logger,
                "error": NO_CHFE_LOGGER_MSG,
            },
        ),
        TestCheck(
            test_name="Verify CHFE to LOGGER request use the POST method",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_http_post_method,
                "error": "FAILED -> CHFE to LOGGER request does not use the POST method",
            },
        ),
        TestCheck(
            test_name="Verify CHFE to LOGGER POST request target endpoint with no query parameters",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_correct_endpoint,
                "error": f"FAILED -> Found a request with an unexpected query parameter or endpoint format. Actual: {test_data.request_target}",
            },
        ),
        TestCheck(
            test_name="Verify JWS use the Flat JSON serialization format and protection",
            precondition=bool(test_data.stimulus_message)
            and bool(test_data.http_requests_chfe_to_logger),
            precondition_error=(
                NOT_RUN if not test_data.stimulus_message else NO_CHFE_LOGGER_MSG
            ),
            test_method=validate_jws_payload_serialization_format,
            test_params={
                "content_body": test_data.post_to_logger_body,
                "json_body": test_data.json_dict_body_from_message,
                "cert_filepath": test_data.cert_filepath,
                "key_filepath": test_data.key_filepath,
            },
        ),
    ]
