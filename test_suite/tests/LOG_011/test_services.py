import json

from checks.general.checks import is_data_present, is_test_data_the_same
from services.aux_services.json_services import decode_base64url
from services.aux_services.message_services import (
    extract_json_data_from_http,
    get_http_response_containing_string_in_http_body_for_message_matching_filter,
    get_messages,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LOG_011.checks import (
    validate_incident_id_recorded,
)


def output_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, other_src_ip, other_dst_ip, log_url,
    incidents_url, response_status_code)
    """
    stimulus = None
    output = None

    stimulus_src_ip = None
    stimulus_dst_ip = None
    other_src_ip = None
    other_dst_ip = None
    incidents_url = None
    log_url = None
    response_status_code = None

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            log_url = message.header_contains
            response_status_code = message.response_status_code
        elif message.message_type == FilterMessageType.OTHER:
            output = message
            incidents_url = message.header_contains

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    other_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    other_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or other_src_ip is None
            or other_dst_ip is None
            or incidents_url is None
            or log_url is None
            or response_status_code is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required"
                "parameters for ts_esrp_ip, log_ip addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                other_src_ip,
                other_dst_ip,
                log_url,
                incidents_url,
                response_status_code,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def _http_request_matches(message_http, method: str, uri: str) -> bool:
    return (
        hasattr(message_http, "request_method")
        and message_http.request_method == method
        and hasattr(message_http, "request_uri")
        and message_http.request_uri == uri
    )


def _get_nested_attr(obj, *attrs, default=None):
    for attr in attrs:
        if not hasattr(obj, attr):
            return default
        obj = getattr(obj, attr)
    return obj


def _extract_incident_id(jws_request_body):
    """
    Decodes the 'payload' segment of a LogEvent JWS and extracts 'incidentId'.
    """
    payload_b64 = (
        jws_request_body.get("payload") if isinstance(jws_request_body, dict) else None
    )
    if not payload_b64:
        return None

    decoded_payload = decode_base64url(payload_b64)
    if not decoded_payload:
        return None

    try:
        payload_data = json.loads(decoded_payload)
    except json.JSONDecodeError:
        return None

    return payload_data.get("incidentId")


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        other_src_ip,
        other_dst_ip,
        log_url,
        incidents_url,
        response_status_code,
    ) = output_parameters(lab_config, filtering_options, variation)

    stimulus_message = None
    incident_ids_request = None

    # HTTP POST request carrying the LogEvent JWS with a failed signature
    stimulus_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
        ),
    )

    for message in stimulus_messages:
        if _http_request_matches(message.http, "POST", log_url):
            stimulus_message = message
        elif _http_request_matches(message.http, "GET", incidents_url):
            incident_ids_request = message

    jws_request_body = (
        extract_json_data_from_http(stimulus_message) if stimulus_message else None
    )
    incident_id = _extract_incident_id(jws_request_body)

    # Response to HTTP POST /LogEvents - expected to be 434, reported as a warning
    post_response = (
        get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
            ),
            uri=log_url,
        )
    )
    response_code = _get_nested_attr(post_response, "http", "response_code")

    # Response to HTTP GET /IncidentIds - used to confirm LogEvent was still recorded
    incident_ids_response = (
        get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=other_src_ip,
                dst_ip=other_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.GET],
            ),
            uri=incidents_url,
        )
    )

    return (
        stimulus_message,
        incident_ids_request,
        response_code,
        jws_request_body,
        incident_id,
        incident_ids_response,
        response_status_code,
    )


def get_test_names() -> list:
    return [
        "Validate HTTP POST to /LogEvents returns a response code.",
        "Validate HTTP POST to /LogEvents returns 'Signature Verification Failed' (434) warning.",
        "Validate LogEvent with failed signature verification is still recorded in HTTP GET /IncidentIds response.",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_message,
        incident_ids_request,
        response_code,
        jws_request_body,
        incident_id,
        incident_ids_response,
        response_status_code,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Validate HTTP POST to /LogEvents returns a response code.",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> Cannot find POST stimulus message",
            test_method=is_data_present,
            test_params={
                "test_data": response_code,
                "error": "FAILED -> No response code from LOGGER found",
            },
        ),
        TestCheck(
            test_name="Validate HTTP POST to /LogEvents returns 'Signature Verification Failed' (434) warning.",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> Cannot find POST stimulus message",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": response_status_code,
                "actual_data": response_code,
            },
        ),
        TestCheck(
            test_name="Validate LogEvent with failed signature verification is still recorded in HTTP GET /IncidentIds response.",
            precondition=incident_ids_request,
            precondition_error="NOT RUN -> Cannot find GET stimulus message",
            test_method=validate_incident_id_recorded,
            test_params={
                "incident_id": incident_id,
                "incident_ids_response": incident_ids_response,
            },
        ),
    ]
