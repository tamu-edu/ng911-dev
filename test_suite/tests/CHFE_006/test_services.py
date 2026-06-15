from services.aux_services.sip_msg_body_services import (
    get_conference_id,
    extract_media_attributes,
)
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
    get_messages,
    get_dns_list,
    get_dns_packets_from_pcap,
)
from enums import PacketTypeEnum, SIPMethodEnum, TransportProtocolEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_006.checks import (
    verify_routing_via_conference_aware,
    verify_routing_w_or_wo_b2bua,
)


def get_filter_parameters(
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
    pcap_service: PcapCaptureService,
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :param pcap_service: PcapCaptureService instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
    xml_sender_data_path, stimulus_#src_ip_list, stimulus_#dst_ip_list, out_#src_ip_list, out_#dst_ip_list)
    """
    interfaces_dict: dict = {}
    # If 'IF_CHFE_TS' not in interfaces - this is a variation #1
    is_variation1 = "IF_CHFE_TS" not in interfaces_dict.keys()

    dns_packets = get_dns_packets_from_pcap(pcap_service)

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
                "ip_list": get_dns_list(dns_packets, interface.fqdn) or [],
                "port_mapping": port_dict,
            }

    if not interfaces_dict:
        raise WrongConfigurationError(
            "Lab Config file error - cannot extract interface data"
        )
    else:
        return interfaces_dict, is_variation1


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    def get_bidirectional_media(ip1: str, ip2: str) -> list:
        """Gets RTP messages for both directions between two interfaces."""
        return [
            get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict[src]["ip"],
                    dst_ip=interfaces_dict[dst]["ip"],
                    src_ip_list=interfaces_dict[src]["ip_list"],
                    dst_ip_list=interfaces_dict[dst]["ip_list"],
                    packet_type=TransportProtocolEnum.RTP,
                ),
            )
            for src, dst in [(ip1, ip2), (ip2, ip1)]
        ]

    def get_payload_type_from_media(packet) -> str:
        if hasattr(packet, "rtp"):
            for line in str(packet.rtp).split("\n"):
                if "Payload type:" in line:
                    return line[len("Payload type: ") :]
        return ""

    interfaces_dict, is_variation1 = get_filter_parameters(
        lab_config, filtering_options, variation, pcap_service
    )

    if is_variation1:
        # TODO #Refer-To: header field with SIP URI of Test System CHFE (Transfer-to) - IP from labconfig

        # FOR VARIATION1:
        esrp_initial_conference_id = chfe_invite_response_code = (
            chfe_subscribe_request
        ) = chfe_conference_id = chfe_request_uri_refer = chfe_refer_to = sip_bye = (
            media_transfer_esrp_to_t_chfe
        ) = media_transfer_esrp_bcf = media_transfer_osp_bcf = bridge_call = (
            esrp_to_t_chfe_payload_type
        ) = esrp_to_bcf_payload_type = osp_to_bcf_payload_type = bcf_osp_media_type = (
            esrp_to_bcf_media_type
        ) = None

        # Filter out Test System OSP cal to BCF
        osp_invite_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_OSP_BCF"]["ip"],
                dst_ip=interfaces_dict["IF_BCF_OSP"]["ip"],
                src_ip_list=interfaces_dict["IF_OSP_BCF"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BCF_OSP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        if osp_invite_request:
            bcf_to_osp_ok = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_BCF_OSP"]["ip"],
                    dst_ip=interfaces_dict["IF_OSP_BCF"]["ip"],
                    src_ip_list=interfaces_dict["IF_BCF_OSP"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_OSP_BCF"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=float(osp_invite_request.sniff_timestamp),
                ),
            )

            bcf_osp_media_type = extract_media_attributes(bcf_to_osp_ok)

        # Filter out Test System BCF call to ESRP
        bcf_to_esrp_invite_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_BCF_ESRP"]["ip"],
                dst_ip=interfaces_dict["IF_ESRP_BCF"]["ip"],
                src_ip_list=interfaces_dict["IF_BCF_ESRP"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_ESRP_BCF"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        if bcf_to_esrp_invite_request:
            esrp_to_bcf_ok = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_ESRP_BCF"]["ip"],
                    dst_ip=interfaces_dict["IF_BCF_ESRP"]["ip"],
                    src_ip_list=interfaces_dict["IF_ESRP_BCF"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_BCF_ESRP"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=float(osp_invite_request.sniff_timestamp),
                ),
            )

            esrp_to_bcf_media_type = extract_media_attributes(esrp_to_bcf_ok)

        esrp_invite_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        if esrp_invite_request:

            esrp_initial_conference_id = get_conference_id(
                esrp_invite_request.sip.get("contact")
            )

            chfe_invite_response = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                    dst_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                    src_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=float(esrp_invite_request.sniff_timestamp),
                ),
            )

            if chfe_invite_response:
                try:
                    chfe_invite_response_code = chfe_invite_response.sip.get(
                        "status_code"
                    )
                except AttributeError:
                    pass

            chfe_subscribe_request = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                    dst_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                    src_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    message_method=[
                        SIPMethodEnum.SUBSCRIBE,
                    ],
                    after_timestamp=float(esrp_invite_request.sniff_timestamp),
                ),
            )

            if chfe_subscribe_request:
                chfe_conference_id = get_conference_id(
                    chfe_subscribe_request.sip.get("to")
                )

        chfe_refer_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                dst_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.REFER,
                ],
            ),
        )

        if chfe_refer_request:
            chfe_request_uri_refer = chfe_refer_request.sip.get("r_uri")
            chfe_refer_to = chfe_refer_request.sip.get("refer_to")

            # Get media transfers by calling the helper function for each pair of interfaces
            media_transfer_esrp_to_t_chfe = get_bidirectional_media(
                "IF_ESRP_TS-CHFE", "IF_TS-CHFE_ESRP"
            )
            media_transfer_esrp_bcf = get_bidirectional_media(
                "IF_BCF_ESRP", "IF_ESRP_BCF"
            )
            media_transfer_osp_bcf = get_bidirectional_media("IF_OSP_BCF", "IF_BCF_OSP")

            if sum(len(lst) for lst in media_transfer_esrp_to_t_chfe) > 2:
                esrp_to_t_chfe_payload_type = get_payload_type_from_media(
                    media_transfer_esrp_to_t_chfe[0][0]
                )
            if sum(len(lst) for lst in media_transfer_esrp_bcf) > 2:
                esrp_to_bcf_payload_type = get_payload_type_from_media(
                    media_transfer_esrp_bcf[0][0]
                )
            if sum(len(lst) for lst in media_transfer_osp_bcf) > 2:
                osp_to_bcf_payload_type = get_payload_type_from_media(
                    media_transfer_osp_bcf[0][0]
                )

            sip_bye = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                    dst_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                    src_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    message_method=[
                        SIPMethodEnum.BYE,
                    ],
                    after_timestamp=float(chfe_refer_request.sniff_timestamp),
                ),
            )

        esrp_notify_msgs = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.NOTIFY,
                ],
            ),
        )

        chfe_ok_msgs = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                dst_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
            ),
        )

        esrp_invite_request_to_t_chfe = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_ESRP_TS-CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_TS-CHFE_ESRP"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_TS-CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_TS-CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        media_attr_response_t_chfe = None
        if esrp_invite_request_to_t_chfe:
            t_chfe_responses = get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_TS-CHFE_ESRP"]["ip"],
                    dst_ip=interfaces_dict["IF_ESRP_TS-CHFE"]["ip"],
                    src_ip_list=interfaces_dict["IF_TS-CHFE_ESRP"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_ESRP_TS-CHFE"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=float(
                        esrp_invite_request_to_t_chfe.sniff_timestamp
                    ),
                ),
            )

            for response in t_chfe_responses:
                status_code = response.sip.get("status_code")
                if status_code and status_code == "200":
                    media_attr_response_t_chfe = extract_media_attributes(response)
                    break

            if (
                interfaces_dict["IF_CHFE_BRIDGE"]["ip"]
                and interfaces_dict["IF_BRIDGE_CHFE"]["ip"]
            ) or (
                interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"]
                and interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"]
            ):
                bridge_call = get_first_message_matching_filter(
                    pcap_service,
                    FilterConfig(
                        src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                        dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                        src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                        dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                        packet_type=PacketTypeEnum.SIP,
                        after_timestamp=float(chfe_refer_request.sniff_timestamp),
                    ),
                )
        # Variation1 output data
        return (
            "Variation1",
            [
                osp_invite_request,
                chfe_invite_response_code,
                esrp_initial_conference_id,
                chfe_subscribe_request,
                chfe_conference_id,
                chfe_refer_request,
                chfe_request_uri_refer,
                chfe_refer_to,
                sip_bye,
                esrp_notify_msgs,
                chfe_ok_msgs,
                media_transfer_esrp_to_t_chfe,
                media_transfer_esrp_bcf,
                media_transfer_osp_bcf,
                bcf_osp_media_type,
                esrp_to_bcf_media_type,
                media_attr_response_t_chfe,
                esrp_to_t_chfe_payload_type,
                esrp_to_bcf_payload_type,
                osp_to_bcf_payload_type,
                bridge_call,
            ],
        )

    # Variation 2/3 workflow
    else:

        osp_call_id = osp_to = osp_from = chfe_invite_response_code = conf_response = (
            esrp_conference_id_init
        ) = chfe_conference_id_bridge = chfe_conference_id_subscribe = (
            chfe_request_uri
        ) = chfe_refer_to = chfe_call_id = chfe_to_tag = chfe_from_tag = (
            chfe_cof_id_refer2
        ) = media_transfer_data = media_attr_request_from_chfe_dict = payload_type = (
            None
        )

        osp_invite_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_OSP_BCF"]["ip"],
                dst_ip=interfaces_dict["IF_BCF_OSP"]["ip"],
                src_ip_list=interfaces_dict["IF_OSP_BCF"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BCF_OSP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        if osp_invite_request:
            osp_call_id = osp_invite_request.get("call_id")
            osp_to = osp_invite_request.get("to")
            osp_from = osp_invite_request.get("from")

        init_sip_invite_to_chfe = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        init_sip_chfe_response = None

        # Define the variation
        if "IF_CHFE_OSP" in interfaces_dict.keys():  # Variation number 2
            source_id = "IF_CHFE_OSP"
            dest_id = "IF_OSP_CHFE"
            variation_name = "Variation2"
        else:  # Variation #3
            source_id = "IF_CHFE_BCF"
            dest_id = "IF_BCF_CHFE"
            variation_name = "Variation3"

            init_sip_chfe_response = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict[source_id]["ip"],
                    dst_ip=interfaces_dict[dest_id]["ip"],
                    src_ip_list=interfaces_dict[source_id]["ip_list"],
                    dst_ip_list=interfaces_dict[dest_id]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=float(init_sip_invite_to_chfe.sniff_timestamp),
                ),
            )

            if init_sip_chfe_response:
                try:
                    chfe_invite_response_code = init_sip_chfe_response.sip.get(
                        "status_code"
                    )
                except AttributeError:
                    pass

        chfe_invite_request_ts = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_TS-CA"]["ip"],
                dst_ip=interfaces_dict["IF_TS-CA_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_TS-CA"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_TS-CA_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        if chfe_invite_request_ts:
            conf_response = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_TS-CA_CHFE"]["ip"],
                    dst_ip=interfaces_dict["IF_CHFE_TS-CA"]["ip"],
                    src_ip_list=interfaces_dict["IF_TS-CA_CHFE"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_CHFE_TS-CA"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,  # TODO it should be Moved Contact SIP
                    after_timestamp=float(chfe_invite_request_ts.sniff_timestamp),
                ),
            )

            if conf_response:
                esrp_conference_id_init = conf_response.sip.get("contact")
                media_attr_request_from_chfe_dict = extract_media_attributes(
                    conf_response
                )

        chfe_invite_request_bridge = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.INVITE,
                ],
            ),
        )

        if chfe_invite_request_bridge:
            chfe_invite_request_ok = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                    dst_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                    src_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,  # TODO HERE SHOULD BE 'OK'
                    after_timestamp=float(chfe_invite_request_bridge.sniff_timestamp),
                ),
            )
            if chfe_invite_request_ok:
                chfe_conference_id_bridge = chfe_invite_request_ok.sip.get(
                    "contact"
                )  # TODO tag for conference_id

            # Get media transfers by calling the helper function for each pair of interfaces
            if variation_name == "Variation2":
                media_transfer_data = get_bidirectional_media(
                    "IF_OSP_TS-CHFE", "IF_TS-CHFE_OSP"
                )
            else:
                media_transfer_data = get_bidirectional_media(
                    "IF_BCF_TS-CHFE", "IF_TS-CHFE_BCF"
                )

            if media_transfer_data:
                if sum(len(lst) for lst in media_transfer_data) > 2:
                    payload_type = get_payload_type_from_media(
                        media_transfer_data[0][0]
                    )

        chfe_subscribe_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.SUBSCRIBE,
                ],
            ),
        )

        if chfe_subscribe_request:
            chfe_conference_id_subscribe = chfe_subscribe_request.sip.get("contact")

        chfe_refer_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.REFER,
                ],
            ),
        )

        chfe_bye_after_refer = None
        if source_id and dest_id and chfe_refer_request:
            chfe_bye_after_refer = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                    dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                    src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                    dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                    packet_type=PacketTypeEnum.SIP,
                    message_method=[
                        SIPMethodEnum.BYE,
                    ],
                    after_timestamp=float(chfe_refer_request.sniff_timestamp),
                ),
            )

        if chfe_refer_request:
            chfe_request_uri = chfe_refer_request.get("r_uri")
            chfe_refer_to = chfe_refer_request.get("refer_to")
            chfe_call_id = chfe_refer_request.sip.replaces.split(";")[0]

            if chfe_refer_request.sip.get("replaces"):
                for tag in chfe_refer_request.sip.replaces.split(";"):
                    if tag.startswith("to-tag"):
                        chfe_to_tag = tag[7:]
                    if tag.startswith("from-tag"):
                        chfe_from_tag = tag[9:]

        chfe_sip_refer_2 = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.REFER,
                ],
            ),
        )
        if chfe_sip_refer_2:
            chfe_cof_id_refer2 = chfe_sip_refer_2.sip.get("contact")

        sip_bye = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_BRIDGE"]["ip"],
                dst_ip=interfaces_dict["IF_BRIDGE_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_CHFE_BRIDGE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_BRIDGE_CHFE"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.BYE,
                ],
            ),
        )

        esrp_notify_msgs = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                dst_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
                message_method=[
                    SIPMethodEnum.NOTIFY,
                ],
            ),
        )

        chfe_ok_msgs = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
                dst_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
                src_ip_list=interfaces_dict["IF_ESRP_CHFE"]["ip_list"],
                dst_ip_list=interfaces_dict["IF_CHFE_ESRP"]["ip_list"],
                packet_type=PacketTypeEnum.SIP,
            ),
        )
        # Variation 2/3
        return (
            variation_name,
            [
                osp_invite_request,
                osp_call_id,
                osp_to,
                osp_from,
                init_sip_chfe_response,
                chfe_invite_response_code,
                chfe_invite_request_ts,
                conf_response,
                esrp_conference_id_init,
                chfe_invite_request_bridge,
                chfe_conference_id_bridge,
                chfe_subscribe_request,
                chfe_conference_id_subscribe,
                chfe_refer_request,
                chfe_bye_after_refer,
                chfe_request_uri,
                chfe_refer_to,
                chfe_call_id,
                chfe_to_tag,
                chfe_from_tag,
                chfe_sip_refer_2,
                chfe_cof_id_refer2,
                sip_bye,
                esrp_notify_msgs,
                chfe_ok_msgs,
                media_transfer_data,
                media_attr_request_from_chfe_dict,
                payload_type,
            ],
        )


def get_test_names() -> list:
    return [
        "Verify routing all calls via a Conference-aware UA",
        "Verify Ad Hoc without B2BUA in the Ingress Call Path/Ad Hoc with B2BUA in the Ingress Call Path",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    variation_name, test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation
    )

    if variation_name == "Variation1":
        (
            osp_invite_request,
            chfe_invite_response_code,
            esrp_initial_conference_id,
            chfe_subscribe_request,
            chfe_conference_id,
            chfe_refer_request,
            chfe_request_uri_refer,
            chfe_refer_to,
            sip_bye,
            esrp_notify_msgs,
            chfe_ok_msgs,
            media_transfer_esrp_to_t_chfe,
            media_transfer_esrp_bcf,
            media_transfer_osp_bcf,
            bcf_osp_media_type,
            esrp_to_bcf_media_type,
            media_attr_response_t_chfe,
            esrp_to_t_chfe_payload_type,
            esrp_to_bcf_payload_type,
            osp_to_bcf_payload_type,
            bridge_call,
        ) = test_data

        return [
            TestCheck(
                test_name="Verify routing all calls via a Conference-aware UA",
                test_method=verify_routing_via_conference_aware,
                test_params={
                    "osp_invite_request": osp_invite_request,
                    "chfe_invite_response_code": chfe_invite_response_code,
                    "esrp_initial_conference_id": esrp_initial_conference_id,
                    "chfe_subscribe_request": chfe_subscribe_request,
                    "chfe_conference_id": chfe_conference_id,
                    "chfe_refer_request": chfe_refer_request,
                    "chfe_request_uri_refer": chfe_request_uri_refer,
                    "chfe_refer_to": chfe_refer_to,
                    "sip_bye": sip_bye,
                    "esrp_notify_msgs": esrp_notify_msgs,
                    "chfe_ok_msgs": chfe_ok_msgs,
                    "media_transfer_esrp_to_t_chfe": media_transfer_esrp_to_t_chfe,
                    "media_transfer_esrp_bcf": media_transfer_esrp_bcf,
                    "media_transfer_osp_bcf": media_transfer_osp_bcf,
                    "bcf_osp_media_type": bcf_osp_media_type,
                    "esrp_to_bcf_media_type": esrp_to_bcf_media_type,
                    "media_attr_response_t_chfe": media_attr_response_t_chfe,
                    "esrp_to_t_chfe_payload_type": esrp_to_t_chfe_payload_type,
                    "esrp_to_bcf_payload_type": esrp_to_bcf_payload_type,
                    "osp_to_bcf_payload_type": osp_to_bcf_payload_type,
                    "bridge_call": bridge_call,
                },
            )
        ]

    else:
        (
            osp_invite_request,
            osp_call_id,
            osp_to,
            osp_from,
            init_sip_chfe_response,
            chfe_invite_response_code,
            chfe_invite_request_ts,
            conf_response,
            esrp_conference_id_init,
            chfe_invite_request_bridge,
            chfe_conference_id_bridge,
            chfe_subscribe_request,
            chfe_conference_id_subscribe,
            chfe_refer_request,
            chfe_bye_after_refer,
            chfe_request_uri,
            chfe_refer_to,
            chfe_call_id,
            chfe_to_tag,
            chfe_from_tag,
            chfe_sip_refer_2,
            chfe_cof_id_refer2,
            sip_bye,
            esrp_notify_msgs,
            chfe_ok_msgs,
            media_transfer_data,
            media_attr_request_from_chfe_dict,
            payload_type,
        ) = test_data

        return [
            TestCheck(
                test_name="Verify Ad Hoc without B2BUA in the Ingress Call Path/Ad Hoc with B2BUA in the Ingress Call Path",
                test_method=verify_routing_w_or_wo_b2bua,
                test_params={
                    "osp_invite_request": osp_invite_request,
                    "osp_call_id": osp_call_id,
                    "osp_to": osp_to,
                    "osp_from": osp_from,
                    "init_sip_chfe_response": init_sip_chfe_response,
                    "chfe_invite_response_code": chfe_invite_response_code,
                    "chfe_invite_request_ts": chfe_invite_request_ts,
                    "conf_response": conf_response,
                    "esrp_conference_id_init": esrp_conference_id_init,
                    "chfe_invite_request_bridge": chfe_invite_request_bridge,
                    "chfe_conference_id_bridge": chfe_conference_id_bridge,
                    "chfe_subscribe_request": chfe_subscribe_request,
                    "chfe_conference_id_subscribe": chfe_conference_id_subscribe,
                    "chfe_refer_request": chfe_refer_request,
                    "chfe_bye_after_refer": chfe_bye_after_refer,
                    "chfe_request_uri": chfe_request_uri,
                    "chfe_refer_to": chfe_refer_to,
                    "chfe_call_id": chfe_call_id,
                    "chfe_to_tag": chfe_to_tag,
                    "chfe_from_tag": chfe_from_tag,
                    "chfe_sip_refer_2": chfe_sip_refer_2,
                    "chfe_cof_id_refer2": chfe_cof_id_refer2,
                    "sip_bye": sip_bye,
                    "esrp_notify_msgs": esrp_notify_msgs,
                    "chfe_ok_msgs": chfe_ok_msgs,
                    "media_transfer_data": media_transfer_data,
                    "media_attr_request_from_chfe_dict": media_attr_request_from_chfe_dict,
                    "payload_type": payload_type,
                },
            )
        ]
