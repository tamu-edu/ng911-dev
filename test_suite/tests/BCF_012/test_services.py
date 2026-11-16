from dataclasses import dataclass
from itertools import chain
from typing import Optional

from checks.general.checks import is_data_present
from services.aux_services.rtp_services import (
    is_srtp_packet,
    is_rtp_packet,
    is_srtp_crypto_suite,
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
from tests.BCF_011.constants import NOT_RUN


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
    osp_bcf_sdp_media: Optional[dict] = None
    variation_number: int = 1

    is_osp_bcf_rtp: bool = False
    is_osp_bcf_srtp: bool = False
    is_bcf_esrp_srtp: bool = False
    is_osp_esrp_srtp: bool = False

    is_osp_bcf_aes128: bool = False
    is_osp_bcf_aes256: bool = False
    is_bcf_esrp_aes256: bool = False
    is_osp_esrp_aes256: bool = False


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
    msg_fetcher.add_route("osp_esrp", stimulus_src_ip, out_dst_ip)

    data: dict = {"variation_number": 1}
    bcf_call_id = None

    stimulus_message, stimulus_message_timestamp = msg_fetcher.get_first_sip_invite(
        "osp_bcf", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Detect Variation by crypto negotiated in OSP -> BCF INVITE SDP
    osp_bcf_sdp_media = extract_media_attributes(
        stimulus_message, return_full_attr=True
    )
    data["osp_bcf_sdp_media"] = osp_bcf_sdp_media

    media_crypto = osp_bcf_sdp_media.get("crypto") if osp_bcf_sdp_media else None
    if not media_crypto:
        data["variation_number"] = 1
    elif "AES_CM_128" in media_crypto:
        data["variation_number"] = 2
    elif "AES_256_CM" in media_crypto:
        data["variation_number"] = 3
    else:
        raise WrongConfigurationError(
            f"Stimulus SDP contains an unrecognized crypto suite: '{media_crypto}'. "
            f"Expected no crypto, AES_CM_128_HMAC_SHA1_80, or AES_256_CM_HMAC_SHA1_80. "
        )

    # Get BCF -> ESRP INVITE Call-ID
    bcf_to_esrp_invite_message, bcf_to_esrp_invite_message_ts = (
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

    # RTP between OSP and BCF media exchange
    osp_to_bcf_rtp_message = msg_fetcher.get_first_rtp(
        "osp_bcf", after_timestamp=stimulus_message_timestamp
    )
    bcf_to_osp_rtp_message = msg_fetcher.get_first_rtp(
        "bcf_osp", after_timestamp=stimulus_message_timestamp
    )

    data["is_osp_bcf_rtp"] = (
        is_rtp_packet(osp_to_bcf_rtp_message)
        and not is_srtp_packet(osp_to_bcf_rtp_message)
        and is_rtp_packet(bcf_to_osp_rtp_message)
        and not is_srtp_packet(bcf_to_osp_rtp_message)
    )
    data["is_osp_bcf_srtp"] = is_srtp_packet(osp_to_bcf_rtp_message) and is_srtp_packet(
        bcf_to_osp_rtp_message
    )

    # SRTP between BCF and ESRP media exchange
    bcf_to_esrp_srtp_message = msg_fetcher.get_first_rtp(
        "bcf_esrp", after_timestamp=bcf_to_esrp_invite_message_ts
    )
    esrp_to_bcf_srtp_message = msg_fetcher.get_first_rtp(
        "esrp_bcf", after_timestamp=bcf_to_esrp_invite_message_ts
    )
    data["is_bcf_esrp_srtp"] = is_srtp_packet(
        bcf_to_esrp_srtp_message
    ) and is_srtp_packet(esrp_to_bcf_srtp_message)

    # SRTP between OSP and ESRP media exchange (Variation 3, pass-through)
    osp_to_esrp_srtp_message = msg_fetcher.get_first_rtp(
        "osp_esrp", after_timestamp=bcf_to_esrp_invite_message_ts
    )
    esrp_to_osp_srtp_message = msg_fetcher.get_first_rtp(
        "esrp_osp", after_timestamp=bcf_to_esrp_invite_message_ts
    )
    data["is_osp_esrp_srtp"] = is_srtp_packet(
        osp_to_esrp_srtp_message
    ) and is_srtp_packet(esrp_to_osp_srtp_message)

    # OSP <-> BCF leg: crypto suite negotiated in BCF's SDP answer
    bcf_to_osp_sdp_ok = msg_fetcher.get_first_sip_ok(
        "bcf_osp", after_timestamp=stimulus_message_timestamp, call_id=bcf_call_id
    )
    if bcf_to_osp_sdp_ok and data["variation_number"] in (2, 3):
        bcf_to_osp_media = extract_media_attributes(
            bcf_to_osp_sdp_ok, return_full_attr=True
        )
        if bcf_to_osp_media:
            data["is_osp_bcf_aes128"] = is_srtp_crypto_suite(
                bcf_to_osp_media, "AES_CM_128_HMAC_SHA1_80"
            )
            data["is_osp_bcf_aes256"] = is_srtp_crypto_suite(
                bcf_to_osp_media, "AES_256_CM_HMAC_SHA1_80"
            )
            # end-to-end from OSP to ESRP (BCF doesn't re-encrypt).
            if data["variation_number"] == 3:
                data["is_osp_esrp_aes256"] = data["is_osp_bcf_aes256"]

    # BCF <-> ESRP: crypto suite negotiated in ESRP's SDP answer
    esrp_to_bcf_sdp_ok = msg_fetcher.get_first_sip_ok(
        "esrp_bcf", after_timestamp=bcf_to_esrp_invite_message_ts, call_id=bcf_call_id
    )
    if esrp_to_bcf_sdp_ok:
        esrp_to_bcf_media = extract_media_attributes(
            esrp_to_bcf_sdp_ok, return_full_attr=True
        )
        if esrp_to_bcf_media:
            data["is_bcf_esrp_aes256"] = is_srtp_crypto_suite(
                esrp_to_bcf_media, "AES_256_CM_HMAC_SHA1_80"
            )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validate that media stream between OSP and BCF is RTP (Variation 1 only)",
        "Validate that media stream between OSP and BCF is SRTP (Variation 2 only)",
        "Validate that media stream between BCF and ESRP is SRTP (Variation 1 & 2 only)",
        "Validate that media stream between OSP and ESRP is SRTP (Variation 3 only)",
        "Validate that media encryption between OSP and BCF is 'AES_CM_128_HMAC_SHA1_80' (Variation 2 only)",
        "Validate that media encryption between BCF and ESRP is 'AES_256_CM_HMAC_SHA1_80' (Variation 1 & 2 only)",
        "Validate that media encryption between OSP and ESRP is 'AES_256_CM_HMAC_SHA1_80' (Variation 3 only)",
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

    check_list = []

    if test_data.variation_number == 1:
        check_list.append(
            TestCheck(
                test_name="Validate that media stream between OSP and BCF is RTP (Variation 1 only)",
                test_method=is_data_present,
                precondition=test_data.stimulus_message,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.is_osp_bcf_rtp,
                    "error": "FAILED -> OSP to BCF media is not RTP.",
                },
            ),
        )
    elif test_data.variation_number == 2:
        check_list.extend(
            [
                TestCheck(
                    test_name="Validate that media stream between OSP and BCF is SRTP (Variation 2 only)",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_osp_bcf_srtp,
                        "error": "FAILED -> OSP to BCF media is not SRTP.",
                    },
                ),
                TestCheck(
                    test_name="Validate that media encryption between OSP and BCF is 'AES_CM_128_HMAC_SHA1_80' (Variation 2 only)",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_osp_bcf_aes128,
                        "error": "FAILED -> Media encryption between OSP and BCF is not 'AES_CM_128_HMAC_SHA1_80'",
                    },
                ),
            ]
        )
    elif test_data.variation_number == 3:
        check_list.extend(
            [
                TestCheck(
                    test_name="Validate that media stream between OSP and ESRP is SRTP (Variation 3 only)",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_osp_esrp_srtp,
                        "error": "FAILED -> OSP to ESRP media is not SRTP.",
                    },
                ),
                TestCheck(
                    test_name="Validate that media encryption between OSP and ESRP is 'AES_256_CM_HMAC_SHA1_80' (Variation 3 only)",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_osp_esrp_aes256,
                        "error": "FAILED -> Media encryption between OSP and ESRP is not 'AES_256_CM_HMAC_SHA1_80'",
                    },
                ),
            ]
        )

    if test_data.variation_number in (1, 2):
        check_list.extend(
            [
                TestCheck(
                    test_name="Validate that media stream between BCF and ESRP is SRTP (Variation 1 & 2 only)",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_bcf_esrp_srtp,
                        "error": "FAILED -> BCF to ESRP media is not SRTP.",
                    },
                ),
                TestCheck(
                    test_name="Validate that media encryption between BCF and ESRP is 'AES_256_CM_HMAC_SHA1_80' (Variation 1 & 2 only)",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_bcf_esrp_aes256,
                        "error": "FAILED -> Media encryption between BCF and ESRP is not 'AES_256_CM_HMAC_SHA1_80'",
                    },
                ),
            ]
        )

    return check_list
