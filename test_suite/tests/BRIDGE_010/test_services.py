from dataclasses import dataclass
from typing import Optional

from pyshark.packet.packet import Packet

from checks.general.checks import is_test_data_the_same, is_data_present
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.inner_types.call_id import CallId
from services.messages.sip.inner_types.cseq import CSeq
from services.messages.sip.inner_types.sip_address import SipAddress
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.BRIDGE_010.constants import NOT_RUN, VARIATIONS


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
) -> tuple[str, str, str, str, str, str]:
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip, out_body_contains, expected_answer_code)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    other = messages_by_type.get(FilterMessageType.OTHER)

    if not (stimulus and output):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    ip_by_interface = {
        interface.name: interface.ip
        for entity in lab_config.entities
        for interface in entity.interfaces
    }

    stimulus_src_ip = ip_by_interface.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface.get(output.src_interface)
    out_dst_ip = ip_by_interface.get(output.dst_interface)

    expected_answer_code = other.response_status_code or None
    out_body_contains = output.body_contains or None

    if not expected_answer_code:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "response_status_code value"
        )

    if None in (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        out_body_contains,
        expected_answer_code,
    )


def _get_variation_number(variation: RunVariation) -> int:
    variation_number = VARIATIONS.get(variation.name)
    if variation_number is None:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{VARIATIONS}'"
        )
    return variation_number


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    expected_answer_code: Optional[str] = None

    # BRIDGE -> peer INVITE
    brg_invite_message: Optional[Packet] = None
    brg_invite_request_uri: Optional[str] = None
    brg_invite_branch: Optional[str] = None
    brg_invite_from: Optional[str] = None
    brg_invite_call_id: Optional[CallId] = None
    brg_invite_cseq: Optional[CSeq] = None
    brg_invite_route: Optional[list[str]] = None

    # Peer -> BRIDGE final response to the INVITE
    peer_answer_message: Optional[Packet] = None
    answer_to: Optional[str] = None
    answer_contact_uri: Optional[str] = None

    # BRIDGE -> peer ACK
    ack_message: Optional[Packet] = None
    ack_request_uri: Optional[str] = None
    ack_branch: Optional[str] = None
    ack_from: Optional[str] = None
    ack_to: Optional[str] = None
    ack_call_id: Optional[CallId] = None
    ack_cseq: Optional[CSeq] = None
    ack_max_forwards: Optional[int] = None
    ack_route: Optional[list[str]] = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
) -> TestData:
    """
    caller -> BRIDGE stimulus, BRIDGE -> peer INVITE, peer -> BRIDGE final response, BRIDGE -> peer ACK.
    Variations 1, 2: caller = CHFE, peer = CHFE-2; Variation 3: caller = CHFE-2, peer = CHFE.
    """
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        out_body_contains,
        expected_answer_code,
    ) = get_filter_parameters(lab_config, filtering_options)

    msg_fetcher = PacketFetcher(pcap_service)
    msg_fetcher.add_route("caller_bridge", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("bridge_peer", out_src_ip, out_dst_ip)

    data: dict = {"expected_answer_code": expected_answer_code}

    # Caller to BRIDGE stimulus INVITE
    body_filter = {"body_part": out_body_contains} if out_body_contains else {}
    stimulus_message, stimulus_timestamp = msg_fetcher.get_first_sip_invite(
        "caller_bridge", return_timestamp=True, **body_filter
    )
    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # BRIDGE to peer INVITE (re-INVITE in Variation 3)
    brg_invite_message, brg_invite_timestamp = msg_fetcher.get_first_sip_invite(
        "bridge_peer", return_timestamp=True, after_timestamp=stimulus_timestamp
    )

    data["brg_invite_message"] = brg_invite_message
    brg_invite_msg = (
        SipMessage.from_packet(brg_invite_message) if brg_invite_message else None
    )
    if not brg_invite_msg:
        return TestData(**data)

    data["brg_invite_request_uri"] = brg_invite_msg.request_line.uri
    data["brg_invite_branch"] = brg_invite_msg.via[0].branch
    data["brg_invite_from"] = brg_invite_msg.from_.raw if brg_invite_msg.from_ else None
    data["brg_invite_call_id"] = brg_invite_msg.call_id
    data["brg_invite_cseq"] = brg_invite_msg.cseq
    data["brg_invite_route"] = (
        [route.raw for route in brg_invite_msg.route] if brg_invite_msg.route else None
    )

    # Call-ID as a plain string
    invite_call_id_raw = brg_invite_msg.call_id.raw

    # Peer to BRIDGE response to the INVITE with the code expected for the variation
    peer_answer_message, peer_answer_timestamp = msg_fetcher.get_first_sip(
        "peer_bridge",
        return_timestamp=True,
        after_timestamp=brg_invite_timestamp,
        call_id=invite_call_id_raw,
        status_code=expected_answer_code,
    )

    data["peer_answer_message"] = peer_answer_message
    answer_msg = (
        SipMessage.from_packet(peer_answer_message) if peer_answer_message else None
    )
    if not answer_msg:
        return TestData(**data)

    data["answer_to"] = answer_msg.to.raw if answer_msg.to else None
    data["answer_contact_uri"] = (
        answer_msg.contact[0].uri if answer_msg.contact else None
    )

    # BRIDGE to peer ACK for the final response
    ack_message = msg_fetcher.get_first_sip_ack(
        "bridge_peer", after_timestamp=peer_answer_timestamp, call_id=invite_call_id_raw
    )
    data["ack_message"] = ack_message
    ack_msg = SipMessage.from_packet(ack_message) if ack_message else None
    if not ack_msg:
        return TestData(**data)

    data["ack_request_uri"] = ack_msg.request_line.uri
    data["ack_branch"] = ack_msg.via[0].branch
    data["ack_from"] = ack_msg.from_.raw if ack_msg.from_ else None
    data["ack_to"] = ack_msg.to.raw if ack_msg.to else None
    data["ack_call_id"] = ack_msg.call_id
    data["ack_cseq"] = ack_msg.cseq
    data["ack_max_forwards"] = ack_msg.max_forwards
    ack_route_headers: list[SipAddress] = ack_msg.route or []
    data["ack_route"] = (
        [route.raw for route in ack_route_headers] if ack_msg.route else None
    )

    return TestData(**data)


def _ack_preconditions(
    test_data: TestData, expected_answer_code: str
) -> tuple[dict, dict]:
    """
    Returns (ack_sent_precondition, ack_fields_precondition) kwargs:
    NOT RUN without stimulus or Test System answer, FAILED without BRIDGE INVITE or ACK.
    """
    if not test_data.stimulus_message:
        error = NOT_RUN
    elif not test_data.brg_invite_message:
        error = "FAILED -> No BRIDGE SIP INVITE found"
    elif not test_data.peer_answer_message:
        error = (
            f"NOT RUN -> No SIP {expected_answer_code} response from Test System found"
        )
    else:
        error = None

    ack_sent = {"precondition": error is None, "precondition_error": error or NOT_RUN}

    if error is None and not test_data.ack_message:
        error = "FAILED -> No BRIDGE SIP ACK found"
    ack_fields = {"precondition": error is None, "precondition_error": error or NOT_RUN}

    return ack_sent, ack_fields


def get_test_names() -> list:
    return [
        "Verify that BRIDGE sends SIP ACK after receiving the final response to SIP INVITE",
        "Verify that SIP ACK Request-URI is the URI from the Contact of the 200 OK response",
        "Verify that SIP ACK Request-URI is the same as in the corresponding SIP INVITE",
        "Verify that SIP ACK Via contains a new branch different from the SIP INVITE",
        "Verify that SIP ACK Via contains the same branch as the SIP INVITE",
        "Verify that SIP ACK 'From' matches the 'From' of the corresponding SIP INVITE",
        "Verify that SIP ACK 'To' matches the 'To' of the received response including the tag",
        "Verify that SIP ACK Call-ID matches the Call-ID of the corresponding SIP INVITE",
        "Verify that SIP ACK CSeq method is ACK",
        "Verify that SIP ACK CSeq number matches the CSeq number of the corresponding SIP INVITE",
        "Verify that SIP ACK contains Max-Forwards header",
        "Verify that SIP ACK contains the exact copy of the SIP INVITE Route header",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    variation_number = _get_variation_number(variation)
    test_data = get_test_parameters(pcap_service, lab_config, filtering_options)

    expected_answer_code = test_data.expected_answer_code

    ack_sent_precondition, ack_precondition = _ack_preconditions(
        test_data, expected_answer_code
    )
    ack_present_check = {"test_method": is_data_present, **ack_precondition}
    ack_compare_check = {"test_method": is_test_data_the_same, **ack_precondition}

    invite_cseq = test_data.brg_invite_cseq
    ack_cseq = test_data.ack_cseq

    check_list = [
        TestCheck(
            test_name="Verify that BRIDGE sends SIP ACK after receiving the final response to SIP INVITE",
            test_method=is_data_present,
            **ack_sent_precondition,
            test_params={
                "test_data": test_data.ack_message,
                "error": f"FAILED -> No BRIDGE SIP ACK found after SIP {expected_answer_code} response",
            },
        ),
    ]

    if variation_number == 2:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify that SIP ACK Request-URI is the same as in the corresponding SIP INVITE",
                    **ack_compare_check,
                    test_params={
                        "expected_data": test_data.brg_invite_request_uri,
                        "actual_data": test_data.ack_request_uri,
                    },
                ),
                TestCheck(
                    test_name="Verify that SIP ACK Via contains the same branch as the SIP INVITE",
                    **ack_compare_check,
                    test_params={
                        "expected_data": test_data.brg_invite_branch,
                        "actual_data": test_data.ack_branch,
                    },
                ),
            ]
        )
    else:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify that SIP ACK Request-URI is the URI from the Contact of the 200 OK response",
                    **ack_compare_check,
                    test_params={
                        "expected_data": test_data.answer_contact_uri,
                        "actual_data": test_data.ack_request_uri,
                    },
                ),
                TestCheck(
                    test_name="Verify that SIP ACK Via contains a new branch different from the SIP INVITE",
                    **ack_present_check,
                    test_params={
                        "test_data": bool(test_data.ack_branch)
                        and test_data.ack_branch != test_data.brg_invite_branch,
                        "error": (
                            "FAILED -> SIP ACK Via branch is missing or the same as in SIP INVITE. "
                            f"ACK: {test_data.ack_branch!r}, INVITE: {test_data.brg_invite_branch!r}"
                        ),
                    },
                ),
            ]
        )

    check_list.extend(
        [
            TestCheck(
                test_name="Verify that SIP ACK 'From' matches the 'From' of the corresponding SIP INVITE",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.brg_invite_from,
                    "actual_data": test_data.ack_from,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK 'To' matches the 'To' of the received response including the tag",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.answer_to,
                    "actual_data": test_data.ack_to,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK Call-ID matches the Call-ID of the corresponding SIP INVITE",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.brg_invite_call_id,
                    "actual_data": test_data.ack_call_id,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK CSeq method is ACK",
                **ack_compare_check,
                test_params={
                    "expected_data": "ACK",
                    "actual_data": ack_cseq.method if ack_cseq else None,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK CSeq number matches the CSeq number of the corresponding SIP INVITE",
                **ack_compare_check,
                test_params={
                    "expected_data": invite_cseq.sequence if invite_cseq else None,
                    "actual_data": ack_cseq.sequence if ack_cseq else None,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK contains Max-Forwards header",
                **ack_present_check,
                test_params={
                    "test_data": test_data.ack_max_forwards is not None,
                    "error": "FAILED -> SIP ACK does not contain Max-Forwards header",
                },
            ),
        ]
    )

    # (optional) Variation 2: ACK must copy the INVITE Route header, if the INVITE has one
    if variation_number == 2 and test_data.brg_invite_route:
        check_list.append(
            TestCheck(
                test_name="Verify that SIP ACK contains the exact copy of the SIP INVITE Route header",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.brg_invite_route,
                    "actual_data": test_data.ack_route,
                },
            )
        )

    return check_list
