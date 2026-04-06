from checks.http.checks import validate_response_code
from services.aux_services.message_services import get_header_field_value
from services.aux_services.sip_msg_body_services import clean_up_string
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_messages,
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_006.checks import (
    validate_bye_transaction_no_ack,
    validate_ack_fields,
    validate_bcf_sends_aks_for_each_invite_confirmation,
    validate_bcf_forwards_bye,
)


def find_200_ok(messages, cseq_method: str) -> str | None:
    """Return '200' if any message in *messages* is a 200 OK for the given CSeq method"""
    if not messages:
        return None

    return next(
        (
            msg.sip.get("status_code")
            for msg in messages
            if hasattr(msg.sip, "status_code")
            and hasattr(msg.sip, "cseq_method")
            and msg.sip.get("status_code") == "200"
            and msg.sip.get("cseq_method") == cseq_method
        ),
        None,
    )


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    sip_method = None
    fqdn_dict = {}

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            sip_method = message.sip_method
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                    fqdn_dict[interface.name] = interface.fqdn
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                    fqdn_dict[interface.name] = interface.fqdn
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                    fqdn_dict[interface.name] = interface.fqdn
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
                    fqdn_dict[interface.name] = interface.fqdn

    if (
        stimulus_src_ip is None
        or stimulus_dst_ip is None
        or out_scr_ip is None
        or out_dst_ip is None
    ):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required"
            "parameters for osp_ip, bcf_ip, esrp_ip addresses"
        )
    else:
        return (
            stimulus_src_ip,
            stimulus_dst_ip,
            out_scr_ip,
            out_dst_ip,
            sip_method,
            fqdn_dict,
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, sip_method, fqdn_dict = (
        get_filter_parameters(lab_config, filtering_options, variation)
    )

    bcf_200_ok = None
    bcf_200_ok_after_osp_bye = None
    ack_after_bye_messages = None
    bcf_invite_to = None
    bcf_invite_call_id = None
    bcf_invite_contacts = []
    esrp_invite_responses_messages = []
    bye_call_id = None

    # Get SIP INVITE from Test System OSP
    osp_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )

    # Get BCF 200 OK response for Test System OSP INVITE
    if osp_invite_message:
        bcf_ok_responses = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=float(osp_invite_message.sniff_timestamp),
            ),
        )
        bcf_200_ok = find_200_ok(bcf_ok_responses, "INVITE")

    # Get INVITE messages from BCF to ESRP
    bcf_invite_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )

    if bcf_invite_messages:
        espr_responses = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=out_dst_ip,
                dst_ip=out_scr_ip,
                packet_type=PacketTypeEnum.SIP,
            ),
        )
        esrp_invite_responses_messages = [
            msg for msg in espr_responses if find_200_ok([msg], "INVITE")
        ]

    if bcf_invite_messages:
        bcf_invite_to = clean_up_string(
            get_header_field_value(bcf_invite_messages[0], "to")
        )
        bcf_invite_call_id = clean_up_string(
            get_header_field_value(bcf_invite_messages[0], "call-id")
        )
        bcf_invite_contacts = [
            clean_up_string(get_header_field_value(msg, "contact"))
            for msg in bcf_invite_messages
        ]

    osp_ack_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.ACK],
        ),
    )

    # Get ACK messages from BCF to ESRP. BCF sends ACK for each 2xx response for SIP INVITE
    bcf_ack_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.ACK],
        ),
    )

    osp_bye_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.BYE],
        ),
    )

    # Get BYE messages from BCF to ESRP
    bcf_bye_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.BYE],
        ),
    )

    if osp_bye_messages and bcf_bye_messages:
        bye_timestamp = float(bcf_bye_messages[0].sniff_timestamp)
        bye_call_id = get_header_field_value(bcf_bye_messages[0], "Call-ID")
        ack_after_bye_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=out_scr_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[SIPMethodEnum.ACK],
                after_timestamp=bye_timestamp,
            ),
        )
        bcf_responses_after_osp_bye = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=float(osp_bye_messages[0].sniff_timestamp),
            ),
        )
        osp_bye_call_id = get_header_field_value(osp_bye_messages[0], "Call-ID")
        bcf_responses_after_osp_bye_with_bye_call_id = [
            msg
            for msg in bcf_responses_after_osp_bye
            if get_header_field_value(msg, "Call-ID") == osp_bye_call_id.strip()
        ]
        bcf_200_ok_after_osp_bye = find_200_ok(
            bcf_responses_after_osp_bye_with_bye_call_id, "BYE"
        )

    return (
        sip_method,
        fqdn_dict,
        stimulus_src_ip,
        stimulus_dst_ip,
        osp_invite_message,
        bcf_invite_to,
        bcf_invite_call_id,
        bcf_invite_contacts,
        bcf_200_ok,
        bcf_invite_messages,
        esrp_invite_responses_messages,
        osp_ack_messages,
        bcf_ack_messages,
        osp_bye_messages,
        bcf_bye_messages,
        ack_after_bye_messages,
        bcf_200_ok_after_osp_bye,
        bye_call_id,
    )


def get_test_names() -> list:
    return [
        "Validate ACK contains correct fields.",
        "Validate BCF sends 200 OK after receiving SIP INVITE from Test System OSP.",
        "Validate BCF sends ACK for each 2xx response for SIP INVITE.",
        "Validate BCF forwards BYE.",
        "Validate BCF completes BYE transaction without ACK.",
        "Validate BCF sends 200 OK after receiving SIP BYE from Test System OSP.",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        sip_method,
        fqdn_dict,
        stimulus_src_ip,
        stimulus_dst_ip,
        osp_invite_message,
        bcf_invite_to,
        bcf_invite_call_id,
        bcf_invite_contacts,
        bcf_200_ok,
        bcf_invite_messages,
        esrp_invite_responses_messages,
        osp_ack_messages,
        bcf_ack_messages,
        osp_bye_messages,
        bcf_bye_messages,
        ack_after_bye_messages,
        bcf_200_ok_after_osp_bye,
        bye_call_id,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    checks = [
        TestCheck(
            test_name="Validate ACK contains correct fields.",
            test_method=validate_ack_fields,
            test_params={
                "bcf_invite_messages": bcf_invite_messages,
                "bcf_ack_messages": bcf_ack_messages,
                "stimulus_src_ip": stimulus_src_ip,
                "stimulus_dst_ip": stimulus_dst_ip,
                "bcf_invite_to": bcf_invite_to,
                "bcf_invite_call_id": bcf_invite_call_id,
                "bcf_invite_contacts": bcf_invite_contacts,
                "fqdn_dict": fqdn_dict,
            },
        ),
        TestCheck(
            test_name="Validate BCF sends 200 OK after receiving SIP INVITE from Test System OSP.",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": "200",
                "response": bcf_200_ok,
            },
        ),
        TestCheck(
            test_name="Validate BCF sends ACK for each 2xx response for SIP INVITE.",
            test_method=validate_bcf_sends_aks_for_each_invite_confirmation,
            test_params={
                "esrp_invite_responses_messages": esrp_invite_responses_messages,
                "bcf_ack_messages": bcf_ack_messages,
            },
        ),
    ]

    if sip_method == "INVITE":
        checks.append(
            TestCheck(
                test_name="Validate BCF forwards BYE.",
                test_method=validate_bcf_forwards_bye,
                test_params={
                    "osp_bye_messages": osp_bye_messages,
                    "bcf_bye_messages": bcf_bye_messages,
                },
            )
        )
        checks.append(
            TestCheck(
                test_name="Validate BCF completes BYE transaction without ACK.",
                test_method=validate_bye_transaction_no_ack,
                test_params={
                    "ack_after_bye_messages": ack_after_bye_messages,
                    "bye_call_id": bye_call_id,
                },
            ),
        )
        checks.append(
            TestCheck(
                test_name="Validate BCF sends 200 OK after receiving SIP BYE from Test System OSP.",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": "200",
                    "response": bcf_200_ok_after_osp_bye,
                },
            ),
        )
    return checks
