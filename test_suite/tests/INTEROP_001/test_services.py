from dataclasses import dataclass, asdict
from typing import Optional

from checks.sip.call_info_header_field_checks.checks import (
    test_incident_tracking_id_urn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn,
    test_emergency_call_id_urn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
)
from checks.sip.header_field_checks.checks import (
    test_adding_header_field_on_top_of_its_section,
    test_urn_service_sos_in_request_uri,
    test_urn_service_sos_in_to_header_field,
    test_all_header_fields_are_same,
    test_header_unchanged_if_equals,
    test_resource_priority_unchanged_if_valid,
    test_from_unchanged_if_valid_verstat,
)
from checks.general.checks import (
    test_if_parameter_has_expected_value,
    test_if_parameter_has_one_of_expected_values,
    is_data_present,
    is_test_data_the_same,
)
from checks.sip.message_body_checks.checks import test_keeping_original_message_bodies
from services.aux_services.message_services import (
    get_header_field_value,
    extract_all_contents_from_message_body,
)
from services.aux_services.sip_msg_body_services import clean_up_string
from services.aux_services.sip_services import (
    extract_sip_header_values,
    get_list_of_all_header_fields_from_sip_message,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.message_collector_service import MessageCollectorService
from services.pcap_service import PcapCaptureService
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_004.checks import validate_bcf_and_source_id
from tests.INTEROP_001.checks import (
    test_geolocation_is_valid,
    validate_contact_header_field,
    validate_sdp_media_message_body,
)
from tests.INTEROP_001.constants import HEADERS_EXCEPTION_LIST


@dataclass
class InviteData:
    """All extracted fields from a single SIP INVITE."""

    message: Optional[object] = None
    message_descr: Optional[str] = None
    all_headers: Optional[list] = None
    message_body: Optional[list] = None
    call_info_header: Optional[str] = None
    call_id: Optional[str] = None
    incident_id: Optional[str] = None
    emergency_source: Optional[str] = None
    resource_priority: Optional[str] = None
    geolocation: Optional[object] = None
    requests_uri: Optional[str] = None
    to_header: Optional[str] = None
    from_header: Optional[str] = None
    contact_header: Optional[str] = None
    route_header: Optional[str] = None
    via_header: Optional[str] = None
    record_route_header: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_invite_data(message, message_descr) -> InviteData:
    return InviteData(
        message=message,
        message_descr=message_descr,
        all_headers=get_list_of_all_header_fields_from_sip_message(message),
        message_body=extract_all_contents_from_message_body(message),
        call_info_header=clean_up_string(get_header_field_value(message, "Call-Info")),
        call_id=clean_up_string(
            str(
                extract_sip_header_values(
                    message, "Call-Info", "purpose=emergency-CallId"
                )
            )
        ),
        incident_id=clean_up_string(
            str(
                extract_sip_header_values(
                    message, "Call-Info", "purpose=emergency-IncidentId"
                )
            )
        ),
        resource_priority=clean_up_string(
            get_header_field_value(message, "Resource-Priority")
        ),
        emergency_source=extract_sip_header_values(
            message, "Call-Info", "purpose=emergency-source"
        ),
        geolocation=get_header_field_value(message, "Geolocation"),
        requests_uri=(
            message.sip.get("r_uri")
            if message and hasattr(message.sip, "r_uri")
            else None
        ),
        to_header=clean_up_string(get_header_field_value(message, "To")),
        from_header=clean_up_string(get_header_field_value(message, "From")),
        contact_header=clean_up_string(get_header_field_value(message, "Contact")),
        route_header=clean_up_string(get_header_field_value(message, "Route")),
        via_header=clean_up_string(get_header_field_value(message, "Via")),
        record_route_header=clean_up_string(
            get_header_field_value(message, "Record-Route")
        ),
    )


@dataclass
class MessageData:
    """All extracted fields from a single SIP INVITE."""

    message: Optional[object] = None
    message_descr: Optional[str] = None
    message_body: Optional[list] = None
    all_headers: Optional[list] = None
    route_header: Optional[str] = None
    via_header: Optional[str] = None
    to_header: Optional[str] = None
    from_header: Optional[str] = None
    requests_uri: Optional[str] = None
    resource_priority: Optional[str] = None
    record_route_header: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_message_data(message, message_descr) -> MessageData:
    return MessageData(
        message=message,
        message_descr=message_descr,
        message_body=extract_all_contents_from_message_body(message),
        all_headers=get_list_of_all_header_fields_from_sip_message(message),
        route_header=clean_up_string(get_header_field_value(message, "Route")),
        via_header=clean_up_string(get_header_field_value(message, "Via")),
        to_header=clean_up_string(get_header_field_value(message, "To")),
        from_header=clean_up_string(get_header_field_value(message, "From")),
        requests_uri=(
            message.sip.get("r_uri") if hasattr(message.sip, "r_uri") else None
        ),
        resource_priority=clean_up_string(
            get_header_field_value(message, "Resource-Priority")
        ),
        record_route_header=clean_up_string(
            get_header_field_value(message, "Record-Route")
        ),
    )


def _get_fqdn_or_ip(interface, interfaces_dict):
    if interface in interfaces_dict:
        fqdn = interfaces_dict[interface].get("fqdn")
        ip = interfaces_dict[interface].get("ip")
        if fqdn:
            return fqdn
        else:
            return ip
    return None


def _first_by_method(packets, method):
    return next(
        (
            p
            for p in (packets or [])
            if hasattr(p, "sip")
            and hasattr(p.sip, "method")
            and p.sip.get("method") == method
        ),
        None,
    )


def _first_by_status(packets, status_code, cseq_method=None):
    for p in packets or []:
        if not hasattr(p, "sip"):
            continue
        if p.sip.get("status_code") != status_code:
            continue
        if cseq_method and p.sip.get("cseq_method") != cseq_method:
            continue
        return p
    return None


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    other = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    output_src_ip = None
    output_dst_ip = None
    other_src_ip = None
    other_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
            output = message
        elif message.message_type == FilterMessageType.OTHER.value:
            other = message

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    output_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    output_dst_ip = interface.ip
                elif interface.name == other.src_interface:
                    other_src_ip = interface.ip
                elif interface.name == other.dst_interface:
                    other_dst_ip = interface.ip

        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or output_src_ip is None
            or output_dst_ip is None
            or other_src_ip is None
            or other_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters"
            )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        output_src_ip,
        output_dst_ip,
        other_src_ip,
        other_dst_ip,
    )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
):
    collector = MessageCollectorService(
        interfaces=[
            "IF_OSP_BCF",
            "IF_BCF_ESRP",
            "IF_ESRP_CHFE",
        ],
        pcap_service=pcap_service,
        lab_config=lab_config,
        packet_type=[PacketTypeEnum.SIP],
    )

    rtp_collector = MessageCollectorService(
        interfaces=["IF_OSP_BCF", "IF_BCF_CHFE"],
        pcap_service=pcap_service,
        lab_config=lab_config,
        packet_type=[PacketTypeEnum.UDP, PacketTypeEnum.RTP],
    )
    interfaces_dict = lab_config.get_interfaces_data()
    bcf_fqdn_or_ip = _get_fqdn_or_ip("IF_BCF_ESRP", interfaces_dict)

    osp_to_bcf_msgs = collector.get_requests("IF_OSP_BCF")
    bcf_to_osp_msgs = collector.get_responses("IF_OSP_BCF")
    bcf_to_esrp_msgs = collector.get_requests("IF_BCF_ESRP")
    esrp_to_bcf_msgs = collector.get_responses("IF_BCF_ESRP")
    esrp_to_chfe_msgs = collector.get_requests("IF_ESRP_CHFE")
    chfe_to_esrp_msgs = collector.get_responses("IF_ESRP_CHFE")

    # OSP -> BCF
    osp_to_bcf_invite = _first_by_method(osp_to_bcf_msgs, "INVITE")
    osp_to_bcf_ack = _first_by_method(osp_to_bcf_msgs, "ACK")
    osp_to_bcf_bye = _first_by_method(osp_to_bcf_msgs, "BYE")

    # BCF -> OSP
    bcf_to_osp_100_trying = _first_by_status(bcf_to_osp_msgs, "100")
    bcf_to_osp_180_ringing = _first_by_status(bcf_to_osp_msgs, "180")
    bcf_to_osp_200_ok = _first_by_status(bcf_to_osp_msgs, "200", cseq_method="INVITE")
    bcf_to_osp_bye_ok = _first_by_status(bcf_to_osp_msgs, "200", cseq_method="BYE")

    # BCF -> ESRP
    bcf_to_esrp_invite = _first_by_method(bcf_to_esrp_msgs, "INVITE")
    bcf_to_esrp_ack = _first_by_method(bcf_to_esrp_msgs, "ACK")
    bcf_to_esrp_bye = _first_by_method(bcf_to_esrp_msgs, "BYE")

    # ESRP -> BCF
    esrp_to_bcf_100_trying = _first_by_status(esrp_to_bcf_msgs, "100")
    esrp_to_bcf_180_ringing = _first_by_status(esrp_to_bcf_msgs, "180")
    esrp_to_bcf_200_ok = _first_by_status(esrp_to_bcf_msgs, "200", cseq_method="INVITE")
    esrp_to_bcf_bye_ok = _first_by_status(esrp_to_bcf_msgs, "200", cseq_method="BYE")

    # ESRP -> CHFE
    esrp_to_chfe_invite = _first_by_method(esrp_to_chfe_msgs, "INVITE")
    esrp_to_chfe_ack = _first_by_method(esrp_to_chfe_msgs, "ACK")
    esrp_to_chfe_bye = _first_by_method(esrp_to_chfe_msgs, "BYE")

    # CHFE -> ESRP
    chfe_to_esrp_100_trying = _first_by_status(chfe_to_esrp_msgs, "100")
    chfe_to_esrp_180_ringing = _first_by_status(chfe_to_esrp_msgs, "180")

    if not chfe_to_esrp_180_ringing and chfe_to_esrp_100_trying:
        print(
            "⚠️WARNING: CHFE to ESRP 100 Trying found BUT CHFE to ESRP 180 Ringing not found.\n"
            "⚠️This may lead to wrong test scenario results..."
        )

    chfe_to_esrp_200_ok = _first_by_status(
        chfe_to_esrp_msgs, "200", cseq_method="INVITE"
    )
    chfe_to_esrp_bye_ok = _first_by_status(chfe_to_esrp_msgs, "200", cseq_method="BYE")

    # RTP Media
    osp_bcf_media = rtp_collector.get_all("IF_OSP_BCF")
    is_valid_osp_to_bcf_media = sum(len(lst) for lst in osp_bcf_media) > 2

    bcf_chfe_media = rtp_collector.get_all("IF_BCF_CHFE")
    is_valid_bcf_to_chfe_media = sum(len(lst) for lst in bcf_chfe_media) > 2

    osp_to_bcf_invite_data = (
        _extract_invite_data(osp_to_bcf_invite, "OSP to BCF INVITE")
        if osp_to_bcf_invite
        else InviteData(message_descr="OSP to BCF INVITE")
    )
    osp_to_bcf_bye_data = (
        _extract_invite_data(osp_to_bcf_bye, "OSP to BCF BYE")
        if osp_to_bcf_invite
        else InviteData(message_descr="OSP to BCF BYE")
    )
    bcf_to_esrp_invite_data = (
        _extract_invite_data(bcf_to_esrp_invite, "BCF to ESRP INVITE")
        if bcf_to_esrp_invite
        else InviteData(message_descr="BCF to ESRP INVITE")
    )
    bcf_to_esrp_ack_data = (
        _extract_message_data(bcf_to_esrp_ack, "BCF to ESRP ACK")
        if bcf_to_esrp_ack
        else MessageData(message_descr="BCF to ESRP ACK")
    )
    bcf_to_esrp_bye_data = (
        _extract_message_data(bcf_to_esrp_bye, "BCF to ESRP BYE")
        if bcf_to_esrp_bye
        else MessageData(message_descr="BCF to ESRP BYE")
    )
    bcf_to_osp_ok_data = (
        _extract_message_data(bcf_to_osp_200_ok, "BCF to OSP 200 OK")
        if bcf_to_osp_200_ok
        else MessageData(message_descr="BCF to OSP 200 OK")
    )
    esrp_to_chfe_invite_data = (
        _extract_invite_data(esrp_to_chfe_invite, "ESRP to CHFE INVITE")
        if esrp_to_chfe_invite
        else InviteData(message_descr="ESRP to CHFE INVITE")
    )
    # esrp_to_chfe_ack_data = _extract_message_data(esrp_to_chfe_ack, "ESRP to CHFE ACK") if esrp_to_chfe_ack else MessageData(message_descr="ESRP to CHFE ACK")
    esrp_to_chfe_bye_data = (
        _extract_message_data(esrp_to_chfe_bye, "ESRP to CHFE BYE")
        if esrp_to_chfe_bye
        else MessageData(message_descr="ESRP to CHFE BYE")
    )
    # esrp_to_bcf_ok_data = _extract_message_data(esrp_to_bcf_200_ok, "ESRP to BCF 200 OK") if esrp_to_bcf_200_ok else MessageData(message_descr="ESRP to BCF 200 OK")
    chfe_to_esrp_200_ok_data = (
        _extract_message_data(chfe_to_esrp_200_ok, "CHFE to ESRP 200 OK")
        if chfe_to_esrp_200_ok
        else MessageData(message_descr="CHFE to ESRP 200 OK")
    )

    return (
        osp_to_bcf_invite_data,
        bcf_to_osp_100_trying,
        bcf_to_esrp_invite_data,
        esrp_to_bcf_100_trying,
        esrp_to_chfe_invite_data,
        chfe_to_esrp_100_trying,
        chfe_to_esrp_180_ringing,
        esrp_to_bcf_180_ringing,
        bcf_to_osp_180_ringing,
        chfe_to_esrp_200_ok_data,
        esrp_to_bcf_200_ok,
        bcf_to_osp_200_ok,
        bcf_to_osp_ok_data,
        osp_to_bcf_ack,
        bcf_to_esrp_ack,
        bcf_to_esrp_ack_data,
        esrp_to_chfe_ack,
        osp_to_bcf_bye,
        osp_to_bcf_bye_data,
        bcf_to_esrp_bye,
        bcf_to_esrp_bye_data,
        esrp_to_chfe_bye_data,
        chfe_to_esrp_bye_ok,
        esrp_to_bcf_bye_ok,
        bcf_to_osp_bye_ok,
        bcf_fqdn_or_ip,
        is_valid_bcf_to_chfe_media,
        is_valid_osp_to_bcf_media,
    )


def get_test_names() -> list:
    return [
        # OSP
        "BCF receives the INVITE from OSP",
        "OSP sends ACK to BCF",
        # BCF
        "BCF sends 100 Trying to OSP",
        "BCF sends INVITE to ESRP",
        "BCF sends 180 Ringing to OSP",
        "BCF sends 200 OK to OSP",
        "BCF sends ACK to ESRP",
        "BCF INVITE: Route header added on top",
        "BCF INVITE: Via header added on top",
        "BCF INVITE: Record-Route header added on top",
        "BCF INVITE: out messages headers preserved",
        "BCF INVITE: 'To' header values preserved",
        "BCF INVITE: 'From' header values preserved",
        "BCF INVITE: 'Request URI' header values preserved",
        "BCF INVITE: 'Resource-Priority' header values preserved",
        "BCF INVITE: out messages body preserved except SDP",
        "BCF INVITE: To header set to urn:service:sos",
        "BCF INVITE: Request-URI set to urn:service:sos",
        "BCF INVITE: Call-Info contains Emergency Call Identifier (CallId)",
        "BCF INVITE: Emergency Call Identifier URN",
        "BCF INVITE: Emergency Call Identifier String ID",
        "BCF INVITE: Emergency Call Identifier FQDN",
        "BCF INVITE: Call-Info contains Incident Tracking Identifier (IncidentId)",
        "BCF INVITE: Incident Tracking Identifier String ID",
        "BCF INVITE: Incident Tracking Identifier FQDN",
        "BCF INVITE: Call-Info contains emergency-source",
        "BCF INVITE: Resource-Priority is esnet value",
        "BCF INVITE: 'Call-Info' was added with value pattern ALPHANUMERIC_UNIQUE_ID@BCF_FQDN with parameter purpose=emergency-source",
        "BCF INVITE: 'Contact' header field must be changed to SIP URI with the BCF FQDN/IP",
        "BCF INVITE: SDP message body must be changed to anchor media",
        "BCF INVITE: Geolocation present",
        # BCF BYE
        "BCF BYE: Route header added on top",
        "BCF BYE: Via header added on top",
        "BCF BYE: Record-Route header added on top",
        "BCF BYE: out messages headers preserved",
        "BCF BYE: 'To' header values preserved",
        "BCF BYE: 'From' header values preserved",
        "BCF BYE: 'Request URI' header values preserved",
        "BCF BYE: 'Resource-Priority' header values preserved",
        # ESRP
        "ESRP sends 100 Trying to BCF",
        "ESRP sends 180 Ringing to BCF",
        "ESRP send SIP INVITE to CHFE",
        "ESRP sends 200 OK to BCF",
        "ESRP sends ACK to CHFE",
        "ESRP INVITE: Route header added on top",
        "ESRP INVITE: Via header added on top",
        "ESRP INVITE: Record-Route header added on top",
        "ESRP INVITE: Non-variable headers preserved",
        "ESRP INVITE: To header remains urn:service:sos",
        "ESRP INVITE: 'To' header values preserved",
        "ESRP INVITE: 'Request URI' header values preserved",
        "ESRP INVITE: 'Resource-Priority' header values preserved",
        "ESRP INVITE: Request-URI remains urn:service:sos",
        "ESRP INVITE: Emergency Call Identifier (CallId) preserved from BCF",
        "ESRP INVITE: Emergency Call Identifier URN",
        "ESRP INVITE: Emergency Call Identifier String ID",
        "ESRP INVITE: Emergency Call Identifier FQDN",
        "ESRP INVITE: Incident Tracking Identifier (IncidentId) preserved from BCF",
        "ESRP INVITE: Geolocation present",
        # CHFE
        "CHFE sends 180 Ringing to ESRP",
        "CHFE sends 200 OK to ESRP",
        # ESRP BYE
        "ESRP BYE: Route header added on top",
        "ESRP BYE: Via header added on top",
        "ESRP BYE: Record-Route header added on top",
        "ESRP BYE: Non-variable headers preserved",
        "ESRP BYE: 'To' header values preserved",
        "ESRP BYE: 'Request URI' header values preserved",
        "ESRP BYE: 'Resource-Priority' header values preserved",
        # Media
        "Media stream established between OSP and BCF",
        "Media stream established between BCF and CHFE",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        osp_to_bcf_invite_data,
        bcf_to_osp_100_trying,
        bcf_to_esrp_invite_data,
        esrp_to_bcf_100_trying,
        esrp_to_chfe_invite_data,
        chfe_to_esrp_100_trying,
        chfe_to_esrp_180_ringing,
        esrp_to_bcf_180_ringing,
        bcf_to_osp_180_ringing,
        chfe_to_esrp_200_ok_data,
        esrp_to_bcf_200_ok,
        bcf_to_osp_200_ok,
        bcf_to_osp_ok_data,
        osp_to_bcf_ack,
        bcf_to_esrp_ack,
        bcf_to_esrp_ack_data,
        esrp_to_chfe_ack,
        osp_to_bcf_bye,
        osp_to_bcf_bye_data,
        bcf_to_esrp_bye,
        bcf_to_esrp_bye_data,
        esrp_to_chfe_bye_data,
        chfe_to_esrp_bye_ok,
        esrp_to_bcf_bye_ok,
        bcf_to_osp_bye_ok,
        bcf_fqdn_or_ip,
        is_valid_bcf_to_chfe_media,
        is_valid_osp_to_bcf_media,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)

    return [
        TestCheck(
            test_name="BCF receives the INVITE from OSP",
            test_method=is_data_present,
            test_params={
                "test_data": osp_to_bcf_invite_data.message,
                "error": "FAILED -> BCF did not receive INVITE from OSP",
            },
        ),
        TestCheck(
            test_name="OSP sends ACK to BCF",
            test_method=is_data_present,
            precondition=bcf_to_osp_200_ok,
            precondition_error="NOT RUN -> No BCF to OSP 200 OK found",
            test_params={
                "test_data": osp_to_bcf_ack,
                "error": "FAILED -> OSP did not send ACK to BCF",
            },
        ),
        # --- BCF messages ---
        TestCheck(
            test_name="BCF sends 100 Trying to OSP",
            test_method=is_data_present,
            test_params={
                "test_data": bcf_to_osp_100_trying,
                "error": "FAILED -> BCF did not send 100 Trying to OSP",
            },
        ),
        TestCheck(
            test_name="BCF sends INVITE to ESRP",
            test_method=is_data_present,
            test_params={
                "test_data": bcf_to_esrp_invite_data.message,
                "error": "FAILED -> BCF did not send INVITE to ESRP",
            },
        ),
        TestCheck(
            test_name="BCF sends 180 Ringing to OSP",
            test_method=is_data_present,
            precondition=esrp_to_bcf_180_ringing,
            precondition_error="NOT RUN -> No ESRP 180 to BCF Ringing not found",
            test_params={
                "test_data": bcf_to_osp_180_ringing,
                "error": "FAILED -> BCF did not send 180 Ringing to OSP",
            },
        ),
        TestCheck(
            test_name="BCF sends 200 OK to OSP",
            test_method=is_data_present,
            precondition=esrp_to_bcf_200_ok,
            precondition_error="NOT RUN -> No ESRP to BCF 200 OK found",
            test_params={
                "test_data": bcf_to_osp_200_ok,
                "error": "FAILED -> BCF did not send 200 OK to OSP",
            },
        ),
        TestCheck(
            test_name="BCF sends ACK to ESRP",
            test_method=is_data_present,
            precondition=osp_to_bcf_ack,
            precondition_error="NOT RUN -> No OSP to BCF ACK found",
            test_params={
                "test_data": bcf_to_esrp_ack,
                "error": "FAILED -> BCF did not send ACK to ESRP",
            },
        ),
        # --- BCF INVITE output checks ---
        TestCheck(
            test_name="BCF INVITE: Route header added on top",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": osp_to_bcf_invite_data.message,
                "output": bcf_to_esrp_invite_data.message,
                "header_field_name": "Route",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Via header added on top",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": osp_to_bcf_invite_data.message,
                "output": bcf_to_esrp_invite_data.message,
                "header_field_name": "Via",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Record-Route header added on top",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": osp_to_bcf_invite_data.message,
                "output": bcf_to_esrp_invite_data.message,
                "header_field_name": "Record-Route",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: out messages headers preserved",
            test_method=test_all_header_fields_are_same,
            test_params={
                "messages": [
                    osp_to_bcf_invite_data.message,
                    bcf_to_esrp_invite_data.message,
                ],
                "exception_headers": HEADERS_EXCEPTION_LIST,
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        osp_to_bcf_invite_data,
                        bcf_to_esrp_invite_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="BCF INVITE: 'To' header values preserved",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": osp_to_bcf_invite_data.to_header,
                "output_values": [
                    bcf_to_esrp_invite_data.to_header,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: 'From' header values preserved",
            test_method=test_from_unchanged_if_valid_verstat,
            test_params={
                "stimulus": osp_to_bcf_invite_data.from_header,
                "outputs": [
                    bcf_to_esrp_invite_data.from_header,
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        bcf_to_esrp_invite_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="BCF INVITE: 'Request URI' header values preserved",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": osp_to_bcf_invite_data.requests_uri,
                "output_values": [
                    bcf_to_esrp_invite_data.requests_uri,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: 'Resource-Priority' header values preserved",
            test_method=test_resource_priority_unchanged_if_valid,
            test_params={
                "stimulus_rp": osp_to_bcf_invite_data.resource_priority,
                "outputs": [
                    bcf_to_esrp_invite_data.resource_priority,
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        bcf_to_esrp_invite_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="BCF INVITE: out messages body preserved except SDP",
            test_method=test_keeping_original_message_bodies,
            test_params={
                "stimulus_message_body_list": osp_to_bcf_invite_data.message_body,
                "output_message_body_list": bcf_to_esrp_invite_data.message_body,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: To header set to urn:service:sos",
            test_method=test_urn_service_sos_in_to_header_field,
            test_params={"output": bcf_to_esrp_invite_data.message},
        ),
        TestCheck(
            test_name="BCF INVITE: Request-URI set to urn:service:sos",
            test_method=test_urn_service_sos_in_request_uri,
            test_params={"output": bcf_to_esrp_invite_data.message},
        ),
        TestCheck(
            test_name="BCF INVITE: Call-Info contains Emergency Call Identifier (CallId)",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": "Call-Info purpose=CallId",
                "parameter_value": bcf_to_esrp_invite_data.call_id,
                "expected_value": "urn:emergency:uid:callid:",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Emergency Call Identifier URN",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": bcf_to_esrp_invite_data.call_id,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Emergency Call Identifier String ID",
            test_method=test_emergency_call_id_string_id,
            test_params={
                "emergency_call_id_header": bcf_to_esrp_invite_data.call_id,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Emergency Call Identifier FQDN",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": bcf_to_esrp_invite_data.call_id,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Call-Info contains Incident Tracking Identifier (IncidentId)",
            test_method=test_incident_tracking_id_urn,
            test_params={
                "incident_tracking_id_header": bcf_to_esrp_invite_data.incident_id,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Incident Tracking Identifier String ID",
            test_method=test_incident_tracking_id_string_id,
            test_params={
                "incident_tracking_id_header": bcf_to_esrp_invite_data.incident_id,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Incident Tracking Identifier FQDN",
            test_method=test_incident_tracking_id_fqdn,
            test_params={
                "incident_tracking_id_header": bcf_to_esrp_invite_data.incident_id,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Call-Info contains emergency-source",
            test_method=is_data_present,
            test_params={
                "test_data": bcf_to_esrp_invite_data.emergency_source,
                "error": "FAILED -> Call-Info purpose=emergency-source not found in BCF output",
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Resource-Priority is esnet value",
            test_method=test_if_parameter_has_one_of_expected_values,
            test_params={
                "parameter_name": "Resource-Priority",
                "parameter_value": bcf_to_esrp_invite_data.resource_priority,
                "expected_values": ["esnet.0", "esnet.1", "esnet.2"],
            },
        ),
        TestCheck(
            test_name="BCF INVITE: 'Call-Info' was added with value pattern ALPHANUMERIC_UNIQUE_ID@BCF_FQDN with parameter purpose=emergency-source",
            test_method=validate_bcf_and_source_id,
            test_params={
                "stimulus_messages": osp_to_bcf_invite_data.message,
                "bcf_output_messages": bcf_to_esrp_invite_data.message,
                "source_id_list": bcf_to_esrp_invite_data.emergency_source,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: 'Contact' header field must be changed to SIP URI with the BCF FQDN/IP",
            test_method=validate_contact_header_field,
            test_params={
                "contact": bcf_to_esrp_invite_data.contact_header,
                "sip_uri": bcf_to_esrp_invite_data.requests_uri,
                "bcf_fqdn_or_ip": bcf_fqdn_or_ip,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: SDP message body must be changed to anchor media",
            test_method=validate_sdp_media_message_body,
            test_params={
                "media_data": bcf_to_esrp_invite_data.message_body,
                "bcf_fqdn_or_ip": bcf_fqdn_or_ip,
            },
        ),
        TestCheck(
            test_name="BCF INVITE: Geolocation present",
            test_method=test_geolocation_is_valid,
            test_params={
                "message_data": bcf_to_esrp_invite_data,
            },
        ),
        # --- BCF BYE output checks ---
        TestCheck(
            test_name="BCF BYE: Route header added on top",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": osp_to_bcf_bye_data.message,
                "output": bcf_to_esrp_bye_data.message,
                "header_field_name": "Route",
            },
        ),
        TestCheck(
            test_name="BCF BYE: Via header added on top",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": osp_to_bcf_bye_data.message,
                "output": bcf_to_esrp_bye_data.message,
                "header_field_name": "Via",
            },
        ),
        TestCheck(
            test_name="BCF BYE: Record-Route header added on top",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": osp_to_bcf_bye_data.message,
                "output": bcf_to_esrp_bye_data.message,
                "header_field_name": "Record-Route",
            },
        ),
        TestCheck(
            test_name="BCF BYE: out messages headers preserved",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_all_header_fields_are_same,
            test_params={
                "messages": [
                    osp_to_bcf_bye_data.message,
                    bcf_to_esrp_bye_data.message,
                ],
                "exception_headers": HEADERS_EXCEPTION_LIST,
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        osp_to_bcf_bye_data,
                        bcf_to_esrp_bye_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="BCF BYE: 'To' header values preserved",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": osp_to_bcf_bye_data.to_header,
                "output_values": [
                    bcf_to_esrp_bye_data.to_header,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="BCF BYE: 'From' header values preserved",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_from_unchanged_if_valid_verstat,
            test_params={
                "stimulus": osp_to_bcf_bye_data.from_header,
                "outputs": [
                    bcf_to_esrp_bye_data.from_header,
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        bcf_to_esrp_bye_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="BCF BYE: 'Request URI' header values preserved",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": osp_to_bcf_bye_data.requests_uri,
                "output_values": [
                    bcf_to_esrp_bye_data.requests_uri,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="BCF BYE: 'Resource-Priority' header values preserved",
            precondition=osp_to_bcf_bye,
            precondition_error="NOT RUN -> No OSP to BCF BYE message found",
            test_method=test_resource_priority_unchanged_if_valid,
            test_params={
                "stimulus_rp": osp_to_bcf_bye_data.resource_priority,
                "outputs": [
                    bcf_to_esrp_bye_data.resource_priority,
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        bcf_to_esrp_bye_data,
                    ]
                ],
            },
        ),
        # --- ESRP messages (INTEROP_2.4_TMS_12, TMS_74, TMS_84) ---
        TestCheck(
            test_name="ESRP sends 100 Trying to BCF",
            test_method=is_data_present,
            precondition=bcf_to_esrp_invite_data.message,
            precondition_error="NOT RUN -> No BCF TO ESRP SIP INVITE found",
            test_params={
                "test_data": esrp_to_bcf_100_trying,
                "error": "FAILED -> ESRP did not send 100 Trying to BCF",
            },
        ),
        TestCheck(
            test_name="ESRP send SIP INVITE to CHFE",
            test_method=is_data_present,
            precondition=bcf_to_esrp_invite_data.message,
            precondition_error="NOT RUN -> No BCF TO ESRP SIP INVITE found",
            test_params={
                "test_data": esrp_to_chfe_invite_data.message,
                "error": "FAILED -> ESRP did not send SIP INVITE to CHFE",
            },
        ),
        TestCheck(
            test_name="ESRP sends 200 OK to BCF",
            test_method=is_data_present,
            precondition=chfe_to_esrp_200_ok_data,
            precondition_error="NOT RUN -> No CHFE to ESRP 200 OK found",
            test_params={
                "test_data": esrp_to_bcf_200_ok,
                "error": "FAILED -> ESRP did not send 200 OK to BCF",
            },
        ),
        TestCheck(
            test_name="ESRP sends ACK to CHFE",
            test_method=is_data_present,
            precondition=bcf_to_esrp_ack,
            precondition_error="NOT RUN -> No BCF to ESRP ACK found",
            test_params={
                "test_data": esrp_to_chfe_ack,
                "error": "FAILED -> ESRP did not send ACK to CHFE",
            },
        ),
        # --- ESRP INVITE output checks ---
        TestCheck(
            test_name="ESRP INVITE: Route header added on top",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": bcf_to_esrp_invite_data.message,
                "output": esrp_to_chfe_invite_data.message,
                "header_field_name": "Route",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Via header added on top",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": bcf_to_esrp_invite_data.message,
                "output": esrp_to_chfe_invite_data.message,
                "header_field_name": "Via",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Record-Route header added on top",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": bcf_to_esrp_invite_data.message,
                "output": esrp_to_chfe_invite_data.message,
                "header_field_name": "Record-Route",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Non-variable headers preserved",
            test_method=test_all_header_fields_are_same,
            test_params={
                "messages": [
                    bcf_to_esrp_invite_data.message,
                    esrp_to_chfe_invite_data.message,
                ],
                "exception_headers": [
                    h for h in HEADERS_EXCEPTION_LIST if h != "Contact"
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        bcf_to_esrp_invite_data,
                        esrp_to_chfe_invite_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: 'To' header values preserved",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": bcf_to_esrp_invite_data.to_header,
                "output_values": [
                    esrp_to_chfe_invite_data.to_header,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: 'Request URI' header values preserved",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": bcf_to_esrp_invite_data.requests_uri,
                "output_values": [
                    esrp_to_chfe_invite_data.requests_uri,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: 'Resource-Priority' header values preserved",
            test_method=test_resource_priority_unchanged_if_valid,
            test_params={
                "stimulus_rp": bcf_to_esrp_invite_data.resource_priority,
                "outputs": [
                    esrp_to_chfe_invite_data.resource_priority,
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        esrp_to_chfe_invite_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: To header remains urn:service:sos",
            test_method=test_urn_service_sos_in_to_header_field,
            test_params={"output": esrp_to_chfe_invite_data.message},
        ),
        TestCheck(
            test_name="ESRP INVITE: Request-URI remains urn:service:sos",
            test_method=test_urn_service_sos_in_request_uri,
            test_params={"output": esrp_to_chfe_invite_data.message},
        ),
        TestCheck(
            test_name="ESRP INVITE: Emergency Call Identifier (CallId) preserved from BCF",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": bcf_to_esrp_invite_data.call_id,
                "actual_data": esrp_to_chfe_invite_data.call_id,
                "error": "Call-Info purpose=CallId changed by ESRP",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Emergency Call Identifier URN",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": esrp_to_chfe_invite_data.call_id,
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Emergency Call Identifier String ID",
            test_method=test_emergency_call_id_string_id,
            test_params={
                "emergency_call_id_header": esrp_to_chfe_invite_data.call_id,
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Emergency Call Identifier FQDN",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": esrp_to_chfe_invite_data.call_id,
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Incident Tracking Identifier (IncidentId) preserved from BCF",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": bcf_to_esrp_invite_data.incident_id,
                "actual_data": esrp_to_chfe_invite_data.incident_id,
                "error": "Call-Info purpose=IncidentId changed by ESRP",
            },
        ),
        TestCheck(
            test_name="ESRP INVITE: Geolocation present",
            test_method=test_geolocation_is_valid,
            test_params={
                "message_data": esrp_to_chfe_invite_data,
            },
        ),
        TestCheck(
            test_name="ESRP sends 180 Ringing to BCF",
            test_method=is_data_present,
            precondition=chfe_to_esrp_180_ringing,  # NOTE: There might be cases when 180 Ringing is optional
            precondition_error="NOT RUN -> No CHFE to ESRP 180 Ringing not found",
            test_params={
                "test_data": esrp_to_bcf_180_ringing,
                "error": "FAILED -> ESRP did not send 180 Ringing to BCF",
            },
        ),
        # --- CHFE messages ---
        TestCheck(
            test_name="CHFE sends 180 Ringing to ESRP",
            test_method=is_data_present,
            precondition=esrp_to_chfe_invite_data.message,
            precondition_error="NOT RUN -> No ESRP to CHFE SIP INVITE found",
            test_params={
                "test_data": chfe_to_esrp_180_ringing,
                "error": "FAILED -> CHFE did not send 180 Ringing to ESRP",
            },
        ),
        TestCheck(
            test_name="CHFE sends 200 OK to ESRP",
            test_method=is_data_present,
            precondition=esrp_to_bcf_180_ringing,
            precondition_error="NOT RUN -> No ESRP to BCF 180 Ringing found",
            test_params={
                "test_data": chfe_to_esrp_200_ok_data.message,
                "error": "FAILED -> CHFE did not send 200 OK to ESRP",
            },
        ),
        # --- ESRP BYE output checks ---
        TestCheck(
            test_name="ESRP BYE: Route header added on top",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": bcf_to_esrp_bye_data.message,
                "output": esrp_to_chfe_bye_data.message,
                "header_field_name": "Route",
            },
        ),
        TestCheck(
            test_name="ESRP BYE: Via header added on top",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": bcf_to_esrp_bye_data.message,
                "output": esrp_to_chfe_bye_data.message,
                "header_field_name": "Via",
            },
        ),
        TestCheck(
            test_name="ESRP BYE: Record-Route header added on top",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_adding_header_field_on_top_of_its_section,
            test_params={
                "stimulus": bcf_to_esrp_bye_data.message,
                "output": esrp_to_chfe_bye_data.message,
                "header_field_name": "Record-Route",
            },
        ),
        TestCheck(
            test_name="ESRP BYE: Non-variable headers preserved",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_all_header_fields_are_same,
            test_params={
                "messages": [
                    bcf_to_esrp_bye_data.message,
                    esrp_to_chfe_bye_data.message,
                ],
                "exception_headers": [
                    h for h in HEADERS_EXCEPTION_LIST if h != "Contact"
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        bcf_to_esrp_bye_data,
                        esrp_to_chfe_bye_data,
                    ]
                ],
            },
        ),
        TestCheck(
            test_name="ESRP BYE: 'To' header values preserved",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": bcf_to_esrp_bye_data.to_header,
                "output_values": [
                    esrp_to_chfe_bye_data.to_header,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="ESRP BYE: 'Request URI' header values preserved",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_header_unchanged_if_equals,
            test_params={
                "stimulus_value": bcf_to_esrp_bye_data.requests_uri,
                "output_values": [
                    esrp_to_chfe_bye_data.requests_uri,
                ],
                "expected_value": "urn:service:sos",
            },
        ),
        TestCheck(
            test_name="ESRP BYE: 'Resource-Priority' header values preserved",
            precondition=bcf_to_esrp_bye_data.message,
            precondition_error="NOT RUN -> No BCF to ESRP BYE message found",
            test_method=test_resource_priority_unchanged_if_valid,
            test_params={
                "stimulus_rp": bcf_to_esrp_bye_data.resource_priority,
                "outputs": [
                    esrp_to_chfe_bye_data.resource_priority,
                ],
                "message_descriptions_list": [
                    msg.message_descr
                    for msg in [
                        esrp_to_chfe_bye_data,
                    ]
                ],
            },
        ),
        # --- Media streams  ---
        TestCheck(
            test_name="Media stream established between OSP and BCF",
            test_method=is_data_present,
            precondition=esrp_to_chfe_ack,
            precondition_error="NOT RUN -> NO ESRP to CHFE ACK found",
            test_params={
                "test_data": is_valid_osp_to_bcf_media,
                "error": "FAILED -> No bidirectional media stream found between OSP and BCF",
            },
        ),
        TestCheck(
            test_name="Media stream established between BCF and CHFE",
            test_method=is_data_present,
            precondition=esrp_to_chfe_ack,
            precondition_error="NOT RUN -> NO ESRP to CHFE ACK found",
            test_params={
                "test_data": is_valid_bcf_to_chfe_media,
                "error": "FAILED -> No bidirectional media stream found between BCF and CHFE",
            },
        ),
    ]
