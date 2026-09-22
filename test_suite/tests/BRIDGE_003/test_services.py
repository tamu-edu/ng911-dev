from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.aux_services.rtp_services import (
    get_rtp_attribute_list_attr,
    get_ssrc_value,
    get_text_from_rtp_messages,
)
from services.aux_services.sip_msg_body_services import (
    extract_media_attributes,
    clean_up_string,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum, TransportProtocolEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BRIDGE_003.checks import validate_bridge_multi_party_session


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip), strings
    """
    interfaces_dict = {}
    expected_resp_code_stimulus = None
    osp_expected_response_code = None
    chfe_message = None
    osp_message = None

    for entity in lab_config.entities:
        for interface in entity.interfaces:
            port_dict = {}
            for pm in interface.port_mapping:
                port_dict[pm.name] = {
                    "protocol": pm.protocol,
                    "port": pm.port,
                    "transport_protocol": pm.transport_protocol,
                }

            interfaces_dict[interface.name] = {
                "ip": interface.ip,
                "ip_list": [],
                "port_mapping": port_dict,
            }

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            expected_resp_code_stimulus = message.response_status_code
        elif message.message_type == FilterMessageType.OTHER and (
            hasattr(message, "response_status_code")
            and message.response_status_code
            and not osp_expected_response_code
        ):
            osp_expected_response_code = message.response_status_code
        elif (
            message.src_interface == "IF_OSP_BCF"
            and message.dst_interface == "IF_BCF_OSP"
            and message.body_contains
        ):
            osp_message = message.body_contains
        elif (
            message.src_interface == "IF_CHFE_BRIDGE"
            and message.dst_interface == "IF_BRIDGE_CHFE"
            and message.body_contains
        ):
            chfe_message = message.body_contains
    if (
        not interfaces_dict
        and not expected_resp_code_stimulus
        and not osp_expected_response_code
        and not chfe_message
        and not osp_message
    ):
        raise WrongConfigurationError(
            "Lab Config file error - cannot extract interface data"
        )
    else:
        return (
            interfaces_dict,
            expected_resp_code_stimulus,
            osp_expected_response_code,
            chfe_message,
            osp_message,
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
):
    (
        interfaces_dict,
        expected_resp_code_stimulus,
        osp_expected_response_code,
        chfe_message,
        osp_message,
    ) = get_filter_parameters(lab_config, filtering_options)

    che_to_bridge_invite_sent = False
    che_to_bridge_communication_successful = False
    bridge_to_bcf_invite_successful = False
    bridge_to_chfe_message_text = None
    bcf_to_osp_message_text = None
    bcf_ssrc = set()
    bcf_to_osp_ssrc = set()
    bridge_to_chfe_ssrc = set()
    bridge_ssrc = set()
    chfe_ssrc = set()
    bridge_to_chfe_csrc = set()
    bridge_to_bcf_csrc = set()
    bcf_to_osp_csrc = set()
    bridge_to_chfe_rtpmap = None
    bridge_to_chfe_mixer = False
    bridge_to_bcf_rtpmap = None
    bridge_to_bcf_mixer = False
    chfe_to_bridge_branch = None
    sdp_media_data = None
    bridge_to_chfe_invite_response = False

    # GET CHFE to BRIDGE SIP INVITE
    che_to_bridge_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
            dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )
    if hasattr(che_to_bridge_invite_message, "sip"):
        chfe_to_bridge_branch = getattr(
            che_to_bridge_invite_message.sip, "via_branch", ""
        )

    if che_to_bridge_invite_message:
        che_to_bridge_invite_sent = True
        bridge_responses_to_chfe = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=float(che_to_bridge_invite_message.sniff_timestamp),
            ),
        )
        for message in bridge_responses_to_chfe:
            if (
                hasattr(message, "sip")
                and hasattr(message.sip, "via_branch")
                and getattr(message.sip, "via_branch", "") == chfe_to_bridge_branch
            ):
                if (
                    getattr(message.sip, "status_code", "")
                    == expected_resp_code_stimulus
                ):
                    bridge_to_chfe_invite_response = True
                    sdp_media_data = extract_media_attributes(
                        message, return_full_attr=True
                    )

            if sdp_media_data:
                bridge_to_chfe_rtpmap = sdp_media_data.get("rtpmap", None)
                get_mixer = sdp_media_data.get("rtt-mixer")
                bridge_to_chfe_mixer = get_mixer not in (None, [""])
                if bridge_to_chfe_mixer:
                    che_to_bridge_communication_successful = True
                    break

    # BRIDGE TO BCF COMMUNICATION
    bridge_to_bcf_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BRIDGE_BCF"]["ip"],
            dst_ip=interfaces_dict["IF_BCF_BRIDGE"]["ip"],
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )
    if bridge_to_bcf_invite_message:
        if hasattr(bridge_to_bcf_invite_message, "sip"):
            sdp_media_data = extract_media_attributes(
                bridge_to_bcf_invite_message, return_full_attr=True
            )
            if sdp_media_data:
                bridge_to_bcf_rtpmap = sdp_media_data.get("rtpmap", None)
                get_mixer = sdp_media_data.get("rtt-mixer")
                bridge_to_bcf_mixer = get_mixer not in (None, [""])
                if not bridge_to_bcf_mixer:
                    bridge_to_bcf_invite_successful = True

    bridge_to_bcf_invite_message_sniff_timestamp = (
        float(bridge_to_bcf_invite_message.sniff_timestamp)
        if bridge_to_bcf_invite_message
        and hasattr(bridge_to_bcf_invite_message, "sniff_timestamp")
        else 0.0
    )

    # GET CHFE SSRC
    rtp_messages_from_chfe_to_bridge = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
            dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
            packet_type=TransportProtocolEnum.RTP,
            after_timestamp=bridge_to_bcf_invite_message_sniff_timestamp,
        ),
    )
    if rtp_messages_from_chfe_to_bridge:
        for message in rtp_messages_from_chfe_to_bridge:
            chfe_ssrc.add(get_ssrc_value(message))

    # GET BRIDGE SSRC
    rtp_messages_from_bridge_to_bcf = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BRIDGE_BCF"]["ip"],
            dst_ip=interfaces_dict["IF_BCF_BRIDGE"]["ip"],
            packet_type=TransportProtocolEnum.RTP,
            after_timestamp=bridge_to_bcf_invite_message_sniff_timestamp,
        ),
    )
    if rtp_messages_from_bridge_to_bcf:
        for message in rtp_messages_from_bridge_to_bcf:
            bridge_ssrc.add(get_ssrc_value(message))
            bridge_to_bcf_csrc.update(get_rtp_attribute_list_attr(message, "csrc"))

    # GET BCF SSRC
    rtp_messages_from_bcf_to_osp = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BCF_OSP"]["ip"],
            dst_ip=interfaces_dict["IF_OSP_BCF"]["ip"],
            packet_type=TransportProtocolEnum.RTP,
            after_timestamp=bridge_to_bcf_invite_message_sniff_timestamp,
        ),
    )
    if rtp_messages_from_bcf_to_osp:
        for message in rtp_messages_from_bcf_to_osp:
            bcf_ssrc.add(get_ssrc_value(message))
            bcf_to_osp_csrc.update(get_rtp_attribute_list_attr(message, "csrc"))

    # GET all RTP messages from BCF to OSP
    rtp_messages_from_bcf_to_osp = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BCF_OSP"]["ip"],
            dst_ip=interfaces_dict["IF_OSP_BCF"]["ip"],
            packet_type=TransportProtocolEnum.RTP,
            after_timestamp=bridge_to_bcf_invite_message_sniff_timestamp,
        ),
    )
    if rtp_messages_from_bcf_to_osp:
        bcf_to_osp_message_text = get_text_from_rtp_messages(
            rtp_messages_from_bcf_to_osp
        )
        if bcf_to_osp_message_text:
            bcf_to_osp_message_text = clean_up_string(bcf_to_osp_message_text)

    for message in rtp_messages_from_bcf_to_osp:
        bcf_to_osp_ssrc.add(get_ssrc_value(message))

    # Get all RTP messages from BRIDGE to CHFE
    rtp_messages_from_bridge_to_chfe = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
            dst_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
            packet_type=TransportProtocolEnum.RTP,
            after_timestamp=bridge_to_bcf_invite_message_sniff_timestamp,
        ),
    )
    if rtp_messages_from_bridge_to_chfe:
        bridge_to_chfe_message_text = get_text_from_rtp_messages(
            rtp_messages_from_bridge_to_chfe
        )
        if bridge_to_chfe_message_text:
            bridge_to_chfe_message_text = clean_up_string(bridge_to_chfe_message_text)

    for message in rtp_messages_from_bridge_to_chfe:
        bridge_to_chfe_ssrc.add(get_ssrc_value(message))
        msg_csrc = get_rtp_attribute_list_attr(message, "csrc")
        if msg_csrc:
            bridge_to_chfe_csrc.update(msg_csrc)

    return (
        bridge_to_chfe_rtpmap,
        bridge_to_chfe_mixer,
        che_to_bridge_invite_sent,
        che_to_bridge_communication_successful,
        bridge_to_bcf_rtpmap,
        bridge_to_bcf_mixer,
        bridge_to_chfe_message_text,
        chfe_message,
        bridge_to_bcf_invite_successful,
        bcf_to_osp_message_text,
        osp_message,
        bcf_ssrc,
        bridge_ssrc,
        chfe_ssrc,
        bcf_to_osp_ssrc,
        bridge_to_chfe_ssrc,
        bridge_to_chfe_csrc,
        bridge_to_bcf_csrc,
        bcf_to_osp_csrc,
        bridge_to_chfe_invite_response,
    )


def get_test_names() -> list:
    return [
        "Validate BRIDGE handling multi-party aware",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        bridge_to_chfe_rtpmap,
        bridge_to_chfe_mixer,
        che_to_bridge_invite_sent,
        che_to_bridge_communication_successful,
        bridge_to_bcf_rtpmap,
        bridge_to_bcf_mixer,
        bridge_to_chfe_message_text,
        chfe_message,
        bridge_to_bcf_invite_successful,
        bcf_to_osp_message_text,
        osp_message,
        bcf_ssrc,
        bridge_ssrc,
        chfe_ssrc,
        bcf_to_osp_ssrc,
        bridge_to_chfe_ssrc,
        bridge_to_chfe_csrc,
        bridge_to_bcf_csrc,
        bcf_to_osp_csrc,
        bridge_to_chfe_invite_response,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)

    return [
        TestCheck(
            test_name="Validate BRIDGE handling multi-party aware",
            test_method=validate_bridge_multi_party_session,
            test_params={
                "bridge_to_chfe_rtpmap": bridge_to_chfe_rtpmap,
                "bridge_to_chfe_mixer": bridge_to_chfe_mixer,
                "che_to_bridge_invite_sent": che_to_bridge_invite_sent,
                "che_to_bridge_communication_successful": che_to_bridge_communication_successful,
                "bridge_to_bcf_rtpmap": bridge_to_bcf_rtpmap,
                "bridge_to_bcf_mixer": bridge_to_bcf_mixer,
                "bridge_to_chfe_message_text": bridge_to_chfe_message_text,
                "chfe_message": chfe_message,
                "bridge_to_bcf_invite_successful": bridge_to_bcf_invite_successful,
                "bcf_to_osp_message_text": bcf_to_osp_message_text,
                "osp_message": osp_message,
                "bcf_ssrc": bcf_ssrc,
                "bridge_ssrc": bridge_ssrc,
                "chfe_ssrc": chfe_ssrc,
                "bcf_to_osp_ssrc": bcf_to_osp_ssrc,
                "bridge_to_chfe_ssrc": bridge_to_chfe_ssrc,
                "bridge_to_chfe_csrc": bridge_to_chfe_csrc,
                "bridge_to_bcf_csrc": bridge_to_bcf_csrc,
                "bcf_to_osp_csrc": bcf_to_osp_csrc,
                "bridge_to_chfe_invite_response": bridge_to_chfe_invite_response,
            },
        )
    ]
