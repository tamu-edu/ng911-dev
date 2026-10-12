import re
from dataclasses import dataclass
from urllib.parse import urlparse

from pyshark.packet.packet import Packet

from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
    verify_value_present_in_collection,
)
from checks.http.checks import is_type
from checks.log_events.checks import (
    get_jws_payloads_list_by_log_event_type,
    get_payload_field,
    verify_timestamp_format,
    verify_query_id,
    is_valid_ip_or_fqdn,
)
from services.aux_services.json_services import is_valid_fqdn
from services.messages.http.http_message import HttpMessage
from tests.ECRF_LVF_009.constants import (
    LOST_QUERY_LOG_EVENT,
    LOST_RESPONSE_LOG_EVENT,
    NOT_RUN,
    RESPONSE_CODES,
)
from tests.ECRF_LVF_009.variations.param_filter_var_one_three import (
    get_filter_parameters_var_one_three,
)
from services.aux_services.message_services import get_http_messages_by_log_event_type
from services.aux_services.xml_services import (
    is_xml_equal,
    EasyXML,
    is_valid_xml,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_009.variations.param_filter_var_other import (
    get_filter_parameters_var_other,
)

# --- Helpers ---


def _extract_attr(xml_string: str | None, attr_name: str) -> str | None:
    """Returns the value of attr_name="..." from an XML string, or None."""
    if not isinstance(xml_string, str):
        return None
    match = re.search(rf'(?<![\w:-]){re.escape(attr_name)}="([^"]+)"', xml_string)
    return match.group(1) if match else None


def _get_lost_incident_ids(lost_body) -> tuple[str | None, str | None]:
    """
    Returns (callId, incidentId) from a LoST body, or (None, None) if there
    is no body or it is not a valid XML.
    """
    if not lost_body or not is_valid_xml(lost_body):
        return None, None
    xml_body = EasyXML(lost_body)
    call_id = getattr(xml_body, "emergencycallincidentid_callid", None) or None
    incident_id = (
        getattr(xml_body, "emergencycallincidentid_incidenttrackingid", None) or None
    )
    return call_id, incident_id


def _get_http_body(packet) -> str | None:
    """Returns the body of an HTTP packet, or None if there is no packet/body."""
    http_message = HttpMessage.from_packet(packet) if packet else None
    return http_message.body if http_message else None


def _get_first_jws_by_fields(
    post_messages: list, log_event_type: str, key_filepath: str, **field_filters
) -> dict:
    """
    Returns the first JWS payload of the given LogEvent type whose fields
    match all the given field_filters (e.g. callId=..., incidentId=...),
    or {} if there is none.
    """
    if any(value is None for value in field_filters.values()):
        return {}

    payloads = get_jws_payloads_list_by_log_event_type(
        post_messages,
        key_filepath=key_filepath,
        log_event_type=log_event_type,
    )
    return next(
        (
            payload
            for payload in payloads
            if all(
                payload.get(field) == expected
                for field, expected in field_filters.items()
            )
        ),
        {},
    )


def _collect_logger_data(
    data: dict, fetcher, key_filepath, stimulus_ts, jws_requests
) -> None:
    """
    Fills in the LOGGER-related fields of data from the ECRF-to-LOGGER POSTs:
    flags telling whether LostQuery/LostResponse LogEvents were posted, and
    the first JWS matching data["call_id"]/data["incident_id"] for each of
    jws_requests.

    :param jws_requests: iterable of (data_key, log_event_type, extra_filters),
        where extra_filters are additional payload field filters,
        e.g. {"direction": "outgoing"}.
    """
    post_messages = fetcher.get_http_posts("ecrf_logger", after_timestamp=stimulus_ts)
    if not post_messages:
        return

    for flag_key, log_event_type in (
        ("is_lost_query_post_messages", LOST_QUERY_LOG_EVENT),
        ("is_lost_response_post_messages", LOST_RESPONSE_LOG_EVENT),
    ):
        data[flag_key] = bool(
            get_http_messages_by_log_event_type(post_messages, log_event_type)
        )

    for data_key, log_event_type, extra_filters in jws_requests:
        data[data_key] = _get_first_jws_by_fields(
            post_messages,
            log_event_type,
            key_filepath,
            callId=data["call_id"],
            incidentId=data["incident_id"],
            **extra_filters,
        )


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Packet | None = None
    stimulus_lost_body: str | None = None
    recursive_lost_body: str | None = None
    find_service_response_body: str | None = None
    recursive_response_body: str | None = None
    ecrf_fqdn: str | None = None

    call_id: str | None = None
    incident_id: str | None = None

    lost_query_jws: dict | None = None
    lost_response_jws: dict | None = None

    is_lost_query_post_messages: bool = False
    is_lost_response_post_messages: bool = False
    is_recursive_find_service_message: bool = False
    is_recursive_response_messages: bool = False


def get_test_parameters_var_one_three(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
    variation_number: int,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        key_filepath,
        ecrf_fqdn,
    ) = filtering_data

    data: dict = {"ecrf_fqdn": ecrf_fqdn}

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_ecrf", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("ecrf_logger", out_src_ip, out_dst_ip)

    # ESRP to ECRF stimulus message
    stimulus_message, stimulus_ts = fetcher.get_first_http_post(
        "esrp_ecrf", return_timestamp=True
    )
    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get Stimulus LoST body
    stimulus_lost_body = _get_http_body(stimulus_message)
    data["stimulus_lost_body"] = stimulus_lost_body

    # Get findServiceResponse 200 OK Body
    find_service_response = fetcher.get_first_http(
        "ecrf_esrp", after_timestamp=stimulus_ts, http_status_code=200
    )
    data["find_service_response_body"] = _get_http_body(find_service_response)

    # Get callId and incidentId from stimulus LoST
    # Variation 3 has a malformed query, so XML parsing is replaced with regex.
    if variation_number == 3:
        call_id = _extract_attr(stimulus_lost_body, "callId")
        incident_id = _extract_attr(stimulus_lost_body, "incidentTrackingId")
    else:
        call_id, incident_id = _get_lost_incident_ids(stimulus_lost_body)
    data["call_id"] = call_id
    data["incident_id"] = incident_id

    # Get LostQueryLogEvent\LostResponseLogEvent POST request messages and JWS
    jws_requests = [
        ("lost_query_jws", LOST_QUERY_LOG_EVENT, {}),
        ("lost_response_jws", LOST_RESPONSE_LOG_EVENT, {}),
    ]

    _collect_logger_data(
        data, fetcher, key_filepath, stimulus_ts, jws_requests=jws_requests
    )

    return TestData(**data)


def get_test_parameters_var_two_four_five(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
    variation_number: int,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        key_filepath,
        ecrf_fqdn,
    ) = filtering_data

    data: dict = {"ecrf_fqdn": ecrf_fqdn}

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_ecrf", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("ecrf_logger", out_src_ip, out_dst_ip)
    fetcher.add_route("ecrf_ecrf2", out_src_ip, other_src_ip)

    # ESRP to ECRF stimulus message
    stimulus_message, stimulus_ts = fetcher.get_first_http_post(
        "esrp_ecrf", return_timestamp=True
    )
    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get Stimulus LoST body, callId and incidentId from
    data["stimulus_lost_body"] = _get_http_body(stimulus_message)
    data["call_id"], data["incident_id"] = _get_lost_incident_ids(
        data["stimulus_lost_body"]
    )

    # Get recursive POST message from ECRF to ECRF2 with matching LoST body
    if data["call_id"] and data["incident_id"]:
        stimulus_ids = (data["call_id"], data["incident_id"])
        for message in fetcher.get_http_messages(
            "ecrf_ecrf2", after_timestamp=stimulus_ts
        ):
            http_msg = HttpMessage.from_packet(message)
            if not http_msg or not http_msg.request_target:
                continue
            if urlparse(http_msg.request_target).path.rstrip("/") != "/LoST":
                continue
            data["is_recursive_find_service_message"] = True
            if _get_lost_incident_ids(http_msg.body) == stimulus_ids:
                data["recursive_lost_body"] = http_msg.body
                break

    # Get response from ECRF2 to ECRF for the recursive LoST request
    recursive_response = fetcher.get_first_http(
        "ecrf2_ecrf", after_timestamp=stimulus_ts, http_status_code=200
    )
    if recursive_response:
        data["is_recursive_response_messages"] = True
        data["recursive_response_body"] = _get_http_body(recursive_response)

    # Get LostQueryLogEvent\LostResponseLogEvent POST request messages and JWS
    _collect_logger_data(
        data,
        fetcher,
        key_filepath,
        stimulus_ts,
        jws_requests=(
            ("lost_query_jws", LOST_QUERY_LOG_EVENT, {"direction": "outgoing"}),
            ("lost_response_jws", LOST_RESPONSE_LOG_EVENT, {"direction": "incoming"}),
        ),
    )

    return TestData(**data)


OPTIONAL_FIELD_CHECKS = (
    ("clientAssignedIdentifier", str, "value is a string if field exists"),
    ("agencyAgentId", str, "value is a string if field exists"),
    ("agencyPositionId", str, "value is a string if field exists"),
    ("ipAddressPort", None, "value is a valid IP:PORT or FQDN format if field exists"),
    ("extension", dict, "value is a dictionary object if field exists"),
)


def build_optional_field_checks(
    payload, log_event_type: str, test_data, include_all: bool = False
) -> list[TestCheck]:
    """
    Builds the checks for the optional LogEvent fields (OPTIONAL_FIELD_CHECKS).
    A check is added only if the field is present in the payload (its value
    is not None), so absent optional fields produce no check.

    :param payload: Decoded JWS payload of the LogEvent (dict), or None/{}
        if it was not found
    :param log_event_type: LogEvent type the payload
    :param test_data: TestData instance;
    :param include_all: If True, checks for all optional fields are built
        regardless of the payload. Used by get_test_names() to register
        every possible test_name. Defaults to False.
    :return: List of TestCheck objects, one per optional field present in
        the payload (or one per optional field if include_all is True).
    """
    checks = []
    for field_name, expected_type, name_suffix in OPTIONAL_FIELD_CHECKS:
        value = get_payload_field(payload, field_name)
        if value is None and not include_all:
            continue

        if field_name == "ipAddressPort":
            test_method = is_data_present
            test_params = {
                "test_data": is_valid_ip_or_fqdn(value),
                "error": f"FAILED -> Invalid IP:PORT or FQDN value for '{log_event_type}'. Received: '{value}'",
            }
        else:
            test_method = is_type
            test_params = {
                "param": value,
                "param_name": field_name,
                "expected_type": expected_type,
            }

        checks.append(
            TestCheck(
                test_name=f"Verify ECRF-LVF to LOGGER {log_event_type} '{field_name}' {name_suffix}",
                test_method=test_method,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params=test_params,
            )
        )
    return checks


def get_test_names() -> list:
    test_names_list = [
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent HTTP messages are present",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent HTTP messages are present",
        "Verify ECRF-LVF to ECRF-LVF2 HTTP POST findService message is present",
        "Verify ECRF-LVF2 to ECRF-LVF HTTP findService response message is present",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent JWS data is available",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent JWS data is available",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'logEventType' field value is 'LostQueryLogEvent'",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'timestamp' field value format",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'elementId' field value contains FQDN of ECRF-LVF",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'agencyId' field value contain a valid FQDN format",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'direction' value is 'incoming' or 'outgoing'",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'queryAdapter' value is entire LoST query",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'queryId' value format",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'callId' value matched findService callId",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'incidentId' value matched findService incidentTrackingId",
        "Verify ECRF-LVF to LOGGER LostQueryLogEvent 'malformedQuery' value is malformed LoST query received from ESRP",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'logEventType' field value is 'LostResponseLogEvent'",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'timestamp' field value format",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'elementId' field value contains FQDN of ECRF-LVF",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'agencyId' field value contain a valid FQDN format",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'direction' value is 'incoming' or 'outgoing'",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseAdapter' value is entire LoST response",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseId' matched queryId value from LostQueryLogEvent",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'callId' value matched findService callId",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'incidentId' value matched findService incidentTrackingId",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'malformedResponse' value is entire LoST response",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseAdapter' value is empty string if no LoST response received",
        "Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseStatus' value is error code from Status Codes Registry",
    ]

    # Optional-field checks are only built when the field is present in a real
    # payload, so their names are generated with include_all=True (dummy payload)
    # to keep them registered.
    stub_test_data = TestData()
    for log_event_type in (LOST_QUERY_LOG_EVENT, LOST_RESPONSE_LOG_EVENT):
        test_names_list += [
            check.test_name
            for check in build_optional_field_checks(
                None, log_event_type, stub_test_data, include_all=True
            )
        ]

    return test_names_list


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    variations = {
        "Valid_LoST_query_and_response": 1,
        "Valid_recursive_LoST_query_and_response": 2,
        "Malformed_LoST_query": 3,
        "LostResponseLogEvent_members_after_ECRF-LVF_receives_malformed_Response": 4,
        "LostResponseLogEvent_members_after_ECRF-LVF_does_not_receive_a_response": 5,
    }

    if run_variation.name in variations:
        variation_number = variations.get(run_variation.name)
    else:
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    if variation_number in (1, 3):
        filtering_data = get_filter_parameters_var_one_three(
            lab_config, filtering_options
        )
        test_data = get_test_parameters_var_one_three(
            pcap_service, filtering_data, variation_number
        )
    else:
        filtering_data = get_filter_parameters_var_other(lab_config, filtering_options)
        test_data = get_test_parameters_var_two_four_five(
            pcap_service, filtering_data, variation_number
        )

    query_payload = test_data.lost_query_jws
    response_payload = test_data.lost_response_jws

    check_list = []

    check_list.extend(
        [
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent HTTP messages are present",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.is_lost_query_post_messages,
                    "error": "FAILED -> ECRF-LVF to LOGGER LostQueryLogEvent HTTP messages not found",
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent JWS data is available",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.lost_query_jws,
                },
            ),
        ]
    )

    if variation_number != 3:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent HTTP messages are present",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_lost_response_post_messages,
                        "error": "FAILED -> ECRF-LVF to LOGGER LostResponseLogEvent HTTP messages not found",
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent JWS data is available",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.lost_response_jws,
                    },
                ),
            ]
        )

    if variation_number in (2, 4, 5):
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to ECRF-LVF2 HTTP POST findService message is present",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_recursive_find_service_message,
                        "error": "FAILED -> ECRF-LVF to ECRF-LVF2 HTTP POST findService message not found",
                    },
                ),
            ]
        )

    if variation_number in (2, 4):
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF2 to ECRF-LVF HTTP findService response message is present",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_recursive_response_messages,
                        "error": "NOT RUN -> ECRF-LVF2 to ECRF-LVF HTTP findService response message not found",
                    },
                ),
            ]
        )

    check_list.extend(
        [
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'logEventType' field value is 'LostQueryLogEvent'",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": "LostQueryLogEvent",
                    "actual_data": get_payload_field(query_payload, "logEventType"),
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'timestamp' field value format",
                test_method=verify_timestamp_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "timestamp": get_payload_field(query_payload, "timestamp"),
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'elementId' field value contains FQDN of ECRF-LVF",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.ecrf_fqdn,
                    "actual_data": get_payload_field(query_payload, "elementId"),
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'agencyId' field value contain a valid FQDN format",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": (
                        is_valid_fqdn(agency_id)
                        if (agency_id := get_payload_field(query_payload, "agencyId"))
                        else False
                    ),
                    "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record for of ECRF_LVF to LOGGER 'agencyId'. Actual: {agency_id}",
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'direction' value is 'incoming' or 'outgoing'",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": (
                        "incoming" if variation_number in (1, 3) else "outgoing"
                    ),
                    "actual_data": get_payload_field(query_payload, "direction"),
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'queryAdapter' value is entire LoST query",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": is_xml_equal(
                        (
                            test_data.stimulus_lost_body
                            if variation_number in (1, 3)
                            else test_data.recursive_lost_body
                        ),
                        get_payload_field(query_payload, "queryAdapter"),
                        is_malformed=True if variation_number == 3 else False,
                    ),
                    "error": "FAILED -> ECRF-LVF to LOGGER LostQueryLogEvent 'queryAdapter' value is not the same as stimulus LoST query XML body",
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'queryId' value format",
                test_method=verify_query_id,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "query_id": get_payload_field(query_payload, "queryId"),
                    "event_type": "LostQueryLogEvent",
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'callId' value matched findService callId",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.call_id,
                    "actual_data": get_payload_field(query_payload, "callId"),
                },
            ),
            TestCheck(
                test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'incidentId' value matched findService incidentTrackingId",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.incident_id,
                    "actual_data": get_payload_field(query_payload, "incidentId"),
                },
            ),
        ]
    )

    # Optional fields: checks are added only if the field is present in the payload
    check_list.extend(
        build_optional_field_checks(query_payload, LOST_QUERY_LOG_EVENT, test_data)
    )

    if variation_number != 3:

        check_list.extend(
            [
                # Common Fields LostResponseLogEvent
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'logEventType' field value is 'LostResponseLogEvent'",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": "LostResponseLogEvent",
                        "actual_data": get_payload_field(
                            response_payload, "logEventType"
                        ),
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'timestamp' field value format",
                    test_method=verify_timestamp_format,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "timestamp": get_payload_field(response_payload, "timestamp"),
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'elementId' field value contains FQDN of ECRF-LVF",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": test_data.ecrf_fqdn,
                        "actual_data": get_payload_field(response_payload, "elementId"),
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'agencyId' field value contain a valid FQDN format",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": (
                            is_valid_fqdn(agency_id)
                            if (
                                agency_id := get_payload_field(
                                    response_payload, "agencyId"
                                )
                            )
                            else False
                        ),
                        "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record for of ECRF_LVF to LOGGER 'agencyId'. Actual: {agency_id}",
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'direction' value is 'incoming' or 'outgoing'",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": (
                            "outgoing" if variation_number == 1 else "incoming"
                        ),
                        "actual_data": get_payload_field(response_payload, "direction"),
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseId' matched queryId value from LostQueryLogEvent",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": get_payload_field(query_payload, "queryId"),
                        "actual_data": get_payload_field(
                            response_payload, "responseId"
                        ),
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'callId' value matched findService callId",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": test_data.call_id,
                        "actual_data": get_payload_field(response_payload, "callId"),
                    },
                ),
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'incidentId' value matched findService incidentTrackingId",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": test_data.incident_id,
                        "actual_data": get_payload_field(
                            response_payload, "incidentId"
                        ),
                    },
                ),
            ]
        )

        # Optional fields: checks are added only if the field is present in the payload
        check_list.extend(
            build_optional_field_checks(
                response_payload, LOST_RESPONSE_LOG_EVENT, test_data
            )
        )

    if variation_number in (1, 2, 4):
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseAdapter' value is entire LoST response",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": is_xml_equal(
                            (
                                test_data.find_service_response_body
                                if variation_number == 1
                                else test_data.recursive_response_body
                            ),
                            get_payload_field(response_payload, "responseAdapter"),
                            is_malformed=True if variation_number == 4 else False,
                        ),
                        "error": "FAILED -> ECRF-LVF to LOGGER 'responseAdapter' value is not the same as LoST response XML body",
                    },
                ),
            ]
        )

    if variation_number == 3:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostQueryLogEvent 'malformedQuery' value is malformed LoST query received from ESRP",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": is_xml_equal(
                            test_data.stimulus_lost_body,
                            get_payload_field(query_payload, "malformedQuery"),
                            is_malformed=True,
                        ),
                        "error": "FAILED -> ECRF-LVF to LOGGER LostQueryLogEvent 'malformedQuery' value and LoST malformed body received from ESRP are not equal",
                    },
                ),
            ]
        )

    if variation_number == 4:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'malformedResponse' value is entire LoST response",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": is_xml_equal(
                            test_data.recursive_response_body,
                            get_payload_field(response_payload, "malformedResponse"),
                            is_malformed=True,
                        ),
                        "error": "FAILED -> ECRF-LVF to LOGGER 'malformedResponse' value is not the same as LoST response XML body",
                    },
                ),
            ]
        )

    if variation_number == 5:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseAdapter' value is empty string if no LoST response received",
                    test_method=is_test_data_the_same,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "expected_data": "",
                        "actual_data": get_payload_field(
                            response_payload, "responseAdapter"
                        ),
                        "error": "FAILED -> ECRF-LVF to LOGGER 'responseAdapter' value is not empty string if no LoST response received",
                    },
                ),
            ]
        )

    if variation_number in (4, 5):
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify ECRF-LVF to LOGGER LostResponseLogEvent 'responseStatus' value is error code from Status Codes Registry",
                    test_method=verify_value_present_in_collection,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "actual_data": get_payload_field(
                            response_payload, "responseStatus"
                        ),
                        "allowed_values": RESPONSE_CODES,
                    },
                ),
            ]
        )

    return check_list
