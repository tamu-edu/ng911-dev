from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
    verify_value_present_in_collection,
)
from checks.http.checks import is_type
from checks.log_events.check import (
    get_payload_field,
    verify_timestamp_format,
    extract_enclosed_value,
    verify_call_id_format,
    verify_incident_id_format,
    verify_call_id_sip,
    is_valid_ip_or_fqdn,
)
from services.aux_services.json_services import is_valid_fqdn
from services.messages.packet_fetcher import PacketFetcher
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_017.checks import validate_text_field

from dataclasses import dataclass
from typing import Any, Optional

from pyshark.packet.packet import Packet

from services.aux_services.message_services import (
    get_message_and_jws_by_event_type,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.http.http_message import HttpMessage
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from tests.CHFE_017.constants import (
    NOT_RUN,
    RESPONSE_EVENT_NAME,
    QUERY_EVENT_NAME,
    RESPONSE_CODES,
)


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
    chfe_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None
    if not chfe_fqdn:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required FQDN records for chfe interfaces"
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
    )


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    variation_number: int = 3

    chfe_fqdn: Optional[str] = None
    stimulus_call_id_sip: Optional[str] = None
    stimulus_call_id: Optional[str] = None
    stimulus_incident_id: Optional[str] = None

    chfe_to_lis_http_post_message: Any = None
    lis_to_chfe_http_response_message: Any = None
    lis_to_chfe_response_message_body: Optional[str] = None

    chfe_to_lis_subscribe_request: Any = None
    lis_to_chfe_notify_response: Any = None
    lis_to_chfe_notify_response_message_body: Optional[str] = None

    chfe_to_logger_post_location_query_jws: Optional[dict] = None
    chfe_to_logger_post_location_response_jws: Optional[dict] = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
    variation_number: int = 1,
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
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_lis", other_src_ip, other_dst_ip)
    fetcher.add_route("chfe_logger", out_src_ip, out_dst_ip)

    data: dict = {
        "chfe_fqdn": chfe_fqdn,
        "stimulus_call_id_sip": "",
        "variation_number": variation_number,
    }

    # ESRP to CHFE stimulus message
    stimulus_message, stimulus_timestamp = fetcher.get_first_sip_invite(
        "esrp_chfe", return_timestamp=True
    )
    stimulus_msg = (
        SipMessage.from_packet(stimulus_message) if stimulus_message else None
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get Stimulus Call-ID, CallId, IncidentId
    if stimulus_msg:
        data["stimulus_call_id_sip"] = str(stimulus_msg.call_id)
        call_info = stimulus_msg.call_info
        if call_info:
            data["stimulus_call_id"] = next(
                (line for line in call_info if "CallId" in line), None
            )
            data["stimulus_incident_id"] = next(
                (line for line in call_info if "IncidentId" in line), None
            )

    # CHFE to LIS HTTP POST request
    chfe_to_lis_http_post_message, chfe_to_lis_http_post_ts = (
        fetcher.get_first_http_post(
            "chfe_lis", after_timestamp=stimulus_timestamp, return_timestamp=True
        )
    )
    data["chfe_to_lis_http_post_message"] = chfe_to_lis_http_post_message

    if chfe_to_lis_http_post_message:
        # LIS to CHFE HTTP response and body
        lis_to_chfe_http_response_message = fetcher.get_first_http(
            "lis_chfe", after_timestamp=chfe_to_lis_http_post_ts
        )
        data["lis_to_chfe_http_response_message"] = lis_to_chfe_http_response_message

        if lis_to_chfe_http_response_message:
            lis_response_msg = HttpMessage.from_packet(
                lis_to_chfe_http_response_message
            )
            data["lis_to_chfe_response_message_body"] = lis_response_msg.body

    # CHFE to LIS SUBSCRIBE request
    chfe_to_lis_subscribe_request, chfe_to_lis_subscribe_ts = (
        fetcher.get_first_sip_subscribe(
            "chfe_lis", after_timestamp=stimulus_timestamp, return_timestamp=True
        )
    )
    data["chfe_to_lis_subscribe_request"] = chfe_to_lis_subscribe_request

    if chfe_to_lis_subscribe_request:

        # Get Subscribe Call-ID for NOTIFY filtering
        subscribe_msg = SipMessage.from_packet(chfe_to_lis_subscribe_request)
        subscribe_call_id = str(subscribe_msg.call_id)

        # LIS to CHFE SIP NOTIFY response
        lis_to_chfe_notify_response = fetcher.get_first_sip_notify(
            "lis_chfe",
            after_timestamp=chfe_to_lis_subscribe_ts,
            call_id=subscribe_call_id,
        )
        data["lis_to_chfe_notify_response"] = lis_to_chfe_notify_response

        if lis_to_chfe_notify_response:
            data["lis_to_chfe_notify_response_message_body"] = SipMessage.from_packet(
                lis_to_chfe_notify_response
            ).body

    # Get Message and JWS of CHFE to LOG LocationQueryLogEvent
    after_timestamp = (
        chfe_to_lis_http_post_ts
        if variation_number in (1, 3)
        else chfe_to_lis_subscribe_ts
    )

    if chfe_to_lis_http_post_message or (
        chfe_to_lis_subscribe_request
        and (chfe_to_lis_http_post_ts or chfe_to_lis_subscribe_ts)
    ):
        query_messages = fetcher.get_http_posts(
            "chfe_logger", after_timestamp=after_timestamp
        )
        query_jws, query_message = get_message_and_jws_by_event_type(
            query_messages, QUERY_EVENT_NAME, key_filepath
        )
        data["chfe_to_logger_post_location_query_jws"] = query_jws

        # Get Message and JWS of CHFE to LOG LocationResponseLogEvent
        if query_message:
            response_messages = fetcher.get_http_posts(
                "chfe_logger", after_timestamp=chfe_to_lis_http_post_ts
            )

            response_jws, _ = get_message_and_jws_by_event_type(
                response_messages, RESPONSE_EVENT_NAME, key_filepath
            )
            data["chfe_to_logger_post_location_response_jws"] = response_jws

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Verify CHFE to LIS HELD location request message sent",
        "Verify CHFE to LIS SIP SUBSCRIBE message sent",
        "Verify LIS to CHFE HELD location response message sent",
        "Verify LIS to CHFE SIP NOTIFY message sent",
        # LocationResponseLogEvent check set
        "Verify LocationResponseLogEvent JWS Query payload is present",
        "Verify LocationResponseLogEvent JWS Response payload is present",
        "Verify LocationResponseLogEvent 'logEventType' field value",
        "Verify LocationResponseLogEvent 'timestamp' field value format",
        "Verify LocationResponseLogEvent 'elementId' field value contains FQDN of CHFE",
        "Verify LocationResponseLogEvent 'agencyId' field value contain a valid FQDN format",
        "Verify LocationResponseLogEvent 'callId' the same value as callId in the SIP INVITE from ESRP",
        "Verify LocationResponseLogEvent 'callId' value format",
        "Verify the same value as incidentId in the SIP INVITE from ESRP",
        "Verify LocationResponseLogEvent 'incidentId' value format",
        "Verify the same value as 'callIdSip' in the SIP INVITE from ESRP",
        "Verify LocationResponseLogEvent 'callIdSip' value format",
        "Verify LocationResponseLogEvent direction value is 'incoming'",
        "Verify LocationResponseLogEvent 'text' field value the same as received HTTP or SIP NOTIFY body from LIS to CHFE",
        "Verify LocationResponseLogEvent 'responseId' field value identical to the 'queryId'",
        "Verify LocationResponseLogEvent 'clientAssignedIdentifier' value is a string if field exists",
        "Verify LocationResponseLogEvent 'agencyAgentId' value is a string if field exists",
        "Verify LocationResponseLogEvent 'agencyPositionId' value is a string if field exists",
        "Verify LocationResponseLogEvent 'ipAddressPort' value is a valid IP:PORT or FQDN format",
        "Verify LocationResponseLogEvent 'extension' value is a dictionary object if field exists",
        "Verify LocationResponseLogEvent 'responseStatus' field value if exists in Status Codes Registry",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:

    variations = {
        "HELD_dereference_response": 1,
        "SIP_presence_dereference": 2,
        "Malformed_HELD_dereference_response": 3,
    }

    if run_variation.name in variations:
        variation_number = variations.get(run_variation.name)
    else:
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation, variation_number
    )

    query_payload = test_data.chfe_to_logger_post_location_query_jws
    response_payload = test_data.chfe_to_logger_post_location_response_jws

    check_list = []

    if variation_number in (1, 3):

        check_list.extend(
            [
                TestCheck(
                    test_name="Verify CHFE to LIS HELD location request message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.chfe_to_lis_http_post_message,
                        "error": "FAILED -> CHFE to LIS HELD location request not found",
                    },
                ),
                TestCheck(
                    test_name="Verify LIS to CHFE HELD location response message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.lis_to_chfe_http_response_message,
                        "error": "NOT RUN -> LIS to CHFE HELD location response not found",
                    },
                ),
            ]
        )

    elif variation_number == 2:

        check_list.extend(
            [
                TestCheck(
                    test_name="Verify CHFE to LIS SIP SUBSCRIBE message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.chfe_to_lis_subscribe_request,
                        "error": "FAILED -> CHFE to LIS SIP SUBSCRIBE message not found",
                    },
                ),
                TestCheck(
                    test_name="Verify LIS to CHFE SIP NOTIFY message sent",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.lis_to_chfe_notify_response,
                        "error": "NOT RUN -> LIS to CHFE SIP NOTIFY message not found",
                    },
                ),
            ]
        )

    check_list.extend(
        [
            TestCheck(
                test_name="Verify LocationResponseLogEvent JWS Query payload is present",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": query_payload,
                    "error": "FAILED -> No JWS response_payload with logEventType 'LocationQueryLogEvent' found",
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent JWS Response payload is present",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": response_payload,
                    "error": "FAILED -> No JWS response_payload with logEventType 'LocationResponseLogEvent' found",
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'logEventType' field value",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": "LocationResponseLogEvent",
                    "actual_data": get_payload_field(response_payload, "logEventType"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'timestamp' field value format",
                test_method=verify_timestamp_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "timestamp": get_payload_field(response_payload, "timestamp"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'elementId' field value contains FQDN of CHFE",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": test_data.chfe_fqdn,
                    "actual_data": get_payload_field(response_payload, "elementId"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'agencyId' field value contain a valid FQDN format",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": (
                        is_valid_fqdn(agency_id)
                        if (
                            agency_id := get_payload_field(response_payload, "agencyId")
                        )
                        else False
                    ),
                    "error": f"FAILED -> 'agencyId' does not contain a valid FQDN format record. Actual: {agency_id}",
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'callId' the same value as callId in the SIP INVITE from ESRP",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": extract_enclosed_value(test_data.stimulus_call_id),
                    "actual_data": get_payload_field(response_payload, "callId"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'callId' value format",
                test_method=verify_call_id_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "call_id": extract_enclosed_value(
                        get_payload_field(response_payload, "callId")
                    ),
                    "event_type": RESPONSE_EVENT_NAME,
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
                    "actual_data": get_payload_field(response_payload, "incidentId"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'incidentId' value format",
                test_method=verify_incident_id_format,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "incident_id": extract_enclosed_value(
                        get_payload_field(response_payload, "incidentId")
                    ),
                    "event_type": RESPONSE_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify the same value as 'callIdSip' in the SIP INVITE from ESRP",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": extract_enclosed_value(
                        test_data.stimulus_call_id_sip
                    ),
                    "actual_data": get_payload_field(response_payload, "callIdSip"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'callIdSip' value format",
                test_method=verify_call_id_sip,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "call_id": extract_enclosed_value(
                        get_payload_field(response_payload, "callIdSip")
                    ),
                    "event_type": RESPONSE_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent direction value is 'incoming'",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": "incoming",
                    "actual_data": get_payload_field(response_payload, "direction"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'text' field value the same as received HTTP or SIP NOTIFY body from LIS to CHFE",
                test_method=validate_text_field,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "text_field_value": get_payload_field(response_payload, "text"),
                    "test_data": test_data,
                    "event_type": RESPONSE_EVENT_NAME,
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'responseId' field value identical to the 'queryId'",
                test_method=is_test_data_the_same,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "expected_data": get_payload_field(query_payload, "queryId"),
                    "actual_data": get_payload_field(response_payload, "responseId"),
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'clientAssignedIdentifier' value is a string if field exists",
                test_method=is_type,
                precondition=(
                    None
                    if not test_data.stimulus_message
                    else (
                        _v := get_payload_field(
                            response_payload, "clientAssignedIdentifier"
                        )
                    )
                    is not None
                ),
                precondition_error=(
                    NOT_RUN if not test_data.stimulus_message else "PASSED"
                ),
                test_params={
                    "param": _v if test_data.stimulus_message else None,
                    "param_name": "clientAssignedIdentifier",
                    "expected_type": str,
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'agencyAgentId' value is a string if field exists",
                test_method=is_type,
                precondition=(
                    None
                    if not test_data.stimulus_message
                    else (_v := get_payload_field(response_payload, "agencyAgentId"))
                    is not None
                ),
                precondition_error=(
                    NOT_RUN if not test_data.stimulus_message else "PASSED"
                ),
                test_params={
                    "param": _v if test_data.stimulus_message else None,
                    "param_name": "agencyAgentId",
                    "expected_type": str,
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'agencyPositionId' value is a string if field exists",
                test_method=is_type,
                precondition=(
                    None
                    if not test_data.stimulus_message
                    else (_v := get_payload_field(response_payload, "agencyPositionId"))
                    is not None
                ),
                precondition_error=(
                    NOT_RUN if not test_data.stimulus_message else "PASSED"
                ),
                test_params={
                    "param": _v if test_data.stimulus_message else None,
                    "param_name": "agencyPositionId",
                    "expected_type": str,
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'ipAddressPort' value is a valid IP:PORT or FQDN format",
                test_method=is_data_present,
                precondition=(
                    None
                    if not test_data.stimulus_message
                    else (
                        ip_address_value := get_payload_field(
                            response_payload, "ipAddressPort"
                        )
                    )
                    is not None
                ),
                precondition_error=(
                    NOT_RUN if not test_data.stimulus_message else "PASSED"
                ),
                test_params={
                    "test_data": (
                        is_valid_ip_or_fqdn(ip_address_value)
                        if test_data.stimulus_message
                        else False
                    ),
                    "error": f"FAILED -> Invalid IP:PORT or FQDN value for '{RESPONSE_EVENT_NAME}'. Received: '{ip_address_value if test_data.stimulus_message else None}'",
                },
            ),
            TestCheck(
                test_name="Verify LocationResponseLogEvent 'extension' value is a dictionary object if field exists",
                test_method=is_type,
                precondition=(
                    None
                    if not test_data.stimulus_message
                    else (_v := get_payload_field(response_payload, "extension"))
                    is not None
                ),
                precondition_error=(
                    NOT_RUN if not test_data.stimulus_message else "PASSED"
                ),
                test_params={
                    "param": _v if test_data.stimulus_message else None,
                    "param_name": "extension",
                    "expected_type": dict,
                },
            ),
        ]
    )
    if test_data.variation_number == 3:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify LocationResponseLogEvent 'responseStatus' field value if exists in Status Codes Registry",
                    test_method=verify_value_present_in_collection,
                    precondition=(
                        None
                        if not test_data.stimulus_message
                        else (
                            _v := get_payload_field(response_payload, "responseStatus")
                        )
                        is not None
                    ),
                    precondition_error=(
                        NOT_RUN if not test_data.stimulus_message else "PASSED"
                    ),
                    test_params={
                        "actual_data": _v if test_data.stimulus_message else None,
                        "allowed_values": RESPONSE_CODES,
                        "error": f"FAILED -> 'responseStatus' not found in Status Codes Registry for '{RESPONSE_EVENT_NAME}'. Received: '{_v if test_data.stimulus_message else None}'",
                    },
                ),
            ]
        )

    return check_list
