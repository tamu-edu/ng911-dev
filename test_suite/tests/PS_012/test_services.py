from urllib.parse import urlparse

from checks.general.checks import (
    is_test_data_the_same,
    is_data_present,
)
from checks.jws.checks import validate_flattened_jws
from checks.log_events.log_events import PolicyChangeLogEvent
from enums import PacketTypeEnum, HTTPMethodEnum
from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.json_services import decode_base64url, get_json
from services.aux_services.message_services import (
    extract_json_data_from_http,
    get_http_response_containing_string_in_http_body_for_message_matching_filter,
    get_messages,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import FilterConfig, PcapCaptureService
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip,
             expected_stimulus_response_code, expected_policy_update_response_code,
             policy_get_url, policy_update_url, logger_url), strings

    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_src_ip = None
    out_dst_ip = None
    expected_stimulus_response_code = None
    expected_policy_update_response_code = None
    policy_get_url = None
    policy_update_url = None
    logger_url = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            expected_policy_update_response_code = message.response_status_code
            policy_update_url = message.header_contains
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message
            logger_url = message.header_contains
        elif message.message_type == FilterMessageType.OTHER:
            expected_stimulus_response_code = message.response_status_code
            policy_get_url = message.header_contains

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                if output:
                    if interface.name == output.src_interface:
                        out_src_ip = interface.ip
                    elif interface.name == output.dst_interface:
                        out_dst_ip = interface.ip
        if not all(
            [
                stimulus_src_ip,
                stimulus_dst_ip,
                out_src_ip,
                out_dst_ip,
                expected_stimulus_response_code,
                expected_policy_update_response_code,
                policy_get_url,
                policy_update_url,
                logger_url,
            ]
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters."
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_src_ip,
                out_dst_ip,
                expected_stimulus_response_code,
                expected_policy_update_response_code,
                policy_get_url,
                policy_update_url,
                logger_url,
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
    variation: RunVariation,
):
    """
    :return: Tuple (stimulus_message, stimulus_response_code,
             expected_stimulus_response_code, mod_policy, mod_policy_response_code,
             expected_policy_update_response_code, jws_data, log_event_payload)
    """
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        expected_stimulus_response_code,
        expected_policy_update_response_code,
        policy_get_url,
        policy_update_url,
        logger_url,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    jws_data = None
    log_event_payload = None
    stimulus_response_code = None
    mod_policy_response_code = None
    is_no_parameter_in_url = False

    # TS ESRP -> PS: POST /Policies
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

    # PS -> TS ESRP response to the stimulus
    if stimulus_message:
        stimulus_response = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.POST,
                ],
            ),
            uri=policy_get_url,
        )

        if stimulus_response:
            if hasattr(stimulus_response.http, "response_code"):
                stimulus_response_code = stimulus_response.http.response_code

    # TS ESRP -> PS: PUT /Policies?policyOwner
    mod_policy = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.PUT,
            ],
        ),
    )

    if mod_policy:
        mod_policy_response = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.PUT,
                ],
            ),
            uri=policy_update_url,
        )

        if mod_policy_response:
            if hasattr(mod_policy_response.http, "response_code"):
                mod_policy_response_code = mod_policy_response.http.response_code

    # PS -> TS LOGGER
    policy_store_log_event_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_src_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    if policy_store_log_event_messages:
        for message in policy_store_log_event_messages:
            request_uri = getattr(message.http, "request_uri", None)
            if request_uri:
                if request_uri != logger_url:
                    continue
            message_jws = extract_json_data_from_http(message)

            if request_uri and not urlparse(request_uri).query:
                is_no_parameter_in_url = True

            if jws_data is None:
                # Keep the first JWS as a fallback so the JWS check still has data
                jws_data = message_jws

            payload_data = None
            if isinstance(message_jws, dict):
                payload_data = get_json(decode_base64url(message_jws.get("payload")))

            if (
                isinstance(payload_data, dict)
                and payload_data.get("logEventType") == "PolicyChangeLogEvent"
            ):
                # Use the first PolicyChangeLogEvent; later messages must not overwrite it
                jws_data = message_jws
                log_event_payload = PolicyChangeLogEvent(payload_data)
                break

    return (
        stimulus_message,
        stimulus_response_code,
        expected_stimulus_response_code,
        mod_policy,
        mod_policy_response_code,
        expected_policy_update_response_code,
        jws_data,
        log_event_payload,
        is_no_parameter_in_url,
    )


def get_test_names() -> list:
    return [
        "Verify PS returns 201 Policy Successfully Created for the POST request",
        "Verify PS returns 200 Policy Successfully Updated for the PUT request",
        "Verify PS request target endpoint with no query parameters",
        "Verify PS sends a valid JWS structure",
        "Verify PS sends a valid logEventType",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_message,
        stimulus_response_code,
        expected_stimulus_response_code,
        mod_policy,
        mod_policy_response_code,
        expected_policy_update_response_code,
        jws_data,
        log_event_payload,
        is_no_parameter_in_url,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify PS returns 201 Policy Successfully Created for the POST request",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": str(expected_stimulus_response_code),
                "actual_data": stimulus_response_code,
                "error": "FAILED -> PS did not return 201 OK for Policy Successfully Created for the POST request",
            },
        ),
        TestCheck(
            test_name="Verify PS returns 200 Policy Successfully Updated for the PUT request",
            precondition=mod_policy,
            precondition_error="NOT RUN -> No HTTP PUT from TestSystem found.",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": str(expected_policy_update_response_code),
                "actual_data": mod_policy_response_code,
                "error": "FAILED -> PS did not return 200 OK for Successfully Updated for the PUT request",
            },
        ),
        TestCheck(
            test_name="Verify PS request target endpoint with no query parameters",
            test_method=is_data_present,
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_params={
                "test_data": is_no_parameter_in_url,
                "error": "FAILED -> Found a request with an unexpected query parameter or endpoint format.",
            },
        ),
        TestCheck(
            test_name="Verify PS sends a valid JWS structure",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus message found.",
            test_method=validate_flattened_jws,
            test_params={"jws": jws_data},
        ),
        TestCheck(
            test_name="Verify PS sends a valid logEventType",
            precondition=log_event_payload,
            precondition_error="NOT RUN -> No valid logEventType found.",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": "PolicyChangeLogEvent",
                "actual_data": (
                    log_event_payload.logEventType if log_event_payload else None
                ),
                "error": "FAILED -> No valid logEvent data found.",
            },
        ),
    ]
