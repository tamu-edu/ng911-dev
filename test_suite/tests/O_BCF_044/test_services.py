from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.aux_services.sdp_services import (
    parse_sdp,
    extract_sdp_from_message_body,
    classify_udp_packets
)

from checks.sip.stimulus_output_by_call_id_check.checks import test_compare_stimulus_and_output_messages
from services.test_services.test_assessment_service import TestCheck

from .constants import (
    OSP,
    O_BCF,
    SBC
)
from .checks import (
    test_udp_exchange_started,
    test_media_ports,
    test_o_bcf_sbc_ports_configuration,
    test_sbc_o_bcf_ports_configuration
)


def get_audio_video_requested_ports(messages):
    for message in messages:
        if hasattr(message, PacketTypeEnum.SIP):
            if hasattr(message.sip, "sdp_media") and hasattr(message.sip, "msg_body"):
                decoded_message_body = parse_sdp(extract_sdp_from_message_body(message))
                try:
                    audio_port = decoded_message_body.get("audio").get("port")
                except AttributeError:
                    audio_port = None

                try:
                    video_port = decoded_message_body.get("video").get("port")
                except AttributeError:
                    video_port = None

                return audio_port, video_port
    return None, None


def get_first_audio_video_first_messages(messages):
    if len(messages) == 0:
        return None, None
    a_packets, video_packets = classify_udp_packets(messages)
    return a_packets[0], video_packets[0]


def get_test_parameters(pcap_service: PcapCaptureService):
    o_bcf_ocsp_invite_messages = pcap_service.get_messages_by_config(
        FilterConfig(
            src_ip=O_BCF,
            dst_ip=OSP,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )
    osp_o_bcf_ok_messages = pcap_service.get_messages_by_config(
        FilterConfig(
            src_ip=OSP,
            dst_ip=O_BCF,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.ACK, ]
        )
    )

    o_bcf_audio_port, o_bcf_video_port = get_audio_video_requested_ports(
        o_bcf_ocsp_invite_messages
    )

    sbc_messages = pcap_service.get_messages_by_config(
            FilterConfig(
                src_ip=OSP,
                dst_ip=O_BCF,
                packet_type=PacketTypeEnum.SIP,
            )
        )

    # TODO add ability to group SIP by CallId
    for message in sbc_messages:
        if hasattr(message, PacketTypeEnum.SIP):
            if hasattr(message.sip, "sdp_media") and hasattr(message.sip, "msg_body"):
                if message.sip.call_id == o_bcf_ocsp_invite_messages[0].sip.call_id:
                    sbc_messages = [message,]
                    break

    sbc_audio_port, sbc_video_port = get_audio_video_requested_ports(sbc_messages)

    o_bcf_sbc_upd_messages = pcap_service.get_messages_by_config(
        FilterConfig(
            src_ip=O_BCF,
            dst_ip=SBC,
            packet_type=PacketTypeEnum.UDP
        )
    )

    o_bcf_sbc_upd_audio_first_message, o_bcf_sbc_upd_video_first_message = get_first_audio_video_first_messages(
                                                                                o_bcf_sbc_upd_messages
                                                                            )
    osp_o_bcf_udp_messages = pcap_service.get_messages_by_config(
        FilterConfig(
            src_ip=SBC,
            dst_ip=O_BCF,
            packet_type=PacketTypeEnum.UDP
        )
    )

    osp_o_bcf_upd_audio_first_message, osp_o_bcf_upd_video_first_message = get_first_audio_video_first_messages(
        osp_o_bcf_udp_messages
    )

    return (
        o_bcf_ocsp_invite_messages,
        osp_o_bcf_ok_messages,
        o_bcf_audio_port,
        o_bcf_video_port,
        sbc_audio_port,
        sbc_video_port,
        o_bcf_sbc_upd_audio_first_message,
        o_bcf_sbc_upd_video_first_message,
        osp_o_bcf_upd_audio_first_message,
        osp_o_bcf_upd_video_first_message
    )


def get_test_list(pcap_service: PcapCaptureService) -> list[TestCheck]:
    (
        o_bcf_ocsp_invite_messages,
        osp_o_bcf_ok_messages,
        o_bcf_audio_port,
        o_bcf_video_port,
        sbc_audio_port,
        sbc_video_port,
        o_bcf_sbc_upd_audio_first_message,
        o_bcf_sbc_upd_video_first_message,
        osp_o_bcf_upd_audio_first_message,
        osp_o_bcf_upd_video_first_message
    ) = get_test_parameters(pcap_service)

    return [
        TestCheck(
            test_name="Stimulus and Output messages comparison",
            test_method=test_compare_stimulus_and_output_messages,
            test_params={
                "stimulus": o_bcf_ocsp_invite_messages[0],
                "output": osp_o_bcf_ok_messages[2]
            }
        ),
        TestCheck(
            test_name="Test to validate Udp exchange started",
            test_method=test_udp_exchange_started,
            test_params={
                "o_bcf_sbc_upd_audio_first_message": o_bcf_sbc_upd_audio_first_message,
                "o_bcf_sbc_upd_video_first_message": o_bcf_sbc_upd_video_first_message,
                "osp_o_bcf_upd_audio_first_message": osp_o_bcf_upd_audio_first_message,
                "osp_o_bcf_upd_video_first_message": osp_o_bcf_upd_video_first_message,
            }
        ),
        TestCheck(
            test_name="Test media ports configuration",
            test_method=test_media_ports,
            test_params={
                "o_bcf_audio_port": o_bcf_audio_port,
                "o_bcf_video_port": o_bcf_video_port,
                "sbc_audio_port": sbc_audio_port,
                "sbc_video_port": sbc_video_port,
            }
        ),
        TestCheck(
            test_name="Test O_BCF -> SBC ports configuration",
            test_method=test_o_bcf_sbc_ports_configuration,
            test_params={
                "o_bcf_sbc_upd_audio_first_message": o_bcf_sbc_upd_audio_first_message,
                "o_bcf_sbc_upd_video_first_message": o_bcf_sbc_upd_video_first_message,
                "o_bcf_audio_port": o_bcf_audio_port,
                "o_bcf_video_port": o_bcf_video_port,
                "sbc_audio_port": sbc_audio_port,
                "sbc_video_port": sbc_video_port,
            }
        ),
        TestCheck(
            test_name="Test SBC -> O_BCF ports configuration",
            test_method=test_sbc_o_bcf_ports_configuration,
            test_params={
                "osp_o_bcf_upd_audio_first_message": osp_o_bcf_upd_audio_first_message,
                "osp_o_bcf_upd_video_first_message": osp_o_bcf_upd_video_first_message,
                "o_bcf_audio_port": o_bcf_audio_port,
                "o_bcf_video_port": o_bcf_video_port,
                "sbc_audio_port": sbc_audio_port,
                "sbc_video_port": sbc_video_port,
            }
        )
    ]
