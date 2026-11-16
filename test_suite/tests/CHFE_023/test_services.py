from dataclasses import dataclass, field
from typing import Optional

from pyshark.packet.packet import Packet

from checks.general.checks import is_test_data_the_same, is_data_present
from enums import SIPMethodEnum, SIPStatusCodeEnum
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.inner_types.call_id import CallId
from services.messages.sip.inner_types.cseq import CSeq
from services.messages.sip.inner_types.sip_address import SipAddress
from services.messages.sip.inner_types.via import Via
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_023.constants import NOT_RUN, VARIATIONS, ANSWER_CODE_OTHER_INDEX


def get_filter_parameters(
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation_number: int,
) -> tuple[str, str, str, str, str]:
    """
    Retrieve required filtering params to work with the pcap file
    :param lab_config: LabConfig instance
    :param filtering_options: list of MessageFilter
    :param variation_number: variation number, selects the OTHER filter with the response code
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip, expected_answer_code)
    """
    filtering_options = filtering_options or []
    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    others = [m for m in filtering_options if m.message_type == FilterMessageType.OTHER]

    if not (stimulus and output and others):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    answer_index = ANSWER_CODE_OTHER_INDEX[variation_number]
    if len(others) <= answer_index:
        raise WrongConfigurationError(
            f"Response status code for variation {variation_number} is expected "
            f"in OTHER filter #{answer_index + 1}, but only {len(others)} "
            f"OTHER filter(s) found in the Run Config"
        )

    expected_answer_code = others[answer_index].response_status_code or None
    if not expected_answer_code:
        raise WrongConfigurationError(
            f"OTHER filter #{answer_index + 1} of the Run Config does not contain "
            f"required response_status_code value (variation {variation_number})"
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

    if None in (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
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

    # CHFE -> BRIDGE INVITE
    chfe_invite_message: Optional[Packet] = None
    chfe_invite_request_uri: Optional[str] = None
    chfe_invite_top_via: Optional[Via] = None
    chfe_invite_branch: Optional[str] = None
    chfe_invite_from: Optional[SipAddress] = None
    chfe_invite_call_id: Optional[CallId] = None
    chfe_invite_cseq: Optional[CSeq] = None
    chfe_invite_route: Optional[list[SipAddress]] = None

    # BRIDGE -> CHFE final response to the INVITE (200 OK / 486 Busy Here)
    bridge_answer_message: Optional[Packet] = None
    answer_to: Optional[SipAddress] = None
    answer_contact_uri: Optional[str] = None

    # CHFE -> BRIDGE ACK
    ack_message: Optional[Packet] = None
    ack_request_uri: Optional[str] = None
    ack_vias: list[Via] = field(default_factory=list)
    ack_branch: Optional[str] = None
    ack_from: Optional[SipAddress] = None
    ack_to: Optional[SipAddress] = None
    ack_call_id: Optional[CallId] = None
    ack_cseq: Optional[CSeq] = None
    ack_max_forwards: Optional[int] = None
    ack_route: Optional[list[SipAddress]] = None
    ack_top_via: Optional[Via] = None

    # CHFE BYE transactions answered with 200 OK and ACKs sent after them
    bye_ok_count: int = 0
    acks_after_bye_ok: list[str] = field(default_factory=list)


def _collect_acks_after_bye_ok(
    msg_fetcher: PacketFetcher, request_route: str, response_route: str, after_ts
) -> tuple[int, list[str]]:
    """
    returns the number of BYEs and descriptions of CHFE ACKs sent after that 200 OK
    """
    bye_ok_count = 0
    acks = []
    for bye in msg_fetcher.get_sip_byes(request_route, after_timestamp=after_ts):
        call_id = SipMessage.from_packet(bye).call_id
        bye_ok = msg_fetcher.get_first_sip(
            response_route,
            after_timestamp=bye.sniff_timestamp,
            call_id=call_id,
            status_code=SIPStatusCodeEnum.OK.value,
            cseq_method=SIPMethodEnum.BYE,
        )
        if not bye_ok:
            continue
        bye_ok_count += 1
        for ack in msg_fetcher.get_sip_acks(
            request_route, after_timestamp=bye_ok.sniff_timestamp, call_id=call_id
        ):
            acks.append(
                f"{request_route}: ACK frame {ack.number} after 200 OK to BYE (Call-ID {call_id})"
            )
    return bye_ok_count, acks


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation_number: int,
) -> TestData:
    """
    ESRP -> CHFE stimulus INVITE, CHFE -> BRIDGE INVITE, BRIDGE -> CHFE final response,
    CHFE -> BRIDGE ACK plus CHFE BYEs towards BRIDGE and ESRP.
    """
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        expected_answer_code,
    ) = get_filter_parameters(lab_config, filtering_options, variation_number)

    msg_fetcher = PacketFetcher(pcap_service)
    msg_fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("chfe_bridge", out_src_ip, out_dst_ip)

    data: dict = {"expected_answer_code": expected_answer_code}

    # ESRP to CHFE stimulus INVITE
    stimulus_message, stimulus_timestamp = msg_fetcher.get_first_sip_invite(
        "esrp_chfe", return_timestamp=True
    )
    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    # CHFE BYEs towards BRIDGE and ESRP: no ACK may follow their 200 OK
    bridge_bye_ok_count, bridge_acks = _collect_acks_after_bye_ok(
        msg_fetcher, "chfe_bridge", "bridge_chfe", stimulus_timestamp
    )
    esrp_bye_ok_count, esrp_acks = _collect_acks_after_bye_ok(
        msg_fetcher, "chfe_esrp", "esrp_chfe", stimulus_timestamp
    )
    data["bye_ok_count"] = bridge_bye_ok_count + esrp_bye_ok_count
    data["acks_after_bye_ok"] = bridge_acks + esrp_acks

    # CHFE to BRIDGE INVITE
    first_chfe_invite = msg_fetcher.get_first_sip_invite(
        "chfe_bridge", after_timestamp=stimulus_timestamp
    )
    data["chfe_invite_message"] = first_chfe_invite
    if not first_chfe_invite:
        return TestData(**data)

    # BRIDGE to CHFE final response to INVITE with the code expected for the variation.
    bridge_answer_message = msg_fetcher.get_first_sip(
        "bridge_chfe",
        after_timestamp=stimulus_timestamp,
        status_code=expected_answer_code,
        cseq_method=SIPMethodEnum.INVITE,
    )

    data["bridge_answer_message"] = bridge_answer_message
    answer_msg = (
        SipMessage.from_packet(bridge_answer_message) if bridge_answer_message else None
    )
    if not answer_msg:
        return TestData(**data)

    data["answer_to"] = answer_msg.to
    data["answer_contact_uri"] = (
        answer_msg.contact[0].uri if answer_msg.contact else None
    )
    answer_top_via = answer_msg.via[0] if answer_msg.via else None

    # CHFE to BRIDGE INVITE
    chfe_invite_message = msg_fetcher.get_first_sip_invite(
        "chfe_bridge",
        after_timestamp=stimulus_timestamp,
        call_id=answer_msg.call_id,
        branch=answer_top_via.branch if answer_top_via else None,
    )
    data["chfe_invite_message"] = chfe_invite_message
    chfe_invite_msg = (
        SipMessage.from_packet(chfe_invite_message) if chfe_invite_message else None
    )
    if not chfe_invite_msg:
        return TestData(**data)

    invite_top_via = chfe_invite_msg.via[0] if chfe_invite_msg.via else None
    data["chfe_invite_request_uri"] = chfe_invite_msg.request_line.uri
    data["chfe_invite_top_via"] = invite_top_via
    data["chfe_invite_branch"] = invite_top_via.branch if invite_top_via else None
    data["chfe_invite_from"] = chfe_invite_msg.from_
    data["chfe_invite_call_id"] = chfe_invite_msg.call_id
    data["chfe_invite_cseq"] = chfe_invite_msg.cseq
    data["chfe_invite_route"] = chfe_invite_msg.route

    invite_call_id = chfe_invite_msg.call_id

    # CHFE to BRIDGE ACK for the final response
    ack_message = msg_fetcher.get_first_sip_ack(
        "chfe_bridge",
        after_timestamp=bridge_answer_message.sniff_timestamp,
        call_id=invite_call_id,
    )
    data["ack_message"] = ack_message
    ack_msg = SipMessage.from_packet(ack_message) if ack_message else None
    if not ack_msg:
        return TestData(**data)

    data["ack_request_uri"] = ack_msg.request_line.uri
    data["ack_vias"] = ack_msg.via
    data["ack_top_via"] = ack_msg.via[0] if ack_msg.via else None
    data["ack_branch"] = data["ack_top_via"].branch if data["ack_top_via"] else None
    data["ack_from"] = ack_msg.from_
    data["ack_to"] = ack_msg.to
    data["ack_call_id"] = ack_msg.call_id
    data["ack_cseq"] = ack_msg.cseq
    data["ack_max_forwards"] = ack_msg.max_forwards
    data["ack_route"] = ack_msg.route

    return TestData(**data)


def _ack_preconditions(test_data: TestData) -> tuple[dict, dict]:
    """
    Returns (ack_sent_precondition, ack_fields_precondition) kwargs:
    NOT RUN without stimulus or BRIDGE answer, FAILED without CHFE INVITE or ACK.
    """
    if not test_data.stimulus_message:
        error = NOT_RUN
    elif not test_data.chfe_invite_message:
        error = "FAILED -> No CHFE SIP INVITE to BRIDGE found"
    elif not test_data.bridge_answer_message:
        error = f"NOT RUN -> No SIP {test_data.expected_answer_code} response from Test System BRIDGE found"
    else:
        error = None

    ack_sent = {"precondition": error is None, "precondition_error": error or NOT_RUN}

    if error is None and not test_data.ack_message:
        error = "FAILED -> No CHFE SIP ACK to BRIDGE found"
    ack_fields = {"precondition": error is None, "precondition_error": error or NOT_RUN}

    return ack_sent, ack_fields


def get_test_names() -> list:
    return [
        "Verify that CHFE sends SIP ACK to BRIDGE after receiving the final response to SIP INVITE",
        "Verify that CHFE does not send SIP ACK after receiving 200 OK to SIP BYE",
        "Verify that SIP ACK Request-URI is the URI from the Contact of the 200 OK response",
        "Verify that SIP ACK Request-URI is the same as in the corresponding SIP INVITE",
        "Verify that SIP ACK Via contains a new branch different from the SIP INVITE",
        "Verify that SIP ACK contains a single Via header",
        "Verify that SIP ACK Via is equal to the top Via of the corresponding SIP INVITE",
        "Verify that SIP ACK 'To' matches the 'To' of the received response including the tag",
        "Verify that SIP ACK 'From' matches the 'From' of the corresponding SIP INVITE",
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

    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation_number
    )

    ack_sent_precondition, ack_precondition = _ack_preconditions(test_data)
    ack_present_check = {"test_method": is_data_present, **ack_precondition}
    ack_compare_check = {"test_method": is_test_data_the_same, **ack_precondition}

    has_stimulus = bool(test_data.stimulus_message)
    invite_cseq = test_data.chfe_invite_cseq
    ack_cseq = test_data.ack_cseq

    check_list = [
        TestCheck(
            test_name="Verify that CHFE sends SIP ACK to BRIDGE after receiving the final response to SIP INVITE",
            test_method=is_data_present,
            **ack_sent_precondition,
            test_params={
                "test_data": test_data.ack_message,
                "error": f"FAILED -> No CHFE SIP ACK to BRIDGE found after SIP {test_data.expected_answer_code} response",
            },
        ),
        TestCheck(
            test_name="Verify that CHFE does not send SIP ACK after receiving 200 OK to SIP BYE",
            test_method=is_data_present,
            precondition=has_stimulus and test_data.bye_ok_count > 0,
            precondition_error=(
                NOT_RUN
                if not has_stimulus
                else "NOT RUN -> No CHFE SIP BYE answered with 200 OK to BRIDGE or ESRP found"
            ),
            test_params={
                "test_data": not test_data.acks_after_bye_ok,
                "error": (
                    "FAILED -> CHFE sent SIP ACK after receiving 200 OK to SIP BYE:\n"
                    + "\n".join(test_data.acks_after_bye_ok)
                ),
            },
        ),
    ]

    # Variation 2 (486): ACK is part of the INVITE client transaction
    # Variation 1 (200 OK): ACK is a separate transaction
    if variation_number == 2:
        check_list.extend(
            [
                TestCheck(
                    test_name="Verify that SIP ACK Request-URI is the same as in the corresponding SIP INVITE",
                    **ack_compare_check,
                    test_params={
                        "expected_data": test_data.chfe_invite_request_uri,
                        "actual_data": test_data.ack_request_uri,
                    },
                ),
                TestCheck(
                    test_name="Verify that SIP ACK contains a single Via header",
                    **ack_present_check,
                    test_params={
                        "test_data": len(test_data.ack_vias) == 1,
                        "error": f"FAILED -> SIP ACK must contain a single Via header. Actual: {test_data.ack_vias}",
                    },
                ),
                TestCheck(
                    test_name="Verify that SIP ACK Via is equal to the top Via of the corresponding SIP INVITE",
                    **ack_compare_check,
                    test_params={
                        "expected_data": test_data.chfe_invite_top_via,
                        "actual_data": test_data.ack_top_via,
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
                        and test_data.ack_branch != test_data.chfe_invite_branch,
                        "error": (
                            "FAILED -> SIP ACK Via does not contain a branch parameter"
                            if not test_data.ack_branch
                            else "FAILED -> SIP ACK Via branch is the same as in SIP INVITE: "
                            f"{test_data.ack_branch!r}"
                        ),
                    },
                ),
            ]
        )

    check_list.extend(
        [
            TestCheck(
                test_name="Verify that SIP ACK 'To' matches the 'To' of the received response including the tag",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.answer_to,
                    "actual_data": test_data.ack_to,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK 'From' matches the 'From' of the corresponding SIP INVITE",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.chfe_invite_from,
                    "actual_data": test_data.ack_from,
                },
            ),
            TestCheck(
                test_name="Verify that SIP ACK Call-ID matches the Call-ID of the corresponding SIP INVITE",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.chfe_invite_call_id,
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

    # ACK must copy the INVITE Route header, if the INVITE has one
    if test_data.chfe_invite_route:
        check_list.append(
            TestCheck(
                test_name="Verify that SIP ACK contains the exact copy of the SIP INVITE Route header",
                **ack_compare_check,
                test_params={
                    "expected_data": test_data.chfe_invite_route,
                    "actual_data": test_data.ack_route,
                },
            )
        )

    return check_list
