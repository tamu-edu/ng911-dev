from dataclasses import dataclass, field
from functools import partial
from typing import List, Optional

from pyshark.packet.packet import Packet

from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
    validate_json_equality,
)
from checks.log_events.checks import (
    get_jws_payloads_list_by_log_event_type,
    validate_optional_log_event_fields,
    verify_timestamp_format,
)
from checks.log_events.log_events import VersionsLogEvent
from services.aux_services.json_services import is_valid_fqdn
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation, MessageFilter
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestCheck
from tests.PS_014.constants import (
    LOG_EVENT_TYPE,
    NOT_RUN_NO_LOGGER_RESPONSE,
    VERSIONS_URL_PART,
    NO_PS_LOGGER_POST,
    NO_PS_GET_VERSIONS,
    NO_JWS_POST,
)


def get_filter_parameters(
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (output_src_ip, output_dst_ip, ps_fqdn, key_filepath, log_events_endpoint)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    output = messages_by_type.get(FilterMessageType.OUTPUT)

    if not output:
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

    output_src_ip = ip_by_interface_name.get(output.src_interface)
    output_dst_ip = ip_by_interface_name.get(output.dst_interface)

    if None in (output_src_ip, output_dst_ip):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    iut_entity = lab_config.get_conformance_iut_entity()
    ps_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None
    if not ps_fqdn:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required FQDN records for Policy Store interfaces"
        )

    log_events_endpoint = output.header_contains

    return output_src_ip, output_dst_ip, ps_fqdn, key_filepath, log_events_endpoint


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    ps_fqdn: Optional[str] = None

    ps_get_versions_message: Optional[Packet] = None
    ps_get_versions_url: Optional[str] = None
    logger_ps_versions_response_message: Optional[Packet] = None
    logger_ps_versions_response_body: Optional[str] = None
    ps_logger_event_post_messages: Optional[List[Packet]] = None
    ps_logger_jws_payload: Optional[dict] = None
    versions_log_event: VersionsLogEvent = field(default_factory=VersionsLogEvent)


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
) -> TestData:
    output_src_ip, output_dst_ip, ps_fqdn, key_filepath, log_events_endpoint = (
        get_filter_parameters(lab_config, filtering_options)
    )

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("ps_log", output_src_ip, output_dst_ip)

    data: dict = {"ps_fqdn": ps_fqdn}

    # Policy Store to LOGGER GET /Versions request
    ps_get_versions_message = fetcher.get_first_http_get(
        "ps_log", url_contains=VERSIONS_URL_PART
    )
    data["ps_get_versions_message"] = ps_get_versions_message
    if not ps_get_versions_message:
        return TestData(**data)

    # Get URL used by the Policy Store
    ps_get_versions_msg = HttpMessage.from_packet(ps_get_versions_message)
    data["ps_get_versions_url"] = (
        ps_get_versions_msg.request_target if ps_get_versions_msg else None
    )

    # Get LOGGER to Policy Store response to the GET /Versions request
    logger_ps_versions_response_message, logger_ps_versions_response_ts = (
        fetcher.get_http_response_for(
            "log_ps", ps_get_versions_message, return_timestamp=True
        )
    )
    data["logger_ps_versions_response_message"] = logger_ps_versions_response_message
    if not logger_ps_versions_response_message:
        return TestData(**data)

    response_msg = HttpMessage.from_packet(logger_ps_versions_response_message)
    data["logger_ps_versions_response_body"] = (
        (response_msg.body or None) if response_msg else None
    )

    # Policy Store to LOGGER LogEvents POSTs after the response, first VersionsLogEvent payload
    ps_logger_event_post_messages = fetcher.get_http_posts(
        "ps_log",
        after_timestamp=logger_ps_versions_response_ts,
        url_contains=log_events_endpoint,
    )
    data["ps_logger_event_post_messages"] = ps_logger_event_post_messages
    if not ps_logger_event_post_messages:
        return TestData(**data)

    ps_logger_jws_payloads = get_jws_payloads_list_by_log_event_type(
        ps_logger_event_post_messages, LOG_EVENT_TYPE, key_filepath
    )
    payload = ps_logger_jws_payloads[0] if ps_logger_jws_payloads else None
    data["ps_logger_jws_payload"] = payload
    if payload:
        data["versions_log_event"] = VersionsLogEvent(payload)

    return TestData(**data)


def _payload_precondition(test_data: TestData) -> tuple[bool, str]:
    """
    Base precondition for VersionsLogEvent field checks:
    FAILED without GET /Versions, POST or JWS, NOT RUN without LOGGER response.
    """
    if not test_data.ps_get_versions_message:
        return False, NO_PS_GET_VERSIONS
    if not test_data.logger_ps_versions_response_message:
        return False, NOT_RUN_NO_LOGGER_RESPONSE
    if not test_data.ps_logger_event_post_messages:
        return False, NO_PS_LOGGER_POST
    if not test_data.ps_logger_jws_payload:
        return False, NO_JWS_POST
    return True, ""


def _field_precondition(
    base_precondition: bool, base_error: str, payload: Optional[dict], field_name: str
) -> dict:
    """Base precondition + presence of the mandatory field in the payload."""
    if not base_precondition:
        return {"precondition": False, "precondition_error": base_error}
    if field_name not in payload:
        return {
            "precondition": False,
            "precondition_error": f"FAILED -> '{field_name}' member is missing in {LOG_EVENT_TYPE}",
        }
    return {"precondition": True, "precondition_error": base_error}


def get_test_names() -> list:
    return [
        "Verify that Policy Store GET /Versions request is present",
        "Verify that LOGGER to Policy Store response for GET /Versions request is present",
        "Verify that Policy Store sends HTTP POST to LOGGER LogEvents endpoint",
        "Verify that Policy Store HTTP POST contains VersionsLogEvent JWS",
        "Verify VersionsLogEvent 'logEventType' value is 'VersionsLogEvent'",
        "Verify VersionsLogEvent 'timestamp' value format",
        "Verify VersionsLogEvent 'elementId' value is Policy Store FQDN",
        "Verify VersionsLogEvent 'agencyId' value is a valid FQDN",
        "Verify VersionsLogEvent 'source' value is the URL used for GET /Versions",
        "Verify VersionsLogEvent 'response' value is the Versions JSON response from LOGGER",
        "Verify VersionsLogEvent optional fields",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    test_data = get_test_parameters(pcap_service, lab_config, filtering_options)

    has_get = bool(test_data.ps_get_versions_message)
    has_response = has_get and bool(test_data.logger_ps_versions_response_message)
    has_posts = has_response and bool(test_data.ps_logger_event_post_messages)

    payload = test_data.ps_logger_jws_payload
    event = test_data.versions_log_event

    payload_precondition, payload_error = _payload_precondition(test_data)
    field_precondition = partial(
        _field_precondition, payload_precondition, payload_error, payload
    )

    # Optional fields check is shown only when the event contains at least one optional field
    has_optional_fields = bool(payload) and any(
        field_name in payload for field_name in VersionsLogEvent.optional_fields()
    )

    check_list = [
        TestCheck(
            test_name="Verify that Policy Store GET /Versions request is present",
            test_method=is_data_present,
            test_params={
                "test_data": test_data.ps_get_versions_message,
                "error": NO_PS_GET_VERSIONS,
            },
        ),
        TestCheck(
            test_name="Verify that LOGGER to Policy Store response for GET /Versions request is present",
            test_method=is_data_present,
            precondition=has_get,
            precondition_error=NO_PS_GET_VERSIONS,
            test_params={
                "test_data": test_data.logger_ps_versions_response_message,
                "error": NOT_RUN_NO_LOGGER_RESPONSE,
            },
        ),
        TestCheck(
            test_name="Verify that Policy Store sends HTTP POST to LOGGER LogEvents endpoint",
            test_method=is_data_present,
            precondition=has_response,
            precondition_error=(
                NOT_RUN_NO_LOGGER_RESPONSE if has_get else NO_PS_GET_VERSIONS
            ),
            test_params={
                "test_data": test_data.ps_logger_event_post_messages,
                "error": NO_PS_LOGGER_POST,
            },
        ),
        TestCheck(
            test_name="Verify that Policy Store HTTP POST contains VersionsLogEvent JWS",
            test_method=is_data_present,
            precondition=has_posts,
            precondition_error=(
                NO_PS_GET_VERSIONS
                if not has_get
                else (
                    NOT_RUN_NO_LOGGER_RESPONSE
                    if not has_response
                    else NO_PS_LOGGER_POST
                )
            ),
            test_params={
                "test_data": payload,
                "error": NO_JWS_POST,
            },
        ),
        TestCheck(
            test_name="Verify VersionsLogEvent 'logEventType' value is 'VersionsLogEvent'",
            test_method=is_test_data_the_same,
            **field_precondition("logEventType"),
            test_params={
                "expected_data": LOG_EVENT_TYPE,
                "actual_data": event.logEventType,
            },
        ),
        TestCheck(
            test_name="Verify VersionsLogEvent 'timestamp' value format",
            test_method=verify_timestamp_format,
            **field_precondition("timestamp"),
            test_params={
                "timestamp": event.timestamp,
            },
        ),
        TestCheck(
            test_name="Verify VersionsLogEvent 'elementId' value is Policy Store FQDN",
            test_method=is_test_data_the_same,
            **field_precondition("elementId"),
            test_params={
                "expected_data": test_data.ps_fqdn,
                "actual_data": event.elementId,
            },
        ),
        TestCheck(
            test_name="Verify VersionsLogEvent 'agencyId' value is a valid FQDN",
            test_method=is_data_present,
            **field_precondition("agencyId"),
            test_params={
                "test_data": isinstance(event.agencyId, str)
                and is_valid_fqdn(event.agencyId),
                "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record. Actual: {event.agencyId!r}",
            },
        ),
        TestCheck(
            test_name="Verify VersionsLogEvent 'source' value is the URL used for GET /Versions",
            test_method=is_test_data_the_same,
            **field_precondition("source"),
            test_params={
                "expected_data": test_data.ps_get_versions_url,
                "actual_data": event.source,
            },
        ),
        TestCheck(
            test_name="Verify VersionsLogEvent 'response' value is the Versions JSON response from LOGGER",
            test_method=validate_json_equality,
            **field_precondition("response"),
            test_params={
                "expected_data": test_data.logger_ps_versions_response_body,
                "actual_data": event.response,
                "error": f"{LOG_EVENT_TYPE} 'response' value is not the same as LOGGER GET /Versions response body",
            },
        ),
    ]

    if has_optional_fields:
        check_list.append(
            TestCheck(
                test_name="Verify VersionsLogEvent optional fields",
                test_method=validate_optional_log_event_fields,
                precondition=payload_precondition,
                precondition_error=payload_error,
                test_params={
                    "log_event_class": test_data.versions_log_event,
                    "raw_payload": test_data.ps_logger_jws_payload,
                },
            )
        )

    return check_list
