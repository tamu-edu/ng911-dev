from dataclasses import dataclass
from itertools import chain
from typing import Optional

from checks.general.checks import is_test_data_the_same
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.test_services.test_assessment_service import TestCheck
from tests.BRIDGE_006.constants import NOT_RUN


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
) -> tuple[str, str, str, str]:
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip, stimulus_dst_port_tls)
    """
    messages_by_type = {m.message_type: m for m in (filtering_options or [])}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)

    if not (stimulus and output):
        raise WrongConfigurationError(
            "Stimulus and output messages must be provided in filtering options"
        )

    interfaces = list(chain.from_iterable(e.interfaces for e in lab_config.entities))
    ip_by_interface = {iface.name: iface.ip for iface in interfaces}

    stimulus_src_ip = ip_by_interface.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface.get(output.src_interface)
    out_dst_ip = ip_by_interface.get(output.dst_interface)

    if None in (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
    ):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses and ports"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
    )


@dataclass
class TestData:
    stimulus_message: Optional[object] = None
    refer_uri: Optional[str] = None
    refer_service_urn: Optional[str] = None
    out_invite_request_uri: Optional[str] = None
    out_invite_route_uri: Optional[str] = None
    out_invite_referred_by: Optional[str] = None
    refer_referred_by: Optional[str] = None


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
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    msg_fetcher = PacketFetcher(pcap_service)
    msg_fetcher.add_route("chfe_bridge", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("bridge_chfe_2", out_src_ip, out_dst_ip)

    data: dict = {}
    chfe_brg_invite_call_id = None
    chfe_brg_invite_message_timestamp = 0
    out_invite_route_raw = None

    # Get stimulus and TimeStamp
    stimulus_message, stimulus_message_timestamp = msg_fetcher.get_first_sip_invite(
        "chfe_bridge", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    stimulus_sip_msg = SipMessage.from_packet(stimulus_message)
    stimulus_call_id = stimulus_sip_msg.call_id if stimulus_sip_msg else None

    # Get first CHFE ACK and TimeStamp for CHFE->BRIDGE invite filtering
    first_chfe_brg_ack_message, first_chfe_brg_ack_message_timestamp = (
        msg_fetcher.get_first_sip_ack(
            "chfe_bridge",
            return_timestamp=True,
            after_timestamp=stimulus_message_timestamp,
            call_id=stimulus_call_id,
        )
    )

    # Get CHFE->BRIDGE INVITE after stimulus and extract Call-ID for subsequent use in filtering
    if first_chfe_brg_ack_message and first_chfe_brg_ack_message_timestamp:
        chfe_brg_invite_message, chfe_brg_invite_message_timestamp = (
            msg_fetcher.get_first_sip_invite(
                "chfe_bridge",
                return_timestamp=True,
                after_timestamp=first_chfe_brg_ack_message_timestamp,
            )
        )

        if chfe_brg_invite_message:
            chfe_brg_invite_sip_msg = SipMessage.from_packet(chfe_brg_invite_message)
            chfe_brg_invite_call_id = (
                chfe_brg_invite_sip_msg.call_id if chfe_brg_invite_sip_msg else None
            )

    # Get REFER message and extract fields data
    refer_message, refer_message_timestamp = msg_fetcher.get_first_sip_refer(
        "chfe_bridge",
        return_timestamp=True,
        after_timestamp=chfe_brg_invite_message_timestamp,
        call_id=chfe_brg_invite_call_id,
    )

    if refer_message:
        refer_sip_msg = SipMessage.from_packet(refer_message)

        if refer_sip_msg.refer_to:
            data["refer_service_urn"] = refer_sip_msg.refer_to[0].service_urn
            data["refer_uri"] = refer_sip_msg.refer_to[0].uri

        data["refer_referred_by"] = (
            refer_sip_msg.referred_by.uri if refer_sip_msg.referred_by else None
        )

    # Get Outgoing INVITE to CHFE-2 and extract fields data
    out_invite_message = msg_fetcher.get_first_sip_invite(
        "bridge_chfe_2", after_timestamp=refer_message_timestamp
    )

    if out_invite_message:
        out_invite_msg = SipMessage.from_packet(out_invite_message)
        if out_invite_msg:
            data["out_invite_request_uri"] = (
                out_invite_msg.request_line.uri if out_invite_msg.request_line else None
            )
            data["out_invite_route_uri"] = (
                out_invite_msg.route[0].uri if out_invite_msg.route else None
            )
            data["out_invite_referred_by"] = (
                out_invite_msg.referred_by.uri if out_invite_msg.referred_by else None
            )
            out_invite_route_raw = (
                out_invite_msg.route[0] if out_invite_msg.route else None
            )

    if out_invite_route_raw and ";lr" not in out_invite_route_raw:
        print(
            "⚠️ WARNING: Optional 'lr' parameter was not included in the Route URI ⚠️"
        )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validate if outgoing SIP INVITE has the Request-URI set to the same service URN supplied in the 'serviceurn' parameter of the received SIP REFER",
        "Validate if 'Route' of outgoing SIP INVITE contains the same SIP URI as the 'Refer-To' header of the received SIP REFER",
        "Validate if 'Referred-By' of outgoing SIP INVITE contains the same URI as the 'Referred-By' header of the received SIP REFER",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation
    )

    check_list = [
        TestCheck(
            test_name="Validate if outgoing SIP INVITE has the Request-URI set to the same service URN supplied in the 'serviceurn' parameter of the received SIP REFER",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.refer_service_urn,
                "actual_data": test_data.out_invite_request_uri,
                "error": "Outgoing SIP INVITE Request-URI and REFER 'serviceurn' parameter are not the same",
            },
        ),
        TestCheck(
            test_name="Validate if 'Route' of outgoing SIP INVITE contains the same SIP URI as the 'Refer-To' header of the received SIP REFER",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.refer_uri,
                "actual_data": test_data.out_invite_route_uri,
                "error": "'Route' of outgoing SIP INVITE and 'Refer-To' of the SIP REFER are not the same",
            },
        ),
        TestCheck(
            test_name="Validate if 'Referred-By' of outgoing SIP INVITE contains the same URI as the 'Referred-By' header of the received SIP REFER",
            test_method=is_test_data_the_same,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.refer_referred_by,
                "actual_data": test_data.out_invite_referred_by,
                "error": "'Referred-By' of outgoing SIP INVITE and REFER 'Referred-By' URI are not the same",
            },
        ),
    ]

    return check_list
