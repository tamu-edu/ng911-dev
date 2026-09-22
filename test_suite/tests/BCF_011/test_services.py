from dataclasses import dataclass, field
from itertools import chain
from typing import Optional

from checks.general.checks import is_data_present
from services.aux_services.message_services import is_udp_packet
from services.aux_services.rtp_services import (
    is_srtp_packet,
    find_server_hello_with_srtp,
    is_srtp_by_dtls_profile,
)
from services.aux_services.sip_msg_body_services import extract_media_attributes
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from enums import TransportProtocolEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_011.constants import TRANSPORT_PROFILES, NOT_RUN


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
) -> tuple[str, str, str, str, int]:
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

    stimulus_src_iface = next(
        (i for i in interfaces if i.name == stimulus.src_interface), None
    )
    stimulus_dst_port_tls = next(
        (
            p.port
            for p in (stimulus_src_iface.port_mapping if stimulus_src_iface else [])
            if p.protocol == "SIP"
            and p.transport_protocol
            in (TransportProtocolEnum.TLSV1_2, TransportProtocolEnum.TLSV1_3)
        ),
        None,
    )

    stimulus_src_ip = ip_by_interface.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface.get(output.src_interface)
    out_dst_ip = ip_by_interface.get(output.dst_interface)

    if None in (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        stimulus_dst_port_tls,
    ):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses and ports"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        stimulus_dst_port_tls,
    )


@dataclass
class TestData:
    stimulus_message: Optional[object] = None
    is_osp_bcf_srtp_media: bool = False
    is_osp_bcf_rtp_over_udp: bool = False
    is_bcf_esrp_srtp_media: bool = False
    is_bcf_esrp_rtp_over_udp: bool = False
    bcf_esrp_invite_sdp_media: dict = field(default_factory=dict)
    esrp_udp_port: Optional[int] = None
    bcf_udp_port: Optional[int] = None
    esrp_bcf_response_sdp_media: dict = field(default_factory=dict)
    is_srtp_with_aes256: bool = False
    variation_number: int = 2


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
        stimulus_dst_port_tls,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    msg_fetcher = PacketFetcher(pcap_service)
    msg_fetcher.add_route("osp_bcf", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("bcf_esrp", out_src_ip, out_dst_ip)

    data: dict = {}
    bcf_call_id = None

    # TLS stimulus
    stimulus_message, stimulus_message_timestamp = msg_fetcher.get_first(
        "osp_bcf", dst_port=stimulus_dst_port_tls, return_timestamp=True
    )

    variation_number = 2

    if stimulus_message:
        variation_number = 1
    else:
        # Plain SIP INVITE stimulus — media type determines the variation
        stimulus_message, stimulus_message_timestamp = msg_fetcher.get_first_sip_invite(
            "osp_bcf", return_timestamp=True
        )
        if stimulus_message:
            stimulus_invite_sdp = extract_media_attributes(
                stimulus_message, return_full_attr=True
            )
            media_type = (
                stimulus_invite_sdp.get("media_type") if stimulus_invite_sdp else None
            )
            if media_type == "audio":
                variation_number = 2
            elif media_type == "video":
                variation_number = 3
            elif media_type == "text":
                variation_number = 4

    data["stimulus_message"] = stimulus_message
    data["variation_number"] = variation_number

    if not stimulus_message:
        return TestData(**data)

    # BCF -> ESRP INVITE
    bcf_to_esrp_invite_message, bcf_to_esrp_invite_ts = (
        msg_fetcher.get_first_sip_invite(
            "bcf_esrp",
            after_timestamp=stimulus_message_timestamp,
            return_timestamp=True,
        )
    )

    # Get Call-ID from BCF Invite for SIP filtering
    if bcf_to_esrp_invite_message:
        bcf_sip_inv_msg = SipMessage.from_packet(bcf_to_esrp_invite_message)
        bcf_call_id = bcf_sip_inv_msg.call_id if bcf_sip_inv_msg else None

    # ESRP -> BCF 200 OK
    esrp_to_bcf_response_200 = msg_fetcher.get_first_sip_ok(
        "esrp_bcf", after_timestamp=bcf_to_esrp_invite_ts, call_id=bcf_call_id
    )

    dtls_bcf_esrp_dtls_messages = msg_fetcher.get_messages(
        "bcf_esrp", packet_type=TransportProtocolEnum.DTLS
    )
    dtls_esrp_bcf_dtls_messages = msg_fetcher.get_messages(
        "esrp_bcf", packet_type=TransportProtocolEnum.DTLS
    )

    # BCF to ESRP SDP data
    if bcf_to_esrp_invite_message:
        bcf_sdp_media = extract_media_attributes(
            bcf_to_esrp_invite_message, return_full_attr=True
        )
        data["bcf_esrp_invite_sdp_media"] = bcf_sdp_media if bcf_sdp_media else {}

    # ESRP to BCF response SDP data
    if esrp_to_bcf_response_200:
        esrp_sdp_media = extract_media_attributes(
            esrp_to_bcf_response_200, return_full_attr=True
        )
        data["esrp_bcf_response_sdp_media"] = esrp_sdp_media if esrp_sdp_media else {}

    # Get first RTP messages between OSP and BCF
    osp_to_bcf_rtp_message = msg_fetcher.get_first(
        "osp_bcf", packet_type=TransportProtocolEnum.RTP
    )
    bcf_to_osp_rtp_message = msg_fetcher.get_first(
        "bcf_osp", packet_type=TransportProtocolEnum.RTP
    )

    # OSP to BCF SRTP/UDP
    if osp_to_bcf_rtp_message and bcf_to_osp_rtp_message:
        data["is_osp_bcf_srtp_media"] = bool(
            is_srtp_packet(osp_to_bcf_rtp_message)
            and is_srtp_packet(bcf_to_osp_rtp_message)
        )
        data["is_osp_bcf_rtp_over_udp"] = bool(
            is_udp_packet(osp_to_bcf_rtp_message)
            and is_udp_packet(bcf_to_osp_rtp_message)
        )

    # Get first RTP messages between BCF and ESRP
    bcf_to_esrp_srtp_message = msg_fetcher.get_first(
        "bcf_esrp", packet_type=TransportProtocolEnum.RTP
    )
    esrp_to_bcf_srtp_message = msg_fetcher.get_first(
        "esrp_bcf", packet_type=TransportProtocolEnum.RTP
    )

    # BCF to ESRP SRTP/UDP
    if bcf_to_esrp_srtp_message and esrp_to_bcf_srtp_message:
        data["is_bcf_esrp_srtp_media"] = bool(
            is_srtp_packet(bcf_to_esrp_srtp_message)
            and is_srtp_packet(esrp_to_bcf_srtp_message)
        )
        data["is_bcf_esrp_rtp_over_udp"] = bool(
            is_udp_packet(bcf_to_esrp_srtp_message)
            and is_udp_packet(esrp_to_bcf_srtp_message)
        )

        if hasattr(bcf_to_esrp_srtp_message, "udp") and hasattr(
            esrp_to_bcf_srtp_message, "udp"
        ):
            data["bcf_udp_port"] = bcf_to_esrp_srtp_message.udp.srcport
            data["esrp_udp_port"] = esrp_to_bcf_srtp_message.udp.srcport

    # Search ServerHello packet with Protection Profile
    server_hello_packet = None
    if dtls_bcf_esrp_dtls_messages and dtls_esrp_bcf_dtls_messages:
        server_hello_packet = find_server_hello_with_srtp(
            dtls_bcf_esrp_dtls_messages + dtls_esrp_bcf_dtls_messages
        )

    if server_hello_packet:
        data["is_srtp_with_aes256"] = is_srtp_by_dtls_profile(
            server_hello_packet, "AEAD_AES_256_GCM"
        )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validate if media stream between OSP and BCF is over UDP",
        "Validate if media stream between BCF and ESRP is over UDP",
        "Validate SRTP media between OSP and BCF",
        "Validate SRTP media between BCF and ESRP",
        "Validate BCF INVITE SDP contains 'a=setup'",
        "Validate BCF INVITE SDP contains 'a=fingerprint'",
        "Validate BCF INVITE use UDP/TLS/RTP/SAVP or UDP/TLS/RTP/SAVPF Transport Profile",
        "Validate SDP and UDP/RTP packet port matching",
        "Validate BCF and ESRP negotiated media stream uses SRTP with AES-256 encryption",
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
            test_name="Validate SRTP media between BCF and ESRP",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_bcf_esrp_srtp_media,
                "error": "FAILED -> No BCF to ESRP SRTP media found.",
            },
        ),
        TestCheck(
            test_name="Validate if media stream between OSP and BCF is over UDP",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_osp_bcf_rtp_over_udp,
                "error": "FAILED -> Media stream between OSP and BCF is not over UDP.",
            },
        ),
        TestCheck(
            test_name="Validate if media stream between BCF and ESRP is over UDP",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_bcf_esrp_rtp_over_udp,
                "error": "FAILED -> Media stream between BCF and ESRP is not over UDP.",
            },
        ),
        TestCheck(
            test_name="Validate BCF INVITE SDP contains 'a=setup'",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.bcf_esrp_invite_sdp_media.get("setup"),
                "error": "FAILED -> BCF INVITE SDP doesn't contain 'a=setup'",
            },
        ),
        TestCheck(
            test_name="Validate BCF INVITE SDP contains 'a=fingerprint'",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.bcf_esrp_invite_sdp_media.get("fingerprint"),
                "error": "FAILED -> BCF INVITE SDP doesnt contain 'a=fingerprint'",
            },
        ),
        TestCheck(
            test_name="Validate BCF INVITE use UDP/TLS/RTP/SAVP or UDP/TLS/RTP/SAVPF Transport Profile",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.bcf_esrp_invite_sdp_media.get("media_transport")
                in TRANSPORT_PROFILES,
                "error": "FAILED -> UDP/TLS/RTP/SAVP or UDP/TLS/RTP/SAVPF Transport Profile not found",
            },
        ),
        TestCheck(
            test_name="Validate SDP and UDP/RTP packet port matching",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": all(
                    [
                        test_data.bcf_esrp_invite_sdp_media.get("media_port")
                        == test_data.bcf_udp_port,
                        test_data.esrp_bcf_response_sdp_media.get("media_port")
                        == test_data.esrp_udp_port,
                        test_data.bcf_udp_port is not None,
                        test_data.esrp_udp_port is not None,
                    ]
                ),
                "error": "FAILED -> SDP media port and UDP/RTP packet media port mismatch",
            },
        ),
        TestCheck(
            test_name="Validate BCF and ESRP negotiated media stream uses SRTP with AES-256 encryption",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_srtp_with_aes256,
                "error": "FAILED -> AES-256 encryption was not found in Server Hello between BCF and ESRP",
            },
        ),
    ]

    if test_data.variation_number == 1:
        check_list.append(
            TestCheck(
                test_name="Validate SRTP media between OSP and BCF",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.is_osp_bcf_srtp_media,
                    "error": "FAILED -> No OSP to BCF SRTP media found.",
                },
            ),
        )

    return check_list
