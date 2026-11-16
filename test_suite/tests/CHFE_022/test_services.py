from dataclasses import dataclass
from functools import partial
from typing import Optional
from urllib.parse import urlparse

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present, is_test_data_the_same
from checks.http.checks import is_type
from checks.log_events.checks import (
    extract_enclosed_value,
    get_payload_field,
    verify_timestamp_format,
    verify_call_id_format,
    verify_incident_id_format,
    is_valid_ip_or_fqdn,
)
from services.aux_services.json_services import is_valid_fqdn
from services.aux_services.message_services import get_message_and_jws_by_event_type
from services.aux_services.sip_services import extract_sip_call_identifiers
from services.aux_services.xml_services import is_xml_equal, EasyXML
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation
from services.config.types.test_config import MessageFilter
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_022.constants import (
    NOT_RUN,
    LOST_QUERY_LOG_EVENT,
    LOST_RESPONSE_LOG_EVENT,
    MALFORMED_RESPONSE_VARIATION,
)


def _normalize_endpoint(endpoint: Optional[str]) -> Optional[str]:
    """Returns the endpoint path without a trailing slash, or None."""
    return urlparse(endpoint or "").path.rstrip("/") or None


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip,
        out_src_ip, out_dst_ip, other_src_ip, other_dst_ip, key_filepath, chfe_fqdn,
        log_events_endpoint, lost_endpoint)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    other = messages_by_type.get(FilterMessageType.OTHER)

    if not (stimulus and output and other):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    log_events_endpoint = _normalize_endpoint(output.header_contains)
    lost_endpoint = _normalize_endpoint(other.header_contains)
    if not (log_events_endpoint and lost_endpoint):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain LogEvents or LoST endpoint"
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
    other_src_ip = ip_by_interface_name.get(other.src_interface)
    other_dst_ip = ip_by_interface_name.get(other.dst_interface)

    required_ips = (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
    )
    if None in required_ips:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    iut_entity = lab_config.get_conformance_iut_entity()
    chfe_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None
    if not chfe_fqdn:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required FQDN records for CHFE interfaces"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        key_filepath,
        chfe_fqdn,
        log_events_endpoint,
        lost_endpoint,
    )


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    chfe_fqdn: Optional[str] = None
    stimulus_call_id_sip: Optional[str] = None
    chfe_ecrf_post_message: Optional[Packet] = None
    chfe_ecrf_post_body: Optional[str] = None
    lost_query_jws: Optional[dict] = None
    lost_query_message: Optional[Packet] = None
    lost_response_jws: Optional[dict] = None
    lost_response_message: Optional[Packet] = None
    ecrf_response_body: Optional[str] = None
    lost_query_call_id: Optional[str] = None
    lost_query_incident_id: Optional[str] = None


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
        other_src_ip,
        other_dst_ip,
        key_filepath,
        chfe_fqdn,
        log_events_endpoint,
        lost_endpoint,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_ecrf", other_src_ip, other_dst_ip)
    fetcher.add_route("chfe_logger", out_src_ip, out_dst_ip)

    data: dict = {
        "chfe_fqdn": chfe_fqdn,
    }

    # ESRP to CHFE stimulus message
    stimulus_message, stimulus_timestamp = fetcher.get_first_sip_invite(
        "esrp_chfe", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get Stimulus Call-ID, CallId, IncidentId
    stimulus_identifiers = extract_sip_call_identifiers(stimulus_message)
    data["stimulus_call_id_sip"] = stimulus_identifiers.call_id_sip

    # CHFE to ECRF findService HTTP POST
    chfe_ecrf_post, chfe_ecrf_post_ts = fetcher.get_first_http_post(
        "chfe_ecrf",
        return_timestamp=True,
        after_timestamp=stimulus_timestamp,
        url_contains=lost_endpoint,
        body_part="findService",
    )
    data["chfe_ecrf_post_message"] = chfe_ecrf_post
    chfe_ecrf_post_msg = (
        HttpMessage.from_packet(chfe_ecrf_post) if chfe_ecrf_post else None
    )
    data["chfe_ecrf_post_body"] = (
        (chfe_ecrf_post_msg.body or None) if chfe_ecrf_post_msg else None
    )

    # ECRF to CHFE findService response body (malformed in variation 2)
    if chfe_ecrf_post:
        ecrf_response = fetcher.get_first_http(
            "ecrf_chfe", after_timestamp=chfe_ecrf_post_ts
        )
        ecrf_response_msg = (
            HttpMessage.from_packet(ecrf_response) if ecrf_response else None
        )
        data["ecrf_response_body"] = (
            (ecrf_response_msg.body or None) if ecrf_response_msg else None
        )

    # CHFE to LOGGER LogEvents POSTs after the stimulus
    logger_posts = (
        fetcher.get_http_posts(
            "chfe_logger",
            after_timestamp=stimulus_timestamp,
            url_contains=log_events_endpoint,
        )
        or []
    )

    # LostQueryLogEvent and LostResponseLogEvent from the same set of POSTs
    data["lost_query_jws"], data["lost_query_message"] = (
        get_message_and_jws_by_event_type(
            logger_posts, LOST_QUERY_LOG_EVENT, key_filepath
        )
    )
    data["lost_response_jws"], data["lost_response_message"] = (
        get_message_and_jws_by_event_type(
            logger_posts, LOST_RESPONSE_LOG_EVENT, key_filepath
        )
    )

    # callId and incidentTrackingId from emergencyCallIncidentId of the findService query
    chfe_ecrf_post_xml = (
        EasyXML(data["chfe_ecrf_post_body"]) if data["chfe_ecrf_post_body"] else None
    )
    data["lost_query_call_id"] = (
        getattr(chfe_ecrf_post_xml, "emergencyCallIncidentId_callId", None) or None
    )
    data["lost_query_incident_id"] = (
        getattr(chfe_ecrf_post_xml, "emergencyCallIncidentId_incidentTrackingId", None)
        or None
    )

    return TestData(**data)


def _payload_precondition(
    has_stimulus: bool,
    message: Optional[Packet],
    payload: Optional[dict],
    event_name: str,
) -> tuple[bool, str]:
    """Returns (precondition, precondition_error) for checks of LogEvent fields."""
    if not has_stimulus:
        return False, NOT_RUN
    if not message:
        return False, f"FAILED -> No CHFE to LOGGER HTTP POST with {event_name} found"
    if not payload:
        return (
            False,
            f"FAILED -> No JWS with {event_name} found in CHFE to LOGGER HTTP POST",
        )
    return True, NOT_RUN


def _get_optional_field_checks(
    payload: Optional[dict], event_name: str, has_stimulus: bool
) -> list:
    """Returns type/format checks for optional LogEvent fields present in the payload."""
    if not payload:
        return []

    checks = []

    for field_name in ("agencyAgentId", "agencyPositionId", "clientAssignedIdentifier"):
        if field_name in payload:
            checks.append(
                TestCheck(
                    test_name=f"Verify {event_name} optional '{field_name}' value is a string",
                    test_method=is_type,
                    precondition=has_stimulus,
                    precondition_error=NOT_RUN,
                    test_params={
                        "param": payload[field_name],
                        "param_name": field_name,
                        "expected_type": str,
                    },
                )
            )

    if "extension" in payload:
        checks.append(
            TestCheck(
                test_name=f"Verify {event_name} optional 'extension' value is an object",
                test_method=is_type,
                precondition=has_stimulus,
                precondition_error=NOT_RUN,
                test_params={
                    "param": payload["extension"],
                    "param_name": "extension",
                    "expected_type": dict,
                },
            )
        )

    if "ipAddressPort" in payload:
        ip_address_port = payload["ipAddressPort"]
        checks.append(
            TestCheck(
                test_name=f"Verify {event_name} optional 'ipAddressPort' value is a valid IP:PORT or FQDN",
                test_method=is_data_present,
                precondition=has_stimulus,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": isinstance(ip_address_port, str)
                    and is_valid_ip_or_fqdn(ip_address_port),
                    "error": (
                        f"FAILED -> Invalid IP:PORT or FQDN value for '{event_name}'. "
                        f"Received: '{ip_address_port}'"
                    ),
                },
            )
        )

    return checks


def _field_precondition(
    base_precondition: bool,
    base_precondition_error: str,
    payload: Optional[dict],
    event_name: str,
    *field_names: str,
) -> dict:
    """
    Returns TestCheck precondition kwargs for checks of mandatory LogEvent fields:
    the base (stimulus/packet/JWS) precondition first, then presence of every field.
    A field present with a null value counts as present, so its check runs and fails by value.
    """
    if not base_precondition:
        return {"precondition": False, "precondition_error": base_precondition_error}
    for field_name in field_names:
        if field_name not in payload:
            return {
                "precondition": False,
                "precondition_error": f"FAILED -> '{field_name}' member is missing in {event_name}",
            }
    return {"precondition": True, "precondition_error": NOT_RUN}


def _with_ecrf_stub(field_kwargs: dict, is_ecrf_stub_missing: bool) -> dict:
    """Adds the ECRF stub condition to the precondition kwargs of LoST response content checks."""
    if field_kwargs["precondition"] and is_ecrf_stub_missing:
        return {
            "precondition": False,
            "precondition_error": "NOT RUN -> No findService response from Test System ECRF found",
        }
    return field_kwargs


def get_test_names() -> list:
    return [
        "Verify CHFE sends findService HTTP POST to ECRF",
        "Verify CHFE sends HTTP POST with LostQueryLogEvent to LOGGER",
        "Verify LostQueryLogEvent HTTP POST contains JWS",
        "Verify CHFE sends HTTP POST with LostResponseLogEvent to LOGGER",
        "Verify LostResponseLogEvent HTTP POST contains JWS",
        # LostQueryLogEvent validation
        "Verify LostQueryLogEvent 'logEventType' value is 'LostQueryLogEvent'",
        "Verify LostQueryLogEvent 'timestamp' value format",
        "Verify LostQueryLogEvent 'elementId' value is CHFE FQDN",
        "Verify LostQueryLogEvent 'agencyId' value is a valid FQDN",
        "Verify LostQueryLogEvent 'queryAdapter' value is the entire LoST query",
        "Verify LostQueryLogEvent 'queryId' value is a non-empty string",
        "Verify LostQueryLogEvent 'direction' value is 'outgoing'",
        "Verify LostQueryLogEvent 'callId' value format",
        "Verify LostQueryLogEvent 'callId' value is the same as in findService LoST query",
        "Verify LostQueryLogEvent 'incidentId' value format",
        "Verify LostQueryLogEvent 'incidentId' value is the same as in findService LoST query",
        "Verify LostQueryLogEvent 'callIdSip' value is the same as stimulus SIP Call-ID",
        "Verify LostQueryLogEvent optional 'agencyAgentId' value is a string",
        "Verify LostQueryLogEvent optional 'agencyPositionId' value is a string",
        "Verify LostQueryLogEvent optional 'clientAssignedIdentifier' value is a string",
        "Verify LostQueryLogEvent optional 'extension' value is an object",
        "Verify LostQueryLogEvent optional 'ipAddressPort' value is a valid IP:PORT or FQDN",
        # LostResponseLogEvent validation
        "Verify LostResponseLogEvent 'logEventType' value is 'LostResponseLogEvent'",
        "Verify LostResponseLogEvent 'responseAdapter' value is the entire LoST response",
        "Verify LostResponseLogEvent 'timestamp' value format",
        "Verify LostResponseLogEvent 'elementId' value is CHFE FQDN",
        "Verify LostResponseLogEvent 'agencyId' value is a valid FQDN",
        "Verify LostResponseLogEvent 'responseId' value is the same as LostQueryLogEvent 'queryId'",
        "Verify LostResponseLogEvent 'direction' value is 'incoming'",
        "Verify LostResponseLogEvent 'callId' value format",
        "Verify LostResponseLogEvent 'callId' value is the same as in findService LoST query",
        "Verify LostResponseLogEvent 'incidentId' value format",
        "Verify LostResponseLogEvent 'incidentId' value is the same as in findService LoST query",
        "Verify LostResponseLogEvent 'callIdSip' value is the same as stimulus SIP Call-ID",
        "Verify LostResponseLogEvent optional 'agencyAgentId' value is a string",
        "Verify LostResponseLogEvent optional 'agencyPositionId' value is a string",
        "Verify LostResponseLogEvent optional 'clientAssignedIdentifier' value is a string",
        "Verify LostResponseLogEvent optional 'extension' value is an object",
        "Verify LostResponseLogEvent optional 'ipAddressPort' value is a valid IP:PORT or FQDN",
        "Verify LostResponseLogEvent 'malformedResponse' value is the malformed LoST response",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    variations = {
        "SIP_INVITE_location_PIDF-LO_Boundary1": 1,
        "SIP_INVITE_location_PIDF-LO_Boundary1_malformed_LoST_response_from_ECRF-LVF": 2,
    }

    variation_number = variations.get(run_variation.name)
    if variation_number is None:
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation
    )

    has_stimulus = bool(test_data.stimulus_message)
    is_malformed_variation = variation_number == MALFORMED_RESPONSE_VARIATION
    query_payload = test_data.lost_query_jws
    response_payload = test_data.lost_response_jws

    # Short accessors
    query = partial(get_payload_field, query_payload)
    response = partial(get_payload_field, response_payload)

    # Base preconditions: NOT RUN without stimulus, FAILED with the real reason without packet or JWS
    query_precondition, query_precondition_error = _payload_precondition(
        has_stimulus, test_data.lost_query_message, query_payload, LOST_QUERY_LOG_EVENT
    )
    response_precondition, response_precondition_error = _payload_precondition(
        has_stimulus,
        test_data.lost_response_message,
        response_payload,
        LOST_RESPONSE_LOG_EVENT,
    )

    # Field preconditions: base precondition + presence of the checked field(s).
    query_field = partial(
        _field_precondition,
        query_precondition,
        query_precondition_error,
        query_payload,
        LOST_QUERY_LOG_EVENT,
    )
    response_field = partial(
        _field_precondition,
        response_precondition,
        response_precondition_error,
        response_payload,
        LOST_RESPONSE_LOG_EVENT,
    )

    # Common kwargs for message presence checks
    presence_check = {
        "test_method": is_data_present,
        "precondition": has_stimulus,
        "precondition_error": NOT_RUN,
    }

    # 'responseId' against 'queryId' precondition, check the response side first, then the query side
    response_id_kwargs = response_field("responseId")
    if response_id_kwargs["precondition"]:
        response_id_kwargs = query_field("queryId")

    # LoST response content checks are NOT RUN when CHFE sent the query but the ECRF stub did not answer
    is_ecrf_stub_missing = (
        bool(test_data.chfe_ecrf_post_message) and not test_data.ecrf_response_body
    )

    check_list = []

    # Messages
    check_list.extend(
        [
            TestCheck(
                test_name="Verify CHFE sends findService HTTP POST to ECRF",
                **presence_check,
                test_params={
                    "test_data": test_data.chfe_ecrf_post_message,
                    "error": "FAILED -> No CHFE to ECRF findService HTTP POST message found",
                },
            ),
            TestCheck(
                test_name="Verify CHFE sends HTTP POST with LostQueryLogEvent to LOGGER",
                **presence_check,
                test_params={
                    "test_data": test_data.lost_query_message,
                    "error": "FAILED -> No CHFE to LOGGER HTTP POST with LostQueryLogEvent found",
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent HTTP POST contains JWS",
                **presence_check,
                test_params={
                    "test_data": query_payload,
                    "error": "FAILED -> No JWS with LostQueryLogEvent found in CHFE to LOGGER HTTP POST",
                },
            ),
            TestCheck(
                test_name="Verify CHFE sends HTTP POST with LostResponseLogEvent to LOGGER",
                **presence_check,
                test_params={
                    "test_data": test_data.lost_response_message,
                    "error": "FAILED -> No CHFE to LOGGER HTTP POST with LostResponseLogEvent found",
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent HTTP POST contains JWS",
                **presence_check,
                test_params={
                    "test_data": response_payload,
                    "error": "FAILED -> No JWS with LostResponseLogEvent found in CHFE to LOGGER HTTP POST",
                },
            ),
        ]
    )

    # LostQueryLogEvent checks
    check_list.extend(
        [
            TestCheck(
                test_name="Verify LostQueryLogEvent 'logEventType' value is 'LostQueryLogEvent'",
                test_method=is_test_data_the_same,
                **query_field("logEventType"),
                test_params={
                    "expected_data": LOST_QUERY_LOG_EVENT,
                    "actual_data": query("logEventType"),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'timestamp' value format",
                test_method=verify_timestamp_format,
                **query_field("timestamp"),
                test_params={
                    "timestamp": query("timestamp"),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'elementId' value is CHFE FQDN",
                test_method=is_test_data_the_same,
                **query_field("elementId"),
                test_params={
                    "expected_data": test_data.chfe_fqdn,
                    "actual_data": query("elementId"),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'agencyId' value is a valid FQDN",
                test_method=is_data_present,
                **query_field("agencyId"),
                test_params={
                    "test_data": isinstance(query("agencyId"), str)
                    and is_valid_fqdn(query("agencyId")),
                    "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record. Actual: {query('agencyId')}",
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'queryAdapter' value is the entire LoST query",
                test_method=is_data_present,
                **query_field("queryAdapter"),
                test_params={
                    "test_data": is_xml_equal(
                        test_data.chfe_ecrf_post_body, query("queryAdapter")
                    ),
                    "error": (
                        "FAILED -> LostQueryLogEvent 'queryAdapter' value "
                        "is not the same as CHFE to ECRF findService HTTP POST XML body"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'queryId' value is a non-empty string",
                test_method=is_data_present,
                **query_field("queryId"),
                test_params={
                    "test_data": isinstance(query("queryId"), str)
                    and bool(query("queryId").strip()),
                    "error": f"FAILED -> LostQueryLogEvent 'queryId' is not a non-empty string. Actual: {query('queryId')!r}",
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'direction' value is 'outgoing'",
                test_method=is_test_data_the_same,
                **query_field("direction"),
                test_params={
                    "expected_data": "outgoing",
                    "actual_data": query("direction"),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'callId' value format",
                test_method=verify_call_id_format,
                **query_field("callId"),
                test_params={
                    "call_id": extract_enclosed_value(query("callId")),
                    "event_type": LOST_QUERY_LOG_EVENT,
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'callId' value is the same as in findService LoST query",
                test_method=is_test_data_the_same,
                **query_field("callId"),
                test_params={
                    "expected_data": test_data.lost_query_call_id,
                    "actual_data": query("callId"),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'incidentId' value format",
                test_method=verify_incident_id_format,
                **query_field("incidentId"),
                test_params={
                    "incident_id": extract_enclosed_value(query("incidentId")),
                    "event_type": LOST_QUERY_LOG_EVENT,
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'incidentId' value is the same as in findService LoST query",
                test_method=is_test_data_the_same,
                **query_field("incidentId"),
                test_params={
                    "expected_data": test_data.lost_query_incident_id,
                    "actual_data": query("incidentId"),
                },
            ),
            TestCheck(
                test_name="Verify LostQueryLogEvent 'callIdSip' value is the same as stimulus SIP Call-ID",
                test_method=is_test_data_the_same,
                **query_field("callIdSip"),
                test_params={
                    "expected_data": test_data.stimulus_call_id_sip,
                    "actual_data": query("callIdSip"),
                },
            ),
        ]
    )

    # LostResponseLogEvent checks
    check_list.extend(
        [
            TestCheck(
                test_name="Verify LostResponseLogEvent 'logEventType' value is 'LostResponseLogEvent'",
                test_method=is_test_data_the_same,
                **response_field("logEventType"),
                test_params={
                    "expected_data": LOST_RESPONSE_LOG_EVENT,
                    "actual_data": response("logEventType"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'responseAdapter' value is the entire LoST response",
                test_method=is_data_present,
                **_with_ecrf_stub(
                    response_field("responseAdapter"), is_ecrf_stub_missing
                ),
                test_params={
                    "test_data": is_xml_equal(
                        test_data.ecrf_response_body,
                        response("responseAdapter"),
                        is_malformed=is_malformed_variation,
                    ),
                    "error": (
                        "FAILED -> LostResponseLogEvent 'responseAdapter' value "
                        "is not the same as ECRF to CHFE findService response XML body"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'timestamp' value format",
                test_method=verify_timestamp_format,
                **response_field("timestamp"),
                test_params={
                    "timestamp": response("timestamp"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'elementId' value is CHFE FQDN",
                test_method=is_test_data_the_same,
                **response_field("elementId"),
                test_params={
                    "expected_data": test_data.chfe_fqdn,
                    "actual_data": response("elementId"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'agencyId' value is a valid FQDN",
                test_method=is_data_present,
                **response_field("agencyId"),
                test_params={
                    "test_data": isinstance(response("agencyId"), str)
                    and is_valid_fqdn(response("agencyId")),
                    "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record. Actual: {response('agencyId')}",
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'responseId' value is the same as LostQueryLogEvent 'queryId'",
                test_method=is_test_data_the_same,
                **response_id_kwargs,
                test_params={
                    "expected_data": query("queryId"),
                    "actual_data": response("responseId"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'direction' value is 'incoming'",
                test_method=is_test_data_the_same,
                **response_field("direction"),
                test_params={
                    "expected_data": "incoming",
                    "actual_data": response("direction"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'callId' value format",
                test_method=verify_call_id_format,
                **response_field("callId"),
                test_params={
                    "call_id": extract_enclosed_value(response("callId")),
                    "event_type": LOST_RESPONSE_LOG_EVENT,
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'callId' value is the same as in findService LoST query",
                test_method=is_test_data_the_same,
                **response_field("callId"),
                test_params={
                    "expected_data": test_data.lost_query_call_id,
                    "actual_data": response("callId"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'incidentId' value format",
                test_method=verify_incident_id_format,
                **response_field("incidentId"),
                test_params={
                    "incident_id": extract_enclosed_value(response("incidentId")),
                    "event_type": LOST_RESPONSE_LOG_EVENT,
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'incidentId' value is the same as in findService LoST query",
                test_method=is_test_data_the_same,
                **response_field("incidentId"),
                test_params={
                    "expected_data": test_data.lost_query_incident_id,
                    "actual_data": response("incidentId"),
                },
            ),
            TestCheck(
                test_name="Verify LostResponseLogEvent 'callIdSip' value is the same as stimulus SIP Call-ID",
                test_method=is_test_data_the_same,
                **response_field("callIdSip"),
                test_params={
                    "expected_data": test_data.stimulus_call_id_sip,
                    "actual_data": response("callIdSip"),
                },
            ),
        ]
    )

    # Optional fields (added only when the field is present in the payload)
    check_list.extend(
        _get_optional_field_checks(query_payload, LOST_QUERY_LOG_EVENT, has_stimulus)
    )
    check_list.extend(
        _get_optional_field_checks(
            response_payload, LOST_RESPONSE_LOG_EVENT, has_stimulus
        )
    )

    # Variation 2 only: malformed LoST response from ECRF is logged in 'malformedResponse'
    if is_malformed_variation:
        check_list.append(
            TestCheck(
                test_name="Verify LostResponseLogEvent 'malformedResponse' value is the malformed LoST response",
                test_method=is_data_present,
                **_with_ecrf_stub(
                    response_field("malformedResponse"), is_ecrf_stub_missing
                ),
                test_params={
                    "test_data": is_xml_equal(
                        test_data.ecrf_response_body,
                        response("malformedResponse"),
                        is_malformed=True,
                    ),
                    "error": (
                        "FAILED -> LostResponseLogEvent 'malformedResponse' value "
                        "is not the same as ECRF to CHFE malformed findService response body"
                    ),
                },
            )
        )

    return check_list
