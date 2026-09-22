from dataclasses import dataclass
from itertools import chain
from typing import Optional

from checks.general.checks import (
    is_data_present,
    verify_str_test_data_the_same_with_normalization_fallback,
)
from checks.sip.message_body_checks.mime_checks.mime_validator import (
    verify_mime_structure,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.test_services.test_assessment_service import TestCheck
from tests.BRIDGE_005.constants import NOT_RUN


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
    invite_bridge_chfe_message: Optional[object] = None
    stimulus_body: Optional[str] = None
    bridge_invite_body: Optional[str] = None
    bridge_invite_content_type: Optional[str] = None


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
    msg_fetcher.add_route("esrp_bridge", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("bridge_chfe", out_src_ip, out_dst_ip)

    data: dict = {}
    stimulus_call_id = None

    # Get stimulus and TimeStamp
    stimulus_message, stimulus_message_timestamp = msg_fetcher.get_first_sip_invite(
        "esrp_bridge", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get Stimulus Test Data
    stimulus_sip_msg = SipMessage.from_packet(stimulus_message)
    if stimulus_sip_msg:
        stimulus_call_id = stimulus_sip_msg.call_id if stimulus_sip_msg else None
        data["stimulus_body"] = stimulus_sip_msg.body if stimulus_sip_msg else None

    # Get BRIDGE -> CHFE message
    bridge_chfe_message = msg_fetcher.get_first_sip_invite(
        "bridge_chfe",
        after_timestamp=stimulus_message_timestamp,
        call_id=stimulus_call_id,
    )
    data["invite_bridge_chfe_message"] = bridge_chfe_message

    # Get BRIDGE -> CHFE message Test Data
    if bridge_chfe_message:
        bridge_invite_msg = SipMessage.from_packet(bridge_chfe_message)
        data["bridge_invite_body"] = (
            bridge_invite_msg.body if bridge_invite_msg else None
        )
        data["bridge_invite_content_type"] = (
            bridge_invite_msg.content_type if bridge_invite_msg else None
        )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validation that the INVITE was forwarded from the BRIDGE to the CHFE",
        "Validation that the MIME BODY structure of the forwarded INVITE at the BRIDGE interface semantically equivalent to the stimulus",
        "Validation that Content-Type headers correctly reflect the boundary strings and multipart subtypes",
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
            test_name="Validation that the INVITE was forwarded from the BRIDGE to the CHFE",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.invite_bridge_chfe_message,
                "error": "FAILED -> SIP INVITE forwarded from BRIDGE to CHFE not found",
            },
        ),
        TestCheck(
            test_name="Validation that the MIME BODY structure of the forwarded INVITE at the BRIDGE interface semantically equivalent to the stimulus",
            test_method=verify_str_test_data_the_same_with_normalization_fallback,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "expected_data": test_data.stimulus_body,
                "actual_data": test_data.bridge_invite_body,
                "error": "MIME structure of the forwarded INVITE at the BRIDGE interface and stimulus are not the same",
            },
        ),
        TestCheck(
            test_name="Validation that Content-Type headers correctly reflect the boundary strings and multipart subtypes",
            test_method=verify_mime_structure,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "content_type_raw": test_data.bridge_invite_content_type,
                "body": test_data.bridge_invite_body,
            },
        ),
    ]

    return check_list
