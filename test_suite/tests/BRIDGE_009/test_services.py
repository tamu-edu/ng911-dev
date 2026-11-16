from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from checks.general.checks import is_data_present, is_test_data_the_same
from checks.http.checks import validate_response_code_class
from checks.log_events.log_events import CallSignalingMessageLogEvent
from services.aux_services.json_services import decode_base64url, get_json
from services.aux_services.message_services import extract_json_data_from_http
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestCheck
from tests.BRIDGE_009.checks import (
    check_protected_header_alg_present_once,
    get_first_sip_response,
    get_raw_http_body,
    validate_jws_format,
)

SERVICE_STATE_EVENT = "emergency-ServiceState"


def _strip_file_prefix(path: str | None) -> str | None:
    return path.removeprefix("file.") if path else path


class Variation(Enum):
    LOG_EVENT = 1  # BRIDGE reports to LOGGER with a LogEvents POST
    POLICY_REJECTED = 2  # Policy rejected -> 4xx to SUBSCRIBE
    POLICY_APPLIED = 3  # Policy applied -> 200 OK to SUBSCRIBE and NOTIFY back


@dataclass(frozen=True)
class FilterParams:
    stimulus_src_ip: str
    stimulus_dst_ip: str
    second_src_ip: str
    second_dst_ip: str
    stimulus_expected_response: str | None
    output_expected_response: str | None
    second_endpoint: str | None
    variation: Variation
    bridge_cert_path: str | None
    bridge_key_path: str | None


@dataclass
class CapturedMessages:
    # Variation 1
    stimulus_message: Any = None
    stimulus_response: Any = None
    stimulus_response_code: str | None = None
    logevents_post: Any = None
    call_signaling_log_event: CallSignalingMessageLogEvent | None = None
    # Variations 2/3
    policy_request: Any = None
    subscribe: Any = None
    subscribe_response_code: str | None = None
    # Variation 3 only
    notify: Any = None
    notify_response_code: str | None = None


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
) -> FilterParams:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: FilterParams. The 'second' filter is 'output' (LogEvents POST) for variation 1
        and 'other' (Policy Store GET) for variations 2/3
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    other = messages_by_type.get(FilterMessageType.OTHER)

    if not (stimulus and (output or other)):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )
    second = output or other

    # Variation is defined by the expected response to the stimulus:
    # Variation 1 - 'output' (LogEvents POST) filter, Variation 2 - '4xx', Variation 3 - '200'
    if output is not None:
        variation = Variation.LOG_EVENT
    elif stimulus.response_status_code == "4xx":
        variation = Variation.POLICY_REJECTED
    elif stimulus.response_status_code == "200":
        variation = Variation.POLICY_APPLIED
    else:
        raise WrongConfigurationError(
            "Stimulus 'response_status_code' for variations 2/3 must be '4xx' or '200', "
            f"got '{stimulus.response_status_code}'"
        )

    ip_by_interface_name = {}
    bridge_cert_path = bridge_key_path = None
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip
            if interface.name == second.src_interface:
                bridge_cert_path = _strip_file_prefix(entity.certificate_file)
                bridge_key_path = _strip_file_prefix(entity.certificate_key)

    stimulus_src_ip = ip_by_interface_name.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface_name.get(stimulus.dst_interface)
    second_src_ip = ip_by_interface_name.get(second.src_interface)
    second_dst_ip = ip_by_interface_name.get(second.dst_interface)

    if None in (stimulus_src_ip, stimulus_dst_ip, second_src_ip, second_dst_ip):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return FilterParams(
        stimulus_src_ip=stimulus_src_ip,
        stimulus_dst_ip=stimulus_dst_ip,
        second_src_ip=second_src_ip,
        second_dst_ip=second_dst_ip,
        stimulus_expected_response=stimulus.response_status_code,
        output_expected_response=output.response_status_code if output else None,
        second_endpoint=second.header_contains,
        variation=variation,
        bridge_cert_path=bridge_cert_path,
        bridge_key_path=bridge_key_path,
    )


def _capture_log_event_flow(
    fetcher: PacketFetcher, params: FilterParams, captured: CapturedMessages
) -> None:
    fetcher.add_route("bridge_logger", params.second_src_ip, params.second_dst_ip)
    captured.stimulus_message, stimulus_ts = fetcher.get_first_sip_invite(
        "chfe_bridge", return_timestamp=True
    )
    if not captured.stimulus_message:
        return

    captured.stimulus_response = get_first_sip_response(
        fetcher.get_sip_messages("bridge_chfe", after_timestamp=stimulus_ts),
        "INVITE",
    )
    if captured.stimulus_response:
        captured.stimulus_response_code = str(
            captured.stimulus_response.sip.status_code
        )
    # Single BRIDGE to LOGGER LogEvents POST request expected per variation
    captured.logevents_post = fetcher.get_first_http_post(
        "bridge_logger", after_timestamp=stimulus_ts
    )
    if captured.logevents_post:
        captured.call_signaling_log_event = get_call_signaling_log_event(
            captured.logevents_post
        )


def _capture_service_state_flow(
    fetcher: PacketFetcher, params: FilterParams, captured: CapturedMessages
) -> None:
    fetcher.add_route("bridge_ps", params.second_src_ip, params.second_dst_ip)
    captured.policy_request = fetcher.get_first_http_get(
        "bridge_ps", url_contains=params.second_endpoint
    )
    captured.subscribe, subscribe_ts = fetcher.get_first_sip_subscribe(
        "chfe_bridge", event=SERVICE_STATE_EVENT, return_timestamp=True
    )
    if not captured.subscribe:
        return

    is_applied = params.variation is Variation.POLICY_APPLIED
    subscribe_call_id = SipMessage.from_packet(captured.subscribe).call_id
    # Variation 3: policy applied -> 200 OK expected
    if is_applied:
        subscribe_response = fetcher.get_first_sip_ok(
            "bridge_chfe", after_timestamp=subscribe_ts, call_id=subscribe_call_id
        )
    # Variation 2: policy rejected -> final non-200 response (4xx) expected
    else:
        subscribe_response = get_first_sip_response(
            fetcher.get_sip_messages(
                "bridge_chfe", after_timestamp=subscribe_ts, call_id=subscribe_call_id
            ),
            "SUBSCRIBE",
        )
    if subscribe_response:
        captured.subscribe_response_code = str(subscribe_response.sip.status_code)

    # Variation 3 only: BRIDGE reports the state back with NOTIFY
    if not is_applied:
        return
    captured.notify, notify_ts = fetcher.get_first_sip_notify(
        "bridge_chfe",
        after_timestamp=subscribe_ts,
        event=SERVICE_STATE_EVENT,
        return_timestamp=True,
    )
    if captured.notify:
        notify_response = fetcher.get_first_sip_ok(
            "chfe_bridge",
            after_timestamp=notify_ts,
            call_id=SipMessage.from_packet(captured.notify).call_id,
        )
        if notify_response:
            captured.notify_response_code = str(notify_response.sip.status_code)


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> tuple[FilterParams, CapturedMessages]:
    """
    Extracts all messages required by the variation from the pcap file.

    Variation 1: stimulus_message, stimulus_response, stimulus_response_code, logevents_post,
        call_signaling_log_event
    Variation 2: policy_request, subscribe, subscribe_response_code
    Variation 3: Variation 2 messages + notify, notify_response_code

    :return: Tuple of (FilterParams, CapturedMessages). Captured values not relevant for
        the variation or not found are None
    """
    params = get_filter_parameters(lab_config, filtering_options)
    captured = CapturedMessages()

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("chfe_bridge", params.stimulus_src_ip, params.stimulus_dst_ip)

    if params.variation is Variation.LOG_EVENT:
        _capture_log_event_flow(fetcher, params, captured)
    else:
        _capture_service_state_flow(fetcher, params, captured)
    return params, captured


def get_call_signaling_log_event(logevents_post) -> CallSignalingMessageLogEvent | None:
    """Extract CallSignalingMessageLogEvent from the JWS payload of the captured LogEvents POST."""
    jws_data = extract_json_data_from_http(logevents_post) if logevents_post else None
    payload_data = (
        get_json(decode_base64url(jws_data.get("payload")))
        if isinstance(jws_data, dict)
        else None
    )
    if (
        isinstance(payload_data, dict)
        and payload_data.get("logEventType") == "CallSignalingMessageLogEvent"
    ):
        return CallSignalingMessageLogEvent(payload_data)
    return None


def get_log_event_data(logevents_post, endpoint: str) -> tuple:
    """Derive (is_http_post, jws_data, raw_body) from the captured LogEvents POST."""
    post_http_msg = HttpMessage.from_packet(logevents_post) if logevents_post else None
    if not post_http_msg:
        return False, None, None

    request_target = urlparse(post_http_msg.request_target)
    is_http_post = (
        post_http_msg.method == "POST"
        and request_target.path.rstrip("/") == endpoint
        and not request_target.query
    )
    return (
        is_http_post,
        extract_json_data_from_http(logevents_post),
        get_raw_http_body(logevents_post),
    )


def get_test_names() -> list:
    return [
        # Variation 1
        "Verify BRIDGE response to the INVITE stimulus",
        "Verify BRIDGE sends HTTP POST to the LogEvents entry point with no query parameters",
        "Verify JWS Protected Header contains exactly one 'alg' field",
        "Verify BRIDGE sends a valid JWS (flattened format, alg, signature, certificate chain, payload)",
        "Verify JWS payload contains a valid LogEvent",
        # Variations 2/3
        "Verify BRIDGE fetches policies from the Policy Store",
        "Verify BRIDGE response to SIP SUBSCRIBE",
        # Variation 3
        "Verify BRIDGE sends SIP NOTIFY with Event emergency-ServiceState",
        "Verify BRIDGE response to SIP NOTIFY",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    params, captured = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation
    )
    stimulus_expected_response = params.stimulus_expected_response
    second_endpoint = params.second_endpoint
    bridge_cert_path = params.bridge_cert_path
    bridge_key_path = params.bridge_key_path
    stimulus_message = captured.stimulus_message
    stimulus_response_code = captured.stimulus_response_code
    logevents_post = captured.logevents_post
    call_signaling_log_event = captured.call_signaling_log_event
    policy_request = captured.policy_request
    subscribe = captured.subscribe
    subscribe_response_code = captured.subscribe_response_code
    notify = captured.notify
    notify_response_code = captured.notify_response_code
    is_var2 = params.variation is Variation.POLICY_REJECTED
    is_var3 = params.variation is Variation.POLICY_APPLIED

    if params.variation is Variation.LOG_EVENT:
        is_http_post, jws_data, raw_body = get_log_event_data(
            logevents_post, second_endpoint
        )
        return [
            TestCheck(
                test_name="Verify BRIDGE response to the INVITE stimulus",
                precondition=stimulus_message,
                precondition_error="NOT RUN -> No stimulus message found.",
                test_method=is_test_data_the_same,
                test_params={
                    "expected_data": stimulus_expected_response,
                    "actual_data": stimulus_response_code,
                    "error": f"FAILED -> No {stimulus_expected_response} response to the INVITE was found",
                },
            ),
            TestCheck(
                test_name="Verify BRIDGE sends HTTP POST to the LogEvents entry point with no query parameters",
                test_method=is_data_present,
                test_params={
                    "test_data": is_http_post,
                    "error": "FAILED -> No HTTP POST to the LogEvents entry point with no query parameters was found",
                },
                precondition=stimulus_message,
                precondition_error="NOT RUN -> No stimulus message found.",
            ),
            TestCheck(
                test_name="Verify JWS Protected Header contains exactly one 'alg' field",
                test_method=check_protected_header_alg_present_once,
                test_params={"raw_body": raw_body},
                precondition=raw_body,
                precondition_error="FAILED -> No LogEvents POST body found.",
            ),
            TestCheck(
                test_name="Verify BRIDGE sends a valid JWS (flattened format, alg, signature, certificate chain, payload)",
                test_method=validate_jws_format,
                test_params={
                    "raw_body": raw_body,
                    "jws_data": jws_data,
                    "cert_filepath": bridge_cert_path,
                    "key_filepath": bridge_key_path,
                },
                precondition=raw_body,
                precondition_error="FAILED -> No LogEvents POST body found.",
            ),
            TestCheck(
                test_name="Verify JWS payload contains a valid LogEvent",
                test_method=is_data_present,
                test_params={
                    "test_data": call_signaling_log_event,
                    "error": "FAILED -> No valid CallSignalingMessageLogEvent was found in the JWS payload",
                },
                precondition=raw_body,
                precondition_error="FAILED -> No LogEvents POST body found.",
            ),
        ]

    checks = [
        TestCheck(
            test_name="Verify BRIDGE fetches policies from the Policy Store",
            test_method=is_data_present,
            test_params={
                "test_data": policy_request,
                "error": "FAILED -> No HTTP GET request to the Policy Store ServiceState entry point was found",
            },
        ),
    ]
    # Variation 2 (policy rejected): 4xx class expected
    if is_var2:
        checks.append(
            TestCheck(
                test_name="Verify BRIDGE response to SIP SUBSCRIBE",
                precondition=subscribe,
                precondition_error="NOT RUN -> No SIP SUBSCRIBE with Event emergency-ServiceState found.",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": stimulus_expected_response,
                    "response_code": subscribe_response_code,
                },
            )
        )
    # Variation 3 (policy applied): 200 OK expected, BRIDGE must also send NOTIFY back
    elif is_var3:
        checks.append(
            TestCheck(
                test_name="Verify BRIDGE response to SIP SUBSCRIBE",
                precondition=subscribe,
                precondition_error="NOT RUN -> No SIP SUBSCRIBE with Event emergency-ServiceState found.",
                test_method=is_test_data_the_same,
                test_params={
                    "expected_data": stimulus_expected_response,
                    "actual_data": subscribe_response_code,
                    "error": f"FAILED -> No {stimulus_expected_response} response to the SIP SUBSCRIBE was found",
                },
            )
        )
        checks.append(
            TestCheck(
                test_name="Verify BRIDGE sends SIP NOTIFY with Event emergency-ServiceState",
                test_method=is_data_present,
                test_params={
                    "test_data": notify,
                    "error": "FAILED -> No SIP NOTIFY with Event emergency-ServiceState was found",
                },
                precondition=subscribe,
                precondition_error="NOT RUN -> No SIP SUBSCRIBE with Event emergency-ServiceState found.",
            )
        )
        checks.append(
            TestCheck(
                test_name="Verify BRIDGE response to SIP NOTIFY",
                precondition=notify,
                precondition_error="NOT RUN -> No SIP NOTIFY with Event emergency-ServiceState found.",
                test_method=is_test_data_the_same,
                test_params={
                    "expected_data": "200",
                    "actual_data": notify_response_code,
                    "error": "FAILED -> No 200 OK response to the SIP NOTIFY was found",
                },
            )
        )
    return checks
