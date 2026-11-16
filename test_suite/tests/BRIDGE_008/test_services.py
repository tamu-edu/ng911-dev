from urllib.parse import urlparse

from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
)
from checks.jws.checks import validate_flattened_jws
from checks.log_events.log_events import CallSignalingMessageLogEvent
from services.aux_services.json_services import (
    decode_base64url,
    get_json,
)
from services.aux_services.message_services import extract_json_data_from_http
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.test_services.test_assessment_service import TestCheck

from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError


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

    if not (stimulus and output):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    log_event_endpoint = output.header_contains
    expected_response_code = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.OUTPUT:
            expected_response_code = (
                message.response_status_code
                if hasattr(message, "response_status_code")
                else expected_response_code
            )

    ip_by_interface_name = {}
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip

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
        expected_response_code,
        log_event_endpoint,
    )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    """
    :return: Tuple of (stimulus_message, is_http_post, call_signaling_log_event, reponse_code)
    """
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        expected_response_code,
        log_event_endpoint,
    ) = get_filter_parameters(lab_config, filtering_options)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("chfe_bridge", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("bridge_logger", out_src_ip, out_dst_ip)

    is_http_post = False
    jws_data = None
    call_signaling_log_event = None
    response_code = None

    # CHFE to BRIDGE stimulus message
    stimulus_message, stimulus_ts = fetcher.get_first_sip_invite(
        "chfe_bridge", return_timestamp=True
    )

    if not stimulus_message:
        return (
            stimulus_message,
            is_http_post,
            jws_data,
            call_signaling_log_event,
            response_code,
            expected_response_code,
        )

    # Single BRIDGE to LOGGER LogEvents POST request expected per variation
    post_message, post_ts = fetcher.get_first_http_post(
        "bridge_logger", after_timestamp=stimulus_ts, return_timestamp=True
    )
    post_http_msg = HttpMessage.from_packet(post_message) if post_message else None

    if post_http_msg:
        target_path = urlparse(post_http_msg.request_target).path.rstrip("/")
        is_http_post = (
            post_http_msg.method == "POST"
            and target_path == log_event_endpoint
            and not urlparse(post_http_msg.request_target).query
        )

        jws_data = extract_json_data_from_http(post_message)

        # Extract CallSignalingMessageLogEvent payload from the JWS body
        payload_data = None
        if isinstance(jws_data, dict):
            payload_data = get_json(decode_base64url(jws_data.get("payload")))

        call_signaling_log_event = (
            CallSignalingMessageLogEvent(payload_data)
            if isinstance(payload_data, dict)
            and payload_data.get("logEventType") == "CallSignalingMessageLogEvent"
            else None
        )

        # LOGGER to BRIDGE response to the LogEvents POST request
        response_message = fetcher.get_first_http(
            "logger_bridge", after_timestamp=post_ts
        )
        response_http_msg = (
            HttpMessage.from_packet(response_message) if response_message else None
        )
        response_code = (
            str(response_http_msg.status_code) if response_http_msg else None
        )

    return (
        stimulus_message,
        is_http_post,
        jws_data,
        call_signaling_log_event,
        response_code,
        expected_response_code,
    )


def get_test_names() -> list:
    test_names_list = [
        "Verify BRIDGE sends HTTP POST to the LogEvents entry point with no query parameters",
        "Verify BRIDGE sends a valid JWS body",
        "Verify BRIDGE sends HTTP POST with CallSignalingMessageLogEvent message",
        "Verify BRIDGE sends a 200 OK response",
    ]
    return test_names_list


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    (
        stimulus_message,
        is_http_post,
        jws_data,
        call_signaling_log_event,
        response_code,
        expected_response_code,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, run_variation)

    return [
        TestCheck(
            test_name="Verify BRIDGE sends HTTP POST to the LogEvents entry point with no query parameters",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_method=is_data_present,
            test_params={
                "test_data": is_http_post,
                "error": "FAILED -> No HTTP POST to the LogEvents entry point with no query parameters was found",
            },
        ),
        TestCheck(
            test_name="Verify BRIDGE sends a valid JWS body",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_method=validate_flattened_jws,
            test_params={
                "jws": jws_data,
            },
        ),
        TestCheck(
            test_name="Verify BRIDGE sends HTTP POST with CallSignalingMessageLogEvent message",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_method=is_data_present,
            test_params={
                "test_data": call_signaling_log_event,
                "error": "FAILED -> No HTTP POST with a valid CallSignalingMessageLogEvent message was found",
            },
        ),
        TestCheck(
            test_name="Verify BRIDGE sends a 200 OK response",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": expected_response_code,
                "actual_data": response_code,
                "error": "FAILED -> No 200 OK response to the LogEvents POST request was found",
            },
        ),
    ]
