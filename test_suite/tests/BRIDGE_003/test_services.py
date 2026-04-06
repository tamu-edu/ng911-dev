from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.aux_services.rtp_services import (
    get_rtp_attribute_list_attr,
    is_attr_list_contains_empty_values,
    get_ssrc_value,
    is_ssrc_in_all_csrc_messages,
    get_text_from_rtp_messages,
)
from services.aux_services.sip_msg_body_services import extract_media_attributes
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
            message.src_interface == "IF_BRIDGE_OSP"
            and message.dst_interface == "IF_OSP_BRIDGE"
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

    che_to_bridge_communication_successful = False
    is_bridge_to_osp_communications_successful = False
    bridge_to_chfe_message_text = None
    is_csrs_present_from_bridge_to_chfe = None
    is_ssrc_correct = None
    bridge_to_osp_message_text = None

    # BRIDGE TO CHFE COMMUNICATION

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
    if che_to_bridge_invite_message:
        bridge_responses_to_chfe = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=float(che_to_bridge_invite_message.sniff_timestamp),
            ),
        )
        # GET Conference-ID from CHFE to BRIDGE
        for message in bridge_responses_to_chfe:
            if (
                hasattr(message, "response_code")
                and message.response_code == expected_resp_code_stimulus
            ):
                #  200 OK response should contain: 'a=rtpmap:98 t140/1000'
                if "rtpmap" in extract_media_attributes(message).keys():
                    che_to_bridge_communication_successful = True
                    break

        # GET all RTP messages from CHFE to BRIDGE
        rtp_messages_from_bridge_to_chfe = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                packet_type=TransportProtocolEnum.RTP,
                after_timestamp=float(che_to_bridge_invite_message.sniff_timestamp),
            ),
        )

        # GET CSRC values in RTP packet - there shouldn't be any
        # All RTP packets sent by BRIDGE to Test System CHFE do not contain any ids in CSRC
        bridge_to_chfe_csrc_attrs_set = [
            get_rtp_attribute_list_attr(packet, "csrc")
            for packet in rtp_messages_from_bridge_to_chfe
        ]

        is_csrs_present_from_bridge_to_chfe = is_attr_list_contains_empty_values(
            bridge_to_chfe_csrc_attrs_set
        )
        bridge_to_chfe_message_text = get_text_from_rtp_messages(
            rtp_messages_from_bridge_to_chfe
        )

    # BRIDGE TO OSP COMMUNICATION
    bridge_to_osp_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BRIDGE_OSP"]["ip"],
            dst_ip=interfaces_dict["IF_OSP_BRIDGE"]["ip"],
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )

    if bridge_to_osp_invite_message:
        rtp_messages_from_bridge_to_osp = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_BRIDGE_OSP"]["ip"],
                dst_ip=interfaces_dict["IF_OSP_BRIDGE"]["ip"],
                packet_type=TransportProtocolEnum.RTP,
                after_timestamp=float(che_to_bridge_invite_message.sniff_timestamp),
            ),
        )

        # GET Conference-ID from CHFE to BRIDGE
        for message in rtp_messages_from_bridge_to_osp:
            if (
                hasattr(message, "response_code")
                and message.response_code == osp_expected_response_code
            ):
                #  200 OK response should contain: 'a=rtpmap:98 t140/1000'
                if "rtpmap" in extract_media_attributes(message).keys():
                    if not hasattr(message, "raw_sip"):
                        message_data = str(message.sip)
                    else:
                        message_data = str(message.raw_sip)
                    if "rtt-mixer" in message_data:
                        is_bridge_to_osp_communications_successful = True
                        break

        bridge_to_osp_csrc_attrs_list = [
            get_rtp_attribute_list_attr(packet, "csrc")
            for packet in rtp_messages_from_bridge_to_osp
        ]

        # All RTP packets received by Test System OSP and Test System CHFE from BRIDGE contain one SSRC
        bridge_to_osp_ssrc_value_list = [
            get_ssrc_value(packet) for packet in rtp_messages_from_bridge_to_osp
        ]
        bridge_to_osp_ssrc_value_set = set(bridge_to_osp_ssrc_value_list)

        bridge_to_osp_message_text = get_text_from_rtp_messages(
            rtp_messages_from_bridge_to_osp
        )

        if len(bridge_to_osp_ssrc_value_set) == 1 and is_ssrc_in_all_csrc_messages(
            bridge_to_osp_csrc_attrs_list, bridge_to_osp_ssrc_value_list[0]
        ):
            is_ssrc_correct = True

    return (
        che_to_bridge_communication_successful,
        is_csrs_present_from_bridge_to_chfe,
        bridge_to_chfe_message_text,
        chfe_message,
        is_bridge_to_osp_communications_successful,
        is_ssrc_correct,
        bridge_to_osp_message_text,
        osp_message,
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
        che_to_bridge_communication_successful,
        is_csrs_present_from_bridge_to_chfe,
        bridge_to_chfe_message_text,
        chfe_message,
        is_bridge_to_osp_communications_successful,
        is_ssrc_correct,
        bridge_to_osp_message_text,
        osp_message,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)

    return [
        TestCheck(
            test_name="Validate BRIDGE handling multi-party aware",
            test_method=validate_bridge_multi_party_session,
            test_params={
                "che_to_bridge_communication_successful": che_to_bridge_communication_successful,
                "is_csrs_present_from_bridge_to_chfe": is_csrs_present_from_bridge_to_chfe,
                "bridge_to_chfe_message_text": bridge_to_chfe_message_text,
                "chfe_message": chfe_message,
                "is_bridge_to_osp_communications_successful": is_bridge_to_osp_communications_successful,
                "is_ssrc_correct": is_ssrc_correct,
                "bridge_to_osp_message_text": bridge_to_osp_message_text,
                "osp_message": osp_message,
            },
        )
    ]
