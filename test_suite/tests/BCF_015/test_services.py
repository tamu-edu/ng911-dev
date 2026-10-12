from urllib.parse import urlparse

from checks.general.checks import (
    is_data_present,
)
from services.aux_services.json_services import is_jws
from services.aux_services.sip_services import extract_sip_call_identifiers
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.test_services.test_assessment_service import TestCheck

from dataclasses import dataclass, field

from pyshark.packet.packet import Packet

from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from tests.BCF_015.constants import NOT_RUN


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    log_event_endpoint = output.header_contains

    if not (stimulus and output):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    ip_by_interface_name = {}
    key_filepath = None
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip
            if interface.name == output.src_interface:
                key_filepath = entity.certificate_key

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
        log_event_endpoint,
    )


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Packet | None = None
    stimulus_call_id_sip: str | None = None

    log_event_endpoint: str | None = None

    http_log_event_msgs: list = field(default_factory=list)

    is_all_http_posts: bool = False
    is_all_log_events_endpoint: bool = False
    is_all_jws_valid: bool = False


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
        log_event_endpoint,
    ) = get_filter_parameters(lab_config, filtering_options)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("osp_bcf", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("bcf_logger", out_src_ip, out_dst_ip)

    data: dict = {"http_log_event_msgs": [], "log_event_endpoint": log_event_endpoint}

    # OSP to BCF stimulus message
    stimulus_message, stimulus_ts = fetcher.get_first_sip_invite(
        "osp_bcf", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get stimulus call identifiers
    stimulus_call_ids = extract_sip_call_identifiers(stimulus_message)
    data["stimulus_call_id_sip"] = stimulus_call_ids.call_id_sip

    # Get BCF to LOGGER POST messages
    bcf_to_logger_post_messages = fetcher.get_http_messages(
        "bcf_logger", after_timestamp=stimulus_ts
    )

    # Get all requests whose target path exactly matches the configured endpoint
    for message in bcf_to_logger_post_messages:
        http_msg = HttpMessage.from_packet(message)
        if not http_msg:
            continue
        target_path = urlparse(http_msg.request_target).path.rstrip("/")
        if target_path == log_event_endpoint:
            data["http_log_event_msgs"].append(http_msg)

    if not data["http_log_event_msgs"]:
        return TestData(**data)

    # Is all HTTP requests using the POST method
    data["is_all_http_posts"] = all(
        http_msg.method == "POST" for http_msg in data["http_log_event_msgs"]
    )

    # Is all endpoints free of query parameters
    data["is_all_log_events_endpoint"] = all(
        not urlparse(http_msg.request_target).query
        for http_msg in data["http_log_event_msgs"]
    )

    # Is request contains a valid JWS JSON body with Base64Url-encoded values
    data["is_all_jws_valid"] = all(
        http_msg.body and is_jws(http_msg.body, check_base64=True)
        for http_msg in data["http_log_event_msgs"]
    )

    return TestData(**data)


def get_test_names() -> list:
    test_names_list = [
        "Verify HTTP POST requests to the target endpoint are found",
        "Verify all found requests use the POST method",
        "Verify all found requests target the configured endpoint with no query parameters",
        "Verify all found requests contain a valid JWS JSON body with Base64Url-encoded values",
    ]
    return test_names_list


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation
    )

    return [
        TestCheck(
            test_name="Verify HTTP POST requests to the target endpoint are found",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.http_log_event_msgs,
                "error": "FAILED -> No HTTP POST requests to the target endpoint were found",
            },
        ),
        TestCheck(
            test_name="Verify all found requests use the POST method",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_all_http_posts,
                "error": "FAILED -> Found a request that does not use the POST method",
            },
        ),
        TestCheck(
            test_name="Verify all found requests target the configured endpoint with no query parameters",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_all_log_events_endpoint,
                "error": "FAILED -> Found a request with an unexpected query parameter or endpoint format",
            },
        ),
        TestCheck(
            test_name="Verify all found requests contain a valid JWS JSON body with Base64Url-encoded values",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_all_jws_valid,
                "error": "FAILED -> Found a request without a valid JWS JSON body or with undecodable Base64Url-encoded values",
            },
        ),
    ]
