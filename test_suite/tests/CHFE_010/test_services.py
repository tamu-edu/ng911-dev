from services.aux_services.json_services import (
    decode_jws,
    get_json,
    is_unsigned_jws,
    decode_base64url,
)
from services.aux_services.message_services import extract_json_data_from_http
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
from tests.CHFE_010.checks import (
    validate_logging_call_signaling_message,
)

from test_suite.services.aux_services.sip_services import extract_raw_sip_message_string


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
                    key_filepath = entity.certificate_key
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
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
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                key_filepath,
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
    raw_conference_invite_message = None
    json_data_from_message = None
    key_found = True
    payload_data = None
    post_to_logger_messages = None
    stimulus_timestamp = None

    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, key_filepath = (
        get_filter_parameters(lab_config, filtering_options, variation)
    )

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

    if stimulus_message:
        raw_conference_invite_message = extract_raw_sip_message_string(stimulus_message)
        if getattr(stimulus_message, "sniff_timestamp", None):
            stimulus_timestamp = float(stimulus_message.sniff_timestamp)

    post_to_logger_messages = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    if post_to_logger_messages:
        if hasattr(post_to_logger_messages, "http"):
            json_data_from_message = extract_json_data_from_http(
                post_to_logger_messages
            )

        if isinstance(json_data_from_message, dict) and is_unsigned_jws(
            json_data_from_message
        ):
            payload_data = get_json(
                decode_base64url(json_data_from_message.get("payload"))
            )
        else:
            try:
                _, payload_data = decode_jws(json_data_from_message, key_filepath)
            except FileExistsError:
                key_found = False

    return (
        stimulus_message,
        raw_conference_invite_message,
        post_to_logger_messages,
        json_data_from_message,
        key_found,
        payload_data,
        stimulus_timestamp,
    )


def get_test_names() -> list:
    return ["Verify CallSignallingMessageLogEvent members and message logging"]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_message,
        raw_conference_invite_message,
        post_to_logger_messages,
        json_data_from_message,
        key_found,
        payload_data,
        stimulus_timestamp,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify CallSignallingMessageLogEvent members and message logging",
            test_method=validate_logging_call_signaling_message,
            test_params={
                "stimulus_message": stimulus_message,
                "raw_conference_invite_message": raw_conference_invite_message,
                "post_to_logger_messages": post_to_logger_messages,
                "json_data_from_message": json_data_from_message,
                "key_found": key_found,
                "payload_data": payload_data,
                "stimulus_timestamp": stimulus_timestamp,
            },
        ),
    ]
