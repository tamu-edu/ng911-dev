from dataclasses import dataclass, field
from typing import Any, Optional

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present, is_test_data_the_same
from checks.log_events.check import (
    assert_required_payload_fields,
    optional_attributes_validation,
    verify_timestamp_format,
    extract_enclosed_value,
    verify_call_id_format,
    verify_incident_id_format,
    verify_call_id_sip,
    verify_query_id,
    get_payload_field,
)
from services.aux_services.json_services import EasyJSON, is_valid_fqdn
from services.aux_services.message_services import get_message_and_jws_by_event_type
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_015.checks import validate_text_field

from tests.CHFE_015.constants import (
    NOT_RUN,
    REQUIRED_FIELDS,
    QUERY_EVENT_NAME,
    OPTIONAL_FIELDS,
)


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    stimulus_timestamp: Optional[float] = None
    stimulus_src_ip: Optional[str] = None
    variation_number: int = 2

    chfe_to_lis_http_post_message: Any = None
    chfe_to_lis_http_post_message_body: Optional[str] = None
    lis_to_chfe_http_response_message: Any = None

    chfe_to_lis_subscribe_request: Any = None
    chfe_to_lis_subscribe_message_body: Optional[str] = None
    lis_to_chfe_notify_response: Any = None

    chfe_to_logger_post_messages: Any = None
    chfe_to_logger_post_location_query_jws: dict = field(default_factory=dict)
    query_jws_payload: Any = None

    chfe_fqdn: Optional[str] = None
    stimulus_call_id_sip: Optional[str] = None
    stimulus_call_id: Optional[str] = None
    stimulus_incident_id: Optional[str] = None
    geolocation_raw: Optional[str] = None


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

    ip_by_interface = {}
    key_filepath = None
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface[interface.name] = interface.ip
            if interface.name == output.src_interface:
                key_filepath = entity.certificate_key

    stimulus_src_ip = ip_by_interface.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface.get(stimulus.dst_interface)
    out_scr_ip = ip_by_interface.get(output.src_interface)
    out_dst_ip = ip_by_interface.get(output.dst_interface)
    other_src_ip = ip_by_interface.get(other.src_interface)
    other_dst_ip = ip_by_interface.get(other.dst_interface)

    if None in (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
    ):
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
        out_scr_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        key_filepath,
        chfe_fqdn,
    )


def get_query_jws_payload_and_msgs(
    fetcher: PacketFetcher, after_timestamp, key_filepath
):
    """
    Fetches CHFE -> LOGGER POST messages and extracts the JWS payload
    for the LocationQueryLogEvent event type.

    :return: tuple (jws_payload, messages)
    """
    messages = fetcher.get_http_posts("chfe_logger", after_timestamp=after_timestamp)

    jws_payload, _ = get_message_and_jws_by_event_type(
        messages, "LocationQueryLogEvent", key_filepath
    )

    return jws_payload, messages


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> TestData:
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        key_filepath,
        chfe_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    msg_fetcher = PacketFetcher(pcap_service)
    msg_fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("chfe_lis", other_src_ip, other_dst_ip)
    msg_fetcher.add_route("chfe_logger", out_src_ip, out_dst_ip)

    data: dict = {}
    data["chfe_fqdn"] = chfe_fqdn

    # ESRP to CHFE stimulus message
    stimulus_message, stimulus_timestamp = msg_fetcher.get_first_sip_invite(
        "esrp_chfe", return_timestamp=True
    )
    stimulus_msg = (
        SipMessage.from_packet(stimulus_message) if stimulus_message else None
    )

    data["stimulus_message"] = stimulus_message
    data["stimulus_timestamp"] = stimulus_timestamp
    data["stimulus_src_ip"] = stimulus_src_ip

    if not stimulus_message:
        return TestData(**data)

    # CHFE to LIS HTTP POST request
    chfe_to_lis_http_post_message, chfe_to_lis_http_post_ts = (
        msg_fetcher.get_first_http_post(
            "chfe_lis", after_timestamp=stimulus_timestamp, return_timestamp=True
        )
    )
    data["chfe_to_lis_http_post_message"] = chfe_to_lis_http_post_message

    if chfe_to_lis_http_post_message:
        data["chfe_to_lis_http_post_message_body"] = HttpMessage.from_packet(
            chfe_to_lis_http_post_message
        ).body

        lis_to_chfe_http_response_message = msg_fetcher.get_first_http(
            "lis_chfe", after_timestamp=chfe_to_lis_http_post_ts
        )
        data["lis_to_chfe_http_response_message"] = lis_to_chfe_http_response_message

    # CHFE to LIS SUBSCRIBE request
    chfe_to_lis_subscribe_request, chfe_to_lis_subscribe_ts = (
        msg_fetcher.get_first_sip_subscribe(
            "chfe_lis", after_timestamp=stimulus_timestamp, return_timestamp=True
        )
    )
    data["chfe_to_lis_subscribe_request"] = chfe_to_lis_subscribe_request

    if chfe_to_lis_subscribe_request:
        data["chfe_to_lis_subscribe_message_body"] = SipMessage.from_packet(
            chfe_to_lis_subscribe_request
        ).body

        lis_to_chfe_notify_response = msg_fetcher.get_first_sip_notify(
            "lis_chfe", after_timestamp=chfe_to_lis_subscribe_ts
        )
        data["lis_to_chfe_notify_response"] = lis_to_chfe_notify_response

    # Geolocation + variation
    variation_number = 2
    geolocation_raw = None
    if stimulus_msg and stimulus_msg.geolocation:
        geolocation_raw = extract_enclosed_value(stimulus_msg.geolocation[0])
    if geolocation_raw and "heldLocation" in geolocation_raw:
        variation_number = 1

    data["geolocation_raw"] = geolocation_raw
    data["variation_number"] = variation_number

    # CHFE to LOGGER: LocationQueryLogEvent
    after_timestamp = (
        chfe_to_lis_http_post_ts if variation_number == 1 else chfe_to_lis_subscribe_ts
    )
    if chfe_to_lis_http_post_message or chfe_to_lis_subscribe_request:
        query_jws, logger_messages = get_query_jws_payload_and_msgs(
            msg_fetcher, after_timestamp, key_filepath
        )
        data["chfe_to_logger_post_location_query_jws"] = query_jws or {}
        data["chfe_to_logger_post_messages"] = logger_messages
        data["query_jws_payload"] = EasyJSON(query_jws) if query_jws else None

    # Get Stimulus Call-ID, CallId, IncidentId
    if stimulus_msg:
        data["stimulus_call_id_sip"] = (
            str(stimulus_msg.call_id) if stimulus_msg.call_id is not None else None
        )
        call_info = stimulus_msg.call_info
        if call_info:
            data["stimulus_call_id"] = next(
                (line for line in call_info if "CallId" in line), None
            )
            data["stimulus_incident_id"] = next(
                (line for line in call_info if "IncidentId" in line), None
            )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Verify CHFE to LIS HTTP HELD location request message sent",
        "Verify LIS to CHFE HTTP HELD location response message sent",
        "Verify CHFE to LIS SIP SUBSCRIBE request message sent",
        "Verify LIS to CHFE NOTIFY message sent",
        "Verify CHFE to LOGGER HTTP POST message sent",
        "Verify JWS payload is present",
        "Verify Event mandatory fields are available",
        "Verify Event optional fields",
        "Verify 'logEventType' is 'LocationQueryLogEvent'",
        "Verify 'timestamp' format",
        "Verify 'elementId' contains FQDN of CHFE",
        "Verify 'agencyId' contains FQDN format record",
        "Verify the same value as callId in the SIP INVITE from ESRP",
        "Verify callId value format",
        "Verify the same value as incidentId in the SIP INVITE from ESRP",
        "Verify incidentId value format",
        "Verify callId value format",
        "Verify the same value as callIdSip in the SIP INVITE from ESRP",
        "Verify callIdSip value format",
        "Verify direction value is 'outgoing'",
        "Verify queryId value format",
        "Verify URI value the same as stimulus Geolocation value",
        "Verify 'text' value the same as outbound request body from CHFE to LIS",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation
    )

    payload = test_data.query_jws_payload

    check_list = []

    if test_data.variation_number == 1:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify CHFE to LIS HTTP HELD location request message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.chfe_to_lis_http_post_message,
                        "error": "FAILED -> CHFE to LIS HTTP HELD location request message not found",
                    },
                ),
                TestCheck(
                    test_name="Verify LIS to CHFE HTTP HELD location response message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.lis_to_chfe_http_response_message,
                        "error": "NOT RUN -> LIS to CHFE HTTP HELD location response message not found",
                    },
                ),
            ]
        )
    elif test_data.variation_number == 2:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify CHFE to LIS SIP SUBSCRIBE request message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.chfe_to_lis_subscribe_request,
                        "error": "FAILED -> CHFE to LIS SIP SUBSCRIBE request message not found",
                    },
                ),
                TestCheck(
                    test_name="Verify LIS to CHFE NOTIFY message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.lis_to_chfe_notify_response,
                        "error": "NOT RUN -> LIS to CHFE NOTIFY message not found",
                    },
                ),
            ]
        )

    check_list.extend(
        [
            TestCheck(
                test_name="Verify CHFE to LOGGER HTTP POST message sent",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.chfe_to_logger_post_messages,
                    "error": "FAILED -> CHFE to LOGGER HTTP POST message not found",
                },
            ),
            TestCheck(
                test_name="Verify JWS payload is present",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.query_jws_payload,
                    "error": "FAILED -> No JWS payload with logEventType 'LocationQueryLogEvent' found",
                },
            ),
            TestCheck(
                test_name="Verify Event mandatory fields are available",
                test_method=assert_required_payload_fields,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "payload_data": test_data.chfe_to_logger_post_location_query_jws,
                    "fields": REQUIRED_FIELDS,
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify Event optional fields",
                test_method=optional_attributes_validation,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "payload_data": test_data.chfe_to_logger_post_location_query_jws,
                    "optional_fields": OPTIONAL_FIELDS,
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify 'logEventType' is 'LocationQueryLogEvent'",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": "LocationQueryLogEvent",
                    "actual_data": get_payload_field(payload, "logEventType"),
                },
            ),
            TestCheck(
                test_name="Verify 'timestamp' format",
                test_method=verify_timestamp_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "timestamp": get_payload_field(payload, "timestamp"),
                },
            ),
            TestCheck(
                test_name="Verify 'elementId' contains FQDN of CHFE",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.chfe_fqdn,
                    "actual_data": get_payload_field(payload, "elementId"),
                },
            ),
            TestCheck(
                test_name="Verify 'agencyId' contains FQDN format record",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": (
                        is_valid_fqdn(agency_id)
                        if (agency_id := get_payload_field(payload, "agencyId"))
                        else False
                    ),
                    "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record. Actual: {agency_id}",
                },
            ),
            TestCheck(
                test_name="Verify the same value as callId in the SIP INVITE from ESRP",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": extract_enclosed_value(test_data.stimulus_call_id),
                    "actual_data": get_payload_field(payload, "callId"),
                },
            ),
            TestCheck(
                test_name="Verify callId value format",
                test_method=verify_call_id_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "call_id": extract_enclosed_value(
                        get_payload_field(payload, "callId")
                    ),
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify the same value as incidentId in the SIP INVITE from ESRP",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": extract_enclosed_value(
                        test_data.stimulus_incident_id
                    ),
                    "actual_data": get_payload_field(payload, "incidentId"),
                },
            ),
            TestCheck(
                test_name="Verify incidentId value format",
                test_method=verify_incident_id_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "incident_id": extract_enclosed_value(
                        get_payload_field(payload, "incidentId")
                    ),
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify the same value as callIdSip in the SIP INVITE from ESRP",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": extract_enclosed_value(
                        test_data.stimulus_call_id_sip
                    ),
                    "actual_data": get_payload_field(payload, "callIdSip"),
                },
            ),
            TestCheck(
                test_name="Verify callIdSip value format",
                test_method=verify_call_id_sip,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "call_id": extract_enclosed_value(
                        get_payload_field(payload, "callIdSip")
                    ),
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify direction value is 'outgoing'",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": "outgoing",
                    "actual_data": get_payload_field(payload, "direction"),
                },
            ),
            TestCheck(
                test_name="Verify queryId value format",
                test_method=verify_query_id,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "query_id": extract_enclosed_value(
                        get_payload_field(payload, "queryId")
                    ),
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify URI value the same as stimulus Geolocation value",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": extract_enclosed_value(test_data.geolocation_raw),
                    "actual_data": get_payload_field(payload, "uri"),
                },
            ),
            TestCheck(
                test_name="Verify 'text' value the same as outbound request body from CHFE to LIS",
                test_method=validate_text_field,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "text_field_value": get_payload_field(payload, "text"),
                    "test_data": test_data,
                    "event_type": QUERY_EVENT_NAME,
                },
            ),
        ]
    )

    return check_list
