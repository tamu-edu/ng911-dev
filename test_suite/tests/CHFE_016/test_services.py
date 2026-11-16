from dataclasses import dataclass
from pyshark.packet.packet import Packet

from services.aux_services.message_services import (
    get_messages,
    get_header_field_value,
    get_message_and_jws_by_event_type,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_016.checks import (
    validate_rec_call_start_log_events,
    validate_rec_call_end_log_events,
)


@dataclass
class TestData:
    stimulus_message: Packet | None = None
    stimulus_timestamp: float = None
    invite_to_logger_message_timestamp: float = None
    bye_to_logger_message_timestamp: float = None
    invite_to_logger_call_id_sip: str | None = None
    stimulus_call_id: str | None = None
    stimulus_call_sip_id: str | None = None
    stimulus_incident_id: str | None = None
    rec_call_start_jws: dict | None = None
    rec_call_start_msg: Packet | None = None
    rec_call_end_jws: dict | None = None
    rec_call_end_msg: Packet | None = None
    chfe_fqdn: str | None = None


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    key_filepath = None
    iut_entity = lab_config.get_conformance_iut_entity()
    chfe_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                    key_filepath = entity.certificate_key
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        elif not chfe_fqdn:
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required FQDN records for CHFE interfaces"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                key_filepath,
                chfe_fqdn,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    test_data = TestData()

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        key_filepath,
        chfe_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )

    if stimulus_message and hasattr(stimulus_message, "sip"):
        if hasattr(stimulus_message.sip, "Call-ID"):
            test_data.stimulus_call_sip_id = get_header_field_value(
                stimulus_message, "Call-ID"
            )

        if hasattr(stimulus_message.sip, "Call-Info"):
            sip_raw = str(stimulus_message.sip)
            call_infos = []
            for line in sip_raw.splitlines():
                line = line.strip()
                if line.lower().startswith("call-info"):
                    if ":" in line:
                        call_infos.append(line.split(":", 1)[1].strip())

            test_data.stimulus_call_id, test_data.stimulus_incident_id = (
                call_infos + [None, None]
            )[:2]

    if getattr(stimulus_message, "sniff_timestamp", 0):
        test_data.stimulus_timestamp = float(stimulus_message.sniff_timestamp)

    invite_to_logger_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
            after_timestamp=test_data.stimulus_timestamp,
        ),
    )

    if getattr(invite_to_logger_message, "sniff_timestamp", 0):
        test_data.invite_to_logger_message_timestamp = float(
            invite_to_logger_message.sniff_timestamp
        )

    if invite_to_logger_message:
        if hasattr(invite_to_logger_message, "sip") and hasattr(
            invite_to_logger_message.sip, "Call-ID"
        ):
            test_data.invite_to_logger_call_id_sip = get_header_field_value(
                invite_to_logger_message, "Call-ID"
            )

    post_to_logger_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=test_data.invite_to_logger_message_timestamp,
        ),
    )

    bye_to_logger_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.BYE,
            ],
            after_timestamp=test_data.invite_to_logger_message_timestamp,
        ),
    )

    if bye_to_logger_message:
        if getattr(bye_to_logger_message, "sniff_timestamp", 0):
            test_data.bye_to_logger_message_timestamp = float(
                bye_to_logger_message.sniff_timestamp
            )

    if post_to_logger_messages:
        jws_start_event, message_start_event = get_message_and_jws_by_event_type(
            post_to_logger_messages,
            "RecCallStartLogEvent",
            key_filepath,
        )

        jws_end_event, message_end_event = get_message_and_jws_by_event_type(
            post_to_logger_messages,
            "RecCallEndLogEvent",
            key_filepath,
        )

        test_data.rec_call_start_jws = jws_start_event
        test_data.rec_call_start_msg = message_start_event

        test_data.rec_call_end_jws = jws_end_event
        test_data.rec_call_end_msg = message_end_event

    test_data.stimulus_message = stimulus_message
    test_data.chfe_fqdn = chfe_fqdn

    return test_data


def get_test_names() -> list:
    return [
        "Verify logging of RecCallStartLogEvent members",
        "Verify logging of RecCallEndLogEvent members",
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

    return [
        TestCheck(
            test_name="Verify logging of RecCallStartLogEvent members",
            test_method=validate_rec_call_start_log_events,
            test_params={
                "test_data": test_data,
            },
        ),
        TestCheck(
            test_name="Verify logging of RecCallEndLogEvent members",
            test_method=validate_rec_call_end_log_events,
            test_params={
                "test_data": test_data,
            },
        ),
    ]
