from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
)
from checks.http.checks import is_type
from checks.log_events.checks import (
    get_payload_field,
    verify_timestamp_format,
    verify_call_id_format,
    verify_incident_id_format,
    verify_call_id_sip,
    is_valid_ip_or_fqdn,
    verify_media_quality_stats,
    validate_log_event_timestamp,
)
from checks.log_events.checks import get_jws_payloads_list_by_log_event_type
from services.aux_services.json_services import is_valid_fqdn
from services.aux_services.sdp_services import extract_sdp_labels_from_string
from services.aux_services.sip_msg_body_services import extract_media_attributes
from services.aux_services.sip_services import extract_sip_call_identifiers
from services.messages.packet_fetcher import PacketFetcher
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_014.checks import verify_media_established, get_final_sip_status_code
from tests.BCF_014.constants import (
    NOT_RUN,
    MEDIA_START_LOG_EVENT,
    MEDIA_END_LOG_EVENT,
    OSP_TO_BCF,
    BCF_TO_ESRP,
    TIMESTAMP_THRESHOLD_SECONDS,
)

from dataclasses import dataclass

from pyshark.packet.packet import Packet

from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError


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
    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    other = messages_by_type.get(FilterMessageType.OTHER)

    if not (stimulus and output and other):
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
    bcf_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None
    if not bcf_fqdn:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required FQDN records for BCF interfaces"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        key_filepath,
        bcf_fqdn,
    )


def _get_by_index(items: list, index: int):
    """Returns items[index] if it exists, otherwise None."""
    return items[index] if len(items) > index else None


def _get_media_log_event_payloads(
    bcf_logger_http_requests, log_event_type: str, key_filepath: str, call_id: str
) -> tuple:
    """
    Fetches JWS payloads for a given media LogEvent type (MediaStartLogEvent
    or MediaEndLogEvent) for one call, and returns them as
    (osp_bcf_payload, bcf_esrp_payload).

    Assumes the two expected LogEvents appear in that order in the log
    (osp_bcf leg logged before bcf_esrp leg) - this is a positional
    assumption, not derived from any payload field, since the payload
    fields themselves are what the test is verifying.
    """
    payloads = get_jws_payloads_list_by_log_event_type(
        bcf_logger_http_requests, log_event_type, key_filepath, call_id=call_id
    )
    return _get_by_index(payloads, 0), _get_by_index(payloads, 1)


def _get_variation_number(stimulus_message: Packet) -> int | None:
    """Get stimulus SDP media type and identify variation number"""

    stimulus_invite_sdp = extract_media_attributes(
        stimulus_message, return_full_attr=True
    )
    media_type = stimulus_invite_sdp.get("media_type") if stimulus_invite_sdp else None

    variation_by_media_type = {
        "audio": 1,
        "video": 2,
        "text": 3,
        "message": 4,
    }

    return variation_by_media_type.get(media_type)


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Packet | None = None
    variation_number: int = 1

    bcf_fqdn: str | None = None
    stimulus_call_id_sip: str | None = None

    bcf_call_id: str | None = None
    bcf_incident_id: str | None = None

    bcf_osp_ok_message: Packet | None = None
    bcf_osp_ok_body: str | None = None

    esrp_bcf_ok_message: Packet | None = None
    esrp_bcf_ok_body: str | None = None
    sdp_media_label: list | None = None

    is_media_established: bool = False

    osp_bcf_media_start_payload: dict | None = None
    osp_bcf_media_end_payload: dict | None = None
    bcf_esrp_media_start_payload: dict | None = None
    bcf_esrp_media_end_payload: dict | None = None

    osp_bcf_invite_ts: float | None = None
    bcf_esrp_invite_ts: float | None = None
    osp_bcf_bye_ts: float | None = None
    bcf_esrp_bye_ts: float | None = None

    ringing_status_code: int | None = None


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
        bcf_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("osp_bcf", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("bcf_esrp", other_src_ip, other_dst_ip)
    fetcher.add_route("bcf_logger", out_src_ip, out_dst_ip)

    data: dict = {
        "bcf_fqdn": bcf_fqdn,
    }

    # OSP to BCF stimulus message
    stimulus_message, stimulus_ts = fetcher.get_first_sip_invite(
        "osp_bcf", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message
    data["osp_bcf_invite_ts"] = float(stimulus_ts) if stimulus_ts else None

    if not stimulus_message:
        return TestData(**data)

    # Get BCF to ESRP INVITE message and time stamp
    bcf_esrp_invite_message, bcf_esrp_invite_ts = fetcher.get_first_sip_invite(
        "bcf_esrp", return_timestamp=True, after_timestamp=stimulus_ts
    )
    data["bcf_esrp_invite_ts"] = (
        float(bcf_esrp_invite_ts) if bcf_esrp_invite_ts else None
    )

    # Get stimulus callIdSip
    stimulus_call_ids = extract_sip_call_identifiers(stimulus_message)
    data["stimulus_call_id_sip"] = stimulus_call_ids.call_id_sip

    # Get BCF INVITE callId and incidentId
    bcf_call_ids = extract_sip_call_identifiers(bcf_esrp_invite_message)
    data["bcf_call_id"] = bcf_call_ids.call_id
    data["bcf_incident_id"] = bcf_call_ids.incident_id

    # Get stimulus SDP media type and identify variation number
    data["variation_number"] = _get_variation_number(stimulus_message)

    # Get BCF -> OSP 200 OK response, SDP body and media labels
    bcf_osp_ok_message, bcf_osp_ok_message_ts = fetcher.get_first_sip_ok(
        "bcf_osp", after_timestamp=stimulus_ts, return_timestamp=True
    )

    if bcf_osp_ok_message:
        data["bcf_osp_ok_message"] = bcf_osp_ok_message

        _bcf_osp_ok_msg = SipMessage.from_packet(bcf_osp_ok_message)
        if _bcf_osp_ok_msg:
            data["bcf_osp_ok_body"] = _bcf_osp_ok_msg.body
            data["sdp_media_label"] = extract_sdp_labels_from_string(
                _bcf_osp_ok_msg.body
            )

    # Get Ringing 180 packet and extract status code
    bcf_osp_ringing_message = fetcher.get_first_sip_ok(
        "bcf_osp", after_timestamp=stimulus_ts, message_method="Ringing"
    )

    if bcf_osp_ringing_message:
        data["ringing_status_code"] = get_final_sip_status_code(bcf_osp_ringing_message)

    # Get ESRP -> BCF 200 OK response and SDP body
    esrp_bcf_ok_message = fetcher.get_first_sip_ok("esrp_bcf")

    if esrp_bcf_ok_message:
        data["esrp_bcf_ok_message"] = esrp_bcf_ok_message

        _esrp_bcf_ok_msg = SipMessage.from_packet(esrp_bcf_ok_message)
        if _esrp_bcf_ok_msg:
            data["esrp_bcf_ok_body"] = _esrp_bcf_ok_msg.body

    # Is media established OSP <-> BCF and BCF <-> ESRP
    data["is_media_established"] = verify_media_established(
        fetcher,
        stimulus_message,
        bcf_esrp_invite_message,
        esrp_bcf_ok_message,
        bcf_osp_ok_message,
    )

    # Get BCF -> LOGGER POST requests and extract MediaStartLogEvent and MediaEndLogEvent JWS
    bcf_logger_http_requests = fetcher.get_http_posts(
        "bcf_logger", after_timestamp=bcf_osp_ok_message_ts
    )

    if bcf_logger_http_requests:
        data["osp_bcf_media_start_payload"], data["bcf_esrp_media_start_payload"] = (
            _get_media_log_event_payloads(
                bcf_logger_http_requests,
                MEDIA_START_LOG_EVENT,
                key_filepath,
                stimulus_call_ids.call_id_sip,
            )
        )
        data["osp_bcf_media_end_payload"], data["bcf_esrp_media_end_payload"] = (
            _get_media_log_event_payloads(
                bcf_logger_http_requests,
                MEDIA_END_LOG_EVENT,
                key_filepath,
                stimulus_call_ids.call_id_sip,
            )
        )

    # Get BYE messages time stamp
    _, osp_bcf_bye_ts = fetcher.get_first_sip_bye(
        "osp_bcf", after_timestamp=bcf_osp_ok_message_ts, return_timestamp=True
    )
    data["osp_bcf_bye_ts"] = float(osp_bcf_bye_ts) if osp_bcf_bye_ts else None

    _, bcf_esrp_bye_ts = fetcher.get_first_sip_bye(
        "bcf_esrp", after_timestamp=osp_bcf_bye_ts, return_timestamp=True
    )
    data["bcf_esrp_bye_ts"] = float(bcf_esrp_bye_ts) if bcf_esrp_bye_ts else None

    return TestData(**data)


# Optional LogEvent fields: a check is added only when the field is present
# in the payload. (field name, expected type, test_name suffix)
OPTIONAL_FIELD_CHECKS = (
    ("clientAssignedIdentifier", str, "value is a string if field exists"),
    ("agencyAgentId", str, "value is a string if field exists"),
    ("agencyPositionId", str, "value is a string if field exists"),
    ("ipAddressPort", None, "value is a valid IP:PORT or FQDN format"),
    ("extension", dict, "value is a object"),
)


def build_log_event_timestamp_check(
    payload,
    log_event_type: str,
    leg_label: str,
    expected_timestamp: float,
    stimulus_message,
) -> TestCheck:
    """
    Builds a single check verifying that a media LogEvent's 'timestamp'
    is within TIMESTAMP_THRESHOLD_SECONDS of the relevant SIP reference
    message time - the INVITE for MediaStartLogEvent, the BYE for
    MediaEndLogEvent, on the matching leg.
    """
    return TestCheck(
        test_name=f"Verify {log_event_type} {leg_label} 'timestamp' is within TIMESTAMP_THRESHOLD_SECONDS of the SIP reference message",
        test_method=validate_log_event_timestamp,
        precondition=stimulus_message,
        precondition_error=NOT_RUN,
        test_params={
            "actual_timestamp": get_payload_field(payload, "timestamp"),
            "expected_timestamp": expected_timestamp,
            "timestamp_threshold": TIMESTAMP_THRESHOLD_SECONDS,
        },
    )


def build_media_log_event_checks(
    payload,
    log_event_type: str,
    leg_label: str,
    test_data,
    include_all_optional: bool = False,
) -> list[TestCheck]:

    direction = "incoming" if leg_label == OSP_TO_BCF else "outgoing"

    checks = [
        TestCheck(
            test_name=f"Verify {leg_label} {log_event_type} JWS payload is present",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": payload,
                "error": f"FAILED -> No JWS payload with logEventType '{log_event_type}' found for {leg_label} leg",
            },
        ),
        TestCheck(
            test_name=f"Verify {leg_label} 'logEventType' field value is '{log_event_type}'",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": log_event_type,
                "actual_data": get_payload_field(payload, "logEventType"),
            },
        ),
        TestCheck(
            test_name=f"Verify {leg_label} {log_event_type} 'timestamp' field value format",
            test_method=verify_timestamp_format,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "timestamp": get_payload_field(payload, "timestamp"),
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'elementId' field value contains FQDN of BCF",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.bcf_fqdn,
                "actual_data": get_payload_field(payload, "elementId"),
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'agencyId' field value contain a valid FQDN format",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": (
                    is_valid_fqdn(agency_id)
                    if (agency_id := get_payload_field(payload, "agencyId"))
                    else False
                ),
                "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record for of {leg_label} {log_event_type}. Actual: {agency_id}",
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'callId' the same value as BCF SIP INVITE 'callId'",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.bcf_call_id,
                "actual_data": get_payload_field(payload, "callId"),
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'callId' value format",
            test_method=verify_call_id_format,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "call_id": get_payload_field(payload, "callId"),
                "event_type": log_event_type,
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'incidentId' the same value as BCF SIP INVITE 'incidentId'",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.bcf_incident_id,
                "actual_data": get_payload_field(payload, "incidentId"),
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'incidentId' value format",
            test_method=verify_incident_id_format,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "incident_id": get_payload_field(payload, "incidentId"),
                "event_type": log_event_type,
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'callIdSip' the same value as stimulus SIP INVITE 'Call-ID'",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.stimulus_call_id_sip,
                "actual_data": get_payload_field(payload, "callIdSip"),
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} 'callIdSip' value format",
            test_method=verify_call_id_sip,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "call_id": get_payload_field(payload, "callIdSip"),
                "event_type": log_event_type,
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} direction value is '{direction}'",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": direction,
                "actual_data": get_payload_field(payload, "direction"),
            },
        ),
        TestCheck(
            test_name=f"Verify {log_event_type} {leg_label} mediaLabel value matches SDP",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.sdp_media_label,
                "actual_data": get_payload_field(payload, "mediaLabel"),
            },
        ),
    ]

    # Optional fields: checked only if present in the payload
    for field_name, expected_type, name_suffix in OPTIONAL_FIELD_CHECKS:
        value = get_payload_field(payload, field_name)
        if value is None and not include_all_optional:
            continue

        test_name = f"Verify {log_event_type} {leg_label} '{field_name}' {name_suffix}"

        if field_name == "ipAddressPort":
            checks.append(
                TestCheck(
                    test_name=test_name,
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": is_valid_ip_or_fqdn(value),
                        "error": f"FAILED -> Invalid IP:PORT or FQDN value for '{log_event_type}'. Received: '{value}'",
                    },
                )
            )
        else:
            checks.append(
                TestCheck(
                    test_name=test_name,
                    test_method=is_type,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "param": value,
                        "param_name": field_name,
                        "expected_type": expected_type,
                    },
                )
            )

    return checks


def build_media_start_end_session_match_checks(
    media_start_payload, media_end_payload, leg_label: str, stimulus_message
) -> list[TestCheck]:
    """
    Builds checks verifying that MediaStartLogEvent and MediaEndLogEvent
    payloads for the same leg refer to the same call session, by
    comparing their callId, incidentId, callIdSip, and mediaLabel values.
    """
    fields_to_compare = ["callId", "incidentId", "callIdSip", "mediaLabel"]

    return [
        TestCheck(
            test_name=f"Verify MediaStartLogEvent and MediaEndLogEvent '{field}' values are identical for {leg_label}",
            test_method=is_test_data_the_same,
            precondition=stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": get_payload_field(media_start_payload, field),
                "actual_data": get_payload_field(media_end_payload, field),
            },
        )
        for field in fields_to_compare
    ]


def get_test_names() -> list:
    test_names_list = [
        "Verify ESRP responded 200 OK to BCF",
        "Verify BCF responded 200 OK to OSP",
        "Verify if media established on the OSP-BCF-ESRP path",
    ]

    # --- Test name generation ---
    # build_media_log_event_checks(), build_media_start_end_session_match_checks()
    # and build_log_event_timestamp_check() are dummy-called here
    # (payload=None, stub TestData()) purely to extract
    # their test_name strings, without needing any real pcap data. This is
    # safe because constructing a TestCheck never executes test_method, and
    # test_name only depends on the log_event_type/leg_label strings passed
    # in - never on the payload/test_data contents. Reusing the same builder
    # functions here guarantees these names can never drift out of sync with
    # what get_test_list() actually produces below.
    # include_all_optional=True registers the names of the optional-field
    # checks too, even though a real run only produces them when the field
    # is present in the payload.

    stub_test_data = TestData()

    for log_event_type, leg_label in [
        (MEDIA_START_LOG_EVENT, OSP_TO_BCF),
        (MEDIA_START_LOG_EVENT, BCF_TO_ESRP),
        (MEDIA_END_LOG_EVENT, OSP_TO_BCF),
        (MEDIA_END_LOG_EVENT, BCF_TO_ESRP),
    ]:
        checks = build_media_log_event_checks(
            payload=None,
            log_event_type=log_event_type,
            leg_label=leg_label,
            test_data=stub_test_data,
            include_all_optional=True,
        )
        test_names_list += [check.test_name for check in checks]

        # expected_timestamp doesn't affect test_name, so None is fine here
        test_names_list.append(
            build_log_event_timestamp_check(
                None, log_event_type, leg_label, None, None
            ).test_name
        )

    for leg_label in [OSP_TO_BCF, BCF_TO_ESRP]:
        checks = build_media_start_end_session_match_checks(
            media_start_payload=None,
            media_end_payload=None,
            leg_label=leg_label,
            stimulus_message=None,
        )
        test_names_list += [check.test_name for check in checks]

    test_names_list.extend(
        [
            "Verify MediaStartLogEvent 'SDP' the same value as the body of 200 OK BCF response (OSP-BCF)",
            "Verify MediaStartLogEvent 'SDP' the same value as the body of 200 OK ESRP response (BCF-ESRP)",
            "Verify MediaEndLogEvent 'mediaQualityStats' value for (OSP-BCF)",
            "Verify MediaEndLogEvent 'mediaQualityStats' value for (BCF-ESRP)",
        ]
    )

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

    check_list = []

    check_list.extend(
        [
            TestCheck(
                test_name="Verify ESRP responded 200 OK to BCF",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.esrp_bcf_ok_message,
                    "error": "NOT RUN -> No ESRP to BCF 200 OK response found",
                },
            ),
            TestCheck(
                test_name="Verify BCF responded 200 OK to OSP",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.bcf_osp_ok_message
                    or test_data.ringing_status_code == 200,
                    "error": "FAILED -> No BCF to OSP 200 OK response found",
                },
            ),
            TestCheck(
                test_name="Verify if media established on the OSP-BCF-ESRP path",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.is_media_established,
                    "error": "FAILED -> No established media found on the OSP-BCF-ESRP path",
                },
            ),
            TestCheck(
                test_name="Verify MediaStartLogEvent 'SDP' the same value as the body of 200 OK BCF response (OSP-BCF)",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.bcf_osp_ok_body,
                    "actual_data": get_payload_field(
                        test_data.osp_bcf_media_start_payload, "sdp"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify MediaStartLogEvent 'SDP' the same value as the body of 200 OK ESRP response (BCF-ESRP)",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.esrp_bcf_ok_body,
                    "actual_data": get_payload_field(
                        test_data.bcf_esrp_media_start_payload, "sdp"
                    ),
                },
            ),
        ]
    )

    if test_data.variation_number in (1, 2):
        check_list += [
            TestCheck(
                test_name="Verify MediaEndLogEvent 'mediaQualityStats' value for (OSP-BCF)",
                test_method=verify_media_quality_stats,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "media_stats": get_payload_field(
                        test_data.osp_bcf_media_end_payload, "mediaQualityStats"
                    ),
                    "log_event_type": MEDIA_END_LOG_EVENT,
                },
            ),
            TestCheck(
                test_name="Verify MediaEndLogEvent 'mediaQualityStats' value for (BCF-ESRP)",
                test_method=verify_media_quality_stats,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "media_stats": get_payload_field(
                        test_data.bcf_esrp_media_end_payload, "mediaQualityStats"
                    ),
                    "log_event_type": MEDIA_END_LOG_EVENT,
                },
            ),
        ]

    # --- Real check construction ---
    # Same builder functions as in get_test_names(), now called with the
    # real payload and test_data extracted from the pcap, producing the
    # TestCheck objects that will actually run. Optional-field checks are
    # built only for the fields actually present in each payload.

    for log_event_type, leg_label, payload, expected_timestamp in [
        (
            MEDIA_START_LOG_EVENT,
            OSP_TO_BCF,
            test_data.osp_bcf_media_start_payload,
            test_data.osp_bcf_invite_ts,
        ),
        (
            MEDIA_START_LOG_EVENT,
            BCF_TO_ESRP,
            test_data.bcf_esrp_media_start_payload,
            test_data.bcf_esrp_invite_ts,
        ),
        (
            MEDIA_END_LOG_EVENT,
            OSP_TO_BCF,
            test_data.osp_bcf_media_end_payload,
            test_data.osp_bcf_bye_ts,
        ),
        (
            MEDIA_END_LOG_EVENT,
            BCF_TO_ESRP,
            test_data.bcf_esrp_media_end_payload,
            test_data.bcf_esrp_bye_ts,
        ),
    ]:
        check_list += build_media_log_event_checks(
            payload=payload,
            log_event_type=log_event_type,
            leg_label=leg_label,
            test_data=test_data,
        )

        check_list.append(
            build_log_event_timestamp_check(
                payload,
                log_event_type,
                leg_label,
                expected_timestamp,
                test_data.stimulus_message,
            )
        )

    check_list += build_media_start_end_session_match_checks(
        test_data.osp_bcf_media_start_payload,
        test_data.osp_bcf_media_end_payload,
        OSP_TO_BCF,
        test_data.stimulus_message,
    )
    check_list += build_media_start_end_session_match_checks(
        test_data.bcf_esrp_media_start_payload,
        test_data.bcf_esrp_media_end_payload,
        BCF_TO_ESRP,
        test_data.stimulus_message,
    )

    return check_list
